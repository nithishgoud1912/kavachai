"""
KavachAI — Evidence Router
Implements: FR-RPT-3 (click evidence reference -> view source)
Endpoint: GET /evidence/{source_id} (API_Reference.md §5)
"""

import re
from pathlib import Path
import pandas as pd
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.sql_models import Document, Dataset, Session as SessionModel
from app.db.object_store import object_store
from app.db.tabular_store import tabular_store
from app.db.graph_store import graph_store
from app.models.evidence import EvidenceResponse
from app.access import assert_owner
from app.deps import Principal, get_current_session, require_permission

router = APIRouter(prefix="/api/v1", tags=["evidence"])


async def _assert_source_scope(
    source_id: str, session: SessionModel, principal: Principal, db: AsyncSession,
) -> None:
    """Do not expose raw/object-store contents merely because an opaque ID is known."""
    document = (await db.execute(select(Document).where(Document.source_id == source_id))).scalar_one_or_none()
    if document is None:
        document = await db.get(Dataset, source_id)
    await assert_owner(document, session, db, shared=True)


@router.get("/evidence/{source_id}", response_model=EvidenceResponse)
async def get_evidence(
    source_id: str,
    page: Optional[int] = Query(None),
    equipment_id: Optional[str] = Query(None),
    current_session: SessionModel = Depends(get_current_session),
    principal: Principal = Depends(require_permission("document:read")),
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
        await _assert_source_scope(source_id, current_session, principal, db)
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
        await assert_owner(ds, current_session, db, shared=True)
        # Resolve target equipment ID dynamically
        target_equipment = equipment_id
        if not target_equipment and ds.table_name and tabular_store.table_exists(ds.table_name):
            try:
                conn = tabular_store._get_connection()
                cursor = conn.execute(f'SELECT DISTINCT equipment_id FROM "{ds.table_name}" LIMIT 1')
                row = cursor.fetchone()
                conn.close()
                if row and row[0]:
                    target_equipment = row[0]
            except Exception:
                pass

        if not target_equipment:
            raise HTTPException(422, "equipment_id required")

        rows = []
        if ds.table_name:
            df = tabular_store.query_by_equipment(ds.table_name, target_equipment)
            rows = df.to_dict(orient="records")

        return EvidenceResponse(
            source_id=source_id,
            type="dataset",
            filename=ds.filename,
            rows=rows,
        )

    raise HTTPException(status_code=404, detail="Evidence not found")


@router.get("/files/{source_id}/page/{page}")
async def get_document_page_render(
    source_id: str, page: int,
    current_session: SessionModel = Depends(get_current_session),
    principal: Principal = Depends(require_permission("document:read")),
    db: AsyncSession = Depends(get_db),
):
    """Serve a rendered PNG page of a PDF document for the Source Viewer."""
    await _assert_source_scope(source_id, current_session, principal, db)
    png_bytes = object_store.get_file_page(source_id, page)
    if png_bytes:
        return Response(content=png_bytes, media_type="image/png")

    raw = object_store.get_raw_file(source_id)
    if raw:
        file_bytes, filename = raw
        return Response(content=file_bytes, media_type="text/plain; charset=utf-8")

    raise HTTPException(status_code=404, detail="Page render not available")


@router.get("/evidence/files/{source_id}/raw")
@router.get("/files/{source_id}/raw")
async def get_raw_file(
    source_id: str,
    current_session: SessionModel = Depends(get_current_session),
    principal: Principal = Depends(require_permission("document:read")),
    db: AsyncSession = Depends(get_db),
):
    """Serve raw uploaded file bytes."""
    await _assert_source_scope(source_id, current_session, principal, db)
    raw = object_store.get_raw_file(source_id)
    if not raw:
        raise HTTPException(status_code=404, detail="File not found")

    file_bytes, filename = raw
    suffix = Path(filename).suffix.lower()
    media_type = "application/octet-stream"
    if suffix == ".pdf":
        media_type = "application/pdf"
    elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        media_type = f"image/{suffix.lstrip('.')}"
    elif suffix in {".txt", ".text", ".md", ".csv", ".json", ".log", ".tsv", ".yaml", ".yml"}:
        media_type = "text/plain; charset=utf-8"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

