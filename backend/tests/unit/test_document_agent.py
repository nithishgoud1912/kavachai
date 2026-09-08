"""
KavachAI — Unit Tests: Document Agent
Implements: Phase 4 DoD, FR-DOC-1..3, API_Reference.md §8.2

Verifies:
- Retrieval against P-102 corpus returns inspection report chunks
- Chunks have valid source_id, page number, score, and text
"""

import pytest
from app.agents import document_agent


@pytest.mark.asyncio
async def test_document_agent_retrieves_p102_chunks():
    """Test retrieving inspection reports for P-102."""
    chunks = await document_agent.retrieve(
        sub_task_goal="Find inspection reports mentioning P-102",
        filters={"equipment_ids": ["P-102"]},
        n_results=3,
    )

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.source_id.startswith("doc_")
        assert chunk.page is not None
        assert chunk.score > 0
        assert len(chunk.chunk_text) > 0


@pytest.mark.asyncio
async def test_document_agent_fire_sop_retrieval():
    """Test retrieving safety evacuation SOP chunks."""
    chunks = await document_agent.retrieve(
        sub_task_goal="fire emergency evacuation procedure",
        filters={"department_scope": "HSE"},
        n_results=2,
    )

    assert len(chunks) > 0
    assert any("evacuat" in c.chunk_text.lower() or "fire" in c.chunk_text.lower() for c in chunks)
