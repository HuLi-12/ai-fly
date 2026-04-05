from app.agents import graph as graph_module
from app.models.schemas import ConfidenceScore, DiagnosisRequest, DiagnosisResult, EvidenceItem, TraceabilityItem


def _request() -> DiagnosisRequest:
    return DiagnosisRequest(
        fault_code="E-204",
        symptom_text="设备运行时振动异常，伴随温度升高。",
        device_type="装配工位",
        context_notes="夜班运行后报警升级。",
        scene_type="fault_diagnosis",
    )


def test_workflow_retries_retrieval_when_recall_is_low(monkeypatch):
    calls = {"search": 0}

    def fake_search(query, corpus_items, scene_type, top_k=5, settings=None):
        calls["search"] += 1
        if calls["search"] == 1:
            return [
                EvidenceItem(
                    evidence_id="doc-1",
                    source_type="manual",
                    title="E-204 手册",
                    snippet="停机后检查轴承。",
                    score=0.8,
                )
            ]
        return [
            EvidenceItem(evidence_id="doc-1", source_type="manual", title="E-204 手册", snippet="停机后检查轴承。", score=0.8),
            EvidenceItem(evidence_id="doc-2", source_type="case", title="振动案例", snippet="联轴器松动会引起振动。", score=0.72),
            EvidenceItem(evidence_id="doc-3", source_type="manual", title="冷却检查", snippet="温升异常需复核冷却回路。", score=0.7),
        ]

    def fake_generate_diagnosis(**kwargs):
        return (
            DiagnosisResult(
                possible_causes=["轴承或联轴器异常。"],
                recommended_checks=["检查轴承间隙。"],
                recommended_actions=["停机后执行人工复核。"],
            ),
            "heuristic_fallback",
        )

    monkeypatch.setattr(graph_module, "search", fake_search)
    monkeypatch.setattr(graph_module, "generate_diagnosis", fake_generate_diagnosis)

    result = graph_module.build_workflow().invoke({"request": _request()})
    response = result["response"]

    assert calls["search"] == 2
    assert len(response.evidence) == 3
    assert any(item.node == "retrieve_retry" for item in response.execution_trace)


def test_workflow_runs_second_opinion_for_low_confidence(monkeypatch):
    score_calls = {"count": 0}

    def fake_search(query, corpus_items, scene_type, top_k=5, settings=None):
        return [
            EvidenceItem(evidence_id="doc-1", source_type="manual", title="E-204 手册", snippet="检查轴承与冷却回路。", score=0.82),
            EvidenceItem(evidence_id="doc-2", source_type="case", title="振动案例", snippet="联轴器偏移会导致振动。", score=0.77),
            EvidenceItem(evidence_id="doc-3", source_type="manual", title="冷却案例", snippet="温升异常需复核风机。", score=0.74),
        ]

    def fake_generate_diagnosis(**kwargs):
        return (
            DiagnosisResult(
                possible_causes=["轴承异常。"],
                recommended_checks=["检查轴承间隙。"],
                recommended_actions=["安排现场复核。"],
            ),
            "ollama:fallback:yixiutong-qwen3b",
        )

    def fake_traceability(diagnosis, evidence):
        return [
            TraceabilityItem(
                recommendation=diagnosis.recommended_checks[0],
                category="check",
                support_score=0.8,
                support_level="strong",
                evidence_links=[],
            )
        ]

    def fake_confidence(**kwargs):
        score_calls["count"] += 1
        if score_calls["count"] == 1:
            return ConfidenceScore(overall_score=48.0, level="low", requires_human_review=True, warnings=["low"])
        return ConfidenceScore(overall_score=72.0, level="medium", requires_human_review=False, warnings=[])

    monkeypatch.setattr(graph_module, "search", fake_search)
    monkeypatch.setattr(graph_module, "generate_diagnosis", fake_generate_diagnosis)
    monkeypatch.setattr(graph_module, "build_traceability", fake_traceability)
    monkeypatch.setattr(graph_module, "compute_confidence", fake_confidence)

    result = graph_module.build_workflow().invoke({"request": _request()})
    response = result["response"]

    assert score_calls["count"] == 2
    assert any(item.node == "second_opinion" for item in response.execution_trace)
    assert response.confidence.overall_score == 72.0
