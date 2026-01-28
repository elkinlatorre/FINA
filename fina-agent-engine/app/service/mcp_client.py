from mcp import ClientSession
from mcp.client.sse import sse_client
from app.core.logger import get_logger

logger = get_logger("MCP_CLIENT")


class MCPClient:
    def __init__(self, host: str = "mcp-data-server", port: int = 8001):
        # El endpoint de entrada para el protocolo es /sse
        self.sse_url = f"http://{host}:{port}/sse"

    async def check_connection(self):
        """Verifica si el Nodo B responde al menos al nivel de red/health."""
        import httpx
        try:
            # Usamos la base del host para el health check
            health_url = self.sse_url.replace("/sse", "/health")
            async with httpx.AsyncClient() as client:
                response = await client.get(health_url, timeout=30.0)
                return response.status_code == 200
        except Exception:
            return False

    async def fetch_portfolio(self, user_id: str = "user123"):
        """
        Establece una sesión MCP real sobre SSE y llama a la herramienta remota.
        """
        logger.info(f"Connecting to MCP Server via SSE: {self.sse_url}")
        try:
            async with sse_client(self.sse_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # Inicialización del protocolo (Handshake)
                    await session.initialize()

                    # Llamada a la herramienta definida en el Nodo B
                    result = await session.call_tool(
                        "fetch_portfolio",
                        arguments={"user_id": user_id}
                    )

                    if result.content and len(result.content) > 0:
                        return result.content[0].text
                    return "[]"  # Devuelve lista vacía en texto si no hay contenido
        except Exception as e:
            logger.error(f"Error in MCP Communication: {str(e)}")
            return f"Error: {str(e)}"