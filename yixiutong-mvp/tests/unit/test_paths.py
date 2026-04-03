from pathlib import Path

from app.core.config import get_settings


def test_all_paths_stay_within_workspace():
    settings = get_settings()
    root = settings.project_root.resolve()
    for value in settings.as_path_map().values():
        assert root in Path(value).resolve().parents or Path(value).resolve() == root

