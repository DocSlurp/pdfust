"""Score explicitly pinned historical P001 outputs with separate old and current metrics."""

# ruff: noqa: EM101, TRY003, C901, PLC0415, PLR0912
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CODE_FILES = (
    "p003_p001_rescore.py",
    "pipeline_scoring.py",
    "pipeline_report.py",
    "pipeline_assembly.py",
    "generalization_scoring.py",
    "p003_report.py",
    "p003_scoring_audit.py",
    "p003_schema_sensitivity.py",
    "p003_content_alignment.py",
    "p003_span_content.py",
    "silver.py",
    "pipeline_run.py",
    "generalization_report.py",
)
TABLE_COLUMNS = 9
EXPECTED_RUNS = 56
VERSION = "p003-p001-retained-output-dual-score-v1"


def historical_rows(text: str) -> dict[str, dict[str, int]]:
    """Read original published counts, without treating that report as runtime authentication."""
    start = text.index("| Run | Exact scored pages |")
    end = text.index("| Run | Output p/min |", start)
    result = {}
    for line in text[start:end].splitlines():
        cells = [s.strip() for s in line.split("|")[1:-1]]
        if len(cells) != TABLE_COLUMNS or cells[0] in {"Run", "---"} or cells[0].startswith("-"):
            continue
        parts = [[int(n.strip()) for n in c.split("/")] for c in cells[1:7]]
        result[cells[0]] = {
            "exact_page": parts[0][0],
            "scored_pages": parts[0][1],
            "complete_tables": parts[1][0],
            "table_denominator": parts[1][1],
            "exact_table_cells": parts[2][0],
            "exact_table_spans": parts[3][0],
            "correct_cell_slots": parts[4][0],
            "cell_slots": parts[4][1],
            "penalized_cell_slots": parts[4][2],
            "missing_tables": parts[5][0],
            "false_positive_tables": parts[5][1],
        }
    return result


def score_outputs(targets: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep the historical slot scorer beside mapped anchor strict and tolerant diagnostics."""
    from bench.p003_report import strict_scores
    from bench.p003_scoring_audit import dual_scores
    from bench.pipeline_scoring import score_dataset

    historical = score_dataset(targets, predictions)
    mapped = strict_scores(targets, predictions)
    return {
        "historical_strict": historical,
        "mapped_strict": mapped,
        "secondary": dual_scores(targets, predictions, mapped),
    }


def admit(entry: dict[str, Any], manifest: dict[str, Any], manifest_sha: str) -> dict[str, Any]:
    """Re-admit literal output/source hashes; do not claim historical request replay."""
    from bench.p003_scoring_audit import pinned
    from bench.pipeline_report import SOURCE_FIELDS, _render_markdown, _verify_markdown_renderer
    from bench.silver import canonical, guard_path, sha

    directory = guard_path(Path(entry["directory"]))
    report = pinned(str(directory / "report.json"), entry["report_sha256"])
    frozen = pinned(str(directory / "frozen.json"), entry["frozen_sha256"])
    if report["config"] != frozen["config"] or report["config"] != entry["config"]:
        raise ValueError("Historical config differs")
    if frozen["manifest_sha256"] != manifest_sha or frozen["code_sha256"] != entry["runtime_code_sha256"]:
        raise ValueError("Historical frozen identity differs")
    records = [r for r in manifest["pages"] if not report["config"]["pilot"] or r["pilot"]]
    expected = {r["id"]: {k: r[k] for k in SOURCE_FIELDS} for r in records}
    if {r["id"]: r for r in frozen["records"]} != expected or len(frozen["records"]) != len(expected):
        raise ValueError("Historical frozen cohort differs")
    for filename, digest in entry["runtime_code_sha256"].items():
        if Path(filename).name != filename:
            raise ValueError("Historical code filename must be a basename")
        code_path = directory / "code" / filename
        if filename in entry["runtime_missing_archives"]:
            if code_path.exists():
                raise ValueError("Historical missing-archive provenance changed")
        elif sha(guard_path(code_path).read_bytes()) != digest:
            raise ValueError("Historical archived source bytes changed")
    rows = report["results"]
    if len(rows) != len(expected) or {r["id"] for r in rows} != set(expected):
        raise ValueError("Complete unique output inventory required")
    if entry["page_ids"] != [r["id"] for r in records]:
        raise ValueError("Pinned selected cohort differs")
    artifacts = {a["id"]: a for a in entry["artifacts"]}
    if len(artifacts) != len(expected) or set(artifacts) != set(expected):
        raise ValueError("Output receipt inventory differs")
    for row in rows:
        ident = row["id"]
        a = artifacts[ident]
        actual = pinned(str(directory / (ident + "-result.json")), a["result_sha256"])
        if actual != row or sha(canonical(row.get("tables", []))) != a["tables_sha256"]:
            raise ValueError("Actual output differs from pinned report")
        source_sha = sha(canonical(row["source"])) if row.get("source") is not None else None
        if source_sha != a["source_sha256"]:
            raise ValueError("Retained source changed")
        if row["status"] == "ok":
            state = pinned(str(directory / (ident + "-structure.json")), a["structure_sha256"])
            markdown = guard_path(directory / (ident + ".md")).read_bytes()
            if sha(markdown) != a["markdown_sha256"] or _render_markdown(row["source"], state).encode() != markdown:
                raise ValueError("Complete source-owned Markdown changed")
            if state["tables"] != row["tables"] or state["unresolved_ids"] != row["unresolved_ids"]:
                raise ValueError("Complete structure differs from output")
    if _verify_markdown_renderer(directory, frozen) != entry["renderer_source_status"]:
        raise ValueError("Historical renderer status differs")
    return report


def audit(plan: Path, output: Path, *, plan_sha256: str, trusted_code: Path) -> dict[str, Any]:
    """Re-admit all sources/outputs before labels, using independently approved current scorers."""
    from bench.generalization_report import load_corpus
    from bench.p003_scoring_audit import pinned
    from bench.pipeline_report import _measure
    from bench.pipeline_run import Resources
    from bench.silver import guard_path, sha, write_json

    authority = json.loads(guard_path(trusted_code).read_bytes())
    if set(authority) != set(CODE_FILES):
        raise ValueError("Exact independent scorer authority required")
    for f in CODE_FILES:
        if authority[f] != sha(Path(__file__).with_name(f).read_bytes()):
            raise ValueError("Current scorer differs from independent authority: " + f)
    declaration = pinned(str(plan), plan_sha256)
    corpus = guard_path(Path(declaration["corpus"]))
    manifest = pinned(str(corpus / "manifest.json"), declaration["manifest_sha256"])
    if manifest["split"] != "DEV" or manifest["dataset_sha256"] != declaration["dataset_sha256"]:
        raise ValueError("Explicit historical DEV corpus required")
    source_report = guard_path(Path(declaration["source_report"]))
    if sha(source_report.read_bytes()) != declaration["source_report_sha256"]:
        raise ValueError("Original historical score report changed")
    previous = historical_rows(source_report.read_text())
    entries = declaration["entries"]
    if (
        len(entries) != EXPECTED_RUNS
        or len({e["name"] for e in entries}) != EXPECTED_RUNS
        or set(previous) != {e["name"] for e in entries}
    ):
        raise ValueError("Exactly the 56 declared historical runs required")
    origins = pinned(declaration["git_origins"], declaration["git_origins_sha256"])
    for entry in entries:
        authenticated = all(
            digest in origins["runtime_and_scorer_origins"].get(filename, {})
            for filename, digest in entry["runtime_code_sha256"].items()
        )
        if authenticated != entry["runtime_all_git_authenticated"]:
            raise ValueError("Runtime Git provenance label differs")
    reports = [admit(e, manifest, declaration["manifest_sha256"]) for e in entries]
    # Only now open construction references; never execute historical artifact code.
    pinned(str(corpus / "private-targets.json"), declaration["targets_sha256"])
    _, targets = load_corpus(corpus)
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh output required")
    output.mkdir(parents=True)
    result: dict[str, Any] = {
        "version": VERSION,
        "plan_sha256": sha(plan.read_bytes()),
        "code_sha256": authority,
        "runs": [],
        "new_api_calls": 0,
        "originals_changed": False,
        "scope": "New metrics of pinned retained outputs; no contemporaneous inference/request replay claim",
    }
    for entry, report in zip(entries, reports, strict=True):
        ids = set(entry["page_ids"])
        selected = [t for t in targets["pages"] if t["id"] in ids]
        with Resources() as resource:
            scores = score_outputs(selected, report["results"])
            old = scores["historical_strict"]["totals"]
            if any(old[k] != v for k, v in previous[entry["name"]].items()):
                raise ValueError("Original historical strict counts differ: " + entry["name"])
        operational = sum(p["status"] == "ok" for p in report["results"])
        wall = report["metrics"].get("wall_seconds")
        effective = report.get("effective_usd")
        if any(report.get("cost_bases", {}).get(s, 0) for s in ("unknown", "reserved")):
            effective = None
        summary = {
            "name": entry["name"],
            "config": report["config"],
            "historical_strict": old,
            "mapped_strict": scores["mapped_strict"]["totals"],
            "secondary": {k: v for k, v in scores["secondary"].items() if k != "pages"},
            "runtime_all_git_authenticated": entry["runtime_all_git_authenticated"],
            "renderer_source_status": entry["renderer_source_status"],
            "resources": resource.summary(),
            "original_inference": {
                "operational_pages": operational,
                "all_errors": len(ids) - operational,
                "effective_usd": effective,
                "provider_reported_usd": report.get("provider_reported_usd"),
                "cost_bases": report.get("cost_bases", {}),
                "metrics": report["metrics"],
                "pages_per_minute": _measure(operational, wall, 60),
                "pages_per_api_usd": _measure(operational, effective),
            },
        }
        write_json(output / (entry["name"] + ".json"), {"entry": entry, "scores": scores, "summary": summary})
        result["runs"].append(summary)
        write_json(output / "progress.json", {"completed": len(result["runs"]), "intended": 56})
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Run an explicitly approved historical-output plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--trusted-code", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    audit(args.plan, args.output, plan_sha256=args.plan_sha256, trusted_code=args.trusted_code)


if __name__ == "__main__":
    main()
