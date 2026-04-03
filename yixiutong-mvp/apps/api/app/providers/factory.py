from __future__ import annotations

from app.core.config import Settings
from app.providers.base import LLMProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai_compatible import OpenAICompatibleProvider


def get_provider(settings: Settings, channel: str = "primary") -> LLMProvider:
    config = settings.provider_config(channel)
    provider = config["provider"].strip().lower()
    if provider == "openai_compatible":
        return OpenAICompatibleProvider(settings, channel=channel)
    if provider == "ollama":
        return OllamaProvider(settings, channel=channel)
    raise RuntimeError(f"Unsupported LLM provider: {config['provider']}")
