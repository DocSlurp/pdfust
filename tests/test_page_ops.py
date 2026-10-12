"""Tests for page insertion, ranges, new_page, and copy_page."""

from __future__ import annotations

import pytest
from conftest import build_raw_pdf, png_size

import pdfust


def test_insert_pdf_range(three_page_pdf: bytes, one_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=one_page_pdf)
    src = pdfust.Document(stream=three_page_pdf)
    doc.insert_pdf(src, from_page=1, to_page=2)
    assert doc.page_count == 3
    assert "Page two" in doc.get_page_text(1)
    assert "Page three" in doc.get_page_text(2)


def test_insert_pdf_reversed_range(three_page_pdf: bytes) -> None:
    doc = pdfust.Document()
    src = pdfust.Document(stream=three_page_pdf)
    doc.insert_pdf(src, from_page=2, to_page=0)
    assert doc.page_count == 3
    assert "Page three" in doc.get_page_text(0)
    assert "Page one" in doc.get_page_text(2)


def test_insert_pdf_negative_range(three_page_pdf: bytes) -> None:
    doc = pdfust.Document()
    doc.insert_pdf(pdfust.Document(stream=three_page_pdf), from_page=-2, to_page=-1)
    assert doc.page_count == 2
    assert "Page two" in doc.get_page_text(0)


def test_insert_pdf_start_at(three_page_pdf: bytes, one_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=three_page_pdf)
    src = pdfust.Document(stream=one_page_pdf)
    doc.insert_pdf(src, start_at=1)
    assert doc.page_count == 4
    assert "Page one" in doc.get_page_text(0)
    assert "Hello PDF" in doc.get_page_text(1)
    assert "Page two" in doc.get_page_text(2)
    # Preserve page order after save and reload.
    reloaded = pdfust.Document(stream=doc.tobytes())
    assert "Hello PDF" in reloaded.get_page_text(1)


def test_insert_pdf_start_at_zero_prepends(three_page_pdf: bytes, one_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=three_page_pdf)
    doc.insert_pdf(pdfust.Document(stream=one_page_pdf), start_at=0)
    assert "Hello PDF" in doc.get_page_text(0)
    assert "Page one" in doc.get_page_text(1)


def test_insert_pdf_start_at_out_of_range(three_page_pdf: bytes, one_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=three_page_pdf)
    with pytest.raises(IndexError, match="start_at"):
        doc.insert_pdf(pdfust.Document(stream=one_page_pdf), start_at=4)


def test_insert_pdf_empty_source_noop(three_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=three_page_pdf)
    doc.insert_pdf(pdfust.Document())
    assert doc.page_count == 3


def test_insert_pdf_does_not_keep_unreachable_source_data() -> None:
    """Do not copy unreachable attachments into the destination."""
    secret = b"SECRET-UNREFERENCED-ATTACHMENT-7c3f"
    source = pdfust.Document()
    source.new_page(width=100, height=100)
    source.embfile_add("secret.txt", secret)

    target = pdfust.Document()
    target.insert_pdf(source)

    assert target.embfile_names() == []
    assert secret not in target.tobytes()


def test_new_page_appends_blank(one_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=one_page_pdf)
    page = doc.new_page()
    assert doc.page_count == 2
    assert page.number == 1
    assert page.mediabox == pdfust.Rect(0.0, 0.0, 595.0, 842.0)
    assert page.get_text() == ""
    assert png_size(doc.render_page(1)) == (595, 842)


def test_new_page_preserves_indirect_root_kids() -> None:
    doc = pdfust.open(
        stream=build_raw_pdf(
            {
                1: "<< /Type /Catalog /Pages 2 0 R >>",
                2: "<< /Type /Pages /Kids 4 0 R /Count 1 >>",
                3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>",
                4: "[3 0 R]",
            }
        )
    )

    doc.new_page(width=200, height=300)

    assert doc.page_count == 2
    assert doc[0].rect.width == pytest.approx(100)
    assert doc[1].rect == pdfust.Rect(0, 0, 200, 300)
    assert pdfust.open(stream=doc.tobytes()).page_count == 2

    doc.delete_page(1)

    assert doc.page_count == 1
    assert doc[0].rect.width == pytest.approx(100)
    assert pdfust.open(stream=doc.tobytes()).page_count == 1


def test_new_page_insert_position_and_size(three_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=three_page_pdf)
    page = doc.new_page(1, width=300, height=400)
    assert page.number == 1
    assert doc.page_count == 4
    assert doc.get_page_text(1) == ""
    assert "Page two" in doc.get_page_text(2)
    reloaded = pdfust.Document(stream=doc.tobytes())
    assert reloaded.page_count == 4
    assert png_size(reloaded.render_page(1)) == (300, 400)


def test_new_page_invalid_size(one_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=one_page_pdf)
    with pytest.raises(ValueError, match="width"):
        doc.new_page(width=0)
    with pytest.raises(ValueError, match="PDF real-number"):
        doc.new_page(width=1e39)


def test_copy_page_append_and_position(three_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=three_page_pdf)
    doc.copy_page(0)
    assert doc.page_count == 4
    assert "Page one" in doc.get_page_text(3)
    doc.copy_page(2, to=0)  # Copy the current Page three to the front.
    assert doc.page_count == 5
    assert "Page three" in doc.get_page_text(0)
    reloaded = pdfust.Document(stream=doc.tobytes())
    assert reloaded.page_count == 5
    assert "Page three" in reloaded.get_page_text(0)
    assert reloaded.render_page(0) == reloaded.render_page(3)


def test_structure_ops_invalidate_pages(three_page_pdf: bytes) -> None:
    doc = pdfust.Document(stream=three_page_pdf)
    page = doc[0]
    doc.new_page()
    with pytest.raises(pdfust.StalePageError):
        _ = page.mediabox


def test_cached_page_order_tracks_structural_edits() -> None:
    """Warm both count and ID lookups before each change to the page tree."""
    doc = pdfust.open()

    def widths() -> list[float]:
        assert doc.page_count == len(doc)
        return [page.rect.width for page in doc]

    assert widths() == []
    doc.new_page(width=100, height=200)
    assert widths() == [100]
    doc.new_page(width=300, height=200)
    assert widths() == [100, 300]
    doc.copy_page(0, to=1)
    assert widths() == [100, 100, 300]
    doc.select([2, 0, 2])
    assert widths() == [300, 100, 300]
    doc.delete_pages([0, 1])
    assert widths() == [300]

    source = pdfust.open()
    source.new_page(width=500, height=200)
    assert source.page_count == 1
    doc.insert_pdf(source, start_at=0)
    assert widths() == [500, 300]
    doc.select([])
    assert widths() == []
    doc.new_page(width=700, height=200)
    assert widths() == [700]

    reloaded = pdfust.open(stream=doc.tobytes())
    assert reloaded.page_count == 1
    assert reloaded[0].rect.width == 700


def test_cached_page_ids_survive_content_and_output_changes() -> None:
    doc = pdfust.open()
    doc.new_page(width=123, height=200)
    doc.new_page(width=456, height=200)
    assert [page.rect.width for page in doc] == [123, 456]

    doc[0].insert_text((10, 30), "Retained page")
    doc.set_metadata({"title": "Updated metadata"})
    doc.tobytes(garbage=True, deflate=True, object_streams=True)

    assert doc.page_count == 2
    assert [page.rect.width for page in doc] == [123, 456]
    assert "Retained page" in doc[0].get_text()
    doc.copy_page(1, to=0)
    assert [page.rect.width for page in doc] == [456, 123, 456]


def test_core_import_duplicate_pages_have_independent_dictionaries(one_page_pdf: bytes) -> None:
    source = pdfust.open(stream=one_page_pdf)
    target = pdfust.open()
    target._doc.merge_pages(source._doc, [1, 1], None)  # noqa: SLF001  # Exercise the native boundary.

    assert target.page_count == 2
    assert target[0].get_text() == target[1].get_text()
    target[0].set_rotation(90)
    assert target[0].rotation == 90
    assert target[1].rotation == 0
    reloaded = pdfust.open(stream=target.tobytes())
    assert reloaded.page_count == 2
    assert reloaded[0].rotation == 90
    assert reloaded[1].rotation == 0
