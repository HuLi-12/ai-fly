from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import Lock
from typing import Callable
from uuid import uuid4

from app.models.schemas import AgentProgressItem, DiagnosisResponse, DiagnosisSessionState


NODE_DEFINITIONS = [
    ("route", "场景路由", "Router Agent"),
    ("retrieve_primary", "首次检索", "Retrieval Agent"),
    ("retrieve_retry", "二次检索", "Retrieval Agent"),
    ("diagnose", "诊断分析", "Diagnosis Agent"),
    ("trace", "证据映射", "Traceability Agent"),
    ("score", "置信度评分", "Confidence Agent"),
    ("second_opinion", "二次校正", "Review Agent"),
    ("draft", "工单生成", "WorkOrder Agent"),
    ("validate", "工单校验", "WorkOrder Agent"),
    ("repair_work_order", "工单修复", "WorkOrder Agent"),
    ("respond", "响应封装", "Audit Agent"),
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def progress_template() -> list[AgentProgressItem]:
    return [
        AgentProgressItem(node=node, label=label, agent=agent, status="pending", updated_at=_now())
        for node, label, agent in NODE_DEFINITIONS
    ]


def get_node_meta(node: str) -> tuple[str, str]:
    for current_node, label, agent in NODE_DEFINITIONS:
        if current_node == node:
            return label, agent
    return node, "Unknown Agent"


class DiagnosisSessionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, DiagnosisSessionState] = {}

    def create(self, session_id: str | None = None, run_id: str = "") -> DiagnosisSessionState:
        with self._lock:
            resolved_session_id = session_id or uuid4().hex
            session = DiagnosisSessionState(
                run_id=run_id,
                session_id=resolved_session_id,
                status="queued",
                started_at=_now(),
                progress=progress_template(),
            )
            self._sessions[resolved_session_id] = session
            return deepcopy(session)

    def get(self, session_id: str) -> DiagnosisSessionState:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(session_id)
            return deepcopy(session)

    def mark_running(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions[session_id]
            session.status = "running"

    def update_step(self, session_id: str, node: str, status: str, summary: str, detail: str = "", agent: str = "") -> None:
        with self._lock:
            session = self._sessions[session_id]
            session.status = "running"
            session.current_node = node
            session.current_agent = agent or get_node_meta(node)[1]
            for item in session.progress:
                if item.node == node:
                    item.status = status  # type: ignore[assignment]
                    item.summary = summary
                    item.detail = detail
                    item.agent = agent or item.agent
                    item.updated_at = _now()
                    break

    def complete(self, session_id: str, response_payload: DiagnosisResponse) -> None:
        with self._lock:
            session = self._sessions[session_id]
            session.run_id = response_payload.run_id
            for item in session.progress:
                if item.status == "pending":
                    item.status = "skipped"
                    item.summary = item.summary or "This optional branch did not trigger for the current request."
                    item.detail = item.detail or "The workflow skipped it based on recall, confidence, or validation state."
                    item.updated_at = _now()
            session.status = "completed"
            session.finished_at = _now()
            session.current_node = "respond"
            session.current_agent = get_node_meta("respond")[1]
            session.response = response_payload

    def fail(self, session_id: str, error_message: str) -> None:
        with self._lock:
            session = self._sessions[session_id]
            session.status = "failed"
            session.error_message = error_message
            session.finished_at = _now()
            session.current_agent = session.current_agent or "System Agent"

    def event_callback(self, session_id: str) -> Callable[[dict], None]:
        def _callback(event: dict) -> None:
            self.update_step(
                session_id=session_id,
                node=str(event.get("node", "")),
                status=str(event.get("status", "running")),
                summary=str(event.get("summary", "")),
                detail=str(event.get("detail", "")),
                agent=str(event.get("agent", "")),
            )

        return _callback


SESSION_STORE = DiagnosisSessionStore()
