"""
KavachAI — Audit Log Router
Implements: FR-AUD-1 (query audit entries), FR-AUD-2 (append-only — NO delete/patch endpoint)
Endpoint: GET /audit-log (API_Reference.md §7)

IMPORTANT: This router exposes ONLY a GET endpoint. There is deliberately NO
DELETE, PATCH, or PUT endpoint for audit entries. This is FR-AUD-2.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.database import get_db
from app.db.sql_models import AuditLogEntry
from app.models.audit import AuditEntry, AuditLogResponse

router = APIRouter(prefix="/api/v1", tags=["audit"])


@router.get("/audit-log", response_model=AuditLogResponse)
async def get_audit_log(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated audit log entries.
    Implements: FR-AUD-1, API_Reference.md §7

    FR-AUD-2: This is the ONLY endpoint for audit_log. No DELETE/PATCH exists by design.
    """
    # Get total count
    count_result = await db.execute(select(func.count(AuditLogEntry.id)))
    total = count_result.scalar() or 0

    # Get entries (reverse chronological)
    result = await db.execute(
        select(AuditLogEntry)
        .order_by(desc(AuditLogEntry.created_at))
        .offset(offset)
        .limit(limit)
    )
    entries = result.scalars().all()

    return AuditLogResponse(
        entries=[
            AuditEntry(
                investigation_id=e.investigation_id,
                user=e.user,
                department=e.department,
                query=e.query,
                agents_invoked=e.agents_invoked or [],
                verification_status=e.verification_status,
                confidence=e.confidence,
                timestamp=(e.resolved_at or e.created_at).isoformat() + "Z",
            )
            for e in entries
        ],
        total=total,
    )
