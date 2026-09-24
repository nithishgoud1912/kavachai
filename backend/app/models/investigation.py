"""
KavachAI — Investigation Pydantic Schemas
Mirrors: API_Reference.md §4
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.chat import AttachmentItem, UploadResponse


class InvestigationCreate(BaseModel):
    """POST /investigations request body."""
    query: str = Field(min_length=1, max_length=20000)
    session_id: Optional[str] = None
    attachments: Optional[List[AttachmentItem]] = Field(default_factory=list, max_length=20)


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
