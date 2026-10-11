"""Offline dual-score audit of explicitly pinned, independently verified full-pipeline outputs."""

# ruff: noqa: EM101, TRY003, C901, PLC0415
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.generalization_scoring import _cells
from bench.p003_content_alignment import compare_content
from bench.p003_report import strict_scores
from bench.p003_schema_sensitivity import compare
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

VERSION = "p003-dual-score-audit-v1"


def pinned(path: str, expected: str) -> dict[str, Any]:
    """Read exactly the authorized artifact and fail before interpreting changed bytes."""
    data = guard_path(Path(path)).read_bytes()
    if sha(data) != expected:
        raise ValueError("Pinned audit artifact changed: " + path)
    value = json.loads(data)
    if not isinstance(value, dict):
        raise TypeError("Audit artifacts must be JSON objects")
    return value


def admit(entry: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Authenticate prior independent evaluation and complete output before reference access."""
    report = pinned(entry["report"], entry["report_sha256"])
    evaluation = pinned(entry["evaluation"], entry["evaluation_sha256"])
    frozen = pinned(entry["frozen"], entry["frozen_sha256"])
    manifest = pinned(entry["run_manifest"], entry["run_manifest_sha256"])
    if len(evaluation.get("runs", [])) != 1:
        raise ValueError("Exactly one prior independently verified run required")
    verified = evaluation["runs"][0]
    if verified["evaluation_scope"] != "complete pipeline" or verified["report_sha256"] != entry["report_sha256"]:
        raise ValueError("Prior evaluation does not authenticate complete-pipeline report")
    if (
        verified["manifest_sha256"] != entry["run_manifest_sha256"]
        or frozen["manifest_sha256"] != entry["run_manifest_sha256"]
    ):
        raise ValueError("Frozen, evaluated, and pinned run manifests differ")
    ids = [row["id"] for row in report["results"]]
    expected = [row["id"] for row in manifest["pages"]]
    if len(ids) != len(set(ids)) or len(expected) != len(set(expected)) or set(ids) != set(expected):
        raise ValueError("Complete unique source-manifest output inventory required")
    if {row["id"] for row in verified["page_scores"]} != set(expected):
        raise ValueError("Prior quality inventory differs from source manifest")
    if len(frozen["records"]) != len(expected) or {row["id"] for row in frozen["records"]} != set(expected):
        raise ValueError("Frozen execution inventory differs from declared source manifest")
    return report, verified


def _units(table: dict[str, Any]) -> int:
    return sum(len(value) for value in _cells(table).values())


def dual_scores(
    targets: list[dict[str, Any]], predictions: list[dict[str, Any]], strict: dict[str, Any]
) -> dict[str, Any]:
    """Keep exact table matches; penalize omitted/extra content and expose unsupported coverage."""
    references, outputs = ({row["id"]: row for row in rows} for rows in (targets, predictions))
    if len(references) != len(targets) or len(outputs) != len(predictions) or set(references) != set(outputs):
        raise ValueError("Complete unique page inventories required")
    counts: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    pages = []
    for page in strict["pages"]:
        counts["pages"] += 1
        if not page["structural_scored"]:
            counts["diagnostic_pages"] += 1
            pages.append({"id": page["id"], "structural_scored": False, "error": page["error"]})
            continue
        target = references[page["id"]]["tables"]
        predicted = outputs[page["id"]].get("tables", []) if not page["error"] else []
        counts["scored_pages"] += 1
        counts["reference_tables"] += len(target)
        counts["prediction_tables"] += len(predicted)
        counts["error_pages"] += bool(page["error"])
        used_reference, used_prediction = set(), set()
        pairs = []
        for match in page["matches"]:
            a, b = match["target"], match["prediction"]
            used_reference.add(a)
            used_prediction.add(b)
            schema = compare(target[a], predicted[b])
            content = compare_content(target[a], predicted[b])
            exact = _cells(target[a]) == _cells(predicted[b])
            counts["strict_complete_tables"] += exact
            counts["strict_or_equivalent_tables"] += exact or schema["schema_equivalent"]
            counts["new_schema_equivalent_tables"] += not exact and schema["schema_equivalent"]
            counts["different_column_equivalent_tables"] += (
                schema["schema_equivalent"] and target[a]["col_count"] != predicted[b]["col_count"]
            )
            counts["schema_eligible_pairs"] += schema["eligible"]
            counts["matched_table_pairs"] += 1
            counts["content_supported_pairs"] += content["supported"]
            if content["supported"]:
                for key, value in content["counts"].items():
                    counts[key] += value
                counts["content_recovered_tables"] += content["content_recovered_with_row_order"]
            else:
                counts["content_unsupported_pairs"] += 1
                counts["unmeasured_reference_characters"] += _units(target[a])
                counts["unmeasured_prediction_characters"] += _units(predicted[b])
                reasons[content["unsupported_reason"]] += 1
            pairs.append({**match, "strict_complete": exact, "schema": schema, "content": content})
        for index, table in enumerate(target):
            if index not in used_reference:
                counts["missing_tables"] += 1
                counts["missing"] += _units(table)
                counts["reference_units"] += _units(table)
        for index, table in enumerate(predicted):
            if index not in used_prediction:
                counts["extra_tables"] += 1
                counts["extra"] += _units(table)
                counts["prediction_units"] += _units(table)
        pages.append(
            {
                "id": page["id"],
                "structural_scored": True,
                "error": page["error"],
                "pairs": pairs,
                "missing_tables": page["missing_tables"],
                "extra_tables": page["false_positive_tables"],
            }
        )
    matched, predicted_units, reference_units = counts["matched"], counts["prediction_units"], counts["reference_units"]
    precision = matched / predicted_units if predicted_units else (1.0 if not reference_units else 0.0)
    recall = matched / reference_units if reference_units else (1.0 if not predicted_units else 0.0)
    complete_coverage = not counts["content_unsupported_pairs"] and counts["scored_pages"] > 0
    return {
        "version": VERSION,
        "counts": dict(counts),
        "unsupported_reasons": dict(reasons),
        "pages": pages,
        "covered_content_precision": precision,
        "covered_content_recall": recall,
        "coverage_scope": "Supported pairs and all missing/extra tables; unsupported pairs counted separately",
        "full_content_precision": precision if complete_coverage else None,
        "full_content_recall": recall if complete_coverage else None,
        "strict_or_equivalent_scope": (
            "Unchanged strict complete tables plus conservative first-row-header-proxy lexical equivalence; "
            "source review still required"
        ),
        "whole_document_semantic_correctness": None,
        "primary_scores_changed": False,
    }


def audit(plan: Path, output: Path) -> dict[str, Any]:
    """Admit all input evidence before references; retain reproducible strict and secondary artifacts."""
    plan = guard_path(plan)
    declaration = json.loads(plan.read_bytes())
    entries = declaration["entries"]
    if not entries or len({e["name"] for e in entries}) != len(entries):
        raise ValueError("Nonempty unique explicit run inventory required")
    admitted = [admit(entry) for entry in entries]
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh audit output required; originals never overwritten")
    output.mkdir(parents=True)
    corpora = {}
    result: dict[str, Any] = {
        "version": VERSION,
        "plan_sha256": sha(plan.read_bytes()),
        "runs": [],
        "new_api_calls": 0,
        "originals_changed": False,
        "reference_use": "Evaluation audit only; no inference tuning",
    }
    for entry, (report, verified) in zip(entries, admitted, strict=True):
        corpus = entry["corpus"]
        if corpus not in corpora:
            # Pinned hashes are independently supplied by root, not taken from candidate output.
            pinned(str(Path(corpus) / "private-targets.json"), entry["targets_sha256"])
            pinned(str(Path(corpus) / "manifest.json"), entry["corpus_manifest_sha256"])
            if entry["corpus_kind"] == "confirmation":
                from bench.p003_confirmation import load_corpus
            else:
                from bench.generalization_report import load_corpus
            corpora[corpus] = load_corpus(guard_path(Path(corpus)))
        manifest, all_targets = corpora[corpus]
        if manifest["dataset_sha256"] != verified["dataset_sha256"]:
            raise ValueError("Verified source dataset differs from authenticated corpus")
        ids = {row["id"] for row in report["results"]}
        targets = [row for row in all_targets["pages"] if row["id"] in ids]
        with Resources() as measurement:
            strict = strict_scores(targets, report["results"])
            if {p["id"]: p for p in strict["pages"]} != {p["id"]: p for p in verified["page_scores"]}:
                raise ValueError("Recomputed original strict page scores differ: " + entry["name"])
            dual = dual_scores(targets, report["results"], strict)
        name = entry["name"]
        write_json(
            output / (name + ".json"),
            {
                "entry": entry,
                "strict": strict,
                "secondary": dual,
                "resources": measurement.summary(),
                "inference_rates": {key: verified[key] for key in ("pages_per_minute", "pages_per_api_usd")},
            },
        )
        result["runs"].append(
            {
                "name": name,
                "strict": strict["totals"],
                "secondary": {key: value for key, value in dual.items() if key != "pages"},
                "resources": measurement.summary(),
            }
        )
        write_json(
            output / "progress.json",
            {"completed": len(result["runs"]), "intended": len(entries), "updated_at": time.time()},
        )
        print(name, json.dumps(dual["counts"], sort_keys=True), flush=True)
    result["code_sha256"] = {
        name: sha(Path(__file__).with_name(name).read_bytes())
        for name in (
            "p003_scoring_audit.py",
            "p003_schema_sensitivity.py",
            "p003_content_alignment.py",
            "p003_report.py",
            "generalization_scoring.py",
        )
    }
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Read only explicit pinned audit inputs and write a fresh ignored result directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    audit(args.plan, args.output)


if __name__ == "__main__":
    main()
