"""Public typing-contract tests."""

from __future__ import annotations

from conftest import build_pdf

import pylopdf


def test_public_return_annotations_describe_real_values() -> None:
    doc = pylopdf.open(stream=build_pdf(["Typed layout"]))
    layout: pylopdf.TextPage = doc[0].get_text("dict")
    metadata: pylopdf.DocumentMetadata = doc.metadata
    complexity: pylopdf.DocumentComplexity = doc.complexity
    labels: list[pylopdf.PageLabelInfo] = doc.get_page_labels()
    fields: list[pylopdf.FormFieldInfo] = doc.get_form_fields()
    drawings: list[pylopdf.DrawingInfo] = doc[0].get_drawings()
    compression: pylopdf.ImageCompressionResult = doc.compress_images()

    assert layout["blocks"][0]["lines"][0]["spans"][0]["text"] == "Typed layout"
    assert metadata["format"].startswith("PDF ")
    assert complexity["page_count"] == 1
    assert labels == []
    assert fields == []
    assert drawings == []
    assert compression["rewritten"] == 0
