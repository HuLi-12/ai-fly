from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import EvidenceItem


@dataclass(frozen=True)
class PromptBundle:
    system_prompt: str
    messages: list[dict[str, str]]


_SCENE_PROFILES: dict[str, dict[str, str]] = {
    "fault_diagnosis": {
        "role": "aviation maintenance diagnostic specialist",
        "goal": "identify the most likely mechanical, thermal, and sensing causes",
        "constraints": "prioritize shutdown safety, inspection order, and evidence-backed actions",
        "example": (
            "Example:\n"
            "Possible causes:\n"
            "- Bearing wear or coupling misalignment amplifies vibration.\n"
            "- Cooling obstruction causes temperature rise and secondary vibration.\n"
            "Recommended checks:\n"
            "- Verify bearing clearance and coupling fasteners.\n"
            "- Inspect cooling airflow and fan status.\n"
            "Recommended actions:\n"
            "- Lock out the equipment before manual inspection.\n"
            "- Escalate before restart if high-risk conditions remain."
        ),
    },
    "process_deviation": {
        "role": "aviation process deviation analyst",
        "goal": "determine which process controls drifted and what containment is required",
        "constraints": "freeze the affected batch, reference process control windows, and avoid unverified release",
        "example": (
            "Example:\n"
            "Possible causes:\n"
            "- Heat-treatment dwell time drifted below the control window.\n"
            "- Tooling or parameter updates were not synchronized to the process card.\n"
            "Recommended checks:\n"
            "- Compare current parameters against the last qualified batch.\n"
            "- Verify tooling calibration and shift handoff records.\n"
            "Recommended actions:\n"
            "- Freeze the affected batch.\n"
            "- Prepare a temporary process disposition for review."
        ),
    },
    "quality_inspection": {
        "role": "aviation quality disposition specialist",
        "goal": "link the defect pattern to likely upstream causes and required containment",
        "constraints": "stop release, preserve traceability, and prepare MRB-ready evidence",
        "example": (
            "Example:\n"
            "Possible causes:\n"
            "- Handling damage introduced repeatable surface scratches.\n"
            "- Burr removal drifted and created batch-level defects.\n"
            "Recommended checks:\n"
            "- Reinspect the same batch with calibrated tools.\n"
            "- Trace the affected workstation and inspection records.\n"
            "Recommended actions:\n"
            "- Quarantine the batch immediately.\n"
            "- Package defect evidence for quality review."
        ),
    },
}


def _format_evidence(evidence: list[EvidenceItem]) -> str:
    if not evidence:
        return "- no evidence retrieved"
    lines: list[str] = []
    for item in evidence:
        lines.append(
            f"- [{item.evidence_id or item.title}] source={item.source_type}; score={item.score:.2f}; "
            f"title={item.title}; snippet={item.snippet}"
        )
    return "\n".join(lines)


def _format_rules(risk_matches: list[str]) -> str:
    if not risk_matches:
        return "- none"
    return "\n".join(f"- {item}" for item in risk_matches)


def build_diagnosis_prompt(
    scene_type: str,
    fault_code: str,
    symptom_text: str,
    context_notes: str,
    evidence: list[EvidenceItem],
    risk_matches: list[str],
) -> PromptBundle:
    profile = _SCENE_PROFILES.get(scene_type, _SCENE_PROFILES["fault_diagnosis"])
    system_prompt = (
        f"You are an {profile['role']}.\n"
        f"Goal: {profile['goal']}.\n"
        f"Constraints: {profile['constraints']}.\n"
        "Answer strictly from the supplied evidence and rules.\n"
        "Do not invent manuals, procedures, or measurements that are not present.\n"
        "Prefer concise, action-oriented recommendations with clear ordering.\n"
        "When evidence is weak, keep the diagnosis conservative and route to human review.\n"
        f"{profile['example']}"
    )
    user_prompt = (
        f"Scene: {scene_type}\n"
        f"Fault code: {fault_code}\n"
        f"Symptoms: {symptom_text}\n"
        f"Context notes: {context_notes or 'none'}\n"
        "Evidence:\n"
        f"{_format_evidence(evidence)}\n"
        "Triggered rules:\n"
        f"{_format_rules(risk_matches)}"
    )
    return PromptBundle(
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

