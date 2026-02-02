import pytest
import json
import os
from unittest.mock import patch
from app.core.settings import settings

# Override settings for EVALS
@pytest.fixture(scope="session", autouse=True)
def setup_eval_env():
    """Configure environment for evaluations."""
    # Ensure we point to the correct MCP host (running in Docker, exposed on localhost)
    settings.MCP_HOST = "localhost"
    settings.MCP_PORT = 8001
    
    # We need a real Groq API key for EVALS (not mocked)
    # The user should have it in their .env
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "tu_llave_groq":
        pytest.fail("GROQ_API_KEY is not set or is default. EVALS require a real LLM API key.")

@pytest.fixture
def benchmarks():
    """Load benchmark data from JSONL."""
    benchmark_path = os.path.join(os.path.dirname(__file__), "benchmarks.jsonl")
    with open(benchmark_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

@pytest.fixture
async def agent_service():
    """Initialize the ChatService for evaluation."""
    from app.graph.builder import FinancialGraphManager
    from app.service.chat_service import ChatService
    
    manager = FinancialGraphManager()
    await manager.initialize()
    service = ChatService(manager)
    yield service
    await manager.close()
