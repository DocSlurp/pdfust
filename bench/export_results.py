"""Collect experiment and test results into one dated folder for later analysis.

    python -m bench.export_results [--output DIR]

Writes flat CSV tables (one row per arm × level, page, document × level,
quirk case and repair arm), copies the raw per-page model records, audit
JSON, dataset manifests, cost ledger subsets, GPU rental records and the
committed Markdown reports, plus a README index. The folder lives under the
ignored artifact tree; held-out silver data is never read.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from bench.silver import guard_path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "bench/results/pdf-master-artifacts"
WILD = ARTIFACTS / "wild-v1"
VISION_DIRECTORIES = ("vision-v1", "vision-raster-v1", "vision-open-v1")
REPORTS = (
    "bench/results/wild-v1-latest.md", "bench/results/wild-v1-models.md", "bench/DATASET_REALISM_REVIEW.md",
    "bench/P003_RESEARCH_EXTENSION.md", "bench/REAL_WORLD_V2.md", "bench/WILD_CORPUS.md",
)
GPU_STATE = Path.home() / ".local/state/pdfust/vast"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        fields.extend(key for key in row if key not in fields)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _copy(source: Path, target: Path) -> bool:
    source = guard_path(source)
    if not source.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        shutil.copy2(source, target)
    return True


def vision_tables(out: Path) -> dict[str, int]:
    """Arm × level scores and per-page records for every vision experiment."""
    from bench import wild_vision  # noqa: PLC0415 - scoring only.

    level_rows: list[dict[str, Any]] = []
    page_rows: list[dict[str, Any]] = []
    for name in VISION_DIRECTORIES:
        directory = WILD / name
        if not directory.is_dir():
            continue
        scores = wild_vision.evaluate(directory)
        for arm, result in scores.items():
            for level, values in result["levels"].items():
                level_rows.append({"experiment": name, "arm": arm, "level": level, **values})
        for path in sorted(directory.glob("*/*--p*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            usage, entry = record.get("usage") or {}, record.get("entry") or {}
            page_rows.append({
                "experiment": name, "arm": path.parent.name, "model": record.get("model"),
                "doc_id": record.get("doc_id"), "level": record.get("level"), "page": record.get("page"),
                "status": record.get("status"), "client_seconds": record.get("client_seconds"),
                "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                "accounted_usd": entry.get("accounted_usd"), "cost_status": entry.get("cost_status"),
                "served_model": entry.get("served_model"), "provider": entry.get("provider"),
                "error": record.get("error"), "markdown_chars": len(record.get("markdown") or ""),
            })
        _copy(directory, out / "vision/raw" / name)
    return {"vision/arm_level_scores.csv": _write_csv(out / "vision/arm_level_scores.csv", level_rows),
            "vision/pages.csv": _write_csv(out / "vision/pages.csv", page_rows)}


def audit_tables(out: Path) -> dict[str, int]:
    """Native extraction and OCR audit summaries per level, document and quirk case."""
    audit = json.loads((WILD / "audit.json").read_text(encoding="utf-8"))
    levels = [{"level": level, **values} for level, values in audit["summary"].items()]
    rows: list[dict[str, Any]] = []
    quirks: list[dict[str, Any]] = []
    for row in audit["audits"]:
        tables = row.get("tables", [])
        flat = {
            "doc_id": row.get("doc_id"), "level": row.get("level"), "family": row.get("family"),
            "producer": row.get("producer"), "languages": " ".join(row.get("languages", [])),
            "error": row.get("error"), "page_count": row.get("page_count"), "text_chars": row.get("text_chars"),
            "text_f1": (row.get("text") or {}).get("f1"), "text_nfkc_f1": (row.get("text_nfkc") or {}).get("f1"),
            "markdown_f1": (row.get("markdown") or {}).get("f1"),
            "image_only_text_recovered": row.get("image_only_text_recovered"),
            "tables": len(tables), "tables_exact": sum(bool(t.get("exact")) for t in tables),
            "table_cell_recall_mean": (sum(t["cell_recall"] for t in tables) / len(tables)) if tables else None,
            "wall_seconds": (row.get("resources") or {}).get("wall_seconds"),
        }
        (quirks if str(row.get("level", "")).startswith("Q:") else rows).append(
            {**flat, "quirk_family": row.get("quirk_family")} if str(row.get("level", "")).startswith("Q:") else flat
        )
    for name in ("audit.json", "audit.md", "ocr-report.json", "ocr-adaptive-report.json", "ocr-fill-report.json"):
        _copy(WILD / name, out / "audit" / name)
    return {"audit/levels.csv": _write_csv(out / "audit/levels.csv", levels),
            "audit/documents.csv": _write_csv(out / "audit/documents.csv", rows),
            "audit/quirk_cases.csv": _write_csv(out / "audit/quirk_cases.csv", quirks)}


def repair_tables(out: Path) -> dict[str, int]:
    """Decision-model local repair scores (synthetic Layer 3 and wild-v1 transfer)."""
    rows = []
    runs = ARTIFACTS / "pipeline-p003/extension-v1/runs"
    for path in sorted(runs.glob("extension-v1-*/local-score-v1.json")):
        score = json.loads(path.read_text(encoding="utf-8"))
        config = score["config"]
        damaged = score["baseline_raw_scenario"]["strict"]["totals"]
        composed = score["composed_with_baseline_retention"]["strict"]["totals"]
        strict, v2 = score["comparisons_by_metric"]["strict"], score["comparisons_by_metric"]["v2"]
        rows.append({
            "run_id": config["run_id"], "model": config["model"], "scenario": config["scenario"],
            "mechanism": config["mechanism"], "intended_pages": score["intended_pages"],
            "status_counts": json.dumps(score["status_counts"]),
            "damaged_exact_pages": damaged["exact_page"], "repaired_exact_pages": composed["exact_page"],
            "strict_improved": strict.get("improved", 0), "strict_regressed": strict.get("regressed", 0),
            "v2_improved": v2.get("improved", 0), "v2_regressed": v2.get("regressed", 0),
            "exact_cells_before": damaged["strict_exact_cells"], "exact_cells_after": composed["strict_exact_cells"],
            "expected_cells": composed["expected_cells"],
            "effective_usd": score["costs"].get("effective_usd"),
            "unresolved_reserved_usd": score["costs"].get("unresolved_reserved_usd"),
        })
    return {"decisions/local_repair.csv": _write_csv(out / "decisions/local_repair.csv", rows)}


def cost_tables(out: Path) -> dict[str, int]:
    """Ledger entries for this research round plus GPU rental records."""
    ledger = json.loads((ARTIFACTS / "decisions/ledger.json").read_text(encoding="utf-8"))
    rows = [
        {key: entry.get(key) for key in ("index", "tag", "requested_model", "served_model", "provider",
                                         "accounted_usd", "provider_reported_usd", "cost_status", "elapsed_ms",
                                         "concurrent_state", "started_at", "completed_at")}
        for entry in ledger["requests"] if str(entry.get("tag", "")).startswith("P003/extension-v1-")
    ]
    header = {key: value for key, value in ledger.items() if key != "requests"}
    (out / "costs").mkdir(parents=True, exist_ok=True)
    (out / "costs/ledger_header.json").write_text(json.dumps(header, indent=1), encoding="utf-8")
    (out / "costs/gpu").mkdir(parents=True, exist_ok=True)
    for name in ("open-ocr-v1.run1.json", "open-ocr-v1.run2.json", "open-ocr-v1.json", "run-open-ocr.log",
                 "run-rest.log", "run-deepseek.log", "run-deepseek2.log"):
        if (GPU_STATE / name).exists():
            shutil.copy2(GPU_STATE / name, out / "costs/gpu" / name)
    return {"costs/ledger_extension_v1.csv": _write_csv(out / "costs/ledger_extension_v1.csv", rows)}


def dataset_copies(out: Path) -> dict[str, int]:
    """Manifests and truth for the DEV corpora (PDFs stay in place; paths are recorded)."""
    copied = 0
    sources = {
        "datasets/wild-v1/truth": WILD / "docs",
        "datasets/wild-v1/quirks-manifest.json": WILD / "quirks/manifest.json",
        "datasets/wild-v1/photos.json": WILD / "photos/photos.json",
        "datasets/wild-v2/build-report.json": ARTIFACTS / "wild-v2/docs/build-report.json",
        "datasets/real-world-v2/manifest.json": ARTIFACTS / "real-world-v2/manifest.json",
        "datasets/real-world-v2/truth": ARTIFACTS / "real-world-v2/truth",
        "datasets/real-world-v2/health.md": ARTIFACTS / "real-world-v2/health.md",
        "datasets/wild-v1-repair/manifest.json": WILD / "repair-v1/manifest.json",
    }
    for target, source in sources.items():
        if source.is_dir():
            for truth in source.glob("*/truth.json"):
                copied += _copy(truth, out / target / truth.parent.name / "truth.json")
            for truth in source.glob("*.json"):
                copied += _copy(truth, out / target / truth.name)
        else:
            copied += _copy(source, out / target)
    raster = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((WILD / "variants").glob("*/raster.json"))]
    (out / "datasets/wild-v1/raster.json").write_text(json.dumps(raster, indent=1), encoding="utf-8")
    return {"datasets (files copied)": copied + 1}


def test_results(out: Path) -> dict[str, int]:
    """Run the test suite once and keep its JUnit XML and summary."""
    target = out / "tests"
    target.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(  # noqa: S603 - fixed local pytest invocation.
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={target / 'junit.xml'}"],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=3600,
    )
    (target / "summary.txt").write_text(result.stdout[-20000:] + result.stderr[-5000:], encoding="utf-8")
    return {"tests/junit.xml": 1}


def main() -> None:
    """Build the export folder and its README index."""
    parser = argparse.ArgumentParser(description=__doc__)
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%MZ")
    parser.add_argument("--output", type=Path, default=ARTIFACTS / f"results-export-{stamp}")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    out = guard_path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for step in (vision_tables, audit_tables, repair_tables, cost_tables, dataset_copies):
        counts.update(step(out))
    for report in REPORTS:
        if _copy(ROOT / report, out / "reports" / Path(report).name):
            counts[f"reports/{Path(report).name}"] = 1
    if not args.skip_tests:
        counts.update(test_results(out))
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,  # noqa: S607
                            check=False).stdout.strip()
    lines = [
        "# Experiment and test results export", "",
        f"Exported {stamp} from commit `{commit}`. DEV data only; held-out silver is excluded.", "",
        "| File | Rows / items |", "|---|---:|",
        *(f"| `{name}` | {count} |" for name, count in counts.items()), "",
        "- `vision/`: hosted and open-model page transcription; `raw/` holds every per-page record.",
        "- `audit/`: pdfust native extraction and OCR policies per level, document and quirk case.",
        "- `decisions/`: decision-model local repair arms (synthetic Layer 3 and wild-v1 transfer).",
        "- `costs/`: ledger rows for `P003/extension-v1-*` requests and GPU rental logs.",
        "- `datasets/`: truth and manifests; source PDFs stay under `bench/results/pdf-master-artifacts/`.",
        "- `reports/`: Markdown summaries; `tests/`: JUnit XML and pytest summary.",
    ]
    (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)
    print(json.dumps(counts, indent=1))


if __name__ == "__main__":
    main()
