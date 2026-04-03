from app.services.rules import evaluate_risk


def test_rules_are_scoped_by_scene():
    rules = {
        "rules": [
            {"scene_type": "fault_diagnosis", "keywords": ["E-204"], "risk_level": "high", "message": "fault risk"},
            {"scene_type": "quality_inspection", "keywords": ["尺寸"], "risk_level": "high", "message": "quality risk"}
        ]
    }
    fault_level, fault_matches = evaluate_risk("fault_diagnosis", "E-204", "振动异常", "", rules)
    quality_level, quality_matches = evaluate_risk("quality_inspection", "QA-305", "关键尺寸异常", "", rules)

    assert fault_level == "high"
    assert fault_matches == ["fault risk"]
    assert quality_level == "high"
    assert quality_matches == ["quality risk"]
