"""Optional, bounded OTLP/HTTP JSON tracing and exact model price registration.

Only explicitly invoked functions load local configuration. Provider errors and
credentials are never returned. Tracing failures cannot retry a paid model call.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import re
import shlex
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from bench.decision_hosted import MODELS

EMBEDDING_MODELS = (
    "google/gemini-embedding-2",
    "voyageai/voyage-multimodal-3.5",
    "nvidia/llama-nemotron-embed-vl-1b-v2:free",
)

_TIMEOUT = 10
_MAX_RESPONSE = 4_000_000
_MAX_PAGES = 50
_MAX_TELEMETRY = 128_000
_MAX_IDENTIFIER = 256
_START_DATE = "2026-10-08T00:00:00.000Z"
_ARTIFACT_DIRECTORY = "bench/results/pdf-master-artifacts/decisions/langfuse"
_CONFIG_KEYS = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL", "LANGFUSE_HOST")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
        return None
    return float(value)


def _configuration(root: Path) -> dict[str, str] | None:  # noqa: C901 - explicit configuration validation.
    values = {}
    for name in (".env.remote-hosts", ".env"):
        path = root / name
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            key = key.strip().removeprefix("export ")
            if key in _CONFIG_KEYS:
                parts = shlex.split(value, comments=True)
                if len(parts) == 1:
                    values[key] = parts[0]
    for key in _CONFIG_KEYS:
        if key in os.environ:
            values[key] = os.environ[key]
    if not values.get("LANGFUSE_PUBLIC_KEY") or not values.get("LANGFUSE_SECRET_KEY"):
        return None
    url = values.get("LANGFUSE_BASE_URL", values.get("LANGFUSE_HOST", "https://cloud.langfuse.com")).rstrip("/")
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme not in {"https", "http"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        message = "invalid Langfuse base URL"
        raise ValueError(message)
    values["LANGFUSE_BASE_URL"] = url.removesuffix("/api/public")
    return values


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Prevent authenticated redirects from forwarding credentials elsewhere."""

    def redirect_request(self, *_args: Any, **_kwargs: Any) -> None:  # noqa: ANN401 - stdlib override.
        return None


def _http(url: str, method: str = "GET", body: object = None, config: dict[str, str] | None = None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if config:
        token = base64.b64encode(f"{config['LANGFUSE_PUBLIC_KEY']}:{config['LANGFUSE_SECRET_KEY']}".encode()).decode()
        headers["Authorization"] = "Basic " + token
        headers["x-langfuse-ingestion-version"] = "4"
    request = urllib.request.Request(  # noqa: S310 - configured HTTP(S) endpoint; redirects refused.
        url, data=_canonical(body) if body is not None else None, method=method, headers=headers
    )
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(request, timeout=_TIMEOUT) as response:
        payload = response.read(_MAX_RESPONSE + 1)
    if len(payload) > _MAX_RESPONSE:
        message = "Langfuse response exceeds bounded admission"
        raise ValueError(message)
    result = json.loads(payload or b"{}")
    if not isinstance(result, dict):
        message = "Langfuse response is not an object"
        raise TypeError(message)
    return result


def _error(error: Exception) -> str:
    return f"HTTP {error.code}" if isinstance(error, urllib.error.HTTPError) else type(error).__name__


def _prices(model: dict[str, Any]) -> dict[str, float] | None:
    pricing = model.get("pricing", {})
    try:
        input_price, output_price = float(pricing["prompt"]), float(pricing["completion"])
    except (KeyError, ValueError, TypeError):
        return None
    if _number(input_price) is None or _number(output_price) is None:
        return None
    return {"input": input_price, "output": output_price}


def _model_definition(model_id: str, prices: dict[str, float]) -> dict[str, Any]:
    return {
        "modelName": model_id,
        "matchPattern": "^" + re.escape(model_id) + "$",
        "startDate": _START_DATE,
        "unit": "TOKENS",
        "pricingTiers": [
            {"name": "OpenRouter catalog", "isDefault": True, "priority": 0, "conditions": [], "prices": prices}
        ],
    }


def _existing_prices(model: dict[str, Any]) -> dict[str, float | None]:
    for tier in model.get("pricingTiers", []):
        if tier.get("isDefault"):
            prices = tier.get("prices", {})
            return {
                key: _number(value.get("price") if isinstance(value, dict) else value) for key, value in prices.items()
            }
    return {"input": _number(model.get("inputPrice")), "output": _number(model.get("outputPrice"))}


def sync_models(root: Path, model_ids: tuple[str, ...] = (*MODELS, *EMBEDDING_MODELS)) -> dict[str, Any]:
    """Register admitted exact model IDs without editing existing definitions.

    Fetch current provider catalog rates per token, not per million tokens.
    Conflicting custom definitions remain untouched and are explicitly reported.
    """
    report: dict[str, Any] = {"status": "disabled", "created": [], "existing": [], "conflicts": [], "missing": []}
    try:
        config = _configuration(root)
        if config is None:
            return report
        catalog: dict[str, Any] = {}
        for catalog_url in (
            "https://openrouter.ai/api/v1/models",
            "https://openrouter.ai/api/v1/models?output_modalities=decisions",
            "https://openrouter.ai/api/v1/embeddings/models",
        ):
            data = _http(catalog_url)
            catalog.update(
                {
                    model["id"]: model
                    for model in data.get("data", [])
                    if isinstance(model, dict) and isinstance(model.get("id"), str)
                }
            )
        existing = []
        for page in range(1, _MAX_PAGES + 1):
            data = _http(config["LANGFUSE_BASE_URL"] + f"/api/public/models?page={page}&limit=100", config=config)
            existing.extend(data.get("data", []))
            if page >= data.get("meta", {}).get("totalPages", page):
                break
        else:
            message = "Langfuse model pagination exceeds bound"
            raise ValueError(message)  # noqa: TRY301 - caught optional telemetry failure.
        rates = {}
        for model_id in sorted(set(model_ids)):
            prices = _prices(catalog.get(model_id, {}))
            if prices is None:
                report["missing"].append(model_id)
                continue
            rates[model_id] = prices
            definition = _model_definition(model_id, prices)
            custom = [
                model
                for model in existing
                if not model.get("isLangfuseManaged")
                and model.get("modelName") == model_id
                and model.get("matchPattern") == definition["matchPattern"]
                and str(model.get("startDate", "")).replace(".000Z", "Z") == _START_DATE.replace(".000Z", "Z")
            ]
            if custom:
                target = "existing" if any(_existing_prices(model) == prices for model in custom) else "conflicts"
                report[target].append(model_id)
                continue
            _http(config["LANGFUSE_BASE_URL"] + "/api/public/models", "POST", definition, config)
            report["created"].append(model_id)
        directory = root / _ARTIFACT_DIRECTORY
        directory.mkdir(parents=True, exist_ok=True)
        # Rates contain no credentials or source content. Root alone invokes this.
        (directory / "catalog-prices.json").write_bytes(_canonical({"fetched_at": time.time(), "prices": rates}))
        report["status"] = "synced"
    except Exception as error:
        report.update(status="error", error=_error(error))
    return report


def _attribute(key: str, value: object) -> dict[str, Any]:
    wrapped: dict[str, Any]
    if isinstance(value, bool):
        wrapped = {"boolValue": value}
    elif isinstance(value, int):
        wrapped = {"intValue": str(value)}
    elif isinstance(value, float):
        wrapped = {"doubleValue": value}
    else:
        wrapped = {"stringValue": value if isinstance(value, str) else _canonical(value).decode()}
    return {"key": key, "value": wrapped}


def _safe_answers(result: dict[str, Any]) -> dict[str, Any]:
    """Export compact numeric decision values, without model free text."""
    answers = result.get("answers", {})
    output: dict[str, Any] = {}
    if not isinstance(answers, dict):
        return output
    for index, answer in enumerate(list(answers.values())[:16]):
        if not isinstance(answer, dict):
            continue
        item = {
            key: answer[key] for key in ("probability", "score", "confidence") if _number(answer.get(key)) is not None
        }
        choice = answer.get("choice")
        if isinstance(choice, str) and choice in {"A", "B", "unresolved", "supported", "contradicted", "insufficient"}:
            item["choice"] = choice
        distribution = answer.get("probabilities")
        if isinstance(distribution, dict):
            item["probabilities"] = {
                key: value
                for key, value in distribution.items()
                if key in {"A", "B", "unresolved", "supported", "contradicted", "insufficient"}
                and _number(value) is not None
            }
        output[f"q{index}"] = item
    return output


def _payload(  # noqa: C901, PLR0912 - explicit usage, cost and privacy projection.
    body: dict[str, Any], result: dict[str, Any], entry: dict[str, Any], prices: dict[str, Any] | None = None
) -> tuple[str, dict[str, Any]]:
    """Create deterministic OTLP identities and sanitized usage/cost metadata."""
    request_sha = entry.get("request_sha256") or _sha(body)
    if not isinstance(request_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", request_sha):
        message = "invalid request SHA-256"
        raise ValueError(message)
    trace_id = request_sha[:32]
    span_id = hashlib.sha256((request_sha + ":generation").encode()).hexdigest()[:16]
    usage = result.get("usage", {})
    if not isinstance(usage, dict):
        usage = {}
    normalized_usage = {}
    for target, source in (("input", "input_tokens"), ("output", "output_tokens"), ("total", "total_tokens")):
        value = usage.get(source)
        if source not in usage:
            value = usage.get({"input": "prompt_tokens", "output": "completion_tokens"}.get(target, source))
        if type(value) is int and value >= 0:
            normalized_usage[target] = value
    provided_cost = _number(usage.get("cost"))
    model = body.get("model", entry.get("requested_model", "unknown"))
    attributes = {
        "langfuse.trace.name": "pdf-master DEV decisions",
        "langfuse.trace.metadata.request_sha256": request_sha,
        "langfuse.observation.type": "embedding" if "input" in body and "questions" not in body else "generation",
        "langfuse.observation.model.name": model,
        "langfuse.observation.usage_details": normalized_usage,
        "langfuse.observation.input": {
            "sha256": request_sha,
            "request_bytes": entry.get("request_bytes", len(_canonical(body))),
            "question_count": len(body.get("questions", {})),
            "state_shape": type(body.get("state")).__name__,
        },
        "langfuse.observation.output": {"answers": _safe_answers(result), "response_sha256": _sha(result)},
        "langfuse.observation.metadata.request_sha256": request_sha,
        "langfuse.observation.metadata.cost_status": entry.get("cost_status", "unknown"),
        "langfuse.observation.metadata.provider_cost_reported": provided_cost is not None,
        "langfuse.environment": "development",
    }
    for key in ("provider", "served_model"):
        value = entry.get(key, result.get("provider" if key == "provider" else "model"))
        if isinstance(value, str) and len(value) < _MAX_IDENTIFIER:
            attributes["langfuse.observation.metadata." + key] = value
    if provided_cost is not None:
        attributes["langfuse.observation.cost_details"] = {"total": provided_cost}
        attributes["langfuse.observation.metadata.provider_reported_usd"] = provided_cost
    else:
        attributes["langfuse.observation.metadata.charge_unknown"] = True
        reserved = _number(entry.get("accounted_usd"))
        if reserved is not None:
            attributes["langfuse.observation.metadata.ledger_reservation_usd"] = reserved
    if (
        provided_cost is None
        and prices
        and model in prices
        and any(key in normalized_usage for key in ("input", "output"))
    ):
        rate = prices[model]
        estimate = sum(normalized_usage.get(key, 0) * rate.get(key, 0) for key in ("input", "output"))
        attributes["langfuse.observation.metadata.catalog_estimated_usd"] = estimate
        attributes["langfuse.observation.metadata.catalog_estimate_is_charge"] = False
    vectors = result.get("data")
    if isinstance(vectors, list):
        attributes["langfuse.observation.output"] = {
            "response_sha256": _sha(result),
            "embedding_dimensions": [
                len(item["embedding"])
                for item in vectors[:256]
                if isinstance(item, dict) and isinstance(item.get("embedding"), list)
            ],
        }
    started = _number(entry.get("started_at"))
    if started is None:
        message = "retained ledger start time is required for deterministic tracing"
        raise ValueError(message)
    elapsed = _number(entry.get("elapsed_ms")) or 0
    span = {
        "traceId": trace_id,
        "spanId": span_id,
        "name": "PDF relationship decision",
        "kind": 3,
        "startTimeUnixNano": str(int(started * 1_000_000_000)),
        "endTimeUnixNano": str(int(started * 1_000_000_000) + int(elapsed * 1_000_000)),
        "attributes": [_attribute(key, value) for key, value in attributes.items()],
        "status": {"code": 2 if entry.get("error") else 1},
    }
    payload = {
        "resourceSpans": [
            {
                "resource": {"attributes": [_attribute("service.name", "pdf-master-bench")]},
                "scopeSpans": [{"scope": {"name": "bench.decision_langfuse", "version": "1"}, "spans": [span]}],
            }
        ]
    }
    return trace_id, payload


def emit_request(root: Path, body: dict[str, Any], result: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    """Export one retained request once; errors are sanitized and nonfatal."""
    try:
        config = _configuration(root)
        if config is None:
            return {"status": "disabled"}
        directory = root / _ARTIFACT_DIRECTORY
        prices_file = directory / "catalog-prices.json"
        prices = json.loads(prices_file.read_text()).get("prices", {}) if prices_file.exists() else None
        trace_id, payload = _payload(body, result, entry, prices)
        marker = directory / (str(entry.get("request_sha256") or _sha(body)) + ".json")
        if marker.exists():
            return {"status": "replayed", "trace_id": trace_id}
        if len(_canonical(payload)) > _MAX_TELEMETRY:
            message = "telemetry payload exceeds bounded admission"
            raise ValueError(message)  # noqa: TRY301 - caught optional telemetry failure.
        response = _http(config["LANGFUSE_BASE_URL"] + "/api/public/otel/v1/traces", "POST", payload, config)
        partial = response.get("partialSuccess", {})
        if partial and int(partial.get("rejectedSpans", 0)):
            message = "Langfuse rejected telemetry spans"
            raise ValueError(message)  # noqa: TRY301 - caught optional telemetry failure.
        directory.mkdir(parents=True, exist_ok=True)
        marker.write_bytes(_canonical({"trace_id": trace_id, "exported_at": time.time()}))
        return {"status": "exported", "trace_id": trace_id}  # noqa: TRY300 - report export beside marker write.
    except Exception as error:
        return {"status": "error", "error": _error(error)}


def verify_trace(root: Path, trace_id: str, started_at: float) -> dict[str, Any]:
    """Read one exact trace through the current observations API, without IO."""
    try:
        config = _configuration(root)
        if config is None:
            return {"status": "disabled"}
        if not re.fullmatch(r"[0-9a-f]{32}", trace_id):
            message = "invalid trace ID"
            raise ValueError(message)  # noqa: TRY301 - caught optional telemetry failure.
        query = urllib.parse.urlencode(
            {
                "traceId": trace_id,
                "fields": "core,basic,model,usage,metadata",
                "limit": 16,
                "fromStartTime": datetime.fromtimestamp(started_at - 60, UTC).isoformat(),
                "toStartTime": datetime.fromtimestamp(started_at + 3600, UTC).isoformat(),
            }
        )
        data = _http(config["LANGFUSE_BASE_URL"] + "/api/public/v2/observations?" + query, config=config)
        rows = [item for item in data.get("data", []) if item.get("traceId") == trace_id]
        safe = [
            {
                key: item[key]
                for key in ("id", "traceId", "type", "model", "usageDetails", "costDetails", "totalCost")
                if key in item
            }
            for item in rows
        ]
        return {"status": "verified" if rows else "pending", "trace_id": trace_id, "observations": safe}  # noqa: TRY300 - readback report beside response projection.
    except Exception as error:
        return {"status": "error", "error": _error(error)}
