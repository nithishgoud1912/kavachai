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


class User(Base):
    """Locally authenticated human user. Password hashes are never returned by APIs."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    department = Column(String, nullable=False)
    clearance = Column(String, nullable=False, default="internal")
    is_active = Column(Boolean, nullable=False, default=True)
    mfa_secret = Column(String, nullable=True)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    failed_login_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", lazy="selectin")


class UserRole(Base):
    """Many-to-one role assignments; role names are constrained in application policy."""
    __tablename__ = "user_roles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    granted_by = Column(String, nullable=True)
    granted_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="roles")

    __table_args__ = (Index("ix_user_roles_user_role", "user_id", "role", unique=True),)


# --- FR-ACC-1/2: Sessions ---
class Session(Base):
    """Lightweight demo session (FR-ACC-1)."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)  # FR-ACC-2: department for permission-aware retrieval
    issued_at = Column(DateTime, default=utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=utcnow, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    mfa_verified = Column(Boolean, default=True, nullable=False)
    auth_method = Column(String, nullable=True)

    # Relationships
    investigations = relationship("Investigation", back_populates="session")
    conversations = relationship("Conversation", back_populates="session")
    documents = relationship("Document", back_populates="session")  # Task 3.1
    datasets = relationship("Dataset", back_populates="session")    # Task 3.1


class AuditEvent(Base):
    """Append-only security event. No update/delete helper is intentionally provided."""
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String, nullable=False, index=True)
    outcome = Column(String, nullable=False)
    actor_user_id = Column(String, nullable=True, index=True)
    actor_service = Column(String, nullable=True)
    session_id = Column(String, nullable=True, index=True)
    department = Column(String, nullable=True)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    classification = Column(String, nullable=True)
    detail = Column(JSON, default=dict)
    previous_event_hash = Column(String, nullable=True)
    event_hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)

    __table_args__ = (Index("ix_audit_events_resource", "resource_type", "resource_id"),)


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
    classification = Column(String, nullable=False, default="internal")
    department_scope = Column(String, nullable=True)  # FR-RAG-2: permission-aware retrieval
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)  # Task 3.1: session ownership
    ingested_at = Column(DateTime, default=utcnow, nullable=False)
    source_id = Column(String, nullable=False, unique=True)  # maps to object store key

    # Relationships
    session = relationship("Session", back_populates="documents")  # Task 3.1

    __table_args__ = (
        Index("ix_documents_equipment", "equipment_ids"),
        Index("ix_documents_type", "document_type"),
        Index("ix_documents_session", "session_id"),
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
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)  # Task 3.1: session ownership
    ingested_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="datasets")  # Task 3.1

    __table_args__ = (
        Index("ix_datasets_session", "session_id"),
    )


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
    events = Column(JSON, default=list)  # SSE streaming timeline events for reconnection
    attachments = Column(JSON, default=list)  # uploaded files and folders for this investigation
    created_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="investigations")
    conversations = relationship("Conversation", back_populates="investigation")

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


# --- Chat: Multi-Turn Conversations ---
class Conversation(Base):
    """
    A chat conversation — either general-purpose AI chat or
    report-grounded follow-up tied to a specific investigation.
    """
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    user = Column(String, nullable=False)
    department = Column(String, nullable=False)
    title = Column(String, nullable=False, default="New Chat")
    type = Column(String, nullable=False, default="general")  # "general" | "report"
    investigation_id = Column(String, ForeignKey("investigations.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="conversations")
    investigation = relationship("Investigation", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation",
                           order_by="ChatMessage.created_at")

    __table_args__ = (
        Index("ix_conversations_session", "session_id"),
        Index("ix_conversations_type", "type"),
        Index("ix_conversations_investigation", "investigation_id"),
    )


class ChatMessage(Base):
    """A single message in a conversation."""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    attachments = Column(JSON, default=list)  # [{filename, url, type, extracted_text}]
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_conversation", "conversation_id"),
    )


class WorkbenchJob(Base):
    __tablename__ = "workbench_jobs"
    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="queued")
    payload = Column(JSON, nullable=False, default=dict)
    events = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String, primary_key=True)
    value = Column(JSON, nullable=False)
