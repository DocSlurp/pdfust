"""Pure geometry projection, tiling and refusal tests; no model dependency."""

from typing import Any

import pytest
from bench import p003_structure_geometry as geometry


def query(label: int, box: list[float], score: float = 0.95) -> dict[str, Any]:
    """Create a finite seven-class model query without neural inference."""
    probabilities = [0.0] * 7
    probabilities[label], probabilities[6] = score, 1 - score
    return {"probabilities": probabilities, "box_cxcywh": box}


def grid() -> list[dict[str, Any]]:
    """Two row and column objects, with a table covering the full viewport."""
    return [
        query(0, [0.5, 0.5, 1, 1]),
        query(2, [0.5, 0.25, 1, 0.5]),
        query(2, [0.5, 0.75, 1, 0.5]),
        query(1, [0.25, 0.5, 0.5, 1]),
        query(1, [0.75, 0.5, 0.5, 1]),
    ]


def test_global_projection_and_atomic_grid_tiling() -> None:
    projected = geometry.project(grid(), [10, 20, 110, 220], list(geometry.LABELS), 0.5)
    candidate = geometry.topology(projected)
    assert candidate["status"] == "geometry_candidate"
    assert candidate["x_edges"] == [10, 60, 110]
    assert candidate["y_edges"] == [20, 120, 220]
    assert len(candidate["anchors"]) == 4
    assert candidate["anchors"][-1]["bbox"] == [60, 120, 110, 220]


def test_clipping_and_threshold_views_preserve_query_identity() -> None:
    queries = [query(0, [0.5, 0.5, 1.2, 1.2], 0.6), query(1, [2, 2, 0.1, 0.1])]
    low = geometry.project(queries, [0, 0, 100, 100], list(geometry.LABELS), 0.3)
    assert low["objects"][0]["clipped"]
    assert low["objects"][0]["bbox"] == [0, 0, 100, 100]
    assert low["excluded"][0]["query"] == 1
    high = geometry.project(queries, [0, 0, 100, 100], list(geometry.LABELS), 0.7)
    assert not high["objects"]


def test_rectangular_span_and_overlap_conflict_refusal() -> None:
    queries = [*grid(), query(5, [0.5, 0.25, 1, 0.5])]
    candidate = geometry.topology(geometry.project(queries, [0, 0, 100, 100], list(geometry.LABELS), 0.5))
    assert len(candidate["anchors"]) == 3
    assert candidate["anchors"][0]["column_span"] == 2
    queries.append(query(5, [0.75, 0.5, 0.5, 1]))
    refused = geometry.topology(geometry.project(queries, [0, 0, 100, 100], list(geometry.LABELS), 0.5))
    assert refused["status"] == "span_conflict"
    assert refused["conflicts"]


def test_axis_duplicate_suppression_and_missing_structure() -> None:
    queries = [*grid(), query(2, [0.5, 0.25, 1, 0.5], 0.8)]
    candidate = geometry.topology(geometry.project(queries, [0, 0, 100, 100], list(geometry.LABELS), 0.5))
    assert candidate["row_count"] == 2
    assert candidate["discarded"][0]["reason"] == "axis_overlap_suppressed"
    assert geometry.topology({"objects": []})["status"] == "no_table_object"
    incomplete = geometry.project(grid()[:2], [0, 0, 100, 100], list(geometry.LABELS), 0.5)
    assert geometry.topology(incomplete)["status"] == "shape_refused"


def test_invalid_model_contract_fails_without_partial_output() -> None:
    with pytest.raises(ValueError, match="finite model"):
        geometry.project([query(0, [0.5, 0.5, float("nan"), 1])], [0, 0, 100, 100], list(geometry.LABELS), 0.5)
    with pytest.raises(ValueError, match="viewport"):
        geometry.project(grid(), [0, 0, float("nan"), 100], list(geometry.LABELS), 0.5)
    with pytest.raises(ValueError, match="label contract"):
        geometry.project(grid(), [0, 0, 100, 100], ["alias"] * 6, 0.5)
