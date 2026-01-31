import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import app
from app.schemas.responses import ChatResponse

client = TestClient(app)

def test_health_endpoint():
    with patch("app.service.mcp_client.MCPClient.check_connection", return_value=True):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

def test_chat_endpoint_success():
    from app.core.dependencies import get_chat_service
    
    # Matching ChatResponse schema exactly
    mock_response = ChatResponse(
        status="success",
        user_id="u1",
        thread_id="t1",
        response="Test OK",
        usage=None
    )
    
    mock_service = AsyncMock()
    # Pydantic models in FastAPI response_model must be returnable as dict or model
    mock_service.process_chat.return_value = mock_response
    
    app.dependency_overrides[get_chat_service] = lambda: mock_service
    
    response = client.post("/api/v1/chat", json={"message": "hi", "user_id": "u1"})
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    assert response.json()["response"] == "Test OK"

def test_chat_endpoint_error():
    from app.core.dependencies import get_chat_service
    mock_service = AsyncMock()
    mock_service.process_chat.side_effect = Exception("Graph fail")
    
    app.dependency_overrides[get_chat_service] = lambda: mock_service
    
    response = client.post("/api/v1/chat", json={"message": "hi", "user_id": "u1"})
    app.dependency_overrides = {}
    
    assert response.status_code == 500
    assert "Agent Reasoning Error" in response.json()["detail"]
