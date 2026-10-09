"""Source conservation and physical/rolling alternatives before independent scoring."""

from __future__ import annotations

import math
from collections import Counter
from copy import deepcopy

import pytest
from bench.rolling_rows import assemble, numeric


def page(*, wrap: bool = True) -> dict:
    words: list[dict[str, str | list[int]]] = []
    for row in range(4):
        y = 30 + row * 40
        for col in range(3):
            text = ("Name", "Units", "Change")[col] if row == 0 else ("North", str(row * 10), str(row))[col]
            words.append({"id": f"w{len(words)}", "text": text, "bbox": [10 + col * 100, y, 40 + col * 100, y + 10]})
        if wrap and row:
            words.append({"id": f"w{len(words)}", "text": "depot", "bbox": [12, y + 15, 40, y + 25]})
    words.append({"id": f"w{len(words)}", "text": "Footer", "bbox": [10, 400, 40, 410]})
    return {"page_size": [0, 0, 300, 500], "words": words}


@pytest.mark.parametrize("variant", ["physical", "rolling"])
def test_word_ownership_and_unresolved_footer(variant: str) -> None:
    source = page()
    result = assemble(source, variant)
    owners = [i for table in result["candidates"] for cell in table["cells"] for i in cell["source_ids"]]
    assert Counter(owners + result["unresolved_ids"]) == Counter(w["id"] for w in source["words"])
    assert result["unresolved_ids"] == [source["words"][-1]["id"]]
    assert all(cell["role"] == "unknown" for table in result["candidates"] for cell in table["cells"])


def test_rolling_joins_hanging_lines_and_retains_final_continuation() -> None:
    source = page()
    physical = assemble(source, "physical")["candidates"][0]
    rolling = assemble(source, "rolling")["candidates"][0]
    assert physical["row_count"] == 7
    assert rolling["row_count"] == 4
    assert rolling["values"][1] == ["North depot", "10", "1"]
    assert rolling["values"][-1] == ["North depot", "30", "3"]
    assert rolling["numeric_column_hypotheses"] == [1, 2]
    assert "unknown" in rolling["header_role"]


def test_complete_numeric_rows_are_never_wrapped() -> None:
    source = page(wrap=False)
    assert (
        assemble(source, "physical")["candidates"][0]["values"]
        == assemble(source, "rolling")["candidates"][0]["values"]
    )


@pytest.mark.parametrize("variant", ["physical", "rolling"])
def test_gold_family_and_existing_candidates_cannot_change_rules(variant: str) -> None:
    source = page()
    original = assemble(source, variant)
    altered = deepcopy(source)
    for key in (
        "gold",
        "family",
        "expected_document",
        "template",
        "private_target",
        "text_candidates",
        "vector_candidates",
        "id",
    ):
        altered[key] = "SECRET"
    assert assemble(altered, variant) == original


def test_insufficient_anchor_support_returns_inventory_not_table_assertion() -> None:
    source = page()
    source["words"] = source["words"][:2]
    result = assemble(source, "rolling")
    assert result["candidates"] == []
    assert result["unresolved_ids"] == ["w0", "w1"]


def test_duplicate_ids_are_refused() -> None:
    source = page()
    source["words"][1]["id"] = "w0"
    with pytest.raises(ValueError, match="Duplicate"):
        assemble(source)


@pytest.mark.parametrize(("text", "expected"), [("$1,024", True), ("(12%)", True), ("12kg", False), ("Units", False)])
def test_literal_numeric_detector(text: str, *, expected: bool) -> None:
    assert numeric(text) is expected


def test_overlap_allowance_is_bounded_and_opt_in() -> None:
    source = {"page_size": [500, 500], "words": []}
    for value in [True, -0.1, 0.51, math.inf, math.nan]:
        with pytest.raises(ValueError, match="overlap_heights"):
            assemble(source, "rolling", overlap_heights=value)
    with pytest.raises(ValueError, match="overlap_heights"):
        assemble(source, "rolling", overlap_heights="0.25")  # type: ignore[arg-type]  # intentionally invalid input
    assert assemble(source, "rolling") == assemble(source, "rolling", overlap_heights=0.0)


def test_overlap_join_applies_only_to_sparse_nonnumeric_continuations() -> None:
    source = page()
    for word in source["words"]:
        word["bbox"][3] = word["bbox"][1] + 20
    baseline = assemble(source, "rolling")["candidates"][0]
    allowed = assemble(source, "rolling", overlap_heights=0.25)["candidates"][0]
    assert baseline["row_count"] == 7
    assert allowed["row_count"] == 4
    assert assemble(source, "physical", overlap_heights=0.5) == assemble(source, "physical")
    assert len({identifier for cell in allowed["cells"] for identifier in cell["source_ids"]}) == sum(
        len(cell["source_ids"]) for cell in allowed["cells"]
    )
    for index, word in enumerate(list(source["words"])):
        if word["text"] == "depot":
            y = word["bbox"][1]
            source["words"].append({"id": f"numeric{index}", "text": "9", "bbox": [110, y, 140, y + 20]})
    numeric_rows = assemble(source, "rolling", overlap_heights=0.5)["candidates"][0]
    assert numeric_rows["row_count"] == 7
