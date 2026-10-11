"""P003 synthetic relationship questions (``pipeline-p003``) as Langfuse experiments.

The synthetic queues ask one local relationship question ("same" or
"separate" row/cell/wrap membership for two source words) per authored page.
Every arm was independently replayed into an ``*evaluation.json`` holding the
verified per-question outcomes (``original_verified.rows``) and the
evaluator's aggregates (``original_scores``). The catalog-alias replay
(``secondary_*``) re-parses the same responses; it is reported beside the
original strict outcome, never instead of it.

- Dataset ``exp/pipeline-p003/<queue>/synthetic-relations-24``: one per queue
  (``parallel-synthetic48-v2``, ``parallel-synthetic-resolution25-v1``,
  ``parallel-synthetic-rules-resolution10-v1``, ``parallel-shared56-v1``).
  Items are the 24 authored cases of the matching private generator gold
  (``synthetic-micro-relations-v*/private-gold.json``, joined by
  ``source_frozen_sha256``): case identity, kind, source-word pair and PDF
  reference as input, ``expected_choice`` as expected output.
- Runs: one per arm. Rows keep every intended case, including abstentions,
  malformed responses, transport errors and not-attempted cases, so the
  strict denominator stays 24.
- Row scores: ``author_label_match`` (decisive answer equal to the generator
  label; 0 for every other status, as the evaluator's strict fraction counts
  it), ``decisive``, ``abstained``, ``malformed``, ``transport_error``,
  ``attempted``, ``raw_confidence`` (uncalibrated) and
  ``alias_replay_author_label_match``. Single-question arms also carry the
  per-question provider-reported charge from ``report.json``; shared-context
  arms are charged per group, so their rows have none.
- Run scores repeat the evaluator aggregates (all 24, visually cued 18,
  indeterminate 6, per kind, twin consistency) plus question rates, CPU/RSS
  and costs. ``metadata["aggregate_check"]`` compares the row sums with
  ``original_scores``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run
from bench.langfuse_adapters.pipeline_p003 import CAMPAIGN, PREFIX, cost_scores, load, mapping, number, rel

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "pipeline-p003-synthetic"
QUEUES = (
    "parallel-synthetic48-v2",
    "parallel-synthetic-resolution25-v1",
    "parallel-synthetic-rules-resolution10-v1",
    "parallel-shared56-v1",
)
ATTEMPTED = {"valid_nonabstaining", "valid_abstention", "malformed_response", "transport_error"}
SUBSETS = ("all_24", "visually_cued_18", "indeterminate_6")
NON_ARMS = {"logs", "trusted-code", "code"}


def golds(root: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    """Private generator gold files keyed by the source freeze they label."""
    found = {}
    for path in sorted(root.glob("*/private-gold.json")):
        value = load(path)
        if isinstance(value, dict) and isinstance(value.get("cases"), list):
            found[str(value.get("source_frozen_sha256"))] = (path, value)
    return found


def items_for(gold_path: Path, gold: dict[str, Any]) -> list[Item]:
    """One item per authored case; the label stays in expected output only."""
    items = []
    for case in gold["cases"]:
        pdf = gold_path.parent / "pdfs" / f"{case['id']}.pdf"
        items.append(
            Item(
                key=str(case["id"]),
                input={
                    "case_id": case["id"],
                    "kind": case.get("kind"),
                    "family": case.get("family"),
                    "pair_source_ids": case.get("pair_source_ids"),
                    "pair_literals": case.get("pair_literals"),
                    "pdf": {"path": rel(pdf) if pdf.is_file() else None, "sha256": case.get("pdf_sha256")},
                },
                expected={"expected_choice": case.get("expected_choice")},
                metadata={
                    "kind": case.get("kind"),
                    "indeterminate": bool(case.get("evidence_limitation")),
                    "label_origin": case.get("label_origin"),
                    "gold": rel(gold_path),
                },
            )
        )
    return items


def evaluation_file(arm: Path) -> Path | None:
    """Prefer the alias-replay evaluation (it embeds the original), else any scored evaluation."""
    candidates = sorted(arm.glob("*evaluation.json"), key=lambda p: ("alias" not in p.name, p.name))
    return candidates[0] if candidates else None


def question_charges(arm: Path) -> dict[int, dict[str, Any]]:
    """Per-question ledger entries from the arm report (single-question arms only)."""
    report = load(arm / "report.json")
    charges = {}
    for result in (report or {}).get("results") or []:
        if isinstance(result, dict) and isinstance(result.get("entry"), dict) and "index" in result:
            charges[int(result["index"])] = result["entry"]
    return charges


def row_scores(row: dict[str, Any], expected: str | None, secondary: dict[str, Any] | None) -> dict[str, Any]:
    """Strict per-question outcome scores."""
    status = str(row.get("status"))
    receipt = mapping(row.get("receipt"))
    decisive = status == "valid_nonabstaining"
    scores: dict[str, Any] = {
        "author_label_match": decisive and receipt.get("choice") == expected,
        "decisive": decisive,
        "abstained": status == "valid_abstention",
        "malformed": status == "malformed_response",
        "transport_error": status == "transport_error",
        "attempted": status in ATTEMPTED,
        "raw_confidence": number(receipt.get("raw_confidence")) if receipt else None,
    }
    if secondary is not None:
        second = mapping(secondary.get("receipt"))
        scores["alias_replay_author_label_match"] = (
            secondary.get("status") == "valid_nonabstaining" and second.get("choice") == expected
        )
    return scores


def run_scores(scores: dict[str, Any], verified: dict[str, Any]) -> dict[str, float | None]:
    """Repeat evaluator aggregates, rates, CPU/RSS and costs."""
    out: dict[str, float | None] = {}
    for subset in SUBSETS:
        block = scores.get(subset) or {}
        for key in (
            "intended_count",
            "valid_nonabstaining_count",
            "author_label_matches",
            "strict_author_label_fraction",
            "conditional_decisive_author_label_fraction",
        ):
            out[f"{subset}_{key}"] = number(block.get(key))
    for kind, block in (scores.get("per_kind") or {}).items():
        out[f"{kind}_strict_author_label_fraction"] = number((block or {}).get("strict_author_label_fraction"))
    for key, value in (scores.get("twins_summary") or {}).items():
        out[f"twins_{key}"] = number(value)
    for key, value in (scores.get("question_rates") or {}).items():
        out[key] = number(value)
    out.update(cost_scores(scores.get("charges") or verified.get("charges")))
    metrics = verified.get("reported_metrics") or {}
    for key in ("cpu_seconds", "cpu_utilization_percent", "peak_sampled_rss_bytes", "wall_seconds"):
        out[key] = number(metrics.get(key))
    return {k: v for k, v in out.items() if v is not None}


def check(rows: list[Row], scores: dict[str, Any], indeterminate: set[str]) -> str:
    """Compare row sums with the evaluator's author-label match counts."""
    problems = []
    subsets = {
        "all_24": rows,
        "visually_cued_18": [r for r in rows if r.item_key not in indeterminate],
        "indeterminate_6": [r for r in rows if r.item_key in indeterminate],
    }
    for subset, selected in subsets.items():
        block = scores.get(subset) or {}
        for key, field in (("author_label_matches", "author_label_match"), ("valid_nonabstaining_count", "decisive")):
            reported = number(block.get(key))
            summed = sum(float(bool(r.scores.get(field))) for r in selected)
            if reported is not None and summed != reported:
                problems.append(f"{subset}.{key}: rows {summed:g} != reported {reported:g}")
        reported = number(block.get("intended_count"))
        if reported is not None and len(selected) != reported:
            problems.append(f"{subset}.intended_count: rows {len(selected)} != reported {reported:g}")
    return "ok" if not problems else "; ".join(problems)


def arm_run(queue: str, arm: Path, gold: dict[str, Any], path: Path, value: dict[str, Any]) -> Run:
    """Build one run from a verified synthetic evaluation."""
    verified = value.get("original_verified") or value.get("verified") or {}
    scores = value.get("original_scores") or value.get("scores") or {}
    secondary = {str(r.get("id")): r for r in (value.get("secondary_verified") or {}).get("rows") or []}
    expected = {str(c["id"]): c.get("expected_choice") for c in gold["cases"]}
    indeterminate = {str(c["id"]) for c in gold["cases"] if c.get("evidence_limitation")}
    config = verified.get("config") or scores.get("config") or {}
    charges = question_charges(arm)
    rows = []
    for row in verified.get("rows") or []:
        case = str(row.get("id"))
        receipt = mapping(row.get("receipt"))
        entry = charges.get(int(row["index"])) if "index" in row and row.get("status") in ATTEMPTED else None
        row_out = Row(
            item_key=case,
            output={
                "status": row.get("status"),
                "choice": receipt.get("choice"),
                "probabilities": receipt.get("raw_probabilities"),
                "abstained": receipt.get("abstained"),
                "alias_replay_status": (secondary.get(case) or {}).get("status") if secondary else None,
            },
            scores=row_scores(row, expected.get(case), secondary.get(case) if secondary else None),
            metadata={
                "status": row.get("status"),
                "model": row.get("model") or config.get("model"),
                "kind": row.get("kind"),
                "group_index": row.get("group_index"),
                "uncalibrated_confidence": True,
            },
            name=f"{arm.name}/{case}",
        )
        if entry is not None:
            row_out.metadata["cost_status"] = entry.get("cost_status")
            row_out.metadata["served_model"] = entry.get("served_model")
            if "provider_reported_usd" in entry:
                row_out.scores["provider_reported_usd"] = number(entry.get("provider_reported_usd"))
            if entry.get("cost_status") != "reserved":
                row_out.scores["accounted_usd"] = number(entry.get("accounted_usd"))
            row_out.wall_ms = number(entry.get("elapsed_ms"))
            row_out.started = number(entry.get("started_at"))
        rows.append(row_out)
    metadata = {
        "campaign": "P003",
        "queue": queue,
        "arm": arm.name,
        "source": rel(path),
        "evaluation": path.name,
        "aggregate_check": check(rows, scores, indeterminate),
        "alias_replay": bool(secondary),
        "gold_access": scores.get("gold_access"),
        **{f"config_{k}": config.get(k) for k in ("model", "mode", "image_edge", "viewport", "transport_concurrency")},
    }
    return Run(
        name=f"{queue}/{arm.name}",
        description=f"P003 synthetic relations {queue} arm {arm.name} ({config.get('model')}); {rel(path)}",
        rows=rows,
        metadata=metadata,
        scores=dict(run_scores(scores, verified)),
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """One experiment per synthetic queue, with the gold matching its source freeze."""
    root = artifacts / CAMPAIGN
    if not root.is_dir():
        return
    labels = golds(root)
    for queue in QUEUES:
        directory = root / queue
        if not directory.is_dir():
            continue
        runs: dict[str, list[Run]] = {}
        gold_for: dict[str, tuple[Path, dict[str, Any]]] = {}
        skipped = 0
        for arm in sorted(p for p in directory.iterdir() if p.is_dir() and p.name not in NON_ARMS):
            path = evaluation_file(arm)
            value = load(path) if path else None
            verified = (value or {}).get("original_verified") or (value or {}).get("verified")
            if not isinstance(verified, dict) or not isinstance(verified.get("rows"), list):
                skipped += 1
                continue
            frozen = str(verified.get("source_frozen_sha256"))
            if frozen not in labels or path is None:
                skipped += 1
                continue
            gold_for[frozen] = labels[frozen]
            runs.setdefault(frozen, []).append(arm_run(queue, arm, labels[frozen][1], path, value or {}))
        for frozen, queue_runs in sorted(runs.items()):
            gold_path, gold = gold_for[frozen]
            suffix = "" if len(runs) == 1 else f"-{frozen[:8]}"
            yield Experiment(
                dataset=f"{PREFIX}/{queue}/synthetic-relations-{len(gold['cases'])}{suffix}",
                description=(
                    f"P003 {queue}: one same/separate relationship question per authored synthetic page, "
                    "scored against hidden generator labels. Agreement is not a recoverability claim; "
                    "confidence is uncalibrated."
                ),
                items=items_for(gold_path, gold),
                runs=queue_runs,
                source=rel(directory),
                labels={"split": "DEV", "heldout": False, "campaign": "P003", "skipped_arms": skipped},
            )
