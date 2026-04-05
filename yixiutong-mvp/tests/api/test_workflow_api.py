from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app
from app.services.ingestion import build_index


def _use_fast_test_runtime(monkeypatch):
    monkeypatch.setenv("PRIMARY_LLM_BASE_URL", "")
    monkeypatch.setenv("PRIMARY_LLM_API_KEY", "")
    monkeypatch.setenv("FALLBACK_LLM_BASE_URL", "")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "")
    monkeypatch.setenv("LOCAL_MODEL_ENABLED", "false")
    get_settings.cache_clear()


def test_main_chain_returns_required_fields(monkeypatch):
    _use_fast_test_runtime(monkeypatch)
    settings = get_settings()
    build_index(settings.materials_root, settings.index_manifest_path)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/diagnosis/start",
        json={
            "fault_code": "E-204",
            "symptom_text": "Equipment vibration is abnormal and temperature rises during operation.",
            "device_type": "Aviation assembly station",
            "context_notes": "Night shift run for 6 hours before alarm escalation.",
            "scene_type": "fault_diagnosis",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["storage_mode"] == "workspace-locked"
    assert data["scene_type"] == "fault_diagnosis"
    assert data["route_confidence"] > 0
    assert data["route_reason"]
    assert "route_signals" in data
    assert len(data["evidence"]) >= 1
    assert "evidence_id" in data["evidence"][0]
    assert "retrieval_method" in data["evidence"][0]
    assert len(data["diagnosis"]["possible_causes"]) >= 1
    assert data["work_order_draft"]["summary"]
    assert "confidence" in data
    assert "traceability" in data
    assert "triggered_rules" in data
    assert "execution_trace" in data
    assert "validation_result" in data
    assert "approval_reasons" in data
    assert "requires_human_confirmation" in data


def test_process_scene_and_system_routes(monkeypatch):
    _use_fast_test_runtime(monkeypatch)
    settings = get_settings()
    build_index(settings.materials_root, settings.index_manifest_path)
    client = TestClient(create_app())

    process_response = client.post(
        "/api/v1/diagnosis/start",
        json={
            "fault_code": "PROC-118",
            "symptom_text": "Heat-treatment dwell time is below the qualified window and batch parameters drifted.",
            "device_type": "Composite curing equipment",
            "context_notes": "Process record shows dwell time below lower limit.",
            "scene_type": "process_deviation",
        },
    )
    assert process_response.status_code == 200, process_response.text
    assert process_response.json()["scene_type"] == "process_deviation"

    system_response = client.get("/api/v1/system/self-check")
    assert system_response.status_code == 200
    assert "fallback_provider" in system_response.json()
    assert "retrieval_embedding_provider" in system_response.json()
    assert "retrieval_vector_enabled" in system_response.json()
    assert "ollama_executable_present" in system_response.json()
    assert "primary_base_url" in system_response.json()

    provider_response = client.get("/api/v1/system/provider-check")
    assert provider_response.status_code == 200
    assert len(provider_response.json()) == 2


def test_confirm_and_feedback_routes(monkeypatch):
    _use_fast_test_runtime(monkeypatch)
    settings = get_settings()
    build_index(settings.materials_root, settings.index_manifest_path)
    client = TestClient(create_app())

    diagnosis_response = client.post(
        "/api/v1/diagnosis/start",
        json={
            "fault_code": "QA-305",
            "symptom_text": "Surface scratch and edge burr were found during final inspection.",
            "device_type": "Final inspection bench",
            "context_notes": "Suspect lot shares the same workstation and handling shift.",
            "scene_type": "quality_inspection",
        },
    )
    assert diagnosis_response.status_code == 200, diagnosis_response.text
    request_id = diagnosis_response.json()["request_id"]
    assert diagnosis_response.json()["validation_result"]["status"] in {"ready_to_submit", "needs_revision"}

    confirm_response = client.post(
        "/api/v1/diagnosis/confirm",
        json={
            "request_id": request_id,
            "approved": True,
            "edited_actions": ["Repeat inspection with calibrated gauge.", "Hold release until MRB review."],
            "operator_note": "Quality engineer approved the draft after adding a hold point.",
        },
    )
    assert confirm_response.status_code == 200, confirm_response.text
    assert confirm_response.json()["status"] == "confirmed"

    feedback_response = client.post(
        "/api/v1/feedback",
        json={
            "request_id": request_id,
            "feedback_type": "quality_board",
            "feedback_text": "The draft was usable after the hold-point edit.",
            "final_resolution": "Affected lot quarantined and routed to MRB.",
        },
    )
    assert feedback_response.status_code == 200, feedback_response.text
    assert feedback_response.json()["saved"] is True

    replay_response = client.post(
        "/api/v1/diagnosis/start",
        json={
            "fault_code": "QA-305",
            "symptom_text": "Surface scratch and edge burr were found during final inspection.",
            "device_type": "Final inspection bench",
            "context_notes": "Suspect lot shares the same workstation and handling shift.",
            "scene_type": "quality_inspection",
        },
    )
    assert replay_response.status_code == 200, replay_response.text
    assert any(item["source_type"] == "case_memory" for item in replay_response.json()["evidence"])
