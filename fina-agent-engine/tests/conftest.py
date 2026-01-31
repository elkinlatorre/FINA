import pytest
from unittest.mock import MagicMock, patch
import os

# Prevent real API calls or DB connections during tests
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test_key")
    monkeypatch.setenv("HUGGINGFACEHUB_API_TOKEN", "test_token")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

@pytest.fixture
def mock_settings():
    with patch("app.core.settings.settings") as mock:
        mock.APP_HOST = "0.0.0.0"
        mock.APP_PORT = 8000
        mock.ALLOWED_ORIGINS = "*"
        mock.get_allowed_origins_list.return_value = ["*"]
        yield mock

@pytest.fixture
def mock_graph_manager():
    with patch("app.graph.builder.graph_manager") as mock:
        mock.initialize = MagicMock()
        mock.close = MagicMock()
        mock.graph = MagicMock()
        yield mock
