"""
KavachAI — Audit Service
Implements: FR-AUD-1 (log every query), FR-AUD-2 (immutable/append-only),
            workflow.md §4 (two-write pattern)

Two-write pattern:
  1. write on investigation creation (status: started)
  2. update on resolution (agents_invoked, verification_status, confidence)
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.sql_models import AuditLogEntry


async def create_audit_entry(
    db: AsyncSession,
    investigation_id: str,
    user: str,
    department: str,
    query: str,
) -> AuditLogEntry:
    """
    First write: create audit entry when investigation starts.
    Implements: FR-AUD-1, workflow.md §4 write-on-creation
    """
    entry = AuditLogEntry(
        investigation_id=investigation_id,
        user=user,
        department=department,
        query=query,
        status="started",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def resolve_audit_entry(
    db: AsyncSession,
    investigation_id: str,
    agents_invoked: list[str],
    verification_status: str | None,
    confidence: int | None,
    status: str,
) -> None:
    """
    Second write: update audit entry when investigation resolves.
    Implements: FR-AUD-1, workflow.md §4 write-on-resolution

    NOTE: This is the ONLY place an audit entry is modified after creation.
    FR-AUD-2: No DELETE or PATCH operations exist anywhere for this table.
    """
    result = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.investigation_id == investigation_id)
        .order_by(AuditLogEntry.created_at.desc())
    )
    entry = result.scalars().first()


    if entry:
        entry.agents_invoked = agents_invoked
        entry.verification_status = verification_status
        entry.confidence = confidence
        entry.status = status
        entry.resolved_at = datetime.now(timezone.utc)
        await db.commit()
