from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import Settings, get_settings
from app.repositories.corpus import save_index
from app.services.embeddings import embed_texts


SCENE_NAMES = {"fault_diagnosis", "process_deviation", "quality_inspection"}


def _read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _chunk_text(text: str) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    return paragraphs or [text]


def _infer_scene_type(path: Path) -> str:
    for part in path.parts:
        if part in SCENE_NAMES:
            return part
    return "fault_diagnosis"


def _infer_source_type(path: Path) -> str:
    parent = path.parent.name.lower()
    if "manual" in parent:
        return "manual"
    if "case" in parent:
        return "case"
    if "template" in parent:
        return "template"
    return parent or "knowledge"


def build_index(materials_root: Path, output_path: Path, settings: Settings | None = None) -> list[dict]:
    settings = settings or get_settings()
    sources = []
    for path in sorted((materials_root / "knowledge").rglob("*.md")):
        raw = _read_markdown(path)
        for idx, chunk in enumerate(_chunk_text(raw), start=1):
            title = path.stem
            sources.append(
                {
                    "id": f"{path.stem}-{idx}",
                    "source_type": _infer_source_type(path),
                    "scene_type": _infer_scene_type(path),
                    "title": title,
                    "snippet": chunk,
                    "path": str(path),
                    "content_hash": hashlib.sha1(f"{title}\n{chunk}".encode("utf-8")).hexdigest(),
                }
            )

    if sources:
        embedding_inputs = [f"{item['title']}\n{item['snippet']}" for item in sources]
        embeddings, backend = embed_texts(settings, embedding_inputs)
        for item, embedding in zip(sources, embeddings):
            item["embedding"] = embedding
            item["embedding_backend"] = backend

    save_index(output_path, sources)
    return sources
