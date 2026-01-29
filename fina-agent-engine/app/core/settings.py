"""Application settings using Pydantic for environment variable validation.

This module provides centralized configuration management with automatic
validation of environment variables at application startup.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    All required environment variables must be set or the application
    will fail to start. Optional variables have sensible defaults.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars
    )
    
    # API Keys (required for external services)
    GROQ_API_KEY: str
    HUGGINGFACEHUB_API_TOKEN: str
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    
    # Database paths
    DB_PATH: str = "checkpoints.sqlite"
    VECTOR_DB_PATH: str = "data/vector_db"
    
    # MCP Server configuration
    MCP_HOST: str = "mcp-data-server"
    MCP_PORT: int = 8001
    
    # Application server configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # Document processing configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100
    
    # Risk scoring configuration
    RISK_SCORE_THRESHOLD: int = 2
    HIGH_RISK_MULTIPLIER: int = 2
    
    # File upload limits
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]
    
    # CORS configuration (comma-separated origins)
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # LLM Configuration
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.0
    
    # Embedding model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    def get_allowed_origins_list(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def mcp_base_url(self) -> str:
        """Full MCP server base URL."""
        return f"http://{self.MCP_HOST}:{self.MCP_PORT}"
    
    @property
    def max_file_size_bytes(self) -> int:
        """Maximum file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Singleton instance
settings = Settings()
