from __future__ import annotations

from datetime import datetime
from pathlib import Path


SCENE_NAMES = {"fault_diagnosis", "process_deviation", "quality_inspection"}


def _safe_relative_path(materials_root: Path, document_id: str) -> Path:
    target = (materials_root / document_id).resolve()
    root = materials_root.resolve()
    if root not in target.parents and target != root:
        raise ValueError("非法文档路径")
    return target


def _infer_scene_type(relative_path: Path) -> str:
    for part in relative_path.parts:
        if part in SCENE_NAMES:
            return part
    if "manuals" in relative_path.parts or "cases" in relative_path.parts:
        return "fault_diagnosis"
    return "general"


def _infer_category(relative_path: Path) -> str:
    if "official_refs" in relative_path.parts:
        return "官方参考"
    if "manuals" in relative_path.parts:
        return "操作手册"
    if "cases" in relative_path.parts:
        return "案例复盘"
    if "templates" in relative_path.parts:
        return "模板制度"
    if "demo" in relative_path.parts:
        return "演示脚本"
    return "资料文档"


def _extract_summary(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped[:90]
    return "暂无摘要"


def _extract_title(relative_path: Path, content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.replace("# ", "", 1).strip()
    return relative_path.stem.replace("_", " ")


def list_documents(materials_root: Path, keyword: str | None = None, category: str | None = None) -> list[dict]:
    items: list[dict] = []
    for path in sorted(materials_root.rglob("*.md")):
        relative_path = path.relative_to(materials_root)
        content = path.read_text(encoding="utf-8")
        updated_at = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        item = {
            "document_id": str(relative_path).replace("\\", "/"),
            "title": _extract_title(relative_path, content),
            "category": _infer_category(relative_path),
            "scene_type": _infer_scene_type(relative_path),
            "summary": _extract_summary(content),
            "updated_at": updated_at,
        }
        items.append(item)

    if keyword:
        lowered = keyword.lower()
        items = [item for item in items if lowered in item["title"].lower() or lowered in item["summary"].lower() or lowered in item["document_id"].lower()]
    if category:
        items = [item for item in items if item["category"] == category]

    items.sort(key=lambda item: item["updated_at"], reverse=True)
    return items


def get_document(materials_root: Path, document_id: str) -> dict:
    target = _safe_relative_path(materials_root, document_id)
    if not target.exists() or target.suffix.lower() != ".md":
        raise FileNotFoundError(document_id)
    relative_path = target.relative_to(materials_root)
    content = target.read_text(encoding="utf-8")
    updated_at = datetime.fromtimestamp(target.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return {
        "document_id": str(relative_path).replace("\\", "/"),
        "title": _extract_title(relative_path, content),
        "category": _infer_category(relative_path),
        "scene_type": _infer_scene_type(relative_path),
        "summary": _extract_summary(content),
        "updated_at": updated_at,
        "content": content,
        "relative_path": str(relative_path).replace("\\", "/"),
    }
