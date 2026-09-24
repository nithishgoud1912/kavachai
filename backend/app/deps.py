"""
KavachAI Backend — Shared FastAPI Dependencies
Provides: DB session, session auth (FR-ACC-1/2), and common dependency injection.
"""

from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Callable, Optional
from fastapi import Header, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.sql_models import Session as SessionModel, User, UserRole
from app.config import settings
from app.security import has_permission
from app.services.security_audit import append_security_event


@dataclass(frozen=True)
class Principal:
    """Authenticated local user plus fresh role assignments for authorization."""
    user_id: str
    username: str
    department: str
    clearance: str
    roles: tuple[str, ...]
    session_id: str


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

    # A password-authenticated session has no access until its MFA challenge is complete.
    if session.user_id and not getattr(session, "mfa_verified", False):
        raise HTTPException(status_code=401, detail="Multi-factor verification required")

    if session.user_id:
        user = await db.get(User, session.user_id)
        if not user or not user.is_active:
            raise HTTPException(401, "User account unavailable")
    elif not settings.ALLOW_DEMO_SESSIONS:
        raise HTTPException(401, "Authenticated user required")
    now = datetime.now(timezone.utc)
    last = session.last_seen_at or session.issued_at
    if last and (now - last.replace(tzinfo=timezone.utc)).total_seconds() > settings.SESSION_IDLE_MINUTES * 60:
        raise HTTPException(401, "Session idle timeout")
    session.last_seen_at = now
    await db.commit()
    return session


async def get_current_principal(
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> Principal:
    """Resolve the human identity and current roles behind a secure local session."""
    if not current_session.user_id:
        # Compatibility for the intentionally isolated hackathon flow. Production
        # disables its creation with ALLOW_DEMO_SESSIONS=false.
        if settings.ALLOW_DEMO_SESSIONS:
            return Principal(
                user_id=f"demo:{current_session.id}", username=current_session.name,
                department=current_session.department, clearance="internal",
                roles=("ai_workbench_user",), session_id=current_session.id,
            )
        raise HTTPException(status_code=401, detail="A production authenticated session is required")

    result = await db.execute(select(User).where(User.id == current_session.user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled or unavailable")

    role_result = await db.execute(select(UserRole.role).where(UserRole.user_id == user.id))
    roles = tuple(role_result.scalars().all())
    return Principal(
        user_id=user.id,
        username=user.username,
        department=user.department,
        clearance=user.clearance,
        roles=roles,
        session_id=current_session.id,
    )


def require_permission(permission: str) -> Callable:
    """Create a FastAPI dependency for a named, default-deny RBAC permission."""
    async def _require(principal: Principal = Depends(get_current_principal), db: AsyncSession = Depends(get_db)) -> Principal:
        if not has_permission(principal.roles, permission):
            await append_security_event(
                db, event_type="AUTHORIZATION_DENIED", outcome="denied",
                actor_user_id=principal.user_id, session_id=principal.session_id,
                department=principal.department, detail={"permission": permission},
            )
            raise HTTPException(status_code=403, detail="Not authorized")
        return principal
    return _require


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
