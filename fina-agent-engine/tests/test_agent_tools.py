import pytest
from app.service.agent_tools import FINA_TOOLS

def test_agent_tools_list():
    assert len(FINA_TOOLS) >= 2
    tool_names = [t.name for t in FINA_TOOLS]
    assert "get_user_portfolio" in tool_names
    assert "search_financial_docs" in tool_names
