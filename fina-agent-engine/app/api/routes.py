import os
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.dependencies import (
    ApprovalServiceDep,
    ChatServiceDep,
    IngestionServiceDep,
    MCPClientDep,
    ThreadServiceDep,
    CurrentUserDep,
)
from app.core.exceptions import FinaAgentException, ValidationError
from app.core.logger import get_logger
from app.schemas.approval_request import ApprovalRequest
from app.schemas.requests import ChatRequest
from app.schemas.responses import (
    ApprovalResponse,
    ChatResponse,
    HealthResponse,
    IngestionResponse,
    ThreadStatusResponse,
)

# Configuration
logger = get_logger("API_ROUTES")
router = APIRouter()

@router.post("/chat", response_model=ChatResponse, tags=["Financial Agent"])
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatServiceDep,
    current_user: CurrentUserDep
) -> ChatResponse:
    # Use user_id from token, or request if matching/provided (token takes precedence)
    user_id = current_user.get("user_id")
    logger.info(f"Received query from authenticated user {user_id}: {request.message}")
    
    try:
        return await chat_service.process_chat(
            message=request.message,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error in Graph Execution: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent Reasoning Error: {str(e)}"
        )


@router.post("/chat/stream", tags=["Financial Agent"])
async def chat_stream_endpoint(
        request: ChatRequest,
        chat_service: ChatServiceDep,
        current_user: CurrentUserDep
):
    user_id = current_user.get("user_id")
    logger.info(f"Stream request from authenticated user {user_id}")

    return StreamingResponse(
        chat_service.process_chat_stream(
            message=request.message,
            user_id=user_id
        ),
        media_type="text/event-stream"
    )

@router.post("/approve", response_model=ApprovalResponse, tags=["Financial Agent"])
async def approve_endpoint(
    request: ApprovalRequest,
    approval_service: ApprovalServiceDep
) -> ApprovalResponse:
    """HITL Endpoint: Handles approval/rejection of financial recommendations.
    
    Implements:
    - Supervisor authorization validation
    - Segregation of duties enforcement
    - Scope verification (user ID matching)
    - Idempotency protection
    - Complete audit trail creation
    
    Args:
        request: Approval request with decision details
        approval_service: Injected ApprovalService dependency
        
    Returns:
        ApprovalResponse with decision result
        
    Raises:
        HTTPException: On validation or processing errors
    """
    try:
        return await approval_service.process_approval(request)
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except FinaAgentException as e:
        # Convert custom exceptions to HTTP responses
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Critical error in approve_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Governance Error.")



@router.get("/chat/{thread_id}", response_model=ThreadStatusResponse, tags=["Financial Agent"])
async def get_chat_status(
    thread_id: str,
    thread_service: ThreadServiceDep
) -> ThreadStatusResponse:
    """Audit Endpoint: Retrieves the full history and final decision for a specific thread.
    
    Provides complete transparency for auditing and compliance purposes.
    
    Args:
        thread_id: Unique thread identifier
        thread_service: Injected ThreadService dependency
        
    Returns:
        ThreadStatusResponse with complete thread information
        
    Raises:
        HTTPException: If thread not found or retrieval fails
    """
    try:
        return await thread_service.get_thread_status(thread_id)
    except FinaAgentException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error retrieving audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(mcp_client: MCPClientDep) -> HealthResponse:
    """Health check endpoint: Verifies Node A status and Node B (MCP) connectivity.
    
    Returns comprehensive system health information including:
    - Node A operational status
    - MCP server connectivity (Node B)
    - API key configuration validation
    - Vector database status
    
    Args:
        mcp_client: Injected MCPClient dependency
        
    Returns:
        HealthResponse with system health details
    """
    mcp_status = await mcp_client.check_connection()
    return HealthResponse(
        status="online",
        node_a="healthy",
        node_b_connected=mcp_status,
        api_keys_set={
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "huggingface": bool(os.getenv("HUGGINGFACEHUB_API_TOKEN"))
        },
        vector_db="exists" if os.path.exists("data/vector_db") else "empty"
    )



@router.post("/ingest", response_model=IngestionResponse, tags=["Data Ingestion"])
async def upload_pdf(
    file: UploadFile = File(...),
    ingest_service: IngestionServiceDep = None,
    current_user: CurrentUserDep = None
) -> IngestionResponse:
    user_id = current_user.get("user_id")
    logger.info(f"File upload from user {user_id}")
    """PDF Ingestion Endpoint: Processes PDF files for vector database storage.
    
    Validates file type, processes the PDF into chunks, and stores
    in the vector database for RAG retrieval.
    
    Args:
        file: Uploaded PDF file
        ingest_service: Injected IngestionService dependency
        
    Returns:
        IngestionResponse with processing results
        
    Raises:
        ValidationError: If file is not a PDF
        HTTPException: On processing errors
    """
    if not file.filename.lower().endswith(".pdf"):
        raise ValidationError("Only PDF files are allowed")

    os.makedirs("data", exist_ok=True)
    temp_path = f"data/temp_{file.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the PDF with user isolation
        chunks = await ingest_service.process_pdf(temp_path, user_id)

        return IngestionResponse(
            status="success",
            filename=file.filename,
            chunks_processed=chunks,
            storage_mode="Ephemeral Cloud RAG (Session Scoped)"
        )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Ingestion error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/auth/logout", tags=["Authentication"])
async def logout_and_cleanup(
    current_user: CurrentUserDep,
    ingest_service: IngestionServiceDep
):
    """
    Logout Endpoint: Cleans up all ephemeral RAG data for the user.
    """
    user_id = current_user.get("user_id")
    await ingest_service.cleanup_user_data(user_id)
    return {"status": "success", "message": "Logged out and user data cleaned up."}
