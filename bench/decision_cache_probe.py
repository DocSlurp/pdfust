"""Opt-in bounded actual resubmission probe; local replay is not provider caching.

Retained successful bodies are submitted once, then twice identically. A first
submission is not presumed cold, and repeated submission is not presumed cached.
Provider cache counters, actual charges and separate token estimates are retained.
"""

# Provider/ledger JSON and injected CPU-only fake clients are heterogeneous.
# ruff: noqa: ANN401, EM101, TRY003, PLR2004, ISC004, C901, PLR0912

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.decision_hosted import (
    ARTIFACTS,
    MAX_IMAGE_BODY_BYTES,
    RESERVATION,
    DecisionClient,
    accounted_cost,
    checkpoint,
    exclusive_lock,
)
from bench.reprice_model_rates import cache_usage, load, request_cost
from bench.silver import guard_path

MAX_MODELS = 4
MAX_CONDITIONS = 2
TRIALS = 3
MAX_CALLS = MAX_MODELS * MAX_CONDITIONS * TRIALS
WAVE_LIMIT = 0.50


def body_sha(body: dict[str, Any]) -> str:
    """Match the hosted client's exact insertion-order JSON request identity."""
    return hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest()


def successful(result: dict[str, Any]) -> bool:
    """Exclude retained HTTP/provider errors, even when an HTTP200 response exists."""
    return (
        bool(result)
        and not result.get("error")
        and all(
            not choice.get("error") and choice.get("finish_reason") != "error" for choice in result.get("choices", [])
        )
    )


def manifest_records(manifest_path: Path) -> list[dict[str, Any]]:
    """Read either individual or batched frozen DEV request metadata."""
    manifest = load(manifest_path)
    if manifest.get("split", "DEV") != "DEV":
        raise ValueError("Cache probe manifest must remain DEV")
    records = manifest.get("records", manifest.get("batches"))
    if not isinstance(records, list):
        raise TypeError("Cache probe manifest requires records or batches")
    return records


def manifest_request_path(manifest_path: Path, record: dict[str, Any]) -> Path:
    """Resolve batched filenames and legacy paths without permitting filename traversal."""
    if "request_file" in record:
        name = Path(record["request_file"])
        if name.name != str(name):
            raise ValueError("Batched request_file must be a filename within its manifest directory")
        return guard_path(manifest_path.parent / name)
    path = Path(record["request_path"])
    if not path.is_absolute():
        path = path if path.exists() else manifest_path.parent / path
    return guard_path(path)


def select_requests(manifest_path: Path, directory: Path = ARTIFACTS) -> list[Path]:
    """Select successful frozen conditions per model, preferring actual1200/128 RGB8 images."""
    records = manifest_records(manifest_path)
    ledger = load(directory / "ledger.json")["requests"]
    retained: dict[str, list[dict[str, Any]]] = {}
    for entry in ledger:
        if entry.get("response_file"):
            retained.setdefault(entry["request_sha256"], []).append(entry)

    def config(record: dict[str, Any]) -> dict[str, Any]:
        return record.get("configuration") or record

    def priority(record: dict[str, Any]) -> tuple[int, int]:
        settings = config(record)
        actual_rgb = settings.get("mode") == "rgb8" and not settings.get("blank")
        edge = settings.get("edge")
        preferred = 0 if actual_rgb and edge == 1200 else 1 if actual_rgb and edge == 128 else 2
        return preferred, int(bool(settings.get("blank")))

    ordered = sorted(records, key=priority)
    chosen: dict[str, list[Path]] = {}
    conditions: dict[str, set[str]] = {}
    for record in ordered:
        model = record["model"]
        entries = retained.get(record["request_sha256"], [])
        if not entries:
            continue
        if model not in chosen and len(chosen) >= MAX_MODELS:
            continue
        group = chosen.get(model, [])
        condition = json.dumps(
            {key: config(record).get(key) for key in ("edge", "mode", "blank", "scope")}, sort_keys=True
        )
        if len(group) >= MAX_CONDITIONS or condition in conditions.get(model, set()):
            continue
        accepted = False
        for entry in entries:
            filename = Path(entry["response_file"])
            if filename.name != str(filename):
                raise ValueError("Retained response must stay within ledger directory")
            accepted = accepted or successful(load(directory / filename))
        if not accepted:
            continue
        path = manifest_request_path(manifest_path, record)
        if body_sha(load(path)) != record["request_sha256"]:
            raise ValueError("Frozen manifest request hash disagrees with selected body")
        chosen.setdefault(model, []).append(path)
        conditions.setdefault(model, set()).add(condition)
    return [path for paths in chosen.values() for path in paths]


def prepare_requests(paths: list[Path], directory: Path, *, manifest_path: Path | None = None) -> list[dict[str, Any]]:
    """Validate selected immutable request bodies against retained successful responses."""
    if not paths or len(paths) > MAX_MODELS * MAX_CONDITIONS:
        raise ValueError("Select1–8 retained successful request bodies")
    ledger = load(directory / "ledger.json")["requests"]
    metadata = {record["request_sha256"]: record for record in manifest_records(manifest_path)} if manifest_path else {}
    prepared = []
    identities: set[str] = set()
    models: Counter[str] = Counter()
    for source_path in paths:
        path = guard_path(source_path)
        body = load(path)
        identity = body_sha(body)
        if identity in identities:
            raise ValueError("Conditions must have distinct bodies; trials repeat each selected body")
        identities.add(identity)
        model = body["model"]
        models[model] += 1
        if len(models) > MAX_MODELS or models[model] > MAX_CONDITIONS:
            raise ValueError("Probe permits at most4models and2conditions per model")
        if len(json.dumps(body, separators=(",", ":")).encode()) > MAX_IMAGE_BODY_BYTES:
            raise ValueError("Retained body exceeds bounded image request admission")
        previous = [entry for entry in ledger if entry.get("request_sha256") == identity and entry.get("response_file")]
        accepted = []
        for entry in previous:
            filename = Path(entry["response_file"])
            if filename.name != str(filename):
                raise ValueError("Retained response must stay within ledger directory")
            if successful(load(directory / filename)):
                accepted.append(entry)
        if not accepted:
            raise ValueError("Each probe body must already have a retained successful provider response")
        prepared.append(
            {
                "request_path": str(path),
                "request_sha256": identity,
                "model": model,
                "condition": f"condition-{models[model]}",
                "original_index": accepted[0]["index"],
                "body": body,
            }
        )
        if identity in metadata:
            record = metadata[identity]
            if record["model"] != model:
                raise ValueError("Frozen batch model differs from selected request")
            prepared[-1]["batch_metadata"] = {
                key: record[key]
                for key in (
                    "configuration",
                    "scope",
                    "arm",
                    "offset",
                    "case_indices",
                    "case_ids",
                    "source_sha256",
                    "request_bytes",
                )
                if key in record
            }
            prepared[-1]["condition"] = record.get("arm", prepared[-1]["condition"])
    return prepared


def admission(ledger: dict[str, Any], start_index: int) -> None:
    """Reserve within both the persistent24-call and$0.50 extra-wave boundaries."""
    entries = ledger["requests"][start_index:]
    if (
        len(entries) >= MAX_CALLS
        or sum(accounted_cost(row["accounted_usd"]) for row in entries) + RESERVATION > WAVE_LIMIT
    ):
        raise RuntimeError("Cache probe extra-wave call or reservation budget exhausted")


def trial_record(
    prepared: dict[str, Any], trial: int, response: dict[str, Any], price: dict[str, Any]
) -> dict[str, Any]:
    """Retain observed counters, charges and latency without inventing cache temperature."""
    entry, result = response["entry"], response["result"]
    usage = result.get("usage") or {}
    pricing = request_cost(entry, usage, price)
    reference_usage = {key: value for key, value in usage.items() if key != "cost"}
    token_reference = request_cost({**entry, "cost_status": "reserved", "accounted_usd": 0}, reference_usage, price)
    return {
        "model": prepared["model"],
        "condition": prepared["condition"],
        "trial": trial,
        "submission": "first" if trial == 0 else f"repeat-{trial}",
        "request_sha256": prepared["request_sha256"],
        "original_index": prepared["original_index"],
        "status": "ok" if successful(result) else "provider-error",
        "entry": entry,
        "served_model": result.get("model"),
        "provider": result.get("provider", entry.get("provider")),
        "usage": usage,
        **cache_usage(usage),
        "provider_reported_usd": usage.get("cost"),
        "effective_pricing": pricing,
        "catalog_token_estimate": token_reference,
        "elapsed_ms": entry.get("elapsed_ms"),
        "local_replayed": response.get("replayed", False),
        "batch_metadata": prepared.get("batch_metadata"),
        "case_count": entry.get("case_count"),
    }


def report(state: dict[str, Any], path: Path) -> None:
    """Write a compact first-versus-repeat report with uncertainty visible."""
    lines = [
        "# Actual resubmission cache probe",
        "",
        "Identical actual provider requests; no automatic retries. "
        "Local retained-response replay is a separate zero-call mechanism and is not provider caching. "
        "First/repeat order does not establish cold/warm cache state. Only returned cache counters support "
        "a cache-use observation. Missing counters leave cache status unverified. Positive provider charges "
        "take precedence; token estimates use published component rates, with missing cache prices unknown.",
        "",
        "| Model | Condition | Submission | Status | Provider | Read tokens | Write tokens | Reported USD | "
        "Effective USD | Token estimate USD | HTTP ms |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in state["records"]:
        pricing = row.get("effective_pricing", {})
        estimate = row.get("catalog_token_estimate", {})
        cells = [
            row["model"],
            row["condition"],
            row["submission"],
            row["status"],
            row.get("provider") or "unknown",
            row.get("cache_read_tokens"),
            row.get("cache_write_tokens"),
            row.get("provider_reported_usd"),
            pricing.get("effective_usd"),
            estimate.get("effective_usd"),
            row.get("elapsed_ms"),
        ]
        lines.append("| " + " | ".join("unknown" if value is None else str(value) for value in cells) + " |")
    lines += [
        "",
        "Catalog token estimates are comparisons, not newly observed charges. Missing cache counters "
        "assume zero for absent components with an explicitly unverified uncached assumption; observed "
        "cache counters without matching published cache prices produce an unknown total. Raw usage, "
        "ledger entries, fallback assumptions and component prices remain in the adjacent results JSON.",
        "",
        f"Extra-wave ceiling: ${WAVE_LIMIT:.2f}; at most{MAX_CALLS} actual calls,4models,2conditions/model, "
        "three submissions/condition. The shared client's cumulative$15 ceiling and reservation ledger also apply.",
        "",
    ]
    path.write_text("\n".join(lines))


def run_probe(  # noqa: PLR0913 - explicit hosted opt-in, fake-client injection and optional frozen metadata.
    paths: list[Path],
    output: Path,
    *,
    hosted: bool = False,
    directory: Path = ARTIFACTS,
    client: Any = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Prepare offline by default; actual resubmissions require explicit hosted opt-in."""
    directory, output = guard_path(directory), guard_path(output)
    prepared = prepare_requests(paths, directory, manifest_path=manifest_path)
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / "results.json"
    plan = [{key: value for key, value in item.items() if key != "body"} for item in prepared]
    if not hosted:
        state: dict[str, Any] = {"schema": 1, "status": "prepared; no provider calls", "plan": plan, "records": []}
        checkpoint(output / "plan.json", state)
        return state
    with exclusive_lock(directory / "run.lock"):
        ledger = load(directory / "ledger.json")
        wave_path = directory / "cache-probe-wave.json"
        if wave_path.exists():
            wave = load(wave_path)
            if wave["plan"] != plan:
                raise ValueError("Existing cache wave has another frozen plan; changing output cannot reset its cap")
        else:
            wave = {
                "schema": 1,
                "plan": plan,
                "wave_start_index": len(ledger["requests"]),
                "limit_usd": WAVE_LIMIT,
                "maximum_calls": MAX_CALLS,
                "records": [],
            }
            checkpoint(wave_path, wave)
        if state_path.exists():
            state = load(state_path)
            if state["plan"] != plan:
                raise ValueError("Existing probe plan differs; use another output directory")
        else:
            state = {
                "schema": 1,
                "status": "running",
                "created_at": time.time(),
                "plan": plan,
                "wave_start_index": wave["wave_start_index"],
                "records": list(wave.get("records", [])),
            }
            checkpoint(state_path, state)
        if len(wave.get("records", [])) > len(state["records"]):
            state["records"] = list(wave["records"])
        prices = load(directory / "langfuse/catalog-prices.json")
        state["catalog_fetched_at"] = prices.get("fetched_at")
        state["cache_pricing_fetched_at"] = prices.get("cache_pricing_fetched_at")
        state["cache_pricing_source"] = prices.get("cache_pricing_source")
        state["catalog_sha256"] = hashlib.sha256((directory / "langfuse/catalog-prices.json").read_bytes()).hexdigest()
        probe_client = client if client is not None else DecisionClient()
        failed_models = {row["model"] for row in state["records"] if row["status"] != "ok"}
        completed = {(row["request_sha256"], row["trial"]) for row in state["records"]}
        for item in prepared:
            if item["model"] in failed_models:
                continue
            for trial in range(TRIALS):
                if (item["request_sha256"], trial) in completed:
                    continue
                try:
                    current_ledger = load(directory / "ledger.json")
                    admission(current_ledger, state["wave_start_index"])
                except RuntimeError as exc:
                    state.update(status="budget-exhausted", error=str(exc))
                    checkpoint(state_path, state)
                    report(state, output / "report.md")
                    return state
                try:
                    response = probe_client.request(
                        item["body"],
                        tag=f"cache-probe/{item['model']}/{item['condition']}/trial-{trial}",
                        max_body_bytes=MAX_IMAGE_BODY_BYTES,
                        replay=False,
                    )
                    row = trial_record(item, trial, response, prices.get("prices", {}).get(item["model"], {}))
                    if row["local_replayed"]:
                        row["status"] = "unexpected-local-replay"
                except Exception as exc:
                    row = {
                        "model": item["model"],
                        "condition": item["condition"],
                        "trial": trial,
                        "submission": "first" if trial == 0 else f"repeat-{trial}",
                        "request_sha256": item["request_sha256"],
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                    additions = load(directory / "ledger.json")["requests"][len(current_ledger["requests"]) :]
                    matching = [entry for entry in additions if entry.get("request_sha256") == item["request_sha256"]]
                    if matching:
                        row["entry"] = matching[-1]
                        row["elapsed_ms"] = matching[-1].get("elapsed_ms")
                state["records"].append(row)
                wave["records"] = list(state["records"])
                checkpoint(wave_path, wave)
                checkpoint(state_path, state)
                report(state, output / "report.md")
                if row["status"] != "ok":
                    failed_models.add(item["model"])
                    break
        state["status"] = "complete"
        checkpoint(state_path, state)
        report(state, output / "report.md")
        return state


def main() -> None:
    """Select frozen successful bodies, opt into actual calls, or report retained evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", type=Path, nargs="+")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--outputdir", type=Path, required=True)
    parser.add_argument("--directory", type=Path, default=ARTIFACTS)
    args = parser.parse_args()
    if args.report_only:
        state = load(args.outputdir / "results.json")
        report(state, guard_path(args.outputdir) / "report.md")
        print("Reported retained cache probe; no provider calls.")
        return
    paths = args.requests or (select_requests(args.manifest, args.directory) if args.manifest else [])
    if not paths:
        parser.error("--requests or --manifest is required for preparation or hosted execution")
    state = run_probe(
        paths, args.outputdir, hosted=args.run_hosted, directory=args.directory, manifest_path=args.manifest
    )
    print(json.dumps({"status": state["status"], "records": len(state["records"])}))


if __name__ == "__main__":
    main()
