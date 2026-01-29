from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Represents the state of our financial agent.
    It keeps track of the conversation history.
    """
    # add_messages is a helper that appends new messages to the history
    # instead of overwriting them.
    messages: Annotated[Sequence[BaseMessage], add_messages]
    # New field to control the flow
    # Options: None (in process), "approved", "rejected"
    final_decision: Optional[str]