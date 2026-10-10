"""Offline P003 evaluation of frozen DEV decision treatments and matched repeats."""

# Artifact observations are heterogeneous; validation occurs at the file boundary.
# ruff: noqa: EM101, TRY003, C901, PLR0912, PLR2004, EM102, PLC0415, S311
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.generalization_scoring import _cells, audit_model_body, score_dataset
from bench.silver import canonical, guard_path, sha, write_json

SOURCE_FIELDS = ("id", "pdf_path", "pdf_sha256", "page_number")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("Expected JSON object")
    return value


def _rate(count: float, denominator: object, factor: float = 1) -> float | None:
    if isinstance(denominator, bool) or not isinstance(denominator, (int, float)):
        return None
    return count / denominator * factor if math.isfinite(denominator) and denominator > 0 else None


def strict_scores(targets: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Add span-aware exact anchors while preserving established P002 metrics."""
    result = score_dataset(targets, predictions)
    observed = {p["id"]: p for p in predictions}
    references = {p["id"]: p for p in targets}
    for page in result["pages"]:
        exact = 0
        if page.get("structural_scored") and not page["error"]:
            prediction = observed[page["id"]]
            tables = prediction.get("tables", [])
            for pair in page["matches"]:
                reference = _cells(references[page["id"]]["tables"][pair["target"]])
                actual = _cells(tables[pair["prediction"]])
                exact += sum(reference[key] == actual[key] for key in reference.keys() & actual.keys())
        page["strict_exact_cells"] = exact
    result["totals"]["strict_exact_cells"] = sum(p["strict_exact_cells"] for p in result["pages"])
    positive = [p for p in result["pages"] if p.get("positive_page")]
    result["positive_macro"] = {
        "positive_pages": len(positive),
        "strict_exact_cell_recall": statistics.mean(p["strict_exact_cells"] / p["expected_cells"] for p in positive)
        if positive
        else None,
        "complete_table_recall": statistics.mean(p["complete_tables"] / p["expected_tables"] for p in positive)
        if positive
        else None,
    }
    return result


def costs(report: dict[str, Any]) -> dict[str, Any]:
    """Never turn missing, unresolved or partially estimated charges into totals."""
    bases = report.get("cost_bases", {})
    effective = report.get("effective_usd")
    complete = report.get("ledger_attempts") is not None and not any(bases.get(k, 0) for k in ("unknown", "reserved"))
    valid = (
        not isinstance(effective, bool)
        and isinstance(effective, (int, float))
        and math.isfinite(effective)
        and effective >= 0
    )
    return {
        "effective_api_usd": effective if complete and valid else None,
        "provider_reported_subtotal_usd": report.get("provider_reported_usd"),
        "missing_provider_charge_count": report.get("missing_provider_charge_count"),
        "ledger_attempts": report.get("ledger_attempts"),
        "cost_bases": bases,
        "accounted_usd_including_reservations": report.get("accounted_usd"),
        "scope": "all attempts attributed to run, including failures; API only; zero charge retained",
    }


def verify_archive(directory: Path, frozen: dict[str, Any], trusted: dict[str, str] | None = None) -> dict[str, str]:
    """Require each archive hash to match a separately trusted local source digest."""
    hashes = frozen["code_sha256"]
    if not hashes:
        raise ValueError("Frozen code inventory is empty")
    checked = {}
    for name, digest in hashes.items():
        if Path(name).name != name or not name.endswith(".py"):
            raise ValueError("Unsafe archived source filename")
        if sha(guard_path(directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived source bytes changed")
        if trusted is None:
            local = Path(__file__).parent / name
            expected = sha(local.read_bytes()) if local.is_file() else None
        else:
            expected = trusted.get(name)
        if digest != expected:
            raise ValueError(
                f"Untrusted archived source: {name}; supply an independently reviewed source digest manifest"
            )
        checked[name] = digest
    return checked


def score_run(
    directory: Path,
    corpus: Path,
    *,
    manifest_path: Path | None = None,
    cohort: str | None = None,
    trusted_code: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate existing runner artifacts without calling inference or executing archives."""
    # The existing offline verifier reconstructs source ownership and Markdown.
    from bench.generalization_report import _bounds, load_corpus, verify_output

    directory = guard_path(directory)
    manifest, targets = load_corpus(corpus)
    manifest_path = manifest_path or corpus / "manifest.json"
    selected_manifest = _read(manifest_path)
    if selected_manifest.get("split") != "DEV" or selected_manifest.get("dataset_sha256") != manifest["dataset_sha256"]:
        raise ValueError("Selected source manifest must identify the same explicit DEV corpus")
    records = [r for r in manifest["pages"] if cohort is None or r.get("cohort") == cohort]
    report = _read(directory / "report.json")
    frozen = _read(directory / "frozen.json")
    if report["config"] != frozen["config"] or frozen["manifest_sha256"] != sha(guard_path(manifest_path).read_bytes()):
        raise ValueError("Frozen configuration or selected manifest changed")
    if cohort is None and report["config"].get("pilot"):
        records = [r for r in records if r["pilot"]]
    expected = [{k: r[k] for k in SOURCE_FIELDS} for r in records]
    frozen_records = frozen["records"]
    if len(frozen_records) != len(expected) or {r["id"]: r for r in frozen_records} != {r["id"]: r for r in expected}:
        raise ValueError("Frozen inventory differs from complete predeclared cohort")
    selected_rows = selected_manifest["pages"]
    selected_by_id = {r["id"]: {k: r[k] for k in SOURCE_FIELDS} for r in selected_rows}
    if len(selected_by_id) != len(selected_rows) or any(selected_by_id.get(r["id"]) != r for r in expected):
        raise ValueError("Selected source manifest does not contain intended corpus inputs")
    code = verify_archive(directory, frozen, trusted_code)
    predictions = report["results"]
    ids = [p["id"] for p in predictions]
    intended = {r["id"] for r in expected}
    if len(ids) != len(set(ids)) or not set(ids) <= intended:
        raise ValueError("Duplicate or unknown result page ID")
    processor = report["config"].get("processor", "whole")
    required = {"pipeline_run.py", "pipeline_assembly.py"}
    if processor == "regions":
        required |= {"generalization_run.py", "pipeline_regions.py"}
    elif processor == "hybrid":
        required |= {"generalization_hybrid_run.py", "pipeline_hybrid_composition.py"}
    elif processor in {"vision", "vision_regions", "vision_multiscale"}:
        required = {"generalization_vision_run.py", "pipeline_vision_transcription.py"}
    elif processor != "whole":
        raise ValueError("Unsupported frozen processor")
    if not required <= code.keys():
        raise ValueError("Frozen code lacks required processor dependencies")
    artifacts = []
    operational = 0
    for prediction in predictions:
        verified = verify_output(directory, prediction, processor=processor)
        operational += int(verified["operational"])
        record = {
            "id": prediction["id"],
            "result_sha256": sha((directory / f"{prediction['id']}-result.json").read_bytes()),
            "tables_sha256": sha(canonical(prediction.get("tables", []))),
            "source_sha256": sha(canonical(prediction["source"])) if prediction.get("source") is not None else None,
            "operational": verified["operational"],
            "detector_evidence_sha256": sha(
                canonical(
                    {
                        key: {
                            k: v
                            for k, v in prediction[key].items()
                            if k not in {"metrics", "parent_cpu_seconds", "parent_wall_seconds"}
                        }
                        for key in (
                            "layout_detector",
                            "layout_detection",
                            "raw_layout_detection",
                            "filtered_layout_detection",
                        )
                        if isinstance(prediction.get(key), dict)
                    }
                )
            ),
        }
        if verified["operational"]:
            record["markdown_sha256"] = sha(guard_path(directory / f"{prediction['id']}.md").read_bytes())
        artifacts.append(record)
    if report.get("complete_output_pages", operational) != operational:
        raise ValueError("Report complete output count differs from independently verified count")
    scoring_predictions = deepcopy(predictions)
    for prediction in scoring_predictions:
        if prediction.get("status") == "ok" and prediction.get("source") is not None:
            _bounds(prediction["source"], {"tables": [t for t in prediction["tables"] if "bbox" not in t]})
    reference_pages = [p for p in targets["pages"] if p["id"] in intended]
    scoring = strict_scores(reference_pages, scoring_predictions)
    audits = []
    request_images = []
    for request in sorted(directory.glob("**/*-request-*.json")):
        body = _read(request)
        audit = audit_model_body(body)
        stack = [body]
        image_hashes = []
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, str) and node.startswith("data:image/"):
                image_hashes.append(sha(node.encode()))
        request_images.append(
            {
                "path": str(request.relative_to(directory)),
                "model": body.get("model"),
                "data_url_sha256": sorted(image_hashes),
            }
        )
        if not audit["explicit_reference_fields_absent"]:
            raise ValueError("Private-reference field in retained request")
        audits.append({"path": str(request.relative_to(directory)), "sha256": sha(request.read_bytes()), **audit})
    accounting = costs(report)
    metrics = dict(report.get("metrics", {}))
    if report.get("layout_detector_initialization") is not None:
        metrics["layout_detector_worker"] = {
            "initialization": report["layout_detector_initialization"],
            "requests": [
                {"id": p["id"], "metrics": p[key]["metrics"]}
                for p in predictions
                for key in ("layout_detector", "layout_detection")
                if isinstance(p.get(key), dict) and "metrics" in p[key]
            ],
            "scope": "Separate CPU worker subprocess; parent process CPU/RSS excludes worker. "
            "Do not sum RSS peaks or overlapping parent per-page CPU intervals.",
        }
    source_fingerprint = sha(
        canonical(sorted([{k: a[k] for k in ("id", "source_sha256")} for a in artifacts], key=lambda a: a["id"]))
    )
    errors = Counter(
        p.get("error_category", p.get("error", "unclassified")) for p in predictions if p.get("status") != "ok"
    )
    if len(predictions) < len(expected):
        errors["missing"] += len(expected) - len(predictions)
    return {
        "name": directory.name,
        "dataset_sha256": manifest["dataset_sha256"],
        "manifest_sha256": frozen["manifest_sha256"],
        "report_sha256": sha((directory / "report.json").read_bytes()),
        "cohort": cohort,
        "config": report["config"],
        "frozen_runtime": {k: frozen.get(k) for k in ("runtime", "python", "platform", "logical_cpus", "concurrency")},
        "intended_pages": len(expected),
        "operational_pages": operational,
        "errors": len(expected) - operational,
        "failure_categories": dict(errors),
        "scores": scoring["totals"],
        "page_scores": scoring["pages"],
        "positive_macro": scoring["positive_macro"],
        "exact_positive_pages": sum(
            p.get("exact_page", False) and p.get("positive_page", False) for p in scoring["pages"]
        ),
        "costs": accounting,
        "resources": metrics,
        "code_sha256": code,
        "artifacts": artifacts,
        "request_audits": audits,
        "request_image_inventory": request_images,
        "source_fingerprint": source_fingerprint,
        "source_inventory_pages": sum(a["source_sha256"] is not None for a in artifacts),
        "detector_evidence_fingerprint": sha(
            canonical(
                sorted(
                    [{k: a[k] for k in ("id", "detector_evidence_sha256")} for a in artifacts], key=lambda a: a["id"]
                )
            )
        ),
        "pages_per_minute": _rate(operational, metrics.get("wall_seconds"), 60),
        "intended_pages_per_minute": _rate(len(expected), metrics.get("wall_seconds"), 60),
        "pages_per_api_usd": _rate(operational, accounting["effective_api_usd"]),
        "exact_positive_pages_per_minute": _rate(
            sum(p.get("exact_page", False) and p.get("positive_page", False) for p in scoring["pages"]),
            metrics.get("wall_seconds"),
            60,
        ),
    }


def paired_comparison(left: dict[str, Any], right: dict[str, Any], *, samples: int = 2000) -> dict[str, Any]:
    """Paired page bootstrap diagnostic; repeated calls require separate repeat rows."""
    for key in ("dataset_sha256", "manifest_sha256", "cohort", "source_fingerprint", "detector_evidence_fingerprint"):
        if left[key] != right[key]:
            raise ValueError(f"Unmatched paired evaluation: {key}")
    if (
        left["source_inventory_pages"] != left["intended_pages"]
        or right["source_inventory_pages"] != right["intended_pages"]
    ):
        raise ValueError("Source-matched decision comparison requires complete retained sources")
    a, b = {p["id"]: p for p in left["page_scores"]}, {p["id"]: p for p in right["page_scores"]}
    if set(a) != set(b):
        raise ValueError("Paired evaluation requires identical page IDs")
    deltas = [b[k]["strict_exact_cells"] - a[k]["strict_exact_cells"] for k in sorted(a)]
    if not deltas or samples < 1:
        raise ValueError("Bootstrap requires pages and positive sample count")
    rng = random.Random(3003)
    totals = sorted(sum(rng.choices(deltas, k=len(deltas))) for _ in range(samples))
    left_config, right_config = treatment_config(left.get("config", {})), treatment_config(right.get("config", {}))
    changes = {
        key: [left_config.get(key), right_config.get(key)]
        for key in left_config.keys() | right_config.keys()
        if left_config.get(key) != right_config.get(key)
    }

    def image_inventory(run: dict[str, Any]) -> list[str]:
        return sorted(
            {digest for record in run.get("request_image_inventory", []) for digest in record["data_url_sha256"]}
        )

    return {
        "left": left["name"],
        "treatment_changes": changes,
        "gate_image_configuration_equal": left_config["gate_image"] == right_config["gate_image"],
        "request_image_hash_sets_equal": image_inventory(left) == image_inventory(right),
        "image_scope": "Serialized data-URL assets across actual requests; routing changes may change request "
        "inventory. Source/detector equality alone does not prove gate pixel equality.",
        "right": right["name"],
        "strict_exact_cell_delta": sum(deltas),
        "paired_page_bootstrap_95_interval": [
            totals[int(samples * 0.025)],
            totals[min(samples - 1, int(samples * 0.975))],
        ],
        "seed": 3003,
        "samples": samples,
        "scope": "DEV page sampling diagnostic, not independent hosted-repeat uncertainty or heldout inference",
        "page_deltas": [
            {
                "id": key,
                "strict_exact_cells": b[key]["strict_exact_cells"] - a[key]["strict_exact_cells"],
                "complete_tables": b[key].get("complete_tables", 0) - a[key].get("complete_tables", 0),
            }
            for key in sorted(a)
        ],
    }


def treatment_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize documented defaults and remove only declared run administration."""
    normalized = {key: value for key, value in config.items() if key not in {"run_id", "repeat_index", "order_seed"}}
    normalized.setdefault("gate_image", True)
    normalized.setdefault("source_order", "legacy")
    return normalized


def repeat_summary(runs: list[dict[str, Any]], *, reviewed_code_changes: bool = False) -> dict[str, Any]:
    """Keep fresh-repeat variation visible without treating pages as hosted repeats."""
    if not runs:
        raise ValueError("Repeat summary requires runs")
    fields = (
        "dataset_sha256",
        "manifest_sha256",
        "cohort",
        "source_fingerprint",
        "detector_evidence_fingerprint",
    )
    for run in runs[1:]:
        if any(run[key] != runs[0][key] for key in fields) or treatment_config(run["config"]) != treatment_config(
            runs[0]["config"]
        ):
            raise ValueError("Repeat summary requires identical treatment, inputs and retained evidence")
    code_identical = len({sha(canonical(run.get("code_sha256", {}))) for run in runs}) == 1
    if not code_identical and not reviewed_code_changes:
        raise ValueError(
            "Repeat code snapshots differ; independent authentication plus operator semantic review required"
        )
    metrics = {}
    for key in ("strict_exact_cells", "complete_tables", "false_positive_page", "all_page_errors"):
        values = [r["scores"].get(key, 0) for r in runs]
        metrics[key] = {
            "observations": values,
            "minimum": min(values),
            "median": statistics.median(values),
            "maximum": max(values),
            "sample_standard_deviation": statistics.stdev(values) if len(values) > 1 else None,
        }
    return {
        "runs": [r["name"] for r in runs],
        "repeat_count": len(runs),
        "administrative_fields": [
            {"name": run["name"], **{key: run["config"].get(key) for key in ("run_id", "repeat_index", "order_seed")}}
            for run in runs
        ],
        "code_snapshots_identical": code_identical,
        "operator_reviewed_code_changes": reviewed_code_changes,
        "code_semantics_scope": "Every snapshot independently authenticated; digest variation is visible and "
        "requires operator review before attributing variation only to fresh model responses",
        "metrics": metrics,
        "scope": "Fresh complete run repetitions of one fixed treatment; no best-repeat selection. "
        "Small repeat count does not establish calibrated confidence.",
    }


def markdown_report(runs: list[dict[str, Any]]) -> str:
    """Render every run independently with complete cost and resource scope."""
    lines = [
        "# P003 frozen DEV evaluation",
        "",
        (
            "All intended pages and errors remain in quality denominators. Pages/min and pages/API USD use "
            "independently verified output pages. API-zero or incomplete costs have undefined pages/API USD. "
            "Strict cells require exact text and anchor span; the P002 text-cell metric ignores spans."
        ),
        "",
        (
            "| Run | Outputs / intended | Errors | Complete tables / expected | Strict cells / expected "
            "| P002 text cells "
            "| Negative FP pages / negatives | Extra tables | Pages/min | Pages/API USD | Effective API USD |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def fmt(value: object) -> str:
        return "unmeasured" if value is None else f"{value:.6g}" if isinstance(value, float) else str(value)

    for run in runs:
        s = run["scores"]
        row = [
            run["name"],
            f"{run['operational_pages']}/{run['intended_pages']}",
            run["errors"],
            f"{s.get('complete_tables', 0)}/{s.get('expected_tables', 0)}",
            f"{s['strict_exact_cells']}/{s.get('expected_cells', 0)}",
            s.get("correct_text_cells", 0),
            f"{s.get('false_positive_page', 0)}/{s.get('negative_page', 0)}",
            s.get("false_positive_tables", 0),
            run["pages_per_minute"],
            run["pages_per_api_usd"],
            run["costs"]["effective_api_usd"],
        ]
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    for run in runs:
        lines += [
            "",
            f"## {run['name']}",
            "",
            f"Dataset `{run['dataset_sha256']}`; manifest `{run['manifest_sha256']}`; report `{run['report_sha256']}`.",
            "",
            "Positive-page macro recall: `" + json.dumps(run["positive_macro"], sort_keys=True) + "`.",
            "",
            "Failure categories: `" + json.dumps(run["failure_categories"], sort_keys=True) + "`.",
            "",
            "Resources (run interval; local preprocessing remains distinct from API inference): `"
            + json.dumps(run["resources"], sort_keys=True)
            + "`.",
            "",
            "All-attempt API accounting: `" + json.dumps(run["costs"], sort_keys=True) + "`.",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Score existing frozen runs using private references only offline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--cohort")
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--trusted-code", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument(
        "--reviewed-repeat-code-changes",
        action="store_true",
        help="Attest operator review of authenticated source changes for repeat comparability",
    )
    parser.add_argument("--repeat-summary", action="store_true", help="Summarize identical treatment repetitions")
    parser.add_argument("--paired", action="store_true", help="Compare exactly two source-matched decision runs")
    args = parser.parse_args()
    trusted = _read(args.trusted_code) if args.trusted_code else None
    runs = [
        score_run(p, args.corpus, manifest_path=args.manifest, cohort=args.cohort, trusted_code=trusted)
        for p in args.run
    ]
    comparison = None
    if args.paired:
        if len(runs) != 2:
            parser.error("--paired requires exactly two --run arguments")
        comparison = paired_comparison(*runs)
    output = guard_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    repeats = (
        repeat_summary(runs, reviewed_code_changes=args.reviewed_repeat_code_changes) if args.repeat_summary else None
    )
    write_json(output, {"schema": 1, "runs": runs, "paired": comparison, "repeats": repeats})
    if args.markdown:
        markdown = markdown_report(runs)
        if repeats is not None:
            markdown += "\nRepeat variation: `" + json.dumps(repeats, sort_keys=True) + "`.\n"
        if comparison is not None:
            summary = {key: value for key, value in comparison.items() if key != "page_deltas"}
            markdown += "\nPaired comparison: `" + json.dumps(summary, sort_keys=True) + "`.\n"
        guard_path(args.markdown).write_text(markdown)


if __name__ == "__main__":
    main()
