"""P001 complete-page pipeline runs (``pipeline-p001``) as one Langfuse experiment.

Dataset ``exp/pipeline-p001/pages``: the 181 frozen DEV pages of
``pipeline-p001/corpus`` (manifest plus private authored silver targets).
Each completed run directory with a ``report.json`` becomes one Run. Pilot runs
cover only the 32 fixed pilot pages; full runs cover all 181. Absent results
remain ``missing`` rows, exactly as ``bench.pipeline_report`` charges them.

Per-page scores are recomputed with the campaign scorer
``bench.pipeline_scoring.score_page`` (the same call ``pipeline_report`` makes);
the reports retain no per-page score file. Run aggregates repeat the scorer
totals plus the report's own cost and resource fields. Provider-reported
charges, catalog estimates, and reservations stay separately named; a missing
or reserved effective total is omitted rather than written as zero.
"""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import ROOT, Experiment, Item, Row, Run, file_ref, guard, read_json
from bench.pipeline_scoring import conservation, score_dataset, score_page

if TYPE_CHECKING:
    from collections.abc import Iterable

NAME = "pipeline_p001"
CAMPAIGN = "pipeline-p001"
DATASET = "exp/pipeline-p001/pages"
_SCORE_KEYS = (
    "error",
    "malformed",
    "expected_tables",
    "detected_tables",
    "matched_tables",
    "missing_tables",
    "false_positive_tables",
    "false_positive_page",
    "exact_page",
    "complete_tables",
    "exact_table_cells",
    "exact_table_spans",
    "correct_cell_slots",
    "cell_slots",
    "penalized_cell_slots",
    "table_denominator",
)


def number(value: object) -> float | None:
    """Return a finite number, or None for booleans, missing, and non-finite values."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


def pdf_ref(artifacts: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Return a corpus PDF reference using its manifest hash, relocated under ``artifacts`` when needed."""
    original = str(record.get("pdf_path", ""))
    marker = "pdf-master-artifacts/"
    candidates = [artifacts / original.split(marker, 1)[1]] if marker in original else []
    if original:
        candidates.append(Path(original))
    path = next((guard(candidate) for candidate in candidates if guard(candidate).is_file()), None)
    reference: dict[str, Any] = {"sha256": record.get("pdf_sha256"), "page_number": record.get("page_number")}
    if path is not None:
        reference["path"] = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        reference["bytes"] = path.stat().st_size
    else:
        reference["path"] = original.split(marker, 1)[-1]
        reference["bytes"] = None
    return reference


def compact_table(table: dict[str, Any]) -> dict[str, Any]:
    """Keep table shape, literal values, optional bbox, and merged spans (1x1 spans omitted)."""
    result: dict[str, Any] = {
        "rows": table.get("row_count"),
        "cols": table.get("col_count"),
        "values": table.get("values"),
    }
    if table.get("bbox") is not None:
        result["bbox"] = table["bbox"]
    merged = [
        span
        for span in table.get("spans", []) or []
        if isinstance(span, dict) and (span.get("row_span", 1) != 1 or span.get("column_span", 1) != 1)
    ]
    if merged:
        result["merged_spans"] = merged
    return result


def call_costs(calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize retained calls without turning a missing charge into zero."""
    entries = [call.get("entry", {}) or {} for call in calls]
    reported = [number(entry.get("provider_reported_usd")) for entry in entries]
    accounted = [number(entry.get("accounted_usd")) for entry in entries]
    positive = [value for value in reported if value is not None and value > 0]
    return {
        "calls": len(entries),
        "provider_reported_usd": sum(positive)
        if positive
        else (0.0 if entries and reported and all(v == 0 for v in reported) else None),
        "provider_charge_missing": sum(value is None for value in reported),
        "provider_charge_zero": sum(value == 0 for value in reported),
        "accounted_usd": sum(value for value in accounted if value is not None)
        if accounted and None not in accounted
        else None,
        "cost_bases": dict(Counter(str(entry.get("cost_status", "unknown")) for entry in entries)),
        "models": sorted({str(entry.get("requested_model")) for entry in entries if entry.get("requested_model")}),
    }


def row_metadata(prediction: dict[str, Any]) -> dict[str, Any]:
    """Per-page status, timing, error, and cost metadata."""
    costs = call_costs(prediction.get("calls", []) or [])
    meta: dict[str, Any] = {
        "status": prediction.get("status", "missing"),
        "route": prediction.get("route"),
        "wall_seconds": number(prediction.get("wall_seconds")),
        "cpu_seconds": number(prediction.get("cpu_seconds")),
        "calls": costs["calls"],
        "provider_charge_missing": costs["provider_charge_missing"],
        "cost_bases": str(costs["cost_bases"]) if costs["cost_bases"] else None,
        "models": ", ".join(costs["models"]) or None,
    }
    if costs["provider_reported_usd"] is not None:
        meta["provider_reported_usd"] = costs["provider_reported_usd"]
    if costs["accounted_usd"] is not None:
        meta["accounted_usd"] = costs["accounted_usd"]
    if prediction.get("error"):
        meta["error"] = str(prediction["error"])[:300]
        meta["error_type"] = prediction.get("error_type")
    return {key: value for key, value in meta.items() if value is not None}


def _md_ref(directory: Path, ident: str) -> dict[str, Any] | None:
    path = directory / f"{ident}.md"
    return file_ref(path) if path.is_file() else None


def _items(artifacts: Path, manifest: dict[str, Any], targets: dict[str, Any]) -> list[Item]:
    target_map = {page["id"]: page for page in targets["pages"]}
    items = []
    for record in manifest["pages"]:
        target = target_map[record["id"]]
        items.append(
            Item(
                key=record["id"],
                input={
                    "page_id": record["id"],
                    "family": record.get("family"),
                    "pilot": record.get("pilot"),
                    "label_status": record.get("label_status"),
                    "pdf": pdf_ref(artifacts, record),
                },
                expected={
                    "structural_scored": target.get("structural_scored", True),
                    "table_count": len(target.get("tables", [])),
                    "tables": [compact_table(table) for table in target.get("tables", [])],
                },
                metadata={"family": record.get("family"), "pilot": bool(record.get("pilot")), "campaign": "P001"},
            )
        )
    return items


def _oracle_rank(score: dict[str, Any]) -> tuple[int, int, int, int]:
    if not score["structural_scored"]:
        return (0, 0, 0, 0)
    return (
        int(score["exact_page"]),
        score["complete_tables"],
        score["correct_cell_slots"],
        -score["false_positive_tables"],
    )


def _run(directory: Path, manifest: dict[str, Any], targets: dict[str, Any]) -> Run:
    report = read_json(directory / "report.json")
    config = report.get("config", {})
    pilot = bool(config.get("pilot"))
    selected = [record for record in manifest["pages"] if not pilot or record.get("pilot")]
    selected_ids = {record["id"] for record in selected}
    private = [target for target in targets["pages"] if target["id"] in selected_ids]
    predictions = report.get("results", [])
    by_id = {prediction["id"]: prediction for prediction in predictions}
    rows: list[Row] = []
    for target in private:
        prediction = by_id.get(target["id"], {"id": target["id"], "status": "missing"})
        status = prediction.get("status", "missing")
        page = score_page(target, prediction.get("tables", []), status=status)
        scores: dict[str, Any] = {"operational_output": status == "ok"}
        if page["structural_scored"]:
            scores.update({key: page[key] for key in _SCORE_KEYS})
            if page["cell_slots"]:
                scores["cell_slot_recall"] = page["correct_cell_slots"] / page["cell_slots"]
        else:
            scores["error"] = page["error"]
        if status == "ok" and prediction.get("source") is not None:
            assigned = list(prediction.get("unresolved_ids", [])) + [
                ident
                for table in prediction.get("tables", [])
                for cell in table.get("cells", [])
                for ident in cell.get("source_ids", [])
            ]
            scores["source_conserved"] = conservation([w["id"] for w in prediction["source"]["words"]], assigned)[
                "exact_conservation"
            ]
        output: dict[str, Any] = {
            "status": status,
            "tables": [compact_table(table) for table in prediction.get("tables", [])],
            "unresolved_words": len(prediction.get("unresolved_ids", []) or []),
        }
        markdown = _md_ref(directory, target["id"]) if status == "ok" else None
        if markdown:
            output["markdown"] = markdown
        meta = row_metadata(prediction)
        meta["structural_scored"] = page["structural_scored"]
        meta["positive_page"] = bool(target.get("tables")) if page["structural_scored"] else None
        wall = number(prediction.get("wall_seconds"))
        rows.append(
            Row(
                item_key=target["id"],
                output=output,
                scores=scores,
                metadata=meta,
                wall_ms=wall * 1000 if wall is not None else None,
            )
        )
    totals = score_dataset(private, predictions)["totals"]
    positives = [t for t in private if t.get("structural_scored", True) and t.get("tables")]
    negatives = [t for t in private if t.get("structural_scored", True) and not t.get("tables")]
    positive = score_dataset(positives, [by_id[t["id"]] for t in positives if t["id"] in by_id])["totals"]
    negative = score_dataset(negatives, [by_id[t["id"]] for t in negatives if t["id"] in by_id])["totals"]
    oracle_exact = 0
    for target in positives:
        candidates = by_id.get(target["id"], {}).get("candidates", [])
        best = max(candidates, key=lambda c: _oracle_rank(score_page(target, c["tables"])), default=None)
        oracle_exact += int(best is not None and score_page(target, best["tables"])["exact_page"])
    metrics = report.get("metrics", {})
    bases = report.get("cost_bases", {}) or {}
    effective = None if bases.get("reserved", 0) else number(report.get("effective_usd"))
    operational = sum(1 for p in predictions if p.get("status") == "ok")
    run_scores: dict[str, Any] = {key: totals[key] for key in ("pages", "scored_pages", *_SCORE_KEYS)}
    run_scores.update(
        {
            "operational_pages": operational,
            "all_errors": len(private) - operational,
            "positive_scored_pages": positive["scored_pages"],
            "positive_exact_pages": positive["exact_page"],
            "negative_scored_pages": negative["scored_pages"],
            "negative_false_positive_pages": negative["false_positive_page"],
            "oracle_positive_exact_pages": oracle_exact,
            "wall_seconds": number(metrics.get("wall_seconds")),
            "cpu_seconds": number(metrics.get("cpu_seconds")),
            "peak_sampled_rss_bytes": number(metrics.get("peak_sampled_rss_bytes")),
            "provider_reported_usd": number(report.get("provider_reported_usd")),
            "missing_provider_charge_count": number(report.get("missing_provider_charge_count")),
            "accounted_usd": number(report.get("accounted_usd")),
            "effective_usd": effective,
            "calls": number(report.get("calls")),
            "ledger_attempts": number(report.get("ledger_attempts")),
            "provider_reported_calls": number(bases.get("provider-reported USD", 0)),
            "catalog_estimate_calls": number(bases.get("catalog estimate", 0)),
            "reserved_calls": number(bases.get("reserved", 0)),
        }
    )
    wall = number(metrics.get("wall_seconds"))
    if wall:
        run_scores["pages_per_minute"] = operational / wall * 60
        run_scores["exact_positive_pages_per_minute"] = positive["exact_page"] / wall * 60
    if effective:
        run_scores["pages_per_dollar"] = operational / effective
        run_scores["exact_positive_pages_per_dollar"] = positive["exact_page"] / effective
    native = config.get("policy") in {"native", "native_text"}
    description = (
        f"P001 {'pilot' if pilot else 'full'} run {directory.name}: policy={config.get('policy')}, "
        f"model={'CPU only' if native else config.get('model')}, review={config.get('gate_review_model')}, "
        f"image_edge={config.get('image_edge')}."
    )
    return Run(
        name=directory.name,
        description=description,
        rows=rows,
        metadata={
            "campaign": "P001",
            "cohort": "pilot" if pilot else "full",
            "intended_pages": len(private),
            "policy": config.get("policy"),
            "model": "CPU only" if native else config.get("model"),
            "gate_review_model": config.get("gate_review_model"),
            "gate_premise": config.get("gate_premise"),
            "image_edge": config.get("image_edge"),
            "context_rows": config.get("context_rows"),
            "normalize_rotation": config.get("normalize_rotation"),
            "ocr_empty": config.get("ocr_empty"),
            "column_consensus": config.get("column_consensus"),
            "compact_packet": config.get("compact_packet"),
            "readable_packet": config.get("readable_packet"),
            "cost_bases": str(dict(bases)),
            "effective_usd_note": (
                "effective_usd omitted: reservation or missing charge"
                if effective is None
                else "effective_usd = provider-reported charges plus labeled catalog estimates for zero/missing charges"
            ),
            "cost_scope": report.get("cost_scope"),
            "resource_measurement": metrics.get("measurement"),
            "scorer": "bench.pipeline_scoring.score_page (recomputed by adapter)",
            "source": str(directory.relative_to(ROOT)) if directory.is_relative_to(ROOT) else str(directory),
        },
        scores={key: value for key, value in run_scores.items() if value is not None},
        started=directory.joinpath("report.json").stat().st_mtime,
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield the single P001 experiment, or nothing when its corpus is absent."""
    root = guard(artifacts / CAMPAIGN)
    corpus = root / "corpus"
    if not (corpus / "manifest.json").is_file() or not (corpus / "private-targets.json").is_file():
        return
    manifest = read_json(corpus / "manifest.json")
    targets = read_json(corpus / "private-targets.json")
    if manifest.get("split") != "DEV":
        return
    reports = sorted(
        (path.parent for path in root.glob("*/report.json")),
        key=lambda path: (path.joinpath("report.json").stat().st_mtime_ns, path.name),
    )
    runs = [_run(directory, manifest, targets) for directory in reports]
    yield Experiment(
        dataset=DATASET,
        description=(
            "P001 complete PDF pipeline DEV corpus: 181 pages (32 fixed pilot pages) with repository-authored "
            "silver table/non-table targets. Runs are native and model-assisted pipeline configurations; "
            "scores are complete-matrix table exactness from bench.pipeline_scoring."
        ),
        items=_items(artifacts, manifest, targets),
        runs=runs,
        source=str(root.relative_to(ROOT)) if root.is_relative_to(ROOT) else str(root),
        labels={"split": "DEV", "heldout": False, "campaign": "P001", "dataset_sha256": manifest.get("dataset_sha256")},
    )
