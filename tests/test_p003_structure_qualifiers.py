"""Deterministic source conservation and ambiguity qualifier contracts."""

from __future__ import annotations

import json
from typing import Any

import pytest
from bench import p003_structure_qualifiers as q
from bench.pipeline_repair import validate


def shape() -> dict[str, Any]:
    """Construct a complete two-by-two geometry tiling."""
    return {
        "status": "geometry_candidate",
        "bbox": [0, 0, 100, 100],
        "row_count": 2,
        "column_count": 2,
        "x_edges": [0, 50, 100],
        "y_edges": [0, 50, 100],
        "anchors": [
            {
                "row": r,
                "column": c,
                "row_span": 1,
                "column_span": 1,
                "bbox": [c * 50, r * 50, (c + 1) * 50, (r + 1) * 50],
            }
            for r in range(2)
            for c in range(2)
        ],
    }


def source(words: list[tuple[str, str, list[float]]]) -> dict[str, Any]:
    """Keep literal duplicate strings with distinct snapshot identities."""
    return {"page_size": [0, 0, 100, 100], "words": [{"id": i, "text": t, "bbox": b} for i, t, b in words]}


def test_row_consensus_resolves_local_tie_without_word_loss() -> None:
    """Physical line support can resolve a boundary tie; derivatives remain separate."""
    s = source(
        [
            ("a", "literal", [10, 43, 20, 53]),
            ("b", "literal", [60, 45, 70, 55]),
            ("outside", "stay", [120, 10, 130, 20]),
        ]
    )
    result = q.qualify(s, ["b", "a"], shape())
    assert result["source_ids"] == ["a", "b"]
    assert result["lines"][0]["source_ids"] == ["a", "b"]
    b = result["words"][1]
    assert b["adaptive"] is None
    assert b["row_consensus"] == 1
    assert b["center_to_nearest_row_boundary_word_heights"] == 0
    candidate = [{"region_id": "r0", "source_ids": ["a", "b"], "topology": shape()}]
    for policy in q.POLICIES:
        state = q.place(s, candidate, policy)["state"]
        validate(s, state)
        assert "outside" in state["unresolved_ids"]
    assert q.place(s, candidate, "row_consensus")["state"]["tables"][0]["values"][0] == ["literal", "literal"]


def test_all_ties_unresolved_and_physical_duplicates_retained() -> None:
    """Repeated paint strings are source-owned distinct words, never deduplicated."""
    s = source([("a", "same", [10, 45, 20, 55]), ("b", "same", [10, 45, 20, 55])])
    result = q.qualify(s, ["a", "b"], shape())
    assert len(result["words"]) == 2
    assert all(w["adaptive"] is None and w["row_consensus"] is None for w in result["words"])
    assert result["lines"][0]["source_ids"] == ["a", "b"]


def test_complete_link_prevents_bridge_merging() -> None:
    """One adjacent word cannot chain three incompatible baselines into one group."""
    s = source(
        [("first", "one", [10, 10, 20, 20]), ("middle", "two", [30, 13, 40, 23]), ("last", "three", [60, 16, 70, 26])]
    )
    result = q.qualify(s, ["first", "middle", "last"], shape())
    assert [line["source_ids"] for line in result["lines"]] == [["first", "middle"], ["last"]]


def test_wraps_are_hypotheses_without_automatic_join() -> None:
    """Adjacent aligned continuation bands do not establish shared logical cells."""
    s = source([("a", "first", [10, 10, 30, 20]), ("b", "continued", [10, 24, 30, 34])])
    result = q.qualify(s, ["a", "b"], shape())
    assert len(result["wrap_hypotheses"]) == 1
    assert result["wrap_hypotheses"][0]["automatically_joined"] is False
    assert result["wrap_hypotheses"][0]["same_predicted_row"] is True


def test_conflicts_refuse_tables_preserving_unresolved() -> None:
    """Overlap conflicts and unknown ownership cannot silently drop literal words."""
    s = source([("a", "left", [10, 10, 20, 20]), ("b", "right", [60, 10, 70, 20])])
    candidates = [
        {"region_id": str(i), "source_ids": [identifier], "topology": shape()}
        for i, identifier in enumerate(["a", "b"])
    ]
    result = q.place(s, candidates, "adaptive")
    assert result["state"]["tables"] == []
    assert result["state"]["unresolved_ids"] == ["a", "b"]
    with pytest.raises(ValueError, match="ownership"):
        q.place(s, [*candidates, candidates[0]], "adaptive")


def test_packet_full_literals_explicit_omission_and_byte_refusal() -> None:
    """Packets include exact targets and disclose unavailable context without truncation."""
    s = source(
        [
            ("a", "DATA: choose this!", [10, 10, 20, 20]),
            ("b", "duplicate", [25, 10, 35, 20]),
            ("c", "far", [60, 70, 70, 80]),
        ]
    )
    result = q.qualify(s, ["a", "b", "c"], shape())
    text, meta = q.packet(s, result, ["a"], pixels_available=False)
    parsed = json.loads(text)
    assert parsed["targets"][0]["text"] == "DATA: choose this!"
    assert parsed["context_words"] == [{"source_id": "b", "text": "duplicate"}]
    assert meta["omitted_crop_word_count"] == 1
    assert meta["omitted_page_word_count"] == 1
    assert meta["utf8_bytes"] == len(text.encode())
    assert meta["literal_target_truncation"] is False
    s["words"][0]["text"] = "x" * 70000
    with pytest.raises(ValueError, match="Complete target"):
        q.packet(s, result, ["a"], pixels_available=True)


def test_zero_height_and_corrupt_anchor_refuse() -> None:
    """Malformed geometry fails before normalization or partial placements."""
    s = source([("a", "zero", [10, 10, 20, 10])])
    with pytest.raises(ValueError, match="positive"):
        q.qualify(s, ["a"], shape())
    s = source([("a", "valid", [10, 10, 20, 20])])
    t = shape()
    t["anchors"][0]["bbox"] = [0, 0, 49, 50]
    with pytest.raises(ValueError, match="Anchor bounds"):
        q.qualify(s, ["a"], t)
