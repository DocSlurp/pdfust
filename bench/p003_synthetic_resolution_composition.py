"""Source-only fixed vector/decision composition plans for all new resolution arms."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import p003_geometry_decision_composition as composition
from bench import p003_synthetic_resolution as resolution
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003, PLR2004, PLC0415, PLR0913, PLR0917
VERSION = "p003-synthetic-resolution-composition-v1"
POLICIES = composition.POLICIES


def arm_plan(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Declare every model and edge with every fixed policy, without reading outcomes."""
    if len(rows) != 25 or len({r["name"] for r in rows}) != 25:
        raise ValueError("Complete unique 25-arm resolution inventory required")
    parsed = []
    for row in rows:
        arguments = row["arguments"]
        options = dict(zip(arguments[::2], arguments[1::2], strict=True))
        parsed.append((row["name"], options["--model"], int(options["--image-edge"])))
    if {(model, edge) for _, model, edge in parsed} != {
        (model, edge) for model in resolution.MODELS for edge in resolution.EDGES
    }:
        raise ValueError("All five models and five new edges required; no outcome-selected edge")
    return [
        {
            "name": f"{name}-{policy}",
            "input_arm": name,
            "model": model,
            "image_edge": edge,
            "policy": policy,
            "question_count": 24,
        }
        for name, model, edge in parsed
        for policy in POLICIES
    ]


def combine(vector_rows: list[dict[str, Any]], verified_model: dict[str, Any], policy: str) -> dict[str, Any]:
    """Apply the unchanged fixed composition protocol to one independently verified model arm."""
    vectors = {r["id"]: r for r in vector_rows}
    rows = verified_model["rows"]
    if len(vectors) != 24 or len(vector_rows) != 24 or len(rows) != 24 or {r["id"] for r in rows} != set(vectors):
        raise ValueError("Complete unique 24-case component inventories required")
    if len({r["id"] for r in rows}) != 24:
        raise ValueError("Duplicate model case IDs refused")
    if (
        verified_model["config"]["model"] not in resolution.MODELS
        or verified_model["config"]["image_edge"] not in resolution.EDGES
    ):
        raise ValueError("Only independently verified new model/edge arms admitted")
    outcomes = [composition.compose(vectors[r["id"]], r, policy) for r in rows]
    return {
        "version": VERSION,
        "config": deepcopy(verified_model["config"]),
        "policy": policy,
        "rows": outcomes,
        "question_count": 24,
        "new_api_calls": 0,
        "gold_accessed": False,
        "actual_retained_model_charges": deepcopy(verified_model["charges"]),
        "charge_scope": "One original model arm; do not sum its charge across three composition policies",
        "hypothetical_suppressed_request_count": sum(v["status"] == "classified" for v in vector_rows)
        if policy == "vector_first"
        else 0,
        "hypothetical_cost_saving_usd": None,
        "fresh_throughput": None,
        "full_pipeline_rate": None,
    }


def prepare(
    queue_prepared: Path,
    approved_queue_sha256: str,
    source: Path,
    source_map: Path,
    vector: Path,
    vector_map: Path,
    vector_frozen_sha256: str,
    output: Path,
    *,
    hosted_queue: Path,
    aliases: Path,
    alias_sha256: str,
) -> dict[str, Any]:
    """Authenticate source/vector receipts, then freeze 75 policies before new model outputs or gold."""
    from bench import p003_synthetic_alias_replay as alias_replay
    from bench import p003_synthetic_geometry_eval as geometry_eval
    from bench import p003_synthetic_relations_eval as evaluator
    from bench import p003_synthetic_resolution_queue as queue

    output = guard_path(output)
    if output.exists():
        raise FileExistsError("New immutable composition preparation required")
    prepared_file = guard_path(queue_prepared) / "frozen.json"
    if sha(prepared_file.read_bytes()) != approved_queue_sha256:
        raise ValueError("Queue preparation differs from independently approved SHA")
    prepared = evaluator.load(prepared_file)
    alias_replay.authority(aliases, alias_sha256)
    context = evaluator.source_context(source, source_map)
    verified_vector = geometry_eval.verify(vector, vector_map, vector_frozen_sha256, context)
    vectors = [r for r in verified_vector["rows"] if r["treatment"] == "direct_vector"]
    if len(vectors) != 24 or len({r["id"] for r in vectors}) != 24:
        raise ValueError("Complete verified vector inventory required")
    preflight = Path(prepared["preflight"])
    if sha((preflight / "frozen.json").read_bytes()) != prepared["preflight_sha256"]:
        raise ValueError("Prepared request pool changed")
    inputs, rows = queue.replay_preflight(preflight)
    if (
        inputs["source_frozen_sha256"] != context["frozen_sha256"]
        or inputs["source_map_sha256"] != context["map_sha256"]
    ):
        raise ValueError("Vector and resolution preparation use different source authorities")
    if rows != prepared["plan"]:
        raise ValueError("Resolution plan differs from authenticated prepared bodies")
    all_arms = arm_plan(rows)
    hosted_queue = guard_path(hosted_queue)
    options = dict(zip(rows[0]["arguments"][::2], rows[0]["arguments"][1::2], strict=True))
    for arm in all_arms:
        arm["original_run_directory"] = str(hosted_queue / arm["input_arm"])
        arm["runtime_map"] = str(hosted_queue / "trusted-code" / (arm["input_arm"] + ".json"))
    output.mkdir(parents=True)
    write_json(output / "plan.json", all_arms)
    write_json(output / "vector-components.json", vectors)
    result = {
        "version": VERSION,
        "plan_sha256": sha((output / "plan.json").read_bytes()),
        "vector_components_sha256": sha((output / "vector-components.json").read_bytes()),
        "queue_prepared_sha256": approved_queue_sha256,
        "queue_prepared": str(guard_path(queue_prepared)),
        "source": str(guard_path(source)),
        "source_map": str(guard_path(source_map)),
        "images": options["--images"],
        "image_map": options["--image-map"],
        "hosted_queue": str(hosted_queue),
        "aliases": str(guard_path(aliases)),
        "alias_sha256": alias_sha256,
        "source_frozen_sha256": context["frozen_sha256"],
        "source_map_sha256": context["map_sha256"],
        "vector_receipt": {
            "directory": str(guard_path(vector)),
            "external_map_sha256": sha(vector_map.read_bytes()),
            "frozen_sha256": vector_frozen_sha256,
        },
        "helper_sha256": sha(Path(__file__).read_bytes()),
        "composition_protocol_sha256": sha(Path(composition.__file__).read_bytes()),
        "policies": list(POLICIES),
        "arm_count": 75,
        "intended_case_receipts": 1800,
        "component_model_arms": 25,
        "case_count_per_arm": 24,
        "new_api_calls": 0,
        "model_outputs_read": False,
        "gold_read": False,
        "selection_policy": "All new model/edge arms; no winning edge chosen from labels",
        "cost_scope": "Actual retained charges once per model arm; hypothetical suppression not actual savings",
        "fresh_throughput": None,
        "full_pipeline_rate": None,
    }
    write_json(output / "frozen.json", result)
    return result


def materialize_arm(
    prepared: Path,
    approved_prepared_sha256: str,
    input_arm: str,
    output: Path,
) -> dict[str, Any]:
    """Verify one immutable completed original arm, then materialize its three policies without labels."""
    from bench import p003_synthetic_relations_eval as evaluator
    from bench import p003_synthetic_resolution_eval as resolution_eval

    prepared, output = guard_path(prepared), guard_path(output)
    if output.exists():
        raise FileExistsError("New immutable per-arm composition output required")
    frozen_path = prepared / "frozen.json"
    if sha(frozen_path.read_bytes()) != approved_prepared_sha256:
        raise ValueError("Composition preparation differs from independently supplied authority")
    frozen = evaluator.load(frozen_path)
    if (
        frozen["helper_sha256"] != sha(Path(__file__).read_bytes())
        or frozen["composition_protocol_sha256"] != sha(Path(composition.__file__).read_bytes())
        or sha((prepared / "plan.json").read_bytes()) != frozen["plan_sha256"]
        or sha((prepared / "vector-components.json").read_bytes()) != frozen["vector_components_sha256"]
    ):
        raise ValueError("Approved pure composition code or frozen inputs changed")
    all_arms = evaluator.load(prepared / "plan.json")
    arms = [a for a in all_arms if a["input_arm"] == input_arm]
    if len(arms) != 3 or {a["policy"] for a in arms} != set(POLICIES):
        raise ValueError("Exactly three frozen policies for a declared model/edge required")
    arm = arms[0]
    directory, runtime_map = Path(arm["original_run_directory"]), Path(arm["runtime_map"])
    if not (directory / "report.json").is_file():
        raise ValueError("Original arm has no immutable final report yet; no partial composition")
    replay = resolution_eval.verify_run(
        directory,
        runtime_map,
        Path(frozen["source"]),
        Path(frozen["source_map"]),
        Path(frozen["images"]),
        Path(frozen["image_map"]),
        Path(frozen["aliases"]),
        frozen["alias_sha256"],
    )
    verified = deepcopy(replay["secondary_verified"])
    original = {r["id"]: r for r in replay["original_verified"]["rows"]}
    for row in verified["rows"]:
        row["original_status"] = original[row["id"]]["status"]
    if verified["config"]["model"] != arm["model"] or verified["config"]["image_edge"] != arm["image_edge"]:
        raise ValueError("Verified original model/edge differs from frozen composition plan")
    vectors = evaluator.load(prepared / "vector-components.json")
    results = [{"name": a["name"], **combine(vectors, verified, a["policy"])} for a in arms]
    output.mkdir(parents=True)
    write_json(output / "original-verification.json", replay)
    write_json(output / "results.json", results)
    receipt = {
        "version": VERSION,
        "input_arm": input_arm,
        "policy_count": 3,
        "case_receipts": 72,
        "prepared_sha256": approved_prepared_sha256,
        "results_sha256": sha((output / "results.json").read_bytes()),
        "verification_sha256": sha((output / "original-verification.json").read_bytes()),
        "original_model_charge_count": 1,
        "actual_retained_model_charges": verified["charges"],
        "gold_read": False,
        "new_api_calls": 0,
        "fresh_throughput": None,
        "full_pipeline_rate": None,
    }
    write_json(output / "frozen.json", receipt)
    return receipt
