import pytest

from app.providers.json_utils import parse_structured_response


def test_parse_structured_response_accepts_plain_json():
    parsed = parse_structured_response('{"possible_causes":["a"],"recommended_checks":["b"],"recommended_actions":["c"]}')
    assert parsed["possible_causes"] == ["a"]


def test_parse_structured_response_extracts_json_from_wrapped_text():
    content = "analysis first\n{\"possible_causes\":[\"a\"],\"recommended_checks\":[\"b\"],\"recommended_actions\":[\"c\"]}\nclosing"
    parsed = parse_structured_response(content)
    assert parsed["recommended_actions"] == ["c"]


def test_parse_structured_response_rejects_non_json():
    with pytest.raises(ValueError):
        parse_structured_response("not json")
