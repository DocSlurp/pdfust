"""Independent DEV oracle over already frozen indivisible literal row-band alternatives."""

# ruff: noqa: EM101, TRY003, PLR2004, C901
from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

from bench import p003_candidate_bands as bands
from bench import p003_valid_regions_oracle as pools
from bench.generalization_report import load_corpus
from bench.p003_report import strict_scores
from bench.silver import guard_path, sha


def read(path: Path) -> dict[str, Any]:
    """Read only an explicitly supplied guarded artifact."""
    return json.loads(guard_path(path).read_bytes())


def rebuild(page: dict[str, Any], threshold: float) -> dict[str, Any]:
    """Rebuild the entire source-only menu without inspecting references."""
    crops = []
    for crop in page["crops"]:
        valid = [a for a in crop["attempts"] if a["valid"]]
        plan = (
            bands.freeze(crop["viewport"], [json.loads(a["canonical_json"]) for a in valid], threshold=threshold)
            if len(valid) == 2
            else None
        )
        alternatives = (
            bands.alternatives(plan)
            if plan
            else [
                {
                    "canonical_json": a["canonical_json"],
                    "sha256": a["state_sha256"],
                    "provenance": [{"whole_original": a["baseline_index"]}],
                }
                for a in valid
            ]
        )
        crops.append(
            {
                "index": crop["index"],
                "viewport": crop["viewport"],
                "image_sha256": crop["image_sha256"],
                "valid_baseline_indexes": crop["valid_baseline_indexes"],
                "plan": plan,
                "status": plan["status"] if plan else "fewer_than_two_valid_controls",
                "alternatives": alternatives,
            }
        )
    return {
        "id": page["id"],
        "page_viewport": page["page_metadata"]["viewport"],
        "threshold": threshold,
        "source_admission_sha256": page["snapshot_sha256"],
        "crops": crops,
        "quality_scored": False,
    }


def enumerate_page(page: dict[str, Any]) -> list[tuple[tuple[int, ...], dict[str, Any]]]:
    """Enumerate bounded atomic whole-page alternatives; never repair invalid combinations."""
    options = [range(len(c["alternatives"])) for c in page["crops"]]
    count = 1
    for option in options:
        count *= len(option)
    if count > pools.MAX_COMPOSITIONS:
        raise ValueError("Frozen band composition bound exceeded")
    predictions = []
    for indexes in itertools.product(*options):
        try:
            state = bands.compose(
                [
                    json.loads(c["alternatives"][i]["canonical_json"])
                    for c, i in zip(page["crops"], indexes, strict=True)
                ],
                [c["viewport"] for c in page["crops"]],
                page["page_viewport"],
            )
        except ValueError:
            continue
        predictions.append((indexes, {"id": page["id"], "status": "ok", "tables": state["tables"]}))
    return predictions


def analyze(
    directory: Path,
    corpus: Path,
    *,
    trusted_code: dict[str, str],
    admission_trusted_code: dict[str, str],
    baseline_trusted_code: list[dict[str, str]],
) -> dict[str, Any]:
    """Authenticate and enumerate every declared menu before separate reference scoring."""
    directory, corpus = guard_path(directory), guard_path(corpus)
    frozen = read(directory / "frozen.json")
    if frozen["quality_references_used_in_freeze"] is not False or frozen["thresholds"] != list(bands.THRESHOLDS):
        raise ValueError("Expected the predeclared source-only band freeze")
    for name, digest in frozen["code_sha256"].items():
        if (
            Path(name).name != name
            or trusted_code.get(name) != digest
            or sha((directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Band archive lacks independent code authentication")
    if frozen["code_sha256"]["p003_candidate_bands.py"] != sha(Path(bands.__file__).read_bytes()):
        raise ValueError("Current band helper differs from authenticated frozen helper")
    nested = directory / "source-admission"
    if sha((nested / "frozen.json").read_bytes()) != frozen["source_admission_frozen_sha256"]:
        raise ValueError("Nested source admission freeze changed")
    source_frozen = read(nested / "frozen.json")
    if source_frozen["records"] != frozen["records"] or source_frozen["manifest_sha256"] != frozen["manifest_sha256"]:
        raise ValueError("Outer source inventory differs from admission freeze")
    expected_ids = {r["id"] for r in frozen["records"]}
    inventories = {}
    for threshold in frozen["thresholds"]:
        label = f"iou-{threshold:.2f}"
        hashes = frozen["prepared_inventory_sha256"][label]
        if set(hashes) != expected_ids:
            raise ValueError("Band freeze omits pages")
        pages, choices = [], []
        for record in frozen["records"]:
            id_ = record["id"]
            source_path = nested / f"{id_}-valid-region-pools.json"
            if sha(source_path.read_bytes()) != source_frozen["valid_region_pools_sha256"][id_]:
                raise ValueError("Source admission pool changed")
            path = directory / label / f"{id_}-bands.json"
            page = read(path)
            if sha(path.read_bytes()) != hashes[id_] or page != rebuild(read(source_path), threshold):
                raise ValueError("Band alternatives differ from exact source-only reconstruction")
            pages.append(page)
            choices.append(enumerate_page(page))
        inventories[label] = (pages, choices)
    # Nested verifier authenticates every original PDF/crop/body and rebuilds its pools before reading gold.
    whole_control = pools.analyze(
        nested, corpus, trusted_code=admission_trusted_code, baseline_trusted_code=baseline_trusted_code
    )
    _, targets = load_corpus(corpus)
    refs = {p["id"]: p for p in targets["pages"]}
    treatments = {}
    for label, (pages, choices) in inventories.items():
        outcomes = [pools.oracle_page(refs[p["id"]], c) for p, c in zip(pages, choices, strict=True)]
        treatments[label] = {
            "scores": strict_scores(targets["pages"], [o["selected"] for o in outcomes]),
            "independent_complete_table_ceiling": sum(o["maximum_complete_tables"] for o in outcomes),
            "feasible_compositions": sum(len(c) for c in choices),
            "pages": [
                {
                    "id": p["id"],
                    "chosen_alternative_indexes": o["origins"],
                    "feasible_compositions": len(c),
                    "score": o.get("score"),
                }
                for p, c, o in zip(pages, choices, outcomes, strict=True)
            ],
        }
    return {
        "scope": "Posthoc DEV literal-band oracle ceiling, not model quality or achievable selection",
        "frozen_sha256": sha((directory / "frozen.json").read_bytes()),
        "code_sha256": frozen["code_sha256"],
        "whole_valid_crop_control": whole_control["scores"],
        "treatments": treatments,
        "new_api_calls": 0,
        "runtime_performance_claim": False,
    }
