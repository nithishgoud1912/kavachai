"""
KavachAI — SQLAlchemy ORM Models
Implements: FR-ACC-1/2 (sessions), FR-ING-1..6 (documents), FR-ING-7 (datasets),
            FR-AUD-1/2 (audit_log — append-only), FR-RPT-1 (investigations)

Note: audit_log has NO update/delete methods anywhere — this is by design (FR-AUD-2).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, JSON, Boolean,
    ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- FR-ACC-1/2: Sessions ---
class Session(Base):
    """Lightweight demo session (FR-ACC-1)."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)  # FR-ACC-2: department for permission-aware retrieval
    issued_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    investigations = relationship("Investigation", back_populates="session")


# --- FR-ING-1..6: Documents ---
class Document(Base):
    """Ingested document metadata — mirrors GET /knowledge-base/documents/{id} response."""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=False)  # inspection_report, maintenance_history, sop, manual, pid_drawing, other
    status = Column(String, default="processing", nullable=False)  # processing, ready, failed
    pages = Column(Integer, nullable=True)
    chunks = Column(Integer, default=0)
    equipment_ids = Column(JSON, default=list)  # e.g. ["P-102"]
    department_scope = Column(String, nullable=True)  # FR-RAG-2: permission-aware retrieval
    ingested_at = Column(DateTime, default=utcnow, nullable=False)
    source_id = Column(String, nullable=False, unique=True)  # maps to object store key

    __table_args__ = (
        Index("ix_documents_equipment", "equipment_ids"),
        Index("ix_documents_type", "document_type"),
    )


# --- FR-ING-7: Datasets ---
class Dataset(Base):
    """Ingested structured dataset metadata."""
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    columns = Column(JSON, default=list)  # ["timestamp", "equipment_id", "metric", "value", "unit"]
    row_count = Column(Integer, default=0)
    status = Column(String, default="processing", nullable=False)  # processing, ready, failed
    table_name = Column(String, nullable=True)  # name of the SQLite table holding the rows
    ingested_at = Column(DateTime, default=utcnow, nullable=False)


# --- FR-RPT-1, FR-PLN-1..3: Investigations ---
class Investigation(Base):
    """An investigation query and its lifecycle state."""
    __tablename__ = "investigations"

    id = Column(String, primary_key=True, default=generate_uuid)
    query = Column(Text, nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    status = Column(String, default="planning", nullable=False)  # planning, investigating, complete, insufficient_evidence, failed
    plan = Column(JSON, nullable=True)  # Planner output: sub_tasks list
    evidence_bundle = Column(JSON, nullable=True)  # assembled evidence from all agents
    draft_findings = Column(JSON, nullable=True)  # synthesis output
    report = Column(JSON, nullable=True)  # final verified report
    confidence = Column(Integer, nullable=True)  # 0-100
    verification_status = Column(String, nullable=True)  # verified, partially_verified, unverified
    created_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="investigations")

    __table_args__ = (
        Index("ix_investigations_session", "session_id"),
        Index("ix_investigations_status", "status"),
    )


# --- FR-AUD-1/2: Audit Log (APPEND-ONLY — no update/delete exposed) ---
class AuditLogEntry(Base):
    """
    Immutable audit trail for every investigation.
    FR-AUD-2: This table is append-only. No UPDATE or DELETE methods are
    exposed at any layer (not just the API — also no ORM helper for it).
    The two-write pattern (workflow.md §4): write on creation, update on resolution.
    """
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    investigation_id = Column(String, nullable=False, index=True)
    user = Column(String, nullable=False)
    department = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    agents_invoked = Column(JSON, default=list)
    verification_status = Column(String, nullable=True)  # set on resolution
    confidence = Column(Integer, nullable=True)  # set on resolution
    status = Column(String, default="started", nullable=False)  # started, completed, insufficient_evidence, failed
    created_at = Column(DateTime, default=utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
