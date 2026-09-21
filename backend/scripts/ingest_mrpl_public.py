"""Ingest the curated, public MRPL reference corpus into KavachAI.

This script never downloads documents.  Place the reviewed source files in
``data/mrpl_public/raw`` and describe them in ``data/mrpl_public/manifest.json``
before running it.  Keeping acquisition separate from ingestion preserves the
air-gapped runtime story: the demonstration only reads local files and sends
embeddings to the configured local Ollama endpoint.

Run from the repository root:
    $env:OLLAMA_HOST = "http://localhost:11434"
    python backend/scripts/ingest_mrpl_public.py
"""

import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(REPO_ROOT)

from app.db.database import async_session, init_db  # noqa: E402
from app.db.object_store import object_store  # noqa: E402
from app.db.sql_models import Document  # noqa: E402
from app.db.vector_store import vector_store  # noqa: E402
from app.ingestion.chunk import chunk_pages  # noqa: E402
from app.ingestion.embed import generate_embeddings  # noqa: E402
from app.ingestion.extract import extract_text, get_page_count  # noqa: E402
from app.ingestion.tag import tag_chunks  # noqa: E402


CORPUS_ROOT = REPO_ROOT / "data" / "mrpl_public"
RAW_DIR = CORPUS_ROOT / "raw"
MANIFEST_PATH = CORPUS_ROOT / "manifest.json"
SUMMARY_PATH = CORPUS_ROOT / "ingestion_summary.json"


def _load_manifest() -> list[dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing corpus manifest: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("manifest.json must contain a non-empty 'documents' list")
    return documents


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def _ingest_document(db, spec: dict[str, Any]) -> dict[str, Any]:
    required = {"source_id", "filename", "document_type", "source_url", "published_at"}
    missing = required - spec.keys()
    if missing:
        raise ValueError(f"{spec.get('source_id', '<unknown>')} missing: {', '.join(sorted(missing))}")

    source_id = spec["source_id"]
    filename = Path(spec["filename"]).name
    file_path = RAW_DIR / filename
    if not file_path.is_file():
        raise FileNotFoundError(f"Missing source document: {file_path}")

    content = file_path.read_bytes()
    checksum = _sha256(content)
    expected_checksum = spec.get("sha256")
    if expected_checksum and expected_checksum != checksum:
        raise ValueError(f"SHA-256 mismatch for {filename}; review the source before ingesting it")

    pages = extract_text(content, filename)
    if not pages:
        raise ValueError(
            f"No extractable text in {filename}. OCR it before adding it to this text RAG corpus."
        )

    chunks = chunk_pages(pages, chunk_size=1800, chunk_overlap=250)
    if not chunks:
        raise ValueError(f"No non-empty chunks produced from {filename}")

    equipment_ids = spec.get("equipment_ids", [])
    department_scope = spec.get("department_scope", "public_corporate")
    tagged = tag_chunks(
        chunks,
        source_id=source_id,
        filename=filename,
        document_type=spec["document_type"],
        equipment_ids=equipment_ids,
        department_scope=department_scope,
    )
    provenance = {
        "organization": spec.get("organization", "MRPL"),
        "classification": spec.get("classification", "public"),
        "authority": spec.get("authority", "official_public"),
        "source_url": spec["source_url"],
        "published_at": spec["published_at"],
        "sha256": checksum,
    }
    for chunk in tagged:
        chunk["metadata"].update(provenance)

    embeddings = await generate_embeddings([chunk["text"] for chunk in tagged])
    if len(embeddings) != len(tagged) or any(len(vector) != 768 for vector in embeddings):
        raise RuntimeError("Embedding model did not produce one 768-dimensional vector per chunk")

    object_store.save_raw_file(source_id, content, filename)
    vector_store.upsert_chunks(
        ids=[f"{source_id}_chunk_{index}" for index in range(len(tagged))],
        documents=[chunk["text"] for chunk in tagged],
        embeddings=embeddings,
        metadatas=[chunk["metadata"] for chunk in tagged],
    )

    result = await db.execute(select(Document).where(Document.source_id == source_id))
    document = result.scalar_one_or_none()
    if document is None:
        document = Document(
            source_id=source_id,
            filename=filename,
            document_type=spec["document_type"],
            status="ready",
            pages=get_page_count(content, filename),
            chunks=len(tagged),
            equipment_ids=equipment_ids,
            department_scope=department_scope,
        )
        db.add(document)
    else:
        document.filename = filename
        document.document_type = spec["document_type"]
        document.status = "ready"
        document.pages = get_page_count(content, filename)
        document.chunks = len(tagged)
        document.equipment_ids = equipment_ids
        document.department_scope = department_scope

    return {
        "source_id": source_id,
        "filename": filename,
        "document_type": spec["document_type"],
        "pages": get_page_count(content, filename),
        "chunks": len(tagged),
        "sha256": checksum,
        "source_url": spec["source_url"],
    }


async def main() -> None:
    documents = _load_manifest()
    await init_db()

    results: list[dict[str, Any]] = []
    async with async_session() as db:
        for spec in documents:
            results.append(await _ingest_document(db, spec))
        await db.commit()

    summary = {
        "corpus": "MRPL public reference corpus",
        "classification": "public",
        "embedding_model": os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
        "chunking": {"size_characters": 1800, "overlap_characters": 250},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "documents": results,
        "document_count": len(results),
        "chunk_count": sum(item["chunks"] for item in results),
        "vector_dimension": 768,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
