import pytest
from app.core.settings import Settings

def test_settings_allowed_origins_list():
    s = Settings()
    # Test default
    assert "*" in s.get_allowed_origins_list()
    
    # Manually set the attribute to test logic
    s.ALLOWED_ORIGINS = "http://localhost,http://app"
    assert "http://localhost" in s.get_allowed_origins_list()
    assert "http://app" in s.get_allowed_origins_list()

def test_settings_sensitive_keywords():
    s = Settings()
    assert "risk" in s.SENSITIVE_FINANCIAL_KEYWORDS
    assert "portfolio" in s.SENSITIVE_FINANCIAL_KEYWORDS
