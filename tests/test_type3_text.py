"""Type 3 text extraction as produced by Chromium/Skia for CJK and other scripts."""

from __future__ import annotations

import pylopdf
from conftest import build_raw_pdf


def _tounicode(mapping: dict[int, str]) -> str:
    rows = "\n".join(f"<{code:02X}> <{text.encode('utf-16-be').hex().upper()}>" for code, text in mapping.items())
    body = (
        "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /Adobe-Identity-UCS def\n/CMapType 2 def\n"
        "1 begincodespacerange\n<00> <FF>\nendcodespacerange\n"
        f"{len(mapping)} beginbfchar\n{rows}\nendbfchar\n"
        "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend"
    )
    return f"<< /Length {len(body)} >>\nstream\n{body}\nendstream"


def build_type3_pdf(
    mapping: dict[int, str], codes: bytes, *, width: int = 1000, content: str | None = None
) -> bytes:
    """One Chromium-style Type 3 font: flipped 0.001 FontMatrix, per-code widths, ToUnicode."""
    proc = f"{width} 0 0 -880 {width} 120 d1\n60 -800 {width - 120} 760 re f"
    names = " ".join(f"/g{code}" for code in mapping)
    procs = " ".join(f"/g{code} 6 0 R" for code in mapping)
    first, last = min(mapping), max(mapping)
    widths = " ".join(str(width) for _ in range(first, last + 1))
    if content is None:
        content = f"BT /F1 12 Tf 72 700 Td <{codes.hex().upper()}> Tj ET"
    return build_raw_pdf({
        1: "<< /Type /Catalog /Pages 2 0 R >>",
        2: "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> "
           "/Contents 4 0 R >>",
        4: f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        5: f"<< /Type /Font /Subtype /Type3 /FontBBox [0 -880 {width} 120] "
           "/FontMatrix [0.001 0 0 -0.001 0 0] "
           f"/CharProcs << {procs} >> /Encoding << /Type /Encoding /Differences [{first} {names}] >> "
           f"/FirstChar {first} /LastChar {last} /Widths [{widths}] /ToUnicode 7 0 R /Resources << >> >>",
        6: f"<< /Length {len(proc)} >>\nstream\n{proc}\nendstream",
        7: _tounicode(mapping),
    })


def test_full_width_type3_glyphs_do_not_gain_inferred_spaces() -> None:
    mapping = {1: "株", 2: "式", 3: "会", 4: "社", 5: "。"}
    doc = pylopdf.open(stream=build_type3_pdf(mapping, bytes([1, 2, 3, 4, 5])))
    assert doc.get_text().strip() == "株式会社。"


def test_hangul_and_kana_type3_glyphs_stay_contiguous() -> None:
    mapping = {1: "한", 2: "국", 3: "あ", 4: "カ", 5: "１"}
    doc = pylopdf.open(stream=build_type3_pdf(mapping, bytes([1, 2, 3, 4, 5])))
    assert doc.get_text().strip() == "한국あカ１"


def test_kangxi_and_supplement_radicals_map_to_unified_ideographs() -> None:
    # Skia's reverse cmap picks the lowest code point sharing a glyph, so a
    # ToUnicode entry can name U+2F47 KANGXI RADICAL SUN instead of U+65E5.
    mapping = {1: "⽇", 2: "⻘", 3: "⽉", 4: "本"}
    doc = pylopdf.open(stream=build_type3_pdf(mapping, bytes([1, 2, 3, 4])))
    assert doc.get_text().strip() == "日青月本"


def _utf16(text: str) -> str:
    return "FEFF" + text.encode("utf-16-be").hex().upper()


def test_actual_text_replaces_nul_mapped_contextual_glyphs() -> None:
    # Chromium maps contextual Arabic forms to U+0000 and wraps each character
    # in its own ActualText span; a span may also cover a base plus a mark glyph.
    mapping = {1: "\0", 2: "\0", 3: "\0", 4: "\0"}
    spans = [("\u0645", "01"), ("\u0631", "02"), ("\u062d\u064e", "0304")]
    # Right-to-left text is painted in visual order: the last character leftmost.
    body = " ".join(
        f"/Span << /ActualText <{_utf16(text)}> >> BDC <{codes}> Tj EMC" for text, codes in reversed(spans)
    )
    content = f"BT /F1 12 Tf 72 700 Td /ReversedChars BMC {body} EMC ET"
    doc = pylopdf.open(stream=build_type3_pdf(mapping, b"", width=500, content=content))
    text = doc.get_text().strip()
    assert "\0" not in text
    assert text == "\u0645\u0631\u062d\u064e"


def test_nul_mapping_outside_actual_text_is_dropped() -> None:
    mapping = {1: "\u0041", 2: "\0", 3: "\u0042"}
    doc = pylopdf.open(stream=build_type3_pdf(mapping, bytes([1, 3, 2]), width=500))
    assert doc.get_text().strip() == "AB"


def test_named_property_spans_keep_glyph_unicode() -> None:
    mapping = {1: "\u0041", 2: "\u0042"}
    content = (
        "BT /F1 12 Tf 72 700 Td /Span << /ActualText <FEFF0058> >> BDC <01> Tj EMC "
        "/Span /P0 BDC <02> Tj EMC ET"
    )
    doc = pylopdf.open(stream=build_type3_pdf(mapping, b"", width=500, content=content))
    assert doc.get_text().strip() == "XB"
