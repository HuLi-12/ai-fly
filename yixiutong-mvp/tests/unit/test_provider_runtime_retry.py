import httpx

from app.core.config import Settings
from app.services import provider_runtime


class _RetryingProvider:
    def __init__(self) -> None:
        self.attempts = 0

    def generate_text(self, messages, system_prompt, options=None):
        self.attempts += 1
        if self.attempts == 1:
            raise httpx.ReadTimeout("temporary timeout")
        return "ok"

    def generate_structured(self, messages, schema, system_prompt, options=None):
        raise NotImplementedError


class _OllamaStructuredFailureProvider:
    def __init__(self) -> None:
        self.attempts = 0

    def generate_text(self, messages, system_prompt, options=None):
        raise NotImplementedError

    def generate_structured(self, messages, schema, system_prompt, options=None):
        self.attempts += 1
        raise ValueError("Unable to parse structured JSON response.")


def test_generate_text_retries_transient_provider_errors(monkeypatch):
    settings = Settings(
        primary_llm_provider="openai_compatible",
        primary_llm_model="demo-model",
        primary_llm_base_url="https://example.com/v1",
        primary_llm_api_key="demo-key",
        fallback_llm_base_url="",
        fallback_llm_model="",
        provider_max_retries=2,
        provider_retry_backoff_ms=0,
    )
    provider = _RetryingProvider()

    monkeypatch.setattr(provider_runtime, "get_provider", lambda settings, channel="primary": provider)

    text, provider_used = provider_runtime.generate_text_with_fallback(
        settings=settings,
        messages=[{"role": "user", "content": "hello"}],
        system_prompt="demo",
    )

    assert text == "ok"
    assert provider.attempts == 2
    assert provider_used == "openai_compatible:primary:demo-model"


def test_generate_structured_does_not_retry_ollama_parse_failures(monkeypatch):
    settings = Settings(
        primary_llm_provider="ollama",
        primary_llm_model="demo-ollama",
        primary_llm_base_url="http://127.0.0.1:11434",
        primary_llm_api_key="",
        fallback_llm_base_url="",
        fallback_llm_model="",
        provider_max_retries=2,
        provider_retry_backoff_ms=0,
    )
    provider = _OllamaStructuredFailureProvider()

    monkeypatch.setattr(provider_runtime, "get_provider", lambda settings, channel="primary": provider)

    try:
        provider_runtime.generate_structured_with_fallback(
            settings=settings,
            messages=[{"role": "user", "content": "hello"}],
            schema={"result": ["string"]},
            system_prompt="demo",
        )
    except RuntimeError as exc:
        assert "Unable to parse structured JSON response." in str(exc)
    else:
        raise AssertionError("Expected runtime error for non-retryable structured parse failure.")

    assert provider.attempts == 1
