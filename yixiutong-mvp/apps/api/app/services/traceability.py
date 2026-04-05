from __future__ import annotations

from collections import Counter

from app.models.schemas import DiagnosisResult, EvidenceReference, EvidenceItem, TraceabilityItem


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in text.replace("/", " ").replace("-", " ").split() if token.strip()]


def _support_score(recommendation: str, evidence: EvidenceItem) -> float:
    recommendation_tokens = Counter(_tokenize(recommendation))
    evidence_tokens = Counter(_tokenize(f"{evidence.title} {evidence.snippet}"))
    if not recommendation_tokens or not evidence_tokens:
        return evidence.score

    overlap = sum(min(recommendation_tokens[token], evidence_tokens[token]) for token in recommendation_tokens)
    recall = overlap / max(sum(recommendation_tokens.values()), 1)
    return min((0.55 * evidence.score) + (0.45 * recall), 1.0)


def _support_level(score: float) -> str:
    if score >= 0.75:
        return "strong"
    if score >= 0.45:
        return "partial"
    return "weak"


def _link_recommendations(category: str, recommendations: list[str], evidence_list: list[EvidenceItem]) -> list[TraceabilityItem]:
    traceability: list[TraceabilityItem] = []
    for recommendation in recommendations:
        ranked = sorted(
            evidence_list,
            key=lambda evidence: _support_score(recommendation, evidence),
            reverse=True,
        )
        linked = ranked[:2] if ranked else []
        best_score = _support_score(recommendation, linked[0]) if linked else 0.0
        traceability.append(
            TraceabilityItem(
                recommendation=recommendation,
                category=category,
                support_score=round(best_score, 4),
                support_level=_support_level(best_score),
                evidence_links=[
                    EvidenceReference(
                        evidence_id=item.evidence_id,
                        title=item.title,
                        relevance_score=round(_support_score(recommendation, item), 4),
                        source_path=item.source_path,
                    )
                    for item in linked
                ],
            )
        )
    return traceability


def build_traceability(diagnosis: DiagnosisResult, evidence_list: list[EvidenceItem]) -> list[TraceabilityItem]:
    return (
        _link_recommendations("cause", diagnosis.possible_causes, evidence_list)
        + _link_recommendations("check", diagnosis.recommended_checks, evidence_list)
        + _link_recommendations("action", diagnosis.recommended_actions, evidence_list)
    )
