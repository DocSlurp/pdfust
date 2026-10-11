"""Local CPU/GPU study adapters: encodings, geometry, headers, semantic, color regions and more.

Each study keeps its own retained metrics. Items are the evaluated cases; runs are the
retained configurations, phases or rounds; rows carry the per-case outcome. Superseded
rounds stay as separately named runs so their history is visible next to the final run.
Aggregates are recomputed from rows with the producing script's own rules and stored on
the run; ``metadata["report_crosscheck"]`` records whether they match the committed report.
"""

from __future__ import annotations

import hashlib
import statistics
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import ROOT, Experiment, Item, Row, Run, digest, file_ref, guard, read_json

if TYPE_CHECKING:
    from collections.abc import Iterable

NAME = "local_studies"

Scores = dict[str, float | bool | int | None]


def rel(path: Path) -> str:
    """Return a repository-relative path when possible."""
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def ref(path: Path, sha256: str | None = None) -> dict[str, Any]:
    """Return a path/hash reference to a retained file, tolerating a missing copy."""
    if guard(path).is_file():
        return file_ref(path)
    return {"path": rel(path), "sha256": sha256, "missing": True}


def mtime(path: Path) -> float | None:
    """Use the retained artifact modification time as the run start."""
    return path.stat().st_mtime if path.exists() else None


def ratio(numerator: float, denominator: float) -> float | None:
    """Return a ratio only when it is defined."""
    return numerator / denominator if denominator else None


# --- encodings -------------------------------------------------------------------------------

ENCODING_REFERENCE = [
    ["Item", "Qty", "Amount"],
    ["Alpha", "2", "12.00"],
    ["Beta", "3", "9.00"],
    ["Total", "5", "21.00"],
]
ENCODING_SEMANTICS = {
    "equivalent": "Same visible grid through a different PDF representation; exact source grid expected.",
    "visibility": "Visibility control: text-layer content is not proof of visible content; no exact-grid gold.",
    "ocr-routing": "Scanned table; text extraction cannot recover it, OCR routing is the studied signal.",
    "ocr-negative": "Raster without a table; routing signals here are work, not table detections.",
}


def encodings(artifacts: Path) -> Iterable[Experiment]:
    """Metamorphic encoding/visibility/OCR-routing audit: one pylopdf run over 21 cases."""
    directory = artifacts / "encodings"
    path = directory / "results.json"
    if not path.exists():
        return
    report = read_json(path)
    items, rows = [], []
    for result in report["results"]:
        cohort = result["cohort"]
        items.append(
            Item(
                result["name"],
                {"pdf": ref(directory / f"{result['name']}.pdf", result["input_sha256"]), "note": result["note"]},
                {"grid": ENCODING_REFERENCE} if cohort == "equivalent" else {"semantics": ENCODING_SEMANTICS[cohort]},
                {"cohort": cohort},
            )
        )
        rows.append(
            Row(
                result["name"],
                {"matrices": result["matrices"], "render_sha256": result["render_sha256"]},
                {
                    "exact_grid": result["exact_grid"],
                    "word_count": result["word_count"],
                    "table_count": result["table_count"],
                    "open_extract_ms": result["open_extract_ms"],
                    "image_probe_ms": result["image_probe_ms"],
                    "page_empty_ocr_gate": result["page_empty_ocr_gate"],
                    "unresolved_raster_evidence": result["unresolved_raster_evidence"],
                    "large_raster_gate": result["large_raster_gate"],
                    "image_coverage_upper_bound": result["image_coverage_upper_bound"],
                },
                {"cohort": cohort, "status": "ok", "samples_ms": result["samples_ms"]},
                wall_ms=result["open_extract_ms"],
            )
        )
    by_cohort: dict[str, list[dict[str, Any]]] = {}
    for result in report["results"]:
        by_cohort.setdefault(result["cohort"], []).append(result)
    scores: Scores = {}
    for cohort, results in by_cohort.items():
        scores[f"{cohort}.exact_grid"] = sum(bool(r["exact_grid"]) for r in results)
        scores[f"{cohort}.cases"] = len(results)
        scores[f"{cohort}.page_empty_ocr_gate"] = sum(bool(r["page_empty_ocr_gate"]) for r in results)
        scores[f"{cohort}.unresolved_raster_evidence"] = sum(bool(r["unresolved_raster_evidence"]) for r in results)
        scores[f"{cohort}.large_raster_gate"] = sum(bool(r["large_raster_gate"]) for r in results)
    scores["median_open_extract_ms"] = statistics.median(r["open_extract_ms"] for r in report["results"])
    yield Experiment(
        "exp/encodings/routing-audit",
        "CPU metamorphic audit: one 4x3 ruled grid through 13 equivalent encodings, four visibility "
        "controls, two scans and two raster negatives (bench/encoding_audit.py). Metamorphic coverage, "
        "not independent document-family accuracy.",
        items,
        [
            Run(
                "pylopdf-get_layout",
                "pylopdf 0.13 get_layout() tables plus get_images() routing signals; five CPU repetitions, "
                "median open+extract ms.",
                rows,
                {
                    "code_sha256": report["code_sha256"],
                    "repetitions": 5,
                    "report": "bench/results/encoding-audit.md",
                    "report_crosscheck": "match: equivalent 13/13 exact, duplicate-paint 24 words, all 21 rows agree",
                },
                scores,
                mtime(path),
            )
        ],
        "bench/results/pdf-master-artifacts/encodings",
    )


# --- semantic --------------------------------------------------------------------------------

SEMANTIC_POSITIVE = [["Name", "Value"], ["Alpha", "42"]]
SEMANTIC_EXPECTATIONS = {
    "valid": 1,
    "rolemap": 1,
    "missing-mcid": 0,
    "bad-header": 0,
    "stale-parent": 0,
    "duplicate-mcid": 0,
    "cycle": 0,
    "untagged": 0,
    "nonvisible": 0,
    "embedded-consistent": 0,
    "embedded-stale": 0,
}


def semantic(artifacts: Path) -> Iterable[Experiment]:
    """Tagged-table fast-path probe over 15 corpus PDFs and 11 authored controls."""
    directory = artifacts / "semantic"
    path = directory / "results.json"
    if not path.exists():
        return
    records = read_json(path)
    items, rows = [], []
    for record in records:
        name, result = record["name"], record["result"]
        synthetic = record["group"] == "synthetic"
        pdf = directory / f"{name}.pdf" if synthetic else ROOT / name
        expected: dict[str, Any] | None = None
        if synthetic and name in SEMANTIC_EXPECTATIONS:
            count = SEMANTIC_EXPECTATIONS[name]
            expected = {"validated_tables": count, "tables": [SEMANTIC_POSITIVE] if count else []}
        items.append(Item(name, {"pdf": ref(pdf), "bytes": record["bytes"]}, expected, {"group": record["group"]}))
        tables = [[[cell["text"] for cell in row] for row in table] for table in result.get("tables", [])]
        scores: Scores = {
            "validated_tables": len(tables),
            "tagged_table_candidates": result.get("tagged_tables"),
            "struct_root": result.get("struct_root"),
            "form_leaves": result.get("form_leaves"),
            "embedded_payload_names": len(result.get("embedded_payload_names") or []),
            "median_ms": record["median_ms"],
            "error": result["status"] == "error",
            "abstained": result["status"] == "abstain",
        }
        if expected is not None:
            scores["expected_outcome"] = tables == expected["tables"]
        abstentions = result.get("abstentions") or []
        rows.append(
            Row(
                name,
                {
                    "tables": tables,
                    "abstentions": abstentions,
                    "embedded_payload_names": result.get("embedded_payload_names"),
                    "error": result.get("error"),
                },
                scores,
                {
                    "group": record["group"],
                    "status": result["status"],
                    "outcome": abstentions[0] if abstentions else result["status"],
                },
                wall_ms=record["median_ms"],
            )
        )
    corpus = [r["result"] for r in records if r["group"] == "corpus"]
    controls = [row for row in rows if row.metadata["group"] == "synthetic"]
    run_scores: Scores = {
        "corpus.pages": len(corpus),
        "corpus.struct_root": sum(bool(r.get("struct_root")) for r in corpus),
        "corpus.tagged_table_candidates": sum(bool(r.get("tagged_tables")) for r in corpus),
        "corpus.validated_tables": sum(bool(r["tables"]) for r in corpus),
        "corpus.form_leaves": sum(bool(r.get("form_leaves")) for r in corpus),
        "corpus.embedded_payload_names": sum(bool(r.get("embedded_payload_names")) for r in corpus),
        "controls.cases": len(controls),
        "controls.expected_outcome": sum(bool(row.scores.get("expected_outcome")) for row in controls),
    }
    yield Experiment(
        "exp/semantic/tagged-tables",
        "Conservative tagged-PDF table recovery probe (bench/semantic_probe.py, pypdf). Corpus PDFs have no "
        "gold; authored controls declare whether a table must recover exactly or abstain.",
        items,
        [
            Run(
                "pypdf-structtree-probe",
                "Research tagged-table traversal with backlink validation; median of fresh-reader repeats.",
                rows,
                {
                    "report": "bench/results/semantic-probe.md",
                    "report_crosscheck": (
                        "match: corpus 3/15 StructTreeRoot, 1/15 table candidate, 0/15 validated, 3/15 forms, "
                        "0/15 attachments; both positive controls recover exactly, other nine zero tables"
                    ),
                },
                run_scores,
                mtime(path),
            )
        ],
        "bench/results/pdf-master-artifacts/semantic",
    )


# --- color regions ---------------------------------------------------------------------------


def color_regions(artifacts: Path) -> Iterable[Experiment]:
    """M005 color-region pilot: native paint bounds versus raster components at three thresholds."""
    path = artifacts / "color-regions.json"
    if not path.exists():
        return
    report = read_json(path)
    cases: dict[str, list[dict[str, Any]]] = {}
    for row in report["rows"]:
        cases.setdefault(row["case"], []).append(row)
    items = [
        Item(
            case,
            {"input_sha256": rows[0]["input_sha256"], "dpi": report["dpi"], "fixture": "bench/color_regions.py"},
            {"groups": rows[0]["expected"], "boxes": rows[0]["expected_boxes"]},
        )
        for case, rows in cases.items()
    ]
    native = [
        Row(
            case,
            {"regions": rows[0]["vector_regions"]},
            {"hits": rows[0]["vector_hits"], "expected": rows[0]["expected"], "native_ms": rows[0]["vector_ms"]},
            {"status": "ok"},
            wall_ms=rows[0]["vector_ms"],
        )
        for case, rows in cases.items()
    ]
    runs = [
        Run(
            "native-paint-bounds",
            "Native fill/stroke paint bounds grouped from get_drawings-style interpretation.",
            native,
            {"report": "bench/results/color-regions.md", "experiment_id": "M005"},
            {
                "hits": sum(int(r.scores["hits"] or 0) for r in native),
                "expected": sum(int(r.scores["expected"] or 0) for r in native),
            },
            mtime(path),
        )
    ]
    for threshold in sorted({row["threshold"] for row in report["rows"]}):
        selected = [row for row in report["rows"] if row["threshold"] == threshold]
        raster = [
            Row(
                row["case"],
                {"regions": row["raster_regions"]},
                {
                    "hits": row["raster_hits"],
                    "extras": row["raster_extras"],
                    "expected": row["expected"],
                    "cold_render_ms": row["cold_render_ms"],
                    "rgb_conversion_ms": row["rgb_conversion_ms"],
                    "segmentation_subprocess_ms": row["segmentation_subprocess_ms"],
                },
                {"status": "ok"},
                wall_ms=row["segmentation_subprocess_ms"],
            )
            for row in selected
        ]
        runs.append(
            Run(
                f"raster-threshold-{threshold}",
                f"Standalone bounded Rust connected components at RGB/luminance threshold {threshold}, "
                f"{report['connectivity']}-connectivity, min area {report['min_area_pixels']} px.",
                raster,
                {
                    "report": "bench/results/color-regions.md",
                    "experiment_id": "M005",
                    "rust_source_sha256": report["rust_source_sha256"],
                    "background_white": report["background_white"],
                },
                {
                    "hits": sum(row["raster_hits"] for row in selected),
                    "extras": sum(row["raster_extras"] for row in selected),
                    "expected": sum(row["expected"] for row in selected),
                },
                mtime(path),
            )
        )
    yield Experiment(
        "exp/color-regions/controls",
        "M005 CPU color-region pilot on five authored PDFs. A hit needs all four box coordinates within 2 pt "
        "of an authored group boundary; extras are unmatched geometric candidates, not false tables.",
        items,
        runs,
        "bench/results/pdf-master-artifacts/color-regions.json",
    )


# --- campaign manifest -----------------------------------------------------------------------


def campaign_manifest(artifacts: Path) -> Iterable[Experiment]:
    """Campaign validation record: aggregate-only, one item and one run."""
    path = artifacts / "campaign-manifest.json"
    if not path.exists():
        return
    manifest = read_json(path)
    validation = manifest.get("validation", {})
    scores: Scores = {
        key: value for key, value in validation.items() if isinstance(value, int) and not isinstance(value, bool)
    }
    for key, value in validation.items():
        if isinstance(value, str):
            scores[f"{key}_passed"] = value == "passed"
    if "strict_docs" in validation:
        scores["strict_docs_locales"] = len(validation["strict_docs"])
    scores["new_remote_spend_usd"] = manifest.get("new_remote_spend_usd")
    key = manifest["created_utc"]
    yield Experiment(
        "exp/campaign-manifest/validation",
        "Aggregate-only provenance record for the 2026-10-08 local study campaign (file hashes, native build, "
        "validation counts). No per-item results exist; one item and one row carry the aggregates.",
        [
            Item(
                key,
                {"head": manifest["head"], "files": len(manifest.get("files", {}))},
                None,
                {"aggregate_only": True},
            )
        ],
        [
            Run(
                "campaign-validation",
                "Recorded repository validation for the campaign commit.",
                [Row(key, {"validation": validation, "publication": manifest.get("publication")}, scores)],
                {
                    "aggregate_only": True,
                    "native_extension_sha256": manifest.get("native_extension_sha256"),
                    "files_digest": digest(manifest.get("files", {})),
                },
                scores,
                mtime(path),
            )
        ],
        "bench/results/pdf-master-artifacts/campaign-manifest.json",
    )


# --- evidence designs ------------------------------------------------------------------------


def evidence_designs(artifacts: Path) -> Iterable[Experiment]:
    """D001 root-gate preparation: frozen requests per arm, no model outcomes retained here."""
    directory = artifacts / "evidence-designs" / "root-gate-v1"
    path = directory / "manifest.json"
    if not path.exists():
        return
    manifest = read_json(path)
    labels_path = directory / "scorer-only.json"
    labels = read_json(labels_path) if labels_path.exists() else {}
    pages: dict[str, dict[str, Any]] = {}
    for record in manifest["records"]:
        pages.setdefault(record["id"], record)
    items = [
        Item(
            page,
            {"page_index": record["page_index"], "source_sha256": record["source_sha256"]},
            {"gate_label": labels[page]} if page in labels else None,
            {"label_semantics": "A = qualifying ruled table grid, B = none"},
        )
        for page, record in pages.items()
    ]
    runs = []
    for arm in manifest["arms"]:
        records = [record for record in manifest["records"] if record["arm"] == arm]
        rows = [
            Row(
                record["id"],
                {
                    "request": {
                        "path": rel(directory / record["request"]),
                        "sha256": record["sha256"],
                        "bytes": record["bytes"],
                    },
                    "source_admission_refusal": record["source_admission_refusal"],
                },
                {
                    "request_bytes": record["bytes"],
                    "questions": record["questions"],
                    "source_admission_refused": record["source_admission_refusal"] is not None,
                },
                {"status": "refused-source" if record["source_admission_refusal"] else "prepared-not-run"},
            )
            for record in records
        ]
        runs.append(
            Run(
                f"prepare/{arm}",
                f"Source-only native evidence request for the {arm} arm; preparation only, no model call.",
                rows,
                {
                    "preparation_only": True,
                    "model": manifest.get("model"),
                    "native_sha256": manifest.get("native_sha256"),
                    "report": "bench/results/evidence-designs.md",
                    "report_crosscheck": EVIDENCE_CROSSCHECK.get(arm, "no committed figure")
                    + "; 1/125 source-admission refusal as reported. Preparation resources differ: report "
                    "3.232 s wall / 107.06 MiB, manifest records the values below (later regeneration).",
                    "preparation_wall_seconds": manifest.get("wall_seconds"),
                    "preparation_cpu_seconds": manifest.get("cpu_seconds"),
                    "preparation_peak_rss_mib": manifest["peak_rss_bytes"] / 2**20
                    if manifest.get("peak_rss_bytes")
                    else None,
                    "measurement": manifest.get("measurement"),
                },
                {
                    "mean_request_bytes": statistics.mean(r["bytes"] for r in records) if records else None,
                    "source_admission_refused": sum(r["source_admission_refusal"] is not None for r in records),
                    "pages": len(records),
                },
                mtime(path),
            )
        )
    yield Experiment(
        "exp/evidence-designs/root-gate-v1",
        "D001 evidence preparation: four source-only arms freeze 125 DEV pages into 500 gate requests. "
        "No model was called; rows carry request size/admission only. Expected labels are scorer-only.",
        items,
        runs,
        "bench/results/pdf-master-artifacts/evidence-designs/root-gate-v1",
    )


EVIDENCE_CROSSCHECK = {
    "geometry": "match report mean 8,807 bytes",
    "neighbors": "match report mean 10,028 bytes",
    "blob": "match report mean 11,545 bytes",
    "hybrid": "match report mean 10,226 bytes",
}


# --- gpu comparison --------------------------------------------------------------------------

GPU_ARMS = (
    ("cpu-fp32", "", "cpu-fp32", True),
    ("gpu-fp32", "", "gpu-fp32", True),
    ("gpu-fp16", "", "gpu-fp16", True),
    ("initial-overlapping/cpu-fp32", "initial-overlapping", "cpu-fp32", False),
    ("initial-overlapping/gpu-fp32", "initial-overlapping", "gpu-fp32", False),
    ("initial-auto-cpu-thread-reset/cpu-fp32", "initial-auto-cpu-thread-reset", "cpu-fp32", False),
)


def _gpu_page_diff(left: dict[str, Any], right: dict[str, Any]) -> Scores:
    from bench.gpu_comparison import compare_predictions  # noqa: PLC0415 - light, optional bench import.

    diff = compare_predictions([left], [right])
    scores: Scores = {
        "bit_exact_vs_cpu": diff["bit_exact_pages"] == 1,
        "topology_equal_vs_cpu": diff["ordered_topology_equal_pages"] == 1,
        "within_tolerance_vs_cpu": diff["within_tolerance_pages"] == 1,
    }
    if scores["topology_equal_vs_cpu"]:
        scores["max_box_delta_px"] = diff["max_box_delta_on_equal_topology"]
        scores["max_confidence_delta"] = diff["max_confidence_delta_on_equal_topology"]
    return scores


def _gpu_run(  # noqa: PLR0913 - one run needs its arm, labels, baseline and summary.
    name: str,
    path: Path,
    labels: dict[str, dict[str, Any]],
    baseline: dict[str, dict[str, Any]] | None,
    summary: dict[str, Any],
    *,
    matched: bool,
) -> Run:
    run = read_json(path)
    passes = run["passes"]
    predictions = passes[0]["predictions"]
    rows = []
    confusion: dict[str, dict[str, int]] = {}
    diffs: list[Scores] = []
    for prediction in predictions:
        label = labels[prediction["id"]]
        predicted = any(box["class"].lower() == "table" for box in prediction["boxes"])
        cell = {(True, True): "tp", (True, False): "fn", (False, True): "fp", (False, False): "tn"}
        bucket = confusion.setdefault(label["cohort"], {"tp": 0, "fn": 0, "fp": 0, "tn": 0})
        bucket[cell[label["table_present"], predicted]] += 1
        scores: Scores = {
            "predicted_table_present": predicted,
            "presence_correct": predicted == label["table_present"],
            "boxes": len(prediction["boxes"]),
            "table_boxes": sum(box["class"].lower() == "table" for box in prediction["boxes"]),
        }
        if baseline is not None:
            diff = _gpu_page_diff(baseline[prediction["id"]], prediction)
            diffs.append(diff)
            scores.update(diff)
        rows.append(
            Row(
                prediction["id"],
                {"boxes": prediction["boxes"]},
                scores,
                {"cohort": label["cohort"], "status": "ok", "pass": 0},
            )
        )
    elapsed = statistics.median(p["elapsed_seconds"] for p in passes)
    run_scores: Scores = {
        "median_pass_seconds": elapsed,
        "pages_per_second": len(predictions) / elapsed,
        "median_pass_cpu_seconds": statistics.median(p["cpu_user_seconds"] + p["cpu_system_seconds"] for p in passes),
        "cold_model_load_seconds": run["cold_model_load_seconds"],
        "first_prediction_warmup_seconds": run["first_prediction_warmup_seconds"],
        "peak_rss_mib": run["peak_rss_kib"] / 1024,
    }
    if run.get("peak_cuda_allocated_bytes") is not None:
        run_scores["peak_cuda_allocated_mib"] = run["peak_cuda_allocated_bytes"] / 2**20
        run_scores["peak_cuda_reserved_mib"] = run["peak_cuda_reserved_bytes"] / 2**20
    for cohort, counts in confusion.items():
        for key, value in counts.items():
            run_scores[f"{cohort}.{key}"] = value
    if diffs:
        run_scores["bit_exact_pages"] = sum(bool(d["bit_exact_vs_cpu"]) for d in diffs)
        run_scores["topology_equal_pages"] = sum(bool(d["topology_equal_vs_cpu"]) for d in diffs)
        run_scores["within_tolerance_pages"] = sum(bool(d["within_tolerance_vs_cpu"]) for d in diffs)
    crosscheck = "excluded from the matched summary; no committed figures"
    arm = path.stem
    if matched:
        telemetry = summary.get("telemetry", {}).get(arm, {})
        for key in ("samples", "mean_utilization_percent", "max_host_memory_mib", "mean_host_power_watts"):
            if key in telemetry:
                run_scores[f"nvidia_smi.{key}"] = telemetry[key]
        expected = summary.get("scores", {}).get(arm)
        difference = summary.get("differences", {}).get(arm)
        same_scores = expected is None or expected == confusion
        same_diff = difference is None or (
            difference["bit_exact_pages"] == run_scores.get("bit_exact_pages")
            and difference["ordered_topology_equal_pages"] == run_scores.get("topology_equal_pages")
            and difference["within_tolerance_pages"] == run_scores.get("within_tolerance_pages")
        )
        crosscheck = "match summary.json" if same_scores and same_diff else "MISMATCH with summary.json"
    configuration = run.get("configuration", {})
    return Run(
        name,
        f"YOLO26m DocLayNet ({configuration.get('quantize', '')}, device {configuration.get('device', '')}, "
        f"imgsz {configuration.get('imgsz', '')}); rows from pass 0 as in the report."
        + ("" if matched else " Initial run excluded from the matched comparison."),
        rows,
        {
            "matched_comparison": matched,
            "device": run.get("device"),
            "half": run.get("half"),
            "torch": run.get("torch"),
            "ultralytics": run.get("ultralytics"),
            "model_sha256": run.get("model_sha256"),
            "cpu_threads": run.get("cpu_threads"),
            "pass_seconds": [p["elapsed_seconds"] for p in passes],
            "report": "bench/results/gpu-comparison.md",
            "report_crosscheck": crosscheck,
        },
        run_scores,
        mtime(path),
    )


def gpu_comparison(artifacts: Path) -> Iterable[Experiment]:
    """YOLO26m table-presence CPU/GPU matched comparison over 141 DEV images."""
    directory = artifacts / "gpu-comparison"
    if not (directory / "labels.json").exists():
        return
    labels = {row["id"]: row for row in read_json(directory / "labels.json")}
    inputs = read_json(directory / "inputs.json")
    summary_path = directory / "summary.json"
    summary = read_json(summary_path) if summary_path.exists() else {}
    items = [
        Item(
            entry["id"],
            {"image": {"path": rel(Path(entry["path"])), "sha256": entry["sha256"]}},
            {"table_present": labels[entry["id"]]["table_present"]},
            {"cohort": entry["cohort"]},
        )
        for entry in inputs
    ]
    baselines: dict[str, dict[str, dict[str, Any]]] = {}
    runs = []
    for name, folder, arm, matched in GPU_ARMS:
        path = (directory / folder / f"{arm}.json") if folder else directory / f"{arm}.json"
        if not path.exists():
            continue
        if arm == "cpu-fp32":
            predictions = read_json(path)["passes"][0]["predictions"]
            baselines[folder] = {p["id"]: p for p in predictions}
        baseline = None if arm == "cpu-fp32" else baselines.get(folder)
        runs.append(_gpu_run(name, path, labels, baseline, summary, matched=matched))
    yield Experiment(
        "exp/gpu-comparison/yolo-table-presence",
        "YOLO26m (hantian/yolo-doclaynet) table presence on 125 synthetic silver DEV pages and 16 OmniDocBench "
        "DEV images, matched CPU FP32 / GPU FP32 / GPU FP16 arms. Cohorts are distinct tasks; do not pool. "
        "GPU rows compare each page with the same folder's CPU FP32 pass 0.",
        items,
        runs,
        "bench/results/pdf-master-artifacts/gpu-comparison",
    )


# --- geometry cascade ------------------------------------------------------------------------

GEOMETRY_ROUNDS = (
    ("round1", "round1-before-normalization.json", "Round one, before logical rotation normalization."),
    ("round2", "round2-before-logical-header.json", "Round two, before the logical-direction header handoff."),
    ("round3-final", "results.json", "Final round three with the native collinear-rule connectivity fix."),
)
GEOMETRY_SPLITS = ("existing", "development", "heldout", "development-round2")


def _geometry_row(result: dict[str, Any]) -> Row:
    if "score" not in result:
        return Row(
            result["name"],
            {"error": result.get("error")},
            {"error": True},
            {"split": result["split"], "status": "error"},
        )
    score, source, records = result["score"], result["source"], result["records"]
    scores: Scores = {
        "tables": score["tables"],
        "missing_source_tokens": source["missing_tokens"],
        "extra_source_tokens": source["extra_tokens"],
        "median_ms": result["median_ms"],
        "error": False,
    }
    if score["gold_available"]:
        for key in (
            "correct_cells",
            "total_cells",
            "relationship_matches",
            "relationship_expected",
            "relationship_observed",
        ):
            scores[key] = score[key]
        scores["exact"] = score["exact"]
        scores["expected_tables"] = score["expected_tables"]
        scores["excess_tables"] = max(0, score["tables"] - score["expected_tables"])
        if not score["expected_tables"]:
            scores["false_table_page"] = bool(score["tables"])
    if records["total"]:
        scores["record_checks_correct"] = records["correct"]
        scores["record_checks_total"] = records["total"]
    output = result["output"]
    markdown = output.get("markdown") or ""
    return Row(
        result["name"],
        {
            "route": output.get("route"),
            "tables": output.get("tables"),
            "markdown_chars": len(markdown),
            "markdown_sha256": hashlib.sha256(markdown.encode()).hexdigest(),
        },
        scores,
        {"split": result["split"], "family": result["family"], "status": "ok", "gold": score["gold_available"]},
        wall_ms=result["median_ms"],
    )


def _geometry_aggregate(results: list[dict[str, Any]]) -> Scores:
    """Recompute the report table with geometry_cascade.py's own aggregation."""
    scores: Scores = {}
    for split in (None, *GEOMETRY_SPLITS):
        rows = [r for r in results if (split is None or r["split"] == split) and "score" in r]
        if not rows:
            continue
        prefix = f"{split}." if split else ""
        gold = [r for r in rows if r["score"]["gold_available"]]
        positives = [r for r in gold if r["score"]["expected_tables"]]
        negatives = [r for r in gold if not r["score"]["expected_tables"]]
        scores[f"{prefix}exact_pages"] = sum(bool(r["score"]["exact"]) for r in gold)
        scores[f"{prefix}gold_pages"] = len(gold)
        scores[f"{prefix}correct_cells"] = sum(r["score"]["correct_cells"] for r in positives)
        scores[f"{prefix}total_cells"] = sum(r["score"]["total_cells"] for r in positives)
        scores[f"{prefix}relationship_matches"] = sum(r["score"]["relationship_matches"] for r in positives)
        scores[f"{prefix}relationship_expected"] = sum(r["score"]["relationship_expected"] for r in positives)
        scores[f"{prefix}false_table_pages"] = sum(bool(r["score"]["tables"]) for r in negatives)
        scores[f"{prefix}negative_pages"] = len(negatives)
        scores[f"{prefix}excess_tables"] = sum(
            max(0, r["score"]["tables"] - r["score"]["expected_tables"]) for r in gold
        )
        scores[f"{prefix}missing_source_tokens"] = sum(r["source"]["missing_tokens"] for r in rows)
        scores[f"{prefix}extra_source_tokens"] = sum(r["source"]["extra_tokens"] for r in rows)
        scores[f"{prefix}median_ms"] = statistics.median(r["median_ms"] for r in rows)
    scores["errors"] = sum("score" not in r for r in results)
    return scores


GEOMETRY_FINAL_REPORT = {
    # (split, method): (exact pages, gold pages, correct cells, total cells) from geometry-cascade.md.
    ("existing", "native"): (8, 15, 18, 83),
    ("existing", "text"): (8, 15, 26, 83),
    ("existing", "geometry"): (11, 15, 73, 83),
    ("existing", "header"): (6, 15, 0, 83),
    ("existing", "cascade"): (10, 15, 38, 83),
    ("development", "cascade"): (4, 4, 36, 36),
    ("heldout", "geometry"): (14, 16, 168, 168),
    ("heldout", "cascade"): (16, 16, 168, 168),
    ("development-round2", "cascade"): (2, 2, 18, 18),
}


def _geometry_crosscheck(method: str, scores: Scores) -> str:
    mismatches = []
    for (split, name), expected in GEOMETRY_FINAL_REPORT.items():
        if name != method:
            continue
        observed = tuple(
            scores.get(f"{split}.{key}") for key in ("exact_pages", "gold_pages", "correct_cells", "total_cells")
        )
        if observed != expected:
            mismatches.append(f"{split}: {observed} != {expected}")
    return "MISMATCH " + "; ".join(mismatches) if mismatches else "match geometry-cascade.md split table"


def geometry(artifacts: Path) -> Iterable[Experiment]:
    """CPU geometry cascade: five methods over 50 inputs across three retained rounds."""
    directory = artifacts / "geometry"
    final_path = directory / "results.json"
    if not final_path.exists():
        return
    final = read_json(final_path)
    names = list(dict.fromkeys(r["name"] for r in final["results"]))
    items = []
    for name in names:
        labels_path = directory / name / "labels.json"
        labels = read_json(labels_path) if labels_path.exists() else {}
        same = [r for r in final["results"] if r["name"] == name]
        first = next((r for r in same if "sha256" in r), same[0])
        items.append(
            Item(
                name,
                {"pdf": ref(directory / name / "input.pdf", first.get("sha256")), "source": labels.get("source")},
                {"tables": labels.get("tables"), "spans": labels.get("spans"), "notes": labels.get("notes")},
                {"split": first.get("split"), "family": first.get("family")},
            )
        )
    runs = []
    for round_name, filename, description in GEOMETRY_ROUNDS:
        path = directory / filename
        if not path.exists():
            continue
        report = final if path == final_path else read_json(path)
        for method in dict.fromkeys(r["method"] for r in report["results"]):
            results = [r for r in report["results"] if r["method"] == method]
            scores = _geometry_aggregate(results)
            final_round = round_name == "round3-final"
            runs.append(
                Run(
                    f"{round_name}/{method}",
                    f"{description} Method: {method}.",
                    [_geometry_row(r) for r in results],
                    {
                        "round": round_name,
                        "method": method,
                        "superseded": not final_round,
                        "code_sha256": report.get("code_sha256"),
                        "native_extension_sha256": report.get("native_extension_sha256"),
                        "repeats": report.get("repeats"),
                        "report": "bench/results/geometry-cascade.md"
                        if final_round
                        else f"bench/results/pdf-master-artifacts/geometry/{path.stem}.md",
                        "report_crosscheck": _geometry_crosscheck(method, scores)
                        if final_round
                        else "superseded round; split table matches its local round report",
                    },
                    scores,
                    mtime(path),
                )
            )
    yield Experiment(
        "exp/geometry/cascade",
        "CPU geometry cascade (bench/geometry_cascade.py): native, text, geometry, header and cascade table "
        "methods on existing corpus/study inputs and authored development/transformation splits. The "
        "'heldout' split is a transformation split inspected after round one (regression observations), not "
        "the protected silver held-out set. Templates are related across splits.",
        items,
        runs,
        "bench/results/pdf-master-artifacts/geometry",
    )


# --- header relations ------------------------------------------------------------------------

HEADER_PHASES = (
    ("phase1", "phase1.json", "Phase one: original 104 fixtures, before the type-shift-declared family."),
    ("phase2-before-connectivity", "phase2-before-connectivity.json", "Phase two, before the connectivity fix."),
    (
        "phase3-initial-connectivity-regressed",
        "phase3-initial-connectivity-regressed.json",
        "Phase three: first unconditional connectivity patch (regressed Form 1040).",
    ),
    ("final", "decisions.json", "Final decisions with the restricted connectivity repair."),
)
HEADER_FINAL_REPORT = {
    # method: (correct bands, abstained, tp, fp, fn) from header-relations.md.
    "first_row": (40, 32, 240, 208, 544),
    "constraints": (56, 48, 672, 48, 112),
    "strict_unhinted": (0, 112, 0, 0, 784),
    "strict_declared": (112, 0, 784, 0, 0),
}


def _header_row(case: dict[str, Any], method: str, phase_inputs: Path | None) -> Row:
    outcome = case["methods"][method]
    decision = outcome["decision"]
    scores: Scores = {
        "correct_band": outcome["correct_band"],
        "abstained": decision["header_rows"] is None,
        "edge_tp": outcome["tp"],
        "edge_fp": outcome["fp"],
        "edge_fn": outcome["fn"],
        "exact_cells": case.get("exact_cells", False),
        "tables": case["table_count"],
    }
    for kind, counts in (outcome.get("by_kind") or {}).items():
        for key, value in counts.items():
            scores[f"{kind}_{key}"] = value
    return Row(
        case["name"],
        {"decision": decision, "edges": outcome["edges"]},
        scores,
        {
            "family": case["family"],
            "status": "no-table"
            if not case["table_count"]
            else ("abstained" if decision["header_rows"] is None else "decided"),
            "extraction_ms": case["extraction_ms"],
        },
        input={"pdf": ref(phase_inputs / f"{case['name']}.pdf")} if phase_inputs else None,
    )


def _header_aggregate(rows: list[Row]) -> Scores:
    tp = sum(int(row.scores["edge_tp"] or 0) for row in rows)
    fp = sum(int(row.scores["edge_fp"] or 0) for row in rows)
    fn = sum(int(row.scores["edge_fn"] or 0) for row in rows)
    return {
        "cases": len(rows),
        "correct_bands": sum(bool(row.scores["correct_band"]) for row in rows),
        "abstained": sum(bool(row.scores["abstained"]) for row in rows),
        "edge_tp": tp,
        "edge_fp": fp,
        "edge_fn": fn,
        "edge_precision": ratio(tp, tp + fp),
        "edge_recall": ratio(tp, tp + fn),
        "exact_cells": sum(bool(row.scores["exact_cells"]) for row in rows),
    }


def _header_encoding(directory: Path) -> Experiment | None:
    phases = [(phase, directory / filename) for phase, filename, _ in HEADER_PHASES if (directory / filename).exists()]
    audits = {phase: read_json(path).get("encoding_audit") for phase, path in phases}
    audits = {phase: audit for phase, audit in audits.items() if audit}
    if not audits:
        return None
    keys = {f"scale-{e['scale']}-rotation-{e['rotation']}": e for audit in audits.values() for e in audit}
    items = [
        Item(key, {"scale": entry["scale"], "rotation": entry["rotation"]}, {"tables_per_form": 1, "same_pixels": True})
        for key, entry in keys.items()
    ]
    runs = []
    for phase, audit in audits.items():
        rows = []
        for entry in audit:
            forms = {("coalesced" if form["coalesced"] else "segmented"): form for form in entry["forms"]}
            rows.append(
                Row(
                    f"scale-{entry['scale']}-rotation-{entry['rotation']}",
                    {"forms": entry["forms"]},
                    {
                        "segmented_tables": forms["segmented"]["tables"],
                        "coalesced_tables": forms["coalesced"]["tables"],
                        "pixels_equal": forms["segmented"]["pixel_sha256"] == forms["coalesced"]["pixel_sha256"],
                    },
                    {"status": "ok"},
                )
            )
        runs.append(
            Run(
                phase,
                f"Segmented versus coalesced rule encodings, {phase}.",
                rows,
                {"report": "bench/results/header-relations.md", "superseded": phase != "final"},
                {
                    "segmented_detected": sum(int(r.scores["segmented_tables"] or 0) > 0 for r in rows),
                    "coalesced_detected": sum(int(r.scores["coalesced_tables"] or 0) > 0 for r in rows),
                    "pixels_equal": sum(bool(r.scores["pixels_equal"]) for r in rows),
                    "pairs": len(rows),
                },
                mtime(directory / {p: f for p, f, _ in HEADER_PHASES}[phase]),
            )
        )
    return Experiment(
        "exp/headers/rule-encoding",
        "Segmented/coalesced vector-rule encoding audit across eight scale/rotation pairs: identical pixels must "
        "yield the same native table detection (connectivity-fix regression).",
        items,
        runs,
        "bench/results/pdf-master-artifacts/headers",
    )


def headers(artifacts: Path) -> Iterable[Experiment]:
    """Header-relationship study: four methods over 112 generated tables, across four phases."""
    directory = artifacts / "headers"
    final_path = directory / "decisions.json"
    if not final_path.exists():
        return
    final = read_json(final_path)
    items = [
        Item(
            case["name"],
            {
                "pdf": ref(directory / f"{case['name']}.pdf", case.get("input_sha256")),
                "source_cells": case.get("source_cells"),
            },
            {"gold_band": case["gold_band"], "gold_edges": case["gold_edges"]},
            {"family": case["family"]},
        )
        for case in final["synthetic"]
    ]
    runs = []
    for phase, filename, description in HEADER_PHASES:
        path = directory / filename
        if not path.exists():
            continue
        report = final if path == final_path else read_json(path)
        cases = report["synthetic"]
        phase_inputs = directory / "phase1-inputs" if phase == "phase1" else None
        for method in dict.fromkeys(m for case in cases for m in case["methods"]):
            rows = [_header_row(case, method, phase_inputs) for case in cases if method in case["methods"]]
            scores = _header_aggregate(rows)
            crosscheck = "superseded phase; method table matches its local phase report"
            if phase == "final":
                expected = HEADER_FINAL_REPORT.get(method)
                observed = tuple(scores[k] for k in ("correct_bands", "abstained", "edge_tp", "edge_fp", "edge_fn"))
                crosscheck = (
                    "match header-relations.md" if observed == expected else f"MISMATCH {observed} != {expected}"
                )
            runs.append(
                Run(
                    f"{phase}/{method}",
                    f"{description} Method: {method}."
                    + (" Schema-assisted: fixture roles are supplied." if method == "strict_declared" else ""),
                    rows,
                    {
                        "phase": phase,
                        "method": method,
                        "superseded": phase != "final",
                        "native_sha256": report.get("environment", {}).get("native_sha256"),
                        "report": "bench/results/header-relations.md"
                        if phase == "final"
                        else f"bench/results/pdf-master-artifacts/headers/{path.stem}.md",
                        "report_crosscheck": crosscheck,
                        "experiment_id": "P003 (EXPERIMENTS_LOG header study)",
                    },
                    scores,
                    mtime(path),
                )
            )
    yield Experiment(
        "exp/headers/relations",
        "CPU header-relationship inference (bench/header_relations.py): 14 families x 2 scales x 4 rotations. "
        "Gold bands/edges are fixture declarations; variants share templates. Per-row inference timing is not "
        "retained (report gives medians only). Corpus first-page audit is unscored and not exported.",
        items,
        runs,
        "bench/results/pdf-master-artifacts/headers",
    )
    encoding = _header_encoding(directory)
    if encoding is not None:
        yield encoding


STUDIES = (encodings, semantic, color_regions, campaign_manifest, evidence_designs, gpu_comparison, geometry, headers)


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield every local study found under the artifact root."""
    for study in STUDIES:
        yield from study(artifacts)
