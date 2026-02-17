from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.service.mcp_client import MCPClient
from app.service.ingestion_service import IngestionService
from app.schemas.agent_schemas import SearchSchema

mcp_client = MCPClient()
ingest_service = IngestionService()

@tool("get_user_portfolio")
async def get_user_portfolio(state: Annotated[dict, InjectedState]):
    """
    Retrieves the current user's financial portfolio including stocks,
    shares, and average purchase prices from the private vault via MCP.
    """
    user_id = state.get("user_id", "user123")
    return await mcp_client.fetch_portfolio(user_id)

@tool("search_financial_docs")
async def search_financial_docs(query: str, state: Annotated[dict, InjectedState]):
    """
    Searches within the uploaded financial PDF documents for specific
    advice, risk analysis, or market trends using the vector database.
    """
    user_id = state.get("user_id", "user123")
    return await ingest_service.search_in_vector_db(query, user_id)

FINA_TOOLS = [get_user_portfolio, search_financial_docs]