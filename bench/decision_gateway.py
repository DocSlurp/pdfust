"""Root-owned Vercel TypeSafe decisions sharing the authorized persistent ledger.

Protocol: https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe
Gateway prices must be frozen separately from OpenRouter prices. Preparation and
unit tests never read credentials; constructing the live client is opt-in.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import time
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from bench import decision_hosted as hosted
from bench.reprice_model_rates import number, request_cost
from bench.silver import guard_path

ENDPOINT = "https://ai-gateway.vercel.sh/typesafe/v1/systemone"
GATEWAY = "vercel"
MODELS = ("convaiinnovations/laya", "convaiinnovations/laya-free", "liquid/d1")
LAYA_MODELS = MODELS[:2]


def read_gateway_key(root: Path) -> str:
    """Prefer the local dotenv key, then remote-hosts dotenv, then process state."""
    for filename in (".env", ".env.remote-hosts"):
        path = root / filename
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            if key.strip().removeprefix("export ") == "AI_GATEWAY_API_KEY":
                parts = shlex.split(value, comments=True)
                if parts and parts[0]:
                    return parts[0]
    process_key = os.environ.get("AI_GATEWAY_API_KEY")
    if process_key:
        return process_key
    message = "AI_GATEWAY_API_KEY is not configured locally"
    raise RuntimeError(message)


def request_identity(encoded: bytes) -> str:
    """Namespace exact transport bytes by the fixed serving endpoint."""
    return hashlib.sha256(ENDPOINT.encode() + b"\0" + encoded).hexdigest()


def _money(value: object) -> float | None:
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return None
    return number(value)


def normalize_response(raw: dict[str, Any]) -> dict[str, Any]:
    """Add generic usage aliases without fabricating missing token observations."""
    if not isinstance(raw, dict):
        message = "Gateway response must be an object"
        raise TypeError(message)
    result = dict(raw)
    usage = raw.get("usage", {})
    if not isinstance(usage, dict):
        message = "Gateway usage must be an object"
        raise TypeError(message)
    usage = dict(usage)
    for target, aliases in (
        ("input_tokens", ("inputTokens", "prompt_tokens", "promptTokens")),
        ("output_tokens", ("outputTokens", "completion_tokens", "completionTokens")),
        ("input_tokens_details", ("inputTokensDetails", "prompt_tokens_details", "promptTokensDetails")),
    ):
        if target not in usage:
            for alias in aliases:
                if alias in usage:
                    usage[target] = usage[alias]
                    break
    metadata = raw.get("provider_metadata", raw.get("providerMetadata", {}))
    metadata = metadata if isinstance(metadata, dict) else {}
    gateway = metadata.get("gateway", {})
    gateway = gateway if isinstance(gateway, dict) else {}
    cost = _money(gateway["cost"]) if "cost" in gateway else _money(usage.get("cost"))
    if cost is not None:
        usage["cost"] = cost
    else:
        usage.pop("cost", None)
    result["usage"] = usage
    if "provider_metadata" not in result and metadata:
        result["provider_metadata"] = metadata
    return result


def _validate(body: dict[str, Any], max_body_bytes: int) -> bytes:  # noqa: C901 - bounded transport and routing gates.
    if type(max_body_bytes) is not int or not 1 <= max_body_bytes <= hosted.MAX_IMAGE_BODY_BYTES:
        message = "Gateway byte admission exceeds the shared bounded ceiling"
        raise ValueError(message)
    if not isinstance(body, dict) or body.get("model") not in MODELS:
        message = "Gateway model is outside the exact frozen allowlist"
        raise ValueError(message)
    if set(body) - {"model", "state", "questions", "images", "providerOptions"} or "state" not in body:
        message = "Gateway request contains unsupported transport fields"
        raise ValueError(message)
    questions = body.get("questions")
    if not isinstance(questions, dict) or not 1 <= len(questions) <= hosted.MAX_QUESTIONS:
        message = "Gateway question inventory exceeds admission"
        raise ValueError(message)
    options = body.get("providerOptions", {})
    if not isinstance(options, dict) or set(options) - {"gateway"}:
        message = "Gateway provider options are outside the bounded contract"
        raise ValueError(message)
    routing = options.get("gateway", {})
    if not isinstance(routing, dict) or set(routing) - {"only"}:
        message = "Gateway model fallbacks and extra routing options are disabled"
        raise ValueError(message)
    if body["model"] in LAYA_MODELS and routing != {"only": ["boundless"]}:
        message = "Laya requires the explicit Boundless provider allowlist"
        raise ValueError(message)
    if "only" in routing and (
        not isinstance(routing["only"], list) or len(routing["only"]) != 1 or not isinstance(routing["only"][0], str)
    ):
        message = "Gateway provider selection must name exactly one provider"
        raise ValueError(message)
    if "images" in body:
        images = body["images"]
        if body["model"] != "liquid/d1" or not isinstance(images, list) or not 1 <= len(images) <= hosted.MAX_QUESTIONS:
            message = "Only liquid/d1 may receive bounded top-level images"
            raise ValueError(message)
        if any(not isinstance(image, str) or not image.startswith("data:image/") for image in images):
            message = "Gateway images must be retained inline data URLs"
            raise ValueError(message)
    encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
    if len(encoded) > max_body_bytes:
        message = "Gateway request exceeds frozen byte admission"
        raise ValueError(message)
    return encoded


class GatewayDecisionClient(hosted.DecisionClient):
    """Use one shared budget lock, Gateway-specific pricing and route-specific replay."""

    gateway = GATEWAY

    def __init__(
        self,
        root: Path = hosted.ROOT,
        *,
        rates: dict[str, dict[str, Any]] | None = None,
        catalog_path: Path | None = None,
        api_key: str | None = None,
    ) -> None:
        """Root may provide exact frozen Gateway rates and a test-only dummy key."""
        self.root = guard_path(root)
        self.directory = self.root / "bench/results/pdf-master-artifacts/decisions"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.ledger = self.directory / "ledger.json"
        self.key = read_gateway_key(self.root) if api_key is None else api_key
        if not self.key:
            message = "Gateway key is empty"
            raise ValueError(message)
        self.catalog: dict[str, Any] = {"prices": rates} if rates is not None else {}
        if rates is None:
            price_path = guard_path(catalog_path or self.directory / "langfuse/gateway-catalog-prices.json")
            if price_path.exists():
                self.catalog = json.loads(price_path.read_bytes())
        # Detach the frozen prices from a caller's mutable mapping.
        self.catalog = json.loads(json.dumps(self.catalog, allow_nan=False))

    def _account_result(self, body: dict[str, Any], result: dict[str, Any], entry: dict[str, Any]) -> None:
        """Positive Gateway charges win; incomplete estimates retain the reservation."""
        cost = number(result.get("usage", {}).get("cost"))
        if cost is not None:
            entry["provider_reported_usd"] = cost
            if cost > 0:
                entry.update(accounted_usd=cost, cost_status="provider-reported USD")
        pricing = self.catalog.get("prices", {}).get(body["model"], {})
        entry.update(catalog_rates=pricing, catalog_fetched_at=self.catalog.get("fetched_at"), pricing_gateway=GATEWAY)
        if entry["cost_status"] == "reserved":
            estimate = request_cost(entry, result.get("usage", {}), pricing)
            if estimate["effective_usd"] is not None:
                entry.update(accounted_usd=estimate["effective_usd"], cost_status=estimate["basis"])

    def request(
        self,
        body: dict[str, Any],
        *,
        tag: str,
        max_body_bytes: int = hosted.MAX_BODY_BYTES,
        replay: bool = True,
        reservation_usd: float = hosted.RESERVATION,
    ) -> dict[str, Any]:
        """Transmit once with a 90-second timeout; successful exact replays are local."""
        hosted.validate_request_reservation(reservation_usd)
        encoded = _validate(body, max_body_bytes)
        body_hash, identity = hashlib.sha256(encoded).hexdigest(), request_identity(encoded)
        with hosted.exclusive_lock(self.directory / "ledger.lock"):
            ledger: dict[str, Any] = (
                json.loads(self.ledger.read_bytes())
                if self.ledger.exists()
                else {
                    "campaign_limit_usd": hosted.CAMPAIGN_LIMIT,
                    "authorized_total_usd": hosted.TOTAL_LIMIT,
                    "prior_rental_reported_usd": hosted.PRIOR_RENTAL,
                    "requests": [],
                }
            )
            charged = sum(hosted.accounted_cost(row["accounted_usd"]) for row in ledger["requests"])
            prior = hosted.PRIOR_RENTAL + self._prior_api_cost()
            for entry in ledger["requests"]:
                if entry.get("gateway") != GATEWAY or entry.get("request_identity_sha256") != identity:
                    continue
                if entry.get("error") or not entry.get("response_file"):
                    message = "Previous identical Gateway call failed; investigation required before retry"
                    raise RuntimeError(message)
                if entry.get("response_file"):
                    if not replay:
                        continue
                    result = normalize_response(
                        json.loads(guard_path(self.directory / entry["response_file"]).read_bytes())
                    )
                    return {
                        "result": result,
                        "entry": entry,
                        "replayed": True,
                        "telemetry": self._telemetry(body, result, entry),
                    }
                message = "Previous identical Gateway call failed; investigation required before retry"
                raise RuntimeError(message)
            if (
                charged + reservation_usd > hosted.CAMPAIGN_LIMIT
                or prior + charged + reservation_usd > hosted.TOTAL_LIMIT
            ):
                message = "Gateway reservation exceeds shared campaign or cumulative authorized spend"
                raise RuntimeError(message)
            index = len(ledger["requests"])
            entry = {
                "index": index,
                "tag": tag,
                "gateway": GATEWAY,
                "provider_gateway": GATEWAY,
                "endpoint": ENDPOINT,
                "requested_model": body["model"],
                "request_sha256": body_hash,
                "request_identity_sha256": identity,
                "request_bytes": len(encoded),
                "force_transmission": not replay,
                "case_count": len(body["questions"]),
                "accounted_usd": reservation_usd,
                "reservation_usd": reservation_usd,
                "cost_status": "reserved",
                "prior_accounted_usd": prior,
                "started_at": time.time(),
            }
            ledger["requests"].append(entry)
            hosted.checkpoint(self.ledger, ledger)
            (self.directory / f"request-{index:03d}.json").write_bytes(encoded)
            request = urllib.request.Request(
                ENDPOINT,
                data=encoded,
                headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"},
                method="POST",
            )
            start = time.perf_counter()
            try:
                with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310 - fixed documented HTTPS endpoint.
                    payload = response.read(hosted.MAX_RESPONSE_BYTES + 1)
                if len(payload) > hosted.MAX_RESPONSE_BYTES:
                    message = "Gateway response exceeds retained payload admission"
                    raise ValueError(message)  # noqa: TRY301 - keep reservation for a transmitted failure.
                response_name = f"response-{index:03d}.json"
                (self.directory / response_name).write_bytes(payload)
                entry["response_file"] = response_name
                raw = json.loads(payload)
                result = normalize_response(raw)
                metadata = result.get("provider_metadata", {})
                gateway = metadata.get("gateway", {}) if isinstance(metadata, dict) else {}
                routing = gateway.get("routing", {}) if isinstance(gateway, dict) else {}
                entry.update(
                    response_file=response_name,
                    served_model=result.get("model"),
                    provider=routing.get("finalProvider") if isinstance(routing, dict) else None,
                    generation_id=gateway.get("generationId") if isinstance(gateway, dict) else None,
                    provider_cost_raw=gateway.get("cost") if isinstance(gateway, dict) else None,
                )
                self._account_result(body, result, entry)
                if result.get("model") not in (None, body["model"]):
                    message = "Gateway returned a different model; model fallback is disabled"
                    raise ValueError(message)  # noqa: TRY301 - preserve the actual paid response/accounting.
            except Exception as error:
                entry["error"] = (
                    f"HTTP {error.code}" if isinstance(error, urllib.error.HTTPError) else type(error).__name__
                )
                entry["elapsed_ms"] = (time.perf_counter() - start) * 1000
                entry["telemetry"] = self._telemetry(body, {}, entry)
                hosted.checkpoint(self.ledger, ledger)
                message = f"Gateway call failed ({entry['error']}); accounting retained; no provider error body logged"
                raise RuntimeError(message) from None
            entry["elapsed_ms"] = (time.perf_counter() - start) * 1000
            entry["telemetry"] = self._telemetry(body, result, entry)
            hosted.checkpoint(self.ledger, ledger)
            return {"result": result, "entry": entry, "replayed": False}
