"""
KavachAI — Audit Log Pydantic Schemas
Mirrors: API_Reference.md §7
"""

from pydantic import BaseModel
from typing import List, Optional


class AuditEntry(BaseModel):
    """Single audit log entry."""
    investigation_id: str
    user: str
    department: str
    query: str
    agents_invoked: List[str]
    verification_status: Optional[str] = None
    confidence: Optional[int] = None
    timestamp: str


class AuditLogResponse(BaseModel):
    """GET /audit-log response."""
    entries: List[AuditEntry]
    total: int
