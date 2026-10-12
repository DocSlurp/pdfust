"""Public typing-contract tests."""

from __future__ import annotations

from conftest import build_pdf

import pdfust


def test_public_return_annotations_describe_real_values() -> None:
    doc = pdfust.open(stream=build_pdf(["Typed layout"]))
    layout: pdfust.TextPage = doc[0].get_text("dict")
    metadata: pdfust.DocumentMetadata = doc.metadata
    complexity: pdfust.DocumentComplexity = doc.complexity
    labels: list[pdfust.PageLabelInfo] = doc.get_page_labels()
    fields: list[pdfust.FormFieldInfo] = doc.get_form_fields()
    drawings: list[pdfust.DrawingInfo] = doc[0].get_drawings()
    compression: pdfust.ImageCompressionResult = doc.compress_images()

    assert layout["blocks"][0]["lines"][0]["spans"][0]["text"] == "Typed layout"
    assert metadata["format"].startswith("PDF ")
    assert complexity["page_count"] == 1
    assert labels == []
    assert fields == []
    assert drawings == []
    assert compression["rewritten"] == 0
