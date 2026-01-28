import os
from langchain_groq import ChatGroq
from langgraph.prebuilt import ToolNode
from app.service.agent_tools import FINA_TOOLS
from app.core.logger import get_logger

logger = get_logger("GRAPH_NODES")

# 1. Setup the LLM with Tools
# We bind the tools to the model so it knows what it can do.
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0, # Financial analysis requires consistency (0 = no creativity)
    groq_api_key=os.getenv("GROQ_API_KEY")
).bind_tools(FINA_TOOLS)

async def call_model(state):
    """
    The Agent Node: It looks at the messages and decides
    if it needs to call a tool or reply to the user.
    """
    logger.info("Agent is thinking...")
    messages = state["messages"]
    response = await llm.ainvoke(messages)
    return {"messages": [response]}

# 2. Setup the Tools Node
# This is a prebuilt LangGraph node that automatically executes
# the tools requested by the model.
tool_node = ToolNode(FINA_TOOLS)