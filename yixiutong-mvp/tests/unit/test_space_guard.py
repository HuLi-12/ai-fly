import pytest

from app.core.storage import ensure_directory_budget, ensure_safe_free_space


def test_space_guard_blocks_low_space(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.storage.get_free_space_gb", lambda path: 11.0)
    with pytest.raises(RuntimeError):
        ensure_safe_free_space(tmp_path, 12)


def test_directory_budget_blocks_oversized_path(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.storage.get_directory_size_bytes", lambda path: 3 * 1024**3)
    with pytest.raises(RuntimeError):
        ensure_directory_budget(tmp_path, 2, "local model directory")
