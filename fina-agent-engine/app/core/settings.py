import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()



class Settings:
    """Application settings and configuration."""
    
    # Valid supervisors with authorization mappings
    VALID_SUPERVISORS: Dict[str, str] = {
        "SUP-9988": "Senior Portfolio Manager - Area A",
        "SUP-1122": "Compliance Officer - Area B"
    }
    
    # Keywords for governance classification
    SENSITIVE_FINANCIAL_KEYWORDS: list[str] = [
        "risk", "riesgo",
        "recommendation", "recomendación", "recomendar",
        "portfolio", "portafolio", "cartera", "balance",
        "assets", "activos",
        "advice", "consejo", "asesoría"
    ]
    
    RISK_FINANCIAL_KEYWORDS: list[str] = [
        "buy", "comprar",
        "sell", "vender",
        "trade", "operar", "trading",
        "allocate", "asignar",
        "invest", "invertir", "inversión"
    ]
    
    # Risk scoring configuration
    HIGH_RISK_MULTIPLIER: int = 2
    RISK_SCORE_THRESHOLD: int = 2
    
    # Database configuration
    CHECKPOINT_DB_PATH: str = "checkpoints.sqlite"
    
    # MCP Server configuration
    MCP_HOST: str = "mcp-data-server"
    MCP_PORT: int = 8001
    
    # LLM Configuration
    LLM_MODEL: str = "llama-3.1-8b-instant" #"llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.0
    PRICE_1K_PROMPT: float = 0.00059
    PRICE_1K_COMPLETION: float = 0.00079

    # Embedding Model configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    HUGGINGFACEHUB_API_TOKEN: str = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Chunking configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Data paths
    DATA_DIR: str = "data"
    VECTOR_DB_PATH: str = "data/vector_db"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Application Server configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "*"

    def get_allowed_origins_list(self) -> list[str]:
        """Convert comma-separated allowed origins string to list."""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    # File upload limits
    MAX_PDF_SIZE_MB: int = 50
    ALLOWED_FILE_EXTENSIONS: list[str] = [".pdf"]


# Global settings instance
settings = Settings()

