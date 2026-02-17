from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.core.exceptions import FinaAgentException
from app.core.logger import get_logger
from app.core.settings import settings
from app.graph.builder import graph_manager

logger = get_logger("MAIN_AGENT")


# FastAPI initialization with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize graph and database
    logger.info("Starting FINA Agent Engine...")
    
    # Permission diagnostics for Windows/Docker volumes
    import os
    data_dir = settings.DATA_DIR
    logger.info(f"🔍 Diagnostic: Checking access to {data_dir}")
    if os.path.exists(data_dir):
        is_writable = os.access(data_dir, os.W_OK)
        stats = os.stat(data_dir)
        logger.info(f"📂 Data dir exists. Protected/Read-only: {not is_writable} | Owner UID: {stats.st_uid} | Current UID: {os.getuid()}")
        
        # Try a real write test
        test_file = os.path.join(data_dir, ".startup_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"✅ Write test PASSED for {data_dir}")
        except Exception as e:
            logger.error(f"❌ Write test FAILED for {data_dir}: {e}")
            logger.warning("💡 TIP: Run 'icacls data /grant Everyone:F /T' on your Windows host in the engine folder.")
    else:
        logger.warning(f"⚠️ Data directory {data_dir} does not exist yet.")

    await graph_manager.initialize()
    logger.info("Graph manager initialized successfully")
    yield
    # Shutdown: Close physical connections
    logger.info("Shutting down FINA Agent Engine...")
    await graph_manager.close()
    logger.info("Shutdown complete")

app = FastAPI(
    title="FINA Agent Engine - Node A",
    description="Intelligent orchestrator for financial queries and portfolio analysis.",
    version="1.0.0",
    docs_url="/docs",  # Swagger URL
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for custom exceptions
@app.exception_handler(FinaAgentException)
async def fina_exception_handler(request: Request, exc: FinaAgentException):
    """Handle all custom FINA exceptions and return appropriate HTTP responses."""
    logger.error(
        f"Exception occurred: {exc.__class__.__name__} - {exc.message}",
        extra={"path": request.url.path, "method": request.method}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message
            }
        }
    )

# Inclusión de rutas
app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirects to API documentation."""
    return {
        "message": "Welcome to FINA Agent Engine. Visit /docs for API documentation.",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.APP_HOST}:{settings.APP_PORT}...")
    uvicorn.run(
        app,
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )