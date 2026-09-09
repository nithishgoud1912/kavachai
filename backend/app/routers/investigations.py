"""
KavachAI — Investigations Router
Implements: FR-PLN-1..3, FR-RPT-1..3, NFR-PERF-3 (SSE streaming)
Endpoints: API_Reference.md §4
    POST /investigations
    GET  /investigations/{id}/stream (SSE)
    GET  /investigations/{id}/report
    GET  /investigations/{id}/plan
"""

import asyncio
import json
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator, Optional, List

from app.db.database import get_db, async_session
from app.db.sql_models import Investigation, Session as SessionModel, Document
from app.db.object_store import object_store
from app.db.vector_store import vector_store
from app.ingestion.extract import extract_text, get_page_count
from app.ingestion.chunk import chunk_pages
from app.ingestion.tag import tag_chunks
from app.ingestion.embed import generate_embeddings
from app.models.investigation import (
    InvestigationCreate, InvestigationCreateResponse, InvestigationPlanResponse,
    SubTaskResponse,
)
from app.models.chat import UploadResponse, BatchUploadResponse
from app.orchestrator.investigation import InvestigationRunner
from app.services.audit_service import create_audit_entry, resolve_audit_entry
from app.deps import get_current_session, get_optional_session

router = APIRouter(prefix="/api/v1", tags=["investigations"])

# In-memory store for active investigation runners
_runners: dict[str, InvestigationRunner] = {}


@router.get("/investigations")
async def list_investigations(
    db: AsyncSession = Depends(get_db),
):
    """
    List all investigations with summary info for the dashboard.
    Sorted by created_at DESC (newest first).
    """
    result = await db.execute(
        select(Investigation).order_by(Investigation.created_at.desc())
    )
    investigations = result.scalars().all()

    return [
        {
            "id": inv.id,
            "query": inv.query,
            "status": inv.status,
            "condition_summary": (inv.report or {}).get("condition_summary", ""),
            "confidence": inv.confidence,
            "verification_status": inv.verification_status,
            "attachments_count": len(inv.attachments or []),
            "created_at": inv.created_at.isoformat() + "Z",
            "completed_at": (
                inv.completed_at.isoformat() + "Z" if inv.completed_at else None
            ),
        }
        for inv in investigations
    ]


async def _run_investigation_background(investigation_id: str):
    """
    Run the investigation pipeline in the background.
    NFR-REL-2: Investigation continues server-side independent of SSE connection.
    """
    async with async_session() as db:
        result = await db.execute(
            select(Investigation).where(Investigation.id == investigation_id)
        )
        investigation = result.scalar_one_or_none()
        if not investigation:
            return

        runner = InvestigationRunner(investigation, db)
        _runners[investigation_id] = runner

        try:
            res = await runner.run()

            # Resolve audit entry
            status = "completed" if res.get("type") == "investigation_complete" else "insufficient_evidence"
            report = res.get("report", {})

            await resolve_audit_entry(
                db=db,
                investigation_id=investigation_id,
                agents_invoked=runner.agents_invoked,
                verification_status=report.get("verification_status"),
                confidence=report.get("confidence"),
                status=status,
            )

        except Exception as e:
            # FR-AUD-1: Failed investigations still produce audit entries
            await resolve_audit_entry(
                db=db,
                investigation_id=investigation_id,
                agents_invoked=runner.agents_invoked if 'runner' in locals() else [],
                verification_status=None,
                confidence=None,
                status="failed",
            )
        finally:
            # Clean up runner from active runners after a grace period
            asyncio.create_task(_cleanup_runner(investigation_id))


async def _cleanup_runner(investigation_id: str, delay_seconds: int = 60):
    """Retain runner briefly in memory for active streams before cleanup."""
    await asyncio.sleep(delay_seconds)
    _runners.pop(investigation_id, None)


@router.post("/investigations/upload", response_model=BatchUploadResponse)
async def upload_investigation_files(
    files: List[UploadFile] = File(...),
    paths: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and index files or folder contents for a Deep Investigation.
    Extracts text, chunks, embeds into ChromaDB, and registers in Document table.
    """
    path_list = []
    if paths:
        try:
            path_list = json.loads(paths)
        except Exception:
            path_list = []

    uploaded_results: List[UploadResponse] = []

    for idx, file in enumerate(files):
        if not file.filename:
            continue

        relative_path = path_list[idx] if idx < len(path_list) else file.filename
        source_id = f"doc_{uuid.uuid4().hex[:8]}"
        file_content = await file.read()
        file_size = len(file_content)

        # 1. Save raw file to object store
        object_store.save_raw_file(source_id, file_content, file.filename)

        # 2. Extract text
        pages = extract_text(file_content, file.filename)
        page_count = get_page_count(file_content, file.filename)

        suffix = Path(file.filename).suffix.lower()
        is_image = suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
        file_type = "image" if is_image else "document"

        chunk_count = 0
        preview_text = None

        if pages:
            full_text = "\n\n".join(p["text"] for p in pages if p.get("text"))
            preview_text = full_text[:500] if full_text else None

            # 3. Chunk text
            chunks = chunk_pages(pages)

            if chunks:
                # 4. Tag chunks with metadata
                tagged_chunks = tag_chunks(
                    chunks=chunks,
                    source_id=source_id,
                    filename=file.filename,
                    document_type="investigation_upload",
                    equipment_ids=[],
                    department_scope=None,
                )

                # 5. Generate embeddings and store in vector DB
                texts = [c["text"] for c in tagged_chunks]
                embeddings = await generate_embeddings(texts)
                chunk_ids = [f"{source_id}_chunk_{i}" for i in range(len(tagged_chunks))]
                metadatas = [c["metadata"] for c in tagged_chunks]
                for m in metadatas:
                    m["relative_path"] = relative_path

                vector_store.upsert_chunks(chunk_ids, texts, embeddings, metadatas)
                chunk_count = len(tagged_chunks)

        # 6. Save document record in DB
        doc = Document(
            id=source_id,
            filename=file.filename,
            document_type="investigation_upload",
            status="ready",
            pages=page_count,
            chunks=chunk_count,
            equipment_ids=[],
            department_scope=None,
            source_id=source_id,
        )
        db.add(doc)
        await db.commit()

        file_url = f"/api/v1/files/{source_id}/raw"

        uploaded_results.append(UploadResponse(
            filename=file.filename,
            url=file_url,
            type=file_type,
            extracted_text_preview=preview_text,
            source_id=source_id,
            path=relative_path,
            size=file_size,
            chunk_count=chunk_count,
        ))

    return BatchUploadResponse(
        files=uploaded_results,
        total_files=len(uploaded_results),
    )


@router.post("/investigations", response_model=InvestigationCreateResponse, status_code=202)
async def create_investigation(
    body: InvestigationCreate,
    background_tasks: BackgroundTasks,
    current_session: Optional[SessionModel] = Depends(get_optional_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new investigation with session validation.
    Implements: FR-PLN-1, API_Reference.md §4 POST /investigations
    """
    from datetime import datetime, timezone
    active_session = current_session
    if not active_session:
        if not body.session_id:
            raise HTTPException(status_code=401, detail="Authentication required: No session provided")
        sess_res = await db.execute(select(SessionModel).where(SessionModel.id == body.session_id))
        active_session = sess_res.scalar_one_or_none()
        if not active_session:
            raise HTTPException(status_code=401, detail="Invalid session_id")
        if getattr(active_session, "is_revoked", False):
            raise HTTPException(status_code=401, detail="Session has been revoked")
        if active_session.expires_at:
            now = datetime.now(timezone.utc)
            exp = active_session.expires_at if active_session.expires_at.tzinfo else active_session.expires_at.replace(tzinfo=timezone.utc)
            if now > exp:
                raise HTTPException(status_code=401, detail="Session has expired")

    attachments_data = [a.model_dump() for a in body.attachments] if body.attachments else []

    # Create investigation
    investigation = Investigation(
        query=body.query,
        session_id=active_session.id,
        status="planning",
        attachments=attachments_data,
    )
    db.add(investigation)
    await db.commit()
    await db.refresh(investigation)

    # Create audit entry (first write — workflow.md §4)
    await create_audit_entry(
        db=db,
        investigation_id=investigation.id,
        user=active_session.name,
        department=active_session.department,
        query=body.query,
    )

    # Kick off investigation in background (NFR-REL-2)
    background_tasks.add_task(_run_investigation_background, investigation.id)

    return InvestigationCreateResponse(
        investigation_id=investigation.id,
        status="planning",
        stream_url=f"/api/v1/investigations/{investigation.id}/stream",
        attachments_count=len(attachments_data),
    )


@router.get("/investigations/{investigation_id}/stream")
async def stream_investigation(
    investigation_id: str,
    current_session: Optional[SessionModel] = Depends(get_optional_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream live agent timeline via SSE with SQLite event persistence for reconnection.
    Implements: API_Reference.md §4 GET /investigations/{id}/stream, NFR-PERF-3
    """
    # Verify investigation exists
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        last_event_index = 0

        while True:
            runner = _runners.get(investigation_id)

            if runner:
                # Emit any new events from active memory runner
                while last_event_index < len(runner.events):
                    event = runner.events[last_event_index]
                    yield f"event: agent_update\ndata: {json.dumps(event)}\n\n"
                    last_event_index += 1
            else:
                # Fallback to persisted database events if runner restarted
                async with async_session() as db_events:
                    inv_res = await db_events.execute(
                        select(Investigation).where(Investigation.id == investigation_id)
                    )
                    inv_row = inv_res.scalar_one_or_none()
                    if inv_row and inv_row.events:
                        while last_event_index < len(inv_row.events):
                            event = inv_row.events[last_event_index]
                            yield f"event: agent_update\ndata: {json.dumps(event)}\n\n"
                            last_event_index += 1

            # Check if investigation is complete
            async with async_session() as check_db:
                check_result = await check_db.execute(
                    select(Investigation.status).where(Investigation.id == investigation_id)
                )
                status = check_result.scalar_one_or_none()

                if status in ("complete", "failed"):
                    yield f"event: investigation_complete\ndata: {json.dumps({'investigation_id': investigation_id, 'report_url': f'/api/v1/investigations/{investigation_id}/report'})}\n\n"
                    break
                elif status == "insufficient_evidence":
                    yield f"event: insufficient_evidence\ndata: {json.dumps({'investigation_id': investigation_id, 'message': 'No relevant evidence found in the knowledge base.'})}\n\n"
                    break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/investigations/{investigation_id}/report")
async def get_report(
    investigation_id: str,
    current_session: Optional[SessionModel] = Depends(get_optional_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch the final investigation report.
    Implements: FR-RPT-1, API_Reference.md §4 GET /investigations/{id}/report
    Works even if SSE was disconnected mid-stream (NFR-REL-2).
    """
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if investigation.status == "insufficient_evidence":
        return {
            "investigation_id": investigation.id,
            "query": investigation.query,
            "overall_status": "insufficient_evidence",
            "condition_summary": "Insufficient evidence for conclusion",
            "findings": [],
            "conclusion": "No relevant evidence found in the knowledge base.",
            "confidence": 0,
            "verification_status": "unverified",
            "generated_at": (investigation.completed_at or investigation.created_at).isoformat() + "Z",
        }

    if not investigation.report:
        if investigation.status in ("planning", "investigating"):
            raise HTTPException(status_code=202, detail="Investigation still in progress")
        raise HTTPException(status_code=404, detail="Report not available")

    report_dict = dict(investigation.report)
    if "attachments" not in report_dict:
        report_dict["attachments"] = investigation.attachments or []
    if "query" not in report_dict or not report_dict["query"]:
        report_dict["query"] = investigation.query or "P-102 Investigation"
    if "findings" not in report_dict or report_dict["findings"] is None:
        report_dict["findings"] = []
    return report_dict


@router.get("/investigations/{investigation_id}/plan", response_model=InvestigationPlanResponse)
async def get_plan(
    investigation_id: str,
    current_session: Optional[SessionModel] = Depends(get_optional_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the Planner's decomposition.
    Implements: FR-PLN-3, API_Reference.md §4 GET /investigations/{id}/plan
    """
    result = await db.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    investigation = result.scalar_one_or_none()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if not investigation.plan:
        raise HTTPException(status_code=202, detail="Plan not yet generated")

    sub_tasks = [
        SubTaskResponse(agent=st["agent"], goal=st["goal"])
        for st in investigation.plan.get("sub_tasks", [])
    ]

    return InvestigationPlanResponse(
        investigation_id=investigation.id,
        sub_tasks=sub_tasks,
    )
