import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.service.agent_tools import get_user_portfolio, search_financial_docs

@pytest.mark.asyncio
async def test_get_user_portfolio_call():
    with patch("app.service.agent_tools.mcp_client.fetch_portfolio", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = "portfolio data"
        result = await get_user_portfolio.ainvoke({"user_id": "u1"})
        assert result == "portfolio data"

@pytest.mark.asyncio
async def test_search_financial_docs_call():
    with patch("app.service.agent_tools.ingest_service.search_in_vector_db", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = "docs data"
        result = await search_financial_docs.ainvoke({"query": "risk"})
        assert result == "docs data"
