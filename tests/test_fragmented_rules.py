"""Vector rule connectivity preserves grids across equivalent paint encodings."""

from __future__ import annotations

import pytest
from conftest import build_raw_pdf

import pdfust


def _pdf(content: str, rotation: int = 0) -> bytes:
    """Serialize one PDF page with a Helvetica resource."""
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: (
                "<< /Type /Pages /Kids [4 0 R] /Count 1 /MediaBox [0 0 400 300] "
                "/Resources << /Font << /F1 3 0 R >> >> >>"
            ),
            3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            4: f"<< /Type /Page /Parent 2 0 R /Rotate {rotation} /Contents 5 0 R >>",
            5: f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        }
    )


def _three_level(*, fragmented: bool, gap: float = 0, rotation: int = 0) -> bytes:
    """Draw a three-row merged stub with an optionally fragmented left border."""
    rules = [
        "40 260 m 355 260 l S",
        "145 230 m 355 230 l S",
        "145 200 m 355 200 l S",
        "40 170 m 355 170 l S",
        "40 140 m 355 140 l S",
        "40 110 m 355 110 l S",
        "145 110 m 145 260 l S",
        "250 110 m 250 230 l S",
        "355 110 m 355 260 l S",
    ]
    if fragmented:
        # The middle piece meets no perpendicular rule; collinear joins must
        # connect it. Positive gaps shorten it; negative gaps overlap neighbors.
        rules += [
            "40 230 m 40 260 l S",
            f"40 {200 + gap} m 40 {230 - gap} l S",
            "40 170 m 40 200 l S",
            "40 140 m 40 170 l S",
            "40 110 m 40 140 l S",
        ]
    else:
        rules.append("40 110 m 40 260 l S")
    values = [
        (50, 241, "Name"),
        (155, 241, "Finance"),
        (155, 211, "Actual"),
        (260, 211, "Forecast"),
        (155, 181, "USD"),
        (260, 181, "USD"),
        (50, 151, "Oak"),
        (155, 151, "10"),
        (260, 151, "20"),
        (50, 121, "Elm"),
        (155, 121, "11"),
        (260, 121, "21"),
    ]
    rules += [f"BT /F1 8 Tf {x} {y} Td ({text}) Tj ET" for x, y, text in values]
    return _pdf("\n".join(rules), rotation)


def _assert_three_level(table: pdfust.SpatialTable) -> None:
    """Check independently declared cells and source header ancestry."""
    expected = {
        (0, 0, 3, 1, "Name"),
        (0, 1, 1, 2, "Finance"),
        (1, 1, 1, 1, "Actual"),
        (1, 2, 1, 1, "Forecast"),
        (2, 1, 1, 1, "USD"),
        (2, 2, 1, 1, "USD"),
        (3, 0, 1, 1, "Oak"),
        (3, 1, 1, 1, "10"),
        (3, 2, 1, 1, "20"),
        (4, 0, 1, 1, "Elm"),
        (4, 1, 1, 1, "11"),
        (4, 2, 1, 1, "21"),
    }
    assert (table.row_count, table.col_count) == (5, 3)
    assert {(c.row, c.column, c.row_span, c.column_span, c.text) for c in table.cells} == expected
    fields = table.records(header_rows=3)
    assert [(f.name, f.value) for f in fields[0]] == [
        ("Name", "Oak"),
        ("Finance / Actual / USD", "10"),
        ("Finance / Forecast / USD", "20"),
    ]
    assert fields[0][1].headers[0].id == fields[0][2].headers[0].id
    assert fields[0][1].headers[-1].id != fields[0][2].headers[-1].id


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_fragmented_and_coalesced_rules_have_same_pixels_and_cells(rotation: int) -> None:
    """A merged-header outer border may be painted with isolated collinear pieces."""
    snapshots = []
    pixels = []
    for fragmented in (False, True):
        with pdfust.open(stream=_three_level(fragmented=fragmented, rotation=rotation)) as doc:
            pixels.append(doc[0].get_pixmap().samples)
            snapshots.append(doc[0].get_layout())
            native = doc[0].find_tables()
            assert len(native) == 1
            assert (native[0].row_count, native[0].col_count) == ((3, 5) if rotation % 180 else (5, 3))
    assert pixels[0] == pixels[1]
    assert snapshots[0].tables == snapshots[1].tables
    _assert_three_level(snapshots[1].tables[0])


@pytest.mark.parametrize("gap", [-0.5, 0.0, 0.5])
def test_overlap_and_small_gap_retain_complete_grid(gap: float) -> None:
    """Joining respects the existing one-point snapping tolerance."""
    with pdfust.open(stream=_three_level(fragmented=True, gap=gap)) as doc:
        tables = doc[0].get_layout().tables
    assert len(tables) == 1
    _assert_three_level(tables[0])


@pytest.mark.parametrize("gap", [1.1, 2.5, 10.0])
def test_join_does_not_extend_missing_outer_boundary(gap: float) -> None:
    """A real gap above snapping tolerance cannot become a complete table."""
    with pdfust.open(stream=_three_level(fragmented=True, gap=gap)) as doc:
        assert doc[0].get_layout().tables == ()


@pytest.mark.parametrize("vertical", [False, True])
def test_nearby_independent_grids_remain_separate(*, vertical: bool) -> None:
    """Collinear borders separated by more than tolerance stay independent."""
    ops: list[str] = []
    for origin_x, origin_y in ((40, 100), (40, 182.5) if vertical else (142.5, 100)):
        ops.extend(f"{origin_x} {y} m {origin_x + 100} {y} l S" for y in (origin_y, origin_y + 40, origin_y + 80))
        ops.extend(f"{x} {origin_y} m {x} {origin_y + 80} l S" for x in (origin_x, origin_x + 50, origin_x + 100))
    with pdfust.open(stream=_pdf("\n".join(ops))) as doc:
        tables = doc[0].get_layout().tables
    assert len(tables) == 2
    assert all((table.row_count, table.col_count) == (2, 2) for table in tables)


@pytest.mark.parametrize("overlap", [False, True])
def test_many_rule_fragments_preserve_small_grid(*, overlap: bool) -> None:
    """Bounded dense overlaps and disjoint short fragments retain their geometry."""
    ops: list[str] = []
    # 1800 rules exercise both worst-case overlapping intervals and the early
    # exit for disjoint interval neighbors without a flaky elapsed-time assertion.
    for y in (100, 140, 180):
        if overlap:
            ops += [f"40 {y} m 340 {y} l S"] * 500
        else:
            ops += [f"{40 + (index % 100) * 3} {y} m {40 + (index % 100 + 1) * 3} {y} l S" for index in range(500)]
    for x in (40, 190, 340):
        ops += [f"{x} {100 + (index % 20) * 4} m {x} {100 + (index % 20 + 1) * 4} l S" for index in range(100)]
    with pdfust.open(stream=_pdf("\n".join(ops))) as doc:
        tables = doc[0].get_layout().tables
    assert len(tables) == 1
    assert (tables[0].row_count, tables[0].col_count) == (2, 2)


def test_parallel_decorations_preserve_an_already_recognized_grid() -> None:
    """Interior orphan strokes must not alter an accepted table's coordinates."""
    grid = [
        "40 100 m 140 100 l S",
        "40 140 m 140 140 l S",
        "40 180 m 140 180 l S",
        "40 100 m 40 180 l S",
        "90 100 m 90 180 l S",
        "140 100 m 140 180 l S",
    ]
    # Neither decoration intersects a perpendicular grid rule. Both overlap a
    # parallel rule within tolerance, which previously shifted grid coordinates
    # when repairs were applied before preserving accepted components.
    decorations = ["39.2 110 m 39.2 130 l S", "50 139.2 m 70 139.2 l S"]
    snapshots = []
    for ops in (grid, grid + decorations):
        with pdfust.open(stream=_pdf("\n".join(ops))) as doc:
            snapshots.append(doc[0].get_layout())
    assert len(snapshots[0].tables) == 1
    assert snapshots[0].tables == snapshots[1].tables
