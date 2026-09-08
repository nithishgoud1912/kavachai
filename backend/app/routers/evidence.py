"""
KavachAI — Evidence Router
Implements: FR-RPT-3 (click evidence reference -> view source)
Endpoint: GET /evidence/{source_id} (API_Reference.md §5)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.sql_models import Document, Dataset
from app.db.object_store import object_store
from app.db.tabular_store import tabular_store
from app.models.evidence import EvidenceResponse

router = APIRouter(prefix="/api/v1", tags=["evidence"])


@router.get("/evidence/{source_id}", response_model=EvidenceResponse)
async def get_evidence(
    source_id: str,
    page: int = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Powers the Source Viewer panel (Design.md §5.6).
    Implements: FR-RPT-3

    Returns document, dataset, or P&ID evidence by source_id.
    """
    # Check if it's a document
    doc_result = await db.execute(
        select(Document).where(Document.source_id == source_id)
    )
    doc = doc_result.scalar_one_or_none()

    if doc:
        # Build document evidence response
        excerpt = None
        view_url = f"/api/v1/files/{source_id}/page/{page or 1}"

        # Try to get an excerpt from the raw file
        raw = object_store.get_raw_file(source_id)
        if raw:
            file_bytes, filename = raw
            from app.ingestion.extract import extract_text
            pages = extract_text(file_bytes, filename)
            if pages and page:
                target_page = next((p for p in pages if p["page"] == page), None)
                if target_page:
                    excerpt = target_page["text"][:300]

        return EvidenceResponse(
            source_id=source_id,
            type="document",
            filename=doc.filename,
            page=page,
            excerpt=excerpt,
            view_url=view_url,
        )

    # Check if it's a dataset
    ds_result = await db.execute(
        select(Dataset).where(Dataset.id == source_id)
    )
    ds = ds_result.scalar_one_or_none()

    if ds:
        # Return dataset rows
        import pandas as pd
        rows = []
        if ds.table_name:
            df = tabular_store.query_by_equipment(ds.table_name, "P-102")  # TODO: parameterize
            rows = df.to_dict(orient="records")

        return EvidenceResponse(
            source_id=source_id,
            type="dataset",
            filename=ds.filename,
            rows=rows,
        )

    # Check if it's a P&ID source
    if source_id.startswith("pid_"):
        from app.db.graph_store import graph_store
        connections = graph_store.get_connections("P-102")  # TODO: parameterize

        return EvidenceResponse(
            source_id=source_id,
            type="pid_drawing",
            filename="P&ID Drawing",
            highlighted_component="P-102",
            connections=connections,
        )

    raise HTTPException(status_code=404, detail="Evidence not found")
