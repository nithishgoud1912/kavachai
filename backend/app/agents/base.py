"""
KavachAI — Agent Base Interface and Contract Types
Implements: NFR-MNT-1 (each agent is independently testable with defined I/O contract)

Defines the common types shared across all agents, matching API_Reference.md §8.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Agent Names (API_Reference.md §4) ---
class AgentName(str, Enum):
    PLANNER = "planner"
    DOCUMENT_AGENT = "document_agent"
    DATA_AGENT = "data_agent"
    VISION_AGENT = "vision_agent"
    RAG_AGENT = "rag_agent"
    VERIFICATION_AGENT = "verification_agent"


class AgentStatus(str, Enum):
    PENDING = "pending"
    WORKING = "working"
    COMPLETE = "complete"
    SKIPPED = "skipped"
    FAILED = "failed"


# --- Planner Types (§8.1) ---
class SubTask(BaseModel):
    agent: AgentName
    goal: str


class InvestigationPlan(BaseModel):
    sub_tasks: List[SubTask]
    is_in_scope: bool


class CorpusSummary(BaseModel):
    documents: int
    datasets: int
    pid_drawings: int
    document_types: List[str] = Field(default_factory=list)
    equipment_ids: List[str] = Field(default_factory=list)


# --- Document Agent Types (§8.2) ---
class DocumentChunk(BaseModel):
    chunk_text: str
    source_id: str
    page: Optional[int] = 1
    score: float


# --- Data Agent Types (§8.3) ---
class DataPoint(BaseModel):
    timestamp: str
    value: float
    unit: str


class TrendDirection(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class DataAnalysisResult(BaseModel):
    """FR-DAT-2: All fields computed by pandas, NEVER by LLM."""
    trend: TrendDirection
    pct_change: float
    data_points: List[DataPoint]
    threshold_breach: Optional[bool] = None


# --- Vision Agent Types (§8.4) ---
class VisionAnalysisResult(BaseModel):
    found: bool
    connections: List[str] = Field(default_factory=list)
    confidence: float = 0.0


# --- RAG Agent Types (§8.5) ---
class SpecChunk(BaseModel):
    chunk_text: str
    source_id: str
    page: Optional[int] = None
    section: Optional[str] = None


# --- Synthesis Types (§8.6) ---
class EvidenceItem(BaseModel):
    """A single piece of evidence from any agent."""
    type: str  # "document", "dataset", "pid_drawing"
    source_id: str
    label: str
    page: Optional[int] = None
    section: Optional[str] = None
    detail: Optional[str] = None


class EvidenceBundle(BaseModel):
    """
    Structured evidence assembled from all agent outputs.
    FR-SYN-1: This is the ONLY input the LLM receives — never raw documents.
    """
    document_findings: List[DocumentChunk] = Field(default_factory=list)
    data_findings: Optional[DataAnalysisResult] = None
    vision_findings: Optional[VisionAnalysisResult] = None
    spec_findings: List[SpecChunk] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)


class DraftFinding(BaseModel):
    """A single finding produced by synthesis."""
    id: str
    title: str
    detail: str
    evidence: List[EvidenceItem] = Field(default_factory=list)


class DraftFindings(BaseModel):
    findings: List[DraftFinding]
    condition_summary: str = ""


# --- Verification Types (§8.7) ---
class VerificationStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"


class VerifiedFinding(BaseModel):
    id: str
    title: str
    detail: str
    verification_status: VerificationStatus
    evidence: List[EvidenceItem] = Field(default_factory=list)


class VerificationResult(BaseModel):
    findings: List[VerifiedFinding]
    overall_confidence: int  # 0-100
    overall_status: str  # "verified", "partially_verified", "unverified"


# --- SSE Event Types ---
class AgentUpdateEvent(BaseModel):
    """SSE agent_update event per API_Reference.md §4."""
    agent: str
    status: str
    message: str
    elapsed_ms: int
