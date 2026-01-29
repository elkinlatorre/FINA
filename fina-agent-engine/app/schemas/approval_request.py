from typing import Optional

from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    thread_id: str  # Identify the agentic flow
    user_id: str  # The owner of the portfolio
    supervisor_id: str  # The person authorizing the trade/report
    approve: bool
    edited_response: Optional[str] = None