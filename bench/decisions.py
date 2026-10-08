"""Opt-in hosted comparison of frozen PDF decisions; all document work is CPU-only."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from typing import TYPE_CHECKING, Any

from bench.decision_analysis import analyze, render_analysis
from bench.decision_cases import build_cases, write_cases
from bench.decision_choice import choice_request, parse_choice
from bench.decision_controls import build_controls, write_controls
from bench.decision_eval import evaluate, render_report
from bench.decision_hosted import (
    ARTIFACTS,
    JEV,
    MODELS,
    ROOT,
    DecisionClient,
    checkpoint,
    exclusive_lock,
    parse_answers,
    request_body,
)

if TYPE_CHECKING:
    from pathlib import Path

BATCH_SIZE = 6


def summarize_requests(entries: list[dict[str, Any]]) -> str:
    """Report unique network requests, without confusing batches with item latency."""
    lines = [
        "",
        "## Request accounting",
        "",
        "This table accounts for the entire campaign, including separately tagged controls and diagnostics.",
        "Latency is complete HTTP wall time. Batch time divided by items is serial amortization, not decision latency.",
        "Unknown charges retain a $0.30 reservation. No automatic retries. Cached replays add no requests.",
        "",
        "| Cohort | Requests | Items | Median HTTP ms | Total HTTP s | Accounted USD | Unsettled |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for tag in sorted({entry["tag"].rsplit("/", 1)[0] for entry in entries}):
        rows = [entry for entry in entries if entry["tag"].rsplit("/", 1)[0] == tag]
        times = [entry["elapsed_ms"] for entry in rows if "elapsed_ms" in entry]
        sizes = [entry.get("case_count", 0) for entry in rows]
        unsettled = sum(entry["cost_status"] != "provider-reported USD" for entry in rows)
        lines.append(
            f"| {tag} | {len(rows)} | {sum(sizes)} | {statistics.median(times) if times else 0:.1f} | "
            f"{sum(times) / 1000:.3f} | {sum(entry['accounted_usd'] for entry in rows):.6f} | {unsettled} |"
        )
    return "\n".join(lines) + "\n"


def save_report(cases: list[dict[str, Any]], predictions: list[dict[str, Any]], suffix: str = "") -> None:
    """Persist complete evaluation after each batch, retaining missing predictions."""
    report = evaluate(cases, predictions)
    if suffix:
        report["notes"][0] = "Small existing-PDF table/prose region study; no full-matrix or production-quality claim."
    ledger_path = ARTIFACTS / "ledger.json"
    entries = json.loads(ledger_path.read_text())["requests"] if ledger_path.exists() else []
    analysis = analyze(cases, predictions, report)
    report["analysis"] = analysis
    report["requests"] = entries
    report["provenance"] = {
        "cases_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
        "default_batch_size": BATCH_SIZE,
        "singleton_suffix": "-b1; absence means batch size six",
        "fixture_scope": (
            "Eight table/prose regions from six existing sources; no relationship or matrix gold."
            if suffix
            else "Authored synthetic fragments; disjoint templates, not independent real issuers."
        ),
    }
    checkpoint(
        ARTIFACTS / f"predictions{suffix}.json",
        {"predictions": predictions, "cases_sha256": report["provenance"]["cases_sha256"]},
    )
    checkpoint(ARTIFACTS / f"evaluation{suffix}.json", report)
    (ROOT / f"bench/results/decisions{suffix}-latest.md").write_text(
        render_report(report) + render_analysis(analysis) + summarize_requests(entries)
    )


def load_predictions(path: Path, evidence_path: Path, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reject stale case labels/evidence before overwriting the frozen manifest."""
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    digest = hashlib.sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest()
    if data.get("cases_sha256") == digest:
        return data["predictions"]
    if "cases_sha256" not in data and evidence_path.exists() and json.loads(evidence_path.read_text()) == cases:
        return data["predictions"]
    message = "Saved predictions do not match frozen evidence; use a separate campaign directory."
    raise ValueError(message)


def run(args: argparse.Namespace) -> None:  # noqa: C901, PLR0912 - explicit benchmark lifecycle
    """Run only explicitly requested models, preserving raw evidence and spend."""
    suffix = "-controls" if args.controls else ""
    cases = build_controls() if args.controls else build_cases()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    evidence_path = ARTIFACTS / ("controls" if args.controls else "cases") / "cases.json"
    prediction_path = ARTIFACTS / f"predictions{suffix}.json"
    predictions = load_predictions(prediction_path, evidence_path, cases)
    if args.controls:
        write_controls(ARTIFACTS / "controls")
    else:
        write_cases(ARTIFACTS / "cases")
    if args.report_only:
        save_report(cases, predictions, suffix)
        return
    client = DecisionClient()
    ordered = list(cases)
    random.Random(8132).shuffle(ordered)  # noqa: S311 - reproducible benchmark ordering
    if args.smoke:
        ordered = [case for case in ordered if case["split"] == "calibration"][:1]
    if args.single:
        ordered = [
            next(case for case in cases if case["split"] == "calibration" and case["task"] == task)
            for task in ("table", "wrap", "header", "assignment")
        ]
    size = 1 if args.single or args.smoke else args.batch_size
    cohort = "smoke" if args.smoke else "single" if args.single else "batch"
    for model in args.models:
        label = f"{model}@{args.variant}" + (
            f"-b{size}" if size != BATCH_SIZE and not args.smoke and not args.single else ""
        )
        for start in range(0, len(ordered), size):
            batch = ordered[start : start + size]
            body = choice_request(batch) if args.variant == "choice" else request_body(model, batch, args.variant)
            tag = f"{'controls/' if args.controls else ''}{label}/{cohort}/{start // size:03d}"
            print(
                f"Start {tag}: {len(batch)} items, {len(json.dumps(body, separators=(',', ':')).encode())} bytes",
                flush=True,
            )
            response = None
            try:
                response = client.request(body, tag=tag)
                answers = (
                    parse_choice(response["result"], len(batch))
                    if args.variant == "choice"
                    else parse_answers(model, response["result"], len(batch))
                )
                error = None
            except (RuntimeError, ValueError, KeyError, TypeError, IndexError) as exception:
                answers = []
                error = type(exception).__name__
                print(f"Failed {tag}: {error}; inspect retained artifacts before any retry", flush=True)
            if response:
                entry = response["entry"]
                print(
                    f"Done {tag}: {entry['elapsed_ms']:.0f} ms, ${entry['accounted_usd']:.6f}, "
                    f"replay={response['replayed']}",
                    flush=True,
                )
            if cohort == "batch":
                ids = {case["id"] for case in batch}
                predictions = [p for p in predictions if p["model"] != label or p["case_id"] not in ids]
                for index, case in enumerate(batch):
                    prediction = {
                        "case_id": case["id"],
                        "model": label,
                        "probability_kind": (
                            "conditional_choice_mass"
                            if args.variant == "choice"
                            else "native_decision_score"
                            if model == JEV
                            else "self_reported"
                        ),
                    }
                    if response:
                        prediction["request_index"] = response["entry"]["index"]
                    if error:
                        prediction["error"] = error
                    else:
                        prediction.update(answers[index])
                    predictions.append(prediction)
                save_report(cases, predictions, suffix)
            if error:
                break
    if cohort == "batch":
        save_report(cases, predictions, suffix)


def main() -> None:
    """Require --run-hosted for any metered request."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--single", action="store_true")
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--variant", choices=("rich", "text", "resolved", "resolved-text", "choice"), default="rich")
    parser.add_argument("--batch-size", type=int, choices=(1, 6), default=BATCH_SIZE)
    args = parser.parse_args()
    if not args.report_only and not args.run_hosted:
        parser.error("Use --run-hosted for paid inference, or --report-only for local evaluation.")
    if args.controls and (args.single or args.smoke):
        parser.error("Grounded controls are test-only; no calibration smoke selection is available.")
    if args.variant == "choice" and args.models != [JEV]:
        parser.error("Choice experiments require --models typesafe/jev-1.13")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(ARTIFACTS / "run.lock"):
        run(args)


if __name__ == "__main__":
    main()
