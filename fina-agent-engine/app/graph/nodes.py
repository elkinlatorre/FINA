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
    groq_api_key=settings.GROQ_API_KEY
).bind_tools(FINA_TOOLS)


async def call_model(state: AgentState) -> dict:
    """Agent Node: Injects dynamic system prompt before LLM decision.
    
    Args:
        state: Current agent state with message history
        
    Returns:
        Dictionary with new message to add to state
    """
    logger.info("Agent is thinking with dynamic prompt...")

    # Load prompt from YAML configuration
    system_content = prompt_loader.get_analyst_prompt()
    system_message = SystemMessage(content=system_content)

    # Build message list: System Prompt + Conversation History
    messages = [system_message] + state["messages"]

    response = await llm.ainvoke(messages)

    # Return message to update graph state
    return {"messages": [response]}


# Setup the Tools Node
# This is a prebuilt LangGraph node that automatically executes
# the tools requested by the model with error handling enabled.
tool_node = ToolNode(FINA_TOOLS, handle_tool_errors=True)