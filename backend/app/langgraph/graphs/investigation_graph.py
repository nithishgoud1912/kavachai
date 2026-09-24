"""
KavachAI — LangGraph Investigation StateGraph
Implements: Phase 3.3 — Dynamic fan-out (Send API), verification retry,
            and end-to-end investigation orchestration.

Graph flow:
    START → classify_request → create_plan
          → [Send: gather_documents, run_ocr, analyze_data]
          → validate_evidence
          → (sufficient) → synthesize → verify → generate_deliverables → END
          → (insufficient, retry<2) → revise_plan → create_plan (retry loop)
"""

import logging
from typing import List, Dict, Any

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from sqlalchemy import select

from app.langgraph.state import InvestigationState
from app.db.database import async_session
from app.db.sql_models import Dataset
from app.agents import document_agent, data_agent
from app.agents.synthesis import synthesize as synthesis_synthesize
from app.agents.verification import verify as verification_verify
from app.agents.base import EvidenceBundle, DraftFindings

logger = logging.getLogger("kavachai.investigation_graph")


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def route_dispatched_agents(state: InvestigationState) -> List[Send]:
    """Dynamic fan-out via LangGraph Send API. Only invokes required agents."""
    sends = []
    attempt = state.get("attempt_id", 1)
    for agent_name in state.get("dispatched_agents", []):
        sends.append(Send(agent_name, {**state, "attempt_id": attempt}))
    return sends


def check_sufficiency(state: InvestigationState) -> str:
    """Route after evidence validation: sufficient → synthesize, insufficient → retry."""
    if state.get("needs_retry", False):
        return "insufficient" if state.get("retry_count", 0) < 2 else "failed"
    return "sufficient"


def check_verification(state: InvestigationState) -> str:
    """Route after verification: verified → deliverables, unverified → retry."""
    vr = state.get("verification_result", {})
    if not vr.get("passed", False):
        return "unverified" if state.get("retry_count", 0) < 2 else "failed"
    return "verified"


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

async def classify_request_node(state: InvestigationState) -> dict:
    """Classify the investigation request and determine task type."""
    query_lower = state.get("query", "").lower()

    # Simple classification based on keywords
    if any(kw in query_lower for kw in ["fire", "emergency", "evacuation"]):
        task_type = "emergency_response"
    elif any(kw in query_lower for kw in ["vibration", "pump", "deteriorat", "failure"]):
        task_type = "root_cause_analysis"
    elif any(kw in query_lower for kw in ["inspect", "maintenance", "schedule"]):
        task_type = "maintenance_review"
    else:
        task_type = "root_cause_analysis"

    return {
        "task_type": task_type,
        "attempt_id": 1,
        "event_log": [{"agent": "classifier", "status": "completed", "task_type": task_type}],
    }


async def create_plan_node(state: InvestigationState) -> dict:
    """Create a plan by deciding which agents to dispatch."""
    dispatched = ["gather_documents"]

    # Add OCR agent if attachments are present
    if state.get("attachment_ids"):
        dispatched.append("run_ocr")

    # Check if operational dataset exists for analysis
    try:
        async with async_session() as db:
            res = await db.execute(
                select(Dataset).where(Dataset.status == "ready").limit(1)
            )
            if res.scalar_one_or_none():
                dispatched.append("analyze_data")
    except Exception as e:
        logger.warning("Dataset check failed: %s", e)

    return {
        "dispatched_agents": dispatched,
        "event_log": [{"agent": "planner", "status": "completed", "dispatched": dispatched}],
    }


async def gather_documents_node(state: InvestigationState) -> dict:
    """Gather relevant documents from the knowledge base."""
    try:
        from app.access import authorized_sources
        from app.db.sql_models import Session
        async with async_session() as db:
            session = await db.get(Session, state.get("session_id"))
            sources = await authorized_sources(session, db) if session else []
        chunks = await document_agent.retrieve(
            sub_task_goal=state["query"],
            filters={"source_ids": sources},
        )
        return {
            "evidence_bundle": {"documents": [c.model_dump() for c in chunks]},
            "event_log": [{"agent": "document_agent", "status": "completed", "count": len(chunks)}],
        }
    except Exception as e:
        logger.error("Document gathering failed: %s", e)
        return {
            "evidence_bundle": {"documents": []},
            "event_log": [{"agent": "document_agent", "status": "failed", "error": str(e)}],
        }


async def run_ocr_node(state: InvestigationState) -> dict:
    """Run OCR on attached files using the tiered pipeline."""
    try:
        from app.ingestion.extract import extract_text_with_ocr
        from app.db.object_store import object_store

        from app.access import authorized_sources
        from app.db.sql_models import Session
        async with async_session() as db:
            session = await db.get(Session, state.get("session_id"))
            sources = await authorized_sources(session, db) if session else []
        ocr_results = []
        for attachment_id in state.get("attachment_ids", []):
            try:
                if attachment_id not in sources: raise ValueError("Unauthorized source")
                file_data = object_store.get_raw_file(attachment_id)
                if file_data:
                    pages = await extract_text_with_ocr(
                        file_data[0],
                        file_data[1],
                    )
                    ocr_results.extend([p["text"] for p in pages if p.get("text")])
            except Exception as e:
                logger.warning("OCR failed for attachment %s: %s", attachment_id, e)

        return {
            "evidence_bundle": {"ocr": ocr_results if ocr_results else ["No OCR content extracted"]},
            "event_log": [{"agent": "ocr_agent", "status": "completed", "pages": len(ocr_results)}],
        }
    except Exception as e:
        logger.error("OCR node failed: %s", e)
        return {
            "evidence_bundle": {"ocr": []},
            "event_log": [{"agent": "ocr_agent", "status": "failed", "error": str(e)}],
        }


async def analyze_data_node(state: InvestigationState) -> dict:
    """Analyze operational data from available datasets."""
    try:
        async with async_session() as db:
            res = await db.execute(
                select(Dataset).where(Dataset.status == "ready").limit(1)
            )
            dataset = res.scalar_one_or_none()

        if not dataset:
            return {
                "event_log": [{"agent": "data_agent", "status": "skipped", "reason": "no dataset"}],
            }

        analysis = data_agent.analyze(
            metric="vibration",
            equipment_id="P-102",
            dataset_id=dataset.id,
        )
        return {
            "evidence_bundle": {"telemetry": analysis.model_dump() if analysis else None},
            "event_log": [{"agent": "data_agent", "status": "completed"}],
        }
    except Exception as e:
        logger.error("Data analysis failed: %s", e)
        return {
            "event_log": [{"agent": "data_agent", "status": "failed", "error": str(e)}],
        }


async def validate_evidence_node(state: InvestigationState) -> dict:
    """Validate that sufficient evidence has been gathered."""
    eb = state.get("evidence_bundle") or {}
    has_documents = bool(eb.get("documents"))
    has_ocr = bool(eb.get("ocr"))
    has_telemetry = bool(eb.get("telemetry"))

    has_any_evidence = has_documents or has_ocr or has_telemetry

    if not has_any_evidence:
        return {
            "needs_retry": True,
            "retry_reason": "Insufficient evidence — no documents, OCR, or telemetry found",
            "retry_count": state.get("retry_count", 0) + 1,
            "attempt_id": state.get("attempt_id", 1) + 1,
            "event_log": [{
                "agent": "validator",
                "status": "insufficient",
                "retry_count": state.get("retry_count", 0) + 1,
            }],
        }
    return {
        "needs_retry": False,
        "event_log": [{"agent": "validator", "status": "sufficient"}],
    }


async def revise_plan_node(state: InvestigationState) -> dict:
    """Revise the investigation plan with expanded scope for retry."""
    reason = state.get("retry_reason", "general expansion")
    return {
        "query": state["query"],
        "retry_count": state.get("retry_count", 0) + 1,
        "event_log": [{"agent": "planner", "status": "revised", "reason": reason}],
    }


async def synthesize_node(state: InvestigationState) -> dict:
    """Synthesize evidence into draft findings."""
    try:
        eb = state.get("evidence_bundle") or {}

        # Build EvidenceBundle from the gathered evidence
        from app.agents.base import DocumentChunk
        doc_findings = []
        for doc in eb.get("documents", []):
            if isinstance(doc, dict):
                doc_findings.append(DocumentChunk(**doc))

        bundle = EvidenceBundle(document_findings=doc_findings)
        draft = await synthesis_synthesize(bundle)

        return {
            "draft_findings": draft.model_dump(),
            "event_log": [{"agent": "synthesis", "status": "completed", "findings": len(draft.findings)}],
        }
    except Exception as e:
        logger.error("Synthesis failed: %s", e)
        return {
            "draft_findings": {
                "findings": [],
                "condition_summary": f"Synthesis failed: {e}",
            },
            "event_log": [{"agent": "synthesis", "status": "failed", "error": str(e)}],
        }


async def verify_node(state: InvestigationState) -> dict:
    """Verify draft findings against evidence."""
    try:
        draft_data = state.get("draft_findings", {})
        draft = DraftFindings(**draft_data)

        eb = state.get("evidence_bundle") or {}
        from app.agents.base import DocumentChunk
        doc_findings = []
        for doc in eb.get("documents", []):
            if isinstance(doc, dict):
                doc_findings.append(DocumentChunk(**doc))

        bundle = EvidenceBundle(document_findings=doc_findings)
        vr = await verification_verify(draft, bundle)

        # Determine if verification passed
        passed = vr.overall_status in ("verified", "partially_verified")

        return {
            "verification_result": {**vr.model_dump(), "passed": passed},
            "event_log": [{"agent": "verification", "status": "completed", "passed": passed}],
        }
    except Exception as e:
        logger.error("Verification failed: %s", e)
        return {
            "verification_result": {"passed": False, "overall_status": "unverified"},
            "event_log": [{"agent": "verification", "status": "failed", "error": str(e)}],
        }


async def generate_deliverables_node(state: InvestigationState) -> dict:
    """Generate final deliverable documents (DOCX, XLSX, PPTX)."""
    try:
        from app.services.document_export import generate_all_exports

        investigation_id = state["investigation_id"]
        draft = state.get("draft_findings", {})
        report = state.get("verification_result", {})

        if not report.get("passed", False):
            raise ValueError("Verified report required before export")
        exports = await generate_all_exports(investigation_id, report={**draft, **report})
        return {
            "deliverables": exports,
            "event_log": [{"agent": "deliverables", "status": "completed", "formats": len(exports)}],
        }
    except Exception as e:
        logger.error("Deliverable generation failed: %s", e)
        return {
            "deliverables": [],
            "event_log": [{"agent": "deliverables", "status": "failed", "error": str(e)}],
        }


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_investigation_graph(checkpointer):
    """
    Build and compile the investigation StateGraph with dynamic fan-out.

    Returns a compiled graph with:
    - Dynamic agent dispatch via Send API
    - Evidence validation with retry logic (max 2 retries)
    - Synthesis + verification pipeline
    - Deliverable generation
    """
    graph = StateGraph(InvestigationState)

    # Add all nodes
    graph.add_node("classify_request", classify_request_node)
    graph.add_node("create_plan", create_plan_node)
    graph.add_node("gather_documents", gather_documents_node)
    graph.add_node("run_ocr", run_ocr_node)
    graph.add_node("analyze_data", analyze_data_node)
    graph.add_node("validate_evidence", validate_evidence_node)
    graph.add_node("revise_plan", revise_plan_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("verify", verify_node)
    graph.add_node("generate_deliverables", generate_deliverables_node)

    # Wire edges
    graph.add_edge(START, "classify_request")
    graph.add_edge("classify_request", "create_plan")

    # Dynamic fan-out using Send API
    graph.add_conditional_edges(
        "create_plan",
        route_dispatched_agents,
        ["gather_documents", "run_ocr", "analyze_data"],
    )

    # All parallel agents join at validate_evidence
    graph.add_edge("gather_documents", "validate_evidence")
    graph.add_edge("run_ocr", "validate_evidence")
    graph.add_edge("analyze_data", "validate_evidence")

    # Sufficiency check
    graph.add_conditional_edges("validate_evidence", check_sufficiency, {
        "sufficient": "synthesize",
        "insufficient": "revise_plan",
        "failed": END,
    })
    graph.add_edge("revise_plan", "create_plan")

    # Verification check
    graph.add_edge("synthesize", "verify")
    graph.add_conditional_edges("verify", check_verification, {
        "verified": "generate_deliverables",
        "unverified": "revise_plan",
        "failed": END,
    })
    graph.add_edge("generate_deliverables", END)

    return graph.compile(checkpointer=checkpointer)
