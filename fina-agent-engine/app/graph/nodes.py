from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode

from app.core.config_loader import prompt_loader
from app.core.logger import get_logger
from app.core.settings import settings
from app.graph.state import AgentState
from app.service.agent_tools import FINA_TOOLS

logger = get_logger("GRAPH_NODES")

def get_llm(model_name: str):
    """Factory to create LLM instances with tools bound."""
    return ChatGroq(
        model=model_name,
        temperature=settings.LLM_TEMPERATURE,
        groq_api_key=settings.GROQ_API_KEY,
        streaming=True
    ).bind_tools(FINA_TOOLS)

async def call_model(state: AgentState) -> dict:
    """Agent Node: Injects dynamic system prompt and handles model fallbacks."""
    
    # Priority list: Primary model followed by fallbacks
    models_to_try = [settings.LLM_MODEL] + settings.LLM_FALLBACK_MODELS
    
    system_content = prompt_loader.get_analyst_prompt()
    system_message = SystemMessage(content=system_content)
    messages = [system_message] + state["messages"]

    last_error = None
    
    for model_name in models_to_try:
        try:
            logger.info(f"Agent is thinking using model: {model_name}")
            current_llm = get_llm(model_name)
            response = await current_llm.ainvoke(messages)
            
            # If successful, break the loop
            break
        except Exception as e:
            error_str = str(e).lower()
            # Detect Rate Limit (429)
            is_rate_limit = "429" in error_str or "rate_limit_exceeded" in error_str
            # Detect Decommissioned (400) or Unsupported
            is_invalid_model = "400" in error_str or "model_decommissioned" in error_str or "not supported" in error_str
            
            if is_rate_limit or is_invalid_model:
                reason = "hit rate limit" if is_rate_limit else "is decommissioned/unsupported"
                logger.warning(f"⚠️ Model {model_name} {reason}. Trying fallback...")
                last_error = e
                continue
            else:
                # Other errors should propagate immediately
                logger.error(f"❌ Unexpected error with model {model_name}: {error_str}")
                raise e
    else:
        # If the loop finishes without 'break', all models failed
        logger.error("🛑 All LLM models exhausted or failed.")
        raise last_error if last_error else Exception("LLM invocation failed")

    # --- ROBUST TOKEN EXTRACTION ---
    # 1. Try standardized 'usage_metadata' (preferred in latest LangChain versions)
    usage = getattr(response, "usage_metadata", {})
    # 2. Fallback to response_metadata dicts
    if not usage:
        usage = response.response_metadata.get("token_usage") or response.response_metadata.get("usage") or {}
    prompt_tokens = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
    completion_tokens = usage.get("output_tokens") or usage.get("completion_tokens") or 0
    # 3. Emergency Heuristic Fallback (Avoids 0.0 costs if API omits metadata in stream)
    if prompt_tokens == 0 and completion_tokens == 0:
        logger.warning("⚠️ API returned zero tokens in stream mode. Applying heuristic estimation.")
        # Rough estimation: ~4 chars per token for English financial text
        prompt_tokens = sum(len(getattr(m, 'content', '')) for m in messages) // 4
        completion_tokens = len(response.content) // 4
    total_tokens = usage.get("total_tokens") or (prompt_tokens + completion_tokens)

    # Cost calculation based on settings
    cost = (
            (prompt_tokens * settings.PRICE_1K_PROMPT) / 1000 +
            (completion_tokens * settings.PRICE_1K_COMPLETION) / 1000
    )

    logger.info(f"Final Usage Capture -> P: {prompt_tokens}, C: {completion_tokens}, Cost: ${cost:.6f}")
    
    if completion_tokens > 0 and not response.content:
        # 1. Manual Tool Call Rescue (for Llama models on Groq/Fireworks)
        raw_tools = response.additional_kwargs.get("tool_calls", [])
        if not getattr(response, 'tool_calls', None) and raw_tools:
            logger.info(f"🩹 Rescuing {len(raw_tools)} tool calls from additional_kwargs")
            parsed_tools = []
            for t in raw_tools:
                fn = t.get("function", {})
                args_str = fn.get("arguments", "{}")
                try:
                    import json
                    args = json.loads(args_str) if args_str and args_str != "null" else {}
                except:
                    args = {}
                parsed_tools.append({
                    "name": fn.get("name"),
                    "args": args,
                    "id": t.get("id"),
                    "type": "tool_call"
                })
            response.tool_calls = parsed_tools

        # --- REFINED WARNING LOGIC ---
        # If there are tool calls, a lack of content is expected (Llama technical turn)
        if response.tool_calls:
            logger.info(f"⚙️ Model turn completed with {len(response.tool_calls)} tool calls (technical turn).")
        else:
            logger.warning(f"⚠️ Model generated {completion_tokens} tokens but content is empty!")

        # 2. Refusal Rescue
        refusal = response.additional_kwargs.get("refusal")
        if refusal:
            logger.info(f"🛡️ Model refusal detected: {refusal}")
            response.content = refusal
            
        # 3. Metadata Content Rescue
        elif not response.tool_calls:
            msg_meta = response.response_metadata.get("message", {})
            if isinstance(msg_meta, dict) and msg_meta.get("content"):
                logger.info(f"🩹 Rescued content from metadata: {msg_meta.get('content')[:50]}...")
                response.content = msg_meta.get("content")

    return {
        "messages": [response],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": cost
        }
    }

# Setup the Tools Node
# This is a prebuilt LangGraph node that automatically executes
# the tools requested by the model with error handling enabled.
tool_node = ToolNode(FINA_TOOLS, handle_tool_errors=True)