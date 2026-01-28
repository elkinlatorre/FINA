from langchain_core.tools import tool
from app.service.mcp_client import MCPClient
from app.service.ingestion_service import IngestionService
from app.schemas.agent_schemas import PortfolioSchema, SearchSchema

# Instancias de servicios
mcp_client = MCPClient()
ingest_service = IngestionService()

@tool("get_user_portfolio", args_schema=PortfolioSchema)
async def get_user_portfolio(user_id: str):
    """
    Retrieves the user's current financial portfolio including stocks,
    shares, and average purchase prices from the private vault via MCP.
    """
    return await mcp_client.fetch_portfolio(user_id)

@tool("search_financial_docs", args_schema=SearchSchema)
async def search_financial_docs(query: str):
    """
    Searches within the uploaded financial PDF documents for specific
    advice, risk analysis, or market trends using the vector database.
    """
    return await ingest_service.search_in_vector_db(query)

# Exportamos la lista para que el Grafo (Fase 2) las vea fácilmente
FINA_TOOLS = [get_user_portfolio, search_financial_docs]