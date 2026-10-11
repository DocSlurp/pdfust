"""Replay source-only synthetic geometry outcomes before opening evaluation labels."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

from bench import p003_synthetic_geometry as geometry
from bench import p003_synthetic_geometry_run as control
from bench import p003_synthetic_relations_eval as evaluation
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003, TRY301, C901
CODE = ("p003_synthetic_geometry.py", "p003_synthetic_geometry_run.py")


def replay(record: dict[str, Any], treatment: str, pool: Path) -> dict[str, Any]:
    """Reconstruct one complete receipt from authenticated evidence without labels."""
    row: dict[str, Any] = {"id": record["id"], "kind": record["kind"], "treatment": treatment}
    try:
        if record.get("status") != "ready":
            raise ValueError("Original source extraction refused")
        lines = []
        if treatment == "direct_vector":
            lines = geometry.vector_segments(record["drawings"])
        elif treatment.startswith("crop_raster"):
            edge = int(treatment.removeprefix("crop_raster"))
            image = next(i for i in record["images"] if i["scope"] == "crop" and i["edge"] == edge)
            with Image.open(guard_path(pool / image["path"])) as pixels:
                if list(pixels.size) != image["dimensions"]:
                    raise ValueError("Authenticated image dimensions differ")
                lines = geometry.raster_segments(pixels, image["viewport"])
            row["image_evidence"] = image
        elif treatment != "bbox_physical_proxy":
            raise ValueError("Unknown geometry treatment")
        row.update(geometry.classify(record, lines, physical_proxy=treatment == "bbox_physical_proxy"))
        row["status"] = "abstained" if row["abstained"] else "classified"
    except (ValueError, KeyError, StopIteration, TypeError) as error:
        row.update(
            status="source_refused",
            choice="unresolved",
            abstained=True,
            error={"type": type(error).__name__, "message": str(error)},
        )
    return row


def verify(directory: Path, authority: Path, frozen_sha256: str, context: dict[str, Any]) -> dict[str, Any]:
    """Authenticate independent code/freeze authority and replay all 96 outputs before gold."""
    directory, authority = guard_path(directory), guard_path(authority)
    raw = (directory / "frozen.json").read_bytes()
    if sha(raw) != frozen_sha256:
        raise ValueError("Control freeze differs from separately supplied authority")
    frozen, approved = json.loads(raw), evaluation.load(authority)
    if set(frozen["code_sha256"]) != set(CODE) or set(approved) != set(CODE):
        raise ValueError("Exact two-file geometry authority required")
    for name in CODE:
        expected = approved[name]
        if (
            frozen["code_sha256"][name] != expected
            or sha((directory / "code" / name).read_bytes()) != expected
            or sha(Path(control.__file__).with_name(name).read_bytes()) != expected
        ):
            raise ValueError("Archived or current geometry code differs from external authority")
    if (
        frozen["source_frozen_sha256"] != context["frozen_sha256"]
        or frozen["external_trusted_code_sha256"] != context["map_sha256"]
        or frozen["policy"] != geometry.POLICY
        or frozen["treatments"] != list(control.TREATMENTS)
        or frozen["gold_read"] is not False
        or frozen["generator_imported"] is not False
        or frozen["hosted_calls"] != 0
    ):
        raise ValueError("Control source identity or declared policy differs")
    inventory = {r["path"]: r["sha256"] for r in context["frozen"]["records"]}
    if frozen["source_inventory"] != inventory:
        raise ValueError("Complete source inventory differs")
    rows: list[dict[str, Any]] = []
    for record in context["records"]:
        source = {k: record.get(k) for k in ("id", "kind", "status", "pair_source_ids", "source", "drawings")}
        if evaluation.load(directory / "sources" / (record["id"] + ".json")) != source:
            raise ValueError("Copied literal source or drawing evidence differs")
        rows.extend(replay(record, treatment, context["pool"]) for treatment in control.TREATMENTS)
    results = (directory / "results.json").read_bytes()
    if sha(results) != frozen["results_sha256"] or json.loads(results) != {"results": rows}:
        raise ValueError("Frozen outcomes fail complete source-only replay")
    report = evaluation.load(directory / "report.json")
    counts = {
        name: {
            "case_count": 24,
            "status_counts": dict(Counter(r["status"] for r in rows if r["treatment"] == name)),
            "choice_counts": dict(Counter(r["choice"] for r in rows if r["treatment"] == name)),
        }
        for name in control.TREATMENTS
    }
    if report["results"] != rows or report["by_treatment"] != counts or report["hosted_calls"] != 0:
        raise ValueError("Reported outcomes differ from independent replay")
    return {
        "rows": rows,
        "frozen_sha256": frozen_sha256,
        "authority_sha256": sha(authority.read_bytes()),
        "results_sha256": sha(results),
        "code_sha256": approved,
        "source_frozen_sha256": context["frozen_sha256"],
        "reported_resources": report["metrics"],
        "verification": "All 96 outcomes independently replayed before gold",
    }


def score(verified: dict[str, Any], gold: dict[str, dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    """Separate full intended label agreement, abstention, and conditional agreement."""

    def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
        decisive = [r for r in rows if r["status"] == "classified"]
        correct = sum(r["choice"] == gold[r["id"]]["expected_choice"] for r in decisive)
        return {
            "intended_count": len(rows),
            "classified_count": len(decisive),
            "abstained_count": sum(r["status"] == "abstained" for r in rows),
            "source_refused_count": sum(r["status"] == "source_refused" for r in rows),
            "author_label_matches": correct,
            "strict_author_label_fraction": correct / len(rows) if rows else None,
            "conditional_classified_author_label_fraction": correct / len(decisive) if decisive else None,
        }

    treatments = {}
    for name in control.TREATMENTS:
        rows = [r for r in verified["rows"] if r["treatment"] == name]
        by_id = {r["id"]: r for r in rows}
        treatments[name] = {
            "all_24": aggregate(rows),
            "visually_cued_18": aggregate([r for r in rows if not gold[r["id"]]["evidence_limitation"]]),
            "indeterminate_6": aggregate([r for r in rows if gold[r["id"]]["evidence_limitation"]]),
            "per_kind": {kind: aggregate([r for r in rows if r["kind"] == kind]) for kind in ("cell", "row", "wrap")},
            "twins": [
                {
                    "case_ids": pair["case_ids"],
                    "kind": pair["kind"],
                    "choices": [by_id[i]["choice"] for i in pair["case_ids"]],
                    "both_abstained": all(by_id[i]["status"] == "abstained" for i in pair["case_ids"]),
                    "author_label_matches": sum(
                        by_id[i]["status"] == "classified" and by_id[i]["choice"] == gold[i]["expected_choice"]
                        for i in pair["case_ids"]
                    ),
                }
                for pair in context["frozen"]["counterfactual_twins"]
            ],
            "claim_scope": "Physical bbox proxy is not logical membership"
            if name == "bbox_physical_proxy"
            else "Actual vector rules or crop pixels; hidden-label agreement, not inferred certainty",
        }
    return {
        "treatments": treatments,
        "hosted_calls": 0,
        "full_pipeline_rate": None,
        "probabilities": None,
        "source_assignments_applied": 0,
        "gold_access": "Evaluation only after complete independent source/code/result replay",
        "interpretation": "Indeterminate opposing labels cannot both be recovered from identical evidence",
    }


def main() -> None:
    """Audit explicit immutable source/control evidence, then evaluate separately supplied gold."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "source-trusted-code", "control", "control-trusted-code", "gold", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--control-frozen-sha256", required=True)
    parser.add_argument("--gold-sha256", required=True)
    args = parser.parse_args()
    output = guard_path(args.output)
    if output.exists():
        raise FileExistsError("Fresh independent evaluation output required")
    context = evaluation.source_context(args.source, args.source_trusted_code)
    verified = verify(args.control, args.control_trusted_code, args.control_frozen_sha256, context)
    gold = evaluation.load_gold(args.gold, args.gold_sha256, context)
    report = {
        "schema": 1,
        "verification": {k: v for k, v in verified.items() if k != "rows"},
        "gold_sha256": args.gold_sha256,
        **score(verified, gold, context),
    }
    write_json(output, report)
    print(json.dumps({name: v["all_24"] for name, v in report["treatments"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
