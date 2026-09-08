"""
KavachAI — Unit Tests: Vision/P&ID Agent
Implements: Phase 6 DoD, FR-VIS-1..3, Decision Q5 (NetworkX Graph Fallback)

Verifies:
- P-102 returns found: True, connections: ["T-101", "V-204"]
- P-102 connection chain returns ["T-101", "P-102", "V-204", "R-101"]
- Non-existent equipment returns found: False gracefully without throwing
"""

import pytest
from app.agents import vision_agent


@pytest.mark.asyncio
async def test_vision_agent_p102_connections():
    """Test P-102 connectivity per FR-VIS-1/2."""
    result = await vision_agent.analyze_pid(pid_source_id="pid_demo", equipment_id="P-102")

    assert result.found is True
    assert set(result.connections) == {"T-101", "V-204"}
    assert result.confidence >= 0.9


@pytest.mark.asyncio
async def test_vision_agent_connection_chain():
    """Test full linear process chain for P-102."""
    chain = await vision_agent.get_connection_chain("P-102")
    assert chain == ["T-101", "P-102", "V-204", "R-101"]


@pytest.mark.asyncio
async def test_vision_agent_graceful_degradation():
    """Test unrecognized equipment returns found: False per FR-VIS-3."""
    result = await vision_agent.analyze_pid(pid_source_id="pid_demo", equipment_id="UNKNOWN_EQUIP")

    assert result.found is False
    assert result.connections == []
    assert result.confidence == 0.0
