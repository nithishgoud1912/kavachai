"""
KavachAI — Unit Tests: Audit Service & Router
Implements: Phase 12 DoD, FR-AUD-1..2, workflow.md §4 (Two-Write Pattern)

Verifies:
- Two-write pattern: write on creation (started), update on resolution
- Append-only integrity: router defines ONLY GET, no DELETE / PATCH / PUT exists
"""

import pytest
from app.db.database import init_db, async_session
from app.db.sql_models import AuditLogEntry
from app.services import audit_service
from app.routers import audit as audit_router
from sqlalchemy import select


@pytest.mark.asyncio
async def test_audit_two_write_pattern():
    """Test two-write audit pattern per workflow.md §4."""
    import uuid
    await init_db()
    inv_id = f"test_inv_{uuid.uuid4().hex[:8]}"

    async with async_session() as db:
        # 1. First write on creation
        entry = await audit_service.create_audit_entry(
            db=db,
            investigation_id=inv_id,
            user="Priya",
            department="HSE",
            query="Test query for pump audit",
        )

        res = await db.execute(select(AuditLogEntry).where(AuditLogEntry.id == entry.id))
        entry_row = res.scalar_one()
        assert entry_row.status == "started"
        assert entry_row.query == "Test query for pump audit"
        assert not entry_row.agents_invoked

        # 2. Second write on resolution
        await audit_service.resolve_audit_entry(
            db=db,
            investigation_id=inv_id,
            status="complete",
            agents_invoked=["planner", "document_agent", "data_agent"],
            verification_status="verified",
            confidence=91,
        )


        res2 = await db.execute(select(AuditLogEntry).where(AuditLogEntry.id == entry.id))
        updated = res2.scalar_one()
        assert updated.status == "complete"
        assert updated.verification_status == "verified"
        assert updated.confidence == 91
        assert "document_agent" in updated.agents_invoked



def test_audit_router_has_no_mutation_endpoints():
    """Test FR-AUD-2: Audit router exposes ONLY GET, no DELETE/PATCH/PUT."""
    routes = audit_router.router.routes
    methods = [method for r in routes for method in r.methods]

    assert "GET" in methods
    assert "DELETE" not in methods
    assert "PATCH" not in methods
    assert "PUT" not in methods
