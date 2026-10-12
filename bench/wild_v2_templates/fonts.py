"""System Noto font files used by the ReportLab and pdfust producers."""

# ruff: noqa: E501
from __future__ import annotations

from pathlib import Path

NOTO = Path("/usr/share/fonts/noto")
CJK = Path("/usr/share/fonts/noto-cjk")
CJK_INDEX = {"ja": 0, "ko": 1, "zh-CN": 2, "zh-TW": 3}

# (path, collection index) per role.
LATIN = {"regular": (NOTO / "NotoSans-Regular.ttf", 0), "bold": (NOTO / "NotoSans-Bold.ttf", 0),
         "italic": (NOTO / "NotoSans-Italic.ttf", 0), "serif": (NOTO / "NotoSerif-Regular.ttf", 0),
         "serif_bold": (NOTO / "NotoSerif-Bold.ttf", 0), "mono": (NOTO / "NotoSansMono-Regular.ttf", 0),
         "math": (NOTO / "NotoSansMath-Regular.ttf", 0), "symbols": (NOTO / "NotoSansSymbols-Regular.ttf", 0),
         "symbols2": (NOTO / "NotoSansSymbols2-Regular.ttf", 0)}
# The repository's own pdfust script font packages ship current Noto builds that also cover Latin,
# digits and punctuation (the distribution's static script fonts lack them), so mixed text fits one box.
PACKAGES = Path(__file__).resolve().parents[2] / "fonts"
SCRIPT = {
    "ar": ((PACKAGES / "pdfust-fonts-ar/src/pdfust_fonts_ar/NotoNaskhArabic-Variable.ttf", 0),) * 2,
    # The Hebrew variable font's default instance is Thin; static Liberation Sans covers Hebrew, Latin and digits.
    "he": ((Path("/usr/share/fonts/liberation/LiberationSans-Regular.ttf"), 0), (Path("/usr/share/fonts/liberation/LiberationSans-Bold.ttf"), 0)),
    "hi": ((PACKAGES / "pdfust-fonts-hi/src/pdfust_fonts_hi/NotoSansDevanagari-Variable.ttf", 0),) * 2,
    "th": ((PACKAGES / "pdfust-fonts-th/src/pdfust_fonts_th/NotoSansThai-Variable.ttf", 0),) * 2,
}


def base(lang: str) -> str:
    """Language key used by the font tables (``zh-CN``/``zh-TW`` keep their region)."""
    return lang if lang in CJK_INDEX else lang.split("-", maxsplit=1)[0]


def stack(lang: str, *, bold: bool = False, role: str = "regular") -> list[tuple[Path, int]]:
    """Ordered font candidates for one text box; the first one covering every glyph wins."""
    key = base(lang)
    fonts: list[tuple[Path, int]] = []
    if role == "mono":
        fonts.append(LATIN["mono"])
    if key in SCRIPT:
        fonts.append(SCRIPT[key][1 if bold else 0])
    if key in CJK_INDEX:
        fonts.append((CJK / ("NotoSansCJK-Bold.ttc" if bold else "NotoSansCJK-Regular.ttc"), CJK_INDEX[key]))
    if role == "serif":
        fonts.append(LATIN["serif_bold" if bold else "serif"])
    fonts.append(LATIN["bold" if bold else "regular"])
    fonts += [(CJK / "NotoSansCJK-Regular.ttc", CJK_INDEX.get(key, 0)), LATIN["math"], LATIN["symbols"], LATIN["symbols2"]]
    fonts += [pair[0] for k, pair in SCRIPT.items() if k != key]
    seen: set[tuple[Path, int]] = set()
    return [f for f in fonts if f[0].is_file() and not (f in seen or seen.add(f))]
