from __future__ import annotations

from app.models.schemas import DiagnosisRequest, RouteDecision


SCENE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "fault_diagnosis": (
        "vibration",
        "temperature",
        "bearing",
        "shaft",
        "coupling",
        "cooling",
        "alarm",
        "shutdown",
        "振动",
        "温升",
        "温度",
        "轴承",
        "联轴器",
        "冷却",
        "告警",
        "停机",
    ),
    "process_deviation": (
        "process",
        "deviation",
        "torque",
        "heat treatment",
        "dwell",
        "batch",
        "parameter",
        "工艺",
        "偏差",
        "扭矩",
        "热处理",
        "保温",
        "批次",
        "参数",
        "冻结",
    ),
    "quality_inspection": (
        "inspection",
        "defect",
        "scratch",
        "burr",
        "dimension",
        "quarantine",
        "mrb",
        "quality",
        "终检",
        "检验",
        "质量",
        "缺陷",
        "划伤",
        "毛刺",
        "尺寸",
        "隔离",
    ),
}

PREFIX_HINTS: dict[str, tuple[str, str, float]] = {
    "E-": ("fault_diagnosis", "故障码前缀 E- 指向设备故障场景", 4.0),
    "PROC-": ("process_deviation", "故障码前缀 PROC- 指向工艺偏差场景", 5.0),
    "QA-": ("quality_inspection", "故障码前缀 QA- 指向质量处置场景", 5.0),
}


def _normalized_text(request: DiagnosisRequest) -> str:
    return " ".join(
        part.strip().lower()
        for part in [request.fault_code, request.device_type, request.symptom_text, request.context_notes]
        if part and part.strip()
    )


def _score_scenes(text: str, fault_code: str) -> tuple[dict[str, float], dict[str, list[str]]]:
    scores = {scene: 0.0 for scene in SCENE_KEYWORDS}
    matched_signals = {scene: [] for scene in SCENE_KEYWORDS}

    normalized_fault_code = fault_code.strip().upper()
    for prefix, (scene, reason, score) in PREFIX_HINTS.items():
        if normalized_fault_code.startswith(prefix):
            scores[scene] += score
            matched_signals[scene].append(reason)

    for scene, keywords in SCENE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[scene] += 1.0
                matched_signals[scene].append(f"命中关键词 {keyword}")

    return scores, matched_signals


def _build_reason(scene: str, signals: list[str], confidence: float) -> str:
    if signals:
        top_signals = "；".join(signals[:3])
        return f"路由到 {scene}，依据：{top_signals}，置信度 {confidence:.2f}。"
    return f"未命中明显场景信号，按默认 {scene} 处理，置信度 {confidence:.2f}。"


def route_request(request: DiagnosisRequest) -> RouteDecision:
    if request.scene_type != "fault_diagnosis":
        return RouteDecision(
            scene_type=request.scene_type,
            confidence=0.99,
            reason=f"用户显式选择了 {request.scene_type} 场景，优先按该场景执行。",
            matched_signals=[f"前端席位已指定 scene_type={request.scene_type}"],
        )

    text = _normalized_text(request)
    scores, matched_signals = _score_scenes(text, request.fault_code)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_scene, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    margin = max(best_score - second_score, 0.0)

    if best_score <= 0:
        confidence = 0.52
        return RouteDecision(
            scene_type="fault_diagnosis",
            confidence=confidence,
            reason=_build_reason("fault_diagnosis", [], confidence),
            matched_signals=[],
        )

    confidence = min(0.58 + (best_score * 0.05) + (margin * 0.04), 0.97)
    signals = matched_signals[best_scene]
    return RouteDecision(
        scene_type=best_scene,  # type: ignore[arg-type]
        confidence=round(confidence, 2),
        reason=_build_reason(best_scene, signals, confidence),
        matched_signals=signals[:6],
    )
