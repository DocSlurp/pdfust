"""Keep OCR chunk identities separate from original tokens and geometry failures."""

from pathlib import Path

import pytest
from bench.ocr_rolling import conservation, geometry_diagnostics, immutable, literal_recall


def test_original_token_recall_does_not_split_or_rewrite_source_items() -> None:
    observed = ["North depot 24 3", "Extra"]
    original = list(observed)
    result = literal_recall(["North depot", "24", "3"], observed)
    assert result["matched_tokens"] == result["expected_tokens"] == 4
    assert result["observed_tokens"] == 5
    assert observed == original
    assert literal_recall(["North"], ["north"])["recall"] == 0


def test_ocr_id_conservation_rejects_duplicate_and_missing_ownership() -> None:
    source = [{"id": "a"}, {"id": "b"}]
    alternative = {"candidates": [{"cells": [{"source_ids": ["a"]}]}], "unresolved_ids": ["b"]}
    assert conservation(source, alternative)
    alternative["unresolved_ids"] = ["a", "b"]
    assert not conservation(source, alternative)
    alternative["unresolved_ids"] = []
    assert not conservation(source, alternative)


def test_overlapping_sparse_ocr_boxes_expose_nonnegative_gap_gate() -> None:
    source = [
        {"id": "label", "bbox": [0, 0, 5, 10]},
        {"id": "value", "bbox": [10, 0, 15, 10]},
        {"id": "continuation", "bbox": [0, 8, 5, 20]},
    ]
    candidate = {
        "row_count": 2,
        "col_count": 2,
        "numeric_column_hypotheses": [1],
        "cells": [
            {"source_ids": ["label"]},
            {"source_ids": ["value"]},
            {"source_ids": ["continuation"]},
            {"source_ids": []},
        ],
    }
    assert geometry_diagnostics(source, {"candidates": [candidate]}) == {
        "sparse_nonnumeric_rows": 1,
        "negative_gap_sparse_rows": 1,
    }


def test_first_ocr_observation_cannot_be_rewritten(tmp_path: Path) -> None:
    path = tmp_path / "observed.json"
    immutable(path, {"text": "first exact chunk"})
    first = path.read_bytes()
    immutable(path, {"text": "first exact chunk"})
    with pytest.raises(ValueError, match="Frozen"):
        immutable(path, {"text": "changed chunk"})
    assert path.read_bytes() == first
