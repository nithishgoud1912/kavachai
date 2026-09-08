"""
KavachAI — Verification Agent
Implements: FR-VER-1 (classify findings as Supported/Partially/Unsupported),
            FR-VER-2 (remove or flag unsupported findings),
            FR-VER-3 (assign confidence score 0-100),
            FR-VER-4 (insufficient_evidence if zero supported findings)

Contract (API_Reference.md §8.7):
    verify(draft_findings: DraftFindings, evidence_bundle: EvidenceBundle)
        -> {findings: [Finding], overall_confidence: int, overall_status: str}

Uses Model Router for all LLM calls (NFR-MNT-2).
"""

import json
from typing import Optional

from app.agents.base import (
    DraftFindings, EvidenceBundle, VerificationResult,
    VerifiedFinding, VerificationStatus,
)
from app.orchestrator.model_router import model_router


VERIFICATION_SYSTEM_PROMPT = """You are the Verification Agent for KavachAI, an industrial investigation system.
Your job is to check each draft finding against the evidence bundle and classify it.

For EACH finding, determine:
- "supported": The evidence directly and clearly supports the finding's claim.
- "partially_supported": Some evidence exists but it's incomplete or indirect.
- "unsupported": No evidence in the bundle supports this claim.

Rules:
1. Be strict — a finding claiming a specific number must have that number in the evidence.
2. A finding quoting Data Agent analysis (trend, percentage) is "supported" if the data analysis result confirms it.
3. NEVER mark a finding as "supported" just because it sounds plausible — it must be traceable to evidence.
4. Assign an overall confidence score (0-100) based on how well the evidence supports the conclusions.

Respond with ONLY valid JSON:
{
  "findings": [
    {
      "id": "f1",
      "verification_status": "supported|partially_supported|unsupported",
      "reason": "Brief reason for the classification"
    }
  ],
  "overall_confidence": 85,
  "overall_status": "verified|partially_verified|unverified"
}"""


async def verify(
    draft_findings: DraftFindings,
    evidence_bundle: EvidenceBundle,
) -> VerificationResult:
    """
    Verify draft findings against the evidence bundle.
    Implements: FR-VER-1, FR-VER-2, FR-VER-3, FR-VER-4

    Args:
        draft_findings: output from synthesis agent
        evidence_bundle: the same evidence the synthesis agent saw

    Returns:
        VerificationResult with classified findings and confidence score
    """
    from app.agents.synthesis import _format_evidence_bundle

    # FR-VER-4: If evidence bundle has zero findings, mark all unsupported immediately
    if (
        not evidence_bundle.document_findings
        and not evidence_bundle.data_findings
        and not (evidence_bundle.vision_findings and evidence_bundle.vision_findings.found)
        and not evidence_bundle.spec_findings
    ):
        return VerificationResult(
            findings=[
                VerifiedFinding(
                    id=f.id,
                    title=f.title,
                    detail=f"[UNVERIFIED] {f.detail}",
                    verification_status=VerificationStatus.UNSUPPORTED,
                    evidence=[],
                )
                for f in draft_findings.findings
            ],
            overall_confidence=0,
            overall_status="unverified",
        )

    # Build verification prompt
    findings_text = "\n".join(
        f"  Finding {f.id}: {f.title} — {f.detail}"
        for f in draft_findings.findings
    )
    evidence_text = _format_evidence_bundle(evidence_bundle)


    prompt = f"""Verify each draft finding against the evidence bundle.

DRAFT FINDINGS:
{findings_text}

EVIDENCE BUNDLE:
{evidence_text}

Classify each finding and assign overall confidence. Respond with JSON only."""

    try:
        response = await model_router.generate(
            prompt=prompt,
            task_type="text_reasoning",
            system=VERIFICATION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=512,
            format="json",
        )

        ver_data = json.loads(response)
        return _build_result(draft_findings, ver_data)

    except json.JSONDecodeError:
        # Fallback: conservatively mark all as partially_supported
        return _fallback_verification(draft_findings)
    except Exception as e:
        raise RuntimeError(f"Verification failed: {type(e).__name__}: {e}")


def _build_result(draft_findings: DraftFindings, ver_data: dict) -> VerificationResult:
    """Build VerificationResult from LLM verification output."""
    ver_map = {}
    for vf in ver_data.get("findings", []):
        f_id = vf.get("id") or vf.get("finding_id", "")
        f_status = vf.get("verification_status") or vf.get("status", "partially_supported")
        ver_map[f_id] = f_status


    verified_findings = []
    supported_count = 0

    for df in draft_findings.findings:
        status_str = ver_map.get(df.id, "partially_supported")

        # Validate status
        try:
            status = VerificationStatus(status_str)
        except ValueError:
            status = VerificationStatus.PARTIALLY_SUPPORTED

        # FR-VER-2: Remove or flag unsupported findings
        if status == VerificationStatus.UNSUPPORTED:
            # Flag but include with warning (don't silently drop)
            df_detail = f"[UNVERIFIED] {df.detail}"
        else:
            df_detail = df.detail

        if status == VerificationStatus.SUPPORTED:
            supported_count += 1

        verified_findings.append(VerifiedFinding(
            id=df.id,
            title=df.title,
            detail=df_detail,
            verification_status=status,
            evidence=df.evidence,
        ))

    # FR-VER-3: Overall confidence
    overall_confidence = ver_data.get("overall_confidence", 50)
    overall_confidence = max(0, min(100, int(overall_confidence)))

    # FR-VER-4: If zero supported findings → insufficient_evidence pathway
    overall_status = ver_data.get("overall_status", "partially_verified")

    if supported_count == 0:
        overall_status = "unverified"
        overall_confidence = min(overall_confidence, 20)

    return VerificationResult(
        findings=verified_findings,
        overall_confidence=overall_confidence,
        overall_status=overall_status,
    )


def _fallback_verification(draft_findings: DraftFindings) -> VerificationResult:
    """Conservative fallback if LLM returns invalid JSON."""
    verified_findings = []
    for df in draft_findings.findings:
        verified_findings.append(VerifiedFinding(
            id=df.id,
            title=df.title,
            detail=df.detail,
            verification_status=VerificationStatus.PARTIALLY_SUPPORTED,
            evidence=df.evidence,
        ))

    return VerificationResult(
        findings=verified_findings,
        overall_confidence=50,
        overall_status="partially_verified",
    )
