"""M001/M002/M004 context-assembly decisions (evidence repair and image side channels).

Covered retained artifacts: ``decisions/context-run-{initial,facts,compact,ablations}.json``.
The per-case ``context-<wave>-<model>-<arm>-NN.json`` files in the same
directory duplicate these records and are not read separately.

Thirty authored DEV row-wrap PDFs (ten correlated templates x three
vocabularies) form one dataset; each run is one wave/model/arm, and the
ablation wave covers its nine-case subset only. Row scores reuse the retained
``bench.decision_records.score_records`` results: ``region_exact`` and
``record_*`` against the full-document label, ``evidence_*`` against the label
the supplied evidence supports, plus the choice, abstention, and probability of
the expected document answer. Run scores count exact regions over the run's
rows, matching ``bench/results/evidence-repair.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.decisions_common import (
    average,
    catalog_prices,
    choice_scores,
    cost_fields,
    cost_summary,
    flag,
    relative,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

NAME = "decisions_context"

WAVES = ("initial", "facts", "compact", "ablations")
SCORES = ("region_exact", "record_f1", "record_precision", "record_recall", "valid", "source_conservation")


def _row(root: Path, record: Mapping[str, Any]) -> Row:
    score = record.get("score") or {}
    evidence = record.get("evidence_score") or {}
    answer = record.get("answer") or {}
    scores: dict[str, float | None] = {name: flag(score.get(name)) for name in SCORES}
    scores.update({f"evidence_{name}": flag(evidence.get(name)) for name in ("region_exact", "record_f1")})
    scores.update(choice_scores(answer, record.get("expected_document")))
    scores["evidence_choice_correct"] = (
        flag(answer.get("choice") == record.get("expected_evidence")) if answer.get("choice") is not None else None
    )
    status = "failed" if record.get("error") else "ok" if answer else "missing"
    entry = record.get("entry") or {}
    return Row(
        item_key=record["case_id"],
        output={
            "choice": answer.get("choice"),
            "probabilities": answer.get("probabilities"),
            "native_choice": record.get("native_choice"),
            "expected_evidence": record.get("expected_evidence"),
            "assembly_cells": len((record.get("assembly") or {}).get("cells", [])),
            "assembly_records": len((record.get("assembly") or {}).get("records", [])),
            **({"error": record["error"]} if record.get("error") else {}),
        },
        scores=scores,
        metadata={
            "status": status,
            "arm": record["arm"],
            "model": record["model"],
            "replayed": bool(record.get("replayed")),
            "image": str(record["image"]) if record.get("image") else None,
            **cost_fields(entry, record.get("usage"), catalog_prices(root).get(record["model"])),
        },
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """Yield one context-assembly dataset with a run per wave/model/arm."""
    root = guard(artifacts / "decisions")
    items: dict[str, Item] = {}
    runs: list[Run] = []
    sources = []
    for wave in WAVES:
        path = root / f"context-run-{wave}.json"
        if not path.exists():
            continue
        sources.append(relative(path))
        report = read_json(path)
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for record in report["records"]:
            groups.setdefault((record["model"], record["arm"]), []).append(record)
            items.setdefault(
                record["case_id"],
                Item(
                    key=record["case_id"],
                    input={
                        "case_id": record["case_id"],
                        "family": record["family"],
                        "pdf_sha256": record["pdf_sha256"],
                    },
                    expected={"document": record["expected_document"]},
                    metadata={"family": record["family"]},
                ),
            )
        for (model, arm), records in groups.items():
            rows = [_row(root, record) for record in records]
            f1 = [row.scores["record_f1"] for row in rows if row.scores.get("record_f1") is not None]
            exact = sum(row.scores.get("region_exact") or 0 for row in rows)
            runs.append(
                Run(
                    name=f"{wave}/{model}/{arm}",
                    description=f"Context assembly {wave}, {model}, arm {arm}: exact regions, {len(rows)} DEV cases.",
                    rows=rows,
                    scores={
                        "region_exact_count": exact,
                        "region_exact_rate": exact / len(rows),
                        "mean_record_f1": average(f1),
                        "evidence_region_exact_count": sum(
                            row.scores.get("evidence_region_exact") or 0 for row in rows
                        ),
                        "abstained_count": sum(row.scores.get("abstained") or 0 for row in rows),
                        "source_conservation_failures": sum(row.scores.get("source_conservation") == 0 for row in rows),
                        "cases": len(rows),
                    },
                    metadata={
                        "wave": wave,
                        "model": model,
                        "arm": arm,
                        "evidence_status": report.get("evidence_status"),
                        "code_sha256": report.get("code_sha256"),
                        **{f"cost_{key}": value for key, value in cost_summary(row.metadata for row in rows).items()},
                        # The retained Markdown sums usage per record, so replayed identical requests count twice.
                        "record_usage_cost_sum_including_replays": sum(
                            (record.get("usage") or {}).get("cost") or 0 for record in records
                        ),
                    },
                )
            )
    if runs:
        yield Experiment(
            dataset="exp/decisions/context-assembly-v1",
            description=(
                "M001/M002/M004 context-assembly choices on 30 authored DEV row-wrap PDFs (ten correlated templates "
                "x three vocabularies): text, compact/derived facts, image and history side channels."
            ),
            items=list(items.values()),
            runs=runs,
            source=", ".join(sources),
        )
