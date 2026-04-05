from pathlib import Path

from app.core.config import Settings
from app.services.embeddings import hashing_embedding
from app.services.ingestion import build_index
from app.services.retrieval import search


def test_hybrid_retrieval_prioritizes_fault_code_and_returns_metadata():
    settings = Settings(retrieval_embedding_provider="hashing", retrieval_enable_model_rerank=False)
    corpus = [
        {
            "id": "doc-1",
            "source_type": "manual",
            "scene_type": "fault_diagnosis",
            "title": "E-204 排故手册",
            "snippet": "E-204 常与振动、温升、轴承异常相关。",
            "path": "materials/knowledge/manuals/e204_manual.md",
            "embedding": hashing_embedding("E-204 常与振动、温升、轴承异常相关。"),
            "embedding_backend": "hashing",
        },
        {
            "id": "doc-2",
            "source_type": "case",
            "scene_type": "fault_diagnosis",
            "title": "通用冷却案例",
            "snippet": "冷却效率下降会引发温度上升。",
            "path": "materials/knowledge/cases/e204_case_01.md",
            "embedding": hashing_embedding("冷却效率下降会引发温度上升。"),
            "embedding_backend": "hashing",
        },
    ]

    results = search("E-204 振动 温度升高", corpus, scene_type="fault_diagnosis", top_k=2, settings=settings)

    assert len(results) == 2
    assert results[0].evidence_id == "doc-1"
    assert results[0].retrieval_method in {"keyword", "hybrid"}
    assert results[0].keyword_score > 0
    assert results[0].semantic_score > 0
    assert results[0].rerank_score > 0
    assert results[0].model_rerank_score == 0
    assert results[0].retrieval_backend.startswith("hashing|disabled")
    assert results[0].source_path.endswith("e204_manual.md")


def test_build_index_persists_embeddings(tmp_path: Path):
    materials_root = tmp_path / "materials"
    manual_dir = materials_root / "knowledge" / "manuals" / "fault_diagnosis"
    manual_dir.mkdir(parents=True)
    (manual_dir / "sample_manual.md").write_text("# Sample\n\nE-204 vibration troubleshooting.", encoding="utf-8")

    settings = Settings(
        project_root=tmp_path,
        materials_root=materials_root,
        runtime_root=tmp_path / "runtime",
        models_root=tmp_path / "models",
        cache_root=tmp_path / "runtime" / "cache",
        retrieval_embedding_provider="hashing",
        retrieval_enable_model_rerank=False,
    )
    output_path = tmp_path / "runtime" / "index" / "index.json"
    items = build_index(materials_root, output_path, settings=settings)

    assert items
    assert "embedding" in items[0]
    assert len(items[0]["embedding"]) == 128
    assert items[0]["embedding_backend"] == "hashing"
    assert items[0]["content_hash"]
    assert output_path.exists()


def test_search_enriches_case_memory_with_dynamic_embeddings():
    settings = Settings(retrieval_embedding_provider="hashing", retrieval_enable_model_rerank=False)
    corpus = [
        {
            "id": "doc-1",
            "source_type": "manual",
            "scene_type": "fault_diagnosis",
            "title": "E-204 排故手册",
            "snippet": "E-204 常与振动、温升和轴承异常相关。",
            "path": "materials/knowledge/manuals/e204_manual.md",
            "embedding": hashing_embedding("E-204 常与振动、温升和轴承异常相关。"),
            "embedding_backend": "hashing",
        },
        {
            "id": "case-memory-1",
            "source_type": "case_memory",
            "scene_type": "fault_diagnosis",
            "title": "闭环案例 | E-204",
            "snippet": "问题编号：E-204 异常现象：设备振动异常并伴随温升。最终结论：更换轴承后恢复正常。",
            "path": "runtime/db/portal.sqlite3#WO-CASE-001",
        },
    ]

    results = search("E-204 振动 温升 轴承", corpus, scene_type="fault_diagnosis", top_k=2, settings=settings)

    assert len(results) == 2
    assert any(item.source_type == "case_memory" for item in results)
    case_memory = next(item for item in results if item.source_type == "case_memory")
    assert case_memory.semantic_score > 0
    assert case_memory.retrieval_backend.startswith("hashing|disabled")
