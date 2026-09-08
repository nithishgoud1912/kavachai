"""
KavachAI — Audit Service
Implements: FR-AUD-1 (log every query), FR-AUD-2 (immutable/append-only WORM pattern),
            workflow.md §4 (two-write pattern)

Two-write pattern:
  1. write on investigation creation (status: started)
  2. finalize on resolution (agents_invoked, verification_status, confidence)
     - Strictly protected: once finalized, records can NEVER be mutated again.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.sql_models import AuditLogEntry

logger = logging.getLogger(__name__)


async def create_audit_entry(
    db: AsyncSession,
    investigation_id: str,
    user: str,
    department: str,
    query: str,
) -> AuditLogEntry:
    """
    First write: create immutable audit entry when investigation starts.
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
    Second write: finalize audit entry when investigation resolves.
    Implements: FR-AUD-1, workflow.md §4 write-on-resolution

    WORM Enforcement (FR-AUD-2):
    - Only unfinalized entries (status == 'started') may transition to completed/failed state.
    - Once resolved, any attempt to overwrite or mutate the entry is strictly rejected.
    - Immutable columns (user, department, query, created_at) are never modified.
    """
    result = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.investigation_id == investigation_id)
        .order_by(AuditLogEntry.created_at.desc())
    )
    entry = result.scalars().first()

    if not entry:
        logger.warning("Audit resolution called for non-existent investigation: %s", investigation_id)
        return

    # Enforce WORM: already finalized records cannot be altered
    if entry.status != "started":
        logger.warning(
            "WORM Violation attempt: Audit entry %s already finalized with status %s. Modification rejected.",
            entry.id,
            entry.status,
        )
        return

    # Perform one-time state finalization
    entry.agents_invoked = list(agents_invoked) if agents_invoked else []
    entry.verification_status = verification_status
    entry.confidence = confidence
    entry.status = status
    entry.resolved_at = datetime.now(timezone.utc)
    await db.commit()
