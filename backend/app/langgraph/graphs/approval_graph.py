"""
KavachAI — LangGraph Human-in-the-Loop Approval Graph
Implements: Phase 4.1 — HITL note review workflow with interrupt/Command pattern.

Graph flow:
    START → draft_note → human_review (interrupt)
          → APPROVED → generate_final → audit_log → END
          → REJECTED → END
          → CONFLICT → handle_conflict → draft_note (re-draft loop)
"""

import logging
from enum import Enum
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

logger = logging.getLogger("kavachai.approval_graph")


class ApprovalAction(str, Enum):
    """Possible outcomes of human review."""
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICT = "conflict"


class ApprovalState(TypedDict):
    """State schema for the approval workflow."""
    investigation_id: str
    session_id: str
    draft_note_text: str
    draft_version: int
    approval_status: Optional[ApprovalAction]
    officer_edits: Optional[str]
    final_docx_url: Optional[str]


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

async def draft_note_node(state: ApprovalState) -> dict:
    """Generate or re-generate the draft briefing note."""
    try:
        from app.services.report_service import render_briefing_draft
        draft = await render_briefing_draft(state["investigation_id"])
    except Exception as e:
        logger.warning("Briefing draft render failed, using fallback: %s", e)
        draft = (
            f"Investigation {state['investigation_id']} — Draft Briefing Note\n\n"
            "Findings and recommendations pending officer review."
        )
    return {
        "draft_note_text": draft,
        "draft_version": state.get("draft_version", 0) + 1,
    }


async def human_review_node(state: ApprovalState) -> dict:
    """
    Pause execution for human review using LangGraph interrupt().

    The interrupt payload tells the frontend what to display.
    Execution resumes when the officer submits via Command(resume=...).
    """
    review_data = interrupt({
        "type": "approval_required",
        "investigation_id": state["investigation_id"],
        "draft_text": state["draft_note_text"],
        "draft_version": state["draft_version"],
    })

    # Version conflict detection
    if review_data.get("draft_version") != state["draft_version"]:
        return {"approval_status": ApprovalAction.CONFLICT}

    # Parse the officer's action
    action_str = review_data.get("action", "rejected")
    try:
        status = ApprovalAction(action_str)
    except ValueError:
        status = ApprovalAction.REJECTED

    return {
        "approval_status": status,
        "officer_edits": review_data.get("edits"),
    }


def route_after_review(state: ApprovalState) -> ApprovalAction:
    """Route based on the officer's approval decision."""
    return state["approval_status"]


async def handle_conflict_node(state: ApprovalState) -> dict:
    """Handle version conflict by flagging and re-drafting."""
    logger.warning(
        "Version conflict on investigation %s (v%d). Re-drafting.",
        state["investigation_id"],
        state["draft_version"],
    )
    return {
        "draft_note_text": (
            f"[VERSION CONFLICT on v{state['draft_version']}] "
            "The draft has been updated since your review began. "
            "A new version is being prepared."
        ),
    }


async def generate_final_node(state: ApprovalState) -> dict:
    """Generate the final approved DOCX document."""
    try:
        from app.services.document_export import generate_briefing_docx

        content = state.get("officer_edits") or state["draft_note_text"]
        url = await generate_briefing_docx(
            state["investigation_id"],
            content,
        )
        return {"final_docx_url": f"/api/v1/exports/{state['investigation_id']}/docx"}
    except Exception as e:
        logger.error("Final DOCX generation failed: %s", e)
        raise RuntimeError("Approved artifact generation failed") from e


async def audit_log_node(state: ApprovalState) -> dict:
    from app.db.database import async_session
    from app.services.security_audit import append_security_event
    from app.db.sql_models import Session
    async with async_session() as db:
        session = await db.get(Session, state['session_id'])
        await append_security_event(db, event_type="APPROVAL_DECISION", outcome=str(state.get('approval_status')),
                                    actor_user_id=session.user_id if session else None,
                                    resource_type="investigation", resource_id=state['investigation_id'],
                                    detail={"version":state['draft_version'], "artifact":state.get('final_docx_url')})
    return {}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_approval_graph(checkpointer):
    """
    Build and compile the HITL approval StateGraph.

    Features:
    - interrupt() pauses for human review
    - Command(resume=...) resumes with officer input
    - Version conflict detection prevents stale approvals
    - Generates final DOCX on approval
    - Immutable audit logging
    """
    graph = StateGraph(ApprovalState)

    graph.add_node("draft_note", draft_note_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("handle_conflict", handle_conflict_node)
    graph.add_node("generate_final", generate_final_node)
    graph.add_node("audit_log", audit_log_node)

    graph.add_edge(START, "draft_note")
    graph.add_edge("draft_note", "human_review")

    graph.add_conditional_edges("human_review", route_after_review, {
        ApprovalAction.APPROVED: "generate_final",
        ApprovalAction.REJECTED: "audit_log",
        ApprovalAction.CONFLICT: "handle_conflict",
    })
    graph.add_edge("handle_conflict", "draft_note")
    graph.add_edge("generate_final", "audit_log")
    graph.add_edge("audit_log", END)

    return graph.compile(checkpointer=checkpointer)
