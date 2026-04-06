from __future__ import annotations

import json
from threading import Lock
from typing import Any

from app.core.config import get_settings
from app.services.agent_runtime import now_iso


_LOG_LOCK = Lock()


def log_agent_event(event: str, payload: dict[str, Any]) -> None:
    settings = get_settings()
    log_line = {"ts": now_iso(), "event": event, **payload}
    path = settings.logs_dir / "agent_events.jsonl"
    encoded = json.dumps(log_line, ensure_ascii=False)
    with _LOG_LOCK:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.write("\n")
