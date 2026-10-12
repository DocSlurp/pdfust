"""Offline retained-response counterfactual; no transport, cache or provider call."""

# ruff: noqa: PLC0415, EM101, TRY003, PLR2004
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import time
from pathlib import Path
from typing import Any

from bench.pipeline_vision_repair import VERSION, repair
from bench.silver_structure import process_peak_rss


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evaluate(directories: list[Path], manifest_path: Path, target_path: Path) -> dict[str, Any]:
    """Prepare every source-only repair before opening references and scoring."""
    import pdfust

    adapter = importlib.import_module("bench.pipeline_vision_transcription")
    scorer = importlib.import_module("bench.generalization_scoring")
    manifest = json.loads(manifest_path.read_text())
    source_records = {row["id"]: row for row in manifest["pages"]}
    start, cpu = time.perf_counter(), time.process_time()
    cohorts: list[dict[str, Any]] = []
    for directory in directories:
        frozen = json.loads((directory / "frozen.json").read_text())
        records = frozen["records"]
        if len(records) != 16 or {row["id"] for row in records} != set(source_records):
            raise ValueError("Counterfactual requires every retained response for the exact sixteen-page manifest")
        snapshot = directory / "code/pipeline_vision_transcription.py"
        if adapter.__file__ is None:
            raise ValueError("Strict adapter has no retained source path")
        adapter_path = Path(adapter.__file__)
        if _sha(snapshot.read_bytes()) != _sha(adapter_path.read_bytes()):
            raise ValueError("Strict adapter differs from the retained run snapshot")
        pages: list[dict[str, Any]] = []
        for record in records:
            identifier = record["id"]
            response_path = directory / (identifier + "-response-0.json")
            original_bytes = response_path.read_bytes()
            raw = json.loads(original_bytes)
            source = source_records[identifier]
            with pdfust.open(source["pdf_path"]) as document:
                viewport = list(document[source.get("page_number", 0)].rect)
            row: dict[str, Any] = {
                "id": identifier,
                "response_sha256": _sha(original_bytes),
                "response_path": str(response_path),
            }
            try:
                row["strict"] = {"id": identifier, "status": "ok", **adapter.parse(raw, viewport)}
            except ValueError as error:
                row["strict"] = {"id": identifier, "status": "error", "tables": [], "error": str(error)}
            try:
                changed = repair(raw, viewport)
                row["counterfactual"] = {"id": identifier, "status": "ok", **changed["parsed"]}
                row["repair"] = {key: value for key, value in changed.items() if key != "parsed"}
            except ValueError as error:
                row["counterfactual"] = {"id": identifier, "status": "error", "tables": [], "error": str(error)}
                row["repair"] = {"repaired": False, "edits": [], "refused": True}
            if original_bytes != response_path.read_bytes() or raw != json.loads(original_bytes):
                raise ValueError("Retained raw response was changed")
            pages.append(row)
        cohort: dict[str, Any] = {
            "directory": str(directory),
            "version": VERSION,
            "pages": pages,
            "provider_calls": 0,
            "provider_cache_hit": False,
            "new_paid_run": False,
        }
        (directory / "counterfactual-format-repair-before-score.json").write_text(
            json.dumps(cohort, ensure_ascii=False, indent=2) + "\n"
        )
        cohorts.append(cohort)
    # All repairs, refusals and provenance are fixed before any gold access.
    targets = json.loads(target_path.read_text())
    for cohort in cohorts:
        cohort["strict_score"] = scorer.score_dataset(targets, [row["strict"] for row in cohort["pages"]])
        cohort["counterfactual_score"] = scorer.score_dataset(
            targets, [row["counterfactual"] for row in cohort["pages"]]
        )
        strict = {row["id"]: row for row in cohort["strict_score"]["pages"]}
        counterfactual = {row["id"]: row for row in cohort["counterfactual_score"]["pages"]}
        cohort["false_positive_changes"] = [
            {
                "id": identifier,
                "before": strict[identifier]["false_positive_tables"],
                "after": counterfactual[identifier]["false_positive_tables"],
            }
            for identifier in strict
            if strict[identifier]["false_positive_tables"] != counterfactual[identifier]["false_positive_tables"]
        ]
        (Path(cohort["directory"]) / "counterfactual-format-repair-authoritative-scored.json").write_text(
            json.dumps(cohort, ensure_ascii=False, indent=2) + "\n"
        )
    peak, tool = process_peak_rss()
    return {
        "schema": 1,
        "version": VERSION,
        "scorer": "bench.generalization_scoring",
        "cohorts": cohorts,
        "scope": "postprocessing diagnostic reusing every retained response; no Pmin or cache-hit claim",
        "target_sha256": _sha(target_path.read_bytes()),
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": peak,
        "rss_tool": tool,
    }


def main() -> None:
    """Require explicit retained run and reference paths for offline evaluation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.run, args.manifest, args.targets)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
