"""Official postprocessing never hides failed pages or drops fixed treatments."""

import pytest
from bench.p003_official_tatr_analysis import row_inventory


def test_failed_rows_remain_in_full_inventory() -> None:
    rows = [{"id": "a", "size": 640, "threshold": 0.5, "status": "error"},
            {"id": "b", "size": 640, "threshold": 0.5, "status": "ok"}]
    row_inventory(rows, {"a", "b"}, [640], [0.5])
    with pytest.raises(ValueError, match="inventory"):
        row_inventory(rows[1:], {"a", "b"}, [640], [0.5])


def test_duplicate_row_cannot_substitute_for_missing_treatment() -> None:
    row = {"id": "a", "size": 640, "threshold": 0.5}
    with pytest.raises(ValueError, match="inventory"):
        row_inventory([row, row], {"a"}, [640], [0.5, 0.7])
