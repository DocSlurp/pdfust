"""Hand-written raw PDF builders for the wild-v1 production-quirks dataset.

Each builder takes a few text lines (normally lifted from a wild-v1 truth file)
and writes one small, deterministic PDF that exercises a single font, encoding,
layout-transform, annotation or form quirk. Builders return the PDF bytes with
the exact visible text in reading order, so scorers do not have to infer it.

Everything here is pure Python plus PIL (bitmap Type 3 glyphs), pypdf (encoding
tables and post-processing) and pylopdf (embedded OpenType generation). No
external tools, network or GPU are used. See ``bench/wild_quirks.py``.
"""

# Builders intentionally keep PDF syntax inline and share a small object writer.
# ruff: noqa: PLR2004, PLR0913, PLR0917, EM101, EM102, TRY003, C901, PLC0415, ANN401, E501, D401, FBT001

from __future__ import annotations

import hashlib
import io
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

NOTO_SANS = Path("/usr/share/fonts/noto/NotoSans-Regular.ttf")

# Standard glyph names for printable ASCII (PDF 32000-1 Annex D).
ASCII_GLYPH_NAMES = [
    "space",
    "exclam",
    "quotedbl",
    "numbersign",
    "dollar",
    "percent",
    "ampersand",
    "quotesingle",
    "parenleft",
    "parenright",
    "asterisk",
    "plus",
    "comma",
    "hyphen",
    "period",
    "slash",
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "colon",
    "semicolon",
    "less",
    "equal",
    "greater",
    "question",
    "at",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "bracketleft",
    "backslash",
    "bracketright",
    "asciicircum",
    "underscore",
    "grave",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "braceleft",
    "bar",
    "braceright",
    "asciitilde",
]
# Standard Latin glyph names used by the /Differences cases.
LATIN_GLYPH_NAMES = {
    "é": "eacute", "è": "egrave", "ê": "ecircumflex", "ë": "edieresis", "É": "Eacute", "È": "Egrave",
    "à": "agrave", "â": "acircumflex", "ä": "adieresis", "Ä": "Adieresis", "ç": "ccedilla", "Ç": "Ccedilla",
    "î": "icircumflex", "ï": "idieresis", "ô": "ocircumflex", "ö": "odieresis", "Ö": "Odieresis",
    "ù": "ugrave", "û": "ucircumflex", "ü": "udieresis", "Ü": "Udieresis", "ß": "germandbls", "œ": "oe",
    "€": "Euro", "“": "quotedblleft", "”": "quotedblright", "„": "quotedblbase", "‘": "quoteleft",
    "’": "quoteright", "–": "endash", "—": "emdash", "°": "degree", "·": "periodcentered", "•": "bullet",
    "§": "section", "²": "twosuperior", "¹": "onesuperior", "×": "multiply", "±": "plusminus", "…": "ellipsis",
    " ": "space", "ñ": "ntilde", "á": "aacute", "í": "iacute", "ó": "oacute", "ú": "uacute",
}  # fmt: skip
MAC_OS_ONLY = (0xAD, 0xB0, 0xB2, 0xB3, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xBD, 0xC3, 0xC5, 0xC6, 0xD7, 0xF0)
ID_SEED = b"pdf-master wild-v1 quirks"


# ---------------------------------------------------------------------------
# Low-level object writer


def pdf_literal(data: bytes) -> bytes:
    """Return a PDF literal string with delimiters, escaping only what is required."""
    out = bytearray(b"(")
    for byte in data:
        if byte in b"()\\":
            out += b"\\" + bytes([byte])
        elif byte < 0x20 or byte > 0x7E:
            out += b"\\%03o" % byte
        else:
            out.append(byte)
    out += b")"
    return bytes(out)


def pdf_text_string(text: str) -> bytes:
    """Encode an Info/annotation text string as PDFDoc (ASCII) or UTF-16BE with BOM."""
    if all(32 <= ord(c) < 127 for c in text):
        return pdf_literal(text.encode("ascii"))
    return b"<FEFF" + text.encode("utf-16-be").hex().upper().encode() + b">"


def fmt(value: float) -> str:
    """Format a number compactly and deterministically."""
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return "0" if text in {"-0", ""} else text


@dataclass
class RawPdf:
    """Minimal deterministic PDF object writer with a classic cross-reference table."""

    version: str = "1.7"
    objects: list[bytes | None] = field(default_factory=list)

    def reserve(self) -> int:
        """Reserve an object number to fill later."""
        self.objects.append(None)
        return len(self.objects)

    def set(self, number: int, body: bytes) -> int:
        """Fill a reserved object."""
        self.objects[number - 1] = body
        return number

    def add(self, body: bytes | str) -> int:
        """Append one object and return its number."""
        self.objects.append(body.encode("latin-1") if isinstance(body, str) else body)
        return len(self.objects)

    def stream(self, entries: bytes | str, data: bytes, *, compress: bool = False) -> int:
        """Append a stream object; ``entries`` is the dictionary body without delimiters."""
        head = entries.encode("latin-1") if isinstance(entries, str) else entries
        if compress:
            data = zlib.compress(data, 9)
            head += b" /Filter /FlateDecode"
        return self.add(b"<< " + head + b" /Length %d >>\nstream\n" % len(data) + data + b"\nendstream")

    def build(self, root: int, info: int | None = None) -> bytes:
        """Serialize every object, the xref table and a content-derived file ID."""
        out = io.BytesIO()
        out.write(b"%PDF-" + self.version.encode() + b"\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        digest = hashlib.md5(ID_SEED, usedforsecurity=False)
        for number, body in enumerate(self.objects, start=1):
            if body is None:
                raise ValueError(f"object {number} was reserved but never written")
            offsets.append(out.tell())
            out.write(b"%d 0 obj\n" % number + body + b"\nendobj\n")
            digest.update(body)
        xref = out.tell()
        out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(self.objects) + 1))
        for offset in offsets:
            out.write(b"%010d 00000 n \n" % offset)
        file_id = digest.hexdigest().upper().encode()
        trailer = b"<< /Size %d /Root %d 0 R" % (len(self.objects) + 1, root)
        if info is not None:
            trailer += b" /Info %d 0 R" % info
        trailer += b" /ID [<" + file_id + b"> <" + file_id + b">] >>"
        out.write(b"trailer\n" + trailer + b"\nstartxref\n%d\n%%%%EOF\n" % xref)
        return out.getvalue()


@dataclass
class PageSpec:
    """One page: content stream, resource dictionary body and page-level entries."""

    content: bytes
    resources: bytes
    media_box: tuple[float, float, float, float] = (0, 0, 612, 792)
    extra: bytes = b""
    annots: list[int] = field(default_factory=list)


def finish(pdf: RawPdf, pages: Sequence[PageSpec], *, title: str, catalog_extra: bytes = b"") -> bytes:
    """Write the page tree, catalog and Info dictionary, then serialize."""
    tree = pdf.reserve()
    kids = []
    for page in pages:
        content = pdf.stream(b"", page.content)
        box = " ".join(fmt(v) for v in page.media_box).encode()
        body = b"<< /Type /Page /Parent %d 0 R /MediaBox [" % tree + box + b"] /Resources " + page.resources
        body += b" /Contents %d 0 R" % content + page.extra
        if page.annots:
            body += b" /Annots [" + b" ".join(b"%d 0 R" % n for n in page.annots) + b"]"
        kids.append(pdf.add(body + b" >>"))
    pdf.set(tree, b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % k for k in kids) + b"] /Count %d >>" % len(kids))
    root = pdf.add(b"<< /Type /Catalog /Pages %d 0 R" % tree + catalog_extra + b" >>")
    info = pdf.add(
        b"<< /Title " + pdf_text_string(title) + b" /Producer (pdf-master wild_quirks_raw)"
        b" /CreationDate (D:20260101000000Z) >>"
    )
    return pdf.build(root, info)


# ---------------------------------------------------------------------------
# Encodings


def encoding_table(name: str) -> dict[str, int]:
    """Map Unicode characters to single-byte codes for a PDF base or built-in encoding.

    ``name`` is one of StandardEncoding, WinAnsiEncoding, MacRomanEncoding,
    Symbol or ZapfDingbats. The lowest code wins when a character repeats.
    """
    from pypdf._codecs import charset_encoding

    table: dict[str, int] = {}
    source = list(charset_encoding["/" + name])
    if name == "MacRomanEncoding":
        # pypdf follows Mac OS Roman; PDF's MacRomanEncoding has /currency at 0xDB
        # and omits the Mac OS math symbols and the Apple logo (PDF 32000-1 Annex D).
        source[0xDB] = "\u00a4"
        for code in MAC_OS_ONLY:
            source[code] = ""
    for code, char in enumerate(source):
        if code >= 0x20 and char and char != "\x00" and char not in table:
            table[char] = code
    table.setdefault(" ", 0x20)  # Every base and built-in encoding names code 32 /space.
    if name in {"WinAnsiEncoding", "StandardEncoding", "MacRomanEncoding"}:
        table.setdefault(" ", 0x20)  # Authored no-break spaces print as plain spaces.
    return table


def encode(text: str, table: dict[str, int]) -> bytes:
    """Encode text through a single-byte table, raising on unmapped characters."""
    try:
        return bytes(table[char] for char in text)
    except KeyError as error:
        raise ValueError(f"character {error.args[0]!r} is not in the encoding") from error


def can_encode(text: str, table: dict[str, int]) -> bool:
    """Return whether every character of ``text`` has a code."""
    return all(char in table for char in text)


def tounicode_cmap(mapping: dict[int, str], code_bytes: int = 1) -> bytes:
    """Build a ToUnicode CMap with one bfchar per code."""
    width = code_bytes * 2
    lines = [
        b"/CIDInit /ProcSet findresource begin 12 dict begin begincmap",
        b"/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def",
        b"/CMapName /Adobe-Identity-UCS def /CMapType 2 def",
        b"1 begincodespacerange <" + b"00" * code_bytes + b"> <" + b"FF" * code_bytes + b"> endcodespacerange",
    ]
    items = sorted(mapping.items())
    for start in range(0, len(items), 100):
        chunk = items[start : start + 100]
        lines.append(b"%d beginbfchar" % len(chunk))
        lines.extend(
            b"<%s> <%s>" % (f"{code:0{width}X}".encode(), text.encode("utf-16-be").hex().upper().encode())
            for code, text in chunk
        )
        lines.append(b"endbfchar")
    lines.append(b"endcmap CMapName currentdict /CMap defineresource pop end end")
    return b"\n".join(lines) + b"\n"


def glyph_name(char: str, scheme: str) -> str:
    """Return the glyph name a producer using ``scheme`` would assign to ``char``."""
    if scheme == "uni":
        return f"uni{ord(char):04X}"
    if 0x20 <= ord(char) <= 0x7E:
        return ASCII_GLYPH_NAMES[ord(char) - 0x20]
    if char in LATIN_GLYPH_NAMES:
        return LATIN_GLYPH_NAMES[char]
    if scheme == "afii":
        from pypdf._codecs import adobe_glyphs

        names = sorted(n for n, v in adobe_glyphs.items() if v == char and n.startswith("/afii"))
        if names:
            return names[0][1:]
        return f"uni{ord(char):04X}"  # Producers fall back to uniXXXX outside the AGL afii range.
    raise ValueError(f"no {scheme} glyph name for {char!r}")


def custom_codes(lines: Sequence[str], keep_ascii: bool) -> dict[str, int]:
    """Assign producer-style single-byte codes in first-use order.

    With ``keep_ascii`` printable ASCII keeps its code and other characters
    receive codes from 1 upward, like subsetting producers that rewrite
    /Differences. Otherwise every distinct character gets the next code from 33.
    """
    codes: dict[str, int] = {}
    next_code = 1 if keep_ascii else 33
    for char in "".join(lines):
        if char in codes:
            continue
        if keep_ascii and 0x20 <= ord(char) <= 0x7E:
            codes[char] = ord(char)
            continue
        if next_code > 255 or (keep_ascii and next_code == 0x20):
            raise ValueError("too many distinct characters for one simple font")
        codes[char] = next_code
        next_code += 1
    return codes


# ---------------------------------------------------------------------------
# Font objects


def std14_font(pdf: RawPdf, base: str, encoding: str | None) -> int:
    """Add an unembedded Standard 14 Type 1 font with an optional base encoding name."""
    body = f"<< /Type /Font /Subtype /Type1 /BaseFont /{base}"
    if encoding:
        body += f" /Encoding /{encoding}"
    return pdf.add(body + " >>")


def differences_font(pdf: RawPdf, base: str, codes: dict[str, int], names: dict[str, str], *, tounicode: bool) -> int:
    """Add a Standard 14 font whose /Differences remap non-ASCII codes to glyph names."""
    diffs = " ".join(f"{code} /{names[char]}" for char, code in sorted(codes.items(), key=lambda i: i[1]) if code < 32)
    body = f"<< /Type /Font /Subtype /Type1 /BaseFont /{base} /Encoding << /Type /Encoding "
    body += f"/BaseEncoding /WinAnsiEncoding /Differences [{diffs}] >>"
    if tounicode:
        cmap = pdf.stream(b"", tounicode_cmap({code: char for char, code in codes.items()}))
        body += f" /ToUnicode {cmap} 0 R"
    return pdf.add(body + " >>")


def _bitmap_glyph(char: str, font: Any, px_per_em: int) -> tuple[bytes, float]:
    """Rasterize one glyph as an inline image mask charproc in 1000-unit glyph space."""
    from PIL import Image, ImageDraw

    scale = 1000 / px_per_em
    advance = font.getlength(char) * scale
    left, top, right, bottom = font.getbbox(char, anchor="ls")
    width, height = right - left, bottom - top
    if char.isspace() or width <= 0 or height <= 0:
        return f"{fmt(advance)} 0 0 0 0 0 d1".encode(), advance
    image = Image.new("L", (width, height), 255)
    ImageDraw.Draw(image).text((-left, -top), char, font=font, fill=0, anchor="ls")
    mask = image.point(lambda v: 255 if v > 127 else 0).convert("1")
    llx, lly, urx, ury = left * scale, -bottom * scale, right * scale, -top * scale
    data = mask.tobytes().hex().upper().encode() + b">"
    proc = (
        f"{fmt(advance)} 0 {fmt(llx)} {fmt(lly)} {fmt(urx)} {fmt(ury)} d1\n"
        f"q {fmt(urx - llx)} 0 0 {fmt(ury - lly)} {fmt(llx)} {fmt(lly)} cm\n"
        f"BI /IM true /W {width} /H {height} /BPC 1 /F /AHx ID\n"
    ).encode()
    return proc + data + b"\nEI Q", advance


def type3_bitmap_font(
    pdf: RawPdf,
    codes: dict[str, int],
    scheme: str,
    *,
    tounicode: bool,
    font_path: Path = NOTO_SANS,
    px_per_em: int = 100,
) -> tuple[int, dict[str, str]]:
    """Add a Type 3 font whose glyphs are bitmap masks named by ``scheme``.

    ``scheme`` is ``g`` (``/g33``-style producer names), ``uni`` (``/uni00E9``)
    or ``afii`` (Adobe names, ``/afii10017`` for Cyrillic). Returns the font
    object and the glyph name per character.
    """
    from PIL import ImageFont

    font = ImageFont.truetype(str(font_path), px_per_em)
    names: dict[str, str] = {}
    procs: list[bytes] = []
    widths: dict[int, float] = {}
    for char, code in sorted(codes.items(), key=lambda i: i[1]):
        name = f"g{code}" if scheme == "g" else glyph_name(char, scheme)
        names[char] = name
        proc, advance = _bitmap_glyph(char, font, px_per_em)
        number = pdf.stream(b"", proc)
        procs.append(f"/{name} {number} 0 R".encode())
        widths[code] = advance
    first, last = min(widths), max(widths)
    width_list = " ".join(fmt(widths.get(code, 0)) for code in range(first, last + 1))
    diffs = " ".join(f"{code} /{names[char]}" for char, code in sorted(codes.items(), key=lambda i: i[1]))
    char_procs = pdf.add(b"<< " + b" ".join(procs) + b" >>")
    body = (
        f"<< /Type /Font /Subtype /Type3 /FontBBox [0 -300 1200 1000] /FontMatrix [0.001 0 0 0.001 0 0] "
        f"/CharProcs {char_procs} 0 R /Encoding << /Type /Encoding /Differences [{diffs}] >> "
        f"/FirstChar {first} /LastChar {last} /Widths [{width_list}] /Resources << >>"
    )
    if tounicode:
        cmap = pdf.stream(b"", tounicode_cmap({code: char for char, code in codes.items()}))
        body += f" /ToUnicode {cmap} 0 R"
    return pdf.add(body + " >>"), names


# ---------------------------------------------------------------------------
# Content helpers


def text_block(
    font: str, size: float, x: float, y: float, encoded: Sequence[bytes], leading: float | None = None
) -> bytes:
    """Return a BT/ET block showing one encoded line per row with T* advances."""
    lead = leading or size * 1.35
    out = [f"BT /{font} {fmt(size)} Tf {fmt(lead)} TL {fmt(x)} {fmt(y)} Td".encode()]
    for index, line in enumerate(encoded):
        out.append((b"T* " if index else b"") + pdf_literal(line) + b" Tj")
    out.append(b"ET")
    return b"\n".join(out) + b"\n"


def helvetica_width(text: str, size: float) -> float:
    """Advance width of WinAnsi Helvetica text using MuPDF's Base 14 metrics."""
    import pymupdf

    # pymupdf.get_text_length maps only Latin-1; the Unicode Font covers WinAnsi's 0x80-0x9F glyphs.
    return float(pymupdf.Font("helv").text_length(text, fontsize=size))


def wrap(text: str, width: int) -> list[str]:
    """Greedy word wrap preserving words; long words stay on one line."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if current and len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


@dataclass
class RawResult:
    """One built raw quirk PDF and its exact expectations."""

    pdf: bytes
    expected_lines: list[str]
    hidden_lines: list[str] = field(default_factory=list)
    code_path: str = ""
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def expected_text(self) -> str:
        """Visible text in reading order, one line per row."""
        return "\n".join(self.expected_lines)


HELV_WIN = b"<< /Font << /F1 %d 0 R >> >>"


# ---------------------------------------------------------------------------
# Font/encoding builders


def build_simple_encoding(lines: Sequence[str], base: str, encoding: str | None, title: str) -> RawResult:
    """Standard 14 font with a predefined base or built-in encoding and no ToUnicode."""
    table = encoding_table(
        encoding or ("Symbol" if base == "Symbol" else "ZapfDingbats" if base == "ZapfDingbats" else "StandardEncoding")
    )
    pdf = RawPdf("1.4")
    font = std14_font(pdf, base, encoding)
    content = text_block("F1", 13, 56, 730, [encode(line, table) for line in lines], leading=19)
    page = PageSpec(content, HELV_WIN % font)
    label = encoding or "built-in encoding"
    return RawResult(
        finish(pdf, [page], title=title),
        list(lines),
        code_path=f"wild_quirks_raw.build_simple_encoding({base}, {label})",
    )


def build_differences_standard_names(lines: Sequence[str], base: str, title: str) -> RawResult:
    """WinAnsi base plus /Differences assigning standard names to low codes; no ToUnicode."""
    codes = custom_codes(lines, keep_ascii=True)
    names = {char: glyph_name(char, "standard") for char in codes}
    pdf = RawPdf("1.4")
    font = differences_font(pdf, base, codes, names, tounicode=False)
    content = text_block("F1", 13, 56, 730, [bytes(codes[c] for c in line) for line in lines], leading=19)
    remapped = {char: f"{code}=/{names[char]}" for char, code in codes.items() if code < 32}
    return RawResult(
        finish(pdf, [PageSpec(content, HELV_WIN % font)], title=title),
        list(lines),
        code_path="wild_quirks_raw.build_differences_standard_names",
        extra={"differences": remapped},
    )


def build_type3_names(lines: Sequence[str], scheme: str, *, tounicode: bool, title: str) -> RawResult:
    """Bitmap Type 3 font with producer glyph names, with or without ToUnicode."""
    codes = custom_codes(lines, keep_ascii=False)
    pdf = RawPdf("1.4")
    font, names = type3_bitmap_font(pdf, codes, scheme, tounicode=tounicode)
    content = text_block("T1", 13, 56, 730, [bytes(codes[c] for c in line) for line in lines], leading=19)
    return RawResult(
        finish(pdf, [PageSpec(content, b"<< /Font << /T1 %d 0 R >> >>" % font)], title=title),
        list(lines),
        code_path=f"wild_quirks_raw.build_type3_names(scheme={scheme}, tounicode={tounicode})",
        notes="Standard 14 fonts cannot draw non-AGL glyph names, so the names live in a bitmap Type 3 font "
        "rasterized from Noto Sans with PIL (like dvips PK fonts or Chromium Type 3 output).",
        extra={"glyph_names": dict(list(names.items())[:12])},
    )


# ---------------------------------------------------------------------------
# Layout-transform builders (Helvetica, WinAnsiEncoding)

WIN = "WinAnsiEncoding"


def _helv_pdf(version: str = "1.4") -> tuple[RawPdf, int, dict[str, int]]:
    pdf = RawPdf(version)
    return pdf, std14_font(pdf, "Helvetica", WIN), encoding_table(WIN)


def build_form_xobject_twice(lines: Sequence[str], title: str) -> RawResult:
    """Letterhead text inside one Form XObject that the page draws twice."""
    pdf, font, table = _helv_pdf()
    form_content = text_block("F1", 12, 0, 80, [encode(line, table) for line in lines], leading=16)
    form = pdf.stream(
        f"/Type /XObject /Subtype /Form /BBox [0 0 520 100] /Resources << /Font << /F1 {font} 0 R >> >>", form_content
    )
    content = b"q 1 0 0 1 56 640 cm /Fm0 Do Q\n0.6 G 56 600 m 556 600 l S\nq 1 0 0 1 56 440 cm /Fm0 Do Q\n"
    page = PageSpec(content, b"<< /XObject << /Fm0 %d 0 R >> >>" % form)
    return RawResult(
        finish(pdf, [page], title=title), [*lines, *lines], code_path="wild_quirks_raw.build_form_xobject_twice"
    )


def build_invisible_over_rect(visible: Sequence[str], hidden: Sequence[str], title: str) -> RawResult:
    """Render-mode 3 text over a filled rectangle, like an OCR layer over a pasted image."""
    pdf, font, table = _helv_pdf()
    content = text_block("F1", 14, 56, 740, [encode(line, table) for line in visible], leading=18)
    content += b"0.85 g 56 520 500 160 re f 0 g\n"
    content += b"3 Tr\n" + text_block("F1", 12, 64, 660, [encode(line, table) for line in hidden], leading=16)
    page = PageSpec(content, HELV_WIN % font)
    return RawResult(
        finish(pdf, [page], title=title),
        list(visible),
        hidden_lines=list(hidden),
        code_path="wild_quirks_raw.build_invisible_over_rect",
        notes="hidden_lines are drawn with 3 Tr (invisible) over a gray rectangle; they are not visible.",
    )


def _tj_kerned(line: str, table: dict[str, int]) -> bytes:
    """Encode a line as TJ with intra-word kerning and spaces replaced by large offsets."""
    parts: list[bytes] = []
    for word_index, word in enumerate(line.split(" ")):
        if word_index:
            parts.append(b"-278")  # Word gap expressed only as a TJ offset (no space glyph).
        for index in range(0, len(word), 3):
            if index:
                parts.append(b"-120")  # False intra-word gap of 0.12 em.
            parts.append(pdf_literal(encode(word[index : index + 3], table)))
    return b"[" + b" ".join(parts) + b"] TJ"


def build_spacing_operators(lines: Sequence[str], title: str) -> RawResult:
    """Tz horizontal scaling, Tc character spacing and TJ kerning that create false gaps."""
    pdf, font, table = _helv_pdf()
    ops = [b"BT /F1 12 Tf 18 TL 56 740 Td"]
    styles = [b"70 Tz 0 Tc", b"100 Tz 1.8 Tc", b"100 Tz 0 Tc", b"130 Tz -0.4 Tc"]
    for index, line in enumerate(lines):
        style = styles[index % len(styles)]
        show = _tj_kerned(line, table) if index % len(styles) == 2 else pdf_literal(encode(line, table)) + b" Tj"
        ops.append((b"T* " if index else b"") + style + b" " + show)
    ops.append(b"ET")
    page = PageSpec(b"\n".join(ops) + b"\n", HELV_WIN % font)
    return RawResult(
        finish(pdf, [page], title=title),
        list(lines),
        code_path="wild_quirks_raw.build_spacing_operators",
        notes="Line styles cycle: 70 Tz; 1.8 Tc; TJ with -120 intra-word kerning and -278 word gaps without "
        "space glyphs; 130 Tz with -0.4 Tc.",
    )


def build_per_glyph_tm(lines: Sequence[str], title: str) -> RawResult:
    """Every glyph positioned by its own Tm; spaces exist only as geometry."""
    pdf, font, table = _helv_pdf()
    ops = [b"BT /F1 12 Tf"]
    for row, line in enumerate(lines):
        x, y = 56.0, 740 - row * 18
        for char in line:
            if char != " ":
                ops.append(f"1 0 0 1 {fmt(x)} {fmt(y)} Tm ".encode() + pdf_literal(encode(char, table)) + b" Tj")
            x += helvetica_width(char, 12)
    ops.append(b"ET")
    return RawResult(
        finish(pdf, [PageSpec(b"\n".join(ops) + b"\n", HELV_WIN % font)], title=title),
        list(lines),
        code_path="wild_quirks_raw.build_per_glyph_tm",
    )


def build_fake_bold(lines: Sequence[str], title: str) -> RawResult:
    """Each line painted twice, offset by 0.3 pt, to simulate bold (overprint duplication)."""
    pdf, font, table = _helv_pdf()
    encoded = [encode(line, table) for line in lines]
    content = text_block("F1", 13, 56, 740, encoded, leading=19) + text_block("F1", 13, 56.3, 740, encoded, leading=19)
    return RawResult(
        finish(pdf, [PageSpec(content, HELV_WIN % font)], title=title),
        list(lines),
        code_path="wild_quirks_raw.build_fake_bold",
        notes="Visible text appears once; the duplicate paint is offset 0.3 pt horizontally.",
    )


def build_clipped_outside_cropbox(visible: Sequence[str], hidden: Sequence[str], title: str) -> RawResult:
    """Text drawn in the MediaBox but outside the CropBox, as left by imposition/cropping."""
    pdf, font, table = _helv_pdf()
    content = text_block("F1", 12, 72, 700, [encode(line, table) for line in visible], leading=17)
    content += text_block("F1", 10, 72, 30, [encode(hidden[0], table)])  # Below the CropBox.
    if len(hidden) > 1:
        content += text_block("F1", 10, 600, 400, [encode(line, table) for line in hidden[1:]])  # Right of it.
    page = PageSpec(content, HELV_WIN % font, media_box=(0, 0, 842, 842), extra=b" /CropBox [36 72 590 790]")
    return RawResult(
        finish(pdf, [page], title=title),
        list(visible),
        hidden_lines=list(hidden),
        code_path="wild_quirks_raw.build_clipped_outside_cropbox",
        notes="MediaBox [0 0 842 842], CropBox [36 72 590 790]; hidden_lines lie outside the CropBox.",
    )


def build_rotated_page(lines: Sequence[str], rotate: int, title: str) -> RawResult:
    """Portrait MediaBox with /Rotate; content is counter-rotated so it reads upright on screen."""
    pdf, font, table = _helv_pdf()
    ops = [b"BT /F1 13 Tf"]
    for row, line in enumerate(lines):
        if rotate == 90:
            ops.append(f"0 1 -1 0 {fmt(72 + row * 20)} 72 Tm ".encode() + pdf_literal(encode(line, table)) + b" Tj")
        elif rotate == 270:
            ops.append(f"0 -1 1 0 {fmt(540 - row * 20)} 720 Tm ".encode() + pdf_literal(encode(line, table)) + b" Tj")
        else:
            raise ValueError("rotate must be 90 or 270")
    ops.append(b"ET")
    page = PageSpec(b"\n".join(ops) + b"\n", HELV_WIN % font, extra=b" /Rotate %d" % rotate)
    return RawResult(
        finish(pdf, [page], title=title),
        list(lines),
        code_path=f"wild_quirks_raw.build_rotated_page(rotate={rotate})",
        notes="Displayed as landscape; text reads upright left-to-right after applying /Rotate.",
    )


def build_cropbox_origin(lines: Sequence[str], title: str) -> RawResult:
    """Large MediaBox with a CropBox whose origin is far from (0, 0)."""
    pdf, font, table = _helv_pdf()
    content = text_block("F1", 12, 340, 1140, [encode(line, table) for line in lines], leading=17)
    page = PageSpec(content, HELV_WIN % font, media_box=(0, 0, 1224, 1584), extra=b" /CropBox [300 400 912 1192]")
    return RawResult(finish(pdf, [page], title=title), list(lines), code_path="wild_quirks_raw.build_cropbox_origin")


def build_user_unit(lines: Sequence[str], title: str) -> RawResult:
    """PDF 1.6 /UserUnit 2: a 306x396-unit page displayed at US Letter size."""
    pdf, font, table = _helv_pdf("1.6")
    content = text_block("F1", 6.5, 28, 370, [encode(line, table) for line in lines], leading=9)
    page = PageSpec(content, HELV_WIN % font, media_box=(0, 0, 306, 396), extra=b" /UserUnit 2")
    return RawResult(finish(pdf, [page], title=title), list(lines), code_path="wild_quirks_raw.build_user_unit")


# ---------------------------------------------------------------------------
# Annotation and form builders


def _appearance(
    pdf: RawPdf, font: int, rect: tuple[float, float, float, float], lines: Sequence[str], size: float
) -> int:
    table = encoding_table(WIN)
    width, height = rect[2] - rect[0], rect[3] - rect[1]
    body = b"/Tx BMC q 1 1 " + f"{fmt(width - 2)} {fmt(height - 2)}".encode() + b" re W n\n"
    body += text_block("Helv", size, 3, height - size - 2, [encode(line, table) for line in lines], leading=size * 1.2)
    body += b"Q EMC\n"
    return pdf.stream(
        f"/Type /XObject /Subtype /Form /BBox [0 0 {fmt(width)} {fmt(height)}] /Resources << /Font << /Helv {font} 0 R >> >>",
        body,
    )


def build_freetext(lines: Sequence[str], note: Sequence[str], title: str) -> RawResult:
    """Page text plus a FreeText annotation whose text lives in /Contents and its appearance."""
    pdf, font, table = _helv_pdf()
    content = text_block("F1", 12, 56, 740, [encode(line, table) for line in lines], leading=17)
    rect = (330.0, 560.0, 556.0, 620.0)
    ap = _appearance(pdf, font, rect, note, 11)
    annot = pdf.add(
        b"<< /Type /Annot /Subtype /FreeText /Rect ["
        + " ".join(fmt(v) for v in rect).encode()
        + b"] /Contents "
        + pdf_text_string("\n".join(note))
        + b" /DA (/Helv 11 Tf 0 0 1 rg) /F 4 /AP << /N %d 0 R >> >>" % ap
    )
    page = PageSpec(content, HELV_WIN % font, annots=[annot])
    return RawResult(
        finish(pdf, [page], title=title),
        [*lines, *note],
        code_path="wild_quirks_raw.build_freetext",
        notes="The last expected lines exist only in a FreeText annotation (/Contents and /AP).",
    )


def build_acroform(
    labels: Sequence[str], values: Sequence[str], *, stored: Sequence[str | None], title: str
) -> RawResult:
    """Text fields whose visible value is only in each widget's appearance stream.

    ``stored`` gives each field's /V: ``None`` omits it (appearance-only value) and
    a different string reproduces a stale appearance that was never regenerated.
    """
    pdf, font, table = _helv_pdf()
    content = b""
    widgets = []
    expected = []
    for index, (label, value, stored_value) in enumerate(zip(labels, values, stored, strict=True)):
        y = 720 - index * 34
        content += text_block("F1", 11, 56, y + 6, [encode(label, table)])
        content += f"0.5 G {fmt(220)} {fmt(y)} 300 22 re S\n".encode()
        rect = (220.0, float(y), 520.0, float(y + 22))
        ap = _appearance(pdf, font, rect, [value], 11)
        body = (
            b"<< /Type /Annot /Subtype /Widget /FT /Tx /T "
            + pdf_literal(f"field{index + 1}".encode())
            + b" /Rect ["
            + " ".join(fmt(v) for v in rect).encode()
            + b"] /F 4 /DA (/Helv 11 Tf 0 g)"
            + b" /AP << /N %d 0 R >>" % ap
        )
        if stored_value is not None:
            body += b" /V " + pdf_text_string(stored_value)
        widgets.append(pdf.add(body + b" >>"))
        expected.append(f"{label} {value}")
    acroform = (
        b" /AcroForm << /Fields [" + b" ".join(b"%d 0 R" % w for w in widgets) + b"]"
        b" /DA (/Helv 0 Tf 0 g) /DR << /Font << /Helv %d 0 R >> >> /NeedAppearances false >>" % font
    )
    page = PageSpec(content, HELV_WIN % font, annots=widgets)
    return RawResult(
        finish(pdf, [page], title=title, catalog_extra=acroform),
        expected,
        code_path="wild_quirks_raw.build_acroform",
        extra={"field_values_stored": list(stored)},
        notes="Each expected line is a static label followed by the value drawn only by the widget appearance.",
    )


# ---------------------------------------------------------------------------
# Embedded OpenType (pylopdf/krilla) and post-processing


def build_embedded(
    lines: Sequence[str], font_path: Path, title: str, *, font_index: int = 0, size: float = 13
) -> RawResult:
    """Identity-H subset font with ToUnicode, generated by pylopdf ``Page.insert_text``."""
    import pylopdf

    document = pylopdf.open()
    page = document.new_page(width=595, height=842)
    for row, line in enumerate(lines):
        page.insert_text((56, 80 + row * size * 1.6), line, fontsize=size, fontfile=font_path, fontindex=font_index)
    document.set_metadata({"title": title})
    data = document.tobytes(garbage=True, deflate=True)
    return RawResult(
        data,
        list(lines),
        code_path=f"pylopdf {pylopdf.__version__} Page.insert_text(fontfile={font_path.name}, fontindex={font_index})",
    )


def _rewrite_fonts(data: bytes, edit: Callable[[Any], bool]) -> tuple[bytes, int]:
    """Apply ``edit`` to every font dictionary reachable from page resources."""
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(data)))
    changed = 0
    seen: set[int] = set()

    def visit(resources: Any, depth: int) -> None:
        nonlocal changed
        if resources is None or depth > 8:
            return
        resources = resources.get_object()
        for font in (resources.get("/Font") or {}).values():
            font_object = font.get_object()
            if id(font_object) not in seen:
                seen.add(id(font_object))
                changed += bool(edit(font_object))
        for xobject in (resources.get("/XObject") or {}).values():
            stream = xobject.get_object()
            if stream.get("/Subtype") == "/Form":
                visit(stream.get("/Resources"), depth + 1)

    for page in writer.pages:
        visit(page.get("/Resources"), 0)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue(), changed


def strip_tounicode(data: bytes) -> tuple[bytes, int]:
    """Remove /ToUnicode from every reachable font; returns the PDF and the count removed."""

    def edit(font: Any) -> bool:
        return font.pop("/ToUnicode", None) is not None

    return _rewrite_fonts(data, edit)


def make_vertical(data: bytes) -> tuple[bytes, int]:
    """Switch Type 0 fonts from Identity-H to Identity-V (WMode 1) without moving the origin."""
    from pypdf.generic import ArrayObject, NameObject, NumberObject

    def edit(font: Any) -> bool:
        if font.get("/Subtype") != "/Type0":
            return False
        font[NameObject("/Encoding")] = NameObject("/Identity-V")
        for descendant in font.get("/DescendantFonts", []):
            descendant.get_object()[NameObject("/DW2")] = ArrayObject([NumberObject(880), NumberObject(-1000)])
        return True

    return _rewrite_fonts(data, edit)


def build_vertical(columns: Sequence[str], font_path: Path, title: str, *, font_index: int = 0) -> RawResult:
    """Vertical CJK columns, right to left, drawn with an Identity-V subset font."""
    import pylopdf

    document = pylopdf.open()
    page = document.new_page(width=595, height=842)
    for index, column in enumerate(columns):
        page.insert_text((520 - index * 26, 70), column, fontsize=16, fontfile=font_path, fontindex=font_index)
    document.set_metadata({"title": title})
    data, changed = make_vertical(document.tobytes(garbage=True, deflate=True))
    return RawResult(
        data,
        list(columns),
        code_path=f"pylopdf {pylopdf.__version__} Page.insert_text + wild_quirks_raw.make_vertical (Identity-H -> Identity-V)",
        notes="pylopdf and PyMuPDF only write horizontal text, so the generated Identity-H Type 0 font is switched "
        "to Identity-V with /DW2 [880 -1000]; each insert_text call becomes one top-to-bottom column, read "
        "right to left. Punctuation keeps horizontal glyph forms (no vert GSUB substitution).",
        extra={"type0_fonts_switched": changed},
    )


def build_symbol_bullets(items: Sequence[str], font: str, bullets: Sequence[str], title: str) -> RawResult:
    """List items whose bullets are drawn in Symbol or ZapfDingbats, item text in Helvetica.

    A last line repeats the bullet glyphs alone, as in legends and checklists.
    """
    pdf, helv, table = _helv_pdf()
    symbol_table = encoding_table(font)
    symbol = std14_font(pdf, font, None)
    ops = []
    expected = []
    for row, item in enumerate(items):
        bullet = bullets[row % len(bullets)]
        y = 740 - row * 20
        ops.append(f"BT /S1 12 Tf 60 {y} Td ".encode() + pdf_literal(encode(bullet, symbol_table)) + b" Tj ET")
        ops.append(f"BT /F1 12 Tf 78 {y} Td ".encode() + pdf_literal(encode(item, table)) + b" Tj ET")
        expected.append(f"{bullet} {item}")
    legend = " ".join(bullets)
    y = 740 - len(items) * 20 - 10
    ops.append(f"BT /S1 14 Tf 60 {y} Td ".encode() + pdf_literal(encode(legend, symbol_table)) + b" Tj ET")
    expected.append(legend)
    resources = b"<< /Font << /F1 %d 0 R /S1 %d 0 R >> >>" % (helv, symbol)
    return RawResult(
        finish(pdf, [PageSpec(b"\n".join(ops) + b"\n", resources)], title=title),
        expected,
        code_path=f"wild_quirks_raw.build_symbol_bullets({font})",
        notes=f"Bullets use the built-in {font} encoding (no /Encoding, no ToUnicode).",
    )


# ---------------------------------------------------------------------------
# Stream filter encoders (decoded by any conforming reader)


def ascii_hex_encode(data: bytes) -> bytes:
    """ASCIIHexDecode payload with 64-byte lines and the ``>`` terminator."""
    text = data.hex().upper().encode()
    return b"\n".join(text[i : i + 128] for i in range(0, len(text), 128)) + b">"


def ascii85_encode(data: bytes) -> bytes:
    """ASCII85Decode payload terminated by ``~>``."""
    import base64

    return base64.a85encode(data, wrapcol=76) + b"~>"


def run_length_encode(data: bytes) -> bytes:
    """RunLengthDecode payload: literal runs up to 128 bytes, repeats up to 128, EOD 128."""
    out = bytearray()
    index = 0
    size = len(data)
    while index < size:
        run = 1
        while index + run < size and run < 128 and data[index + run] == data[index]:
            run += 1
        if run > 1:
            out += bytes([257 - run, data[index]])
            index += run
            continue
        start = index
        while index < size and index - start < 128 and not (index + 1 < size and data[index + 1] == data[index]):
            index += 1
        if index == start:  # Next byte begins a repeat; emit it as a one-byte literal run.
            index += 1
        out.append(index - start - 1)
        out += data[start:index]
    out.append(128)
    return bytes(out)


def lzw_encode(data: bytes) -> bytes:
    """LZWDecode payload with the default /EarlyChange 1 and 9-12 bit codes."""
    bits = 0
    nbits = 0
    out = bytearray()

    def write(code: int, width: int) -> None:
        nonlocal bits, nbits
        bits = (bits << width) | code
        nbits += width
        while nbits >= 8:
            nbits -= 8
            out.append((bits >> nbits) & 0xFF)
        bits &= (1 << nbits) - 1

    def reset() -> dict[bytes, int]:
        return {bytes([i]): i for i in range(256)}

    table = reset()
    next_code, width = 258, 9
    write(256, width)
    current = b""
    for value in data:
        candidate = current + bytes([value])
        if candidate in table:
            current = candidate
            continue
        write(table[current], width)
        table[candidate] = next_code
        next_code += 1
        if next_code >= 4094:
            write(256, width)
            table, next_code, width = reset(), 258, 9
        elif next_code >= (1 << width):
            width += 1
        current = bytes([value])
    if current:
        write(table[current], width)
        if next_code + 1 >= (1 << width) and width < 12:
            width += 1  # The decoder adds one entry for the final code before reading EOD.
    write(257, width)
    if nbits:
        out.append((bits << (8 - nbits)) & 0xFF)
    return bytes(out)


FILTER_ENCODERS: dict[str, tuple[list[str], Callable[[bytes], bytes]]] = {
    "asciihex": (["/ASCIIHexDecode"], ascii_hex_encode),
    "ascii85_flate": (["/ASCII85Decode", "/FlateDecode"], lambda d: ascii85_encode(zlib.compress(d, 9))),
    "lzw": (["/LZWDecode"], lzw_encode),
    "runlength": (["/RunLengthDecode"], run_length_encode),
}


def reencode_content_streams(data: bytes, filter_key: str, password: str = "") -> tuple[bytes, int]:
    """Re-encode page content streams and Form XObjects with one filter chain via pypdf."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, NameObject

    names, encoder = FILTER_ENCODERS[filter_key]
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        reader.decrypt(password)
    writer = PdfWriter(clone_from=reader)
    seen: set[int] = set()
    count = 0

    def recode(stream: Any) -> None:
        nonlocal count
        if id(stream) in seen:
            return
        seen.add(id(stream))
        decoded = stream.get_data()
        stream.pop("/DecodeParms", None)
        stream[NameObject("/Filter")] = (
            NameObject(names[0]) if len(names) == 1 else ArrayObject(NameObject(n) for n in names)
        )
        stream._data = encoder(decoded)  # noqa: SLF001 - pypdf writes _data verbatim with the new /Filter.
        count += 1

    def visit(resources: Any, depth: int) -> None:
        if resources is None or depth > 8:
            return
        for xobject in (resources.get_object().get("/XObject") or {}).values():
            stream = xobject.get_object()
            if stream.get("/Subtype") == "/Form":
                recode(stream)
                visit(stream.get("/Resources"), depth + 1)

    for page in writer.pages:
        contents = page.get("/Contents")
        if contents is not None:
            contents = contents.get_object()
            for item in contents if isinstance(contents, list) else [contents]:
                recode(item.get_object())
        visit(page.get("/Resources"), 0)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue(), count
