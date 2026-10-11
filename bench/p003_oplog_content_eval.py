"""Evaluate root-approved R002 conditional source-owned body outputs."""

# ruff: noqa: EM101, TRY003, PLC0415, C901, PLR2004
from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from bench import p003_oplog_content_audit as source

CODE_FILES = (
    "p003_oplog_content_eval.py",
    "p003_oplog_content_audit.py",
    "decision_oplog.py",
    "decision_context_cases.py",
    "decision_oplog_run.py",
    "p003_row_content_audit.py",
    "p003_content_alignment.py",
    "p003_render_reuse.py",
)


def target_body(case: dict[str, Any], initial: Any) -> tuple[dict[str, Any] | None, str | None]:  # noqa: ANN401
    """Require original body slot annotations; never derive target coordinates from predictions."""
    choice = case["gold"]["choice"]
    if choice == "unresolved":
        return None, "author-unresolved"
    if choice not in {"A", "B"}:
        raise ValueError("Original target choice invalid")
    words = case["evidence"]["words"]
    if [(w["text"], tuple(w["bbox"])) for w in words] != [(a.text, a.bbox) for a in initial.atoms]:
        raise ValueError("Target source differs from admitted wire atoms")
    aliases = {w["id"]: a.id for w, a in zip(words, initial.atoms, strict=True)}
    headers = {i for c in initial.cells for i in c.source_ids}
    cells = case["evidence"]["assemblies"][choice]["cells"]
    body, assigned, slots = [], [], set()
    for cell in cells:
        ids = [aliases[i] for i in cell["source_ids"]]
        if cell["id"] in {"description_header", "value_header"}:
            if not set(ids) <= headers:
                raise ValueError("Target header source differs")
            continue
        match = re.fullmatch(r"r(\d+)c([01])", cell["id"])
        if match is None:
            return None, "missing-slot-annotation"
        row, column = map(int, match.groups())
        if row >= 255 or (row, column) in slots or headers.intersection(ids):
            raise ValueError("Invalid target body slot/source")
        slots.add((row, column))
        body.append((row, column, ids))
        assigned.extend(ids)
    if Counter(assigned) != Counter(a.id for a in initial.atoms if a.id not in headers):
        raise ValueError("Complete exact target body source conservation required")
    if not body:
        return None, "missing-slot-annotation"
    values = [["", ""] for _ in range(max(r for r, _, _ in body) + 1)]
    text = {a.id: a.text for a in initial.atoms}
    for row, column, ids in body:
        values[row][column] = " ".join(text[i] for i in ids)
    return {"row_count": len(values), "col_count": 2, "values": values, "spans": []}, None


def verify(prepared: Path, approved_sha256: str, trusted_code: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate root code pins and repeat every source/wire/output check before targets."""
    from bench.silver import guard_path

    authority = source.read_json(trusted_code)
    for name in CODE_FILES:
        if authority.get(name) != source.digest(Path(__file__).with_name(name).read_bytes()):
            raise ValueError("Independent runtime helper authority differs: " + name)
    if source.digest((prepared / "frozen.json").read_bytes()) != approved_sha256:
        raise ValueError("Approved source freeze changed")
    frozen = source.read_json(prepared / "frozen.json")
    for name, expected in frozen["code_sha256"].items():
        if authority.get(name) != expected:
            raise ValueError("Frozen preparation code differs")
    if source.digest((prepared / "source-output.json").read_bytes()) != frozen["source_output_sha256"]:
        raise ValueError("Frozen source-owned body output differs")
    for path, expected in frozen["artifact_sha256"].items():
        if source.digest(guard_path(Path(path)).read_bytes()) != expected:
            raise ValueError("Retained source/wire/raw receipt differs")
    with tempfile.TemporaryDirectory(prefix="p003-r002-source-replay-") as temp:
        replay = Path(temp) / "replay"
        regenerated = source.prepare(Path(frozen["directory"]), replay)
        if (replay / "source-output.json").read_bytes() != (prepared / "source-output.json").read_bytes():
            raise ValueError("Exact source replay differs")
        if {k: v for k, v in regenerated.items() if k != "resources"} != {
            k: v for k, v in frozen.items() if k != "resources"
        }:
            raise ValueError("Source preparation authority differs")
    return frozen, source.read_json(prepared / "source-output.json")


def evaluate(prepared: Path, approved_sha256: str, trusted_code: Path, output: Path) -> dict[str, Any]:
    """Retain all attempted sessions and costs, with unfinished recovery separated."""
    from bench.decision_context_cases import context_cases
    from bench.decision_oplog import from_context
    from bench.decision_oplog_run import score
    from bench.p003_render_reuse import Monitor
    from bench.p003_row_content_audit import compare_body
    from bench.silver import guard_path, write_json

    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh evaluation required")
    with Monitor() as resources:
        frozen, inventory = verify(prepared, approved_sha256, trusted_code)
        # Target generation/interpretation follows root-pin verification and complete source-only replay.
        cases = context_cases()
        manifest = source.read_json(Path(frozen["directory"]) / "manifest.json")
        original = source.read_json(Path(frozen["directory"]) / "results.json")
        selected_targets, records = {}, []
        for row in inventory["records"]:
            case = cases[row["case_index"]]
            item = next(c for c in manifest["cases"] if c["index"] == row["case_index"])
            initial = source.state_from(row["initial_state"])
            state = source.state_from(row["final_state"])
            if source.digest(case["pdf_bytes"]) != item["source_sha256"] or from_context(case) != initial:
                raise ValueError("Original PDF/initial source hypothesis differs")
            rescored = score(case, state)
            if rescored != row["original_score"]:
                raise ValueError("Historical score dictionary does not reproduce exactly")
            reference, exclusion = target_body(case, initial)
            content = compare_body(reference, row["body_table"]) if reference is not None else None
            selected_targets[str(row["case_index"])] = {
                "source_sha256": item["source_sha256"],
                "gold": case["gold"],
                "assemblies": case["evidence"]["assemblies"],
            }
            records.append(
                {
                    **row,
                    "case_id": case["id"],
                    "reference_body": reference,
                    "exclusion": exclusion,
                    "content": content,
                    "strict_body_complete": reference == row["body_table"] if reference is not None else None,
                    "completed_content_recovery": row["stop_reason"] == "finished"
                    and content is not None
                    and content.get("content_recovered_with_row_order", False),
                }
            )
        models = []
        for model in manifest["models"]:
            group = [r for r in records if r["model"] == model]
            comparisons = [r["content"] for r in group if r["content"] is not None]
            counts: Counter[str] = Counter()
            for comparison in comparisons:
                if not comparison["supported"]:
                    raise ValueError("Declared reference comparison unsupported")
                counts.update(comparison["counts"])
            calls = [c for c in original["calls"] if c["model"] == model]
            models.append(
                {
                    "model": model,
                    "intended_sessions": len(group),
                    "known_content_sessions": len(comparisons),
                    "exclusions": dict(Counter(r["exclusion"] for r in group if r["exclusion"])),
                    "stop_reasons": dict(Counter(r["stop_reason"] for r in group)),
                    "counts": dict(counts),
                    "emitted_content_precision": counts["matched"] / counts["prediction_units"]
                    if counts["prediction_units"]
                    else 0.0,
                    "known_body_content_recall": counts["matched"] / counts["reference_units"]
                    if counts["reference_units"]
                    else 0.0,
                    "strict_body_complete": sum(r["strict_body_complete"] is True for r in group),
                    "emitted_content_recovered_bodies": sum(
                        c.get("content_recovered_with_row_order", False) for c in comparisons
                    ),
                    "completed_content_recovery": sum(r["completed_content_recovery"] for r in group),
                    "original_group_exact": sum(r["original_score"]["source_group_exact"] for r in group),
                    "original_slot_exact": sum(r["original_score"]["row_column_exact"] is True for r in group),
                    "original_placement_correct": sum(
                        r["original_score"]["placement_correct_sources"] or 0 for r in group
                    ),
                    "original_placement_scored": sum(r["original_score"]["placement_scored_sources"] for r in group),
                    "original_mean_pair_precision": mean(
                        r["original_score"]["pair_precision"]
                        for r in group
                        if r["original_score"]["pair_precision"] is not None
                    ),
                    "original_mean_pair_recall": mean(
                        r["original_score"]["pair_recall"]
                        for r in group
                        if r["original_score"]["pair_recall"] is not None
                    ),
                    "original_calls": len(calls),
                    "original_costs": [c["cost"] for c in calls],
                    "original_effective_usd": sum(c["cost"]["effective_usd"] for c in calls),
                    "schema_acceptance": None,
                    "full_page_extraction": None,
                }
            )
    result = {
        "version": "p003-r002-body-evaluation-v1",
        "policy": frozen["policy"],
        "records": records,
        "models": models,
        "source_frozen_sha256": approved_sha256,
        "source_output_sha256": frozen["source_output_sha256"],
        "selected_targets_sha256": source.digest(json.dumps(selected_targets, sort_keys=True).encode()),
        "runtime_authority_sha256": source.digest(trusted_code.read_bytes()),
        "resources": resources.metrics(),
        "new_api_calls": 0,
        "original_scores_reproduced": True,
        "original_calls_and_costs_preserved": True,
        "original_calls": original["calls"],
    }
    output.mkdir(parents=True)
    write_json(output / "targets.json", selected_targets)
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Require explicit root-approved source freeze and external runtime code pins."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", required=True, type=Path)
    parser.add_argument("--source-frozen-sha256", required=True)
    parser.add_argument("--trusted-code", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    evaluate(args.prepared, args.source_frozen_sha256, args.trusted_code, args.output)


if __name__ == "__main__":
    main()
