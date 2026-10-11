"""Pin literal diagnostic evidence without reinterpreting it as semantic quality."""

import pytest
from bench.p003_secondary_visual_review import witness_changes


def test_literal_space_is_exposed_without_removing_numeric_boundaries() -> None:
    cell = {
        "reference_text": "12",
        "prediction_text": "1 2",
        "character_witness": [
            {"operation": "equal", "reference_index": 0, "prediction_index": 0},
            {"operation": "extra", "reference_index": None, "prediction_index": 1},
            {"operation": "equal", "reference_index": 1, "prediction_index": 2},
        ],
    }
    assert witness_changes(cell) == [{"operation": "extra", "reference": None, "prediction": " "}]


def test_false_equality_witness_is_rejected() -> None:
    with pytest.raises(ValueError, match="contradicts"):
        witness_changes(
            {
                "reference_text": "4",
                "prediction_text": "3",
                "character_witness": [
                    {"operation": "equal", "reference_index": 0, "prediction_index": 0},
                ],
            }
        )


def test_missing_and_substituted_characters_remain_literal() -> None:
    cell = {
        "reference_text": "23",
        "prediction_text": "4",
        "character_witness": [
            {"operation": "substitute", "reference_index": 0, "prediction_index": 0},
            {"operation": "missing", "reference_index": 1, "prediction_index": None},
        ],
    }
    assert witness_changes(cell) == [
        {"operation": "substitute", "reference": "2", "prediction": "4"},
        {"operation": "missing", "reference": "3", "prediction": None},
    ]
