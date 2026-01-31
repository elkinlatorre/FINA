import pytest
from unittest.mock import MagicMock
from app.graph.builder import FinancialGraphManager
from langchain_core.messages import AIMessage, HumanMessage

def test_should_continue_tools():
    manager = FinancialGraphManager()
    # Fix tool_calls structure to match what LangGraph/LangChain expects
    msg = AIMessage(content="")
    msg.tool_calls = [{"name": "get_portfolio", "args": {}, "id": "1"}]
    state = {"messages": [msg]}
    result = manager.should_continue(state)
    assert result == "tools"

def test_should_continue_end():
    manager = FinancialGraphManager()
    state = {
        "messages": [AIMessage(content="Hello world")]
    }
    result = manager.should_continue(state)
    assert result == "end"

def test_should_continue_review():
    manager = FinancialGraphManager()
    # Use explicit keyword from settings
    from app.core.settings import settings
    word = settings.RISK_FINANCIAL_KEYWORDS[0]
    state = {
        "messages": [AIMessage(content=f"I suggest you {word} some stocks")]
    }
    result = manager.should_continue(state)
    assert result == "review"

@pytest.mark.asyncio
async def test_gatekeeper_node():
    manager = FinancialGraphManager()
    state = {"messages": []}
    result = await manager.gatekeeper_node(state)
    assert result == state
