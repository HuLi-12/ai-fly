from __future__ import annotations

from app.models.schemas import (
    DiagnosisResult,
    TraceabilityItem,
    ValidationIssue,
    ValidationResult,
    WorkOrderDraft,
    WorkOrderStepItem,
)


TEMPLATES = {
    "fault_diagnosis": {
        "summary_prefix": "智能排故工单草案",
        "assignee": "维修工程师",
        "safety_notes": ["执行前完成停机挂牌确认。", "未完成人工签核前不得复机。"],
    },
    "process_deviation": {
        "summary_prefix": "工艺偏差处置单草案",
        "assignee": "工艺工程师",
        "safety_notes": ["偏差批次在签审完成前保持冻结。"],
    },
    "quality_inspection": {
        "summary_prefix": "质量处置单草案",
        "assignee": "质量工程师",
        "safety_notes": ["缺陷批次未完成评审前不得放行。"],
    },
}


def _action_type(scene_type: str, action: str) -> str:
    lowered = action.lower()
    if any(keyword in lowered for keyword in ("停", "隔离", "hold", "shutdown", "freeze", "quarantine")):
        return "immediate"
    if scene_type == "quality_inspection" and "观察" in action:
        return "monitor"
    if "monitor" in lowered or "观察" in action:
        return "monitor"
    return "planned"


def _priority(risk_level: str) -> str:
    return {"high": "high", "medium": "medium", "low": "low"}.get(risk_level, "medium")


def build_work_order_draft(
    scene_type: str,
    fault_code: str,
    symptom_text: str,
    diagnosis: DiagnosisResult,
    risk_level: str,
    traceability: list[TraceabilityItem],
) -> WorkOrderDraft:
    template = TEMPLATES[scene_type]
    evidence_references = sorted(
        {
            evidence.evidence_id
            for item in traceability
            for evidence in item.evidence_links
            if evidence.evidence_id
        }
    )

    step_items: list[WorkOrderStepItem] = []
    for recommendation in diagnosis.recommended_checks:
        linked_ids = [
            evidence.evidence_id
            for item in traceability
            if item.recommendation == recommendation
            for evidence in item.evidence_links
        ]
        step_items.append(
            WorkOrderStepItem(
                kind="check",
                title="检查步骤",
                instruction=recommendation,
                priority=_priority(risk_level),
                estimated_duration_minutes=15 if risk_level == "low" else 20,
                evidence_ids=linked_ids,
            )
        )

    for recommendation in diagnosis.recommended_actions:
        linked_ids = [
            evidence.evidence_id
            for item in traceability
            if item.recommendation == recommendation
            for evidence in item.evidence_links
        ]
        step_items.append(
            WorkOrderStepItem(
                kind="action",
                title="处置动作",
                instruction=recommendation,
                priority=_priority(risk_level),
                estimated_duration_minutes=10 if _action_type(scene_type, recommendation) == "immediate" else 25,
                action_type=_action_type(scene_type, recommendation),
                evidence_ids=linked_ids,
            )
        )

    safety_notes = list(template["safety_notes"])
    if risk_level == "high":
        safety_notes.append("当前为高风险场景，必须经过人工审批。")

    return WorkOrderDraft(
        summary=f"{template['summary_prefix']}：{fault_code} | {symptom_text}",
        steps=[item.instruction for item in step_items],
        risk_notice=f"当前风险等级：{risk_level}。执行前请核对安全条件与审批状态。",
        assignee_placeholder=template["assignee"],
        scene_type=scene_type,
        fault_code=fault_code,
        symptom_description=symptom_text,
        evidence_references=evidence_references,
        step_items=step_items,
        safety_notes=safety_notes,
        approval_required=risk_level == "high",
        validation_status="draft",
    )


def validate_work_order(work_order: WorkOrderDraft) -> ValidationResult:
    issues: list[ValidationIssue] = []

    required_fields = {
        "summary": work_order.summary,
        "scene_type": work_order.scene_type,
        "fault_code": work_order.fault_code,
        "symptom_description": work_order.symptom_description,
        "assignee_placeholder": work_order.assignee_placeholder,
    }
    for field_name, value in required_fields.items():
        if not value:
            issues.append(
                ValidationIssue(
                    field=field_name,
                    severity="error",
                    message=f"{field_name} 不能为空。",
                    suggested_fix=f"补充 {field_name} 字段。",
                )
            )

    if not work_order.step_items:
        issues.append(
            ValidationIssue(
                field="step_items",
                severity="error",
                message="工单缺少结构化步骤。",
                suggested_fix="至少生成检查步骤和处置动作。",
            )
        )

    kinds = [item.kind for item in work_order.step_items]
    if "action" in kinds and "check" in kinds:
        first_action = kinds.index("action")
        last_check = max(index for index, kind in enumerate(kinds) if kind == "check")
        if last_check > first_action:
            issues.append(
                ValidationIssue(
                    field="step_items",
                    severity="warning",
                    message="检查步骤应排在处置动作之前。",
                    suggested_fix="调整步骤顺序，先检查后处置。",
                )
            )

    if work_order.approval_required and not work_order.safety_notes:
        issues.append(
            ValidationIssue(
                field="safety_notes",
                severity="error",
                message="高风险工单缺少安全注意事项。",
                suggested_fix="补充高风险场景安全说明。",
            )
        )

    status = "ready_to_submit" if not any(issue.severity == "error" for issue in issues) else "needs_revision"
    return ValidationResult(
        status=status,
        requires_approval=work_order.approval_required,
        issues=issues,
    )
