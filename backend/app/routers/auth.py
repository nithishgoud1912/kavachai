"""Air-gapped local authentication and the five-role RBAC administration API."""

from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.db.sql_models import Session, User, UserRole
from app.deps import Principal, get_current_principal, get_current_session, require_permission
from app.models.auth import (
    AssignRolesRequest, AuthResponse, BootstrapRequest, CreateUserRequest,
    LoginRequest, MfaVerifyRequest, UserResponse,
)
from app.security import Role, generate_totp_secret, hash_password, normalise_role, verify_password, verify_totp
from app.services.security_audit import append_security_event

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

LOGIN_LOCK_MINUTES = 15
MAX_FAILED_LOGINS = 5


def _roles_for(user: User) -> list[str]:
    return sorted({assignment.role for assignment in user.roles})


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id, username=user.username, department=user.department,
        clearance=user.clearance, roles=_roles_for(user), is_active=user.is_active,
        mfa_enabled=user.mfa_enabled,
    )


async def _create_session(db: AsyncSession, user: User, *, mfa_verified: bool) -> Session:
    now = datetime.now(timezone.utc)
    session = Session(
        name=user.username, department=user.department, user_id=user.id,
        issued_at=now,
        # MFA challenges are deliberately short-lived; an authenticated session
        # remains bounded by the configured local maximum lifetime.
        expires_at=now + (timedelta(minutes=settings.ACCESS_TOKEN_TTL_MINUTES) if not mfa_verified else timedelta(hours=settings.SESSION_MAX_HOURS)),
        is_revoked=False, mfa_verified=mfa_verified, auth_method="password_totp",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
async def bootstrap_admin(body: BootstrapRequest, db: AsyncSession = Depends(get_db)):
    """Create the initial Admin once; only available with an out-of-band bootstrap secret."""
    count = await db.scalar(select(func.count(User.id)))
    if count:
        raise HTTPException(status_code=409, detail="Initial administrator already exists")
    if not settings.BOOTSTRAP_TOKEN or not hmac.compare_digest(body.bootstrap_token, settings.BOOTSTRAP_TOKEN):
        raise HTTPException(status_code=403, detail="Invalid bootstrap token")
    user = User(
        username=body.username.lower(), password_hash=hash_password(body.password),
        department=body.department, clearance="defence_sensitive", mfa_secret=generate_totp_secret(),
        mfa_enabled=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(user_id=user.id, role=Role.ADMIN.value, granted_by="bootstrap"))
    await db.commit()
    await db.refresh(user)
    await append_security_event(
        db, event_type="ADMIN_BOOTSTRAPPED", outcome="success", actor_user_id=user.id,
        department=user.department, resource_type="user", resource_id=user.id,
    )
    # This secret is shown only at bootstrap. Enrol it in a local authenticator immediately.
    return {"user": _user_response(user).model_dump(), "totp_secret": user.mfa_secret}


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Validate a local password, enforce lockout, then issue an MFA-pending session."""
    username = body.username.lower()
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    generic_failure = HTTPException(status_code=401, detail="Invalid username or password")
    if not user or not user.is_active:
        await append_security_event(db, event_type="LOGIN_FAILURE", outcome="denied", detail={"username": username})
        raise generic_failure
    if user.locked_until and (user.locked_until if user.locked_until.tzinfo else user.locked_until.replace(tzinfo=timezone.utc)) > now:
        await append_security_event(db, event_type="LOGIN_LOCKED", outcome="denied", actor_user_id=user.id, department=user.department)
        raise HTTPException(status_code=429, detail="Account is temporarily locked")
    if not verify_password(body.password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=LOGIN_LOCK_MINUTES)
            user.failed_login_count = 0
        await db.commit()
        await append_security_event(db, event_type="LOGIN_FAILURE", outcome="denied", actor_user_id=user.id, department=user.department)
        raise generic_failure
    user.failed_login_count = 0
    user.locked_until = None
    await db.commit()
    session = await _create_session(db, user, mfa_verified=not user.mfa_enabled)
    if user.mfa_enabled:
        await append_security_event(db, event_type="LOGIN_PASSWORD_ACCEPTED", outcome="pending_mfa", actor_user_id=user.id, session_id=session.id, department=user.department)
        return AuthResponse(session_id=session.id, mfa_required=True, user_id=user.id, username=user.username, department=user.department)
    await append_security_event(db, event_type="LOGIN_SUCCESS", outcome="success", actor_user_id=user.id, session_id=session.id, department=user.department)
    return AuthResponse(session_id=session.id, expires_at=session.expires_at.isoformat(), user_id=user.id, username=user.username, department=user.department, roles=_roles_for(user))


@router.post("/mfa/verify", response_model=AuthResponse)
async def verify_mfa(body: MfaVerifyRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == body.session_id))
    session = result.scalar_one_or_none()
    if not session or session.is_revoked or not session.user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication challenge")
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not user.mfa_secret or not verify_totp(user.mfa_secret, body.code):
        session.is_revoked = True
        await db.commit()
        await append_security_event(db, event_type="MFA_FAILURE", outcome="denied", actor_user_id=session.user_id, session_id=session.id)
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    session.mfa_verified = True
    session.expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_MAX_HOURS)
    await db.commit()
    await append_security_event(db, event_type="LOGIN_SUCCESS", outcome="success", actor_user_id=user.id, session_id=session.id, department=user.department)
    roles = (await db.execute(select(UserRole.role).where(UserRole.user_id == user.id))).scalars().all()
    return AuthResponse(session_id=session.id, expires_at=session.expires_at.isoformat(), user_id=user.id, username=user.username, department=user.department, roles=roles)


@router.get("/me", response_model=UserResponse)
async def me(principal: Principal = Depends(get_current_principal), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == principal.user_id))).scalar_one()
    return _user_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(session: Session = Depends(get_current_session), db: AsyncSession = Depends(get_db)):
    session.is_revoked = True
    await db.commit()
    await append_security_event(db, event_type="LOGOUT", outcome="success", actor_user_id=session.user_id, session_id=session.id, department=session.department)


@router.get("/users", response_model=list[UserResponse])
async def list_users(_: Principal = Depends(require_permission("users:manage")), db: AsyncSession = Depends(get_db)):
    users = (await db.execute(select(User).order_by(User.username))).scalars().all()
    return [_user_response(user) for user in users]


@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    principal: Principal = Depends(require_permission("users:manage")),
    db: AsyncSession = Depends(get_db),
):
    if (await db.execute(select(User).where(User.username == body.username.lower()))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")
    try:
        roles = [normalise_role(role).value for role in body.roles]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    user = User(username=body.username.lower(), password_hash=hash_password(body.password), department=body.department,
                clearance=body.clearance, mfa_secret=generate_totp_secret(), mfa_enabled=True)
    db.add(user)
    await db.flush()
    for role in sorted(set(roles)):
        db.add(UserRole(user_id=user.id, role=role, granted_by=principal.user_id))
    await db.commit()
    await db.refresh(user)
    await append_security_event(db, event_type="USER_CREATED", outcome="success", actor_user_id=principal.user_id,
        session_id=principal.session_id, department=user.department, resource_type="user", resource_id=user.id,
        detail={"roles": roles})
    return {"user": _user_response(user).model_dump(), "totp_secret": user.mfa_secret}


@router.put("/users/{user_id}/roles", response_model=UserResponse)
async def assign_roles(
    user_id: str, body: AssignRolesRequest,
    principal: Principal = Depends(require_permission("roles:manage")),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        roles = sorted({normalise_role(role).value for role in body.roles})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    old_roles = list((await db.execute(select(UserRole).where(UserRole.user_id == user.id))).scalars().all())
    for assignment in old_roles:
        await db.delete(assignment)
    for role in roles:
        db.add(UserRole(user_id=user.id, role=role, granted_by=principal.user_id))
    await db.commit()
    await db.refresh(user)
    await append_security_event(db, event_type="ROLE_ASSIGNMENT", outcome="success", actor_user_id=principal.user_id,
        session_id=principal.session_id, resource_type="user", resource_id=user.id, detail={"roles": roles})
    return _user_response(user)
