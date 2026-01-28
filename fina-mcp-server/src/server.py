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

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="fetch_portfolio",
            description="Retrieve the user's financial portfolio from the private database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Unique ID of the analyst/user"}
                },
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

async def handle_messages(request):
    """
    Wrapper para manejar las peticiones POST del cliente MCP.
    Pasa los componentes ASGI necesarios al transporte SSE.
    """
    await sse.handle_post_message(request.scope, request.receive, request._send)

sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

async def health(request):
    return JSONResponse({"status": "ok"})

async def startup():
    await init_db()
    logger.info("Database initialized and MCP server ready.")

app = Starlette(
    debug=True,
    on_startup=[startup],
    routes=[
        Route("/health", endpoint=health),
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ],
)