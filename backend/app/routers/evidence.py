"""
KavachAI — Evidence Router
Implements: FR-RPT-3 (click evidence reference -> view source)
Endpoint: GET /evidence/{source_id} (API_Reference.md §5)
"""

import re
import pandas as pd
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.sql_models import Document, Dataset, Session as SessionModel
from app.db.object_store import object_store
from app.db.tabular_store import tabular_store
from app.db.graph_store import graph_store
from app.models.evidence import EvidenceResponse
from app.deps import get_current_session

router = APIRouter(prefix="/api/v1", tags=["evidence"])


@router.get("/evidence/{source_id}", response_model=EvidenceResponse)
async def get_evidence(
    source_id: str,
    page: Optional[int] = Query(None),
    equipment_id: Optional[str] = Query(None),
    current_session: SessionModel = Depends(get_current_session),
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

        target_equipment = target_equipment or "P-102"

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

    # Check if it's a P&ID source
    if source_id.startswith("pid_") or source_id == "pid_drawing":
        target_equipment = equipment_id
        if not target_equipment:
            # Check if source_id contains equipment suffix (e.g. pid_P-102)
            suffix_match = re.search(r"pid_([A-Z]-\d{2,4})", source_id)
            if suffix_match:
                target_equipment = suffix_match.group(1)
            else:
                target_equipment = "P-102"

        connections = graph_store.get_connections(target_equipment)

        return EvidenceResponse(
            source_id=source_id,
            type="pid_drawing",
            filename="P&ID Drawing",
            highlighted_component=target_equipment,
            connections=connections,
        )

    raise HTTPException(status_code=404, detail="Evidence not found")
