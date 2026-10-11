"""Prepare and rescore the explicit 35 retained mixed-evidence candidate arms."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bench import p003_additional_incremental_audit as existing
from bench.p003_scoring_audit import pinned
from bench.pipeline_run import Resources
from bench.silver import canonical, guard_path, sha, write_json

ARM_COUNT = 35
PAGE_COUNT = 16

VERSION = "p003-mixed-candidate-audit-v1"
STATUS_SHA256 = "616a333631c6e690d28fd3192e748c605c1e4f2be263cd89c79bee538b4e4293"
INVENTORY_SHA256 = "9cca3621f32d377a52b49f6dd88a43f466af6a9cda7fe00dec17baa33c984567"
REFERENCE_PLAN_SHA256 = "0c12d3d66af28b3f1710a35c1e17a734b4a8385b85219b21b95cb62ae725f1b0"
CODE_FILES = (*existing.CODE_FILES, "p003_mixed_candidate_audit.py", "generalization_report.py")


def names() -> set[str]:
    """Declare all treatments from the tracked mixed-evidence report before scoring."""
    images = {
        f"choice-pplx-{edge}-{encoding}-r1-c3"
        for edge in (128, 256, 400, 512, 768, 1024, 1200)
        for encoding in ("rgb", "rgb_png", "grayscale8", "rgb_palette16")
    }
    differences = {f"choice-diff-{model}-0-r0-c3" for model in ("d1", "jev", "luna", "pplx", "tev")}
    differences.update(f"choice-diff-{model}-512-r0-c3" for model in ("luna", "pplx"))
    return images | differences


def validate_inventory(entries: list[dict[str, Any]]) -> None:
    """Reject omissions, additions, duplicate identities and unrelated processors."""
    if len(entries) != ARM_COUNT or {e["name"] for e in entries} != names():
        raise ValueError("Exactly the declared 35 mixed-evidence candidate treatments required")
    if any(e["family"] != "candidate" for e in entries):
        raise ValueError("Candidate attribution required")
    if len({e["report_sha256"] for e in entries}) != len(entries):
        raise ValueError("Reports must have distinct identities")


def prepare(queue: Path, reference_plan: Path, output: Path) -> dict[str, Any]:
    """Freeze source/output admission and selected predictions without accessing targets."""
    queue, output = guard_path(queue), guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh preparation directory required")
    with Resources() as resources:
        status = pinned(str(queue / "status.json"), STATUS_SHA256)
        comparison_path = queue / "independent-mixed-comparison.json"
        comparison = json.loads(guard_path(comparison_path).read_bytes())
        if comparison["status_sha256"] != STATUS_SHA256 or sha(canonical(comparison["inventory"])) != INVENTORY_SHA256:
            raise ValueError("Independent mixed-evidence inventory identity differs")
        approved = pinned(str(reference_plan), REFERENCE_PLAN_SHA256)
        reference = next(e for e in approved["entries"] if e["family"] == "candidate")
        corpus_fields = {k: reference[k] for k in ("corpus", "corpus_manifest_sha256", "targets_sha256")}
        arms = [a for a in status["arms"] if a["name"] in names()]
        if len(arms) != ARM_COUNT or any(a["status"] != "completed" or a["exit_code"] != 0 for a in arms):
            raise ValueError("All 35 completed candidate arms required")
        prior = {e["name"]: e for e in comparison["inventory"]}
        entries, preparations = [], []
        for arm in arms:
            name = arm["name"]
            directory = queue / name
            receipt = prior[name]
            report = pinned(str(directory / "report.json"), receipt["report_sha256"])
            if report["config"].get("processor") != "p003_candidate_choice":
                raise ValueError("Mixed candidate processor changed")
            predictions, _scope = existing.primary(report)
            command = arm["command"]
            manifest = (
                Path(command[command.index("--manifest") + 1]) if "--manifest" in command else Path(status["manifest"])
            )
            entry = {
                "name": name,
                "family": "candidate",
                **corpus_fields,
                "primary_predictions_sha256": sha(canonical(predictions)),
            }
            paths = {
                "report": directory / "report.json",
                "evaluation": directory / "evaluation.json",
                "frozen": directory / "frozen.json",
                "run_manifest": manifest,
            }
            for key, path in paths.items():
                entry[key] = str(guard_path(path))
                entry[key + "_sha256"] = sha(guard_path(path).read_bytes())
            if (
                entry["report_sha256"] != receipt["report_sha256"]
                or entry["evaluation_sha256"] != receipt["evaluation_sha256"]
            ):
                raise ValueError("Independent mixed receipt identity differs")
            _report, verified, admitted, scope = existing.admit(entry)
            if len(admitted) != PAGE_COUNT or verified["intended_pages"] != PAGE_COUNT:
                raise ValueError("Complete natural16 intended denominator required")
            preparations.append(
                {
                    "name": name,
                    "primary_predictions": admitted,
                    "primary_scope": scope,
                    "historical_scores": verified["scores"],
                    "operational_errors": verified["errors"],
                    "prior_artifacts_sha256": sha(canonical(verified["artifacts"])),
                }
            )
            entries.append(entry)
        validate_inventory(entries)
        output.mkdir(parents=True)
        for row in preparations:
            write_json(output / (row["name"] + "-prepared.json"), row)
        declaration = {
            "version": VERSION,
            "entries": entries,
            "source_status_sha256": STATUS_SHA256,
            "source_inventory_sha256": INVENTORY_SHA256,
            "comparison_sha256": sha(comparison_path.read_bytes()),
            "reference_identity_copied_from_plan_sha256": REFERENCE_PLAN_SHA256,
            "reference_files_opened": False,
            "new_api_calls": 0,
            "intended_page_runs": 560,
            "historical_strict_scope": "Complete retained page composition",
            "primary_scope": "Committed complete model-selected crops; no baseline credit",
        }
        write_json(output / "plan.json", declaration)
    freeze = {
        "version": VERSION,
        "plan_sha256": sha((output / "plan.json").read_bytes()),
        "prepared_predictions": {
            r["name"]: sha((output / (r["name"] + "-prepared.json")).read_bytes()) for r in preparations
        },
        "resources": resources.summary(),
        "code_sha256": {n: sha(Path(__file__).with_name(n).read_bytes()) for n in CODE_FILES},
        "reference_files_opened": False,
        "new_api_calls": 0,
    }
    write_json(output / "freeze.json", freeze)
    return freeze


def audit(plan: Path, output: Path, *, plan_sha256: str, trusted_code: Path) -> dict[str, Any]:
    """Require external current-code authority before the unchanged dual-score replay."""
    authority = json.loads(guard_path(trusted_code).read_bytes())
    for name in CODE_FILES:
        if authority.get(name) != sha(Path(__file__).with_name(name).read_bytes()):
            raise ValueError("Independent current helper authority differs: " + name)
    declaration = pinned(str(plan), plan_sha256)
    if declaration.get("version") != VERSION or declaration.get("source_status_sha256") != STATUS_SHA256:
        raise ValueError("Frozen mixed-evidence declaration required")
    validate_inventory(declaration["entries"])
    return existing.audit(plan, output, plan_sha256=plan_sha256, trusted_code=trusted_code)


def main() -> None:
    """Separate source preparation from explicitly authorized scoring."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--queue", type=Path, required=True)
    prep.add_argument("--reference-plan", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    score = commands.add_parser("score")
    score.add_argument("--plan", type=Path, required=True)
    score.add_argument("--plan-sha256", required=True)
    score.add_argument("--trusted-code", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.queue, args.reference_plan, args.output)
    else:
        audit(args.plan, args.output, plan_sha256=args.plan_sha256, trusted_code=args.trusted_code)


if __name__ == "__main__":
    main()
