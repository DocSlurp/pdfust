"""Posthoc DEV source-only sparse-band column proposals, frozen before validation."""

# ruff: noqa: EM101, TRY003, E501, C901, PLR0912
from __future__ import annotations

import argparse
import json
from bisect import bisect_right
from pathlib import Path
from statistics import median
from typing import Any

from bench.decision_evidence_designs import fragments
from bench.pipeline_assembly import _clean_table
from bench.pipeline_repair import _sources, validate
from bench.silver import canonical, guard_path, sha, write_json

POLICY = {"version": 1, "minimum_columns": 3, "maximum_columns": 16, "minimum_body_bands": 3,
          "maximum_sparse_band_width_ratio": 0.60, "maximum_row_leading_ratio": 1.75,
          "left_edge_tolerance_em": 0.5, "maximum_words": 4096,
          "native_table_policy": "Preserve source-native baseline when present",
          "text_policy": "No keywords, lexical categories or family labels; exact word IDs only"}


def proposals(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive word tracks from sparse source bands and contiguous physical body rows."""
    lookup = _sources(source)
    if not source["words"]:
        return []
    height = median(max(1, word["bbox"][3] - word["bbox"][1]) for word in source["words"])
    by_band: dict[int, list[dict[str, Any]]] = {}
    for fragment in fragments(source["words"]):
        by_band.setdefault(fragment["band"], []).append(fragment)
    bands = [sorted(parts, key=lambda part: part["bbox"][0]) for _, parts in sorted(by_band.items())]
    centers = [median((part["bbox"][1] + part["bbox"][3]) / 2 for part in parts) for parts in bands]
    result = []
    for index, sparse in enumerate(bands):
        columns = len(sparse)
        if not POLICY["minimum_columns"] <= columns <= POLICY["maximum_columns"] or index + 3 >= len(bands):
            continue
        left, right = sparse[0]["bbox"][0], sparse[-1]["bbox"][2]
        widths = sum(part["bbox"][2] - part["bbox"][0] for part in sparse)
        if right <= left or widths > POLICY["maximum_sparse_band_width_ratio"] * (right - left):
            continue
        starts = [part["bbox"][0] - POLICY["left_edge_tolerance_em"] * height for part in sparse]
        first_gap = centers[index + 1] - centers[index]
        if first_gap <= height:
            continue
        active = [index]
        for following in range(index + 1, len(bands)):
            gap = centers[following] - centers[following - 1]
            if gap < height * 0.5 or gap > POLICY["maximum_row_leading_ratio"] * first_gap:
                break
            # Complete source rows must fit the observed outer support; do not clip words.
            if any(part["bbox"][0] < starts[0] for part in bands[following]):
                break
            active.append(following)
        if len(active) <= POLICY["minimum_body_bands"]:
            continue
        ids_by_row = []
        for band in active:
            ids = [ident for part in bands[band] for ident in part["source_ids"]]
            ids.sort(key=lambda ident: (lookup[ident]["bbox"][0], lookup[ident]["bbox"][1], ident))
            ids_by_row.append(ids)
        rows = []
        for ids in ids_by_row:
            row: list[list[str]] = [[] for _ in starts]
            for ident in ids:
                box = lookup[ident]["bbox"]
                column = min(columns - 1, max(0, bisect_right(starts, (box[0] + box[2]) / 2) - 1))
                row[column].append(ident)
            rows.append(row)
        # Require each observed track to have support beyond the sparse seed band.
        support = [sum(bool(row[column]) for row in rows[1:]) for column in range(columns)]
        if min(support) < POLICY["minimum_body_bands"]:
            continue
        table = {"row_count": len(rows), "col_count": columns,
                 "cells": [{"source_ids": ids, "role": "unknown"} for row in rows for ids in row],
                 "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1}
                           for r in range(len(rows)) for c in range(columns)]}
        owned = {ident for row in ids_by_row for ident in row}
        boxes = [lookup[ident]["bbox"] for ident in owned]
        bounds = [min(box[0] for box in boxes), min(box[1] for box in boxes),
                  max(box[2] for box in boxes), max(box[3] for box in boxes)]
        state = {"id": "c0", "tables": [{**_clean_table(table, lookup), "bbox": bounds}],
                 "unresolved_ids": [word["id"] for word in source["words"] if word["id"] not in owned]}
        validate(source, state)
        result.append({"state": state, "source_receipt": {"sparse_band": index, "active_bands": active,
                                                          "observed_track_starts": starts, "body_support": support}})
    # Source-only rank: prefer longest supported region, then more retained words.
    result.sort(key=lambda proposal: (-len(proposal["source_receipt"]["active_bands"]),
                                     -sum(len(cell["source_ids"]) for table in proposal["state"]["tables"] for cell in table["cells"]),
                                     sha(canonical(proposal["state"]))))
    return result


def prepare(corpus: Path, output: Path) -> dict[str, Any]:
    """Freeze proposals for every source family without opening target files."""
    corpus, output = guard_path(corpus), guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh derivative directory required")
    manifest = json.loads((corpus / "manifest.json").read_bytes())
    inventory = json.loads((corpus / "source-inventory.json").read_bytes())
    if manifest["split"] != "DEV" or not inventory["source_only"]:
        raise ValueError("Source-only DEV corpus required")
    output.mkdir(parents=True)
    (output / "menus").mkdir()
    rows = []
    for page in manifest["pages"]:
        ident = page["id"]
        raw = guard_path(corpus / "menus" / (ident + ".json")).read_bytes()
        if sha(raw) != inventory["artifacts"][f"menus/{ident}.json"]:
            raise ValueError("Frozen source menu changed")
        menu = json.loads(raw)
        if sha(canonical(menu["source"])) != menu["source_sha256"]:
            raise ValueError("Source snapshot changed")
        additions = proposals(menu["source"])
        seen = {sha(canonical(candidate["state"])) for candidate in menu["candidates"]}
        for addition in additions[:1]:
            digest = sha(canonical(addition["state"]))
            if digest not in seen:
                menu["candidates"].append({"id": "c" + sha(f"{ident}/headerband/{digest}".encode())[:16], "state": addition["state"]})
        menu["candidates"].sort(key=lambda candidate: candidate["id"])
        chosen = additions[0]["state"] if additions and not menu["baseline"]["tables"] else menu["baseline"]
        write_json(output / "menus" / (ident + ".json"), menu)
        rows.append({"id": ident, "source_menu_sha256": sha(raw), "menu_sha256": sha((output / "menus" / (ident + ".json")).read_bytes()),
                     "proposal_count": len(additions), "source_receipt": additions[0]["source_receipt"] if additions else None,
                     "deterministic_state": chosen})
    receipt = {"version": 1, "corpus": str(corpus), "policy": POLICY, "policy_sha256": sha(canonical(POLICY)),
               "code_sha256": sha(Path(__file__).read_bytes()), "source_manifest_sha256": sha((corpus / "manifest.json").read_bytes()),
               "source_inventory_sha256": sha((corpus / "source-inventory.json").read_bytes()), "pages": rows,
               "posthoc_dev": True, "references_read": False, "family_filters_used": False, "existing_menus_modified": False}
    write_json(output / "frozen.json", receipt)
    return receipt


def main() -> None:
    """Prepare a separately versioned source-only derivative before any scoring."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = prepare(args.corpus, args.output)
    print(json.dumps({"pages": len(receipt["pages"]), "proposal_pages": sum(bool(page["proposal_count"]) for page in receipt["pages"]),
                      "policy_sha256": receipt["policy_sha256"]}))


if __name__ == "__main__":
    main()
