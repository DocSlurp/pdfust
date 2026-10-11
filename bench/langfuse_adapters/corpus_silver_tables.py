"""Silver-v1 bordered-table structure and corpus-route screens, per physical page.

Sources under ``silver-v1/<version>/``:

- ``structure-runs/<stamp>/`` from ``bench/silver_structure.py`` (``lines`` and ``text``
  strategies; committed summary ``bench/results/silver-structure.md``);
- ``corpus-route-runs/<stamp>/`` from ``bench/corpus_routes.py`` (five frozen routes;
  committed summary ``bench/results/corpus-routes.md``).

Both score the same 125 pages against the same authored ``targets.json``, so they share one
dataset. One Langfuse run is one ``(run directory, strategy or route)`` pair.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.corpus_common import (
    check_metadata,
    compact_tables,
    compare,
    jsonl,
    mtime,
    numeric,
    ref,
    rel,
    scalars,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "corpus-silver-tables"
CORPUS = "silver-v1"
SUMMED = (
    "cell_slots",
    "correct_cell_slots",
    "correct_owned_values",
    "detected_tables",
    "expected_tables",
    "false_positive_tables",
    "owned_values",
)


def page_key(record: dict[str, Any]) -> str:
    """Dataset key for one physical page."""
    return f"{record['id']}#p{record.get('page_number', 0)}"


def _computed(rows: list[dict[str, Any]], *, exact_suffix: str) -> dict[str, float]:
    """Recompute the retained totals from per-page rows."""
    ok = [r for r in rows if r.get("status") == "ok"]
    totals: dict[str, float] = dict.fromkeys(SUMMED, 0.0)
    for row in ok:
        for name in SUMMED:
            totals[name] += float((row.get("scores") or {}).get(name) or 0)
    for name in ("exact_page", "false_positive_page"):
        totals[name] = float(sum(bool((r.get("scores") or {}).get(name)) for r in ok))
    totals[f"exact{exact_suffix}cells"] = float(sum((r.get("scores") or {}).get("exact_cells") is True for r in ok))
    totals[f"exact{exact_suffix}spans"] = float(sum((r.get("scores") or {}).get("exact_spans") is True for r in ok))
    totals["errors"] = float(len(rows) - len(ok))
    totals["completed_pages"] = float(len(ok))
    totals["pages"] = float(len(rows))
    return totals


def _rows(rows: list[dict[str, Any]], arm: str, label: str, wall_key: str, cpu_key: str) -> list[Row]:
    out = []
    for record in rows:
        ok = record.get("status") == "ok"
        wall = record.get(wall_key)
        out.append(
            Row(
                item_key=page_key(record),
                output={
                    "status": record.get("status"),
                    "tables": compact_tables(record.get("observed")),
                    **({"error": record["error"]} if "error" in record else {}),
                },
                scores={"completed": ok, **(numeric(record.get("scores")) if ok else {})},
                metadata={
                    "status": record.get("status"),
                    label: arm,
                    "family": record.get("family"),
                    wall_key: wall,
                    cpu_key: record.get(cpu_key),
                },
                wall_ms=wall if isinstance(wall, (int, float)) else None,
                name=f"{CORPUS}/{page_key(record)}/{arm}",
            )
        )
    return out


def _runs(directory: Path, kind: str) -> list[Run]:
    summary = read_json(directory / "summary.json")
    totals = summary.get("totals") or {}
    pages = jsonl(directory / "pages.jsonl")
    label = "strategy" if kind == "structure" else "route"
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in pages:
        groups.setdefault(str(record.get(label)), []).append(record)
    if kind == "structure":
        wall_key, cpu_key, suffix = "wall_ms", "cpu_ms", "_table_"
        description = (
            "silver_structure strategy {arm!r}: authored bordered-table structure and non-table false positives"
        )
    else:
        wall_key, cpu_key, suffix = "shared_evidence_wall_ms", "shared_evidence_cpu_ms", "_"
        description = "corpus_routes frozen route {arm!r}: source-only table routing screen over all DEV pages"
    runs = []
    for arm, rows in groups.items():
        reported = totals.get(arm, {})
        runs.append(
            Run(
                name=f"{kind} {directory.name} {arm}",
                description=description.format(arm=arm) + " (repository-authored silver, not reviewed gold)",
                rows=_rows(rows, arm, label, wall_key, cpu_key),
                metadata={
                    label: arm,
                    "study": kind,
                    "run_directory": rel(directory),
                    "runner_sha256": summary.get("runner_sha256"),
                    "dataset_sha256": summary.get("dataset_sha256"),
                    **scalars(summary.get("resources") or {}, "resources."),
                    **check_metadata(compare(_computed(rows, exact_suffix=suffix), reported)),
                },
                scores=numeric(reported),
                started=mtime(directory / "summary.json"),
            )
        )
    return runs


def _items(version: Path, targets: dict[str, Any]) -> list[Item]:
    manifest = read_json(version / "manifest.json")
    cases = {case["id"]: case for case in manifest.get("cases", [])}
    items = []
    for page in targets.get("pages", []):
        case = cases.get(page["id"], {})
        pdf = version / case.get("pdf_path", f"pdfs/{page['id']}.pdf")
        items.append(
            Item(
                key=page_key(page),
                input={
                    "case": page["id"],
                    "page_number": page.get("page_number", 0),
                    "family": page.get("family"),
                    "encoding": page.get("encoding"),
                    "pdf": ref(pdf),
                },
                expected={"tables": compact_tables(page.get("tables")), "table_count": len(page.get("tables") or [])},
                metadata={"family": page.get("family"), "expected_tables": len(page.get("tables") or [])},
            )
        )
    return items


def collect(artifacts: Path) -> Iterable[Experiment]:
    """One dataset per (corpus version, targets content); structure and route runs share it."""
    root = guard(artifacts / CORPUS)
    for version in sorted(p for p in root.iterdir() if (p / "manifest.json").is_file()) if root.is_dir() else []:
        groups: dict[str, tuple[Path, list[Run]]] = {}
        for kind, folder in (("structure", "structure-runs"), ("routes", "corpus-route-runs")):
            for directory in sorted((version / folder).glob("*/")):
                target_path = directory / "targets.json"
                if not (target_path.is_file() and (directory / "pages.jsonl").is_file()):
                    continue
                key = hashlib.sha256(target_path.read_bytes()).hexdigest()[:12]
                groups.setdefault(key, (target_path, []))[1].extend(_runs(directory, kind))
        for index, (key, (target_path, runs)) in enumerate(sorted(groups.items(), key=lambda kv: str(kv[1][0]))):
            suffix = "" if index == 0 and len(groups) == 1 else f"-{key}"
            yield Experiment(
                dataset=f"exp/{CORPUS}/{version.name}/tables{suffix}",
                description=(
                    "Silver-v1 physical pages scored for authored bordered-table structure (exact cells/spans, "
                    "owned values) and non-table false positives. Runs: silver_structure strategies and "
                    "corpus_routes frozen routes. Repository-authored silver, not independently reviewed gold."
                ),
                items=_items(version, read_json(target_path)),
                runs=runs,
                source=rel(version),
            )
