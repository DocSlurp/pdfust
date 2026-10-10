"""Offline posthoc row-join oracle, restricted to frozen source-owned boundaries."""

from __future__ import annotations

from typing import Any

from bench.decision_p003_boundaries import build
from bench.generalization_scoring import _cells
from bench.pipeline_repair import _sources, _table


def legal_groups(source: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Freeze all legal length1–3 row groups without references or scoring."""
    menu = build(source, state)
    lookup = _sources(source)
    tables = []
    for table_info in menu["tables"]:
        ti = table_info["table"]
        table = state["tables"][ti]
        count, cols = table["row_count"], table["col_count"]
        allowed = {b["after_row"]: b["join_available"] for b in menu["boundaries"] if b["table"] == ti}
        rows = [[cell["source_ids"] for cell in table["cells"][r * cols : (r + 1) * cols]] for r in range(count)]
        groups = []
        for start in range(count):
            for end in range(start + 1, min(count, start + 3) + 1):
                if all(allowed[r] for r in range(start, end - 1)):
                    ids = [[ident for r in range(start, end) for ident in rows[r][c]] for c in range(cols)]
                    groups.append(
                        {"start": start, "end": end, "source_ids": ids, "values": _table([ids], lookup)["values"][0]}
                    )
        tables.append({"table": ti, "physical_rows": count, "columns": cols, "groups": groups})
    return {"menu": menu, "tables": tables, "generation_scope": "Source-only; references absent"}


def best_partition(graph: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Exact anchor-score dynamic program over the already frozen legal group graph."""
    target_cells = _cells(target)
    rows = graph["physical_rows"]
    best: dict[tuple[int, int], tuple[int, list[dict[str, Any]]]] = {(0, 0): (0, [])}
    for start in range(rows):
        for logical in range(start + 1):
            previous = best.get((start, logical))
            if previous is None:
                continue
            for group in graph["groups"]:
                if group["start"] != start:
                    continue
                observed = _cells({"row_count": 1, "col_count": graph["columns"], "values": [group["values"]]})
                gain = sum(target_cells.get((logical, c, 1, 1)) == text for (_, c, _, _), text in observed.items())
                key = (group["end"], logical + 1)
                candidate = (previous[0] + gain, [*previous[1], group])
                if key not in best or candidate[0] > best[key][0]:
                    best[key] = candidate
    options = [(value, logical) for (end, logical), value in best.items() if end == rows and logical >= min(2, rows)]
    (score, partition), logical = max(options, key=lambda item: (item[0][0], item[1]))
    return {
        "strict_anchor_score": score,
        "partition": [[g["start"], g["end"]] for g in partition],
        "logical_rows": logical,
        "best_score_by_logical_rows": {str(n): value[0] for value, n in options},
        "values": [g["values"] for g in partition],
        "exact_scope": "Restricted legal groups, fixed target pairing, reconstructed-cell anchor score",
    }
