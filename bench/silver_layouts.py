"""Repository-authored development PDFs with explicit layout template ancestry.

These are silver observations, not independent producers or held-out ground truth.
Visible anchors describe source content; they do not prescribe inferred relations.
"""

from __future__ import annotations

import zlib
from typing import Any

from bench.feature_cases import stream_object, text_op

FAMILIES = (
    "two-column",
    "three-column",
    "image-inset",
    "image-flow",
    "headers-footers",
    "rotated-page",
    "cropped-page",
    "merged-table",
    "multilevel-table",
    "form-fields",
    "sidebar",
    "footnotes",
    "reading-order",
    "duplicate-overprint",
    "vector-noise",
    "mixed-panels",
)


FAMILY_NOTES = {
    "two-column": "Two dense columns share baseline bands, with full-width title and conclusion.",
    "three-column": "Three dense columns share baseline bands and include a full-width conclusion.",
    "image-inset": "A 16x16 RGB XObject is placed beside eleven text lines; continuation sits below its caption.",
    "image-flow": "Two actual RGB placements have different scales; text sits beside and below both figures.",
    "headers-footers": "Two or three physical pages repeat a header and footer, with distinct page and section labels.",
    "rotated-page": "Page dictionary rotation is 90, 180, or 270 degrees; text and a raster use unrotated PDF space.",
    "cropped-page": "CropBox offsets exclude one painted outside-crop phrase; visible anchors omit that phrase.",
    "merged-table": "Vector rules form a three-column grid with a two-column merged first header and three data rows.",
    "multilevel-table": "A merged group header and subordinate labels occupy two header bands above data rows.",
    "form-fields": "A real AcroForm text widget has a normal appearance; visible checkbox marks are vector drawings.",
    "sidebar": "A gray-filled sidebar sits beside sixteen article lines; its seven short facts have separate geometry.",
    "footnotes": "Bracketed body references and two smaller-font footnotes are separated by a horizontal rule.",
    "reading-order": "Right-column operators precede left-column operators despite left-to-right column geometry.",
    "duplicate-overprint": "Exact, half-point-offset, and distinct baseline-sharing overprints are painted.",
    "vector-noise": "Forty-five diagonal gray rules decorate the page and cross ordinary foreground text.",
    "mixed-panels": "A bordered prose panel, actual raster with caption, and lower full-width prose share one page.",
}


def _serialize(objects: list[bytes | str], version: str) -> bytes:
    output = bytearray(f"%PDF-{version}\n%\xe2\xe3\xcf\xd3\n".encode("latin-1"))
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(output))
        data = body.encode("latin-1") if isinstance(body, str) else body
        output.extend(f"{number} 0 obj\n".encode() + data + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(output)


def _pdf(contents: list[str], variant: int, family: str, version: str) -> bytes:
    # Fonts and the image are shared within the document, including repeated pages.
    count = len(contents)
    font = 3 + count * 2
    bold, image = font + 1, font + 2
    widget = image + 1
    catalog_extra = (
        f"/AcroForm << /Fields [{widget} 0 R] /DR << /Font << /F1 {font} 0 R >> >> /DA (/F1 12 Tf 0 g) >>"
        if family == "form-fields"
        else ""
    )
    objects: list[bytes | str] = [
        f"<< /Type /Catalog /Pages 2 0 R {catalog_extra} >>",
        f"<< /Type /Pages /Count {count} /Kids [{' '.join(f'{3 + i * 2} 0 R' for i in range(count))}] >>",
    ]
    for index, content in enumerate(contents):
        page_extra = ""
        if family == "rotated-page":
            page_extra = f"/Rotate {(variant % 3 + 1) * 90}"
        elif family == "cropped-page":
            page_extra = f"/CropBox [{20 + variant * 2} 24 580 760]"
        elif family == "form-fields" and index == 0:
            page_extra = f"/Annots [{widget} 0 R]"
        objects.extend(
            [
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {4 + index * 2} 0 R "
                    f"/Resources << /Font << /F1 {font} 0 R /F2 {bold} 0 R >> "
                    f"/XObject << /Im1 {image} 0 R >> >> {page_extra} >>"
                ),
                stream_object(zlib.compress(content.encode("latin-1")), "/Filter /FlateDecode")
                if variant % 2
                else stream_object(content),
            ]
        )
    encoding = "/Encoding /WinAnsiEncoding" if variant % 2 else ""
    objects.extend(
        [
            f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica {encoding} >>",
            f"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold {encoding} >>",
            stream_object(
                zlib.compress(
                    bytes(
                        (x * 13 % 256, y * 17 % 256, (x + y) * 9 % 256)[c]
                        for y in range(16)
                        for x in range(16)
                        for c in range(3)
                    )
                ),
                (
                    "/Type /XObject /Subtype /Image /Width 16 /Height 16 /ColorSpace /DeviceRGB "
                    "/BitsPerComponent 8 /Filter /FlateDecode"
                ),
            ),
        ]
    )
    if family == "form-fields":
        appearance = widget + 1
        objects.extend(
            [
                (
                    "<< /Type /Annot /Subtype /Widget /FT /Tx /T (customer) /V (Ada Example) "
                    f"/Rect [170 570 430 600] /P 3 0 R /F 4 /AP << /N {appearance} 0 R >> >>"
                ),
                stream_object(
                    "0.95 g 0 0 260 30 re f 0 g 0 0 260 30 re S\n" + text_op("Ada Example", 8, 10),
                    f"/Type /XObject /Subtype /Form /BBox [0 0 260 30] /Resources << /Font << /F1 {font} 0 R >> >>",
                ),
            ]
        )
    return _serialize(objects, version)


# Explicit branches keep each authored layout readable beside its geometry.
def _content(family: str, variant: int, page: int) -> tuple[str, list[str]]:  # noqa: C901, PLR0912
    ops: list[str] = []
    anchors: list[str] = []
    shift = variant * 3

    def label(value: str, x: float, y: float, size: float = 11, *, bold: bool = False) -> None:
        anchors.append(value)
        ops.append(text_op(value, x + shift, y, size=size, font="F2" if bold else "F1"))

    def rows(prefix: str, x: float, y: float, count: int = 8, width: str = "body words keep this line dense") -> None:
        for row in range(count):
            label(f"{prefix} {row + 1}: {width}", x, y - row * (17 + variant))

    def raster(x: float, y: float, width: float, height: float) -> None:
        ops.append(f"q {width} 0 0 {height} {x} {y} cm /Im1 Do Q")

    label(f"Report {FAMILIES.index(family) * 4 + variant + 1:03d} page {page + 1}", 40, 738, 18, bold=True)
    if family in {"two-column", "three-column"}:
        columns = 2 if family == "two-column" else 3
        for column in range(columns):
            rows(
                f"Column {column + 1}",
                40 + column * (270 if family == "two-column" else 185),
                685,
                width="clear body text" if family == "two-column" else "dense words",
            )
        label("Full width conclusion", 40, 420)
    elif family in {"image-inset", "image-flow"}:
        raster(330, 470, 190, 180)
        label("Figure 1: authored color raster", 320, 450)
        rows("Beside figure", 40, 665, 11, "text wraps along inset")
        rows("Below figure", 40, 410, 5, "full width paragraph after the raster with more words")
        if family == "image-flow":
            raster(40, 250, 130, 100)
            rows("Second wrap", 195, 335, 5, "text beside smaller image")
    elif family == "headers-footers":
        label("Recurring report header", 40, 775, 9)
        rows(f"Section {page + 1}", 40, 680, 14)
        label("Recurring report footer", 40, 25, 9)
        label(f"Page {page + 1}", 510, 25, 9)
    elif family in {"rotated-page", "cropped-page"}:
        rows("Display coordinates", 55, 670, 10)
        raster(300, 300, 160, 110)
        label("Visible raster caption", 300, 280)
        if family == "cropped-page":
            ops.append(text_op("Outside crop", 5, 10))
    elif family in {"merged-table", "multilevel-table"}:
        xs = [40, 200, 365, 550]
        ys = [680, 645, 610, 575, 540, 505]
        ops.extend(f"40 {y} m 550 {y} l S" for y in ys)
        ops.extend(f"{x} 505 m {x} 680 l S" for x in (xs[0], xs[-1]))
        ops.extend(["200 505 m 200 645 l S", "365 505 m 365 680 l S"])
        label("Regional totals", 65, 658, 12, bold=True)
        label("Year", 395, 658, 12, bold=True)
        for column, title in enumerate(("East", "West", "Combined")):
            label(title, xs[column] + 10, 622, 11, bold=True)
        for row in range(3):
            for column in range(3):
                label(f"R{row + 1}C{column + 1} {10 * (row + 1) + column + variant}", xs[column] + 10, 587 - row * 35)
        if family == "multilevel-table":
            label("Grouped metrics", 40, 455, 14, bold=True)
            label("North / local / net", 40, 420)
            label("South / local / net", 40, 395)
    elif family == "form-fields":
        label("Customer name", 40, 580)
        label("Ada Example", 180, 580)
        label("Delivery preferences", 40, 525, 13, bold=True)
        for row, value in enumerate(("Standard service", "Priority service", "Pickup service")):
            ops.append(f"40 {490 - row * 35} 12 12 re S")
            label(value, 65, 491 - row * 35)
        ops.append("42 493 m 46 489 l 51 499 l S")
        label("Signed: A. Example", 40, 330)
    elif family == "sidebar":
        ops.append("0.92 g 385 425 170 260 re f 0 g")
        rows("Main article", 40, 680, 16, "ordinary prose line")
        label("Sidebar key facts", 395, 660, 12, bold=True)
        rows("Fact", 395, 630, 7, "short note")
        label("Article continuation", 40, 360)
    elif family == "footnotes":
        rows("Body reference [1]", 40, 680, 15)
        ops.append("40 190 m 300 190 l S")
        label("[1] Source note with visible reference marker", 40, 165, 9)
        label("[2] Additional note: cafe and resume", 40, 148, 9)
    elif family == "reading-order":
        # Paint order intentionally differs from geometric column order.
        rows("Right painted first", 315, 680, 9, "reading order words")
        rows("Left painted second", 40, 680, 9, "reading order words")
        label("Cross-column ending", 40, 450)
    elif family == "duplicate-overprint":
        rows("Base content", 40, 680, 9)
        label("Overprinted phrase", 40, 450)
        ops.append(text_op("Overprinted phrase", 40 + shift, 450))
        label("Offset duplicate", 40, 410)
        ops.append(text_op("Offset duplicate", 41 + shift, 410.5))
        label("Distinct overlay", 40, 370)
        ops.append(text_op("Alternate overlay", 40 + shift, 370))
        anchors.append("Alternate overlay")
    elif family == "vector-noise":
        ops.extend(f"0.7 G {35 + line * 11} 240 m {45 + line * 11} 700 l S" for line in range(45))
        ops.append("0 G")
        rows("Readable foreground", 40, 680, 14)
        label("Noise is vector decoration", 40, 390)
    else:
        raster(365, 460, 150, 150)
        ops.append("40 450 250 190 re S")
        label("Panel A body", 55, 615, 13, bold=True)
        rows("Panel A", 55, 585, 6, "short text")
        label("Panel B raster caption", 345, 440)
        rows("Lower full width", 40, 380, 8)
    if variant % 2:
        label("Encoding sample: caf\xe9 \xa3 25", 40, 80, 10)
    return "\n".join(ops), anchors


def generate_cases() -> list[dict[str, Any]]:
    """Return 64 deterministic silver-development records from 16 template families."""
    result: list[dict[str, Any]] = []
    versions = ("1.3", "1.4", "1.5", "1.7")
    for family in FAMILIES:
        for variant in range(len(versions)):
            page_count = 2 + variant % 2 if family == "headers-footers" else 1 + (variant == len(versions) - 1)
            contents, anchors = [], []
            for page in range(page_count):
                content, visible = _content(family, variant, page)
                contents.append(content)
                anchors.extend(visible)
            version = versions[variant]
            result.append(
                {
                    "id": f"layout-{family}-v{variant + 1}",
                    "family": family,
                    "flavors": [
                        family,
                        "multipage" if page_count > 1 else "single-page",
                        "flate-content" if variant % 2 else "plain-content",
                    ],
                    "pdf": _pdf(contents, variant, family, version),
                    "expected_text": anchors,
                    "notes": "Development/silver fixture. Visible source anchors only; "
                    "geometric relationships require review. "
                    "Standard 14 fonts are unembedded. Four variants share one template ancestry; "
                    "they are not independent producers. "
                    + FAMILY_NOTES[family]
                    + " "
                    + (
                        "Actual RGB image placements with beside/below text geometry."
                        if family in {"image-inset", "image-flow", "mixed-panels", "rotated-page", "cropped-page"}
                        else ""
                    ),
                    "producer_group": f"repository-classic-layout/{family}",
                    "encoding": "WinAnsiEncoding" if variant % 2 else "StandardEncoding",
                    "license": "MIT",
                    "provenance": "repository-authored",
                    "page_count": page_count,
                    "pdf_version": version,
                }
            )
    return result
