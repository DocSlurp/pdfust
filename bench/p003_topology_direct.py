"""Single-stage disputed word ownership with explicit geometric candidate menus."""

# ruff: noqa: SLF001, EM101, TRY003, PLR2004, PLR0913, PLR0917, FBT001
from __future__ import annotations

import json
import math
import re
from typing import Any

from bench import p003_topology_geometry as geometry
from bench import p003_topology_hybrid as hybrid
from bench import p003_topology_ownership as own

MAX_ANCHORS = 32
NEAREST_ANCHORS = 8


def _menus(mixed: hybrid.Hybrid) -> dict[str, list[dict[str, Any]]]:
    value, audit = hybrid._audit(mixed)
    if not audit["baseline_topology_compatible"]:
        return {}
    scored = geometry.place(mixed.snapshot, band_mode="source")
    output = {}
    for item in scored["assignments"]:
        identifier = item["source_id"]
        if identifier not in audit["disputed_ids"]:
            continue
        ranks = item["anchor_scores"]
        selected = {r["anchor"] for r in ranks[:NEAREST_ANCHORS]}
        selected.update(r["anchor"] for r in ranks if r["overlap_fraction"] > 0)
        if identifier in audit["baseline_fallbacks"]:
            selected.add(audit["baseline_fallbacks"][identifier])
        if len(selected) > MAX_ANCHORS:
            raise ValueError("Complete intersecting direct-cell candidate menu exceeds explicit cap")
        retained = []
        bands = scored["geometry_policy"]["bands"]
        for rank in ranks:
            if rank["anchor"] not in selected:
                continue
            anchor = rank["anchor"]
            t, r, c = (int(v) for v in re.fullmatch(r"t(\d+)r(\d+)c(\d+)", anchor).groups())
            span = next(
                (s for s in value["topology"]["canonical"][t]["spans"] if s["row"] == r and s["column"] == c),
                {"row_span": 1, "column_span": 1},
            )
            retained.append(
                {
                    **rank,
                    "bbox": [
                        bands[t]["x_edges"][c],
                        bands[t]["y_edges"][r],
                        bands[t]["x_edges"][c + span["column_span"]],
                        bands[t]["y_edges"][r + span["row_span"]],
                    ],
                    "row_span": span["row_span"],
                    "column_span": span["column_span"],
                }
            )
        output[identifier] = retained
    return output


def _body(
    mixed: hybrid.Hybrid,
    value: dict[str, Any],
    audit: dict[str, Any],
    indexes: list[int],
    menus: dict[str, Any],
    model: str,
    url: str | None,
    image: bool,
    evidence_mode: str,
) -> dict[str, Any]:
    body = hybrid._body(mixed, value, audit, indexes, model, url, None, image, evidence_mode)
    evidence = json.loads(body["state"][0] if image else body["state"])
    evidence["ownership_stage"] = "direct_cell"
    evidence["stage"] = "direct_cell"
    evidence["direct_candidate_policy"] = {
        "nearest_anchors": NEAREST_ANCHORS,
        "max_anchors": MAX_ANCHORS,
        "all_positive_overlap_anchors_included": True,
        "compatible_baseline_owner_included": True,
        "other_owners_withheld": True,
        "scores_are_probabilities": False,
        "limitation": "Geometry shortlist may miss a true owner; choose unresolved rather than invent another owner",
    }
    evidence["direct_anchor_scores"] = {}
    for alias, identifier in evidence["target_source_ids"].items():
        ranks = menus[identifier]
        evidence["direct_anchor_scores"][alias] = ranks
        criteria = {r["anchor"]: f"Complete source word belongs to frozen physical anchor {r['anchor']}" for r in ranks}
        criteria.update(outside="Word is outside every table", unresolved="Evidence cannot establish an asked owner")
        body["questions"][alias]["criteria"] = criteria
        body["questions"][alias]["instructions"] += (
            " Select a physical cell anchor directly in this single stage. "
            "direct_anchor_scores.bbox uses original global display coordinates; "
            "geometric scores are not probabilities. "
            "No prior row selection restricts this menu; only exactly listed owners are admissible."
        )
    state = own._dump(evidence)
    if len(state.encode()) + len(own._dump(body["questions"]).encode()) > own.MAX_PACKET_BYTES:
        raise ValueError("Complete direct-cell evidence exceeds local cap")
    if image:
        body["state"][0] = state
    else:
        body["state"] = state
    return body


def batches(
    mixed: hybrid.Hybrid,
    model: str,
    url: str,
    *,
    max_questions: int = 16,
    image: bool = True,
    evidence_mode: str = "neighbors",
) -> list[dict[str, Any]]:
    """Ask one complete ownership question per disputed original source word."""
    value, audit = hybrid._audit(mixed)
    if type(max_questions) is not int or not 1 <= max_questions <= 16 or type(image) is not bool:
        raise ValueError("Invalid direct-cell batch admission")
    if own._image(url) != value["image_sha256"]:
        raise ValueError("Direct-cell viewport image changed")
    menus = _menus(mixed)
    indexes = [i for i, w in enumerate(value["source"]["words"]) if w["id"] in menus]
    if math.ceil(len(indexes) / max_questions) > hybrid.chunks.MAX_BATCHES:
        raise ValueError("Direct-cell batch count exceeds cap")
    return [
        _body(mixed, value, audit, indexes[s : s + max_questions], menus, model, url, image, evidence_mode)
        for s in range(0, len(indexes), max_questions)
    ]


def collect(mixed: hybrid.Hybrid, bodies: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    """Strictly replay exactly asked physical anchors and retain their raw probabilities."""
    value, audit = hybrid._audit(mixed)
    menus = _menus(mixed)
    lookup = {w["id"]: i for i, w in enumerate(value["source"]["words"])}
    if len(bodies) != len(results) or len(bodies) > hybrid.chunks.MAX_BATCHES:
        raise ValueError("Incomplete direct-cell batches")
    output = {}
    for body, result in zip(bodies, results, strict=True):
        image = isinstance(body["state"], list)
        evidence = json.loads(body["state"][0] if image else body["state"])
        mapping = evidence["target_source_ids"]
        if set(mapping) != {f"w{i}" for i in range(len(mapping))} or not 1 <= len(mapping) <= 16:
            raise ValueError("Direct-cell local aliases changed")
        ids = [mapping[f"w{i}"] for i in range(len(mapping))]
        if len(set(ids)) != len(ids) or any(i not in menus or i in output for i in ids):
            raise ValueError("Direct-cell source IDs unknown or duplicate")
        expected = _body(
            mixed,
            value,
            audit,
            [lookup[i] for i in ids],
            menus,
            body["model"],
            body["state"][1]["image_url"]["url"] if image else None,
            image,
            evidence["evidence_mode"],
        )
        if body != expected or not isinstance(result, dict) or set(result.get("answers", {})) != set(mapping):
            raise ValueError("Direct-cell immutable request/answer identities changed")
        for alias, identifier in mapping.items():
            output[identifier] = own._choices(result["answers"][alias], body["questions"][alias]["criteria"])
    if set(output) != set(menus):
        raise ValueError("Direct-cell source decisions incomplete")
    return {"hybrid_snapshot_sha256": mixed.sha256, "ownership_stage": "direct_cell", "decisions": output}


def assemble(mixed: hybrid.Hybrid, bodies: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine one-stage model disputes and deterministic locks atomically."""
    value, audit = hybrid._audit(mixed)
    if not audit["baseline_topology_compatible"]:
        if bodies or results:
            raise ValueError("Protected baseline requires no direct-cell requests")
        return hybrid.assemble(mixed, [], [], [], [])
    receipt = collect(mixed, bodies, results)
    choices = {i: d["choice"] for i, d in audit["locked"].items()}
    provenance = {i: d["provenance"] for i, d in audit["locked"].items()}
    for identifier, decision in receipt["decisions"].items():
        choice = decision["choice"]
        if choice == "unresolved" and identifier in audit["baseline_fallbacks"]:
            choice = audit["baseline_fallbacks"][identifier]
            provenance[identifier] = "explicit_baseline_abstention_fallback"
        else:
            provenance[identifier] = "model_direct_cell_choice"
        choices[identifier] = choice
    return {
        "state": hybrid._state(value, choices, audit),
        "hybrid_snapshot_sha256": mixed.sha256,
        "source_conserved": True,
        "text_provenance": "literal-source-words",
        "status": "geometry_and_direct_disputes",
        "assignment_choices": choices,
        "assignment_provenance": provenance,
        "direct": receipt,
        "geometry_policy": hybrid.POLICY,
        "geometry_locked_count": len(audit["locked"]),
        "model_disputed_count": len(audit["disputed_ids"]),
        "quality_verified": False,
        "missing_source_text_recoverable": False,
    }
