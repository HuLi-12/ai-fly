from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.auth import router as auth_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.portal import router as portal_router
from app.api.v1.system import router as system_router
from app.api.v1.workflows import router as workflows_router
from app.core.config import get_settings
from app.core.storage import ensure_safe_free_space, get_directory_size_bytes, get_free_space_gb
from app.services.ingestion import build_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_safe_free_space(settings.project_root, settings.safe_operation_floor_gb)
    if not settings.index_manifest_path.exists():
        build_index(settings.materials_root, settings.index_manifest_path)
    log_line = (
        f"startup provider={settings.primary_llm_provider}:{settings.primary_llm_model} "
        f"fallback={settings.fallback_llm_provider}:{settings.fallback_llm_model} "
        f"local_model_enabled={settings.local_model_enabled} "
        f"local_model_present={settings.local_model_present} "
        f"free_gb={get_free_space_gb(settings.project_root)} "
        f"project_size_mb={round(get_directory_size_bytes(settings.project_root)/(1024**2), 2)} "
        f"cache_root={settings.cache_root}\n"
    )
    (settings.logs_dir / "startup.log").write_text(log_line, encoding="utf-8")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Yixiutong API", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(system_router, prefix="/api/v1")
    app.include_router(workflows_router, prefix="/api/v1")
    app.include_router(feedback_router, prefix="/api/v1")
    app.include_router(portal_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(notifications_router, prefix="/api/v1")
    return app


app = create_app()
