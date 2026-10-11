"""Rescore pinned incremental table outputs without inherited baseline credit."""

# ruff: noqa: EM101, TRY003, PLC0415, C901, PLR0912
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "p003-additional-incremental-dual-score-v1"
CODE_FILES = (
    "p003_additional_incremental_audit.py",
    "p003_scoring_audit.py",
    "p003_schema_sensitivity.py",
    "p003_content_alignment.py",
    "p003_span_content.py",
    "p003_report.py",
    "generalization_scoring.py",
    "p003_decision_evidence.py",
    "p003_geometry_diagram_verification.py",
    "silver.py",
    "pipeline_run.py",
    "generalization_vision_regions.py",
)


def primary(report: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    """Credit only selected or actually changed complete table outputs."""
    from bench.p003_decision_evidence import confirmed_candidate_predictions
    from bench.p003_geometry_diagram_verification import quality_predictions
    from bench.silver import canonical

    processor = report["config"].get("processor")
    if processor == "p003_candidate_choice":
        rows = confirmed_candidate_predictions(report)
        if rows is None:
            raise ValueError("Missing candidate view")
        return rows, "selected candidate crops only; atomic failures and abstention zero"
    if processor == "p003_geometry_diagram":
        return quality_predictions(report), "selected disjoint complete crops, including operational partial pages"
    if processor == "p003_structure_admission":
        return report["results"], "admitted source-owned tables only; rejection and failure zero"
    if processor != "p003_boundary_repair":
        raise ValueError("Unsupported additional incremental processor")
    rows = []
    for page in report["results"]:
        selected, joins, changed_regions = [], 0, 0
        if page.get("status") == "ok" and page.get("repair_status") == "completed":
            whole = {canonical({k: v for k, v in t.items() if k != "bbox"}): t for t in page["tables"]}
            for region in page.get("repair_regions", []):
                if region.get("repair_status") != "completed":
                    continue
                original = region["original_state"]
                updated = region["updated_state"]
                applied = region["audit"].get("joined", [])
                if not applied or canonical(original) == canonical(updated):
                    continue
                joins += len(applied)
                changed_regions += 1
                old = {canonical(t) for t in original["tables"]}
                for table in updated["tables"]:
                    key = canonical(table)
                    if key not in old:
                        if key not in whole:
                            raise ValueError("Changed complete table absent from retained composition")
                        selected.append(whole[key])
        if len({canonical(t) for t in selected}) != len(selected):
            raise ValueError("Duplicate changed table attribution")
        rows.append({**page, "status": "ok", "tables": selected,
                     "applied_join_count": joins, "changed_region_count": changed_regions,
                     "original_operational_status": page.get("status")})
    return rows, "changed complete tables from applied model joins; frozen source/geometry included"


def admit(entry: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], str]:
    """Pin prior independent source/output receipt and rebuild primary states before gold."""
    from bench.p003_scoring_audit import pinned
    from bench.silver import canonical, guard_path, sha

    report = pinned(entry["report"], entry["report_sha256"])
    evaluation = pinned(entry["evaluation"], entry["evaluation_sha256"])
    frozen = pinned(entry["frozen"], entry["frozen_sha256"])
    manifest = pinned(entry["run_manifest"], entry["run_manifest_sha256"])
    if len(evaluation.get("runs", [])) != 1:
        raise ValueError("Exactly one prior independent replay required")
    verified = evaluation["runs"][0]
    if not verified["evaluation_scope"].startswith("incremental "):
        raise ValueError("Incremental scope required; complete-pipeline audit stays separate")
    if verified["report_sha256"] != entry["report_sha256"]:
        raise ValueError("Prior source/output replay receipt differs")
    if (
        verified["manifest_sha256"] != entry["run_manifest_sha256"]
        or frozen["manifest_sha256"] != entry["run_manifest_sha256"]
    ):
        raise ValueError("Manifest identities differ")
    if report["config"] != frozen["config"]:
        raise ValueError("Frozen configuration differs")
    ids = [p["id"] for p in manifest["pages"]]
    rows = report["results"]
    if len(ids) != len(set(ids)) or len(rows) != len(ids) or {p["id"] for p in rows} != set(ids):
        raise ValueError("All intended unique pages required")
    if len(frozen["records"]) != len(ids) or {p["id"] for p in frozen["records"]} != set(ids):
        raise ValueError("Frozen source inventory incomplete")
    artifacts = verified["artifacts"]
    if len(artifacts) != len(ids) or {p["id"] for p in artifacts} != set(ids):
        raise ValueError("Independent output inventory incomplete")
    by_id = {p["id"]: p for p in rows}
    directory = Path(entry["report"]).parent
    for receipt in artifacts:
        page = by_id[receipt["id"]]
        data = guard_path(directory / (page["id"] + "-result.json")).read_bytes()
        if sha(data) != receipt["result_sha256"] or json.loads(data) != page:
            raise ValueError("Actual page output differs from independent receipt/report")
        if sha(canonical(page.get("tables", []))) != receipt["tables_sha256"]:
            raise ValueError("Retained table bytes differ")
        source_sha = sha(canonical(page["source"])) if page.get("source") is not None else None
        if source_sha != receipt["source_sha256"]:
            raise ValueError("Retained source differs")
    predictions, quality_key = primary(report)
    if sha(canonical(predictions)) != entry["primary_predictions_sha256"]:
        raise ValueError("Primary attribution differs from pinned preparation")
    return report, verified, predictions, quality_key


def audit(plan: Path, output: Path, *, plan_sha256: str, trusted_code: Path) -> dict[str, Any]:
    """Admit every output before reference access, then compare exact original primary scores."""
    from bench.generalization_report import load_corpus
    from bench.p003_report import strict_scores
    from bench.p003_scoring_audit import dual_scores, pinned
    from bench.pipeline_run import Resources
    from bench.silver import guard_path, sha, write_json

    authority = json.loads(guard_path(trusted_code).read_bytes())
    for name in CODE_FILES:
        if authority.get(name) != sha(Path(__file__).with_name(name).read_bytes()):
            raise ValueError("Independent current helper authority differs: " + name)
    declaration = pinned(str(plan), plan_sha256)
    entries = declaration["entries"]
    if not entries or len({e["name"] for e in entries}) != len(entries):
        raise ValueError("Nonempty unique explicit inventory required")
    admitted = [admit(entry) for entry in entries]
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh output required")
    output.mkdir(parents=True)
    corpora = {}
    result: dict[str, Any] = {
        "version": VERSION,
        "plan_sha256": sha(plan.read_bytes()),
        "runs": [],
        "new_api_calls": 0,
        "originals_changed": False,
        "fresh_pipeline_throughput": None,
        "admission_basis": ("Pinned prior independent source/wire/output replay receipts; "
            "no archived execution"),
    }
    for entry, (admitted_report, verified, predictions, key) in zip(entries, admitted, strict=True):
        corpus = entry["corpus"]
        if corpus not in corpora:
            pinned(str(Path(corpus) / "manifest.json"), entry["corpus_manifest_sha256"])
            pinned(str(Path(corpus) / "private-targets.json"), entry["targets_sha256"])
            corpora[corpus] = load_corpus(guard_path(Path(corpus)))
        manifest, targets = corpora[corpus]
        if manifest["dataset_sha256"] != verified["dataset_sha256"]:
            raise ValueError("Corpus differs from verified source")
        with Resources() as resource:
            strict = strict_scores(targets["pages"], predictions)
            legacy_predictions = (predictions if entry["family"] == "diagram" else admitted_report["results"])
            legacy = strict_scores(targets["pages"], legacy_predictions)
            if legacy["totals"] != verified["scores"] or {p["id"]: p for p in legacy["pages"]} != {
                p["id"]: p for p in verified["page_scores"]
            }:
                raise ValueError("Historical strict witnesses differ: " + entry["name"])
            dual = dual_scores(targets["pages"], predictions, strict)
        row = {
            "name": entry["name"],
            "family": entry["family"],
            "primary_scope": key,
            "legacy_strict": legacy["totals"],
            "operational_errors": sum(p.get("status") != "ok" for p in admitted_report["results"]),
            "incremental_costs": verified.get("costs"),
            "incremental_rates": {k: verified.get(k) for k in (
                "incremental_attempted_pages_per_minute", "incremental_attempted_pages_per_api_usd")},
            "strict": strict["totals"],
            "secondary": {k: v for k, v in dual.items() if k != "pages"},
            "resources": resource.summary(),
            "inference_rates": None,
        }
        write_json(
            output / (entry["name"] + ".json"),
            {"entry": entry, "primary_predictions": predictions, "strict": strict,
             "historical_strict": legacy, "secondary": dual, "summary": row},
        )
        result["runs"].append(row)
        write_json(output / "progress.json", {"completed": len(result["runs"]), "intended": len(entries)})
    result["code_sha256"] = {n: sha(Path(__file__).with_name(n).read_bytes()) for n in CODE_FILES}
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Run only an explicit pinned plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--trusted-code", required=True, type=Path)
    args = parser.parse_args()
    audit(args.plan, args.output, plan_sha256=args.plan_sha256, trusted_code=args.trusted_code)


if __name__ == "__main__":
    main()
