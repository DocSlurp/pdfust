"""Offline invariants for experimental gate evidence packets."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from bench import p003_gate_packet as gate
from bench import pipeline_admission as admission


def source(count: int = 4) -> dict[str, Any]:
    return {
        "page_size": [0, 0, 300, 300],
        "words": [
            {"id": f"w{i}", "text": f"literal{i}", "bbox": [i, 10, i + 1, 20], "line": [0, i // 2]}
            for i in range(count)
        ],
        "gold": "SECRET",
    }


@pytest.mark.parametrize("style", gate.STYLES)
@pytest.mark.parametrize("pixels", [True, False])
def test_styles_scope_provenance(style: str, pixels: bool) -> None:  # noqa: FBT001
    page = source()
    before = copy.deepcopy(page)
    text, meta = gate.packet(page, [0, 0, 300, 300], pixels, style)
    obj = json.loads(text)
    assert page == before
    assert "SECRET" not in text
    assert "instructions" not in obj
    assert obj["availability"]["region_pixels"] == ("supplied separately" if pixels else "unavailable")
    assert "requested region only" in obj["scope"]["classification_scope"]
    assert meta["counts"]["supplied_words"] == 4
    assert meta["packet_bytes"] == len(text.encode("utf-8"))
    assert len(meta["full_source_sha256"]) == 64
    assert meta["counts"]["omitted_region_words"] == (4 if style == "image_only" else 0)


def test_hashes_independent_of_style_pixels_and_extraneous_keys() -> None:
    page = source()
    hashes = {gate.packet(page, [0, 0, 300, 300], False, s)[1]["full_source_sha256"] for s in gate.STYLES}
    assert len(hashes) == 1
    page["gold"] = "different"
    assert gate.packet(page, [0, 0, 300, 300], True, "compact")[1]["full_source_sha256"] in hashes
    page["words"][0]["text"] = "changed"
    assert gate.packet(page, [0, 0, 300, 300], True, "compact")[1]["full_source_sha256"] not in hashes


@pytest.mark.parametrize("style", ["image_only", "sample64", "compact"])
def test_complete_admission_precedes_projection(style: str) -> None:
    page = source(100)
    page["words"][-1]["id"] = page["words"][0]["id"]
    with pytest.raises(ValueError, match="unique"):
        gate.packet(page, [0, 0, 1, 1], False, style)


def test_fullsource_byte_admission_even_image_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admission, "MAX_PACKET_BYTES", 10)
    with pytest.raises(ValueError, match="no truncation"):
        gate.packet(source(), [0, 0, 300, 300], True, "image_only")


def test_explicit_output_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "MAX_PACKET_BYTES", 10)
    with pytest.raises(ValueError, match="no truncation"):
        gate.packet(source(), [0, 0, 300, 300], False, "lineflow")


def test_projection_crossing_and_closed_edges() -> None:
    page = source()
    text, meta = gate.packet(page, [1.5, 0, 2.5, 30], False, "fullwords")
    assert [w["id"] for w in json.loads(text)["evidence"]["words"]] == ["w1", "w2"]
    assert meta["counts"]["boundary_crossing_words"] == 2
    assert meta["counts"]["outside_region_words"] == 2
    assert meta["counts"]["omitted_region_words"] == 0
    page["words"][0]["bbox"] = [1.5, 0, 1.5, 0]
    text, _ = gate.packet(page, [1.5, 0, 2.5, 30], False, "fullwords")
    assert json.loads(text)["evidence"]["words"][0]["id"] == "w0"


def test_uniform_sampling_preserves_literal_first_last_and_omissions() -> None:
    page = source(100)
    text, meta = gate.packet(page, [0, 0, 300, 300], False, "sample64")
    words = json.loads(text)["evidence"]["words"]
    assert len(words) == 64
    assert words[0] == {k: page["words"][0][k] for k in ("id", "text", "bbox")}
    assert words[-1]["id"] == "w99"
    assert len({w["id"] for w in words}) == 64
    assert [w["id"] for w in words] == [f"w{i * 99 // 63}" for i in range(64)]
    assert meta["counts"]["omitted_region_words"] == 36
    assert meta["text_sizes"]["region"]["characters"] == (
        meta["text_sizes"]["evidence"]["characters"] + meta["text_sizes"]["omitted_region"]["characters"]
    )


def test_compact_rounding_and_physical_duplicates() -> None:
    page = source(2)
    page["words"][0].update(text="同じ", bbox=[0.125, 0.375, 1.125, 1.375])
    page["words"][1].update(text="同じ", bbox=[0.125, 0.375, 1.125, 1.375])
    text, meta = gate.packet(page, [0, 0, 300, 300], False, "compact")
    assert json.loads(text)["evidence"]["words"] == [["同じ", 0, 2, 4, 6], ["同じ", 0, 2, 4, 6]]
    assert meta["coordinate_precision"]["maximum_error_points"] == 0.125
    assert meta["source_ids_retained"] is False
    assert meta["text_sizes"]["evidence"]["utf8_bytes"] == 12


def test_lineflow_two_views_keep_all_physical_words() -> None:
    page = source(3)
    page["words"][0]["bbox"] = [30, 40, 40, 50]
    page["words"][1]["bbox"] = [10, 10, 20, 20]
    page["words"][2]["bbox"] = [10, 10, 20, 20]
    page["words"][2]["text"] = page["words"][1]["text"]
    text, meta = gate.packet(page, [0, 0, 300, 300], False, "lineflow")
    views = json.loads(text)["evidence"]["reading_views"]
    assert views["native_word_order"]["source_ids"] == ["w0", "w1", "w2"]
    assert views["geometry_row_bands"]["lines"][0]["source_ids"] == ["w1", "w2"]
    assert meta["counts"]["evidence_words"] == 3
    assert meta["counts"]["omitted_region_words"] == 0
    page["words"][0]["line"] = None
    assert "unavailable or invalid" in json.loads(
        gate.packet(page, [0, 0, 300, 300], False, "lineflow")[0]
    )["evidence"]["reading_views"]["native_word_order"]["line_source"]


@pytest.mark.parametrize("box", [[0, 0, 0, 1], [-1, 0, 3, 3], [0, 0, 301, 3], [0, 0, float("nan"), 3]])
def test_invalid_region(box: list[float]) -> None:
    with pytest.raises(ValueError, match=r"region|Region"):
        gate.packet(source(), box, False, "fullwords")


