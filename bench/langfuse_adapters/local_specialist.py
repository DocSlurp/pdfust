"""Local SLANet-plus specialist and saved-prediction cell-matching study adapters (P004).

- ``matching``: upstream rapid-table TableMatch versus the bounded NumPy matcher on saved
  specialist predictions. Items are case/route pairs; equivalence to upstream is the gold.
- ``specialist`` and ``specialist-invalid-alpha-v1``: the eight-case CPU pilot, one run per
  route. The invalid run discarded alpha (black rasters) and is exported only as a labeled
  harness failure, never as model quality.
- ``specialist-resolution-v1``: the 28-page DEV DPI/crop sweep (12 runs) and the frozen
  source-only SLANet/geometry agreement simulation (12 config/rule/gate runs).
"""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, read_json
from bench.langfuse_adapters.local_studies import Scores, mtime, ratio, ref

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "local_specialist"

REPORT_ROUTES = 16  # Equivalent routes reported in cell-matching.md.
SPECIALIST_REPORT = {
    # route: (cells correct, cells total, exact, positives, prose FP, negatives, records correct, records total)
    "specialist": {"full": (0, 35, 0, 4, 2, 2, 7, 35), "cropped": (35, 35, 4, 4, 1, 2, 17, 35)},
}


# --- matching --------------------------------------------------------------------------------


def matching(artifacts: Path) -> Iterable[Experiment]:
    """Saved-prediction cell matching: upstream reference versus optimized matcher."""
    directory = artifacts / "matching"
    path = directory / "results.json"
    if not path.exists():
        return
    report = read_json(path)
    items, reference_rows, optimized_rows = [], [], []
    for result in report["results"]:
        key = f"{result['name']}/{result['route']}"
        empty = not result["word_count"] or not result["cell_count"]
        items.append(
            Item(
                key,
                {
                    "saved_inputs": ref(directory / result["name"] / f"{result['route']}-inputs.json"),
                    "saved_results_sha256": result["saved_results_sha256"],
                    "pdf_sha256": result["input_sha256"],
                    "words": result["word_count"],
                    "cells": result["cell_count"],
                    "regions": result["regions"],
                },
                {"equivalence": "upstream TableMatch associations, region HTML, saved HTML and complete HTML"},
                {"case": result["name"], "route": result["route"]},
            )
        )
        status = "error" if result["error"] else ("empty-route" if empty else "ok")
        meta = {"status": status, "route": result["route"]}
        reference_scores: Scores = {"error": bool(result["error"])}
        optimized_scores: Scores = {
            "choices_equal": result["choices_equal"],
            "html_equal": result["html_equal"],
            "saved_html_equal": result["saved_html_equal"],
            "complete_html_equal": result["complete_html_equal"],
            "peak_traced_kib": result["peak_traced_bytes"] / 1024,
            "unassigned_ids": sum(len(o.get("unassigned_ids", [])) for o in result["outputs"]),
            "error": bool(result["error"]),
        }
        if not empty:
            reference_scores["median_ms"] = result["reference_median_ms"]
            optimized_scores["median_ms"] = result["optimized_median_ms"]
            optimized_scores["speedup"] = ratio(result["reference_median_ms"], result["optimized_median_ms"])
        reference_rows.append(
            Row(
                key,
                {"samples_ms": result["reference_ms"]},
                reference_scores,
                meta,
                wall_ms=None if empty else result["reference_median_ms"],
            )
        )
        optimized_rows.append(
            Row(
                key,
                {
                    "samples_ms": result["optimized_ms"],
                    "matches": [o.get("matches") for o in result["outputs"]],
                    "unassigned_ids": [o.get("unassigned_ids") for o in result["outputs"]],
                },
                optimized_scores,
                {**meta, "error_text": result["error"]} if result["error"] else meta,
                wall_ms=None if empty else result["optimized_median_ms"],
            )
        )
    equal = sum(
        all(bool(row.scores[k]) for k in ("choices_equal", "html_equal", "saved_html_equal", "complete_html_equal"))
        for row in optimized_rows
    )
    common = {
        "code_sha256": report["code_sha256"],
        "repeats": report["repeats"],
        "chunk_words": report["chunk_words"],
        "rapid_table_version": report["provenance"]["rapid_table_version"],
        "numpy_version": report["provenance"]["numpy_version"],
        "report": "bench/results/cell-matching.md",
        "experiment_id": "P004",
    }
    nonempty = [r for r in report["results"] if r["word_count"] and r["cell_count"]]
    yield Experiment(
        "exp/matching/cell-matching",
        "Saved-prediction CPU cell matching (bench/cell_matching.py) on the eight-case SLANet pilot: upstream "
        "rapid-table TableMatch versus a bounded NumPy matcher. No inference; equivalence, not table quality.",
        items,
        [
            Run(
                "upstream-tablematch",
                "Upstream rapid-table 3.0.2 TableMatch loaded in isolation; filtering, matching and HTML assembly.",
                reference_rows,
                {**common, "report_crosscheck": "match: 15 nonempty routes, medians as in cell-matching.md"},
                {"nonempty_routes": len(nonempty)},
                mtime(path),
            ),
            Run(
                "optimized-numpy-matcher",
                "Bounded NumPy matcher with precomputed AABBs and chunked IoU/L1; same tie rules and HTML assembly.",
                optimized_rows,
                {
                    **common,
                    "report_crosscheck": f"{'match' if equal == len(optimized_rows) == REPORT_ROUTES else 'MISMATCH'}: "
                    f"{equal}/{len(optimized_rows)} equivalent routes (report 16/16)",
                },
                {
                    "equivalent_routes": equal,
                    "routes": len(optimized_rows),
                    "nonempty_routes": len(nonempty),
                    "median_speedup": statistics.median(
                        r["reference_median_ms"] / r["optimized_median_ms"] for r in nonempty
                    )
                    if nonempty
                    else None,
                },
                mtime(path),
            ),
        ],
        "bench/results/pdf-master-artifacts/matching",
    )


# --- specialist pilot ------------------------------------------------------------------------


def _specialist_row(result: dict[str, Any], route_name: str) -> Row:
    route = result["routes"][route_name]
    score, source, records = route["score"], route["source"], route["records"]
    gold = result["gold"]
    scores: Scores = {
        "regions": route["region_count"],
        "tables": score.get("tables"),
        "source_matched_tokens": source["matched_tokens"],
        "source_tokens": source["source_tokens"],
        "missing_source_tokens": source["missing_tokens"],
        "extra_source_tokens": source["extra_tokens"],
        "render_ms": result["render_ms"],
        "native_ms": result["native_text_ms"],
        "inference_ms": route["inference_ms"],
        "matching_ms": route["matching_ms"],
        "total_ms": route["total_ms"],
        "error": bool(route["error"]),
    }
    if gold is not None:
        for key in ("exact", "correct_cells", "total_cells", "relationship_matches", "relationship_expected"):
            if key in score:
                scores[key] = score[key]
        if gold == []:
            scores["prose_false_positive"] = bool(route["tables"])
    if records["total"]:
        scores["record_checks_correct"] = records["correct"]
        scores["record_checks_total"] = records["total"]
    kind = "corpus-partial" if gold is None else ("table" if gold else "prose-negative")
    return Row(
        result["name"],
        {
            "tables": route["tables"],
            "complete_sha256": route["complete_sha256"],
            "regions": [o.get("region") for o in route["outputs"]],
        },
        scores,
        {"status": "error" if route["error"] else "ok", "kind": kind, "error_text": route["error"]},
        wall_ms=route["total_ms"],
    )


def _specialist_aggregate(rows: list[Row], gold: dict[str, Any]) -> Scores:
    positive = [row for row in rows if gold[row.item_key]]
    negative = [row for row in rows if gold[row.item_key] == []]
    corpus = [row for row in rows if gold[row.item_key] is None]
    return {
        "correct_cells": sum(int(row.scores.get("correct_cells") or 0) for row in positive),
        "total_cells": sum(int(row.scores.get("total_cells") or 0) for row in positive),
        "exact_matrices": sum(bool(row.scores.get("exact")) for row in positive),
        "positive_pages": len(positive),
        "prose_false_positives": sum(bool(row.scores.get("prose_false_positive")) for row in negative),
        "negative_pages": len(negative),
        "corpus_records_correct": sum(int(row.scores.get("record_checks_correct") or 0) for row in corpus),
        "corpus_records_total": sum(int(row.scores.get("record_checks_total") or 0) for row in corpus),
        "errors": sum(bool(row.scores["error"]) for row in rows),
    }


def _specialist(artifacts: Path, folder: str) -> Iterable[Experiment]:
    directory = artifacts / folder
    path = directory / "manifest.json"
    if not path.exists():
        return
    manifest = read_json(path)
    invalid = (directory / "INVALID-RUN.txt").exists()
    reason = (directory / "INVALID-RUN.txt").read_text(encoding="utf-8").strip() if invalid else ""
    meta = manifest["metadata"]
    items = [
        Item(
            result["name"],
            {
                "pdf": ref(directory / result["name"] / "input.pdf", result["input_sha256"]),
                "dpi": result["dpi"],
                "words": result["word_count"],
                "notes": result["notes"],
                "source": result["source"],
            },
            {
                "tables": result["gold"],
                "semantics": "corpus page: partial record spot checks only"
                if result["gold"] is None
                else ("no-table prose control" if result["gold"] == [] else "declared table matrix"),
            },
        )
        for result in manifest["results"]
    ]
    gold = {result["name"]: result["gold"] for result in manifest["results"]}
    runs = []
    for route_name in ("full", "cropped"):
        rows = [_specialist_row(result, route_name) for result in manifest["results"]]
        if invalid:
            for row in rows:
                row.metadata["status"] = "invalid-harness"
        scores = _specialist_aggregate(rows, gold)
        expected = SPECIALIST_REPORT.get(folder, {}).get(route_name)
        observed = tuple(
            scores[k]
            for k in (
                "correct_cells",
                "total_cells",
                "exact_matrices",
                "positive_pages",
                "prose_false_positives",
                "negative_pages",
                "corpus_records_correct",
                "corpus_records_total",
            )
        )
        if invalid:
            crosscheck = "INVALID harness run; per-row table matches invalid-report.md; not model quality"
        elif expected is None:
            crosscheck = "no committed figures"
        else:
            crosscheck = (
                "match specialist-cpu.md observed quality"
                if observed == expected
                else f"MISMATCH {observed} != {expected}"
            )
        runs.append(
            Run(
                f"slanet-plus-cpu/{route_name}" + ("-INVALID-alpha" if invalid else ""),
                ("INVALID HARNESS RUN (alpha discarded, black rasters). " if invalid else "")
                + f"SLANet-plus ONNX on CPU, {route_name} route at 120 DPI; one model call per admitted region.",
                rows,
                {
                    "route": route_name,
                    "invalid_harness": invalid,
                    "invalid_reason": reason or None,
                    "model_sha256": meta.get("model_sha256"),
                    "providers": ",".join(meta.get("providers", [])),
                    "intra_threads": meta.get("actual_intra_threads"),
                    "inter_threads": meta.get("actual_inter_threads"),
                    "initialization_ms": meta.get("initialization_ms"),
                    "pilot_wall_seconds": meta.get("wall_seconds"),
                    "extension_sha256": meta.get("extension_sha256"),
                    "report": "bench/results/pdf-master-artifacts/specialist-invalid-alpha-v1/invalid-report.md"
                    if invalid
                    else "bench/results/specialist-cpu.md",
                    "report_crosscheck": crosscheck,
                    "experiment_id": "P004",
                },
                scores,
                mtime(path),
            )
        )
    yield Experiment(
        f"exp/{folder}/slanet-plus-cpu-pilot",
        ("INVALID harness run retained for provenance only: transparent alpha was discarded. " if invalid else "")
        + "SLANet-plus CPU pilot (bench/specialist_cpu.py): four declared table matrices, two prose controls and "
        "two corpus pages with partial record checks; full-page versus native-proposal cropped routes.",
        items,
        runs,
        f"bench/results/pdf-master-artifacts/{folder}",
        {"split": "DEV", "heldout": False, "invalid_harness": invalid},
    )


def specialist(artifacts: Path) -> Iterable[Experiment]:
    """Yield the valid and invalid-alpha SLANet-plus pilots."""
    yield from _specialist(artifacts, "specialist")
    yield from _specialist(artifacts, "specialist-invalid-alpha-v1")


# --- specialist resolution sweep -------------------------------------------------------------

RESOLUTION_DPIS = (72, 120, 180)
RESOLUTION_ROUTES = ("page", "crop", "crop-pad4", "crop-pad12")
RESOLUTION_REPORT = {
    # (dpi, route): (borderless exact, prose false table, owned values, owned words) from specialist-resolution.md.
    (72, "page"): (0, 8, 0, 0),
    (72, "crop-pad4"): (3, 8, 76, 94),
    (72, "crop-pad12"): (7, 8, 149, 185),
    (120, "crop-pad12"): (5, 8, 126, 154),
    (180, "crop"): (1, 8, 16, 16),
    (180, "crop-pad12"): (5, 8, 118, 144),
}
SCORE_KEYS = ("exact_page", "false_positive_page", "exact_cells", "exact_spans", "owned_values", "owned_words")


def _resolution_items(directory: Path, artifacts: Path) -> tuple[list[Item], dict[str, dict[str, Any]]]:
    source = read_json(directory / "source-frozen.json")
    corpus = artifacts / "silver-realism-v2" / directory.name
    targets_path = corpus / "private-targets.json"
    targets = {t["id"]: t for t in read_json(targets_path)} if targets_path.exists() else {}
    items = []
    for page in source["pages"]:
        target = targets.get(page["id"], {})
        expected = (
            {
                "kind": target.get("kind"),
                "truth_status": target.get("truth_status"),
                "tables": [
                    {"values": t["values"], "spans": t.get("spans"), "rows": t["row_count"], "cols": t["col_count"]}
                    for t in target.get("tables", [])
                ],
            }
            if target
            else None
        )
        items.append(
            Item(
                page["id"],
                {
                    "pdf": ref(corpus / "pdfs" / f"{page['id']}.pdf", page["pdf_sha256"]),
                    "words": len(page["words"]),
                    "source_crops": page["routes"],
                },
                expected,
                {"kind": target.get("kind"), "corpus": f"silver-realism-v2/{directory.name}"},
            )
        )
    return items, targets


def _resolution_row(output: dict[str, Any] | None, score: dict[str, Any], identifier: str) -> Row:
    scores: Scores = {"error": bool(score["error"]), "span_available": score["span_available"]}
    if score["source_conservation"] is not None:
        scores["source_ids_conserved"] = score["source_conservation"]
    if score["scored"] and score["scores"]:
        scores.update({key: score["scores"][key] for key in SCORE_KEYS if key in score["scores"]})
    result: dict[str, Any] = {}
    if output:
        observed = output.get("observed", {})
        scores.update(
            {
                "regions": observed.get("region_count"),
                "inference_ms": observed.get("inference_ms"),
                "matching_ms": observed.get("matching_ms"),
                "wall_seconds": output.get("wall_seconds"),
                "cpu_seconds": output.get("cpu_seconds"),
                "model_cpu_seconds": output.get("model_cpu_seconds"),
                "matching_cpu_seconds": output.get("matching_cpu_seconds"),
                "peak_rss_mib": output["peak_rss_bytes"] / 2**20 if output.get("peak_rss_bytes") else None,
            }
        )
        result = {
            "matrices": [{"values": m["values"], "spans": m.get("spans")} for m in output.get("matrices", [])],
            "complete_sha256": observed.get("complete_sha256"),
            "unresolved_ids": len(output.get("ownership", {}).get("unresolved_ids", [])),
        }
    status = "error" if score["error"] else ("ambiguous-unscored" if not score["scored"] else "ok")
    return Row(
        identifier,
        result,
        scores,
        {"status": status, "kind": score["kind"]},
        wall_ms=output["wall_seconds"] * 1000 if output and output.get("wall_seconds") else None,
    )


def _resolution_aggregate(rows: list[Row], targets: dict[str, dict[str, Any]]) -> Scores:
    positive = [row for row in rows if row.metadata["kind"] == "borderless"]
    prose = [row for row in rows if row.metadata["kind"] == "prose"]
    value_total = sum(
        bool(v)
        for t in targets.values()
        if t["kind"] == "borderless"
        for table in t["tables"]
        for row in table["values"]
        for v in row
    )
    word_total = sum(
        len(v.split())
        for t in targets.values()
        if t["kind"] == "borderless"
        for table in t["tables"]
        for row in table["values"]
        for v in row
        if v
    )
    scores: Scores = {
        "borderless_exact": sum(bool(row.scores.get("exact_page")) for row in positive),
        "borderless_pages": len(positive),
        "prose_false_table": sum(bool(row.scores.get("false_positive_page")) for row in prose),
        "prose_pages": len(prose),
        "ambiguous_unscored": sum(row.metadata["kind"] == "ambiguous" for row in rows),
        "errors": sum(bool(row.scores["error"]) for row in rows),
        "exact_cells": sum(bool(row.scores.get("exact_cells")) for row in positive),
        "exact_spans": sum(bool(row.scores.get("exact_spans")) for row in positive),
        "owned_values": sum(int(row.scores.get("owned_values") or 0) for row in positive),
        "owned_words": sum(int(row.scores.get("owned_words") or 0) for row in positive),
        "source_ids_conserved": sum(bool(row.scores.get("source_ids_conserved")) for row in rows),
        "model_wall_seconds": sum(float(row.scores.get("inference_ms") or 0) for row in rows) / 1000,
        "model_cpu_seconds": sum(float(row.scores.get("model_cpu_seconds") or 0) for row in rows),
        "matching_wall_seconds": sum(float(row.scores.get("matching_ms") or 0) for row in rows) / 1000,
        "matching_cpu_seconds": sum(float(row.scores.get("matching_cpu_seconds") or 0) for row in rows),
        "route_wall_seconds": sum(float(row.scores.get("wall_seconds") or 0) for row in rows),
        "route_cpu_seconds": sum(float(row.scores.get("cpu_seconds") or 0) for row in rows),
    }
    if targets:
        scores["owned_values_total"] = value_total
        scores["owned_words_total"] = word_total
    return scores


def _resolution_sweep(directory: Path, items: list[Item], targets: dict[str, dict[str, Any]]) -> Experiment:
    frozen = directory / "outputs-frozen.json"
    outputs_path = frozen if frozen.exists() else directory / "progress.json"
    outputs = {(r["id"], r["dpi"], r["route"]): r for r in read_json(outputs_path)["rows"]}
    private = read_json(directory / "private-scores.json")
    model = read_json(directory / "model.json")
    execution_path = directory / "execution.json"
    execution = read_json(execution_path) if execution_path.exists() else {}
    runs = []
    for dpi in RESOLUTION_DPIS:
        for route in RESOLUTION_ROUTES:
            selected = [s for s in private if s["dpi"] == dpi and s["route"] == route]
            rows = [_resolution_row(outputs.get((s["id"], dpi, route)), s, s["id"]) for s in selected]
            scores = _resolution_aggregate(rows, targets)
            expected = RESOLUTION_REPORT.get((dpi, route))
            observed = tuple(
                scores[k] for k in ("borderless_exact", "prose_false_table", "owned_values", "owned_words")
            )
            crosscheck = (
                "match specialist-resolution.md (all tables)"
                if expected is None or observed == expected
                else f"MISMATCH {observed} != {expected}"
            )
            runs.append(
                Run(
                    f"slanet-plus-cpu/dpi{dpi}/{route}",
                    f"SLANet-plus CPU at {dpi} DPI, {route} route (source-only native crops; fixed 488 px tensor).",
                    rows,
                    {
                        "dpi": dpi,
                        "route": route,
                        "model_sha256": model.get("model_sha256"),
                        "intra_threads": model.get("actual_intra_threads"),
                        "inter_threads": model.get("actual_inter_threads"),
                        "fixed_preprocess_max_side": model.get("fixed_preprocess_max_side"),
                        "worker_peak_rss_mib": execution["sampled_worker_peak_rss_bytes"] / 2**20
                        if execution.get("sampled_worker_peak_rss_bytes")
                        else None,
                        "outputs": outputs_path.name,
                        "report": "bench/results/specialist-resolution.md",
                        "report_crosscheck": crosscheck,
                    },
                    scores,
                    mtime(outputs_path),
                )
            )
    return Experiment(
        f"exp/specialist-resolution-v1/{directory.name}/sweep",
        "CPU SLANet-plus DPI (72/120/180) x source-crop (page, crop, +4 pt, +12 pt) sweep on 28 reviewed "
        "silver-realism-v2 DEV pages: 16 borderless, 8 prose, 4 ambiguous (unscored). Scores are the post-freeze "
        "private-scores.json; RSS is per-process VmHWM.",
        items,
        runs,
        f"bench/results/pdf-master-artifacts/specialist-resolution-v1/{directory.name}",
    )


def _agreement(agreement: Path, items: list[Item]) -> Experiment | None:
    evaluation_path = agreement / "private-evaluation.json"
    if not evaluation_path.exists():
        return None
    evaluation = read_json(evaluation_path)
    frozen = read_json(agreement / "agreement-frozen.json")
    accepted = {(r["id"], r["config"], r["rule"]): r for r in frozen["rows"]}
    kinds = {item.key: (item.metadata.get("kind") or "") for item in items}
    runs = []
    for cohort in evaluation["cohorts"]:
        scored = {row["id"]: row for row in cohort["rows"]}
        rows = []
        for item in items:
            row = scored.get(item.key)
            if row is not None:
                scores: Scores = {"accepted": row["accepted"], **{k: row["scores"][k] for k in SCORE_KEYS}}
                rows.append(
                    Row(item.key, {"accepted": row["accepted"]}, scores, {"status": "ok", "kind": kinds[item.key]})
                )
                continue
            decision = accepted.get((item.key, cohort["config"], cohort["rule"]))
            output: dict[str, Any] = {}
            if decision is not None and not cohort["gate_simulated"]:
                output = {"accepted": decision["accepted"], "agreeing_candidates": decision["agreeing_candidates"]}
            rows.append(Row(item.key, output, {}, {"status": "ambiguous-unscored", "kind": kinds[item.key]}))
        gate = "gated" if cohort["gate_simulated"] else "ungated"
        runs.append(
            Run(
                f"{cohort['config']}/{cohort['rule']}/{gate}",
                f"Frozen source-only SLANet/T005 agreement, {cohort['rule']} rule, "
                + ("with offline retained PPLX G001 gate simulation." if cohort["gate_simulated"] else "no gate."),
                rows,
                {
                    "config": cohort["config"],
                    "rule": cohort["rule"],
                    "gate_simulated": cohort["gate_simulated"],
                    "gate_measured_pages": cohort.get("gate_measured_pages"),
                    "frozen_sha256": evaluation.get("frozen_sha256"),
                    "report": "bench/results/specialist-agreement.md",
                    "report_crosscheck": "match: 7 correct / 0 wrong / 0 prose FP / 9 deferred in every cohort; "
                    "ambiguous accepted 2/4 strict, 4/4 text_matrix, 1/4 gated",
                },
                dict(cohort["counts"]),
                mtime(evaluation_path),
            )
        )
    return Experiment(
        f"exp/specialist-resolution-v1/{agreement.name}",
        "Offline source-only SLANet/geometry agreement: accept only when a unique T005 geometry candidate matches "
        "SLANet (strict source-ID partition, or weaker text matrix); nonagreement defers. Ambiguous pages are "
        "unscored; gated per-page acceptance on them is not retained.",
        items,
        runs,
        f"bench/results/pdf-master-artifacts/specialist-resolution-v1/{agreement.name}",
    )


def specialist_resolution(artifacts: Path) -> Iterable[Experiment]:
    """Every retained specialist-resolution corpus directory."""
    root = artifacts / "specialist-resolution-v1"
    if not root.is_dir():
        return
    corpus_items: list[Item] = []
    for directory in sorted(p for p in root.iterdir() if (p / "source-frozen.json").exists()):
        items, targets = _resolution_items(directory, artifacts)
        corpus_items = corpus_items or items
        if (directory / "private-scores.json").exists():
            yield _resolution_sweep(directory, items, targets)
    # The agreement study re-reads the same 28 reviewed DEV pages; reuse the first corpus's items.
    agreement = _agreement(root / "agreement-v1", corpus_items) if corpus_items else None
    if agreement is not None:
        yield agreement


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield matching, specialist pilot and specialist-resolution experiments."""
    yield from matching(artifacts)
    yield from specialist(artifacts)
    yield from specialist_resolution(artifacts)
