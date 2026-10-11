"""Silver-realism-v2 frozen rolling-candidate admission (A002 image512), per page.

Source: ``silver-realism-v2/<version>/admission-image512/{evaluation,hosted-results}.json``
(``bench/rolling_row_run.py`` with ``bench/decision_hosted.py``); committed summary
``bench/results/realistic-rolling-admission.md``. Runs are each hosted model cohort plus the
two offline candidate-ceiling variants. Ambiguous pages stay in every run with unscored
(omitted) correctness, matching the report's denominators. Costs are the retained
provider-reported/effective USD; nothing is re-requested.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.corpus_common import Score, check_metadata, compare, mtime, numeric, ref, rel, scalars

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "corpus-silver-realism"
CORPUS = "silver-realism-v2"
ARM = "admission-image512"
SLICE_FIELDS = ("exact_page", "exact_cells", "exact_spans", "owned_values", "owned_words", "false_positive_page")
EXPECTED_KEYS = ("kind", "truth_status", "binary_admission_eligible", "columns", "row_count", "wrap", "tables")


def _slices(rows: list[dict[str, Any]], kinds: dict[str, str]) -> dict[str, Score]:
    """Recompute per-kind slice sums over scored (non-ambiguous) rows."""
    totals: dict[str, Any] = {}
    for row in rows:
        kind = kinds.get(row["id"]) or row.get("kind") or "unknown"
        scores = row.get("scores") or {}
        if all(value is None for value in scores.values()):
            continue
        totals[f"{kind}.pages"] = totals.get(f"{kind}.pages", 0.0) + 1
        for name in SLICE_FIELDS:
            value = scores.get(name)
            totals[f"{kind}.{name}"] = totals.get(f"{kind}.{name}", 0.0) + float(value or 0)
    return totals


def _items(version: Path, targets: dict[str, dict[str, Any]]) -> list[Item]:
    manifest = read_json(version / "manifest.json")
    items = []
    for case in manifest.get("cases", []):
        target = targets.get(case["id"], {})
        items.append(
            Item(
                key=case["id"],
                input={
                    "case": case["id"],
                    "pdf": ref(version / case.get("pdf_path", f"pdfs/{case['id']}.pdf")),
                    "page_image": ref(version / f"{case['id']}.png"),
                },
                expected={key: target[key] for key in EXPECTED_KEYS if key in target} or None,
                metadata={"kind": target.get("kind"), "truth_status": target.get("truth_status")},
            )
        )
    return items


def _cohort_run(
    directory: Path,
    cohort: str,
    data: dict[str, Any],
    calls: dict[tuple[str, str], dict[str, Any]],
    kinds: dict[str, str],
) -> Run:
    model = cohort.rsplit("/", 1)[0]
    rows = []
    usd = 0.0
    for record in data.get("rows", []):
        call = calls.get((model, record["id"]), {})
        cost = call.get("cost") or {}
        usage = call.get("usage") or {}
        answer = call.get("answer") or {}
        usd += float(cost.get("effective_usd") or 0)
        elapsed = call.get("http_elapsed_ms")
        scored = record.get("truth_status") != "ambiguous-unscored"
        rows.append(
            Row(
                item_key=record["id"],
                output={
                    "selection": record.get("selection"),
                    "probabilities": answer.get("probabilities"),
                    "owned_source_ids": record.get("owned_source_ids"),
                    "unresolved_source_ids": record.get("unresolved_source_ids"),
                },
                scores={
                    **numeric(record.get("scores")),
                    "source_conservation": record.get("conservation"),
                    "owned_source_ids": record.get("owned_source_ids"),
                    "unresolved_source_ids": record.get("unresolved_source_ids"),
                    "effective_usd": cost.get("effective_usd"),
                },
                metadata={
                    "status": call.get("status", "missing-call"),
                    "kind": kinds.get(record["id"], record.get("kind")),
                    "truth_status": record.get("truth_status"),
                    "scored": scored,
                    "model": model,
                    "served_model": (call.get("entry") or {}).get("served_model"),
                    "provider": (call.get("entry") or {}).get("provider"),
                    "cost_basis": cost.get("basis"),
                    "provider_reported_usd": cost.get("reported_usd"),
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "http_elapsed_ms": elapsed,
                    "request_sha256": call.get("sha256"),
                    "replayed": call.get("replayed"),
                },
                wall_ms=elapsed if isinstance(elapsed, (int, float)) else None,
                name=f"{CORPUS}/{record['id']}/{cohort}",
            )
        )
    reported = numeric(data.get("slices"))
    reported |= {
        "pages": data.get("pages"),
        "ambiguous_unscored_pages": data.get("ambiguous_unscored_pages"),
        "native_zero_call_pages": data.get("native_zero_call_pages"),
        "effective_usd": usd,
    }
    return Run(
        name=f"{ARM} {cohort}",
        description=(
            f"Hosted rolling-candidate admission by {model} on the A002 image512 arm (frozen candidates; "
            "authored DEV silver; model confidence is not calibrated correctness)"
        ),
        rows=rows,
        metadata={
            "model": model,
            "arm": cohort.rsplit("/", 1)[-1],
            "run_directory": rel(directory),
            "tag_prefix": (read_json(directory / "evaluation.json").get("tag_prefix")),
            **check_metadata(compare(_slices(data.get("rows", []), kinds), numeric(data.get("slices")))),
        },
        scores=reported,
        started=mtime(directory / "hosted-results.json"),
    )


def _ceiling_runs(directory: Path, evaluation: dict[str, Any], kinds: dict[str, str]) -> list[Run]:
    by_variant: dict[str, list[dict[str, Any]]] = {}
    for record in evaluation.get("candidate_ceiling_rows", []):
        by_variant.setdefault(record["variant"], []).append(record)
    runs = []
    for variant, records in sorted(by_variant.items()):
        rows = [
            Row(
                item_key=record["id"],
                output={
                    "owned_source_ids": record.get("owned_source_ids"),
                    "unresolved_source_ids": record.get("unresolved_source_ids"),
                    "matched_text_groups": record.get("matched_text_groups"),
                    "expected_text_groups": record.get("expected_text_groups"),
                },
                scores={
                    **numeric(record.get("scores")),
                    "source_conservation": record.get("source_conservation"),
                    "text_group_exact": record.get("text_group_exact"),
                    "matched_text_groups": record.get("matched_text_groups"),
                },
                metadata={
                    "status": "complete",
                    "variant": variant,
                    "kind": kinds.get(record["id"], record.get("kind")),
                },
                name=f"{CORPUS}/{record['id']}/ceiling-{variant}",
            )
            for record in records
        ]
        runs.append(
            Run(
                name=f"{ARM} candidate-ceiling {variant}",
                description=(
                    f"Offline candidate ceiling for the frozen {variant!r} candidate: whether the candidate itself "
                    "matches the authored table (not an achieved selection)"
                ),
                rows=rows,
                metadata={"variant": variant, "run_directory": rel(directory), "summary_check": "not-retained"},
                scores=dict(_slices(records, kinds)),
                started=mtime(directory / "evaluation.json"),
            )
        )
    return runs


def collect(artifacts: Path) -> Iterable[Experiment]:
    """One dataset per realism corpus version with retained admission results."""
    root = guard(artifacts / CORPUS)
    for version in sorted(p for p in root.iterdir() if (p / "manifest.json").is_file()) if root.is_dir() else []:
        directory = version / ARM
        if not (directory / "evaluation.json").is_file():
            continue
        targets_path = version / "private-targets.json"
        targets = {row["id"]: row for row in read_json(targets_path)} if targets_path.is_file() else {}
        kinds = {key: str(value.get("kind")) for key, value in targets.items()}
        evaluation = read_json(directory / "evaluation.json")
        hosted_path = directory / "hosted-results.json"
        hosted = read_json(hosted_path) if hosted_path.is_file() else {}
        calls = {(call["model"], call["id"]): call for call in hosted.get("calls", [])}
        runs = [
            _cohort_run(directory, cohort, data, calls, kinds) for cohort, data in evaluation.get("cohorts", {}).items()
        ]
        runs.extend(_ceiling_runs(directory, evaluation, kinds))
        yield Experiment(
            dataset=f"exp/{CORPUS}/{version.name}/{ARM}",
            description=(
                "Silver-realism-v2 DEV pages (16 borderless, 8 prose, 4 ambiguous-unscored). Runs: hosted "
                "rolling-candidate admission per model and offline candidate ceilings. Authored DEV silver."
            ),
            items=_items(version, targets),
            runs=runs,
            source=rel(directory),
            labels={
                "split": "DEV",
                "heldout": False,
                **scalars({"effective_usd": evaluation.get("effective_usd")}),
                "unknown_cost_requests": evaluation.get("unknown_cost_requests"),
            },
        )
