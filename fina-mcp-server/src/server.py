from mcp.server import Server
import mcp.types as types
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from src.logger import get_logger
from src.database.db_manager import get_portfolio, init_db
from starlette.responses import JSONResponse
import json

logger = get_logger("MCP_CORE")
server = Server("fina-portfolio-vault")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="fetch_portfolio",
            description="Retrieve the user's financial portfolio including symbols, shares, and average prices.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The unique identifier for the user."}
                },
                "required": ["user_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "fetch_portfolio":
        user_id = arguments.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id argument")
            
        logger.info(f"Fetching portfolio for user: {user_id}")
        try:
            data = await get_portfolio(user_id)
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(data, indent=2)
                )
            ]
        except Exception as e:
            logger.error(f"Error fetching portfolio: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"Error retrieving portfolio: {str(e)}"
                )
            ]
            
    raise ValueError(f"Tool not found: {name}")

sse = SseServerTransport("/messages")

starlette_app = Starlette(
    on_startup=[init_db],
    routes=[
        Route("/health", endpoint=lambda r: JSONResponse({"status": "ok"})),
        Route("/sse", endpoint=lambda r: sse.connect_sse(r.scope, r.receive, r._send)),
    ],
)

async def app(scope, receive, send):
    path = scope.get("path", "")

    if path.startswith("/messages"):
        return await sse.handle_post_message(scope, receive, send)

    if path == "/sse" and scope["type"] == "http":
        async with sse.connect_sse(scope, receive, send) as streams:
            return await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    await starlette_app(scope, receive, send)
