from mcp.server import Server
import mcp.types as types
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from src.logger import get_logger
from src.database.db_manager import get_portfolio, init_db
from starlette.responses import JSONResponse

logger = get_logger("MCP_CORE")
server = Server("fina-portfolio-vault")


# --- Lógica de herramientas (Igual) ---
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="fetch_portfolio",
            description="Retrieve the user's financial portfolio.",
            inputSchema={
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "fetch_portfolio":
        user_id = arguments.get("user_id")
        logger.info(f"Portfolio invoke received for: {user_id}")
        data = await get_portfolio(user_id)
        return [types.TextContent(type="text", text=str(data))]
    raise ValueError(f"Tool not found: {name}")


# --- Transporte ---
# Usamos una ruta simple sin trailing slash para el transporte
sse = SseServerTransport("/messages")

# --- App de Starlette (SOLO para Health y la conexión inicial SSE) ---
starlette_app = Starlette(
    on_startup=[init_db],
    routes=[
        Route("/health", endpoint=lambda r: JSONResponse({"status": "ok"})),
        Route("/sse", endpoint=lambda r: sse.connect_sse(r.scope, r.receive, r._send)),
    ],
)


# --- MANEJADOR ASGI MAESTRO (El corazón de la solución) ---
async def app(scope, receive, send):
    path = scope.get("path", "")

    # 1. Si es la ruta de mensajes de MCP, BYPASS TOTAL de Starlette.
    if path.startswith("/messages"):
        # Llamamos directamente al SDK.
        # Al terminar el await, la función sale.
        # Uvicorn ve una app ASGI que terminó correctamente.
        return await sse.handle_post_message(scope, receive, send)

    # 2. Si es la conexión SSE, necesitamos correr el servidor MCP
    if path == "/sse" and scope["type"] == "http":
        async with sse.connect_sse(scope, receive, send) as streams:
            return await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    # 3. Todo lo demás (health, 404s) lo maneja Starlette
    await starlette_app(scope, receive, send)