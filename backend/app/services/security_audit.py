"""Append-only security audit writer with a local tamper-evident hash chain."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sql_models import AuditEvent


async def append_security_event(
    db: AsyncSession,
    *,
    event_type: str,
    outcome: str,
    actor_user_id: str | None = None,
    actor_service: str | None = None,
    session_id: str | None = None,
    department: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    classification: str | None = None,
    detail: dict[str, Any] | None = None,
) -> AuditEvent:
    """Append, never update, a security event and link it to its predecessor."""
    # SQLite serializes writers before reading the predecessor, including across workers.
    await db.commit()
    await db.execute(text("BEGIN IMMEDIATE"))
    if session_id:
        session_id = hashlib.sha256(session_id.encode()).hexdigest()
    previous = await db.execute(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(1))
    previous_hash = previous.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    safe_detail = detail or {}
    envelope = {
        "event_type": event_type, "outcome": outcome, "actor_user_id": actor_user_id,
        "actor_service": actor_service, "session_id": session_id, "department": department,
        "resource_type": resource_type, "resource_id": resource_id,
        "classification": classification, "detail": safe_detail,
        "previous_event_hash": previous_hash.event_hash if previous_hash else None,
        "created_at": now.isoformat(),
    }
    digest = hashlib.sha256(json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    event = AuditEvent(**{**envelope, "created_at": now, "event_hash": digest})
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
