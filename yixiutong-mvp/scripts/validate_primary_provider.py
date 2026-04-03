from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.core.storage import write_json


def mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:6]}...{secret[-4:]}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an OpenAI-compatible primary provider without persisting the raw key.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    output_path = Path(args.output)

    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "api_key_preview": mask_secret(args.api_key),
        "reachable": False,
        "valid": False,
        "status_code": None,
        "detail": "",
    }

    try:
        response = httpx.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {args.api_key}"},
            timeout=30.0,
        )
        result["status_code"] = response.status_code
        result["reachable"] = True
        if response.is_success:
            result["valid"] = True
            result["detail"] = "ok"
        else:
            result["detail"] = response.text[:500]
    except Exception as exc:  # pragma: no cover - network path
        result["detail"] = str(exc)

    write_json(output_path, result)
    print(f"Validation report written to {output_path}")
    print(f"reachable={result['reachable']} valid={result['valid']} status_code={result['status_code']}")


if __name__ == "__main__":
    main()
