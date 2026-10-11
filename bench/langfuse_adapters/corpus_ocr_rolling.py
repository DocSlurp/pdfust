"""Raster OCR to rolling/physical table assembly on the borderless DEV corpus, per page.

Source: ``ocr-rolling-v1/<version>/scores.json`` and ``overlap-a004-v1/scores.json`` from
``bench/ocr_rolling.py``; committed summaries ``bench/results/ocr-rolling.md`` and
``bench/results/ocr-rolling-overlap.md``. ``<version>`` is the borderless-dev-v1 dataset, whose
authored targets are reused as expected outputs. Each run is one ``(edge, assembly)`` OCR arm
(pure OCR and native-vector hybrid scores side by side) or one A004 overlap allowance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.corpus_common import Score, mtime, numeric, ref, rel, scalars

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "corpus-ocr-rolling"
STUDY = "ocr-rolling-v1"
CORPUS = "borderless-dev-v1"
PATHS = ("pure", "hybrid")


def _aggregate(records: list[dict[str, Any]], kinds: dict[str, str]) -> dict[str, Score]:
    """Report-style counts: exact borderless/controls, prose false positives, complete exact pages."""
    scores: dict[str, Any] = {"pages": float(len(records))}
    for path in PATHS:
        for record in records:
            values = record.get(path) or {}
            kind = kinds.get(record["id"]) or record.get("kind") or "unknown"
            scores[f"{path}.{kind}.pages"] = scores.get(f"{path}.{kind}.pages", 0.0) + 1
            for name in ("exact_cells", "exact_page", "false_positive_page", "owned_values", "owned_words"):
                key = f"{path}.{kind}.{name}"
                scores[key] = scores.get(key, 0.0) + float(values.get(name) or 0)
            scores[f"{path}.complete_exact"] = scores.get(f"{path}.complete_exact", 0.0) + float(
                bool(values.get("exact_page")) and kind != "prose"
            )
    return scores


def _items(version: Path, corpus: Path) -> list[Item]:
    inputs = read_json(version / "inputs.json")
    targets_path = corpus / "private-targets.json"
    targets = {row["id"]: row for row in read_json(targets_path)} if targets_path.is_file() else {}
    by_case: dict[str, list[dict[str, Any]]] = {}
    for page in inputs.get("pages", []):
        by_case.setdefault(page["id"], []).append(page)
    return [
        Item(
            key=case,
            input={
                "case": case,
                "source_pdf_sha256": pages[0].get("source_pdf_sha256"),
                "pdf": ref(corpus / "pdfs" / f"{case}.pdf"),
                "rasters": {
                    f"e{page['edge']}": {
                        "dpi": page.get("dpi"),
                        **(ref(version / "pixels" / f"{case}-e{page['edge']}.png") or {}),
                    }
                    for page in pages
                },
            },
            expected=targets.get(case),
            metadata={"kind": (targets.get(case) or {}).get("kind")},
        )
        for case, pages in sorted(by_case.items())
    ]


def _arm_runs(version: Path, kinds: dict[str, str]) -> list[Run]:
    path = version / "scores.json"
    groups: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for record in read_json(path):
        groups.setdefault((int(record["edge"]), record["variant"]), []).append(record)
    runs = []
    for (edge, variant), records in sorted(groups.items()):
        rows = []
        for record in records:
            recall = record.get("original_token_recall") or {}
            complete = record.get("status") == "complete"
            rows.append(
                Row(
                    item_key=record["id"],
                    output={
                        "status": record.get("status"),
                        "ocr_items": record.get("ocr_items"),
                        "observed_sha256": record.get("observed_sha256"),
                        "candidates": ref(version / str(edge) / record["id"] / "candidates.json"),
                    },
                    scores={
                        "completed": complete,
                        **(numeric(record.get("pure"), "pure.") if complete else {}),
                        **(numeric(record.get("hybrid"), "hybrid.") if complete else {}),
                        "native_override": record.get("native_override"),
                        "ocr_ids_conserved": record.get("ocr_ids_conserved"),
                        "target_token_recall": recall.get("recall"),
                        "target_tokens_matched": recall.get("matched_tokens"),
                        "ocr_items": record.get("ocr_items"),
                        "multi_token_ocr_items": record.get("multi_token_ocr_items"),
                        **numeric(record.get("geometry_diagnostics"), "geometry."),
                    },
                    metadata={
                        "status": record.get("status"),
                        "kind": kinds.get(record["id"], record.get("kind")),
                        "edge": edge,
                        "variant": variant,
                        "ocr_seconds": record.get("ocr_seconds"),
                        "ocr_cpu_seconds": record.get("ocr_cpu_seconds"),
                        "whole_worker_wall_seconds": record.get("whole_worker_wall_seconds"),
                        "peak_rss_kib": record.get("peak_rss_kib"),
                        **scalars(record.get("initialization") or {}, "initialization."),
                    },
                    wall_ms=(record.get("ocr_seconds") or 0) * 1000,
                    name=f"{STUDY}/{record['id']}/e{edge}-{variant}",
                )
            )
        scores = _aggregate([r for r in records if r.get("status") == "complete"], kinds)
        scores |= {
            "pages": float(len(records)),
            "refused_or_missing": float(sum(r.get("status") != "complete" for r in records)),
            "ocr_ids_conserved": float(sum(bool(r.get("ocr_ids_conserved")) for r in records)),
            "ocr_seconds_total": sum(float(r.get("ocr_seconds") or 0) for r in records),
            "ocr_cpu_seconds_total": sum(float(r.get("ocr_cpu_seconds") or 0) for r in records),
            "max_peak_rss_kib": float(max((r.get("peak_rss_kib") or 0) for r in records)),
        }
        runs.append(
            Run(
                name=f"e{edge} {variant}",
                description=(
                    f"Native OCR at max edge {edge}px, {variant} row assembly; pure OCR and native-vector hybrid "
                    "scores against authored borderless targets (correlated authored DEV evidence)"
                ),
                rows=rows,
                metadata={"edge": edge, "variant": variant, "run_file": rel(path), "summary_check": "not-retained"},
                scores=scores,
                started=mtime(path),
            )
        )
    return runs


def _overlap_runs(version: Path, kinds: dict[str, str]) -> list[Run]:
    directory = version / "overlap-a004-v1"
    path = directory / "scores.json"
    if not path.is_file():
        return []
    config_path = directory / "frozen-config.json"
    config = read_json(config_path) if config_path.is_file() else {}
    resources_path = directory / "resources.json"
    resources = read_json(resources_path) if resources_path.is_file() else {}
    groups: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for record in read_json(path):
        groups.setdefault((int(record["edge"]), str(record["allowance"])), []).append(record)
    runs = []
    for (edge, allowance), records in sorted(groups.items()):
        rows = [
            Row(
                item_key=record["id"],
                output={"wrap": record.get("wrap"), "conserved": record.get("conserved")},
                scores={
                    **numeric(record.get("pure"), "pure."),
                    **numeric(record.get("hybrid"), "hybrid."),
                    "ocr_ids_conserved": record.get("conserved"),
                },
                metadata={
                    "status": "complete",
                    "kind": kinds.get(record["id"], record.get("kind")),
                    "edge": edge,
                    "allowance": allowance,
                    "wrap": record.get("wrap"),
                },
                name=f"{STUDY}/{record['id']}/a004-e{edge}-{allowance}",
            )
            for record in records
        ]
        runs.append(
            Run(
                name=f"overlap-a004 e{edge} allowance-{allowance}",
                description=(
                    f"A004 OCR-overlap ablation: rolling assembly at edge {edge}px allowing {allowance} line-height "
                    "overlap for sparse nonnumeric continuations (no new OCR calls)"
                ),
                rows=rows,
                metadata={
                    "edge": edge,
                    "allowance": allowance,
                    "run_file": rel(path),
                    "assembler_sha256": config.get("assembler_sha256"),
                    **scalars(resources, "resources."),
                    "summary_check": "not-retained",
                },
                scores={
                    **_aggregate(records, kinds),
                    "ocr_ids_conserved": float(sum(bool(r.get("conserved")) for r in records)),
                    "pure.wrapped.pages": float(sum(bool(r.get("wrap")) for r in records)),
                    "pure.wrapped.exact_cells": float(
                        sum(bool(r.get("wrap")) and bool((r.get("pure") or {}).get("exact_cells")) for r in records)
                    ),
                },
                started=mtime(path),
            )
        )
    return runs


def collect(artifacts: Path) -> Iterable[Experiment]:
    """One dataset per OCR study version."""
    root = guard(artifacts / STUDY)
    for version in sorted(p for p in root.iterdir() if (p / "scores.json").is_file()) if root.is_dir() else []:
        corpus = guard(artifacts / CORPUS / version.name)
        targets_path = corpus / "private-targets.json"
        kinds = {row["id"]: str(row.get("kind")) for row in read_json(targets_path)} if targets_path.is_file() else {}
        yield Experiment(
            dataset=f"exp/{STUDY}/{version.name}",
            description=(
                "Borderless DEV pages rendered to frozen rasters, natively OCRed, then assembled into tables. "
                "Runs: OCR edge x assembly arms (pure and hybrid scores) and the A004 overlap ablation. "
                "Authored silver targets; correlated DEV evidence."
            ),
            items=_items(version, corpus),
            runs=_arm_runs(version, kinds) + _overlap_runs(version, kinds),
            source=rel(version),
        )
