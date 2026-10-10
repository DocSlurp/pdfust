"""Source-conserved placement into independently frozen CPU structure geometry."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLR2004
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

from bench import p003_structure_geometry as geometry
from bench.p003_gate_run import authenticate
from bench.pipeline_assembly import _clean_table
from bench.pipeline_repair import _sources, validate
from bench.pipeline_run import Resources
from bench.silver import canonical, guard_path, sha, write_json

POLICIES = ("overlap_margin", "max_overlap", "center")


def intersection(a: list[float], b: list[float]) -> float:
    """Return nonnegative display-coordinate intersection area."""
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))


def place(source: dict[str, Any], candidates: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    """Use only exact source words and declared detector ownership; no model fallback."""
    if policy not in POLICIES:
        raise ValueError("Unknown frozen placement policy")
    if len(canonical(source)) > 2 * 1024 * 1024:
        raise ValueError("Complete source exceeds two MiB admission")
    lookup = _sources(source)
    tables: list[dict[str, Any]] = []
    anchors: list[tuple[int, int, list[float], set[str]]] = []
    refusals: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        ids = candidate["source_ids"]
        if len(ids) != len(set(ids)) or set(ids) - set(lookup) or seen & set(ids):
            raise ValueError("Detector source ownership is duplicated or unknown")
        seen.update(ids)
        shape = candidate["topology"]
        if shape["status"] != "geometry_candidate":
            refusals.append({"region_id": candidate["region_id"], "reason": shape["status"]})
            continue
        rows, cols = shape["row_count"], shape["column_count"]
        if not 0 < rows * cols <= 4096:
            raise ValueError("Structure cell admission exceeded")
        table = {"row_count": rows, "col_count": cols, "bbox": shape["bbox"],
                 "cells": [{"source_ids": [], "role": "unknown"} for _ in range(rows * cols)],
                 "spans": [{k: a[k] for k in ("row", "column", "row_span", "column_span")}
                           for a in shape["anchors"]]}
        _clean_table(table, lookup)  # Complete rectangular tiling must precede assignments.
        index = len(tables)
        tables.append(table)
        allowed = set(ids)
        anchors.extend((index, a["row"] * cols + a["column"], a["bbox"], allowed) for a in shape["anchors"])
    conflicting = {i for i, a in enumerate(tables) for j, b in enumerate(tables)
                   if i != j and intersection(a["bbox"], b["bbox"]) > 0}
    # Refuse all overlapping tables, retaining their words as unresolved source.
    decisions = []
    for word in source["words"]:
        box = word["bbox"]
        area = (box[2] - box[0]) * (box[3] - box[1])
        ranked = []
        for t, slot, bounds, ids in anchors:
            if t in conflicting or word["id"] not in ids:
                continue
            overlap = intersection(box, bounds) / area if area > 0 else 0
            center = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
            contains = bounds[0] <= center[0] < bounds[2] and bounds[1] <= center[1] < bounds[3]
            if not math.isfinite(overlap):
                raise ValueError("Invalid source overlap geometry")
            ranked.append((overlap, t, slot, contains))
        ranked.sort(key=lambda r: (-r[0], r[1], r[2]))
        best = ranked[0] if ranked else None
        margin = best[0] - (ranked[1][0] if len(ranked) > 1 else 0) if best else 0
        chosen = None
        if policy == "center":
            hits = [row for row in ranked if row[3]]
            if len(hits) == 1:
                chosen = hits[0]
        elif best and ((policy == "max_overlap" and best[0] > 0 and margin > 1e-9)
                       or (policy == "overlap_margin" and best[0] >= 0.8 and margin >= 0.15)):
            chosen = best
        if chosen:
            tables[chosen[1]]["cells"][chosen[2]]["source_ids"].append(word["id"])
        decisions.append({"source_id": word["id"], "table": chosen[1] if chosen else None,
                          "slot": chosen[2] if chosen else None, "best_overlap": best[0] if best else None,
                          "margin": margin, "status": "placed" if chosen else "unresolved"})
    output = [{**_clean_table(t, lookup), "bbox": t["bbox"]} for i, t in enumerate(tables) if i not in conflicting]
    state = {"id": "c0", "tables": output,
             "unresolved_ids": [d["source_id"] for d in decisions if d["status"] == "unresolved"],
             "mechanism": "p003_cpu_structure_geometry_" + policy}
    validate(source, state)
    return {"state": state, "decisions": decisions, "refused_topologies": refusals,
            "conflicting_table_indices": sorted(conflicting), "source_conserved": True,
            "scores_are_probabilities": False, "policy": policy}


def run(directory: Path, output: Path) -> dict[str, Any]:
    """Authenticate source and raw geometry, freezing all nine treatments before scores."""
    directory, output = guard_path(directory), guard_path(output)
    source_path, report_path = directory / "source/manifest.json", directory / "geometry/report.json"
    manifest, report = json.loads(source_path.read_bytes()), json.loads(report_path.read_bytes())
    if report["source_manifest_sha256"] != sha(source_path.read_bytes()):
        raise ValueError("Geometry source manifest changed")
    if report["code_sha256"] != sha(Path(geometry.__file__).read_bytes()):
        raise ValueError("Unreviewed geometry implementation")
    baseline, trusted = guard_path(Path(manifest["baseline"])), guard_path(Path(manifest["independent_trusted_code"]))
    if sha(trusted.read_bytes()) != manifest["trusted_code_sha256"]:
        raise ValueError("Independent source trust map changed")
    frozen, _ = authenticate(baseline, json.loads(trusted.read_bytes()))
    if [r["id"] for r in frozen["records"]] != [r["id"] for r in manifest["pages"]]:
        raise ValueError("Incomplete intended page inventory")
    if [r["id"] for r in report["pages"]] != [r["id"] for r in manifest["pages"]]:
        raise ValueError("Incomplete geometry page inventory")
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "frozen.json", {
        "source_manifest_sha256": sha(source_path.read_bytes()),
        "geometry_report_sha256": sha(report_path.read_bytes()),
        "thresholds": list(geometry.THRESHOLDS), "policies": list(POLICIES), "references_read": False,
        "code_sha256": {name: sha(Path(__file__).with_name(name).read_bytes()) for name in
                        ("p003_structure_place.py", "p003_structure_geometry.py", "pipeline_assembly.py",
                         "pipeline_repair.py")},
        "output_scope": "Source placement conditional on frozen detector crops; no generated fallback text",
    })
    rows = []
    with Resources() as resources:
        for page, measured in zip(manifest["pages"], report["pages"], strict=True):
            raw = (directory / "source" / page["source_path"]).read_bytes()
            if sha(raw) != page["source_sha256"]:
                raise ValueError("Source snapshot changed")
            source = json.loads(raw)
            original_raw = (baseline / (page["id"] + "-result.json")).read_bytes()
            if sha(original_raw) != page["baseline_result_sha256"] or json.loads(original_raw)["source"] != source:
                raise ValueError("Source differs from independently authenticated extraction")
            candidates: dict[float, list[dict[str, Any]]] = {threshold: [] for threshold in geometry.THRESHOLDS}
            if len(page["crops"]) != len(measured["crops"]):
                raise ValueError("Geometry crop inventory differs")
            for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
                raw = (directory / "geometry" / receipt["path"]).read_bytes()
                if sha(raw) != receipt["sha256"]:
                    raise ValueError("Geometry receipt changed")
                prediction = json.loads(raw)
                if prediction["crop"] != crop:
                    raise ValueError("Geometry crop provenance differs")
                for view in prediction["views"]:
                    expected = geometry.project(
                        prediction["queries"], crop["bbox"], report["labels"], view["threshold"]
                    )
                    expected["topology"] = geometry.topology(expected)
                    if view != expected:
                        raise ValueError("Geometry projection differs from frozen raw model queries")
                    candidates[view["threshold"]].append({"region_id": crop["region_id"],
                                                          "source_ids": crop["source_ids"],
                                                          "topology": view["topology"]})
            for threshold, shapes in candidates.items():
                for policy in POLICIES:
                    started = time.perf_counter()
                    placed = place(source, shapes, policy)
                    name = f"{page['id']}-t{threshold}-{policy}.json"
                    payload = {"id": page["id"], "source": source, "threshold": threshold, **placed}
                    write_json(output / name, payload)
                    rows.append({"id": page["id"], "threshold": threshold, "policy": policy,
                                 "path": name, "sha256": sha((output / name).read_bytes()),
                                 "tables": len(placed["state"]["tables"]),
                                 "unresolved_words": len(placed["state"]["unresolved_ids"]),
                                 "wall_seconds": time.perf_counter() - started})
    result = {"rows": rows, "resources": resources.summary(), "references_read": False, "new_api_calls": 0,
              "scope": "Offline placement only; original OCR/detection and structure inference excluded"}
    write_json(output / "report.json", result)
    return result


def main() -> None:
    """Prepare frozen source placements without quality references or credentials."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.geometry, args.output)
    print(json.dumps({"page_treatments": len(result["rows"]), "resources": result["resources"]}))


if __name__ == "__main__":
    main()
