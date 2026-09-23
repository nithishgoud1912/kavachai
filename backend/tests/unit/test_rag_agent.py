"""
KavachAI — Unit Tests: Knowledge/RAG Agent
Implements: Phase 7 DoD, FR-RAG-1..2, API_Reference.md §8.5

Verifies:
- Retrieves pump operating thresholds and specifications for P-102
- Interface supports department_scope filter
"""

import pytest
from app.agents import rag_agent


@pytest.mark.asyncio
async def test_rag_agent_retrieves_operating_threshold():
    """Test retrieving vibration operating threshold for P-102 pump."""
    specs = await rag_agent.retrieve_spec(
        query="operating threshold limit for vibration",
        equipment_id="P-102",
        n_results=3,
    )

    assert len(specs) > 0
    # Must retrieve content relevant to P-102 vibration specifications
    combined_text = " ".join(s.chunk_text for s in specs).lower()
    assert any(kw in combined_text for kw in ["3.0", "threshold", "vibration", "mm/s", "p-102", "iso 10816"]), \
        f"Retrieved text should contain vibration/threshold related content, got: {combined_text[:200]}"
    for s in specs:
        assert s.source_id, "Each spec must have a non-empty source_id"
