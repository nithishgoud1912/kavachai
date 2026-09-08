"""
KavachAI — ChromaDB Vector Store Wrapper
Implements: FR-ING-5 (vector storage), FR-DOC-1 (vector retrieval), FR-RAG-1 (spec retrieval)

Chunk record schema: {chunk_text, source_id, page, equipment_ids[], document_type,
                      department_scope, embedding}
Collection dimension: 768 (nomic-embed-text)
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional

from app.config import settings


class VectorStore:
    """ChromaDB wrapper for document chunk storage and retrieval."""

    COLLECTION_NAME = "kavachai_chunks"

    def __init__(self):
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Store document chunks with embeddings and metadata.
        Implements: FR-ING-5

        Each metadata dict should contain:
        - source_id: str
        - page: int
        - equipment_ids: str (JSON-encoded list, Chroma doesn't support list metadata)
        - document_type: str
        - department_scope: str (optional)
        """
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k chunks by embedding similarity.
        Implements: FR-DOC-1, FR-RAG-1

        Returns list of: {chunk_text, source_id, page, score, metadata}
        """
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        if where_document:
            kwargs["where_document"] = where_document

        results = self._collection.query(**kwargs)

        chunks = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                chunks.append({
                    "chunk_id": chunk_id,
                    "chunk_text": results["documents"][0][i] if results["documents"] else "",
                    "source_id": metadata.get("source_id", ""),
                    "page": metadata.get("page", None),
                    "score": 1.0 - results["distances"][0][i] if results["distances"] else 0.0,  # cosine distance → similarity
                    "metadata": metadata,
                })

        return chunks

    def count(self) -> int:
        """Return total number of stored chunks."""
        return self._collection.count()

    def delete_by_source(self, source_id: str) -> None:
        """Delete all chunks for a given source document."""
        self._collection.delete(where={"source_id": source_id})


# Singleton instance
vector_store = VectorStore()
