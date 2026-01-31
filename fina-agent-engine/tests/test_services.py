import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.service.chat_service import ChatService
from app.schemas.responses import ChatResponse, UsageStats

@pytest.mark.asyncio
async def test_process_chat_success():
    mock_graph = AsyncMock()
    # usage needs to be a dict that can be validated into UsageStats or None
    mock_graph.ainvoke.return_value = MagicMock(
        values={
            "messages": [MagicMock(content="Mocked answer")],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20, "estimated_cost": 0.1}
        }
    )
    # Correcting the return structure for ainvoke to match state dict
    mock_graph.ainvoke.return_value = {
        "messages": [MagicMock(content="Mocked answer")],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20, "estimated_cost": 0.1}
    }
    
    mock_snapshot = MagicMock()
    mock_snapshot.next = []
    mock_graph.aget_state.return_value = mock_snapshot
    
    mock_manager = MagicMock()
    mock_manager.graph = mock_graph
    
    service = ChatService(mock_manager)
    
    response = await service.process_chat("Hello", "user-1")
    
    assert isinstance(response, ChatResponse)
    assert response.status == "success"
    assert response.response == "Mocked answer"

@pytest.mark.asyncio
async def test_process_chat_pending_review():
    mock_graph = AsyncMock()
    mock_graph.ainvoke.return_value = {
        "messages": [MagicMock(content="Pending review")],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20, "estimated_cost": 0.1}
    }
    
    mock_snapshot = MagicMock()
    mock_snapshot.next = ["human_review_gate"]
    mock_graph.aget_state.return_value = mock_snapshot
    
    mock_manager = MagicMock()
    mock_manager.graph = mock_graph
    
    service = ChatService(mock_manager)
    
    response = await service.process_chat("Invest in BTC", "user-1")
    assert response.status == "pending_review"

@pytest.mark.asyncio
async def test_process_chat_stream_success():
    mock_graph = AsyncMock()
    
    async def mock_astream_events(*args, **kwargs):
        yield {
            "event": "on_chat_model_end",
            "metadata": {"langgraph_node": "agent"},
            "data": {"output": MagicMock(content="Streaming answer")}
        }
        yield {
            "event": "on_tool_start",
            "name": "get_portfolio"
        }

    mock_graph.astream_events = mock_astream_events
    
    mock_snapshot = MagicMock()
    mock_snapshot.next = []
    mock_snapshot.values = {"usage": {"tokens": 10}}
    mock_graph.aget_state.return_value = mock_snapshot
    
    mock_manager = MagicMock()
    mock_manager.graph = mock_graph
    
    service = ChatService(mock_manager)
    
    events = []
    async for event in service.process_chat_stream("hi", "u1"):
        events.append(event)
    
    assert any("Streaming answer" in e for e in events)
    assert any("get_portfolio" in e for e in events)
    assert any('"type": "final"' in e for e in events)
