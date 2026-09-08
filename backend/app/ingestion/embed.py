"""
KavachAI — Embedding Generation via Model Router
Implements: FR-ING-5 (generate vector embeddings for each chunk)

IMPORTANT: This module calls embeddings through the Model Router ONLY (NFR-MNT-2).
It does NOT import httpx or call Ollama directly.
"""

from typing import List

from app.orchestrator.model_router import model_router


async def generate_embeddings(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks.
    Implements: FR-ING-5

    Routes through Model Router (NFR-MNT-2) — never calls Ollama directly.

    Args:
        texts: list of text strings to embed
        batch_size: number of texts per batch (to avoid OOM on large corpora)

    Returns:
        List of embedding vectors (768-dim for nomic-embed-text)
    """
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = await model_router.embed(batch)
        all_embeddings.extend(batch_embeddings)

    return all_embeddings
