from pydantic import BaseModel

class ApprovalRequest(BaseModel):
    thread_id: str
    approve: bool
    edited_response: str = None