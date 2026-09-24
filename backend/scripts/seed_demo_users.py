"""
KavachAI — Seed Demo Users Script
Populates the database with canonical users for the five approved roles:
1. Admin (defence_sensitive)
2. AI Workbench User (confidential)
3. Knowledge Base Manager (restricted)
4. Reviewer / Approver (restricted)
5. Auditor (confidential)
Plus an Admin with MFA enabled to demonstrate TOTP challenge.
"""

import asyncio
import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import select
from app.db.database import init_db, async_session
from app.db.sql_models import User, UserRole
from app.security import Role, hash_password, generate_totp_secret

DEMO_USERS = [
    {
        "username": "admin",
        "password": "KavachAI_Admin_2026!",
        "department": "IT_SECURITY",
        "clearance": "defence_sensitive",
        "roles": [Role.ADMIN.value],
        "mfa_enabled": False,
        "mfa_secret": "JBSWY3DPEHPK3PXP",
    },
    {
        "username": "admin_mfa",
        "password": "KavachAI_AdminMFA_2026!",
        "department": "IT_SECURITY",
        "clearance": "defence_sensitive",
        "roles": [Role.ADMIN.value],
        "mfa_enabled": True,
        "mfa_secret": "JBSWY3DPEHPK3PXP",  # Standard base32 test key
    },
    {
        "username": "analyst",
        "password": "KavachAI_Analyst_2026!",
        "department": "OPERATIONS",
        "clearance": "confidential",
        "roles": [Role.WORKBENCH_USER.value],
        "mfa_enabled": False,
        "mfa_secret": "MZXW6YTBOJUW4ZY2",
    },
    {
        "username": "kbmanager",
        "password": "KavachAI_KbManager_2026!",
        "department": "REFINERY",
        "clearance": "restricted",
        "roles": [Role.KNOWLEDGE_BASE_MANAGER.value],
        "mfa_enabled": False,
        "mfa_secret": "NB2HI4DTHIXS653X",
    },
    {
        "username": "reviewer",
        "password": "KavachAI_Reviewer_2026!",
        "department": "HSE",
        "clearance": "restricted",
        "roles": [Role.REVIEWER_APPROVER.value],
        "mfa_enabled": False,
        "mfa_secret": "OBXXE2LTMVRXEZLU",
    },
    {
        "username": "auditor",
        "password": "KavachAI_Auditor_2026!",
        "department": "AUDIT",
        "clearance": "confidential",
        "roles": [Role.AUDITOR.value],
        "mfa_enabled": False,
        "mfa_secret": "PBZXG5DJONSWG4TF",
    },
    {
        "username": "operations_lead",
        "password": "KavachAI_Analyst_2026!",
        "department": "OPERATIONS",
        "clearance": "confidential",
        "roles": [Role.WORKBENCH_USER.value],
        "mfa_enabled": False,
        "mfa_secret": "MZXW6YTBOJUW4ZY2",
    },
    {
        "username": "maint_eng",
        "password": "KavachAI_Analyst_2026!",
        "department": "MAINTENANCE",
        "clearance": "confidential",
        "roles": [Role.WORKBENCH_USER.value],
        "mfa_enabled": False,
        "mfa_secret": "MZXW6YTBOJUW4ZY2",
    },
    {
        "username": "safety_reviewer",
        "password": "KavachAI_Reviewer_2026!",
        "department": "HSE",
        "clearance": "restricted",
        "roles": [Role.REVIEWER_APPROVER.value],
        "mfa_enabled": False,
        "mfa_secret": "OBXXE2LTMVRXEZLU",
    },
    {
        "username": "process_eng",
        "password": "KavachAI_KbManager_2026!",
        "department": "REFINERY",
        "clearance": "restricted",
        "roles": [Role.KNOWLEDGE_BASE_MANAGER.value],
        "mfa_enabled": False,
        "mfa_secret": "NB2HI4DTHIXS653X",
    },
]


async def seed():
    await init_db()
    async with async_session() as db:
        for u_data in DEMO_USERS:
            # Check if user already exists
            existing = (await db.execute(select(User).where(User.username == u_data["username"]))).scalar_one_or_none()
            if existing:
                # Update password and roles
                existing.password_hash = hash_password(u_data["password"])
                existing.department = u_data["department"]
                existing.clearance = u_data["clearance"]
                existing.mfa_enabled = u_data["mfa_enabled"]
                existing.mfa_secret = u_data["mfa_secret"]
                existing.failed_login_count = 0
                existing.locked_until = None
                existing.is_active = True
                # Remove existing roles
                from sqlalchemy import delete
                await db.execute(delete(UserRole).where(UserRole.user_id == existing.id))
                await db.flush()
                user_id = existing.id
            else:
                user = User(
                    username=u_data["username"],
                    password_hash=hash_password(u_data["password"]),
                    department=u_data["department"],
                    clearance=u_data["clearance"],
                    mfa_enabled=u_data["mfa_enabled"],
                    mfa_secret=u_data["mfa_secret"],
                    is_active=True,
                )
                db.add(user)
                await db.flush()
                user_id = user.id

            for role in u_data["roles"]:
                db.add(UserRole(user_id=user_id, role=role, granted_by="seed_script"))
            await db.flush()

        await db.commit()
    print("Successfully seeded all 5 canonical demo users:")
    for u in DEMO_USERS:
        print(f"  - {u['username']} ({', '.join(u['roles'])}) [Dept: {u['department']}, Clearance: {u['clearance']}, MFA: {u['mfa_enabled']}]")


if __name__ == "__main__":
    asyncio.run(seed())
