"""Source-only physical/rolling row hypotheses; no model or private targets."""

# ruff: noqa: EM101, TRY003, PLR2004
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from bench.decision_evidence_designs import fragments
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss

MAX_WORDS = 4096
MAX_COLUMNS = 16
MIN_SUPPORT = 3
ANCHOR_TOLERANCE = 0.75
WRAP_HEIGHTS = 1.8


def numeric(text: str) -> bool:
    """Recognize literal numeric-like tokens without inferring units or values."""
    stripped = text.strip().strip("()%+−-$€£¥")
    return bool(stripped) and any(c.isdigit() for c in stripped) and all(c.isdigit() or c in ".,/:" for c in stripped)


def project(page: dict[str, Any]) -> dict[str, Any]:
    """Admit only literal words and display geometry, ignoring all other fields."""
    words = page["words"]
    if not isinstance(words, list) or len(words) > MAX_WORDS:
        raise ValueError("Complete word input exceeds admission")
    clean = []
    for word in words:
        box = word["bbox"]
        if len(box) != 4 or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in box
        ):
            raise ValueError("Invalid source box")
        if box[0] > box[2] or box[1] > box[3] or not isinstance(word["id"], str) or not isinstance(word["text"], str):
            raise ValueError("Invalid literal source word")
        clean.append({"id": word["id"], "text": word["text"], "bbox": list(box)})
    if len({w["id"] for w in clean}) != len(clean):
        raise ValueError("Duplicate source IDs")
    return {"words": clean, "page_size": list(page["page_size"])}


def _anchors(parts: list[dict[str, Any]], height: float) -> list[dict[str, Any]]:
    """Cluster repeated left/right fragment edges, retaining the strongest disjoint anchors."""
    proposals = []
    for edge in (0, 2):
        groups: list[list[dict[str, Any]]] = []
        for part in sorted(parts, key=lambda f: (f["bbox"][edge], f["band"], f["id"])):
            if not groups or part["bbox"][edge] - groups[-1][0]["bbox"][edge] > height * ANCHOR_TOLERANCE:
                groups.append([])
            groups[-1].append(part)
        for group in groups:
            support = len({p["band"] for p in group})
            if support >= MIN_SUPPORT:
                proposals.append(
                    {
                        "edge": edge,
                        "position": median(p["bbox"][edge] for p in group),
                        "support": support,
                        "fragment_ids": [p["id"] for p in group],
                    }
                )
    selected, owned = [], set()
    for proposal in sorted(proposals, key=lambda a: (-a["support"], a["edge"], a["position"])):
        ids = set(proposal["fragment_ids"])
        if not ids & owned:
            selected.append(proposal)
            owned.update(ids)
    selected.sort(key=lambda a: median(p["bbox"][0] for p in parts if p["id"] in a["fragment_ids"]))
    return selected


def assemble(page: dict[str, Any], variant: str = "physical") -> dict[str, Any]:  # noqa: C901, PLR0912
    """Return unaccepted candidate cells and complete unresolved word inventory."""
    if variant not in ("physical", "rolling"):
        raise ValueError("Unknown row hypothesis")
    source = project(page)
    words, lookup = source["words"], {w["id"]: w for w in source["words"]}
    height = median(max(1, w["bbox"][3] - w["bbox"][1]) for w in words) if words else 1
    parts = fragments(words)
    anchors = _anchors(parts, height)
    base = {
        "variant": variant,
        "status": "candidate_only; table/header semantics unknown",
        "source_words": words,
        "anchors": anchors,
        "candidates": [],
        "unresolved_ids": [w["id"] for w in words],
    }
    if not 2 <= len(anchors) <= MAX_COLUMNS:
        return base
    bands: dict[int, list[dict[str, Any]]] = {}
    for part in parts:
        # A fragment can be wider than a normal column. Keep its ambiguity visible.
        scores = [abs(part["bbox"][a["edge"]] - a["position"]) for a in anchors]
        column = min(range(len(anchors)), key=lambda i: (scores[i], i))
        if scores[column] <= height * 2:
            bands.setdefault(part["band"], []).append({**part, "column": column})
    full = [band for band, items in bands.items() if len({p["column"] for p in items}) >= 2]
    if len(full) < MIN_SUPPORT:
        return base
    first, last = min(full), max(full)
    last_bottom = max(p["bbox"][3] for p in bands[last])
    trailing = [
        band
        for band in sorted(bands)
        if band == last + 1 and min(p["bbox"][1] for p in bands[band]) - last_bottom <= height * WRAP_HEIGHTS
    ]
    active = [(band, bands[band]) for band in sorted(bands) if first <= band <= last or band in trailing]
    numeric_columns = []
    for column in range(len(anchors)):
        supporting = [p for _, items in active for p in items if p["column"] == column]
        number_count = sum(all(numeric(lookup[i]["text"]) for i in p["source_ids"]) for p in supporting)
        if number_count >= MIN_SUPPORT:
            numeric_columns.append(column)
    rows: list[list[list[str]]] = []
    row_bands: list[list[int]] = []
    previous_bottom = None
    for band, items in active:
        top = min(p["bbox"][1] for p in items)
        bottom = max(p["bbox"][3] for p in items)
        columns = {p["column"] for p in items}
        hanging = len(columns) < len(anchors) and not any(c in numeric_columns for c in columns)
        close = previous_bottom is not None and 0 <= top - previous_bottom <= height * WRAP_HEIGHTS
        join = variant == "rolling" and bool(rows) and hanging and close
        if not join:
            rows.append([[] for _ in anchors])
            row_bands.append([])
        row_bands[-1].append(band)
        for item in sorted(items, key=lambda p: (p["column"], p["bbox"][0])):
            rows[-1][item["column"]].extend(item["source_ids"])
        previous_bottom = bottom
    owned = [i for row in rows for cell in row for i in cell]
    if len(owned) != len(set(owned)):
        raise ValueError("Candidate has duplicate source ownership")
    cells = []
    values = []
    for row in rows:
        values.append([" ".join(lookup[i]["text"] for i in cell) for cell in row])
        cells.extend([{"source_ids": cell, "role": "unknown"} for cell in row])
    candidate = {
        "row_count": len(rows),
        "col_count": len(anchors),
        "values": values,
        "cells": cells,
        "spans": [
            {"row": r, "column": c, "row_span": 1, "column_span": 1}
            for r in range(len(rows))
            for c in range(len(anchors))
        ],
        "row_physical_bands": row_bands,
        "numeric_column_hypotheses": numeric_columns,
        "header_role": "unknown; first row retained without assumed header semantics",
    }
    base["candidates"] = [candidate]
    base["unresolved_ids"] = [w["id"] for w in words if w["id"] not in set(owned)]
    if Counter(owned + base["unresolved_ids"]) != Counter(w["id"] for w in words):
        raise ValueError("Candidate violates source conservation")
    return base


def freeze(source_path: Path, output: Path) -> dict[str, Any]:
    """Freeze both alternatives and hashes before any external scorer opens private targets."""
    source_path, output = guard_path(source_path), guard_path(output)
    raw = source_path.read_bytes()
    source = json.loads(raw)
    start, cpu = time.perf_counter(), time.process_time()
    pages = [
        {"id": page["id"], "alternatives": [assemble(page, variant) for variant in ("physical", "rolling")]}
        for page in source["pages"]
    ]
    rss, tool = process_peak_rss()
    result = {
        "schema": 1,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "rules": {
            "min_anchor_support": MIN_SUPPORT,
            "anchor_tolerance_heights": ANCHOR_TOLERANCE,
            "wrap_gap_heights": WRAP_HEIGHTS,
            "numeric_support": MIN_SUPPORT,
        },
        "pages": pages,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"perf_counter/process_time; {tool}; lifetime peak; no sampling; sequential CPU",
    }
    data = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return {
        "output": str(output),
        "sha256": hashlib.sha256(data).hexdigest(),
        "pages": len(pages),
        **{k: result[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes")},
    }


def main() -> None:
    """Prepare candidates with no inference or scoring input."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.source, args.output), indent=2))


if __name__ == "__main__":
    main()
