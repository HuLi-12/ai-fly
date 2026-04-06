from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.models.schemas import AgentMetricNodeSummary, AgentMetricsResponse, AgentRunReplayResponse, AgentRunSnapshot
from app.services.agent_runtime import now_iso


def _to_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _from_json(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    return json.loads(raw)


class AgentRuntimeRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    request_id TEXT NOT NULL DEFAULT '',
                    request_hash TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    response_json TEXT NOT NULL DEFAULT '',
                    error_text TEXT NOT NULL DEFAULT '',
                    user_id TEXT NOT NULL DEFAULT '',
                    scene_type TEXT NOT NULL DEFAULT '',
                    provider_used TEXT NOT NULL DEFAULT '',
                    cache_hit INTEGER NOT NULL DEFAULT 0,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL DEFAULT '',
                    last_updated_at TEXT NOT NULL,
                    total_duration_ms REAL NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_agent_runs_request_hash_status
                    ON agent_runs(request_hash, status, finished_at);
                CREATE INDEX IF NOT EXISTS idx_agent_runs_request_id
                    ON agent_runs(request_id);

                CREATE TABLE IF NOT EXISTS agent_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    node TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_agent_snapshots_run_seq
                    ON agent_snapshots(run_id, seq);

                CREATE TABLE IF NOT EXISTS agent_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    node TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    tags_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_metric_name
                    ON agent_metrics(metric_name, node);
                """
            )

    def create_run(
        self,
        run_id: str,
        session_id: str,
        request_hash: str,
        idempotency_key: str,
        request_payload: dict[str, Any],
        user_id: str = "",
    ) -> None:
        now = now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_runs(
                    run_id, session_id, request_hash, idempotency_key, status, request_json, user_id,
                    started_at, last_updated_at
                )
                VALUES (?, ?, ?, ?, 'running', ?, ?, ?, ?)
                """,
                (run_id, session_id, request_hash, idempotency_key, _to_json(request_payload), user_id, now, now),
            )

    def mark_cache_hit(self, run_id: str, response_payload: dict[str, Any], total_duration_ms: float) -> None:
        now = now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE agent_runs
                SET status = 'completed',
                    response_json = ?,
                    cache_hit = 1,
                    request_id = ?,
                    scene_type = ?,
                    provider_used = ?,
                    finished_at = ?,
                    last_updated_at = ?,
                    total_duration_ms = ?
                WHERE run_id = ?
                """,
                (
                    _to_json(response_payload),
                    str(response_payload.get("request_id", "")),
                    str(response_payload.get("scene_type", "")),
                    str(response_payload.get("provider_used", "")),
                    now,
                    now,
                    total_duration_ms,
                    run_id,
                ),
            )

    def find_cached_response(self, request_hash: str, ttl_hours: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT response_json, finished_at
                FROM agent_runs
                WHERE request_hash = ? AND status = 'completed' AND response_json != ''
                ORDER BY finished_at DESC
                """,
                (request_hash,),
            ).fetchall()
        if not rows:
            return None
        cutoff = datetime.now() - timedelta(hours=max(ttl_hours, 0))
        for row in rows:
            finished_at = row["finished_at"]
            if finished_at:
                try:
                    if datetime.fromisoformat(finished_at) < cutoff:
                        continue
                except ValueError:
                    continue
            return _from_json(row["response_json"], {})
        return None

    def append_snapshot(
        self,
        run_id: str,
        node: str,
        status: str,
        summary: str,
        detail: str,
        payload: dict[str, Any],
    ) -> None:
        now = now_iso()
        with self._connect() as conn:
            seq = conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM agent_snapshots WHERE run_id = ?",
                (run_id,),
            ).fetchone()["next_seq"]
            conn.execute(
                """
                INSERT INTO agent_snapshots(run_id, seq, node, status, summary, detail, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, seq, node, status, summary, detail, _to_json(payload), now),
            )
            conn.execute(
                "UPDATE agent_runs SET last_updated_at = ? WHERE run_id = ?",
                (now, run_id),
            )

    def record_metric(
        self,
        run_id: str,
        node: str,
        metric_name: str,
        metric_value: float,
        tags: dict[str, Any] | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_metrics(run_id, node, metric_name, metric_value, tags_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, node, metric_name, metric_value, _to_json(tags or {}), now_iso()),
            )

    def complete_run(
        self,
        run_id: str,
        response_payload: dict[str, Any],
        total_duration_ms: float,
    ) -> None:
        now = now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE agent_runs
                SET status = 'completed',
                    request_id = ?,
                    scene_type = ?,
                    provider_used = ?,
                    response_json = ?,
                    finished_at = ?,
                    last_updated_at = ?,
                    total_duration_ms = ?
                WHERE run_id = ?
                """,
                (
                    str(response_payload.get("request_id", "")),
                    str(response_payload.get("scene_type", "")),
                    str(response_payload.get("provider_used", "")),
                    _to_json(response_payload),
                    now,
                    now,
                    total_duration_ms,
                    run_id,
                ),
            )

    def fail_run(self, run_id: str, error_text: str, total_duration_ms: float) -> None:
        now = now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE agent_runs
                SET status = 'failed',
                    error_text = ?,
                    finished_at = ?,
                    last_updated_at = ?,
                    total_duration_ms = ?
                WHERE run_id = ?
                """,
                (error_text, now, now, total_duration_ms, run_id),
            )

    def get_run_replay(self, run_id: str) -> AgentRunReplayResponse:
        with self._connect() as conn:
            run_row = conn.execute("SELECT * FROM agent_runs WHERE run_id = ?", (run_id,)).fetchone()
            if run_row is None:
                raise KeyError(run_id)
            snapshot_rows = conn.execute(
                "SELECT seq, node, status, summary, detail, payload_json, created_at FROM agent_snapshots WHERE run_id = ? ORDER BY seq",
                (run_id,),
            ).fetchall()

        return AgentRunReplayResponse(
            run_id=run_row["run_id"],
            session_id=run_row["session_id"],
            request_id=run_row["request_id"],
            request_hash=run_row["request_hash"],
            idempotency_key=run_row["idempotency_key"],
            status=run_row["status"],
            scene_type=run_row["scene_type"],
            user_id=run_row["user_id"],
            provider_used=run_row["provider_used"],
            started_at=run_row["started_at"],
            finished_at=run_row["finished_at"],
            total_duration_ms=round(float(run_row["total_duration_ms"]), 2),
            request=_from_json(run_row["request_json"], {}),
            response=_from_json(run_row["response_json"], {}),
            error_message=run_row["error_text"],
            snapshots=[
                AgentRunSnapshot(
                    seq=row["seq"],
                    node=row["node"],
                    status=row["status"],
                    summary=row["summary"],
                    detail=row["detail"],
                    created_at=row["created_at"],
                    payload=_from_json(row["payload_json"], {}),
                )
                for row in snapshot_rows
            ],
        )

    def get_run_replay_by_request_id(self, request_id: str) -> AgentRunReplayResponse:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT run_id FROM agent_runs WHERE request_id = ? ORDER BY finished_at DESC LIMIT 1",
                (request_id,),
            ).fetchone()
        if row is None:
            raise KeyError(request_id)
        return self.get_run_replay(row["run_id"])

    def get_metrics_summary(self) -> AgentMetricsResponse:
        with self._connect() as conn:
            total_runs = conn.execute("SELECT COUNT(*) AS count FROM agent_runs").fetchone()["count"]
            completed_runs = conn.execute(
                "SELECT COUNT(*) AS count FROM agent_runs WHERE status = 'completed'"
            ).fetchone()["count"]
            failed_runs = conn.execute(
                "SELECT COUNT(*) AS count FROM agent_runs WHERE status = 'failed'"
            ).fetchone()["count"]
            cached_hits = conn.execute(
                "SELECT COUNT(*) AS count FROM agent_runs WHERE cache_hit = 1"
            ).fetchone()["count"]
            avg_row = conn.execute(
                "SELECT COALESCE(AVG(total_duration_ms), 0) AS avg_duration_ms FROM agent_runs WHERE total_duration_ms > 0"
            ).fetchone()
            node_rows = conn.execute(
                """
                SELECT node, COUNT(*) AS count, AVG(metric_value) AS avg_duration_ms, MAX(metric_value) AS max_duration_ms
                FROM agent_metrics
                WHERE metric_name = 'node_duration_ms'
                GROUP BY node
                ORDER BY node
                """
            ).fetchall()

        return AgentMetricsResponse(
            total_runs=total_runs,
            completed_runs=completed_runs,
            failed_runs=failed_runs,
            cached_hits=cached_hits,
            avg_run_duration_ms=round(float(avg_row["avg_duration_ms"]), 2),
            node_summaries=[
                AgentMetricNodeSummary(
                    node=row["node"],
                    count=row["count"],
                    avg_duration_ms=round(float(row["avg_duration_ms"]), 2),
                    max_duration_ms=round(float(row["max_duration_ms"]), 2),
                )
                for row in node_rows
            ],
        )
