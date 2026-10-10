"""Full-page acquisition controls preserve source ownership and report refusals."""
from __future__ import annotations

import pytest
from bench import p003_fullsource_tracks as tracks


def test_sweep_counts_distinct_lines_and_respects_open_gaps() -> None:
    gaps = [(0.0, 10.0, "a"), (1.0, 9.0, "a"), (3.0, 5.0, "b"), (5.0, 8.0, "c")]
    result = tracks.gutter_intervals(gaps, 2)
    assert result == [
        {"left": 3.0, "right": 5.0, "support": ["a", "b"]},
        {"left": 5.0, "right": 8.0, "support": ["a", "c"]},
    ]


def test_full_source_grid_preserves_repeated_strings_and_crossing_words() -> None:
    source = {"page_size": [0, 0, 200, 200], "words": [
        {"id": f"w{row * 2 + col}", "text": "same", "bbox": [10 + 90 * col, 10 + row * 20,
                                                                  40 + 90 * col, 20 + row * 20]}
        for row in range(3) for col in range(2)
    ]}
    source["words"].extend([
        {"id": "w6", "text": "crossing", "bbox": [10, 70, 130, 80]},
        {"id": "w7", "text": "outside", "bbox": [210, 10, 240, 20]},
    ])
    frozen = tracks.physical(source)
    plan = tracks.prepare(source, frozen, 0.5, 0.5)
    state = tracks.decode(source, plan)
    assert state["tables"][0]["row_count"] == 4
    assert state["tables"][0]["col_count"] == 2
    owned = [i for t in state["tables"] for cell in t["cells"] for i in cell["source_ids"]]
    assert len(owned) == len(set(owned)) == 6
    assert state["unresolved_ids"] == ["w6", "w7"]
    assert frozen["excluded_ids"] == ["w7"]
    source["words"][0]["text"] = "changed"
    with pytest.raises(ValueError, match="changed"):
        tracks.prepare(source, frozen, 0.5, 0.5)


def test_single_column_is_refusal_not_an_invented_table() -> None:
    source = {"page_size": [0, 0, 200, 200], "words": [
        {"id": "w0", "text": "prose", "bbox": [10, 10, 50, 20]},
    ]}
    plan = tracks.prepare(source, tracks.physical(source), 1.0, 0.25)
    assert plan["status"] == "no_candidate_refusal"
    assert tracks.decode(source, plan)["unresolved_ids"] == ["w0"]
