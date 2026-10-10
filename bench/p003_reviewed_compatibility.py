"""Narrow operator-reviewed administrative source compatibility, without archived execution."""

from __future__ import annotations

import ast
import hashlib
from typing import Any

PRECOUNT_SHA256 = "1e2f92afc1a284954f25cba50eca5029eca7f34fd74ae94b60a5acba4a62125d"
COUNT_SHA256 = "5a6f6ad407cda8b9b2286c3ede05a244ba352e3323616df3b29c568490edc2e5"
HISTORICAL_PAGES = 16


def _helper_ast(code: bytes) -> str:
    tree = ast.parse(code)
    tree.body = [
        node
        for node in tree.body
        if not (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {"run", "main"})
        and not (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "MAX_EXPECTED_PAGES"
        )
    ]
    return ast.dump(tree, include_attributes=False)


def reviewed_precount_helper(
    archived: bytes, current: bytes, config: dict[str, Any], records: list[dict[str, Any]]
) -> bool:
    """Allow exact e16332d pair for sixteen historical records only, after independent archive authentication.

    All called helper functions, classes, imports and prior constants must match.
    The reviewed change affects run/main corpus admission alone. Caller still
    authenticates archived bytes against an independently supplied code map.
    No archived source is executed, and no new corpus/config inherits this review.
    """
    if (
        hashlib.sha256(archived).hexdigest() != PRECOUNT_SHA256
        or hashlib.sha256(current).hexdigest() != COUNT_SHA256
        or len(records) != HISTORICAL_PAGES
        or "expected_pages" in config
    ):
        return False
    return _helper_ast(archived) == _helper_ast(current)
