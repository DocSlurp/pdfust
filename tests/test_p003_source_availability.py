"""Literal availability bags remain separate from reference correctness and placement."""

from __future__ import annotations

from typing import Any

import pytest
from bench import p003_source_availability as a
from bench.pipeline_assembly import _clean_table
from bench.pipeline_repair import _sources


def source() -> dict[str, Any]:
    """Retain canonically equivalent duplicate words and physically distinct source IDs."""
    return {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "a", "text": " Cafe\u0301  ", "bbox": [0, 0, 10, 10]},
            {"id": "b", "text": "Café", "bbox": [0, 0, 10, 10]},
            {"id": "c", "text": "TOTAL", "bbox": [20, 0, 30, 10]},
            {"id": "d", "text": "two\twords", "bbox": [0, 20, 30, 30]},
            {"id": "e", "text": "\u2003", "bbox": [40, 20, 50, 30]},
        ],
    }


def test_nfc_whitespace_only_and_duplicate_multiplicity_preserved() -> None:
    """Availability diagnostics do not correct case, accents, punctuation or OCR."""
    page = source()
    result = a.bag(page, ["e", "d", "c", "b", "a"])
    assert result["selected_source_ids"] == ["a", "b", "c", "d", "e"]
    assert ["Café", 2] in result["normalized_word_string_bag"]
    assert ["TOTAL", 1] in result["whitespace_token_bag"]
    assert ["two", 1] in result["whitespace_token_bag"]
    assert ["words", 1] in result["whitespace_token_bag"]
    assert ["é", 2] in result["nonspace_character_bag"]
    assert result["word_count"] == 5
    assert result["normalized_empty_word_count"] == 1
    assert result["availability_score"] is None
    assert all(char != " " for char, _ in result["nonspace_character_bag"])
    assert result["literal_words"][0][1] == " Cafe\u0301  "


def test_exact_overlap_histogram_preserves_physical_duplicates() -> None:
    """Overlapping paint/source receipts are counted, not deduplicated."""
    result = a.diagnostics(source(), ["a", "b", "c", "d", "e"])
    overlap = result["source_overlap"]
    assert overlap["positive_area_pairs"] == 1
    assert overlap["words_with_any_positive_overlap"] == 2
    assert overlap["pair_iou_histogram_counts"][-1] == 1
    assert result["exact_duplicate_bbox_extra_occurrences"] == 1
    assert result["bbox_height_points"]["median"] == 10
    assert result["ocr_correctness_measured"] is False


def test_detector_union_and_actual_assigned_subset_remain_distinct() -> None:
    """Detector ownership does not imply any cell assignment or correctness."""
    page = source()
    table = {
        "row_count": 1,
        "col_count": 1,
        "cells": [{"source_ids": ["a"], "role": "unknown"}],
        "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1}],
    }
    control = {
        "id": "c0",
        "tables": [{**_clean_table(table, _sources(page)), "bbox": [0, 0, 10, 10]}],
        "unresolved_ids": ["b", "c", "d", "e"],
    }
    regions = [
        {"id": "r0", "kind": "detector_proposal", "bbox": [0, 0, 10, 10], "source_ids": ["a", "b"]},
        {"id": "r1", "kind": "detector_proposal", "bbox": [0, 0, 10, 10], "source_ids": ["b"]},
    ]
    result = a.audit(page, regions, control)
    assert result["detector_owned_word_appearances"] == 3
    assert result["detector_owned_unique_ids"] == 2
    assert result["detector_multiple_owner_extra_occurrences"] == 1
    assert result["subsets"]["geometry_control_assigned"]["bag"]["word_count"] == 1
    assert result["detector_ownership_fraction"] == 0.4
    assert result["geometry_assignment_fraction"] == 0.2
    assert result["availability_or_ceiling_score"] is None


def test_invalid_partition_and_source_ids_are_refused() -> None:
    """Bag diagnostics cannot hide missing IDs in a control or invented source evidence."""
    page = source()
    with pytest.raises(ValueError, match="bag admission"):
        a.bag(page, ["foreign"])
    with pytest.raises(ValueError, match="bag admission"):
        a.bag(page, ["a", "a"])
    with pytest.raises(ValueError, match="exactly one owner"):
        a.audit(page, [], {"id": "c0", "tables": [], "unresolved_ids": []})


def test_empty_distributions_are_explicitly_absent() -> None:
    """Unavailable sample distributions are not recorded as zero observations."""
    result = a.diagnostics(source(), [])
    assert result["bbox_height_points"]["count"] == 0
    assert result["bbox_height_points"]["median"] is None
    assert result["source_overlap"]["positive_area_pairs"] == 0
