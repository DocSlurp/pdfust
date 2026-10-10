"""Offline partial evidence from strict isolated tables in complete vision replies."""

# Heterogeneous response dictionaries retain strict adapter provenance.
# ruff: noqa: EM101, TRY003, TRY004, TRY301, SLF001, C901, PLR0912
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from bench import pipeline_vision_transcription as adapter
from bench.pipeline_frontier import _invalid_constant, _unique_pairs

MAX_RESPONSES = 32
MAX_RAW_TABLES = MAX_RESPONSES * adapter.MAX_TABLES
MAX_RETAINED_SLOTS = 4096
SPEC = {
    "version": 1,
    "eligibility": "Exact outer JSON schema, one normal stop/end_turn completion, no refusal; complete bounded content",
    "table_validation": "Each original table independently parsed by unchanged strict vision adapter",
    "geometry": "Original crop viewport to display mapping; viewport wholly within page; no clipping or unit inference",
    "conflicts": "Page-global positive-area overlap graph; quarantine all vertices of every nontrivial component",
    "retention": "Only isolated valid tables in response/table order; no text, shape or geometry repair",
    "limits": {
        "responses": MAX_RESPONSES,
        "raw_tables": MAX_RAW_TABLES,
        "retained_tables": adapter.MAX_TABLES,
        "retained_slots": MAX_RETAINED_SLOTS,
        "retained_text_bytes": adapter.MAX_TEXT_BYTES,
    },
    "status": "Always partial, never complete-page success or source-conserved",
    "accounting": "Offline secondary evidence only; original errors, requests, charges and elapsed time unchanged",
}


def _tables(response: dict[str, Any], viewport: list[float]) -> list[Any]:
    """Use empty-inventory strict parse to attest the unchanged response envelope."""
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise ValueError("Invalid completion inventory")
    message = choices[0].get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise ValueError("Missing complete JSON content")
    content = message["content"]
    if len(content) > adapter.MAX_CONTENT_BYTES or len(content.encode("utf-8")) > adapter.MAX_CONTENT_BYTES:
        raise ValueError("Response content admission exceeded")
    payload = json.loads(content, object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
    answers = adapter._exact(payload, {"answers"})["answers"]
    answer = adapter._exact(answers, {"q0"})["q0"]
    tables = adapter._exact(answer, {"tables"})["tables"]
    if not isinstance(tables, list) or len(tables) > adapter.MAX_TABLES:
        raise ValueError("Raw table admission exceeded")
    empty = deepcopy(response)
    empty["choices"][0]["message"]["content"] = '{"answers":{"q0":{"tables":[]}}}'
    adapter.parse(empty, viewport)
    return tables


def salvage(responses: list[dict[str, Any]], viewport: list[float]) -> dict[str, Any]:
    """Retain only strict isolated tables; never expose a successful complete page."""
    page = adapter._viewport(viewport)
    if not isinstance(responses, list) or len(responses) > MAX_RESPONSES:
        raise ValueError("Complete response inventory admission exceeded")
    candidates, origins, quarantined = [], [], []
    raw_count = 0
    for ri, descriptor in enumerate(responses):
        try:
            bounds = adapter._viewport(descriptor["viewport"])
            if any(bounds[i] < page[i] for i in (0, 1)) or any(bounds[i] > page[i] for i in (2, 3)):
                raise ValueError("Crop viewport exceeds page")
            response = descriptor["response"]
            if not isinstance(response, dict):
                raise ValueError("Missing retained complete response")
            raw_tables = _tables(response, list(bounds))
        except (ValueError, KeyError, TypeError, UnicodeError, RecursionError) as error:
            quarantined.append({"response_index": ri, "code": "response_ineligible", "detail": str(error)[:300]})
            continue
        raw_count += len(raw_tables)
        if raw_count > MAX_RAW_TABLES:
            raise ValueError("Complete raw table inventory admission exceeded")
        for ti, raw_table in enumerate(raw_tables):
            origin = {"response_index": ri, "table_index": ti}
            try:
                single = deepcopy(response)
                single["choices"][0]["message"]["content"] = json.dumps(
                    {"answers": {"q0": {"tables": [raw_table]}}}, ensure_ascii=False, allow_nan=False
                )
                table = adapter.parse(single, list(bounds))["tables"][0]
                candidates.append(table)
                origins.append(origin)
            except (ValueError, KeyError, TypeError, UnicodeError, RecursionError) as error:
                quarantined.append({**origin, "code": "invalid_table", "detail": str(error)[:300]})
    parents = list(range(len(candidates)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for i, table in enumerate(candidates):
        a = table["bbox"]
        for j in range(i):
            b = candidates[j]["bbox"]
            if min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1]):
                first, second = find(i), find(j)
                parents[max(first, second)] = min(first, second)
    components: dict[int, list[int]] = {}
    for i in range(len(candidates)):
        components.setdefault(find(i), []).append(i)
    conflicts = [members for members in components.values() if len(members) > 1]
    excluded = {i for members in conflicts for i in members}
    quarantined.extend({**origins[i], "code": "overlap_component", "component": find(i)} for i in sorted(excluded))
    kept = [i for i in range(len(candidates)) if i not in excluded]
    tables = [candidates[i] for i in kept]
    if len(tables) > adapter.MAX_TABLES or sum(t["row_count"] * t["col_count"] for t in tables) > MAX_RETAINED_SLOTS:
        quarantined.extend({**origins[i], "code": "aggregate_admission"} for i in kept)
        kept, tables = [], []
    parsed = {"tables": tables, "text_provenance": adapter.PROVENANCE, "source_conserved": False}
    try:
        markup = adapter.markdown(parsed)
    except ValueError as error:
        quarantined.extend({**origins[i], "code": "aggregate_admission", "detail": str(error)[:300]} for i in kept)
        kept, tables, markup = [], [], ""
    return {
        "status": "partial",
        "complete_page": False,
        "source_conserved": False,
        "text_provenance": adapter.PROVENANCE,
        "viewport": list(page),
        "spec": deepcopy(SPEC),
        "tables": tables,
        "table_origins": [origins[i] for i in kept],
        "markdown": markup,
        "quarantined": quarantined,
        "raw_table_count": raw_count,
        "validated_table_count": len(candidates),
        "overlap_components": [[origins[i] for i in members] for members in conflicts],
        "response_count": len(responses),
        "coverage": "partial_unverified",
    }
