from __future__ import annotations

from typing import TypedDict
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
    TraceabilityItem,
    TriggeredRule,
    ValidationResult,
    WorkOrderDraft,
)
from app.repositories.corpus import load_index
from app.services.confidence import compute_confidence
from app.services.retrieval import search
from app.services.rules import evaluate_risk_details, load_rules
from app.services.traceability import build_traceability
from app.services.work_orders import build_work_order_draft, validate_work_order


class WorkflowState(TypedDict, total=False):
    request: DiagnosisRequest
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


def _append_trace(state: WorkflowState, node: str, summary: str, detail: str = "", status: str = "completed") -> None:
    trace = list(state.get("execution_trace", []))
    trace.append(
        ExecutionTraceItem(
            node=node,
            status=status,
            summary=summary,
            detail=detail,
        )
    )
    state["execution_trace"] = trace


def _build_query(request: DiagnosisRequest, task_type: str) -> str:
    return f"{request.fault_code} {request.symptom_text} {request.context_notes} {task_type}"


def _build_retry_query(request: DiagnosisRequest, task_type: str) -> str:
    scene_hint = {
        "fault_diagnosis": "振动 温升 告警 复核",
        "process_deviation": "工艺 参数 偏差 冻结 复核",
        "quality_inspection": "缺陷 复检 隔离 追溯",
    }.get(task_type, "")
    return f"{request.fault_code} {request.symptom_text} {scene_hint}"


def _merge_evidence(primary: list[EvidenceItem], secondary: list[EvidenceItem], top_k: int = 5) -> list[EvidenceItem]:
    merged: dict[str, EvidenceItem] = {}
    for item in primary + secondary:
        key = item.evidence_id or f"{item.title}:{item.snippet}"
        existing = merged.get(key)
        if existing is None or item.score > existing.score:
            merged[key] = item
    return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:top_k]


def _route_node(state: WorkflowState) -> WorkflowState:
    state["task_type"] = route_request(state["request"])
    state["retrieval_attempts"] = 0
    state["second_opinion_attempts"] = 0
    state["repair_attempts"] = 0
    _append_trace(
        state,
        node="route",
        summary=f"请求已路由到 {state['task_type']} 场景。",
        detail=f"fault_code={state['request'].fault_code}",
    )
    return state


def _retrieve_primary_node(state: WorkflowState) -> WorkflowState:
    settings = get_settings()
    corpus_items = load_index(settings.index_manifest_path)
    scene_type = state["task_type"]
    query = _build_query(state["request"], scene_type)
    state["evidence"] = search(query, corpus_items, scene_type=scene_type, top_k=5, settings=settings)
    state["retrieval_attempts"] = 1

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
        node="retrieve",
        summary=f"首次召回 {len(state['evidence'])} 条证据，风险等级判定为 {risk_level}。",
        detail=", ".join(item.rule_id for item in triggered_rules) or "no-rule-hit",
        status="warning" if len(state["evidence"]) < 3 else "completed",
    )
    return state


def _retrieve_retry_node(state: WorkflowState) -> WorkflowState:
    settings = get_settings()
    corpus_items = load_index(settings.index_manifest_path)
    retry_query = _build_retry_query(state["request"], state["task_type"])
    retry_evidence = search(retry_query, corpus_items, scene_type=state["task_type"], top_k=8, settings=settings)
    state["evidence"] = _merge_evidence(state.get("evidence", []), retry_evidence, top_k=5)
    state["retrieval_attempts"] = state.get("retrieval_attempts", 1) + 1
    _append_trace(
        state,
        node="retrieve_retry",
        summary=f"低召回触发二次检索，当前保留 {len(state['evidence'])} 条证据。",
        detail=f"retry_query={retry_query}",
        status="retry",
    )
    return state


def _should_retry_retrieval(state: WorkflowState) -> str:
    if len(state.get("evidence", [])) < 3 and state.get("retrieval_attempts", 0) < 2:
        return "retry"
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
        summary=f"已生成诊断结果，provider={provider_used}。",
        detail=f"causes={len(diagnosis.possible_causes)}, checks={len(diagnosis.recommended_checks)}, actions={len(diagnosis.recommended_actions)}",
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
        summary=f"已建立 {len(traceability)} 条建议-证据映射。",
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
    )
    state["confidence"] = confidence
    _append_trace(
        state,
        node="score",
        summary=f"已计算置信度 {confidence.overall_score:.1f}（{confidence.level}）。",
        detail=" | ".join(confidence.warnings) or "no-warning",
        status="warning" if confidence.requires_human_review else "completed",
    )
    return state


def _should_run_second_opinion(state: WorkflowState) -> str:
    if state["confidence"].overall_score < 60 and state.get("second_opinion_attempts", 0) < 1:
        return "second_opinion"
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
        summary="低置信度触发二次校正，已融合启发式建议。",
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
        node="draft_work_order",
        summary="已生成结构化工单草案。",
        detail=f"steps={len(work_order.step_items)}",
    )
    return state


def _validate_node(state: WorkflowState) -> WorkflowState:
    validation_result = validate_work_order(state["work_order_draft"])
    state["validation_result"] = validation_result
    state["work_order_draft"].validation_status = validation_result.status
    _append_trace(
        state,
        node="validate",
        summary=f"工单校验状态：{validation_result.status}。",
        detail="; ".join(issue.message for issue in validation_result.issues) or "no-issues",
        status="warning" if validation_result.issues else "completed",
    )
    return state


def _should_repair_work_order(state: WorkflowState) -> str:
    if state["validation_result"].status == "needs_revision" and state.get("repair_attempts", 0) < 1:
        return "repair"
    return "respond"


def _repair_work_order_node(state: WorkflowState) -> WorkflowState:
    work_order = state["work_order_draft"]
    issues = state["validation_result"].issues
    issue_fields = {issue.field for issue in issues}

    if "safety_notes" in issue_fields and not work_order.safety_notes:
        work_order.safety_notes = ["补充安全注意事项后方可提交。"]
    if "step_items" in issue_fields and work_order.steps and not work_order.step_items:
        work_order.step_items = []

    work_order.validation_status = "draft"
    state["work_order_draft"] = work_order
    state["repair_attempts"] = state.get("repair_attempts", 0) + 1
    _append_trace(
        state,
        node="repair_work_order",
        summary="根据校验结果执行了一次自动修复。",
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

    response = DiagnosisResponse(
        request_id=str(uuid4()),
        storage_mode="workspace-locked",
        provider_used=state["provider_used"],
        scene_type=state["task_type"],
        evidence=state["evidence"],
        diagnosis=state["diagnosis_result"],
        risk_level=state["risk_level"],
        work_order_draft=state["work_order_draft"],
        requires_human_confirmation=requires_confirmation,
        confidence=state["confidence"],
        traceability=state["traceability"],
        triggered_rules=state["triggered_rules"],
        execution_trace=state.get("execution_trace", []),
        validation_result=state["validation_result"],
        approval_reasons=approval_reasons,
    )
    _append_trace(
        state,
        node="respond",
        summary="工作流已完成响应封装。",
        detail=" | ".join(approval_reasons) or "no-approval-required",
        status="warning" if requires_confirmation else "completed",
    )
    response.execution_trace = state.get("execution_trace", [])
    state["response"] = response
    return state


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("route", _route_node)
    graph.add_node("retrieve_primary", _retrieve_primary_node)
    graph.add_node("retrieve_retry", _retrieve_retry_node)
    graph.add_node("diagnose", _diagnose_node)
    graph.add_node("trace", _trace_node)
    graph.add_node("score", _score_node)
    graph.add_node("second_opinion", _second_opinion_node)
    graph.add_node("draft", _draft_work_order_node)
    graph.add_node("validate", _validate_node)
    graph.add_node("repair_work_order", _repair_work_order_node)
    graph.add_node("respond", _respond_node)

    graph.add_edge(START, "route")
    graph.add_edge("route", "retrieve_primary")
    graph.add_conditional_edges(
        "retrieve_primary",
        _should_retry_retrieval,
        {
            "retry": "retrieve_retry",
            "diagnose": "diagnose",
        },
    )
    graph.add_edge("retrieve_retry", "diagnose")
    graph.add_edge("diagnose", "trace")
    graph.add_edge("trace", "score")
    graph.add_conditional_edges(
        "score",
        _should_run_second_opinion,
        {
            "second_opinion": "second_opinion",
            "draft": "draft",
        },
    )
    graph.add_edge("second_opinion", "trace")
    graph.add_edge("draft", "validate")
    graph.add_conditional_edges(
        "validate",
        _should_repair_work_order,
        {
            "repair": "repair_work_order",
            "respond": "respond",
        },
    )
    graph.add_edge("repair_work_order", "validate")
    graph.add_edge("respond", END)
    return graph.compile()


WORKFLOW = build_workflow()
