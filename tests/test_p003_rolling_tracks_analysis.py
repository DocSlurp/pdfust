"""All fixed rolling controls include every page and explicit source refusals."""

import pytest
from bench.p003_rolling_tracks_analysis import inventory


def test_missing_refused_page_cannot_improve_denominator() -> None:
    rows = [{"id": "a", "ratio": 1.0, "key_columns": 1}]
    with pytest.raises(ValueError, match="inventory"):
        inventory(rows, {"a", "b"}, [[1.0, 1]])


def test_duplicate_page_cannot_replace_second_control() -> None:
    row = {"id": "a", "ratio": 1.0, "key_columns": 1}
    with pytest.raises(ValueError, match="inventory"):
        inventory([row, row], {"a"}, [[1.0, 1], [1.0, 2]])
