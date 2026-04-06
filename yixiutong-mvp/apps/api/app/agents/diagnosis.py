from __future__ import annotations

import re

from app.core.config import Settings
from app.models.schemas import DiagnosisResult, EvidenceItem, TraceabilityItem, WorkOrderDraft
from app.services.prompting import build_diagnosis_prompt
from app.services.provider_runtime import generate_structured_with_fallback, generate_text_with_fallback
from app.services.work_orders import build_work_order_draft as build_structured_work_order_draft


DIAGNOSIS_SCHEMA = {
    "possible_causes": ["string"],
    "recommended_checks": ["string"],
    "recommended_actions": ["string"],
}

SECTION_ALIASES = {
    "possible_causes": ("Possible causes", "Likely causes", "Root causes", "可能原因"),
    "recommended_checks": ("Recommended checks", "Checks", "Inspection checks", "建议检查"),
    "recommended_actions": ("Recommended actions", "Actions", "Immediate actions", "建议处置"),
}


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _fault_diagnosis(evidence: list[EvidenceItem], risk_matches: list[str], symptom_text: str) -> DiagnosisResult:
    combined = f"{' '.join(item.snippet for item in evidence)} {symptom_text}".lower()
    causes: list[str] = []
    checks: list[str] = []

    if _contains_any(combined, ("vibration", "bearing", "shaft", "coupling", "振动", "轴承", "联轴器")):
        causes.append("Transmission-chain wear, loose bearings, or coupling misalignment may amplify vibration.")
        checks.append("Verify coupling alignment, fasteners, bearing clearance, and lubrication condition.")

    if _contains_any(combined, ("temperature", "cooling", "fan", "温度", "冷却", "风机")):
        causes.append("Cooling-path degradation or airflow blockage may drive temperature rise and secondary vibration.")
        checks.append("Inspect fan status, airflow path, cooling loop flow, and duct cleanliness.")

    if _contains_any(combined, ("sensor", "alarm", "probe", "传感器", "报警")):
        causes.append("Sensor drift or alarm-chain anomalies may amplify the observed warning pattern.")
        checks.append("Cross-check sensor readings against handheld instruments and calibration records.")

    if not causes:
        causes = ["Start with the mechanical chain, thermal management path, and sensing chain in sequence."]
        checks = ["Lock out the equipment, complete a visual inspection, and verify baseline parameters first."]

    actions = [
        "Preserve the current alarm snapshot and lock out the equipment before intrusive checks.",
        "Execute the inspection path in mechanical, cooling, and sensing order.",
        "Escalate to supervised review before restart if high-risk conditions remain unresolved.",
    ]
    if risk_matches:
        actions.append("Do not release the equipment without manual approval after a high-risk rule hit.")

    return DiagnosisResult(
        possible_causes=causes[:3],
        recommended_checks=checks[:3],
        recommended_actions=actions[:4],
    )


def _process_deviation(risk_matches: list[str], symptom_text: str) -> DiagnosisResult:
    causes = [
        "A critical process parameter likely drifted outside the qualified window.",
        "Tooling or fixture wear may have introduced a repeatable deviation pattern.",
        "A process-card update or changeover may not have propagated to the station.",
    ]
    if "heat" in symptom_text.lower() or "热处理" in symptom_text or "固化" in symptom_text:
        causes[0] = "A heat-treatment or curing parameter likely drifted outside the qualified window."

    return DiagnosisResult(
        possible_causes=causes,
        recommended_checks=[
            "Compare the current parameter set against the released process card and the latest qualified batch.",
            "Verify tooling calibration, fixture wear, and shift handoff records.",
            "Confirm material batch, environment conditions, and changeover records.",
        ],
        recommended_actions=[
            "Freeze the affected batch and mark it for process review.",
            "Prepare a temporary process disposition with corrected parameters and validation points.",
            "Do not resume normal production until process approval is complete.",
            *(
                ["Escalate to joint process-quality review because a risk rule was triggered."]
                if risk_matches
                else []
            ),
        ][:4],
    )


def _quality_inspection(risk_matches: list[str], symptom_text: str) -> DiagnosisResult:
    causes = [
        "The part shows a repeatable dimensional or surface defect pattern.",
        "Inspection drift or measurement-tool issues may be contributing to misclassification.",
        "An unstable upstream process may have introduced a batch-level defect mode.",
    ]
    if "scratch" in symptom_text.lower() or "划伤" in symptom_text:
        causes[0] = "Handling damage or contamination is the leading surface-defect hypothesis."

    return DiagnosisResult(
        possible_causes=causes,
        recommended_checks=[
            "Repeat the inspection with calibrated tooling and a second inspector if available.",
            "Trace the affected batch, workstation, operator, and inspection records.",
            "Check whether the defect falls within an existing rework, concession, or MRB standard.",
        ],
        recommended_actions=[
            "Quarantine the suspected batch and stop downstream release.",
            "Package defect evidence, dimensions, and photos into an inspection report draft.",
            "Submit the case to MRB or quality engineering for disposition.",
            *(
                ["Do not release the batch until quality approval is complete."]
                if risk_matches
                else []
            ),
        ][:4],
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
    if cleaned[-1] not in ".!?;。；":
        cleaned += "."
    return cleaned


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?;。；])\s*|\n+", text)
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
        if any(keyword in lower for keyword in ("cause", "due to", "wear", "drift", "damage", "instability", "原因", "磨损", "漂移")):
            buckets["possible_causes"].append(sentence)
        if any(keyword in lower for keyword in ("check", "inspect", "verify", "measure", "trace", "review", "检查", "复核", "确认")):
            buckets["recommended_checks"].append(sentence)
        if any(keyword in lower for keyword in ("hold", "stop", "escalate", "repair", "replace", "quarantine", "document", "停", "隔离", "升级", "处置")):
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
    prompt_bundle = build_diagnosis_prompt(
        scene_type=scene_type,
        fault_code=fault_code,
        symptom_text=symptom_text,
        context_notes=context_notes,
        evidence=evidence,
        risk_matches=risk_matches,
    )
    try:
        structured, provider_used = generate_structured_with_fallback(
            settings=settings,
            messages=prompt_bundle.messages,
            schema=DIAGNOSIS_SCHEMA,
            system_prompt=prompt_bundle.system_prompt,
            options={"temperature": 0.1},
        )
        diagnosis = DiagnosisResult(**structured)
        return diagnosis, provider_used
    except Exception:
        text_prompt = (
            f"{prompt_bundle.system_prompt}\n"
            "Return plain text with these exact headings:\n"
            "Possible causes:\n"
            "Recommended checks:\n"
            "Recommended actions:"
        )
        try:
            llm_text, provider_used = generate_text_with_fallback(
                settings=settings,
                messages=prompt_bundle.messages,
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
