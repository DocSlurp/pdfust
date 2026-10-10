"""Independent source fixtures for optional consensus column alternatives."""

from copy import deepcopy
from typing import Any

import pytest
from bench.pipeline_assembly import propose as baseline_propose
from bench.pipeline_assembly import validate
from bench.pipeline_column_consensus import propose


def source() -> dict[str, Any]:
    page: dict[str, Any] = {"page_size": [400, 300], "words": [], "vector_candidates": []}
    rows: list[list[tuple[str, int, int]]] = [
        [("Name", 20, 50), ("Notes", 170, 205), ("Amount", 310, 350)],
        [("Oak", 20, 45), ("dry", 168, 192), ("12", 330, 346)],
        [("Pine", 21, 50), ("wet", 169, 194)],
    ]
    for row, cells in enumerate(rows):
        for text, x0, x1 in cells:
            page["words"].append(
                {"id": f"w{len(page['words'])}", "text": text, "bbox": [x0, 30 + row * 30, x1, 40 + row * 30]}
            )
    return page


def values(candidates: list[dict[str, Any]]) -> list[list[list[str | None]]]:
    return [t["values"] for c in candidates for t in c["tables"]]


def test_sparse_column_edge_drift_gets_complete_alternative_and_keeps_prefix() -> None:
    page = source()
    existing = baseline_propose(page)
    before = deepcopy(existing)
    combined = propose(page, existing)
    assert combined[: len(existing)] == before
    assert existing == before
    assert [["Name", "Notes", "Amount"], ["Oak", "dry", "12"], ["Pine", "wet", ""]] in values(combined)
    assert [c["id"] for c in combined] == [f"c{i}" for i in range(len(combined))]
    for candidate in combined:
        validate(page, candidate)
    assert propose(page, combined) == combined


def test_aligned_prose_is_only_a_hypothesis_and_no_table_option_stays() -> None:
    page = source()
    for word in page["words"]:
        word["text"] = "Independent sentence."
    existing = baseline_propose(page)
    combined = propose(page, existing)
    assert combined[0]["tables"] == []
    assert len(combined[0]["unresolved_ids"]) == len(page["words"])
    assert any(c["tables"] for c in combined)
    assert all(cell["role"] == "unknown" for c in combined for t in c["tables"] for cell in t["cells"])


def test_missing_middle_cells_and_empty_final_cells_remain_distinct() -> None:
    page = source()
    page["words"] = [w for w in page["words"] if w["text"] not in {"dry", "wet"}]
    combined = propose(page, baseline_propose(page))
    assert [["Name", "Notes", "Amount"], ["Oak", "", "12"], ["Pine", "", ""]] in values(combined)
    for candidate in combined:
        validate(page, candidate)


def test_wrapped_continuations_and_independent_numeric_rows_have_both_alternatives() -> None:
    page = source()
    page["words"].append({"id": "tail", "text": "tail", "bbox": [169, 74, 199, 84]})
    page["words"] = [w for w in page["words"] if w["text"] != "wet"]
    combined = propose(page, baseline_propose(page))
    matrices = values(combined)
    assert [["Name", "Notes", "Amount"], ["Oak", "dry tail", "12"], ["Pine", "", ""]] in matrices
    assert any(len(matrix) == 4 for matrix in matrices)
    assert any(matrix[1][2] == "12" for matrix in matrices if len(matrix) >= 2 and len(matrix[1]) == 3)


def test_multiple_separated_regions_preserve_all_source_ids() -> None:
    page = source()
    other = deepcopy(page["words"])
    for word in other:
        word["id"] += "-other"
        word["bbox"][1] += 160
        word["bbox"][3] += 160
    page["page_size"] = [400, 500]
    page["words"].extend(other)
    combined = propose(page, baseline_propose(page))
    assert any(len(c["tables"]) == 2 and not c["unresolved_ids"] for c in combined)
    for candidate in combined:
        validate(page, candidate)


def test_extra_labels_and_annotations_cannot_change_new_candidates() -> None:
    page = source()
    existing = baseline_propose(page)
    altered = deepcopy(page)
    altered.update(gold="SECRET", family="SECRET", filename="SECRET")
    for word in altered["words"]:
        word["expected_column"] = "SECRET"
    assert propose(page, existing) == propose(altered, existing)


def test_empty_and_single_row_inputs_add_nothing() -> None:
    page: dict[str, Any] = {"page_size": [400, 300], "words": [], "vector_candidates": []}
    existing = baseline_propose(page)
    assert propose(page, existing) == existing
    page = source()
    page["words"] = page["words"][:3]
    existing = baseline_propose(page)
    assert propose(page, existing) == existing


def test_duplicate_ids_and_invalid_existing_inventory_are_refused() -> None:
    page = source()
    existing = baseline_propose(page)
    existing[0]["unresolved_ids"].append("unknown")
    with pytest.raises(ValueError, match="conservation"):
        propose(page, existing)
    page["words"].append(deepcopy(page["words"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        propose(page, [])


def test_native_grid_and_outside_caption_preserved_with_new_residual_table() -> None:
    page = source()
    boxes = [[10, 180, 60, 200], [60, 180, 110, 200], [10, 200, 60, 220], [60, 200, 110, 220]]
    page["vector_candidates"] = [
        {
            "row_count": 2,
            "col_count": 2,
            "cells": boxes,
            "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)],
        }
    ]
    for index, box in enumerate(boxes):
        page["words"].append(
            {"id": f"native-{index}", "text": f"N{index}", "bbox": [box[0] + 5, box[1] + 5, box[0] + 15, box[1] + 15]}
        )
    page["words"].append({"id": "caption", "text": "Caption", "bbox": [10, 270, 60, 280]})
    existing = baseline_propose(page)
    combined = propose(page, existing)
    native = next(c for c in existing if c["mechanism"] == "native_vector")["tables"][0]
    new = combined[len(existing) :]
    assert new
    assert all(c["tables"][0] == native for c in new)
    assert all("caption" in c["unresolved_ids"] for c in new)
    for candidate in combined:
        validate(page, candidate)


def test_right_aligned_numeric_data_use_seed_column_separators() -> None:
    page = source()
    for word in page["words"]:
        if word["text"] == "dry":
            word["text"], word["bbox"] = "91.5", [190, 60, 214, 70]
        elif word["text"] == "wet":
            word["text"], word["bbox"] = "2", [204, 90, 214, 100]
    combined = propose(page, baseline_propose(page))
    assert [["Name", "Notes", "Amount"], ["Oak", "91.5", "12"], ["Pine", "2", ""]] in values(combined)
