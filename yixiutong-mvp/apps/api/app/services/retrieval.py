from __future__ import annotations

import math
import re
from collections import Counter

from app.core.config import Settings, get_settings
from app.models.schemas import EvidenceItem
from app.services.embeddings import cosine_similarity, embed_texts
from app.services.reranker import model_rerank_candidates


TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_./-]+")
FAULT_CODE_RE = re.compile(r"\b[A-Z]{1,4}-\d{2,4}\b", re.IGNORECASE)

RETRIEVAL_WEIGHTS: dict[str, dict[str, float]] = {
    "fault_diagnosis": {"keyword": 0.42, "semantic": 0.58},
    "process_deviation": {"keyword": 0.32, "semantic": 0.68},
    "quality_inspection": {"keyword": 0.35, "semantic": 0.65},
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
        weights["keyword"] = max(weights["keyword"], 0.45)
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


def _fallback_semantic_score(query: str, item: dict) -> float:
    query_counter = Counter(_tokenize(query))
    item_counter = Counter(_tokenize(f"{item.get('title', '')} {item.get('snippet', '')}"))
    return _cosine_similarity(query_counter, item_counter)


def _vector_score(query_embedding: list[float] | None, query_backend: str, item: dict) -> float:
    item_embedding = item.get("embedding")
    item_backend = str(item.get("embedding_backend", "")).strip()
    if not query_embedding or not item_embedding or not item_backend:
        return 0.0
    if item_backend != query_backend:
        return 0.0
    try:
        return max(cosine_similarity(query_embedding, item_embedding), 0.0)
    except Exception:
        return 0.0


def _heuristic_rerank_score(query: str, item: dict, keyword_score: float, semantic_score: float, fused_score: float) -> float:
    title = item.get("title", "").lower()
    snippet = item.get("snippet", "").lower()
    query_lower = query.lower()
    title_bonus = 0.12 if query_lower[:24] and query_lower[:24] in title else 0.0
    exact_fault_bonus = 0.18 if FAULT_CODE_RE.search(query) and FAULT_CODE_RE.search(query).group(0).lower() in snippet else 0.0
    overlap_bonus = 0.08 if any(token in snippet for token in _tokenize(query)[:3]) else 0.0
    rerank_score = (0.45 * fused_score) + (0.3 * keyword_score) + (0.25 * semantic_score) + title_bonus + exact_fault_bonus + overlap_bonus
    return min(rerank_score, 1.0)


def _query_embedding_for_corpus(settings: Settings, query: str, corpus_items: list[dict]) -> tuple[list[float] | None, str]:
    if not settings.retrieval_vector_enabled:
        return None, "disabled"
    if not any(item.get("embedding") for item in corpus_items):
        return None, "missing_index_embedding"
    embeddings, backend = embed_texts(settings, [query])
    return (embeddings[0] if embeddings else None), backend


def _ensure_embeddings(settings: Settings, items: list[dict]) -> list[dict]:
    if not settings.retrieval_vector_enabled:
        return items

    missing = [(index, item) for index, item in enumerate(items) if not item.get("embedding")]
    if not missing:
        return items

    mutable_items = [dict(item) for item in items]
    embedding_inputs = [f"{item.get('title', '')}\n{item.get('snippet', '')}" for _, item in missing]
    embeddings, backend = embed_texts(settings, embedding_inputs)
    for (index, _), embedding in zip(missing, embeddings):
        mutable_items[index]["embedding"] = embedding
        mutable_items[index]["embedding_backend"] = backend
    return mutable_items


def search(
    query: str,
    corpus_items: list[dict],
    scene_type: str,
    top_k: int = 5,
    settings: Settings | None = None,
) -> list[EvidenceItem]:
    settings = settings or get_settings()
    filtered_items = [item for item in corpus_items if item.get("scene_type") == scene_type] or corpus_items
    filtered_items = _ensure_embeddings(settings, filtered_items)
    weights = _scene_weights(scene_type, query)
    query_embedding, query_backend = _query_embedding_for_corpus(settings, query, filtered_items)

    candidates: list[dict] = []
    for item in filtered_items:
        keyword_score = _keyword_score(query, item)
        vector_score = _vector_score(query_embedding, query_backend, item)
        semantic_score = vector_score or _fallback_semantic_score(query, item)
        fused_score = (weights["keyword"] * keyword_score) + (weights["semantic"] * semantic_score)
        if item.get("scene_type") == scene_type:
            fused_score += 0.03
        if item.get("source_type") == "case_memory":
            fused_score += 0.08
        if fused_score <= 0:
            continue

        method = "hybrid"
        if keyword_score and semantic_score == 0:
            method = "keyword"
        elif semantic_score and keyword_score == 0:
            method = "semantic"

        heuristic_rerank_score = _heuristic_rerank_score(query, item, keyword_score, semantic_score, fused_score)
        candidates.append(
            {
                "item": item,
                "keyword_score": round(keyword_score, 4),
                "semantic_score": round(semantic_score, 4),
                "fused_score": round(fused_score, 4),
                "heuristic_rerank_score": round(heuristic_rerank_score, 4),
                "retrieval_method": method,
            }
        )

    ranked_candidates = sorted(candidates, key=lambda candidate: candidate["fused_score"], reverse=True)
    rerank_pool = [candidate["item"] for candidate in ranked_candidates[: settings.retrieval_rerank_candidate_count]]
    model_scores, rerank_backend = model_rerank_candidates(settings, query, scene_type, rerank_pool)

    deduped: dict[str, EvidenceItem] = {}
    for candidate in ranked_candidates:
        item = candidate["item"]
        evidence_id = item.get("id", "")
        model_rerank_score = model_scores.get(evidence_id, 0.0)
        combined_rerank_score = candidate["heuristic_rerank_score"]
        if model_scores:
            combined_rerank_score = round((0.6 * model_rerank_score) + (0.4 * candidate["heuristic_rerank_score"]), 4)
        final_score = round((0.55 * combined_rerank_score) + (0.45 * candidate["fused_score"]), 4)

        evidence = EvidenceItem(
            evidence_id=evidence_id,
            source_type=item.get("source_type", "knowledge"),
            title=item.get("title", "Untitled"),
            snippet=item.get("snippet", "")[:240],
            score=final_score,
            source_path=item.get("path", ""),
            retrieval_backend=f"{query_backend}|{rerank_backend}",
            retrieval_method=candidate["retrieval_method"],
            keyword_score=candidate["keyword_score"],
            semantic_score=candidate["semantic_score"],
            rerank_score=combined_rerank_score,
            model_rerank_score=round(model_rerank_score, 4),
        )
        key = evidence.evidence_id or f"{evidence.title}:{evidence.snippet}"
        existing = deduped.get(key)
        if existing is None or evidence.score > existing.score:
            deduped[key] = evidence

    return sorted(deduped.values(), key=lambda item: item.score, reverse=True)[:top_k]
