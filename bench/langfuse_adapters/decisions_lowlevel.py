"""L-series lower-level decisions (``decisions/lowlevel-v1/*``) before word assembly.

Every wave directory whose ``evaluation.json`` retains per-input ``outcomes``
becomes one dataset (``exp/decisions/lowlevel-v1/<wave>``): items are the
authored DEV pages with their private join/split/unresolved target, runs are the
evaluated model x arm cohorts plus the zero-call ``native-baseline``.

Row scores are the retained outcome scores (``choice_correct``,
``description_partition_exact``, ``answerable``, ``ambiguous_abstention``,
``candidate_oracle``) plus the answer's probability of the expected option.
Failed, refused, and unattempted inputs stay as rows without scores and keep
their status and reason, so cohort denominators match the retained reports.
Run scores are the retained cohort counts; ``known_exact`` and
``ambiguous_abstentions`` are also recomputed from rows and any difference is
recorded in ``metadata["retained_mismatch"]``.

Waves without an outcome-level evaluation (preparation-only ``basic``,
``basic-v2``, ``history-final``, ``natural-source``, ``gateway-images-large``;
routing-only ``hybrid-*``; the ``natural-matrix``, ``gateway-sanity``,
``gateway-probe``, ``ocr-gate``, ``ocr-alignment``, and ``provider-cache``
protocol checks) are not converted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.decisions_common import (
    catalog_prices,
    choice_scores,
    cost_fields,
    cost_summary,
    flag,
    mismatches,
    relative,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

NAME = "decisions_lowlevel"

SCORES = ("choice_correct", "description_partition_exact", "answerable", "ambiguous_abstention", "candidate_oracle")
COHORT_SCORES = (
    "inputs",
    "scored",
    "known_inputs",
    "known_exact",
    "ambiguous_inputs",
    "ambiguous_abstentions",
    "failures",
    "unattempted",
    "refused_inputs",
    "conservation_failures",
    "encoding_consistent_logical_cases",
    "logical_cases",
)
COHORT_METADATA = (
    "effective_usd",
    "estimated_cost",
    "known_cost_component_usd",
    "unknown_cost_requests",
    "http_elapsed_ms",
    "unique_transmissions",
    "replayed_requests",
    "pages_per_usd",
    "correct_regions_per_usd",
    "api_only_pages_per_minute",
)


def _calls(wave: Path) -> dict[tuple[str, str, str], tuple[dict[str, Any], dict[str, Any]]]:
    """Map (model, arm, page) to the retained call and that page's answer."""
    path = wave / "results.json"
    found: dict[tuple[str, str, str], tuple[dict[str, Any], dict[str, Any]]] = {}
    if not path.exists():
        return found
    for call in read_json(path).get("calls", []):
        answers = call.get("answers") or []
        for index, page in enumerate(call.get("page_ids", [])):
            key = (call.get("model", ""), call.get("arm", ""), page)
            answer = answers[index] if index < len(answers) and isinstance(answers[index], dict) else {}
            if key not in found or (call.get("status") == "ok" and found[key][0].get("status") != "ok"):
                found[key] = (call, answer)
    return found


def _items(wave: Path, outcomes: list[dict[str, Any]], baseline: list[dict[str, Any]]) -> list[Item]:
    targets_path = wave / "private-targets.json"
    targets = {target["id"]: target for target in read_json(targets_path)} if targets_path.exists() else {}
    manifest_path = wave / "manifest.json"
    pages = {page["id"]: page for page in read_json(manifest_path).get("pages", [])} if manifest_path.exists() else {}
    items: dict[str, Item] = {}
    for outcome in [*outcomes, *baseline]:
        page = outcome["id"]
        if page in items:
            continue
        target = targets.get(page, {})
        source = pages.get(page, {})
        items[page] = Item(
            key=page,
            input={
                "page_id": page,
                "logical_id": outcome.get("logical_id", target.get("logical_id")),
                "family": outcome.get("family", target.get("family")),
                "encoding": outcome.get("encoding", target.get("encoding")),
                "recoverability": outcome.get("recoverability"),
                "history_variant": outcome.get("history_variant"),
                "source_sha256": source.get("source_sha256"),
                "observation_sha256": source.get("observation_sha256"),
            },
            expected={"choice": outcome["expected"], "groups": target.get("expected_groups")},
            metadata={"family": outcome.get("family"), "expected": outcome["expected"]},
        )
    return list(items.values())


def _row(root: Path, outcome: Mapping[str, Any], call: Mapping[str, Any] | None, answer: Mapping[str, Any]) -> Row:
    score = outcome.get("score") or {}
    scores: dict[str, float | None] = {}
    if score:
        scores = {name: flag(score.get(name)) for name in SCORES}
        scores.update(choice_scores(answer, outcome["expected"]) if answer else {})
        scores["choice_correct"] = flag(score.get("choice_correct"))
    model = outcome.get("model", "native")
    accounting = {}
    if call and call.get("entry"):
        accounting = cost_fields(call["entry"], call.get("usage"), catalog_prices(root).get(model))
    output = {"choice": outcome.get("choice")}
    if answer.get("probabilities"):
        output["probabilities"] = answer["probabilities"]
    if score.get("output"):
        output["groups"] = score["output"].get("groups")
        output["conservation"] = score["output"].get("conservation")
    return Row(
        item_key=outcome["id"],
        output=output,
        scores=scores,
        metadata={
            "status": outcome.get("status", "ok"),
            "refused": bool(outcome.get("refused")),
            "reason": outcome.get("reason"),
            "expected": outcome["expected"],
            "family": outcome.get("family"),
            **accounting,
        },
    )


def _recount(rows: list[Row]) -> dict[str, float]:
    known = [row for row in rows if row.metadata["expected"] != "unresolved"]
    ambiguous = [row for row in rows if row.metadata["expected"] == "unresolved"]
    return {
        "known_exact": sum(row.scores.get("description_partition_exact") or 0 for row in known),
        "ambiguous_abstentions": sum(row.scores.get("ambiguous_abstention") or 0 for row in ambiguous),
        "scored": sum(bool(row.scores) for row in rows),
        "inputs": len(rows),
    }


def _wave(root: Path, wave: Path) -> Experiment | None:
    evaluation = read_json(wave / "evaluation.json")
    outcomes = evaluation.get("outcomes")
    if not outcomes:
        return None
    baseline = evaluation.get("native_baseline") or []
    calls = _calls(wave)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for outcome in outcomes:
        groups.setdefault((outcome["model"], outcome["arm"]), []).append(outcome)
    cohorts = {(cohort["model"], cohort["arm"]): cohort for cohort in evaluation.get("cohorts", [])}
    label = evaluation.get("experiment") or wave.name
    runs = []
    for (model, arm), members in groups.items():
        rows = []
        for outcome in members:
            call, answer = calls.get((model, arm, outcome["id"]), (None, {}))
            rows.append(_row(root, outcome, call, answer))
        cohort = cohorts.get((model, arm), {})
        scores = {name: cohort.get(name) for name in COHORT_SCORES if name in cohort}
        if cohort.get("known_inputs"):
            scores["known_exact_rate"] = cohort["known_exact"] / cohort["known_inputs"]
        if cohort.get("ambiguous_inputs"):
            scores["ambiguous_abstention_rate"] = cohort["ambiguous_abstentions"] / cohort["ambiguous_inputs"]
        recount = _recount(rows)
        problems = mismatches({key: cohort[key] for key in recount if key in cohort}, recount)
        runs.append(
            Run(
                name=f"{model}/{arm}",
                description=f"{label} {wave.name}: {model}, arm {arm}; join/split/unresolved description partition.",
                rows=rows,
                scores=scores,
                metadata={
                    "experiment": label,
                    "wave": wave.name,
                    "model": model,
                    "arm": arm,
                    "retained_mismatch": "; ".join(problems) or (None if cohort else "no retained cohort"),
                    **{f"retained_{key}": cohort.get(key) for key in COHORT_METADATA if key in cohort},
                    **{f"cost_{key}": value for key, value in cost_summary(row.metadata for row in rows).items()},
                },
            )
        )
    if baseline:
        rows = [_row(root, {**outcome, "model": "native", "status": "ok"}, None, {}) for outcome in baseline]
        recount = _recount(rows)
        runs.append(
            Run(
                name="native-baseline",
                description=f"{label} {wave.name}: zero-call native extraction baseline.",
                rows=rows,
                scores={
                    **recount,
                    "known_inputs": sum(row.metadata["expected"] != "unresolved" for row in rows),
                    "ambiguous_inputs": sum(row.metadata["expected"] == "unresolved" for row in rows),
                },
                metadata={"experiment": label, "wave": wave.name, "model": "native", "arm": "native"},
            )
        )
    return Experiment(
        dataset=f"exp/decisions/lowlevel-v1/{wave.name}",
        description=(
            f"{label} lower-level DEV decisions ({wave.name}): join/split/unresolved partition of two target "
            f"description chunks. {evaluation.get('scope') or ''}".strip()
        ),
        items=_items(wave, outcomes, baseline),
        runs=runs,
        source=relative(wave),
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield one dataset per L-series wave with outcome-level evaluation."""
    root = guard(artifacts / "decisions")
    base = root / "lowlevel-v1"
    if not base.is_dir():
        return
    for wave in sorted(path for path in base.iterdir() if path.is_dir()):
        if (guard(wave) / "evaluation.json").exists():
            experiment = _wave(root, wave)
            if experiment is not None:
                yield experiment
