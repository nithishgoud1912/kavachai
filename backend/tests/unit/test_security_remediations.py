"""
KavachAI — Unit Tests: Security & Architectural Remediations
Validates fixes for all 11 vulnerabilities:
- Session authentication on protected routers (deps.py)
- Session expiry and revocation
- TabularStore SQL injection sanitization and async operations
- Audit log WORM immutability
- Equipment graph dynamic additions and cycle-safety
- Export router path traversal prevention
- ModelRouter offline fallback generalization
"""

import pytest
import pandas as pd
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import init_db, async_session
from app.db.sql_models import Session as SessionModel, AuditLogEntry
from sqlalchemy import select
from app.db.tabular_store import tabular_store
from app.db.graph_store import graph_store
from app.services import audit_service
from app.orchestrator.model_router import model_router


@pytest.mark.asyncio
async def test_authentication_enforced_on_endpoints():
    """Verify that unauthenticated requests to protected endpoints return 401."""
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Knowledge Base Summary
        resp = await client.get("/api/v1/knowledge-base/summary")
        assert resp.status_code == 401
        assert "Authentication required" in resp.json()["detail"]

        # Audit Log
        resp = await client.get("/api/v1/audit-log")
        assert resp.status_code == 401

        # Evidence
        resp = await client.get("/api/v1/evidence/doc_test")
        assert resp.status_code == 401

        # Investigations create
        resp = await client.post("/api/v1/investigations", json={"query": "test"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_session_expiry_and_revocation():
    """Verify session expiry and revocation return 401."""
    await init_db()
    transport = ASGITransport(app=app)

    async with async_session() as db:
        # Create an expired session
        expired_session = SessionModel(
            name="ExpiredUser",
            department="Operations",
            issued_at=datetime.now(timezone.utc) - timedelta(hours=48),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=24),
            is_revoked=False,
        )
        # Create a revoked session
        revoked_session = SessionModel(
            name="RevokedUser",
            department="HSE",
            issued_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_revoked=True,
        )
        db.add_all([expired_session, revoked_session])
        await db.commit()
        await db.refresh(expired_session)
        await db.refresh(revoked_session)

        exp_id = expired_session.id
        rev_id = revoked_session.id

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Expired session request
        resp = await client.get(
            "/api/v1/knowledge-base/summary",
            headers={"Authorization": f"Bearer {exp_id}"},
        )
        assert resp.status_code == 401
        assert "Session has expired" in resp.json()["detail"]

        # Revoked session request
        resp = await client.get(
            "/api/v1/knowledge-base/summary",
            headers={"Authorization": f"Bearer {rev_id}"},
        )
        assert resp.status_code == 401
        assert "Session has been revoked" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_session_creation_sets_expiry():
    """Verify POST /session sets expires_at."""
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/session",
            json={"name": "Alice", "department": "Maintenance"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "expires_at" in data
        assert data["expires_at"] is not None

        # Verify revoke endpoint
        session_id = data["session_id"]
        revoke_resp = await client.post(
            "/api/v1/session/revoke",
            headers={"Authorization": f"Bearer {session_id}"},
        )
        assert revoke_resp.status_code == 200
        assert revoke_resp.json()["revoked"] is True


def test_tabular_store_sql_injection_prevention():
    """Verify that malicious table names are strictly rejected in TabularStore."""
    # Malicious injection table names
    bad_tables = [
        "dataset_123; DROP TABLE users;--",
        "dataset_123' OR '1'='1",
        "dataset/[test]",
        "dataset 123",
        "",
    ]
    for bad in bad_tables:
        with pytest.raises(ValueError):
            tabular_store.query_by_equipment(bad, "P-102")


@pytest.mark.asyncio
async def test_tabular_store_async_methods():
    """Verify that TabularStore non-blocking async operations work correctly."""
    df = pd.DataFrame({
        "timestamp": ["2026-01-01 00:00:00", "2026-01-01 01:00:00"],
        "equipment_id": ["E-999", "E-999"],
        "metric": ["temperature", "temperature"],
        "value": [85.5, 92.0],
        "unit": ["C", "C"],
    })
    res = await tabular_store.async_ingest_dataframe("test_async_ds", df)
    table_name = res["table_name"]

    query_df = await tabular_store.async_query_by_equipment(table_name, "E-999", "temperature")
    assert len(query_df) == 2

    metrics = await tabular_store.async_get_distinct_metrics(table_name, "E-999")
    assert "temperature" in metrics


@pytest.mark.asyncio
async def test_audit_log_worm_immutability():
    """Verify that once an audit entry is resolved, subsequent mutation attempts are rejected."""
    import uuid
    await init_db()
    inv_id = f"test_inv_worm_guard_{uuid.uuid4().hex[:8]}"

    async with async_session() as db:
        # First write
        entry = await audit_service.create_audit_entry(
            db=db,
            investigation_id=inv_id,
            user="Tester",
            department="Reliability",
            query="Test query",
        )
        assert entry.status == "started"

        # Second write (resolution)
        await audit_service.resolve_audit_entry(
            db=db,
            investigation_id=inv_id,
            agents_invoked=["planner"],
            verification_status="verified",
            confidence=95,
            status="completed",
        )

        # Attempt forbidden third write (tamper attempt)
        await audit_service.resolve_audit_entry(
            db=db,
            investigation_id=inv_id,
            agents_invoked=["tampered_agent"],
            verification_status="unverified",
            confidence=10,
            status="failed",
        )

        # Confirm the record was NOT tampered with
        result = await db.execute(
            select(AuditLogEntry).where(AuditLogEntry.investigation_id == inv_id)
        )
        current = result.scalar_one()
        assert current.status == "completed"
        assert current.confidence == 95
        assert current.verification_status == "verified"
        assert current.agents_invoked == ["planner"]


def test_graph_store_add_and_cycle_safety():
    """Verify dynamic node/edge addition and cycle-safe traversal."""
    # Add new equipment nodes
    graph_store.add_node("TX-100", equipment_type="turbine", label="Gas Turbine TX-100")
    graph_store.add_node("HX-200", equipment_type="heat_exchanger", label="Heat Exchanger HX-200")
    graph_store.add_edge("TX-100", "HX-200", relationship="exhausts_to")

    assert graph_store.equipment_exists("TX-100")
    assert "HX-200" in graph_store.get_connections("TX-100")

    # Test cycle safety: create a circular reference A -> B -> C -> A
    graph_store.add_edge("CYC-A", "CYC-B", relationship="feeds")
    graph_store.add_edge("CYC-B", "CYC-C", relationship="feeds")
    graph_store.add_edge("CYC-C", "CYC-A", relationship="feeds")

    # Traversal MUST terminate and not hang indefinitely
    chain = graph_store.get_connection_chain("CYC-A")
    assert len(chain) >= 1
    assert "CYC-A" in chain


@pytest.mark.asyncio
async def test_export_path_traversal_prevention():
    """Verify path traversal attacks on /exports/{filename} are rejected."""
    await init_db()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Malicious filename patterns
        bad_filenames = [
            "../../etc/passwd",
            "..%2F..%2Fwindows%2Fwin.ini",
            "exp_test/../../something.pdf",
            "malicious.exe",
            "exp_1234.txt",
        ]
        for bad in bad_filenames:
            resp = await client.get(f"/api/v1/exports/{bad}")
            assert resp.status_code in [400, 404]


def test_model_router_offline_generic_synthesis_and_verification():
    """Verify that offline model router generates valid JSON with required schema for generic prompts."""
    # Generic synthesis prompt
    synth_prompt = "Synthesize findings for Tank T-300 with evidence doc_999."
    synth_resp = model_router._offline_generate(synth_prompt, task_type="synthesis", fmt="json")
    import json
    parsed_synth = json.loads(synth_resp)
    assert "findings" in parsed_synth
    assert len(parsed_synth["findings"]) >= 1
    assert "condition_summary" in parsed_synth

    # Generic verification prompt
    ver_prompt = 'Verify findings for Compressor C-401 with {"id": "f1"}'
    ver_resp = model_router._offline_generate(ver_prompt, task_type="verification", fmt="json")
    parsed_ver = json.loads(ver_resp)
    assert "findings" in parsed_ver
    assert "overall_status" in parsed_ver
    assert "overall_confidence" in parsed_ver
