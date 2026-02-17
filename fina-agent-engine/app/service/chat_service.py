"""ChatService - Business logic for chat operations.

Handles chat request processing, thread management, and graph orchestration.
Separates business logic from the API layer for better testability and reusability.
"""

import uuid
import json

from langchain_core.messages import HumanMessage
from typing import AsyncGenerator, Optional
from app.core.logger import get_logger
from app.core.settings import settings
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
            "user_id": user_id,
            "usage": {
                "prompt_tokens": 0, 
                "completion_tokens": 0, 
                "total_tokens": 0, 
                "estimated_cost": 0.0
            }
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

        usage_data = final_state.get("usage")

        # Determine if human review is needed
        if snapshot.next:
            # Agent requires human review (financial recommendation detected)
            return ChatResponse(
                status="pending_review",
                user_id=user_id,
                thread_id=thread_id,
                message="Your request involves a financial recommendation and is pending human approval.",
                preview=final_state["messages"][-1].content,
                usage=usage_data
            )
        
        # Direct response (informational query)
        return ChatResponse(
            status="success",
            user_id=user_id,
            thread_id=thread_id,
            response=final_state["messages"][-1].content,
            usage=usage_data
        )

    async def process_chat_stream(self, message: str, user_id: str) -> AsyncGenerator[str, None]:
        thread_id = self._generate_thread_id()
        config = self._build_config(thread_id)
        graph = self.graph_manager.graph
        initial_state = self._build_initial_state(message, user_id)

        has_yielded_content = False
        # 1. stream execution
        async for event in graph.astream_events(initial_state, config=config, version="v2"):
            kind = event["event"]
            node_name = event.get("metadata", {}).get("langgraph_node")

            if kind == "on_chat_model_end" and node_name == "agent":
                output = event["data"]["output"]
                content = output.content
                if content:
                    has_yielded_content = True
                    yield f"data: {json.dumps({'type': 'answer', 'content': content})}\n\n"
                
                # If turn has tool calls, notify frontend that we are continuing to process
                if hasattr(output, 'tool_calls') and output.tool_calls:
                    yield f"data: {json.dumps({'type': 'thinking', 'content': f'Agent is executing {len(output.tool_calls)} tool(s)...'})}\n\n"

            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool', 'tool': event['name']})}\n\n"

        # 2. async pause to allow checkpoint consolidation
        import asyncio
        await asyncio.sleep(0.1)

        # 3. Recover the REAL state from the SQLite checkpointer
        snapshot = await graph.aget_state(config)
        final_state = snapshot.values

        # Extract accumulated usage
        usage = final_state.get("usage", {
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "estimated_cost": 0.0
        })
        
        # Get final message content
        messages = final_state.get("messages", [])
        final_msg_content = ""
        if messages:
            final_msg_content = messages[-1].content
            logger.info(f"🏁 Final state messages count: {len(messages)} | Last message content length: {len(final_msg_content)}")

        # Determine true status
        safety = final_state.get("safety_metadata", {})
        is_safe = safety.get("is_safe", True)
        
        if not is_safe:
            status = "blocked"
            # If it was blocked by guardrail, we definitively yield the block message
            yield f"data: {json.dumps({'type': 'answer', 'content': final_msg_content})}\n\n"
        elif snapshot.next:
            status = "pending_review"
            # For HITL, we MUST yield the final message as the definitive "preview"
            # but we use a distinct event to avoid simple duplication if possible
            # or we just rely on the frontend to replace content with 'final' content.
        else:
            status = "success"

        # The 'final' event is the absolute source of truth.
        # Frontend should use this content to replace the accumulated state.
        yield f"data: {json.dumps({
            'type': 'final',
            'status': status,
            'thread_id': thread_id,
            'content': final_msg_content,
            'usage': usage
        })}\n\n"
