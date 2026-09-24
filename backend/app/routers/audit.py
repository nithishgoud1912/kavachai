"""
KavachAI — Audit Log Router
Implements: FR-AUD-1 (query audit entries), FR-AUD-2 (append-only — NO delete/patch endpoint)
Endpoint: GET /audit-log (API_Reference.md §7)

IMPORTANT: This router exposes ONLY a GET endpoint. There is deliberately NO
DELETE, PATCH, or PUT endpoint for audit entries. This is FR-AUD-2.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.database import get_db
from app.db.sql_models import AuditLogEntry, AuditEvent, Session as SessionModel
from app.models.audit import AuditEntry, AuditLogResponse
from app.deps import Principal, get_current_session, require_permission

router = APIRouter(prefix="/api/v1", tags=["audit"])


@router.get("/audit-log", response_model=AuditLogResponse)
async def get_audit_log(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0, le=100000),
    current_session: SessionModel = Depends(get_current_session),
    _: Principal = Depends(require_permission("audit:read")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated audit log entries.
    Implements: FR-AUD-1, API_Reference.md §7

    FR-AUD-2: This is the ONLY endpoint for audit_log. No DELETE/PATCH exists by design.
    """
    legacy = (await db.execute(select(AuditLogEntry).order_by(desc(AuditLogEntry.created_at)).limit(offset+limit))).scalars().all()
    security = (await db.execute(select(AuditEvent).order_by(desc(AuditEvent.created_at)).limit(offset+limit))).scalars().all()
    entries = [AuditEntry(investigation_id=e.investigation_id, user=e.user, department=e.department,
                         query=e.query, agents_invoked=e.agents_invoked or [], verification_status=e.verification_status,
                         confidence=e.confidence, timestamp=(e.resolved_at or e.created_at).isoformat()) for e in legacy]
    entries.extend(AuditEntry(investigation_id=e.resource_id or e.id, user=e.actor_user_id or e.actor_service or "system",
                              department=e.department or "", query=f"{e.event_type}: {e.outcome}", agents_invoked=[],
                              verification_status=None, confidence=None, timestamp=e.created_at.isoformat()) for e in security)
    entries.sort(key=lambda e:e.timestamp, reverse=True)
    total = (await db.scalar(select(func.count(AuditLogEntry.id)))) + (await db.scalar(select(func.count(AuditEvent.id))))
    return AuditLogResponse(entries=entries[offset:offset+limit], total=total)
