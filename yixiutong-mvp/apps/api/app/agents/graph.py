from __future__ import annotations

from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.agents.audit import requires_human_confirmation
from app.agents.diagnosis import build_work_order_draft, generate_diagnosis
from app.agents.router import route_request
from app.core.config import get_settings
from app.models.schemas import DiagnosisRequest, DiagnosisResponse, EvidenceItem
from app.repositories.corpus import load_index
from app.services.retrieval import search
from app.services.rules import evaluate_risk, load_rules


class WorkflowState(TypedDict, total=False):
    request: DiagnosisRequest
    task_type: str
    evidence: list[EvidenceItem]
    risk_level: str
    risk_matches: list[str]
    provider_used: str
    diagnosis: dict
    work_order_draft: dict
    response: DiagnosisResponse


def _route_node(state: WorkflowState) -> WorkflowState:
    state["task_type"] = route_request(state["request"])
    return state


def _retrieve_node(state: WorkflowState) -> WorkflowState:
    settings = get_settings()
    corpus_items = load_index(settings.index_manifest_path)
    scene_type = state["task_type"]
    query = f"{state['request'].fault_code} {state['request'].symptom_text} {state['request'].context_notes}"
    state["evidence"] = search(query, corpus_items, scene_type=scene_type, top_k=5)
    rules = load_rules(settings.materials_root / "rules" / "risk_rules.json")
    risk_level, matches = evaluate_risk(
        scene_type=scene_type,
        fault_code=state["request"].fault_code,
        symptom_text=state["request"].symptom_text,
        context_notes=state["request"].context_notes,
        rules=rules,
    )
    state["risk_level"] = risk_level
    state["risk_matches"] = matches
    return state


def _diagnosis_node(state: WorkflowState) -> WorkflowState:
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
    work_order = build_work_order_draft(
        scene_type=state["task_type"],
        request_fault=state["request"].fault_code,
        symptom_text=state["request"].symptom_text,
        diagnosis=diagnosis,
        risk_level=state["risk_level"],
    )
    response = DiagnosisResponse(
        request_id=str(uuid4()),
        storage_mode="workspace-locked",
        provider_used=provider_used,
        scene_type=state["task_type"],
        evidence=state["evidence"],
        diagnosis=diagnosis,
        risk_level=state["risk_level"],
        work_order_draft=work_order,
        requires_human_confirmation=requires_human_confirmation(state["risk_level"], state["evidence"]),
    )
    state["provider_used"] = provider_used
    state["diagnosis"] = diagnosis.model_dump()
    state["work_order_draft"] = work_order.model_dump()
    state["response"] = response
    return state


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("route", _route_node)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("diagnose", _diagnosis_node)
    graph.add_edge(START, "route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "diagnose")
    graph.add_edge("diagnose", END)
    return graph.compile()


WORKFLOW = build_workflow()
