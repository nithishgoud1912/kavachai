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
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator, Optional

from app.db.database import get_db, async_session
from app.db.sql_models import Investigation, Session as SessionModel
from app.models.investigation import (
    InvestigationCreate, InvestigationCreateResponse, InvestigationPlanResponse,
    SubTaskResponse,
)
from app.orchestrator.investigation import InvestigationRunner
from app.services.audit_service import create_audit_entry, resolve_audit_entry
from app.deps import get_current_session, get_optional_session

router = APIRouter(prefix="/api/v1", tags=["investigations"])

# In-memory store for active investigation runners
_runners: dict[str, InvestigationRunner] = {}


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

    # Create investigation
    investigation = Investigation(
        query=body.query,
        session_id=active_session.id,
        status="planning",
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

    return investigation.report


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
