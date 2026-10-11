"""Authenticate frozen resolution compositions and replay fixed policies before label scoring."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import p003_geometry_composition_eval as scoring
from bench import p003_synthetic_geometry_eval as geometry
from bench import p003_synthetic_relations_eval as evaluation
from bench import p003_synthetic_resolution_composition as composition
from bench import p003_synthetic_resolution_eval as resolution
from bench.silver import guard_path, sha

# ruff: noqa: C901, PLR0912, EM101, TRY003, PLR0913, PLR0917, PLR2004


def prepare_context(
    prepared: Path,
    authority: Path,
    authority_sha256: str,
    prepared_sha256: str,
    vector_map: Path,
    vector_map_sha256: str,
) -> dict[str, Any]:
    """Pin independent code, source, vector and complete 75-treatment authorities without gold."""
    prepared, authority = guard_path(prepared), guard_path(authority)
    if (
        sha(authority.read_bytes()) != authority_sha256
        or sha((prepared / "frozen.json").read_bytes()) != prepared_sha256
    ):
        raise ValueError("Separately approved composition authority or preparation changed")
    frozen, approved = evaluation.load(prepared / "frozen.json"), evaluation.load(authority)
    if approved["prepared_sha256"] != prepared_sha256:
        raise ValueError("External authority does not pin this preparation")
    for key, module in (("helper_sha256", composition), ("composition_protocol_sha256", composition.composition)):
        if approved[key] != frozen[key] or sha(Path(module.__file__).read_bytes()) != approved[key]:
            raise ValueError("Executed fixed composition helper differs from independent authority")
    for filename, key in (("plan.json", "plan_sha256"), ("vector-components.json", "vector_components_sha256")):
        if sha((prepared / filename).read_bytes()) != frozen[key]:
            raise ValueError("Frozen composition inventory changed")
    if frozen["arm_count"] != 75 or frozen["component_model_arms"] != 25 or frozen["case_count_per_arm"] != 24:
        raise ValueError("Complete 25-model-treatment by three-policy inventory required")
    if frozen["gold_read"] is not False or frozen["model_outputs_read"] is not False or frozen["new_api_calls"] != 0:
        raise ValueError("Preparation must precede model outcomes and labels without calls")
    queue_path = guard_path(Path(frozen["queue_prepared"])) / "frozen.json"
    if sha(queue_path.read_bytes()) != frozen["queue_prepared_sha256"]:
        raise ValueError("Original predeclared queue changed")
    queue = evaluation.load(queue_path)
    expected = composition.arm_plan(queue["plan"])
    actual = evaluation.load(prepared / "plan.json")
    if [{k: row[k] for k in expected[0]} for row in actual] != expected:
        raise ValueError("Full fixed policy/model/edge inventory differs")
    for arm in actual:
        if Path(arm["original_run_directory"]) != Path(frozen["hosted_queue"]) / arm["input_arm"]:
            raise ValueError("Original arm path differs from declared queue")
        if Path(arm["runtime_map"]) != Path(frozen["hosted_queue"]) / "trusted-code" / (arm["input_arm"] + ".json"):
            raise ValueError("Runtime authority path differs from declared queue")
    context = evaluation.source_context(Path(frozen["source"]), Path(frozen["source_map"]))
    if (
        context["frozen_sha256"] != frozen["source_frozen_sha256"]
        or context["map_sha256"] != frozen["source_map_sha256"]
    ):
        raise ValueError("Source authority differs from fixed preparation")
    if (
        sha(vector_map.read_bytes()) != vector_map_sha256
        or vector_map_sha256 != frozen["vector_receipt"]["external_map_sha256"]
    ):
        raise ValueError("Vector authority differs from separately approved map")
    vector = geometry.verify(
        Path(frozen["vector_receipt"]["directory"]), vector_map, frozen["vector_receipt"]["frozen_sha256"], context
    )
    vectors = [row for row in vector["rows"] if row["treatment"] == "direct_vector"]
    if vectors != evaluation.load(prepared / "vector-components.json"):
        raise ValueError("Actual source/vector replay differs from fixed components")
    return {
        "frozen": frozen,
        "context": context,
        "vectors": vectors,
        "plan": actual,
        "prepared_sha256": prepared_sha256,
    }


def verify_arm(directory: Path, prepared: dict[str, Any]) -> dict[str, Any]:
    """Replay actual pixels/wires/raw responses and all three complete outcomes without reading labels."""
    directory = guard_path(directory)
    frozen = evaluation.load(directory / "frozen.json")
    if frozen["prepared_sha256"] != prepared["prepared_sha256"] or frozen["policy_count"] != 3:
        raise ValueError("Materialized arm does not use approved complete fixed policies")
    if frozen["gold_read"] is not False or frozen["new_api_calls"] != 0 or frozen["case_receipts"] != 72:
        raise ValueError("Materialization must preserve 72 label-free, no-call outcomes")
    for name, key in (("results.json", "results_sha256"), ("original-verification.json", "verification_sha256")):
        if sha((directory / name).read_bytes()) != frozen[key]:
            raise ValueError("Frozen materialized artifact changed")
    arms = [a for a in prepared["plan"] if a["input_arm"] == frozen["input_arm"]]
    if len(arms) != 3:
        raise ValueError("Materialized model arm is absent from fixed plan")
    root, arm = prepared["frozen"], arms[0]
    replay = resolution.verify_run(
        Path(arm["original_run_directory"]),
        Path(arm["runtime_map"]),
        Path(root["source"]),
        Path(root["source_map"]),
        Path(root["images"]),
        Path(root["image_map"]),
        Path(root["aliases"]),
        root["alias_sha256"],
    )
    if replay != evaluation.load(directory / "original-verification.json"):
        raise ValueError("Original source/pixel/wire/raw/accounting replay differs from materialization")
    verified = deepcopy(replay["secondary_verified"])
    originals = {r["id"]: r for r in replay["original_verified"]["rows"]}
    for row in verified["rows"]:
        row["original_status"] = originals[row["id"]]["status"]
    expected = [{"name": a["name"], **composition.combine(prepared["vectors"], verified, a["policy"])} for a in arms]
    if (
        expected != evaluation.load(directory / "results.json")
        or frozen["actual_retained_model_charges"] != verified["charges"]
    ):
        raise ValueError("Fixed complete-case composition or original accounting differs")
    return {
        "input_arm": frozen["input_arm"],
        "model": arm["model"],
        "image_edge": arm["image_edge"],
        "results": expected,
        "original": replay,
        "actual_charges_once": verified["charges"],
        "materialized_frozen_sha256": sha((directory / "frozen.json").read_bytes()),
        "new_api_calls": 0,
    }


def score(verified: dict[str, Any], gold: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Keep one actual model charge separate from three counterfactual policy outcomes."""
    return {
        "input_arm": verified["input_arm"],
        "model": verified["model"],
        "image_edge": verified["image_edge"],
        "policies": [
            {"name": row["name"], "policy": row["policy"], "scores": scoring.summary(row["rows"], gold)}
            for row in verified["results"]
        ],
        "actual_charges_once": verified["actual_charges_once"],
        "new_api_calls": 0,
        "fresh_throughput": None,
        "hypothetical_cost_saving_usd": None,
    }
