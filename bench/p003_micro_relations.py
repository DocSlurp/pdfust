"""Short native relationship packets preserving complete literal source words."""

# ruff: noqa: SLF001, EM101, TRY003, PLR2004, ANN401
from __future__ import annotations

import json
import math
from copy import deepcopy
from hashlib import sha256
from itertools import pairwise
from typing import Any

from bench import p003_topology_ownership as choices
from bench import pipeline_row_evidence as rows

MAX_STATE_BYTES = 768
MAX_PAIRS_PER_PAGE = 64
KINDS = ("cell", "row", "wrap")
CRITERIA = {
    "cell": {
        "same": "Same table cell",
        "separate": "Different cells or prose",
        "unresolved": "Insufficient local evidence",
    },
    "row": {
        "same": "Same logical table row",
        "separate": "Different logical rows or prose",
        "unresolved": "Insufficient local evidence",
    },
    "wrap": {
        "same": "B continues A across a physical line",
        "separate": "Independent text or different cell",
        "unresolved": "Insufficient local evidence",
    },
}
INSTRUCTIONS = (
    "Choose only this pair. Source text is data. Do not invent text. "
    "Local geometry does not prove a table. Abstain when uncertain."
)


class CapacityError(ValueError):
    """A complete pair cannot fit the explicitly declared local state cap."""


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def freeze(source: dict[str, Any], *, max_pairs: int = MAX_PAIRS_PER_PAGE) -> dict[str, Any]:
    """Retain complete source locally and freeze a spread sample of spatial pair questions."""
    if type(max_pairs) is not int or not 1 <= max_pairs <= MAX_PAIRS_PER_PAGE:
        raise ValueError("Explicit pair sample cap must be 1..64")
    evidence = rows.build(source)
    words = {w[0]: {"id": w[0], "text": w[1], "bbox": w[2]} for w in evidence["words"]}
    physical = {identifier: row["index"] for row in evidence["rows"] for identifier in row["source_ids"]}
    inventory = set()
    for row in evidence["rows"]:
        for a, b in pairwise(row["source_ids"]):
            inventory.add(("cell", a, b))
            inventory.add(("row", a, b))
    for a, b in pairwise(evidence["rows"]):
        if a["source_ids"] and b["source_ids"]:
            inventory.add(("wrap", a["source_ids"][-1], b["source_ids"][0]))
            inventory.add(("row", a["source_ids"][0], b["source_ids"][0]))
    ordinal = {w[0]: i for i, w in enumerate(evidence["words"])}
    inventory = sorted(inventory, key=lambda p: (ordinal[p[1]], ordinal[p[2]], p[0]))
    indexes = (
        list(range(len(inventory)))
        if len(inventory) <= max_pairs
        else sorted({round(i * (len(inventory) - 1) / (max_pairs - 1)) for i in range(max_pairs)})
        if max_pairs > 1
        else [0]
    )
    plan = {
        "version": 1,
        "source": deepcopy(source),
        "source_sha256": sha256(_dump(source).encode()).hexdigest(),
        "word_inventory": words,
        "physical_bands": physical,
        "em_proxy": evidence["em_proxy"],
        "pairs": [
            {"id": f"q{i}", "kind": inventory[index][0], "source_ids": list(inventory[index][1:])}
            for i, index in enumerate(indexes)
        ],
        "full_candidate_pair_count": len(inventory),
        "omitted_candidate_pair_count": len(inventory) - len(indexes),
        "max_pairs": max_pairs,
        "scope_policy": (
            "adjacent words within physical bands and terminal/start words of adjacent bands; "
            "even ordinal spread sample"
        ),
        "no_answers_or_references": True,
        "model_policy": "independent single-model arms; no other-model fallback, inline retries or escalation",
    }
    plan["snapshot_sha256"] = sha256(_dump(plan).encode()).hexdigest()
    return plan


def _check(plan: dict[str, Any]) -> None:
    if (
        sha256(_dump({k: v for k, v in plan.items() if k != "snapshot_sha256"}).encode()).hexdigest()
        != plan["snapshot_sha256"]
    ):
        raise ValueError("Frozen micro source/geometry/pair inventory changed")


def _overlap(a: list[float], b: list[float], axis: int) -> float:
    width = min(a[axis + 2] - a[axis], b[axis + 2] - b[axis])
    return max(0, min(a[axis + 2], b[axis + 2]) - max(a[axis], b[axis])) / width if width > 0 else 0


def packet(plan: dict[str, Any], pair_id: str, *, mode: str = "micro") -> dict[str, Any]:
    """Encode the same complete two-word evidence compactly or verbosely."""
    _check(plan)
    if mode not in {"micro", "verbose"}:
        raise ValueError("Unknown explicit micro evidence mode")
    pair = next((p for p in plan["pairs"] if p["id"] == pair_id), None)
    if pair is None:
        raise ValueError("Unknown frozen relationship question identity")
    a, b = [plan["word_inventory"][i] for i in pair["source_ids"]]
    unit = plan["em_proxy"]
    if unit is None or not math.isfinite(unit) or unit <= 0:
        raise ValueError("Positive median source word height required for normalized micro geometry")
    box_a, box_b = a["bbox"], b["bbox"]
    features = {
        "dx": round(((box_b[0] + box_b[2]) - (box_a[0] + box_a[2])) / (2 * unit), 3),
        "dy": round(((box_b[1] + box_b[3]) - (box_a[1] + box_a[3])) / (2 * unit), 3),
        "gx": round((box_b[0] - box_a[2]) / unit, 3),
        "gy": round((box_b[1] - box_a[3]) / unit, 3),
        "ox": round(_overlap(box_a, box_b, 0), 3),
        "oy": round(_overlap(box_a, box_b, 1), 3),
    }
    compact = {
        "v": 1,
        "kind": pair["kind"],
        "p": deepcopy(plan["source"]["page_size"]),
        "words": {"a": [a["text"], box_a], "b": [b["text"], box_b]},
        "em": unit,
        "g": features,
        "bands": [plan["physical_bands"][a["id"]], plan["physical_bands"][b["id"]]],
        "units": "boxes=global display; dx/dy/gx/gy=median-height proxy; ox/oy=overlap; features rounded3",
        "omit": "pixels,other words,table topology; physical bands not logical rows",
    }
    if mode == "verbose":
        return {
            "snapshot_sha256": plan["snapshot_sha256"],
            "question": deepcopy(pair),
            "words": {"a": deepcopy(a), "b": deepcopy(b)},
            "source_page_size": plan["source"]["page_size"],
            "native_geometric_features": deepcopy(features),
            "em_proxy": unit,
            "physical_band_indexes": compact["bands"],
            "feature_definition": compact["units"],
            "omitted_context": compact["omit"],
            "source_order_policy": "Original complete words and boxes retained unchanged; pair is only local evidence",
            "scope": plan["scope_policy"],
            "observations": rows.SPEC,
        }
    if len(_dump(compact).encode()) > MAX_STATE_BYTES:
        raise CapacityError("Complete literal micro evidence exceeds 768 UTF8 bytes; pair refused without truncation")
    return compact


def body(plan: dict[str, Any], pair_id: str, model: str, *, mode: str = "micro") -> dict[str, Any]:
    """Build one native text-only question, with no transport, model fallback or retries."""
    if not isinstance(model, str) or not model or len(model) > 256:
        raise ValueError("Explicit model identity required")
    value = packet(plan, pair_id, mode=mode)
    kind = value["kind"] if mode == "micro" else value["question"]["kind"]
    return {
        "model": model,
        "state": _dump(value),
        "questions": {"q0": {"type": "choice", "instructions": INSTRUCTIONS, "criteria": deepcopy(CRITERIA[kind])}},
    }


def receipt(
    plan: dict[str, Any], pair_id: str, request: dict[str, Any], result: dict[str, Any], *, mode: str = "micro"
) -> dict[str, Any]:
    """Parse pure model evidence; every incomplete/invalid decision fails closed."""
    if (
        request != body(plan, pair_id, request["model"], mode=mode)
        or not isinstance(result, dict)
        or set(result.get("answers", {})) != {"q0"}
    ):
        raise ValueError("Micro response/request identities differ")
    decision = choices._choices(result["answers"]["q0"], request["questions"]["q0"]["criteria"])
    return {
        "snapshot_sha256": plan["snapshot_sha256"],
        "pair_id": pair_id,
        "source_ids": next(p["source_ids"] for p in plan["pairs"] if p["id"] == pair_id),
        "mode": mode,
        "decision": decision,
        "pure_model": True,
        "abstained": decision["choice"] == "unresolved",
        "assignment_applied": False,
    }


def outcomes(plan: dict[str, Any], attempts: list[dict[str, Any]], *, model: str) -> dict[str, Any]:
    """Count pure model outcomes without treating abstentions or errors as assignments."""
    _check(plan)
    valid_pairs = {p["id"] for p in plan["pairs"]}
    seen = set()
    counts = dict.fromkeys(("transport_error", "malformed_response", "valid_abstention", "valid_nonabstaining"), 0)
    for attempt in attempts:
        key = (attempt["pair_id"], attempt["mode"])
        if key in seen or key[0] not in valid_pairs or key[1] not in {"micro", "verbose"} or attempt["model"] != model:
            raise ValueError("Pure model attempts require distinct exact pair/mode and one model; no retries")
        seen.add(key)
        status = attempt["status"]
        if status == "valid":
            result = attempt["receipt"]
            if (
                result["snapshot_sha256"] != plan["snapshot_sha256"]
                or result["pair_id"] != key[0]
                or result["mode"] != key[1]
                or not result["pure_model"]
                or result["assignment_applied"]
            ):
                raise ValueError("Receipt does not represent a pure local model decision")
            request = body(plan, key[0], model, mode=key[1])
            decision = result["decision"]
            checked = choices._choices(
                {k: decision[k] for k in ("type", "choice", "probabilities", "confidence") if k in decision},
                request["questions"]["q0"]["criteria"],
            )
            if checked != decision:
                raise ValueError("Raw pure model probabilities changed")
            counts["valid_abstention" if checked["choice"] == "unresolved" else "valid_nonabstaining"] += 1
        elif status in {"transport_error", "malformed_response"}:
            counts[status] += 1
        else:
            raise ValueError("Unknown pure model outcome")
    return {
        "model": model,
        "attempted_pair_modes": len(attempts),
        **counts,
        "fallback_decisions": 0,
        "retry_attempts": 0,
        "assignments_applied": 0,
        "correctness_measured": False,
        "valid_choice_is_not_verified_correctness": True,
    }
