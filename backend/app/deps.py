"""
KavachAI Backend — Shared FastAPI Dependencies
Provides: DB session, session auth (FR-ACC-1/2), and common dependency injection.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import Header, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.sql_models import Session as SessionModel


async def get_current_session(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> SessionModel:
    """
    Authenticate and validate incoming session.
    Supports:
      1. Authorization: Bearer <session_id>
      2. X-Session-ID: <session_id>
      3. Query parameter ?session_id=<session_id> (essential for SSE / EventSource & downloads)

    Validates:
      - Session exists in database
      - Session is not revoked
      - Session has not expired
    """
    token: Optional[str] = None

    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()
    elif x_session_id:
        token = x_session_id.strip()
    elif session_id:
        token = session_id.strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: No session token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(SessionModel).where(SessionModel.id == token))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid session ID")

    if getattr(session, "is_revoked", False):
        raise HTTPException(status_code=401, detail="Session has been revoked")

    if session.expires_at:
        now = datetime.now(timezone.utc)
        exp = session.expires_at if session.expires_at.tzinfo else session.expires_at.replace(tzinfo=timezone.utc)
        if now > exp:
            raise HTTPException(status_code=401, detail="Session has expired")

    return session


async def get_optional_session(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[SessionModel]:
    """Optional session authentication for non-blocking public / informational routes."""
    try:
        return await get_current_session(authorization, x_session_id, session_id, db)
    except HTTPException:
        return None
