"""Independent conditional DEV ceiling for frozen source-segment topology candidates."""

# ruff: noqa: EM101, TRY003, C901, PLR0912
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bench import p003_segment_topology as segments
from bench.generalization_report import load_corpus
from bench.p003_gate_run import authenticate
from bench.p003_report import strict_scores
from bench.silver import canonical, guard_path, sha

OBJECTIVE = ("strict_exact_cells", "complete_tables", "correct_text_cells")


def read(path: Path) -> Any:  # noqa: ANN401
    """Read only explicitly supplied guarded artifacts."""
    return json.loads(guard_path(path).read_bytes())


def fixed_crop_inventory(source: dict[str, Any], crops: list[list[dict[str, Any]]]) -> None:
    """Prove candidate table presence/bbox and crop ownership cannot change across choices."""
    owned = set()
    for pool in crops:
        if not pool:
            raise ValueError("Empty frozen topology pool")
        boxes = [t["bbox"] for t in pool[0]["state"]["tables"]]
        crop_ids = set()
        for candidate in pool:
            state = candidate["state"]
            if [t["bbox"] for t in state["tables"]] != boxes:
                raise ValueError("Candidate table bbox/presence varies; factorized oracle is invalid")
            for table in state["tables"]:
                crop_ids.update(i for cell in table["cells"] for i in cell["source_ids"])
        if crop_ids & owned:
            raise ValueError("Candidate source ownership crosses crops; factorized oracle is invalid")
        owned.update(crop_ids)
        # Geometry conflicts are then constant; source conflicts cannot introduce additional variation.
    if owned - {w["id"] for w in source["words"]}:
        raise ValueError("Candidate owns foreign source identifiers")


def prediction(
    source: dict[str, Any], pools: list[list[dict[str, Any]]], indexes: list[int], ident: str
) -> dict[str, Any]:
    """Compose complete source-safe states using unchanged conflict refusal."""
    state = segments.compose(source, [p[i]["state"] for p, i in zip(pools, indexes, strict=True)])
    return {"id": ident, "status": "ok", "tables": state["tables"]}


def oracle_page(target: dict[str, Any], source: dict[str, Any], pools: list[list[dict[str, Any]]]) -> dict[str, Any]:
    """Factor fixed geometry matching; verify summed objective against final whole-page score."""
    fixed_crop_inventory(source, pools)
    control_indexes = [0] * len(pools)
    control = prediction(source, pools, control_indexes, target["id"])
    base = strict_scores([target], [control])
    matches = base["pages"][0]["matches"]
    choices, complete_choices, deltas, complete_deltas = [], [], [], []
    evaluated = 0
    for crop_index, pool in enumerate(pools):
        results = []
        for index in range(len(pool)):
            indexes = control_indexes.copy()
            indexes[crop_index] = index
            scored = strict_scores([target], [prediction(source, pools, indexes, target["id"])])
            if scored["pages"][0]["matches"] != matches:
                raise ValueError("Reference matching depends on topology; factorized oracle is invalid")
            results.append(scored["totals"])
            evaluated += 1
        # All objective components are additive across fixed matched tables. Lexical ties choose first state.
        best = max(range(len(results)), key=lambda i: tuple(results[i][k] for k in OBJECTIVE))
        complete = max(range(len(results)), key=lambda i: results[i]["complete_tables"])
        choices.append(best)
        complete_choices.append(complete)
        deltas.append({k: results[best][k] - base["totals"][k] for k in OBJECTIVE})
        complete_deltas.append(results[complete]["complete_tables"] - base["totals"]["complete_tables"])
    selected = prediction(source, pools, choices, target["id"])
    score = strict_scores([target], [selected])
    if any(score["totals"][k] != base["totals"][k] + sum(d[k] for d in deltas) for k in OBJECTIVE):
        raise ValueError("Whole-page composition violates factorized oracle objective")
    max_complete_prediction = prediction(source, pools, complete_choices, target["id"])
    max_complete = strict_scores([target], [max_complete_prediction])["totals"]["complete_tables"]
    if max_complete != base["totals"]["complete_tables"] + sum(complete_deltas):
        raise ValueError("Whole-page complete-table ceiling violates factorization")
    return {
        "selected": selected,
        "control": control,
        "selected_indexes": choices,
        "score": score["totals"],
        "maximum_complete_tables": max_complete,
        "evaluated_crop_states": evaluated,
    }


def analyze(
    directory: Path, corpus: Path, *, trusted_code: dict[str, str], source_trusted_code: dict[str, str]
) -> dict[str, Any]:
    """Authenticate and rebuild every source-only state before loading DEV references."""
    directory, corpus = guard_path(directory), guard_path(corpus)
    frozen, report = read(directory / "frozen.json"), read(directory / "report.json")
    if (
        frozen["references_read"] is not False
        or frozen["fresh_confirmation_accessed"] is not False
        or frozen["inference_calls"] != 0
        or frozen["policy"] != segments.POLICY
    ):
        raise ValueError("Expected frozen source-only segment policy")
    for name, digest in frozen["code_sha256"].items():
        if (
            Path(name).name != name
            or trusted_code.get(name) != digest
            or sha((directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Segment archive lacks independent code authentication")
        if (
            name != "p003_segment_topology_prepare.py"
            and sha(Path(segments.__file__).with_name(name).read_bytes()) != digest
        ):
            raise ValueError("Current segment replay helper differs from freeze")
    baseline = guard_path(Path(frozen["baseline"]))
    original_frozen, original_report = authenticate(baseline, source_trusted_code)
    if (
        sha((baseline / "frozen.json").read_bytes()) != frozen["baseline_frozen_sha256"]
        or original_frozen["records"] != frozen["records"]
        or len(report["pages"]) != len(frozen["records"])
        or read(directory / "source-trusted-code.json") != source_trusted_code
        or report["frozen_sha256"] != sha((directory / "frozen.json").read_bytes())
    ):
        raise ValueError("Segment source provenance differs")
    originals = {p["id"]: p for p in original_report["results"]}
    if [p["id"] for p in report["pages"]] != [r["id"] for r in frozen["records"]]:
        raise ValueError("Segment inventory drops or reorders pages")
    inventories = []
    for page in report["pages"]:
        ident = page["id"]
        original = originals[ident]
        source = read(directory / page["source_path"])
        if (
            source != original["source"]
            or sha((directory / page["source_path"]).read_bytes()) != page["source_sha256"]
            or sha(canonical(source)) != page["source_identity_sha256"]
            or sha((baseline / f"{ident}-result.json").read_bytes()) != page["baseline_result_sha256"]
        ):
            raise ValueError("Segment complete source changed")
        regions = [r for r in original["region_plan"]["regions"] if r["kind"] == "detector_proposal"]
        if len(regions) != len(page["crops"]):
            raise ValueError("Frozen segment acquisition inventory changed")
        pools = []
        for crop, region in zip(page["crops"], regions, strict=True):
            if (
                crop["region_id"] != region["id"]
                or crop["bbox"] != region["bbox"]
                or crop["source_ids"] != region["source_ids"]
                or crop["region_sha256"] != sha(canonical(region))
            ):
                raise ValueError("Frozen segment crop differs from original source-only acquisition")
            plan = read(directory / crop["folder"] / "plan.json")
            pool = read(directory / crop["folder"] / "candidates.json")
            if (
                sha((directory / crop["folder"] / "plan.json").read_bytes()) != crop["plan_sha256"]
                or sha((directory / crop["folder"] / "candidates.json").read_bytes()) != crop["candidates_sha256"]
                or plan != segments.freeze(source, region["source_ids"], region["bbox"])
                or pool != segments.candidates(source, plan)
            ):
                raise ValueError("Segment pool differs from complete source-only reconstruction")
            pools.append(pool)
        fixed_crop_inventory(source, pools)
        control = segments.compose(source, [pool[0]["state"] for pool in pools])
        if (
            read(directory / page["geometry_control_path"]) != control
            or sha((directory / page["geometry_control_path"]).read_bytes()) != page["geometry_control_sha256"]
        ):
            raise ValueError("Segment geometry control changed")
        inventories.append((ident, source, pools))
    # Source menus and fixed-geometry factorization preconditions are frozen and validated before references.
    manifest, targets = load_corpus(corpus)
    if original_frozen["manifest_sha256"] != sha((corpus / "manifest.json").read_bytes()):
        raise ValueError("Separate DEV references differ from frozen source inventory")
    references = {t["id"]: t for t in targets["pages"]}
    outcomes = [oracle_page(references[i], s, p) for i, s, p in inventories]
    return {
        "scope": "DEV posthoc conditional source-topology oracle; not model quality or global acquisition ceiling",
        "dataset_sha256": manifest["dataset_sha256"],
        "frozen_sha256": sha((directory / "frozen.json").read_bytes()),
        "code_sha256": frozen["code_sha256"],
        "scores": strict_scores(targets["pages"], [o["selected"] for o in outcomes]),
        "geometry_control_scores": strict_scores(targets["pages"], [o["control"] for o in outcomes]),
        "independent_complete_table_ceiling": sum(o["maximum_complete_tables"] for o in outcomes),
        "evaluated_crop_states": sum(o["evaluated_crop_states"] for o in outcomes),
        "pages": [{k: v for k, v in o.items() if k not in {"selected", "control"}} for o in outcomes],
        "no_table_choice_in_prepared_crops": True,
        "new_api_calls": 0,
        "source_conserved": True,
    }
