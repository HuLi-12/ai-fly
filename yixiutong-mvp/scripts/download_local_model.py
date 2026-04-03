from __future__ import annotations

from datetime import datetime, timezone

from huggingface_hub import snapshot_download

from app.core.config import get_settings
from app.core.storage import ensure_directory_budget, ensure_safe_free_space, get_directory_size_bytes, write_json
from app.services.provider_runtime import discover_local_model_file


def main() -> None:
    settings = get_settings()
    ensure_safe_free_space(settings.project_root, settings.safe_operation_floor_gb)
    ensure_directory_budget(settings.local_model_dir, settings.local_model_download_budget_gb, "local model directory")

    local_dir = settings.local_model_repo_dir
    local_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=settings.local_fallback_model_id,
        local_dir=str(local_dir),
        allow_patterns=settings.local_model_allow_patterns_list,
        token=settings.hf_token or None,
    )

    ensure_safe_free_space(settings.project_root, settings.free_space_floor_gb)
    ensure_directory_budget(settings.local_model_dir, settings.local_model_download_budget_gb, "local model directory")

    gguf_file = discover_local_model_file(local_dir)
    manifest = {
        "model_id": settings.local_fallback_model_id,
        "local_dir": str(local_dir),
        "allow_patterns": settings.local_model_allow_patterns_list,
        "gguf_file": str(gguf_file) if gguf_file else "",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "size_mb": round(get_directory_size_bytes(local_dir) / (1024**2), 2),
    }
    write_json(settings.local_model_manifest_path, manifest)
    print(f"Downloaded local fallback model to {local_dir}")
    print(f"Manifest written to {settings.local_model_manifest_path}")


if __name__ == "__main__":
    main()
