"""Borderless companion DEV challenge: per-page route results for every retained run.

Source: ``borderless-dev-v1/<version>/run-*/{summary,private-scores}.json`` written by
``bench/borderless_challenge.py``; committed summary ``bench/results/borderless-challenge.md``.
Each run directory evaluates six frozen routes over the same 28 authored pages, so one
Langfuse run is one ``(run directory, route)`` pair. Errored pages stay in the run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.corpus_common import (
    check_metadata,
    compact_tables,
    compare,
    mtime,
    numeric,
    ref,
    rel,
    scalars,
    tally,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "corpus-borderless"
CORPUS = "borderless-dev-v1"
FIELDS = ("exact_cells", "exact_page", "exact_spans", "false_positive_page", "owned_values", "owned_words")


def _items(version: Path, targets: dict[str, dict[str, Any]]) -> list[Item]:
    manifest = read_json(version / "manifest.json")
    items = []
    for case in manifest["cases"]:
        target = targets.get(case["id"], {})
        items.append(
            Item(
                key=case["id"],
                input={"case": case["id"], "pdf": ref(version / case.get("pdf_path", f"pdfs/{case['id']}.pdf"))},
                expected=target or None,
                metadata={"kind": target.get("kind"), "setting": target.get("setting"), "wrap": target.get("wrap")},
            )
        )
    return items


def _run(run_dir: Path, route: str, rows: list[dict[str, Any]], kinds: dict[str, str]) -> Run:
    summary = read_json(run_dir / "summary.json")
    reported = (summary.get("results") or {}).get(route, {})
    out: list[Row] = []
    for record in rows:
        ok = record.get("status") == "ok"
        image = run_dir / f"{record['id']}.png"
        out.append(
            Row(
                item_key=record["id"],
                output={
                    "status": record.get("status"),
                    "tables": compact_tables(record.get("observed")) if "observed" in record else None,
                    **({"error": record["error"]} if "error" in record else {}),
                },
                scores={"completed": ok, **(numeric(record.get("scores")) if ok else {})},
                metadata={
                    "status": record.get("status"),
                    "route": route,
                    "kind": kinds.get(record["id"]),
                    "image_path": rel(image) if image.is_file() else None,
                },
                name=f"{CORPUS}/{record['id']}/{route}",
            )
        )
    computed = tally(
        ((kinds.get(r["id"], "unknown"), r.get("scores") or {}) for r in rows if r.get("status") == "ok"), FIELDS
    )
    flat = {f"{kind}.{name}": value for kind, values in computed.items() for name, value in values.items()}
    flat["errors"] = float(sum(r.get("status") != "ok" for r in rows))
    flat["pages"] = float(len(rows))
    resources = summary.get("resources") or {}
    return Run(
        name=f"{run_dir.name} {route}",
        description=(
            f"borderless_challenge route {route!r} over authored DEV borderless/prose/ruled-control pages "
            "(repository-authored silver, not adjudicated gold)"
        ),
        rows=out,
        metadata={
            "route": route,
            "run_directory": rel(run_dir),
            "runner_sha256": summary.get("runner_sha256"),
            "rules_sha256": summary.get("rules_sha256"),
            "dataset_sha256": summary.get("dataset_sha256"),
            **scalars(resources, "resources."),
            **check_metadata(compare(flat, reported)),
        },
        scores=numeric(reported),
        started=mtime(run_dir / "summary.json"),
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """One dataset per corpus version; one run per (run directory, route)."""
    root = guard(artifacts / CORPUS)
    for version in sorted(p for p in root.iterdir() if (p / "manifest.json").is_file()) if root.is_dir() else []:
        targets_path = version / "private-targets.json"
        targets = {row["id"]: row for row in read_json(targets_path)} if targets_path.is_file() else {}
        kinds = {key: str(value.get("kind")) for key, value in targets.items()}
        runs: list[Run] = []
        for run_dir in sorted(version.glob("run-*/")):
            scores_path = run_dir / "private-scores.json"
            if not scores_path.is_file() or not (run_dir / "summary.json").is_file():
                continue
            by_route: dict[str, list[dict[str, Any]]] = {}
            for record in read_json(scores_path):
                by_route.setdefault(record["route"], []).append(record)
            runs.extend(_run(run_dir, route, rows, kinds) for route, rows in by_route.items())
        yield Experiment(
            dataset=f"exp/{CORPUS}/{version.name}",
            description=(
                "Borderless companion DEV challenge (12 borderless, 12 numeric prose negatives, 4 ruled controls). "
                "Runs are (run directory, route); scores are the challenge's exact-cell/span/page, false-positive "
                "and ownership counts. Authored silver targets, not adjudicated gold."
            ),
            items=_items(version, targets),
            runs=runs,
            source=rel(version),
        )
