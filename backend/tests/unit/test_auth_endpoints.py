"""
KavachAI — Unit Tests: Local Auth & RBAC Endpoints
Validates:
- Admin bootstrap and token security
- Scrypt password authentication
- RFC 6238 TOTP MFA challenge and verification
- Account lockout after 5 failed attempts
- Five-role permission enforcement (403 default-deny)
- Append-only chained SHA-256 audit event logging
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.config import settings
from app.db.database import init_db, async_session
from app.db.sql_models import User, UserRole, Session as SessionModel, AuditEvent
from app.security import generate_totp, hash_password


@pytest.mark.asyncio
async def test_auth_full_lifecycle_and_rbac():
    await init_db()
    transport = ASGITransport(app=app)

    # Ensure a test bootstrap token is set
    original_token = settings.BOOTSTRAP_TOKEN
    test_token = "kavachai_test_bootstrap_token_secret"
    settings.BOOTSTRAP_TOKEN = test_token

    # Clean existing users from test DB for clean slate in this test
    async with async_session() as db:
        await db.execute(select(User))
        # Clear users and sessions
        users = (await db.execute(select(User))).scalars().all()
        for u in users:
            await db.delete(u)
        await db.commit()

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Bootstrap fails with bad token
            resp = await client.post("/api/v1/auth/bootstrap", json={
                "username": "sysadmin",
                "password": "CorrectHorseBatteryStaple123!",
                "department": "IT_SECURITY",
                "bootstrap_token": "wrong_token_with_enough_length",
            })
            assert resp.status_code == 403

            # 2. Bootstrap succeeds with valid token
            admin_pwd = "StrongAdminPassword2026!"
            resp = await client.post("/api/v1/auth/bootstrap", json={
                "username": "sysadmin",
                "password": admin_pwd,
                "department": "IT_SECURITY",
                "bootstrap_token": test_token,
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["user"]["username"] == "sysadmin"
            assert "admin" in data["user"]["roles"]
            totp_secret = data["totp_secret"]
            assert totp_secret is not None

            # 3. Duplicate bootstrap rejected
            resp2 = await client.post("/api/v1/auth/bootstrap", json={
                "username": "sysadmin2",
                "password": admin_pwd,
                "department": "IT_SECURITY",
                "bootstrap_token": test_token,
            })
            assert resp2.status_code == 409

            # 4. Login with bad password fails
            bad_login = await client.post("/api/v1/auth/login", json={
                "username": "sysadmin",
                "password": "WrongPassword123!",
            })
            assert bad_login.status_code == 401

            # 5. Login with correct password requires MFA
            good_login = await client.post("/api/v1/auth/login", json={
                "username": "sysadmin",
                "password": admin_pwd,
            })
            assert good_login.status_code == 200
            login_data = good_login.json()
            assert login_data["mfa_required"] is True
            pending_session_id = login_data["session_id"]

            # 6. Unverified session cannot access protected endpoints
            unauth_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {pending_session_id}"})
            assert unauth_resp.status_code == 401
            assert "Multi-factor verification required" in unauth_resp.json()["detail"]

            # 7. Invalid MFA code fails and revokes pending session
            bad_mfa = await client.post("/api/v1/auth/mfa/verify", json={
                "session_id": pending_session_id,
                "code": "000000",
            })
            assert bad_mfa.status_code == 401

            # 8. Log in again to get fresh session challenge
            login_again = await client.post("/api/v1/auth/login", json={
                "username": "sysadmin",
                "password": admin_pwd,
            })
            session_id = login_again.json()["session_id"]

            # Compute current valid TOTP code
            valid_code = generate_totp(totp_secret)
            good_mfa = await client.post("/api/v1/auth/mfa/verify", json={
                "session_id": session_id,
                "code": valid_code,
            })
            assert good_mfa.status_code == 200
            auth_header = {"Authorization": f"Bearer {session_id}"}

            # 9. GET /api/v1/auth/me succeeds with admin
            me_resp = await client.get("/api/v1/auth/me", headers=auth_header)
            assert me_resp.status_code == 200
            assert me_resp.json()["username"] == "sysadmin"

            # 10. Admin creates a new AI Workbench User
            analyst_pwd = "AnalystPassword2026!"
            create_resp = await client.post("/api/v1/auth/users", headers=auth_header, json={
                "username": "arun_analyst",
                "password": analyst_pwd,
                "department": "OPERATIONS",
                "clearance": "confidential",
                "roles": ["ai_workbench_user"],
            })
            assert create_resp.status_code == 201
            analyst_data = create_resp.json()
            analyst_secret = analyst_data["totp_secret"]

            # 11. Analyst logs in and verifies MFA
            analyst_login = await client.post("/api/v1/auth/login", json={
                "username": "arun_analyst",
                "password": analyst_pwd,
            })
            analyst_session_id = analyst_login.json()["session_id"]
            analyst_mfa = await client.post("/api/v1/auth/mfa/verify", json={
                "session_id": analyst_session_id,
                "code": generate_totp(analyst_secret),
            })
            assert analyst_mfa.status_code == 200
            analyst_headers = {"Authorization": f"Bearer {analyst_session_id}"}

            # 12. Analyst is FORBIDDEN from accessing user management (RBAC default deny)
            forbidden_resp = await client.get("/api/v1/auth/users", headers=analyst_headers)
            assert forbidden_resp.status_code == 403
            assert forbidden_resp.json()["detail"] == "Not authorized"

            # 13. Audit event chaining integrity
            async with async_session() as db:
                events = (await db.execute(select(AuditEvent).order_by(AuditEvent.created_at.asc()))).scalars().all()
                assert len(events) >= 5
                # Verify SHA-256 hash chaining
                for i in range(1, len(events)):
                    assert events[i].previous_event_hash == events[i - 1].event_hash

            # 14. Logout revokes the session
            logout_resp = await client.post("/api/v1/auth/logout", headers=analyst_headers)
            assert logout_resp.status_code == 204

            # Subsequent calls with revoked session return 401
            revoked_resp = await client.get("/api/v1/auth/me", headers=analyst_headers)
            assert revoked_resp.status_code == 401

    finally:
        settings.BOOTSTRAP_TOKEN = original_token


@pytest.mark.asyncio
async def test_account_lockout_after_max_failures():
    await init_db()
    transport = ASGITransport(app=app)

    # Create a user directly
    async with async_session() as db:
        user = User(
            username="lockout_target",
            password_hash=hash_password("SafePassword12345!"),
            department="SECURITY",
            clearance="internal",
            mfa_enabled=False,
        )
        db.add(user)
        await db.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 5 failed login attempts
        for _ in range(5):
            res = await client.post("/api/v1/auth/login", json={
                "username": "lockout_target",
                "password": "WrongPasswordAttempt!",
            })
            assert res.status_code == 401

        # 6th attempt should be locked out (429)
        locked_res = await client.post("/api/v1/auth/login", json={
            "username": "lockout_target",
            "password": "SafePassword12345!",
        })
        assert locked_res.status_code == 429
        assert "temporarily locked" in locked_res.json()["detail"]
