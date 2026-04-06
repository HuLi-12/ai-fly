from __future__ import annotations

import time
from threading import Thread

from fastapi import APIRouter, Depends, HTTPException

from app.agents.graph import WORKFLOW
from app.core.config import get_settings
from app.models.schemas import (
    AgentMetricsResponse,
    AgentRunReplayResponse,
    ConfirmRequest,
    ConfirmResponse,
    DiagnosisRequest,
    DiagnosisResponse,
    DiagnosisSessionStartResponse,
    DiagnosisSessionState,
)
from app.repositories.agent_runtime import AgentRuntimeRepository
from app.repositories.portal import PortalRepository
from app.services.agent_observability import log_agent_event
from app.services.agent_runtime import AgentRunContext
from app.services.auth import PortalUser, get_optional_current_user
from app.services.diagnosis_sessions import SESSION_STORE


router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])


def _runtime_repo() -> AgentRuntimeRepository:
    settings = get_settings()
    return AgentRuntimeRepository(settings.agent_runtime_db_path)


def _persist_diagnosis_response(response: DiagnosisResponse, request: DiagnosisRequest, user: PortalUser | None) -> DiagnosisResponse:
    settings = get_settings()
    portal_repo = PortalRepository(settings.portal_db_path)
    work_order = portal_repo.create_work_order_from_diagnosis(
        request_payload=request.model_dump(),
        diagnosis_response=response.model_dump(),
        user=user,
    )
    response.work_order_id = work_order["work_order_id"]
    return response


def _cache_lookup(run_ctx: AgentRunContext) -> DiagnosisResponse | None:
    settings = get_settings()
    if not settings.idempotency_enabled:
        return None
    cached = _runtime_repo().find_cached_response(run_ctx.request_hash, settings.idempotency_ttl_hours)
    if not cached:
        return None
    response = DiagnosisResponse.model_validate(cached)
    response.run_id = run_ctx.run_id
    return response


def _workflow_callbacks(repo: AgentRuntimeRepository, run_id: str):
    def snapshot_callback(event: dict) -> None:
        repo.append_snapshot(
            run_id=run_id,
            node=str(event.get("node", "")),
            status=str(event.get("status", "")),
            summary=str(event.get("summary", "")),
            detail=str(event.get("detail", "")),
            payload=dict(event.get("payload", {})),
        )

    def metric_callback(node: str, metric_name: str, metric_value: float, tags: dict | None = None) -> None:
        repo.record_metric(run_id=run_id, node=node, metric_name=metric_name, metric_value=metric_value, tags=tags or {})

    return snapshot_callback, metric_callback


def _execute_workflow(
    run_ctx: AgentRunContext,
    request: DiagnosisRequest,
    user: PortalUser | None,
    progress_callback: object | None = None,
) -> DiagnosisResponse:
    settings = get_settings()
    repo = _runtime_repo()
    started = time.perf_counter()

    repo.create_run(
        run_id=run_ctx.run_id,
        session_id=run_ctx.session_id,
        request_hash=run_ctx.request_hash,
        idempotency_key=run_ctx.idempotency_key,
        request_payload=run_ctx.normalized_request,
        user_id=run_ctx.user_id,
    )
    log_agent_event(
        "workflow_run_started",
        {
            "run_id": run_ctx.run_id,
            "session_id": run_ctx.session_id,
            "request_hash": run_ctx.request_hash,
            "user_id": run_ctx.user_id,
        },
    )
    repo.append_snapshot(
        run_id=run_ctx.run_id,
        node="workflow",
        status="started",
        summary="Workflow run created.",
        detail=f"idempotency_key={run_ctx.idempotency_key}",
        payload=run_ctx.normalized_request,
    )

    cached_response = _cache_lookup(run_ctx)
    if cached_response is not None:
        cached_payload = cached_response.model_dump(mode="json")
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        repo.mark_cache_hit(run_ctx.run_id, cached_payload, duration_ms)
        repo.append_snapshot(
            run_id=run_ctx.run_id,
            node="workflow",
            status="cache_hit",
            summary="Completed using idempotency cache.",
            detail=f"request_id={cached_response.request_id}",
            payload={"request_id": cached_response.request_id, "work_order_id": cached_response.work_order_id},
        )
        log_agent_event(
            "workflow_run_cache_hit",
            {
                "run_id": run_ctx.run_id,
                "request_hash": run_ctx.request_hash,
                "request_id": cached_response.request_id,
                "duration_ms": duration_ms,
            },
        )
        return cached_response

    snapshot_callback, metric_callback = _workflow_callbacks(repo, run_ctx.run_id)
    result = WORKFLOW.invoke(
        {
            "request": request,
            "run_id": run_ctx.run_id,
            "deadline_epoch": run_ctx.deadline_epoch,
            "progress_callback": progress_callback,
            "snapshot_callback": snapshot_callback,
            "metric_callback": metric_callback,
        }
    )
    response = result["response"]
    response.run_id = run_ctx.run_id
    response = _persist_diagnosis_response(response, request, user)
    response.run_id = run_ctx.run_id

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    payload = response.model_dump(mode="json")
    repo.complete_run(run_ctx.run_id, payload, duration_ms)
    repo.append_snapshot(
        run_id=run_ctx.run_id,
        node="workflow",
        status="completed",
        summary="Workflow run completed.",
        detail=f"request_id={response.request_id}",
        payload={"request_id": response.request_id, "work_order_id": response.work_order_id},
    )
    log_agent_event(
        "workflow_run_completed",
        {
            "run_id": run_ctx.run_id,
            "request_id": response.request_id,
            "provider_used": response.provider_used,
            "duration_ms": duration_ms,
        },
    )
    return response


def _run_live_diagnosis_session(run_ctx: AgentRunContext, request: DiagnosisRequest, user: PortalUser | None) -> None:
    SESSION_STORE.mark_running(run_ctx.session_id)
    started = time.perf_counter()
    try:
        response = _execute_workflow(
            run_ctx=run_ctx,
            request=request,
            user=user,
            progress_callback=SESSION_STORE.event_callback(run_ctx.session_id),
        )
        SESSION_STORE.complete(run_ctx.session_id, response)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        repo = _runtime_repo()
        repo.fail_run(run_ctx.run_id, str(exc), duration_ms)
        repo.append_snapshot(
            run_id=run_ctx.run_id,
            node="workflow",
            status="failed",
            summary="Workflow run failed.",
            detail=str(exc),
            payload={"request_hash": run_ctx.request_hash},
        )
        log_agent_event("workflow_run_failed", {"run_id": run_ctx.run_id, "error": str(exc)})
        SESSION_STORE.fail(run_ctx.session_id, str(exc))


@router.post("/start", response_model=DiagnosisResponse)
def start_diagnosis(request: DiagnosisRequest, user: PortalUser | None = Depends(get_optional_current_user)) -> DiagnosisResponse:
    settings = get_settings()
    run_ctx = AgentRunContext.create(settings, request, user_id=user.user_id if user else "")
    started = time.perf_counter()
    try:
        return _execute_workflow(run_ctx=run_ctx, request=request, user=user)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        repo = _runtime_repo()
        repo.fail_run(run_ctx.run_id, str(exc), duration_ms)
        repo.append_snapshot(
            run_id=run_ctx.run_id,
            node="workflow",
            status="failed",
            summary="Workflow run failed.",
            detail=str(exc),
            payload={"request_hash": run_ctx.request_hash},
        )
        log_agent_event("workflow_run_failed", {"run_id": run_ctx.run_id, "error": str(exc)})
        raise


@router.post("/start-live", response_model=DiagnosisSessionStartResponse)
def start_live_diagnosis(
    request: DiagnosisRequest,
    user: PortalUser | None = Depends(get_optional_current_user),
) -> DiagnosisSessionStartResponse:
    settings = get_settings()
    run_ctx = AgentRunContext.create(settings, request, user_id=user.user_id if user else "")
    session = SESSION_STORE.create(session_id=run_ctx.session_id, run_id=run_ctx.run_id)
    worker = Thread(target=_run_live_diagnosis_session, args=(run_ctx, request, user), daemon=True)
    worker.start()
    return DiagnosisSessionStartResponse(run_id=run_ctx.run_id, session_id=session.session_id, status=session.status)


@router.get("/sessions/{session_id}", response_model=DiagnosisSessionState)
def get_live_diagnosis_session(session_id: str) -> DiagnosisSessionState:
    try:
        return SESSION_STORE.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Diagnosis session not found.") from exc


@router.get("/runs/{run_id}", response_model=AgentRunReplayResponse)
def get_run_replay(run_id: str) -> AgentRunReplayResponse:
    try:
        return _runtime_repo().get_run_replay(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found.") from exc


@router.get("/replay/{request_id}", response_model=AgentRunReplayResponse)
def get_run_replay_by_request(request_id: str) -> AgentRunReplayResponse:
    try:
        return _runtime_repo().get_run_replay_by_request_id(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Request replay not found.") from exc


@router.get("/metrics", response_model=AgentMetricsResponse)
def get_workflow_metrics() -> AgentMetricsResponse:
    return _runtime_repo().get_metrics_summary()


@router.post("/confirm", response_model=ConfirmResponse)
def confirm_result(request: ConfirmRequest, user: PortalUser | None = Depends(get_optional_current_user)) -> ConfirmResponse:
    settings = get_settings()
    portal_repo = PortalRepository(settings.portal_db_path)
    work_order = portal_repo.get_work_order_by_request(request.request_id)
    if work_order is not None:
        updated = portal_repo.decide_work_order(
            work_order_id=work_order["work_order_id"],
            approved=request.approved,
            comment=request.operator_note,
            edited_actions=request.edited_actions,
            reviewer=user,
        )
        summary = updated["latest_note"]
    else:
        summary = "Manual review has been recorded."
        if request.operator_note:
            summary = f"{summary} Note: {request.operator_note}"
    return ConfirmResponse(status="confirmed" if request.approved else "rejected", final_summary=summary)
