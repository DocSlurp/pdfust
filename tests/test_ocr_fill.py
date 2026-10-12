"""OCR-fill policy: add OCR text only where the native text layer is missing."""

from __future__ import annotations

from pathlib import Path

import pytest

import pdfust
from pdfust.pdfust_core import _Document

MODEL_ROOT = Path(__file__).parents[1] / "models" / "pdfust-ocr-models" / "src" / "pdfust_ocr_models"


@pytest.fixture(scope="module")
def ocr_engine() -> pdfust.OcrEngine:
    """Load the bundled model set once."""
    return pdfust.OcrEngine(
        MODEL_ROOT / "PP-OCRv6_det_small.rten",
        MODEL_ROOT / "PP-OCRv6_rec_small.rten",
        MODEL_ROOT / "ppocrv6_dict.txt",
    )


def _mixed_page() -> pdfust.Document:
    """Native heading on top, a scanned (image) sentence below."""
    scan = pdfust.Document()
    scan.new_page(width=360, height=80)
    scan[0].insert_text((10, 55), "Scanned region text", fontsize=28)
    png = scan[0].render(dpi=150)
    doc = pdfust.Document()
    page = doc.new_page(width=360, height=200)
    page.insert_text((10, 40), "Native heading text on this page", fontsize=16)
    page.insert_image((0, 100, 360, 180), stream=png)
    return doc


def test_fill_adds_only_missing_text_and_is_idempotent(ocr_engine: pdfust.OcrEngine) -> None:
    doc = _mixed_page()
    page = doc[0]
    assert "Scanned" not in page.get_text()

    result = page.ocr_fill(engine=ocr_engine, dpi=150)

    assert result["policy"] == "fill"
    assert result["recognized"] >= 2
    assert result["filled"] >= 1
    assert result["replaced_pages"] == 0
    assert "Native heading text" in result["text"]
    assert "Scanned" in result["text"]
    assert result["text"].count("Native") == 1  # native text is not duplicated by OCR
    assert "Scanned" in result["markdown"]
    assert all(word["bbox"].y0 > 90 for word in result["words"])  # only the scanned region

    again = page.ocr_fill(engine=ocr_engine, dpi=150)
    assert again["filled"] == 0
    assert again["text"] == result["text"]


def test_adaptive_ocrs_only_large_raster_regions_on_pages_with_text(ocr_engine: pdfust.OcrEngine) -> None:
    doc = _mixed_page()
    result = doc[0].ocr_fill(policy="adaptive", engine=ocr_engine, dpi=150)
    assert result["regions"] == 1
    assert result["replaced_pages"] == 0
    assert "Scanned" in result["text"]
    assert result["text"].count("Native") == 1


def test_adaptive_runs_full_page_when_native_text_is_absent(ocr_engine: pdfust.OcrEngine) -> None:
    scan = pdfust.Document()
    scan.new_page(width=360, height=100)
    scan[0].insert_text((10, 60), "Only pixels here", fontsize=28)
    png = scan[0].render(dpi=150)
    doc = pdfust.Document()
    doc.new_page(width=360, height=100)
    doc[0].insert_image((0, 0, 360, 100), stream=png)
    assert doc[0].get_text().strip() == ""
    result = doc[0].ocr_fill(policy="adaptive", engine=ocr_engine, dpi=150)
    assert result["replaced_pages"] == 1
    assert "pixels" in result["text"]


def test_selection_keeps_every_word_when_native_layer_is_unusable() -> None:
    native = [(10.0, 10.0, 50.0, 20.0)]
    ocr = [(5.0, 5.0, 60.0, 25.0, "alpha beta"), (5.0, 40.0, 60.0, 55.0, "gamma delta")]
    # Unmapped glyphs and little native text: everything is inserted.
    assert _Document.select_ocr_fill_words(native, 3, True, ocr, 2.0, 0.5) == (True, [0, 1])
    # Mapped native text gates OCR boxes that contain a native word centre.
    assert _Document.select_ocr_fill_words(native, 3, False, ocr, 2.0, 0.5) == (False, [1])
    # Enough native characters: unmapped glyphs alone do not replace the layer.
    assert _Document.select_ocr_fill_words(native, 100, True, ocr, 2.0, 0.5) == (False, [1])
    # Slack lets a centre just outside the OCR box still count as inside it.
    near = [(58.0, 12.0, 64.0, 20.0)]
    assert _Document.select_ocr_fill_words(near, 100, False, ocr, 2.0, 0.5) == (False, [1])
    assert _Document.select_ocr_fill_words(near, 100, False, ocr, 0.0, 0.5) == (False, [0, 1])


def test_ocr_fill_validates_arguments() -> None:
    page = pdfust.Document().new_page()
    with pytest.raises(ValueError, match="policy"):
        page.ocr_fill(policy="bogus")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="engine"):
        page.ocr_fill(engine=object())  # type: ignore[arg-type]
