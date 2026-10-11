"""Source-freeze retained A002 decisions with model-only and fixed-native scopes."""

# ruff: noqa: EM101, TRY003, PLC0415, C901, PLR0912
from __future__ import annotations

import argparse
import ast
import json
import resource as usage_resource
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_rolling_candidate_audit as candidates
from bench.decision_oplog_run import parse_choice
from bench.p003_scoring_audit import pinned
from bench.pipeline_run import Resources
from bench.rolling_rows import admission_request
from bench.silver import canonical, guard_path, sha, write_json

VERSION = "p003-rolling-admission-audit-v1"
CALLS_SHA256 = "c7281ec5885547d4557852bce587cd0a56ee8325fb0dc8d5a3564b3754bb0289"
CANDIDATE_PLAN_SHA256 = "ea0cc2171bb981ed7471511fa8bcd06b4283ef5f2abff65361ac4eea50b920a0"
MODELS = {"pplx": "perplexity/pplx-decider-v1.1-27b", "luna": "openai/gpt-6-luna-decisions"}
ARMS = ("text", "image512")
MODEL_PAGES = 24
NATIVE_PAGES = 4
CODE_FILES = (
    *candidates.CODE_FILES,
    "p003_rolling_admission_audit.py",
    "rolling_rows.py",
    "decision_oplog_run.py",
    "decision_hosted.py",
)
HISTORICAL_CODE = {
    "rolling_row_run.py": (
        "2655f5a7921b23d988c2c4bb68b32ad7dd1f0896",
        "2b1ffa16f0eb96586772578431246744ce7d32956f1a494f262f6fc8b4c1b336",
    ),
    "rolling_rows.py": (
        "2655f5a7921b23d988c2c4bb68b32ad7dd1f0896",
        "22b1062e9b66ca838ee81bdbc3062f9c49501449c6aa890a6791fb24f5ccd26b",
    ),
    "decision_hosted.py": (
        "3e1d32a4d8154a996b0824f190f55083cbb7b7cc",
        "01ea1c35796d81ce034a1b85dcfbaec399467efc9854fc60d23aa732dd65218f",
    ),
    "decision_oplog_run.py": (
        "2655f5a7921b23d988c2c4bb68b32ad7dd1f0896",
        "082a71f1ae15663e1c69b2aaf83ba5f72581246efd1571c6e601b34d5723bdfe",
    ),
}
STABLE_FUNCTIONS = {
    "rolling_rows.py": ("project", "_candidate_identity", "source_image", "admission_request"),
    "decision_oplog_run.py": ("parse_choice",),
    "decision_hosted.py": ("probability",),
}


def git_authority(evaluation: dict[str, Any]) -> dict[str, Any]:
    """Read authenticated Git source as data; never import or execute historical Python."""
    result = {}
    repository = Path(__file__).resolve().parents[1]
    for name, (commit, digest) in HISTORICAL_CODE.items():
        raw = subprocess.check_output(["/usr/bin/git", "show", commit + ":bench/" + name], cwd=repository)  # noqa: S603
        if sha(raw) != digest or (name in evaluation["code_sha256"] and evaluation["code_sha256"][name] != digest):
            raise ValueError("Historical Git authority differs")
        original = ast.parse(raw)
        current = ast.parse(Path(__file__).with_name(name).read_bytes())
        for function in STABLE_FUNCTIONS.get(name, ()):
            old = next(n for n in original.body if isinstance(n, ast.FunctionDef) and n.name == function)
            new = next(n for n in current.body if isinstance(n, ast.FunctionDef) and n.name == function)
            if ast.dump(old, include_attributes=False) != ast.dump(new, include_attributes=False):
                raise ValueError("Current pure helper differs from historical function: " + function)
        result[name] = {
            "git_commit": commit,
            "sha256": digest,
            "recorded_original_hash": name in evaluation["code_sha256"],
            "verified_current_functions": list(STABLE_FUNCTIONS.get(name, ())),
        }
    return result


def native_prediction(source: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    """Validate fixed native literals and ownership without attributing them to a model."""
    if selection["tables"] != source["vector_candidates"]:
        raise ValueError("Fixed native tables differ from original source export")
    lookup = {w["id"]: w["text"] for w in source["words"]}
    owners = selection["word_ownership"]
    if len(lookup) != len(source["words"]):
        raise ValueError("Unique native source IDs required")
    keys = {(o["table"], o["cell"]) for o in owners}
    if len(keys) != len(owners):
        raise ValueError("Unique complete native ownership records required")
    expected = {
        (t, i)
        for t, table in enumerate(selection["tables"])
        for i, value in enumerate(v for row in table["values"] for v in row)
        if value is not None
    }
    if keys != expected:
        raise ValueError("Complete fixed native anchor ownership required")
    ids = []
    for owner in owners:
        table = selection["tables"][owner["table"]]
        value = [v for row in table["values"] for v in row][owner["cell"]]
        source_ids = owner["source_ids"]
        if any(i not in lookup for i in source_ids) or value != " ".join(lookup[i] for i in source_ids):
            raise ValueError("Fixed native literal differs from source IDs")
        ids.extend(source_ids)
    if Counter(ids + selection["unresolved_ids"]) != Counter(lookup.keys()):
        raise ValueError("Fixed native ownership conservation differs")
    return {
        "id": source["id"],
        "status": "ok",
        "tables": [{k: t[k] for k in candidates.TABLE_FIELDS} for t in selection["tables"]],
        "owned_source_ids": len(ids),
        "unresolved_source_ids": len(selection["unresolved_ids"]),
        "selection": "fixed_native_vector",
    }


def chosen_prediction(
    source: dict[str, Any], alternatives: list[dict[str, Any]], call: dict[str, Any] | None
) -> dict[str, Any]:
    """Select an exact retained literal alternative; empty failures/abstentions conserve source."""
    choice = call["answer"]["choice"] if call and call["status"] == "ok" else "unattempted_or_failed"
    if choice in candidates.VARIANTS:
        alternative = next(a for a in alternatives if a["variant"] == choice)
        row = candidates.admit_alternative(source, alternative)
    else:
        if choice not in {"not_table", "unresolved", "unattempted_or_failed"}:
            raise ValueError("Unsupported retained choice")
        row = {
            "id": source["id"],
            "status": "error" if choice == "unattempted_or_failed" else "ok",
            "tables": [],
            "owned_source_ids": 0,
            "unresolved_source_ids": len(source["words"]),
            "header_roles": "unknown; no model-selected table",
        }
    return {**row, "selection": choice}


def verify_call(record: dict[str, Any], call: dict[str, Any], body: dict[str, Any], responses: Path) -> dict[str, Any]:
    """Authenticate exact wire, response metadata, usage and complete typed-choice replay."""
    for key in ("model", "arm", "id", "request", "sha256", "choices", "route", "bytes"):
        if call[key] != record[key]:
            raise ValueError("Call differs from frozen request receipt")
    entry = call.get("entry")
    if call["status"] != "ok" and entry is None:
        return {
            "status": call["status"],
            "entry": None,
            "raw_response_sha256": None,
            "call_sha256": sha(canonical(call)),
            "wire_identity": "unavailable",
        }
    if not isinstance(entry, dict):
        raise TypeError("Successful call must retain its actual request/response entry")
    expected_tag = "A002-rolling-admission/" + "/".join(record[k] for k in ("model", "arm", "id"))
    if entry.get("tag") != expected_tag:
        raise ValueError("Retained A002 request tag differs")
    if (
        entry["request_sha256"] != sha(json.dumps(body, separators=(",", ":")).encode())
        or entry["requested_model"] != record["model"]
    ):
        raise ValueError("Retained actual wire/model identity differs")
    if call["status"] != "ok":
        return {"status": call["status"], "entry": entry, "raw_response_sha256": None}
    filename = entry["response_file"]
    if Path(filename).name != filename or filename != "response-" + str(entry["index"]) + ".json":
        raise ValueError("Raw response filename differs from provider receipt index")
    path = guard_path(responses / filename)
    data = path.read_bytes()
    response = json.loads(data)
    if parse_choice(response, set(record["choices"])) != call["answer"]:
        raise ValueError("Typed raw choice differs from retained answer")
    if response.get("usage", {}) != call["usage"]:
        raise ValueError("Retained response usage differs")
    for field, entry_field in (("model", "served_model"), ("provider", "provider"), ("id", "generation_id")):
        if response.get(field) != entry.get(entry_field):
            raise ValueError("Raw response reported identity differs")
    return {
        "response": str(path),
        "raw_response_sha256": sha(data),
        "status": call["status"],
        "index": entry["index"],
        "entry_sha256": sha(canonical(entry)),
        "call_sha256": sha(canonical(call)),
        "wire_sha256": entry["request_sha256"],
    }


def validate_provider_indices(calls: list[dict[str, Any]]) -> None:
    """Count unique observed provider receipt identities without counting missing calls as attempts."""
    indices = [c["entry"]["index"] for c in calls if isinstance(c.get("entry"), dict)]
    if len(indices) != len(set(indices)):
        raise ValueError("Global unique provider receipt indices required")


def validate_targets(targets: list[dict[str, Any]], expected_ids: set[str]) -> None:
    """Prevent dictionary conversion from hiding duplicate or missing original reference pages."""
    ids = [t["id"] for t in targets]
    if len(ids) != candidates.PAGE_COUNT or len(set(ids)) != candidates.PAGE_COUNT or set(ids) != expected_ids:
        raise ValueError("Complete exact unique 28-page reference inventory required")


def prepare(original: Path, candidate_plan: Path, responses: Path, output: Path) -> dict[str, Any]:
    """Freeze all four model inventories, separate native controls and composed states before gold."""
    original, responses, output = (guard_path(p) for p in (original, responses, output))
    if output.exists():
        raise FileExistsError("Fresh source preparation directory required")
    children_before = usage_resource.getrusage(usage_resource.RUSAGE_CHILDREN)
    with Resources() as resource:
        declaration = pinned(str(candidate_plan), CANDIDATE_PLAN_SHA256)
        artifacts = {n: pinned(str(original / n), h) for n, h in candidates.ORIGINAL_HASHES.items()}
        evaluation, manifest = artifacts["evaluation.json"], artifacts["manifest.json"]
        history = git_authority(evaluation)
        sources = {p["id"]: p for p in artifacts["source-frozen.json"]["pages"]}
        alternatives = {p["id"]: p["alternatives"] for p in artifacts["candidates-frozen.json"]["pages"]}
        calls_artifact = pinned(str(original / "hosted-results.json"), CALLS_SHA256)
        calls = calls_artifact["calls"]
        validate_provider_indices(calls)
        if len(sources) != candidates.PAGE_COUNT or set(sources) != set(alternatives):
            raise ValueError("Complete source/candidate inventory required")
        for receipt in declaration["source_receipts"]:
            if sha(canonical(sources[receipt["id"]])) != receipt["source_sha256"]:
                raise ValueError("A001 source receipt differs")
            for field in ("pdf", "image"):
                if sha(guard_path(Path(receipt[field])).read_bytes()) != receipt[field + "_sha256"]:
                    raise ValueError("A001 source PDF/image bytes differ")
        for page_id, options in alternatives.items():
            for alternative in options:
                candidates.admit_alternative(sources[page_id], alternative)
        native_records = [r for r in manifest["records"] if r["route"] == "native_vector"]
        model_records = [r for r in manifest["records"] if r["route"] == "hosted_admission"]
        native_ids = {r["id"] for r in native_records}
        model_ids = set(sources) - native_ids
        if len(native_records) != NATIVE_PAGES or len(native_ids) != NATIVE_PAGES or len(model_ids) != MODEL_PAGES:
            raise ValueError("Complete separate native4/model24 scope required")
        expected = {(model, arm, i) for model in MODELS.values() for arm in ARMS for i in model_ids}
        keys = [(r["model"], r["arm"], r["id"]) for r in model_records]
        call_keys = [(r["model"], r["arm"], r["id"]) for r in calls]
        if (
            len(set(keys)) != len(keys)
            or set(keys) != expected
            or len(set(call_keys)) != len(call_keys)
            or not set(call_keys) <= expected
        ):
            raise ValueError("Complete unique intended request inventory and unique call identities required")
        call_map = dict(zip(call_keys, calls, strict=True))
        receipts = []
        for record in model_records:
            filename = record["request"]
            if Path(filename).name != filename:
                raise ValueError("Frozen request filename escapes directory")
            request_path = original / filename
            raw = request_path.read_bytes()
            if sha(raw) != record["sha256"] or len(raw) != record["bytes"]:
                raise ValueError("Frozen request bytes differ")
            body = json.loads(raw)
            reconstructed = admission_request(
                sources[record["id"]],
                alternatives[record["id"]],
                record["model"],
                with_image=record["arm"] == "image512",
            )
            if reconstructed != body or set(body["questions"]["q0"]["criteria"]) != set(record["choices"]):
                raise ValueError("Frozen whole source/candidate/image request reconstruction differs")
            call = call_map.get((record["model"], record["arm"], record["id"]))
            receipt = verify_call(record, call, body, responses) if call else {"status": "unattempted"}
            receipts.append(
                {
                    "model": record["model"],
                    "arm": record["arm"],
                    "id": record["id"],
                    "request": str(request_path),
                    "request_sha256": record["sha256"],
                    **receipt,
                }
            )
        native = [native_prediction(sources[r["id"]], r["native_selection"]) for r in native_records]
        cohorts = []
        output.mkdir(parents=True)
        write_json(output / "native-predictions.json", {"pages": native})
        for label, model in MODELS.items():
            for arm in ARMS:
                name = label + "-" + arm
                chosen = [
                    chosen_prediction(sources[i], alternatives[i], call_map.get((model, arm, i)))
                    for i in sources
                    if i in model_ids
                ]
                composed = chosen + native
                write_json(output / (name + "-model.json"), {"pages": chosen})
                write_json(output / (name + "-composed.json"), {"pages": composed})
                old = evaluation["cohorts"][model + "/" + arm]
                if len(old["rows"]) != candidates.PAGE_COUNT or {r["id"] for r in old["rows"]} != set(sources):
                    raise ValueError("Complete original composed legacy witness required")
                retained = [c for c in calls if c["model"] == model and c["arm"] == arm]
                cohorts.append(
                    {
                        "name": name,
                        "model": model,
                        "arm": arm,
                        "intended_model_pages": MODEL_PAGES,
                        "model_predictions_sha256": sha((output / (name + "-model.json")).read_bytes()),
                        "composed_predictions_sha256": sha((output / (name + "-composed.json")).read_bytes()),
                        "selection_counts": dict(Counter(r["selection"] for r in chosen)),
                        "call_status_counts": dict(Counter(c["status"] for c in retained)),
                        "unattempted_pages": MODEL_PAGES - len(retained),
                        "retained_costs": [c["cost"] for c in retained],
                        "http_elapsed_ms": [c.get("http_elapsed_ms") for c in retained],
                    }
                )
        plan = {
            "version": VERSION,
            "original": str(original),
            "original_sha256": candidates.ORIGINAL_HASHES,
            "calls_sha256": CALLS_SHA256,
            "candidate_plan": str(candidate_plan),
            "candidate_plan_sha256": CANDIDATE_PLAN_SHA256,
            "historical_git_authority": history,
            "receipts": receipts,
            "cohorts": cohorts,
            "native_ids": sorted(native_ids),
            "model_ids": sorted(model_ids),
            "native_predictions_sha256": sha((output / "native-predictions.json").read_bytes()),
            "original_parser_hash_recorded": False,
            "historical_raw_response_hashes_recorded": False,
            "reference_files_opened": False,
            "new_api_calls": 0,
            "scope": "Four model24 decisions; separate fixed native4 and composed28 diagnostics",
        }
        write_json(output / "plan.json", plan)
    children_after = usage_resource.getrusage(usage_resource.RUSAGE_CHILDREN)
    measured = resource.summary()
    measured.update(
        measurement="psutil main-process RSS every 100 ms; process_time CPU; four Git blob readers measured separately",
        git_subprocess_count=len(HISTORICAL_CODE),
        git_subprocess_cpu_seconds=(
            children_after.ru_utime + children_after.ru_stime - children_before.ru_utime - children_before.ru_stime
        ),
        git_child_lifetime_peak_rss_bytes=children_after.ru_maxrss * 1024,
        git_child_measurement="Linux getrusage(RUSAGE_CHILDREN) CPU delta; maximum child lifetime RSS, not summed",
    )
    freeze = {
        "plan_sha256": sha((output / "plan.json").read_bytes()),
        "resources": measured,
        "code_sha256": {n: sha(Path(__file__).with_name(n).read_bytes()) for n in CODE_FILES},
        "reference_files_opened": False,
        "new_api_calls": 0,
    }
    write_json(output / "freeze.json", freeze)
    return freeze


def audit(plan: Path, output: Path, *, plan_sha256: str, trusted_code: Path, targets_sha256: str) -> dict[str, Any]:
    """Re-admit retained bytes before gold; assert all112 legacy rows, then score separate views."""
    from bench.borderless_challenge import score
    from bench.p003_report import strict_scores
    from bench.p003_scoring_audit import dual_scores

    authority = json.loads(guard_path(trusted_code).read_bytes())
    for name in CODE_FILES:
        if authority.get(name) != sha(Path(__file__).with_name(name).read_bytes()):
            raise ValueError("Independent current helper authority differs: " + name)
    declaration = pinned(str(plan), plan_sha256)
    if declaration["version"] != VERSION or len(declaration["cohorts"]) != len(MODELS) * len(ARMS):
        raise ValueError("Complete frozen four-cohort scope required")
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh score output required")
    output.mkdir(parents=True)
    responses = {str(Path(r["response"]).parent) for r in declaration["receipts"] if r.get("response")}
    if len(responses) != 1:
        raise ValueError("One explicit raw response directory required")
    # Rebuild the entire source-owned declaration before the first reference read.
    prepare(
        Path(declaration["original"]),
        Path(declaration["candidate_plan"]),
        Path(next(iter(responses))),
        output / "source-readmission",
    )
    if sha((output / "source-readmission/plan.json").read_bytes()) != plan_sha256:
        raise ValueError("Complete source/request/response/selection readmission differs")
    candidate_plan = pinned(declaration["candidate_plan"], declaration["candidate_plan_sha256"])
    evaluation = pinned(
        str(Path(declaration["original"]) / "evaluation.json"), candidates.ORIGINAL_HASHES["evaluation.json"]
    )
    native = pinned(str(plan.parent / "native-predictions.json"), declaration["native_predictions_sha256"])["pages"]
    views = []
    for cohort in declaration["cohorts"]:
        for scope in ("model", "composed"):
            rows = pinned(
                str(plan.parent / (cohort["name"] + "-" + scope + ".json")), cohort[scope + "_predictions_sha256"]
            )["pages"]
            expected_ids = (
                declaration["model_ids"] if scope == "model" else declaration["model_ids"] + declaration["native_ids"]
            )
            if len(rows) != len(expected_ids) or {r["id"] for r in rows} != set(expected_ids):
                raise ValueError("Complete unique view inventory required")
            views.append((cohort, scope, rows))
    corpus = guard_path(Path(candidate_plan["corpus"]))
    target_bytes = guard_path(corpus / "private-targets.json").read_bytes()
    if sha(target_bytes) != targets_sha256:
        raise ValueError("Externally approved reference identity differs")
    targets = json.loads(target_bytes)
    expected_target_ids = set(declaration["model_ids"] + declaration["native_ids"])
    validate_targets(targets, expected_target_ids)
    gold = {t["id"]: t for t in targets}
    for cohort, scope, rows in views:
        if scope == "composed":
            old = {r["id"]: r for r in evaluation["cohorts"][cohort["model"] + "/" + cohort["arm"]]["rows"]}
            if any(score(gold[r["id"]], r["tables"]) != old[r["id"]]["scores"] for r in rows):
                raise ValueError("Original composed legacy per-page score differs")
    result: dict[str, Any] = {
        "version": VERSION,
        "plan_sha256": plan_sha256,
        "targets_sha256": targets_sha256,
        "legacy_page_witnesses_reproduced": candidates.PAGE_COUNT * len(MODELS) * len(ARMS),
        "new_api_calls": 0,
        "runs": [],
        "retained_cohorts": declaration["cohorts"],
    }
    for cohort, scope, rows in [*views, ({"name": "native", "model": None, "arm": None}, "fixed_native", native)]:
        ids = {r["id"] for r in rows}
        selected_targets = [t for t in targets if t["id"] in ids]
        with Resources() as resource:
            strict = strict_scores(selected_targets, rows)
            secondary = dual_scores(selected_targets, rows, strict)
        name = cohort["name"] + "-" + scope
        summary = {
            "name": name,
            "model": cohort["model"],
            "arm": cohort["arm"],
            "scope": scope,
            "strict": strict["totals"],
            "secondary": {k: v for k, v in secondary.items() if k != "pages"},
            "resources": resource.summary(),
        }
        write_json(
            output / (name + ".json"),
            {"predictions": rows, "strict": strict, "secondary": secondary, "summary": summary},
        )
        result["runs"].append(summary)
    result["retained_call_count"] = sum(sum(c["call_status_counts"].values()) for c in declaration["cohorts"])
    result["code_sha256"] = {n: sha(Path(__file__).with_name(n).read_bytes()) for n in CODE_FILES}
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Keep source-freeze and externally approved scoring separate CLI modes."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    prep = commands.add_parser("prepare")
    for name in ("original", "candidate-plan", "responses", "output"):
        prep.add_argument("--" + name, type=Path, required=True)
    scoring = commands.add_parser("score")
    for name in ("plan", "trusted-code", "output"):
        scoring.add_argument("--" + name, type=Path, required=True)
    scoring.add_argument("--plan-sha256", required=True)
    scoring.add_argument("--targets-sha256", required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.original, args.candidate_plan, args.responses, args.output)
    else:
        audit(
            args.plan,
            args.output,
            plan_sha256=args.plan_sha256,
            trusted_code=args.trusted_code,
            targets_sha256=args.targets_sha256,
        )


if __name__ == "__main__":
    main()
