"""Offline partial-output contract: retain strictly valid, nonconflicting tables.

This does not relax the atomic production parser. It measures how much already
returned data survives a separately declared partial-results contract. No text,
coordinates, spans, or ragged rows are repaired, and no inference occurs here.
"""

# The retained JSON interface deliberately uses heterogeneous dictionaries.
# ruff: noqa: EM101, TRY003, SLF001, TRY004
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from bench import generalization_vision_regions as crops
from bench import pipeline_vision_transcription as adapter


def response_tables(response: dict[str, Any], viewport: list[float]) -> dict[str, Any]:
    """Validate the entire envelope, then each literal table without any repair."""
    bounds = adapter._viewport(viewport)
    # Reuse envelope admission on an empty table payload; independently admit the
    # complete original JSON below before inspecting any of its tables.
    envelope = deepcopy(response)
    choices = envelope.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise ValueError("Response must contain exactly one completion")
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("Response content is missing")
    content = message["content"]
    if len(content) > adapter.MAX_CONTENT_BYTES or len(content.encode()) > adapter.MAX_CONTENT_BYTES:
        raise ValueError("Complete response content admission exceeded")
    message["content"] = '{"answers":{"q0":{"tables":[]}}}'
    adapter.parse(envelope, viewport)  # Includes finish reason and refusal checks.
    payload = json.loads(content, object_pairs_hook=adapter._unique_pairs, parse_constant=adapter._invalid_constant)
    answers = adapter._exact(payload, {"answers"})["answers"]
    answer = adapter._exact(answers, {"q0"})["q0"]
    tables = adapter._exact(answer, {"tables"})["tables"]
    if not isinstance(tables, list) or len(tables) > adapter.MAX_TABLES:
        raise ValueError("Complete table inventory admission exceeded")
    retained: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, raw in enumerate(tables):
        try:
            table, slots, size = adapter._canonical(raw, bounds)
        except ValueError as error:
            rejected.append({"table_index": index, "reason": str(error)})
        else:
            retained.append({"table_index": index, "table": table, "slots": slots, "text_bytes": size})
    return {"retained": retained, "rejected": rejected, "declared_tables": len(tables)}


def recover(regions: list[dict[str, Any]], viewport: list[float]) -> dict[str, Any]:  # noqa: C901
    """Drop every member of an overlap conflict; never choose a preferred answer."""
    adapter._viewport(viewport)
    if not isinstance(regions, list) or len(regions) > crops.MAX_REGIONS:
        raise ValueError("Complete region inventory admission exceeded")
    retained: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, region in enumerate(regions):
        if region.get("index") != index or region.get("request_index") != index:
            raise ValueError("Region order or request identity differs")
        bounds = crops._contained(region["viewport"], viewport)
        if region.get("transcription_representation", "legacy") != "legacy":
            raise ValueError("Partial-table experiment requires original matrix representation")
        response = region.get("transcription_response")
        if response is None:
            rejected.append({"region_index": index, "reason": "no_returned_response"})
            continue
        try:
            result = response_tables(response, bounds)
        except (ValueError, TypeError, RecursionError) as error:
            rejected.append({"region_index": index, "reason": str(error)})
            continue
        retained.extend({"region_index": index, **item} for item in result["retained"])
        rejected.extend({"region_index": index, **item} for item in result["rejected"])
    conflicts: set[int] = set()
    for i, left in enumerate(retained):
        a = left["table"]["bbox"]
        for j in range(i + 1, len(retained)):
            b = retained[j]["table"]["bbox"]
            if min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1]):
                conflicts.update((i, j))
    for i in sorted(conflicts):
        item = retained[i]
        rejected.append({"region_index": item["region_index"], "table_index": item["table_index"],
                         "reason": "overlap_ownership_conflict"})
    kept = [item for i, item in enumerate(retained) if i not in conflicts]
    if (sum(item["slots"] for item in kept) > crops.MAX_PAGE_SLOTS
            or sum(item["text_bytes"] for item in kept) > adapter.MAX_TEXT_BYTES):
        raise ValueError("Aggregate partial-table admission exceeded; no size-based subset selection")
    state = {"tables": [item["table"] for item in kept], "text_provenance": adapter.PROVENANCE,
             "source_conserved": False}
    adapter.markdown(state)  # Independently validate canonical output before exposure.
    return {"state": state, "retained_table_ids": [[item["region_index"], item["table_index"]] for item in kept],
            "rejected": rejected, "contract": "explicit_partial_tables", "full_page_success": False}
