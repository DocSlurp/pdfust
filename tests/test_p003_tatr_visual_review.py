"""Reject changed strict scores and ambiguous source ownership in TATR diagnostics."""

from typing import Any

import pytest
from bench.generalization_scoring import score_page
from bench.p003_tatr_visual_review import source_word_verdicts, verify_page


def test_retained_strict_score_must_replay_before_rendering() -> None:
    table: dict[str, Any] = {"row_count": 1, "col_count": 1, "values": [["A"]], "spans": []}
    target: dict[str, Any] = {"tables": [table]}
    score = {**score_page(target, [table]), "strict_exact_cells": 1}
    assert verify_page(target, [table], score)["input_tables"] == {0: "success"}
    score["strict_exact_cells"] = 0
    with pytest.raises(ValueError, match="Independent strict"):
        verify_page(target, [table], score)


def test_owned_word_conflicts_remain_amber() -> None:
    table: dict[str, Any] = {
        "row_count": 1, "col_count": 2,
        "cells": [{"source_ids": ["w1", "w2"]}, {"source_ids": ["w1", "w3"]}],
    }
    marks: dict[str, Any] = {"output_cells": {0: {(0, 0, 1, 1): "success", (0, 1, 1, 1): "failure"}}}
    assert source_word_verdicts([table], marks) == {"w1": "unscored", "w2": "success", "w3": "failure"}
    table["cells"].pop()
    with pytest.raises(ValueError, match="row-major"):
        source_word_verdicts([table], marks)
