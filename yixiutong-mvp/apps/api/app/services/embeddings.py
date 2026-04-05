from __future__ import annotations

import hashlib
import math
import re

import httpx

from app.core.config import Settings


TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[A-Za-z0-9_./-]+")
DEFAULT_VECTOR_DIMENSION = 128


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "")]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 8) for value in vector]


def hashing_embedding(text: str, dimension: int = DEFAULT_VECTOR_DIMENSION) -> list[float]:
    vector = [0.0] * dimension
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
        primary = int.from_bytes(digest[0:4], "big") % dimension
        secondary = int.from_bytes(digest[4:8], "big") % dimension
        sign = 1.0 if digest[8] % 2 == 0 else -1.0
        weight = 1.0 + (digest[9] / 255.0)
        vector[primary] += sign * weight
        vector[secondary] += sign * 0.5

    return _normalize(vector)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return max(min(sum(a * b for a, b in zip(left, right)), 1.0), -1.0)


def _openai_headers(api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _embed_with_openai_compatible(config: dict[str, str], texts: list[str]) -> list[list[float]]:
    response = httpx.post(
        f"{config['base_url'].rstrip('/')}/embeddings",
        headers=_openai_headers(config["api_key"]),
        json={
            "model": config["model"],
            "input": texts,
            "encoding_format": "float",
        },
        timeout=float(config["timeout_seconds"]),
    )
    response.raise_for_status()
    data = response.json()
    return [item["embedding"] for item in data["data"]]


def _embed_with_ollama(config: dict[str, str], texts: list[str]) -> list[list[float]]:
    response = httpx.post(
        f"{config['base_url'].rstrip('/')}/api/embed",
        json={
            "model": config["model"],
            "input": texts,
            "truncate": True,
        },
        timeout=float(config["timeout_seconds"]),
    )
    response.raise_for_status()
    data = response.json()
    if "embeddings" in data:
        return data["embeddings"]
    if "embedding" in data:
        return [data["embedding"]]
    raise RuntimeError("Embedding response does not contain embeddings.")


def embed_texts(settings: Settings, texts: list[str]) -> tuple[list[list[float]], str]:
    normalized = [text.strip() or " " for text in texts]
    config = settings.retrieval_embedding_config()
    provider = config["provider"].strip().lower() or "hashing"

    if not settings.retrieval_vector_enabled or provider == "hashing":
        return [hashing_embedding(text) for text in normalized], "hashing"

    if not config["base_url"] or not config["model"]:
        return [hashing_embedding(text) for text in normalized], f"hashing_fallback:{provider}"

    try:
        if provider == "openai_compatible":
            embeddings = _embed_with_openai_compatible(config, normalized)
        elif provider == "ollama":
            embeddings = _embed_with_ollama(config, normalized)
        else:
            raise RuntimeError(f"Unsupported embedding provider: {provider}")
        return [_normalize([float(value) for value in embedding]) for embedding in embeddings], f"{provider}:{config['model']}"
    except Exception:
        return [hashing_embedding(text) for text in normalized], f"hashing_fallback:{provider}"
