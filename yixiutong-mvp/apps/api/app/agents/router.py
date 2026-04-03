from __future__ import annotations

from app.models.schemas import DiagnosisRequest


def route_request(request: DiagnosisRequest) -> str:
    text = f"{request.fault_code} {request.symptom_text} {request.context_notes}".lower()
    if request.scene_type != "fault_diagnosis":
        return request.scene_type
    if any(keyword in text for keyword in ["process", "torque", "heat treatment", "deviation", "参数", "工艺", "偏差"]):
        return "process_deviation"
    if any(keyword in text for keyword in ["defect", "scratch", "dimension", "inspection", "质检", "缺陷", "尺寸"]):
        return "quality_inspection"
    return "fault_diagnosis"
