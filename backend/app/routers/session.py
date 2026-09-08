"""
KavachAI — Session Router
Implements: FR-ACC-1 (capture name + department), FR-ACC-2 (department parameter),
            Session Expiry & Revocation
Endpoints: API_Reference.md §2
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.sql_models import Session as SessionModel
from app.models.session import (
    SessionCreate,
    SessionResponse,
    SessionRevokeRequest,
    SessionRevokeResponse,
)
from app.deps import get_current_session

router = APIRouter(prefix="/api/v1", tags=["session"])

# Default session duration: 24 hours
DEFAULT_SESSION_TTL_HOURS = 24


@router.post("/session", response_model=SessionResponse)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a lightweight session with 24-hour expiration.
    Implements: FR-ACC-1, FR-ACC-2
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=DEFAULT_SESSION_TTL_HOURS)

    session = SessionModel(
        name=body.name,
        department=body.department,
        issued_at=now,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        session_id=session.id,
        name=session.name,
        department=session.department,
        issued_at=session.issued_at.isoformat() + "Z",
        expires_at=session.expires_at.isoformat() + "Z" if session.expires_at else None,
    )


@router.get("/session/me", response_model=SessionResponse)
async def get_my_session(current_session: SessionModel = Depends(get_current_session)):
    """Return the currently authenticated session details."""
    return SessionResponse(
        session_id=current_session.id,
        name=current_session.name,
        department=current_session.department,
        issued_at=current_session.issued_at.isoformat() + "Z",
        expires_at=current_session.expires_at.isoformat() + "Z" if current_session.expires_at else None,
    )


@router.post("/session/revoke", response_model=SessionRevokeResponse)
async def revoke_session(
    body: SessionRevokeRequest = None,
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke a session (defaults to current session if no session_id specified).
    """
    target_id = body.session_id if (body and body.session_id) else current_session.id

    result = await db.execute(select(SessionModel).where(SessionModel.id == target_id))
    session_to_revoke = result.scalar_one_or_none()

    if not session_to_revoke:
        raise HTTPException(status_code=404, detail="Session not found")

    session_to_revoke.is_revoked = True
    await db.commit()

    return SessionRevokeResponse(
        session_id=target_id,
        revoked=True,
        message="Session has been successfully revoked.",
    )
