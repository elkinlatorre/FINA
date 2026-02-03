from typing import Annotated, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

def reduce_usage(current: dict, new: dict) -> dict:
    """It accumulates the usage of tokens throughout the steps of the graph."""
    if not current: current = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "estimated_cost": 0.0}
    return {
        "prompt_tokens": current.get("prompt_tokens", 0) + new.get("prompt_tokens", 0),
        "completion_tokens": current.get("completion_tokens", 0) + new.get("completion_tokens", 0),
        "total_tokens": current.get("total_tokens", 0) + new.get("total_tokens", 0),
        "estimated_cost": current.get("estimated_cost", 0.0) + new.get("estimated_cost", 0.0)
    }

class AgentState(TypedDict):
    """Represents the state of our financial agent.
    
    It keeps track of the conversation history, decision status,
    and authorization metadata for audit purposes.
    
    Attributes:
        messages: Annotated sequence of messages in the conversation
        final_decision: Final approval decision (None, "approved", or "rejected")
        user_id: ID of the thread owner
        decision_by: ID of the supervisor who made the decision
        decision_at: ISO timestamp of when the decision was made
    """
    # add_messages is a helper that appends new messages to the history
    # instead of overwriting them.
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # New field to control the flow
    # Options: None (in process), "approved", "rejected"
    final_decision: Optional[str] = None
    user_id: str  # thread owner
    decision_by: Optional[str] = None  # Who approved/rejected
    decision_at: Optional[str] = None  # decision Timestamp
    usage: Annotated[dict, reduce_usage]
    safety_metadata: dict = {"is_safe": True, "reason": None, "category": None}