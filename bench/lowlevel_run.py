"""L001 frozen DEV grouping decisions: explicit hosted execution and local scoring.

Outputs describe target-description partitions, not complete table reconstruction.
Gold is read only after frozen requests have finished executing. Probabilities are
uncalibrated distributions; mechanical source conservation does not prove quality.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, NoReturn

from bench.decision_hosted import RESERVATION, DecisionClient, accounted_cost, checkpoint, exclusive_lock, probability
from bench.reprice_model_rates import number, request_cost
from bench.silver import rss_bytes

CHOICES = ("join", "split", "unresolved")
SUM_TOLERANCE = 0.015000001
WAVE_LIMIT = 5.0
TAG_PREFIX = "L001/"
MAX_BODY_BYTES = 200_000
MAX_BATCH = 3
ENCODING_COUNT = 3
TARGET_CHUNKS = 2


def _fail(reason: str) -> NoReturn:
    message = f"L001: {reason}"
    raise ValueError(message)


def _path(directory: Path, filename: str) -> Path:
    base = directory.resolve()
    candidate = (base / filename).resolve()
    if not candidate.is_relative_to(base) or {"heldout-silver", "silver-heldout-v1"}.intersection(candidate.parts):
        _fail("artifact path escapes admitted DEV directory")
    return candidate


def verify_directory(directory: Path) -> dict[str, Any]:
    """Delegate complete source/request/observation freeze checks to the preparer."""
    _path(directory, "manifest.json")
    return importlib.import_module("bench.lowlevel_evidence").verify(directory)


def parse_response(result: dict[str, Any], count: int) -> list[dict[str, Any]]:
    """Validate complete Choice distributions and abstain on tied maxima."""
    if not 1 <= count <= MAX_BATCH:
        _fail("batch size must be one through three")
    if not isinstance(result, dict):
        _fail("response must be an object")
    answers = result.get("answers")
    if not isinstance(answers, dict) or set(answers) != {f"q{i}" for i in range(count)}:
        _fail("response question keys differ from frozen request")
    parsed = []
    for index in range(count):
        answer = answers[f"q{index}"]
        if not isinstance(answer, dict) or answer.get("type") != "choice":
            _fail("response is not a typed Choice")
        raw = answer.get("probabilities")
        if not isinstance(raw, dict) or set(raw) != set(CHOICES):
            _fail("probability options differ from declared choices")
        values = {key: probability(raw[key]) for key in CHOICES}
        total = sum(values.values())
        if abs(total - 1) > SUM_TOLERANCE:
            _fail("probabilities do not sum to one within rounding tolerance")
        choice = answer.get("choice")
        best = max(values.values())
        if not isinstance(choice, str) or choice not in values or values[choice] != best:
            _fail("provider Choice is not a declared maximum")
        winners = [key for key in CHOICES if values[key] == best]
        ordered = sorted(values.values(), reverse=True)
        parsed.append(
            {
                "choice": choice if len(winners) == 1 else "unresolved",
                "raw_choice": choice,
                "raw_probabilities": values,
                "probabilities": {key: value / total for key, value in values.items()},
                "normalization_delta": total - 1,
                "tie_abstention": len(winners) != 1,
                "margin": (ordered[0] - ordered[1]) / total,
                "provider_confidence": answer.get("confidence"),
                "calibration": "unvalidated",
            }
        )
    return parsed


def partition_contract(observation: dict[str, Any]) -> dict[str, list[list[str]]]:
    """Derive the two-chunk relation independently of supplied candidate aliases."""
    chunks = observation.get("target_atoms")
    if (
        not isinstance(chunks, list)
        or len(chunks) != TARGET_CHUNKS
        or any(not isinstance(chunk, list) or not chunk for chunk in chunks)
    ):
        _fail("target partition requires two nonempty source chunks")
    atoms = [atom for chunk in chunks for atom in chunk]
    if any(
        not isinstance(atom, dict) or not isinstance(atom.get("id"), str) or not isinstance(atom.get("text"), str)
        for atom in atoms
    ):
        _fail("target atoms require literal text and string source IDs")
    ids = [atom["id"] for atom in atoms]
    if len(ids) != len(set(ids)) or ids != observation.get("all_target_ids"):
        _fail("observation contains duplicate or omitted target atoms")
    return {"join": [ids], "split": [[atom["id"] for atom in chunk] for chunk in chunks], "unresolved": []}


def materialize(observation: dict[str, Any], choice: str) -> dict[str, Any]:
    """Validate every candidate against the independent source partition contract."""
    if choice not in CHOICES:
        _fail("unknown grouping choice")
    contract = partition_contract(observation)
    if observation.get("candidates") != contract:
        _fail("candidate source partitions differ from ordered join/split contract")
    atoms = [atom for chunk in observation["target_atoms"] for atom in chunk]
    ids = [atom["id"] for atom in atoms]
    groups = observation["candidates"][choice]
    selected = [source for group in groups for source in group]
    if any(not group for group in groups) or len(selected) != len(set(selected)) or not set(selected) <= set(ids):
        _fail("candidate duplicates or fabricates source ownership")
    if choice != "unresolved" and Counter(selected) != Counter(ids):
        _fail("resolved candidate omits target sources")
    if choice == "unresolved" and groups:
        _fail("unresolved candidate must leave targets unassigned")
    by_id = {atom["id"]: atom for atom in atoms}
    unresolved = [source for source in ids if source not in set(selected)]
    return {
        "choice": choice,
        "groups": [list(group) for group in groups],
        "group_text_semantics": "literal glyph concatenation; no inferred chunk separator",
        "group_text": ["".join(by_id[source]["text"] for source in group) for group in groups],
        "unresolved_ids": unresolved,
        "unresolved_atoms": [by_id[source] for source in unresolved],
        "conservation": Counter(selected + unresolved) == Counter(ids),
        "scope": "two target-description chunks only; amount/header/cell reconstruction unmeasured",
    }


def score(observation: dict[str, Any], target: dict[str, Any], choice: str) -> dict[str, Any]:
    """Score frozen authored choice and exact description partition separately."""
    output = materialize(observation, choice)
    if target["expected"] not in CHOICES:
        _fail("unknown authored expected relation")
    expected_groups = partition_contract(observation)[target["expected"]]
    expected_unassigned = observation["all_target_ids"] if target["expected"] == "unresolved" else []
    exact = output["groups"] == expected_groups and output["unresolved_ids"] == expected_unassigned
    return {
        "expected": target["expected"],
        "choice_correct": choice == target["expected"],
        "description_partition_exact": exact,
        "answerable": target["expected"] != "unresolved",
        "ambiguous_abstention": target["expected"] == "unresolved" and choice == "unresolved",
        "candidate_oracle": True,
        "output": output,
    }


def wave_admission(
    entries: list[dict[str, Any]], *, tag_prefix: str = TAG_PREFIX, wave_limit: float = WAVE_LIMIT
) -> None:
    """Enforce the persistent cap including failed reservations."""
    charged = sum(accounted_cost(row["accounted_usd"]) for row in entries if row.get("tag", "").startswith(tag_prefix))
    if charged + RESERVATION > wave_limit + 1e-12:
        message = f"{tag_prefix} persistent wave cap exhausted"
        raise RuntimeError(message)


def _entries(client: Any) -> list[dict[str, Any]]:  # noqa: ANN401 - shared or injected transport.
    return json.loads(client.ledger.read_text())["requests"] if client.ledger.exists() else []


def persistent_stops(
    client: Any,  # noqa: ANN401
    models: list[str],
    calls: list[dict[str, Any]],
    *,
    tag_prefix: str = TAG_PREFIX,
) -> dict[str, Any]:
    """Retain model failures across L001 freezes without altering provider charges."""
    path = client.ledger.parent / f"{tag_prefix.rstrip('/')}-model-stops.json"
    registry: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {"schema": 1, "models": {}}
    if registry.get("schema") != 1 or not isinstance(registry.get("models"), dict):
        _fail("persistent model-stop registry is malformed")
    stops = registry["models"]
    for entry in _entries(client):
        tag = entry.get("tag", "")
        if not tag.startswith(tag_prefix) or (not entry.get("error") and entry.get("response_file")):
            continue
        model = entry.get("requested_model") or next(
            (model for model in models if tag.startswith(f"{tag_prefix}{model}/")), None
        )
        if model is not None:
            stops.setdefault(
                model,
                {
                    "reason": f"failed or unsettled {tag_prefix} ledger request",
                    "request_sha256": entry.get("request_sha256"),
                },
            )
    for row in calls:
        if row["status"] == "failed":
            stops.setdefault(
                row["model"],
                {"reason": row.get("reason", f"failed {tag_prefix} request"), "request_sha256": row["request_sha256"]},
            )
    checkpoint(path, registry)
    return stops


def _price(directory: Path, model: str) -> dict[str, Any]:
    path = _path(directory, "catalog-prices.json")
    return json.loads(path.read_text()).get("prices", {}).get(model, {}) if path.exists() else {}


def _evaluation_answers(result: dict[str, Any], count: int, experiment: str | None) -> list[dict[str, Any]]:
    if experiment == "L003":
        from bench.lowlevel_frontier import parse_response as parse_frontier  # noqa: PLC0415

        return parse_frontier(result, count)
    return parse_response(result, count)


def reservation_preflight(request_bytes: int, price: dict[str, Any]) -> float:
    """Screen a one-input-token-per-body-byte estimate against the reservation.

    These native Choice calls request no generative output tokens. This is a
    catalog forecast, separate from actual usage and persistent ledger admission.
    """
    rate = number(price.get("input"))
    if rate is None:
        _fail("frozen catalog input rate is missing")
    forecast = request_bytes * rate
    if forecast > RESERVATION:
        _fail("catalog byte-token forecast exceeds request reservation")
    return forecast


def run(
    directory: Path,
    *,
    client: Any = None,  # noqa: ANN401
    max_requests: int | None = None,
    tag_prefix: str = TAG_PREFIX,
    wave_limit: float = WAVE_LIMIT,
) -> dict[str, Any]:
    """Execute only through the root-owned client, preserving resumable checkpoints."""
    if tag_prefix not in {"L001/", "L004/"} or not 0 < wave_limit <= WAVE_LIMIT:
        _fail("unknown wave or unsupported wave cap")
    manifest = verify_directory(directory)
    if (manifest.get("experiment") == "L004") != (tag_prefix == "L004/"):
        _fail("wave policy differs from frozen experiment")
    if max_requests is not None and (type(max_requests) is not int or max_requests < 1):
        _fail("max_requests must be a positive integer")
    client = DecisionClient() if client is None else client
    with exclusive_lock(client.ledger.parent / "run.lock"):
        # Reverify inside serialization boundary before any body reaches transport.
        manifest = verify_directory(directory)
        return _run_locked(
            directory, manifest, client, max_requests=max_requests, tag_prefix=tag_prefix, wave_limit=wave_limit
        )


def _run_locked(  # noqa: C901, PLR0912, PLR0913
    directory: Path,
    manifest: dict[str, Any],
    client: Any,  # noqa: ANN401 - shared or mocked transport.
    *,
    max_requests: int | None = None,
    tag_prefix: str = TAG_PREFIX,
    wave_limit: float = WAVE_LIMIT,
) -> dict[str, Any]:
    result_path = _path(directory, "results.json")
    manifest_hash = hashlib.sha256(_path(directory, "manifest.json").read_bytes()).hexdigest()
    results: dict[str, Any] = (
        json.loads(result_path.read_text())
        if result_path.exists()
        else {
            "schema": 1,
            "manifest_sha256": manifest_hash,
            "status": "running",
            "calls": [],
        }
    )
    if results.get("manifest_sha256") != manifest_hash:
        _fail("retained results belong to another frozen manifest")
    stop_details = persistent_stops(client, manifest["models"], results["calls"], tag_prefix=tag_prefix)
    stopped = set(stop_details).intersection(manifest["models"])
    completed = {row["request_sha256"] for row in results["calls"] if row["status"] in {"ok", "failed"}}
    budget_exhausted = False
    attempted = 0
    slice_limited = False
    start, cpu = time.perf_counter(), time.process_time()
    for record in manifest["records"]:
        digest = record["sha256"]
        if digest in completed:
            continue
        if max_requests is not None and attempted >= max_requests:
            slice_limited = True
            break
        row = next((value for value in results["calls"] if value["request_sha256"] == digest), None)
        if row is None:
            row = {
                "request_sha256": digest,
                "model": record["model"],
                "arm": record["arm"],
                "page_ids": record["page_ids"],
                "request_file": record["request"],
                "status": "pending",
            }
            results["calls"].append(row)
        if record["model"] in stopped or budget_exhausted:
            row.update(
                status="unattempted",
                refused=True,
                reason="persistent model stop" if record["model"] in stopped else "wave cap",
            )
            checkpoint(result_path, results)
            continue
        body_bytes = _path(directory, record["request"]).read_bytes()
        body = json.loads(body_bytes)
        if hashlib.sha256(body_bytes).hexdigest() != digest or len(body_bytes) > MAX_BODY_BYTES:
            _fail("frozen request changed or exceeds byte cap")
        checkpoint(result_path, results)
        try:
            row["reservation_forecast_usd"] = reservation_preflight(len(body_bytes), _price(directory, record["model"]))
            entries = _entries(client)
            known = next((entry for entry in entries if entry.get("request_sha256") == digest), None)
            if known is not None and not known.get("response_file"):
                message = "Previous identical request failed; no retry"
                raise RuntimeError(message)  # noqa: TRY301
            if known is None:
                wave_admission(entries, tag_prefix=tag_prefix, wave_limit=wave_limit)
            attempted += 1
            response = client.request(
                body, tag=f"{tag_prefix}{record['model']}/{record['arm']}/{digest}", max_body_bytes=MAX_BODY_BYTES
            )
            row.update(response=response["result"], entry=response["entry"], replayed=response["replayed"])
            row["usage"] = response["result"].get("usage", {})
            rates = response["entry"].get("catalog_rates", {}) if response["replayed"] else None
            row["cost"] = request_cost(
                response["entry"], row["usage"], rates if rates is not None else _price(directory, record["model"])
            )
            row["http_elapsed_ms"] = response["entry"].get("elapsed_ms")
            row["answers"] = parse_response(response["result"], len(record["page_ids"]))
            row["status"] = "ok"
        except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
            row.update(status="failed", error=type(error).__name__, reason="model stopped on first failure; no retry")
            retained = next((entry for entry in _entries(client) if entry.get("request_sha256") == digest), None)
            if retained is not None:
                row.setdefault("entry", retained)
                row.setdefault("cost", request_cost(retained, row.get("usage", {}), _price(directory, record["model"])))
            if "persistent wave cap exhausted" in str(error):
                budget_exhausted = True
                row.update(status="unattempted", refused=True, reason="wave cap exhausted before transmission")
            else:
                stopped.add(record["model"])
                row["refused"] = retained is None
                stop_details = persistent_stops(client, manifest["models"], results["calls"], tag_prefix=tag_prefix)
        checkpoint(result_path, results)
    resources = {
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss_bytes(),
        "attempted_requests": attempted,
        "measurement": (
            "serial current process perf_counter/process_time; current-exec VmHWM; no sampling; "
            "includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured"
        ),
    }
    if "execution_history" not in results:
        results["execution_history"] = []
        if results.get("execution_resources"):
            results["execution_history"].append({**results["execution_resources"], "legacy_import": True})
    results["execution_history"].append(resources)
    history = results["execution_history"]
    peaks = [row["peak_rss_bytes"] for row in history if row.get("peak_rss_bytes") is not None]
    results.update(
        status="slice_complete" if slice_limited else "complete",
        planned_requests=len(manifest["records"]),
        completed_requests=sum(row["status"] in {"ok", "failed"} for row in results["calls"]),
        invocation_request_limit=max_requests,
        stopped_models=sorted(stopped),
        model_stop_details={model: stop_details[model] for model in sorted(stopped)},
        budget_exhausted=budget_exhausted,
        wave_limit_usd=wave_limit,
        wave_tag_prefix=tag_prefix,
        execution_resources={
            "wall_seconds": sum(row["wall_seconds"] for row in history),
            "cpu_seconds": sum(row["cpu_seconds"] for row in history),
            "peak_rss_bytes": max(peaks) if peaks else None,
            "invocations": len(history),
            "legacy_prior_invocations_unmeasured": any(row.get("legacy_import") for row in history),
            "measurement": (
                "sum of retained serial invocation wall/CPU counters; "
                "maximum process lifetime VmHWM across invocations; "
                "no sampling; includes HTTP waiting, excludes preparation; provider CPU/RAM unmeasured"
            ),
        },
    )
    checkpoint(result_path, results)
    return results


def evaluate(directory: Path) -> dict[str, Any]:  # noqa: C901, PLR0912 - explicit cohort denominators.
    """Verify every frozen input before reading private targets or retained results."""
    manifest = verify_directory(directory)
    targets_path = _path(directory, "private-targets.json")
    if (
        "targets_sha256" in manifest
        and hashlib.sha256(targets_path.read_bytes()).hexdigest() != manifest["targets_sha256"]
    ):
        _fail("private scoring targets changed")
    targets = json.loads(targets_path.read_text())
    by_id = {row["id"]: row for row in targets}
    if len(by_id) != len(targets) or set(by_id) != {page["id"] for page in manifest["pages"]}:
        _fail("target IDs differ from frozen pages")
    observations = {
        page["id"]: json.loads(_path(directory, page["observation_file"]).read_text()) for page in manifest["pages"]
    }
    results_path = _path(directory, "results.json")
    results = json.loads(results_path.read_text()) if results_path.exists() else {"calls": []}
    if results.get("manifest_sha256") not in (
        None,
        hashlib.sha256(_path(directory, "manifest.json").read_bytes()).hexdigest(),
    ):
        _fail("retained results belong to another frozen manifest")
    calls = {row["request_sha256"]: row for row in results["calls"]}
    outcomes = []
    cohort_calls: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in manifest["records"]:
        call = calls.get(record["sha256"], {})
        cohort_calls[record["model"], record["arm"]].append(call)
        answers = (
            _evaluation_answers(call["response"], len(record["page_ids"]), manifest.get("experiment"))
            if call.get("status") == "ok"
            else []
        )
        for index, page_id in enumerate(record["page_ids"]):
            target = by_id[page_id]
            choice = answers[index]["choice"] if answers else None
            outcome = {
                "id": page_id,
                "model": record["model"],
                "arm": record["arm"],
                "logical_id": target["logical_id"],
                "family": target["family"],
                "encoding": target["encoding"],
                "expected": target["expected"],
                "choice": choice,
                "status": call.get("status", "unattempted"),
                "refused": call.get("refused", False),
                "reason": call.get("reason"),
                "score": score(observations[page_id], target, choice) if choice is not None else None,
            }
            outcomes.append(outcome)
    native = []
    for page_id, target in by_id.items():
        observation = observations[page_id]
        native.append(
            {
                "id": page_id,
                "family": target["family"],
                "expected": target["expected"],
                "choice": observation["native_choice"],
                "score": score(observation, target, observation["native_choice"]),
            }
        )
    cohorts = []
    for model in manifest["models"]:
        for arm in manifest["arms"]:
            rows = [row for row in outcomes if (row["model"], row["arm"]) == (model, arm)]
            if not rows:
                continue
            entries = cohort_calls[model, arm]
            unique = {row["entry"]["index"]: row for row in entries if row.get("entry")}
            fresh = [row for row in unique.values() if not row.get("replayed")]
            costs = [row.get("cost", {}).get("effective_usd") for row in fresh]
            total = sum(costs) if costs and all(value is not None for value in costs) else None
            partial = sum(value for value in costs if value is not None)
            http = sum(row.get("http_elapsed_ms") or row.get("entry", {}).get("elapsed_ms", 0) or 0 for row in fresh)
            fresh_inputs = sum(len(call["page_ids"]) for call in fresh if call.get("status") == "ok")
            fresh_exact = 0
            for call in fresh:
                if call.get("status") != "ok":
                    continue
                selected = _evaluation_answers(call["response"], len(call["page_ids"]), manifest.get("experiment"))
                for page_id, answer in zip(call["page_ids"], selected, strict=True):
                    judged = score(observations[page_id], by_id[page_id], answer["choice"])
                    fresh_exact += judged["answerable"] and judged["description_partition_exact"]
            known = [row for row in rows if row["expected"] != "unresolved"]
            ambiguous = [row for row in rows if row["expected"] == "unresolved"]
            exact = sum(bool(row["score"] and row["score"]["description_partition_exact"]) for row in known)
            logical: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                logical[row["logical_id"]].append(row)
            consistent = sum(
                len(values) == ENCODING_COUNT
                and all(row["choice"] is not None for row in values)
                and len({row["choice"] for row in values}) == 1
                for values in logical.values()
            )
            scored = sum(row["score"] is not None for row in rows)
            cohorts.append(
                {
                    "model": model,
                    "arm": arm,
                    "inputs": len(rows),
                    "scored": scored,
                    "known_inputs": len(known),
                    "known_exact": exact,
                    "ambiguous_inputs": len(ambiguous),
                    "ambiguous_abstentions": sum(row["choice"] == "unresolved" for row in ambiguous),
                    "failures": sum(row["status"] == "failed" for row in rows),
                    "unattempted": sum(row["status"] == "unattempted" for row in rows),
                    "refused_inputs": sum(row["refused"] for row in rows),
                    "refusal_reasons": dict(Counter(row["reason"] for row in rows if row["refused"])),
                    "planned_requests": len(entries),
                    "unique_transmissions": len(fresh),
                    "fresh_scored_page_inputs": fresh_inputs,
                    "fresh_correct_regions": fresh_exact,
                    "alias_or_replayed_scored_inputs": scored - fresh_inputs,
                    "completed_requests": sum(row.get("status") in {"ok", "failed"} for row in entries),
                    "conservation_failures": sum(
                        bool(row["score"] and not row["score"]["output"]["conservation"]) for row in rows
                    ),
                    "encoding_consistent_logical_cases": consistent
                    if manifest.get("encoding_comparison", True)
                    else None,
                    "logical_cases": len(logical),
                    "effective_usd": total,
                    "estimated_cost": any(
                        row.get("cost", {}).get("basis") == "catalog estimate" for row in unique.values()
                    ),
                    "replayed_requests": sum(bool(row.get("replayed")) for row in unique.values()),
                    "known_cost_component_usd": partial,
                    "unknown_cost_requests": sum(value is None for value in costs),
                    "http_elapsed_ms": http,
                    "pages_per_usd": fresh_inputs / total if total else None,
                    "correct_regions_per_usd": fresh_exact / total if total else None,
                    "api_only_pages_per_minute": fresh_inputs * 60000 / http if http else None,
                    "per_family": {
                        family: {
                            "inputs": len(subset),
                            "known_exact": sum(
                                bool(
                                    row["score"]
                                    and row["score"]["answerable"]
                                    and row["score"]["description_partition_exact"]
                                )
                                for row in subset
                            ),
                            "ambiguous_abstentions": sum(
                                row["expected"] == "unresolved" and row["choice"] == "unresolved" for row in subset
                            ),
                        }
                        for family in sorted({row["family"] for row in rows})
                        if (subset := [row for row in rows if row["family"] == family])
                    },
                }
            )
    return {
        "schema": 1,
        "scope": "authored DEV description partition only; not independent documents or full tables",
        "cohorts": cohorts,
        "outcomes": outcomes,
        "native_baseline": native,
        "preparation": manifest.get("preparation"),
        "execution_resources": results.get("execution_resources"),
        "execution_history": results.get("execution_history", []),
        "planned_requests": len(manifest["records"]),
        "completed_requests": sum(row.get("status") in {"ok", "failed"} for row in results["calls"]),
        "model_stop_details": results.get("model_stop_details", {}),
        "probabilities": "unreported" if manifest.get("experiment") == "L003" else "uncalibrated",
        "encoding_variants": "correlated; consistency requires all three attempted",
    }


def report(directory: Path) -> dict[str, Any]:
    """Write a standalone local report without credentials or inference."""
    evaluation = evaluate(directory)
    checkpoint(_path(directory, "evaluation.json"), evaluation)
    lines = [
        "# L001 lower-level DEV decisions",
        "",
        evaluation["scope"] + ".",
        "",
        f"Completed requests: {evaluation['completed_requests']}/{evaluation['planned_requests']} planned.",
        "",
        (
            "Known exactness scores only the two target-text chunks. Missing/failed inputs remain in denominators. "
            "Ambiguous abstention is separate. Literal outputs and source ownership are retained in evaluation.json. "
            "Header/value/cell reconstruction is unmeasured. Probabilities are " + evaluation["probabilities"] + "; "
            "the three encodings share each logical template."
        ),
        "",
        (
            "| Model | Arm | Scored/all | Known exact/all | Ambiguous abstain/all | Encoding consistent/all "
            "| USD | Pages/USD | Correct regions/USD | API pages/min |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in evaluation["cohorts"]:

        def metric(key: str, row: dict[str, Any] = row) -> str:
            value = row[key]
            return "unknown" if value is None else f"{value:.6g}"

        encoding = (
            "unmeasured"
            if row["encoding_consistent_logical_cases"] is None
            else f"{row['encoding_consistent_logical_cases']}/{row['logical_cases']}"
        )
        lines.append(
            f"| {row['model']} | {row['arm']} | {row['scored']}/{row['inputs']} "
            f"| {row['known_exact']}/{row['known_inputs']} "
            f"| {row['ambiguous_abstentions']}/{row['ambiguous_inputs']} "
            f"| {encoding} "
            f"| {'~' if row['estimated_cost'] else ''}{metric('effective_usd')} | {metric('pages_per_usd')} "
            f"| {metric('correct_regions_per_usd')} | {metric('api_only_pages_per_minute')} |"
        )
    lines.extend(
        [
            "",
            (
                "Costs preserve positive provider charges; ~ marks frozen-catalog estimates. "
                "Unknown costs never become complete totals. Local replay is not another provider transmission; "
                "rate numerators count successful fresh transmitted page inputs, excluding identical-input aliases. "
                "API timing excludes preparation. Source conservation covers validated outputs only; "
                "invalid/failed inputs are listed separately."
            ),
            "",
            f"Preparation: `{json.dumps(evaluation['preparation'], sort_keys=True)}`.",
            "",
            f"Execution: `{json.dumps(evaluation['execution_resources'], sort_keys=True)}`.",
            "",
        ]
    )
    lines.extend(
        [
            "Native word/physical-line proxy:",
            "",
            "| Family | Known exact/all | Ambiguous abstain/all |",
            "|---|---:|---:|",
        ]
    )
    for family in sorted({row["family"] for row in evaluation["native_baseline"]}):
        rows = [row for row in evaluation["native_baseline"] if row["family"] == family]
        known = [row for row in rows if row["expected"] != "unresolved"]
        unknown = [row for row in rows if row["expected"] == "unresolved"]
        exact = sum(row["score"]["description_partition_exact"] for row in known)
        abstain = sum(row["choice"] == "unresolved" for row in unknown)
        lines.append(f"| {family} | {exact}/{len(known)} | {abstain}/{len(unknown)} |")
    lines.extend(["", "Per-family model results:", ""])
    lines.extend(
        f"- {row['model']} / {row['arm']}: `{json.dumps(row['per_family'], sort_keys=True)}`."
        for row in evaluation["cohorts"]
    )
    lines.extend(["", "Request/refusal accounting:", ""])
    lines.extend(
        f"- {row['model']} / {row['arm']}: {row['completed_requests']}/{row['planned_requests']} "
        f"requests completed; {row['refused_inputs']} page inputs refused; "
        f"reasons `{json.dumps(row['refusal_reasons'], sort_keys=True)}`."
        for row in evaluation["cohorts"]
    )
    lines.extend(["", f"Persistent model stops: `{json.dumps(evaluation['model_stop_details'], sort_keys=True)}`.", ""])
    _path(directory, "report.md").write_text("\n".join(lines))
    return evaluation


def main() -> None:
    """Default to offline reporting; execution requires an explicit flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--max-requests", type=int)
    args = parser.parse_args()
    if args.run_hosted:
        run(args.directory, max_requests=args.max_requests)
    print(json.dumps(report(args.directory)["cohorts"], indent=2))


if __name__ == "__main__":
    main()
