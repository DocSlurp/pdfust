"""Pure CPU hybrid composition tests; no model calls or references."""

from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_assembly import native_state
from bench.pipeline_hybrid_composition import (
    compose,
    exclude_native_proposals,
    markdown,
    native_boxes,
    sanitize_vectors,
)
from bench.pipeline_run import markdown as baseline_markdown
from bench.pipeline_vision_transcription import _canonical


def source() -> dict[str, Any]:
    return {
        "page_size": [200, 200],
        "words": [
            {"id": "heading", "text": "<Heading>", "bbox": [5, 2, 50, 8]},
            {"id": "a", "text": "literal native", "bbox": [12, 12, 25, 17]},
            {"id": "inside", "text": "OCR misstake", "bbox": [12, 82, 35, 88]},
            {"id": "crossing", "text": "cross & keep", "bbox": [45, 88, 60, 94]},
            {"id": "footer", "text": "Footer", "bbox": [2, 180, 30, 185]},
        ],
        "vector_candidates": [
            {
                "row_count": 2,
                "col_count": 2,
                "bbox": [10, 10, 50, 50],
                "cells": [[10, 10, 30, 30], [30, 10, 50, 30], [10, 30, 30, 50], [30, 30, 50, 50]],
                "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)],
            }
        ],
    }


def transcription(bbox: list[float] | None = None) -> dict[str, Any]:
    table, _, _ = _canonical(
        {"bbox": [0, 0, 1000, 1000], "matrix": [["<script>& | exact\ntext", ""]], "mergedspans": [[0, 0, 1, 2]]},
        (0, 0, 200, 200),
    )
    table["bbox"] = bbox if bbox is not None else [10, 80, 50, 100]
    return {"tables": [table], "text_provenance": "model-transcribed", "source_conserved": False}


def test_mixed_composition_partitions_all_source_and_keeps_crossing_prose() -> None:
    page = source()
    state = native_state(page)
    transcribed = transcription()
    before = deepcopy((page, state, transcribed))
    result = compose(page, state, transcribed)
    assert (page, state, transcribed) == before
    assert result["status"] == "ok"
    assert result["superseded_ids"] == ["inside"]
    assert result["unresolved_ids"] == ["heading", "crossing", "footer"]
    assert result["source_conserved"] is False
    assert result["accounting_complete"] is True
    assert result["tables"][0]["text_provenance"] == "native-source"
    assert result["tables"][1] == transcribed["tables"][0]
    assert [e["owner"] for e in result["source_ledger"]] == ["prose", "native", "superseded", "prose", "prose"]
    assert [e["id"] for e in result["source_ledger"]] == [w["id"] for w in page["words"]]
    text = markdown(result)
    assert "OCR misstake" not in text
    assert "cross &amp; keep" in text
    assert "&lt;script&gt;&amp; | exact<br>text" in text
    assert text.index("&lt;Heading&gt;") < text.index("literal native") < text.index("exact<br>") < text.index("Footer")


def test_zero_transcription_matches_existing_baseline_exactly() -> None:
    page = source()
    page["words"][0]["line"] = [1, 1]
    state = native_state(page)
    empty = {"tables": [], "text_provenance": "model-transcribed", "source_conserved": False}
    result = compose(page, state, empty)
    assert markdown(result) == baseline_markdown(page, state)
    assert result["source_conserved"] is True
    assert result["superseded_ids"] == []


def test_runtime_text_bbox_cannot_shrink_full_native_grid() -> None:
    page = source()
    state = native_state(page)
    state["tables"][0]["bbox"] = page["words"][1]["bbox"]
    assert native_boxes(page, state) == [[10, 10, 50, 50]]
    result = compose(page, state, transcription([40, 40, 60, 60]))
    assert result["status"] == "abstained"
    assert "overlaps native" in result["diagnostics"][0]["detail"]
    assert result["markdown"] is None
    assert result["tables"] == []
    assert result["accounting_complete"] is False
    assert result["diagnostic_baseline"]["diagnostic_only"] is True
    with pytest.raises(ValueError, match="complete successful"):
        markdown(result)


@pytest.mark.parametrize("kind", ["overlap", "outside", "nonfinite", "literal", "provenance"])
def test_transcription_failure_is_page_atomic(kind: str) -> None:
    page = source()
    transcribed = transcription()
    if kind == "overlap":
        transcribed["tables"].append(deepcopy(transcribed["tables"][0]))
    elif kind == "outside":
        transcribed["tables"][0]["bbox"] = [190, 190, 210, 210]
    elif kind == "nonfinite":
        transcribed["tables"][0]["bbox"][0] = float("nan")
    elif kind == "literal":
        transcribed["tables"][0]["values"][0][0] = 3
    else:
        transcribed["text_provenance"] = "source-owned"
    result = compose(page, native_state(page), transcribed)
    assert result["status"] == "abstained"
    assert result["tables"] == []
    assert result["source_ledger"] == []
    assert result["diagnostic_baseline"]["source_conserved"] is True


def test_native_exclusion_preserves_raw_response_and_other_classes() -> None:
    detection: dict[str, Any] = {
        "boxes": [
            {"label": "Table", "bbox": [40, 40, 80, 80], "confidence": 0.9},
            {"label": "Table", "bbox": [50, 10, 90, 50], "confidence": 0.8},
            {"label": "Picture", "bbox": [15, 15, 45, 45], "confidence": 0.8},
        ],
        "worker": {"cpu": 1},
    }
    before = deepcopy(detection)
    filtered, diagnostics = exclude_native_proposals(detection, [[10, 10, 50, 50]])
    assert detection == before
    assert filtered["boxes"] == detection["boxes"][1:]
    assert diagnostics[0]["proposal"] == detection["boxes"][0]
    assert diagnostics[0]["coverage_uncertain"] is True
    assert filtered["worker"] == detection["worker"]


def test_sanitize_ignores_gold_and_annotations_without_mutating_source() -> None:
    page = source()
    page["gold"] = "must not leak"
    page["vector_candidates"][0]["values"] = [["annotation"]]
    page["vector_candidates"][0]["diagnostics"] = {"label": "must not leak"}
    clean = sanitize_vectors(page)
    assert "gold" not in clean
    assert "values" not in clean["vector_candidates"][0]
    assert "diagnostics" not in clean["vector_candidates"][0]
    assert "gold" in page


def test_complete_large_source_does_not_apply_legacy_packet_limit() -> None:
    page: dict[str, Any] = {
        "page_size": [200, 200],
        "words": [{"id": str(i), "text": "retained source", "bbox": [1, 1, 2, 2]} for i in range(5000)],
        "vector_candidates": [],
    }
    state = {"tables": [], "unresolved_ids": [w["id"] for w in page["words"]]}
    result = compose(page, state, {"tables": [], "text_provenance": "model-transcribed", "source_conserved": False})
    assert result["status"] == "ok"
    assert len(result["source_ledger"]) == 5000
    assert result["markdown"].count("retained source") == 5000


def test_invalid_native_inventory_refuses_before_output() -> None:
    page = source()
    state = native_state(page)
    state["unresolved_ids"].append("inside")
    with pytest.raises(ValueError, match="ownership"):
        compose(page, state, transcription())


@pytest.mark.parametrize("kind", ["slots", "tables", "geometry"])
def test_native_and_hybrid_budgets_are_atomic(kind: str) -> None:
    page = source()
    state = native_state(page)
    if kind == "geometry":
        page["vector_candidates"][0]["cells"] = [[1, 1, 2, 2]] * 4097
        with pytest.raises(ValueError, match="geometry inventory"):
            sanitize_vectors(page)
        return
    transcribed = transcription()
    if kind == "tables":
        transcribed["tables"] *= 32
    else:
        table, _, _ = _canonical(
            {"bbox": [0, 0, 1000, 1000], "matrix": [[""] * 64 for _ in range(64)], "mergedspans": []}, (10, 80, 50, 100)
        )
        transcribed["tables"] = [table]
    result = compose(page, state, transcribed)
    assert result["status"] == "abstained"
    assert "aggregate" in result["diagnostics"][0]["detail"]
