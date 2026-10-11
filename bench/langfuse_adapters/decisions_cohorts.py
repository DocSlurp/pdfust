"""P001-style page admission decisions retained under ``decisions/``.

Covered evaluations (each directory has ``evaluation.json`` with a ``cohorts``
mapping of per-page ``rows`` and per-kind ``slices``, plus
``hosted-results.json``):

- ``anthropic55-baseline-v1/matched-medium`` (A055 matched chat baselines),
- ``extent-prompt-transfer-v1/E00*`` (T006 extent prompt transfer),
- ``ocr-semantic-combo-v1/P00*`` (A005 OCR + semantic prompt combination),
- ``prompt-sweep-v1/<cohort>/<family>/<prompt>`` (P001 prompt sweep; the
  ``fresh`` and ``neutral`` cohorts are diagnostic only, see
  ``bench/results/prompt-tuning.md``).

Pages are items (expected = authored page kind); each prompt/model cohort is a
run. Row scores are the retained page scores (``exact_page``, ``exact_cells``,
``exact_spans``, ``false_positive_page``, owned value/word counts, source
conservation). Ambiguous pages keep ``scores=None`` in the retained evaluation
and stay as unscored rows. Run scores are the retained per-kind slice counts
(``<kind>_<metric>``) plus exact-page rates; slice counts are recomputed from
rows and any difference is recorded in ``metadata["retained_mismatch"]``.
``candidate_ceiling_rows`` (the frozen candidate oracle) become one extra run
per experiment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, digest, guard, read_json
from bench.langfuse_adapters.decisions_common import (
    catalog_prices,
    cost_fields,
    cost_summary,
    flag,
    mismatches,
    relative,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

NAME = "decisions_cohorts"

FAMILIES = ("anthropic55-baseline-v1", "extent-prompt-transfer-v1", "ocr-semantic-combo-v1", "prompt-sweep-v1")
PAGE_SCORES = ("exact_page", "exact_cells", "exact_spans", "false_positive_page", "owned_values", "owned_words")
RECOUNT = ("exact_page", "exact_cells", "exact_spans", "false_positive_page", "owned_values", "owned_words")
DIAGNOSTIC = {"fresh": "answer-cue quarantine; audit only", "neutral": "ambiguous prose labels; diagnostic only"}


def _calls(directory: Path) -> dict[tuple[str, str], dict[str, Any]]:
    path = directory / "hosted-results.json"
    found: dict[tuple[str, str], dict[str, Any]] = {}
    if not path.exists():
        return found
    for call in read_json(path).get("calls", []):
        key = (call.get("id", ""), call.get("model", ""))
        if key not in found or (call.get("status") == "ok" and found[key].get("status") != "ok"):
            found[key] = call
    return found


def _model(cohort: str, models: list[str]) -> str:
    return next((model for model in sorted(models, key=len, reverse=True) if model in cohort), cohort)


def _page_row(root: Path, row: Mapping[str, Any], call: Mapping[str, Any] | None, model: str) -> Row:
    page_scores = row.get("scores") or {}
    scores = {name: flag(page_scores.get(name)) for name in PAGE_SCORES if page_scores.get(name) is not None}
    for name in ("candidate_ceiling_exact", "accepted", "accepted_wrong_table", "text_group_exact"):
        if row.get(name) is not None and page_scores:
            scores[name] = flag(row[name])
    conservation = row.get("source_conservation", row.get("conservation"))
    if conservation is not None:
        scores["source_conservation"] = flag(conservation)
    answer = (call or {}).get("answer") or {}
    status = (call or {}).get("status") or ("ok" if page_scores else "unscored")
    if not page_scores:
        status = row.get("truth_status") or ("unscored" if call is None or call.get("status") == "ok" else status)
    accounting = (
        cost_fields(call["entry"], call.get("usage"), catalog_prices(root).get(model))
        if call and call.get("entry")
        else {}
    )
    return Row(
        item_key=row["id"],
        output={
            "selection": row.get("selection"),
            "probabilities": answer.get("probabilities"),
            "owned_source_ids": row.get("owned_source_ids"),
            "unresolved_source_ids": row.get("unresolved_source_ids"),
        },
        scores=scores,
        metadata={
            "status": status,
            "kind": row.get("kind"),
            "call_status": (call or {}).get("status"),
            "route": (call or {}).get("route"),
            **accounting,
        },
    )


def _slice_scores(slices: Mapping[str, Mapping[str, Any]]) -> dict[str, float | None]:
    scores: dict[str, float | None] = {}
    for kind, values in slices.items():
        for metric, value in values.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                scores[f"{kind}_{metric}"] = value
        pages = values.get("scored_pages", values.get("pages"))
        if pages:
            scores[f"{kind}_exact_page_rate"] = values.get("exact_page", 0) / pages
    return scores


def _recount(slices: Mapping[str, Mapping[str, Any]], rows: list[Row]) -> list[str]:
    problems: list[str] = []
    for kind, values in slices.items():
        members = [row for row in rows if row.metadata.get("kind") == kind]
        recount = {name: sum(row.scores.get(name) or 0 for row in members) for name in RECOUNT if name in values}
        problems.extend(f"{kind}/{item}" for item in mismatches({k: values[k] for k in recount}, recount))
    return problems


def _ceiling_runs(root: Path, ceiling: list[dict[str, Any]], label: str) -> list[Run]:
    """Return one candidate-oracle run per retained ceiling variant (no model call)."""
    variants: dict[str, list[dict[str, Any]]] = {}
    for record in ceiling:
        variants.setdefault(str(record.get("variant", "default")), []).append(record)
    runs = []
    for variant, members in variants.items():
        rows = [_page_row(root, row, None, "candidate-oracle") for row in members]
        for row in rows:
            row.metadata["status"] = "oracle"
        runs.append(
            Run(
                name=f"{label}candidate-ceiling/{variant}",
                description=f"Frozen candidate-oracle ceiling ({variant}): best retained candidate per page; no call.",
                rows=rows,
                scores={
                    name: sum(row.scores.get(name) or 0 for row in rows)
                    for name in ("exact_page", "exact_cells", "false_positive_page", "owned_values", "text_group_exact")
                },
                metadata={"model": "candidate-oracle", "variant": variant, "ceiling_sha256": digest(members, 64)},
            )
        )
    return runs


def _experiment_runs(root: Path, directory: Path, label: str) -> tuple[list[Run], dict[str, Item]]:
    evaluation = read_json(directory / "evaluation.json")
    calls = _calls(directory)
    models = sorted({model for _, model in calls})
    runs: list[Run] = []
    items: dict[str, Item] = {}
    for cohort, entry in evaluation.get("cohorts", {}).items():
        model = _model(cohort, models)
        rows = [_page_row(root, row, calls.get((row["id"], model)), model) for row in entry.get("rows", [])]
        for row in entry.get("rows", []):
            items.setdefault(
                row["id"],
                Item(
                    key=row["id"],
                    input={"page_id": row["id"], "source_id": row.get("source_id")},
                    expected={"kind": row.get("kind")},
                    metadata={"kind": row.get("kind")},
                ),
            )
        slices = entry.get("slices", {})
        problems = _recount(slices, rows)
        runs.append(
            Run(
                name=f"{label}/{cohort}",
                description=f"{label}: {cohort}; page admission with exact cell/span recovery by authored page kind.",
                rows=rows,
                scores=_slice_scores(slices),
                metadata={
                    "experiment": label,
                    "model": model,
                    "cohort": cohort,
                    "pages": entry.get("pages"),
                    "diagnostic_only": entry.get("diagnostic_only"),
                    "native_zero_call_pages": entry.get("native_zero_call_pages"),
                    "retained_mismatch": "; ".join(problems) or None,
                    **{f"cost_{key}": value for key, value in cost_summary(row.metadata for row in rows).items()},
                },
            )
        )
    return runs, items


def _dataset_key(family: str, relative_parts: tuple[str, ...]) -> str:
    if family == "prompt-sweep-v1" and relative_parts:
        return f"{family}/{relative_parts[0]}"
    return family


def _dataset(root: Path, key: str, directories: list[Path]) -> Experiment:
    """Merge every evaluation sharing one frozen page cohort into a dataset."""
    runs: list[Run] = []
    items: dict[str, Item] = {}
    conflicts = []
    ceilings: dict[str, tuple[str, list[dict[str, Any]]]] = {}
    for directory in directories:
        label = "/".join(directory.relative_to(root / key).parts) or directory.name
        new_runs, new_items = _experiment_runs(root, directory, label)
        for item_key, item in new_items.items():
            if item_key in items and items[item_key].expected != item.expected:
                conflicts.append(item_key)
            items.setdefault(item_key, item)
        runs.extend(new_runs)
        ceiling = read_json(directory / "evaluation.json").get("candidate_ceiling_rows") or []
        if ceiling:
            ceilings.setdefault(digest(ceiling, 64), (label, ceiling))
    for label, ceiling in ceilings.values():
        runs.extend(_ceiling_runs(root, ceiling, f"{label}/" if len(ceilings) > 1 else ""))
    if conflicts:
        message = f"{key}: page kinds disagree across evaluations for {sorted(conflicts)[:5]}"
        raise ValueError(message)
    cohort = key.split("/", 1)[1] if "/" in key else None
    return Experiment(
        dataset=f"exp/decisions/{key}",
        description=(
            f"Page admission decisions ({key}): table/prose candidate selection with exact cell/span scoring "
            "on DEV pages; ambiguous pages are unscored."
            + (f" Cohort status: {DIAGNOSTIC[cohort]}." if cohort in DIAGNOSTIC else "")
        ),
        items=list(items.values()),
        runs=runs,
        source=f"{relative(root / key)} ({len(directories)} evaluations)",
        labels={
            "split": "DEV",
            "heldout": False,
            **({"diagnostic": DIAGNOSTIC[cohort]} if cohort in DIAGNOSTIC else {}),
        },
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield one dataset per page cohort with a run per prompt/model evaluation."""
    root = guard(artifacts / "decisions")
    grouped: dict[str, list[Path]] = {}
    for family in FAMILIES:
        base = root / family
        if not base.is_dir():
            continue
        for path in sorted(guard(base).rglob("evaluation.json")):
            parts = path.parent.relative_to(base).parts
            grouped.setdefault(_dataset_key(family, parts), []).append(path.parent)
    for key, directories in grouped.items():
        yield _dataset(root, key, directories)
