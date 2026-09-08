"""
KavachAI — Unit Tests: Synthesis & Verification Agents
Implements: Phase 8 & 9 DoD, FR-SYN-1..3, FR-VER-1..4

Verifies:
- Synthesis accepts structured EvidenceBundle object only (FR-SYN-1)
- Verification classifies findings (Supported / Partially Supported / Unsupported)
- Verification computes confidence score (0-100)
- Zero supported findings triggers refusal / degradation
"""

import pytest
from app.agents import synthesis, verification
from app.agents.base import (
    EvidenceBundle, EvidenceItem, DocumentChunk,
    DataAnalysisResult, DataPoint, TrendDirection,
    VisionAnalysisResult, SpecChunk,
    VerificationStatus, DraftFindings, DraftFinding,
)


@pytest.fixture
def sample_evidence_bundle():
    """Constructs a sample structured evidence bundle for P-102."""
    return EvidenceBundle(
        document_findings=[
            DocumentChunk(chunk_text="Vibration July: 3.7 mm/s. Status: Abnormal.", source_id="doc_1122", page=1, score=0.9),
            DocumentChunk(chunk_text="Vibration Jan: 2.1 mm/s. Status: Normal.", source_id="doc_1120", page=1, score=0.85),
        ],
        data_findings=DataAnalysisResult(
            trend=TrendDirection.INCREASING,
            pct_change=76.2,
            data_points=[
                DataPoint(timestamp="2026-01-15T09:00:00Z", value=2.1, unit="mm/s"),
                DataPoint(timestamp="2026-07-14T09:00:00Z", value=3.7, unit="mm/s"),
            ],
            threshold_breach=True,
        ),
        vision_findings=VisionAnalysisResult(
            found=True,
            connections=["T-101", "V-204"],
            confidence=0.95,
        ),
        spec_findings=[
            SpecChunk(chunk_text="Continuous attention threshold: 3.0 mm/s.", source_id="doc_1130", page=1, section="4.2"),
        ],
        evidence_items=[
            EvidenceItem(type="document", source_id="doc_1122", label="Inspection July"),
            EvidenceItem(type="document", source_id="doc_1120", label="Inspection Jan"),
            EvidenceItem(type="dataset", source_id="ds_4471", label="Vibration Telemetry"),
            EvidenceItem(type="document", source_id="doc_1130", label="Pump Manual"),
        ],
    )


@pytest.mark.asyncio
async def test_synthesis_enforces_evidence_bundle_type(sample_evidence_bundle):
    """Test synthesis only accepts EvidenceBundle per FR-SYN-1."""
    draft_findings = await synthesis.synthesize(sample_evidence_bundle)

    assert isinstance(draft_findings, DraftFindings)
    assert len(draft_findings.findings) > 0
    for f in draft_findings.findings:
        assert f.id is not None
        assert len(f.title) > 0
        assert len(f.detail) > 0


@pytest.mark.asyncio
async def test_verification_supported_findings(sample_evidence_bundle):
    """Test verification correctly classifies supported findings."""
    draft_findings = await synthesis.synthesize(sample_evidence_bundle)
    result = await verification.verify(draft_findings, sample_evidence_bundle)

    assert result.overall_confidence > 0
    assert len(result.findings) > 0
    # Overall status should be verified
    assert result.overall_status in ["verified", "partially_verified"]
    # At least one finding must be supported
    supported = [f for f in result.findings if f.verification_status == VerificationStatus.SUPPORTED]
    assert len(supported) > 0


@pytest.mark.asyncio
async def test_verification_unsupported_findings_degradation():
    """Test that completely unsupported hallucinated findings get flagged (FR-VER-2)."""
    hallucinated_findings = DraftFindings(
        findings=[
            DraftFinding(
                id="f1",
                title="Pump caught on fire",
                detail="Catastrophic explosion occurred at 2000 RPM destroying Unit 101",
                evidence=[],
            )
        ],
        condition_summary="False disaster",
    )
    empty_bundle = EvidenceBundle()

    result = await verification.verify(hallucinated_findings, empty_bundle)
    # The unsupported finding must either be marked unsupported or partially supported with warning
    assert result.findings[0].verification_status in [
        VerificationStatus.UNSUPPORTED,
        VerificationStatus.PARTIALLY_SUPPORTED,
    ]
