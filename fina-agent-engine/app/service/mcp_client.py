from mcp import ClientSession
from mcp.client.sse import sse_client

from app.core.exceptions import MCPConnectionError
from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger("MCP_CLIENT")


class MCPClient:
    """Client for communicating with MCP (Model Context Protocol) server.
    
    Handles connection to remote MCP server and provides methods to
    fetch portfolio data and check connection health.
    """
    
    def __init__(self, host: str = None, port: int = None):
        """Initialize MCP Client.
        
        Args:
            host: MCP server hostname (defaults to settings.MCP_HOST)
            port: MCP server port (defaults to settings.MCP_PORT)
        """
        # Use provided values or fall back to settings
        self.host = host or settings.MCP_HOST
        self.port = port or settings.MCP_PORT
        # The entry endpoint for the protocol is /sse
        self.sse_url = f"http://{self.host}:{self.port}/sse"

    async def check_connection(self) -> bool:
        """Verify if MCP server responds at network/health level.
        
        Returns:
            True if server is reachable, False otherwise
        """
        import httpx
        try:
            # Use the base host for health check
            health_url = self.sse_url.replace("/sse", "/health")
            async with httpx.AsyncClient() as client:
                response = await client.get(health_url, timeout=30.0)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"MCP health check failed: {str(e)}")
            return False

    async def fetch_portfolio(self, user_id: str = "user123") -> str:
        """Establishes a real MCP session over SSE and calls the remote tool.
        
        Args:
            user_id: User identifier to fetch portfolio for
            
        Returns:
            Portfolio data as JSON string
            
        Raises:
            MCPConnectionError: If unable to connect or call fails
        """
        logger.info(f"Connecting to MCP Server via SSE: {self.sse_url}")
        try:
            async with sse_client(self.sse_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # Protocol initialization (Handshake)
                    await session.initialize()

                    # Call the tool defined in MCP Server
                    result = await session.call_tool(
                        "fetch_portfolio",
                        arguments={"user_id": user_id}
                    )

                    if result.content and len(result.content) > 0:
                        return result.content[0].text
                    return "[]"  # Return empty list as text if no content
        except Exception as e:
            error_msg = f"MCP Communication failed: {str(e)}"
            logger.error(error_msg)
            raise MCPConnectionError(error_msg)