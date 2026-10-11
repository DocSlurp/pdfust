"""Shared helpers for the hosted relationship-decision adapters.

This module has no ``NAME`` and is therefore not an adapter itself. It keeps
request accounting consistent across the decision adapters:

- ``provider_reported_usd`` is the charge the provider reported, including a
  reported zero. It is omitted when the provider reported nothing.
- ``effective_usd`` and ``cost_basis`` come from
  ``bench.reprice_model_rates.request_cost``: a positive reported charge wins;
  a zero or missing charge becomes a catalog-rate estimate only when tokens
  and published rates exist (``estimated_usd`` is then set as well); otherwise
  the basis starts with ``unknown`` and no amount is recorded.
- ``reservation_usd`` is ledger admission accounting, never a charge.

Batched requests share one charge, so rows carry ``request_case_count`` and
run-level totals deduplicate by ledger request index.
"""

from __future__ import annotations

import json
from functools import cache
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import ROOT, canonical, digest, guard, read_json
from bench.reprice_model_rates import number, request_cost

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

DECISION_THRESHOLD = 0.5


def flag(value: object) -> float | None:
    """Return 1.0/0.0 for booleans and finite numbers unchanged; everything else is unmeasured."""
    if isinstance(value, bool):
        return float(value)
    return number(value)


def relative(path: Path) -> str:
    """Return a repository-relative path when possible."""
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def state_ref(value: object) -> dict[str, Any]:
    """Return a canonical size and hash reference for a request state, never its content."""
    text = canonical(value)
    return {"sha256": digest(value, 64), "bytes": len(text.encode())}


@cache
def ledger(root: Path) -> dict[int, dict[str, Any]]:
    """Return shared-ledger request entries by index (empty when the ledger is absent)."""
    path = guard(root / "ledger.json")
    if not path.exists():
        return {}
    return {entry["index"]: entry for entry in read_json(path).get("requests", []) if "index" in entry}


@cache
def catalog_prices(root: Path) -> dict[str, Any]:
    """Return the frozen catalog price map used for labeled zero/missing-charge estimates."""
    path = guard(root / "langfuse" / "catalog-prices.json")
    return read_json(path).get("prices", {}) if path.exists() else {}


def response_usage(root: Path, entry: Mapping[str, Any]) -> dict[str, Any]:
    """Read only the usage block of a retained response, if it exists."""
    name = entry.get("response_file")
    if not isinstance(name, str):
        return {}
    path = guard(root / name)
    if not path.is_file():
        return {}
    try:
        usage = json.loads(path.read_text(encoding="utf-8")).get("usage", {})
    except (OSError, ValueError, AttributeError):
        return {}
    return usage if isinstance(usage, dict) else {}


def cost_fields(
    entry: Mapping[str, Any] | None,
    usage: Mapping[str, Any] | None,
    price: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return per-request accounting metadata without converting unknown charges into zero."""
    if not entry or "index" not in entry:
        return {}
    usage = dict(usage or {})
    rates = dict(entry.get("catalog_rates") or price or {})
    quote = request_cost(dict(entry), usage, rates)
    fields: dict[str, Any] = {
        "request_index": entry["index"],
        "ledger_cost_status": entry.get("cost_status"),
        "request_case_count": entry.get("case_count"),
        "cost_basis": quote["basis"],
    }
    if quote["reported_usd"] is not None:
        fields["provider_reported_usd"] = quote["reported_usd"]
    if quote["effective_usd"] is not None:
        fields["effective_usd"] = quote["effective_usd"]
        if quote["basis"] == "catalog estimate":
            fields["estimated_usd"] = quote["effective_usd"]
    if entry.get("cost_status") == "reserved" and number(entry.get("accounted_usd")) is not None:
        fields["reservation_usd"] = entry["accounted_usd"]
    fields.update(_request_facts(entry, usage))
    return fields


def _request_facts(entry: Mapping[str, Any], usage: Mapping[str, Any]) -> dict[str, Any]:
    """Return reported token counts, served identity, and HTTP latency when present."""
    facts: dict[str, Any] = {}
    for name, keys in (
        ("input_tokens", ("input_tokens", "prompt_tokens")),
        ("output_tokens", ("output_tokens", "completion_tokens")),
    ):
        value = next((usage[key] for key in keys if number(usage.get(key)) is not None), None)
        if value is not None:
            facts[name] = value
    for name in ("served_model", "provider"):
        if isinstance(entry.get(name), str):
            facts[name] = entry[name]
    if number(entry.get("elapsed_ms")) is not None:
        facts["http_elapsed_ms"] = entry["elapsed_ms"]
    return facts


def cost_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Deduplicate request accounting by ledger index; partial totals never claim completeness."""
    unique: dict[Any, Mapping[str, Any]] = {}
    for fields in rows:
        if "request_index" in fields:
            unique.setdefault(fields["request_index"], fields)
    values = list(unique.values())
    reported = [fields["provider_reported_usd"] for fields in values if "provider_reported_usd" in fields]
    known = [fields["effective_usd"] for fields in values if "effective_usd" in fields]
    unknown = len(values) - len(known)
    return {
        "unique_requests": len(values),
        "provider_reported_usd": sum(reported) if reported else None,
        "provider_reported_requests": len(reported),
        "provider_reported_zero_requests": sum(value == 0 for value in reported),
        "estimated_usd": sum(fields.get("estimated_usd", 0.0) for fields in values),
        "estimated_requests": sum("estimated_usd" in fields for fields in values),
        "effective_usd_known": sum(known),
        "effective_usd": sum(known) if values and not unknown else None,
        "unknown_cost_requests": unknown,
        "input_tokens": sum(fields.get("input_tokens", 0) for fields in values),
        "output_tokens": sum(fields.get("output_tokens", 0) for fields in values),
    }


def cohort_ledger(root: Path, prefix: str) -> dict[str, Any]:
    """Summarize ledger requests tagged ``prefix/NNN`` exactly as the retained request-accounting table does."""
    entries = [entry for entry in ledger(root).values() if str(entry.get("tag", "")).rsplit("/", 1)[0] == prefix]
    return {
        "ledger_requests": len(entries),
        "ledger_accounted_usd": sum(number(entry.get("accounted_usd")) or 0.0 for entry in entries),
        "ledger_unsettled_requests": sum(entry.get("cost_status") != "provider-reported USD" for entry in entries),
    }


def average(values: Iterable[float | bool | int | None]) -> float | None:
    """Return the mean of measured values, or None when nothing was measured."""
    measured = [float(value) for value in values if value is not None]
    return sum(measured) / len(measured) if measured else None


def mismatches(expected: Mapping[str, Any], actual: Mapping[str, Any], tolerance: float = 1e-9) -> list[str]:
    """List keys whose recomputed value differs from the retained report value."""
    found = []
    for key, value in expected.items():
        other = actual.get(key)
        if isinstance(value, (int, float)) and isinstance(other, (int, float)):
            if abs(float(value) - float(other)) > tolerance:
                found.append(f"{key}: retained {value} != recomputed {other}")
        elif value != other:
            found.append(f"{key}: retained {value!r} != recomputed {other!r}")
    return found


def choice_scores(answer: Mapping[str, Any] | None, expected: str | None) -> dict[str, float | None]:
    """Score a categorical decision answer against one expected option."""
    answer = answer or {}
    choice = answer.get("choice")
    probabilities = answer.get("probabilities") if isinstance(answer.get("probabilities"), dict) else {}
    scores: dict[str, float | None] = {"abstained": flag(choice == "unresolved") if choice is not None else None}
    if expected is not None and choice is not None:
        scores["choice_correct"] = flag(choice == expected)
    if expected is not None and probabilities:
        scores["p_expected"] = number(probabilities.get(expected))
    return scores
