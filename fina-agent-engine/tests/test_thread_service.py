import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.service.thread_service import ThreadService
from app.core.exceptions import ThreadNotFoundError

@pytest.mark.asyncio
async def test_get_thread_status_not_found():
    mock_manager = MagicMock()
    mock_graph = AsyncMock()
    # Empty values means thread not found
    mock_graph.aget_state.return_value = MagicMock(values={})
    mock_manager.graph = mock_graph
    
    service = ThreadService(mock_manager)
    with pytest.raises(ThreadNotFoundError):
        await service.get_thread_status("t1")

@pytest.mark.asyncio
async def test_get_thread_status_success():
    mock_manager = MagicMock()
    mock_graph = AsyncMock()
    mock_snapshot = MagicMock()
    mock_snapshot.values = {
        "final_decision": "approved",
        "messages": [MagicMock(content="hi"), MagicMock(content="hey")],
        "usage": None
    }
    mock_snapshot.next = []
    mock_graph.aget_state.return_value = mock_snapshot
    mock_manager.graph = mock_graph
    
    service = ThreadService(mock_manager)
    response = await service.get_thread_status("t1")
    assert response.thread_id == "t1"
    assert response.status == "completed"
    assert response.final_decision == "approved"
    assert response.history_count == 2
