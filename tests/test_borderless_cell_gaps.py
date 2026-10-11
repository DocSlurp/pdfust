"""Borderless tables padded like CSS tables, and prose columns that are not tables."""

from __future__ import annotations

from conftest import build_raw_pdf

import pylopdf

SIZE = 10
# Helvetica AFM advances (per 1000 em) for the characters used below.
WIDTHS = {**dict.fromkeys("0123456789$", 556), ".": 278, "F": 611, "e": 556}


def _width(text: str) -> float:
    return sum(WIDTHS[c] for c in text) * SIZE / 1000


def _pdf(lines: list[tuple[float, float, str]], font: str = "Helvetica") -> bytes:
    """Place Helvetica strings at top-left display coordinates on a Letter page."""
    ops = " ".join(f"BT /F1 {SIZE} Tf {x:.2f} {792 - y:.2f} Td ({text}) Tj ET" for x, y, text in lines)
    return build_raw_pdf({
        1: "<< /Type /Catalog /Pages 2 0 R >>",
        2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
           "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        4: f"<< /Length {len(ops)} >>\nstream\n{ops}\nendstream",
        5: f"<< /Type /Font /Subtype /Type1 /BaseFont /{font} >>",
    })


def test_right_aligned_amount_column_with_one_em_padding_splits_cleanly() -> None:
    rows = [
        ("Date", "Session", "Fee", "Closes"),
        ("14 Apr", "Signal workshop", "$45.00", "31 Mar"),
        ("14 Apr", "Accessibility audit", "$120.00", "1 Apr"),
        ("15 Apr", "Depot tour", "$5.00", "8 Apr"),
    ]
    lines = []
    for index, (date, session, fee, closes) in enumerate(rows):
        y = 100 + index * 18
        # The fee column is right-aligned at x=330; the next column starts 1.2 em later.
        lines += [(50, y, date), (130, y, session), (330 - _width(fee), y, fee), (342, y, closes)]
    doc = pylopdf.open(stream=_pdf(lines))
    tables = doc[0].find_tables(strategy="text")
    assert len(tables) == 1
    assert tables[0].extract() == [list(row) for row in rows]


def test_side_by_side_prose_columns_with_narrow_gutter_are_not_a_table() -> None:
    # Courier advances 6 pt at 10 pt, so 40-character left lines end at x=290
    # and leave a constant 1.2 em gutter before the right column at x=302.
    left = [
        "members who cannot look after their plot",
        "this season should please tell us by the",
        "end of April so a neighbour on the list",
        "can take it over before planting begins.",
    ]
    right = [
        "last year our members",
        "donated more than a",
        "thousand pounds of fresh",
        "produce to the pantry.",
    ]
    left[2] += " "
    assert all(len(line) == 40 for line in left)
    lines = [(50, 100 + i * 14, text) for i, text in enumerate(left)]
    lines += [(302, 100 + i * 14, text) for i, text in enumerate(right)]
    doc = pylopdf.open(stream=_pdf(lines, font="Courier"))
    assert len(doc[0].find_tables(strategy="text")) == 0
