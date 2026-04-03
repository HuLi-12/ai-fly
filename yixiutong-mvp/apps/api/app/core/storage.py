from __future__ import annotations

import json
import shutil
from pathlib import Path


def get_free_space_gb(path: Path) -> float:
    drive_root = Path(f"{path.resolve().drive}\\")
    total, used, free = shutil.disk_usage(drive_root)
    del total, used
    return round(free / (1024**3), 2)


def get_directory_size_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def ensure_safe_free_space(path: Path, safe_floor_gb: int) -> None:
    free_gb = get_free_space_gb(path)
    if free_gb < safe_floor_gb:
        raise RuntimeError(
            f"Insufficient D drive headroom. Free space {free_gb} GB is below safe floor {safe_floor_gb} GB."
        )


def ensure_directory_budget(path: Path, budget_gb: int, label: str) -> None:
    used_gb = round(get_directory_size_bytes(path) / (1024**3), 3)
    if used_gb > budget_gb:
        raise RuntimeError(f"{label} size {used_gb} GB exceeds configured budget {budget_gb} GB.")


def ensure_within_root(path: Path, root: Path) -> None:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if resolved_path != resolved_root and resolved_root not in resolved_path.parents:
        raise RuntimeError(f"Path {resolved_path} escapes controlled root {resolved_root}.")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
