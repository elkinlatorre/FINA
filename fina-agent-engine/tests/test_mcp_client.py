import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.service.mcp_client import MCPClient
from app.core.exceptions import MCPConnectionError
import respx
from httpx import Response

@pytest.mark.asyncio
@respx.mock
async def test_check_connection_success():
    client = MCPClient(host="mcp", port=8001)
    respx.get("http://mcp:8001/health").mock(return_value=Response(200))
    
    result = await client.check_connection()
    assert result is True

@pytest.mark.asyncio
@respx.mock
async def test_check_connection_fail():
    client = MCPClient(host="mcp", port=8001)
    respx.get("http://mcp:8001/health").mock(side_effect=Exception("Conn error"))
    
    result = await client.check_connection()
    assert result is False

@pytest.mark.asyncio
async def test_fetch_portfolio_success():
    client = MCPClient(host="mcp", port=8001)
    
    # Mocking the entire session flow
    mock_result = MagicMock()
    mock_result.content = [MagicMock(text='[{"asset": "BTC"}]')]
    
    mock_session = AsyncMock()
    mock_session.call_tool.return_value = mock_result
    
    # Nested async context managers are tricky to mock
    with patch("app.service.mcp_client.sse_client") as mock_sse:
        # Mocking async context manager __aenter__
        mock_sse.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())
        with patch("app.service.mcp_client.ClientSession") as mock_sess_cls:
            mock_sess_cls.return_value.__aenter__.return_value = mock_session
            
            result = await client.fetch_portfolio("u1")
            assert "BTC" in result
            mock_session.initialize.assert_called_once()
            mock_session.call_tool.assert_called_once_with("fetch_portfolio", arguments={"user_id": "u1"})

@pytest.mark.asyncio
async def test_fetch_portfolio_empty():
    client = MCPClient(host="mcp", port=8001)
    mock_result = MagicMock()
    mock_result.content = [] # Empty result
    mock_session = AsyncMock()
    mock_session.call_tool.return_value = mock_result
    with patch("app.service.mcp_client.sse_client") as mock_sse:
        mock_sse.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())
        with patch("app.service.mcp_client.ClientSession") as mock_sess_cls:
            mock_sess_cls.return_value.__aenter__.return_value = mock_session
            result = await client.fetch_portfolio("u1")
            assert result == "[]"

@pytest.mark.asyncio
async def test_fetch_portfolio_error():
    # Mocking the sse_client context manager is hard, but we can mock the internal flow
    # Since we can't easily mock sse_client without changing code, we test the exception handling
    client = MCPClient()
    with patch("app.service.mcp_client.sse_client", side_effect=Exception("SSE Fail")):
        with pytest.raises(MCPConnectionError):
            await client.fetch_portfolio("u1")
