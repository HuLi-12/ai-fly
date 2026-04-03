from __future__ import annotations

import json
from pathlib import Path


def load_rules(rules_path: Path) -> dict:
    return json.loads(rules_path.read_text(encoding="utf-8"))


def evaluate_risk(scene_type: str, fault_code: str, symptom_text: str, context_notes: str, rules: dict) -> tuple[str, list[str]]:
    matches: list[str] = []
    risk_level = "low"
    combined = f"{fault_code} {symptom_text} {context_notes}".lower()
    for rule in rules.get("rules", []):
        if rule.get("scene_type", "fault_diagnosis") != scene_type:
            continue
        if any(keyword.lower() in combined for keyword in rule.get("keywords", [])):
            matches.append(rule["message"])
            if rule["risk_level"] == "high":
                risk_level = "high"
            elif risk_level == "low":
                risk_level = "medium"
    return risk_level, matches
