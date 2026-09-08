"""
KavachAI — Integration Tests: Workflow E (Out-of-Scope / Hallucination Refusal)
Implements: Phase 15 Acceptance Criterion #2, PRD §5, workflow.md §5

Verifies:
- Out-of-scope query ("What is the current price of crude oil?")
  triggers terminal status "insufficient_evidence", NOT a hallucinated guess.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import init_db


@pytest.mark.asyncio
async def test_workflow_e_out_of_scope_refusal():
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session
        sess_resp = await client.post("/api/v1/session", json={"name": "Rajesh", "department": "Finance"})
        assert sess_resp.status_code == 200
        session_id = sess_resp.json()["session_id"]

        # Start out-of-scope investigation
        inv_resp = await client.post("/api/v1/investigations", json={
            "query": "What is the current price of crude oil?",
            "session_id": session_id,
        })
        assert inv_resp.status_code == 202
        investigation_id = inv_resp.json()["investigation_id"]

        # Wait for background pipeline to complete
        import asyncio
        for _ in range(10):
            rep_resp = await client.get(f"/api/v1/investigations/{investigation_id}/report")
            if rep_resp.status_code in [404, 400]:
                # Insufficient evidence investigations do not have a report URL
                break
            await asyncio.sleep(0.3)

        # Confirm terminal status in DB
        from app.db.database import async_session
        from app.db.sql_models import Investigation
        from sqlalchemy import select

        async with async_session() as db:
            res = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
            inv = res.scalar_one()
            assert inv.status == "insufficient_evidence"
            assert inv.report is None
