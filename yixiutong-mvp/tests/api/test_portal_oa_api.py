from __future__ import annotations

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
    get_settings.cache_clear()
    settings = get_settings()
    build_index(settings.materials_root, settings.index_manifest_path)
    return settings


def _login(client: TestClient, username: str, password: str = "123456") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_auth_portal_and_knowledge_routes(monkeypatch, tmp_path):
    _use_fast_test_runtime(monkeypatch, tmp_path)
    client = TestClient(create_app())
    headers = _login(client, "admin")

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["role"] == "admin"

    overview_response = client.get("/api/v1/portal/overview", headers=headers)
    assert overview_response.status_code == 200, overview_response.text
    overview = overview_response.json()
    assert overview["summary"]["work_order_count"] >= 3
    assert "pending_execution_count" in overview["summary"]
    assert "rework_count" in overview["summary"]
    assert len(overview["work_orders"]) >= 1

    docs_response = client.get("/api/v1/knowledge/documents")
    assert docs_response.status_code == 200, docs_response.text
    documents = docs_response.json()
    assert len(documents) >= 1
    document_id = documents[0]["document_id"]

    detail_response = client.get(f"/api/v1/knowledge/documents/{document_id}")
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["content"]


def test_diagnosis_creates_work_order_and_portal_refresh(monkeypatch, tmp_path):
    _use_fast_test_runtime(monkeypatch, tmp_path)
    client = TestClient(create_app())
    headers = _login(client, "zhangwei")

    diagnosis_response = client.post(
        "/api/v1/diagnosis/start",
        headers=headers,
        json={
            "fault_code": "E-204",
            "symptom_text": "设备运行时振动异常，伴随温度偏高。",
            "device_type": "航空装配工位",
            "context_notes": "夜班连续运行 6 小时后告警升级，需要人工复核。",
            "scene_type": "fault_diagnosis",
        },
    )
    assert diagnosis_response.status_code == 200, diagnosis_response.text
    diagnosis = diagnosis_response.json()
    assert diagnosis["work_order_id"]
    assert diagnosis["provider_used"]

    work_orders_response = client.get("/api/v1/portal/work-orders", headers=headers)
    assert work_orders_response.status_code == 200, work_orders_response.text
    work_orders = work_orders_response.json()
    created = next((item for item in work_orders if item["work_order_id"] == diagnosis["work_order_id"]), None)
    assert created is not None
    assert created["scene_type"] == "fault_diagnosis"
    assert created["status_bucket"] == "pending_approval"
    assert created["symptom_text"] == "设备运行时振动异常，伴随温度偏高。"

    pending_only_response = client.get("/api/v1/portal/work-orders?status_bucket=pending_approval", headers=headers)
    assert pending_only_response.status_code == 200, pending_only_response.text
    assert any(item["work_order_id"] == diagnosis["work_order_id"] for item in pending_only_response.json())

    detail_response = client.get(f"/api/v1/portal/work-orders/{diagnosis['work_order_id']}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["diagnosis"]["recommended_actions"]
    assert detail["work_order_draft"]["steps"]

    supervisor_headers = _login(client, "chenhao")
    approvals_before = client.get("/api/v1/portal/approvals", headers=supervisor_headers)
    assert approvals_before.status_code == 200, approvals_before.text
    assert any(item["work_order_id"] == diagnosis["work_order_id"] for item in approvals_before.json())

    decision_response = client.post(
        f"/api/v1/portal/work-orders/{diagnosis['work_order_id']}/decision",
        headers=supervisor_headers,
        json={"approved": True, "comment": "批准进入执行。", "edited_actions": ["停机挂牌", "机械链路复核", "冷却回路检查"]},
    )
    assert decision_response.status_code == 200, decision_response.text
    assert decision_response.json()["status_bucket"] == "pending_execution"

    approvals_after = client.get("/api/v1/portal/approvals", headers=supervisor_headers)
    assert approvals_after.status_code == 200, approvals_after.text
    assert all(item["work_order_id"] != diagnosis["work_order_id"] for item in approvals_after.json())

    approval_history = client.get("/api/v1/portal/approvals?include_history=true", headers=supervisor_headers)
    assert approval_history.status_code == 200, approval_history.text
    assert any(item["work_order_id"] == diagnosis["work_order_id"] and item["status"] == "approved" for item in approval_history.json())


def test_notification_permissions_update_and_test(monkeypatch, tmp_path):
    _use_fast_test_runtime(monkeypatch, tmp_path)
    client = TestClient(create_app())

    maint_headers = _login(client, "zhangwei")
    forbidden_response = client.get("/api/v1/notifications/channels", headers=maint_headers)
    assert forbidden_response.status_code == 403, forbidden_response.text

    supervisor_headers = _login(client, "chenhao")
    channels_response = client.get("/api/v1/notifications/channels", headers=supervisor_headers)
    assert channels_response.status_code == 200, channels_response.text
    assert len(channels_response.json()) == 2

    update_response = client.put(
        "/api/v1/notifications/channels/wecom_bot",
        headers=supervisor_headers,
        json={
            "enabled": True,
            "webhook_url": "https://example.invalid/wecom-bot",
            "secret": "",
            "receiver_hint": "运维值班群",
        },
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["enabled"] is True

    monkeypatch.setattr("app.api.v1.notifications.send_notification", lambda *args, **kwargs: "企业微信机器人推送成功")

    test_response = client.post(
        "/api/v1/notifications/channels/wecom_bot/test",
        headers=supervisor_headers,
        json={"title": "测试通知", "content": "审批待办已同步到消息通道。"},
    )
    assert test_response.status_code == 200, test_response.text
    assert test_response.json()["success"] is True

    final_channels_response = client.get("/api/v1/notifications/channels", headers=supervisor_headers)
    assert final_channels_response.status_code == 200, final_channels_response.text
    wecom_channel = next(item for item in final_channels_response.json() if item["channel"] == "wecom_bot")
    assert wecom_channel["last_status"] == "成功"
