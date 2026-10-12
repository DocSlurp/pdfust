"""Column ordering: N columns, mixed font sizes at the gutter, running headers and footers."""

from __future__ import annotations

import re

import pytest

import pdfust

GUTTER = 18.0  # exactly two ems at the 9 pt body size


def _words(tag: str, count: int) -> str:
    return " ".join(f"{tag}w{i}" for i in range(1, count + 1))


def _columns_page(
    columns: int,
    *,
    heading_in_last: bool = False,
    header: bool = False,
    footer: bool = False,
) -> pdfust.Document:
    doc = pdfust.Document()
    page = doc.new_page(width=612, height=792)
    width = (612 - 108 - (columns - 1) * GUTTER) / columns
    if header:
        page.insert_text((54, 30), "RUNNINGHEAD", fontsize=9)
    for column in range(columns):
        x0 = 54 + column * (width + GUTTER)
        top = 100.0
        if heading_in_last and column == columns - 1:
            page.insert_text((x0, top + 11), "SIDEHEAD title", fontsize=11.5)
            top += 20
        for block in range(3):
            y0 = top + block * 200
            page.insert_textbox((x0, y0, x0 + width, y0 + 190), _words(f"c{column}b{block}", 30), fontsize=9)
    if footer:
        page.insert_textbox((286, 740, 326, 760), "Page 1", fontsize=9)
    return doc


def _first_word_order(text: str) -> list[tuple[int, int]]:
    return [(int(c), int(b)) for c, b in re.findall(r"c(\d)b(\d)w1\b", text)]


@pytest.mark.parametrize("columns", [2, 3, 4])
@pytest.mark.parametrize("method", ["text", "markdown"])
def test_plain_columns_read_down_each_column(columns: int, method: str) -> None:
    page = _columns_page(columns)[0]
    text = page.get_text() if method == "text" else page.to_markdown()
    expected = [(c, b) for c in range(columns) for b in range(3)]
    assert _first_word_order(text) == expected


@pytest.mark.parametrize("columns", [2, 3])
def test_larger_heading_at_the_gutter_does_not_merge_columns(columns: int) -> None:
    text = _columns_page(columns, heading_in_last=True)[0].to_markdown()
    assert _first_word_order(text) == [(c, b) for c in range(columns) for b in range(3)]
    # The previous column's last line must not run into the heading on the same baseline.
    assert not re.search(rf"c{columns - 2}b2w\d+ SIDEHEAD", text)


@pytest.mark.parametrize("columns", [2, 3])
def test_running_header_and_centered_footer_do_not_break_columns(columns: int) -> None:
    text = _columns_page(columns, header=True, footer=True)[0].to_markdown()
    assert _first_word_order(text) == [(c, b) for c in range(columns) for b in range(3)]
    assert text.index("RUNNINGHEAD") < text.index("c0b0w1")
    if columns == 2:  # noqa: PLR2004 - a centred footer crosses only the two-column gutter
        assert text.index("Page 1") > text.index("c1b2w1")
