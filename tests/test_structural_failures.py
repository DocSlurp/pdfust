"""Structural planning failures preserve the document and existing page views."""

from __future__ import annotations

import pytest
from conftest import build_raw_pdf

import pdfust


def _invalid_page_inheritance_pdf() -> bytes:
    # The Kids tree is valid, but a missing inherited attribute reaches a cycle.
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            3: "<< /Type /Page /Parent 3 0 R /MediaBox [0 0 100 200] >>",
        }
    )


@pytest.mark.parametrize("operation", ["select", "copy", "new"])
def test_rejected_structural_plan_preserves_document_and_views(operation: str) -> None:
    doc = pdfust.open(stream=_invalid_page_inheritance_pdf())
    page = doc[0]
    assert page.mediabox == pdfust.Rect(0, 0, 100, 200)
    before = doc.tobytes()

    def mutate() -> None:
        if operation == "select":
            doc.select([0, 0])
        elif operation == "copy":
            doc.copy_page(0)
        else:
            doc.new_page(width=300, height=400)

    for _ in range(2):
        with pytest.raises(pdfust.PdfError, match=r"inheritance.*cycle"):
            mutate()

        assert doc.page_count == 1
        assert page.mediabox == pdfust.Rect(0, 0, 100, 200)
        assert doc.tobytes() == before


def test_rejected_import_preserves_target_document_and_views(one_page_pdf: bytes) -> None:
    target = pdfust.open(stream=one_page_pdf)
    source = pdfust.open(stream=_invalid_page_inheritance_pdf())
    page = target[0]
    original_box = page.mediabox
    before = target.tobytes()

    with pytest.raises(pdfust.PdfError, match=r"inheritance.*cycle"):
        target.insert_pdf(source)

    assert target.page_count == 1
    assert page.mediabox == original_box
    assert target.tobytes() == before


def test_rejected_import_into_malformed_target_preserves_document(one_page_pdf: bytes) -> None:
    target = pdfust.open(stream=_invalid_page_inheritance_pdf())
    source = pdfust.open(stream=one_page_pdf)
    page = target[0]
    before = target.tobytes()

    with pytest.raises(pdfust.PdfError, match=r"inheritance.*cycle"):
        target.insert_pdf(source)

    assert target.page_count == 1
    assert page.mediabox == pdfust.Rect(0, 0, 100, 200)
    assert target.tobytes() == before
