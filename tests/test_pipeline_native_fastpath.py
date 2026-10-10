"""Structural proof tests; no detector worker or inference is started."""

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.pipeline_assembly import native_state
from bench.pipeline_layout_detector import detector_regions
from bench.pipeline_native_fastpath import audit, native_fastpath
from bench.pipeline_regions import compose


def grid(*, merged: bool = False) -> dict[str, Any]:
    cells: list[list[float] | None] = [[10, 10, 50, 30], [50, 10, 90, 30], [10, 30, 50, 50], [50, 30, 90, 50]]
    spans = [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)]
    if merged:
        cells[0] = [10, 10, 90, 30]
        cells[1] = None
        spans = [{"row": 0, "column": 0, "row_span": 1, "column_span": 2}, *spans[2:]]
    words = [
        {"id": str(i), "text": f"literal{i}", "bbox": [b[0] + 1, b[1] + 1, b[0] + 10, b[1] + 10]}
        for i, b in enumerate(cells)
        if b is not None
    ]
    return {
        "page_size": [200, 200],
        "words": words,
        "vector_candidates": [{"row_count": 2, "col_count": 2, "cells": cells, "spans": spans}],
    }


def test_native_complete_equivalent_for_arbitrary_cached_detector_boxes() -> None:
    source = grid()
    before = deepcopy(source)
    fast = native_fastpath(source, source_id_only=True)
    assert fast["eligible"] is True
    detections = [
        {"label": "Table", "confidence": 0.99, "bbox": [0, 0, 200, 200]},
        {"label": "Table", "confidence": 0.9, "bbox": [5, 5, 70, 70]},
        {"label": "Text", "confidence": 0.95, "bbox": [10, 10, 50, 50]},
    ]
    baseline = detector_regions(source, detections)
    assert source == before
    assert fast["plan"]["regions"] == baseline["regions"]
    assert fast["plan"]["words"] == baseline["words"]
    assert fast["plan"]["detector_diagnostics"]["table_proposals"] == 0
    assert baseline["detector_diagnostics"]["empty_table_proposals"] == 2
    states = {r["id"]: native_state(r["source"]) for r in fast["plan"]["regions"]}
    assert compose(fast["plan"], states) == compose(baseline, states)


def test_one_outside_word_prevents_skip() -> None:
    source = grid()
    source["words"].append({"id": "outside", "text": "caption", "bbox": [10, 90, 30, 100]})
    proof = native_fastpath(source, source_id_only=True)
    assert proof["eligible"] is False
    assert proof["residual_ids"] == ["outside"]
    assert proof["plan"] is None


def test_mixed_native_borderless_region_prevents_skip() -> None:
    source = grid()
    source["words"].extend(
        {"id": f"b{r}{c}", "text": str(r + c), "bbox": [10 + 50 * c, 80 + 20 * r, 30 + 50 * c, 90 + 20 * r]}
        for r in range(3)
        for c in range(2)
    )
    proof = native_fastpath(source, source_id_only=True)
    assert proof["eligible"] is False
    assert len(proof["residual_ids"]) == 6


def test_invalid_vector_has_no_successful_skip_proof() -> None:
    source = grid()
    source["vector_candidates"][0]["spans"][0]["row_span"] = 5
    result = native_fastpath(source, source_id_only=True)
    assert result["eligible"] is False
    assert result["reason"] == "invalid_source_or_native_layout"


def test_merged_cells_preserve_literal_ownership() -> None:
    source = grid(merged=True)
    result = native_fastpath(source, source_id_only=True)
    assert result["eligible"] is True
    assert Counter(i for r in result["plan"]["regions"] for i in r["source_ids"]) == Counter(
        w["id"] for w in source["words"]
    )
    region = result["plan"]["regions"][0]
    assert native_state(region["source"])["tables"][0]["values"][0][1] is None


def test_zero_words_never_skips_even_with_empty_native_grid() -> None:
    source = grid()
    source["words"] = []
    result = native_fastpath(source, source_id_only=True)
    assert result["eligible"] is False
    assert result["reason"] == "zero_source_words"


def test_image_transcription_scope_never_skips() -> None:
    result = native_fastpath(grid())
    assert result == {"eligible": False, "reason": "source_id_scope_required", "plan": None}


def test_retained_profile_keeps_nested_metrics_and_memory_separate(tmp_path: Path) -> None:
    source = grid()
    run = tmp_path / "run"
    run.mkdir()
    frozen = {"records": [{"id": "a"}, {"id": "b"}], "config": {"region_words": 512, "region_characters": 8000}}
    (run / "frozen.json").write_text(json.dumps(frozen))
    a = {
        "status": "ok",
        "source": source,
        "wall_seconds": 9,
        "cpu_seconds": 7,
        "stages": {"source_seconds": 2},
        "ocr": {"wall_seconds": 1},
        "layout_detector": {
            "boxes": [{"label": "Table", "confidence": 0.9, "bbox": [0, 0, 200, 200]}],
            "parent_wall_seconds": 3,
            "parent_cpu_seconds": 0.5,
            "metrics": {"wall_seconds": 2, "cpu_seconds": 4, "peak_sampled_rss_bytes": 100},
        },
        "calls": [{"client_wall_seconds": 1, "client_cpu_seconds": 0.1}],
    }
    (run / "a-result.json").write_text(json.dumps(a))
    with pytest.raises(ValueError, match="completed report"):
        audit(run, tmp_path / "output")
    (run / "b-result.json").write_text(
        json.dumps({"status": "unsupported_no_text", "wall_seconds": 1, "cpu_seconds": 0.5, "calls": []})
    )
    (run / "report.json").write_text(json.dumps({"metrics": {"wall_seconds": 10, "peak_sampled_rss_bytes": 50}}))
    report = audit(run, tmp_path / "output")
    assert report["complete"] is True
    assert report["eligible_pages"] == 1
    assert report["pages"][0]["cached_region_equivalence"] is True
    timings = report["timing_summary"]
    assert timings["total_parent_wall"]["sum"] == 10
    assert timings["other_or_uninstrumented_parent_wall"]["sum"] == 4
    assert timings["detector_worker_wall_nested"]["sum"] == 2
    assert timings["detector_worker_sampled_rss"]["sum"] is None
    assert timings["detector_worker_sampled_rss"]["maximum"] == 100
    assert report["eligible_retained_upper_bounds"]["detector_parent_wall_including_worker"]["sum"] == 3
