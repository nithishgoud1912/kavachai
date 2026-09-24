"""
KavachAI — Knowledge/RAG Agent
Implements: FR-RAG-1 (retrieve spec/threshold values),
            FR-RAG-2 (department_scope filter — interface exists, enforcement simplified)

Contract (API_Reference.md §8.5):
    retrieve_spec(query: str, equipment_id: str, filters: {department_scope?})
        -> [{chunk_text, source_id, page, section}]

Uses Model Router for embedding queries (NFR-MNT-2).
"""

import re
from typing import List, Dict, Any, Optional

from app.agents.base import SpecChunk
from app.db.vector_store import vector_store
from app.orchestrator.model_router import model_router


async def retrieve_spec(
    query: str,
    equipment_id: str,
    filters: Optional[Dict[str, Any]] = None,
    n_results: int = 3,
) -> List[SpecChunk]:
    """
    Retrieve specification/threshold values from the document corpus.
    Implements: FR-RAG-1, FR-RAG-2

    Args:
        query: what spec/threshold to find (e.g., "vibration threshold for pump")
        equipment_id: equipment to scope the search to
        filters: optional {department_scope} for permission-aware retrieval (FR-RAG-2)
        n_results: max chunks to return

    Returns:
        List of SpecChunk with source references
    """
    from app.agents.document_agent import retrieve
    chunks = await retrieve(f"specification threshold limit {query} {equipment_id}", filters, n_results)
    return [SpecChunk(chunk_text=c.chunk_text, source_id=c.source_id, page=c.page,
                      section=_extract_section_ref(c.chunk_text)) for c in chunks]


def _build_spec_filter(
    filters: Optional[Dict[str, Any]] = None,
) -> Optional[Dict]:
    """Build ChromaDB where filter for spec retrieval."""
    conditions = []

    # FR-RAG-2: department_scope filter
    if filters and "department_scope" in filters and filters["department_scope"]:
        conditions.append({"department_scope": filters["department_scope"]})

    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}



def _extract_section_ref(text: str) -> Optional[str]:
    """
    Try to extract a section reference (e.g., "§4.2" or "Section 4.2") from text.
    """
    # Match patterns like "§4.2", "Section 4.2", "section 4.2", "Sec. 4.2"
    patterns = [
        r'[§](\d+\.?\d*)',
        r'[Ss]ection\s+(\d+\.?\d*)',
        r'[Ss]ec\.\s*(\d+\.?\d*)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None
