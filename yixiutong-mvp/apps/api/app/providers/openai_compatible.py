from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import Settings
from app.providers.json_utils import parse_structured_response


class OpenAICompatibleProvider:
    provider_name = "openai_compatible"

    def __init__(self, settings: Settings, channel: str = "primary"):
        self.settings = settings
        self.channel = channel
        self.config = self.settings.provider_config(channel)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config["api_key"]:
            headers["Authorization"] = f"Bearer {self.config['api_key']}"
        return headers

    def generate_text(self, messages: list[dict[str, str]], system_prompt: str, options: dict[str, Any] | None = None) -> str:
        if not self.config["base_url"]:
            raise RuntimeError(f"{self.channel} provider requires a base URL.")
        payload = {
            "model": self.config["model"],
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "temperature": (options or {}).get("temperature", 0.1),
        }
        response = httpx.post(
            f"{self.config['base_url'].rstrip('/')}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=float(self.config["timeout_seconds"]),
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

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
