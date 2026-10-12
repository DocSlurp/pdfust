"""Unicode recovery from the font program when a PDF declares no (or incomplete) ToUnicode."""

from __future__ import annotations

import warnings

import pytest
from conftest import build_raw_pdf

import pdfust


def _generated(text: str, language: pdfust.FontLanguage) -> bytes:
    doc = pdfust.Document()
    doc.new_page(width=300, height=150)
    doc[0].insert_text((20, 60), text, fontsize=24, font_language=language)
    return doc.tobytes()


def _strip_declared_text(pdf: bytes) -> bytes:
    """Hide ToUnicode and ActualText with same-length keys so offsets stay valid."""
    assert b"/ToUnicode" in pdf
    return pdf.replace(b"/ToUnicode", b"/XoUnicode").replace(b"/ActualText", b"/XctualText")


def _extract(pdf: bytes) -> tuple[str, pdfust.ScanStats]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pdfust.open(stream=pdf) as doc:
            return doc[0].get_text().strip(), doc[0].scan()["stats"]


@pytest.mark.parametrize(
    ("language", "text"),
    [("he", "שלום עולם"), ("hi", "नमस्ते"), ("th", "ภาษาไทย")],
)
def test_glyph_names_recover_text_without_tounicode(language: pdfust.FontLanguage, text: str) -> None:
    pytest.importorskip(f"pdfust_fonts_{language.replace('-', '_')}")
    pdf = _generated(text, language)
    assert _extract(pdf)[0] == text
    recovered, stats = _extract(_strip_declared_text(pdf))
    assert recovered == text
    assert stats["unmapped"] == 0


def test_arabic_contextual_forms_recover_their_base_letters() -> None:
    pytest.importorskip("pdfust_fonts_ar")
    recovered, stats = _extract(_strip_declared_text(_generated("مرحبا بالعالم", "ar")))
    # Glyph names such as uni066E.init identify the letter shape (dotless beh); the dots are
    # separate glyphs with no Unicode, so they stay unmapped rather than being guessed.
    assert recovered.startswith("مرح")
    assert recovered.endswith("العالم")
    assert stats["unmapped"] == 2


def test_cid_keyed_cff_without_names_stays_unmapped() -> None:
    pytest.importorskip("pdfust_fonts_jp")
    recovered, stats = _extract(_strip_declared_text(_generated("日本語", "ja")))
    assert recovered == ""
    assert stats["unmapped"] == 3


def test_actual_text_in_form_xobject_still_wins_over_glyph_name_recovery() -> None:
    pytest.importorskip("pdfust_fonts_ar")
    text = "مرحبا بالعالم"
    pdf = _generated(text, "ar")
    assert b"/ActualText" in pdf
    # ToUnicode alone is incomplete for the contextual forms; ActualText supplies them.
    assert _extract(pdf)[0] == text


def test_adobe_collection_maps_cids_to_unicode_for_embedded_cid_fonts() -> None:
    pytest.importorskip("pdfust_fonts_jp")
    pdf = _strip_declared_text(_generated("日本語", "ja"))
    # Same-length edit: Ordering (Identity) -> hex string for "GB1" padded with whitespace.
    patched = pdf.replace(b"/Ordering(Identity)", b"/Ordering<474231  >")
    assert patched != pdf
    recovered, stats = _extract(patched)
    assert stats["unmapped"] == 0
    # CIDs 1..3 of Adobe-GB1 are space, "!" and '"'; Adobe-GB1-UCS2 turns them into Unicode.
    assert recovered == '!"'


def test_fonts_report_null_or_dangling_tounicode_as_absent() -> None:
    def font_pdf(to_unicode: str) -> bytes:
        return build_raw_pdf(
            {
                1: "<< /Type /Catalog /Pages 2 0 R >>",
                2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Resources << /Font << /F1 5 0 R >> >> "
                "/Contents 4 0 R >>",
                4: "<< /Length 31 >>\nstream\nBT /F1 12 Tf 10 10 Td (x) Tj ET\nendstream",
                5: f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica {to_unicode} >>",
                6: "<< /Length 0 >>\nstream\n\nendstream",
            }
        )

    def has_tounicode(pdf: bytes) -> bool:
        with pdfust.open(stream=pdf) as doc:
            (font,) = doc.get_fonts()
            return font["has_tounicode"]

    assert has_tounicode(font_pdf("")) is False
    assert has_tounicode(font_pdf("/ToUnicode null")) is False
    assert has_tounicode(font_pdf("/ToUnicode 99 0 R")) is False
    assert has_tounicode(font_pdf("/ToUnicode 6 0 R")) is True


def test_vertical_cmap_fonts_report_wmode() -> None:
    pytest.importorskip("pdfust_fonts_jp")
    pdf = _generated("日本語", "ja")
    assert b"/Encoding/Identity-H" in pdf
    with pdfust.open(stream=pdf) as doc:
        assert {span["wmode"] for span in doc[0].scan()["spans"]} == {0}
    with pdfust.open(stream=pdf.replace(b"/Encoding/Identity-H", b"/Encoding/Identity-V")) as doc:
        assert {span["wmode"] for span in doc[0].scan()["spans"]} == {1}
