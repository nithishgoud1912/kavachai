"""Rebuild registered documents with real local embeddings; default is inventory only.

Run with backend stopped and after backing up SQLite, objects and Chroma together.
No model downloads, source deletion or old collection deletion are performed.
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def main(apply):
    from sqlalchemy import select
    from app.db.database import async_session
    from app.db.sql_models import Document
    async with async_session() as db:
        documents = (await db.execute(select(Document).where(Document.status == 'ready'))).scalars().all()
        if not apply:
            print(json.dumps({'apply': False, 'ready_documents': len(documents), 'source_ids': [d.source_id for d in documents]}))
            return 0
        from app.db.object_store import object_store
        from app.db.vector_store import vector_store
        from app.ingestion.extract import extract_text_with_ocr
        from app.ingestion.chunk import chunk_pages
        from app.ingestion.tag import tag_chunks
        from app.ingestion.embed import generate_embeddings
        from app.orchestrator.model_router import model_router
        failed = []
        try:
            for doc in documents:
                try:
                    raw = object_store.get_raw_file(doc.source_id)
                    if not raw: raise ValueError('Registered source file missing')
                    pages = await extract_text_with_ocr(*raw)
                    chunks = tag_chunks(chunk_pages(pages), doc.source_id, doc.filename, doc.document_type,
                                        doc.equipment_ids, doc.department_scope, doc.session_id)
                    if not chunks: raise ValueError('No readable chunks')
                    texts = [c['text'] for c in chunks]
                    vectors = await generate_embeddings(texts)
                    vector_store.upsert_chunks([f'{doc.source_id}_chunk_{i}' for i in range(len(chunks))],
                                               texts, vectors, [c['metadata'] for c in chunks])
                    doc.chunks = len(chunks)
                    await db.commit()
                    print(json.dumps({'source_id': doc.source_id, 'chunks': len(chunks), 'status': 'indexed'}))
                except Exception as exc:
                    failed.append(doc.source_id)
                    print(json.dumps({'source_id': doc.source_id, 'status': 'failed', 'error': str(exc)[:500]}))
        finally:
            await model_router.close()
        print(json.dumps({'collection': vector_store.COLLECTION_NAME, 'failed_sources': failed}))
        return 1 if failed else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Write real embeddings to the new collection')
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.apply)))
