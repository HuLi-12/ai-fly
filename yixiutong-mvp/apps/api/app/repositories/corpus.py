from __future__ import annotations

import json
from pathlib import Path


def load_index(index_path: Path) -> list[dict]:
    if not index_path.exists():
        return []
    return json.loads(index_path.read_text(encoding="utf-8"))


def save_index(index_path: Path, items: list[dict]) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

