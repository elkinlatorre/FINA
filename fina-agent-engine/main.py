from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import router as api_router
from app.graph.builder import graph_manager
from app.core.logger import get_logger

logger = get_logger("MAIN_AGENT")

# Inicialización de FastAPI con metadata para el Swagger
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Al arrancar: Inicializamos el grafo y la DB
    await graph_manager.initialize()
    yield
    # Al apagar: Cerramos la conexión física
    await graph_manager.close()
app = FastAPI(
    title="FINA Agent Engine - Nodo A",
    description="Orquestador Inteligente para consultas financieras y análisis de portafolio.",
    version="1.0.0",
    docs_url="/docs",  # URL del Swagger
    redoc_url="/redoc",
    lifespan=lifespan
)

# Inclusión de rutas
app.include_router(api_router, prefix="/api/v1")

# Opcional: Ruta raíz para redirección o saludo
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to FINA Agent Engine. Visit /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Nodo A server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)