"""CPU-only DEV analysis of fixed, predeclared native-model combination rules.

All model outputs must pass remote_report before scorer references enter this
analysis. Rules depend only on model labels, never references or source IDs.
No provider, credential, GPU or inference operation is exposed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import time
from collections import Counter
from pathlib import Path
from typing import Any, NoReturn

MODELS = {
    "intern": "internlm/Intern-Decision-4B",
    "flash": "Cloudflare/clef-flash",
    "pplx": "perplexity-ai/pplx-decider-v1.1-27b",
    "clef": "Cloudflare/clef",
    "qwen4": "Qwen/Qwen3.5-4B",
}
POLICIES = {
    "unanimity3": ("intern", "flash", "pplx"),
    "majority3": ("intern", "flash", "pplx"),
    "flash_pplx_consensus": ("flash", "pplx"),
    "intern_flash_consensus": ("intern", "flash"),
}
ARMS = ("fresh-rgb-512", "fresh-rgb-768", "fresh-rgb-1024")
CHOICES = {"join", "split", "unresolved"}
MAX_JSON_BYTES = 16 * 1024 * 1024
MAJORITY = 2


def _fail(message: str) -> NoReturn:
    raise ValueError(message)


def _path(path: str | Path) -> Path:
    path = Path(path)
    if {"heldout-silver", "silver-heldout-v1"} & set(path.parts):
        _fail("Combination analysis refuses protected held-out paths")
    resolved = path.resolve()
    if {"heldout-silver", "silver-heldout-v1"} & set(resolved.parts):
        _fail("Combination analysis refuses protected held-out paths")
    return resolved


def _read(path: Path) -> bytes:
    path = _path(path)
    if path.stat().st_size > MAX_JSON_BYTES:
        _fail("Combination artifact exceeds byte admission")
    with path.open("rb") as handle:
        raw = handle.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        _fail("Combination artifact exceeds byte admission")
    return raw


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _seconds(value: Any) -> float | None:  # noqa: ANN401
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        return None
    return float(value)


def combine(policy: str, labels: dict[str, str]) -> str:
    """Apply a fixed label-only rule; unresolved is a vote and ties abstain."""
    if policy not in POLICIES:
        _fail("Unknown predeclared combination rule")
    values = [labels[model] for model in POLICIES[policy]]
    if any(value not in CHOICES for value in values):
        _fail("Combination received an invalid model label")
    if policy == "majority3":
        winner, count = Counter(values).most_common(1)[0]
        return winner if count >= MAJORITY else "unresolved"
    return values[0] if len(set(values)) == 1 else "unresolved"


def _metric(name: str, members: tuple[str, ...], rows: list[dict[str, Any]], *, policy: bool) -> dict[str, Any]:
    choices = [combine(name, row["labels"]) if policy else row["labels"][name] for row in rows]
    known = [(row, choice) for row, choice in zip(rows, choices, strict=True) if row["expected"] != "unresolved"]
    ambiguous = [(row, choice) for row, choice in zip(rows, choices, strict=True) if row["expected"] == "unresolved"]
    durations = [row["durations"][model] for row in rows for model in members]
    measured = all(value is not None for value in durations)
    serial = sum(durations) if measured else None
    return {
        "name": name,
        "members": list(members),
        "inputs": len(rows),
        "known_denominator": len(known),
        "ambiguous_denominator": len(ambiguous),
        "known_correct": sum(choice == row["expected"] for row, choice in known),
        "wrong_known_decisions": sum(choice != row["expected"] and choice != "unresolved" for row, choice in known),
        "known_abstentions": sum(choice == "unresolved" for _, choice in known),
        "ambiguous_abstentions": sum(choice == "unresolved" for _, choice in ambiguous),
        "ambiguous_decisions": sum(choice != "unresolved" for _, choice in ambiguous),
        "calls_per_page_input": len(members),
        "inference_calls": len(rows) * len(members),
        "measured_serial_latency_sum_seconds": serial,
        "measured_serial_mean_seconds_per_page_input": serial / len(rows) if serial is not None and rows else None,
        "cost_usd": None,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:  # noqa: C901
    """Score verified matched labels; the oracle union is only an unattainable ceiling."""
    if not rows or len({row["id"] for row in rows}) != len(rows):
        _fail("Combination matrix needs nonempty unique matched input IDs")
    for row in rows:
        if (
            row["arm"] not in ARMS
            or row["expected"] not in CHOICES
            or set(row["labels"]) != set(MODELS)
            or set(row["durations"]) != set(MODELS)
            or any(choice not in CHOICES for choice in row["labels"].values())
        ):
            _fail("Combination matrix differs from the fixed model/choice/arm inventory")
        row["durations"] = {model: _seconds(value) for model, value in row["durations"].items()}
    metrics: list[dict[str, Any]] = []
    complementarity: list[dict[str, Any]] = []
    for arm in (*ARMS, "all-rgb"):
        selected = [row for row in rows if arm == "all-rgb" or row["arm"] == arm]
        metrics.extend(dict(arm=arm, **_metric(name, (name,), selected, policy=False)) for name in MODELS)
        metrics.extend(
            dict(arm=arm, **_metric(name, members, selected, policy=True)) for name, members in POLICIES.items()
        )
        trio = POLICIES["unanimity3"]
        known = [row for row in selected if row["expected"] != "unresolved"]
        ambiguous = [row for row in selected if row["expected"] == "unresolved"]

        def disagrees(row: dict[str, Any], members: tuple[str, ...] = trio) -> bool:
            return len({row["labels"][model] for model in members}) > 1

        complementarity.append(
            {
                "arm": arm,
                "known_inputs": len(known),
                "ambiguous_inputs": len(ambiguous),
                "known_disagreements": sum(disagrees(row) for row in known),
                "ambiguous_disagreements": sum(disagrees(row) for row in ambiguous),
                "trio_shared_wrong_known": sum(
                    not disagrees(row) and row["labels"][trio[0]] not in {row["expected"], "unresolved"}
                    for row in known
                ),
                "trio_shared_ambiguous_decisions": sum(
                    not disagrees(row) and row["labels"][trio[0]] != "unresolved" for row in ambiguous
                ),
                "oracle_union_known_correct_trio": sum(
                    any(row["labels"][model] == row["expected"] for model in trio) for row in known
                ),
                "oracle_union_known_correct_all5": sum(
                    any(choice == row["expected"] for choice in row["labels"].values()) for row in known
                ),
                "oracle_semantics": "unattainable reference-based ceiling; not an executable selector or "
                "benchmark score",
            }
        )
    logical: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        logical.setdefault(row.get("page_id", row["id"]), []).append(row)
    shared_known, shared_ambiguous = [], []
    for page_id, treatments in logical.items():
        if len({row["expected"] for row in treatments}) != 1:
            _fail("Scorer expected relation differs across matched size treatments")
        if treatments[0]["expected"] != "unresolved":
            if all(
                all(label not in {row["expected"], "unresolved"} for label in row["labels"].values())
                for row in treatments
            ):
                shared_known.append(page_id)
        elif all(
            len({row["labels"][model] for model in POLICIES["unanimity3"]}) == 1
            and row["labels"]["intern"] != "unresolved"
            for row in treatments
        ):
            shared_ambiguous.append(page_id)
    return {
        "metrics": metrics,
        "complementarity": complementarity,
        "matched_inputs": len(rows),
        "logical_inputs": len(logical),
        "priority_groups": {
            "shared_known_wrong_all5_all_sizes": shared_known,
            "shared_decisive_ambiguity_trio_all_sizes": shared_ambiguous,
            "semantics": "diagnostic review groups only; never a selector or model-input change",
        },
    }


def evaluate(source_dir: Path, source_index: Path, outputs: Path, packets: Path) -> dict[str, Any]:
    """Verify each completed run with the approved DEV scorer before combining."""
    # This is the sole reference-access mechanism. No direct target-file reads.
    from bench import remote_report  # noqa: PLC0415

    started, cpu = time.perf_counter(), time.process_time()
    source_dir, source_index, outputs, packets = map(_path, (source_dir, source_index, outputs, packets))
    index_raw = _read(source_index)
    index = json.loads(index_raw)
    selected = [row for row in index if row["arm"] in ARMS]
    pages_by_arm = {arm: {row["page_ids"][0] for row in selected if row["arm"] == arm} for arm in ARMS}
    if not selected or any(pages != pages_by_arm[ARMS[0]] for pages in pages_by_arm.values()):
        _fail("RGB resolutions must contain the same complete source-page inventory")
    ids = {row["id"] for row in selected}
    if len(ids) != len(selected) or any(
        sum(row["arm"] == arm for row in selected) != len(pages) for arm, pages in pages_by_arm.items()
    ):
        _fail("RGB matrix has duplicate IDs or duplicate/missing source-page treatments")
    evaluations, timings, provenance = {}, {}, {}
    for name, model in MODELS.items():
        directory = _path(outputs / (name + "-l015"))
        attempts_raw, status_raw = _read(directory / "attempts.jsonl"), _read(directory / "status.json")
        verified = remote_report.evaluate(source_dir, source_index, directory, model=model, packets=packets)
        if verified["checkpoint"] or verified["incomplete_final_log_line"]:
            _fail("Combination analysis requires completed verified runs")
        if _read(directory / "attempts.jsonl") != attempts_raw or _read(directory / "status.json") != status_raw:
            _fail("Completed worker artifacts changed during scoring")
        answers = {row["id"]: row for row in verified["results"] if row["id"] in ids}
        if set(answers) != ids or any(row["status"] != "ok" for row in answers.values()):
            _fail("A selected RGB model output is missing or invalid; no quality exclusions")
        evaluations[name] = answers
        timings[name] = {
            event["id"]: _seconds(event.get("inference_wall_seconds"))
            for event in map(json.loads, attempts_raw.splitlines())
            if event.get("event") == "attempt_completed" and event["id"] in ids
        }
        if set(timings[name]) != ids:
            _fail("Selected RGB timing inventory differs from verified completions")
        provenance[name] = {
            "model": model,
            "attempts_sha256": _hash(attempts_raw),
            "status_sha256": _hash(status_raw),
            "source_manifest_sha256": verified["source_manifest_sha256"],
            "source_index_sha256": verified["source_index_sha256"],
            "worker_status": verified["worker_status"]["status"],
        }
    rows = []
    for entry in selected:
        expected = {evaluations[model][entry["id"]]["score"]["expected"] for model in MODELS}
        if len(expected) != 1:
            _fail("Approved scorer references disagree across model runs")
        rows.append(
            {
                "id": entry["id"],
                "page_id": entry["page_ids"][0],
                "arm": entry["arm"],
                "expected": expected.pop(),
                "labels": {model: evaluations[model][entry["id"]]["parsed"]["choice"] for model in MODELS},
                "durations": {model: timings[model][entry["id"]] for model in MODELS},
            }
        )
    report = summarize(rows)
    report.update(
        {
            "schema": 1,
            "scope": "fixed DEV supplied-region label combinations; no inference, prompt tuning or "
            "full-page reconstruction",
            "policies": {name: list(members) for name, members in POLICIES.items()},
            "inputs_sha256": _hash(index_raw),
            "packets_sha256": _hash(_read(packets)),
            "approved_scorer_sha256": _hash(_read(Path(remote_report.__file__))),
            "provenance": provenance,
            "rows": rows,
            "resources": {
                "analysis_wall_seconds": time.perf_counter() - started,
                "analysis_cpu_seconds": time.process_time() - cpu,
                "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                "scope": "one local CPU scoring process; perf_counter/process_time and Linux getrusage "
                "lifetime RSS high-water mark, no sampling; remote model resources/costs not inferred",
            },
            "latency_scope": "sum of retained per-call worker inference_wall_seconds; serial "
            "composition estimate, excludes startup/download/idle/teardown",
            "cost_scope": "unknown; no exact per-model/fleet-cost allocation supplied",
            "oracle_semantics": "unattainable reference-based ceiling only",
        }
    )
    return report


def markdown(report: dict[str, Any]) -> str:
    """Render fixed-policy tradeoffs and uncertainty without a trained-selector claim."""
    lines = [
        "# Fixed remote DEV decision combinations",
        "",
        (
            "R001 matched RGB512/768/1024, 24 authored source pages per size: 16 known relations and 8 "
            "ambiguous relations. "
            "All five native/stock runs passed the approved DEV scorer before combination. These are supplied-region "
            "decisions, not complete PDF extraction."
        ),
        "",
        (
            "Rules were declared before this analysis: Intern+Flash+PPLX unanimity or unresolved; three-vote majority "
            "including unresolved, with three-way ties unresolved; Flash then PPLX agreement or unresolved; and "
            "Intern+Flash agreement or unresolved. Both agreement rules pay both calls on every input."
        ),
        "",
        (
            "| Size | Rule/model | Known correct /16 | Wrong known | Known abstentions | Ambiguous "
            "abstentions /8 | Calls/input | Serial sum s | Mean s/input |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["metrics"]:
        if row["arm"] == "all-rgb":
            continue
        total = row["measured_serial_latency_sum_seconds"]
        mean = row["measured_serial_mean_seconds_per_page_input"]
        total_text = f"{total:.3f}" if total is not None else "unmeasured"
        mean_text = f"{mean:.3f}" if mean is not None else "unmeasured"
        lines.append(
            f"| {row['arm'].rsplit('-', 1)[1]} | {row['name']} | {row['known_correct']} | "
            f"{row['wrong_known_decisions']} | {row['known_abstentions']} | {row['ambiguous_abstentions']} | "
            f"{row['calls_per_page_input']} | {total_text} | {mean_text} |"
        )
    lines.extend(
        [
            "",
            (
                "Latency sums use retained measured inference durations. They estimate serial composition of existing "
                "calls; no ensemble was freshly timed. Initialization, downloads, idle time, fleet provisioning and "
                "teardown are excluded. Local GPU resources are available in original worker reports but are not "
                "combined into a hypothetical fleet profile. Costs and pages/USD remain unknown."
            ),
            "",
            (
                "| Size | Known disagreements | Ambiguous disagreements caught | Shared wrong known | "
                "Shared decisive ambiguity missed | Oracle union known /16: trio | Oracle union known /16: all five |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report["complementarity"]:
        if row["arm"] != "all-rgb":
            lines.append(  # noqa: PERF401
                f"| {row['arm'].rsplit('-', 1)[1]} | {row['known_disagreements']} | {row['ambiguous_disagreements']} | "
                f"{row['trio_shared_wrong_known']} | {row['trio_shared_ambiguous_decisions']} | "
                f"{row['oracle_union_known_correct_trio']} | {row['oracle_union_known_correct_all5']} |"
            )
    lines.extend(["", "The fixed rules expose the following tradeoffs:", ""])
    for arm in ARMS:
        matrix = {row["name"]: row for row in report["metrics"] if row["arm"] == arm}
        consensus, majority = matrix["unanimity3"], matrix["majority3"]
        cheap, intern_pair = matrix["flash_pplx_consensus"], matrix["intern_flash_consensus"]
        best = max(matrix[model]["known_correct"] for model in MODELS)
        lines.append(
            f"- {arm.rsplit('-', 1)[1]}: unanimity retains {consensus['known_correct']} known correct "
            f"decisions versus the best single model's {best}, with {consensus['wrong_known_decisions']} wrong "
            f"known decisions and {consensus['known_abstentions']} known abstentions. Majority gives "
            f"{majority['known_correct']} known correct and {majority['ambiguous_abstentions']} ambiguous "
            f"abstentions. Flash+PPLX catches {cheap['ambiguous_abstentions']} ambiguous cases; "
            f"Intern+Flash catches {intern_pair['ambiguous_abstentions']} at the serial latency shown above."
        )
    priorities = report["priority_groups"]
    lines.extend(
        [
            "",
            (
                "Agreement leaves correlated decisive errors. Disagreement is therefore an incomplete sufficiency "
                "gate; fewer wrong decisions must be read alongside lost correct decisions and remaining decisive "
                "ambiguous answers. Majority does not provide an automatic abstention benefit. Adding models to an "
                "oracle "
                "union does not establish an executable routing policy."
            ),
            "",
            "The following diagnostic priorities preserve original packets and use no source-ID routing:",
            "",
            (
                f"1. Review the {len(priorities['shared_known_wrong_all5_all_sizes'])} known cases wrong across "
                "all five models and all sizes for clipped or missing structural evidence and limits of the "
                "supplied-region assembly contract. Keep original references and inputs; do not write case-specific "
                "prompt fixes."
            ),
            (
                f"2. The {len(priorities['shared_decisive_ambiguity_trio_all_sizes'])} ambiguous cases with stable "
                "decisive trio agreement justify fresh, independent DEV sufficiency controls. Evaluate the blinded "
                "generic prompt screen across its whole cohort; selecting only these misses would bias the comparison."
            ),
            (
                "3. Test an independently frozen architecture or cheap gate under identical evidence and wording. More "
                "pixels or another correlated model is a hypothesis to test, not a demonstrated remedy. Review groups "
                "are diagnostic observations, not a trained policy or inputs for models."
            ),
        ]
    )
    lines.extend(
        [
            "",
            (
                "Oracle unions use references to identify any correct model and are unattainable ceilings, "
                "not executable "
                "selectors or reported quality scores. The 72 RGB treatments reuse 24 logical pages; pooled counts are "
                "correlated size treatments, not 72 independent cases. No protected held-out set was accessed."
            ),
            "",
            (
                "Reproduce locally with `python -m bench.remote_combinations --source-dir <L015 freeze> --source-index "
                "<R001 source-index.json> --outputs <R001 outputs> --packets <R001 packets/manifest.json> "
                "--markdown bench/results/remote-gpu-combinations.md --json <ignored evaluation path>`. "
                "The command verifies hashes and scores DEV references through `bench.remote_report`; it "
                "makes no inference calls."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """Evaluate only retained DEV artifacts and write explicit output reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-dir", "source-index", "outputs", "packets", "markdown", "json"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = vars(parser.parse_args())
    md_path, json_path = _path(args.pop("markdown")), _path(args.pop("json"))
    report = evaluate(**args)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown(report))
    json_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
