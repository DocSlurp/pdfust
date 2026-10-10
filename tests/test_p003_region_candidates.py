"""Source-only region proposals preserve uncertainty and enforce admissions."""

from copy import deepcopy
from typing import Any

import pytest
from bench import p003_region_candidates as regions
from bench.p003_region_candidates import propose
from bench.pipeline_dense_candidates import MAX_PIXELS, raster_vectors
from PIL import Image, ImageDraw


def page(rows: int = 6, *, top: int = 20) -> dict[str, Any]:
    words: list[dict[str, Any]] = []
    for row in range(rows):
        words.extend(
            {
                "id": f"w{row}-{column}",
                "text": f"literal-{row}-{column}",
                "bbox": [20 + column * 90, top + row * 20, 60 + column * 90, top + row * 20 + 10],
            }
            for column in range(3)
        )
    return {"page_size": [400, 1000], "words": words}


def open_grid() -> Image.Image:
    image = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(image)
    for y in (40, 140, 240, 340):
        draw.line((40, y, 340, y), fill="black", width=2)
    # Deliberately omit the right outer border; existing full-grid admission fails.
    for x in (40, 140, 240):
        draw.line((x, 40, x, 340), fill="black", width=2)
    return image


def test_repeated_tracks_preserve_literal_packets_and_input() -> None:
    source = page()
    before = deepcopy(source)
    result = propose(source)
    assert source == before
    assert result["diagnostics"]["retained_candidates"] >= 1
    whole = next(c for c in result["candidates"] if not c["capacity_window"])
    assert whole["mechanisms"] == ["ocr_aligned_tracks"]
    assert whole["semantic_status"] == "proposal_only"
    assert whole["packet"]["words"] == source["words"]
    assert whole["packet"]["source_context_complete"]
    assert whole["packet"]["physical_table_completeness"] == "unknown"
    assert whole["evidence_records"][0]["physical_rows"] == 6
    assert "tables" not in whole


def test_unrelated_keys_and_reordered_source_do_not_change_geometry() -> None:
    source = page()
    clean = propose(source)
    source.update(reference_boxes=[[0, 0, 400, 1000]], tables="ignored", detector="ignored")
    assert propose(source) == clean
    source["words"].reverse()
    reordered = propose(source)
    assert [c["bbox"] for c in reordered["candidates"]] == [c["bbox"] for c in clean["candidates"]]
    # Packets retain supplied source order instead of silently rewriting provenance.
    assert reordered["candidates"][0]["packet"]["source_ids"] == list(
        reversed(clean["candidates"][0]["packet"]["source_ids"])
    )


def test_single_prose_lines_and_isolated_pairs_are_not_track_evidence() -> None:
    source = page(2)
    assert propose(source)["candidates"] == []
    source = page(6)
    source["words"] = [w for w in source["words"] if w["id"].endswith("-0")]
    assert propose(source)["candidates"] == []


def test_single_line_between_tables_breaks_tracks() -> None:
    source = page(7)
    source["words"] = [w for w in source["words"] if not w["id"].startswith("w3-")]
    source["words"].append({"id": "heading", "text": "Heading", "bbox": [20, 80, 250, 90]})
    whole = [c for c in propose(source)["candidates"] if not c["capacity_window"]]
    assert len(whole) == 2
    assert all(c["evidence_records"][0]["physical_rows"] == 3 for c in whole)


def test_open_raster_rules_propose_without_complete_grid_or_text() -> None:
    image = open_grid()
    assert raster_vectors(image, [100, 200, 900, 1000]) == []
    result = propose({"page_size": [100, 200, 900, 1000], "words": []}, image=image)
    assert len(result["candidates"]) == 1
    c = result["candidates"][0]
    assert c["mechanisms"] == ["raster_rule_component"]
    assert c["bbox"] == pytest.approx([176, 276, 785, 885], abs=3)
    assert c["packet"]["source_word_count"] == 0
    assert c["evidence_records"][0]["outer_edge_completeness"] == "not_required_or_inferred"


@pytest.mark.parametrize("kind", ["underline", "rectangle", "axes", "filled"])
def test_rule_negative_controls(kind: str) -> None:
    image = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(image)
    if kind == "underline":
        draw.line((40, 40, 340, 40), fill="black", width=2)
    elif kind == "rectangle":
        draw.rectangle((40, 40, 340, 340), outline="black", width=2)
    elif kind == "axes":
        draw.line((40, 40, 40, 340, 340, 340), fill="black", width=2)
    else:
        draw.rectangle((40, 40, 340, 340), fill="black")
    assert propose({"page_size": [400, 400], "words": []}, image=image)["candidates"] == []


def test_candidate_and_packet_omissions_are_explicit() -> None:
    result = propose(page(40), max_candidates=1)
    assert result["diagnostics"]["omitted_candidates"] > 0
    assert len(result["candidates"]) == 1
    c = result["candidates"][0]
    assert c["packet"]["source_word_count"] == 120
    long = page(100)
    long["page_size"] = [400, 2500]
    c = propose(long, max_candidates=1)["candidates"][0]
    assert c["packet"]["source_word_count"] == 300
    assert c["packet"]["omitted_source_words"] >= 44
    assert not c["packet"]["source_context_complete"]


@pytest.mark.parametrize("cap", [0, 65, True, 2.5])
def test_candidate_cap_admission(cap: Any) -> None:  # noqa: ANN401 - invalid runtime input cases.
    with pytest.raises(ValueError, match="candidate cap"):
        propose(page(), max_candidates=cap)


def test_malformed_source_and_oversize_raster_refuse_before_partial_output() -> None:
    source = page()
    source["words"][0]["bbox"][0] = -1
    with pytest.raises(ValueError, match="outside display"):
        propose(source)
    source = page()
    source["words"][1]["id"] = source["words"][0]["id"]
    with pytest.raises(ValueError, match="Duplicate"):
        propose(source)
    with pytest.raises(ValueError, match="pixel admission"):
        propose(page(), image=Image.new("RGB", (MAX_PIXELS, 1)))


def test_raster_rule_refusal_preserves_independently_admitted_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(_image: Any, _bounds: list[float]) -> list[dict[str, Any]]:  # noqa: ANN401 - synthetic raster protocol.
        raise ValueError("Raster rule inventory exceeds admission")  # noqa: EM101, TRY003 - pin collector refusal.

    monkeypatch.setattr(regions, "_raster_regions", refuse)
    result = propose(page(), image=Image.new("RGB", (400, 400)), raster_grid=2)
    assert result["candidates"]
    assert result["diagnostics"]["refused_raster_views"] == 5
    assert all(v["status"] == "rule_inventory_refused" for v in result["diagnostics"]["raster_views"])
    assert all(c["mechanisms"] == ["ocr_aligned_tracks"] for c in result["candidates"])


def test_fixed_raster_views_map_global_coordinates_and_mark_interior_edges() -> None:
    image = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(image)
    for coordinate in range(40, 341, 50):
        draw.line((40, coordinate, 340, coordinate), fill="black", width=2)
        draw.line((coordinate, 40, coordinate, 340), fill="black", width=2)
    result = propose({"page_size": [100, 200, 900, 1000], "words": []}, image=image, raster_grid=2)
    assert len(result["diagnostics"]["raster_views"]) == 5
    assert result["candidates"]
    assert all(100 <= c["bbox"][0] < c["bbox"][2] <= 900 for c in result["candidates"])
    assert all(200 <= c["bbox"][1] < c["bbox"][3] <= 1000 for c in result["candidates"])
    assert any("interior raster-view boundary" in warning for c in result["candidates"] for warning in c["warnings"])


def test_small_cap_keeps_both_mechanisms_with_ambiguous_proposals() -> None:
    result = propose(page(), image=open_grid(), max_candidates=2)
    assert len(result["candidates"]) == 2
    assert result["candidates"][0]["mechanisms"] == ["ocr_aligned_tracks"]
    assert result["candidates"][1]["mechanisms"] == ["raster_rule_component"]
    assert all(c["semantic_status"] == "proposal_only" for c in result["candidates"])
