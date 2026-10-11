"""Sparse source tracks retain headers and distinguish adjacent word owners."""
from __future__ import annotations

from copy import deepcopy

import pytest
from bench import p003_extension_headerband as repair
from bench.pipeline_repair import validate


def source() -> dict:
    words = [
        {"id": "title", "text": "Neutral", "bbox": [10, 0, 90, 12]},
        *[{"id": f"h{c}", "text": text, "bbox": [10 + c * 100, 30, 20 + c * 100, 38]}
          for c, text in enumerate(("A", "B", "C"))],
    ]
    for row in range(4):
        y = 55 + row * 25
        words.extend([
            {"id": f"a{row}", "text": "left", "bbox": [10, y, 25, y + 8]},
            {"id": f"b{row}", "text": "$10.00", "bbox": [175, y, 207, y + 8]},
            {"id": f"c{row}", "text": "right", "bbox": [211, y, 241, y + 8]},
        ])
    words.append({"id": "footer", "text": "Neutral", "bbox": [10, 250, 90, 258]})
    return {"page_size": [0, 0, 300, 300], "words": words}


def test_sparse_band_restores_header_and_splits_merged_body_fragments_by_word_ids() -> None:
    page = source()
    proposals = repair.proposals(page)
    assert proposals
    state = proposals[0]["state"]
    validate(page, state)
    table = state["tables"][0]
    assert (table["row_count"], table["col_count"]) == (5, 3)
    assert table["values"] == [["A", "B", "C"], *[["left", "$10.00", "right"] for _ in range(4)]]
    assert table["cells"][4]["source_ids"] == ["b0"]
    assert table["cells"][5]["source_ids"] == ["c0"]
    assert state["unresolved_ids"] == ["title", "footer"]


def test_proposals_ignore_labels_values_and_family_annotations() -> None:
    page = source()
    renamed = deepcopy(page)
    for index, word in enumerate(renamed["words"]):
        word["text"] = "opaque" + str(index)
    renamed["family"] = "invented-misleading-label"
    original = repair.proposals(page)[0]
    replacement = repair.proposals(renamed)[0]
    assert original["source_receipt"] == replacement["source_receipt"]
    assert original["state"]["tables"][0]["cells"] == replacement["state"]["tables"][0]["cells"]
    assert original["state"]["unresolved_ids"] == replacement["state"]["unresolved_ids"]


def test_no_sparse_band_prose_and_insufficient_body_support_abstain() -> None:
    prose = {"page_size": [0, 0, 300, 300], "words": [
        {"id": f"p{i}", "text": "paragraph", "bbox": [10, 20 + i * 25, 270, 28 + i * 25]}
        for i in range(8)
    ]}
    assert repair.proposals(prose) == []
    short = source()
    short["words"] = [w for w in short["words"] if not w["id"].endswith(("2", "3"))]
    assert repair.proposals(short) == []


def test_unknown_duplicate_or_nonfinite_source_refused_before_proposals() -> None:
    page = source()
    page["words"].append(deepcopy(page["words"][0]))
    with pytest.raises(ValueError, match="Invalid source"):
        repair.proposals(page)
    page = source()
    page["words"][0]["bbox"][0] = float("inf")
    with pytest.raises(ValueError, match="geometry"):
        repair.proposals(page)
