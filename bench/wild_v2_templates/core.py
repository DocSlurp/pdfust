"""Multi-page authored document model, truth projection and validation for wild-v2.

A wild-v2 document is a dictionary with explicit pages::

    {"template": "bank_statement", "page_size": "A4" | "Letter" | "slide",
     "languages": ["fr-FR"], "dir": "ltr", "metadata": {...}, "theme": {...},
     "running_header": "... {page} ...", "running_footer": "...",
     "pages": [[block, ...], [block, ...]]}

Each inner list is one physical page; renderers insert a hard page break
between pages and shrink the whole document uniformly when a page overflows,
so every truth block carries an exact one-based ``page``. Blocks reuse the
wild-v1 kinds (see ``bench.wild_templates.common``) plus ``code``,
``equation``, ``form`` (AcroForm fields) and nested list items. A table that
continues across pages is authored as one segment per page with a repeated
header; segments after the first carry ``continues_from`` (the previous
segment id) and ``logical_id`` (the first segment id).
"""

# ruff: noqa: ANN401, C901, E501, EM102, PLR0912, PLR0913, TRY003, D401, FBT001, ERA001
from __future__ import annotations

import random
import unicodedata
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from bench.wild_templates import model
from bench.wild_templates.common import H, L, P, box, chart, chart_table, group, photo, screenshot

__all__ = [
    "H",
    "L",
    "P",
    "box",
    "chart",
    "chart_table",
    "code",
    "columns",
    "continued",
    "equation",
    "field",
    "form",
    "group",
    "item",
    "pair",
    "photo",
    "rng",
    "screenshot",
    "table",
    "truth",
    "validate",
]

PRODUCERS = ("chromium", "libreoffice", "reportlab", "pylopdf")
EXTRA_KINDS = {"code", "equation", "form_field"}


def rng(key: str) -> random.Random:
    """Deterministic per-document random generator (string seeds hash stably)."""
    return random.Random(f"wild-v2|{key}")  # noqa: S311 - reproducible content, not security


# ------------------------------------------------------------------ block helpers


def table(table_id: str, values: list[list[str]], *, rendering: str = "ruled", header_rows: int = 1, caption: str = "",
          align: list[str] | None = None, widths: list[float] | None = None, total_rows: list[int] | None = None,
          merges: tuple[tuple[int, int, int, int], ...] = (), **hints: Any) -> dict[str, Any]:
    """A single-page table block (``align`` uses ``l``/``r``/``c`` per column)."""
    return model.table(table_id, rendering, values, header_rows=header_rows, merges=merges, caption=caption,
                       align=align or ["l"] * len(values[0]), widths=widths, total_rows=total_rows or [], **hints)


def continued(table_id: str, header: list[list[str]], rows: list[list[str]], sizes: list[int], *, rendering: str = "ruled",
              caption: str = "", continued_caption: str = "", align: list[str] | None = None,
              widths: list[float] | None = None, total: list[list[str]] | None = None, **hints: Any) -> list[dict[str, Any]]:
    """Split one logical table into per-page segments that each repeat ``header``.

    ``sizes`` lists the body rows per segment and must sum to ``len(rows)``.
    ``total`` rows are appended to the last segment.
    """
    if sum(sizes) != len(rows) or any(size <= 0 for size in sizes):
        raise ValueError(f"{table_id}: segment sizes {sizes} do not cover {len(rows)} rows")
    segments: list[dict[str, Any]] = []
    start = 0
    for index, size in enumerate(sizes):
        body = rows[start:start + size]
        start += size
        tail = list(total or []) if index == len(sizes) - 1 else []
        values = [list(r) for r in header] + [list(r) for r in body] + [list(r) for r in tail]
        totals = list(range(len(header) + len(body), len(values)))
        segment_id = table_id if index == 0 else f"{table_id}-{index + 1}"
        block = table(segment_id, values, rendering=rendering, header_rows=len(header),
                      caption=caption if index == 0 else (continued_caption or caption), align=align, widths=widths,
                      total_rows=totals, **hints)
        if index:
            block["continues_from"] = segments[-1]["id"]
            block["logical_id"] = table_id
            block["repeated_header"] = True
        segments.append(block)
    return segments


def code(text: str, language: str = "", caption: str = "") -> dict[str, Any]:
    """Preformatted code or console block (monospace, whitespace preserved)."""
    return {"kind": "code", "text": text, "language": language, "caption": caption}


def equation(equation_id: str, mathml: str, text: str, starmath: str, *, number: str = "") -> dict[str, Any]:
    """Display equation: MathML body (without the ``<math>`` element), linear Unicode text and StarMath source.

    Chromium renders the MathML, LibreOffice embeds a Math object, and
    ReportLab/pylopdf typeset ``text`` as a centred line.
    """
    return {"kind": "equation", "id": equation_id, "mathml": mathml, "text": text, "starmath": starmath, "number": number}


def item(text: str, children: list[Any], *, ordered: bool = True) -> dict[str, Any]:
    """A list item with a nested sub-list."""
    return {"text": text, "items": children, "ordered": ordered}


def columns(blocks: list[dict[str, Any]], count: int = 2) -> dict[str, Any]:
    """Multi-column flow region."""
    return {"kind": "columns", "count": count, "blocks": blocks}


def pair(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Two blocks side by side."""
    return {"kind": "pair", "blocks": [left, right]}


def form(title: str, rows: list[list[dict[str, Any]]]) -> dict[str, Any]:
    """AcroForm section: each row lists fields made with :func:`field` laid out left to right."""
    return {"kind": "form", "title": title, "rows": rows}


def field(name: str, label: str, value: str | bool, *, field_type: str = "text", width: float = 1.0,
          options: list[str] | None = None, max_len: int = 0, multiline: bool = False) -> dict[str, Any]:
    """One AcroForm field; ``width`` is the share of its row. Checkbox values are booleans."""
    return {"name": name, "label": label, "value": value, "field_type": field_type, "width": width,
            "options": options or [], "max_len": max_len, "multiline": multiline}


# ------------------------------------------------------------------ truth


def _list_items(items: list[Any]) -> list[Any]:
    out: list[Any] = []
    for entry in items:
        if isinstance(entry, dict):
            out.append({"text": model.plain(entry["text"]), "ordered": entry["ordered"], "items": _list_items(entry["items"])})
        else:
            out.append(model.plain(entry))
    return out


def list_strings(items: list[Any]) -> list[str]:
    """Flatten nested list items to strings in reading order."""
    out: list[str] = []
    for entry in items:
        if isinstance(entry, dict):
            out.append(entry["text"])
            out += list_strings(entry["items"])
        else:
            out.append(entry)
    return out


def truth_blocks(block: dict[str, Any], page: int) -> list[dict[str, Any]]:
    """Project one authored leaf block onto truth blocks with a page index."""
    kind = block["kind"]
    if kind == "list":
        result = {"kind": "list", "ordered": block["ordered"], "items": _list_items(block["items"])}
    elif kind == "table":
        result = model.truth_block(block)
        for key in ("continues_from", "logical_id", "repeated_header"):
            if key in block:
                result[key] = block[key]
    elif kind == "code":
        result = {"kind": "code", "text": block["text"], "language": block["language"]}
        if block.get("caption"):
            result["caption"] = model.plain(block["caption"])
    elif kind == "equation":
        result = {"kind": "equation", "id": block["id"], "text": block["text"], "number": block["number"],
                  "mathml": block["mathml"]}
    elif kind == "form":
        out = [{"kind": "heading", "level": 2, "text": block["title"], "page": page}] if block["title"] else []
        for row in block["rows"]:
            for spec in row:
                value = spec["value"]
                out.append({"kind": "form_field", "name": spec["name"], "label": spec["label"], "field_type": spec["field_type"],
                            "value": value, "options": list(spec["options"]), "page": page})
        return out
    else:
        result = model.truth_block(block)
    result["page"] = page
    return [result]


def native_strings(block: dict[str, Any]) -> list[str]:
    """Strings carried by the native text layer for one truth block (used for Unicode features and page checks)."""
    kind = block["kind"]
    if kind == "list":
        return list_strings(block["items"])
    if kind in {"code", "equation"}:
        return [block["text"]]
    if kind == "form_field":
        return [block["label"]] + ([block["value"]] if isinstance(block["value"], str) else [])
    return model.native_strings(block)


def leaves(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand layout containers in reading order."""
    return model.flatten(blocks)


def truth(doc: dict[str, Any], *, page_count: int, outline: list[dict[str, Any]], pdf_facts: dict[str, Any]) -> dict[str, Any]:
    """Project an authored, media-resolved document onto the wild-v2 truth schema."""
    blocks: list[dict[str, Any]] = []
    for number, page_blocks in enumerate(doc["pages"], start=1):
        if doc.get("running_header"):
            blocks.append({"kind": "header", "text": doc["running_header"].format(page=number, pages=page_count), "page": number})
        for block in leaves(page_blocks):
            blocks += truth_blocks(block, number)
        if doc.get("running_footer"):
            blocks.append({"kind": "footer", "text": doc["running_footer"].format(page=number, pages=page_count), "page": number})
    links: list[dict[str, Any]] = []
    for number, page_blocks in enumerate(doc["pages"], start=1):
        for markup in markup_strings(page_blocks):
            links += [{**link, "page": number} for link in model.links(markup)]
    native = [s for block in blocks for s in native_strings(block)]
    tables = [b for b in blocks if b["kind"] == "table"]
    return {
        "version": 2, "corpus": "wild-v2", "doc_id": doc["doc_id"], "template": doc["template"], "producer": doc["producer"],
        "producer_detail": pdf_facts.get("producer_detail", {}), "tagged": bool(pdf_facts.get("tagged")),
        "base_plan_id": None, "family": doc.get("family", doc["template"]), "page_count": page_count,
        "page_size": doc["page_size"], "metadata": doc["metadata"], "outline": outline, "links": links, "blocks": blocks,
        "continued_tables": [{"logical_id": t["logical_id"], "segment": t["id"], "continues_from": t["continues_from"],
                              "page": t["page"]} for t in tables if "continues_from" in t],
        "languages": doc["languages"], "dir": doc.get("dir", "ltr"),
        "unicode_features": model.detect_features(native), "arithmetic": list(doc.get("arithmetic", [])),
    }


def markup_strings(blocks: list[dict[str, Any]]) -> list[str]:
    """Inline-markup strings of authored blocks (for link discovery)."""
    out: list[str] = []
    for block in leaves(blocks):
        out += [block[key] for key in ("text", "title", "caption") if isinstance(block.get(key), str) and block["kind"] != "code"]
        if block["kind"] == "list":
            out += list_strings(block["items"])
    return out


# ------------------------------------------------------------------ validation


TABLE_KEYS = {"kind", "id", "rendering", "header_rows", "values", "spans", "caption", "page"}
TABLE_OPTIONAL = {"continues_from", "logical_id", "repeated_header"}


def _valid_items(items: Any) -> bool:
    if not isinstance(items, list) or not items:
        return False
    for entry in items:
        if isinstance(entry, dict):
            if not isinstance(entry.get("text"), str) or not isinstance(entry.get("ordered"), bool) or not _valid_items(entry.get("items")):
                return False
        elif not isinstance(entry, str):
            return False
    return True


def validate(record: dict[str, Any]) -> list[str]:
    """Return schema violations for one wild-v2 truth record (empty when valid)."""
    problems: list[str] = []
    required = {"version", "corpus", "doc_id", "template", "producer", "page_count", "metadata", "outline", "links", "blocks",
                "languages", "unicode_features", "continued_tables", "page_size", "tagged"}
    problems += [f"missing {key}" for key in sorted(required - record.keys())]
    if record.get("producer") not in PRODUCERS:
        problems.append("producer")
    for key in ("title", "author", "subject", "keywords", "lang", "created"):
        if key not in record.get("metadata", {}):
            problems.append(f"metadata.{key}")
    problems += [f"feature {f}" for f in record.get("unicode_features", []) if f not in model.UNICODE_FEATURES]
    pages = record.get("page_count", 0)
    ids: dict[str, dict[str, Any]] = {}
    for index, block in enumerate(record.get("blocks", [])):
        kind = block.get("kind")
        where = f"block {index} ({kind})"
        page = block.get("page")
        if not isinstance(page, int) or not 1 <= page <= pages:
            problems.append(where + " page")
        if kind == "heading":
            if not isinstance(block.get("level"), int) or not isinstance(block.get("text"), str):
                problems.append(where)
        elif kind in model.TEXT_KINDS:
            if not isinstance(block.get("text"), str) or set(block) != {"kind", "text", "page"}:
                problems.append(where)
        elif kind == "list":
            if not isinstance(block.get("ordered"), bool) or not _valid_items(block.get("items")):
                problems.append(where)
        elif kind == "table":
            values = block.get("values", [])
            if block.get("rendering") not in model.TABLE_RENDERINGS or not values:
                problems.append(where)
                continue
            width = len(values[0])
            if any(len(row) != width for row in values):
                problems.append(where + " ragged")
            slots = {(s["row"], s["column"]) for s in block["spans"]}
            covered = {(r, c) for r, row in enumerate(values) for c, v in enumerate(row) if v is None}
            if slots & covered or len(slots) + len(covered) != len(values) * width:
                problems.append(where + " spans")
            if not set(block) >= TABLE_KEYS or set(block) - TABLE_KEYS - TABLE_OPTIONAL:
                problems.append(where + " keys")
            if block["id"] in ids:
                problems.append(where + " duplicate id")
            ids[block["id"]] = block
            if "continues_from" in block:
                previous = ids.get(block["continues_from"])
                if previous is None or previous["page"] >= page or previous.get("logical_id", previous["id"]) != block.get("logical_id"):
                    problems.append(where + " continuation")
                elif previous["values"][:block["header_rows"]] != values[:block["header_rows"]] or len(previous["values"][0]) != width:
                    problems.append(where + " repeated header")
        elif kind == "figure":
            if block.get("figure_kind") not in model.FIGURE_KINDS or block.get("wrap") not in {"left", "right", "none"}:
                problems.append(where)
        elif kind == "code":
            if not isinstance(block.get("text"), str) or not block["text"]:
                problems.append(where)
        elif kind == "equation":
            if not isinstance(block.get("text"), str) or not isinstance(block.get("mathml"), str):
                problems.append(where)
        elif kind == "form_field":
            if block.get("field_type") not in {"text", "checkbox", "choice", "comb"} or not isinstance(block.get("name"), str):
                problems.append(where)
            if block["field_type"] == "checkbox" and not isinstance(block.get("value"), bool):
                problems.append(where + " checkbox value")
        else:
            problems.append(where + " unknown kind")
    return problems


# ------------------------------------------------------------------ arithmetic checks
#
# A document may declare ``"arithmetic": [...]`` so truth records which values must
# add up; ``check_arithmetic`` verifies them at build time and in tests. Kinds:
#   {"kind": "running_balance", "table": logical_id, "debit": col, "credit": col, "balance": col}
#       every body row with a debit or credit moves the balance; rows with neither
#       (opening, brought/carried forward) must repeat the current balance.
#   {"kind": "line_items", "table": logical_id, "quantity": col, "unit_price": col, "amount": col, "decimal": "."}
#       quantity x unit price = amount (rounded half up to the amount's decimals) where all three are present;
#       ``decimal`` is the decimal mark used in those columns (grouping separators are ignored).
#   {"kind": "column_sum", "table": logical_id, "columns": [col, ...], "label_column": col, "total_label": "Total"}
#       the row labelled ``total_label`` equals the sum of the body rows before it.
#   {"kind": "sum", "terms": [["+", "1,234.50"], ["-", "200.00"]], "equals": "1,034.50"}
#       a signed sum of formatted amounts quoted in prose or summary boxes.


def amount(text: str) -> int:
    """Parse a formatted amount to minor units (any Unicode decimal digits; −, -, △, parentheses or trailing minus)."""
    stripped = text.strip()
    digits = "".join(str(unicodedata.digit(ch)) for ch in stripped if unicodedata.category(ch) == "Nd")
    if not digits:
        raise ValueError(f"no digits in {text!r}")
    negative = stripped.startswith(("−", "-", "(", "‑", "△", "▲")) or stripped.endswith((")", "-", "−"))
    return -int(digits) if negative else int(digits)


def decimal_value(text: str, decimal: str = ".") -> Decimal:
    """Parse a locale number (``decimal`` is the decimal mark; other separators are grouping)."""
    cleaned = "".join(str(unicodedata.digit(ch)) if unicodedata.category(ch) == "Nd" else ch for ch in text)
    kept = "".join(ch for ch in cleaned if ch.isdigit() or ch == decimal)
    if not any(ch.isdigit() for ch in kept):
        raise ValueError(f"no number in {text!r}")
    value = Decimal(kept.replace(decimal, ".")) if decimal != "." else Decimal(kept)
    stripped = text.strip()
    return -value if stripped.startswith(("−", "-", "(", "△", "▲")) else value


def logical_rows(record: dict[str, Any], table_id: str) -> list[list[str | None]]:
    """Body rows of one logical table across all its segments (repeated headers removed)."""
    rows: list[list[str | None]] = []
    for block in record["blocks"]:
        if block["kind"] == "table" and block.get("logical_id", block["id"]) == table_id:
            rows += block["values"][block["header_rows"]:]
    if not rows:
        raise ValueError(f"no table {table_id}")
    return rows


def check_arithmetic(record: dict[str, Any]) -> list[str]:
    """Return failed arithmetic declarations (empty when everything adds up)."""
    failures: list[str] = []
    for check in record.get("arithmetic", []):
        kind = check["kind"]
        try:
            if kind == "running_balance":
                balance: int | None = None
                for row in logical_rows(record, check["table"]):
                    debit, credit, value = row[check["debit"]], row[check["credit"]], row[check["balance"]]
                    if not value:
                        continue
                    current = amount(value)
                    if debit or credit:
                        if balance is None:
                            failures.append(f"{check['table']}: movement before an opening balance")
                            break
                        balance = balance - (amount(debit) if debit else 0) + (amount(credit) if credit else 0)
                        if balance != current:
                            failures.append(f"{check['table']}: balance {value} != computed {balance}")
                            break
                    elif balance is not None and current != balance:
                        failures.append(f"{check['table']}: carried {value} != {balance}")
                        break
                    balance = current
            elif kind == "line_items":
                mark = check.get("decimal", ".")
                for row in logical_rows(record, check["table"]):
                    quantity, unit, total = row[check["quantity"]], row[check["unit_price"]], row[check["amount"]]
                    if not (quantity and unit and total) or not any(ch.isdigit() for ch in quantity):
                        continue
                    got = decimal_value(total, mark)
                    places = Decimal(1).scaleb(got.as_tuple().exponent)
                    expected = (decimal_value(quantity, mark) * decimal_value(unit, mark)).quantize(places, rounding=ROUND_HALF_UP)
                    if expected != got:
                        failures.append(f"{check['table']}: {quantity} x {unit} = {expected} != {total}")
            elif kind == "column_sum":
                rows = logical_rows(record, check["table"])
                labels = [row[check["label_column"]] for row in rows]
                if check["total_label"] not in labels:
                    failures.append(f"{check['table']}: no row labelled {check['total_label']!r}")
                    continue
                end = labels.index(check["total_label"])
                for column in check["columns"]:
                    total = sum(amount(row[column]) for row in rows[:end] if row[column])
                    if total != amount(rows[end][column] or "0"):
                        failures.append(f"{check['table']}: column {column} sums to {total}, total says {rows[end][column]}")
            elif kind == "sum":
                total = sum(amount(value) * (-1 if sign == "-" else 1) for sign, value in check["terms"])
                if total != amount(check["equals"]):
                    failures.append(f"sum {check['terms']} = {total} != {check['equals']}")
            else:
                failures.append(f"unknown arithmetic kind {kind}")
        except (ValueError, IndexError, TypeError) as error:
            failures.append(f"{kind}: {error}")
    return failures
