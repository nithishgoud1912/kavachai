"""
KavachAI Backend Configuration
Reads from .env via pydantic-settings. Single source of truth for all config values.
Implements: NFR-MNT-2 (model swap via config only), NFR-SEC-1 (local-only endpoints)
"""

from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import List
import json

_CANONICAL_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class Settings(BaseSettings):
    """Application settings — all values configurable via .env or environment variables."""

    # --- Ollama ---
    OLLAMA_HOST: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen2.5:3b"
    CODING_MODEL: str = "qwen2.5-coder:3b"
    ALLOWED_INFERENCE_HOSTS: str = "localhost,127.0.0.1,::1,ollama"
    MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024
    MAX_EXTRACTED_BYTES: int = 100 * 1024 * 1024
    MAX_DOCUMENT_PAGES: int = 100
    MAX_BATCH_FILES: int = 20
    TESSERACT_CMD: str = (str(Path("C:/Program Files/Tesseract-OCR/tesseract.exe"))
                         if Path("C:/Program Files/Tesseract-OCR/tesseract.exe").is_file() else "tesseract")
    SANDBOX_IMAGE: str = "python:3.11-slim"
    RETRIEVAL_MIN_SCORE: float = 0.25
    VISION_MODEL: str = "qwen2.5vl:3b"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    # --- Database ---
    SQLITE_DB_PATH: str = str(_CANONICAL_DATA_DIR / "kavachai.db")
    CHROMA_DB_PATH: str = str(_CANONICAL_DATA_DIR / "chroma")
    OBJECT_STORE_PATH: str = str(_CANONICAL_DATA_DIR / "objects")

    # --- Ingestion ---
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    EMBEDDING_DIMENSION: int = 768

    # --- Performance ---
    LLM_TIMEOUT_SECONDS: int = 300
    LLM_CONTEXT_TOKENS: int = Field(default=8192, ge=4096, le=32768)
    AGENT_TIMEOUT_SECONDS: int = 300
    VISION_TIMEOUT_SECONDS: int = 180
    VISION_MAX_IMAGE_EDGE: int = Field(default=1024, ge=512, le=4096)

    # --- Local security / RBAC ---
    # Set ENVIRONMENT=production and a long random BOOTSTRAP_TOKEN before first start.
    ENVIRONMENT: str = "production"
    ALLOW_DEMO_SESSIONS: bool = False
    BOOTSTRAP_TOKEN: str = ""
    ACCESS_TOKEN_TTL_MINUTES: int = 5
    SESSION_IDLE_MINUTES: int = 15
    SESSION_MAX_HOURS: int = 8

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        return json.loads(self.CORS_ORIGINS)

    @field_validator("SQLITE_DB_PATH", "CHROMA_DB_PATH", "OBJECT_STORE_PATH", mode="after")
    @classmethod
    def make_absolute_path(cls, v: str) -> str:
        p = Path(v)
        if not p.is_absolute():
            parts = p.parts[1:] if p.parts and p.parts[0] == "." else p.parts
            if parts and parts[0] == "data":
                return str(_CANONICAL_DATA_DIR / Path(*parts[1:]))
            return str((_CANONICAL_DATA_DIR.parent / p).resolve())
        return str(p)

    model_config = {
        "env_file": (".env", str(_CANONICAL_DATA_DIR.parent / ".env")),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        # The repository-level Compose environment also defines frontend/backend
        # port variables. They are intentionally not backend Settings fields.
        "extra": "ignore",
    }


# Singleton instance — import this everywhere
settings = Settings()
