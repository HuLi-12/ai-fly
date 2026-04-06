from __future__ import annotations

from app.models.schemas import ConfidenceScore, EvidenceItem, TraceabilityItem
from app.services.confidence_calibration import apply_confidence_calibration


def _provider_reliability(provider_used: str) -> float:
    lowered = provider_used.lower()
    if lowered == "heuristic_fallback":
        return 42.0
    if "+text_assist" in lowered:
        return 62.0
    if "openai_compatible" in lowered:
        return 88.0
    if "ollama" in lowered:
        return 76.0
    return 70.0


def _evidence_quality(evidence_list: list[EvidenceItem]) -> tuple[float, list[str]]:
    warnings: list[str] = []
    if not evidence_list:
        return 20.0, ["No supporting evidence was retrieved."]

    avg_score = sum(item.score for item in evidence_list) / len(evidence_list)
    diversity = len({item.source_type for item in evidence_list})
    quality = (avg_score * 74.0) + min(len(evidence_list), 5) * 4.5 + min(diversity, 3) * 3.0

    if len(evidence_list) < 3:
        quality -= 12.0
        warnings.append("Evidence count is below 3; manual review is recommended.")

    return max(min(round(quality, 2), 100.0), 0.0), warnings


def _traceability_quality(traceability: list[TraceabilityItem]) -> tuple[float, float, list[str]]:
    warnings: list[str] = []
    if not traceability:
        return 30.0, 0.0, ["No traceability map was generated."]

    supported = [item for item in traceability if item.evidence_links]
    strong = [item for item in traceability if item.support_level == "strong"]
    coverage = len(supported) / max(len(traceability), 1)
    strong_ratio = len(strong) / max(len(traceability), 1)
    score = (coverage * 70.0) + (strong_ratio * 30.0)

    if coverage < 0.8:
        warnings.append("Some recommendations still lack strong evidence support.")

    return round(score, 2), round(strong_ratio, 4), warnings


def _risk_component(risk_level: str, evidence_count: int) -> float:
    base = {"low": 92.0, "medium": 80.0, "high": 68.0}.get(risk_level, 75.0)
    if evidence_count < 3:
        base -= 10.0
    return max(base, 20.0)


def compute_confidence(
    evidence_list: list[EvidenceItem],
    traceability: list[TraceabilityItem],
    provider_used: str,
    risk_level: str,
    scene_type: str = "fault_diagnosis",
) -> ConfidenceScore:
    evidence_quality, evidence_warnings = _evidence_quality(evidence_list)
    traceability_score, strong_trace_ratio, traceability_warnings = _traceability_quality(traceability)
    provider_score = _provider_reliability(provider_used)
    risk_score = _risk_component(risk_level, len(evidence_list))

    raw_score = (
        (0.45 * evidence_quality)
        + (0.30 * traceability_score)
        + (0.15 * provider_score)
        + (0.10 * risk_score)
    )
    raw_score = round(max(min(raw_score, 100.0), 0.0), 2)

    calibrated_score, calibration_components, calibration_notes = apply_confidence_calibration(
        raw_score=raw_score,
        scene_type=scene_type,
        provider_used=provider_used,
        risk_level=risk_level,
        evidence_count=len(evidence_list),
        strong_trace_ratio=strong_trace_ratio,
    )

    if calibrated_score >= 80:
        level = "high"
    elif calibrated_score >= 60:
        level = "medium"
    else:
        level = "low"

    warnings = [*evidence_warnings, *traceability_warnings, *calibration_notes]
    requires_human_review = calibrated_score < 60 or risk_level == "high"
    if provider_used == "heuristic_fallback":
        warnings.append("当前结果使用了启发式 fallback 路径，建议人工复核。")

    return ConfidenceScore(
        overall_score=calibrated_score,
        level=level,
        components={
            "raw_score": raw_score,
            "evidence_quality": round(evidence_quality, 2),
            "traceability": round(traceability_score, 2),
            "provider_reliability": round(provider_score, 2),
            "risk_component": round(risk_score, 2),
            **{key: round(value, 2) for key, value in calibration_components.items()},
        },
        warnings=warnings,
        requires_human_review=requires_human_review,
    )
