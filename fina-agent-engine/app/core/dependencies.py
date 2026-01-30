"""FastAPI dependency injection providers.

Provides singleton services and dependencies for route handlers,
enabling proper separation of concerns and testability.
"""

from typing import Annotated

from fastapi import Depends

from app.graph.builder import graph_manager
from app.service.approval_service import ApprovalService
from app.service.chat_service import ChatService
from app.service.ingestion_service import IngestionService
from app.service.mcp_client import MCPClient
from app.service.thread_service import ThreadService


def get_chat_service() -> ChatService:
    """Provide ChatService instance.
    
    Returns:
        Configured ChatService
    """
    return ChatService(graph_manager)


def get_approval_service() -> ApprovalService:
    """Provide ApprovalService instance.
    
    Returns:
        Configured ApprovalService
    """
    return ApprovalService(graph_manager)


def get_thread_service() -> ThreadService:
    """Provide ThreadService instance.
    
    Returns:
        Configured ThreadService
    """
    return ThreadService(graph_manager)


def get_mcp_client() -> MCPClient:
    """Provide MCPClient instance.
    
    Returns:
        Configured MCPClient
    """
    return MCPClient()


def get_ingestion_service() -> IngestionService:
    """Provide IngestionService instance.
    
    Returns:
        Configured IngestionService
    """
    return IngestionService()


# Type annotations for dependency injection
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
ApprovalServiceDep = Annotated[ApprovalService, Depends(get_approval_service)]
ThreadServiceDep = Annotated[ThreadService, Depends(get_thread_service)]
MCPClientDep = Annotated[MCPClient, Depends(get_mcp_client)]
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]
