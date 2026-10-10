"""Retained structure probabilities must correspond to complete raw model logits."""

import pytest
from bench.p003_yolo_structure_analysis import CLASSES, QUERIES, validate_logits


def test_raw_logits_bind_complete_class_probabilities() -> None:
    value = {
        "raw_logits": [[0.0] * CLASSES for _ in range(QUERIES)],
        "queries": [{"probabilities": [1 / CLASSES] * CLASSES} for _ in range(QUERIES)],
    }
    validate_logits(value)
    value["queries"][0]["probabilities"][0] += 0.01
    with pytest.raises(ValueError, match="probabilities"):
        validate_logits(value)


def test_missing_model_queries_are_not_silently_ignored() -> None:
    with pytest.raises(ValueError, match="inventory"):
        validate_logits({"raw_logits": [], "queries": []})


def test_nonfinite_logits_are_rejected() -> None:
    value = {
        "raw_logits": [[0.0] * CLASSES for _ in range(QUERIES)],
        "queries": [{"probabilities": [1 / CLASSES] * CLASSES} for _ in range(QUERIES)],
    }
    value["raw_logits"][0][0] = float("nan")
    with pytest.raises(ValueError, match="logits"):
        validate_logits(value)
