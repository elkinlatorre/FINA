from app.schemas.requests import ChatRequest
from app.schemas.approval_request import ApprovalRequest
from app.schemas.responses import ChatResponse, HealthResponse, IngestionResponse, UsageStats
import pytest
from pydantic import ValidationError

def test_chat_request_validation():
    req = ChatRequest(message="Hello", user_id="user123")
    assert req.message == "Hello"
    assert req.user_id == "user123"

def test_approval_request_validation():
    # Fix: use 'approve: bool' instead of 'decision: str'
    req = ApprovalRequest(
        thread_id="thread1",
        user_id="user1",
        approve=True,
        supervisor_id="SUP-1"
    )
    assert req.approve is True

def test_responses_defaults():
    resp = HealthResponse(
        status="online",
        node_a="healthy",
        node_b_connected=True,
        api_keys_set={"key": True},
        vector_db="exists"
    )
    assert resp.status == "online"

def test_usage_stats():
    usage = UsageStats(prompt_tokens=10, completion_tokens=10, total_tokens=20, estimated_cost=0.01)
    assert usage.total_tokens == 20
