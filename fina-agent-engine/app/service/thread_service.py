"""ThreadService - Business logic for thread status queries.

Handles retrieving and formatting thread state for audit purposes.
"""

from app.core.exceptions import ThreadNotFoundError
from app.core.logger import get_logger
from app.graph.builder import FinancialGraphManager
from app.schemas.responses import ThreadStatusResponse

logger = get_logger("THREAD_SERVICE")


class ThreadService:
    """Service for handling thread status queries."""
    
    def __init__(self, graph_manager: FinancialGraphManager):
        """Initialize ThreadService.
        
        Args:
            graph_manager: Graph manager instance for state access
        """
        self.graph_manager = graph_manager
    
    async def get_thread_status(self, thread_id: str) -> ThreadStatusResponse:
        """Retrieve full status and history for a thread.
        
        This is the audit endpoint that provides complete transparency
        into a conversation thread's state, history, and final decision.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            ThreadStatusResponse with complete thread information
            
        Raises:
            ThreadNotFoundError: If thread doesn't exist
        """
        logger.info(f"Retrieving status for thread {thread_id}")
        
        config = {"configurable": {"thread_id": thread_id}}
        graph = self.graph_manager.graph
        
        # Retrieve current state from database
        snapshot = await graph.aget_state(config)
        
        if not snapshot.values:
            raise ThreadNotFoundError(thread_id)
        
        # Extract relevant data
        messages = snapshot.values.get("messages", [])
        decision = snapshot.values.get("final_decision", "pending")
        usage_data = snapshot.values.get("usage", {})

        # Format message history
        history = [
            {
                "role": msg.type,  # 'human' or 'ai'
                "content": msg.content
            }
            for msg in messages
        ]
        
        # Determine overall status
        status = "completed" if not snapshot.next else "pending_review"
        
        return ThreadStatusResponse(
            thread_id=thread_id,
            status=status,
            final_decision=decision,
            history_count=len(history),
            full_history=history,
            usage=usage_data
        )
