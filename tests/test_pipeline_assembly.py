"""Complete page assemblies conserve source ownership without label access."""

from collections import Counter
from copy import deepcopy
from typing import Any

import bench.pipeline_assembly as assembly
import pytest
from bench.pipeline_assembly import packet, propose, validate


def source() -> dict[str, Any]:
    words: list[dict[str, Any]] = [
        {"id": "w0", "text": "Category", "bbox": [10, 10, 50, 20]},
        {"id": "w1", "text": "Measure", "bbox": [110, 10, 150, 20]},
        {"id": "w2", "text": "Node", "bbox": [10, 50, 35, 60]},
        {"id": "w3", "text": "12", "bbox": [170, 50, 180, 60]},
        {"id": "w4", "text": "tail", "bbox": [10, 65, 30, 75]},
        {"id": "w5", "text": "detail", "bbox": [10, 80, 40, 90]},
        {"id": "w6", "text": "Footer", "bbox": [10, 400, 45, 410]},
    ]
    return {"page_size": [0, 0, 300, 500], "words": words, "vector_candidates": []}


def test_complete_source_conservation_and_wrapped_alternatives() -> None:
    page = source()
    candidates = propose(page)
    assert candidates[0]["mechanism"] == "none"
    matrices = [t["values"] for c in candidates for t in c["tables"]]
    assert [["Category", "Measure"], ["Node tail detail", "12"]] in matrices
    assert any(len(matrix) == 4 for matrix in matrices)
    for candidate in candidates:
        validate(page, candidate)
        ids = [i for t in candidate["tables"] for cell in t["cells"] for i in cell["source_ids"]]
        assert Counter(ids + candidate["unresolved_ids"]) == Counter(w["id"] for w in page["words"])
    assert len(packet(page, candidates)) <= 25_000


def test_ambiguous_multicolumn_prose_retains_no_table_option() -> None:
    page: dict[str, Any] = {"page_size": [300, 500], "words": [], "vector_candidates": []}
    for row in range(4):
        for column in range(2):
            page["words"].append(
                {
                    "id": f"w{row}-{column}",
                    "text": "Sentence ends.",
                    "bbox": [10 + column * 150, 20 + row * 20, 100 + column * 150, 30 + row * 20],
                }
            )
    candidates = propose(page)
    assert candidates[0]["tables"] == []
    assert len(candidates[0]["unresolved_ids"]) == 8
    assert any(c["tables"] for c in candidates)
    assert '"choice":"unresolved"' in packet(page, candidates)


def native_source() -> dict[str, Any]:
    page: dict[str, Any] = {"page_size": [300, 500], "words": [], "vector_candidates": []}
    for table in range(2):
        y = 20 + table * 200
        boxes = [[10, y, 60, y + 20], [60, y, 110, y + 20], [10, y + 20, 60, y + 40], [60, y + 20, 110, y + 40]]
        page["vector_candidates"].append(
            {
                "row_count": 2,
                "col_count": 2,
                "cells": boxes,
                "values": [["untrusted", "annotation"], ["do not", "copy"]],
                "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)],
            }
        )
        for index, box in enumerate(boxes):
            page["words"].append(
                {
                    "id": f"t{table}w{index}",
                    "text": str(index),
                    "bbox": [box[0] + 5, box[1] + 5, box[0] + 15, box[1] + 15],
                }
            )
    return page


def test_native_multiple_tables_and_mutated_annotations() -> None:
    page = native_source()
    candidates = propose(page)
    native = next(c for c in candidates if c["mechanism"] == "native_vector")
    assert len(native["tables"]) == 2
    assert all(t["values"] == [["0", "1"], ["2", "3"]] for t in native["tables"])
    changed = deepcopy(page)
    changed.update({"gold": "SECRET", "family": "SECRET", "filename": "SECRET"})
    for word in changed["words"]:
        word["expected_role"] = "SECRET"
    for table in changed["vector_candidates"]:
        table["values"] = [["SECRET"]]
        table["diagnostics"] = {"gold": "SECRET"}
    assert propose(changed) == candidates
    assert packet(changed, candidates) == packet(page, candidates)
    assert "SECRET" not in packet(changed, candidates)


def test_duplicate_input_and_duplicate_state_are_refused() -> None:
    page = source()
    state = propose(page)[0]
    state["unresolved_ids"].append("w0")
    with pytest.raises(ValueError, match="conservation"):
        validate(page, state)
    page["words"].append(page["words"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        propose(page)


def test_fabricated_values_and_partial_context_are_refused() -> None:
    page = native_source()
    candidates = propose(page)
    candidates[1]["tables"][0]["values"][0][0] = "invented"
    with pytest.raises(ValueError, match="owned source"):
        packet(page, candidates)
    with pytest.raises(ValueError, match="full-page"):
        packet(source(), propose(source()), context_style="selected")
    huge = source()
    huge["words"][0]["text"] = "x" * 16_001
    with pytest.raises(ValueError, match="no truncation"):
        propose(huge)


def test_empty_page_is_a_complete_no_table_alternative() -> None:
    page: dict[str, Any] = {"page_size": [300, 500], "words": [], "vector_candidates": []}
    assert propose(page) == [
        {
            "id": "c0",
            "tables": [],
            "unresolved_ids": [],
            "description": "No table admission; retain all source words as unresolved prose or other content.",
            "mechanism": "none",
        }
    ]


def test_separated_text_tables_can_coexist_in_one_complete_assembly() -> None:
    page: dict[str, Any] = {"page_size": [300, 500], "words": [], "vector_candidates": []}
    for block in range(2):
        for row in range(3):
            for column in range(2):
                x, y = 10 + column * 150, 20 + block * 200 + row * 20
                page["words"].append(
                    {"id": f"w{block}{row}{column}", "text": str(row + column), "bbox": [x, y, x + 20, y + 10]}
                )
    candidates = propose(page)
    assert any(len(c["tables"]) == 2 and not c["unresolved_ids"] for c in candidates)
    for candidate in candidates:
        validate(page, candidate)


def test_complete_packet_overflow_is_refused() -> None:
    page = source()
    page["words"][0]["text"] = "x" * 8000
    candidates = propose(page)
    with pytest.raises(ValueError, match="no partial context"):
        packet(page, candidates)


def test_native_merged_covered_slots_are_none_but_empty_cells_are_strings() -> None:
    page = native_source()
    page["vector_candidates"] = page["vector_candidates"][:1]
    page["words"] = page["words"][:4]
    vector = page["vector_candidates"][0]
    vector["cells"][0] = [10, 20, 110, 40]
    vector["cells"][1] = None
    vector["spans"] = [
        {"row": 0, "column": 0, "row_span": 1, "column_span": 2},
        {"row": 1, "column": 0, "row_span": 1, "column_span": 1},
        {"row": 1, "column": 1, "row_span": 1, "column_span": 1},
    ]
    page["words"] = page["words"][:3]
    native = next(c for c in propose(page) if c["mechanism"] == "native_vector")
    assert native["tables"][0]["values"] == [["0 1", None], ["2", ""]]
    assert native["tables"][0]["cells"][1]["source_ids"] == []
    validate(page, native)
    changed = deepcopy(native)
    changed["tables"][0]["values"][0][1] = ""
    with pytest.raises(ValueError, match="owned source"):
        validate(page, changed)


def test_native_state_avoids_heuristic_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(*_args: object, **_kwargs: object) -> None:
        message = "Heuristic proposal called"
        raise AssertionError(message)

    monkeypatch.setattr(assembly, "topology_propose", unexpected)
    monkeypatch.setattr(assembly, "assemble", unexpected)
    page = native_source()
    state = assembly.native_state(page)
    assert len(state["tables"]) == 2
    validate(page, state)
    empty = assembly.native_state(source())
    assert empty["mechanism"] == "none"
    assert len(empty["unresolved_ids"]) == len(source()["words"])


@pytest.mark.parametrize("pathology", ["duplicate", "overlap", "incomplete"])
def test_span_pathologies_are_rejected(pathology: str) -> None:
    page = native_source()
    state = propose(page)[1]
    spans = state["tables"][0]["spans"]
    if pathology == "duplicate":
        spans.append(dict(spans[0]))
    elif pathology == "overlap":
        spans[0]["column_span"] = 2
    else:
        spans.pop()
    with pytest.raises(ValueError, match=r"span|Spans"):
        validate(page, state)
