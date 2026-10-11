"""Shared helpers for the corpus benchmark adapters (``corpus_*.py``).

This module defines no ``NAME``/``collect`` and is therefore not an adapter.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import ROOT, file_ref, guard

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

Score = float | bool | int | None
TOLERANCE = 1e-9


def rel(path: Path) -> str:
    """Repository-relative path when possible."""
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def ref(path: Path) -> dict[str, Any] | None:
    """``file_ref`` for an existing file, else ``None`` (missing inputs stay visible as null)."""
    return file_ref(path) if guard(path).is_file() else None


def mtime(path: Path) -> float | None:
    """File modification time as an approximate run start."""
    return path.stat().st_mtime if path.exists() else None


def jsonl(path: Path) -> list[dict[str, Any]]:
    """Read JSON Lines from a guarded path."""
    return [json.loads(line) for line in guard(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def numeric(scores: dict[str, Any] | None, prefix: str = "") -> dict[str, Score]:
    """Keep numeric/boolean values (nested dicts flattened with dots); drop ``None`` and text."""
    result: dict[str, Score] = {}
    for key, value in (scores or {}).items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            result.update(numeric(value, f"{name}."))
        elif isinstance(value, (bool, int, float)):
            result[name] = value
    return result


def scalars(values: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten scalar metadata (strings, numbers, booleans, None) with dotted keys."""
    result: dict[str, Any] = {}
    for key, value in values.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            result.update(scalars(value, f"{name}."))
        elif value is None or isinstance(value, (str, int, float, bool)):
            result[name] = value
    return result


def compact_tables(tables: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Table observations without per-cell geometry: shape, values, strategy and confidence."""
    compact = []
    for table in tables or []:
        diagnostics = table.get("diagnostics") or {}
        compact.append(
            {
                "rows": table.get("row_count"),
                "columns": table.get("col_count"),
                "values": table.get("values"),
                **({"strategy": diagnostics["strategy"]} if "strategy" in diagnostics else {}),
                **({"confidence": diagnostics["confidence"]} if "confidence" in diagnostics else {}),
            }
        )
    return compact


def tally(rows: Iterable[tuple[str, dict[str, Any]]], fields: Iterable[str]) -> dict[str, dict[str, float]]:
    """Sum integer/boolean score fields per group (``None`` counts as zero)."""
    fields = tuple(fields)
    totals: dict[str, dict[str, float]] = {}
    for group, scores in rows:
        bucket = totals.setdefault(group, dict.fromkeys(fields, 0.0))
        for name in fields:
            value = scores.get(name)
            if isinstance(value, (bool, int, float)):
                bucket[name] += float(value)
    return totals


def compare(computed: dict[str, Any], reported: dict[str, Any]) -> list[str]:
    """Return ``name: computed != reported`` for every reported numeric key that disagrees."""
    mismatches = []
    for name, value in sorted(numeric(reported).items()):
        if name in computed and abs(float(computed[name]) - float(value or 0)) > TOLERANCE:
            mismatches.append(f"{name}: computed {computed[name]:g} != reported {float(value or 0):g}")
    return mismatches


def check_metadata(mismatches: list[str]) -> dict[str, Any]:
    """Run metadata recording the cross-check against the retained summary."""
    return {
        "summary_check": "match" if not mismatches else "mismatch",
        "summary_mismatches": "; ".join(mismatches)[:900] if mismatches else None,
    }
