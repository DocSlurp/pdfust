"""Image-only control validation; no network, models, corpus, or credentials."""

import json
from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_vision_transcription import (
    MAX_CONTENT_BYTES,
    MAX_TABLES,
    MAX_TEXT_BYTES,
    MAX_TOKENS,
    MODELS,
    PROVENANCE,
    markdown,
    parse,
    request,
)

BOUNDS = [100, 200, 900, 600]
URL = "data:image/png;base64,AA=="


def table() -> dict[str, Any]:
    return {"bbox": [100, 250, 900, 750], "matrix": [["Header", "Rate"], ["Ω₂ + x^2", "−3.14%"]], "mergedspans": []}


def response(tables: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "choices": [
            {"finish_reason": "stop", "message": {"content": json.dumps({"answers": {"q0": {"tables": tables}}})}}
        ]
    }


@pytest.mark.parametrize("model", MODELS)
def test_request_is_image_only_and_contains_no_source_metadata(model: str) -> None:
    body = request(model, URL, BOUNDS)
    assert body["model"] == model
    assert body["max_tokens"] == MAX_TOKENS == 16_384
    assert "temperature" not in body
    assert "reasoning" not in body
    assert body["messages"][1] == {
        "role": "user",
        "content": [{"type": "image_url", "image_url": {"url": URL, "detail": "high"}}],
    }
    assert body == request(model, URL, [0, 0, 1, 1])
    schema = body["response_format"]["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    table_schema = schema["properties"]["answers"]["properties"]["q0"]["properties"]["tables"]["items"]
    assert set(table_schema["properties"]) == {"bbox", "matrix", "mergedspans"}
    assert table_schema["additionalProperties"] is False


def test_parse_preserves_literal_text_multiple_tables_and_display_geometry() -> None:
    original = response([table(), {**table(), "matrix": [["second"]]}])
    before = deepcopy(original)
    parsed = parse(original, BOUNDS)
    assert original == before
    assert len(parsed["tables"]) == 2
    first = parsed["tables"][0]
    assert first["values"] == table()["matrix"]
    assert (first["row_count"], first["col_count"]) == (2, 2)
    assert first["bbox"] == [180, 300, 820, 500]
    assert first["spans"] == []
    assert parsed["text_provenance"] == first["text_provenance"] == PROVENANCE
    assert parsed["source_conserved"] is first["source_conserved"] is False
    assert all(c["source_ids"] == [] and c["text_provenance"] == PROVENANCE for c in first["cells"])
    assert len(first["cells"]) == 4


def test_no_table_is_an_explicit_labeled_empty_result() -> None:
    parsed = parse(response([]), BOUNDS)
    assert parsed == {"tables": [], "text_provenance": PROVENANCE, "source_conserved": False}
    assert markdown(parsed) == ""


def test_merged_spans_convert_only_covered_slots_to_none_and_escape_html() -> None:
    source = table()
    source.update(matrix=[['<script>& "quoted"\nCase | math', ""], ["", ""]], mergedspans=[[0, 0, 2, 2]])
    parsed = parse(response([source]), BOUNDS)
    canonical = parsed["tables"][0]
    assert canonical["values"] == [[source["matrix"][0][0], None], [None, None]]
    assert canonical["spans"] == [{"row": 0, "column": 0, "row_span": 2, "column_span": 2}]
    text = markdown(parsed)
    assert '<td rowspan="2" colspan="2">' in text
    assert "&lt;script&gt;&amp; &quot;quoted&quot;<br>Case | math" in text
    assert "<script>" not in text
    assert text.count("<td") == 1


@pytest.mark.parametrize("reason", ["length", "content_filter", None, [], "tool_calls"])
def test_truncation_and_non_normal_finish_are_rejected(reason: object) -> None:
    raw = response([table()])
    raw["choices"][0]["finish_reason"] = reason
    with pytest.raises(ValueError, match=r"finish|truncated"):
        parse(raw, BOUNDS)


@pytest.mark.parametrize("mutation", ["refusal", "two", "missing", "nontext"])
def test_refusal_or_missing_complete_json_rejects(mutation: str) -> None:
    raw = response([table()])
    if mutation == "refusal":
        raw["choices"][0]["message"]["refusal"] = "refused"
    elif mutation == "two":
        raw["choices"] *= 2
    elif mutation == "missing":
        raw["choices"][0].pop("message")
    else:
        raw["choices"][0]["message"]["content"] = []
    with pytest.raises(ValueError, match=r".+"):
        parse(raw, BOUNDS)


@pytest.mark.parametrize(
    "content",
    [
        '{"answers":{"q0":{"tables":[],"tables":[]}}}',
        '{"answers":{"q0":{"tables":[]}},"answers":{"q0":{"tables":[]}}}',
        '{"answers":{"q0":{"tables":[],"extra":0}}}',
        '{"answers":{"q0":{"tables":[]},"q1":{}}}',
        '{"answers":{"q0":{"tables":[]}},"reason":"x"}',
        '{"answers":{"q0":{"tables":[{"bbox":[0,0,NaN,1000],"matrix":[["x"]],"mergedspans":[]}]}}}',
        '{"answers":{"q0":{"tables":[]}}',
        '```json\n{"answers":{"q0":{"tables":[]}}}\n```',
    ],
)
def test_non_strict_json_is_rejected(content: str) -> None:
    raw = response([])
    raw["choices"][0]["message"]["content"] = content
    with pytest.raises(ValueError, match=r".+"):
        parse(raw, BOUNDS)


@pytest.mark.parametrize(
    "update",
    [
        {"bbox": [0, 0, 1001, 1000]},
        {"bbox": [0, 0, 0, 1000]},
        {"bbox": [0, False, 1000, 1000]},
        {"extra": "x"},
        {"matrix": []},
        {"matrix": [["x"], ["a", "b"]]},
        {"matrix": [[None]]},
        {"matrix": [[1]]},
        {"matrix": [["x"]] * 4097},
        {"mergedspans": [[0, 0, 1, 1]]},
        {"mergedspans": [[0, 0, 3, 2]]},
        {"mergedspans": [[0, 0, 1, 2]]},
        {"mergedspans": [[False, 0, 1, 2]]},
        {"mergedspans": [[0, 0, 0, 2]]},
        {"mergedspans": [[0, 0, 1, 2], [0, 0, 1, 2]]},
        {"matrix": [["", ""], ["", ""]], "mergedspans": [[0, 0, 1, 2], [0, 1, 2, 1]]},
    ],
)
def test_invalid_table_shapes_bounds_spans_and_unknown_keys_reject(update: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r".+"):
        parse(response([{**table(), **update}]), BOUNDS)


def test_oversized_content_text_and_aggregate_data_reject_atomically() -> None:
    with pytest.raises(ValueError, match="inventory"):
        parse(response([table()] * (MAX_TABLES + 1)), BOUNDS)
    raw = response([])
    raw["choices"][0]["message"]["content"] = " " * (MAX_CONTENT_BYTES + 1)
    with pytest.raises(ValueError, match="content admission"):
        parse(raw, BOUNDS)
    with pytest.raises(ValueError, match="text admission"):
        parse(response([{**table(), "matrix": [["x" * (MAX_TEXT_BYTES + 1)]]}]), BOUNDS)
    large = {**table(), "matrix": [[""] * 64] * 64}
    with pytest.raises(ValueError, match="Aggregate"):
        parse(response([large] * 5), BOUNDS)
    with pytest.raises(ValueError, match="Aggregate"):
        parse(response([{**table(), "matrix": [["x" * 600_000]]}] * 2), BOUNDS)


@pytest.mark.parametrize("viewport", [[0, 0], [0, 0, 0, 1], [0, 0, float("nan"), 1], [0, False, 1, 1]])
def test_viewport_rejection(viewport: list[float]) -> None:
    with pytest.raises(ValueError, match="Viewport"):
        request(MODELS[0], URL, viewport)
    with pytest.raises(ValueError, match="Viewport"):
        parse(response([]), viewport)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/source.pdf.png",
        "data:image/png;name=source.pdf;base64,AA==",
        "data:image/png;base64,",
        "data:image/png;base64,!!!",
    ],
)
def test_only_bounded_filename_free_image_data_urls_are_allowed(url: str) -> None:
    with pytest.raises(ValueError, match=r".+"):
        request(MODELS[0], url, BOUNDS)


def test_unknown_model_and_invalid_token_limits_reject() -> None:
    with pytest.raises(ValueError, match="controls"):
        request("other/model", URL, BOUNDS)
    for limit in (True, 0, 65_537):
        with pytest.raises(ValueError, match="token"):
            request(MODELS[0], URL, BOUNDS, max_tokens=limit)


@pytest.mark.parametrize("mutation", ["source", "covered", "dimensions", "unknown"])
def test_markdown_revalidates_mutated_canonical_data(mutation: str) -> None:
    parsed = parse(response([table()]), BOUNDS)
    first = parsed["tables"][0]
    if mutation == "source":
        first["cells"][0]["source_ids"] = ["w1"]
    elif mutation == "covered":
        first["values"][0][0] = None
    elif mutation == "dimensions":
        first["row_count"] = 5
    else:
        first["confidence"] = 0.9
    with pytest.raises(ValueError, match=r".+"):
        markdown(parsed)


def test_late_invalid_table_never_returns_an_admitted_prefix() -> None:
    raw = response([table(), {**table(), "matrix": [["good", "bad"], ["ragged"]]}])
    before = deepcopy(raw)
    with pytest.raises(ValueError, match="rectangular"):
        parse(raw, BOUNDS)
    assert raw == before


def test_literal_whitespace_and_unicode_are_not_normalized_by_adapter() -> None:
    literal = "  e\u0301 = Σ₁\n0,00; A/a—B  "
    parsed = parse(response([{**table(), "matrix": [[literal]]}]), BOUNDS)
    assert parsed["tables"][0]["values"] == [[literal]]
    assert literal.replace("\n", "<br>") in markdown(parsed)


def test_nonfinite_numeric_overflow_and_deep_json_reject() -> None:
    raw = response([])
    for content in (
        '{"answers":{"q0":{"tables":[{"bbox":[0,0,1e309,1000],"matrix":[["x"]],"mergedspans":[]}]}}}',
        "[" * 2000 + "0" + "]" * 2000,
    ):
        raw["choices"][0]["message"]["content"] = content
        with pytest.raises(ValueError, match=r".+"):
            parse(raw, BOUNDS)
