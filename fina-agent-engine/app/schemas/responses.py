"""Response schemas for API endpoints.

These schemas provide type-safe response models for all endpoints,
improving API documentation and client code generation.
"""

from typing import Optional

from pydantic import BaseModel, Field

class UsageStats(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float

class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    
    status: str = Field(..., description="Status of the request: 'success' or 'pending_review'")
    user_id: str = Field(..., description="User who initiated the chat")
    thread_id: str = Field(..., description="Unique thread identifier")
    message: Optional[str] = Field(None, description="Status message for pending reviews")
    response: Optional[str] = Field(None, description="Agent's final response")
    preview: Optional[str] = Field(None, description="Preview of pending response")
    usage: Optional[UsageStats] = Field(None, description="Usage statistics")


class ApprovalResponse(BaseModel):
    """Response from approval endpoint."""
    
    status: str = Field(..., description="Status: 'approved', 'rejected', or 'already_processed'")
    thread_id: str = Field(..., description="Thread identifier")
    auditor: Optional[str] = Field(None, description="Name of the supervisor")
    decision_at: Optional[str] = Field(None, description="ISO timestamp of decision")
    message: Optional[str] = Field(None, description="Status message")
    response: Optional[str] = Field(None, description="Final agent response")
    new_agent_response: Optional[str] = Field(None, description="Alternative response after rejection")


class ThreadStatusResponse(BaseModel):
    """Response from thread status endpoint."""
    
    thread_id: str = Field(..., description="Thread identifier")
    status: str = Field(..., description="Status: 'completed' or 'pending_review'")
    final_decision: str = Field(..., description="Decision: 'approved', 'rejected', or 'pending'")
    history_count: int = Field(..., description="Number of messages in conversation")
    full_history: list[dict] = Field(..., description="Complete message history")
    usage: Optional[UsageStats] = Field(None, description="Usage statistics")


class HealthResponse(BaseModel):
    """Response from health check endpoint."""
    
    status: str = Field(..., description="Overall status")
    node_a: str = Field(..., description="Node A health status")
    node_b_connected: bool = Field(..., description="MCP server connectivity")
    api_keys_set: dict[str, bool] = Field(..., description="API key validation status")
    vector_db: str = Field(..., description="Vector database status")


class IngestionResponse(BaseModel):
    """Response from PDF ingestion endpoint."""
    
    status: str = Field(..., description="Ingestion status")
    filename: str = Field(..., description="Name of processed file")
    chunks_processed: int = Field(..., description="Number of chunks created")
    storage_mode: str = Field(..., description="Storage mode description")

class StreamEvent(BaseModel):
    type: str # 'token', 'tool', or 'final'
    content: Optional[str] = None
    tool: Optional[str] = None
    # If type is 'final', it would include usage, thread_id, etc.