"""
KavachAI — Investigation Pydantic Schemas
Mirrors: API_Reference.md §4
"""

from pydantic import BaseModel
from typing import List, Optional
from app.models.chat import AttachmentItem, UploadResponse


class InvestigationCreate(BaseModel):
    """POST /investigations request body."""
    query: str
    session_id: Optional[str] = None
    attachments: Optional[List[AttachmentItem]] = []


class InvestigationCreateResponse(BaseModel):
    """POST /investigations response (202)."""
    investigation_id: str
    status: str  # "planning"
    stream_url: str
    attachments_count: int = 0



class SubTaskResponse(BaseModel):
    agent: str
    goal: str


class InvestigationPlanResponse(BaseModel):
    """GET /investigations/{id}/plan response."""
    investigation_id: str
    sub_tasks: List[SubTaskResponse]
