"""Bounded hypothetical header structures over immutable retained literal responses."""

# ruff: noqa: ANN401, EM101, TRY003, SLF001, PLR2004, C901, PLR0912, TRY301
from __future__ import annotations

import json
import math
from copy import deepcopy
from itertools import product
from typing import Any

from bench import generalization_vision_regions as regions
from bench import pipeline_vision_transcription as strict
from bench.pipeline_frontier import _invalid_constant, _unique_pairs
from bench.silver import canonical, sha

MAX_TABLE_ALTERNATIVES = 32
MAX_PAGE_ALTERNATIVES = 256


def payload(result: dict[str, Any]) -> dict[str, Any]:
    """Require a normally finished exact original envelope; never repair JSON or truncation."""
    if not isinstance(result, dict) or not isinstance(result.get("choices"), list) or len(result["choices"]) != 1:
        raise ValueError("Exactly one original completion required")
    completion = result["choices"][0]
    if not isinstance(completion, dict) or completion.get("finish_reason") not in {"stop", "end_turn"}:
        raise ValueError("Original response did not finish normally")
    message = completion.get("message")
    if not isinstance(message, dict) or message.get("refusal") or not isinstance(message.get("content"), str):
        raise ValueError("Original response refused or lacked JSON")
    text = message["content"]
    if len(text.encode()) > strict.MAX_CONTENT_BYTES:
        raise ValueError("Original content capacity exceeded")
    value = json.loads(text, object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
    answers = strict._exact(value, {"answers"})["answers"]
    answer = strict._exact(answers, {"q0"})["q0"]
    tables = strict._exact(answer, {"tables"})["tables"]
    if not isinstance(tables, list) or len(tables) > strict.MAX_TABLES:
        raise ValueError("Original table inventory exceeded")
    return value


def response_with(result: dict[str, Any], tables: list[dict[str, Any]]) -> dict[str, Any]:
    """Create an explicitly derived hypothetical envelope; preserve original separately."""
    derived = deepcopy(result)
    derived["choices"][0]["message"]["content"] = canonical({"answers": {"q0": {"tables": tables}}}).decode()
    return derived


def partitions(total: int, count: int) -> list[tuple[int, ...]]:
    """Enumerate all bounded positive ordered column partitions, never truncate."""
    if type(total) is not int or type(count) is not int or not 1 <= count <= total:
        raise ValueError("Invalid positive header partition")
    if math.comb(total - 1, count - 1) + 2 > MAX_TABLE_ALTERNATIVES:
        raise ValueError("Complete header alternative inventory exceeds table cap")
    if count == 1:
        return [(total,)]
    return [(head, *tail) for head in range(1, total - count + 2) for tail in partitions(total - head, count - 1)]


def table_alternatives(table: Any, viewport: list[float]) -> list[dict[str, Any]]:
    """Alter only a single short row0, preserving every original whole string and bbox."""
    try:
        strict._canonical(table, strict._viewport(viewport))
    except ValueError:
        pass
    else:
        return [{"table": deepcopy(table), "mechanism": "strict_original_unchanged", "header_anchors": None}]
    strict._exact(table, {"bbox", "matrix", "mergedspans"})
    matrix = table["matrix"]
    if (
        not isinstance(matrix, list)
        or not 2 <= len(matrix) <= strict.MAX_SLOTS
        or any(not isinstance(row, list) or not row or any(not isinstance(cell, str) for cell in row) for row in matrix)
        or table["mergedspans"] != []
    ):
        raise ValueError("Only one short row0 and explicit empty original merges are admitted")
    columns, headers = len(matrix[1]), matrix[0]
    if not 0 < len(headers) < columns or any(len(row) != columns for row in matrix[1:]):
        raise ValueError("Body must be rectangular and only row0 shorter than its width")
    if len(matrix) * columns > strict.MAX_SLOTS:
        raise ValueError("Complete proposed slot capacity exceeded")
    alternatives = []
    for widths in partitions(columns, len(headers)):
        row, spans, anchors = [""] * columns, [], []
        offset = 0
        for index, width in enumerate(widths):
            row[offset] = headers[index]
            anchors.append(offset)
            if width > 1:
                spans.append([0, offset, 1, width])
            offset += width
        alternatives.append(
            {
                "table": {**deepcopy(table), "matrix": [row, *deepcopy(matrix[1:])], "mergedspans": spans},
                "mechanism": "hypothesized_header_partitions",
                "header_anchors": anchors,
            }
        )
    for offset, mechanism in ((0, "hypothesized_left_padding"), (columns - len(headers), "hypothesized_right_padding")):
        row = [""] * columns
        row[offset : offset + len(headers)] = headers
        alternatives.append(
            {
                "table": {**deepcopy(table), "matrix": [row, *deepcopy(matrix[1:])]},
                "mechanism": mechanism,
                "header_anchors": list(range(offset, offset + len(headers))),
            }
        )
    unique = {}
    for item in alternatives:
        candidate = item["table"]
        strict._canonical(candidate, strict._viewport(viewport))
        if candidate["bbox"] != table["bbox"] or candidate["matrix"][1:] != matrix[1:]:
            raise ValueError("Hypothesis changed original body or geometry")
        if [candidate["matrix"][0][anchor] for anchor in item["header_anchors"]] != headers:
            raise ValueError("Original whole header strings changed")
        key = sha(canonical(candidate))
        unique.setdefault(
            key,
            {
                **item,
                "id": key,
                "header_literal_inventory": deepcopy(headers),
                "inferred_header_structure": True,
                "source_conserved": False,
            },
        )
    if len(unique) > MAX_TABLE_ALTERNATIVES:
        raise ValueError("Complete table proposal inventory exceeds cap")
    return list(unique.values())


def freeze_page(page: dict[str, Any], *, input_refusal: str | None = None) -> dict[str, Any]:
    """Freeze complete page alternatives or explicitly refuse any other malformed content."""
    original = deepcopy(page)
    base = {
        "version": 1,
        "id": page["id"],
        "original_page_status": page["status"],
        "original_page_sha256": sha(canonical(original)),
        "original_page": original,
        "max_table_alternatives": MAX_TABLE_ALTERNATIVES,
        "max_page_alternatives": MAX_PAGE_ALTERNATIVES,
        "source_conserved": False,
        "references_read": False,
        "hosted_calls": 0,
        "provenance": "retained model literals; hypothetical header structure; no original parser repair",
    }
    if input_refusal is not None:
        return {
            **base,
            "status": "refused",
            "reason": input_refusal,
            "error_type": "UnauthenticatedAttempt",
            "complete_page_alternatives": [],
            "primary_predicted_tables": [],
        }
    try:
        crop_plans, menus = [], []
        for crop in page["transcription_regions"]:
            if crop.get("transcription_representation", "legacy") != "legacy":
                raise ValueError("Only original legacy literal matrix envelopes admitted")
            value = payload(crop["transcription_response"])
            table_menus = [table_alternatives(table, crop["viewport"]) for table in value["answers"]["q0"]["tables"]]
            count = math.prod(len(menu) for menu in table_menus)
            if count > MAX_PAGE_ALTERNATIVES:
                raise ValueError("Complete crop alternative inventory exceeds page cap")
            options = []
            for combination in product(*table_menus):
                tables = [item["table"] for item in combination]
                response = response_with(crop["transcription_response"], tables)
                state = strict.parse(response, crop["viewport"])
                options.append(
                    {
                        "derived_response": response,
                        "state": state,
                        "table_choices": [item.get("id", "strict_original") for item in combination],
                    }
                )
            crop_plans.append({"index": crop["index"], "viewport": crop["viewport"], "table_menus": table_menus})
            menus.append(options)
        count = math.prod(len(menu) for menu in menus)
        if count > MAX_PAGE_ALTERNATIVES:
            raise ValueError("Complete page alternative inventory exceeds cap")
        alternatives = {}
        for choices in product(*menus):
            staged = deepcopy(page["transcription_regions"])
            for crop, choice in zip(staged, choices, strict=True):
                crop.update(
                    status="ok", transcription_response=choice["derived_response"], tables=choice["state"]["tables"]
                )
            state = regions.compose(staged, page["viewport"])
            key = sha(canonical(state))
            alternatives.setdefault(
                key, {"id": key, "state": state, "crop_table_choices": [c["table_choices"] for c in choices]}
            )
        changed = any(
            item["mechanism"] != "strict_original_unchanged"
            for crop in crop_plans
            for menu in crop["table_menus"]
            for item in menu
        )
        if not changed and page["status"] != "ok":
            raise ValueError("Original failed page has no admitted short-header defect; no unrelated rescue")
        return {
            **base,
            "status": "header_proposals" if changed else "unchanged_valid",
            "crop_plans": crop_plans,
            "complete_page_alternatives": list(alternatives.values()),
        }
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, RecursionError) as error:
        return {
            **base,
            "status": "refused",
            "reason": str(error),
            "error_type": type(error).__name__,
            "complete_page_alternatives": [],
            "primary_predicted_tables": [],
        }
