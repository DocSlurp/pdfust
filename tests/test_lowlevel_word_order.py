"""Preserve word membership under reverse per-glyph painting of disjoint fields."""

from __future__ import annotations

from itertools import permutations

import pytest
from conftest import build_raw_pdf

import pdfust


def _glyph_pdf(
    texts: list[tuple[str, float]],
    *,
    reverse: bool,
    rotation: int = 0,
    width: int = 500,
    paint_order: tuple[int, ...] | None = None,
) -> bytes:
    glyphs = [(char, start + 6 * index) for text, start in reversed(texts) for index, char in enumerate(text)]
    if paint_order is not None:
        glyphs = [glyphs[index] for index in paint_order]
    elif reverse:
        glyphs.reverse()
    stream = "\n".join(f"BT /F1 10 Tf 1 0 0 1 {x} 100 Tm ({char}) Tj ET" for char, x in glyphs)
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
            3: "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
            4: (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} 200] "
                f"/Rotate {rotation} /Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>"
            ),
            5: f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        }
    )


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize(
    "texts",
    [
        [("12", 40), ("AB", 100)],
        [("105", 40), ("pressure-rated fittings", 100)],
        [("105", 40), ("weekend service hours", 100)],
        [("105", 40), ("weather-resistant conduit", 100)],
    ],
)
def test_disjoint_fields_keep_words_under_reverse_glyph_painting(texts: list[tuple[str, float]], rotation: int) -> None:
    with pdfust.open(stream=_glyph_pdf(texts, reverse=False, rotation=rotation)) as forward:
        expected = forward[0].get_text()
        expected_words = [word[4] for word in forward[0].get_text("words")]
        expected_lines = forward[0].get_text("dict")["blocks"]
    with pdfust.open(stream=_glyph_pdf(texts, reverse=True, rotation=rotation)) as reverse:
        assert reverse[0].get_text() == expected
        assert [word[4] for word in reverse[0].get_text("words")] == expected_words
        assert reverse[0].get_text("dict")["blocks"] == expected_lines
        assert len(reverse[0].search_for(texts[1][0])) == 1
        assert texts[1][0] in reverse[0].to_markdown()


def test_wide_gaps_do_not_hide_true_overprinted_words() -> None:
    doc = pdfust.Document()
    page = doc.new_page(width=400, height=200)
    # One complete overprint has two physically disconnected words. It must
    # remain a distinct source layer after the forward-gap run split.
    for _ in range(2):
        page.insert_text((40, 100), "AB")
        page.insert_text((200, 100), "CD")
    assert page.get_text().count("AB") == 2
    assert page.get_text().count("CD") == 2
    assert len(page.search_for("AB")) == len(page.search_for("CD")) == 2
    assert sorted(word[4] for word in page.get_text("words")) == ["AB", "AB", "CD", "CD"]


@pytest.mark.parametrize("reverse", [False, True])
def test_sparse_monotone_glyphs_preserve_every_word(*, reverse: bool) -> None:
    texts = [("A", float(40 + index * 20)) for index in range(256)]
    with pdfust.open(stream=_glyph_pdf(texts, reverse=reverse, width=6000)) as doc:
        assert [word[4] for word in doc[0].get_text("words")] == ["A"] * 256
        assert doc[0].get_text().split() == ["A"] * 256


@pytest.mark.parametrize("paint_order", list(permutations(range(4))))
def test_disjoint_fields_ignore_arbitrary_glyph_paint_order(paint_order: tuple[int, ...]) -> None:
    with pdfust.open(stream=_glyph_pdf([("12", 40), ("AB", 100)], reverse=False, paint_order=paint_order)) as doc:
        assert doc[0].get_text() == "12 AB\n"
        assert [word[4] for word in doc[0].get_text("words")] == ["12", "AB"]
