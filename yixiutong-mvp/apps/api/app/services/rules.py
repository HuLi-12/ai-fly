from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import TriggeredRule


def load_rules(rules_path: Path) -> dict:
    return json.loads(rules_path.read_text(encoding="utf-8"))


def evaluate_risk_details(
    scene_type: str,
    fault_code: str,
    symptom_text: str,
    context_notes: str,
    rules: dict,
) -> tuple[str, list[TriggeredRule]]:
    combined = f"{fault_code} {symptom_text} {context_notes}".lower()
    matches: list[TriggeredRule] = []
    risk_level = "low"

    for rule in rules.get("rules", []):
        if rule.get("scene_type", "fault_diagnosis") != scene_type:
            continue
        matched_keywords = [keyword for keyword in rule.get("keywords", []) if keyword.lower() in combined]
        if not matched_keywords:
            continue

        match = TriggeredRule(
            rule_id=rule.get("name", "unknown-rule"),
            risk_level=rule.get("risk_level", "low"),
            message=rule.get("message", ""),
            matched_keywords=matched_keywords,
        )
        matches.append(match)

        if match.risk_level == "high":
            risk_level = "high"
        elif risk_level == "low":
            risk_level = "medium"

    return risk_level, matches


def evaluate_risk(scene_type: str, fault_code: str, symptom_text: str, context_notes: str, rules: dict) -> tuple[str, list[str]]:
    risk_level, matches = evaluate_risk_details(scene_type, fault_code, symptom_text, context_notes, rules)
    return risk_level, [item.message for item in matches]
