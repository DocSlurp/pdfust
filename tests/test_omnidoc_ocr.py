"""Post-OCR spatial scoring must not imply full reading-order accuracy."""

import pytest
from bench.omnidoc_ocr import normalized_counter, score_blocks


def block(category: str, text: str, bounds: list[int], *, ignore: bool = False) -> dict:
    """Build a small annotation polygon for scorer checks."""
    x0, y0, x1, y1 = bounds
    return {"category_type": category, "text": text, "ignore": ignore, "poly": [x0, y0, x1, y0, x1, y1, x0, y1]}


def test_spatial_assignment_does_not_duplicate_overlapping_blocks() -> None:
    annotation = {
        "layout_dets": [
            block("text_block", "AB", [0, 0, 40, 40]),
            block("text_block", "A", [10, 10, 20, 20]),
            block("text_block", "ignored", [40, 40, 50, 50], ignore=True),
            block("table", "table text", [0, 0, 40, 40]),
            block("equation_isolated", "math", [0, 0, 40, 40]),
        ]
    }
    score = score_blocks(
        annotation,
        [
            {"source_bbox": [14, 14, 16, 16], "text": "A"},
            {"source_bbox": [44, 44, 46, 46], "text": "ignored"},
        ],
    )
    assert score["text_blocks"] == 2
    assert score["spatially_covered_text_blocks"] == 1
    assert score["unassigned_words"] == 1
    assert score["character_bags"]["strict"]["character_bag_recall"] == pytest.approx(1 / 3)
    assert score["excluded_formula_blocks"] == score["excluded_table_blocks"] == 1


def test_markup_exclusion_and_nfkc_are_explicit() -> None:
    annotation = {
        "layout_dets": [
            block("text_block", "Ａ", [0, 0, 10, 10]),
            block("text_block", "$x$", [20, 20, 30, 30]),
        ]
    }
    score = score_blocks(
        annotation,
        [
            {"source_bbox": [1, 1, 2, 2], "text": "A"},
            {"source_bbox": [21, 21, 22, 22], "text": "wrong math"},
        ],
    )
    assert score["spatially_covered_text_blocks"] == 2
    assert score["character_bags"]["strict"]["plain_text_blocks"] == 1
    assert score["character_bags"]["strict"]["character_bag_recall"] == 0
    assert score["character_bags"]["nfkc"]["character_bag_recall"] == 1
    assert normalized_counter(" A\nＡ", nfkc=True).total() == 2
