"""Wire grammar simplification leaves instructions and strict local validation intact."""

from copy import deepcopy

import pytest
from bench.p003_wire_schema import simplify
from bench.pipeline_vision_transcription import parse, request


def test_only_schema_bounds_change_and_local_geometry_stays_strict() -> None:
    body = request("anthropic/claude-haiku-5.5", "data:image/png;base64,eA==", [0, 0, 10, 10])
    original = deepcopy(body)
    changed, removed = simplify(body)
    assert body == original
    assert changed["messages"] == body["messages"]
    assert changed["model"] == body["model"]
    assert changed["response_format"]["json_schema"]["strict"] is True
    assert removed["maxItems"] > 0
    assert removed["maxLength"] > 0
    schema = changed["response_format"]["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["answers"]
    response = {"choices": [{"finish_reason": "stop", "message": {"content":
        '{"answers":{"q0":{"tables":[{"bbox":[0,0,1010,1000],'
        '"matrix":[["A","B"]],"mergedspans":[]}]}}}'}}]}
    with pytest.raises(ValueError, match="outside normalized"):
        parse(response, [0, 0, 10, 10])
