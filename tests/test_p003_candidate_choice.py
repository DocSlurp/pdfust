"""Whole-crop ranking preserves one exact transcription candidate without blending."""

import base64
import json
from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest
from bench import p003_candidate_choice as choice
from bench.pipeline_vision_transcription import parse as transcription

VIEWPORT = [10, 20, 210, 120]
IMAGE = "data:image/png;base64," + base64.b64encode(b"offline-image-bytes").decode()


def candidate(value: str = "literal") -> dict[str, Any]:
    payload = {
        "answers": {
            "q0": {
                "tables": [
                    {"bbox": [0, 0, 1000, 1000], "matrix": [["Item", "Price"], [value, "20"]], "mergedspans": []}
                ]
            }
        }
    }
    return transcription(
        {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(payload)}}]}, VIEWPORT
    )


def result(pool: choice.Pool, selected: str, *, maximum: float = 0.7) -> dict[str, Any]:
    options = [c.alias for c in pool.candidates] + ["unresolved"]
    remaining = (1 - maximum) / (len(options) - 1)
    return {
        "answers": {
            "q0": {
                "type": "choice",
                "choice": selected,
                "probabilities": {option: maximum if option == selected else remaining for option in options},
                "confidence": 0.123,
            }
        }
    }


def test_seeded_order_opaque_evidence_and_exact_selected_bytes() -> None:
    original = [candidate("Alpha"), candidate("Beta"), candidate("Gamma")]
    before = deepcopy(original)
    pool = choice.freeze_pool(VIEWPORT, original, seed=17)
    assert choice.freeze_pool(VIEWPORT, original, seed=17) == pool
    assert {c.alias for c in pool.candidates} == {"A", "B", "C"}
    body = choice.request(pool, "typesafe/jev-1.13", IMAGE)
    assert set(body) == {"model", "state", "questions"}
    evidence = json.loads(body["state"][0])
    assert set(evidence["candidates"]) == {"A", "B", "C"}
    assert "input_indexes" not in body["state"][0]
    assert "source_conserved" not in body["state"][0]
    assert body["state"][1]["type"] == "image_url"
    assert evidence["image_viewport"] == VIEWPORT
    assert all(
        set(t) == {"bbox", "values", "merged_spans"} for tables in evidence["candidates"].values() for t in tables
    )
    parsed = choice.parse(pool, result(pool, "B"))
    selected, audit = choice.select(pool, parsed)
    assert selected == pool.candidates[1].canonical_bytes
    assert selected == choice.canonical_json(original[pool.candidates[1].input_indexes[0]])
    assert audit["text_provenance"] == "model-transcribed"
    assert audit["source_conserved"] is False
    assert audit["choice"]["raw_confidence"] == 0.123
    assert original == before


def test_deduplication_preserves_original_indices_and_literal_text() -> None:
    one, two = candidate("same"), candidate("different")
    reordered = dict(reversed(list(one.items())))
    pool = choice.freeze_pool(VIEWPORT, [one, reordered, two, deepcopy(two)], seed=1)
    assert len(pool.candidates) == 2
    assert {c.input_indexes for c in pool.candidates} == {(0, 1), (2, 3)}
    duplicates = choice.freeze_pool(VIEWPORT, [one, deepcopy(one)], seed=1)
    assert len(duplicates.candidates) == 1
    with pytest.raises(ValueError, match="not applicable"):
        choice.request(duplicates, "typesafe/jev-1.13", IMAGE)
    distinct = choice.freeze_pool(VIEWPORT, [candidate("same"), candidate("same ")], seed=1)
    assert len(distinct.candidates) == 2


def test_explicit_abstention_and_no_extra_confidence_gate() -> None:
    pool = choice.freeze_pool(VIEWPORT, [candidate("one"), candidate("two")], seed=2)
    selected, audit = choice.select(pool, choice.parse(pool, result(pool, "unresolved")))
    assert selected is None
    assert audit["selection_status"] == "unresolved"
    low = result(pool, "A", maximum=0.34)
    low["answers"]["q0"]["confidence"] = 0.001
    selected, audit = choice.select(pool, choice.parse(pool, low))
    assert selected == pool.candidates[0].canonical_bytes
    assert audit["choice"]["raw_confidence"] == 0.001


def test_frozen_pool_selection_cannot_cross_snapshots_or_blend() -> None:
    pool = choice.freeze_pool(VIEWPORT, [candidate("one"), candidate("two")], seed=2)
    parsed = choice.parse(pool, result(pool, "A"))
    other = choice.freeze_pool(VIEWPORT, [candidate("three"), candidate("four")], seed=2)
    with pytest.raises(ValueError, match="different frozen"):
        choice.select(other, parsed)
    parsed["probabilities"]["A"] = 0.9
    with pytest.raises(ValueError, match="modified"):
        choice.select(pool, parsed)


def test_invalid_candidates_and_geometry_fail_before_request() -> None:
    good = candidate()
    malformed = deepcopy(good)
    malformed["tables"][0]["values"][0].append("extra")
    with pytest.raises(ValueError, match="dimensions"):
        choice.freeze_pool(VIEWPORT, [good, malformed], seed=1)
    outside = deepcopy(good)
    outside["tables"][0]["bbox"][0] = -100
    with pytest.raises(ValueError, match="viewport"):
        choice.freeze_pool(VIEWPORT, [good, outside], seed=1)
    overlap = deepcopy(good)
    overlap["tables"].append(deepcopy(overlap["tables"][0]))
    with pytest.raises(ValueError, match="overlapping"):
        choice.freeze_pool(VIEWPORT, [good, overlap], seed=1)
    unknown = deepcopy(good)
    unknown["gold"] = "forbidden"
    with pytest.raises(ValueError, match="keys"):
        choice.freeze_pool(VIEWPORT, [good, unknown], seed=1)
    with pytest.raises(ValueError, match="2-4"):
        choice.freeze_pool(VIEWPORT, [good], seed=1)


def test_merged_cells_empty_inventory_and_unicode_survive() -> None:
    merged = candidate("Unicode: é 漢字")
    merged["tables"][0]["values"][0][1] = None
    merged["tables"][0]["spans"] = [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}]
    empty = {"tables": [], "text_provenance": "model-transcribed", "source_conserved": False}
    pool = choice.freeze_pool(VIEWPORT, [merged, empty], seed=1)
    selected_alias = next(c.alias for c in pool.candidates if c.state() == merged)
    selected, _ = choice.select(pool, choice.parse(pool, result(pool, selected_alias)))
    assert selected == choice.canonical_json(merged)
    assert b"null" in selected


@pytest.mark.parametrize("bad", [True, float("nan"), -1, 1.1, "0.7"])
def test_invalid_probability_and_choice_fields(bad: Any) -> None:  # noqa: ANN401
    pool = choice.freeze_pool(VIEWPORT, [candidate("one"), candidate("two")], seed=2)
    invalid = result(pool, "A")
    invalid["answers"]["q0"]["probabilities"]["A"] = bad
    with pytest.raises(ValueError, match="finite numbers"):
        choice.parse(pool, invalid)


def test_exact_options_rounding_and_raw_argmax() -> None:
    pool = choice.freeze_pool(VIEWPORT, [candidate("one"), candidate("two")], seed=2)
    raw = result(pool, "A")
    raw["answers"]["q0"]["probabilities"] = {"A": 0.8, "B": 0.1, "unresolved": 0.09}
    parsed = choice.parse(pool, raw)
    assert parsed["normalization_delta"] == pytest.approx(-0.01)
    assert parsed["raw_probabilities"]["A"] == 0.8
    assert parsed["probabilities"]["A"] == pytest.approx(0.8 / 0.99)
    for invalid in (
        {"answers": {}},
        {
            "answers": {
                "q0": {"type": "choice", "choice": "B", "probabilities": {"A": 0.8, "B": 0.1, "unresolved": 0.1}}
            }
        },
        {"answers": {"q0": {"type": "choice", "choice": "A", "probabilities": {"A": 0.8, "B": 0.1}}}},
    ):
        with pytest.raises(ValueError, match=r"exact|maximum"):
            choice.parse(pool, invalid)


def test_complete_pool_and_comparison_refusal_never_truncate(monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = [candidate("one"), candidate("two")]
    monkeypatch.setattr(choice, "MAX_POOL_BYTES", 10)
    with pytest.raises(ValueError, match="no truncation"):
        choice.freeze_pool(VIEWPORT, inputs, seed=0)
    monkeypatch.setattr(choice, "MAX_POOL_BYTES", 8 * 1024 * 1024)
    pool = choice.freeze_pool(VIEWPORT, inputs, seed=0)
    monkeypatch.setattr(choice, "MAX_COMPARISON_BYTES", 10)
    with pytest.raises(ValueError, match="no truncation"):
        choice.request(pool, "typesafe/jev-1.13", IMAGE)
    with pytest.raises(ValueError, match="inline"):
        choice.request(pool, "typesafe/jev-1.13", "https://example.com/image.png")


def test_immutable_pool_record_and_modified_frozen_candidate_rejected() -> None:
    pool = choice.freeze_pool(VIEWPORT, [candidate("one"), candidate("two")], seed=2)
    record = choice.pool_record(pool)
    assert record["candidates"][0]["canonical_json"].encode() == pool.candidates[0].canonical_bytes
    parsed = choice.parse(pool, result(pool, "A"))
    altered = replace(pool.candidates[0], canonical_bytes=choice.canonical_json(candidate("invented")))
    changed = replace(pool, candidates=(altered, pool.candidates[1]))
    with pytest.raises(ValueError, match="bytes changed"):
        choice.select(changed, parsed)
