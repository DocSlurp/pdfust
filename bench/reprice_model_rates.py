"""Reprice zero/missing reported costs offline using retained catalog token rates.

Positive provider-reported USD wins. Reservations are never treated as spend.
No requests, credentials, quality scores, or original accounting are modified.
"""

# Retained response/ledger dictionaries have heterogeneous provider-defined fields.
# ruff: noqa: ANN401, EM101, TRY003, PLR2004

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "bench/results/pdf-master-artifacts/decisions"
REPORT = ROOT / "bench/results/model-experiment-rates.md"
CATALOG_URL = "https://openrouter.ai/api/v1/models?output_modalities=decisions"


def load(path: Path) -> Any:
    """Read one retained artifact, refusing held-out paths and symlink targets."""
    for candidate in (path, path.resolve()):
        if any(name in str(candidate).lower() for name in ("heldout-silver", "silver-heldout-v1")):
            raise ValueError("Held-out artifacts are excluded")
    return json.loads(path.read_text())


def number(value: object) -> float | None:
    """Accept finite nonnegative numeric observations, excluding booleans."""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return float(value)
    return None


def cache_usage(usage: dict[str, Any]) -> dict[str, Any]:
    """Retain provider cache counters and flag absent/invalid counters without inference."""
    inputs = number(usage.get("input_tokens", usage.get("prompt_tokens")))
    details = usage.get("input_tokens_details", usage.get("prompt_tokens_details"))
    details = details if isinstance(details, dict) else {}
    read_present, write_present = "cached_tokens" in details, "cache_write_tokens" in details
    read = number(details.get("cached_tokens")) if read_present else 0.0
    write = number(details.get("cache_write_tokens")) if write_present else 0.0
    valid = read is not None and write is not None and (inputs is None or read + write <= inputs)
    return {
        "cache_read_counter_present": read_present,
        "cache_write_counter_present": write_present,
        "cache_read_tokens": details.get("cached_tokens") if read_present else None,
        "cache_write_tokens": details.get("cache_write_tokens") if write_present else None,
        "cache_counters_valid": valid,
        "cache_assumption": None
        if read_present and write_present
        else "unreported counters assumed zero (uncached component unverified)",
        "cache_status": "invalid counters"
        if not valid
        else "reported counters"
        if read_present or write_present
        else "unreported",
    }


def request_cost(entry: dict[str, Any], usage: dict[str, Any], price: dict[str, Any]) -> dict[str, Any]:
    """Prefer positive actual charges; estimate observed cache components at published rates.

    A provider-reported zero remains zero in ``reported_usd``. The separate
    estimate never changes original charges or treats ledger reservations as
    observed spend. Missing cache counters assume zero with an explicit warning;
    reported cache use without the corresponding published rate remains unknown.
    """
    reported = number(usage.get("cost", entry.get("provider_reported_usd")))
    if reported is None and entry.get("cost_status") == "provider-reported USD":
        reported = number(entry.get("accounted_usd"))
    ledger = number(entry.get("accounted_usd")) if entry.get("cost_status") == "provider-reported USD" else None
    positive = next((cost for cost in (reported, ledger) if cost is not None and cost > 0), None)
    cache = cache_usage(usage)
    result: dict[str, Any] = {
        "index": entry["index"],
        "reported_usd": reported,
        "ledger_accounted_usd": entry.get("accounted_usd"),
        "ledger_cost_status": entry.get("cost_status"),
        "usage": usage,
        **cache,
    }
    # BYOK gateway fees and direct-provider inference are distinct amounts.
    # Preserve the original gateway zero; never add upstream costs for shared routing.
    details = usage.get("cost_details")
    upstream = number(details.get("upstream_inference_cost")) if isinstance(details, dict) else None
    if usage.get("is_byok") is True and upstream is not None and upstream > 0:
        return {
            **result, "upstream_inference_usd": upstream, "gateway_reported_usd": reported,
            "effective_usd": upstream + reported if reported is not None else None,
            "basis": "provider-reported BYOK upstream plus gateway USD"
            if reported is not None else "unknown: missing BYOK gateway charge",
            "cost_scope": "API-reported upstream inference plus gateway fee; not invoice reconciliation",
        }
    if positive is not None:
        return {**result, "effective_usd": positive, "basis": "provider-reported USD"}
    inputs = number(usage.get("input_tokens", usage.get("prompt_tokens")))
    outputs = number(usage.get("output_tokens", usage.get("completion_tokens")))
    input_price, output_price = number(price.get("input")), number(price.get("output"))
    if inputs is None or outputs is None or input_price is None or output_price is None:
        return {**result, "effective_usd": None, "basis": "unknown: missing usage or catalog price"}
    if not cache["cache_counters_valid"]:
        return {**result, "effective_usd": None, "basis": "unknown: invalid cache usage"}
    read = number(cache["cache_read_tokens"]) or 0.0
    write = number(cache["cache_write_tokens"]) or 0.0
    components = {"uncached_input": (inputs - read - write) * input_price, "output": outputs * output_price}
    missing = []
    for name, count, key in (("cache_read", read, "input_cache_read"), ("cache_write", write, "input_cache_write")):
        rate = number(price.get(key))
        if count and rate is None:
            missing.append(key)
        else:
            components[name] = count * (rate or 0.0)
    if missing:
        return {
            **result,
            "effective_usd": None,
            "basis": "unknown: missing required cache price",
            "known_components_usd": components,
            "missing_price_keys": missing,
        }
    return {
        **result,
        "effective_usd": sum(components.values()),
        "basis": "catalog estimate",
        "estimated_components_usd": components,
        "input_usd_per_token": input_price,
        "output_usd_per_token": output_price,
        "input_cache_read_usd_per_token": price.get("input_cache_read"),
        "input_cache_write_usd_per_token": price.get("input_cache_write"),
    }


def aggregate(requests: list[dict[str, Any]], price: dict[str, Any]) -> dict[str, Any]:
    """Deduplicate per experiment request index and retain unknown charges as unknown."""
    unique = {request["entry"]["index"]: request for request in requests}
    costs = [request_cost(r["entry"], r.get("usage") or {}, price) for r in unique.values()]
    pages = sum(request["entry"].get("case_count", 1) for request in unique.values())
    total = None if any(r["effective_usd"] is None for r in costs) else sum(r["effective_usd"] for r in costs)
    return {
        "admitted_page_inputs": pages,
        "requests": costs,
        "effective_usd": total,
        "pages_per_usd": pages / total if total is not None and total > 0 else None,
        "estimated": any(r["basis"] == "catalog estimate" for r in costs),
    }


def cohort(directory: Path, model: str, experiment: str, ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select original cohort requests, including only the one reused relationship smoke."""
    if experiment.startswith("Assembly "):
        arm = experiment.removeprefix("Assembly ").split(" [", 1)[0]
        return [
            record
            for name in ("initial", "ablations", "compact", "facts")
            for record in load(directory / f"context-run-{name}.json")["records"]
            if record["model"] == model and record["arm"] == arm
        ]
    if experiment.startswith("Region gate "):
        variant = experiment.removeprefix("Region gate ")
        tags = (f"controls/{model}@{variant}/batch/",)
    elif experiment.startswith("Relationships "):
        variant = experiment.removeprefix("Relationships ")
        tags = (f"{model}@{variant}/batch/",)
    elif experiment == "Smoke only":
        tags = (f"{model}@rich/smoke/",)
    else:
        raise ValueError("No retained cohort selector for this experiment")
    selected = [entry for entry in ledger if any(entry["tag"].startswith(tag) for tag in tags)]
    if experiment == "Relationships resolved-b1" and sum(r.get("case_count", 1) for r in selected) == 95:
        # The first singleton request replays the earlier successful resolved smoke.
        smoke = [entry for entry in ledger if entry["tag"] == f"{model}@resolved/smoke/000"]
        if len(smoke) != 1:
            raise ValueError("Relationship cohort lacks its unique reused first request")
        selected += smoke
    records = []
    for entry in selected:
        response_name = Path(entry["response_file"])
        if response_name.name != str(response_name):
            raise ValueError("Response files must remain within retained artifact directory")
        response = load(directory / response_name)
        records.append({"entry": entry, "usage": response.get("usage") or {}})
    return records


def reprice(directory: Path, report: Path) -> dict[str, Any]:
    """Change only undefined cost cells and pricing notes, preserving scores and timing."""
    catalog_path = directory / "langfuse/catalog-prices.json"
    catalog = load(catalog_path)
    ledger = load(directory / "ledger.json")["requests"]
    lines = report.read_text().splitlines()
    repriced = []
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) != 7 or (
            cells[3] not in ("$0 reported", "unknown", "Unknown", "— (unknown cost)", "— (failed smoke; 0 tokens)")
            and not cells[3].startswith("~")
        ):
            continue
        model, experiment = cells[1:3]
        requests = cohort(directory, model, experiment, ledger)
        result = aggregate(requests, catalog["prices"].get(model, {}))
        if not requests:
            result["pages_per_usd"] = None
        rate = result["pages_per_usd"]
        cells[3] = f"~{rate:,.0f}" if rate is not None else "— (unknown cost)"
        if experiment == "Smoke only" and result["effective_usd"] == 0:
            cells[3] = "— (failed smoke; 0 tokens)"
        lines[index] = "| " + " | ".join(cells[1:-1]) + " |"
        repriced.append({"model": model, "experiment": experiment, **result})
    text = "\n".join(lines) + "\n"
    text = text.replace("admitted page inputs / provider-reported USD", "admitted page inputs / effective USD")
    old = (
        "`$0 reported` means the provider returned zero and division is undefined; "
        "it is not a claim of free future inference."
    )
    note = (
        "Positive provider-reported costs take precedence. For zero or missing reported costs, `~` marks an estimate "
        "from the [OpenRouter catalog](" + CATALOG_URL + ") checked 2026-10-09 and retained observed input/output "
        "tokens; Luna pricing is $0.10 per million input tokens and $0 per output token. Original provider zeros "
        "and the spending ledger remain unchanged; these estimates are not actual campaign spend. Missing token "
        "usage or pricing remains unknown. Gemini's failed smoke reported zero input/output tokens, so no "
        "positive cost or usable pages/$ estimate exists. Timing and scores are unchanged."
    )
    text = text.replace(old, note)
    report.write_text(text)
    artifact = {
        "schema": 1,
        "catalog_url": CATALOG_URL,
        "catalog_checked_date": "2026-10-09",
        "catalog_fetched_at": catalog["fetched_at"],
        "catalog_sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        "scope": "offline replacement of zero/missing cost cells only; per-experiment request-index deduplication",
        "rows": repriced,
    }
    (directory / "model-experiment-repricing.json").write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n")
    return artifact


def main() -> None:
    """Run a local repricing pass without network or inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DATA)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    result = reprice(args.directory, args.report)
    print(f"Repriced {len(result['rows'])} rows; original ledger preserved.")


if __name__ == "__main__":
    main()
