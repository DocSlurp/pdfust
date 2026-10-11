"""P003 continuation content re-evaluations as Langfuse experiments.

The continuation studies replay retained hosted decision sessions on the ten
authored ``financial-context`` cases and score the emitted table bodies with
the content-alignment metric (``p003-span-content``), without new API calls:

- ``continuation-oplog-evaluation-v1``: original operation-log sessions per
  model.
- ``continuation-oplog-termination-evaluation-v1``: the same sessions under
  counterfactual termination policies (baseline-original, P1-P3); omitted
  suffix costs are hypothetical, not savings already realized.
- ``r001-content-eval-v1``: region-decision arms (geometry, image...) per model.

Each study becomes dataset ``exp/pipeline-p003/<study>/financial-context-<n>``.
Items are cases (reference body as expected output when the study retains
it); runs are model (and policy or arm) combinations; rows keep excluded
cases (``author-unresolved``) with ``metadata["status"]`` and no content
score, matching the evaluator's known-case denominators.

Row scores: ``content_precision`` / ``content_recall`` (per-case alignment),
``content_matched`` / ``content_reference_units`` / ``content_prediction_units``,
``strict_body_complete``, ``completed_content_recovery`` and study-specific
counters (call counts, source completeness, original pair metrics,
hypothetical omitted cost). Run scores repeat the study summaries;
``metadata["aggregate_check"]`` re-derives the micro content recall from rows.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run
from bench.langfuse_adapters.pipeline_p003 import CAMPAIGN, PREFIX, RATIO_TOLERANCE, load, mapping, number, rel

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "pipeline-p003-continuation"
STUDIES = {
    "continuation-oplog-evaluation-v1": ("models", ("model",), "known_body_content_recall"),
    "continuation-oplog-termination-evaluation-v1": ("models", ("model", "policy"), "known_body_content_recall"),
    "r001-content-eval-v1": ("arms", ("model", "arm"), "content_recall"),
}
ROW_FLAGS = (
    "strict_body_complete",
    "completed_content_recovery",
    "source_complete",
    "all_fragments_unassigned",
    "author_unresolved",
    "call_count",
    "processed_original_calls",
    "omitted_original_calls",
    "hypothetical_omitted_effective_usd",
)
ORIGINAL = ("pair_precision", "pair_recall", "row_column_exact", "source_group_exact", "conservation")


def case_key(record: dict[str, Any]) -> str:
    """Case identity (termination records keep only the case index)."""
    if record.get("case_id"):
        return str(record["case_id"])
    return f"case-{record.get('case_index')}"


def status(record: dict[str, Any]) -> str:
    """Excluded cases stay as rows without content credit."""
    if record.get("exclusion"):
        return f"excluded:{record['exclusion']}"
    if record.get("author_unresolved"):
        return "excluded:author-unresolved"
    content = mapping(record.get("content"))
    return "scored" if content.get("supported") else "unsupported"


def row_for(run: str, record: dict[str, Any]) -> Row:
    """Content alignment outcome for one case."""
    content = mapping(record.get("content"))
    counts = mapping(content.get("counts"))
    outcome = status(record)
    scores: dict[str, Any] = {k: number(record.get(k)) for k in ROW_FLAGS if k in record}
    if outcome == "scored":
        scores.update(
            content_precision=number(content.get("precision")),
            content_recall=number(content.get("recall")),
            content_matched=number(counts.get("matched")),
            content_reference_units=number(counts.get("reference_units")),
            content_prediction_units=number(counts.get("prediction_units")),
            content_recovered_with_row_order=number(content.get("content_recovered_with_row_order")),
        )
    original = mapping(record.get("original_score"))
    scores.update({f"original_{k}": number(original.get(k)) for k in ORIGINAL if k in original})
    return Row(
        item_key=case_key(record),
        output={
            "status": outcome,
            "stop_reason": record.get("stop_reason", record.get("original_stop_reason")),
            "controller_stop": record.get("controller_stop"),
            "body_sha256": record.get("body_sha256"),
            "predicted_body": (record.get("predicted_body") or record.get("body_table") or {}).get("values"),
        },
        scores=scores,
        metadata={
            "status": outcome,
            "model": record.get("model"),
            "policy": record.get("policy"),
            "arm": record.get("arm"),
        },
        name=f"{run}/{case_key(record)}",
    )


def check(rows: list[Row], reported: float | None) -> str:
    """Micro content recall over scored rows versus the study summary."""
    scored = [r for r in rows if r.metadata["status"] == "scored"]
    reference = sum(r.scores.get("content_reference_units") or 0.0 for r in scored)
    if reported is None or not reference:
        return "unchecked"
    recall = sum(r.scores.get("content_matched") or 0.0 for r in scored) / reference
    return (
        "ok"
        if abs(recall - reported) < RATIO_TOLERANCE
        else f"content recall rows {recall:.6f} != reported {reported:.6f}"
    )


def summary_scores(summary: dict[str, Any]) -> dict[str, float | None]:
    """Numeric study summary fields (costs keep their retained basis names)."""
    out: dict[str, float | None] = {}
    for key, value in summary.items():
        if key in {"model", "policy", "arm"} or isinstance(value, (dict, list)):
            continue
        out[key] = number(value)
    for key, value in (summary.get("counts") or summary.get("content_counts") or {}).items():
        out[f"content_{key}"] = number(value)
    costs = [c for c in summary.get("original_costs") or [] if isinstance(c, dict)]
    if costs:
        out["original_cost_entries"] = float(len(costs))
        for basis in sorted({str(c.get("basis")) for c in costs}):
            selected = [number(c.get("effective_usd")) for c in costs if str(c.get("basis")) == basis]
            known = [v for v in selected if v is not None]
            label = re.sub(r"[^a-z0-9]+", "_", basis.lower()).strip("_")
            out[f"original_{label}_entries"] = float(len(selected))
            if len(known) == len(selected):
                out[f"original_{label}_effective_usd"] = sum(known)
    return {k: v for k, v in out.items() if v is not None}


def collect(artifacts: Path) -> Iterable[Experiment]:
    """One experiment per continuation study."""
    root = artifacts / CAMPAIGN
    for study, (summary_key, fields, recall_key) in STUDIES.items():
        path = root / study / "report.json"
        value = load(path)
        if not isinstance(value, dict) or not isinstance(value.get("records"), list):
            continue
        grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        cases: dict[str, dict[str, Any]] = {}
        for record in value["records"]:
            if isinstance(record, dict):
                grouped[tuple(str(record.get(f)) for f in fields)].append(record)
                cases.setdefault(case_key(record), record)
        summaries = {
            tuple(str(s.get(f)) for f in fields): s for s in value.get(summary_key) or [] if isinstance(s, dict)
        }
        runs = []
        for group, records in sorted(grouped.items()):
            name = f"{study}/{'/'.join(group)}"
            rows = [row_for(name, r) for r in records]
            summary = summaries.get(group, {})
            runs.append(
                Run(
                    name=name,
                    description=f"P003 {study} {' '.join(group)}; retained sessions re-scored without API calls",
                    rows=rows,
                    metadata={
                        "campaign": "P003",
                        "queue": study,
                        "source": rel(path),
                        **dict(zip(fields, group, strict=True)),
                        "new_api_calls": value.get("new_api_calls"),
                        "aggregate_check": check(rows, number(summary.get(recall_key))),
                    },
                    scores=dict(summary_scores(summary)),
                )
            )
        items = []
        for key, record in sorted(cases.items()):
            reference = record.get("reference_body") if isinstance(record.get("reference_body"), dict) else None
            items.append(
                Item(
                    key=key,
                    input={"case": key, "case_index": record.get("case_index"), "study": study},
                    expected={"reference_body": reference.get("values"), "spans": reference.get("spans")}
                    if reference
                    else None,
                    metadata={"reference_retained": reference is not None},
                )
            )
        yield Experiment(
            dataset=f"{PREFIX}/{study}/financial-context-{len(items)}",
            description=(
                f"P003 {study}: retained continuation sessions on authored financial-context cases, "
                "re-scored with content alignment (no new API calls)."
            ),
            items=items,
            runs=runs,
            source=rel(path),
            labels={"split": "DEV", "heldout": False, "campaign": "P003"},
        )
