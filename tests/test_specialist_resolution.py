"""Explicit HTML structure, source-owned crops and center-ownership conservation."""

from bench.specialist_resolution import ownership, padded, parse_matrix


def test_explicit_merged_html_matrix() -> None:
    """HTML spans produce covered None slots and exact anchor positions."""
    parsed = parse_matrix('<table><tr><td colspan="2">Header</td></tr><tr><td>A</td><td>B</td></tr></table>')
    assert parsed is not None
    assert parsed["values"] == [["Header", None], ["A", "B"]]
    assert parsed["spans"][0] == {"row": 0, "column": 0, "row_span": 1, "column_span": 2}
    assert parsed["row_count"] == parsed["col_count"] == 2


def test_missing_html_not_guessed() -> None:
    """Raw retained text alone does not establish a table matrix."""
    assert parse_matrix("<p>Retained source words</p>") is None


def test_source_crop_padding_is_explicit() -> None:
    """Source-only boxes expand by the frozen amount and stay within page bounds."""
    assert padded([[10, 10, 40, 40]], [0, 0, 100, 100], 4) == [[6, 6, 44, 44]]
    assert padded([[10, 10, 40, 40]], [0, 0, 100, 100], 12) == [[0, 0, 52, 52]]


def test_predicted_cell_center_mapping_conserves_inventory() -> None:
    """Overlapping predicted cells leave ambiguous source IDs unresolved."""
    page = {"words": [{"id": "a", "bbox": [1, 1, 3, 3]}, {"id": "b", "bbox": [8, 1, 10, 3]}]}
    outputs = [{"pixel_box": [0, 0, 20, 20], "cell_boxes": [[[0, 0, 5, 5], [7, 0, 12, 5], [7, 0, 13, 6]]]}]
    result = ownership(page, outputs, (1, 1))
    assert result["conserved"]
    assert result["cells"][0]["source_ids"] == ["a"]
    assert result["unresolved_ids"] == ["b"]
