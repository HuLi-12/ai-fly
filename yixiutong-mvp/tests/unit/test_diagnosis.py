from app.agents import diagnosis as diagnosis_module
from app.core.config import Settings
from app.models.schemas import EvidenceItem


def test_diagnosis_from_text_parses_sectioned_output():
    result = diagnosis_module._diagnosis_from_text(
        scene_type="fault_diagnosis",
        evidence=[
            EvidenceItem(
                source_type="manual",
                title="E-204 troubleshooting",
                snippet="Bearing wear and cooling flow degradation are typical triggers.",
                score=0.92,
            )
        ],
        risk_matches=["high-vibration"],
        symptom_text="Equipment vibration is abnormal and temperature rises during operation.",
        llm_text=(
            "Possible causes:\n"
            "1. Bearing wear is increasing shaft vibration.\n"
            "2. Cooling flow degradation is pushing temperature upward.\n"
            "Recommended checks:\n"
            "1. Inspect the shaft coupling and bearing lubrication.\n"
            "2. Verify coolant flow and fan status.\n"
            "Recommended actions:\n"
            "1. Hold restart until the vibration source is isolated.\n"
            "2. Escalate to maintenance review before release.\n"
        ),
    )

    assert result.possible_causes[0] == "Bearing wear is increasing shaft vibration."
    assert result.recommended_checks[0] == "Inspect the shaft coupling and bearing lubrication."
    assert result.recommended_actions[0] == "Hold restart until the vibration source is isolated."


def test_generate_diagnosis_uses_text_assist_when_structured_generation_fails(monkeypatch):
    def fake_structured(*args, **kwargs):
        raise RuntimeError("structured parse failed")

    def fake_text(*args, **kwargs):
        return (
            "Possible causes:\n"
            "1. Tool wear introduced dimensional drift.\n"
            "Recommended checks:\n"
            "1. Review tooling calibration records.\n"
            "Recommended actions:\n"
            "1. Freeze the affected batch.\n",
            "ollama:fallback:yixiutong-qwen3b",
        )

    monkeypatch.setattr(diagnosis_module, "generate_structured_with_fallback", fake_structured)
    monkeypatch.setattr(diagnosis_module, "generate_text_with_fallback", fake_text)

    diagnosis, provider_used = diagnosis_module.generate_diagnosis(
        settings=Settings(local_model_enabled=True),
        scene_type="process_deviation",
        fault_code="PROC-118",
        symptom_text="Heat-treatment dwell time is below the qualified window.",
        context_notes="The last qualified batch used a longer dwell time.",
        evidence=[
            EvidenceItem(
                source_type="case",
                title="Process deviation note",
                snippet="Tool wear and process drift were both observed in previous cases.",
                score=0.88,
            )
        ],
        risk_matches=["hold-batch"],
    )

    assert provider_used == "ollama:fallback:yixiutong-qwen3b+text_assist"
    assert diagnosis.possible_causes[0] == "Tool wear introduced dimensional drift."
    assert diagnosis.recommended_checks[0] == "Review tooling calibration records."
    assert diagnosis.recommended_actions[0] == "Freeze the affected batch."
