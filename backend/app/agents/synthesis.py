"""
KavachAI — Synthesis (LLM Reasoning)
Implements: FR-SYN-1 (only EvidenceBundle as input, never raw docs),
            FR-SYN-2 (draft findings with evidence references),
            FR-SYN-3 (LLM never does arithmetic — Data Agent owns that)

Contract (API_Reference.md §8.6):
    synthesize(evidence_bundle: EvidenceBundle) -> DraftFindings

Uses Model Router for all LLM calls (NFR-MNT-2).
"""

import json
from typing import Optional

from app.agents.base import (
    EvidenceBundle, DraftFindings, DraftFinding, EvidenceItem,
)
from app.orchestrator.model_router import model_router


SYNTHESIS_SYSTEM_PROMPT = """You are the Synthesis Agent for KavachAI, an industrial investigation system.
You receive a structured evidence bundle gathered by specialist agents and must produce draft findings.

Rules:
1. ONLY use information present in the evidence bundle. Do NOT invent facts.
2. NEVER perform arithmetic or numeric calculations — the Data Agent has already computed all trends and percentages. Quote those numbers exactly as given.
3. Each finding must reference which evidence item(s) support it.
4. Produce separate, distinct findings for each type of evidence present:
   - Generate finding(s) for Document Evidence (inspection/maintenance reports).
   - Generate finding(s) for Data Analysis (sensor operating trends, percentage changes, threshold breaches).
   - Generate finding(s) for P&ID / Specification Evidence if present.
5. Generate distinct findings for each operational trend, threshold breach, and inspection observation. Aim for at least 2 distinct findings when multiple evidence sources exist. Do NOT collapse separate evidence types into a single combined finding.
6. Be precise and technical. Use specific values, not vague language.
7. If the evidence is insufficient for a confident conclusion, say so explicitly.

Respond with ONLY valid JSON in this exact format:
{
  "condition_summary": "Brief one-line summary",
  "findings": [
    {
      "id": "f1",
      "title": "Finding title",
      "detail": "Detailed finding with specific values from evidence",
      "evidence_refs": ["evidence item labels or source_ids that support this"]
    }
  ]
}"""


async def synthesize(evidence_bundle: EvidenceBundle) -> DraftFindings:
    """
    Synthesize draft findings from structured evidence.
    Implements: FR-SYN-1, FR-SYN-2, FR-SYN-3

    FR-SYN-1 ENFORCED: This function's signature accepts ONLY EvidenceBundle,
    never raw strings or documents. The type system prevents misuse.

    Args:
        evidence_bundle: structured evidence from Document/Data/Vision/RAG agents

    Returns:
        DraftFindings with each finding tagged to supporting evidence
    """
    # Build a concise evidence summary for the LLM prompt
    evidence_text = _format_evidence_bundle(evidence_bundle)

    prompt = f"""Analyze the following evidence bundle and produce draft findings.

EVIDENCE BUNDLE:
{evidence_text}

Produce findings that synthesize this evidence. Each finding must cite specific evidence items. Respond with JSON only."""

    try:
        response = await model_router.generate(
            prompt=prompt,
            task_type="text_reasoning",
            system=SYNTHESIS_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=1024,
            format="json",
        )

        synthesis_data = json.loads(response)

        findings = []
        for i, f in enumerate(synthesis_data.get("findings", [])):
            finding_id = f.get("id", f"f{i+1}")

            # Map evidence refs back to actual evidence items
            evidence_refs = f.get("evidence_refs", [])
            evidence_items = _resolve_evidence_refs(evidence_refs, evidence_bundle)

            findings.append(DraftFinding(
                id=finding_id,
                title=f.get("title", f"Finding {i+1}"),
                detail=f.get("detail", ""),
                evidence=evidence_items,
            ))

        # Safeguard: If data findings exist but were omitted from findings, ensure representation
        has_data_finding = any(any(ev.type == "dataset" for ev in f.evidence) for f in findings)
        if not has_data_finding and evidence_bundle.data_findings and evidence_bundle.data_findings.data_points:
            df = evidence_bundle.data_findings
            findings.append(DraftFinding(
                id=f"f{len(findings)+1}",
                title=f"Operating Parameter Trend: {df.trend.value.capitalize()}",
                detail=f"Sensor analysis indicates a {df.trend.value} trend ({df.pct_change}% change) across recorded intervals.",
                evidence=[EvidenceItem(type="dataset", source_id="dataset", label="Operating Data")],
            ))

        return DraftFindings(
            findings=findings,
            condition_summary=synthesis_data.get("condition_summary", ""),
        )

    except json.JSONDecodeError:
        # Fallback: create a basic finding from evidence
        return _fallback_synthesis(evidence_bundle)
    except Exception as e:
        raise RuntimeError(f"Synthesis failed: {type(e).__name__}: {e}")


def _format_evidence_bundle(bundle: EvidenceBundle) -> str:
    """Format evidence bundle as concise text for the LLM prompt."""
    parts = []

    if bundle.document_findings:
        parts.append("DOCUMENT EVIDENCE:")
        for doc in bundle.document_findings:
            parts.append(f"  - Source {doc.source_id} (p.{doc.page}): {doc.chunk_text[:200]}")

    if bundle.data_findings:
        df = bundle.data_findings
        parts.append("DATA ANALYSIS (computed by Data Agent — do NOT recalculate):")
        parts.append(f"  - Trend: {df.trend.value}")
        parts.append(f"  - Percentage change: {df.pct_change}%")
        if df.threshold_breach is not None:
            parts.append(f"  - Threshold breach: {df.threshold_breach}")
        if df.data_points:
            points_str = ", ".join(
                f"{dp.timestamp}: {dp.value} {dp.unit}" for dp in df.data_points
            )
            parts.append(f"  - Data points: {points_str}")

    if bundle.vision_findings and bundle.vision_findings.found:
        vf = bundle.vision_findings
        parts.append("P&ID ANALYSIS:")
        parts.append(f"  - Equipment found: yes (confidence: {vf.confidence})")
        parts.append(f"  - Connected equipment: {', '.join(vf.connections)}")

    if bundle.spec_findings:
        parts.append("SPECIFICATION/THRESHOLD EVIDENCE:")
        for spec in bundle.spec_findings:
            section_str = f" (§{spec.section})" if spec.section else ""
            parts.append(f"  - Source {spec.source_id}{section_str}: {spec.chunk_text[:200]}")

    return "\n".join(parts) if parts else "No evidence available."


def _resolve_evidence_refs(refs: list[str], bundle: EvidenceBundle) -> list[EvidenceItem]:
    """Map evidence reference strings back to EvidenceItem objects."""
    items = []

    # Use existing evidence_items from the bundle if available
    if bundle.evidence_items:
        return bundle.evidence_items[:len(refs)] if refs else bundle.evidence_items

    # Build from individual findings
    for doc in bundle.document_findings:
        items.append(EvidenceItem(
            type="document",
            source_id=doc.source_id,
            label="Document",
            page=doc.page,
        ))

    if bundle.data_findings and bundle.data_findings.data_points:
        items.append(EvidenceItem(
            type="dataset",
            source_id="dataset",
            label="Operating Data",
        ))

    for spec in bundle.spec_findings:
        items.append(EvidenceItem(
            type="document",
            source_id=spec.source_id,
            label="Specification",
            page=spec.page,
            section=spec.section,
        ))

    return items


def _fallback_synthesis(bundle: EvidenceBundle) -> DraftFindings:
    """Fallback if LLM returns invalid JSON — build basic findings from evidence."""
    findings = []

    if bundle.data_findings:
        df = bundle.data_findings
        findings.append(DraftFinding(
            id="f1",
            title=f"{df.trend.value.capitalize()} trend detected",
            detail=f"Values changed by {df.pct_change}%",
            evidence=[EvidenceItem(type="dataset", source_id="dataset", label="Operating Data")],
        ))

    if not findings:
        findings.append(DraftFinding(
            id="f1",
            title="Evidence reviewed",
            detail="Evidence was gathered but synthesis produced no structured findings.",
            evidence=[],
        ))

    return DraftFindings(findings=findings, condition_summary="Review required")
