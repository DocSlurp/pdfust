"""Offline private scoring of completed P001 pipeline runs."""

# Heterogeneous frozen artifact schemas are retained without model access.
# ruff: noqa: EM101, TRY003, C901, E501, ISC004
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TypeGuard

from bench.pipeline_scoring import conservation, score_dataset, score_page
from bench.silver import canonical, guard_path, sha

SOURCE_FIELDS = ("id", "pdf_path", "pdf_sha256", "page_number")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("Expected an object artifact")
    return value


def _positive_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        return None
    return float(value)


def _measure(count: int, denominator: object, factor: float = 1) -> float | None:
    number = _positive_number(denominator)
    return count / number * factor if number is not None else None


def _successful_call_models(predictions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group retained admitted calls only; failed ledger attempts are not present."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prediction in predictions:
        for call in prediction.get("calls", []):
            entry = call.get("entry", {})
            requested = entry.get("requested_model")
            model = requested if isinstance(requested, str) and requested else "unknown"
            groups[model].append(entry)
    result = {}
    for model, entries in groups.items():
        reported = [entry.get("provider_reported_usd") for entry in entries]
        accounted = [entry.get("accounted_usd") for entry in entries]
        valid_reported = [value for value in reported if _nonnegative_number(value)]
        valid_accounted = [value for value in accounted if _nonnegative_number(value)]
        complete_accounted = len(valid_accounted) == len(accounted)
        bases = dict(Counter(entry.get("cost_status", "unknown") for entry in entries))
        total = sum(valid_accounted) if complete_accounted else None
        settled = complete_accounted and not any(base in {"reserved", "unknown"} for base in bases)
        result[model] = {
            "calls": len(entries),
            "provider_reported_subtotal_usd": sum(valid_reported),
            "missing_provider_charge_count": len(entries) - len(valid_reported),
            "accounted_usd": total,
            "effective_usd": total if settled else None,
            "cost_bases": bases,
        }
    return result


def _nonnegative_number(value: object) -> TypeGuard[float]:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0


def _source_contract(directory: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    manifest_path = directory / "corpus/manifest.json"
    manifest = _read(manifest_path)
    targets = _read(directory / "corpus/private-targets.json")
    if manifest.get("split") != "DEV":
        raise ValueError("Only explicit DEV inputs may be scored")
    records = manifest["pages"]
    ids = [record["id"] for record in records]
    target_ids = [target["id"] for target in targets["pages"]]
    if len(set(ids)) != len(ids) or len(set(target_ids)) != len(target_ids) or set(ids) != set(target_ids):
        raise ValueError("Manifest and target IDs must match uniquely")
    identity_records = [{key: value for key, value in row.items() if key != "pdf_path"} for row in records]
    identity = sha(canonical({"schema": 1, "pages": identity_records, "targets": targets["pages"]}))
    if manifest["dataset_sha256"] != identity or targets["dataset_sha256"] != identity:
        raise ValueError("Frozen corpus identity does not match complete references")
    checked = set()
    for record in records:
        path = guard_path(Path(record["pdf_path"]))
        if not path.is_absolute():
            raise ValueError("Corpus PDF paths must follow the absolute path convention")
        key = (str(path), record["pdf_sha256"])
        if key not in checked:
            if sha(path.read_bytes()) != record["pdf_sha256"]:
                raise ValueError("Frozen PDF bytes changed")
            checked.add(key)
    return manifest, targets, sha(manifest_path.read_bytes())


def _score_run(path: Path, manifest: dict[str, Any], targets: dict[str, Any], manifest_hash: str) -> dict[str, Any]:
    report = _read(path / "report.json")
    frozen = _read(path / "frozen.json")
    config = report["config"]
    if config != frozen["config"] or frozen["manifest_sha256"] != manifest_hash:
        raise ValueError("Run config or manifest differs from frozen source contract")
    selected = [record for record in manifest["pages"] if not config["pilot"] or record["pilot"]]
    expected = {record["id"]: {key: record[key] for key in SOURCE_FIELDS} for record in selected}
    actual = {record["id"]: record for record in frozen["records"]}
    if len(actual) != len(frozen["records"]) or actual != expected:
        raise ValueError("Frozen records do not match the complete intended cohort")
    private = [target for target in targets["pages"] if target["id"] in expected]
    predictions = report["results"]
    # Unknown/duplicate IDs are rejected by score_dataset; missing outputs remain errors.
    scores = score_dataset(private, predictions)
    by_id = {row["id"]: row for row in predictions}
    target_map = {row["id"]: row for row in private}
    family_members: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in selected:
        family_members[record["family"]].append(target_map[record["id"]])
    families = {
        family: score_dataset(members, [by_id[t["id"]] for t in members if t["id"] in by_id])["totals"]
        for family, members in family_members.items()
    }
    operational, conserved, conservation_available = 0, 0, 0
    for prediction in predictions:
        if prediction.get("status") != "ok":
            continue
        ident = prediction["id"]
        structure_path, markdown_path = path / (ident + "-structure.json"), path / (ident + ".md")
        if not structure_path.is_file() or not markdown_path.is_file():
            raise ValueError("Successful page is missing a complete retained output")
        structure = _read(structure_path)
        if structure["tables"] != prediction["tables"] or structure["unresolved_ids"] != prediction["unresolved_ids"]:
            raise ValueError("Retained output does not match the reported complete state")
        operational += 1
        source = prediction.get("source")
        if source is not None:
            conservation_available += 1
            assigned = structure["unresolved_ids"] + [
                ident for table in structure["tables"] for cell in table["cells"] for ident in cell["source_ids"]
            ]
            conserved += conservation([word["id"] for word in source["words"]], assigned)["exact_conservation"]
    oracle = []
    for target in private:
        prediction = by_id.get(target["id"], {})
        candidates = prediction.get("candidates", [])
        best = max(
            candidates, key=lambda candidate: _oracle_rank(score_page(target, candidate["tables"])), default=None
        )
        oracle.append(
            {"id": target["id"], "status": "ok" if best else "missing", "tables": best["tables"] if best else []}
        )
    positives = [target for target in private if target["structural_scored"] and target["tables"]]
    negatives = [target for target in private if target["structural_scored"] and not target["tables"]]
    positive_scores = score_dataset(positives, [by_id[t["id"]] for t in positives if t["id"] in by_id])["totals"]
    negative_scores = score_dataset(negatives, [by_id[t["id"]] for t in negatives if t["id"] in by_id])["totals"]
    metrics = report["metrics"]
    bases = report.get("cost_bases", {})
    # Never turn reservations or incomplete estimates into complete effective totals.
    effective = report.get("effective_usd")
    if bases.get("reserved", 0):
        effective = None
    exact_positive = positive_scores["exact_page"]
    return {
        "name": path.name,
        "config": config,
        "scores": scores["totals"],
        "positive": positive_scores,
        "negative": negative_scores,
        "families": families,
        "oracle": score_dataset(private, oracle)["totals"],
        "oracle_positive": score_dataset(
            positives, [row for row in oracle if row["id"] in {t["id"] for t in positives}]
        )["totals"],
        "operational_pages": operational,
        "all_errors": len(expected) - operational,
        "page_scores": scores["pages"],
        "conserved_pages": conserved,
        "conservation_available_pages": conservation_available,
        "metrics": metrics,
        "provider_reported_usd": report.get("provider_reported_usd"),
        "missing_provider_charge_count": report.get("missing_provider_charge_count"),
        "accounted_usd": report.get("accounted_usd"),
        "effective_usd": effective,
        "cost_bases": bases,
        "calls": report.get("calls"),
        "successful_call_models": _successful_call_models(predictions),
        "ledger_attempts": report.get("ledger_attempts"),
        "pages_per_minute": _measure(operational, metrics.get("wall_seconds"), 60),
        "pages_per_dollar": _measure(operational, effective),
        "exact_positive_pages_per_minute": _measure(exact_positive, metrics.get("wall_seconds"), 60),
        "exact_positive_pages_per_dollar": _measure(exact_positive, effective),
        "frozen": {
            key: frozen.get(key) for key in ("code_sha256", "python", "platform", "logical_cpus", "concurrency")
        },
    }


def _oracle_rank(score: dict[str, Any]) -> tuple[int, int, int, int]:
    if not score["structural_scored"]:
        return (0, 0, 0, 0)
    return (
        int(score["exact_page"]),
        score["complete_tables"],
        score["correct_cell_slots"],
        -score["false_positive_tables"],
    )


def _fmt(value: object) -> str:
    if value is None:
        return "unknown"
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def _label(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def run(directory: Path, output: Path) -> dict[str, Any]:  # noqa: PLR0912 - complete retained report sections.
    """Score finished runs only, preserving every run artifact and writing one summary."""
    directory, output = guard_path(directory), guard_path(output)
    manifest, targets, manifest_hash = _source_contract(directory)
    paths = sorted(directory.glob("*/report.json"), key=lambda path: (path.stat().st_mtime_ns, path.parent.name))
    if output.name in {"report.json", "frozen.json", "manifest.json", "private-targets.json"} or output.suffix != ".md":
        raise ValueError("Summary must be a separate Markdown artifact")
    frozen_paths = sorted(directory.glob("*/frozen.json"))
    incomplete = []
    for frozen_path in frozen_paths:
        if (frozen_path.parent / "report.json").is_file():
            continue
        frozen = _read(frozen_path)
        config = frozen.get("config", {})
        selected = [record for record in manifest["pages"] if not config.get("pilot", False) or record["pilot"]]
        expected = {record["id"]: {key: record[key] for key in SOURCE_FIELDS} for record in selected}
        frozen_records = frozen.get("records", [])
        actual = {record["id"]: record for record in frozen_records}
        incomplete.append(
            {
                "name": frozen_path.parent.name,
                "config": config,
                "planned_pages": len(frozen_records),
                "result_files": len(list(frozen_path.parent.glob("*-result.json"))),
                "source_contract_matches": frozen.get("manifest_sha256") == manifest_hash
                and len(actual) == len(frozen_records)
                and actual == expected,
            }
        )
    if any(output.is_relative_to(path.parent) for path in frozen_paths):
        raise ValueError("Summary must not overwrite completed run artifacts")
    runs = [_score_run(path.parent, manifest, targets, manifest_hash) for path in paths]
    lines = [
        "# P001 complete-page pipeline comparison",
        "",
        "Offline private scoring after complete pipeline runs. Chronological completed-report order; "
        "each row retains its run name. DEV authored silver supports table/non-table structure only. "
        "Operational output means retained Markdown and complete source-owned state; it does not imply semantic correctness.",
        "",
        f"Dataset SHA-256: `{manifest['dataset_sha256']}`. Manifest bytes SHA-256: `{manifest_hash}`. "
        "The fixed pilot is selected by frozen manifest membership; absent results remain failures. "
        "Full and pilot cohorts have distinct denominators.",
        "",
        "| Run | Cohort | Policy | Model | Gate review model | Image edge | Context rows | Legend | Normalize rotation | OCR empty pages | Gate premise | Output / pages | Exact positive pages | Negative FP pages | All / scored errors |",
        "|---|---|---|---|---|---|---:|---:|---|---|---|---|---:|---:|---:|---:|",
    ]
    for item in runs:
        config, pos, neg = item["config"], item["positive"], item["negative"]
        native = config["policy"] in {"native", "native_text"}
        model = "CPU only" if native else config.get("model", "unknown")
        review_model = config.get("gate_review_model") or "—"
        image_edge = "—" if native else config.get("image_edge", "unknown")
        context_rows = "—" if native else config.get("context_rows", "unknown")
        legend = "—" if native else config.get("legend", "unknown")
        premise = config.get("gate_premise", "unknown") if config["policy"] == "gated" else "—"
        lines.append(
            f"| {_label(item['name'])} | {'pilot' if config['pilot'] else 'full'} | {_label(config['policy'])} | "
            f"{_label(model)} | {_label(review_model)} | {image_edge} | {context_rows} | {legend} | "
            f"{config.get('normalize_rotation', False)} | {config.get('ocr_empty', False)} | {_label(premise)} | "
            f"{item['operational_pages']}/{item['scores']['pages']} | {pos['exact_page']}/{pos['scored_pages']} | "
            f"{neg['false_positive_page']}/{neg['scored_pages']} | {item['all_errors']}/{item['scores']['error']} |"
        )
    lines += [
        "",
        "| Run | Exact scored pages | Complete tables / charged tables | Exact cells / expected tables | Exact spans / expected tables | Correct slots / expected / charged slots | Missing / extra tables | Conserved / checked output pages | Oracle exact positive pages |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in runs:
        score = item["scores"]
        oracle_positive = item["oracle_positive"]["exact_page"]
        lines.append(
            f"| {_label(item['name'])} | {score['exact_page']}/{score['scored_pages']} | "
            f"{score['complete_tables']}/{score['table_denominator']} | {score['exact_table_cells']}/{score['expected_tables']} | "
            f"{score['exact_table_spans']}/{score['expected_tables']} | {score['correct_cell_slots']}/{score['cell_slots']}/{score['penalized_cell_slots']} | "
            f"{score['missing_tables']}/{score['false_positive_tables']} | {item['conserved_pages']}/{item['conservation_available_pages']} | {oracle_positive}/{item['positive']['scored_pages']} |"
        )
    lines += [
        "",
        "| Run | Output p/min | Output p/USD | Exact positive p/min | Exact positive p/USD | Wall s | CPU s | Peak sampled RSS bytes | Provider USD | Missing provider charges | Effective USD | Accounted USD | Cost bases |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in runs:
        keys = (
            "pages_per_minute",
            "pages_per_dollar",
            "exact_positive_pages_per_minute",
            "exact_positive_pages_per_dollar",
        )
        values = [_fmt(item[key]) for key in keys]
        values += [_fmt(item["metrics"].get(key)) for key in ("wall_seconds", "cpu_seconds", "peak_sampled_rss_bytes")]
        values += [
            _fmt(item[key])
            for key in ("provider_reported_usd", "missing_provider_charge_count", "effective_usd", "accounted_usd")
        ]
        lines.append(
            f"| {_label(item['name'])} | "
            + " | ".join(values)
            + f" | {_label(json.dumps(item['cost_bases'], sort_keys=True))} |"
        )
    lines += [
        "",
        "Successful retained calls by requested model:",
        "",
        "Primary and optional review models form one experimental policy; both charges enter the run total. "
        "This breakdown covers only calls retained in completed page results. Failed or parse-rejected attempts "
        "may be absent, so the complete-run ledger-attempt cost totals above remain authoritative. "
        "Reported USD is a known-value subtotal with missing counts, not a complete total when values are missing.",
        "",
        "| Run | Requested model | Successful calls | Reported USD subtotal | Missing reported charges | Effective USD for listed calls | Accounted USD for listed calls | Cost bases |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in runs:
        for model, group in sorted(item["successful_call_models"].items()):
            values = [
                _fmt(group[key])
                for key in (
                    "calls",
                    "provider_reported_subtotal_usd",
                    "missing_provider_charge_count",
                    "effective_usd",
                    "accounted_usd",
                )
            ]
            lines.append(
                f"| {_label(item['name'])} | {_label(model)} | "
                + " | ".join(values)
                + f" | {_label(json.dumps(group['cost_bases'], sort_keys=True))} |"
            )
    lines += [
        "",
        "Candidate oracle coverage uses private references to choose an already-retained complete candidate. "
        "It is reference-informed and unrunnable as an extraction policy; it does not synthesize missing candidates. "
        "Coverage is policy-specific: it scores only alternatives retained by that run. "
        "No output or model was supplied references during inference. Exactness compares complete matrices and spans "
        "after whitespace normalization; extra tables charge both table and cell denominators. "
        "Errors on negative pages remain failures, not correct zero-table pages.",
        "",
        "Source conservation covers extracted snapshot word IDs, not all painted PDF content, Unicode mapping, "
        "visibility, OCR or semantic relations. Natural documents with incomplete references are diagnostic-only. "
        "Headings, lists, forms, equations, images and general document quality are not gold-scored. "
        "See [corpus contract](pipeline-corpus-design.md).",
        "",
        "API cost excludes local electricity and amortization. Positive provider charges and catalog estimates "
        "retain distinct bases; missing provider counts remain visible. Accounted USD can contain reservations, "
        "which are separate from effective charges. Unknown effective totals yield unknown p/USD. "
        "Zero-cost native throughput has no finite p/USD.",
        "",
        "<details>",
        "<summary>Complete per-family structure scores</summary>",
        "",
        "| Run | Family | Scored / diagnostic pages | Exact positive / positives | Negative FP / negatives | Exact scored pages | Errors |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for item in runs:
        for family, score in sorted(item["families"].items()):
            members = [
                row
                for row in manifest["pages"]
                if row["family"] == family and (not item["config"]["pilot"] or row["pilot"])
            ]
            ids = {row["id"] for row in members}
            positive_targets = [
                t for t in targets["pages"] if t["id"] in ids and t["structural_scored"] and t["tables"]
            ]
            positive_ids = {target["id"] for target in positive_targets}
            exact_positive = sum(row["exact_page"] for row in item["page_scores"] if row["id"] in positive_ids)
            lines.append(
                f"| {_label(item['name'])} | {_label(family)} | {score['scored_pages']}/{score['diagnostic_pages']} | "
                f"{exact_positive}/{score['positive_page']} | {score['false_positive_page']}/{score['negative_page']} | "
                f"{score['exact_page']}/{score['scored_pages']} | {score['error']} |"
            )
    lines += [
        "",
        "</details>",
        "",
        "Incomplete frozen runs (not scored):",
        "",
        "No completed report exists for these frozen runs; they may be running or aborted. "
        "Result-file counts are progress evidence only. Accuracy, charges, wall/CPU and RSS remain unknown. "
        "Jobs not yet frozen by the runner are outside this observed inventory.",
        "",
        "| Run | Policy | Model | Gate review model | Planned pages | Result files | Source contract matches |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for item in incomplete:
        config = item["config"]
        model = "CPU only" if config.get("policy") in {"native", "native_text"} else config.get("model", "unknown")
        lines.append(
            f"| {_label(item['name'])} | {_label(config.get('policy', 'unknown'))} | "
            f"{_label(model)} | {_label(config.get('gate_review_model') or '—')} | "
            f"{item['planned_pages']} | {item['result_files']} | {item['source_contract_matches']} |"
        )
    if not incomplete:
        lines.append("| None observed | — | — | — | — | — | — |")
    lines += ["", "Measurement and frozen provenance:", ""]
    for item in runs:
        lines.append(
            f"- `{item['name']}`: {_label(item['metrics'].get('measurement', 'unmeasured'))}; "
            f"frozen environment/code: `{json.dumps(item['frozen'], sort_keys=True)}`. "
            "Overall wall includes API waiting; CPU and RSS cover the current process only. "
            "Remote GPU and separate stage resource totals are unmeasured."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")
    return {
        "dataset_sha256": manifest["dataset_sha256"],
        "runs": runs,
        "incomplete_runs": incomplete,
        "output": str(output),
    }


def main() -> None:
    """Rerun the offline Markdown aggregation without changing completed artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.directory, args.output)
    print(
        json.dumps(
            {"runs": len(result["runs"]), "incomplete_runs": len(result["incomplete_runs"]), "output": result["output"]}
        )
    )


if __name__ == "__main__":
    main()
