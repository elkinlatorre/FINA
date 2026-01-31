import pytest
from app.core.exceptions import (
    FinaAgentException,
    ConfigurationError,
    MCPConnectionError,
    IngestionError,
    AuthorizationError,
    ValidationError,
    ThreadNotFoundError,
    ConflictOfInterestError
)
from app.core.settings import Settings

def test_fina_agent_exception():
    exc = FinaAgentException("Test error", status_code=418)
    assert exc.message == "Test error"
    assert exc.status_code == 418
    assert str(exc) == "Test error"

def test_specific_exceptions():
    assert ConfigurationError("config error").status_code == 500
    assert MCPConnectionError("mcp error").status_code == 503
    assert IngestionError("ingest error").status_code == 422
    assert AuthorizationError("auth error").status_code == 403
    assert ValidationError("valid error").status_code == 400
    assert ThreadNotFoundError("123").status_code == 404
    assert ConflictOfInterestError().status_code == 403

def test_settings_allowed_origins():
    settings = Settings()
    settings.ALLOWED_ORIGINS = "*"
    assert settings.get_allowed_origins_list() == ["*"]
    
    settings.ALLOWED_ORIGINS = "http://localhost:3000, https://fina.app"
    assert settings.get_allowed_origins_list() == ["http://localhost:3000", "https://fina.app"]
    
    settings.ALLOWED_ORIGINS = "  "
    assert settings.get_allowed_origins_list() == []
