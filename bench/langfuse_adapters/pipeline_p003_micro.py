"""P003 micro relationship probes as Langfuse experiments.

Micro arms ask hosted decision models one same/separate relationship question
per selected real-page word pair (``micro`` packets or ``verbose`` packets).
These probes have no reference labels: the retained reports state
``correctness_measured: false`` and ``table_quality_measured: false``. The
experiment therefore records operational outcomes only (decisive answers,
abstentions, malformed responses, transport errors), uncalibrated confidence,
and provider-reported charges; it never derives an accuracy.

- Dataset ``exp/pipeline-p003/<queue>/micro-relations-<n>q``: one per queue
  (``parallel-confirmation-header-micro51-v1`` micro arms,
  ``gateway-micro-v1``). Items are questions keyed ``<page_id>/<pair_id>``
  with kind and source-word IDs as input and no expected output.
- Runs: one per arm ``report.json``; every intended question remains a row.
- Row scores: ``decisive``, ``abstained``, ``malformed``,
  ``transport_error``, ``attempted``, ``raw_confidence`` (uncalibrated) and,
  when present in the ledger entry, ``provider_reported_usd`` and
  ``input_tokens``. Run scores repeat the report's counts, rates, charges and
  CPU/RSS; ``metadata["aggregate_check"]`` compares row statuses with
  ``status_counts``.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run
from bench.langfuse_adapters.pipeline_p003 import (
    CAMPAIGN,
    PREFIX,
    cost_scores,
    load,
    mapping,
    number,
    rel,
    resource_scores,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "pipeline-p003-micro"
QUEUES = {"parallel-confirmation-header-micro51-v1": "micro-", "gateway-micro-v1": ""}
ATTEMPTED = {"valid_nonabstaining", "valid_abstention", "malformed_response", "transport_error"}


def key(result: dict[str, Any]) -> str:
    """Question identity shared across arms."""
    return f"{result.get('page_id')}/{result.get('pair_id')}"


def row_for(arm: str, result: dict[str, Any]) -> Row:
    """Operational outcome of one probe question."""
    status = str(result.get("status"))
    receipt = mapping(result.get("receipt"))
    decision = mapping(receipt.get("decision"))
    entry = mapping(result.get("entry"))
    usage = mapping(result.get("usage"))
    scores: dict[str, Any] = {
        "decisive": status == "valid_nonabstaining",
        "abstained": status == "valid_abstention",
        "malformed": status == "malformed_response",
        "transport_error": status == "transport_error",
        "attempted": status in ATTEMPTED,
        "raw_confidence": number(decision.get("confidence")),
        "input_tokens": number(usage.get("input_tokens")),
    }
    if entry.get("cost_status") == "provider-reported USD" and "provider_reported_usd" in entry:
        scores["provider_reported_usd"] = number(entry.get("provider_reported_usd"))
    return Row(
        item_key=key(result),
        output={"status": status, "choice": decision.get("choice"), "abstained": receipt.get("abstained")},
        scores=scores,
        metadata={
            "status": status,
            "model": result.get("model"),
            "served_model": entry.get("served_model"),
            "cost_status": entry.get("cost_status"),
            "uncalibrated_confidence": True,
        },
        wall_ms=number(entry.get("elapsed_ms")),
        started=number(entry.get("started_at")),
        name=f"{arm}/{key(result)}",
    )


def run_for(queue: str, arm: Path, report: dict[str, Any]) -> Run:
    """One micro arm."""
    results = [r for r in report.get("results") or [] if isinstance(r, dict)]
    rows = [row_for(arm.name, r) for r in results]
    counts = Counter(str(r.get("status")) for r in results)
    reported = report.get("status_counts") or {}
    check = "ok" if dict(counts) == reported else f"row statuses {dict(counts)} != reported {reported}"
    config = report.get("config") or {}
    scores: dict[str, float | None] = {
        "question_count": number(report.get("question_count")),
        "attempted_question_count": number(report.get("attempted_question_count")),
        "questions_per_minute": number(report.get("questions_per_minute")),
        "valid_nonabstaining_questions_per_minute": number(report.get("valid_nonabstaining_questions_per_minute")),
        "questions_per_dollar": number(report.get("questions_per_dollar")),
        **{f"status_{k}": number(v) for k, v in reported.items()},
    }
    scores.update(cost_scores(report.get("charges")))
    scores.update(resource_scores(report.get("metrics")))
    return Run(
        name=f"{queue}/{arm.name}",
        description=f"P003 micro relationship probe {arm.name} ({config.get('model')}); correctness not measured",
        rows=rows,
        metadata={
            "campaign": "P003",
            "queue": queue,
            "arm": arm.name,
            "source": rel(arm / "report.json"),
            "scope": report.get("scope"),
            "correctness_measured": report.get("correctness_measured"),
            "aggregate_check": check,
            **{f"config_{k}": config.get(k) for k in ("model", "mode", "image", "transport_concurrency", "provider")},
        },
        scores={k: v for k, v in scores.items() if v is not None},
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """One experiment per micro queue."""
    root = artifacts / CAMPAIGN
    for queue, prefix in QUEUES.items():
        directory = root / queue
        if not directory.is_dir():
            continue
        runs: list[Run] = []
        questions: dict[str, dict[str, Any]] = {}
        skipped = 0
        for arm in sorted(p for p in directory.iterdir() if p.is_dir() and p.name.startswith(prefix)):
            report = load(arm / "report.json")
            if not isinstance(report, dict) or not isinstance(report.get("results"), list):
                skipped += 1
                continue
            if not any(isinstance(r, dict) and "pair_id" in r for r in report["results"]):
                skipped += 1
                continue
            for result in report["results"]:
                if isinstance(result, dict):
                    questions.setdefault(key(result), result)
            runs.append(run_for(queue, arm, report))
        if not runs:
            continue
        items = [
            Item(
                key=question,
                input={
                    "page_id": result.get("page_id"),
                    "pair_id": result.get("pair_id"),
                    "kind": result.get("kind"),
                    "source_ids": result.get("source_ids"),
                },
                expected=None,
                metadata={"kind": result.get("kind"), "labels": "none; correctness not measured"},
            )
            for question, result in sorted(questions.items())
        ]
        yield Experiment(
            dataset=f"{PREFIX}/{queue}/micro-relations-{len(items)}q",
            description=(
                f"P003 {queue}: micro same/separate probes on real-page word pairs. "
                "No reference labels; operational outcomes and uncalibrated confidence only."
            ),
            items=items,
            runs=runs,
            source=rel(directory),
            labels={"split": "DEV", "heldout": False, "campaign": "P003", "skipped_arms": skipped},
        )
