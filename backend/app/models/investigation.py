"""
KavachAI — Investigation Pydantic Schemas
Mirrors: API_Reference.md §4
"""

from pydantic import BaseModel
from typing import List, Optional


class InvestigationCreate(BaseModel):
    """POST /investigations request body."""
    query: str
    session_id: str


class InvestigationCreateResponse(BaseModel):
    """POST /investigations response (202)."""
    investigation_id: str
    status: str  # "planning"
    stream_url: str


class SubTaskResponse(BaseModel):
    agent: str
    goal: str


class InvestigationPlanResponse(BaseModel):
    """GET /investigations/{id}/plan response."""
    investigation_id: str
    sub_tasks: List[SubTaskResponse]
