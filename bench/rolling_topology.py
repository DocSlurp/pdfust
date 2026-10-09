"""T001–T003 source-only seed-band column corridors and short-table hypotheses."""

# ruff: noqa: EM101, TRY003, PLR2004, PLC0415
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import time
from collections import Counter
from copy import deepcopy
from itertools import pairwise
from pathlib import Path
from statistics import median
from typing import Any, TypedDict

from bench.decision_evidence_designs import fragments
from bench.rolling_rows import numeric, project
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss


class Config(TypedDict):
    """Declared source-only topology proposal policy."""

    name: str
    merge: str
    seed_limit: int
    maximum_columns: int
    stop_gap_multiple: float
    wrap_gap_heights: float


_CONFIGS: tuple[Config, ...] = (
    {
        "name": "T001-seed-physical",
        "merge": "none",
        "seed_limit": 3,
        "maximum_columns": 8,
        "stop_gap_multiple": 2.5,
        "wrap_gap_heights": 1.8,
    },
    {
        "name": "T002-seed-sparse",
        "merge": "sparse",
        "seed_limit": 3,
        "maximum_columns": 8,
        "stop_gap_multiple": 2.5,
        "wrap_gap_heights": 1.8,
    },
    {
        "name": "T003-seed-numeric-boundary",
        "merge": "numeric",
        "seed_limit": 3,
        "maximum_columns": 8,
        "stop_gap_multiple": 2.5,
        "wrap_gap_heights": 1.8,
    },
)


def configs() -> list[Config]:
    """Return immutable-in-intent policies for freezing before private scoring."""
    return deepcopy(list(_CONFIGS))


def _identity(table: dict[str, Any]) -> str:
    return json.dumps({k: table[k] for k in ("row_count", "col_count", "values", "spans", "cells")}, sort_keys=True)


def _native_candidate(page: dict[str, Any], words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retain source vector topology and map source centers without private references."""
    result: list[dict[str, Any]] = []
    for index, table in enumerate(page.get("vector_candidates", [])):
        cells: list[dict[str, Any]] = [{"source_ids": [], "role": "unknown"} for _ in table["cells"]]
        for word in words:
            x, y = ((word["bbox"][i] + word["bbox"][i + 2]) / 2 for i in (0, 1))
            hits = [
                i
                for i, box in enumerate(table["cells"])
                if box is not None and box[0] <= x <= box[2] and box[1] <= y <= box[3]
            ]
            if len(hits) == 1:
                cells[hits[0]]["source_ids"].append(word["id"])
        owned = [i for cell in cells for i in cell["source_ids"]]
        result.append(
            {
                "name": f"native-vector-{index}",
                "row_count": table["row_count"],
                "col_count": table["col_count"],
                "values": deepcopy(table["values"]),
                "spans": deepcopy(table["spans"]),
                "cells": cells,
                "unresolved_ids": [w["id"] for w in words if w["id"] not in set(owned)],
                "status": "source-native grid prior; no new merged-cell inference",
            }
        )
    return result


def propose(page: dict[str, Any], config: Config) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Propose complete source-owned tables from seed corridors, never admitting a table automatically."""
    if config not in _CONFIGS:
        raise ValueError("Topology configuration must match a frozen declared policy")
    words = project(page)["words"]
    lookup = {w["id"]: w for w in words}
    parts = fragments(words)
    by_band: dict[int, list[dict[str, Any]]] = {}
    for part in parts:
        by_band.setdefault(part["band"], []).append(part)
    seeds = [(band, items) for band, items in by_band.items() if 2 <= len(items) <= config["maximum_columns"]][
        : config["seed_limit"]
    ]
    candidates = _native_candidate(page, words)
    for seed_band, seed_parts in seeds:
        anchors = sorted(p["bbox"][0] for p in seed_parts)
        if len(set(anchors)) != len(anchors):
            continue
        height = median(max(1, p["bbox"][3] - p["bbox"][1]) for p in seed_parts)
        full_tops = [
            min(p["bbox"][1] for p in items) for band, items in by_band.items() if band >= seed_band and len(items) >= 2
        ]
        differences = [b - a for a, b in pairwise(full_tops) if b > a]
        typical_gap = median(differences) if differences else height * 4
        numeric_columns: set[int] = set()
        admitted: list[tuple[int, list[list[str]], float, float]] = []
        previous_bottom = None
        for band, items in by_band.items():
            if band < seed_band:
                continue
            top = min(p["bbox"][1] for p in items)
            bottom = max(p["bbox"][3] for p in items)
            if previous_bottom is not None and top - previous_bottom > max(
                height * 3, typical_gap * config["stop_gap_multiple"]
            ):
                break
            if (
                len(items) == 1
                and band > seed_band
                and items[0]["bbox"][2] - items[0]["bbox"][0] > (anchors[-1] - anchors[0]) * 0.9
            ):
                break
            cells: list[list[str]] = [[] for _ in anchors]
            for part in items:
                for source_id in part["source_ids"]:
                    word = lookup[source_id]
                    x = word["bbox"][0]
                    if x < anchors[0] - height * 0.5:
                        continue
                    column = max(0, bisect.bisect_right(anchors, x + 0.05) - 1)
                    cells[column].append(source_id)
                    if numeric(word["text"]):
                        numeric_columns.add(column)
            if any(cells):
                admitted.append((band, cells, top, bottom))
                previous_bottom = bottom
        if len(admitted) < 2:
            continue
        rows: list[list[list[str]]] = []
        physical_bands: list[list[int]] = []
        previous_bottom = None
        for band, cells, top, bottom in admitted:
            occupied = {c for c, ids in enumerate(cells) if ids}
            close = previous_bottom is not None and 0 <= top - previous_bottom <= height * config["wrap_gap_heights"]
            numeric_here = any(any(numeric(lookup[i]["text"]) for i in ids) for ids in cells)
            sparse = len(occupied) < len(anchors)
            join = bool(rows) and close and sparse and config["merge"] != "none"
            if config["merge"] == "sparse":
                join = join and not bool(occupied & numeric_columns)
            elif config["merge"] == "numeric":
                join = join and not numeric_here
            if not join:
                rows.append([[] for _ in anchors])
                physical_bands.append([])
            physical_bands[-1].append(band)
            for column, ids in enumerate(cells):
                rows[-1][column].extend(ids)
            previous_bottom = bottom
        cell_list = [{"source_ids": ids, "role": "unknown"} for row in rows for ids in row]
        owned = [i for cell in cell_list for i in cell["source_ids"]]
        table = {
            "name": f"{config['name']}-seed-{seed_band}",
            "row_count": len(rows),
            "col_count": len(anchors),
            "values": [[" ".join(lookup[i]["text"] for i in ids) for ids in row] for row in rows],
            "spans": [
                {"row": r, "column": c, "row_span": 1, "column_span": 1}
                for r in range(len(rows))
                for c in range(len(anchors))
            ],
            "cells": cell_list,
            "unresolved_ids": [w["id"] for w in words if w["id"] not in set(owned)],
            "column_corridor_starts": anchors,
            "physical_bands": physical_bands,
            "header_role": "unknown; seed band is a geometry hypothesis, not an assumed header",
            "status": "unaccepted complete candidate; no source words invented",
        }
        if not any(_identity(table) == _identity(old) for old in candidates):
            candidates.append(table)
    for candidate in candidates:
        owned = [i for cell in candidate["cells"] for i in cell["source_ids"]]
        if Counter(owned + candidate["unresolved_ids"]) != Counter(w["id"] for w in words):
            raise ValueError("Topology candidate violates exact source conservation")
    return {
        "config": config["name"],
        "candidates": candidates,
        "source_word_ids": [w["id"] for w in words],
        "candidate_only": True,
    }


def freeze(sources: list[Path], output: Path) -> dict[str, Any]:
    """Freeze every declared config and complete cohort candidate bytes before private scoring."""
    output = guard_path(output)
    if output.exists():
        raise ValueError("Topology output already exists; preserve the original freeze")
    output.mkdir(parents=True)
    policies = configs()
    (output / "configs.json").write_text(json.dumps(policies, sort_keys=True, indent=2))
    start, cpu = time.perf_counter(), time.process_time()
    cohorts = []
    for source_path in sources:
        raw = guard_path(source_path).read_bytes()
        pages = json.loads(raw)["pages"]
        cohorts.append(
            {
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "source_path": str(source_path.resolve()),
                "pages": [{"id": p["id"], "alternatives": [propose(p, config) for config in policies]} for p in pages],
            }
        )
    rss, measurement = process_peak_rss()
    payload = {
        "schema": 1,
        "configs": policies,
        "cohorts": cohorts,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"perf_counter/process_time; {measurement}; process lifetime; sequential CPU; no sampling",
    }
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    (output / "candidates.json").write_bytes(data)
    return {
        "output": str(output),
        "sha256": hashlib.sha256(data).hexdigest(),
        "cohort_pages": [len(c["pages"]) for c in cohorts],
    }


def score_frozen(directory: Path, target_paths: list[Path]) -> dict[str, Any]:
    """Private evaluation of already frozen candidates; never call the generator with references."""
    from bench.borderless_challenge import score
    from bench.rolling_robustness import exact_source_ownership

    directory = guard_path(directory)
    frozen_bytes = (directory / "candidates.json").read_bytes()
    payload = json.loads(frozen_bytes)
    if payload["configs"] != configs() or len(target_paths) != len(payload["cohorts"]):
        raise ValueError("Frozen policy/cohort identity mismatch")
    rows: list[dict[str, Any]] = []
    for cohort_index, (cohort, target_path) in enumerate(zip(payload["cohorts"], target_paths, strict=True)):
        raw = guard_path(Path(cohort["source_path"])).read_bytes()
        if hashlib.sha256(raw).hexdigest() != cohort["source_sha256"]:
            raise ValueError("Source export changed after candidate freeze")
        sources = {p["id"]: p for p in json.loads(raw)["pages"]}
        targets = {p["id"]: p for p in json.loads(guard_path(target_path).read_bytes())}
        if set(sources) != set(targets):
            raise ValueError("Private references differ from frozen source cohort")
        for page in cohort["pages"]:
            target = targets[page["id"]]
            for alternative in page["alternatives"]:
                tables = alternative["candidates"]
                scored = [score(target, [table]) for table in tables]
                best_index = max(
                    range(len(scored)),
                    key=lambda i: (
                        scored[i]["exact_page"],
                        scored[i]["exact_cells"],
                        scored[i]["owned_values"],
                        scored[i]["owned_words"],
                    ),
                    default=None,
                )
                best = scored[best_index] if best_index is not None else score(target, [])
                ownership = (
                    exact_source_ownership(
                        target, sources[page["id"]], tables[best_index] if best_index is not None else None
                    )
                    if target.get("authored_slots")
                    else None
                )
                candidate_conservation = all(
                    Counter([i for cell in t["cells"] for i in cell["source_ids"]] + t["unresolved_ids"])
                    == Counter(w["id"] for w in sources[page["id"]]["words"])
                    for t in tables
                )
                if not candidate_conservation:
                    raise ValueError("Frozen topology candidates violate inventory conservation")
                rows.append(
                    {
                        "cohort": cohort_index,
                        "id": page["id"],
                        "config": alternative["config"],
                        "kind": target["kind"],
                        "candidate_count": len(tables),
                        "best_index": best_index,
                        "scores": best,
                        "ownership": ownership,
                        "source_conservation": candidate_conservation,
                        "all_candidate_scores": scored,
                    }
                )
    aggregates: dict[str, Any] = {}
    for cohort_index in range(len(payload["cohorts"])):
        aggregates[str(cohort_index)] = {}
        for policy in payload["configs"]:
            selected = [r for r in rows if r["cohort"] == cohort_index and r["config"] == policy["name"]]
            aggregates[str(cohort_index)][policy["name"]] = {
                "candidate_count": sum(r["candidate_count"] for r in selected),
                "maximum_candidates_per_page": max(r["candidate_count"] for r in selected),
                "source_conservation": all(r["source_conservation"] for r in selected),
                "slices": {
                    kind: {
                        "pages": sum(r["kind"] == kind for r in selected),
                        **{
                            key: sum(r["scores"][key] for r in selected if r["kind"] == kind)
                            for key in (
                                "exact_page",
                                "exact_cells",
                                "exact_spans",
                                "owned_values",
                                "owned_words",
                                "false_positive_page",
                            )
                        },
                        "zero_candidate_pages": sum(r["candidate_count"] == 0 for r in selected if r["kind"] == kind),
                        "wrong_only_candidate_pages": sum(
                            r["candidate_count"] > 0 and not r["scores"]["exact_page"]
                            for r in selected
                            if r["kind"] == kind
                        ),
                        "correct_slot_word_ids": sum(
                            r["ownership"]["correct_slot_word_ids"]
                            for r in selected
                            if r["kind"] == kind and r["ownership"]
                        ),
                        "intended_word_ids": sum(
                            r["ownership"]["intended_word_ids"]
                            for r in selected
                            if r["kind"] == kind and r["ownership"]
                        ),
                    }
                    for kind in ("borderless", "prose", "ruled-control")
                },
            }
    summary = {
        "candidate_freeze_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
        "aggregates": aggregates,
        "resource_measurements": {
            k: payload[k] for k in ("wall_seconds", "cpu_seconds", "peak_rss_bytes", "measurement")
        },
        "limits": "Oracle over unaccepted source-only candidates. False proposals are not actual admissions. "
        "Original fresh model results are cue-contaminated; neutral source geometry scoring only.",
    }
    (directory / "private-scores.json").write_text(json.dumps({"rows": rows}, indent=2))
    (directory / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def union_candidates(
    page: dict[str, Any], original: list[dict[str, Any]], topology: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deduplicate complete source layouts while retaining all technique provenance outside model state."""
    words = project(page)["words"]
    retained: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    proposed = [(a["variant"], table, a["unresolved_ids"]) for a in original for table in a["candidates"]]
    proposed += [(a["config"], table, table["unresolved_ids"]) for a in topology for table in a["candidates"]]
    for name, table, unresolved in proposed:
        clean = {key: deepcopy(table[key]) for key in ("row_count", "col_count", "values", "spans", "cells")}
        owned = [i for cell in clean["cells"] for i in cell["source_ids"]]
        if Counter(owned + unresolved) != Counter(w["id"] for w in words):
            raise ValueError("Union layout violates complete source conservation")
        identity = _identity(clean)
        existing = next((i for i, old in enumerate(retained) if _identity(old["table"]) == identity), None)
        if existing is None:
            existing = len(retained)
            retained.append({"id": f"c{existing}", "table": clean, "unresolved_ids": list(unresolved)})
            provenance.append({"candidate_id": f"c{existing}", "source_policies": []})
        provenance[existing]["source_policies"].append(name)
    return retained, provenance


def union_request(
    page: dict[str, Any],
    candidates: list[dict[str, Any]],
    model: str,
    *,
    with_image: bool = False,
    instructions: str | None = None,
) -> dict[str, Any]:
    """Build a generic-ID source-only admission body, with no technique name or scorer fields."""
    import base64

    from bench.rolling_rows import admission_request, assemble, source_image

    source = project(page)
    originals = [assemble(source, v) for v in ("physical", "rolling")]
    baseline = admission_request(source, originals, model)["questions"]["q0"]["instructions"]
    visible: dict[str, Any] = {
        "coordinates": "display points; y downward; row/column zero-based",
        "page_size": source["page_size"],
        "source_words": source["words"],
        "candidate_tables": {c["id"]: {"table": c["table"], "unresolved_ids": c["unresolved_ids"]} for c in candidates},
        "header_policy": "All candidate cell roles and first-row header role remain unknown.",
    }
    criteria = {
        c[
            "id"
        ]: f"Accept the complete candidate {c['id']} as a source-supported table, preserving its exact word ownership."
        for c in candidates
    }
    criteria.update(
        {
            "not_table": "Source supports prose or another non-table structure; keep every word outside table cells.",
            "unresolved": "Evidence cannot establish a table or choose a complete candidate; "
            "retain all source words unresolved.",
        }
    )
    state: Any = visible
    if with_image:
        data, pixels = source_image(page)
        visible["image_mapping"] = {
            "display_bbox": source["page_size"],
            "pixels": pixels,
            "scope": "whole source page; native pixels downsampled, white background",
        }
        state = [
            json.dumps(visible, separators=(",", ":")),
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64," + base64.b64encode(data).decode("ascii"),
                    "detail": "high",
                },
            },
        ]
    body = {
        "model": model,
        "state": state,
        "questions": {
            "q0": {
                "type": "choice",
                "instructions": instructions if instructions is not None else baseline,
                "criteria": criteria,
            }
        },
    }
    if len(json.dumps(body).encode()) > 750_000:
        raise ValueError("Complete union decision body exceeds byte admission")
    return body


def freeze_union(  # noqa: PLR0913 - independent source/candidate/model identities.
    source_paths: list[Path],
    original_paths: list[Path],
    topology_directory: Path,
    output: Path,
    models: list[str],
    *,
    prompt_variant: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Freeze generic menus using only source and already frozen candidates, with no target input."""
    from bench.prompt_variants_structure import transform
    from bench.rolling_rows import _native_inventory

    topology_raw = (guard_path(topology_directory) / "candidates.json").read_bytes()
    topology = json.loads(topology_raw)
    if len(source_paths) != len(original_paths) or len(source_paths) != len(topology["cohorts"]):
        raise ValueError("Union input cohorts do not align")
    output = guard_path(output)
    if output.exists():
        raise ValueError("Union output already exists; preserve frozen requests")
    output.mkdir(parents=True)
    start, cpu = time.perf_counter(), time.process_time()
    records: list[dict[str, Any]] = []
    cohorts: list[dict[str, Any]] = []
    for cohort_index, (source_path, original_path, topo) in enumerate(
        zip(source_paths, original_paths, topology["cohorts"], strict=True)
    ):
        source_raw = guard_path(source_path).read_bytes()
        original_raw = guard_path(original_path).read_bytes()
        source, original = json.loads(source_raw), json.loads(original_raw)
        digest = hashlib.sha256(source_raw).hexdigest()
        if digest != original["source_sha256"] or digest != topo["source_sha256"]:
            raise ValueError("Union exact source identity does not match candidate freezes")
        originals = {p["id"]: p["alternatives"] for p in original["pages"]}
        topologies = {p["id"]: p["alternatives"] for p in topo["pages"]}
        pages = []
        for page_index, page in enumerate(source["pages"]):
            candidates, provenance = union_candidates(page, originals[page["id"]], topologies[page["id"]])
            local_id = f"cohort{cohort_index}-page{page_index:03}"
            pages.append({"id": local_id, "source_id": page["id"], "candidates": candidates, "provenance": provenance})
            if page["vector_candidates"]:
                records.append(
                    {"id": local_id, "route": "native_vector", "native_selection": _native_inventory(page), "calls": 0}
                )
                continue
            for model_index, model in enumerate(models):
                body = union_request(page, candidates, model, with_image=True)
                if prompt_variant is not None:
                    body = transform(body, prompt_variant)
                data = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
                filename = f"{local_id}-model{model_index}-image512.json"
                (output / filename).write_bytes(data)
                records.append(
                    {
                        "id": local_id,
                        "model": model,
                        "arm": "image512",
                        "route": "hosted_admission",
                        "request": filename,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "bytes": len(data),
                        "choices": list(body["questions"]["q0"]["criteria"]),
                    }
                )
        cohorts.append(
            {
                "source_sha256": digest,
                "source_path": str(source_path.resolve()),
                "original_candidates_sha256": hashlib.sha256(original_raw).hexdigest(),
                "pages": pages,
            }
        )
    rss, measurement = process_peak_rss()
    manifest = {
        "schema": 1,
        "models": models,
        "arms": ["image512"],
        "prompt_variant": prompt_variant,
        "topology_freeze_sha256": hashlib.sha256(topology_raw).hexdigest(),
        "cohorts": cohorts,
        "records": records,
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": f"perf_counter/process_time; {measurement}; sequential CPU; lifetime RSS; no sampling",
    }
    data = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    (output / "manifest.json").write_bytes(data)
    return {
        "output": str(output),
        "manifest_sha256": hashlib.sha256(data).hexdigest(),
        "requests": sum(r["route"] == "hosted_admission" for r in records),
        "native_pages": sum(r["route"] == "native_vector" for r in records),
    }


def main() -> None:
    """Prepare candidates without targets, credentials or inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="*")
    parser.add_argument(
        "--targets", type=Path, nargs="+", help="Evaluate existing frozen candidates only; never regenerate"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.targets:
        result = score_frozen(args.output, args.targets)
    else:
        if not args.sources:
            parser.error("Preparation requires source exports")
        result = freeze(args.sources, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
