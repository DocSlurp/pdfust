"""Versioned schema-granularity acceptance alongside unchanged exact-reference scores."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import re
import unicodedata
from typing import Any

from bench.generalization_scoring import _cells

VERSION = "unheaded-adjacent-column-equivalence-v1"
MAX_COLUMNS = 32
MAX_CHARACTERS = 1_000_000


def tokens(value: str) -> tuple[str, ...]:
    """Preserve ordered words, number runs and punctuation, allowing inter-token spacing."""
    return tuple(re.findall(r"[^\W\d_]+|\d+|[^\w\s]|_", unicodedata.normalize("NFC", value)))


def matrix(table: dict[str, Any]) -> list[list[str]] | None:
    """Validate structure; decline merged-cell equivalence rather than flattening spans."""
    anchors = _cells(table)
    if any(key[2:] != (1, 1) for key in anchors):
        return None
    if table["col_count"] > MAX_COLUMNS:
        return None
    values = table["values"]
    if sum(len(value) for row in values for value in row) > MAX_CHARACTERS:
        return None
    return values


def partition(coarse: list[list[str]], fine: list[list[str]]) -> list[list[int]] | None:
    """Find one uniform contiguous mapping, without row permutations or named-header collapse."""
    rows, n, m = len(coarse), len(coarse[0]), len(fine[0])
    if rows != len(fine) or n > m:
        return None
    coarse_tokens = [[tokens(value) for value in row] for row in coarse]
    fine_tokens = [[tokens(value) for value in row] for row in fine]
    if n < m and any(not any(fine_tokens[r][c] for r in range(rows)) for c in range(m)):
        return None  # An entirely blank extra column is padding, not an evidenced field.
    paths: dict[int, list[list[int]]] = {0: []}
    for col in range(n):
        following: dict[int, list[list[int]]] = {}
        for start, groups in sorted(paths.items()):
            for end in range(start + 1, m - (n - col - 1) + 1):
                if end - start > 1 and sum(bool(fine_tokens[0][j]) for j in range(start, end)) > 1:
                    continue  # Distinct named headers establish a meaningful boundary.
                # Join literals first: never erase a separator inside a word or number run.
                if all(coarse_tokens[r][col] == tokens(" ".join(fine[r][start:end])) for r in range(rows)):
                    following.setdefault(end, [*groups, list(range(start, end))])
        paths = following
    return paths.get(m)


def compare(reference: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    """Accept exact tokens or an unheaded adjacent-column split with every row intact."""
    a, b = matrix(reference), matrix(prediction)
    result: dict[str, Any] = {
        "version": VERSION,
        "eligible": a is not None and b is not None,
        "reference_rows": reference["row_count"],
        "prediction_rows": prediction["row_count"],
        "reference_columns": reference["col_count"],
        "prediction_columns": prediction["col_count"],
        "same_position_row_token_matches": 0,
        "schema_equivalent": False,
        "scope": "Content and header-compatible granularity; physical boundary ambiguity needs source review",
    }
    if a is None or b is None:
        return {**result, "reason": "merged_cells_or_bounded_admission_not_supported"}
    result["same_position_row_token_matches"] = sum(
        tokens(" ".join(x)) == tokens(" ".join(y)) for x, y in zip(a, b, strict=False)
    )
    if len(a) != len(b):
        return {**result, "reason": "different_row_counts"}
    reference_is_coarse = len(a[0]) <= len(b[0])
    groups = partition(a, b) if reference_is_coarse else partition(b, a)
    if groups is None:
        return {**result, "reason": "no_uniform_header_compatible_literal_partition"}
    return {
        **result,
        "schema_equivalent": True,
        "fine_side": "prediction" if reference_is_coarse else "reference",
        "fine_column_groups": groups,
        "reason": "same_columns_ordered_tokens" if len(a[0]) == len(b[0]) else "unheaded_column_granularity",
    }


def summarize(
    targets: list[dict[str, Any]], predictions: list[dict[str, Any]], strict: dict[str, Any]
) -> dict[str, Any]:
    """Reuse every existing table match; preserve errors, unmatched tables and full denominators."""
    refs = {p["id"]: p for p in targets}
    outputs = {p["id"]: p for p in predictions}
    if len(refs) != len(targets) or len(outputs) != len(predictions) or set(refs) != set(outputs):
        raise ValueError("Complete unique matched page inventory required")
    if {p["id"] for p in strict["pages"]} != set(refs):
        raise ValueError("Original strict page inventory differs")
    pages = []
    for score in strict["pages"]:
        target, output = refs[score["id"]], outputs[score["id"]]
        pairs = []
        if not score["error"] and score["structural_scored"]:
            for match in score["matches"]:
                detail = compare(target["tables"][match["target"]], output["tables"][match["prediction"]])
                pairs.append({"target": match["target"], "prediction": match["prediction"], **detail})
        pages.append(
            {
                "id": score["id"],
                "error": score["error"],
                "reference_tables": score.get("expected_tables", 0),
                "missing_tables": score.get("missing_tables", 0),
                "extra_tables": score.get("false_positive_tables", 0),
                "pairs": pairs,
                "schema_equivalent_tables": sum(p["schema_equivalent"] for p in pairs),
                "different_column_equivalent_tables": sum(
                    p["schema_equivalent"] and p["reference_columns"] != p["prediction_columns"] for p in pairs
                ),
                "row_token_matches": sum(p["same_position_row_token_matches"] for p in pairs),
            }
        )
    return {
        "version": VERSION,
        "primary_strict_scores_changed": False,
        "physical_boundary_ambiguity_automatically_established": False,
        "pages": pages,
        "totals": {
            "pages": len(pages),
            "reference_tables": sum(p["reference_tables"] for p in pages),
            "schema_equivalent_tables": sum(p["schema_equivalent_tables"] for p in pages),
            "different_column_equivalent_tables": sum(p["different_column_equivalent_tables"] for p in pages),
            "row_token_matches": sum(p["row_token_matches"] for p in pages),
            "error_pages": sum(bool(p["error"]) for p in pages),
            "missing_tables": sum(p["missing_tables"] for p in pages),
            "extra_tables": sum(p["extra_tables"] for p in pages),
        },
    }
