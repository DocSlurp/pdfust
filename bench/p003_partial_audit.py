"""Authenticate retained matrix runs and score an explicit partial-table contract."""

# Benchmark JSON records are heterogeneous and private helper reuse is deliberate.
# ruff: noqa: EM101, TRY003, SLF001
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import p003_candidate_run as candidate
from bench import p003_partial_tables as partial
from bench.generalization_report import load_corpus
from bench.p003_report import strict_scores
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json


def audit(baseline: Path, trusted: Path, corpus: Path, output: Path) -> dict[str, Any]:
    """Freeze all fragment predictions before loading any DEV scoring references."""
    baseline, output = guard_path(baseline), guard_path(output)
    reviewed = tuple(candidate.ROOT_REVIEWED_PARSER_SHA256)
    with Resources() as resources:
        frozen, report, _code = candidate.authenticate(
            baseline, candidate._read(trusted), reviewed_parser_sha256=reviewed,
        )
        if frozen["config"].get("transcription_representation", "legacy") != "legacy":
            raise ValueError("Partial audit requires original matrix representation")
        output.mkdir(parents=True, exist_ok=False)
        predictions, evidence = [], []
        for row in report["results"]:
            prediction = {"id": row["id"], "status": row["status"], "tables": deepcopy(row["tables"])}
            item: dict[str, Any] = {"id": row["id"], "original_status": row["status"], "partial": False}
            if row["status"] != "ok" and row.get("viewport") is not None:
                for region in row.get("transcription_regions", []):
                    response = region.get("transcription_response")
                    if response is not None:
                        path = baseline / f"{row['id']}-response-{region['request_index']}.json"
                        if candidate._read(path) != response:
                            raise ValueError("Retained region response differs from raw response file")
                recovered = partial.recover(row.get("transcription_regions", []), row["viewport"])
                item["recovery"] = recovered
                if recovered["state"]["tables"]:
                    # Scorer gets valid fragment tables; operational completeness
                    # is separately and explicitly unchanged in the report.
                    prediction.update(status="ok", tables=recovered["state"]["tables"])
                    item["partial"] = True
            predictions.append(prediction)
            evidence.append(item)
        write_json(output / "predictions.json", {"predictions": predictions, "evidence": evidence})
    manifest, references = load_corpus(guard_path(corpus))
    if frozen["manifest_sha256"] != sha((guard_path(corpus) / "manifest.json").read_bytes()):
        raise ValueError("Partial audit requires the complete matched DEV source manifest")
    if {r["id"] for r in manifest["pages"]} != {r["id"] for r in frozen["records"]}:
        raise ValueError("Partial audit must retain the entire intended page denominator")
    result = {
        "contract": "explicit_partial_tables_offline", "baseline": str(baseline),
        "baseline_report_sha256": sha((baseline / "report.json").read_bytes()),
        "baseline_scores": strict_scores(references["pages"], report["results"]),
        "partial_fragment_scores": strict_scores(references["pages"], predictions),
        "original_complete_outputs": sum(r["status"] == "ok" for r in report["results"]),
        "original_page_failures": sum(r["status"] != "ok" for r in report["results"]),
        "failed_pages_with_valid_fragments": sum(r["partial"] for r in evidence),
        "evidence": evidence, "resources": resources.summary(),
        "fresh_api_calls": 0, "pages_per_api_usd": None, "full_pipeline_pages_per_minute": None,
        "rate_scope": "Offline retained-response audit; original generation costs and latency excluded",
        "code_sha256": {name: sha((Path(__file__).parent / name).read_bytes()) for name in (
            "p003_partial_tables.py", "p003_partial_audit.py", "pipeline_vision_transcription.py",
        )},
    }
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Run one explicit DEV audit without credentials, generation, or retries."""
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("baseline", "trusted-code", "corpus", "output"):
        parser.add_argument("--" + argument, type=Path, required=True)
    args = parser.parse_args()
    audit(args.baseline, args.trusted_code, args.corpus, args.output)


if __name__ == "__main__":
    main()
