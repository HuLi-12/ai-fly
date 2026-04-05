from app.core.config import Settings
from app.services.reranker import model_rerank_candidates


def test_model_reranker_parses_scores(monkeypatch):
    settings = Settings(retrieval_enable_model_rerank=True)

    def fake_generate_structured_with_fallback(**kwargs):
        return (
            {
                "scored": [
                    {"evidence_id": "doc-1", "score": 0.92},
                    {"evidence_id": "doc-2", "score": 0.41},
                ]
            },
            "ollama:fallback:yixiutong-qwen3b",
        )

    monkeypatch.setattr(
        "app.services.reranker.generate_structured_with_fallback",
        fake_generate_structured_with_fallback,
    )

    scores, provider = model_rerank_candidates(
        settings=settings,
        query="E-204 振动 温度升高",
        scene_type="fault_diagnosis",
        candidates=[
            {"id": "doc-1", "title": "Manual", "snippet": "bearing vibration", "source_type": "manual"},
            {"id": "doc-2", "title": "Case", "snippet": "cooling drift", "source_type": "case"},
        ],
    )

    assert provider == "ollama:fallback:yixiutong-qwen3b"
    assert scores["doc-1"] == 0.92
    assert scores["doc-2"] == 0.41
