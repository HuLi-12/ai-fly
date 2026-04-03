import httpx

from app.core.config import Settings
from app.services.provider_runtime import check_provider_channel


def test_openai_provider_reports_auth_failure_as_reachable(monkeypatch):
    settings = Settings(
        primary_llm_provider="openai_compatible",
        primary_llm_model="demo-model",
        primary_llm_base_url="https://example.com/v1",
        primary_llm_api_key="demo-key",
    )

    def fake_get(*args, **kwargs):
        request = httpx.Request("GET", "https://example.com/v1/models")
        return httpx.Response(status_code=401, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    result = check_provider_channel(settings, "primary")
    assert result.configured is True
    assert result.reachable is True
    assert result.detail == "auth_failed:401"


def test_ollama_provider_reports_connection_error(monkeypatch):
    settings = Settings(
        fallback_llm_provider="ollama",
        fallback_llm_model="yixiutong-qwen3b",
        fallback_llm_base_url="http://127.0.0.1:11434",
        local_model_enabled=True,
    )

    def fake_get(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "get", fake_get)
    result = check_provider_channel(settings, "fallback")
    assert result.configured is True
    assert result.reachable is False
    assert "connection refused" in result.detail
