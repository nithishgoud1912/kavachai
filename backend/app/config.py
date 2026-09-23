"""
KavachAI Backend Configuration
Reads from .env via pydantic-settings. Single source of truth for all config values.
Implements: NFR-MNT-2 (model swap via config only), NFR-SEC-1 (local-only endpoints)
"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings — all values configurable via .env or environment variables."""

    # --- Ollama ---
    OLLAMA_HOST: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen2.5:3b"
    VISION_MODEL: str = "qwen2.5vl:3b"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    # --- Database ---
    SQLITE_DB_PATH: str = "./data/kavachai.db"
    CHROMA_DB_PATH: str = "./data/chroma"
    OBJECT_STORE_PATH: str = "./data/objects"

    # --- Ingestion ---
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    EMBEDDING_DIMENSION: int = 768

    # --- Performance ---
    LLM_TIMEOUT_SECONDS: int = 60
    AGENT_TIMEOUT_SECONDS: int = 30
    VISION_TIMEOUT_SECONDS: int = 60

    # --- Local security / RBAC ---
    # Set ENVIRONMENT=production and a long random BOOTSTRAP_TOKEN before first start.
    ENVIRONMENT: str = "development"
    ALLOW_DEMO_SESSIONS: bool = True
    BOOTSTRAP_TOKEN: str = ""
    ACCESS_TOKEN_TTL_MINUTES: int = 5
    SESSION_IDLE_MINUTES: int = 15
    SESSION_MAX_HOURS: int = 8

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        return json.loads(self.CORS_ORIGINS)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        # The repository-level Compose environment also defines frontend/backend
        # port variables. They are intentionally not backend Settings fields.
        "extra": "ignore",
    }


# Singleton instance — import this everywhere
settings = Settings()
