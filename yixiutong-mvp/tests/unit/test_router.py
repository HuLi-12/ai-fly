from app.agents.router import route_request
from app.models.schemas import DiagnosisRequest


def test_route_request_uses_fault_code_prefix_and_keywords():
    decision = route_request(
        DiagnosisRequest(
            fault_code="PROC-118",
            symptom_text="热处理保温时间低于下限，批次参数出现漂移。",
            device_type="热处理设备",
            context_notes="需要冻结批次并复核工艺卡。",
            scene_type="fault_diagnosis",
        )
    )

    assert decision.scene_type == "process_deviation"
    assert decision.confidence >= 0.8
    assert "PROC-" in "".join(decision.matched_signals)


def test_route_request_respects_explicit_scene_selection():
    decision = route_request(
        DiagnosisRequest(
            fault_code="E-204",
            symptom_text="设备振动异常并伴随温升。",
            device_type="装配工位",
            context_notes="夜班告警升级。",
            scene_type="quality_inspection",
        )
    )

    assert decision.scene_type == "quality_inspection"
    assert decision.confidence == 0.99
    assert "用户显式选择" in decision.reason
