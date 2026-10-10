"""Explicit schema-complexity ablation, retaining unchanged local output admission.

Provider grammars may reject large array/string bounds before inference. The
simple treatment removes numeric and collection bounds from the wire schema,
while retaining types, required fields, closed objects and the exact response
shape. It never changes the parser or accepts a previously invalid output.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

BOUND_KEYS = frozenset({"minItems", "maxItems", "minLength", "maxLength", "minimum", "maximum"})


def simplify(body: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    """Copy one chat request and remove only declared grammar bounds from its schema."""
    result = deepcopy(body)
    schema = result["response_format"]["json_schema"]["schema"]
    removed: dict[str, int] = {}

    def visit(node: Any) -> None:  # noqa: ANN401 - recursive JSON schema nodes.
        if isinstance(node, list):
            for item in node:
                visit(item)
        elif isinstance(node, dict):
            for key in tuple(node):
                if key in BOUND_KEYS:
                    del node[key]
                    removed[key] = removed.get(key, 0) + 1
                else:
                    visit(node[key])

    visit(schema)
    return result, removed
