"""Bounded exact posthoc oracle for independently chosen source-word cohorts.

References are supplied only after candidate/cohort generation has been frozen.
This helper does not create candidates or call a provider.
"""

# ruff: noqa: EM101, TRY003, C901
from __future__ import annotations

import itertools
import math
from copy import deepcopy
from typing import Any

from bench.generalization_scoring import _cells, normalize_text
from bench.p003_source_choices import apply_cohorts, owners

MAX_ENTRIES = 100_000


def maximize(domains: list[int], factors: list[dict[str, Any]]) -> tuple[int, list[int], int]:
    """Exact max-sum variable elimination with an explicit intermediate-state cap."""
    factors = deepcopy(factors)
    pending, trace, peak = set(range(len(domains))), [], 0
    while pending:

        def neighbors(variable: int, current: list[dict[str, Any]] = factors) -> list[int]:
            return sorted(
                {v for factor in current if variable in factor["scope"] for v in factor["scope"]} - {variable}
            )

        variable = min(pending, key=lambda v: (math.prod(domains[n] for n in neighbors(v)), v))
        selected = [f for f in factors if variable in f["scope"]]
        scope = neighbors(variable)
        count = math.prod(domains[v] for v in scope) * domains[variable]
        if count > MAX_ENTRIES:
            raise ValueError("Exact oracle intermediate exceeds bounded admission")
        peak = max(peak, count)
        scores, choices = {}, {}
        for assignment in itertools.product(*(range(domains[v]) for v in scope)):
            lookup = dict(zip(scope, assignment, strict=True))
            values = []
            for value in range(domains[variable]):
                lookup[variable] = value
                values.append(sum(f["scores"][tuple(lookup[v] for v in f["scope"])] for f in selected))
            winner = max(range(domains[variable]), key=lambda value: values[value])
            scores[assignment], choices[assignment] = values[winner], winner
        trace.append((variable, scope, choices))
        factors = [f for f in factors if variable not in f["scope"]]
        factors.append({"scope": tuple(scope), "scores": scores})
        pending.remove(variable)
    result = [0] * len(domains)
    for variable, scope, choices in reversed(trace):
        result[variable] = choices[tuple(result[v] for v in scope)]
    return sum(f["scores"][()] for f in factors), result, peak


def select(
    source: dict[str, Any], pool: dict[str, Any], menu: dict[str, Any], references_by_table: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    """Exact restricted fixed-pairing anchor oracle; return a fully replayable selection."""
    candidates = pool["candidates"]
    fallback_sha = next(p["state_sha256"] for p in pool["policies"] if p["policy"] == "source_id_fallback")
    fallback = next(c for c in candidates if c["state_sha256"] == fallback_sha)
    candidate_owners = {
        c["label"]: owners(source, c["state"])
        for c in sorted(candidates, key=lambda c: (c["label"] != fallback["label"], c["label"]))
    }
    lookup = {w["id"]: w for w in source["words"]}
    order = {w["id"]: i for i, w in enumerate(source["words"])}
    items, labels, alternatives = menu["cohorts"], [], []
    # Domains deduplicate exact ownership alternatives within each physical line.
    for item in items:
        unique: dict[tuple[Any, ...], str] = {}
        for label, placement in candidate_owners.items():
            vector = tuple(
                None if placement[ident] is None else tuple(placement[ident]) for ident in item["source_ids"]
            )
            unique.setdefault(vector, label)
        labels.append(list(unique.values()))
        alternatives.append(
            [{ident: candidate_owners[label][ident] for ident in item["source_ids"]} for label in labels[-1]]
        )
    changed_ids = set(menu["changed_source_ids"])
    factors = []
    fixed_score = 0
    for ti, reference in references_by_table.items():
        table = fallback["state"]["tables"][ti]
        baseline_cells, target = _cells(table), _cells(reference)
        for key, expected in target.items():
            r, c, rs, cs = key
            if key not in baseline_cells:
                continue
            slot = (ti, r, c)
            if (rs, cs) != (1, 1):
                fixed_score += baseline_cells[key] == expected
                continue
            original_ids = table["cells"][r * table["col_count"] + c]["source_ids"]
            fixed_ids = [ident for ident in original_ids if ident not in changed_ids]
            scope = [
                index
                for index, domain in enumerate(alternatives)
                if any(
                    any(owner is not None and tuple(owner) == slot for owner in alternative.values())
                    for alternative in domain
                )
            ]
            count = math.prod(len(labels[v]) for v in scope)
            if count > MAX_ENTRIES:
                raise ValueError("Exact oracle cell factor exceeds bounded admission")
            scores = {}
            for assignment in itertools.product(*(range(len(labels[v])) for v in scope)):
                retained = [*fixed_ids]
                for variable, choice in zip(scope, assignment, strict=True):
                    retained.extend(
                        ident
                        for ident, owner in alternatives[variable][choice].items()
                        if owner is not None and tuple(owner) == slot
                    )
                # The decoder preserves untouched source order, rebuilding only
                # cells whose membership changes from the authenticated fallback.
                ids = original_ids if set(retained) == set(original_ids) else sorted(retained, key=order.__getitem__)
                scores[assignment] = int(normalize_text(" ".join(lookup[ident]["text"] for ident in ids)) == expected)
            if scope:
                factors.append({"scope": tuple(scope), "scores": scores})
            else:
                fixed_score += scores[()]
    score, values, peak = maximize([len(v) for v in labels], factors)
    choices = {item["id"]: labels[index][values[index]] for index, item in enumerate(items)}
    state = apply_cohorts(source, pool, menu, choices, default=fallback["label"])
    replayed = sum(
        target.get(key) == value
        for ti, reference in references_by_table.items()
        for target in [_cells(reference)]
        for key, value in _cells(state["tables"][ti]).items()
    )
    if replayed != score + fixed_score:
        raise ValueError("Exact oracle factor score does not reproduce actual decoder")
    return {
        "state": state,
        "choices": choices,
        "strict_anchor_score": replayed,
        "exact": True,
        "scope": "Frozen disjoint-cohort language, fixed baseline table pairing",
        "largest_elimination_entries": peak,
        "factor_count": len(factors),
        "cohort_count": len(items),
        "domain_sizes": [len(v) for v in labels],
    }
