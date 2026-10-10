"""Independent same-model continuation provenance, snapshot accounting and full-DEV scoring."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415
from __future__ import annotations

import json
import math
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from bench.generalization_report import load_corpus
from bench.p003_report import score_run, strict_scores
from bench.silver import guard_path, sha


def read(path: Path) -> Any:  # noqa: ANN401
    """Read explicitly supplied guarded files, never live financial or credential stores."""
    return json.loads(guard_path(path).read_bytes())


def close(a: Any, b: Any) -> bool:  # noqa: ANN401
    """Compare finite accounting sums without accepting booleans or absent totals."""
    return (
        type(a) in (int, float)
        and type(b) in (int, float)
        and math.isfinite(a)
        and math.isfinite(b)
        and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
    )


def verify_measurements(
    directory: Path, specs: list[dict[str, Any]], reports: list[dict[str, Any] | None]
) -> dict[str, Any]:
    """Reproduce exact-prefix costs and supervisor intervals from immutable captured snapshots."""
    from bench.p003_boundary_run import _charges

    ledger_path = directory / "ledger.json"
    ledger_hash = sha(ledger_path.read_bytes())
    ledger = read(ledger_path)
    entries, segments, seen = [], [], set()
    for index, (spec, report) in enumerate(zip(specs, reports, strict=True)):
        measured = spec["measurement"]
        costs_path, queue_path = directory / f"costs-{index}.json", directory / f"queue-{index}.json"
        if (
            sha(costs_path.read_bytes()) != measured["cost_receipt_sha256"]
            or sha(queue_path.read_bytes()) != measured["queue_status_sha256"]
            or ledger_hash != measured["ledger_sha256"]
            or guard_path(Path(measured["cost_receipt"])) != costs_path
        ):
            raise ValueError("Continuation measurement snapshot/hash differs")
        config = read(Path(spec["directory"]) / "frozen.json")["config"]
        prefix = f"P003/{config['run_id']}/"
        attempt_rows = [e for e in ledger["requests"] if e.get("tag", "").startswith(prefix)]
        if any(type(e.get("index")) is not int or e["index"] in seen for e in attempt_rows):
            raise ValueError("Continuation costs repeat an attempt across segments")
        seen.update(e["index"] for e in attempt_rows)
        actual = read(costs_path)
        expected = _charges(attempt_rows)
        expected["cost_scope"] = (
            "All attempts in exact original segment tag prefix; includes failures and preserves all accounting bases."
        )
        for key, value in expected.items():
            if key == "entries":
                if actual[key] != value:
                    raise ValueError("Continuation snapshot costs omit or change exact-prefix attempts")
            elif isinstance(value, (float, int)):
                if not close(actual.get(key), value):
                    raise ValueError("Continuation cost counters/sums differ from snapshot")
            elif actual.get(key) != value:
                raise ValueError("Continuation cost bases differ from snapshot")
        if not close(measured["effective_usd"], expected["effective_usd"]) or not close(
            measured["accounted_usd"], expected["accounted_usd"]
        ):
            raise ValueError("Continuation measured cost differs from complete attempt accounting")
        arms = [a for a in read(queue_path)["arms"] if a["name"] == config["run_id"]]
        if len(arms) != 1 or not close(arms[0]["wall_seconds"], measured["metrics"]["wall_seconds"]):
            raise ValueError("Continuation supervisor segment interval differs")
        for key in ("cpu_seconds", "peak_sampled_rss_bytes"):
            expected_metric = report.get("metrics", {}).get(key) if report else None
            if measured["metrics"].get(key) != expected_metric:
                raise ValueError("Continuation resource measurement invents absent parent totals")
        entries.extend(attempt_rows)
        segments.append(
            {
                "run_id": config["run_id"],
                "ledger_attempts": len(attempt_rows),
                "effective_api_usd": expected["effective_usd"],
                "provider_reported_usd": expected["provider_reported_usd"],
                "metrics": measured["metrics"],
                "cost_receipt_sha256": measured["cost_receipt_sha256"],
                "queue_status_sha256": measured["queue_status_sha256"],
            }
        )
    totals = _charges(entries)
    totals["cost_scope"] = "All original and continuation attempts once per disjoint segment; failures included"
    return {
        "ledger_sha256": ledger_hash,
        "segments": segments,
        "all_attempt_costs": totals,
        "wall_seconds": sum(s["metrics"]["wall_seconds"] for s in segments),
        "aggregate_parent_cpu_seconds": None
        if any(s["metrics"]["cpu_seconds"] is None for s in segments)
        else sum(s["metrics"]["cpu_seconds"] for s in segments),
        "scope": "Captured all-attempt ledger plus measured supervisor intervals; "
        "absent stopped parent CPU/RSS stay unknown",
    }


def analyze(
    directory: Path, measurements: Path, corpus: Path, *, trusted_code: dict[str, str], continuation_helper_sha256: str
) -> dict[str, Any]:
    """Authenticate disjoint source-equivalent segments/proofs before scoring the entire original cohort."""
    from bench import p003_pipeline_continuation as continuation

    directory, measurements = guard_path(directory), guard_path(measurements)
    frozen, report = read(directory / "frozen.json"), read(directory / "report.json")
    if (
        frozen["continuation_helper_sha256"] != continuation_helper_sha256
        or sha(Path(continuation.__file__).read_bytes()) != continuation_helper_sha256
    ):
        raise ValueError("Continuation helper differs from independently Git-approved source")
    specs = read(measurements / "segments.json")
    for spec in specs:
        authority = read(Path(spec["trusted_code"]))
        segment_code = read(Path(spec["directory"]) / "frozen.json")["code_sha256"]
        if segment_code != frozen["code_sha256"] or any(
            authority.get(n) != d or trusted_code.get(n) != d for n, d in segment_code.items()
        ):
            raise ValueError("Segment code authority differs from independent original treatment map")
    for index, segment in enumerate(frozen["continuation_segments"]):
        for name, digest in segment["artifact_sha256"].items():
            relative = Path(name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or sha(guard_path(directory / "segments" / str(index) / relative).read_bytes()) != digest
            ):
                raise ValueError("Copied immutable segment archive differs from original attested bytes")
    if report["segment_measurements"] != [s["measurement"] for s in specs]:
        raise ValueError("Continuation report changes supplied measurements")
    # This pure helper checks same-model/config/code, original errors, no repeated
    # completed page, and exact never-admitted proof for request-only artifacts.
    with tempfile.TemporaryDirectory(prefix="p003-continuation-replay-", dir=directory.parent) as temp:
        rebuilt = Path(temp) / "run"
        replay = continuation.combine(specs, rebuilt)
        if replay != report or read(rebuilt / "frozen.json") != frozen:
            raise ValueError("Combined continuation differs from independent same-source replay")
        for prediction in replay["results"]:
            ident = prediction["id"]
            for path in rebuilt.glob(ident + "*"):
                if path.is_file() and path.read_bytes() != (directory / path.name).read_bytes():
                    raise ValueError("Combined page artifacts differ from immutable original segment bytes")
    reports = [
        read(Path(s["directory"]) / "report.json") if (Path(s["directory"]) / "report.json").exists() else None
        for s in specs
    ]
    measured = verify_measurements(measurements, specs, reports)
    if (
        not close(report["effective_usd"], measured["all_attempt_costs"]["effective_usd"])
        or not close(report["metrics"]["wall_seconds"], measured["wall_seconds"])
        or report["metrics"]["cpu_seconds"] != measured["aggregate_parent_cpu_seconds"]
    ):
        raise ValueError("Combined totals differ from verified captured measurements")
    scored = score_run(directory, corpus, trusted_code=trusted_code)
    manifest, targets = load_corpus(corpus)
    references = {p["id"]: p for p in targets["pages"]}
    predictions = {p["id"]: p for p in report["results"]}
    strata = defaultdict(list)
    for record in manifest["pages"]:
        strata["cohort/" + record["cohort"]].append(record["id"])
        strata["family/" + record["family"]].append(record["id"])
    stratified = {}
    for name, ids in strata.items():
        rows = [predictions[i] for i in ids]
        stratified[name] = {
            **strict_scores([references[i] for i in ids], rows),
            "attempted_pages": len(ids),
            "operational_pages": sum(p["status"] == "ok" for p in rows),
            "scope": "Existing manifest metadata subset; no subset cost or latency allocation",
        }
    useful, wall, cost = (
        scored["operational_pages"],
        measured["wall_seconds"],
        measured["all_attempt_costs"]["effective_usd"],
    )
    measured.update(
        operational_pages_per_minute=useful * 60 / wall if wall else None,
        operational_pages_per_api_usd=useful / cost if cost else None,
    )
    return {
        "runs": [scored],
        "metadata_strata": stratified,
        "verified_continuation_measurements": measured,
        "continuation_helper_sha256": continuation_helper_sha256,
        "measurement_specs_sha256": sha((measurements / "segments.json").read_bytes()),
        "same_model_only": True,
        "automatic_retries": False,
        "new_api_calls": 0,
    }
