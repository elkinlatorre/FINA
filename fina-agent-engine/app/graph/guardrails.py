import json
from langchain_groq import ChatGroq
from app.core.settings import settings
from app.core.logger import get_logger
from app.graph.state import AgentState

logger = get_logger("GUARDRAILS")

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
    
    llm = ChatGroq(
        temperature=0,
        model_name=settings.LLM_MODEL,
        groq_api_key=settings.GROQ_API_KEY
    )

    prompt = settings.GUARDRAIL_PROMPT.format(domain=settings.GUARDRAIL_SENSITIVE_DOMAIN)
    
    try:
        # We wrap the user query in a system context for the guardrail
        system_msg = {"role": "system", "content": prompt}
        user_msg = {"role": "user", "content": last_user_message}
        guard_messages = [system_msg, user_msg]
        
        response = await llm.ainvoke(guard_messages)
        
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
    # This could be more complex, but for now we'll check if it's already marked as review
    # or if we need to append a mandatory disclaimer.
    messages = state.get("messages", [])
    if not messages:
        return state

    last_message = messages[-1]
    logger.info(f"🛡️ OUTPUT GUARDRAIL START: Checking response content (length: {len(getattr(last_message, 'content', ''))})")
    
    # Example: Check if it's an AI message and doesn't have a disclaimer
    disclaimer = "\n\n*Note: This information is for educational purposes and does not constitute legal financial advice.*"
    
    # Financial keywords to trigger disclaimer (in English now)
    financial_triggers = ["advice", "invest", "portfolio", "recommendation", "buy", "sell", "asset", "shares", "stock", "balance"]
    
    content = ""
    if hasattr(last_message, "content"):
        content = last_message.content
    elif isinstance(last_message, dict):
        content = last_message.get("content", "")
        
    content_lower = content.lower()
    
    should_add_disclaimer = any(trigger in content_lower for trigger in financial_triggers)
    
    if content and should_add_disclaimer:
        if disclaimer not in content:
            logger.info("➕ Adding mandatory financial disclaimer to response.")
            if hasattr(last_message, "content"):
                last_message.content += disclaimer
            elif isinstance(last_message, dict):
                last_message["content"] += disclaimer
            
    logger.info("✅ OUTPUT GUARDRAIL END")
    return {"messages": [last_message]}
