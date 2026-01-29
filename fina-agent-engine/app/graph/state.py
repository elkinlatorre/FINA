from typing import Annotated, Optional, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(dict):
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