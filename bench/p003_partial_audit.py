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
from bench.generalization_report import SOURCE_FIELDS, load_corpus
from bench.p003_report import strict_scores
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json


def selected_references(
    corpus_manifest: dict[str, Any],
    references: dict[str, Any],
    selected: dict[str, Any],
    records: list[dict[str, Any]],
    cohort: str | None,
) -> list[dict[str, Any]]:
    """Require the complete predeclared cohort, including failed pages, before scoring."""
    if selected.get("split") != "DEV" or selected.get("dataset_sha256") != corpus_manifest["dataset_sha256"]:
        raise ValueError("Partial audit selection must match the explicit DEV corpus")
    expected = {
        r["id"]: {k: r[k] for k in SOURCE_FIELDS}
        for r in corpus_manifest["pages"]
        if cohort is None or r.get("cohort") == cohort
    }
    observed = {r["id"]: {k: r[k] for k in SOURCE_FIELDS} for r in selected["pages"]}
    if (
        not expected
        or len(observed) != len(selected["pages"])
        or observed != expected
        or len(records) != len(expected)
        or {r["id"]: r for r in records} != expected
    ):
        raise ValueError("Partial audit requires the complete matched DEV cohort and source records")
    targets = [r for r in references["pages"] if r["id"] in expected]
    if len(targets) != len(expected) or {r["id"] for r in targets} != set(expected):
        raise ValueError("Partial audit cohort references are incomplete")
    return targets


def audit(  # noqa: PLR0913 - explicit source, trust, output and complete-cohort controls.
    baseline: Path,
    trusted: Path,
    corpus: Path,
    output: Path,
    *,
    manifest_path: Path | None = None,
    cohort: str | None = None,
) -> dict[str, Any]:
    """Freeze all fragment predictions before loading any DEV scoring references."""
    baseline, output = guard_path(baseline), guard_path(output)
    reviewed = tuple(candidate.ROOT_REVIEWED_PARSER_SHA256)
    with Resources() as resources:
        frozen, report, _code = candidate.authenticate(
            baseline,
            candidate._read(trusted),
            reviewed_parser_sha256=reviewed,
        )
        if frozen["config"].get("transcription_representation", "legacy") not in {"legacy", "matrix_strict"}:
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
    selected_path = guard_path(manifest_path or corpus / "manifest.json")
    if frozen["manifest_sha256"] != sha(selected_path.read_bytes()):
        raise ValueError("Partial audit requires the complete matched DEV source manifest")
    targets = selected_references(manifest, references, candidate._read(selected_path), frozen["records"], cohort)
    result = {
        "contract": "explicit_partial_tables_offline",
        "baseline": str(baseline),
        "baseline_report_sha256": sha((baseline / "report.json").read_bytes()),
        "cohort": cohort,
        "manifest_sha256": frozen["manifest_sha256"],
        "baseline_scores": strict_scores(targets, report["results"]),
        "partial_fragment_scores": strict_scores(targets, predictions),
        "original_complete_outputs": sum(r["status"] == "ok" for r in report["results"]),
        "original_page_failures": sum(r["status"] != "ok" for r in report["results"]),
        "failed_pages_with_valid_fragments": sum(r["partial"] for r in evidence),
        "evidence": evidence,
        "resources": resources.summary(),
        "fresh_api_calls": 0,
        "pages_per_api_usd": None,
        "full_pipeline_pages_per_minute": None,
        "rate_scope": "Offline retained-response audit; original generation costs and latency excluded",
        "code_sha256": {
            name: sha((Path(__file__).parent / name).read_bytes())
            for name in (
                "p003_partial_tables.py",
                "p003_partial_audit.py",
                "pipeline_vision_transcription.py",
            )
        },
    }
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Run one explicit DEV audit without credentials, generation, or retries."""
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("baseline", "trusted-code", "corpus", "output"):
        parser.add_argument("--" + argument, type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--cohort")
    args = parser.parse_args()
    audit(args.baseline, args.trusted_code, args.corpus, args.output, manifest_path=args.manifest, cohort=args.cohort)


if __name__ == "__main__":
    main()
