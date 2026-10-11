"""Prepare label-free offline compositions of retained vector and same-model decisions."""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

# ruff: noqa: EM101, TRY003, PLR0913, PLR0917, PLR2004, PLC0415, C901, PLR0912
VERSION = "p003-geometry-decision-composition-v1"
POLICIES = ("vector_first", "agreement_only", "either_evidence_conflicts_abstain")
MODELS = {
    "pplx": "perplexity/pplx-decider-v1.1-27b",
    "clef": "cloudflare/clef",
    "clefflash": "cloudflare/clef-flash",
    "clefomni": "cloudflare/clef-omni",
    "lunadec": "openai/gpt-6-luna-decisions",
}
EDGES = (128, 512)


def compose(vector: dict[str, Any], model: dict[str, Any], policy: str) -> dict[str, Any]:
    """Apply one fixed label-free policy; retain component errors and abstentions."""
    if policy not in POLICIES:
        raise ValueError("Unknown composition policy")
    if vector["id"] != model["id"] or vector["kind"] != model["kind"]:
        raise ValueError("Component source identities differ")
    if vector.get("treatment") != "direct_vector":
        raise ValueError("Only independently verified direct-vector control is admitted")
    vchoice = vector.get("choice")
    mchoice = model.get("receipt", {}).get("choice")
    vdecisive = vector["status"] == "classified" and vchoice in ("same", "separate")
    mdecisive = model["status"] == "valid_nonabstaining" and mchoice in ("same", "separate")
    if vector["status"] == "classified" and not vdecisive:
        raise ValueError("Invalid decisive vector choice")
    if model["status"] == "valid_nonabstaining" and not mdecisive:
        raise ValueError("Invalid decisive model choice")
    conflict = vdecisive and mdecisive and vchoice != mchoice
    choice, selected, reason = "unresolved", None, "Neither component supplies a usable decision"
    if policy == "vector_first":
        if vdecisive:
            choice, selected, reason = str(vchoice), "vector", "Vector is decisive"
        elif vector["status"] == "abstained" and mdecisive:
            choice, selected, reason = str(mchoice), "same_model", "Vector abstains; same configured model is decisive"
        elif vector["status"] != "abstained":
            reason = "Vector input failed/refused; this policy does not replace that failure"
    elif policy == "agreement_only":
        if vdecisive and mdecisive and not conflict:
            choice, selected, reason = str(vchoice), "agreement", "Both components are decisive and equal"
        else:
            reason = "Conflict" if conflict else "Both components must supply equal decisive choices"
    elif conflict:
        reason = "Conflicting decisive choices; abstain"
    elif vdecisive or mdecisive:
        choice = str(vchoice if vdecisive else mchoice)
        selected = "agreement" if vdecisive and mdecisive else "vector" if vdecisive else "same_model"
        reason = "Available decisive evidence; no decisive conflict"
    return {
        "id": vector["id"],
        "kind": vector["kind"],
        "policy": policy,
        "choice": choice,
        "status": "classified" if selected is not None else "abstained",
        "selected_component": selected,
        "reason": reason,
        "decisive_conflict": conflict,
        "vector_status": vector["status"],
        "model_status": model["status"],
        "vector_choice": vchoice,
        "model_choice": mchoice,
        "component_error": vector["status"] not in ("classified", "abstained")
        or model["status"] not in ("valid_nonabstaining", "valid_abstention"),
        "probability": None,
        "probability_basis": "No merged or calibrated confidence inferred",
        "raw_model_receipt": model.get("receipt"),
        "original_model_status": model.get("original_status"),
        "raw_response_sha256": model.get("response_sha256"),
    }


def prepare(
    source: Path,
    source_map: Path,
    queue: Path,
    plan: Path,
    plan_sha256: str,
    aliases: Path,
    alias_sha256: str,
    vector: Path,
    vector_map: Path,
    vector_frozen_sha256: str,
    output: Path,
) -> dict[str, Any]:
    """Reauthenticate source/outputs and freeze all 30 policies without opening labels."""
    from bench import p003_synthetic_alias_replay as alias  # type: ignore[attr-defined]  # current root dependency
    from bench import p003_synthetic_geometry_eval as geometry_eval
    from bench import p003_synthetic_relations_eval as evaluation
    from bench import p003_synthetic_relations_run as runner
    from bench.silver import guard_path, sha, write_json

    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh composition directory required")
    began, cpu = time.perf_counter(), time.process_time()
    for path in (source, source_map, queue, plan, aliases, vector, vector_map):
        guard_path(path)
    if sha(plan.read_bytes()) != plan_sha256:
        raise ValueError("Original 48-arm plan differs from approved authority")
    original_plan = evaluation.load(plan)
    if not isinstance(original_plan, list) or len(original_plan) != 48:
        raise ValueError("Exact approved 48-arm original plan required")
    planned = {entry["name"]: entry for entry in original_plan}
    context = evaluation.source_context(source, source_map)
    verified_vector = geometry_eval.verify(vector, vector_map, vector_frozen_sha256, context)
    vectors = {row["id"]: row for row in verified_vector["rows"] if row["treatment"] == "direct_vector"}
    if len(vectors) != 24:
        raise ValueError("Complete unique 24-case vector inventory required")
    all_arms, input_runs, model_receipts = [], {}, {}
    for short, slug in MODELS.items():
        for edge in EDGES:
            name = f"synth-{short}-geometry-crop{edge}-r0-c3"
            if name not in planned:
                raise ValueError("Required fixed model/edge absent from approved original plan")
            directory, runtime_map = queue / name, queue / "trusted-code" / (name + ".json")
            replayed = alias.replay(directory, runtime_map, context, aliases, alias_sha256)
            original, secondary = replayed["original_verified"], replayed["secondary_verified"]
            cfg = secondary["config"]
            if (
                cfg["model"] != slug
                or cfg["image_edge"] != edge
                or cfg["mode"] != "text_geometry"
                or cfg["viewport"] != "crop"
                or cfg["model_fallback"] is not False
            ):
                raise ValueError("Retained input does not match predeclared fixed model/image treatment")
            original_rows = {r["id"]: r for r in original["rows"]}
            rows = [{**r, "original_status": original_rows[r["id"]]["status"]} for r in secondary["rows"]]
            if len(rows) != 24 or set(vectors) != {r["id"] for r in rows}:
                raise ValueError("Model outcomes must preserve complete intended 24 cases")
            model_receipts[name] = {
                "config": cfg,
                "rows": rows,
                "alias_receipts": secondary["alias_receipts"],
                "actual_retained_charges": original["charges"],
                "actual_retained_metrics": original["reported_metrics"],
                "original_outcomes_changed": False,
            }
            inventory = {
                "frozen.json": sha((directory / "frozen.json").read_bytes()),
                "report.json": sha((directory / "report.json").read_bytes()),
            }
            for row in rows:
                index = row["index"]
                for suffix in (
                    "canonical-request.json",
                    "wire-request.json",
                    "wire-encoded.json",
                    "response.json",
                    "result.json",
                ):
                    relative = f"question-{index}-{suffix}"
                    path = directory / relative
                    if path.is_file():
                        inventory[relative] = sha(path.read_bytes())
            input_runs[name] = {
                "directory": str(directory.resolve()),
                "runtime_map": str(runtime_map.resolve()),
                "runtime_map_sha256": sha(runtime_map.read_bytes()),
                "artifacts": inventory,
            }
            for policy in POLICIES:
                composed = [compose(vectors[r["id"]], r, policy) for r in rows]
                suppressed = (
                    sum(vectors[r["id"]]["status"] == "classified" for r in rows) if policy == "vector_first" else 0
                )
                all_arms.append(
                    {
                        "name": name + "-" + policy,
                        "retained_model_arm": name,
                        "model": slug,
                        "image_edge": edge,
                        "mode": "text_geometry",
                        "viewport": "crop",
                        "policy": policy,
                        "results": composed,
                        "intended_cases": 24,
                        "actual_retained_charges_reference": name,
                        "counterfactual_suppressed_request_count": suppressed,
                        "counterfactual_cost_savings": None,
                        "fresh_throughput": None,
                        "cost_scope": "All original calls actually occurred; no actual financial saving claimed",
                    }
                )
    output.mkdir(parents=True)
    (output / "code").mkdir()
    code_names = tuple(
        dict.fromkeys(
            (
                *runner.CODE_FILES,
                "p003_geometry_decision_composition.py",
                "p003_synthetic_relations_eval.py",
                "p003_synthetic_alias_replay.py",
                "p003_synthetic_geometry.py",
                "p003_synthetic_geometry_run.py",
                "p003_synthetic_geometry_eval.py",
            )
        )
    )
    code = {}
    for name in code_names:
        path = Path(__file__) if name == Path(__file__).name else Path(runner.__file__).with_name(name)
        raw = path.read_bytes()
        (output / "code" / name).write_bytes(raw)
        code[name] = sha(raw)
    write_json(
        output / "source-evidence.json",
        {"records": context["records"], "source_frozen_sha256": context["frozen_sha256"]},
    )
    write_json(output / "components.json", {"vector_rows": list(vectors.values()), "model_runs": model_receipts})
    write_json(
        output / "composition-plan.json",
        {
            "version": VERSION,
            "policies": POLICIES,
            "models": MODELS,
            "image_edges": EDGES,
            "arms": all_arms,
            "gold_read": False,
            "charges_scope": "Ten unique original runs; reused policy charges must not be summed thirty times",
        },
    )
    frozen = {
        "version": VERSION,
        "prepared_unix_seconds": time.time(),
        "gold_read": False,
        "new_api_calls": 0,
        "new_gpu_work": False,
        "original_outcomes_changed": False,
        "source": str(source.resolve()),
        "source_map": str(source_map.resolve()),
        "source_map_sha256": context["map_sha256"],
        "source_frozen_sha256": context["frozen_sha256"],
        "plan": str(plan.resolve()),
        "plan_sha256": plan_sha256,
        "aliases": str(aliases.resolve()),
        "alias_sha256": alias_sha256,
        "vector_directory": str(vector.resolve()),
        "vector_map": str(vector_map.resolve()),
        "vector_frozen_sha256": vector_frozen_sha256,
        "vector_verification": {k: v for k, v in verified_vector.items() if k != "rows"},
        "input_runs": input_runs,
        "code_sha256": code,
        "arm_count": 30,
        "case_count_per_arm": 24,
        "artifact_sha256": {
            name: sha((output / name).read_bytes())
            for name in ("source-evidence.json", "components.json", "composition-plan.json")
        },
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": (
                "Single CPU preparation process, including full source/render/response replay; "
                "unsampled lifetime RSS includes imports"
            ),
        },
    }
    write_json(output / "frozen.json", frozen)
    return frozen


def main() -> None:
    """Prepare only; this CLI has no labels, hosted client, or scoring option."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "source-map", "queue", "plan", "aliases", "vector", "vector-map", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("plan-sha256", "alias-sha256", "vector-frozen-sha256"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    frozen = prepare(
        args.source,
        args.source_map,
        args.queue,
        args.plan,
        args.plan_sha256,
        args.aliases,
        args.alias_sha256,
        args.vector,
        args.vector_map,
        args.vector_frozen_sha256,
        args.output,
    )
    print(json.dumps({"arm_count": frozen["arm_count"], "resources": frozen["resources"]}, sort_keys=True))


if __name__ == "__main__":
    main()
