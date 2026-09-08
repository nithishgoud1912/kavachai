"""
KavachAI — Document Intelligence Agent
Implements: FR-DOC-1 (vector search with metadata filter),
            FR-DOC-2 (named-value extraction),
            FR-DOC-3 (traceable source references)

Contract (API_Reference.md §8.2):
    retrieve(sub_task_goal: str, filters: dict)
        -> [{chunk_text, source_id, page, score}]

Uses Model Router for embedding queries (NFR-MNT-2).
"""

from typing import List, Dict, Any, Optional

from app.agents.base import DocumentChunk
from app.db.vector_store import vector_store
from app.orchestrator.model_router import model_router


async def retrieve(
    sub_task_goal: str,
    filters: Optional[Dict[str, Any]] = None,
    n_results: int = 5,
) -> List[DocumentChunk]:
    """
    Query the vector database for relevant document chunks.
    Implements: FR-DOC-1, FR-DOC-3

    Args:
        sub_task_goal: what the planner wants this agent to find
        filters: optional filters {equipment_ids?, document_types?, department_scope?}
        n_results: max chunks to return

    Returns:
        List of DocumentChunk with traceable source references
    """
    # Generate embedding for the query (through Model Router)
    query_embeddings = await model_router.embed([sub_task_goal])
    if not query_embeddings:
        return []

    query_embedding = query_embeddings[0]

    # Build ChromaDB where filter (only metadata exact match supported in Chroma)
    where = _build_where_filter(filters) if filters else None

    # Query vector store
    results = vector_store.query(
        query_embedding=query_embedding,
        n_results=max(n_results * 2, 8),
        where=where,
    )

    # Convert to DocumentChunk contract and prioritize equipment matches
    target_eids = set(filters.get("equipment_ids") or []) if filters else set()
    chunks = []
    for r in results:
        meta = r.get("metadata", {}) or {}
        chunk_eids = set(meta.get("equipment_ids", "").split(",")) if meta.get("equipment_ids") else set()
        matches_eq = False
        if target_eids:
            matches_eq = bool(target_eids & chunk_eids) or any(eid in r["chunk_text"] for eid in target_eids)

        score = r.get("score", 0.0)
        if matches_eq:
            score += 0.5  # boost matching equipment chunks

        chunks.append(DocumentChunk(
            chunk_text=r["chunk_text"],
            source_id=r["source_id"],
            page=r.get("page", 1),
            score=score,
        ))

    # Sort by boosted score
    chunks.sort(key=lambda c: c.score, reverse=True)
    return chunks[:n_results]


def _build_where_filter(filters: Dict[str, Any]) -> Optional[Dict]:
    """
    Build a ChromaDB where filter from agent filters.
    Supports: document_types, department_scope
    Note: equipment_ids is matched in python post-retrieval because ChromaDB does
    not support substring $contains on metadata fields.
    """
    conditions = []

    if "document_types" in filters and filters["document_types"]:
        if len(filters["document_types"]) == 1:
            conditions.append({"document_type": filters["document_types"][0]})
        else:
            conditions.append({"document_type": {"$in": filters["document_types"]}})

    if "department_scope" in filters and filters["department_scope"]:
        conditions.append({"department_scope": filters["department_scope"]})

    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}

