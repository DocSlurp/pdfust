"""Literal ownership and strict ambiguity checks without models or source PDFs."""

from copy import deepcopy
from typing import Any

import pytest
from bench.p003_structure_place import place


def fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = {"page_size": [0, 0, 100, 100], "words": [
        {"id": "a", "text": "wrapped", "bbox": [2, 2, 20, 9]},
        {"id": "b", "text": "value", "bbox": [2, 12, 20, 19]},
        {"id": "c", "text": "crossing", "bbox": [45, 60, 60, 70]},
        {"id": "d", "text": "note", "bbox": [2, 90, 20, 99]},
    ]}
    shape = {"status": "geometry_candidate", "row_count": 2, "column_count": 2,
             "bbox": [0, 0, 100, 80], "anchors": [
                 {"row": 0, "column": 0, "row_span": 1, "column_span": 2, "bbox": [0, 0, 100, 40]},
                 {"row": 1, "column": 0, "row_span": 1, "column_span": 1, "bbox": [0, 40, 50, 80]},
                 {"row": 1, "column": 1, "row_span": 1, "column_span": 1, "bbox": [50, 40, 100, 80]},
             ]}
    return source, [{"region_id": "r0", "source_ids": ["a", "b", "c"], "topology": shape}]


def test_wrapped_source_text_stays_literal_and_ambiguous_word_remains_unresolved() -> None:
    source, candidates = fixture()
    result = place(source, candidates, "overlap_margin")
    assert result["state"]["tables"][0]["values"] == [["wrapped value", None], ["", ""]]
    assert result["state"]["unresolved_ids"] == ["c", "d"]
    assert result["source_conserved"]
    assert not result["scores_are_probabilities"]


@pytest.mark.parametrize("policy", ["center", "max_overlap"])
def test_alternative_geometry_policies_assign_crossing_word_without_copying_prose(policy: str) -> None:
    source, candidates = fixture()
    result = place(source, candidates, policy)
    assert result["state"]["tables"][0]["values"][1] == ["", "crossing"]
    assert result["state"]["unresolved_ids"] == ["d"]


def test_conflicting_grids_refuse_both_and_duplicate_region_ownership_rejects() -> None:
    source, candidates = fixture()
    other = deepcopy(candidates[0])
    other.update(region_id="r1", source_ids=["d"])
    result = place(source, [*candidates, other], "center")
    assert result["state"]["tables"] == []
    assert result["state"]["unresolved_ids"] == ["a", "b", "c", "d"]
    with pytest.raises(ValueError, match="duplicated"):
        place(source, candidates * 2, "center")
