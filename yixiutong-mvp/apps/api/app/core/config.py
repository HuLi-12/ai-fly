from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


WORKSPACE_ROOT = Path(__file__).resolve().parents[5]
APP_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(APP_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_root: Path = Field(default=WORKSPACE_ROOT)
    app_root: Path = Field(default=APP_ROOT)
    materials_root: Path = Field(default=WORKSPACE_ROOT / "materials")
    models_root: Path = Field(default=WORKSPACE_ROOT / "models")
    runtime_root: Path = Field(default=WORKSPACE_ROOT / "runtime")
    cache_root: Path = Field(default=WORKSPACE_ROOT / "runtime" / "cache")
    free_space_floor_gb: int = Field(default=10)
    safe_operation_floor_gb: int = Field(default=12)
    llm_timeout_seconds: int = Field(default=180)
    workflow_timeout_seconds: int = Field(default=75)
    provider_max_retries: int = Field(default=2)
    provider_retry_backoff_ms: int = Field(default=250)
    idempotency_enabled: bool = Field(default=True)
    idempotency_ttl_hours: int = Field(default=24)
    retrieval_vector_enabled: bool = Field(default=True)
    retrieval_embedding_provider: str = Field(default="hashing")
    retrieval_embedding_model: str = Field(default="")
    retrieval_embedding_base_url: str = Field(default="")
    retrieval_embedding_api_key: str = Field(default="")
    retrieval_embedding_timeout_seconds: int = Field(default=60)
    retrieval_enable_model_rerank: bool = Field(default=True)
    retrieval_rerank_candidate_count: int = Field(default=6)
    primary_llm_provider: str = Field(default="openai_compatible")
    primary_llm_model: str = Field(default="qwen2.5-7b-instruct")
    primary_llm_base_url: str = Field(default="")
    primary_llm_api_key: str = Field(default="")
    fallback_llm_provider: str = Field(default="ollama")
    fallback_llm_model: str = Field(default="yixiutong-qwen3b")
    fallback_llm_base_url: str = Field(default="http://127.0.0.1:11434")
    fallback_llm_api_key: str = Field(default="")
    ollama_executable_path: str = Field(default="")
    local_model_enabled: bool = Field(default=False)
    local_model_name: str = Field(default="qwen2.5-3b-instruct")
    local_fallback_model_id: str = Field(default="Qwen/Qwen2.5-3B-Instruct-GGUF")
    local_fallback_allow_patterns: str = Field(default="*Q4_K_M.gguf,README.md")
    local_model_download_budget_gb: int = Field(default=3)
    hf_token: str = Field(default="")

    @property
    def pip_cache_dir(self) -> Path:
        return self.cache_root / "pip"

    @property
    def npm_cache_dir(self) -> Path:
        return self.cache_root / "npm"

    @property
    def hf_cache_dir(self) -> Path:
        return self.cache_root / "hf"

    @property
    def transformers_cache_dir(self) -> Path:
        return self.cache_root / "transformers"

    @property
    def langgraph_dir(self) -> Path:
        return self.runtime_root / "langgraph"

    @property
    def index_dir(self) -> Path:
        return self.runtime_root / "index"

    @property
    def logs_dir(self) -> Path:
        return self.runtime_root / "logs"

    @property
    def db_dir(self) -> Path:
        return self.runtime_root / "db"

    @property
    def local_model_dir(self) -> Path:
        return self.models_root / "local-llm"

    @property
    def ollama_model_dir(self) -> Path:
        return self.models_root / "ollama"

    @property
    def workflow_snapshot_dir(self) -> Path:
        return self.langgraph_dir / "snapshots"

    @property
    def index_manifest_path(self) -> Path:
        return self.index_dir / "index.json"

    @property
    def feedback_db_path(self) -> Path:
        return self.db_dir / "feedback.sqlite3"

    @property
    def portal_db_path(self) -> Path:
        return self.db_dir / "portal.sqlite3"

    @property
    def agent_runtime_db_path(self) -> Path:
        return self.db_dir / "agent_runtime.sqlite3"

    @property
    def local_model_manifest_path(self) -> Path:
        return self.local_model_dir / "download_manifest.json"

    @property
    def local_model_repo_dir(self) -> Path:
        return self.local_model_dir / "Qwen2.5-3B-Instruct-GGUF"

    @property
    def local_model_allow_patterns_list(self) -> list[str]:
        return [item.strip() for item in self.local_fallback_allow_patterns.split(",") if item.strip()]

    @property
    def local_model_present(self) -> bool:
        if self.local_model_manifest_path.exists():
            return True
        if not self.local_model_repo_dir.exists():
            return False
        return any(
            path.is_file() and path.suffix.lower() in {".gguf", ".bin", ".json"}
            for path in self.local_model_repo_dir.rglob("*")
        )

    @property
    def ollama_host(self) -> str:
        base_url = self.fallback_llm_base_url.strip()
        if not base_url:
            return "127.0.0.1:11434"
        if "://" in base_url:
            return base_url.split("://", 1)[1].rstrip("/")
        return base_url.rstrip("/")

    @property
    def ollama_executable_present(self) -> bool:
        if not self.ollama_executable_path.strip():
            return False
        return Path(self.ollama_executable_path).exists()

    def ensure_directories(self) -> None:
        for path in [
            self.project_root,
            self.materials_root,
            self.models_root,
            self.runtime_root,
            self.cache_root,
            self.pip_cache_dir,
            self.npm_cache_dir,
            self.hf_cache_dir,
            self.transformers_cache_dir,
            self.langgraph_dir,
            self.workflow_snapshot_dir,
            self.index_dir,
            self.logs_dir,
            self.db_dir,
            self.local_model_dir,
            self.ollama_model_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def as_path_map(self) -> dict[str, str]:
        return {
            "PROJECT_ROOT": str(self.project_root),
            "MATERIALS_ROOT": str(self.materials_root),
            "MODELS_ROOT": str(self.models_root),
            "RUNTIME_ROOT": str(self.runtime_root),
            "CACHE_ROOT": str(self.cache_root),
            "PIP_CACHE_DIR": str(self.pip_cache_dir),
            "NPM_CACHE_DIR": str(self.npm_cache_dir),
            "HF_HOME": str(self.hf_cache_dir),
            "TRANSFORMERS_CACHE": str(self.transformers_cache_dir),
            "LANGGRAPH_DIR": str(self.langgraph_dir),
            "WORKFLOW_SNAPSHOT_DIR": str(self.workflow_snapshot_dir),
            "INDEX_DIR": str(self.index_dir),
            "LOGS_DIR": str(self.logs_dir),
            "DB_DIR": str(self.db_dir),
            "LOCAL_MODEL_DIR": str(self.local_model_dir),
            "OLLAMA_MODEL_DIR": str(self.ollama_model_dir),
            "OLLAMA_MODELS": str(self.ollama_model_dir),
        }

    def export_runtime_env(self) -> None:
        for key, value in self.as_path_map().items():
            os.environ[key] = value
        os.environ["HF_TOKEN"] = self.hf_token
        os.environ["OLLAMA_HOST"] = self.ollama_host
        if self.ollama_executable_path.strip():
            os.environ["YIXIUTONG_OLLAMA_EXE"] = self.ollama_executable_path

    def provider_config(self, channel: str) -> dict[str, str]:
        if channel == "primary":
            return {
                "provider": self.primary_llm_provider,
                "model": self.primary_llm_model,
                "base_url": self.primary_llm_base_url,
                "api_key": self.primary_llm_api_key,
                "timeout_seconds": str(self.llm_timeout_seconds),
            }
        if channel == "fallback":
            return {
                "provider": self.fallback_llm_provider,
                "model": self.fallback_llm_model,
                "base_url": self.fallback_llm_base_url,
                "api_key": self.fallback_llm_api_key,
                "timeout_seconds": str(self.llm_timeout_seconds),
            }
        raise RuntimeError(f"Unsupported provider channel: {channel}")

    def retrieval_embedding_config(self) -> dict[str, str]:
        return {
            "provider": self.retrieval_embedding_provider,
            "model": self.retrieval_embedding_model,
            "base_url": self.retrieval_embedding_base_url,
            "api_key": self.retrieval_embedding_api_key,
            "timeout_seconds": str(self.retrieval_embedding_timeout_seconds),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    settings.export_runtime_env()
    return settings
