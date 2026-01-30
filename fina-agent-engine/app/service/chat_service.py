"""ChatService - Business logic for chat operations.

Handles chat request processing, thread management, and graph orchestration.
Separates business logic from the API layer for better testability and reusability.
"""

import uuid
from typing import Optional

from langchain_core.messages import HumanMessage

from app.core.logger import get_logger
from app.graph.builder import FinancialGraphManager
from app.schemas.responses import ChatResponse

logger = get_logger("CHAT_SERVICE")


class ChatService:
    """Service for handling chat operations with the financial agent."""
    
    def __init__(self, graph_manager: FinancialGraphManager):
        """Initialize ChatService.
        
        Args:
            graph_manager: Graph manager instance for agent orchestration
        """
        self.graph_manager = graph_manager
    
    def _generate_thread_id(self) -> str:
        """Generate a unique thread identifier.
        
        Returns:
            UUID string for the thread
        """
        return str(uuid.uuid4())
    
    def _build_config(self, thread_id: str) -> dict:
        """Build configuration for graph execution.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            Configuration dictionary
        """
        return {"configurable": {"thread_id": thread_id}}
    
    def _build_initial_state(self, message: str, user_id: str) -> dict:
        """Build initial state for graph execution.
        
        Args:
            message: User's message
            user_id: User identifier
            
        Returns:
            Initial state dictionary
        """
        return {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id
        }
    
    async def process_chat(
        self,
        message: str,
        user_id: str
    ) -> ChatResponse:
        """Process a chat request through the financial agent.
        
        This method orchestrates the entire chat flow:
        1. Generates a unique thread ID
        2. Builds the initial state
        3. Executes the graph (agent reasoning cycle)
        4. Determines if human review is needed
        5. Returns appropriate response
        
        Args:
            message: User's message/query
            user_id: User identifier (scope owner)
            
        Returns:
            ChatResponse with status and content
            
        Raises:
            Exception: If graph execution fails
        """
        logger.info(f"Processing chat for user {user_id}")
        
        # Generate thread ID and configuration
        thread_id = self._generate_thread_id()
        config = self._build_config(thread_id)
        graph = self.graph_manager.graph
        
        # Build initial state
        initial_state = self._build_initial_state(message, user_id)
        
        # Execute agent graph (ReAct cycle: Agent -> Tools -> Agent -> END)
        final_state = await graph.ainvoke(initial_state, config=config)
        snapshot = await graph.aget_state(config)
        
        # Determine if human review is needed
        if snapshot.next:
            # Agent requires human review (financial recommendation detected)
            return ChatResponse(
                status="pending_review",
                user_id=user_id,
                thread_id=thread_id,
                message="Your request involves a financial recommendation and is pending human approval.",
                preview=final_state["messages"][-1].content
            )
        
        # Direct response (informational query)
        return ChatResponse(
            status="success",
            user_id=user_id,
            thread_id=thread_id,
            response=final_state["messages"][-1].content
        )
