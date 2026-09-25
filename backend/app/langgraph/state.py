"""
LangGraph state definitions for KavachAI investigation workflows.
Person B owns this file exclusively.
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from operator import add


def merge_evidence(existing: dict | None, new: dict | None) -> dict:
    """Custom reducer that merges evidence bundles from parallel agent branches."""
    if existing is None:
        return new or {}
    if new is None:
        return existing
    merged = dict(existing)
    for key, value in new.items():
        if isinstance(merged.get(key), list) and isinstance(value, list):
            merged[key] = merged[key] + value
        elif value is not None:
            merged[key] = value
    return merged


class InvestigationState(TypedDict):
    investigation_id: str
    session_id: str
    query: str
    dataset_id: Optional[str]
    equipment_id: Optional[str]
    metric: Optional[str]
    attachment_ids: List[str]
    task_type: str
    selected_models: Dict[str, str]
    plan: Optional[Dict[str, Any]]

    # Evidence merged across parallel branches
    evidence_bundle: Annotated[Optional[Dict[str, Any]], merge_evidence]

    # Logs
    event_log: Annotated[List[Dict[str, Any]], add]

    # Dynamic dispatch tracking scoped to current attempt
    attempt_id: int
    dispatched_agents: List[str]

    # Iteration & verification
    retry_count: int
    needs_retry: bool
    retry_reason: Optional[str]

    # Deliverables
    draft_findings: Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    deliverables: List[Dict[str, Any]]
