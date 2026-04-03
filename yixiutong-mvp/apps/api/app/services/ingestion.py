from __future__ import annotations

from pathlib import Path

from app.repositories.corpus import save_index


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


def build_index(materials_root: Path, output_path: Path) -> list[dict]:
    sources = []
    for path in sorted((materials_root / "knowledge").rglob("*.md")):
        raw = _read_markdown(path)
        for idx, chunk in enumerate(_chunk_text(raw), start=1):
            sources.append(
                {
                    "id": f"{path.stem}-{idx}",
                    "source_type": _infer_source_type(path),
                    "scene_type": _infer_scene_type(path),
                    "title": path.stem,
                    "snippet": chunk,
                    "path": str(path),
                }
            )
    save_index(output_path, sources)
    return sources
