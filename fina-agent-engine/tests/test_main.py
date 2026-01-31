import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock, AsyncMock

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to FINA Agent Engine" in response.json()["message"]

def test_fina_exception_handler():
    from app.core.exceptions import ValidationError
    from main import fina_exception_handler
    
    request = MagicMock()
    exc = ValidationError("Custom validation error")
    
    import asyncio
    response = asyncio.run(fina_exception_handler(request, exc))
    
    assert response.status_code == 400
    import json
    data = json.loads(response.body)
    assert data["error"]["type"] == "ValidationError"
    assert "Custom validation error" in data["error"]["message"]

@pytest.mark.asyncio
async def test_app_lifespan():
    from main import lifespan
    mock_app = MagicMock()
    
    with patch("app.graph.builder.graph_manager.initialize", new_callable=AsyncMock) as mock_init:
        with patch("app.graph.builder.graph_manager.close", new_callable=AsyncMock) as mock_close:
            async with lifespan(mock_app):
                mock_init.assert_called_once()
            mock_close.assert_called_once()
