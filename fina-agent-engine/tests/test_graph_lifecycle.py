import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.graph.builder import FinancialGraphManager

@pytest.mark.asyncio
async def test_graph_manager_lifecycle():
    manager = FinancialGraphManager()
    
    # Mock AsyncSqliteSaver
    mock_saver_cls = MagicMock()
    mock_checkpointer = AsyncMock()
    mock_saver_cls.from_conn_string.return_value = mock_checkpointer
    
    with patch("app.graph.builder.AsyncSqliteSaver", mock_saver_cls):
        # Trigger initialization
        graph = await manager.initialize()
        assert graph is not None
        mock_saver_cls.from_conn_string.assert_called_once()
        
        # Trigger close
        await manager.close()
        # Verify __aexit__ or similar if possible, or just that it doesn't crash
