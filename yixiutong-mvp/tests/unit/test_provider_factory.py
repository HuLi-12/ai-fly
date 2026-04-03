import pytest

from app.core.config import Settings
from app.providers.factory import get_provider


def test_primary_provider_switches_to_openai_compatible():
    settings = Settings(
        primary_llm_provider="openai_compatible",
        primary_llm_model="demo-model",
        primary_llm_base_url="https://example.com/v1"
    )
    provider = get_provider(settings, channel="primary")
    assert provider.provider_name == "openai_compatible"


def test_fallback_provider_switches_to_ollama():
    settings = Settings(
        fallback_llm_provider="ollama",
        fallback_llm_model="yixiutong-qwen3b",
        fallback_llm_base_url="http://127.0.0.1:11434",
        local_model_enabled=True
    )
    provider = get_provider(settings, channel="fallback")
    assert provider.provider_name == "ollama"


def test_provider_rejects_unknown_provider():
    settings = Settings(primary_llm_provider="unknown")
    with pytest.raises(RuntimeError):
        get_provider(settings, channel="primary")
