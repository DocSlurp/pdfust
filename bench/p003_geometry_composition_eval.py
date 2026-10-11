"""Independent offline replay and label scoring of frozen geometry/model compositions."""

from __future__ import annotations

# ruff: noqa: C901, PLR0912, PLR2004, EM101, TRY003
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_geometry_decision_composition as composition
from bench import p003_synthetic_relations_eval as evaluation
from bench.silver import guard_path, sha


def verify(directory: Path, authority: Path, authority_sha256: str, frozen_sha256: str) -> dict[str, Any]:
    """Authenticate all code and inputs, then reconstruct all policies before labels."""
    directory, authority = guard_path(directory), guard_path(authority)
    if sha(authority.read_bytes()) != authority_sha256:
        raise ValueError("Composition authority differs from separately approved hash")
    raw = (directory / "frozen.json").read_bytes()
    if sha(raw) != frozen_sha256:
        raise ValueError("Composition freeze differs from separately approved hash")
    frozen, approved = json.loads(raw), evaluation.load(authority)
    if frozen["code_sha256"] != approved:
        raise ValueError("Complete composition code inventory differs from authority")
    for name, digest in approved.items():
        if Path(name).name != name or sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived composition code differs from authority")
        if sha(Path(composition.__file__).with_name(name).read_bytes()) != digest:
            raise ValueError("Current composition dependency differs from authority")
    if frozen["arm_count"] != 30 or frozen["case_count_per_arm"] != 24 or frozen["gold_read"] is not False:
        raise ValueError("Composition inventory or label isolation declaration differs")
    if frozen["new_api_calls"] != 0 or frozen["original_outcomes_changed"] is not False:
        raise ValueError("Composition scope must preserve original outcomes without calls")
    for name, digest in frozen["artifact_sha256"].items():
        if Path(name).name != name or sha((directory / name).read_bytes()) != digest:
            raise ValueError("Frozen composition artifact differs")
    for receipt in frozen["input_runs"].values():
        source = guard_path(Path(receipt["directory"]))
        if sha(guard_path(Path(receipt["runtime_map"])).read_bytes()) != receipt["runtime_map_sha256"]:
            raise ValueError("Component runtime authority changed")
        for name, digest in receipt["artifacts"].items():
            if Path(name).name != name or sha((source / name).read_bytes()) != digest:
                raise ValueError("Original component artifact changed")
    with tempfile.TemporaryDirectory(prefix="p003-composition-replay-") as temporary:
        replay = Path(temporary) / "replay"
        composition.prepare(
            Path(frozen["source"]),
            Path(frozen["source_map"]),
            Path(next(iter(frozen["input_runs"].values()))["directory"]).parent,
            Path(frozen["plan"]),
            frozen["plan_sha256"],
            Path(frozen["aliases"]),
            frozen["alias_sha256"],
            Path(frozen["vector_directory"]),
            Path(frozen["vector_map"]),
            frozen["vector_frozen_sha256"],
            replay,
        )
        for name, digest in frozen["artifact_sha256"].items():
            if sha((replay / name).read_bytes()) != digest:
                raise ValueError("Source/response policy replay differs from frozen composition")
    context = evaluation.source_context(Path(frozen["source"]), Path(frozen["source_map"]))
    return {
        "frozen_sha256": frozen_sha256,
        "authority_sha256": authority_sha256,
        "context": context,
        "components": evaluation.load(directory / "components.json"),
        "plan": evaluation.load(directory / "composition-plan.json"),
        "new_api_calls": 0,
        "fresh_pages_per_minute": None,
        "gold_accessed": False,
    }


def summary(rows: list[dict[str, Any]], gold: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Count every intended source case, without inventing combined probabilities."""
    if len(rows) != 24 or len({r["id"] for r in rows}) != 24 or {r["id"] for r in rows} != set(gold):
        raise ValueError("Complete unique 24-case denominator required")

    def counts(selected: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "intended_count": len(selected),
            "author_label_matches": sum(r.get("choice") == gold[r["id"]]["expected_choice"] for r in selected),
            "classified": sum(r["status"] == "classified" for r in selected),
            "abstained": sum(r["status"] == "abstained" for r in selected),
            "status_counts": dict(Counter(r["status"] for r in selected)),
            "component_errors": sum(bool(r.get("component_error")) for r in selected),
            "decisive_conflicts": sum(bool(r.get("decisive_conflict")) for r in selected),
            "selected_components": dict(Counter(r.get("selected_component") for r in selected)),
        }

    return {
        "all_24": counts(rows),
        "visually_cued_18": counts([r for r in rows if not gold[r["id"]]["evidence_limitation"]]),
        "indeterminate_6": counts([r for r in rows if gold[r["id"]]["evidence_limitation"]]),
        "per_kind": {kind: counts([r for r in rows if r["kind"] == kind]) for kind in ("cell", "row", "wrap")},
    }


def score(verified: dict[str, Any], gold: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Keep actual component baselines and all fixed policies separate."""
    components = verified["components"]
    models = {}
    for name, run in components["model_runs"].items():
        rows = [
            {
                **r,
                "choice": r.get("receipt", {}).get("choice"),
                "status": "classified"
                if r["status"] == "valid_nonabstaining"
                else "abstained"
                if r["status"] == "valid_abstention"
                else r["status"],
            }
            for r in run["rows"]
        ]
        models[name] = {"scores": summary(rows, gold), "actual_retained_charges": run["actual_retained_charges"]}
    return {
        "vector_baseline": summary(components["vector_rows"], gold),
        "model_baselines": models,
        "arms": [
            {
                "name": a["name"],
                "model": a["model"],
                "image_edge": a["image_edge"],
                "policy": a["policy"],
                "scores": summary(a["results"], gold),
            }
            for a in verified["plan"]["arms"]
        ],
        "new_api_calls": 0,
        "fresh_pages_per_minute": None,
        "cost_scope": (
            "Ten original model runs actually occurred; policies reuse them without new charges or measured savings"
        ),
        "probabilities": None,
        "source_assignments": None,
    }
