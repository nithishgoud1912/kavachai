"""
KavachAI — Report Pydantic Schemas
Mirrors: API_Reference.md §4 (GET /investigations/{id}/report) and §6 (export)
"""

from pydantic import BaseModel
from typing import List, Optional


class FindingEvidence(BaseModel):
    type: str  # "document", "dataset", "pid_drawing"
    source_id: str
    label: str
    page: Optional[int] = None
    section: Optional[str] = None


class Finding(BaseModel):
    id: str
    title: str
    detail: str
    verification_status: str  # "supported", "partially_supported", "unsupported"
    evidence: List[FindingEvidence]


class InvestigationReport(BaseModel):
    """GET /investigations/{id}/report response (FR-RPT-1)."""
    investigation_id: str
    query: str
    overall_status: str  # "attention_required", "normal", "abnormal", "insufficient_evidence"
    condition_summary: str
    findings: List[Finding]
    pid_relationship: Optional[List[str]] = None
    conclusion: str
    confidence: int  # 0-100
    verification_status: str  # "verified", "partially_verified", "unverified"
    generated_at: str


class ExportRequest(BaseModel):
    """POST /investigations/{id}/export request."""
    format: str = "pdf"


class ExportResponse(BaseModel):
    """POST /investigations/{id}/export response."""
    export_id: str
    download_url: str
