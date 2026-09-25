"""
KavachAI — Ingestion Pydantic Schemas
Mirrors: API_Reference.md §3
"""

from pydantic import BaseModel, Field
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


class GraphNodeCreate(BaseModel):
    """POST /knowledge-base/graph/nodes request body."""
    equipment_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._ -]*$")
    equipment_type: str = Field(default="equipment", min_length=1, max_length=64)
    label: Optional[str] = Field(default=None, max_length=160)


class GraphEdgeCreate(BaseModel):
    """POST /knowledge-base/graph/edges request body."""
    from_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._ -]*$")
    to_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._ -]*$")
    relationship: str = Field(default="connected_to", min_length=1, max_length=64)
    label: Optional[str] = Field(default=None, max_length=160)


class GraphResponse(BaseModel):
    """GET /knowledge-base/graph response."""
    nodes: List[dict]
    edges: List[dict]
