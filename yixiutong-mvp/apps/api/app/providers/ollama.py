from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import Settings
from app.providers.json_utils import parse_structured_response


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, settings: Settings, channel: str = "fallback"):
        self.settings = settings
        self.channel = channel
        self.config = self.settings.provider_config(channel)

    def generate_text(self, messages: list[dict[str, str]], system_prompt: str, options: dict[str, Any] | None = None) -> str:
        if not self.config["base_url"]:
            raise RuntimeError(f"{self.channel} provider requires a base URL.")
        resolved_options = {
            "temperature": (options or {}).get("temperature", 0.1),
        }
        for key in ("num_predict", "num_ctx", "repeat_penalty", "top_k", "top_p"):
            if key in (options or {}):
                resolved_options[key] = options[key]
        response = httpx.post(
            f"{self.config['base_url'].rstrip('/')}/api/chat",
            json={
                "model": self.config["model"],
                "stream": False,
                "messages": [{"role": "system", "content": system_prompt}, *messages],
                "options": resolved_options,
            },
            timeout=float(self.config["timeout_seconds"]),
            trust_env=False,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def generate_structured(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        system_prompt: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt = (
            f"{system_prompt}\n"
            "Return JSON only. Do not add markdown, explanation, or code fences.\n"
            "Return strict JSON matching this schema shape:\n"
            f"{json.dumps(schema, ensure_ascii=False)}"
        )
        content = self.generate_text(messages=messages, system_prompt=prompt, options=options)
        return parse_structured_response(content)
