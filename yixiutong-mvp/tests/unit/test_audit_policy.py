from app.agents.audit import evaluate_approval_policy
from app.models.schemas import ConfidenceScore, EvidenceItem, ValidationIssue, ValidationResult


def test_approval_policy_collects_reasons():
    requires_review, reasons = evaluate_approval_policy(
        risk_level="high",
        evidence=[
            EvidenceItem(
                evidence_id="doc-1",
                source_type="manual",
                title="E-204 manual",
                snippet="Shutdown required before restart.",
                score=0.81,
            )
        ],
        confidence=ConfidenceScore(
            overall_score=52.0,
            level="low",
            requires_human_review=True,
        ),
        validation_result=ValidationResult(
            status="needs_revision",
            requires_approval=True,
            issues=[
                ValidationIssue(
                    field="safety_notes",
                    severity="error",
                    message="High-risk order lacks safety notes.",
                )
            ],
        ),
        provider_used="heuristic_fallback",
    )

    assert requires_review is True
    assert any("风险等级" in reason for reason in reasons)
    assert any("证据数量" in reason for reason in reasons)
    assert any("置信度偏低" in reason for reason in reasons)
    assert any("启发式兜底" in reason for reason in reasons)
