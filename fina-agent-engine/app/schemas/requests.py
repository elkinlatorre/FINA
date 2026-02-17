from typing import Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User's query or message"
    )
    user_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="User identifier (auto-filled from JWT if not provided)"
    )