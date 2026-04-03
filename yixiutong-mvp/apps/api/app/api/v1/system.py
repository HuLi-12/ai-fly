from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.storage import ensure_within_root, get_directory_size_bytes, get_free_space_gb
from app.models.schemas import ProviderCheck, SystemSelfCheck
from app.services.provider_runtime import check_provider_channels


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/self-check", response_model=SystemSelfCheck)
def self_check() -> SystemSelfCheck:
    settings = get_settings()
    for value in settings.as_path_map().values():
        ensure_within_root(Path(value), settings.project_root)
    size_mb = round(get_directory_size_bytes(settings.project_root) / (1024**2), 2)
    return SystemSelfCheck(
        current_free_space_gb=get_free_space_gb(settings.project_root),
        current_project_size_mb=size_mb,
        provider=settings.primary_llm_provider,
        fallback_provider=settings.fallback_llm_provider,
        primary_base_url=settings.primary_llm_base_url,
        fallback_base_url=settings.fallback_llm_base_url,
        cache_root=str(settings.cache_root),
        local_model_enabled=settings.local_model_enabled,
        local_model_present=settings.local_model_present,
        ollama_executable_path=settings.ollama_executable_path,
        ollama_executable_present=settings.ollama_executable_present,
        controlled_roots=settings.as_path_map(),
    )


@router.get("/provider-check", response_model=list[ProviderCheck])
def provider_check() -> list[ProviderCheck]:
    settings = get_settings()
    return check_provider_channels(settings)
