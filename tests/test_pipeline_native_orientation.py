"""Generated merged/multiline grid metamorphisms without corpus annotations."""

from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_assembly import native_state
from bench.pipeline_hybrid_composition import native_boxes
from bench.pipeline_native_orientation import SPEC, compose, evidence
from bench.pipeline_run import source
from bench.pipeline_vision_transcription import _canonical
from conftest import build_raw_pdf

import pylopdf


def grid(*, counterrotate: bool = False, heading: bool = False) -> bytes:
    stream = (
        "q 0 G 1 w 40 260 m 300 260 l 40 220 m 300 220 l 40 180 m 300 180 l "
        "40 140 m 300 140 l 40 140 m 40 260 l 300 140 m 300 260 l 170 140 m 170 220 l S Q\n"
        "BT /F1 12 Tf 50 235 Td (Merged heading) Tj ET\n"
        "BT /F1 12 Tf 50 200 Td (Alpha one) Tj ET\n"
        "BT /F1 12 Tf 50 185 Td (continuation) Tj ET\n"
        "BT /F1 12 Tf 180 200 Td (42) Tj ET\n"
        "BT /F1 12 Tf 50 155 Td (Beta) Tj ET\n"
        "BT /F1 12 Tf 180 155 Td (99) Tj ET"
    )
    if counterrotate:
        stream = "q 0 1 -1 0 360 0 cm\n" + stream + "\nQ"
    if heading:
        stream += "\nq 0 1 -1 0 350 10 cm BT /F1 12 Tf 0 0 Td (Outside heading with different direction) Tj ET Q"
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: (
                "<< /Type /Pages /Kids [4 0 R] /Count 1 /MediaBox [0 0 360 360] "
                "/Resources << /Font << /F1 3 0 R >> >> >>"
            ),
            3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            4: "<< /Type /Page /Parent 2 0 R /Contents 5 0 R >>",
            5: f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        }
    )


def project(rotation: int, *, cropped: bool = False, counterrotate: bool = False, heading: bool = False) -> tuple:
    with pylopdf.open(stream=grid(counterrotate=counterrotate, heading=heading)) as document:
        page = document[0]
        if cropped:
            page.set_cropbox((20, 20, 340, 340))
        page.set_rotation(rotation)
        snapshot = source(page)
        state = native_state(snapshot)
        boxes = native_boxes(snapshot, state)
        directions = evidence(page, boxes)
        before = deepcopy((snapshot, state, boxes))
        result = compose(
            snapshot,
            state,
            {"tables": [], "text_provenance": "model-transcribed", "source_conserved": False},
            directions,
        )
        assert (snapshot, state, boxes) == before
        assert result["source_ledger"] == [
            {
                "id": w["id"],
                "owner": "native" if w["id"] not in state["unresolved_ids"] else "prose",
                "table_index": None if w["id"] in state["unresolved_ids"] else 0,
            }
            for w in snapshot["words"]
        ]
        assert [t["bbox"] for t in result["tables"]] == boxes
        return result, directions, document.to_markdown()


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("cropped", [False, True])
def test_logical_merged_multiline_grid_is_rotation_and_crop_invariant(rotation: int, *, cropped: bool) -> None:
    reference, _, _ = project(0)
    result, directions, core_markdown = project(rotation, cropped=cropped)
    assert result["status"] == "ok"
    assert result["tables"][0]["values"] == reference["tables"][0]["values"]
    assert result["tables"][0]["spans"] == reference["tables"][0]["spans"]
    assert result["tables"][0]["row_count"] == 3
    assert result["tables"][0]["col_count"] == 2
    assert result["tables"][0]["values"][1][0] == "Alpha one continuation"
    assert directions["tables"][0]["direction"] == ("right", "down", "left", "up")[rotation // 90]
    assert "Merged heading" in core_markdown


def test_counterrotated_content_uses_actual_baselines_and_ignores_other_heading() -> None:
    reference, _, _ = project(0)
    result, directions, _ = project(90, cropped=True, counterrotate=True, heading=True)
    assert directions["original_rotation"] == 90
    assert directions["tables"][0]["direction"] == "right"
    assert directions["tables"][0]["scope"] == "table"
    assert result["tables"][0]["values"] == reference["tables"][0]["values"]
    assert result["tables"][0]["spans"] == reference["tables"][0]["spans"]


def test_model_tables_and_source_partition_are_preserved() -> None:
    snapshot: dict[str, Any] = {
        "page_size": [200, 200],
        "vector_candidates": [],
        "words": [{"id": "a", "text": "native prose", "bbox": [1, 1, 20, 10]}],
    }
    state = native_state(snapshot)
    table, _, _ = _canonical(
        {"bbox": [0, 0, 1000, 1000], "matrix": [["model literal"]], "mergedspans": []}, (50, 50, 100, 100)
    )
    direction = {"spec": SPEC, "viewport": [0, 0, 200, 200], "original_rotation": 0, "tables": []}
    result = compose(
        snapshot,
        state,
        {"tables": [table], "text_provenance": "model-transcribed", "source_conserved": False},
        direction,
    )
    assert result["tables"] == [table]
    assert result["unresolved_ids"] == ["a"]
    assert result["superseded_ids"] == []
