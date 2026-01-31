import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# We need to mock the 'llm' instance and its configuration BEFORE it's used in the module
# A robust way is to patch it in the module scope during the test.

@pytest.mark.asyncio
async def test_call_model_success():
    from langchain_core.messages import AIMessage, HumanMessage
    state = {"messages": [HumanMessage(content="test")], "usage": {}}
    
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "Response"
    mock_response.usage_metadata = {"input_tokens": 10, "output_tokens": 5}
    mock_response.response_metadata = {}
    
    # Importing here so it uses the patched version if possible, 
    # but we will patch the instance directly in the module.
    import app.graph.nodes as nodes
    
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = mock_response
    
    with patch.object(nodes, "llm", mock_llm):
        with patch("app.core.config_loader.prompt_loader.get_analyst_prompt", return_value="System"):
            result = await nodes.call_model(state)
            
            assert "messages" in result
            assert result["usage"]["prompt_tokens"] == 10
            assert result["usage"]["completion_tokens"] == 5

@pytest.mark.asyncio
async def test_call_model_heuristic():
    from langchain_core.messages import AIMessage, HumanMessage
    state = {"messages": [HumanMessage(content="test")], "usage": {}}
    
    mock_response = MagicMock(spec=AIMessage)
    mock_response.content = "Short"
    mock_response.usage_metadata = {}
    mock_response.response_metadata = {}
    
    import app.graph.nodes as nodes
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = mock_response
    
    with patch.object(nodes, "llm", mock_llm):
        with patch("app.core.config_loader.prompt_loader.get_analyst_prompt", return_value="System"):
            result = await nodes.call_model(state)
            
            assert result["usage"]["prompt_tokens"] > 0
            assert result["usage"]["completion_tokens"] > 0
