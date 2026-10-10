"""Opt-in derived row context, without duplicating or changing source words."""

# Bounded experiment JSON and deliberate complete-packet refusal.
# ruff: noqa: EM101, TRY003
from __future__ import annotations

import json
from typing import Any

from bench.pipeline_row_evidence import SPEC, build

MAX_CONTEXT_BYTES = 128_000


def context(source: dict[str, Any], *, ordinal: bool = False) -> str:
    """Describe every observed row; never classify, trim, merge or rewrite it."""
    packet = build(source)
    words = packet.pop("words")
    packet.pop("word_fields")
    if ordinal:
        positions = {word[0]: index for index, word in enumerate(words)}
        for row in packet["rows"]:
            row["word_indexes"] = [positions[identifier] for identifier in row.pop("source_ids")]
    packet["specification"] = SPEC
    packet["source_reference"] = (
        "Zero-based positions in the complete supplied words array" if ordinal else "Exact supplied source IDs"
    )
    encoded = json.dumps(packet, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode()) > MAX_CONTEXT_BYTES:
        raise ValueError("Complete derived row context exceeds byte admission; no truncation")
    return (
        "Additional source-derived observations follow. These geometric bands are not logical rows or a table "
        "proposal. The em unit is only median word-box height. Compare adjacent baselines, signed gaps, tracks "
        "and lexical/numeric roles with the original words and pixels. Wrapped cells may cross bands; prose "
        "may share tracks. These features neither establish a table nor justify changing literal source text.\n"
        + encoded
    )
