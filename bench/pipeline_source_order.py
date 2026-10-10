"""Render-only original source order, independent of regional proposal ordering."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from bench.pipeline_regions import MAX_PAGE_WORDS


def render_source(snapshot: dict[str, Any], region: dict[str, Any]) -> dict[str, Any]:
    """Preserve original word dictionaries after proving identical regional evidence."""
    original = snapshot["words"]
    selected = region["source"]["words"]
    identifiers = region["source_ids"]
    if not isinstance(original, list) or len(original) > MAX_PAGE_WORDS:
        message = "Original render source exceeds complete page word admission"
        raise ValueError(message)
    lookup = {word["id"]: word for word in original}
    regional = {word["id"]: word for word in selected}
    if (
        len(lookup) != len(original) or len(regional) != len(selected)
        or len(set(identifiers)) != len(identifiers) or set(identifiers) != set(regional)
        or not set(regional) <= set(lookup)
    ):
        message = "Render source IDs differ from the original regional partition"
        raise ValueError(message)
    if any(
        regional[ident][key] != lookup[ident][key] for ident in identifiers for key in ("id", "text", "bbox")
    ):
        message = "Render source literal text or display geometry changed"
        raise ValueError(message)
    if region["source"]["page_size"] != snapshot["page_size"]:
        message = "Render source page geometry differs from original snapshot"
        raise ValueError(message)
    result = deepcopy(region["source"])
    result["words"] = [deepcopy(word) for word in original if word["id"] in regional]
    return result
