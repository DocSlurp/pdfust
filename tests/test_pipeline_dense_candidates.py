"""Raster rule hypotheses preserve physical cells without semantic acceptance."""

from typing import Any

import pytest
from bench.pipeline_assembly import validate
from bench.pipeline_dense_candidates import propose, raster_vectors
from PIL import Image, ImageDraw, ImageOps


def grid(rows: int, columns: int) -> Image.Image:
    image = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(image)
    for row in range(rows + 1):
        y = 40 + row * 300 / rows
        draw.line((40, y, 340, y), fill="black", width=2)
    for column in range(columns + 1):
        x = 40 + column * 300 / columns
        draw.line((x, 40, x, 340), fill="black", width=2)
    return image


@pytest.mark.parametrize(("rows", "columns"), [(1, 2), (2, 1), (3, 4)])
def test_complete_physical_grids_and_global_display_mapping(rows: int, columns: int) -> None:
    vectors = raster_vectors(grid(rows, columns), [100, 200, 900, 1000])
    assert len(vectors) == 1
    assert (vectors[0]["row_count"], vectors[0]["col_count"]) == (rows, columns)
    assert len(vectors[0]["spans"]) == rows * columns
    assert vectors[0]["bbox"] == pytest.approx([181, 281, 781, 881], abs=2)


def test_missing_internal_divider_proposes_rectangular_merged_cell() -> None:
    image = grid(2, 2)
    ImageDraw.Draw(image).rectangle((189, 42, 192, 188), fill="white")
    vectors = raster_vectors(image, [0, 0, 400, 400])
    assert len(vectors) == 1
    assert {"row": 0, "column": 0, "row_span": 1, "column_span": 2} in vectors[0]["spans"]
    assert vectors[0]["cells"][1] is None


def test_open_grid_and_negative_line_art_controls() -> None:
    image = grid(2, 2)
    ImageDraw.Draw(image).rectangle((335, 30, 345, 350), fill="white")
    assert raster_vectors(image, [0, 0, 400, 400]) == []
    for kind in ("underline", "axes", "rectangle", "filled", "diagonals"):
        image = Image.new("RGB", (400, 400), "white")
        draw = ImageDraw.Draw(image)
        if kind == "underline":
            draw.line((40, 40, 340, 40), fill="black", width=2)
        elif kind == "axes":
            draw.line((40, 40, 40, 340, 340, 340), fill="black", width=2)
        elif kind == "rectangle":
            draw.rectangle((40, 40, 340, 340), outline="black", width=2)
        elif kind == "filled":
            draw.rectangle((40, 40, 340, 340), fill="black")
        else:
            draw.line((40, 40, 340, 340), fill="black", width=2)
            draw.line((40, 340, 340, 40), fill="black", width=2)
        assert raster_vectors(image, [0, 0, 400, 400]) == []


def test_multiline_ownership_without_row_invention() -> None:
    image = grid(1, 2)
    page: dict[str, Any] = {"page_size": [400, 400], "words": [], "vector_candidates": []}
    for row in range(7):
        for column in range(2):
            page["words"].append(
                {
                    "id": f"w{row}-{column}",
                    "text": f"line {row}",
                    "bbox": [60 + column * 180, 60 + row * 30, 150 + column * 180, 75 + row * 30],
                }
            )
    page["words"].append({"id": "footer", "text": "Footer", "bbox": [10, 370, 80, 385]})
    states = propose(image, [0, 0, 400, 400], page)
    assert len(states) == 2
    assert states[0]["tables"] == []
    assert states[1]["tables"][0]["row_count"] == 1
    assert states[1]["tables"][0]["col_count"] == 2
    assert all(len(cell["source_ids"]) == 7 for cell in states[1]["tables"][0]["cells"])
    assert states[1]["unresolved_ids"] == ["footer"]
    for state in states:
        validate(page, state)
    page["vector_candidates"] = raster_vectors(image, [0, 0, 400, 400])
    assert len(propose(image, [0, 0, 400, 400], page)) == 1


@pytest.mark.parametrize("bounds", [[0, 0, 0, 400], [0, 0, float("nan"), 400]])
def test_invalid_bounds_reject_complete_output(bounds: list[float]) -> None:
    with pytest.raises(ValueError, match="bounds"):
        raster_vectors(grid(1, 2), bounds)


def test_pixel_budget_is_checked_before_conversion() -> None:
    with pytest.raises(ValueError, match="pixel admission"):
        raster_vectors(Image.new("RGB", (2200, 2200)), [0, 0, 2200, 2200])


def test_separate_grids_are_preserved_independently() -> None:
    image = Image.new("RGB", (600, 400), "white")
    draw = ImageDraw.Draw(image)
    for left, top in ((20, 20), (350, 210)):
        draw.rectangle((left, top, left + 200, top + 160), outline="black", width=2)
        draw.line((left + 100, top, left + 100, top + 160), fill="black", width=2)
    vectors = raster_vectors(image, [0, 0, 600, 400])
    assert len(vectors) == 2
    assert all(v["row_count"] == 1 and v["col_count"] == 2 for v in vectors)


def test_nonrectangular_missing_dividers_reject_grid() -> None:
    image = grid(2, 2)
    draw = ImageDraw.Draw(image)
    draw.rectangle((189, 42, 192, 188), fill="white")
    draw.rectangle((42, 189, 188, 192), fill="white")
    assert raster_vectors(image, [0, 0, 400, 400]) == []


def test_oversized_slot_inventory_rejects_complete_result() -> None:
    with pytest.raises(ValueError, match="slots exceed"):
        raster_vectors(grid(65, 65), [0, 0, 400, 400])


@pytest.mark.parametrize("color", [(180, 180, 180), (220, 220, 220), (240, 220, 20)])
def test_contrast_method_recovers_faint_or_colored_rules_without_changing_baseline(color: tuple[int, int, int]) -> None:
    image = grid(2, 2)
    image = image.convert("L").point(lambda value: 255 if value == 255 else 0).convert("RGB")
    pixels = image.load()
    assert pixels is not None
    for y in range(image.height):
        for x in range(image.width):
            if pixels[x, y] == (0, 0, 0):
                pixels[x, y] = color
    assert raster_vectors(image, [0, 0, 400, 400]) == []
    recovered = raster_vectors(image, [0, 0, 400, 400], method="contrast")
    assert [(v["row_count"], v["col_count"]) for v in recovered] == [(2, 2)]


def test_contrast_method_handles_inverted_scan_polarity() -> None:
    image = ImageOps.invert(grid(2, 2))
    assert raster_vectors(image, [0, 0, 400, 400]) == []
    assert len(raster_vectors(image, [0, 0, 400, 400], method="contrast")) == 1


def test_repair_method_recovers_short_breaks_and_thick_strokes() -> None:
    image = grid(2, 2)
    draw = ImageDraw.Draw(image)
    for coordinate in (40, 190, 340):
        draw.rectangle((130, coordinate - 2, 131, coordinate + 2), fill="white")
        draw.rectangle((coordinate - 2, 130, coordinate + 2, 131), fill="white")
    assert raster_vectors(image, [0, 0, 400, 400]) == []
    assert len(raster_vectors(image, [0, 0, 400, 400], method="repair")) == 1
    thick = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(thick)
    for coordinate in (40, 190, 340):
        draw.line((40, coordinate, 340, coordinate), fill="black", width=8)
        draw.line((coordinate, 40, coordinate, 340), fill="black", width=8)
    assert raster_vectors(thick, [0, 0, 400, 400]) == []
    assert len(raster_vectors(thick, [0, 0, 400, 400], method="repair")) == 1


@pytest.mark.parametrize("method", ["baseline", "contrast", "gap", "repair"])
def test_all_methods_preserve_negative_rectangle_and_subdivided_chart_ambiguity(method: str) -> None:
    image = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 340, 340), outline=(200, 200, 200), width=2)
    assert raster_vectors(image, [0, 0, 400, 400], method=method) == []
    chart = grid(2, 2)
    ImageDraw.Draw(chart).line((40, 320, 140, 200, 240, 260, 340, 100), fill="red", width=2)
    # Physical partitions are compatible with either a chart or a table.
    # The detector must retain a proposal rather than assert table semantics.
    assert len(raster_vectors(chart, [0, 0, 400, 400], method=method)) == 1


def test_unknown_method_refuses_complete_result() -> None:
    with pytest.raises(ValueError, match="Unknown raster"):
        raster_vectors(grid(2, 2), [0, 0, 400, 400], method="unknown")


def test_default_is_exactly_the_explicit_baseline() -> None:
    for rows, columns in ((1, 2), (2, 1), (3, 4)):
        image = grid(rows, columns)
        assert raster_vectors(image, [0, 0, 400, 400]) == raster_vectors(image, [0, 0, 400, 400], method="baseline")


def test_gap_method_preserves_threshold_and_repairs_only_geometry() -> None:
    image = grid(2, 2)
    draw = ImageDraw.Draw(image)
    for coordinate in (40, 190, 340):
        draw.rectangle((130, coordinate - 2, 131, coordinate + 2), fill="white")
        draw.rectangle((coordinate - 2, 130, coordinate + 2, 131), fill="white")
    assert len(raster_vectors(image, [0, 0, 400, 400], method="gap")) == 1
    faint = image.convert("L").point(lambda value: 255 if value == 255 else 220).convert("RGB")
    assert raster_vectors(faint, [0, 0, 400, 400], method="gap") == []
    assert len(raster_vectors(faint, [0, 0, 400, 400], method="repair")) == 1
