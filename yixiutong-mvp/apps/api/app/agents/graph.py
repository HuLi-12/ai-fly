from __future__ import annotations

import time
from typing import Any, Callable, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.agents.audit import evaluate_approval_policy
from app.agents.diagnosis import generate_diagnosis, refine_diagnosis_with_second_opinion
from app.agents.router import route_request
from app.core.config import get_settings
from app.models.schemas import (
    ConfidenceScore,
    DiagnosisRequest,
    DiagnosisResponse,
    DiagnosisResult,
    EvidenceItem,
    ExecutionTraceItem,
    RouteDecision,
    TraceabilityItem,
    TriggeredRule,
    ValidationResult,
    WorkOrderDraft,
    WorkOrderStepItem,
)
from app.repositories.corpus import load_index
from app.repositories.portal import PortalRepository
from app.services.agent_observability import log_agent_event
from app.services.agent_runtime import state_excerpt
from app.services.confidence import compute_confidence
from app.services.diagnosis_sessions import get_node_meta
from app.services.retrieval import search
from app.services.rules import evaluate_risk_details, load_rules
from app.services.traceability import build_traceability
from app.services.work_orders import build_work_order_draft, validate_work_order


class WorkflowState(TypedDict, total=False):
    request: DiagnosisRequest
    run_id: str
    deadline_epoch: float
    snapshot_callback: object
    metric_callback: object
    progress_callback: object
    route_decision: RouteDecision
    task_type: str
    evidence: list[EvidenceItem]
    risk_level: str
    risk_matches: list[str]
    triggered_rules: list[TriggeredRule]
    provider_used: str
    diagnosis_result: DiagnosisResult
    traceability: list[TraceabilityItem]
    confidence: ConfidenceScore
    validation_result: ValidationResult
    execution_trace: list[ExecutionTraceItem]
    work_order_draft: WorkOrderDraft
    approval_reasons: list[str]
    response: DiagnosisResponse
    retrieval_attempts: int
    second_opinion_attempts: int
    repair_attempts: int
    case_memory_count: int


DEADLINE_GUARDED_NODES = {"diagnose"}


def _emit_progress(state: WorkflowState, node: str, status: str, summary: str, detail: str = "") -> None:
    callback = state.get("progress_callback")
    label, agent = get_node_meta(node)
    if callable(callback):
        callback(
            {
                "node": node,
                "label": label,
                "agent": agent,
                "status": status,
                "summary": summary,
                "detail": detail,
            }
        )


def _record_snapshot(state: WorkflowState, node: str, status: str, summary: str, detail: str = "") -> None:
    callback = state.get("snapshot_callback")
    if callable(callback):
        callback(
            {
                "node": node,
                "status": status,
                "summary": summary,
                "detail": detail,
                "payload": state_excerpt(state),
            }
        )


def _record_metric(state: WorkflowState, node: str, metric_name: str, metric_value: float, tags: dict[str, Any] | None = None) -> None:
    callback = state.get("metric_callback")
    if callable(callback):
        callback(node, metric_name, float(metric_value), tags or {})


def _ensure_before_deadline(state: WorkflowState, node: str) -> None:
    deadline = state.get("deadline_epoch")
    if deadline is None:
        return
    if node not in DEADLINE_GUARDED_NODES:
        return
    if time.perf_counter() > deadline:
        raise TimeoutError(f"Workflow deadline exceeded before node '{node}'.")


def _append_trace(state: WorkflowState, node: str, summary: str, detail: str = "", status: str = "completed") -> None:
    label, agent = get_node_meta(node)
    trace = list(state.get("execution_trace", []))
    trace.append(ExecutionTraceItem(node=node, status=status, summary=summary, detail=detail, agent=agent))
    state["execution_trace"] = trace
    _emit_progress(state, node=node, status=status, summary=summary, detail=detail)
    _record_snapshot(state, node=node, status=status, summary=summary, detail=detail)
    log_agent_event(
        "agent_node_finished",
        {
            "run_id": state.get("run_id", ""),
            "node": node,
            "status": status,
            "summary": summary,
            "detail": detail,
        },
    )


def _mark_skipped(state: WorkflowState, node: str, summary: str, detail: str = "") -> None:
    _emit_progress(state, node=node, status="skipped", summary=summary, detail=detail)
    _record_snapshot(state, node=node, status="skipped", summary=summary, detail=detail)
    log_agent_event(
        "agent_node_skipped",
        {
            "run_id": state.get("run_id", ""),
            "node": node,
            "summary": summary,
            "detail": detail,
        },
    )


def _with_node_runtime(node: str, summary: str, handler: Callable[[WorkflowState], WorkflowState]) -> Callable[[WorkflowState], WorkflowState]:
    def _wrapped(state: WorkflowState) -> WorkflowState:
        _ensure_before_deadline(state, node)
        started = time.perf_counter()
        _emit_progress(state, node=node, status="running", summary=summary)
        _record_snapshot(state, node=node, status="running", summary=summary)
        log_agent_event(
            "agent_node_started",
            {"run_id": state.get("run_id", ""), "node": node, "summary": summary},
        )
        try:
            next_state = handler(state)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            _record_metric(state, node, "node_duration_ms", duration_ms, {"outcome": "failed"})
            _emit_progress(state, node=node, status="failed", summary=f"{summary} failed", detail=str(exc))
            _record_snapshot(state, node=node, status="failed", summary=f"{summary} failed", detail=str(exc))
            log_agent_event(
                "agent_node_failed",
                {
                    "run_id": state.get("run_id", ""),
                    "node": node,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                },
            )
            raise
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        _record_metric(state, node, "node_duration_ms", duration_ms, {"outcome": "ok"})
        return next_state

    return _wrapped


def _build_query(request: DiagnosisRequest, task_type: str) -> str:
    return f"{request.fault_code} {request.symptom_text} {request.context_notes} {task_type}"


def _build_retry_query(request: DiagnosisRequest, task_type: str) -> str:
    scene_hint = {
        "fault_diagnosis": "vibration temperature alarm bearing cooling manual case",
        "process_deviation": "process deviation parameter batch freeze review",
        "quality_inspection": "inspection defect quarantine mrb traceability",
    }.get(task_type, "")
    return f"{request.fault_code} {request.symptom_text} {scene_hint}".strip()


def _merge_evidence(primary: list[EvidenceItem], secondary: list[EvidenceItem], top_k: int = 5) -> list[EvidenceItem]:
    merged: dict[str, EvidenceItem] = {}
    for item in primary + secondary:
        key = item.evidence_id or f"{item.title}:{item.snippet}"
        existing = merged.get(key)
        if existing is None or item.score > existing.score:
            merged[key] = item
    return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:top_k]


def _load_agent_corpus(task_type: str) -> tuple[list[dict], int]:
    settings = get_settings()
    corpus_items = load_index(settings.index_manifest_path)
    portal_repo = PortalRepository(settings.portal_db_path)
    case_memory_items = portal_repo.list_case_memory_items(scene_type=task_type, limit=12)
    return corpus_items + case_memory_items, len(case_memory_items)


def _route_node(state: WorkflowState) -> WorkflowState:
    route_decision = route_request(state["request"])
    state["route_decision"] = route_decision
    state["task_type"] = route_decision.scene_type
    state["retrieval_attempts"] = 0
    state["second_opinion_attempts"] = 0
    state["repair_attempts"] = 0
    state["case_memory_count"] = 0
    _append_trace(
        state,
        node="route",
        summary=f"Request routed to {route_decision.scene_type}.",
        detail=f"confidence={route_decision.confidence:.2f}; reason={route_decision.reason}",
    )
    return state


def _retrieve_primary_node(state: WorkflowState) -> WorkflowState:
    settings = get_settings()
    scene_type = state["task_type"]
    corpus_items, case_memory_count = _load_agent_corpus(scene_type)
    query = _build_query(state["request"], scene_type)
    state["evidence"] = search(query, corpus_items, scene_type=scene_type, top_k=5, settings=settings)
    state["retrieval_attempts"] = 1
    state["case_memory_count"] = case_memory_count

    rules = load_rules(settings.materials_root / "rules" / "risk_rules.json")
    risk_level, triggered_rules = evaluate_risk_details(
        scene_type=scene_type,
        fault_code=state["request"].fault_code,
        symptom_text=state["request"].symptom_text,
        context_notes=state["request"].context_notes,
        rules=rules,
    )
    state["risk_level"] = risk_level
    state["triggered_rules"] = triggered_rules
    state["risk_matches"] = [item.message for item in triggered_rules]
    _append_trace(
        state,
        node="retrieve_primary",
        summary=f"Primary retrieval returned {len(state['evidence'])} evidence items.",
        detail=f"risk={risk_level}; case_memory={case_memory_count}; rules={','.join(item.rule_id for item in triggered_rules) or 'none'}",
        status="warning" if len(state["evidence"]) < 3 else "completed",
    )
    return state


def _retrieve_retry_node(state: WorkflowState) -> WorkflowState:
    settings = get_settings()
    corpus_items, case_memory_count = _load_agent_corpus(state["task_type"])
    retry_query = _build_retry_query(state["request"], state["task_type"])
    retry_evidence = search(retry_query, corpus_items, scene_type=state["task_type"], top_k=8, settings=settings)
    state["evidence"] = _merge_evidence(state.get("evidence", []), retry_evidence, top_k=5)
    state["retrieval_attempts"] = state.get("retrieval_attempts", 1) + 1
    state["case_memory_count"] = case_memory_count
    _append_trace(
        state,
        node="retrieve_retry",
        summary=f"Secondary retrieval retained {len(state['evidence'])} evidence items.",
        detail=f"retry_query={retry_query}; case_memory={case_memory_count}",
        status="retry",
    )
    return state


def _should_retry_retrieval(state: WorkflowState) -> str:
    if len(state.get("evidence", [])) < 3 and state.get("retrieval_attempts", 0) < 2:
        return "retry"
    _mark_skipped(
        state,
        node="retrieve_retry",
        summary="Secondary retrieval did not trigger.",
        detail=f"evidence_count={len(state.get('evidence', []))}; retrieval_attempts={state.get('retrieval_attempts', 0)}",
    )
    return "diagnose"


def _diagnose_node(state: WorkflowState) -> WorkflowState:
    settings = get_settings()
    diagnosis, provider_used = generate_diagnosis(
        settings=settings,
        scene_type=state["task_type"],
        fault_code=state["request"].fault_code,
        symptom_text=state["request"].symptom_text,
        context_notes=state["request"].context_notes,
        evidence=state["evidence"],
        risk_matches=state["risk_matches"],
    )
    state["provider_used"] = provider_used
    state["diagnosis_result"] = diagnosis
    _append_trace(
        state,
        node="diagnose",
        summary=f"Diagnosis generated with provider {provider_used}.",
        detail=f"causes={len(diagnosis.possible_causes)}; checks={len(diagnosis.recommended_checks)}; actions={len(diagnosis.recommended_actions)}",
        status="fallback" if provider_used == "heuristic_fallback" else "completed",
    )
    return state


def _trace_node(state: WorkflowState) -> WorkflowState:
    traceability = build_traceability(state["diagnosis_result"], state["evidence"])
    state["traceability"] = traceability
    weak_count = len([item for item in traceability if item.support_level == "weak"])
    _append_trace(
        state,
        node="trace",
        summary=f"Built {len(traceability)} recommendation-to-evidence links.",
        detail=f"weak_links={weak_count}",
        status="warning" if weak_count else "completed",
    )
    return state


def _score_node(state: WorkflowState) -> WorkflowState:
    confidence = compute_confidence(
        evidence_list=state["evidence"],
        traceability=state["traceability"],
        provider_used=state["provider_used"],
        risk_level=state["risk_level"],
        scene_type=state["task_type"],
    )
    state["confidence"] = confidence
    _append_trace(
        state,
        node="score",
        summary=f"Confidence scored at {confidence.overall_score:.1f} ({confidence.level}).",
        detail=" | ".join(confidence.warnings) or "no-warning",
        status="warning" if confidence.requires_human_review else "completed",
    )
    return state


def _should_run_second_opinion(state: WorkflowState) -> str:
    if state["confidence"].overall_score < 60 and state.get("second_opinion_attempts", 0) < 1:
        return "second_opinion"
    _mark_skipped(
        state,
        node="second_opinion",
        summary="Second opinion did not trigger.",
        detail=f"confidence={state['confidence'].overall_score:.1f}; threshold=60.0",
    )
    return "draft"


def _second_opinion_node(state: WorkflowState) -> WorkflowState:
    refined = refine_diagnosis_with_second_opinion(
        scene_type=state["task_type"],
        evidence=state["evidence"],
        risk_matches=state["risk_matches"],
        symptom_text=state["request"].symptom_text,
        diagnosis=state["diagnosis_result"],
        traceability=state["traceability"],
    )
    state["diagnosis_result"] = refined
    state["second_opinion_attempts"] = state.get("second_opinion_attempts", 0) + 1
    _append_trace(
        state,
        node="second_opinion",
        summary="Second-opinion review merged stronger supported recommendations.",
        detail=f"attempt={state['second_opinion_attempts']}",
        status="retry",
    )
    return state


def _draft_work_order_node(state: WorkflowState) -> WorkflowState:
    work_order = build_work_order_draft(
        scene_type=state["task_type"],
        fault_code=state["request"].fault_code,
        symptom_text=state["request"].symptom_text,
        diagnosis=state["diagnosis_result"],
        risk_level=state["risk_level"],
        traceability=state["traceability"],
    )
    state["work_order_draft"] = work_order
    _append_trace(
        state,
        node="draft",
        summary="Structured work-order draft generated.",
        detail=f"step_items={len(work_order.step_items)}",
    )
    return state


def _validate_node(state: WorkflowState) -> WorkflowState:
    validation_result = validate_work_order(state["work_order_draft"])
    state["validation_result"] = validation_result
    state["work_order_draft"].validation_status = validation_result.status
    _append_trace(
        state,
        node="validate",
        summary=f"Work order validation finished with status {validation_result.status}.",
        detail="; ".join(issue.message for issue in validation_result.issues) or "no-issues",
        status="warning" if validation_result.issues else "completed",
    )
    return state


def _should_repair_work_order(state: WorkflowState) -> str:
    if state["validation_result"].status == "needs_revision" and state.get("repair_attempts", 0) < 1:
        return "repair"
    if state["validation_result"].status == "ready_to_submit":
        _mark_skipped(
            state,
            node="repair_work_order",
            summary="Work-order repair did not trigger.",
            detail="validation_result=ready_to_submit",
        )
    return "respond"


def _repair_work_order_node(state: WorkflowState) -> WorkflowState:
    work_order = state["work_order_draft"]
    issues = state["validation_result"].issues
    issue_fields = {issue.field for issue in issues}

    if "safety_notes" in issue_fields and not work_order.safety_notes:
        work_order.safety_notes = ["Add lockout, isolation, and restart conditions before submission."]
    if "step_items" in issue_fields and not work_order.step_items:
        work_order.step_items = []
        for index, step in enumerate(work_order.steps, start=1):
            work_order.step_items.append(
                WorkOrderStepItem(
                    kind="action",
                    title=f"Recovered step {index}",
                    instruction=step,
                    priority="medium",
                    estimated_duration_minutes=15,
                    action_type="planned",
                    evidence_ids=[],
                )
            )

    work_order.validation_status = "draft"
    state["work_order_draft"] = work_order
    state["repair_attempts"] = state.get("repair_attempts", 0) + 1
    _append_trace(
        state,
        node="repair_work_order",
        summary="Automatic work-order repair applied once.",
        detail=f"attempt={state['repair_attempts']}; fields={','.join(sorted(issue_fields)) or 'no-op'}",
        status="retry",
    )
    return state


def _respond_node(state: WorkflowState) -> WorkflowState:
    requires_confirmation, approval_reasons = evaluate_approval_policy(
        risk_level=state["risk_level"],
        evidence=state["evidence"],
        confidence=state["confidence"],
        validation_result=state["validation_result"],
        provider_used=state["provider_used"],
    )
    state["approval_reasons"] = approval_reasons
    route_decision = state["route_decision"]

    response = DiagnosisResponse(
        run_id=state.get("run_id", ""),
        request_id=str(uuid4()),
        storage_mode="workspace-locked",
        provider_used=state["provider_used"],
        scene_type=state["task_type"],  # type: ignore[arg-type]
        route_confidence=route_decision.confidence,
        route_reason=route_decision.reason,
        route_signals=route_decision.matched_signals,
        evidence=state["evidence"],
        diagnosis=state["diagnosis_result"],
        risk_level=state["risk_level"],  # type: ignore[arg-type]
        work_order_draft=state["work_order_draft"],
        requires_human_confirmation=requires_confirmation,
        confidence=state["confidence"],
        traceability=state["traceability"],
        triggered_rules=state["triggered_rules"],
        execution_trace=state.get("execution_trace", []),
        validation_result=state["validation_result"],
        approval_reasons=approval_reasons,
    )
    state["response"] = response
    _append_trace(
        state,
        node="respond",
        summary="Workflow response packaged successfully.",
        detail=" | ".join(approval_reasons) or "no-approval-required",
        status="warning" if requires_confirmation else "completed",
    )
    response.execution_trace = state.get("execution_trace", [])
    return state


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("route", _with_node_runtime("route", "Routing request", _route_node))
    graph.add_node("retrieve_primary", _with_node_runtime("retrieve_primary", "Running primary retrieval", _retrieve_primary_node))
    graph.add_node("retrieve_retry", _with_node_runtime("retrieve_retry", "Running secondary retrieval", _retrieve_retry_node))
    graph.add_node("diagnose", _with_node_runtime("diagnose", "Generating diagnosis", _diagnose_node))
    graph.add_node("trace", _with_node_runtime("trace", "Building traceability map", _trace_node))
    graph.add_node("score", _with_node_runtime("score", "Calculating confidence", _score_node))
    graph.add_node("second_opinion", _with_node_runtime("second_opinion", "Running second opinion", _second_opinion_node))
    graph.add_node("draft", _with_node_runtime("draft", "Generating work order", _draft_work_order_node))
    graph.add_node("validate", _with_node_runtime("validate", "Validating work order", _validate_node))
    graph.add_node("repair_work_order", _with_node_runtime("repair_work_order", "Repairing work order", _repair_work_order_node))
    graph.add_node("respond", _with_node_runtime("respond", "Packaging final response", _respond_node))

    graph.add_edge(START, "route")
    graph.add_edge("route", "retrieve_primary")
    graph.add_conditional_edges(
        "retrieve_primary",
        _should_retry_retrieval,
        {"retry": "retrieve_retry", "diagnose": "diagnose"},
    )
    graph.add_edge("retrieve_retry", "diagnose")
    graph.add_edge("diagnose", "trace")
    graph.add_edge("trace", "score")
    graph.add_conditional_edges(
        "score",
        _should_run_second_opinion,
        {"second_opinion": "second_opinion", "draft": "draft"},
    )
    graph.add_edge("second_opinion", "trace")
    graph.add_edge("draft", "validate")
    graph.add_conditional_edges(
        "validate",
        _should_repair_work_order,
        {"repair": "repair_work_order", "respond": "respond"},
    )
    graph.add_edge("repair_work_order", "validate")
    graph.add_edge("respond", END)
    return graph.compile()


WORKFLOW = build_workflow()
