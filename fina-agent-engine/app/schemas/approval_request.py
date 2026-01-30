from typing import Optional

from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    """Request schema for approval/rejection decisions.
    
    Used for HITL (Human-In-The-Loop) governance workflow.
    """
    
    thread_id: str = Field(
        ...,
        min_length=1,
        description="Unique thread identifier"
    )
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User who created the request"
    )
    supervisor_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Supervisor ID (must be authorized)"
    )
    approve: bool = Field(
        ...,
        description="True for approval, False for rejection"
    )
    edited_response: Optional[str] = Field(
        None,
        max_length=10000,
        description="Optional edited response from supervisor"
    )
