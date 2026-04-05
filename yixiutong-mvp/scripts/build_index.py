from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.core.config import get_settings
from app.services.ingestion import build_index


def main() -> None:
    settings = get_settings()
    items = build_index(settings.materials_root, settings.index_manifest_path)
    backends = sorted({item.get("embedding_backend", "none") for item in items}) or ["none"]
    print(f"Index built: {len(items)} items -> {settings.index_manifest_path}")
    print(f"Embedding backends: {', '.join(backends)}")


if __name__ == "__main__":
    main()
