"""Regional physical-row/gutter controls conserving whole literal source IDs."""

# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

from typing import Any

from bench import p003_fullsource_tracks as tracks
from bench import p003_segment_topology as segments
from bench.p003_structure_place import intersection
from bench.pipeline_repair import MAX_PACKET_BYTES, MAX_SLOTS, _sources, validate
from bench.silver import canonical, sha

PROFILES = tuple((gap, support) for gap in tracks.GAPS for support in tracks.SUPPORTS)
HYBRID_THRESHOLDS = (0.3, 0.5, 0.7)


def regional_source(source: dict[str, Any], region: dict[str, Any]) -> dict[str, Any]:
    """Restrict grouping to authenticated unique ownership without editing literals."""
    lookup = _sources(source)
    ids = region["source_ids"]
    if len(ids) != len(set(ids)) or set(ids) - set(lookup):
        raise ValueError("Unknown or duplicated regional source ownership")
    return {**source, "page_size": region["bbox"],
            "words": [word for word in source["words"] if word["id"] in set(ids)]}


def region_plan(source: dict[str, Any], region: dict[str, Any], gap: float, support: float,
                topology: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Freeze complete regional evidence; crossing words remain unresolved, never cut."""
    local = regional_source(source, region)
    frozen = tracks.physical(local)
    plan = tracks.prepare(local, frozen, gap, support)
    if topology is not None:
        plan.update(column_proposals=[], status="no_candidate_refusal", treatment="tatr_columns_physical_rows")
        edges = topology.get("x_edges", [])
        if topology.get("status") != "geometry_candidate" or len(edges) < 3:
            plan["refusal"] = "no_valid_frozen_tatr_columns"
        elif not all(region["bbox"][0] < x < region["bbox"][2] for x in edges[1:-1]):
            plan["refusal"] = "tatr_column_boundary_outside_region"
        elif (len(frozen["lines"]) * (len(edges) - 1) > MAX_SLOTS or not frozen["lines"]
              or len(frozen["lines"]) > tracks.MAX_LINES or len(edges) - 1 > tracks.MAX_COLUMNS):
            plan["refusal"] = "complete_grid_admission_no_truncation"
        else:
            plan.update(status="prepared", column_proposals=[
                {"id": f"c{i}", "x": x} for i, x in enumerate(edges[1:-1])])
            plan.pop("refusal", None)
    return local, {**plan, "region_id": region["region_id"],
                   "original_source_sha256": sha(canonical(source)),
                   "crossing_owned_word_ids": region.get("crossing_owned_word_ids", []),
                   "literal_policy": "Complete owned words; crossing bounds unresolved; no wrap inference"}


def compose(source: dict[str, Any], regions: list[dict[str, Any]], gap: float, support: float,
            topologies: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Reject all overlapping proposals and preserve a complete global source partition."""
    if (gap, support) not in PROFILES:
        raise ValueError("Unadmitted frozen regional profile")
    _sources(source)
    if len(canonical(source)) > MAX_PACKET_BYTES:
        raise ValueError("Complete source admission exceeded; no truncation")
    owned = [ident for region in regions for ident in region["source_ids"]]
    if len(owned) != len(set(owned)):
        raise ValueError("Regions cannot share owned source IDs")
    conflicts = {region["region_id"] for region in regions for other in regions
                 if region is not other and intersection(region["bbox"], other["bbox"]) > 0}
    tables, receipts = [], []
    for region in regions:
        topology = topologies.get(region["region_id"], {"status": "missing"}) if topologies is not None else None
        local, plan = region_plan(source, region, gap, support, topology)
        if region["region_id"] in conflicts:
            plan.update(status="no_candidate_refusal", refusal="overlapping_proposals_all_participants_refused")
        state = segments.decode(local, plan, [p["id"] for p in plan["column_proposals"]])
        tables.extend(state["tables"])
        assigned = {ident for table in state["tables"] for cell in table["cells"] for ident in cell["source_ids"]}
        receipts.append({"region_id": region["region_id"], "plan": plan,
                         "status": "decoded" if state["tables"] else "refused", "state": state,
                         "owned_word_count": len(local["words"]), "assigned_word_count": len(assigned),
                         "unresolved_owned_ids": state["unresolved_ids"],
                         "ambiguity_inventory": [{"source_id": w["id"], "text": w["text"], "bbox": w["bbox"],
                                                  "reason": "crosses_bounds_or_column" if plan["status"] == "prepared"
                                                  else plan.get("refusal", "no_candidate")}
                                                 for w in local["words"] if w["id"] not in assigned]})
    page_refusal = None
    if sum(table["row_count"] * table["col_count"] for table in tables) > MAX_SLOTS:
        page_refusal = "whole_page_slot_admission_all_proposed_tables_refused"
        tables = []
    for receipt in receipts:
        receipt["effective_page_accepted"] = page_refusal is None and receipt["status"] == "decoded"
    assigned = {ident for table in tables for cell in table["cells"] for ident in cell["source_ids"]}
    state = {"id": "c0", "tables": tables,
             "unresolved_ids": [word["id"] for word in source["words"] if word["id"] not in assigned]}
    validate(source, state)
    return {"state": state, "regions": receipts, "conflicting_region_ids": sorted(conflicts),
            "page_refusal": page_refusal,
            "assigned_word_count": len(assigned), "unresolved_word_count": len(state["unresolved_ids"]),
            "source_word_count": len(source["words"]), "source_conserved": True,
            "scores_are_probabilities": False, "references_read": False,
            "policy": "Unique YOLO ownership; physical rows; all overlaps refused; whole literals exactly once"}
