"""
KavachAI — Ingestion Pydantic Schemas
Mirrors: API_Reference.md §3
"""

from pydantic import BaseModel
from typing import List, Optional


class DocumentUploadResponse(BaseModel):
    """POST /knowledge-base/documents response (202)."""
    document_id: str
    status: str  # "processing"
    chunks_expected: bool = True


class DocumentDetailResponse(BaseModel):
    """GET /knowledge-base/documents/{document_id} response."""
    document_id: str
    filename: str
    document_type: str
    status: str  # "processing", "ready", "failed"
    pages: Optional[int] = None
    chunks: int = 0
    equipment_ids: List[str] = []
    ingested_at: str


class DatasetUploadResponse(BaseModel):
    """POST /knowledge-base/datasets response (200)."""
    dataset_id: str
    columns: List[str]
    row_count: int
    status: str  # "ready"


class KnowledgeBaseSummary(BaseModel):
    """GET /knowledge-base/summary response."""
    documents: int
    datasets: int
    pid_drawings: int
