"""Experimental bounded fresh OpenRouter requests with atomic shared reservations.

No client is constructed or transport invoked at import. Root-only future callers
must supply an existing DecisionClient and a sufficient worst-case reservation.
"""

# Existing provider/ledger dictionaries and callbacks have heterogeneous schemas.
# ruff: noqa: EM101, EM102, TRY003, TRY301, C901, PLR0912, PLR0913
from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.error
import urllib.request
import uuid
from contextlib import suppress
from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from bench import decision_hosted as hosted
from bench.decision_gateway import safe_http_error

MAX_INFLIGHT = 8
WAVE_LIMITS = {"P001": 50.0, "P002": 50.0, "P003": 50.0}
SETTLEMENT_FIELDS = {
    "response_file",
    "response_prefix_file",
    "response_truncated",
    "served_model",
    "provider",
    "generation_id",
    "provider_reported_usd",
    "upstream_inference_usd",
    "gateway_reported_usd",
    "accounted_usd",
    "cost_status",
    "catalog_fetched_at",
    "catalog_rates",
    "error",
    "http_error_diagnostic",
    "elapsed_ms",
    "telemetry",
    "concurrent_state",
    "completed_at",
    "reservation_exceeded",
}


class ConcurrentDecisionClient:
    """Fresh-only wrapper; shared ledger bounds admission across threads/processes."""

    def __init__(
        self,
        client: hosted.DecisionClient,
        *,
        max_inflight: int = 2,
        wave_limits: dict[str, float] | None = None,
        opener: Callable[..., Any] | None = None,
        allow_matched_replicates: bool = False,
    ) -> None:
        """Wrap an existing exact OpenRouter client without reading credentials."""
        if type(client) is not hosted.DecisionClient:
            raise ValueError("Only the exact OpenRouter DecisionClient transport is supported")
        if type(max_inflight) is not int or not 1 <= max_inflight <= MAX_INFLIGHT:
            raise ValueError("Concurrent admission must be an integer from 1 through 8")
        waves = WAVE_LIMITS if wave_limits is None else wave_limits
        if not waves or any(
            k not in WAVE_LIMITS or hosted.accounted_cost(v) > WAVE_LIMITS[k] or v <= 0 for k, v in waves.items()
        ):
            raise ValueError("Wave limits must tighten the existing P001/P002/P003 caps")
        if type(allow_matched_replicates) is not bool or (allow_matched_replicates and set(waves) != {"P003"}):
            raise ValueError("Matched replicate policy is restricted to P003-only admission")
        self._client = client
        self.root, self.directory, self.ledger = client.root, client.directory, client.ledger
        self.policy: dict[str, Any] = {"max_inflight": max_inflight, "wave_limits_usd": deepcopy(waves)}
        if allow_matched_replicates:
            self.policy["allow_matched_replicates"] = True
        self._opener = urllib.request.urlopen if opener is None else opener

    def _load(self) -> dict[str, Any]:
        ledger: dict[str, Any] = (
            json.loads(self.ledger.read_text())
            if self.ledger.exists()
            else {
                "campaign_limit_usd": hosted.CAMPAIGN_LIMIT,
                "authorized_total_usd": hosted.TOTAL_LIMIT,
                "prior_rental_reported_usd": hosted.PRIOR_RENTAL,
                "requests": [],
            }
        )
        if not isinstance(ledger.get("requests"), list) or any(
            type(e.get("index")) is not int or e["index"] != i for i, e in enumerate(ledger["requests"])
        ):
            raise ValueError("Ledger requires unique contiguous retained request indices")
        for entry in ledger["requests"]:
            hosted.accounted_cost(entry["accounted_usd"])
        return ledger

    def _reserve(self, body: dict[str, Any], encoded: bytes, tag: str, reservation: float) -> dict[str, Any]:
        wave = tag.split("/", 1)[0]
        if wave not in self.policy["wave_limits_usd"]:
            raise ValueError("Request tag must identify an admitted wave")
        key = hashlib.sha256(encoded).hexdigest()
        with hosted.exclusive_lock(self.directory / "ledger.lock"):
            ledger = self._load()
            if ledger.get("concurrent_policy", self.policy) != self.policy:
                raise RuntimeError("Existing concurrent policy differs; explicit offline reconciliation required")
            if ledger.get("concurrent_spend_blocked"):
                raise RuntimeError("Concurrent admission blocked after reservation overrun")
            entries = ledger["requests"]
            for entry in entries:
                if entry.get("concurrent_state") == "in_flight" and (
                    (self.directory / f"response-{entry['index']:03d}.json").exists()
                    or (self.directory / f"response-{entry['index']:03d}.oversized-prefix.bin").exists()
                ):
                    raise RuntimeError("Retained response awaits settlement; concurrent admission blocked")
                if entry.get("gateway", "openrouter") != "openrouter" or entry.get("request_sha256") != key:
                    continue
                matched_policy = self.policy.get("allow_matched_replicates", False)
                if matched_policy and entry.get("tag") == tag:
                    raise RuntimeError("Identical matched replicate tag already retained; no automatic retry")
                if (
                    matched_policy and entry.get("concurrent_state") == "in_flight" and not entry.get("error")
                    and entry.get("tag", "").split("/", 1)[0] == "P003" and wave == "P003"
                ):
                    continue  # Same input, independently named arm; all reservations still count.
                if entry.get("error") or not entry.get("response_file") or entry.get("concurrent_state") == "in_flight":
                    raise RuntimeError("Identical request is in flight, failed or unresolved; no automatic retry")
            if sum(e.get("concurrent_state") == "in_flight" for e in entries) >= self.policy["max_inflight"]:
                raise RuntimeError("Persistent concurrent in-flight limit reached")
            charged = math.fsum(hosted.accounted_cost(e["accounted_usd"]) for e in entries)
            wave_charged = math.fsum(
                hosted.accounted_cost(e["accounted_usd"]) for e in entries if e.get("tag", "").split("/", 1)[0] == wave
            )
            prior = hosted.PRIOR_RENTAL + self._client._prior_api_cost()  # noqa: SLF001 - reuse existing accounting.
            campaign_limit = min(
                hosted.CAMPAIGN_LIMIT, hosted.accounted_cost(ledger.get("campaign_limit_usd", hosted.CAMPAIGN_LIMIT))
            )
            total_limit = min(
                hosted.TOTAL_LIMIT, hosted.accounted_cost(ledger.get("authorized_total_usd", hosted.TOTAL_LIMIT))
            )
            if (
                charged + reservation > campaign_limit
                or prior + charged + reservation > total_limit
                or wave_charged + reservation > self.policy["wave_limits_usd"][wave]
            ):
                raise RuntimeError("Reservation exceeds atomic campaign, cumulative or wave cap")
            from bench.research_policy import admit_wave  # noqa: PLC0415 - same shared locked wave policy.

            admit_wave(ledger, tag, reservation)
            index = len(entries)
            entry = {
                "index": index,
                "tag": tag,
                "gateway": "openrouter",
                "requested_model": body["model"],
                "request_sha256": key,
                "request_bytes": len(encoded),
                "force_transmission": True,
                "case_count": len(body["input"])
                if body["model"] in hosted.EMBEDDING_MODELS
                else len({name.rsplit("_", 1)[0] for name in body["questions"]})
                if body["model"] in hosted.DECISION_MODELS
                else len(body["response_format"]["json_schema"]["schema"]["properties"]["answers"]["properties"]),
                "accounted_usd": reservation,
                "reservation_usd": reservation,
                "cost_status": "reserved",
                "prior_accounted_usd": prior,
                "started_at": time.time(),
                "concurrent_state": "in_flight",
                "reservation_uuid": uuid.uuid4().hex,
            }
            (self.directory / f"request-{index:03d}.json").write_bytes(encoded)
            ledger["concurrent_policy"] = deepcopy(self.policy)
            entries.append(entry)
            hosted.checkpoint(self.ledger, ledger)
            return deepcopy(entry)

    def _settle_locked(
        self, ledger: dict[str, Any], reservation: dict[str, Any], completed: dict[str, Any]
    ) -> dict[str, Any]:
        """Patch one reservation while the caller holds the shared ledger lock."""
        matches = [e for e in ledger["requests"] if e.get("reservation_uuid") == reservation["reservation_uuid"]]
        if len(matches) != 1:
            raise RuntimeError("Unique reservation missing; settlement refused")
        current = matches[0]
        if any(
            current.get(k) != reservation[k]
            for k in ("index", "request_sha256", "accounted_usd", "cost_status", "concurrent_state")
        ):
            raise RuntimeError("Reservation changed externally; stale settlement refused")
        current.update({k: deepcopy(v) for k, v in completed.items() if k in SETTLEMENT_FIELDS})
        if current.get("reservation_exceeded"):
            ledger["concurrent_spend_blocked"] = {
                "reason": "provider_or_catalog_charge_exceeded_reservation",
                "index": current["index"],
            }
        hosted.checkpoint(self.ledger, ledger)
        return deepcopy(current)

    def _annotate_telemetry(self, reservation: dict[str, Any], telemetry: object) -> dict[str, Any]:
        with hosted.exclusive_lock(self.directory / "ledger.lock"):
            ledger = self._load()
            matches = [e for e in ledger["requests"] if e.get("reservation_uuid") == reservation["reservation_uuid"]]
            if len(matches) != 1 or any(
                matches[0].get(k) != reservation[k] for k in ("index", "request_sha256")
            ):
                raise RuntimeError("Unique telemetry reservation missing or changed")
            matches[0]["telemetry"] = deepcopy(telemetry)
            hosted.checkpoint(self.ledger, ledger)
            return deepcopy(matches[0])

    def request(
        self,
        body: dict[str, Any],
        *,
        tag: str,
        max_body_bytes: int = hosted.MAX_BODY_BYTES,
        replay: bool = False,
        reservation_usd: float = hosted.RESERVATION,
        retry_failed_index: int | None = None,
        retry_reason: str | None = None,
    ) -> dict[str, Any]:
        """Reserve, transmit once outside the lock, and uniquely settle after reload."""
        if replay is not False or retry_failed_index is not None or retry_reason is not None:
            raise ValueError("Concurrent client is fresh-only with no replay or retry")
        hosted.validate_request_reservation(reservation_usd)
        if type(max_body_bytes) is not int or not 1 <= max_body_bytes <= hosted.MAX_IMAGE_BODY_BYTES:
            raise ValueError("Request byte admission exceeds bounded image ceiling")
        encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
        frozen = json.loads(encoded)
        if (
            len(encoded) > max_body_bytes
            or frozen["model"] not in hosted.HOSTED_MODELS
            or (frozen["model"] in hosted.DECISION_MODELS and len(frozen["questions"]) > hosted.MAX_QUESTIONS)
            or (
                frozen["model"] in hosted.EMBEDDING_MODELS
                and (not isinstance(frozen.get("input"), list) or not 1 <= len(frozen["input"]) <= hosted.MAX_QUESTIONS)
            )
        ):
            raise ValueError("Request exceeds frozen model/input admission")
        reservation = self._reserve(frozen, encoded, tag, reservation_usd)
        entry = deepcopy(reservation)
        endpoint = (
            "v1/embeddings"
            if frozen["model"] in hosted.EMBEDDING_MODELS
            else "alpha/decisions"
            if frozen["model"] in hosted.DECISION_MODELS
            else "v1/chat/completions"
        )
        request = urllib.request.Request(
            "https://openrouter.ai/api/" + endpoint,
            data=encoded,
            headers={"Authorization": "Bearer " + self._client.key, "Content-Type": "application/json"},
            method="POST",
        )
        start = time.perf_counter()
        result: dict[str, Any] = {}
        failure = False
        payload: bytes | None = None
        try:
            with self._opener(request, timeout=90) as response:
                payload = response.read(hosted.MAX_RESPONSE_BYTES + 1)
        except Exception as error:
            failure = True
            entry["error"] = f"HTTP {error.code}" if isinstance(error, urllib.error.HTTPError) else type(error).__name__
            if isinstance(error, urllib.error.HTTPError):
                entry["http_error_diagnostic"] = safe_http_error(error)
        try:
            # Only bounded local receipt IO, parsing and catalog accounting hold
            # this lock. No transport, response read or telemetry runs here.
            with hosted.exclusive_lock(self.directory / "ledger.lock"):
                try:
                    if payload is not None:
                        if len(payload) > hosted.MAX_RESPONSE_BYTES:
                            name = f"response-{entry['index']:03d}.oversized-prefix.bin"
                            (self.directory / name).write_bytes(payload)
                            entry.update(response_prefix_file=name, response_truncated=True)
                            raise ValueError("Response exceeds retained payload admission")
                        name = f"response-{entry['index']:03d}.json"
                        (self.directory / name).write_bytes(payload)
                        entry["response_file"] = name
                        result = json.loads(payload)
                        if not isinstance(result, dict):
                            raise ValueError("Response must be a JSON object")
                        entry.update(
                            served_model=result.get("model"),
                            provider=result.get("provider"),
                            generation_id=result.get("id")
                        )
                        self._client._account_result(frozen, result, entry)  # noqa: SLF001 - identical offline pricing.
                except Exception as error:
                    failure = True
                    entry["error"] = type(error).__name__
                entry.update(
                    elapsed_ms=(time.perf_counter() - start) * 1000,
                    concurrent_state="failed" if failure else "completed",
                    completed_at=time.time(),
                )
                if hosted.accounted_cost(entry["accounted_usd"]) > reservation_usd:
                    entry["reservation_exceeded"] = True
                settled = self._settle_locked(self._load(), reservation, entry)
        except Exception as error:
            # Preserve the existing best-effort trace attempt even when the
            # financial checkpoint fails; its independent marker is retained.
            with suppress(Exception):
                self._client._telemetry(frozen, result if isinstance(result, dict) else {}, entry)  # noqa: SLF001
            message = (
                f"Settlement failed ({type(error).__name__}); "
                "unique reservation and any raw response retained; no retransmission"
            )
            raise RuntimeError(message) from None
        try:
            telemetry = self._client._telemetry(frozen, result if isinstance(result, dict) else {}, settled)  # noqa: SLF001 - preserve optional traces outside lock.
        except Exception as error:
            telemetry = {"status": "error", "error": type(error).__name__}
        try:
            settled = self._annotate_telemetry(reservation, telemetry)
        except Exception as error:
            raise RuntimeError(
                f"Telemetry checkpoint failed ({type(error).__name__}); "
                "financial accounting retained; no retransmission"
            ) from None
        if failure:
            raise RuntimeError(
                f"Hosted call failed ({settled['error']}); accounting retained; no automatic retry"
            ) from None
        return {"result": result, "entry": settled, "replayed": False}
