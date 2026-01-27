import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.service.mcp_client import MCPClient
from app.service.ingestion_service import IngestionService
from app.core.logger import get_logger

# Configuración
logger = get_logger("API_ROUTES")
router = APIRouter()

# Inicialización de servicios (se pueden inyectar o instanciar aquí)
mcp_client = MCPClient()
ingest_service = IngestionService()


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