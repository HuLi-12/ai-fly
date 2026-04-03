from __future__ import annotations

import sqlite3
from pathlib import Path

from app.models.feedback import FeedbackRecord


class FeedbackRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback_records (
                    request_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    feedback_text TEXT NOT NULL,
                    final_resolution TEXT NOT NULL
                )
                """
            )

    def save(self, record: FeedbackRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO feedback_records(request_id, feedback_type, feedback_text, final_resolution) VALUES (?, ?, ?, ?)",
                (record.request_id, record.feedback_type, record.feedback_text, record.final_resolution),
            )

