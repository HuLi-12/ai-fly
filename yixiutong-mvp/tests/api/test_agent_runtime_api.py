from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app
from app.services.ingestion import build_index


def _use_fast_test_runtime(monkeypatch, tmp_path):
    monkeypatch.setenv("RUNTIME_ROOT", str(tmp_path / "runtime"))
    monkeypatch.setenv("PRIMARY_LLM_BASE_URL", "")
    monkeypatch.setenv("PRIMARY_LLM_API_KEY", "")
    monkeypatch.setenv("FALLBACK_LLM_BASE_URL", "")
    monkeypatch.setenv("FALLBACK_LLM_MODEL", "")
    monkeypatch.setenv("LOCAL_MODEL_ENABLED", "false")
    monkeypatch.setenv("IDEMPOTENCY_ENABLED", "true")
    monkeypatch.setenv("IDEMPOTENCY_TTL_HOURS", "24")
    get_settings.cache_clear()
    settings = get_settings()
    build_index(settings.materials_root, settings.index_manifest_path)
    return settings


def _login(client: TestClient, username: str, password: str = "123456") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _payload() -> dict:
    return {
        "fault_code": "E-204",
        "symptom_text": "设备运行时振动异常，并伴随温度偏高。",
        "device_type": "航空装配工位",
        "context_notes": "夜班连续运行 6 小时后报警升级，需要人工复核。",
        "scene_type": "fault_diagnosis",
    }


def test_diagnosis_replay_metrics_and_idempotency(monkeypatch, tmp_path):
    _use_fast_test_runtime(monkeypatch, tmp_path)
    client = TestClient(create_app())
    headers = _login(client, "zhangwei")

    first = client.post("/api/v1/diagnosis/start", headers=headers, json=_payload())
    assert first.status_code == 200, first.text
    first_payload = first.json()
    assert first_payload["run_id"]
    assert first_payload["request_id"]
    assert first_payload["work_order_id"]

    second = client.post("/api/v1/diagnosis/start", headers=headers, json=_payload())
    assert second.status_code == 200, second.text
    second_payload = second.json()

    assert second_payload["run_id"] != first_payload["run_id"]
    assert second_payload["request_id"] == first_payload["request_id"]
    assert second_payload["work_order_id"] == first_payload["work_order_id"]

    replay_by_run = client.get(f"/api/v1/diagnosis/runs/{first_payload['run_id']}")
    assert replay_by_run.status_code == 200, replay_by_run.text
    replay_run_payload = replay_by_run.json()
    assert replay_run_payload["status"] == "completed"
    assert replay_run_payload["request"]["fault_code"] == "E-204"
    assert len(replay_run_payload["snapshots"]) >= 2

    replay_by_request = client.get(f"/api/v1/diagnosis/replay/{first_payload['request_id']}")
    assert replay_by_request.status_code == 200, replay_by_request.text
    assert replay_by_request.json()["request_id"] == first_payload["request_id"]

    metrics = client.get("/api/v1/system/agent-metrics")
    assert metrics.status_code == 200, metrics.text
    metrics_payload = metrics.json()
    assert metrics_payload["total_runs"] >= 2
    assert metrics_payload["completed_runs"] >= 2
    assert metrics_payload["cached_hits"] >= 1
    assert any(item["node"] == "diagnose" for item in metrics_payload["node_summaries"])
