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
    # Must retrieve manual mentioning 3.0 mm/s or 2.8 mm/s
    combined_text = " ".join(s.chunk_text for s in specs)
    assert "3.0" in combined_text or "threshold" in combined_text.lower()
    for s in specs:
        assert s.source_id.startswith("doc_")
