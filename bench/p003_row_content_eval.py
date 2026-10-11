"""Evaluate approved R001 body outputs only after independent source-only replay."""

# ruff: noqa: EM101, TRY003, PLC0415
from __future__ import annotations

import argparse
import json
import tempfile
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from bench import p003_row_content_audit as source

VERSION = "p003-r001-body-evaluation-v1"
CODE_FILES = ("p003_row_content_eval.py", *source.CODE_FILES)


def verify(prepared: Path, approved_frozen_sha256: str, trusted_code: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reconstruct every source, wire and literal body before any target field is interpreted."""
    from bench.silver import guard_path, sha

    prepared = guard_path(prepared)
    authority = json.loads(guard_path(trusted_code).read_bytes())
    for name in CODE_FILES:
        if authority.get(name) != sha(Path(__file__).with_name(name).read_bytes()):
            raise ValueError("Independent current helper authority differs: " + name)
    frozen_path = prepared / "frozen.json"
    if sha(frozen_path.read_bytes()) != approved_frozen_sha256:
        raise ValueError("Approved source preparation changed")
    frozen = json.loads(frozen_path.read_bytes())
    if frozen["code_sha256"] != {name: authority[name] for name in source.CODE_FILES}:
        raise ValueError("Prepared current source code differs")
    if sha((prepared / "source-output.json").read_bytes()) != frozen["source_output_sha256"]:
        raise ValueError("Frozen source-owned outputs changed")
    for name, expected in frozen["artifact_sha256"].items():
        if sha(guard_path(Path(name)).read_bytes()) != expected:
            raise ValueError("Historical source/wire/raw artifact changed")
    history = Path(frozen["historical_authority"])
    if sha(history.read_bytes()) != frozen["historical_authority_sha256"]:
        raise ValueError("Historical Git authority changed")
    with tempfile.TemporaryDirectory(prefix="p003-r001-replay-") as temp:
        replay = Path(temp) / "replay"
        regenerated = source.prepare(
            Path(frozen["directory"]), history, Path(frozen["aliases"]), frozen["alias_sha256"], replay
        )
        if (
            regenerated != frozen
            or (replay / "source-output.json").read_bytes() != (prepared / "source-output.json").read_bytes()
        ):
            raise ValueError("Source-only replay differs from approved preparation")
    return frozen, json.loads((prepared / "source-output.json").read_bytes())


def evaluate(prepared: Path, approved_frozen_sha256: str, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Keep all records; author-unresolved cases have abstention coverage, never empty-table gold."""
    from bench import decision_rows as rows
    from bench.decision_records import materialize
    from bench.pipeline_run import Resources
    from bench.silver import guard_path, sha, write_json

    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh evaluation output required")
    with Resources() as resources:
        frozen, inventory = verify(prepared, approved_frozen_sha256, trusted_code)
        # FIRST interpretation of target fields occurs after complete source/raw replay above.
        directory = Path(frozen["directory"])
        manifest = json.loads((directory / "manifest.json").read_bytes())
        targets = manifest["targets"]
        if sha(json.dumps(targets, sort_keys=True).encode()) != manifest["targets_sha256"]:
            raise ValueError("Original embedded target identity differs")
        original = json.loads((directory / "results.json").read_bytes())
        originals = {(r["model"], r["arm"], r["case_index"]): r for r in original["records"]}
        records = []
        for record in inventory["records"]:
            target = targets[str(record["case_index"])]
            if target["input"] != record["source_input"]:
                raise ValueError("Private target source differs from admitted request evidence")
            raw = json.loads(Path(record["raw_response_path"]).read_bytes())
            rescored = rows.score_response(target, raw)
            original_score = originals[(record["model"], record["arm"], record["case_index"])]["score"]
            if rescored != original_score:
                raise ValueError("Original fragment/record witnesses do not reproduce exactly")
            unresolved = target["expected_choice"] == "unresolved"
            reference = (
                None
                if unresolved
                else source.body_table(
                    record["source_input"], materialize(target["original_case"], target["expected_choice"])
                )
            )
            if not unresolved and reference is None:
                raise ValueError("Known original body has no reference records")
            comparison = None if reference is None else source.compare_body(reference, record["body_table"])
            records.append(
                {
                    "model": record["model"],
                    "arm": record["arm"],
                    "case_index": record["case_index"],
                    "case_id": record["case_id"],
                    "entry_index": record["entry_index"],
                    "raw_response_sha256": record["raw_response_sha256"],
                    "author_unresolved": unresolved,
                    "all_fragments_unassigned": all(v is None for v in record["assignments"].values()),
                    "reference_body": reference,
                    "predicted_body": record["body_table"],
                    "content": comparison,
                    "strict_body_complete": reference == record["body_table"] if not unresolved else None,
                    "original_fragment_record_metrics": original_score,
                }
            )
        arms = []
        for model, arm in sorted({(r["model"], r["arm"]) for r in records}):
            group = [r for r in records if (r["model"], r["arm"]) == (model, arm)]
            counts: Counter[str] = Counter()
            supported = 0
            for record in group:
                comparison = record["content"]
                if comparison is not None and comparison["supported"]:
                    supported += 1
                    counts.update(comparison["counts"])
            complete = supported == sum(not r["author_unresolved"] for r in group)
            arms.append(
                {
                    "model": model,
                    "arm": arm,
                    "intended_cases": len(group),
                    "known_cases": sum(not r["author_unresolved"] for r in group),
                    "author_unresolved_cases": sum(r["author_unresolved"] for r in group),
                    "unresolved_abstentions": sum(
                        r["author_unresolved"] and r["all_fragments_unassigned"] for r in group
                    ),
                    "content_supported_cases": supported,
                    "counts": dict(counts),
                    "content_precision": counts["matched"] / counts["prediction_units"]
                    if counts["prediction_units"] and complete
                    else None,
                    "content_recall": counts["matched"] / counts["reference_units"]
                    if counts["reference_units"] and complete
                    else None,
                    "strict_body_complete": sum(r["strict_body_complete"] is True for r in group),
                    "content_recovered_bodies": sum(
                        r["content"] is not None and r["content"].get("content_recovered_with_row_order", False)
                        for r in group
                    ),
                    "original_mean_fragment_accuracy": mean(
                        r["original_fragment_record_metrics"]["selector_accuracy"] for r in group
                    ),
                    "original_mean_record_f1": mean(r["original_fragment_record_metrics"]["record_f1"] for r in group),
                    "original_exact_regions": sum(r["original_fragment_record_metrics"]["region_exact"] for r in group),
                    "schema_acceptance": None,
                    "full_page_extraction": None,
                }
            )
    result = {
        "version": VERSION,
        "source_frozen_sha256": approved_frozen_sha256,
        "source_output_sha256": frozen["source_output_sha256"],
        "targets_sha256": manifest["targets_sha256"],
        "records": records,
        "arms": arms,
        "resources": resources.summary(),
        "new_api_calls": 0,
        "fresh_inference_rates": None,
        "charges_reinterpreted": False,
        "scope": "Conditional body-only row_key/value content; fixed headers excluded; no page/table schema acceptance",
        "original_scores_reproduced": True,
        "original_initial_parser_failures_changed": False,
        "cross_directory_replay": (
            "Parser-v2 reuses retained response identities, including initial stopped-parser calls"
        ),
        "code_sha256": {name: sha(Path(__file__).with_name(name).read_bytes()) for name in CODE_FILES},
    }
    output.mkdir(parents=True)
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Require explicit source freeze and independent seven-helper authority."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", required=True, type=Path)
    parser.add_argument("--source-frozen-sha256", required=True)
    parser.add_argument("--trusted-code", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    evaluate(args.prepared, args.source_frozen_sha256, args.trusted_code, args.output)


if __name__ == "__main__":
    main()
