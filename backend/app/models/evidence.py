"""
KavachAI — Evidence Pydantic Schemas
Mirrors: API_Reference.md §5
"""

from pydantic import BaseModel
from typing import List, Optional, Any


class EvidenceResponse(BaseModel):
    """GET /evidence/{source_id} response — polymorphic by type."""
    source_id: str
    type: str  # "document", "dataset", "pid_drawing"
    filename: str
    page: Optional[int] = None
    excerpt: Optional[str] = None
    section: Optional[str] = None
    view_url: Optional[str] = None
    # For dataset evidence
    rows: Optional[List[dict]] = None
    # For P&ID evidence
    highlighted_component: Optional[str] = None
    connections: Optional[List[str]] = None
