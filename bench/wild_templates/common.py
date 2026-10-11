"""Helpers shared by the authored wild-v1 document builders."""

# ruff: noqa: ANN401, C901, E501, EM101, EM102, PLR0913, PLR0917, TRY003

from __future__ import annotations

import unicodedata
from typing import Any

from bench.wild_templates import model

MAX_ROWS = 14


def shape(plan: dict[str, Any], index: int = 0, cap: int = MAX_ROWS) -> dict[str, Any]:
    """Return the structural shape of one plan table (rows trimmed to ``cap`` unless merged)."""
    source = plan["tables"][index]
    rows = source["target"]["row_count"]
    if not source["merges"]:
        rows = min(rows, cap)
    return {"rows": rows, "cols": source["target"]["col_count"], "kinds": list(source["kinds"]),
            "merges": tuple(tuple(m) for m in source["merges"]), "ruled": source["ruled"]}


def assemble(kinds: list[str], rows: list[dict[str, list[str]]]) -> list[list[str]]:
    """Place semantic per-kind values into the plan's column order.

    Each row maps a value kind to its values in left-to-right occurrence order,
    so a plan with two ``word2`` columns takes ``{"word2": [first, second]}``.
    """
    result = []
    for row in rows:
        queues = {kind: list(values) for kind, values in row.items()}
        cells = []
        for kind in kinds:
            if not queues.get(kind):
                raise ValueError(f"Missing {kind} value for row {row}")
            cells.append(queues[kind].pop(0))
        leftovers = {k: v for k, v in queues.items() if v}
        if leftovers:
            raise ValueError(f"Unused values {leftovers}")
        result.append(cells)
    return result


def align(kinds: list[str], numeric: tuple[str, ...] = ("usd",)) -> list[str]:
    """Right-align money (and other numeric) columns."""
    return ["r" if kind in numeric else "l" for kind in kinds]


def plan_table(plan: dict[str, Any], index: int, table_id: str, rendering: str, kinds: list[str],
               rows: list[dict[str, list[str]]], *, header: dict[str, list[str]] | None, caption: str = "",
               total: dict[str, list[str]] | None = None, subheader: dict[str, list[str]] | None = None,
               numeric: tuple[str, ...] = ("usd",), **hints: Any) -> dict[str, Any]:
    """Build a plan-derived table block preserving shape, merges and blank header rows."""
    spec = shape(plan, index)
    if kinds != spec["kinds"]:
        raise ValueError("Kinds must follow the plan")
    matrix: list[list[str]] = []
    header_rows = 1
    if header is None:  # unnamed family: blank first row
        matrix.append([""] * spec["cols"])
        header_rows = 0
    else:
        matrix += assemble(kinds, [header])
    if subheader is not None:
        matrix += assemble(kinds, [subheader])
        header_rows = 2
    body_count = spec["rows"] - len(matrix) - (1 if total else 0)
    if len(rows) < body_count:
        raise ValueError(f"Need {body_count} rows, got {len(rows)}")
    matrix += assemble(kinds, rows[:body_count])
    total_rows = []
    if total:
        total_rows.append(len(matrix))
        matrix += assemble(kinds, [total])
    if spec["merges"]:  # merged header cells: covered header slots carry an empty authored value
        for r, c, rs, cs in spec["merges"]:
            for row in range(r, r + rs):
                for col in range(c, c + cs):
                    if (row, col) != (r, c) and matrix[row][col]:
                        raise ValueError("Covered merge slots must be authored empty")
    return model.table(table_id, rendering, matrix, header_rows=header_rows, merges=spec["merges"], caption=caption,
                       align=align(kinds, numeric), total_rows=total_rows, plan_table=index, **hints)


def nfd(value: Any) -> Any:
    """Recursively normalize authored strings to NFD (Vietnamese decomposed-text profile)."""
    if isinstance(value, str):
        return unicodedata.normalize("NFD", value)
    if isinstance(value, list):
        return [nfd(v) for v in value]
    if isinstance(value, tuple):
        return tuple(nfd(v) for v in value)
    if isinstance(value, dict):
        return {k: (v if k in {"kind", "rendering", "cls", "src", "wrap", "figure_kind", "id", "render"} else nfd(v))
                for k, v in value.items()}
    return value


def H(level: int, text: str, **hints: Any) -> dict[str, Any]:  # noqa: N802
    """Heading block."""
    return {"kind": "heading", "level": level, "text": text, **hints}


def P(text: str, cls: str = "") -> dict[str, Any]:  # noqa: N802
    """Paragraph block."""
    return {"kind": "paragraph", "text": text, "cls": cls}


def L(items: list[str], *, ordered: bool = False) -> dict[str, Any]:  # noqa: N802
    """List block."""
    return {"kind": "list", "ordered": ordered, "items": items}


def box(kind: str, text: str, title: str = "", cls: str = "") -> dict[str, Any]:
    """Sidebar, callout or footnote."""
    block = {"kind": kind, "text": text, "cls": cls}
    if title:
        block["title"] = title
    return block


def group(blocks: list[dict[str, Any]], cls: str = "") -> dict[str, Any]:
    """Layout-only container."""
    return {"kind": "group", "cls": cls, "blocks": blocks}


def photo(figure_id: str, prefer: list[str], tags: list[str], captions: dict[str, str], fallback: str,
          wrap: str, width: str = "42%", width_cm: float = 6.5) -> dict[str, Any]:
    """Photo figure resolved against ``photos.json`` at build time."""
    return {"kind": "figure", "id": figure_id, "figure_kind": "photo", "wrap": wrap, "width": width, "width_cm": width_cm,
            "photo": {"prefer": prefer, "tags": tags, "captions": captions, "fallback": fallback}, "caption": fallback}


def screenshot(figure_id: str, mockup: str, spec: dict[str, Any], caption: str, *, wrap: str = "none",
               width: str = "100%", width_cm: float = 15.0) -> dict[str, Any]:
    """UI screenshot figure rendered by headless Chromium at build time."""
    return {"kind": "figure", "id": figure_id, "figure_kind": "screenshot", "wrap": wrap, "width": width,
            "width_cm": width_cm, "render": {"mockup": mockup, "spec": spec}, "caption": caption, "cls": "shadow"}


def chart(figure_id: str, chart_type: str, spec: dict[str, Any], caption: str, *, raster: bool, wrap: str = "none",
          width: str = "100%", width_cm: float = 15.0, size: tuple[int, int] = (520, 230)) -> dict[str, Any]:
    """Vector (inline SVG, labels as text) or raster (PNG screenshot) chart figure."""
    return {"kind": "figure", "id": figure_id, "figure_kind": "chart", "wrap": wrap, "width": width, "width_cm": width_cm,
            "chart": {"type": chart_type, "spec": spec, "raster": raster, "size": size}, "caption": caption}


def chart_table(table_id: str, label: str, spec: dict[str, Any], fmt: Any, caption: str = "") -> dict[str, Any]:
    """Underlying chart values as a ``chart_data`` table (not drawn as a table)."""
    values = [[label, *[name for name, _ in spec["series"]]]]
    values += [[category, *[fmt(series[i]) for _, series in spec["series"]]] for i, category in enumerate(spec["categories"])]
    return model.table(table_id, "chart_data", values, caption=caption)
