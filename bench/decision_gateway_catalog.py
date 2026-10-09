"""Freeze Vercel decision rates and register distinct Gateway Langfuse models."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from bench import decision_langfuse as telemetry
from bench.decision_hosted import ROOT, checkpoint

MODELS = ("convaiinnovations/laya", "convaiinnovations/laya-free", "liquid/d1")


def prices(catalog: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Use exact serving-catalog rates; missing components remain absent."""
    by_id = {row["id"]: row for row in catalog["data"]}
    result = {}
    for model in MODELS:
        record = by_id[model]
        if record.get("type") != "evaluation":
            message = "Gateway candidate is not a catalog decision model"
            raise ValueError(message)
        rates = {}
        for key in ("input", "output", "input_cache_read", "input_cache_write"):
            if key in record.get("pricing", {}):
                raw = record["pricing"][key]
                rate = None if isinstance(raw, bool) else telemetry._number(float(raw))  # noqa: SLF001
                if rate is None:
                    message = "Gateway catalog has invalid numeric rate"
                    raise ValueError(message)
                rates[key] = rate
        result[model] = rates
    return result


def sync(root: Path, rates: dict[str, dict[str, float]]) -> dict[str, Any]:
    """Register Gateway-scoped model identities without changing existing definitions."""
    config = telemetry._configuration(root)  # noqa: SLF001 - same project telemetry configuration.
    if config is None:
        return {"status": "disabled"}
    existing = []
    for page in range(1, 21):
        data = telemetry._http(  # noqa: SLF001
            config["LANGFUSE_BASE_URL"] + f"/api/public/models?page={page}&limit=100", config=config
        )
        existing.extend(data.get("data", []))
        if page >= data.get("meta", {}).get("totalPages", page):
            break
    else:
        message = "Gateway Langfuse model pagination exceeds bound"
        raise ValueError(message)
    report: dict[str, Any] = {"status": "synced", "created": [], "existing": [], "conflicts": []}
    for model, rate in rates.items():
        name = "vercel/" + model
        definition = telemetry._model_definition(name, rate)  # noqa: SLF001
        definition["pricingTiers"][0]["name"] = "Vercel AI Gateway catalog"
        custom = [
            row
            for row in existing
            if not row.get("isLangfuseManaged")
            and row.get("modelName") == name
            and row.get("matchPattern") == definition["matchPattern"]
        ]
        if custom:
            field = "existing" if any(telemetry._existing_prices(row) == rate for row in custom) else "conflicts"  # noqa: SLF001
            report[field].append(name)
        else:
            telemetry._http(config["LANGFUSE_BASE_URL"] + "/api/public/models", "POST", definition, config)  # noqa: SLF001
            report["created"].append(name)
    return report


def main() -> None:
    """Read the retained public catalog; only explicit telemetry sync writes remotely."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--sync-langfuse", action="store_true")
    args = parser.parse_args()
    raw = args.catalog.read_bytes()
    rates = prices(json.loads(raw))
    directory = ROOT / "bench/results/pdf-master-artifacts/decisions/langfuse"
    checkpoint(
        directory / "gateway-catalog-prices.json",
        {
            "prices": rates,
            "fetched_at": time.time(),
            "catalog_sha256": hashlib.sha256(raw).hexdigest(),
            "source": "https://ai-gateway.vercel.sh/v1/models",
        },
    )
    result = sync(ROOT, rates) if args.sync_langfuse else {"status": "rates frozen", "models": list(rates)}
    checkpoint(directory / "gateway-model-sync.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
