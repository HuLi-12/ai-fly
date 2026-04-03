from __future__ import annotations

from app.models.schemas import EvidenceItem


def requires_human_confirmation(risk_level: str, evidence: list[EvidenceItem]) -> bool:
    return risk_level != "low" or len(evidence) < 3

