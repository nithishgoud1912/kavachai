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
    # Build a search query that targets specs/manuals
    search_query = f"specification threshold limit {query} {equipment_id}"

    # Generate embedding (through Model Router)
    query_embeddings = await model_router.embed([search_query])
    if not query_embeddings:
        return []

    query_embedding = query_embeddings[0]

    # Build ChromaDB filter — prefer manuals and SOPs
    where_filter = _build_spec_filter(filters)

    # Query vector store
    results = vector_store.query(
        query_embedding=query_embedding,
        n_results=max(n_results * 2, 6),
        where=where_filter,
    )

    # Convert to SpecChunk contract and rank by equipment & spec relevance
    specs = []
    for r in results:
        meta = r.get("metadata", {}) or {}
        section = _extract_section_ref(r["chunk_text"])
        
        # Boost if chunk contains equipment_id or is manual/sop
        is_eq = equipment_id in r["chunk_text"] or equipment_id in meta.get("equipment_ids", "")
        is_spec_doc = meta.get("document_type") in ["manual", "sop"]
        score = r.get("score", 0.0)
        if is_eq:
            score += 0.4
        if is_spec_doc:
            score += 0.3

        specs.append((score, SpecChunk(
            chunk_text=r["chunk_text"],
            source_id=r["source_id"],
            page=r.get("page"),
            section=section,
        )))

    specs.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in specs[:n_results]]


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
