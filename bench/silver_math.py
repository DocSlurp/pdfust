"""Forty authored math encoding probes, with silver references rather than gold semantics.

Four expressions share ten PDF producer variants. They are controlled interventions,
not forty independent documents or an exhaustive catalog of mathematical typography.
The tiny block glyphs below are repository-authored; no external fonts are embedded.
"""

from __future__ import annotations

import zlib
from typing import TypedDict

from bench.feature_cases import raw_pdf, stream_object, text_op


class MathCase(TypedDict):
    """Keep visual anchors separate from unverified mathematical references."""

    id: str
    family: str
    flavors: list[str]
    pdf: bytes
    expected_text: list[str]
    reference_math: str
    notes: str
    producer_group: str
    encoding: str
    license: str
    provenance: str


# Five columns by seven rows; original block lettering for deterministic PDF paths.
_GLYPHS = {
    "A": "01110/10001/10001/11111/10001/10001/10001",
    "B": "11110/10001/10001/11110/10001/10001/11110",
    "C": "01111/10000/10000/10000/10000/10000/01111",
    "D": "11110/10001/10001/10001/10001/10001/11110",
    "E": "11111/10000/10000/11110/10000/10000/11111",
    "F": "11111/10000/10000/11110/10000/10000/10000",
    "G": "01111/10000/10000/10111/10001/10001/01111",
    "H": "10001/10001/10001/11111/10001/10001/10001",
    "I": "11111/00100/00100/00100/00100/00100/11111",
    "J": "00111/00010/00010/00010/00010/10010/01100",
    "K": "10001/10010/10100/11000/10100/10010/10001",
    "L": "10000/10000/10000/10000/10000/10000/11111",
    "M": "10001/11011/10101/10101/10001/10001/10001",
    "N": "10001/11001/10101/10011/10001/10001/10001",
    "O": "01110/10001/10001/10001/10001/10001/01110",
    "P": "11110/10001/10001/11110/10000/10000/10000",
    "Q": "01110/10001/10001/10001/10101/10010/01101",
    "R": "11110/10001/10001/11110/10100/10010/10001",
    "S": "01111/10000/10000/01110/00001/00001/11110",
    "T": "11111/00100/00100/00100/00100/00100/00100",
    "U": "10001/10001/10001/10001/10001/10001/01110",
    "V": "10001/10001/10001/10001/10001/01010/00100",
    "W": "10001/10001/10001/10101/10101/10101/01010",
    "X": "10001/10001/01010/00100/01010/10001/10001",
    "Y": "10001/10001/01010/00100/00100/00100/00100",
    "Z": "11111/00001/00010/00100/01000/10000/11111",
    "0": "01110/10001/10011/10101/11001/10001/01110",
    "1": "00100/01100/00100/00100/00100/00100/01110",
    "2": "01110/10001/00001/00010/00100/01000/11111",
    "3": "11110/00001/00001/01110/00001/00001/11110",
    "4": "00010/00110/01010/10010/11111/00010/00010",
    "5": "11111/10000/10000/11110/00001/00001/11110",
    "6": "01110/10000/10000/11110/10001/10001/01110",
    "7": "11111/00001/00010/00100/01000/01000/01000",
    "8": "01110/10001/10001/01110/10001/10001/01110",
    "9": "01110/10001/10001/01111/00001/00001/01110",
    "+": "00000/00100/00100/11111/00100/00100/00000",
    "-": "00000/00000/00000/11111/00000/00000/00000",
    "*": "00000/10101/01110/11111/01110/10101/00000",
    "/": "00001/00001/00010/00100/01000/10000/10000",
    "^": "00100/01010/10001/00000/00000/00000/00000",
    "=": "00000/00000/11111/00000/11111/00000/00000",
    "(": "00010/00100/01000/01000/01000/00100/00010",
    ")": "01000/00100/00010/00010/00010/00100/01000",
    "[": "01110/01000/01000/01000/01000/01000/01110",
    "]": "01110/00010/00010/00010/00010/00010/01110",
    ",": "00000/00000/00000/00000/00100/00100/01000",
    ".": "00000/00000/00000/00000/00000/00100/00100",
    ";": "00000/00100/00100/00000/00100/00100/01000",
    " ": "00000/00000/00000/00000/00000/00000/00000",
}

# These references are declared before extraction. ASCII notation is deliberate;
# the fixtures do not promise a semantic MathML tree or traditional glyph shapes.
FORMULAS = (
    (
        "quadratic",
        ("X = (-B +/- SQRT(B^2 - 4*A*C))/(2*A)", "D = B^2 - 4*A*C; A*X^2 + B*X + C = 0"),
        r"x_{\pm}=\frac{-b\pm\sqrt{b^2-4ac}}{2a},\quad ax^2+bx+c=0",
    ),
    (
        "gaussian",
        ("I(A) = INTEGRAL[-INF,INF] EXP(-A*X^2) DX", "I(A) = SQRT(PI/A); I'(A) = -I(A)/(2*A)"),
        r"I(a)=\int_{-\infty}^{\infty}e^{-ax^2}\,dx=\sqrt{\pi/a},\quad I'(a)=-\frac{I(a)}{2a}",
    ),
    (
        "fourier",
        ("F(X) = A0/2 + SUM[N=1,INF]", "(AN*COS(N*X) + BN*SIN(N*X))", "AN = INTEGRAL[-PI,PI] F(X)*COS(N*X) DX/PI"),
        (
            r"f(x)=\frac{a_0}{2}+\sum_{n=1}^{\infty}(a_n\cos nx+b_n\sin nx),"
            r"\quad a_n=\frac1\pi\int_{-\pi}^{\pi}f(x)\cos nx\,dx"
        ),
    ),
    (
        "matrix",
        ("M = [A B; C D]; DET(M-L*I)", "= (A-L)*(D-L) - B*C = 0", "L = (A+D +/- SQRT((A-D)^2+4*B*C))/2"),
        (
            r"M=\begin{pmatrix}a&b\\c&d\end{pmatrix},\quad\det(M-\lambda I)=0,"
            r"\quad\lambda_{\pm}=\frac{a+d\pm\sqrt{(a-d)^2+4bc}}2"
        ),
    ),
)
ENCODINGS = (
    "literal-tj",
    "split-kerned-tj",
    "positioned-math",
    "tounicode-multichar",
    "type3-mapped",
    "type3-unmapped",
    "actualtext",
    "vector-outlines",
    "raster-image",
    "raster-invisible-text",
)


def _rectangles(text: str) -> list[tuple[int, int]]:
    return [
        (index * 600 + column * 80, (6 - row) * 80)
        for index, char in enumerate(text)
        for row, pattern in enumerate(_GLYPHS[char].split("/"))
        for column, bit in enumerate(pattern)
        if bit == "1"
    ]


def _paths(text: str) -> str:
    return "\n".join(f"{x} {y} 75 75 re f" for x, y in _rectangles(text))


def _literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _cmap(tokens: list[str]) -> bytes:
    pairs = "\n".join(f"<{index:02X}> <{token.encode('utf-16-be').hex()}>" for index, token in enumerate(tokens, 1))
    return stream_object(
        "/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n"
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /AuthoredMath def /CMapType 2 def\n"
        "1 begincodespacerange <01> <FF> endcodespacerange\n"
        f"{len(tokens)} beginbfchar\n{pairs}\nendbfchar\n"
        "endcmap CMapName currentdict /CMap defineresource pop end end"
    )


def _type3(lines: tuple[str, ...], *, mapped: bool, multichar: bool) -> tuple[list[bytes | str], list[str]]:
    chunks = [
        [line[i : i + (2 if multichar else 1)] for i in range(0, len(line), 2 if multichar else 1)] for line in lines
    ]
    tokens = sorted({token for row in chunks for token in row})
    codes = {token: index for index, token in enumerate(tokens, 1)}
    procedures = " ".join(f"/g{index} {7 + index} 0 R" for index in range(1, len(tokens) + 1))
    encoding = " ".join(f"{index} /g{index}" for index in range(1, len(tokens) + 1))
    widths = " ".join(str(len(token) * 600) for token in tokens)
    font = (
        "<< /Type /Font /Subtype /Type3 /FontBBox [0 0 1200 700] "
        "/FontMatrix [0.001 0 0 0.001 0 0] /Resources << >> "
        f"/CharProcs << {procedures} >> /Encoding << /Type /Encoding /Differences [{encoding}] >> "
        f"/FirstChar 1 /LastChar {len(tokens)} /Widths [{widths}] " + ("/ToUnicode 7 0 R " if mapped else "") + ">>"
    )
    # Object 7 is a reserved CMap slot even in the intentionally unmapped font.
    extras: list[bytes | str] = [font, _cmap(tokens) if mapped else "null"]
    extras.extend(
        stream_object(f"{len(token) * 600} 0 0 0 {len(token) * 600} 700 d1\n{_paths(token)}") for token in tokens
    )
    runs = [
        f"BT /Math 14 Tf 1 0 0 1 40 {620 - row * 40} Tm "
        f"<{''.join(f'{codes[token]:02x}' for token in chunks[row])}> Tj ET"
        for row in range(len(lines))
    ]
    return extras, runs


def _raster(lines: tuple[str, ...]) -> bytes:
    width, height = max(map(len, lines)) * 12, len(lines) * 20
    pixels = bytearray(b"\xff" * (width * height))
    for row, line in enumerate(lines):
        for x, y in _rectangles(line):
            left, top = x // 40, row * 20 + (480 - y) // 40
            for dy in range(2):
                for dx in range(2):
                    pixels[(top + dy) * width + left + dx] = 0
    return stream_object(
        zlib.compress(pixels),
        f"/Type /XObject /Subtype /Image /Width {width} /Height {height} "
        "/ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode",
    )


def _positioned(lines: tuple[str, ...]) -> list[str]:
    """Raise powers/subscripts and add a stacked fraction from the same expression."""
    ops: list[str] = []
    for row, line in enumerate(lines):
        x, y, index = 40.0, 620.0 - row * 65, 0
        while index < len(line):
            char = line[index]
            if char == "^" and index + 1 < len(line):
                ops.append(text_op(line[index + 1], x, y + 9, size=9, font="F1"))
                x += 6
                index += 2
                continue
            # Numeric/coefficient suffixes are displayed as subscripts.
            if char in "N0" and index > 0 and line[index - 1] in "AB":
                ops.append(text_op(char, x, y - 5, size=9, font="F1"))
                x += 6
            else:
                ops.append(text_op(char, x, y, size=12, font="F1"))
                x += 7.2
            index += 1
        # A second stacked rendering demonstrates explicit fraction geometry.
    if lines[0].startswith("X ="):
        label, numerator, denominator, suffix = "X =", "-B +/- SQRT(B^2 - 4*A*C)", "2*A", ""
    elif lines[0].startswith("I(A)"):
        label, numerator, denominator, suffix = "I PRIME(A) =", "-I(A)", "2*A", ""
    elif lines[0].startswith("F(X)"):
        label, numerator, denominator = "F(X) =", "A0", "2"
        suffix = "+ SUM[N=1,INF] (AN*COS(N*X) + BN*SIN(N*X))"
    else:
        label, numerator, denominator, suffix = "L =", "A+D +/- SQRT((A-D)^2+4*B*C)", "2", ""
    left = 40 + len(label) * 7.2 + 10
    right = left + max(len(numerator), len(denominator)) * 7.2
    ops.extend(
        [
            text_op(label, 40, 330, size=12),
            text_op(numerator, left, 340, size=12),
            f"{left} 335 m {right} 335 l S",
            text_op(denominator, (left + right) / 2 - len(denominator) * 3.6, 318, size=12),
        ]
    )
    if suffix:
        ops.append(text_op(suffix, right + 10, 330, size=10))
    return ops


def _pdf(lines: tuple[str, ...], anchor: str, encoding: str) -> bytes:
    ops = [
        "1 1 1 rg 0 0 612 792 re f 0 0 0 rg",
        text_op(anchor, 40, 740, size=16),
        text_op("Technical appendix", 40, 710),
    ]
    extras: list[bytes | str] = []
    resources = "/Font << /F1 5 0 R >>"
    if encoding in ("type3-mapped", "type3-unmapped", "tounicode-multichar"):
        extras, runs = _type3(lines, mapped=encoding != "type3-unmapped", multichar=encoding == "tounicode-multichar")
        resources = "/Font << /F1 5 0 R /Math 6 0 R >>"
        ops.extend(runs)
    elif encoding == "vector-outlines":
        ops.extend(f"q .014 0 0 .014 40 {620 - row * 40} cm\n{_paths(line)}\nQ" for row, line in enumerate(lines))
    elif encoding.startswith("raster-"):
        extras = [_raster(lines)]
        resources += " /XObject << /Formula 6 0 R >>"
        width, height = max(map(len, lines)) * 8.4, len(lines) * 14
        ops.append(f"q {width} 0 0 {height} 40 {620 - height} cm /Formula Do Q")
        if encoding == "raster-invisible-text":
            ops.append("3 Tr")
            ops.extend(text_op(line, 40, 620 - row * 40, size=14) for row, line in enumerate(lines))
            ops.append("0 Tr")
    elif encoding == "positioned-math":
        ops.extend(_positioned(lines))
    else:
        for row, line in enumerate(lines):
            if encoding == "split-kerned-tj":
                show = "[" + " -8 ".join(f"({_literal(char)})" for char in line) + "] TJ"
            else:
                show = f"({_literal(line)}) Tj"
            run = f"BT /F1 12 Tf 1 0 0 1 40 {620 - row * 40} Tm {show} ET"
            if encoding == "actualtext":
                actual = ("\ufeff" + line).encode("utf-16-be").hex()
                run = f"/Span << /ActualText <{actual}> >> BDC\n{run}\nEMC"
            ops.append(run)
    return raw_pdf(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << {resources} >> >>",
            stream_object("\n".join(ops)),
            "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
            *extras,
        ]
    )


def generate_cases() -> list[MathCase]:
    """Return exactly forty deterministic PDF inputs and declared silver references."""
    cases: list[MathCase] = []
    for name, original_lines, reference in FORMULAS:
        lines = tuple(line.replace("'", " PRIME") for line in original_lines)
        for encoding in ENCODINGS:
            case_id = f"math-{name}-{encoding}"
            anchor = f"Reference {len(cases) + 1:03d}"
            notes = (
                "Silver authored reference: review mathematical structure manually. Four repeated expressions "
                "across ten related producer variants; no exhaustive coverage or independent holdout claim. "
                "ASCII function names stand for mathematical operators; block-letter appearances are intentional. "
            )
            if encoding == "type3-unmapped":
                notes += (
                    "Type3 formula has no ToUnicode map: expected extraction limitation; "
                    "visible anchor remains extractable. "
                )
            if encoding == "actualtext":
                notes += (
                    "ActualText matches the visible ASCII formula; this does not prove replacement support. "
                    "Hayro extraction may ignore marked-content replacement. "
                )
            if encoding == "tounicode-multichar":
                notes += "Type3 two-character glyphs map through UTF-16BE ToUnicode; this is not a CID font test. "
            if encoding == "positioned-math":
                notes += (
                    "Independent glyph placement raises powers/lowers coefficient suffixes; "
                    "the same mathematical relationship also has a stacked fraction rendering. "
                    "SQRT is spelled out rather than drawn as a radical glyph. "
                )
            if encoding in ("vector-outlines", "raster-image"):
                notes += (
                    "Formula has no text operators or Unicode mapping; "
                    "digital anchor alone is not evidence of formula recovery. "
                )
            if encoding == "raster-invisible-text":
                notes += (
                    "Visible raster plus authored invisible text; "
                    "layer fidelity is controlled, not a measured OCR result. "
                )
            cases.append(
                MathCase(
                    id=case_id,
                    family="math",
                    flavors=[name, encoding, "silver-reference"],
                    pdf=_pdf(lines, anchor, encoding),
                    expected_text=[anchor],
                    reference_math=reference,
                    notes=notes,
                    producer_group=f"silver-math-authored-{name}",
                    encoding=encoding,
                    license="MIT",
                    provenance="repository-authored",
                )
            )
    return cases
