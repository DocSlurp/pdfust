"""Lossless compact packets, pure byte admission and independent hints."""

from copy import deepcopy
from typing import Any

import pytest
from bench.lowlevel_compact import adaptive_requests, compact, encoded, expand, relation_hint


def state() -> dict[str, Any]:
    return {
        "task": "line_ownership",
        "target_boxes": [[50, 180, 200, 196], [50, 198, 200, 214]],
        "chunks": [{"text": "literal source"}, {"text": "other source"}],
        "glyphs": [
            {
                "id": f"g{index}",
                "text": text,
                "origin": [50 + index * 6.0, 192.0],
                "font": "f0",
                "font_name": "Courier",
                "font_flags": 8,
                "size": 10.0,
                "source_order": index,
            }
            for index, text in enumerate("literal source")
        ],
        "text_operators": [
            {"operator": "Tj", "operands": [{"bytes_hex": "4142", "parser_text": "AB"}]},
            {"operator": "Tm", "operands": [1, 0, 0, 1, 50, 192]},
        ],
    }


@pytest.mark.parametrize("canonical", [False, True])
def test_exact_json_roundtrip_and_no_source_mutation(*, canonical: bool) -> None:
    source = state()
    if canonical:
        for glyph in source["glyphs"]:
            glyph.pop("source_order")
    before = deepcopy(source)
    packet = compact(source)
    assert source == before
    assert expand(packet) == source
    assert encoded(expand(packet)) == encoded(source)
    assert packet["glyphs"]["font_fields"] == ["font", "font_name", "font_flags"]
    assert packet["glyphs"]["fonts"] == [["f0", "Courier", 8]]
    assert len(encoded(packet)) < len(encoded(source))


def test_all_empty_and_multiple_font_records_roundtrip() -> None:
    assert expand(compact({"glyphs": [], "text_operators": []})) == {"glyphs": [], "text_operators": []}
    source = state()
    source["glyphs"][-1]["font"] = "f1"
    source["glyphs"][-1]["font_name"] = "Other font"
    source["glyphs"][-1]["font_flags"] = 16
    assert len(compact(source)["glyphs"]["fonts"]) == 2
    assert encoded(expand(compact(source))) == encoded(source)


def test_adaptive_batches_preserve_inventory_and_count_all_instructions() -> None:
    source = [{"data": "a" * 40}, {"data": "b" * 40}, {"data": "c" * 40}]

    def builder(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {"state": rows, "instructions": "x" * 40}

    cap = len(encoded(builder(source[:2])))
    before = deepcopy(source)
    batches = adaptive_requests(source, builder, max_bytes=cap)
    assert source == before
    assert [(batch["start"], batch["stop"]) for batch in batches] == [(0, 2), (2, 3)]
    assert [row for batch in batches for row in batch["body"]["state"]] == source
    assert all(batch["utf8_bytes"] == len(encoded(batch["body"])) <= cap for batch in batches)
    assert all(batch["body"]["instructions"] == "x" * 40 for batch in batches)
    with pytest.raises(ValueError, match="singleton"):
        adaptive_requests(source, builder, max_bytes=len(encoded(builder(source[:1]))) - 1)


def test_hints_use_only_retained_vector_geometry() -> None:
    source = state()
    assert relation_hint(source)["source_geometry_hint"]["choice"] == "unresolved"
    source["vector_marks"] = [{"type": "s", "color": [0, 0, 0], "width": 0.8, "items": [("l", (40, 201), (210, 201))]}]
    hinted = relation_hint(source)
    assert hinted["source_geometry_hint"]["choice"] == "split"
    assert hinted["glyphs"] == source["glyphs"]
    assert hinted["vector_marks"] == source["vector_marks"]
    assert "source_geometry_hint" not in source


def test_malformed_packet_and_inconsistent_source_refuse() -> None:
    source = state()
    source["glyphs"][0]["additional"] = "different field inventory"
    with pytest.raises(ValueError, match="inconsistent"):
        compact(source)
    packet = compact(state())
    packet["glyphs"]["rows"][0][-1] = True
    with pytest.raises(ValueError, match="font index"):
        expand(packet)
    packet = compact(state())
    position = packet["text_operators"]["columns"].index("operands")
    packet["text_operators"]["rows"][0][position] = -1
    with pytest.raises(ValueError, match="reference index"):
        expand(packet)
