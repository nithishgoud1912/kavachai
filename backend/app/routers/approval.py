"""
KavachAI — Approval Router
Implements: Phase 4.1 — Authenticated FastAPI endpoints for HITL approval workflow.

Endpoints:
  POST /api/v1/investigations/{id}/approval/start   — Start approval workflow
  POST /api/v1/investigations/{id}/approval/resume  — Resume with officer decision
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from langgraph.types import Command

from app.db.database import get_db, async_session
from app.db.sql_models import Investigation
from app.deps import get_current_session
from app.db.sql_models import Session as SessionModel

router = APIRouter(prefix="/api/v1/investigations", tags=["approval"])


class ReviewPayload(BaseModel):
    """Officer review submission."""
    action: str  # "approved" | "rejected"
    edits: Optional[str] = None
    draft_version: int


@router.post("/{id}/approval/start")
async def start_approval(
    id: str,
    request: Request,
    session: SessionModel = Depends(get_current_session),
):
    """
    Start the approval workflow for an investigation.

    Initiates the HITL approval graph which:
    1. Generates a draft briefing note
    2. Pauses at human_review (interrupt) awaiting officer decision

    Returns the draft text and version for the officer to review.
    """
    # Verify investigation ownership
    async with async_session() as db:
        res = await db.execute(
            select(Investigation).where(
                Investigation.id == id,
                Investigation.session_id == session.id,
            )
        )
        inv = res.scalar_one_or_none()
        if not inv:
            raise HTTPException(404, "Investigation not found or unauthorized")

    graph = request.app.state.approval_graph
    config = {"configurable": {"thread_id": f"approval_{id}"}}

    # Check if already started (idempotent)
    curr_state = await graph.aget_state(config)
    if not curr_state.values:
        # First invocation — start the workflow
        await graph.ainvoke(
            {
                "investigation_id": id,
                "session_id": session.id,
                "draft_note_text": "",
                "draft_version": 0,
            },
            config=config,
        )

    state = await graph.aget_state(config)
    return {
        "status": "pending_review",
        "draft_text": state.values.get("draft_note_text"),
        "draft_version": state.values.get("draft_version"),
    }


@router.post("/{id}/approval/resume")
async def resume_approval(
    id: str,
    body: ReviewPayload,
    request: Request,
    session: SessionModel = Depends(get_current_session),
):
    """
    Resume the approval workflow with the officer's decision.

    Accepts:
    - action: "approved" → generates final DOCX and logs audit entry
    - action: "rejected" → ends workflow
    - draft_version: must match current version (conflict detection)
    - edits: optional officer modifications to the draft text
    """
    # Verify investigation ownership
    async with async_session() as db:
        res = await db.execute(
            select(Investigation).where(
                Investigation.id == id,
                Investigation.session_id == session.id,
            )
        )
        if not res.scalar_one_or_none():
            raise HTTPException(404, "Investigation not found or unauthorized")

    graph = request.app.state.approval_graph
    config = {"configurable": {"thread_id": f"approval_{id}"}}

    # Verify the workflow is actually waiting for approval
    state = await graph.aget_state(config)
    if not state.next:
        raise HTTPException(400, "Workflow is not awaiting approval")

    # Resume the graph with the officer's decision
    result = await graph.ainvoke(
        Command(resume={
            "action": body.action,
            "edits": body.edits,
            "draft_version": body.draft_version,
        }),
        config=config,
    )

    return {
        "status": result.get("approval_status"),
        "final_docx_url": result.get("final_docx_url"),
    }
