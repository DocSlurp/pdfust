"""Score PDF-to-Markdown element recovery across converters against known ground truth.

Usage (inputs, raw outputs, and JSON stay in an ignored artifact directory)::

    uv sync --group bench-rich
    uv run python -m bench.markdown_scores --build
    uv run python -m bench.markdown_scores --run pdfust pymupdf4llm-layout ...
    /path/to/isolated/python bench/markdown_score_run.py markitdown INPUTS OUTPUTS
    uv run python -m bench.markdown_scores --score   # also syncs to Langfuse when .env configures it

Every output is parsed as CommonMark + GFM tables + dollar math + raw HTML,
because that is how a Markdown consumer would read it. Plain-text extractors
are included as floors. Each check yields a value in [0, 1]; a category score is
the mean of its checks and the overall score is the unweighted mean of
categories. Fixtures are small and synthetic, so scores rank element-recovery
behavior on known inputs; they are not a corpus-wide accuracy estimate.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import dataclasses
import html
import json
import re
import statistics
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from itertools import pairwise
from typing import TYPE_CHECKING, Any

from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin

from bench import markdown_score_langfuse
from bench.feature_cases import ROOT
from bench.markdown_score_cases import Truth, score_cases

if TYPE_CHECKING:
    from pathlib import Path

MIN_IMAGE_BYTES = 8
IMAGE = "<image>"
ARTIFACTS = ROOT / "bench" / "results" / "pdf-master-artifacts" / "markdown-scores"
SUMMARY = ROOT / "bench" / "results" / "markdown-scores.md"
LOCAL_TOOLS = (
    "pdfust",
    "pdfust-text-tables",
    "pymupdf4llm-layout",
    "pymupdf4llm-legacy",
    "pymupdf",
    "pypdf",
    "pdfplumber",
)
TEXT_ONLY = {"pymupdf", "pypdf", "pdfplumber"}
CATEGORIES = (
    "Text",
    "Order",
    "Headings",
    "Emphasis",
    "Code",
    "Lists",
    "Escaping",
    "Tables",
    "Math",
    "Images",
    "Links",
)


# --------------------------------------------------------------------------- parsing


def norm(text: str) -> str:
    """NFC, unescaped entities, and collapsed whitespace."""
    return " ".join(unicodedata.normalize("NFC", html.unescape(text)).split())


class _HtmlFragments(HTMLParser):
    """Collect tables, emphasis, links, images, anchors, and visible text from raw HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.tables: list[list[list[tuple[str, int]]]] = []
        self.links: list[tuple[str, str]] = []
        self.images = 0
        self.image_srcs: list[str] = []
        self.ids: list[str] = []
        self.styled: dict[str, list[str]] = {"bold": [], "italic": [], "code": []}
        self._stack: list[tuple[str, list[str]]] = []
        self._row: list[tuple[str, int]] | None = None
        self._cell: list[str] | None = None
        self._colspan = 1
        self._href: tuple[str, list[str]] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("id", "name"):
            if values.get(key):
                self.ids.append(str(values[key]))
        if tag == "table":
            self.tables.append([])
        elif tag == "tr" and self.tables:
            self._row = []
            self.tables[-1].append(self._row)
        elif tag in {"td", "th"}:
            self._cell = []
            self._colspan = int(values.get("colspan") or 1)
        elif tag == "a" and values.get("href"):
            self._href = (str(values["href"]), [])
        elif tag == "img":
            self.images += 1
            self.image_srcs.append(str(values.get("src") or ""))
        elif tag == "br":
            self.handle_data(" ")
        style = {"b": "bold", "strong": "bold", "i": "italic", "em": "italic", "code": "code"}.get(tag)
        if style:
            self._stack.append((style, []))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append((norm("".join(self._cell)), self._colspan))
            self._cell = None
        elif tag == "a" and self._href:
            self.links.append((norm("".join(self._href[1])), self._href[0]))
            self._href = None
        style = {"b": "bold", "strong": "bold", "i": "italic", "em": "italic", "code": "code"}.get(tag)
        if style and self._stack and self._stack[-1][0] == style:
            _, parts = self._stack.pop()
            self.styled[style].append(norm("".join(parts)))

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        for target in ([self._cell] if self._cell is not None else []) + ([self._href[1]] if self._href else []):
            target.append(data)
        for _, parts in self._stack:
            parts.append(data)


@dataclass
class Block:
    """One top-level rendered block in document order."""

    kind: str
    text: str
    level: int = 0
    ids: list[str] = field(default_factory=list)


@dataclass
class Parsed:
    """Elements a Markdown reader would see."""

    blocks: list[Block] = field(default_factory=list)
    headings: list[tuple[str, int]] = field(default_factory=list)
    bold: list[str] = field(default_factory=list)
    italic: list[str] = field(default_factory=list)
    code_inline: list[str] = field(default_factory=list)
    code_blocks: list[str] = field(default_factory=list)
    list_items: list[tuple[str, bool, int]] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    links: list[tuple[str, str]] = field(default_factory=list)
    math: list[str] = field(default_factory=list)
    image_srcs: list[str] = field(default_factory=list)
    # Rendered text with images as an <image> token, for order checks.
    flow: str = ""

    @property
    def text(self) -> str:
        """Return all rendered block text as one normalized string."""
        return norm(" ".join(block.text for block in self.blocks))


_MD = MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough").use(dollarmath_plugin)


def _slug(text: str) -> str:
    """GitHub-style heading anchor."""
    return re.sub(r"[^\w\- ]", "", text.lower()).strip().replace(" ", "-")


def _expand_html_table(rows: list[list[tuple[str, int]]]) -> list[list[str]]:
    grid = []
    for row in rows:
        cells: list[str] = []
        for text, span in row:
            cells.extend([text] + ["\x00span"] * (span - 1))
        grid.append(cells)
    return grid


def _inline(children: list[Any], parsed: Parsed, flow: list[str], ids: list[str]) -> str:  # noqa: C901, PLR0912
    """Render inline tokens to text and record emphasis, code, links, images, and math."""
    out: list[str] = []
    styles: list[tuple[str, int]] = []
    link: tuple[str, int] | None = None
    for token in children:
        kind = token.type
        if kind in {"text", "code_inline", "math_inline"}:
            content = token.content
            if kind == "code_inline":
                parsed.code_inline.append(norm(content))
            if kind == "math_inline":
                parsed.math.append(content)
            out.append(content)
        elif kind in {"softbreak", "hardbreak"}:
            out.append(" ")
        elif kind in {"strong_open", "em_open"}:
            styles.append((kind, len(out)))
        elif kind in {"strong_close", "em_close"} and styles:
            opened, start = styles.pop()
            target = parsed.bold if opened == "strong_open" else parsed.italic
            target.append(norm("".join(out[start:])))
        elif kind == "link_open":
            link = (str(token.attrGet("href") or ""), len(out))
        elif kind == "link_close" and link:
            parsed.links.append((norm("".join(out[link[1] :])), link[0]))
            link = None
        elif kind == "image":
            parsed.image_srcs.append(str(token.attrGet("src") or ""))
            flow.append(" <image> ")
        elif kind == "html_inline":
            fragment = _HtmlFragments()
            fragment.feed(token.content)
            ids.extend(fragment.ids)
            parsed.image_srcs.extend(fragment.image_srcs)
            if token.content.lower().startswith("<br"):
                out.append(" ")
            elif re.fullmatch(r"</?(sup|sub)>", token.content.strip(), re.IGNORECASE):
                out.append(token.content)
    text = "".join(out)
    flow.append(re.sub(r"</?su[pb]>", "", text, flags=re.IGNORECASE))
    return text


def parse(markdown: str) -> Parsed:  # noqa: C901, PLR0912
    """Parse Markdown the way a CommonMark/GFM reader would."""
    parsed = Parsed()
    flow: list[str] = []
    tokens = _MD.parse(markdown)
    list_stack: list[bool] = []
    item_texts: list[list[str]] = []
    heading_level = 0
    table: list[list[str]] | None = None
    row: list[str] | None = None
    for index, token in enumerate(tokens):
        kind = token.type
        if kind in {"bullet_list_open", "ordered_list_open"}:
            list_stack.append(kind == "ordered_list_open")
        elif kind in {"bullet_list_close", "ordered_list_close"}:
            list_stack.pop()
        elif kind == "list_item_open":
            item_texts.append([])
        elif kind == "list_item_close":
            text = norm(" ".join(item_texts.pop()))
            parsed.list_items.append((text, list_stack[-1], len(list_stack) - 1))
        elif kind == "heading_open":
            heading_level = int(token.tag[1])
        elif kind == "table_open":
            table = []
        elif kind == "tr_open":
            row = []
        elif kind == "tr_close" and table is not None and row is not None:
            table.append(row)
        elif kind == "table_close" and table is not None:
            parsed.tables.append(table)
            table = None
        elif kind == "inline":
            ids: list[str] = []
            text = norm(_inline(token.children or [], parsed, flow, ids))
            if row is not None and table is not None and tokens[index - 1].type in {"th_open", "td_open"}:
                row.append(text)
            if item_texts:
                item_texts[-1].append(text)
            previous = tokens[index - 1].type
            if previous == "heading_open":
                parsed.headings.append((text, heading_level))
                parsed.blocks.append(Block("heading", text, heading_level, [*ids, _slug(text)]))
            elif previous not in {"th_open", "td_open"}:
                parsed.blocks.append(Block("paragraph", text, ids=ids))
            else:
                parsed.blocks.append(Block("cell", text))
        elif kind in {"fence", "code_block"}:
            if token.info.strip().lower() == "math":
                parsed.math.append(token.content)
            else:
                parsed.code_blocks.append(token.content)
            parsed.blocks.append(Block("code", token.content))
            flow.append(token.content)
        elif kind == "math_block":
            parsed.math.append(token.content)
            parsed.blocks.append(Block("math", token.content))
            flow.append(token.content)
        elif kind == "html_block":
            fragment = _HtmlFragments()
            fragment.feed(token.content)
            parsed.tables.extend(_expand_html_table(rows) for rows in fragment.tables)
            parsed.links.extend(fragment.links)
            parsed.image_srcs.extend(fragment.image_srcs)
            parsed.bold.extend(fragment.styled["bold"])
            parsed.italic.extend(fragment.styled["italic"])
            parsed.code_inline.extend(fragment.styled["code"])
            text = norm(" ".join(fragment.text))
            if re.search(r"<math[\s>]", token.content):
                parsed.math.append(token.content)
            parsed.blocks.append(Block("html", text, ids=fragment.ids))
            flow.append(" <image> " * fragment.images + text)
    parsed.flow = norm(" ".join(flow))
    return parsed


# --------------------------------------------------------------------------- scoring


def _contains(haystack: str, needle: str) -> bool:
    return norm(needle) in haystack or norm(needle).replace(" ", "") in haystack.replace(" ", "")


def _style_score(spans: list[str], target: str) -> float:
    """1 for an exact styled span, 0.5 when the style covers the target plus extra text."""
    wanted = norm(target)
    if any(span == wanted for span in spans):
        return 1.0
    return 0.5 if any(wanted in span for span in spans) else 0.0


def _table_score(expected: tuple[tuple[tuple[str, ...], ...], ...], tables: list[list[list[str]]]) -> float:
    """Best position-aware cell F1 over emitted tables; covered colspan slots match ``("x", "")`` cells."""
    best = 0.0
    expected_cells = sum(len(row) for row in expected)
    for table in tables:
        emitted_cells = sum(len(row) for row in table)
        matches = 0
        for r, row in enumerate(expected):
            for c, accepted in enumerate(row):
                if r >= len(table) or c >= len(table[r]):
                    continue
                value = table[r][c]
                options = {norm(option) for option in accepted}
                if value in options or (value == "\x00span" and len(options) > 1):
                    matches += 1
        if matches:
            precision, recall = matches / emitted_cells, matches / expected_cells
            best = max(best, 2 * precision * recall / (precision + recall))
    return best


def _math_norm(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<sup>(.*?)</sup>", r"^\1", text, flags=re.IGNORECASE)
    text = re.sub(r"<sub>(.*?)</sub>", r"_\1", text, flags=re.IGNORECASE)
    text = text.replace("²", "^2").replace("₂", "_2")
    text = re.sub(r"\\(left|right|displaystyle|,|;|!|quad)", "", text)
    text = re.sub(r"\\(mathrm|mathit|text|operatorname)\{([^{}]*)\}", r"\2", text)
    text = text.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    text = re.sub(r"([\^_])\{(\w)\}", r"\1\2", text)
    return re.sub(r"\$|\\\(|\\\)|\\\[|\\\]|\s", "", text)


def _math_score(reference: str, parsed: Parsed, raw: str) -> float:
    """1: exact in a math element (or script markup); 0.75: bare exact LaTeX; 0.5: fraction structure; 0.25: image."""
    wanted = _math_norm(reference)
    if any(wanted in _math_norm(math) for math in parsed.math):
        return 1.0
    if "\\" not in reference:
        # Script-only references (mc^2, H_2O): HTML/Unicode/LaTeX script markup counts as recovered.
        return 1.0 if wanted in _math_norm(raw) else 0.0
    if wanted in _math_norm(raw):
        return 0.75
    if any("\\frac" in math for math in parsed.math):
        return 0.5
    return 0.25 if parsed.image_srcs else 0.0


def _asset_ok(src: str, output: Path) -> bool:
    """Accept a data URI that decodes to image bytes or a relative reference to an existing file."""
    if src.startswith("data:image/"):
        try:
            return len(base64.b64decode(src.split(",", 1)[1], validate=False)) > MIN_IMAGE_BYTES
        except (IndexError, binascii.Error):
            return False
    return bool(src) and "://" not in src and (output.parent / src).is_file()


def _order_score(tokens: tuple[str, ...], text: str) -> float:
    """Fraction of consecutive reference pairs that appear in order; missing tokens fail."""
    positions = [text.find(token) for token in tokens]
    pairs = list(pairwise(positions))
    return sum(0 <= a < b for a, b in pairs) / len(pairs) if pairs else 0.0


def _internal_link_ok(href: str, target: str, parsed: Parsed) -> bool:
    if not href.startswith("#"):
        return False
    anchor = href[1:]
    for index, block in enumerate(parsed.blocks):
        if anchor in block.ids:
            following = " ".join(b.text for b in parsed.blocks[index : index + 2])
            return norm(target) in following
    return False


def score_case(truth: Truth, markdown: str, output: Path) -> dict[str, list[float]]:  # noqa: C901, PLR0912
    """Return per-category check scores for one case."""
    parsed = parse(markdown)
    text = parsed.text
    scores: dict[str, list[float]] = {}

    def add(category: str, value: float) -> None:
        scores.setdefault(category, []).append(value)

    for expected in truth.text:
        add("Text", float(_contains(text, expected)))
    if truth.order:
        add("Order", _order_score(truth.order, text))
    if truth.headings:
        emitted = {heading for heading, _ in parsed.headings}
        wanted = {norm(heading) for heading, _ in truth.headings}
        found = [h for h in truth.headings if norm(h[0]) in emitted]
        recall = len(found) / len(wanted)
        precision = len(emitted & wanted) / len(emitted) if emitted else 0.0
        add("Headings", 2 * precision * recall / (precision + recall) if precision + recall else 0.0)
        levels = dict(parsed.headings)
        pairs = [(a, b) for i, a in enumerate(found) for b in found[i + 1 :]]
        if len({level for _, level in truth.headings}) > 1:
            # Relative hierarchy: same/greater/lesser level relations must match the source tiers.
            consistent = sum(
                (a[1] > b[1]) == (levels[norm(a[0])] > levels[norm(b[0])])
                and (a[1] == b[1]) == (levels[norm(a[0])] == levels[norm(b[0])])
                for a, b in pairs
            )
            total = len(truth.headings) * (len(truth.headings) - 1) // 2
            add("Headings", consistent / total)
    for span in truth.bold:
        add("Emphasis", _style_score(parsed.bold, span))
    for span in truth.italic:
        add("Emphasis", _style_score(parsed.italic, span))
    for span in truth.code_inline:
        in_code = any(norm(span) in code for code in parsed.code_inline) or any(
            norm(span) in norm(block) for block in parsed.code_blocks
        )
        add("Code", float(in_code))
    if truth.code_block:
        # Join all code blocks: a converter may split one listing into several fences.
        joined = "\n".join(parsed.code_blocks)
        block = joined if norm(truth.code_block[0]) in norm(joined) else None
        add("Code", float(block is not None))
        lines = [line for line in (block or "").splitlines() if line.strip()]
        base = min((len(line) - len(line.lstrip()) for line in lines), default=0)
        emitted = {line[base:].rstrip() for line in lines}
        add("Code", sum(line in emitted for line in truth.code_block) / len(truth.code_block))
    if truth.list_items:
        for item, ordered, depth in truth.list_items:
            match = next((entry for entry in parsed.list_items if norm(item) in entry[0]), None)
            if match is None:
                add("Lists", 0.0)
            else:
                add("Lists", 0.5 + 0.25 * (match[1] == ordered) + 0.25 * (match[2] == depth))
    for literal in truth.literals:
        add("Escaping", float(norm(literal) in text))
    if truth.literals:
        add("Escaping", float(not any("asterisks" in span for span in parsed.italic + parsed.bold)))
    if truth.table:
        add("Tables", _table_score(truth.table, parsed.tables))
    for reference in truth.math:
        add("Math", _math_score(reference, parsed, markdown))
    if truth.images:
        add("Images", min(len(parsed.image_srcs), truth.images) / truth.images)
        resolved = sum(_asset_ok(src, output) for src in parsed.image_srcs)
        add("Images", min(resolved, truth.images) / truth.images)
        if truth.image_order:
            add("Images", _image_order(truth, parsed))
    for link in truth.links:
        hits = [
            href for label, href in parsed.links if norm(link.label) in label or (label and label in norm(link.label))
        ]
        if link.uri:
            add("Links", float(any(html.unescape(href) == link.uri for href in hits)))
        else:
            ok = any(_internal_link_ok(href, link.internal_target or "", parsed) for href in hits)
            add("Links", 1.0 if ok else 0.5 if any(href.startswith("#") for href in hits) else 0.0)
    return scores


def _image_order(truth: Truth, parsed: Parsed) -> float:
    """Each image token must sit between the preceding text anchor and its caption."""
    flow = parsed.flow
    cursor, correct = 0, 0
    steps = truth.image_order
    for index, step in enumerate(steps):
        found = flow.find(step, cursor)
        if found < 0:
            continue
        if step == IMAGE and index + 1 < len(steps):
            caption = flow.find(steps[index + 1], found)
            correct += caption > found
        cursor = found + len(step)
    return correct / steps.count(IMAGE)


# --------------------------------------------------------------------------- orchestration


def build() -> None:
    """Write every scored input PDF and its ground truth."""
    inputs = ARTIFACTS / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for case in score_cases():
        (inputs / f"{case.name}.pdf").write_bytes(case.data)
        manifest[case.name] = {"source": case.source, "notes": case.notes, "truth": _truth_json(case.truth)}
    (ARTIFACTS / "truth.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(manifest)} inputs -> {inputs}")


def _truth_json(truth: Truth) -> dict[str, Any]:
    return {key: value for key, value in dataclasses.asdict(truth).items() if value}


def run(tools: list[str], python: str) -> None:
    """Convert inputs with each tool in its own process so RSS/CPU are per tool."""
    for tool in tools:
        subprocess.run(  # noqa: S603
            [
                python,
                str(ROOT / "bench" / "markdown_score_run.py"),
                tool,
                str(ARTIFACTS / "inputs"),
                str(ARTIFACTS / "outputs"),
            ],
            check=True,
        )


def score() -> dict[str, Any]:
    """Score every tool directory under outputs/ and write the JSON and Markdown summaries."""
    cases = {case.name: case for case in score_cases()}
    tools: dict[str, Any] = {}
    for run_path in sorted((ARTIFACTS / "outputs").glob("*/run.json")):
        meta = json.loads(run_path.read_text(encoding="utf-8"))
        per_case: dict[str, dict[str, list[float]]] = {}
        for name, case in cases.items():
            output = run_path.parent / f"{name}.md"
            markdown = output.read_text(encoding="utf-8") if output.exists() else ""
            per_case[name] = score_case(case.truth, markdown, output)
        categories = {}
        for category in CATEGORIES:
            values = [v for checks in per_case.values() for v in checks.get(category, [])]
            categories[category] = {"score": statistics.fmean(values) if values else None, "checks": len(values)}
        overall = statistics.fmean(c["score"] for c in categories.values() if c["score"] is not None)
        tools[meta["tool"]] = {"meta": meta, "categories": categories, "overall": overall, "cases": per_case}
    report = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain", "--", "rust", "src"], cwd=ROOT, text=True)  # noqa: S607
        ),
        "cases": {name: {"source": case.source, "notes": case.notes} for name, case in cases.items()},
        "tools": tools,
    }
    (ARTIFACTS / "scores.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SUMMARY.write_text(format_summary(report), encoding="utf-8")
    print(SUMMARY)
    return report


def _source(meta: dict[str, Any]) -> str:
    source = meta.get("source") or {}
    if not source.get("commit"):
        return "unrecorded"
    return f"`{source['commit'][:12]}`" + (" dirty" if source.get("dirty") else "")


def _cell(value: float | None) -> str:
    return "–" if value is None else f"{value * 100:.0f}"


CATEGORY_HELP = {
    "Text": "Each expected string appears in the rendered text (NFC, collapsed whitespace; Unicode, RTL, ActualText).",
    "Order": "Consecutive reference tokens appear in order (two-column, rotated, and tagged pages).",
    "Headings": "Heading-text F1 (false headings cost precision) plus relative levels across 26/18/14 pt tiers.",
    "Emphasis": "1 for an exact `**`/`*`/`<b>` span; 0.5 when the style also covers neighbouring text.",
    "Code": "Courier tokens in inline code; a code block exists and keeps relative indentation.",
    "Lists": "Each item is a list item (0.5), with the right ordered/bullet type (+0.25) and depth (+0.25).",
    "Escaping": "Literal `*`, `[]`, `#`, `<tag>`, `\\` survive rendering, and no false emphasis is created.",
    "Tables": "Best position-aware cell F1 over emitted GFM/HTML tables; a merged slot accepts repeat/empty/colspan.",
    "Math": (
        "1: exact LaTeX in math markup, or exact `<sup>`/`^`/Unicode scripts; 0.75: bare exact LaTeX; "
        "0.5: `\\frac` structure; 0.25: equation only as an image."
    ),
    "Images": "References emitted, assets resolve (decodable data URI or existing file), image precedes caption.",
    "Links": "URI label with exact href; internal links resolve to an emitted anchor (0.5 if unresolved).",
}
PREAMBLE = (
    "Scores are 0-100. Each check scores 0-1, a category is the mean of its checks, and **Overall** is the "
    "unweighted mean of categories. Outputs are parsed as CommonMark + GFM tables + `$` math + raw HTML, "
    "the way a Markdown consumer reads them. Plain-text extractors (marked †) are floors: they emit no "
    "Markdown, so only text, order, and accidental syntax can score. The fixtures are small and each pins "
    "a specific behavior; treat a gap of a few points as noise, not a ranking."
)
RESOURCE_NOTE = (
    "Wall and CPU time sum all cases after one unmeasured warmup conversion; initialization is separate. "
    "CPU time is `time.process_time()` across all threads of the converter process. Peak RSS is "
    "`getrusage(RUSAGE_SELF).ru_maxrss` for the whole converter process, including model loading. "
    "There is one measured conversion per case. Timings are not equivalent-work comparisons, because some "
    "tools embed images or run layout models."
)
REPRODUCE = (
    "Reproduce with the commands in the `bench/markdown_scores.py` docstring. Inputs, raw outputs, image "
    "assets, `truth.json`, and `scores.json` stay in the ignored "
    "`bench/results/pdf-master-artifacts/markdown-scores/` directory."
)


def format_summary(report: dict[str, Any]) -> str:
    """Render the score matrix, per-case detail, and resource measurements."""
    tools = sorted(report["tools"].items(), key=lambda item: -item[1]["overall"])
    checks = {c: max(t["categories"][c]["checks"] for _, t in tools) for c in CATEGORIES}
    dirty = " with uncommitted `rust/` or `src/` changes in the pdfust build" if report["dirty"] else ""
    lines = [
        "# PDF-to-Markdown element score matrix",
        "",
        (
            f"- Generated: {report['generated']}; scorer commit `{report['commit'][:12]}`{dirty}. "
            "The resource table records the checkout that produced each converter's outputs."
        ),
        (
            f"- Inputs: {len(report['cases'])} synthetic PDFs with exact ground truth "
            "(`bench/markdown_score_cases.py`). Corpus pages are excluded because they lack structural truth."
        ),
        "",
        PREAMBLE,
        "",
        "| Tool | Overall | " + " | ".join(f"{c} ({checks[c]})" for c in CATEGORIES) + " |",
        "|---|---:|" + "---:|" * len(CATEGORIES),
    ]
    for name, tool in tools:
        label = f"{name} †" if name in TEXT_ONLY else name
        cells = " | ".join(_cell(tool["categories"][c]["score"]) for c in CATEGORIES)
        lines.append(f"| {label} | **{tool['overall'] * 100:.0f}** | {cells} |")
    lines += ["", "Numbers in column headers are check counts.", "", "## What each category checks", ""]
    lines += ["| Category | Checks |", "|---|---|"]
    lines += [f"| {category} | {text} |" for category, text in CATEGORY_HELP.items()]
    lines += ["", "## Resource use", "", RESOURCE_NOTE, ""]
    lines += [
        "| Tool | Version | Options | Source | Init (ms) | Wall (ms) | Median (ms) | CPU (ms) | RSS (MiB) | Errors |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, tool in tools:
        meta = tool["meta"]
        runs = meta["cases"].values()
        wall = [r["wall_ms"] for r in runs]
        version = ", ".join(f"{k} {v}" for k, v in meta["versions"].items())
        cpu = sum(r["cpu_ms"] for r in runs)
        errors = sum(r["error"] is not None for r in runs)
        lines.append(
            f"| {name} | {version} | `{meta['options']}` | {_source(meta)} | {meta['initialization']['wall_ms']:.0f} | "
            f"{sum(wall):.0f} | {statistics.median(wall):.1f} | {cpu:.0f} | {meta['peak_rss_mib']:.0f} | {errors} |"
        )
    platform_line = tools[0][1]["meta"]["platform"] if tools else ""
    lines += ["", f"Machine: {platform_line}; converters ran sequentially, one process per tool.", ""]
    lines += ["## Per-case scores", "", "Mean of all checks in each case, per tool.", ""]
    names = [name for name, _ in tools]
    lines += ["| Case | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
    for case in report["cases"]:
        row = []
        for _, tool in tools:
            values = [v for checks in tool["cases"][case].values() for v in checks]
            row.append(_cell(statistics.fmean(values) if values else None))
        lines.append(f"| {case} | " + " | ".join(row) + " |")
    lines += ["", REPRODUCE, ""]
    return "\n".join(lines)


def main() -> None:
    """Build inputs, run local converters, and/or score retained outputs."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build", action="store_true", help="Write input PDFs and truth.json")
    parser.add_argument("--run", nargs="*", metavar="TOOL", help=f"Run tools (default: {', '.join(LOCAL_TOOLS)})")
    parser.add_argument("--python", default=sys.executable, help="Interpreter for --run tools")
    parser.add_argument("--score", action="store_true", help="Score outputs and write the summary")
    parser.add_argument("--no-langfuse", action="store_true", help="Skip syncing the dataset and runs to Langfuse")
    parser.add_argument("--langfuse-force", action="store_true", help="Re-send runs that were already synced")
    args = parser.parse_args()
    if args.build:
        build()
    if args.run is not None:
        run(args.run or list(LOCAL_TOOLS), args.python)
    if args.score:
        report = score()
        if not args.no_langfuse:
            status = markdown_score_langfuse.sync(ROOT, ARTIFACTS, report, force=args.langfuse_force)
            print("langfuse:", json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
