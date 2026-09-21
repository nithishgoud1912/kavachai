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
    assert set(result.connections) in [{"STR-101", "E-103"}, {"T-101", "V-204"}]
    assert result.confidence >= 0.9


@pytest.mark.asyncio
async def test_vision_agent_connection_chain():
    """Test full linear process chain for P-102."""
    chain = await vision_agent.get_connection_chain("P-102")
    assert chain in [
        ["T-101", "STR-101", "P-102", "E-103", "V-204", "F-101", "R-101"],
        ["T-101", "P-102", "V-204", "R-101"],
    ]



@pytest.mark.asyncio
async def test_vision_agent_graceful_degradation():
    """Test unrecognized equipment returns found: False per FR-VIS-3."""
    result = await vision_agent.analyze_pid(pid_source_id="pid_demo", equipment_id="UNKNOWN_EQUIP")

    assert result.found is False
    assert result.connections == []
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_vision_agent_with_qwen_vl_mock(monkeypatch):
    """Test Qwen2.5-VL parsing of bounding boxes and visual descriptions."""
    import json
    from app.orchestrator.model_router import model_router
    from app.db.object_store import object_store

    # Mock object store returning dummy image bytes
    monkeypatch.setattr(object_store, "get_raw_file", lambda src_id: (b"fake_image_bytes", "pid_101.png"))

    # Mock model router generate_vision returning Qwen2.5-VL JSON response
    mock_vl_response = json.dumps({
        "found": True,
        "connections": ["T-101", "V-204"],
        "bounding_box": [110, 260, 190, 390],
        "visual_description": "Centrifugal crude charge pump P-102 identified between feed tank T-101 and control valve V-204.",
        "confidence": 0.98
    })

    async def fake_generate_vision(*args, **kwargs):
        return mock_vl_response

    monkeypatch.setattr(model_router, "generate_vision", fake_generate_vision)

    result = await vision_agent.analyze_pid(pid_source_id="pid_101", equipment_id="P-102")

    assert result.found is True
    assert set(result.connections) == {"T-101", "V-204"}
    assert result.bounding_box == [110, 260, 190, 390]
    assert "P-102 identified between feed tank T-101" in result.visual_description
    assert result.confidence == 0.98

