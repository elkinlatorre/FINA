import os
import uuid
import shutil
from pydantic import BaseModel

from app.schemas.approval_request import ApprovalRequest
from app.service.mcp_client import MCPClient
from langchain_core.messages import HumanMessage
from app.graph.builder import graph_manager
from app.service.ingestion_service import IngestionService
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.logger import get_logger

# Configuración
logger = get_logger("API_ROUTES")
router = APIRouter()

# Inicialización de servicios (se pueden inyectar o instanciar aquí)
mcp_client = MCPClient()
ingest_service = IngestionService()


# --- Esquema para el Chat ---
class ChatRequest(BaseModel):
    message: str
    user_id: str = "user123"


@router.post("/chat", tags=["Financial Agent"])
async def chat_endpoint(request: ChatRequest):
    """
    Financial Advisor Chat: Orchestrates reasoning between PDF (RAG)
    and Private Vault (MCP) using a ReAct cycle.
    """
    logger.info(f"Received query from {request.user_id}: {request.message}")
    generated_thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": generated_thread_id}}
    graph = graph_manager.graph

    try:
        # Inicializamos el estado del grafo con el mensaje del usuario
        initial_state = {
            "messages": [HumanMessage(content=request.message)]
        }

        # Ejecutamos el grafo (Fase 2 completa)
        # Esto disparará el ciclo: Agent -> Tools -> Agent -> END
        final_state = await graph.ainvoke(initial_state,config=config)
        snapshot = await graph.aget_state(config)

        if snapshot.next:
            return {
                "status": "pending_review",
                "user_id": request.user_id,
                "thread_id": generated_thread_id,
                "message": "Your request involves a financial recommendation and is pending human approval.",
                "preview": final_state["messages"][-1].content
            }

        return {
            "status": "success",
            "user_id": request.user_id,
            "thread_id": generated_thread_id,
            "response": final_state["messages"][-1].content
        }
    except Exception as e:
        logger.error(f"Error in Graph Execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent Reasoning Error: {str(e)}")


@router.post("/approve", tags=["Financial Agent"])
async def approve_endpoint(request: ApprovalRequest):
    """
    HITL Endpoint: Approves, edits, or rejects a pending financial recommendation.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    graph = graph_manager.graph

    try:
        # 1. Recuperamos el estado actual desde SQLite
        snapshot = await graph.aget_state(config)

        # If a final decision already exists, we block reprocessing.
        existing_decision = snapshot.values.get("final_decision")
        if existing_decision in ["approved", "rejected"]:
            return {
                "status": "already_processed",
                "message": f"This thread has already been {existing_decision}.",
                "thread_id": request.thread_id,
                "final_decision": existing_decision
            }

        if not snapshot.next:
            raise HTTPException(status_code=400, detail="No pending review found for this thread.")

        decision = "approved" if request.approve else "rejected"
        await graph.aupdate_state(config, {"final_decision": decision})

        if request.approve:
            # Lógica de edición (opcional)
            if request.edited_response:
                current_messages = list(snapshot.values["messages"])
                current_messages[-1].content = request.edited_response
                await graph.aupdate_state(config, {"messages": current_messages})

            final_state = await graph.ainvoke(None, config=config)
            return {
                "status": "approved",
                "thread_id": request.thread_id,
                "response": final_state["messages"][-1].content
            }
        else:
            # Feedback del rechazo (Punto 1 ya implementado)
            feedback_message = HumanMessage(
                content="REJECTED: Your previous recommendation was not authorized. Provide an alternative."
            )
            await graph.aupdate_state(config, {"messages": [feedback_message]})

            final_state = await graph.ainvoke(None, config=config)
            return {
                "status": "rejected",
                "thread_id": request.thread_id,
                "message": "The agent has been notified of the rejection.",
                "new_agent_response": final_state["messages"][-1].content
            }
    except Exception as e:
        logger.error(f"Error during approval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/{thread_id}", tags=["Financial Agent"])
async def get_chat_status(thread_id: str):
    """
    Audit Endpoint: Retrieves the full history and final decision for a specific thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    graph = graph_manager.graph

    try:
        # Recuperamos el estado actual de la base de datos física
        snapshot = await graph.aget_state(config)

        if not snapshot.values:
            raise HTTPException(status_code=404, detail="Thread ID not found.")

        # Extraemos los datos relevantes para el auditor/usuario
        messages = snapshot.values.get("messages", [])
        decision = snapshot.values.get("final_decision", "pending")

        # Formateamos el historial de forma legible
        history = [
            {
                "role": msg.type,  # 'human' or 'ai'
                "content": msg.content
            }
            for msg in messages
        ]

        return {
            "thread_id": thread_id,
            "status": "completed" if not snapshot.next else "pending_review",
            "final_decision": decision,
            "history_count": len(history),
            "full_history": history
        }

    except Exception as e:
        logger.error(f"Error retrieving audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", tags=["System"])
async def health_check():
    """Verifica el estado de salud del Nodo A y su conexión con el Nodo B."""
    mcp_status = await mcp_client.check_connection()
    return {
        "status": "online",
        "node_a": "healthy",
        "node_b_connected": mcp_status,
        "api_keys_set": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "huggingface": bool(os.getenv("HUGGINGFACEHUB_API_TOKEN"))
        },
        "vector_db": "exists" if os.path.exists("data/vector_db") else "empty"
    }


@router.post("/ingest", tags=["Data Ingestion"])
async def upload_pdf(file: UploadFile = File(...)):
    """Recibe y procesa un PDF para alimentar la base de datos vectorial."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    os.makedirs("data", exist_ok=True)
    temp_path = f"data/temp_{file.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Procesa el PDF
        chunks = await ingest_service.process_pdf(temp_path)

        return {
            "status": "success",
            "filename": file.filename,
            "chunks_processed": chunks,
            "storage_mode": "Cloud API (Zero Disk Impact)"
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)