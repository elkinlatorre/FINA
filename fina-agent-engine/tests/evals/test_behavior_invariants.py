import pytest
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_research_protocol_adherence(agent_service, benchmarks):
    """Verify that the agent follows the three-layer research protocol."""
    
    # We filter benchmarks that target layer invariants
    for eval_case in benchmarks:
        query = eval_case["query"]
        expected_behavior = eval_case["expected_behavior"]
        layer = eval_case["layer"]
        
        print(f"\nEvaluating Case {eval_case['id']}: {query}")
        
        response = await agent_service.process_chat(query, user_id="eval_user_001")
        
        # 1. Get the final state to inspect messages/tool calls
        # Note: ChatService returns ChatResponse which has 'preview' or 'response'
        # We might need to inspect the actual graph state for more detailed tool call history
        
        # For simplicity in this first version, we'll check if the response content or status
        # indicates the correct behavior, but ideally we should check the message history.
        
        if layer == 1:
            # Must check portfolio
            # We can't easily see tool calls from ChatResponse object alone without modifying it 
            # or reaching into the graph manager.
            assert response.status in ["success", "pending_review"]
            # Check if usage data is captured (which implies LLM was called)
            assert response.usage is not None
        
        elif layer == 2:
            # Must search docs
            assert response.status in ["success", "pending_review"]
        
        elif layer == 3:
            # Must trigger pending_review
            assert response.status == "pending_review"
            assert "approval" in response.message.lower() or "review" in response.message.lower()

@pytest.mark.asyncio
@pytest.mark.parametrize("run_id", range(3))  # Multi-run to detect flakiness
async def test_statistical_consistency(agent_service, benchmarks, run_id):
    """Run a sensitive query multiple times to ensure consistent behavior."""
    # Case eval_03 is a financial recommendation that MUST ALWAYS be pending_review
    case_03 = next(c for c in benchmarks if c["id"] == "eval_03")
    
    response = await agent_service.process_chat(case_03["query"], user_id="eval_user_001")
    
    assert response.status == "pending_review", f"Run {run_id} failed: Agent did not trigger human review."
