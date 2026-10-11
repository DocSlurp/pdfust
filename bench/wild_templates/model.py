"""Block model, inline markup, locale formatting, truth flattening and Unicode feature detection.

Authored blocks use a tiny inline markup that both renderers understand:
``**bold**``, ``*italic*`` and ``[link text](https://example.org/...)``. Truth
strings are the markup-free text, stored exactly as authored (no Unicode
normalization). Layout containers (``columns`` and ``pair``) only exist in the
authored model; truth flattens them in reading order.
"""

# ruff: noqa: PLR2004, ANN401, C901, E501, EM102, PLR0911, PLR0912, PLR0913, TRY003
from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date

UNICODE_FEATURES = (
    "ligature", "nbsp", "narrow_nbsp", "zero_width", "soft_hyphen", "combining_marks", "nfd_text", "fullwidth",
    "unicode_minus", "dashes", "smart_quotes", "currency", "math_symbols", "superscripts", "emoji",
    "bidi_controls", "rtl_numbers", "thousands_separators", "date_formats", "private_use",
)
TEXT_KINDS = {"paragraph", "sidebar", "callout", "footnote", "header", "footer"}
TABLE_RENDERINGS = {"ruled", "borderless", "screenshot", "chart_data"}
FIGURE_KINDS = {"photo", "screenshot", "chart"}

_MARKUP = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*|\[([^\]]+)\]\(([^)\s]+)\)")


# ------------------------------------------------------------------ inline markup


def tokens(markup: str) -> list[tuple[str, str, str | None]]:
    """Split markup into ``(style, text, href)`` runs; style is plain, bold, italic or link."""
    result: list[tuple[str, str, str | None]] = []
    position = 0
    for match in _MARKUP.finditer(markup):
        if match.start() > position:
            result.append(("plain", markup[position:match.start()], None))
        if match.group(1) is not None:
            result.append(("bold", match.group(1), None))
        elif match.group(2) is not None:
            result.append(("italic", match.group(2), None))
        else:
            result.append(("link", match.group(3), match.group(4)))
        position = match.end()
    if position < len(markup):
        result.append(("plain", markup[position:], None))
    return result


def plain(markup: str) -> str:
    """Return the markup-free text exactly as authored."""
    return "".join(text for _, text, _ in tokens(markup))


def links(markup: str) -> list[dict[str, str]]:
    """Return hyperlinks in authored order."""
    return [{"text": text, "href": href} for style, text, href in tokens(markup) if style == "link" and href]


# ------------------------------------------------------------------ locale formatting

_GROUPING: dict[str, tuple[str, str, int]] = {
    # Locale key mapped to thousands separator, decimal mark and decimal places.
    "en": (",", ".", 2), "de": (".", ",", 2), "fr": (" ", ",", 2), "es": (".", ",", 2),
    "pl": (" ", ",", 2), "vi": (".", ",", 0), "tr": (".", ",", 2), "ja": (",", ".", 0),
    "zh": (",", ".", 2), "zhTW": (",", ".", 0), "ko": (",", ".", 0), "hi": (",", ".", 2),
    "th": (",", ".", 2), "ru": (" ", ",", 2), "he": (",", ".", 2),
}
_CURRENCY: dict[str, tuple[str, str]] = {
    # Locale key mapped to currency prefix and suffix.
    "en-US": ("$", ""), "en-GB": ("£", ""), "de": ("", " €"), "fr": ("", " €"), "es": ("", " €"),
    "pl": ("", " zł"), "vi": ("", " ₫"), "tr": ("", " ₺"), "ja": ("¥", ""), "zh": ("￥", ""),
    "zhTW": ("NT$", ""), "ko": ("₩", ""), "hi": ("₹", ""), "th": ("฿", ""), "ru": ("", " ₽"), "he": ("₪", ""),
}


def number(value: float, locale: str, decimals: int | None = None) -> str:
    """Format a nonnegative number with the locale's grouping (Indian lakh grouping for ``hi``)."""
    sep, mark, default = _GROUPING[locale]
    places = default if decimals is None else decimals
    text = f"{abs(value):.{places}f}"
    whole, _, fraction = text.partition(".")
    if locale == "hi" and len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        groups.insert(0, head)
        whole = ",".join(groups) + "," + tail
    else:
        whole = f"{int(whole):,}".replace(",", sep)
    return whole + (mark + fraction if fraction else "")


def money(cents: int, locale: str, *, minus: str = "−", parens: bool = False) -> str:
    """Format an amount in minor units (whole units for zero-decimal currencies)."""
    key = locale if locale in _CURRENCY else locale.split("-", maxsplit=1)[0]
    prefix, suffix = _CURRENCY[key]
    grouping = "zhTW" if locale == "zhTW" else key.split("-")[0]
    decimals = _GROUPING[grouping][2]
    value = cents / 100 if decimals else cents
    body = prefix + number(value, grouping) + suffix
    if cents < 0:
        return f"({body})" if parens else minus + body
    return body


def parse_money(text: str) -> int:
    """Recover minor units from a formatted amount (sign from U+2212, hyphen or parentheses)."""
    negative = text.startswith(("−", "-", "(")) or text.endswith(")")
    digits = re.sub(r"[^0-9]", "", text)
    return -int(digits) if negative else int(digits)


def day(value: date, style: str) -> str:
    """Format a date in one of the corpus styles."""
    months_en = ("January", "February", "March", "April", "May", "June", "July", "August", "September",
                 "October", "November", "December")
    if style == "iso":
        return value.isoformat()
    if style == "us":
        return f"{value.month:02d}/{value.day:02d}/{value.year}"
    if style == "en_short":
        return f"{months_en[value.month - 1][:3]} {value.day}, {value.year}"
    if style == "en_gb":
        return f"{value.day} {months_en[value.month - 1]} {value.year}"
    if style == "dotted":
        return f"{value.day:02d}.{value.month:02d}.{value.year}"
    if style == "slash_dmy":
        return f"{value.day:02d}/{value.month:02d}/{value.year}"
    if style == "cjk":
        return f"{value.year}年{value.month}月{value.day}日"
    if style == "ko":
        return f"{value.year}. {value.month}. {value.day}."
    if style == "md_cjk":
        return f"{value.month}月{value.day}日"
    raise ValueError(style)


# ------------------------------------------------------------------ block helpers


def table_spans(values: list[list[str | None]], merges: tuple[tuple[int, int, int, int], ...] = ()) -> list[dict[str, int]]:
    """Return anchor spans in the same convention as ``bench.pipeline_corpus._table``."""
    merged = {(r, c): (rs, cs) for r, c, rs, cs in merges}
    covered = {(row, col) for r, c, rs, cs in merges for row in range(r, r + rs) for col in range(c, c + cs)
               if (row, col) != (r, c)}
    return [{"row": r, "column": c, "row_span": merged.get((r, c), (1, 1))[0],
             "column_span": merged.get((r, c), (1, 1))[1]}
            for r, row in enumerate(values) for c, _ in enumerate(row) if (r, c) not in covered]


def table(table_id: str, rendering: str, values: list[list[str | None]], *, header_rows: int = 1,
          merges: tuple[tuple[int, int, int, int], ...] = (), caption: str = "", **hints: Any) -> dict[str, Any]:
    """Build a table block; covered merge slots become ``None``."""
    grid = [list(row) for row in values]
    for r, c, rs, cs in merges:
        for row in range(r, r + rs):
            for col in range(c, c + cs):
                if (row, col) != (r, c):
                    grid[row][col] = None
    return {"kind": "table", "id": table_id, "rendering": rendering, "header_rows": header_rows, "values": grid,
            "spans": table_spans(grid, merges), "caption": caption, "merges": list(merges), **hints}


def flatten(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand layout containers in reading order."""
    result: list[dict[str, Any]] = []
    for block in blocks:
        if block["kind"] in {"columns", "pair", "group"}:
            result.extend(flatten(block["blocks"]))
        else:
            result.append(block)
    return result


def truth_block(block: dict[str, Any]) -> dict[str, Any]:
    """Project one authored block onto the contract schema."""
    kind = block["kind"]
    if kind == "heading":
        return {"kind": kind, "level": block["level"], "text": plain(block["text"])}
    if kind in TEXT_KINDS:
        text = plain(block["text"])
        if block.get("title"):
            text = plain(block["title"]) + "\n" + text
        return {"kind": kind, "text": text}
    if kind == "list":
        return {"kind": kind, "ordered": block["ordered"], "items": [plain(item) for item in block["items"]]}
    if kind == "table":
        return {"kind": kind, "id": block["id"], "rendering": block["rendering"], "header_rows": block["header_rows"],
                "values": block["values"], "spans": block["spans"], "caption": plain(block.get("caption", ""))}
    if kind == "figure":
        return {"kind": kind, "id": block["id"], "figure_kind": block["figure_kind"],
                "photo_id": block.get("photo_id"), "wrap": block.get("wrap", "none"),
                "caption": plain(block.get("caption", "")), "text_in_image": list(block.get("text_in_image", []))}
    if kind == "fields":
        return {"kind": "paragraph", "text": "\n".join(f"{label}: {value}" for label, value in block["items"])}
    raise ValueError(f"Unknown block kind {kind}")


def native_strings(block: dict[str, Any]) -> list[str]:
    """Strings carried by the native text layer for one truth block."""
    kind = block["kind"]
    if kind == "list":
        return list(block["items"])
    if kind == "table":
        if block["rendering"] not in {"ruled", "borderless"}:
            return [block["caption"]]
        return [cell for row in block["values"] for cell in row if cell] + [block["caption"]]
    if kind == "figure":
        return [block["caption"]]
    return [block.get("text", "")]


# ------------------------------------------------------------------ unicode features

_SETS = {
    "nbsp": " ", "narrow_nbsp": " ", "zero_width": "\u200b\u200c\u200d\u2060", "soft_hyphen": "\u00ad",
    "unicode_minus": "−", "dashes": "‒–—", "smart_quotes": "‘’‚“”„«»‹›",
    "currency": "€£¥₹₩₪฿₫₽₺￥", "math_symbols": "±×÷≤≥µ°‰√∑≈", "superscripts": "¹²³⁰⁴⁵⁶⁷⁸⁹⁺⁻",
    "bidi_controls": "\u200e\u200f\u061c\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069",
}
_THOUSANDS = re.compile(r"\d{1,3}(?:[,.   ]\d{3})+(?:[.,]\d{1,2})?(?!\d)|\d{1,2}(?:,\d{2})+,\d{3}|[٠-٩]+٬[٠-٩]{3}")
_DATES = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{2}\.\d{2}\.\d{4}\b|\d{4}年\d{1,2}月\d{1,2}日|\b\d{2}/\d{2}/\d{4}\b"
                    r"|\d{4}\. \d{1,2}\. \d{1,2}\.")


def _emoji(char: str) -> bool:
    # Emoji-presentation characters only; text-style symbols such as ballot boxes do not count.
    return 0x1F000 <= ord(char) <= 0x1FAFF or char in "☕⚡✅✨❌⭐⌛⌚⛔"


def detect_features(strings: list[str]) -> list[str]:
    """Return the contract's ``unicode_features`` actually present in the given strings."""
    found: set[str] = set()
    for text in strings:
        for name, chars in _SETS.items():
            if any(c in text for c in chars):
                found.add(name)
        if any(0xFB00 <= ord(c) <= 0xFB06 for c in text):
            found.add("ligature")
        if any(unicodedata.category(c) == "Mn" for c in text):
            found.add("combining_marks")
        if unicodedata.normalize("NFC", text) != text:
            found.add("nfd_text")
        if any(0xFF01 <= ord(c) <= 0xFF60 or 0xFFE0 <= ord(c) <= 0xFFE6 for c in text):
            found.add("fullwidth")
        if any(_emoji(c) for c in text):
            found.add("emoji")
        if any(0xE000 <= ord(c) <= 0xF8FF or ord(c) >= 0xF0000 for c in text):
            found.add("private_use")
        rtl = any(unicodedata.bidirectional(c) in {"R", "AL"} for c in text)
        if rtl and any(unicodedata.category(c) == "Nd" for c in text):
            found.add("rtl_numbers")
        if _THOUSANDS.search(text):
            found.add("thousands_separators")
        if _DATES.search(text):
            found.add("date_formats")
    return [name for name in UNICODE_FEATURES if name in found]


# ------------------------------------------------------------------ validation


def validate_truth(truth: dict[str, Any]) -> list[str]:
    """Return schema violations for one truth document (empty when valid)."""
    problems: list[str] = []
    required = {"version", "doc_id", "template", "producer", "base_plan_id", "family", "page_count", "metadata",
                "outline", "links", "blocks", "languages", "unicode_features"}
    problems += [f"missing {key}" for key in sorted(required - truth.keys())]
    if truth.get("producer") not in {"chromium", "libreoffice"}:
        problems.append("producer")
    meta = truth.get("metadata", {})
    for key in ("title", "author", "subject", "keywords", "lang", "created"):
        if key not in meta:
            problems.append(f"metadata.{key}")
    for feature in truth.get("unicode_features", []):
        if feature not in UNICODE_FEATURES:
            problems.append(f"feature {feature}")
    for index, block in enumerate(truth.get("blocks", [])):
        kind = block.get("kind")
        where = f"block {index} ({kind})"
        if kind == "heading":
            if not isinstance(block.get("level"), int) or not isinstance(block.get("text"), str):
                problems.append(where)
        elif kind in TEXT_KINDS:
            if not isinstance(block.get("text"), str) or set(block) != {"kind", "text"}:
                problems.append(where)
        elif kind == "list":
            if not isinstance(block.get("ordered"), bool) or not all(isinstance(i, str) for i in block.get("items", [None])):
                problems.append(where)
        elif kind == "table":
            values = block.get("values", [])
            if block.get("rendering") not in TABLE_RENDERINGS or not values:
                problems.append(where)
                continue
            width = len(values[0])
            if any(len(row) != width for row in values):
                problems.append(where + " ragged")
            slots = {(s["row"], s["column"]) for s in block["spans"]}
            covered = {(r, c) for r, row in enumerate(values) for c, v in enumerate(row) if v is None}
            if slots & covered or len(slots) + len(covered) != len(values) * width:
                problems.append(where + " spans")
            if set(block) != {"kind", "id", "rendering", "header_rows", "values", "spans", "caption"}:
                problems.append(where + " keys")
        elif kind == "figure":
            if block.get("figure_kind") not in FIGURE_KINDS or block.get("wrap") not in {"left", "right", "none"}:
                problems.append(where)
            if set(block) != {"kind", "id", "figure_kind", "photo_id", "wrap", "caption", "text_in_image"}:
                problems.append(where + " keys")
        else:
            problems.append(where + " unknown kind")
    return problems
