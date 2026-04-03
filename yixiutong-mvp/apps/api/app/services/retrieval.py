from __future__ import annotations

import math
import re
from collections import Counter

from app.models.schemas import EvidenceItem


TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_./-]+")


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _cosine_similarity(a: Counter[str], b: Counter[str]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0) * b.get(k, 0) for k in keys)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def search(query: str, corpus_items: list[dict], scene_type: str, top_k: int = 5) -> list[EvidenceItem]:
    query_tokens = _tokenize(query)
    query_counter = Counter(query_tokens)
    ranked: list[tuple[float, dict]] = []
    filtered_items = [item for item in corpus_items if item.get("scene_type") == scene_type] or corpus_items
    for item in filtered_items:
        counter = Counter(_tokenize(item["title"] + " " + item["snippet"]))
        score = _cosine_similarity(query_counter, counter)
        if item.get("scene_type") == scene_type:
            score += 0.05
        if any(token in item["snippet"].lower() for token in query_tokens[:3]):
            score += 0.05
        if score > 0:
            ranked.append((score, item))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return [
        EvidenceItem(
            source_type=item["source_type"],
            title=item["title"],
            snippet=item["snippet"][:240],
            score=round(score, 4),
        )
        for score, item in ranked[:top_k]
    ]
