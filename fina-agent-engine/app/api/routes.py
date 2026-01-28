import os
import uuid
import shutil
from pydantic import BaseModel
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