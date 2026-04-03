from __future__ import annotations

import json


def parse_structured_response(content: str) -> dict:
    text = content.strip()
    if not text:
        raise ValueError("Structured response was empty.")

    candidates = [text]

    if text.startswith("```"):
        fence_lines = text.splitlines()
        if len(fence_lines) >= 3:
            candidates.append("\n".join(fence_lines[1:-1]).strip())

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        candidates.append(text[first_brace:last_brace + 1].strip())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("Unable to parse structured JSON response.")
