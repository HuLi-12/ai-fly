from app.services.retrieval import search


def test_hybrid_retrieval_prioritizes_fault_code_and_returns_metadata():
    corpus = [
        {
            "id": "doc-1",
            "source_type": "manual",
            "scene_type": "fault_diagnosis",
            "title": "E-204 排故手册",
            "snippet": "E-204 常与振动、温升、轴承异常相关。",
            "path": "materials/knowledge/manuals/e204_manual.md",
        },
        {
            "id": "doc-2",
            "source_type": "case",
            "scene_type": "fault_diagnosis",
            "title": "通用冷却案例",
            "snippet": "冷却效率下降会引发温度上升。",
            "path": "materials/knowledge/cases/e204_case_01.md",
        },
    ]

    results = search("E-204 振动 温度升高", corpus, scene_type="fault_diagnosis", top_k=2)

    assert len(results) == 2
    assert results[0].evidence_id == "doc-1"
    assert results[0].retrieval_method in {"keyword", "hybrid"}
    assert results[0].keyword_score > 0
    assert results[0].rerank_score > 0
    assert results[0].source_path.endswith("e204_manual.md")
