import pytest

@pytest.mark.asyncio
async def test_guardrail_blocks_non_financial_query(agent_service):
    """
    Verify that the guardrail blocks a query that is clearly out of scope.
    """
    query = "Dime cómo hacer una pizza pepperoni"
    response = await agent_service.process_chat(query, user_id="test_user_guardrail")
    
    # The response should indicate it was blocked or the content should contain the rejection message
    # Depending on how ChatService handles END state without an AI message (if any)
    # In our implementation, input_guardrail appends an AIMessage to state before returning block.
    
    assert "cannot process" in response.response.lower()
    assert "request" in response.response.lower()

@pytest.mark.asyncio
async def test_guardrail_allows_financial_query(agent_service):
    """
    Verify that the guardrail allows a financial query.
    """
    query = "¿Cuál es el riesgo de invertir en bonos del tesoro?"
    response = await agent_service.process_chat(query, user_id="test_user_guardrail")
    
    # It should pass and be processed by the agent (either success or pending_review)
    assert response.status in ["success", "pending_review"]
    # It should NOT have the rejection message
    assert "cannot process your request" not in response.response.lower()
