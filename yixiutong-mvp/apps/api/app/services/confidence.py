from __future__ import annotations

from app.models.schemas import ConfidenceScore, EvidenceItem, TraceabilityItem


def _provider_reliability(provider_used: str) -> float:
    lowered = provider_used.lower()
    if lowered == "heuristic_fallback":
        return 45.0
    if "+text_assist" in lowered:
        return 65.0
    if "openai_compatible" in lowered:
        return 88.0
    if "ollama" in lowered:
        return 76.0
    return 70.0


def _evidence_quality(evidence_list: list[EvidenceItem]) -> tuple[float, list[str]]:
    warnings: list[str] = []
    if not evidence_list:
        return 20.0, ["未召回到有效证据，结果可信度较低。"]

    avg_score = sum(item.score for item in evidence_list) / len(evidence_list)
    diversity = len({item.source_type for item in evidence_list})
    quality = (avg_score * 75.0) + min(len(evidence_list), 5) * 4.0 + min(diversity, 3) * 3.0

    if len(evidence_list) < 3:
        warnings.append("证据数量少于 3 条，建议人工复核。")
        quality -= 12.0

    return max(min(quality, 100.0), 0.0), warnings


def _traceability_quality(traceability: list[TraceabilityItem]) -> tuple[float, list[str]]:
    warnings: list[str] = []
    if not traceability:
        return 30.0, ["未生成建议到证据的映射。"]

    supported = [item for item in traceability if item.evidence_links]
    strong = [item for item in traceability if item.support_level == "strong"]
    coverage = len(supported) / max(len(traceability), 1)
    strength = len(strong) / max(len(traceability), 1)
    score = (coverage * 70.0) + (strength * 30.0)

    if coverage < 0.8:
        warnings.append("部分建议缺少强证据支撑。")
    return round(score, 2), warnings


def _risk_adjustment(risk_level: str, evidence_count: int) -> float:
    base = {"low": 92.0, "medium": 80.0, "high": 68.0}.get(risk_level, 75.0)
    if evidence_count < 3:
        base -= 10.0
    return max(base, 20.0)


def compute_confidence(
    evidence_list: list[EvidenceItem],
    traceability: list[TraceabilityItem],
    provider_used: str,
    risk_level: str,
) -> ConfidenceScore:
    evidence_quality, evidence_warnings = _evidence_quality(evidence_list)
    traceability_score, traceability_warnings = _traceability_quality(traceability)
    provider_score = _provider_reliability(provider_used)
    risk_score = _risk_adjustment(risk_level, len(evidence_list))

    overall = (
        (0.45 * evidence_quality)
        + (0.30 * traceability_score)
        + (0.15 * provider_score)
        + (0.10 * risk_score)
    )
    overall = round(max(min(overall, 100.0), 0.0), 2)

    if overall >= 80:
        level = "high"
    elif overall >= 60:
        level = "medium"
    else:
        level = "low"

    warnings = evidence_warnings + traceability_warnings
    requires_human_review = overall < 60 or risk_level == "high"
    if provider_used == "heuristic_fallback":
        warnings.append("当前结果使用启发式兜底生成，建议人工复核。")

    return ConfidenceScore(
        overall_score=overall,
        level=level,
        components={
            "evidence_quality": round(evidence_quality, 2),
            "traceability": round(traceability_score, 2),
            "provider_reliability": round(provider_score, 2),
            "risk_adjustment": round(risk_score, 2),
        },
        warnings=warnings,
        requires_human_review=requires_human_review,
    )
