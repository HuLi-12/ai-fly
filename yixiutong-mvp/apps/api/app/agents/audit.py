from __future__ import annotations

from app.models.schemas import ConfidenceScore, EvidenceItem, ValidationResult


def requires_human_confirmation(risk_level: str, evidence: list[EvidenceItem]) -> bool:
    return risk_level != "low" or len(evidence) < 3


def evaluate_approval_policy(
    risk_level: str,
    evidence: list[EvidenceItem],
    confidence: ConfidenceScore,
    validation_result: ValidationResult,
    provider_used: str,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if risk_level != "low":
        reasons.append(f"风险等级为 {risk_level}。")
    if len(evidence) < 3:
        reasons.append("证据数量少于 3 条。")
    if confidence.overall_score < 60 or confidence.requires_human_review:
        reasons.append(f"置信度偏低（{confidence.overall_score:.1f}）。")
    if validation_result.requires_approval:
        reasons.append("工单校验要求进入审批流。")
    if validation_result.status != "ready_to_submit":
        reasons.append("工单校验未完全通过。")
    if provider_used == "heuristic_fallback":
        reasons.append("当前结果来自启发式兜底通道。")

    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            deduped.append(reason)
    return bool(deduped), deduped
