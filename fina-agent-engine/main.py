import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.service.mcp_client import MCPClient
from app.service.ingestion_service import IngestionService
from app.core.logger import get_logger

# 1. Configuración de logs
logger = get_logger("MAIN_AGENT")
app = FastAPI(title="FINA Agent Engine - Nodo A")

# 2. Inicialización de servicios (Conectamos al Nodo B y preparamos Ingesta)
mcp_client = MCPClient()
ingest_service = IngestionService()

# Crear carpeta de datos si no existe
os.makedirs("data", exist_ok=True)


@app.get("/health")
async def health_check():
    """Estado de salud y conectividad"""
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


@app.post("/ingest")
async def upload_pdf(file: UploadFile = File(...)):
    """Recibe y procesa el PDF usando APIs externas para ahorrar disco"""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")

    temp_path = f"data/temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Procesa el PDF (Smart Load con Hash + API de Hugging Face)
        chunks = await ingest_service.process_pdf(temp_path)

        return {
            "status": "success",
            "filename": file.filename,
            "chunks": chunks,
            "mode": "Cloud API (Zero Disk Impact)"
        }
    except Exception as e:
        logger.error(f"Error en ingesta: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)