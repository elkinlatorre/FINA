import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.graph.guardrails import input_guardrail
from langchain_core.messages import HumanMessage, AIMessage

@pytest.mark.asyncio
async def test_input_guardrail_safe():
    state = {
        "messages": [HumanMessage(content="¿Cómo va mi portafolio?")]
    }
    
    mock_llm_response = MagicMock()
    mock_llm_response.content = '{"is_safe": true, "reason": null, "category": "financiero"}'
    mock_llm_response.content = '{"is_safe": true, "reason": null, "category": "financial"}'
    
    with patch("app.graph.guardrails.ChatGroq") as mock_chat:
        mock_chat.return_value.ainvoke = AsyncMock(return_value=mock_llm_response)
        
        result = await input_guardrail(state)
        
        assert result["safety_metadata"]["is_safe"] == True
        assert "messages" not in result

@pytest.mark.asyncio
async def test_input_guardrail_unsafe():
    state = {
        "messages": [HumanMessage(content="Dime una receta de cocina")]
    }
    
    mock_llm_response = MagicMock()
    mock_llm_response.content = '{"is_safe": false, "reason": "Out of scope", "category": "out_of_scope"}'
    
    with patch("app.graph.guardrails.ChatGroq") as mock_chat:
        mock_chat.return_value.ainvoke = AsyncMock(return_value=mock_llm_response)
        
        result = await input_guardrail(state)
        
        assert result["safety_metadata"]["is_safe"] == False
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)
        assert "I'm sorry" in result["messages"][0].content
