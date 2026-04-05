from __future__ import annotations

import math
import re
from collections import Counter

from app.models.schemas import EvidenceItem


TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_./-]+")
FAULT_CODE_RE = re.compile(r"\b[A-Z]{1,4}-\d{2,4}\b", re.IGNORECASE)

RETRIEVAL_WEIGHTS: dict[str, dict[str, float]] = {
    "fault_diagnosis": {"keyword": 0.5, "semantic": 0.5},
    "process_deviation": {"keyword": 0.35, "semantic": 0.65},
    "quality_inspection": {"keyword": 0.4, "semantic": 0.6},
}


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _cosine_similarity(a: Counter[str], b: Counter[str]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(key, 0) * b.get(key, 0) for key in keys)
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _contains_fault_code(query: str) -> bool:
    return bool(FAULT_CODE_RE.search(query))


def _scene_weights(scene_type: str, query: str) -> dict[str, float]:
    weights = dict(RETRIEVAL_WEIGHTS.get(scene_type, {"keyword": 0.4, "semantic": 0.6}))
    if _contains_fault_code(query):
        weights["keyword"] = max(weights["keyword"], 0.5)
        weights["semantic"] = round(1.0 - weights["keyword"], 2)
    return weights


def _keyword_score(query: str, item: dict) -> float:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0
    text = f"{item.get('title', '')} {item.get('snippet', '')}".lower()
    title = item.get("title", "").lower()
    match_count = sum(1 for token in query_tokens if token in text)
    score = match_count / max(len(query_tokens), 1)

    fault_match = FAULT_CODE_RE.search(query)
    if fault_match and fault_match.group(0).lower() in text:
        score += 0.35
    if any(token in title for token in query_tokens[:4]):
        score += 0.1
    return min(score, 1.0)


def _semantic_score(query: str, item: dict) -> float:
    query_counter = Counter(_tokenize(query))
    item_counter = Counter(_tokenize(f"{item.get('title', '')} {item.get('snippet', '')}"))
    return _cosine_similarity(query_counter, item_counter)


def _rerank_score(query: str, item: dict, keyword_score: float, semantic_score: float, fused_score: float) -> float:
    title = item.get("title", "").lower()
    snippet = item.get("snippet", "").lower()
    query_lower = query.lower()
    title_bonus = 0.12 if query_lower[:24] and query_lower[:24] in title else 0.0
    exact_fault_bonus = 0.18 if FAULT_CODE_RE.search(query) and FAULT_CODE_RE.search(query).group(0).lower() in snippet else 0.0
    overlap_bonus = 0.08 if any(token in snippet for token in _tokenize(query)[:3]) else 0.0
    rerank_score = (0.45 * fused_score) + (0.3 * keyword_score) + (0.25 * semantic_score) + title_bonus + exact_fault_bonus + overlap_bonus
    return min(rerank_score, 1.0)


def search(query: str, corpus_items: list[dict], scene_type: str, top_k: int = 5) -> list[EvidenceItem]:
    filtered_items = [item for item in corpus_items if item.get("scene_type") == scene_type] or corpus_items
    weights = _scene_weights(scene_type, query)

    candidates: list[tuple[float, EvidenceItem]] = []
    for item in filtered_items:
        keyword_score = _keyword_score(query, item)
        semantic_score = _semantic_score(query, item)
        fused_score = (weights["keyword"] * keyword_score) + (weights["semantic"] * semantic_score)
        if item.get("scene_type") == scene_type:
            fused_score += 0.03
        if fused_score <= 0:
            continue

        method = "hybrid"
        if keyword_score and semantic_score == 0:
            method = "keyword"
        elif semantic_score and keyword_score == 0:
            method = "semantic"

        rerank_score = _rerank_score(query, item, keyword_score, semantic_score, fused_score)
        final_score = round(((0.65 * rerank_score) + (0.35 * fused_score)), 4)
        evidence = EvidenceItem(
            evidence_id=item.get("id", ""),
            source_type=item.get("source_type", "knowledge"),
            title=item.get("title", "Untitled"),
            snippet=item.get("snippet", "")[:240],
            score=final_score,
            source_path=item.get("path", ""),
            retrieval_method=method,
            keyword_score=round(keyword_score, 4),
            semantic_score=round(semantic_score, 4),
            rerank_score=round(rerank_score, 4),
        )
        candidates.append((final_score, evidence))

    deduped: dict[str, tuple[float, EvidenceItem]] = {}
    for score, evidence in sorted(candidates, key=lambda pair: pair[0], reverse=True):
        key = evidence.evidence_id or f"{evidence.title}:{evidence.snippet}"
        if key not in deduped:
            deduped[key] = (score, evidence)

    ranked = sorted(deduped.values(), key=lambda pair: pair[0], reverse=True)
    return [item for _, item in ranked[:top_k]]
