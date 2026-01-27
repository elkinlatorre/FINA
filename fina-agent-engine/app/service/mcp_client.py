import httpx
from app.core.logger import get_logger

logger = get_logger("MCP_CLIENT")

class MCPClient:
    def __init__(self, host: str = "mcp-data-server", port: int = 8001):
        self.base_url = f"http://{host}:{port}"

    async def check_connection(self):
        """Verifica si el Nodo B responde."""
        try:
            async with httpx.AsyncClient() as client:
                # Intentamos contactar el endpoint SSE del Nodo B
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error conectando al Nodo B: {e}")
            return False