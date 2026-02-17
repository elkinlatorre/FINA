import json
from langchain_groq import ChatGroq
from app.core.settings import settings
from app.core.logger import get_logger
from app.graph.state import AgentState

logger = get_logger("GUARDRAILS")

def get_guard_llm(model_name: str):
    """Creates a guardrail LLM instance."""
    return ChatGroq(
        temperature=0,
        model_name=model_name,
        groq_api_key=settings.GROQ_API_KEY
    )

async def input_guardrail(state: AgentState):
    """
    Checks if the user input is within the allowed financial domain.
    """
    if not settings.ENABLE_GUARDRAILS:
        return {"safety_metadata": {"is_safe": True, "reason": None, "category": "disabled"}}

    messages = state.get("messages", [])
    if not messages:
        return {"safety_metadata": {"is_safe": True, "reason": "No messages", "category": "empty"}}

    last_user_message = messages[-1].content
    logger.info(f"🔍 INPUT GUARDRAIL START: Checking message: '{last_user_message[:50]}...'")
    
    # Cascade list
    models_to_try = [settings.LLM_MODEL] + settings.LLM_FALLBACK_MODELS
    prompt = settings.GUARDRAIL_PROMPT.format(domain=settings.GUARDRAIL_SENSITIVE_DOMAIN)
    
    last_error = None
    response = None

    for model_name in models_to_try:
        try:
            logger.info(f"Guardrail is running using model: {model_name}")
            llm = get_guard_llm(model_name)
            
            # We wrap the user query in a system context for the guardrail
            system_msg = {"role": "system", "content": prompt}
            user_msg = {"role": "user", "content": last_user_message}
            guard_messages = [system_msg, user_msg]
            
            response = await llm.ainvoke(guard_messages)
            break # Success
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = "429" in error_str or "rate_limit_exceeded" in error_str
            is_invalid_model = "400" in error_str or "model_decommissioned" in error_str or "not supported" in error_str
            
            if is_rate_limit or is_invalid_model:
                reason = "hit rate limit" if is_rate_limit else "is decommissioned/unsupported"
                logger.warning(f"⚠️ Guardrail model {model_name} {reason}. Trying fallback...")
                last_error = e
                continue
            else:
                logger.error(f"❌ Guardrail unexpected error with {model_name}: {error_str}")
                # For non-transient errors, we might want to fail the guardrail (or fail open)
                # But here we'll continue to see if another model works unless it's a critical auth error
                last_error = e
                continue

    if not response:
        logger.error("🛑 All Guardrail models failed.")
        # Fall-safe: if guardrail fails completely, we allow the message but log it
        return {"safety_metadata": {"is_safe": True, "reason": "All guardrail models failed", "category": "error"}}

    try:
        # Robust JSON extraction using regex (finds first { and last })
        import re
        match = re.search(r'(\{.*\})', response.content, re.DOTALL)
        if match:
            json_str = match.group(1)
            result = json.loads(json_str)
        else:
            # Fallback for plain JSON without delimiters
            result = json.loads(response.content.strip())
            
        logger.info(f"Guardrail result: {result}")
        
        # --- TOKEN EXTRACTION ---
        usage_meta = getattr(response, "usage_metadata", {})
        if not usage_meta:
            usage_meta = response.response_metadata.get("token_usage") or response.response_metadata.get("usage") or {}
            
        p_tokens = usage_meta.get("input_tokens") or usage_meta.get("prompt_tokens") or 0
        c_tokens = usage_meta.get("output_tokens") or usage_meta.get("completion_tokens") or 0
        
        if p_tokens == 0 and c_tokens == 0:
            p_tokens = sum(len(str(m)) for m in guard_messages) // 4
            c_tokens = len(response.content) // 4
            
        cost = (
            (p_tokens * settings.PRICE_1K_PROMPT) / 1000 +
            (c_tokens * settings.PRICE_1K_COMPLETION) / 1000
        )
        
        updates = {
            "safety_metadata": result,
            "usage": {
                "prompt_tokens": p_tokens,
                "completion_tokens": c_tokens,
                "total_tokens": p_tokens + c_tokens,
                "estimated_cost": cost
            }
        }
        
        if not result.get("is_safe", True):
            from langchain_core.messages import AIMessage
            block_msg = AIMessage(content=f"I'm sorry, I cannot process your request. Reason: {result.get('reason', 'Outside of allowed scope')}")
            updates["messages"] = [block_msg]
            
        logger.info(f"✅ INPUT GUARDRAIL END: result={result.get('is_safe', True)}")
        return updates
    except Exception as e:
        logger.error(f"Error in input guardrail: {e}. Raw content: {response.content if 'response' in locals() else 'N/A'}")
        # Default to safe if guardrail fails, but log heavily
        return {"safety_metadata": {"is_safe": True, "reason": "Guardrail error", "category": "error"}}

async def output_guardrail(state: AgentState):
    """
    Checks the agent output for compliance and adds disclaimers if needed.
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    last_message = messages[-1]
    content = getattr(last_message, "content", "")
    logger.info(f"🛡️ OUTPUT GUARDRAIL START: Checking response content (length: {len(content)})")
    
    # Financial triggers to trigger disclaimer
    financial_triggers = ["advice", "invest", "portfolio", "recommendation", "buy", "sell", "asset", "shares", "stock", "balance"]
    disclaimer = "\n\n*Note: This information is for educational purposes and does not constitute legal financial advice.*"
    
    content_lower = content.lower()
    should_add_disclaimer = any(trigger in content_lower for trigger in financial_triggers)
    
    if content and should_add_disclaimer:
        if disclaimer not in content:
            logger.info("➕ Adding mandatory financial disclaimer to response.")
            from langchain_core.messages import AIMessage
            
            # Create a NEW message to ensure compatibility with all checkpointers
            if isinstance(last_message, AIMessage):
                last_message = AIMessage(
                    content=content + disclaimer,
                    tool_calls=last_message.tool_calls,
                    additional_kwargs=last_message.additional_kwargs,
                    response_metadata=last_message.response_metadata,
                    id=last_message.id
                )
            else:
                # Fallback for simpler message types or dicts
                if hasattr(last_message, "content"):
                    last_message.content = content + disclaimer
                elif isinstance(last_message, dict):
                    last_message["content"] = content + disclaimer
            
    logger.info("✅ OUTPUT GUARDRAIL END")
    return {"messages": [last_message]}
