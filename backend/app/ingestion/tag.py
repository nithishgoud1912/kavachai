"""
KavachAI — Chunk Metadata Tagging
Implements: FR-ING-4 (tag each chunk with source doc name, page, equipment IDs,
            document date, document type)

Tags are stored as ChromaDB metadata for filtered retrieval.
"""

import re
from typing import List, Dict, Any, Optional


# Known equipment ID patterns (P-xxx, T-xxx, V-xxx, R-xxx, E-xxx, C-xxx)
EQUIPMENT_PATTERN = re.compile(r"\b([A-Z]-\d{2,4})\b")


def tag_chunks(
    chunks: List[Dict[str, Any]],
    source_id: str,
    filename: str,
    document_type: str,
    equipment_ids: Optional[List[str]] = None,
    department_scope: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Tag each chunk with metadata for retrieval filtering.
    Implements: FR-ING-4

    Args:
        chunks: output from chunk.chunk_pages()
        source_id: unique document ID
        filename: original filename
        document_type: inspection_report, maintenance_history, sop, manual, pid_drawing, other
        equipment_ids: explicitly provided equipment IDs (optional, also auto-detected)
        department_scope: for permission-aware retrieval (FR-RAG-2)

    Returns:
        Chunks with metadata attached (ready for vector store)
    """
    provided_ids = set(equipment_ids or [])

    tagged_chunks = []
    for chunk in chunks:
        # Auto-detect equipment IDs in chunk text
        detected_ids = set(EQUIPMENT_PATTERN.findall(chunk["text"]))
        all_ids = provided_ids | detected_ids

        # Build metadata dict (ChromaDB-compatible: no nested objects, no list values)
        metadata = {
            "source_id": source_id,
            "filename": filename,
            "page": chunk["page"],
            "chunk_index": chunk["chunk_index"],
            "document_type": document_type,
            "equipment_ids": ",".join(sorted(all_ids)) if all_ids else "",  # CSV string for Chroma
            "department_scope": department_scope or "",
        }

        tagged_chunks.append({
            "text": chunk["text"],
            "metadata": metadata,
        })

    return tagged_chunks
