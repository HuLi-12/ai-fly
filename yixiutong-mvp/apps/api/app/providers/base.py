from __future__ import annotations

from typing import Any, Protocol


class LLMProvider(Protocol):
    provider_name: str

    def generate_text(self, messages: list[dict[str, str]], system_prompt: str, options: dict[str, Any] | None = None) -> str:
        ...

    def generate_structured(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        system_prompt: str,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...

