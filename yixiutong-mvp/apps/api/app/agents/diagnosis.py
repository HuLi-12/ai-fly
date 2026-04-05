from __future__ import annotations

import re

from app.core.config import Settings
from app.models.schemas import DiagnosisResult, EvidenceItem, TraceabilityItem, WorkOrderDraft
from app.services.provider_runtime import generate_structured_with_fallback, generate_text_with_fallback
from app.services.work_orders import build_work_order_draft as build_structured_work_order_draft


DIAGNOSIS_SCHEMA = {
    "possible_causes": ["string"],
    "recommended_checks": ["string"],
    "recommended_actions": ["string"],
}

SECTION_ALIASES = {
    "possible_causes": ("可能原因", "原因判断", "Possible causes", "Likely causes", "Causes"),
    "recommended_checks": ("建议检查", "检查项", "Recommended checks", "Checks", "Inspection checks"),
    "recommended_actions": ("建议处置", "处置动作", "Recommended actions", "Actions", "Immediate actions"),
}


def _fault_diagnosis(evidence: list[EvidenceItem], risk_matches: list[str], symptom_text: str) -> DiagnosisResult:
    combined = f"{' '.join(item.snippet for item in evidence)} {symptom_text}".lower()
    causes: list[str] = []
    checks: list[str] = []

    if any(keyword in combined for keyword in ["vibration", "bearing", "shaft", "振动", "轴承", "联轴器"]):
        causes.append("传动链磨损、轴承松旷或联轴器偏移可能导致振动被放大。")
        checks.append("复核联轴器、紧固件、轴承间隙和润滑状态。")

    if any(keyword in combined for keyword in ["temperature", "cooling", "温度", "冷却", "风机"]):
        causes.append("冷却回路效率下降或风道堵塞可能引发温升并诱发二次振动。")
        checks.append("检查风机状态、冷却回路流量和风道洁净度。")

    if any(keyword in combined for keyword in ["sensor", "alarm", "传感器", "报警"]):
        causes.append("温度传感器漂移或报警链路异常可能放大告警表现。")
        checks.append("使用手持仪表交叉校验测点并核对传感器标定记录。")

    if not causes:
        causes = ["建议按机械链路、热管理和传感链路三段顺序进行排查。"]
        checks = ["先执行停机挂牌、外观检查和基线参数复核。"]

    actions = [
        "记录停机挂牌状态，并保留当前告警快照。",
        "按机械、冷却、传感三段顺序完成排查。",
        "如高风险项未消除，复机前升级至维修复核。",
    ]
    if risk_matches:
        actions.append("命中高风险规则后，未经人工签批不得复机。")

    return DiagnosisResult(
        possible_causes=causes[:3],
        recommended_checks=checks[:3],
        recommended_actions=actions[:4],
    )


def _process_deviation(risk_matches: list[str], symptom_text: str) -> DiagnosisResult:
    causes = [
        "关键工艺参数偏离了合格窗口。",
        "工装或夹具磨损引入了可重复偏差。",
        "换型或交接变更未同步到工艺卡。",
    ]
    if "heat" in symptom_text.lower() or "热处理" in symptom_text or "固化" in symptom_text:
        causes[0] = "热处理或固化参数偏离了合格窗口。"

    actions = [
        "冻结受影响批次，并标记为待复核。",
        "形成临时工艺处置，明确纠偏参数和验证点。",
        "未完成工艺签审前不得恢复正常生产。",
    ]
    if risk_matches:
        actions.append("命中风险规则后，升级到工艺质量联审。")

    return DiagnosisResult(
        possible_causes=causes,
        recommended_checks=[
            "对比当前过程参数、受控工艺卡和最近合格批次。",
            "复核工装校准、夹具磨损和班组交接记录。",
            "检查材料批次、环境温度或换型设定是否发生变化。",
        ],
        recommended_actions=actions[:4],
    )


def _quality_inspection(risk_matches: list[str], symptom_text: str) -> DiagnosisResult:
    causes = [
        "零件存在可重复的尺寸或表面缺陷。",
        "检验方法漂移或量具校准异常导致误判。",
        "上游过程不稳定形成了批次性缺陷模式。",
    ]
    if "scratch" in symptom_text.lower() or "划伤" in symptom_text:
        causes[0] = "表面损伤或搬运污染是首要质量假设。"

    actions = [
        "隔离可疑零件并停止下游放行。",
        "生成检验报告草案，附缺陷证据和追溯字段。",
        "提交 MRB 或质量工程进行处置判定。",
    ]
    if risk_matches:
        actions.append("未完成质量审批前，不得放行该批次。")

    return DiagnosisResult(
        possible_causes=causes,
        recommended_checks=[
            "使用校准后的量具重新执行外观与尺寸复检。",
            "追溯受影响批次、工位和检验员记录。",
            "核对缺陷是否落入既有让步或返工标准。",
        ],
        recommended_actions=actions[:4],
    )


def _heuristic_diagnosis(scene_type: str, evidence: list[EvidenceItem], risk_matches: list[str], symptom_text: str) -> DiagnosisResult:
    if scene_type == "process_deviation":
        return _process_deviation(risk_matches, symptom_text)
    if scene_type == "quality_inspection":
        return _quality_inspection(risk_matches, symptom_text)
    return _fault_diagnosis(evidence, risk_matches, symptom_text)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = " ".join(item.split()).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _normalize_item(text: str) -> str:
    cleaned = re.sub(r"^[\-\*\u2022\d\)\.(\s]+", "", text.strip())
    cleaned = cleaned.strip(" -\t")
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?。；":
        cleaned += "."
    return cleaned


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?。；])\s*|\n+", text)
    return [_normalize_item(chunk) for chunk in chunks if _normalize_item(chunk)]


def _extract_section_block(text: str, aliases: tuple[str, ...]) -> str:
    all_aliases = [alias for values in SECTION_ALIASES.values() for alias in values]
    section_pattern = "|".join(re.escape(alias) for alias in aliases)
    all_pattern = "|".join(re.escape(alias) for alias in all_aliases)
    pattern = re.compile(
        rf"(?is)(?:^|\n)\s*(?:{section_pattern})\s*:?\s*(.*?)(?=(?:\n\s*(?:{all_pattern})\s*:?)|\Z)"
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip()


def _extract_items_from_block(block: str) -> list[str]:
    if not block:
        return []
    items: list[str] = []
    for line in block.splitlines():
        normalized = _normalize_item(line)
        if normalized:
            items.append(normalized)
    if items:
        return _dedupe(items)
    return _dedupe(_split_sentences(block))


def _classify_free_text(text: str) -> dict[str, list[str]]:
    sentences = _split_sentences(text)
    buckets = {
        "possible_causes": [],
        "recommended_checks": [],
        "recommended_actions": [],
    }
    for sentence in sentences:
        lower = sentence.lower()
        if any(keyword in lower for keyword in ("cause", "due to", "wear", "drift", "degradation", "damage", "instability", "原因", "磨损", "漂移", "异常", "损伤")):
            buckets["possible_causes"].append(sentence)
        if any(keyword in lower for keyword in ("check", "inspect", "verify", "measure", "trace", "review", "confirm", "检查", "复核", "确认", "追溯", "校验")):
            buckets["recommended_checks"].append(sentence)
        if any(keyword in lower for keyword in ("hold", "stop", "escalate", "repair", "replace", "quarantine", "document", "resume", "停", "隔离", "升级", "更换", "处置", "放行")):
            buckets["recommended_actions"].append(sentence)
    return {key: _dedupe(value) for key, value in buckets.items()}


def _merge_with_baseline(parsed: dict[str, list[str]], baseline: DiagnosisResult) -> DiagnosisResult:
    return DiagnosisResult(
        possible_causes=_dedupe(parsed["possible_causes"] + baseline.possible_causes)[:3],
        recommended_checks=_dedupe(parsed["recommended_checks"] + baseline.recommended_checks)[:3],
        recommended_actions=_dedupe(parsed["recommended_actions"] + baseline.recommended_actions)[:4],
    )


def _diagnosis_from_text(
    scene_type: str,
    evidence: list[EvidenceItem],
    risk_matches: list[str],
    symptom_text: str,
    llm_text: str,
) -> DiagnosisResult:
    baseline = _heuristic_diagnosis(scene_type, evidence, risk_matches, symptom_text)
    parsed = {
        key: _extract_items_from_block(_extract_section_block(llm_text, aliases))
        for key, aliases in SECTION_ALIASES.items()
    }
    if not any(parsed.values()):
        parsed = _classify_free_text(llm_text)
    return _merge_with_baseline(parsed, baseline)


def generate_diagnosis(
    settings: Settings,
    scene_type: str,
    fault_code: str,
    symptom_text: str,
    context_notes: str,
    evidence: list[EvidenceItem],
    risk_matches: list[str],
) -> tuple[DiagnosisResult, str]:
    messages = [
        {
            "role": "user",
            "content": (
                f"场景: {scene_type}\n"
                f"故障码/问题编号: {fault_code}\n"
                f"症状描述: {symptom_text}\n"
                f"补充上下文: {context_notes}\n"
                f"证据片段: {[item.model_dump() for item in evidence]}\n"
                f"命中规则: {risk_matches}"
            ),
        }
    ]
    system_prompt = (
        "你是一名面向航空制造与运维场景的智能协同 Agent。"
        "请严格基于给定证据输出诊断建议，不要编造证据中不存在的内容。"
        "仅返回 JSON。"
    )
    try:
        structured, provider_used = generate_structured_with_fallback(
            settings=settings,
            messages=messages,
            schema=DIAGNOSIS_SCHEMA,
            system_prompt=system_prompt,
            options={"temperature": 0.1},
        )
        diagnosis = DiagnosisResult(**structured)
        return diagnosis, provider_used
    except Exception:
        text_prompt = (
            "你是一名面向航空制造与运维场景的智能协同 Agent。"
            "请只基于证据回答，并按下面固定标题输出纯文本，每个标题下给 2 到 3 条简短编号项。\n"
            "可能原因:\n"
            "1. ...\n"
            "2. ...\n"
            "建议检查:\n"
            "1. ...\n"
            "2. ...\n"
            "建议处置:\n"
            "1. ...\n"
            "2. ..."
        )
        try:
            llm_text, provider_used = generate_text_with_fallback(
                settings=settings,
                messages=messages,
                system_prompt=text_prompt,
                options={"temperature": 0.0, "num_predict": 220, "num_ctx": 2048},
            )
            diagnosis = _diagnosis_from_text(scene_type, evidence, risk_matches, symptom_text, llm_text)
            return diagnosis, f"{provider_used}+text_assist"
        except Exception:
            diagnosis = _heuristic_diagnosis(scene_type, evidence, risk_matches, symptom_text)
            return diagnosis, "heuristic_fallback"


def build_work_order_draft(
    scene_type: str,
    request_fault: str,
    symptom_text: str,
    diagnosis: DiagnosisResult,
    risk_level: str,
) -> WorkOrderDraft:
    return build_structured_work_order_draft(
        scene_type=scene_type,
        fault_code=request_fault,
        symptom_text=symptom_text,
        diagnosis=diagnosis,
        risk_level=risk_level,
        traceability=[],
    )


def refine_diagnosis_with_second_opinion(
    scene_type: str,
    evidence: list[EvidenceItem],
    risk_matches: list[str],
    symptom_text: str,
    diagnosis: DiagnosisResult,
    traceability: list[TraceabilityItem],
) -> DiagnosisResult:
    baseline = _heuristic_diagnosis(scene_type, evidence, risk_matches, symptom_text)
    supported = {
        "cause": [item.recommendation for item in traceability if item.category == "cause" and item.support_level != "weak"],
        "check": [item.recommendation for item in traceability if item.category == "check" and item.support_level != "weak"],
        "action": [item.recommendation for item in traceability if item.category == "action" and item.support_level != "weak"],
    }

    return DiagnosisResult(
        possible_causes=_dedupe(supported["cause"] + diagnosis.possible_causes + baseline.possible_causes)[:3],
        recommended_checks=_dedupe(supported["check"] + diagnosis.recommended_checks + baseline.recommended_checks)[:3],
        recommended_actions=_dedupe(supported["action"] + diagnosis.recommended_actions + baseline.recommended_actions)[:4],
    )
