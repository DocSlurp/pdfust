"""Regional analysis admits complete fixed treatment cohorts only."""

import pytest
from bench.p003_regional_tracks_analysis import verify_rows


def test_missing_refused_page_cannot_improve_denominator() -> None:
    expected = {("page-a", 640, "fixed"), ("page-b", 640, "fixed")}
    rows = [{"id": "page-a", "size": 640, "treatment": "fixed"}]
    with pytest.raises(ValueError, match="Incomplete"):
        verify_rows(rows, expected)


def test_duplicate_page_is_not_a_repeat() -> None:
    row = {"id": "page-a", "size": 640, "treatment": "fixed"}
    with pytest.raises(ValueError, match="duplicated"):
        verify_rows([row, row], {("page-a", 640, "fixed")})


def test_exact_fixed_inventory_passes() -> None:
    verify_rows([{"id": "page-a", "size": 640, "treatment": "fixed"}], {("page-a", 640, "fixed")})
