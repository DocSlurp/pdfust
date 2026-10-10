"""Geometry-first ownership with explicit baseline protection and model disputes.

Source support and placement margins are deterministic geometric diagnostics,
not probabilities. Only returned provider choices carry raw probabilities.
"""

# ruff: noqa: SLF001, EM101, TRY003, PLR2004, PLR0913, PLR0917, FBT001
from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from bench import p003_topology_chunks as chunks
from bench import p003_topology_geometry as geometry
from bench import p003_topology_ownership as own

POLICY = {
    "min_word_overlap": 0.98,
    "min_score_margin": 0.35,
    "box_padding_height_fraction": 0.1,
    "min_gutter_clear_fraction": 0.9,
    "min_gutter_bilateral_fraction": 0.5,
    "min_row_gap_height_fraction": 0.35,
    "baseline_box_coverage": 0.98,
    "scores_are_probabilities": False,
}


@dataclass(frozen=True)
class Hybrid:
    """Immutable complete source snapshot plus frozen source-only admission audit."""

    snapshot: own.Plan
    audit_json: str

    @property
    def sha256(self) -> str:
        """Bind the full plan, geometric decisions and original baseline structure."""
        return hashlib.sha256((self.snapshot.sha256 + self.audit_json).encode()).hexdigest()


def _spans(table: dict[str, Any]) -> list[list[int]]:
    return sorted(
        [
            [s["row"], s["column"], s["row_span"], s["column_span"]]
            for s in table["spans"]
            if s["row_span"] > 1 or s["column_span"] > 1
        ]
    )


def _coverage(a: list[float], b: list[float]) -> float:
    return geometry._intersection(a, b) / ((a[2] - a[0]) * (a[3] - a[1]))


def _baseline(value: dict[str, Any], tables: list[dict[str, Any]]) -> tuple[dict[str, str], bool]:
    canonical = value["topology"]["canonical"]
    mapping, used = {}, set()
    for table in tables:
        matches = [
            t
            for t, target in enumerate(canonical)
            if (table["row_count"], table["col_count"], _spans(table))
            == (target["row_count"], target["col_count"], _spans(target))
            and _coverage(table["bbox"], target["bbox"]) >= POLICY["baseline_box_coverage"]
        ]
        if len(matches) != 1 or matches[0] in used:
            return {}, False
        t = matches[0]
        used.add(t)
        for slot, cell in enumerate(table["cells"]):
            r, c = divmod(slot, table["col_count"])
            for identifier in cell["source_ids"]:
                if identifier in mapping:
                    raise ValueError("Baseline ownership duplicates a source ID")
                mapping[identifier] = f"t{t}r{r}c{c}"
    return mapping, True


def prepare(snapshot: own.Plan, baseline_tables: list[dict[str, Any]]) -> Hybrid:
    """Freeze conservative geometric commits and explicit baseline fallback choices."""
    value = chunks.packet(snapshot)
    source = value["source"]
    lookup = {w["id"]: w for w in source["words"]}
    # Revalidate original literal source ownership; its semantic correctness remains unverified.
    baseline = deepcopy(baseline_tables)
    ids = [i for t in baseline for c in t["cells"] for i in c["source_ids"]]
    if len(set(ids)) != len(ids) or not set(ids) <= set(lookup):
        raise ValueError("Baseline crop ownership is not an exact source subset")
    original_state = {
        "id": "c0",
        "tables": baseline,
        "unresolved_ids": [w["id"] for w in source["words"] if w["id"] not in set(ids)],
    }
    own.validate(source, original_state)
    fallbacks, compatible = _baseline(value, baseline)
    audit = {
        "policy": deepcopy(POLICY),
        "baseline_state": original_state,
        "baseline_fallbacks": fallbacks,
        "baseline_topology_compatible": compatible,
        "baseline_semantic_quality_verified": False,
        "locked": {},
        "disputed_ids": [],
        "geometry": [],
        "source_band_diagnostics": [],
        "baseline_gate": (
            "Native grids protected by runner; compatible source assignments require unique topology/box match"
        ),
    }
    if not compatible:
        audit["status"] = "baseline_topology_not_expressible_retained"
        return Hybrid(snapshot, own._dump(audit))
    measured = geometry.place(snapshot, band_mode="source")
    bands = measured["geometry_policy"]["bands"]
    audit["source_band_diagnostics"] = bands
    source_words = source["words"]
    heights = []
    supported = []
    for table, band in zip(value["topology"]["canonical"], bands, strict=True):
        words = [w for w in source_words if geometry._intersection(w["bbox"], table["bbox"]) > 0]
        height = statistics.median(w["bbox"][3] - w["bbox"][1] for w in words) if words else 1
        heights.append(height)
        rows = band["rows"]
        cols = band["columns"]
        row_ok = rows["method"] == "largest_physical_line_clearances" and all(
            g["clearance"] >= POLICY["min_row_gap_height_fraction"] * height for g in rows["selected_gaps"]
        )
        col_ok = cols["method"] == "single_column" or (
            cols["method"] == "persistent_source_whitespace"
            and all(
                g["clear_fraction"] >= POLICY["min_gutter_clear_fraction"]
                and g["bilateral_line_fraction"] >= POLICY["min_gutter_bilateral_fraction"]
                for g in cols["selected_gutters"]
            )
        )
        supported.append(row_ok and col_ok)
    for placement in measured["assignments"]:
        identifier = placement["source_id"]
        choice = placement["choice"]
        strong = False
        if choice not in {"outside", "unresolved"}:
            match = re.fullmatch(r"t(\d+)r(\d+)c(\d+)", choice)
            t, r, c = map(int, match.groups())
            table = value["topology"]["canonical"][t]
            span = next(
                (s for s in table["spans"] if (s["row"], s["column"]) == (r, c)), {"row_span": 1, "column_span": 1}
            )
            band = bands[t]
            bounds = [
                band["x_edges"][c],
                band["y_edges"][r],
                band["x_edges"][c + span["column_span"]],
                band["y_edges"][r + span["row_span"]],
            ]
            box = lookup[identifier]["bbox"]
            padding = POLICY["box_padding_height_fraction"] * heights[t]
            stable = (
                box[0] - padding >= bounds[0]
                and box[1] - padding >= bounds[1]
                and box[2] + padding <= bounds[2]
                and box[3] + padding <= bounds[3]
            )
            strong = (
                supported[t]
                and stable
                and placement["best_overlap_fraction"] >= POLICY["min_word_overlap"]
                and placement["margin"] >= POLICY["min_score_margin"]
            )
        # Baseline disagreement is a dispute even when the new geometric score is large.
        agree = identifier not in fallbacks or choice == fallbacks[identifier]
        if strong and agree:
            audit["locked"][identifier] = {
                "choice": choice,
                "provenance": "baseline_geometry_agreement"
                if identifier in fallbacks
                else "high_support_source_geometry",
            }
        else:
            audit["disputed_ids"].append(identifier)
        audit["geometry"].append(
            {k: placement[k] for k in ("source_id", "choice", "best_score", "best_overlap_fraction", "margin")}
            | {"support_passed": strong, "baseline_agreement": agree}
        )
    audit["status"] = "geometry_and_disputes"
    return Hybrid(snapshot, own._dump(audit))


def _audit(hybrid: Hybrid) -> tuple[dict[str, Any], dict[str, Any]]:
    value = chunks.packet(hybrid.snapshot)
    audit = json.loads(hybrid.audit_json)
    ids = {w["id"] for w in value["source"]["words"]}
    if audit["policy"] != POLICY or (
        audit["baseline_topology_compatible"]
        and (
            set(audit["locked"]) & set(audit["disputed_ids"])
            or set(audit["locked"]) | set(audit["disputed_ids"]) != ids
        )
    ):
        raise ValueError("Hybrid source assignment partition changed")
    return value, audit


def _body(
    hybrid: Hybrid,
    value: dict[str, Any],
    audit: dict[str, Any],
    indexes: list[int],
    model: str,
    url: str | None,
    rows: dict[str, Any] | None,
    image: bool,
    evidence_mode: str,
) -> dict[str, Any]:
    body = chunks._body(hybrid.snapshot, value, indexes, model, url, rows, image, evidence_mode)
    text = json.loads(body["state"][0] if image else body["state"])
    ids = [value["source"]["words"][i]["id"] for i in indexes]
    text["hybrid_snapshot_sha256"] = hybrid.sha256
    text["baseline_fallbacks"] = {i: audit["baseline_fallbacks"][i] for i in ids if i in audit["baseline_fallbacks"]}
    text["geometric_disputes"] = [d for d in audit["geometry"] if d["source_id"] in set(ids)]
    text["baseline_policy"] = (
        "Original source assignment fallback is explicit; formal/source validity is not semantic correctness"
    )
    state = own._dump(text)
    if len(state.encode()) + len(own._dump(body["questions"]).encode()) > own.MAX_PACKET_BYTES:
        raise ValueError("Complete hybrid local evidence exceeds cap")
    if image:
        body["state"][0] = state
    else:
        body["state"] = state
    return body


def _rows(hybrid: Hybrid, receipt: dict[str, Any], value: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    own.transcription._exact(receipt, {"hybrid_snapshot_sha256", "decisions"})
    if receipt["hybrid_snapshot_sha256"] != hybrid.sha256 or set(receipt["decisions"]) != set(audit["disputed_ids"]):
        raise ValueError("Hybrid row receipt lacks exact disputed IDs")
    options = own._row_options(value)
    output = {}
    for identifier, answer in receipt["decisions"].items():
        keys = set(answer["probabilities"])
        if not {"outside", "unresolved"} <= keys <= set(options):
            raise ValueError("Hybrid row receipt contains unknown menu options")
        for t, table in enumerate(value["tables"]):
            admitted = {f"t{t}r{r}" for r in range(table["row_count"])}
            if keys & admitted and not admitted <= keys:
                raise ValueError("Hybrid row receipt omitted admitted table rows")
        checked = own._choices(
            {k: answer[k] for k in ("type", "choice", "probabilities", "confidence") if k in answer},
            {k: options[k] for k in keys},
        )
        if checked != answer:
            raise ValueError("Hybrid row receipt raw evidence changed")
        output[identifier] = checked
    return output


def batches(
    hybrid: Hybrid,
    model: str,
    url: str,
    *,
    rows: dict[str, Any] | None = None,
    max_questions: int = 16,
    image: bool = True,
    evidence_mode: str = "neighbors",
) -> list[dict[str, Any]]:
    """Ask only disputed original IDs, retaining complete neighboring source data."""
    value, audit = _audit(hybrid)
    if (
        type(max_questions) is not int
        or not 1 <= max_questions <= 16
        or type(image) is not bool
        or own._image(url) != value["image_sha256"]
    ):
        raise ValueError("Invalid hybrid request admission")
    if not audit["baseline_topology_compatible"]:
        return []
    decisions = None if rows is None else _rows(hybrid, rows, value, audit)
    indexes = [
        i
        for i, w in enumerate(value["source"]["words"])
        if w["id"] in set(audit["disputed_ids"])
        and (decisions is None or decisions[w["id"]]["choice"] not in {"outside", "unresolved"})
    ]
    if math.ceil(len(indexes) / max_questions) > chunks.MAX_BATCHES:
        raise ValueError("Hybrid batch count exceeds cap")
    return [
        _body(hybrid, value, audit, indexes[start : start + max_questions], model, url, decisions, image, evidence_mode)
        for start in range(0, len(indexes), max_questions)
    ]


def collect(
    hybrid: Hybrid, bodies: list[dict[str, Any]], results: list[dict[str, Any]], *, rows: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Atomically replay every model dispute without inventing geometric probabilities."""
    value, audit = _audit(hybrid)
    decisions = None if rows is None else _rows(hybrid, rows, value, audit)
    expected = {
        i for i in audit["disputed_ids"] if decisions is None or decisions[i]["choice"] not in {"outside", "unresolved"}
    }
    lookup = {w["id"]: i for i, w in enumerate(value["source"]["words"])}
    if len(bodies) != len(results) or len(bodies) > chunks.MAX_BATCHES:
        raise ValueError("Incomplete hybrid batches")
    output = {}
    for body, result in zip(bodies, results, strict=True):
        image = isinstance(body["state"], list)
        evidence = json.loads(body["state"][0] if image else body["state"])
        mapping = evidence["target_source_ids"]
        if set(mapping) != {f"w{i}" for i in range(len(mapping))}:
            raise ValueError("Invalid hybrid local aliases")
        ids = [mapping[f"w{i}"] for i in range(len(mapping))]
        if not 1 <= len(ids) <= 16 or len(set(ids)) != len(ids) or any(i not in expected or i in output for i in ids):
            raise ValueError("Hybrid dispute identities changed or duplicate")
        canonical = _body(
            hybrid,
            value,
            audit,
            [lookup[i] for i in ids],
            body["model"],
            body["state"][1]["image_url"]["url"] if image else None,
            decisions,
            image,
            evidence["evidence_mode"],
        )
        if body != canonical or not isinstance(result, dict) or set(result.get("answers", {})) != set(mapping):
            raise ValueError("Hybrid body/answers differ from exact evidence")
        output.update(
            {
                identifier: own._choices(result["answers"][key], body["questions"][key]["criteria"])
                for key, identifier in mapping.items()
            }
        )
    if set(output) != expected:
        raise ValueError("Hybrid dispute decisions incomplete")
    return {"hybrid_snapshot_sha256": hybrid.sha256, "decisions": output}


def _state(value: dict[str, Any], choices: dict[str, str], audit: dict[str, Any]) -> dict[str, Any]:
    source, tables = value["source"], deepcopy(value["topology"]["canonical"])
    owners = {}
    for t, table in enumerate(tables):
        merged = {(s["row"], s["column"]): s for s in table["spans"]}
        table["spans"] = [
            deepcopy(merged.get((r, c), {"row": r, "column": c, "row_span": 1, "column_span": 1}))
            for r, row in enumerate(table["values"])
            for c, v in enumerate(row)
            if v is not None
        ]
        table["cells"] = [{"source_ids": [], "role": "unknown"} for _ in table["cells"]]
        owners.update(
            {
                f"t{t}r{r}c{c}": (t, r * table["col_count"] + c)
                for r, row in enumerate(table["values"])
                for c, v in enumerate(row)
                if v is not None
            }
        )
    unresolved = []
    for w in source["words"]:
        choice = choices[w["id"]]
        if choice in owners:
            t, slot = owners[choice]
            tables[t]["cells"][slot]["source_ids"].append(w["id"])
        elif choice in {"outside", "unresolved"}:
            unresolved.append(w["id"])
        else:
            raise ValueError("Hybrid choice cannot express a physical anchor")
    # Preserve the exact original cell order/role when its ownership set is unchanged.
    for original in audit["baseline_state"]["tables"]:
        for cell in original["cells"]:
            if cell["source_ids"]:
                anchor = audit["baseline_fallbacks"][cell["source_ids"][0]]
                t, slot = owners[anchor]
                if set(tables[t]["cells"][slot]["source_ids"]) == set(cell["source_ids"]):
                    tables[t]["cells"][slot] = deepcopy(cell)
    lookup = {w["id"]: w for w in source["words"]}
    state = {
        "id": "c0",
        "tables": [{**own._clean_table(t, lookup), "bbox": t["bbox"]} for t in tables],
        "unresolved_ids": unresolved,
        "mechanism": "p003_geometry_first_model_disputes",
    }
    own.validate(source, state)
    return state


def assemble(
    hybrid: Hybrid,
    row_bodies: list[dict[str, Any]],
    row_results: list[dict[str, Any]],
    cell_bodies: list[dict[str, Any]],
    cell_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Commit deterministic and provider assignments once, preserving explicit fallback."""
    value, audit = _audit(hybrid)
    if not audit["baseline_topology_compatible"]:
        if any((row_bodies, row_results, cell_bodies, cell_results)):
            raise ValueError("Protected baseline needs no model requests")
        return {
            "state": audit["baseline_state"],
            "hybrid_snapshot_sha256": hybrid.sha256,
            "status": audit["status"],
            "source_conserved": True,
            "baseline_structure_retained": True,
            "new_model_questions": 0,
        }
    rows = collect(hybrid, row_bodies, row_results)
    cells = collect(hybrid, cell_bodies, cell_results, rows=rows)
    choices = {i: d["choice"] for i, d in audit["locked"].items()}
    provenance = {i: d["provenance"] for i, d in audit["locked"].items()}
    for identifier in audit["disputed_ids"]:
        row = rows["decisions"][identifier]["choice"]
        choice = cells["decisions"].get(identifier, {}).get("choice", row)
        if choice == "unresolved" and identifier in audit["baseline_fallbacks"]:
            choice = audit["baseline_fallbacks"][identifier]
            provenance[identifier] = "explicit_baseline_abstention_fallback"
        else:
            provenance[identifier] = "model_dispute_choice"
        choices[identifier] = choice
    return {
        "state": _state(value, choices, audit),
        "hybrid_snapshot_sha256": hybrid.sha256,
        "source_conserved": True,
        "text_provenance": "literal-source-words",
        "status": "geometry_and_disputes",
        "assignment_choices": choices,
        "assignment_provenance": provenance,
        "rows": rows,
        "cells": cells,
        "geometry_policy": POLICY,
        "geometry_locked_count": len(audit["locked"]),
        "model_disputed_count": len(audit["disputed_ids"]),
        "quality_verified": False,
        "missing_source_text_recoverable": False,
    }
