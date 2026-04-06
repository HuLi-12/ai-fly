import time

import pytest

from app.agents.graph import _ensure_before_deadline


def test_deadline_only_blocks_expensive_nodes() -> None:
    state = {"deadline_epoch": time.perf_counter() - 1}

    _ensure_before_deadline(state, "trace")
    _ensure_before_deadline(state, "respond")

    with pytest.raises(TimeoutError):
        _ensure_before_deadline(state, "diagnose")
