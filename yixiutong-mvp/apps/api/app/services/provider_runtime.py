from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, TypeVar

import httpx

from app.core.config import Settings
from app.models.schemas import ProviderCheck
from app.providers.factory import get_provider
from app.services.agent_observability import log_agent_event


T = TypeVar("T")


def _is_channel_configured(settings: Settings, channel: str) -> bool:
    config = settings.provider_config(channel)
    provider = config["provider"].strip().lower()
    if provider == "openai_compatible":
        return bool(config["base_url"] and config["model"] and config["api_key"])
    if provider == "ollama":
        if channel == "fallback" and not settings.local_model_enabled:
            return False
        return bool(config["base_url"] and config["model"])
    return False


def _provider_label(settings: Settings, channel: str) -> str:
    config = settings.provider_config(channel)
    return f"{config['provider']}:{channel}:{config['model']}"


def _openai_headers(api_key: str) -> dict[str, str]:
    if not api_key:
        return {}
    return {"Authorization": f"Bearer {api_key}"}


def _is_retryable_exception(exc: Exception, operation: str = "", provider_label: str = "") -> bool:
    retryable_types = (
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.ReadError,
        httpx.WriteError,
        httpx.NetworkError,
        httpx.RemoteProtocolError,
    )
    if isinstance(exc, retryable_types):
        return True
    if isinstance(exc, ValueError):
        if operation == "generate_structured" and provider_label.startswith("ollama:"):
            return False
        return True
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        return exc.response.status_code in {408, 409, 425, 429, 500, 502, 503, 504}
    return False


def _invoke_with_retries(
    settings: Settings,
    channel: str,
    operation: str,
    callback: Callable[[], T],
) -> tuple[T, str]:
    label = _provider_label(settings, channel)
    max_attempts = max(int(settings.provider_max_retries), 0) + 1

    for attempt in range(1, max_attempts + 1):
        started = time.perf_counter()
        log_agent_event(
            "provider_attempt_started",
            {"provider": label, "operation": operation, "attempt": attempt, "max_attempts": max_attempts},
        )
        try:
            result = callback()
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            log_agent_event(
                "provider_attempt_succeeded",
                {
                    "provider": label,
                    "operation": operation,
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                },
            )
            return result, label
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            retryable = _is_retryable_exception(exc, operation=operation, provider_label=label)
            log_agent_event(
                "provider_attempt_failed",
                {
                    "provider": label,
                    "operation": operation,
                    "attempt": attempt,
                    "duration_ms": duration_ms,
                    "retryable": retryable,
                    "error": str(exc),
                },
            )
            if attempt >= max_attempts or not retryable:
                raise
            backoff = (settings.provider_retry_backoff_ms * attempt) / 1000.0
            time.sleep(backoff)

    raise RuntimeError(f"Provider retry loop exited unexpectedly for {label}.")


def check_provider_channel(settings: Settings, channel: str) -> ProviderCheck:
    config = settings.provider_config(channel)
    provider = config["provider"].strip().lower()
    configured = _is_channel_configured(settings, channel)
    if not configured:
        detail = "not configured"
        if channel == "fallback" and provider == "ollama" and not settings.local_model_enabled:
            detail = "local fallback disabled"
        return ProviderCheck(channel=channel, provider=provider, configured=False, reachable=False, detail=detail)

    try:
        if provider == "openai_compatible":
            response = httpx.get(
                f"{config['base_url'].rstrip('/')}/models",
                headers=_openai_headers(config["api_key"]),
                timeout=float(config["timeout_seconds"]),
            )
        elif provider == "ollama":
            response = httpx.get(
                f"{config['base_url'].rstrip('/')}/api/tags",
                timeout=float(config["timeout_seconds"]),
            )
        else:
            return ProviderCheck(channel=channel, provider=provider, configured=True, reachable=False, detail="unsupported provider")
        if provider == "openai_compatible" and response.status_code in {401, 403}:
            return ProviderCheck(
                channel=channel,
                provider=provider,
                configured=True,
                reachable=True,
                detail=f"auth_failed:{response.status_code}",
            )
        response.raise_for_status()
        detail = "ok"
        if channel == "fallback":
            detail = f"ok; local_model_present={settings.local_model_present}"
        return ProviderCheck(channel=channel, provider=provider, configured=True, reachable=True, detail=detail)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        return ProviderCheck(
            channel=channel,
            provider=provider,
            configured=True,
            reachable=exc.response is not None,
            detail=f"http_status:{status_code}",
        )
    except Exception as exc:
        return ProviderCheck(channel=channel, provider=provider, configured=True, reachable=False, detail=str(exc))


def check_provider_channels(settings: Settings) -> list[ProviderCheck]:
    return [check_provider_channel(settings, "primary"), check_provider_channel(settings, "fallback")]


def generate_structured_with_fallback(
    settings: Settings,
    messages: list[dict[str, str]],
    schema: dict[str, Any],
    system_prompt: str,
    options: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    errors: list[str] = []
    for channel in ("primary", "fallback"):
        config = settings.provider_config(channel)
        provider_name = config["provider"].strip().lower()
        if channel == "fallback" and provider_name == "ollama" and not settings.local_model_enabled:
            errors.append("fallback disabled")
            continue
        if not _is_channel_configured(settings, channel):
            errors.append(f"{channel} not configured")
            continue

        provider = get_provider(settings, channel=channel)
        try:
            return _invoke_with_retries(
                settings=settings,
                channel=channel,
                operation="generate_structured",
                callback=lambda: provider.generate_structured(messages, schema, system_prompt, options),
            )
        except Exception as exc:
            errors.append(f"{_provider_label(settings, channel)} -> {exc}")
            continue
    raise RuntimeError("; ".join(errors) if errors else "No provider configured")


def generate_text_with_fallback(
    settings: Settings,
    messages: list[dict[str, str]],
    system_prompt: str,
    options: dict[str, Any] | None = None,
) -> tuple[str, str]:
    errors: list[str] = []
    for channel in ("primary", "fallback"):
        config = settings.provider_config(channel)
        provider_name = config["provider"].strip().lower()
        if channel == "fallback" and provider_name == "ollama" and not settings.local_model_enabled:
            errors.append("fallback disabled")
            continue
        if not _is_channel_configured(settings, channel):
            errors.append(f"{channel} not configured")
            continue

        provider = get_provider(settings, channel=channel)
        try:
            return _invoke_with_retries(
                settings=settings,
                channel=channel,
                operation="generate_text",
                callback=lambda: provider.generate_text(messages, system_prompt, options),
            )
        except Exception as exc:
            errors.append(f"{_provider_label(settings, channel)} -> {exc}")
            continue
    raise RuntimeError("; ".join(errors) if errors else "No provider configured")


def discover_local_model_file(model_root: Path) -> Path | None:
    if not model_root.exists():
        return None
    candidates = sorted(path for path in model_root.rglob("*.gguf") if path.is_file())
    return candidates[0] if candidates else None
