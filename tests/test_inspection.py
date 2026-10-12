"""Public inspection APIs: page scan, fonts, JavaScript, layers, attachments, widgets."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
from conftest import build_raw_pdf
from test_acroform import _build_form_pdf

import pdfust

ASSETS = Path(__file__).parent / "assets" / "real_world"


def _page_pdf(  # noqa: PLR0913 - test builder
    content: str,
    *,
    fonts: str = "/F1 3 0 R",
    extra: dict[int, str] | None = None,
    page_extra: str = "",
    catalog_extra: str = "",
    resources_extra: str = "",
) -> bytes:
    """One 300x200 page drawing ``content``; objects 6.. come from ``extra``."""
    objects: dict[int, bytes | str] = {
        1: f"<< /Type /Catalog /Pages 2 0 R {catalog_extra} >>",
        2: "<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
        3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        4: (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
            f"/Resources << /Font << {fonts} >> {resources_extra} >> /Contents 5 0 R {page_extra} >>"
        ),
        5: f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
    }
    objects.update(extra or {})
    return build_raw_pdf(objects)


def test_scan_reports_render_modes_and_invisible_text() -> None:
    content = (
        "BT /F1 12 Tf 30 150 Td (Fill) Tj ET "
        "BT /F1 12 Tf 1 Tr 30 120 Td (Stroke) Tj ET "
        "BT /F1 12 Tf 2 Tr 30 90 Td (Both) Tj ET "
        "BT /F1 12 Tf 3 Tr 30 60 Td (Hidden) Tj ET"
    )
    with pdfust.open(stream=_page_pdf(content)) as doc:
        spans = doc[0].get_text_spans()
    by_text = {span["text"]: span for span in spans}
    assert [span["text"] for span in spans] == ["Fill", "Stroke", "Both", "Hidden"]
    assert [by_text[t]["render_mode"] for t in ("Fill", "Stroke", "Both", "Hidden")] == [0, 1, 2, 3]
    assert [span["invisible"] for span in spans] == [False, False, False, True]
    # Fill+stroke is one run, not two overlapping ones.
    assert by_text["Both"]["glyphs"] == 4
    assert all(span["unmapped"] == 0 and not span["type3"] for span in spans)
    assert by_text["Fill"]["size"] == pytest.approx(12)
    box = by_text["Fill"]["bbox"]
    assert box.x0 == pytest.approx(30)
    assert 40 < box.y0 < 50  # display space: top-left origin (200 - 150 - ascent)


def test_scan_splits_runs_on_font_size_and_gaps() -> None:
    content = "BT /F1 12 Tf 30 150 Td (One) Tj /F1 18 Tf (Big) Tj ET BT /F1 12 Tf 200 150 Td (Far) Tj ET"
    with pdfust.open(stream=_page_pdf(content)) as doc:
        texts = [span["text"] for span in doc[0].get_text_spans()]
    assert texts == ["One", "Big", "Far"]


def test_scan_counts_unmapped_type3_glyphs() -> None:
    with pdfust.open(ASSETS / "pdfium-type3.pdf") as doc:
        page = doc[0]
        with pytest.warns(pdfust.PdfustWarning, match="no Unicode mapping"):
            scan = page.scan()
        fonts = page.get_fonts()
    assert scan["stats"]["unmapped"] == 3
    assert scan["stats"]["mapped"] == 0
    assert scan["stats"]["glyphs"] == 3
    assert sum(span["unmapped"] for span in scan["spans"]) == 3
    assert all(span["text"] == "" and span["type3"] for span in scan["spans"])
    assert [(f["type"], f["is_type3"], f["embedded"], f["has_tounicode"]) for f in fonts] == [
        ("Type3", True, True, False)
    ]


def test_scan_matches_text_extraction_and_leaves_caches_alone() -> None:
    doc = pdfust.Document()
    page = doc.new_page(width=300, height=200)
    page.insert_text((30, 80), "Right")
    page.insert_text((30, 120), "Left")
    before = page.get_text()
    spans = page.get_text_spans()
    assert "".join(span["text"] for span in spans) == "RightLeft"
    assert page.get_text() == before


def test_image_info_reports_pixels_and_effective_dpi_without_decoding() -> None:
    doc = pdfust.Document()
    page = doc.new_page(width=300, height=200)
    source = pdfust.Document()
    src_page = source.new_page(width=100, height=100)
    src_page.insert_text((10, 50), "x")
    png = src_page.render(dpi=144)  # 200x200 px
    page.insert_image((50, 50, 150, 150), stream=png)  # 100x100 pt
    infos = page.get_image_info()
    assert len(infos) == 1
    info = infos[0]
    assert (info["width"], info["height"]) == (200, 200)
    assert info["xdpi"] == pytest.approx(144, rel=0.02)
    assert info["dpi"] == pytest.approx(144, rel=0.02)
    assert info["bbox"].x0 == pytest.approx(50)
    assert info["bbox"].y1 == pytest.approx(150)
    assert info["stencil"] is False


def test_over_image_counts_text_on_large_host_images() -> None:
    doc = pdfust.Document()
    page = doc.new_page(width=300, height=200)
    source = pdfust.Document()
    source.new_page(width=300, height=200)
    page.insert_image((0, 0, 300, 200), stream=source[0].render(dpi=72))
    page.insert_text((30, 80), "Scan")
    scan = page.scan()
    assert scan["stats"]["over_image"] == 4
    assert page.scan(host_coverage=1.0)["images"][0]["width"] == 300
    with pytest.raises(ValueError, match="host_coverage"):
        page.scan(host_coverage=2.0)


def test_scan_rotated_page_uses_display_space() -> None:
    content = "BT /F1 12 Tf 30 150 Td (Hi) Tj ET"
    pdf = _page_pdf(content, page_extra="/Rotate 90")
    with pdfust.open(stream=pdf) as doc:
        scan = doc[0].scan()
        words = doc[0].get_text("words")
    assert (scan["width"], scan["height"]) == (200, 300)
    box = scan["spans"][0]["bbox"]
    word = words[0]
    assert box.x0 == pytest.approx(word[0], abs=3)
    assert box.y0 == pytest.approx(word[1], abs=3)


def test_fonts_inventory_for_composite_and_form_fonts() -> None:
    extra: dict[int, str] = {
        6: ("<< /Type /Font /Subtype /Type0 /BaseFont /ABCDEF+Body /Encoding /Identity-H /DescendantFonts [7 0 R] >>"),
        7: "<< /Type /Font /Subtype /CIDFontType2 /BaseFont /ABCDEF+Body /FontDescriptor 8 0 R >>",
        8: "<< /Type /FontDescriptor /FontName /ABCDEF+Body /FontFile2 9 0 R >>",
        9: "<< /Length 0 >>\nstream\n\nendstream",
        10: (
            "<< /Type /XObject /Subtype /Form /BBox [0 0 10 10] "
            "/Resources << /Font << /F9 11 0 R >> >> /Length 0 >>\nstream\n\nendstream"
        ),
        11: "<< /Type /Font /Subtype /TrueType /BaseFont /Courier /ToUnicode 9 0 R >>",
    }
    pdf = _page_pdf(
        "BT /F1 12 Tf 10 10 Td (x) Tj ET",
        fonts="/F1 3 0 R /F2 6 0 R",
        extra=extra,
        resources_extra="/XObject << /Fm 10 0 R >>",
    )
    with pdfust.open(stream=pdf) as doc:
        fonts = {font["name"]: font for font in doc.get_fonts()}
        page_fonts = doc[0].get_fonts()
    assert set(fonts) == {"Helvetica", "ABCDEF+Body", "Courier"}
    assert len(page_fonts) == 3
    helv = fonts["Helvetica"]
    assert (helv["type"], helv["embedded"], helv["has_tounicode"], helv["subset"]) == ("Type1", False, False, False)
    body = fonts["ABCDEF+Body"]
    assert (body["type"], body["descendant_type"], body["embedded"], body["subset"]) == (
        "Type0",
        "CIDFontType2",
        True,
        True,
    )
    assert body["encoding"] == "Identity-H"
    assert body["has_tounicode"] is False
    assert fonts["Courier"]["has_tounicode"] is True  # reached through the Form XObject
    assert fonts["Courier"]["pages"] == [1]


def test_javascript_detection_covers_catalog_pages_and_widgets() -> None:
    plain = pdfust.open(stream=_page_pdf("BT ET"))
    assert plain.has_javascript() is False
    assert plain.get_javascript() == []

    open_action = _page_pdf("BT ET", catalog_extra="/OpenAction << /S /JavaScript /JS (app.alert\\(1\\)) >>")
    with pdfust.open(stream=open_action) as doc:
        assert doc.get_javascript() == [{"scope": "open-action", "page": None, "event": None}]

    names = _page_pdf(
        "BT ET",
        extra={6: "<< /JavaScript << /Names [(init) 7 0 R] >> >>", 7: "<< /S /JavaScript /JS (1) >>"},
        catalog_extra="/Names 6 0 R",
    )
    with pdfust.open(stream=names) as doc:
        assert [item["scope"] for item in doc.get_javascript()] == ["names"]

    widget = _page_pdf(
        "BT ET",
        extra={
            6: (
                "<< /Type /Annot /Subtype /Widget /FT /Tx /T (f) /Rect [10 10 100 30] "
                "/AA << /K << /S /JavaScript /JS (1) >> >> >>"
            )
        },
        page_extra="/Annots [6 0 R]",
    )
    with pdfust.open(stream=widget) as doc:
        assert doc.get_javascript() == [{"scope": "form-field", "page": 1, "event": "K"}]
        assert doc.has_javascript() is True


def test_optional_content_groups_report_default_visibility() -> None:
    pdf = _page_pdf(
        "BT ET",
        extra={
            6: "<< /Type /OCG /Name (Watermark) >>",
            7: "<< /Type /OCG /Name (Body) /Intent /View >>",
        },
        catalog_extra="/OCProperties << /OCGs [6 0 R 7 0 R] /D << /OFF [6 0 R] >> >>",
    )
    with pdfust.open(stream=pdf) as doc:
        groups = doc.get_ocgs()
    assert [(g["xref"], g["name"], g["visible"]) for g in groups] == [(6, "Watermark", False), (7, "Body", True)]
    assert groups[1]["intent"] == ["View"]
    assert pdfust.Document().get_ocgs() == []


def test_embfile_info_reports_sizes_and_mime() -> None:
    doc = pdfust.Document()
    doc.new_page()
    payload = b"hello attachment" * 50
    doc.embfile_add("b.txt", payload)
    doc.embfile_add("a.xml", b"<x/>", desc="data")
    info = doc.embfile_info()
    assert [item["name"] for item in info] == ["a.xml", "b.txt"]
    sizes = {item["name"]: item["size"] for item in info}
    assert sizes["b.txt"] == len(payload)
    assert info[0]["description"] == "data"
    assert all(item["stored_size"] > 0 for item in info)
    assert doc.embfile_names() == ["a.xml", "b.txt"]


def test_widgets_per_page_with_kinds_and_values() -> None:
    with pdfust.open(stream=_build_form_pdf()) as doc:
        widgets = {w["name"]: w for w in doc[0].widgets()}
    assert widgets["customer"]["kind"] == "text"
    assert widgets["customer"]["value"] == "initial"
    assert widgets["customer"]["filled"] is True
    assert widgets["agree"]["kind"] == "checkbox"
    assert widgets["agree"]["filled"] is False
    assert widgets["person.first"]["kind"] == "text"  # type inherited from the parent
    assert widgets["person.first"]["filled"] is False
    assert widgets["level"]["kind"] == "combobox"
    assert widgets["plan"]["kind"] == "radio"
    rect = widgets["customer"]["rect"]
    assert (rect.x0, rect.x1) == (50, 250)
    assert rect.y0 == pytest.approx(792 - 720)  # display space is top-left origin


def test_closed_document_rejects_inspection() -> None:
    doc = pdfust.open(stream=_page_pdf("BT ET"))
    page = doc[0]
    doc.close()
    for call in (doc.get_fonts, doc.get_ocgs, doc.get_javascript, doc.embfile_info, page.scan, page.widgets):
        with pytest.raises(pdfust.PdfError):
            call()


def test_scan_respects_document_glyph_limits() -> None:
    content = "BT /F1 12 Tf 10 100 Td (" + "a" * 200 + ") Tj ET"
    limits = pdfust.DocumentLimits(max_text_glyphs=50)
    with pdfust.open(stream=_page_pdf(content), limits=limits) as doc, warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(pdfust.LimitError):
            doc[0].scan()
