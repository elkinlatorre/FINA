from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode

from app.core.config_loader import prompt_loader
from app.core.logger import get_logger
from app.core.settings import settings
from app.graph.state import AgentState
from app.service.agent_tools import FINA_TOOLS

logger = get_logger("GRAPH_NODES")

# Setup the LLM with Tools
# We bind the tools to the model so it knows what it can do.
llm = ChatGroq(
    model=settings.LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE,  # Financial analysis requires consistency
    groq_api_key=settings.GROQ_API_KEY,
    streaming=True
).bind_tools(FINA_TOOLS)


async def call_model(state: AgentState) -> dict:
    """Agent Node: Injects dynamic system prompt before LLM decision."""
    logger.info("Agent is thinking with dynamic prompt...")

    system_content = prompt_loader.get_analyst_prompt()
    system_message = SystemMessage(content=system_content)
    messages = [system_message] + state["messages"]

    # In streaming mode, 'ainvoke' should reconstruct the full message and metadata
    response = await llm.ainvoke(messages)

    # --- US4.1: ROBUST TOKEN EXTRACTION ---
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