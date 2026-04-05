from app.models.schemas import EvidenceItem, TraceabilityItem, EvidenceReference
from app.services.confidence import compute_confidence


def test_confidence_marks_low_support_results_for_human_review():
    evidence = [
        EvidenceItem(
            evidence_id="doc-1",
            source_type="manual",
            title="General note",
            snippet="Generic troubleshooting guidance only.",
            score=0.34,
        )
    ]
    traceability = [
        TraceabilityItem(
            recommendation="Inspect bearing clearance.",
            category="check",
            support_score=0.3,
            support_level="weak",
            evidence_links=[
                EvidenceReference(
                    evidence_id="doc-1",
                    title="General note",
                    relevance_score=0.3,
                )
            ],
        )
    ]

    confidence = compute_confidence(
        evidence_list=evidence,
        traceability=traceability,
        provider_used="heuristic_fallback",
        risk_level="high",
    )

    assert confidence.overall_score < 60
    assert confidence.level == "low"
    assert confidence.requires_human_review is True
    assert any("启发式" in warning for warning in confidence.warnings)
