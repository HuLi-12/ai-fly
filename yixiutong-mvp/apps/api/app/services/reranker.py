from __future__ import annotations

from app.core.config import Settings
from app.services.provider_runtime import generate_structured_with_fallback


RERANK_SCHEMA = {
    "scored": [
        {
            "evidence_id": "string",
            "score": 0.0,
        }
    ]
}


def model_rerank_candidates(
    settings: Settings,
    query: str,
    scene_type: str,
    candidates: list[dict],
) -> tuple[dict[str, float], str]:
    if not settings.retrieval_enable_model_rerank or len(candidates) < 2:
        return {}, "disabled"

    compact_candidates = [
        {
            "evidence_id": candidate.get("id", ""),
            "title": candidate.get("title", ""),
            "snippet": candidate.get("snippet", "")[:220],
            "source_type": candidate.get("source_type", "knowledge"),
        }
        for candidate in candidates[: settings.retrieval_rerank_candidate_count]
    ]
    if not compact_candidates:
        return {}, "disabled"

    messages = [
        {
            "role": "user",
            "content": (
                f"scene_type={scene_type}\n"
                f"query={query}\n"
                f"candidates={compact_candidates}"
            ),
        }
    ]
    system_prompt = (
        "You are a retrieval reranker for an aviation maintenance assistant. "
        "Score each candidate from 0.0 to 1.0 by how well it supports the user query. "
        "Favor exact fault code matches, direct symptom alignment, and operational relevance. "
        "Return JSON only."
    )

    try:
        structured, provider_used = generate_structured_with_fallback(
            settings=settings,
            messages=messages,
            schema=RERANK_SCHEMA,
            system_prompt=system_prompt,
            options={"temperature": 0.0},
        )
    except Exception:
        return {}, "unavailable"

    scored = structured.get("scored", [])
    results: dict[str, float] = {}
    for item in scored:
        evidence_id = str(item.get("evidence_id", "")).strip()
        if not evidence_id:
            continue
        try:
            score = float(item.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        results[evidence_id] = max(0.0, min(score, 1.0))
    return results, provider_used
