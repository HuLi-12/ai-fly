from __future__ import annotations

from app.core.config import get_settings
from app.services.ingestion import build_index


def main() -> None:
    settings = get_settings()
    items = build_index(settings.materials_root, settings.index_manifest_path)
    print(f"Index built: {len(items)} items -> {settings.index_manifest_path}")


if __name__ == "__main__":
    main()

