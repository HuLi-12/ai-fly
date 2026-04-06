from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.config import Settings
from app.models.schemas import DiagnosisRequest


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normalize_request_payload(request: DiagnosisRequest) -> dict[str, Any]:
    payload = request.model_dump()
    payload["fault_code"] = payload["fault_code"].strip().upper()
    payload["symptom_text"] = " ".join(payload["symptom_text"].split())
    payload["device_type"] = " ".join(payload["device_type"].split())
    payload["context_notes"] = " ".join(payload["context_notes"].split())
    return payload


def request_hash_for_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def state_excerpt(state: dict[str, Any]) -> dict[str, Any]:
    evidence = state.get("evidence") or []
    confidence = state.get("confidence")
    validation_result = state.get("validation_result")
    response = state.get("response")
    return {
        "task_type": state.get("task_type", ""),
        "evidence_count": len(evidence),
        "risk_level": state.get("risk_level", ""),
        "provider_used": state.get("provider_used", ""),
        "retrieval_attempts": state.get("retrieval_attempts", 0),
        "second_opinion_attempts": state.get("second_opinion_attempts", 0),
        "repair_attempts": state.get("repair_attempts", 0),
        "case_memory_count": state.get("case_memory_count", 0),
        "confidence_score": getattr(confidence, "overall_score", None),
        "validation_status": getattr(validation_result, "status", ""),
        "response_request_id": getattr(response, "request_id", ""),
    }


@dataclass(slots=True)
class AgentRunContext:
    run_id: str
    session_id: str
    request_hash: str
    idempotency_key: str
    normalized_request: dict[str, Any]
    started_at: str
    deadline_epoch: float
    user_id: str = ""

    @classmethod
    def create(
        cls,
        settings: Settings,
        request: DiagnosisRequest,
        user_id: str = "",
        session_id: str = "",
    ) -> "AgentRunContext":
        normalized = normalize_request_payload(request)
        request_hash = request_hash_for_payload(normalized)
        run_id = session_id or uuid4().hex
        started_at = now_iso()
        return cls(
            run_id=run_id,
            session_id=session_id or run_id,
            request_hash=request_hash,
            idempotency_key=request_hash[:24],
            normalized_request=normalized,
            started_at=started_at,
            deadline_epoch=time.perf_counter() + float(settings.workflow_timeout_seconds),
            user_id=user_id,
        )
