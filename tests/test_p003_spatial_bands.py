"""Variable bands use spatial evidence without reading cell strings or labels."""

import pytest
from bench.p003_spatial_bands import derive


def test_unequal_columns_and_wrapped_physical_lines() -> None:
    words = []
    for y in (10, 22, 50, 62):
        for x0, x1 in ((10, 30), (90, 150), (155, 185)):
            words.append({"id": f"w{len(words)}", "bbox": [x0, y, x1, y + 8], "text": "ignored"})
    table = {"bbox": [0, 0, 200, 80], "row_count": 2, "col_count": 2}
    result = derive(words, table)
    assert 30 < result["x_edges"][1] < 90
    assert 30 < result["y_edges"][1] < 50
    assert result["rows"]["physical_lines_per_row"] == [2, 2]
    assert result["columns"]["method"] == "persistent_source_whitespace"
    changed = [{**word, "text": "completely different value"} for word in reversed(words)]
    assert derive(changed, table) == result


def test_explicit_fallback_and_invalid_geometry_admission() -> None:
    table = {"bbox": [0, 0, 100, 100], "row_count": 2, "col_count": 2}
    result = derive([], table)
    assert result["x_edges"] == result["y_edges"] == [0, 50, 100]
    assert "insufficient" in result["rows"]["method"]
    assert result["scores_are_probabilities"] is False
    with pytest.raises(ValueError, match="source boxes"):
        derive([{"id": "w", "bbox": [0, 0, float("nan"), 10]}], table)
