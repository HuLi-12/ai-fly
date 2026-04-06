from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.core.config import Settings, get_settings


_DEFAULT_CONFIG: dict[str, Any] = {
    "scene_bias": {
        "fault_diagnosis": 0.0,
        "process_deviation": -1.5,
        "quality_inspection": -1.0,
    },
    "provider_bias": {
        "heuristic_fallback": -12.0,
        "+text_assist": -4.0,
        "ollama": -1.0,
        "openai_compatible": 1.5,
    },
    "risk_penalty": {
        "low": 0.0,
        "medium": -1.5,
        "high": -4.0,
    },
    "evidence_thresholds": {
        "min_evidence": 3,
        "low_evidence_penalty": -6.0,
        "strong_trace_target": 0.65,
        "weak_trace_penalty": -5.0,
    },
}


@lru_cache(maxsize=1)
def _load_config_file(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except FileNotFoundError:
        return _DEFAULT_CONFIG
    except json.JSONDecodeError:
        return _DEFAULT_CONFIG

    merged = dict(_DEFAULT_CONFIG)
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def _provider_bias(provider_used: str, config: dict[str, Any]) -> float:
    lowered = provider_used.lower()
    provider_table = config["provider_bias"]
    if lowered == "heuristic_fallback":
        return float(provider_table.get("heuristic_fallback", -12.0))
    if "+text_assist" in lowered:
        return float(provider_table.get("+text_assist", -4.0))
    if "openai_compatible" in lowered:
        return float(provider_table.get("openai_compatible", 1.5))
    if "ollama" in lowered:
        return float(provider_table.get("ollama", -1.0))
    return 0.0


def apply_confidence_calibration(
    raw_score: float,
    scene_type: str,
    provider_used: str,
    risk_level: str,
    evidence_count: int,
    strong_trace_ratio: float,
    settings: Settings | None = None,
) -> tuple[float, dict[str, float], list[str]]:
    runtime_settings = settings or get_settings()
    config = _load_config_file(str(runtime_settings.materials_root / "rules" / "confidence_calibration.json"))
    evidence_thresholds = config["evidence_thresholds"]

    scene_bias = float(config["scene_bias"].get(scene_type, 0.0))
    provider_bias = _provider_bias(provider_used, config)
    risk_penalty = float(config["risk_penalty"].get(risk_level, -2.0))
    low_evidence_penalty = (
        float(evidence_thresholds.get("low_evidence_penalty", -6.0))
        if evidence_count < int(evidence_thresholds.get("min_evidence", 3))
        else 0.0
    )
    weak_trace_penalty = (
        float(evidence_thresholds.get("weak_trace_penalty", -5.0))
        if strong_trace_ratio < float(evidence_thresholds.get("strong_trace_target", 0.65))
        else 0.0
    )

    adjustment = scene_bias + provider_bias + risk_penalty + low_evidence_penalty + weak_trace_penalty
    calibrated = round(max(min(raw_score + adjustment, 100.0), 0.0), 2)

    notes: list[str] = []
    if low_evidence_penalty < 0:
        notes.append("Evidence count stayed below the calibration target.")
    if weak_trace_penalty < 0:
        notes.append("Traceability support stayed below the strong-support target.")
    if provider_used == "heuristic_fallback":
        notes.append("Fallback generation reduces calibrated confidence.")

    return calibrated, {
        "scene_bias": scene_bias,
        "provider_bias": provider_bias,
        "risk_penalty": risk_penalty,
        "low_evidence_penalty": low_evidence_penalty,
        "weak_trace_penalty": weak_trace_penalty,
        "calibration_adjustment": adjustment,
    }, notes

