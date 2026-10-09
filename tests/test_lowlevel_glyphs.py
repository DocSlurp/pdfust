"""Private pre-clustering experiment evidence and resource boundaries."""

from __future__ import annotations

import pytest
from conftest import build_pdf, build_raw_pdf

import pylopdf


def _snapshot(doc: pylopdf.Document, page: int = 1, **limits: int) -> tuple:
    return doc._doc.extract_glyph_snapshot(page, **limits)  # noqa: SLF001 - private experiment API


def _raw_text(content: str, *, rotation: int = 0) -> bytes:
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
            3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            4: (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
                f"/Rotate {rotation} /Resources << /Font << /F1 3 0 R >> >> /Contents 5 0 R >>"
            ),
            5: f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        }
    )


def test_snapshot_preserves_callback_order_before_geometry() -> None:
    doc = pylopdf.Document()
    page = doc.new_page(width=300, height=200)
    page.insert_text((180, 80), "Right")
    page.insert_text((30, 80), "Left")
    original = page.get_text()
    width, height, rows, skipped = _snapshot(doc)
    assert (width, height, skipped) == (300, 200, 0)
    assert "".join(row[1] for row in rows) == "RightLeft"
    assert [row[0] for row in rows] == list(range(len(rows)))
    assert original == "Left Right\n"
    assert page.get_text() == original
    assert all(len(row[6]) == 32 and row[9] == "fill" for row in rows)
    assert _snapshot(doc) == (width, height, rows, skipped)
    doc.close()
    assert "".join(row[1] for row in rows) == "RightLeft"


def test_snapshot_preserves_overprint_and_invisible_mode() -> None:
    stream = "BT /F1 12 Tf 30 120 Td (AB) Tj ET BT /F1 12 Tf 3 Tr 30 120 Td (AB) Tj ET"
    doc = pylopdf.open(stream=_raw_text(stream))
    rows = _snapshot(doc)[2]
    assert "".join(row[1] for row in rows) == "ABAB"
    assert [row[9] for row in rows] == ["fill", "fill", "invisible", "invisible"]
    assert rows[0][2] == rows[2][2]
    assert doc[0].get_text() == "AB\nAB\n"


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_snapshot_rotation_matches_display_line_origin(rotation: int) -> None:
    doc = pylopdf.open(stream=_raw_text("BT /F1 12 Tf 30 120 Td (AB) Tj ET", rotation=rotation))
    width, height, rows, _ = _snapshot(doc)
    assert (width, height) == ((300, 200) if rotation in {0, 180} else (200, 300))
    line = doc[0].get_text("dict")["blocks"][0]["lines"][0]
    assert rows[0][2] == pytest.approx(line["spans"][0]["origin"])
    assert rows[0][5] == pytest.approx(line["dir"])


def test_snapshot_refusal_preserves_cache_and_does_not_admit_failed_page() -> None:
    doc = pylopdf.open(stream=build_pdf(["AB", "CD"]), limits=pylopdf.DocumentLimits(max_text_glyphs=4))
    cached = doc[0].get_text("dict")
    with pytest.raises(pylopdf.LimitError) as exc:
        _snapshot(doc, 2, max_glyphs=1)
    assert exc.value.code == "text_glyph_count"
    assert doc[0].get_text("dict") == cached
    assert "".join(row[1] for row in _snapshot(doc, 2)[2]) == "CD"
    assert doc[1].get_text() == "CD\n"
    assert _snapshot(doc, 1)[2] == _snapshot(doc, 1)[2]


def test_snapshot_shares_cumulative_document_admission() -> None:
    doc = pylopdf.open(stream=build_pdf(["AB", "CD"]), limits=pylopdf.DocumentLimits(max_text_glyphs=3))
    _snapshot(doc)
    assert doc[0].get_text() == "AB\n"
    with pytest.raises(pylopdf.LimitError) as exc:
        _snapshot(doc, 2)
    assert exc.value.code == "text_glyph_count"
    assert doc[0].get_text() == "AB\n"


def test_snapshot_text_budget_and_edit_invalidation() -> None:
    doc = pylopdf.Document()
    page = doc.new_page()
    page.insert_text((30, 80), "AB")
    with pytest.raises(pylopdf.LimitError) as exc:
        _snapshot(doc, max_text_bytes=1)
    assert exc.value.code == "text_size"
    old = _snapshot(doc)[2]
    page.insert_text((30, 120), "CD")
    assert "".join(row[1] for row in _snapshot(doc)[2]) == "ABCD"
    assert "".join(row[1] for row in old) == "AB"


@pytest.mark.parametrize(
    "limits", [{"max_glyphs": 0}, {"max_glyphs": 65537}, {"max_text_bytes": 0}, {"max_text_bytes": 1048577}]
)
def test_snapshot_rejects_unbounded_or_invalid_limits(limits: dict[str, int]) -> None:
    doc = pylopdf.open(stream=build_pdf(["AB"]))
    with pytest.raises(ValueError, match="max_glyphs must be"):
        _snapshot(doc, **limits)
    assert doc[0].get_text() == "AB\n"


@pytest.mark.parametrize("page", [0, 2])
def test_snapshot_invalid_page_restores_interpretation(page: int) -> None:
    doc = pylopdf.open(stream=build_pdf(["AB"]))
    with pytest.raises(pylopdf.PdfError):
        _snapshot(doc, page)
    assert doc[0].get_text() == "AB\n"
