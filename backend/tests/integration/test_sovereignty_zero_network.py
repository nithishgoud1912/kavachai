"""
KavachAI — Integration Tests: Sovereignty & Zero External Calls
Implements: Phase 15 Acceptance Criterion #5, NFR-SEC-1 (Local-Only Inference)

Verifies:
- Zero external HTTP calls (OpenAI, Anthropic, Google Gemini, external CDNs) occur.
- All endpoints communicate strictly with local Ollama / local DB / localhost.
"""

import pytest
import socket
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import init_db


@pytest.mark.asyncio
async def test_zero_external_network_calls_during_investigation():
    await init_db()
    """

    Monitors all socket connection attempts during an investigation run.
    Asserts that NO external host (outside 127.0.0.1 / localhost / 0.0.0.0) is contacted.
    Implements: NFR-SEC-1
    """
    external_calls = []
    original_getaddrinfo = socket.getaddrinfo

    def audited_getaddrinfo(host, port, *args, **kwargs):
        allowed_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "test"}
        if host not in allowed_hosts and not host.endswith(".local"):
            external_calls.append((host, port))
        return original_getaddrinfo(host, port, *args, **kwargs)

    with patch("socket.getaddrinfo", side_effect=audited_getaddrinfo):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Run session + investigation
            sess_resp = await client.post("/api/v1/session", json={"name": "Auditor", "department": "Security"})
            session_id = sess_resp.json()["session_id"]

            await client.post("/api/v1/investigations", json={
                "query": "Investigate Pump P-102 and determine whether its condition has deteriorated.",
                "session_id": session_id,
            })

    # Assert ZERO external hosts contacted
    assert len(external_calls) == 0, f"External network calls detected (NFR-SEC-1 breach): {external_calls}"
