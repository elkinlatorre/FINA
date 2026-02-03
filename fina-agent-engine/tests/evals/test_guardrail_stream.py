import pytest
import json

@pytest.mark.asyncio
async def test_guardrail_stream_blocks_correctly(agent_service):
    """
    Verify that the streaming endpoint correctly returns a 'blocked' status
    and the blocking message when a query is out of scope.
    """
    query = "How to make a pepperoni pizza"
    user_id = "test_stream_user"
    
    events = []
    async for event_str in agent_service.process_chat_stream(query, user_id):
        # Parse SSE data: "data: {...}\n\n"
        if event_str.startswith("data: "):
            data = json.loads(event_str[6:].strip())
            events.append(data)
    
    # Check that we received an answer event (the blocking message)
    answer_events = [e for e in events if e["type"] == "answer"]
    assert len(answer_events) > 0
    assert "cannot process" in answer_events[0]["content"].lower()
    
    # Check the final event
    final_events = [e for e in events if e["type"] == "final"]
    assert len(final_events) == 1
    assert final_events[0]["status"] == "blocked"
    assert "usage" in final_events[0]

@pytest.mark.asyncio
async def test_guardrail_output_appends_disclaimer(agent_service):
    """
    Verify that the output guardrail appends a disclaimer to financial responses.
    """
    query = "Should I buy Tesla shares?"
    user_id = "test_disclaimer_user"
    
    events = []
    async for event_str in agent_service.process_chat_stream(query, user_id):
        if event_str.startswith("data: "):
            data = json.loads(event_str[6:].strip())
            events.append(data)
    
    # Collect all 'answer' events
    answer_events = [e for e in events if e["type"] == "answer"]
    assert len(answer_events) > 0
    
    for i, e in enumerate(answer_events):
        print(f"Debug Event {i}: {e['content']}")
    
    # Combine all content to check for the disclaimer
    full_text = "".join([e["content"] for e in answer_events])
    print(f"Full Text Length: {len(full_text)}")
    
    # Check the actual content
    assert "Note: This information is for educational purposes" in full_text
