"""Ground truth for scoring PDF-to-Markdown element recovery.

Reuses the synthetic fixtures in ``bench.feature_cases`` and adds focused cases
whose expected headings, emphasis, lists, code, tables, links, math, and images
are known exactly from the generating content stream. Independent corpus pages
have no structural ground truth and are not scored.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bench.feature_cases import build_cases, raw_pdf, stream_object, text_op

if TYPE_CHECKING:
    from collections.abc import Callable

FRACTION = r"\frac{x^2+1}{y}=z^2"


@dataclass(frozen=True)
class Link:
    """A link label and its exact URI, or the text its internal target must reach."""

    label: str
    uri: str | None = None
    internal_target: str | None = None


@dataclass(frozen=True)
class Truth:
    """Known structure of one fixture; empty fields are not scored for the case."""

    text: tuple[str, ...] = ()
    order: tuple[str, ...] = ()
    headings: tuple[tuple[str, int], ...] = ()
    bold: tuple[str, ...] = ()
    italic: tuple[str, ...] = ()
    code_inline: tuple[str, ...] = ()
    code_block: tuple[str, ...] = ()
    list_items: tuple[tuple[str, bool, int], ...] = ()
    literals: tuple[str, ...] = ()
    # Each cell lists acceptable values; "" is a genuinely empty cell.
    table: tuple[tuple[tuple[str, ...], ...], ...] = ()
    links: tuple[Link, ...] = ()
    math: tuple[str, ...] = ()
    images: int = 0
    image_order: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScoreCase:
    """One input PDF and its ground truth."""

    name: str
    data: bytes
    truth: Truth
    source: str = "Repository-authored synthetic PDF; repository MIT license"
    notes: str = ""


def _page(content: str, *, extra_page: str = "", extras: tuple[bytes | str, ...] = ()) -> bytes:
    """Build a one-page PDF with WinAnsi Standard 14 fonts so bullets and dashes map to Unicode."""
    font = "<< /Type /Font /Subtype /Type1 /BaseFont /{} /Encoding /WinAnsiEncoding >>"
    return raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
                f"/Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R /F4 8 0 R >> {extra_page} >> >>"
            ),
            stream_object(content),
            font.format("Helvetica"),
            font.format("Helvetica-Bold"),
            font.format("Helvetica-Oblique"),
            font.format("Courier"),
            *extras,
        ]
    )


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _runs(runs: list[tuple[str, str]], x: float, y: float, size: float = 11) -> str:
    """Show consecutive font runs in one text object so positions advance naturally."""
    shown = " ".join(f"/{font} {size} Tf ({_escape(text)}) Tj" for text, font in runs)
    return f"BT {x} {y} Td {shown} ET"


# Helvetica AFM advances for right-aligned numeric cells.
_WIDTHS = {**dict.fromkeys("0123456789", 556), ",": 278, "Q": 778, "T": 611, "o": 611, "t": 333, "a": 556, "l": 278}


def _width(text: str, size: float) -> float:
    return sum(_WIDTHS.get(char, 556) for char in text) * size / 1000


def _headings_case() -> ScoreCase:
    content = "\n".join(
        [
            text_op("Annual Report", 40, 740, size=26),
            text_op("Overview", 40, 700, size=18),
            text_op("Revenue grew steadily during the year while operating costs remained flat.", 40, 676, size=11),
            text_op("The board approved two new regional offices in the second half.", 40, 662, size=11),
            text_op("Regional detail", 40, 630, size=14, font="F2"),
            text_op("Northern offices reported the strongest growth of all regions.", 40, 610, size=11),
            text_op("Methods", 40, 578, size=18),
            text_op("Figures are unaudited and rounded to the nearest thousand.", 40, 556, size=11),
        ]
    )
    return ScoreCase(
        "score-headings",
        _page(content),
        Truth(
            text=("Revenue grew steadily", "nearest thousand"),
            headings=(("Annual Report", 1), ("Overview", 2), ("Regional detail", 3), ("Methods", 2)),
        ),
        notes="Three font-size tiers (26/18/14 bold) over 11 pt body text.",
    )


def _emphasis_case() -> ScoreCase:
    content = "\n".join(
        [
            _runs(
                [
                    ("The results were ", "F1"),
                    ("statistically significant", "F2"),
                    (" across all ", "F1"),
                    ("three cohorts", "F3"),
                    (".", "F1"),
                ],
                40,
                700,
            ),
            _runs(
                [
                    ("Use the ", "F1"),
                    ("--verbose", "F4"),
                    (" flag to print ", "F1"),
                    ("detailed", "F2"),
                    (" diagnostics.", "F1"),
                ],
                40,
                680,
            ),
            text_op("Each measurement was repeated five times and the median value is reported.", 40, 660, size=11),
        ]
    )
    return ScoreCase(
        "score-inline-emphasis",
        _page(content),
        Truth(
            text=("The results were", "across all", "flag to print", "median value is reported"),
            bold=("statistically significant", "detailed"),
            italic=("three cohorts",),
            code_inline=("--verbose",),
        ),
        notes="Mid-line font switches inside one text object: bold, italic, and a Courier token.",
    )


def _lists_case() -> ScoreCase:
    bullet, dash = "\x95", "\x96"
    rows = [
        (f"{bullet} Apples", 50, 700),
        (f"{bullet} Bread", 50, 682),
        (f"{dash} Whole wheat", 70, 664),
        (f"{dash} Sourdough", 70, 646),
        (f"{bullet} Coffee", 50, 628),
        ("Steps to follow:", 40, 596),
        ("1. Preheat the oven", 50, 578),
        ("2. Mix the ingredients", 50, 560),
        ("3. Bake for twenty minutes", 50, 542),
    ]
    return ScoreCase(
        "score-lists",
        _page("\n".join(text_op(text, x, y, size=11) for text, x, y in rows)),
        Truth(
            text=("Apples", "Whole wheat", "Steps to follow:", "Bake for twenty minutes"),
            list_items=(
                ("Apples", False, 0),
                ("Bread", False, 0),
                ("Whole wheat", False, 1),
                ("Sourdough", False, 1),
                ("Coffee", False, 0),
                ("Preheat the oven", True, 0),
                ("Mix the ingredients", True, 0),
                ("Bake for twenty minutes", True, 0),
            ),
        ),
        notes="WinAnsi bullet and en-dash glyphs with indentation, then a numbered list.",
    )


CODE_LINES = (
    "def total(values):",
    "    result = 0",
    "    for value in values:",
    "        result += value",
    "    return result",
)


def _code_case() -> ScoreCase:
    ops = [
        text_op("Example function", 40, 740, size=16),
        text_op("The helper below sums a sequence of numbers.", 40, 712, size=11),
    ]
    for row, line in enumerate(CODE_LINES):
        indent = len(line) - len(line.lstrip(" "))
        # Courier advances 600/1000 em, so 10 pt indentation is 6 pt per space.
        ops.append(text_op(line.lstrip(" "), 40 + indent * 6, 686 - row * 13, size=10, font="F4"))
    return ScoreCase(
        "score-code-block",
        _page("\n".join(ops)),
        Truth(text=("sums a sequence",), code_block=CODE_LINES),
        notes="Five Courier lines with 4/8-space indentation encoded only by x position.",
    )


def _links_case() -> ScoreCase:
    labels = [
        ("Project homepage", "<< /S /URI /URI (https://example.com/home) >>"),
        ("Contact support", "<< /S /URI /URI (mailto:support@example.com) >>"),
        ("API reference", "<< /S /URI /URI (https://example.com/api?v=2&lang=en) >>"),
    ]
    first = "\n".join(text_op(label, 40, 720 - row * 30) for row, (label, _) in enumerate(labels))
    first += "\n" + text_op("Go to appendix", 40, 630)
    annots = [
        f"<< /Type /Annot /Subtype /Link /Rect [40 {716 - row * 30} 160 {734 - row * 30}] /A {action} >>"
        for row, (_, action) in enumerate(labels)
    ]
    annots.append("<< /Type /Annot /Subtype /Link /Rect [40 626 160 644] /Dest [4 0 R /XYZ 40 740 null] >>")
    second = text_op("Appendix", 40, 740, size=18) + "\n" + text_op("Supplementary tables are listed here.", 40, 710)
    data = raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R "
                "/Resources << /Font << /F1 7 0 R >> >> /Annots [8 0 R 9 0 R 10 0 R 11 0 R] >>"
            ),
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 6 0 R "
                "/Resources << /Font << /F1 7 0 R >> >> >>"
            ),
            stream_object(first),
            stream_object(second),
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            *annots,
        ]
    )
    return ScoreCase(
        "score-links",
        data,
        Truth(
            text=("Project homepage", "Contact support", "API reference", "Supplementary tables"),
            links=(
                Link("Project homepage", uri="https://example.com/home"),
                Link("Contact support", uri="mailto:support@example.com"),
                Link("API reference", uri="https://example.com/api?v=2&lang=en"),
                Link("Go to appendix", internal_target="Appendix"),
            ),
        ),
        notes="HTTPS, mailto, query-string, and direct page-destination link annotations.",
    )


SALES = (
    ("Region", "Q1", "Q2", "Total"),
    ("North", "1,200", "1,350", "2,550"),
    ("South", "980", "1,105", "2,085"),
    ("East", "1,410", "1,390", "2,800"),
    ("West", "760", "845", "1,605"),
)


def _sales_case(*, bordered: bool) -> ScoreCase:
    edges = (40, 200, 320, 440, 560)
    ops = [text_op("Quarterly sales", 40, 740, size=18)]
    top = 700
    for row, values in enumerate(SALES):
        baseline = top - row * 24 - 16
        for column, value in enumerate(values):
            font = "F2" if row == 0 else "F1"
            if column == 0:
                ops.append(text_op(value, edges[0] + 8, baseline, size=11, font=font))
            else:
                ops.append(text_op(value, edges[column + 1] - 8 - _width(value, 11), baseline, size=11, font=font))
    if bordered:
        bottom = top - len(SALES) * 24
        ops.extend(f"{edges[0]} {top - row * 24} m {edges[-1]} {top - row * 24} l" for row in range(len(SALES) + 1))
        ops.extend(f"{x} {bottom} m {x} {top} l" for x in edges)
        ops.append("S")
    ops.append(text_op("Values are in thousands of units.", 40, 560, size=10))
    return ScoreCase(
        "score-table-" + ("bordered" if bordered else "borderless"),
        _page("\n".join(ops)),
        Truth(
            text=("Quarterly sales", "thousands of units"),
            table=tuple(tuple((value,) for value in row) for row in SALES),
        ),
        notes="Five rows by four columns with right-aligned comma-grouped numbers"
        + ("; full vector grid." if bordered else "; no rules."),
    )


def _math_inline_case() -> ScoreCase:
    def rise(base: str, script: str, after: str, offset: float) -> list[str]:
        return [f"({_escape(base)}) Tj", f"/F1 7 Tf {offset} Ts ({script}) Tj 0 Ts /F1 12 Tf", f"({_escape(after)}) Tj"]

    energy = ["BT /F1 12 Tf 40 700 Td", *rise("Energy: E = mc", "2", " where c is the speed of light.", 5), "ET"]
    water = ["BT /F1 12 Tf 40 670 Td", *rise("Water is H", "2", "O at room temperature.", -3), "ET"]
    pythagoras = [
        "BT /F1 12 Tf 220 630 Td",
        *rise("a", "2", " + b", 5),
        "/F1 7 Tf 5 Ts (2) Tj 0 Ts /F1 12 Tf ( = c) Tj /F1 7 Tf 5 Ts (2) Tj 0 Ts",
        "ET",
    ]
    return ScoreCase(
        "score-math-scripts",
        _page("\n".join([*energy, *water, *pythagoras])),
        Truth(text=("speed of light", "room temperature"), math=("mc^2", "H_2O", "a^2+b^2=c^2")),
        notes="Superscripts and subscripts drawn with text rise (Ts); a centered display equation.",
    )


def _rgb_image(width: int, height: int, pixel: Callable[[int, int], tuple[int, int, int]]) -> bytes:
    raw = bytes(channel for y in range(height) for x in range(width) for channel in pixel(x, y))
    return stream_object(
        zlib.compress(raw),
        f"/Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace /DeviceRGB "
        "/BitsPerComponent 8 /Filter /FlateDecode",
    )


def _images_case() -> ScoreCase:
    content = "\n".join(
        [
            text_op("Image gallery", 40, 750, size=18),
            "q 160 0 0 120 40 600 cm /Im1 Do Q",
            text_op("Figure 1: Red block", 40, 585, size=10),
            "q 160 0 0 120 40 430 cm /Im2 Do Q",
            text_op("Figure 2: Blue gradient", 40, 415, size=10),
            text_op("Both figures are synthetic rasters without OCR text.", 40, 380, size=11),
        ]
    )
    data = raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
                "/Resources << /Font << /F1 5 0 R >> /XObject << /Im1 6 0 R /Im2 7 0 R >> >> >>"
            ),
            stream_object(content),
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            _rgb_image(32, 24, lambda _x, _y: (220, 30, 30)),
            _rgb_image(32, 24, lambda x, y: (20, 20 + x * 4, 120 + y * 5)),
        ]
    )
    return ScoreCase(
        "score-images",
        data,
        Truth(
            text=("Figure 1: Red block", "Figure 2: Blue gradient"),
            images=2,
            image_order=("Image gallery", "<image>", "Figure 1", "<image>", "Figure 2"),
        ),
        notes="Two distinct rasters, each followed by its caption.",
    )


def _grid(rows: list[list[str | tuple[str, ...]]]) -> tuple[tuple[tuple[str, ...], ...], ...]:
    return tuple(tuple(cell if isinstance(cell, tuple) else (cell,) for cell in row) for row in rows)


_EXISTING: dict[str, Truth] = {
    "text-structure-and-literals": Truth(
        headings=(("Section heading", 1),),
        bold=("Bold phrase",),
        italic=("Italic phrase",),
        code_inline=("code_value = 42",),
        list_items=(("First item", True, 0), ("Second item", True, 0), ("Nested bullet", False, 1)),
        literals=("*asterisks*", "[brackets]", "# hash", "<tag>", "\\ backslash"),
    ),
    "positioned-math": Truth(math=(FRACTION,)),
    "math-actualtext": Truth(math=(FRACTION,)),
    "omml-equations": Truth(math=(FRACTION,), bold=("Bold body",), italic=("Italic body",)),
    "table-bordered": Truth(table=_grid([["Left", "Center", "Right"], ["Alpha", "A|B", "42"], ["Beta", "C\\D", ""]])),
    "table-borderless": Truth(table=_grid([["Left", "Center", "Right"], ["Alpha", "A|B", "42"], ["Beta", "C\\D", ""]])),
    "table-merged": Truth(
        table=_grid([["Merged header", ("Merged header", ""), "Right"], ["Alpha", "A|B", "42"], ["Beta", "C\\D", ""]])
    ),
    "table-borderless-aligned": Truth(
        table=_grid([["Name", "Amount"], ["Alpha", "42"], ["Beta", "7"], ["Gamma", "16"]])
    ),
    "links-and-outline": Truth(
        links=(
            Link("External documentation", uri="https://example.org/docs"),
            Link("Jump to second page", internal_target="Destination section"),
            Link("Named section", internal_target="Destination section"),
        )
    ),
    "images-and-vectors": Truth(images=1),
    "image-only": Truth(images=1),
}


def score_cases() -> list[ScoreCase]:
    """Return every scored fixture; corpus pages without ground truth are excluded."""
    cases = []
    for case in build_cases():
        if case.name.startswith("corpus-"):
            continue
        truth = _EXISTING.get(case.name, Truth())
        truth = Truth(**{**truth.__dict__, "text": case.expected_text, "order": case.expected_order})
        cases.append(ScoreCase(case.name, case.data, truth, case.source, case.notes))
    cases.extend(
        [
            _headings_case(),
            _emphasis_case(),
            _lists_case(),
            _code_case(),
            _links_case(),
            _sales_case(bordered=True),
            _sales_case(bordered=False),
            _math_inline_case(),
            _images_case(),
        ]
    )
    return cases


__all__ = ["CODE_LINES", "FRACTION", "Link", "ScoreCase", "Truth", "score_cases"]
