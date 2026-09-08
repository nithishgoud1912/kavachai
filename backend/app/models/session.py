"""
KavachAI — Session Pydantic Schemas
Mirrors: API_Reference.md §2
"""

from pydantic import BaseModel
from typing import Optional


class SessionCreate(BaseModel):
    """POST /session request body (FR-ACC-1)."""
    name: str
    department: str


class SessionResponse(BaseModel):
    """POST /session response body."""
    session_id: str
    name: str
    department: str
    issued_at: str
