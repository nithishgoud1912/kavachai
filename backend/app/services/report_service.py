"""
KavachAI — Report Service
Implements: FR-RPT-1 (assemble structured report from evidence + verification)

Assembles the final report response from the Investigation model data.
"""

from datetime import datetime, timezone
from typing import Optional

from app.models.report import (
    InvestigationReport, Finding, FindingEvidence,
)
from app.agents.base import VerificationResult, EvidenceBundle


def build_report(
    investigation_id: str,
    query: str,
    verification_result: VerificationResult,
    evidence_bundle: EvidenceBundle,
    pid_chain: Optional[list[str]] = None,
) -> dict:
    """
    Assemble the final investigation report.
    Implements: FR-RPT-1

    Returns:
        Dict matching the InvestigationReport schema (API_Reference.md §4)
    """
    # Build findings with evidence
    findings = []
    for vf in verification_result.findings:
        evidence = []
        for ev in vf.evidence:
            evidence.append({
                "type": ev.type,
                "source_id": ev.source_id,
                "label": ev.label,
                "page": ev.page,
                "section": ev.section,
            })

        findings.append({
            "id": vf.id,
            "title": vf.title,
            "detail": vf.detail,
            "verification_status": vf.verification_status.value,
            "evidence": evidence,
        })

    # Determine overall status
    overall_status = _determine_overall_status(verification_result)

    # Build condition summary
    condition_summary = _determine_condition_summary(verification_result)

    # Build conclusion
    conclusion = _build_conclusion(verification_result, findings)

    return {
        "investigation_id": investigation_id,
        "query": query,
        "overall_status": overall_status,
        "condition_summary": condition_summary,
        "findings": findings,
        "pid_relationship": pid_chain,
        "conclusion": conclusion,
        "confidence": verification_result.overall_confidence,
        "verification_status": verification_result.overall_status,
        "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
    }


def _determine_overall_status(result: VerificationResult) -> str:
    """Map verification result to overall report status."""
    if result.overall_status == "unverified":
        return "insufficient_evidence"
    if result.overall_confidence >= 80:
        return "attention_required"  # High confidence that something needs attention
    if result.overall_confidence >= 50:
        return "attention_required"
    return "normal"


def _determine_condition_summary(result: VerificationResult) -> str:
    """Generate a one-line condition summary."""
    supported_count = sum(
        1 for f in result.findings
        if f.verification_status.value == "supported"
    )

    if supported_count == 0:
        return "Insufficient evidence for conclusion"
    if result.overall_confidence >= 80:
        return "Potential deterioration detected"
    return "Condition under review"


def _build_conclusion(result: VerificationResult, findings: list) -> str:
    """Build a conclusion paragraph from the verified findings."""
    if result.overall_status == "unverified":
        return "Insufficient evidence to draw a reliable conclusion. Additional data or inspection is recommended."

    supported = [f for f in findings if f["verification_status"] == "supported"]
    if not supported:
        return "The available evidence is inconclusive. Further investigation is recommended."

    return (
        "The available evidence indicates a condition change over the observed period. "
        "Engineering inspection is recommended. "
        "The evidence does NOT establish imminent failure."
    )
