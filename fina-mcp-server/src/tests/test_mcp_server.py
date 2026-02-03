import pytest
from src.server import server
import mcp.types as types

@pytest.mark.asyncio
async def test_handle_list_tools():
    # Tools are registered in server._request_handlers
    handler = server._request_handlers[types.ListToolsRequest]
    tools = await handler(types.ListToolsRequest())
    assert len(tools.tools) == 1
    assert tools.tools[0].name == "fetch_portfolio"

@pytest.mark.asyncio
async def test_handle_call_tool_fetch_portfolio():
    handler = server._request_handlers[types.CallToolRequest]
    arguments = {"user_id": "user123"}
    request = types.CallToolRequest(
        params=types.CallToolRequestParams(name="fetch_portfolio", arguments=arguments)
    )
    result = await handler(request)
    
    assert len(result.content) == 1
    assert isinstance(result.content[0], types.TextContent)
    assert "AAPL" in result.content[0].text
    assert "NVDA" in result.content[0].text

@pytest.mark.asyncio
async def test_handle_call_tool_missing_arg():
    handler = server._request_handlers[types.CallToolRequest]
    request = types.CallToolRequest(
        params=types.CallToolRequestParams(name="fetch_portfolio", arguments={})
    )
    with pytest.raises(ValueError, match="Missing user_id argument"):
        await handler(request)

@pytest.mark.asyncio
async def test_handle_call_tool_not_found():
    handler = server._request_handlers[types.CallToolRequest]
    request = types.CallToolRequest(
        params=types.CallToolRequestParams(name="unknown_tool", arguments={})
    )
    with pytest.raises(ValueError, match="Tool not found: unknown_tool"):
        await handler(request)
