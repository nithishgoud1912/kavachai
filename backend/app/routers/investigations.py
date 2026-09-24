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
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File, Form, Request
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
from app.deps import get_current_session, require_permission
from app.access import assert_owner, owner_filter, validate_attachments
from app.config import settings
from app.ingestion.limits import read_upload

router = APIRouter(prefix="/api/v1", tags=["investigations"], dependencies=[Depends(require_permission("investigation:write"))])

# In-memory store for active investigation runners
_runners: dict[str, InvestigationRunner] = {}


@router.get("/investigations")
async def list_investigations(
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    List all investigations with summary info for the dashboard.
    Sorted by created_at DESC (newest first).
    """
    result = await db.execute(
        select(Investigation).where(owner_filter(Investigation, current_session)).order_by(Investigation.created_at.desc())
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
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and index files or folder contents for a Deep Investigation.
    Extracts text, chunks, embeds into ChromaDB, and registers in Document table.
    """
    from app.routers.chat import _process_chat_file
    if len(files) > settings.MAX_BATCH_FILES:
        raise HTTPException(413, "Too many files")
    try:
        path_list = json.loads(paths) if paths else []
        if not isinstance(path_list, list):
            raise ValueError()
    except (ValueError, TypeError):
        raise HTTPException(422, "paths must be a JSON list")
    results = []
    for i, file in enumerate(files):
        results.append(await _process_chat_file(file, path_list[i] if i < len(path_list) else file.filename, db, current_session))
    return BatchUploadResponse(files=results, total_files=len(results))


@router.post("/investigations", response_model=InvestigationCreateResponse, status_code=202)
async def create_investigation(
    body: InvestigationCreate,
    background_tasks: BackgroundTasks,
    current_session: SessionModel = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new investigation with session validation.
    Implements: FR-PLN-1, API_Reference.md §4 POST /investigations
    """
    active_session = current_session
    attachments_data = await validate_attachments(body.attachments or [], current_session, db)

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
    request: Request,
    current_session: SessionModel = Depends(get_current_session),
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
    await assert_owner(investigation, current_session, db)

    async def event_generator() -> AsyncGenerator[str, None]:
        last_event_index = 0
        iterations = 0
        max_iterations = 1200  # Safety break after 10 minutes (1200 * 0.5s)

        while iterations < max_iterations:
            if await request.is_disconnected():
                break
            iterations += 1

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

                if status == "failed":
                    yield f"event: investigation_failed\ndata: {json.dumps({'investigation_id': investigation_id, 'message': 'Investigation failed; inspect task events'})}\n\n"
                    break
                if status == "complete":
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
    current_session: SessionModel = Depends(get_current_session),
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
    await assert_owner(investigation, current_session, db)

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
        report_dict["query"] = investigation.query or "Investigation"
    if "findings" not in report_dict or report_dict["findings"] is None:
        report_dict["findings"] = []
    return report_dict


@router.get("/investigations/{investigation_id}/plan", response_model=InvestigationPlanResponse)
async def get_plan(
    investigation_id: str,
    current_session: SessionModel = Depends(get_current_session),
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
    await assert_owner(investigation, current_session, db)

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
