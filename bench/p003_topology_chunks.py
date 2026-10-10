"""Complete retained source inventory with bounded local ownership questions.

All source strings stay immutable locally; each body names <=16 target words.
Context selection is explicit and cannot remove or truncate a target word.
"""

# ruff: noqa: SLF001, EM101, TRY003, PLR2004, PLR0913, PLR0917, FBT001
from __future__ import annotations

import json
import math
from copy import deepcopy
from typing import Any

from bench import p003_spatial_bands as spatial
from bench import p003_topology_ownership as own

MAX_WORDS = 4096
MAX_INVENTORY_BYTES = 1024 * 1024
MAX_BATCHES = 256
MAX_CONTEXT_WORDS = 12
MAX_CONTEXT_BYTES = 16_000


def _topology(tables: list[dict[str, Any]], viewport: list[float]) -> dict[str, Any]:
    """Admit complete topology locally, while each request keeps the old row cap."""
    if not isinstance(tables, list) or len(tables) > own.MAX_TABLES:
        raise ValueError("Complete chunk table inventory exceeds cap")
    canonical = []
    total_rows, total_slots = 0, 0
    for table in tables:
        parsed = own._topology([table], viewport)
        total_rows += table["row_count"]
        total_slots += table["row_count"] * table["col_count"]
        if total_rows > 256 or total_slots > own.MAX_SLOTS:
            raise ValueError("Complete chunk topology exceeds 256 rows/4096 slots")
        box = parsed["canonical"][0]["bbox"]
        for previous in canonical:
            a = previous["bbox"]
            if min(a[2], box[2]) > max(a[0], box[0]) and min(a[3], box[3]) > max(a[1], box[1]):
                raise ValueError("Chunk topology tables overlap")
        canonical.extend(parsed["canonical"])
    return {"tables": deepcopy(tables), "viewport": list(viewport), "canonical": canonical}


def packet(plan: own.Plan) -> dict[str, Any]:
    """Validate the complete immutable inventory independently of request size."""
    if not isinstance(plan, own.Plan) or len(plan.packet_json.encode()) > MAX_INVENTORY_BYTES:
        raise ValueError("Complete chunk inventory exceeds explicit 1MiB cap")
    value = json.loads(plan.packet_json, object_pairs_hook=own._unique_pairs, parse_constant=own._invalid_constant)
    own.transcription._exact(value, {"source", "tables", "viewport", "image_sha256", "version"})
    if value["version"] != 2 or type(value["version"]) is not int:
        raise ValueError("Unknown chunk ownership version")
    source = own._source(value["source"])
    if (
        source != value["source"]
        or len(source["words"]) > MAX_WORDS
        or any(not w["id"] or len(w["id"]) > 128 for w in source["words"])
    ):
        raise ValueError("Invalid complete chunk source inventory")
    value["topology"] = _topology(value["tables"], value["viewport"])
    return value


def freeze(source: dict[str, Any], response: dict[str, Any], viewport: list[float], url: str) -> own.Plan:
    """Keep complete strings/boxes locally; never increase per-request text caps."""
    payload, _ = own.scaffold._payload(response)
    topology = _topology(payload["answers"]["q0"]["tables"], viewport)
    plan = own.Plan(
        own._dump(
            {
                "version": 2,
                "source": own._source(source),
                "tables": topology["tables"],
                "viewport": topology["viewport"],
                "image_sha256": own._image(url),
            }
        )
    )
    packet(plan)
    return plan


def _receipt(plan: own.Plan, rows: dict[str, Any], value: dict[str, Any]) -> dict[str, Any]:
    own.transcription._exact(rows, {"snapshot_sha256", "decisions"})
    if rows["snapshot_sha256"] != plan.sha256 or set(rows["decisions"]) != {w["id"] for w in value["source"]["words"]}:
        raise ValueError("Chunk receipt must cover complete global source IDs")
    global_options = own._row_options(value)
    output = {}
    for key, answer in rows["decisions"].items():
        keys = set(answer["probabilities"])
        if not {"outside", "unresolved"} <= keys <= set(global_options):
            raise ValueError("Chunk row receipt contains unknown menu options")
        for t, table in enumerate(value["tables"]):
            table_keys = {f"t{t}r{r}" for r in range(table["row_count"])}
            if keys & table_keys and not table_keys <= keys:
                raise ValueError("Chunk row menu omitted part of an admitted table")
        output[key] = own._choices(
            {k: answer[k] for k in ("type", "choice", "probabilities", "confidence") if k in answer},
            {k: global_options[k] for k in keys},
        )
    return output


def _body(
    plan: own.Plan,
    value: dict[str, Any],
    indexes: list[int],
    model: str,
    url: str | None,
    rows: dict[str, Any] | None,
    image: bool,
    evidence_mode: str,
) -> dict[str, Any]:
    if evidence_mode not in {"compact", "neighbors", "bands"}:
        raise ValueError("Unknown chunk evidence mode")
    words = value["source"]["words"]
    table_indexes = [
        t
        for t, table in enumerate(value["topology"]["canonical"])
        if any(
            min(words[i]["bbox"][2], table["bbox"][2]) > max(words[i]["bbox"][0], table["bbox"][0])
            and min(words[i]["bbox"][3], table["bbox"][3]) > max(words[i]["bbox"][1], table["bbox"][1])
            for i in indexes
        )
    ]
    if rows is not None:
        selected_tables = {
            t
            for t in range(len(value["tables"]))
            if any(rows[words[i]["id"]]["choice"].startswith(f"t{t}r") for i in indexes)
        }
        table_indexes = sorted(set(table_indexes) | selected_tables)
    local = own.Plan(
        own._dump(
            {
                **{k: v for k, v in value.items() if k not in {"topology", "source", "version"}},
                "version": 1,
                "tables": [value["tables"][t] for t in table_indexes],
                "source": {"page_size": value["source"]["page_size"], "words": [words[i] for i in indexes]},
            }
        )
    )
    local_packet = own._packet(local)
    decisions = None if rows is None else {f"w{i}": rows[words[index]["id"]] for i, index in enumerate(indexes)}
    body = own._body(local, local_packet, list(range(len(indexes))), model, url, decisions, image=image)
    row_menu = {
        key: description
        for key, description in own._row_options(value).items()
        if key in {"outside", "unresolved"} or any(key.startswith(f"t{t}r") for t in table_indexes)
    }
    for i, index in enumerate(indexes):
        body["questions"][f"w{i}"]["criteria"] = (
            row_menu if rows is None else own._anchors(value, rows[words[index]["id"]]["choice"])
        )
    text = body["state"][0] if image else body["state"]
    evidence = json.loads(text)
    evidence["global_snapshot_sha256"] = plan.sha256
    evidence["table_ids"] = [f"t{t}" for t in table_indexes]
    evidence["table_menu_policy"] = (
        "Every frozen table whose global box intersects a target word box; whole row menu per included table; "
        "other tables withheld; this is a geometric hypothesis"
    )
    evidence["target_source_ids"] = {f"w{i}": words[index]["id"] for i, index in enumerate(indexes)}
    evidence["inventory_scope"] = (
        "Complete inventory retained locally; only named targets receive questions, context selection explicit"
    )
    evidence["evidence_mode"] = evidence_mode
    if evidence_mode == "neighbors":
        target = [words[i] for i in indexes]
        excluded = set(indexes)
        # Geometry-only nearest context, with four topmost header-like words; no label semantics.
        header = sorted(
            (i for i in range(len(words)) if i not in excluded),
            key=lambda i: (words[i]["bbox"][1], words[i]["bbox"][0], i),
        )[:4]
        nearest = sorted(
            (i for i in range(len(words)) if i not in excluded and i not in header),
            key=lambda i: (
                min(
                    abs((words[i]["bbox"][1] + words[i]["bbox"][3]) - (w["bbox"][1] + w["bbox"][3]))
                    + 0.1 * abs((words[i]["bbox"][0] + words[i]["bbox"][2]) - (w["bbox"][0] + w["bbox"][2]))
                    for w in target
                ),
                i,
            ),
        )[: MAX_CONTEXT_WORDS - len(header)]
        evidence["context_words"] = [words[i] for i in header + nearest]
        evidence["context_policy"] = (
            "At most 4 topmost and 8 nearest words by box coordinates; other nontarget words explicitly omitted"
        )
        if len(own._dump(evidence["context_words"]).encode()) > MAX_CONTEXT_BYTES:
            raise ValueError("Complete selected neighbor context exceeds cap; no clipping")
    if evidence_mode == "bands":
        evidence["source_band_hints"] = [spatial.derive(words, t) for t in value["topology"]["canonical"]]
        evidence["band_policy"] = (
            "Source-only geometric hints, explicit uniform fallback possible; not correctness or probability"
        )
    text = own._dump(evidence)
    if len(text.encode()) + len(own._dump(body["questions"]).encode()) > own.MAX_PACKET_BYTES:
        raise ValueError("Complete local targets/menu/context exceed request cap; no truncation")
    if image:
        body["state"][0] = text
    else:
        body["state"] = text
    return body


def batches(
    plan: own.Plan,
    model: str,
    url: str,
    *,
    rows: dict[str, Any] | None = None,
    max_questions: int = 16,
    image: bool = True,
    evidence_mode: str = "compact",
) -> list[dict[str, Any]]:
    """Declare bounded local batches covering each eligible original ID exactly once."""
    value = packet(plan)
    if (
        type(max_questions) is not int
        or not 1 <= max_questions <= 16
        or type(image) is not bool
        or own._image(url) != value["image_sha256"]
    ):
        raise ValueError("Invalid chunk batch/image admission")
    decisions = _receipt(plan, rows, value) if rows is not None else None
    indexes = [
        i
        for i, w in enumerate(value["source"]["words"])
        if decisions is None or decisions[w["id"]]["choice"] not in {"outside", "unresolved"}
    ]
    if math.ceil(len(indexes) / max_questions) > MAX_BATCHES:
        raise ValueError("Chunk stage exceeds explicit 256 batch cap")
    return [
        _body(plan, value, indexes[start : start + max_questions], model, url, decisions, image, evidence_mode)
        for start in range(0, len(indexes), max_questions)
    ]


def collect(
    plan: own.Plan, bodies: list[dict[str, Any]], results: list[dict[str, Any]], *, rows: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate bodies and exact question IDs, then combine without partial success."""
    value = packet(plan)
    decisions = _receipt(plan, rows, value) if rows is not None else None
    expected = {
        w["id"]
        for w in value["source"]["words"]
        if decisions is None or decisions[w["id"]]["choice"] not in {"outside", "unresolved"}
    }
    lookup = {w["id"]: i for i, w in enumerate(value["source"]["words"])}
    if len(bodies) != len(results) or len(bodies) > MAX_BATCHES:
        raise ValueError("Incomplete chunk response inventory")
    output = {}
    for body, result in zip(bodies, results, strict=True):
        image = isinstance(body["state"], list)
        evidence = json.loads(body["state"][0] if image else body["state"])
        mapping = evidence["target_source_ids"]
        if set(mapping) != {f"w{i}" for i in range(len(mapping))}:
            raise ValueError("Chunk local aliases must exactly match bounded numeric identities")
        ids = [mapping[f"w{i}"] for i in range(len(mapping))]
        if not 1 <= len(ids) <= 16 or len(ids) != len(set(ids)) or any(i not in expected or i in output for i in ids):
            raise ValueError("Unknown or duplicate global chunk identity")
        canonical = _body(
            plan,
            value,
            [lookup[i] for i in ids],
            body["model"],
            body["state"][1]["image_url"]["url"] if image else None,
            decisions,
            image,
            evidence["evidence_mode"],
        )
        if (
            body != canonical
            or not isinstance(result, dict)
            or set(result.get("answers", {})) != set(body["questions"])
        ):
            raise ValueError("Chunk body/answers differ from immutable evidence")
        for key, identifier in evidence["target_source_ids"].items():
            output[identifier] = own._choices(result["answers"][key], body["questions"][key]["criteria"])
    if set(output) != expected:
        raise ValueError("Chunk global source assignments incomplete")
    return {"snapshot_sha256": plan.sha256, "decisions": output}


def assemble(
    plan: own.Plan,
    row_bodies: list[dict[str, Any]],
    row_results: list[dict[str, Any]],
    cell_bodies: list[dict[str, Any]],
    cell_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble globally only after every original word decision validates."""
    rows = collect(plan, row_bodies, row_results)
    cells = collect(plan, cell_bodies, cell_results, rows=rows)
    value = packet(plan)
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
    outside, unresolved = [], []
    for word in source["words"]:
        identifier = word["id"]
        row = rows["decisions"][identifier]["choice"]
        choice = cells["decisions"].get(identifier, {}).get("choice", row)
        if choice in owners:
            t, slot = owners[choice]
            tables[t]["cells"][slot]["source_ids"].append(identifier)
        else:
            (outside if row == "outside" else unresolved).append(identifier)
    lookup = {w["id"]: w for w in source["words"]}
    tables = [{**own._clean_table(t, lookup), "bbox": t["bbox"]} for t in tables]
    remaining = set(outside + unresolved)
    state = {
        "id": "c0",
        "tables": tables,
        "unresolved_ids": [w["id"] for w in source["words"] if w["id"] in remaining],
        "mechanism": "p003_topology_chunked_ownership",
    }
    own.validate(source, state)
    return {
        "state": state,
        "snapshot_sha256": plan.sha256,
        "source_conserved": True,
        "text_provenance": "literal-source-words",
        "outside_ids": outside,
        "abstained_ids": unresolved,
        "rows": rows,
        "cells": cells,
        "quality_verified": False,
        "missing_source_text_recoverable": False,
        "inventory_scope": "Complete inventory retained locally; local batch evidence bounded",
    }
