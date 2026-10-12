"""Compensated display geometry and separate orientation construction references."""

from __future__ import annotations

from bench.generalization_orientation_audit import construction_references, source_cases

import pdfust


def test_compensated_sources_have_upright_display_despite_page_rotation() -> None:
    cases = {case["id"]: case for case in source_cases()}
    rendered = []
    for identifier in ("upright-control", "compensated-90", "compensated-180", "compensated-270"):
        with pdfust.Document(stream=cases[identifier]["pdf"]) as document:
            page = document[0]
            clip = page.get_images()[0]["bbox"]
            rendered.append(page.get_pixmap(clip=clip).samples)
    assert all(pixels == rendered[0] for pixels in rendered)


def test_physical_sideways_scan_keeps_zero_page_rotation_and_native_header() -> None:
    cases = {case["id"]: case for case in source_cases()}
    with pdfust.Document(stream=cases["mixed-physical-90"]["pdf"]) as document:
        assert document[0].rotation == 0
        assert "Native header" in document[0].get_text()
        box = document[0].get_images()[0]["bbox"]
        assert box.height > box.width
    reference = construction_references()["mixed-physical-90"]
    assert reference["preserved_correction"] == reference["normalized_correction"] == 270
