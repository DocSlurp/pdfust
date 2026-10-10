"""Frozen row observations preserve exact source while leaving decisions unmade."""

from copy import deepcopy

import pytest
from bench.pipeline_row_evidence import SPEC, build, encode


def source() -> dict:
    return {
        "page_size": [0, 0, 200, 100],
        "words": [
            {"id": "r:w零", "text": "Header", "bbox": [10, 10, 40, 20]},
            {"id": "opaque-β", "text": "12", "bbox": [70, 10, 80, 20]},
            {"id": "x", "text": "continued", "bbox": [20, 30, 55, 40]},
            {"id": "y", "text": "sentence.", "bbox": [70, 30, 110, 40]},
        ],
    }


def test_literal_complete_source_and_observations_are_preserved() -> None:
    data = source()
    original = deepcopy(data)
    packet = build(data)
    assert data == original
    assert packet["words"] == [[w["id"], w["text"], w["bbox"]] for w in data["words"]]
    assert packet["em_proxy"] == 10
    first, second = packet["rows"]
    assert first["gaps_em"] == [3]
    assert second["gaps_em"] == [1.5]
    assert first["roles"] == [1, 1, 0, 0]
    assert second["adjacent"]["previous"]["indent_shift_em"] == 1
    assert second["adjacent"]["previous"]["center_gap_em"] == 2
    assert second["adjacent"]["previous"]["shared_start_tracks"] == 1
    assert second["ending"] == "sentence"
    assert second["lowercase_start"] is True
    assert "r:w零" in encode(packet)
    assert "threshold" not in packet
    assert SPEC["decisions"].startswith("Observations only")


def test_family_annotations_and_gold_cannot_affect_evidence() -> None:
    data = source()
    expected = build(data)
    data.update(family="prose", filename="selected.pdf", gold="invented")
    data["words"][0]["gold"] = "invented"
    assert build(data) == expected


def test_empty_and_degenerate_word_geometry_have_explicit_missing_proxy() -> None:
    assert build({"page_size": [100, 100], "words": []})["rows"] == []
    packet = build({"page_size": [100, 100], "words": [{"id": "w0", "text": "字", "bbox": [10, 10, 20, 10]}]})
    assert packet["em_proxy"] is None
    assert packet["rows"][0]["lowercase_start"] is None


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True])
def test_invalid_geometry_is_refused(bad: object) -> None:
    data = source()
    data["words"][0]["bbox"][0] = bad
    with pytest.raises(ValueError, match=r".+"):
        build(data)


def test_duplicate_identity_and_complete_admission_are_not_repaired(monkeypatch: pytest.MonkeyPatch) -> None:
    data = source()
    data["words"].append(deepcopy(data["words"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        build(data)
    monkeypatch.setattr("bench.pipeline_row_evidence.MAX_PACKET_BYTES", 50)
    with pytest.raises(ValueError, match="Complete row evidence"):
        build(source())


def test_uniform_scale_preserves_normalized_features_and_original_geometry() -> None:
    data = source()
    initial = build(data)
    for word in data["words"]:
        word["bbox"] = [value * 2 for value in word["bbox"]]
    data["page_size"] = [value * 2 for value in data["page_size"]]
    scaled = build(data)
    assert scaled["em_proxy"] == initial["em_proxy"] * 2
    for before, after in zip(initial["rows"], scaled["rows"], strict=True):
        assert before["gaps_em"] == after["gaps_em"]
        assert before["start_tracks"] == after["start_tracks"]
        assert before["adjacent"] == after["adjacent"]
    assert scaled["words"][0][2] == data["words"][0]["bbox"]
