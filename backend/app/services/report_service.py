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

    # Build dynamic, evidence-grounded conclusion
    conclusion = _build_conclusion(verification_result, findings, evidence_bundle, query)

    # Extract vision findings
    vision_obs = None
    b_box = None
    if evidence_bundle and evidence_bundle.vision_findings and evidence_bundle.vision_findings.found:
        vf = evidence_bundle.vision_findings
        vision_obs = getattr(vf, "visual_description", None)
        b_box = getattr(vf, "bounding_box", None)

    # Extract telemetry trend points
    telemetry_trend = None
    if evidence_bundle and evidence_bundle.data_findings and evidence_bundle.data_findings.data_points:
        telemetry_trend = [
            {"label": dp.timestamp, "value": dp.value, "unit": dp.unit}
            for dp in evidence_bundle.data_findings.data_points
        ]

    process_topology = [{"tag": tag, "name": tag, "role": "Observed connection", "spec": "Not established", "status": "Unknown"}
                        for tag in (pid_chain or [])]

    return {
        "investigation_id": investigation_id,
        "query": query,
        "overall_status": overall_status,
        "condition_summary": condition_summary,
        "findings": findings,
        "pid_relationship": pid_chain,
        "vision_observation": vision_obs,
        "bounding_box": b_box,
        "telemetry_trend": telemetry_trend,
        "process_topology": process_topology,
        "bypass_loops": [],
        "conclusion": conclusion,
        "confidence": verification_result.overall_confidence,
        "verification_status": verification_result.overall_status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _determine_overall_status(result: VerificationResult) -> str:
    """Map verification result to overall report status."""
    if result.overall_status == "unverified":
        return "insufficient_evidence"
    return "attention_required"  # A report requires human review; confidence is not equipment condition.


def _determine_condition_summary(result: VerificationResult) -> str:
    """Generate a one-line condition summary."""
    supported_count = sum(
        1 for f in result.findings
        if f.verification_status.value == "supported"
    )

    if supported_count == 0:
        return "Insufficient evidence for conclusion"
    return "Evidence reviewed; engineering assessment required"


def _build_conclusion(
    result: VerificationResult,
    findings: list,
    evidence_bundle: Optional[EvidenceBundle] = None,
    query: Optional[str] = None,
) -> str:
    """
    Build a dynamic, technically rigorous conclusion paragraph synthesized from verified
    findings, multimodal visual grounding (Qwen2.5-VL), sensor trends, and cascading risk analysis.
    """
    if result.overall_status == "unverified":
        return "Insufficient evidence to draw a reliable conclusion. Additional diagnostic telemetry or inspection is recommended."

    supported = [f for f in findings if f.get("verification_status") == "supported"]
    if not supported:
        return "The available evidence is inconclusive. Further technical investigation is recommended."

    return " ".join(f.get("detail", "") for f in supported if f.get("detail"))


async def render_briefing_draft(investigation_id: str) -> str:
    """
    Render a draft briefing note for an investigation.
    Used by the HITL approval graph to generate the draft for officer review.

    Args:
        investigation_id: the investigation to render

    Returns:
        Plain text draft briefing note content
    """
    from app.db.database import async_session
    from app.db.sql_models import Investigation
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(
            select(Investigation).where(Investigation.id == investigation_id)
        )
        inv = result.scalar_one_or_none()

    if not inv or inv.status != 'complete' or not inv.report:
        raise ValueError('Completed report required for approval')
    report = inv.report
    sections = [f"BRIEFING NOTE — Investigation {investigation_id}", f"Query: {inv.query}",
                f"Verification: {report.get('verification_status', 'unverified')}"]
    for finding in report.get('findings', []):
        sections.append(f"{finding.get('title', 'Finding')}: {finding.get('detail', '')}")
        sections.append(f"Support: {finding.get('verification_status', 'unverified')}")
        for evidence in finding.get('evidence', []):
            sections.append(f"Source: {evidence.get('source_id')} page {evidence.get('page')}")
    sections.extend([report.get('conclusion', ''), 'Pending officer review'])
    return '\n'.join(sections)
