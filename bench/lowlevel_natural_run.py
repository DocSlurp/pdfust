"""L011 bounded metered execution and provisional natural DEV reference scores."""

from __future__ import annotations

import argparse
import importlib
import json
import random
import shutil
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.decision_hosted import RESERVATION, accounted_cost, checkpoint, exclusive_lock
from bench.lowlevel_evidence import digest, encode, write
from bench.lowlevel_images import MODELS
from bench.lowlevel_natural import ARMS
from bench.lowlevel_natural import request as source_request
from bench.lowlevel_natural import verify as source_verify
from bench.lowlevel_packets import _file
from bench.lowlevel_run import parse_response
from bench.reprice_model_rates import number, request_cost
from bench.silver import guard_path, rss_bytes

ROUTES = (*(("openrouter", model) for model in MODELS), ("vercel", "liquid/d1"))
TAG_PREFIX = "L011/"
WAVE_LIMIT = 5.0
BODY_CAP = 200000
MAX_LEDGER_BYTES = 64 * 1024 * 1024


def request(observation: dict[str, Any], provider: str, model: str, arm: str) -> dict[str, Any]:
    """Preserve the shared source packet; Gateway changes modality transport only."""
    if (provider, model) not in ROUTES:
        message = "Natural execution route outside frozen model inventory"
        raise ValueError(message)
    body = source_request(observation, model, arm)
    if provider == "vercel":
        strings = [part for part in body["state"] if isinstance(part, str)]
        images = [part["image_url"]["url"] for part in body["state"] if isinstance(part, dict)]
        if len(strings) != 1 or len(images) != 1:
            message = "Natural Gateway transport requires one literal source state and one image"
            raise ValueError(message)
        body.update(state="\n".join(strings), images=images)
    return body


def identity(provider: str, body_hash: str) -> str:
    """Keep serving-route identity separate from the exact transport body hash."""
    return digest(encode([provider, body_hash]))


def prepare(source: Path, directory: Path, catalogs: dict[str, Path]) -> dict[str, Any]:  # noqa: C901 - source-before-reference freeze ordering.
    """Freeze every provider/model body before reading separate reviewed references."""
    started, cpu = time.perf_counter(), time.process_time()
    source, directory = guard_path(source).resolve(), guard_path(directory).resolve()
    parent = source_verify(source)
    parent_hash = digest((source / "manifest.json").read_bytes())
    if directory.exists():
        message = "Preserve the existing L011 matrix freeze"
        raise ValueError(message)
    catalog_bytes = {provider: guard_path(catalogs[provider]).read_bytes() for provider in ("openrouter", "vercel")}
    prices = {provider: json.loads(raw)["prices"] for provider, raw in catalog_bytes.items()}
    for provider, model in ROUTES:
        rates = prices[provider].get(model, {})
        if number(rates.get("input")) is None or number(rates.get("output")) is None:
            message = "L011 requires complete published input/output rates for each serving route"
            raise ValueError(message)
    directory.mkdir(parents=True)
    for filename in ("source.pdf", "selection.json", "manifest.json"):
        shutil.copyfile(
            source / filename, directory / ("source-manifest.json" if filename == "manifest.json" else filename)
        )
    for page in parent["pages"]:
        shutil.copyfile(_file(source, page["observation_file"]), _file(directory, page["observation_file"]))
    for provider, raw in catalog_bytes.items():
        (directory / f"catalog-{provider}.json").write_bytes(raw)
    records: list[dict[str, Any]] = []
    for page in parent["pages"]:
        observation = json.loads(_file(directory, page["observation_file"]).read_bytes())
        for arm in ARMS:
            for provider, model in ROUTES:
                body = request(observation, provider, model, arm)
                raw = encode(body)
                if len(raw) > BODY_CAP or len(raw) * prices[provider][model]["input"] > RESERVATION:
                    message = "L011 full-body byte/token forecast exceeds request admission; no truncation"
                    raise ValueError(message)
                filename = f"request-{len(records):04d}.json"
                body_hash = write(directory / filename, body)
                records.append(
                    {
                        "provider": provider,
                        "model": model,
                        "arm": arm,
                        "page_ids": [page["id"]],
                        "request": filename,
                        "sha256": body_hash,
                        "identity_sha256": identity(provider, body_hash),
                        "body_bytes": len(raw),
                    }
                )
    random.Random(17461).shuffle(records)  # noqa: S311 - reproducible source-only schedule.
    # Only now open the reviewed scorer references; no label can select bodies.
    references = (source / "private-references.json").read_bytes()
    reviewed = json.loads(references)
    if reviewed["source_manifest_sha256"] != parent_hash or (
        {row["id"] for row in reviewed["references"]} != {page["id"] for page in parent["pages"]}
    ):
        message = "L011 reviewed references do not identify the complete frozen source"
        raise ValueError(message)
    (directory / "private-references.json").write_bytes(references)
    manifest = {
        "schema": 1,
        "experiment": "L011",
        "pages": parent["pages"],
        "arms": list(ARMS),
        "routes": [list(route) for route in ROUTES],
        "records": records,
        "parent_directory": str(source),
        "parent_manifest_sha256": parent_hash,
        "catalog_sha256": {provider: digest(raw) for provider, raw in catalog_bytes.items()},
        "references_sha256": digest(references),
        "wave_limit_usd": WAVE_LIMIT,
        "reservation_usd": RESERVATION,
        "body_cap": BODY_CAP,
        "logical_pair_count": len(parent["pages"]),
        "source_bytes": parent["source_bytes"],
        "source_sha256": parent["source_sha256"],
        "single_source_aware_review": True,
        "preparation": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "measurement": "serial process counters/VmHWM; no provider requests",
        },
    }
    write(directory / "manifest.json", manifest)
    return manifest


def verify(directory: Path) -> dict[str, Any]:  # noqa: C901 - complete immutable packet checks.
    """Reconstruct complete source-derived model inventory without scoring labels."""
    directory = guard_path(directory).resolve()
    manifest = json.loads((directory / "manifest.json").read_bytes())
    parent = guard_path(Path(manifest["parent_directory"])).resolve()
    original = source_verify(parent)
    if (
        manifest.get("experiment") != "L011"
        or manifest["routes"] != [list(route) for route in ROUTES]
        or manifest["arms"] != list(ARMS)
        or manifest["pages"] != original["pages"]
        or digest((parent / "manifest.json").read_bytes()) != manifest["parent_manifest_sha256"]
        or (directory / "source-manifest.json").read_bytes() != (parent / "manifest.json").read_bytes()
        or digest((directory / "source.pdf").read_bytes()) != original["source_sha256"]
        or manifest.get("wave_limit_usd") != WAVE_LIMIT
        or manifest.get("reservation_usd") != RESERVATION
        or manifest.get("body_cap") != BODY_CAP
    ):
        message = "L011 immutable parent or execution policy changed"
        raise ValueError(message)
    prices = {}
    for provider in ("openrouter", "vercel"):
        raw = (directory / f"catalog-{provider}.json").read_bytes()
        if digest(raw) != manifest["catalog_sha256"][provider]:
            message = "L011 serving catalog changed"
            raise ValueError(message)
        prices[provider] = json.loads(raw)["prices"]
    observations = {}
    for page in manifest["pages"]:
        raw = _file(directory, page["observation_file"]).read_bytes()
        if digest(raw) != page["observation_sha256"]:
            message = "L011 source observation changed"
            raise ValueError(message)
        observations[page["id"]] = json.loads(raw)
    seen, filenames = set(), set()
    for record in manifest["records"]:
        if len(record["page_ids"]) != 1:
            message = "L011 model requests must remain singleton"
            raise ValueError(message)
        ident = record["page_ids"][0]
        key = (record["provider"], record["model"], record["arm"], ident)
        raw = _file(directory, record["request"]).read_bytes()
        body = request(observations[ident], record["provider"], record["model"], record["arm"])
        rate = number(prices[record["provider"]][record["model"]].get("input"))
        if (
            key in seen
            or record["request"] in filenames
            or raw != encode(body)
            or digest(raw) != record["sha256"]
            or len(raw) != record["body_bytes"]
            or len(raw) > BODY_CAP
            or record["identity_sha256"] != identity(record["provider"], record["sha256"])
            or rate is None
            or len(raw) * rate > RESERVATION
        ):
            message = "L011 frozen model packet or inventory changed"
            raise ValueError(message)
        seen.add(key)
        filenames.add(record["request"])
    if seen != {(provider, model, arm, ident) for provider, model in ROUTES for arm in ARMS for ident in observations}:
        message = "L011 model matrix incomplete"
        raise ValueError(message)
    if digest((directory / "private-references.json").read_bytes()) != manifest["references_sha256"]:
        message = "L011 separate reviewed references changed"
        raise ValueError(message)
    return manifest


def _entries(ledger: Path) -> list[dict[str, Any]]:
    if not ledger.exists():
        return []
    ledger = guard_path(ledger)
    if ledger.stat().st_size > MAX_LEDGER_BYTES:
        message = "Shared ledger exceeds distinct 64MiB JSON admission"
        raise ValueError(message)
    with ledger.open("rb") as stream:
        raw = stream.read(MAX_LEDGER_BYTES + 1)
    if len(raw) > MAX_LEDGER_BYTES:
        message = "Shared ledger grew beyond 64MiB during admission"
        raise ValueError(message)
    return json.loads(raw)["requests"]


def _known(entries: list[dict[str, Any]], record: dict[str, Any]) -> dict[str, Any] | None:
    return next(
        (
            entry
            for entry in entries
            if entry.get("gateway", "openrouter") == record["provider"] and entry["request_sha256"] == record["sha256"]
        ),
        None,
    )


def run(directory: Path, *, clients: dict[str, Any], max_requests: int | None = None) -> dict[str, Any]:
    """Use root-owned clients only, under one persistent shared-ledger budget lock."""
    directory = guard_path(directory).resolve()
    verify(directory)
    if (
        set(clients) != {"openrouter", "vercel"}
        or len({str(client.ledger.resolve()) for client in clients.values()}) != 1
        or any(getattr(client, "gateway", "openrouter") != provider for provider, client in clients.items())
        or (max_requests is not None and (type(max_requests) is not int or max_requests < 1))
    ):
        message = "L011 requires two correctly scoped shared-ledger clients and a positive slice limit"
        raise ValueError(message)
    ledger = next(iter(clients.values())).ledger
    with exclusive_lock(ledger.parent / "run.lock"):
        manifest = verify(directory)
        return _run_locked(directory, manifest, clients, ledger, max_requests)


def _run_locked(
    directory: Path, manifest: dict[str, Any], clients: dict[str, Any], ledger: Path, max_requests: int | None
) -> dict[str, Any]:
    path = directory / "results.json"
    manifest_hash = digest((directory / "manifest.json").read_bytes())
    results: dict[str, Any] = (
        json.loads(path.read_bytes())
        if path.exists()
        else {"schema": 1, "manifest_sha256": manifest_hash, "calls": [], "execution_history": []}
    )
    if results.get("manifest_sha256") != manifest_hash:
        message = "L011 results belong to another source/model freeze"
        raise ValueError(message)
    stop_path = ledger.parent / "L011-model-stops.json"
    stopped = json.loads(stop_path.read_bytes()) if stop_path.exists() else {}
    calls = {row["identity_sha256"]: row for row in results["calls"]}
    prices = {
        provider: json.loads((directory / f"catalog-{provider}.json").read_bytes())["prices"] for provider in clients
    }
    start, cpu = time.perf_counter(), time.process_time()
    invoked = 0
    prior_indices = {entry["index"] for entry in _entries(ledger)}
    for record in manifest["records"]:
        ident = record["identity_sha256"]
        if ident in calls and calls[ident]["status"] in ("ok", "failed"):
            continue
        if max_requests is not None and invoked >= max_requests:
            break
        row = {key: record[key] for key in ("identity_sha256", "sha256", "provider", "model", "arm", "page_ids")}
        row["status"] = "pending"
        calls[ident] = row
        results["calls"] = list(calls.values())
        checkpoint(path, results)
        route = record["provider"] + "/" + record["model"]
        entries = _entries(ledger)
        known = _known(entries, record)
        if route in stopped or (known is not None and (known.get("error") or not known.get("response_file"))):
            row.update(status="unattempted", reason="persistent route stop or failed identical body; no retry")
            stopped.setdefault(route, {"identity_sha256": ident, "reason": "prior failure; no retry"})
            checkpoint(stop_path, stopped)
            checkpoint(path, results)
            continue
        wave_accounted = sum(
            accounted_cost(entry["accounted_usd"]) for entry in entries if entry.get("tag", "").startswith(TAG_PREFIX)
        )
        if known is None and wave_accounted + RESERVATION > WAVE_LIMIT + 1e-12:
            row.update(status="unattempted", reason="USD5 persistent wave cap; reservation retained")
            checkpoint(path, results)
            continue
        try:
            invoked += 1
            response = clients[record["provider"]].request(
                json.loads(_file(directory, record["request"]).read_bytes()),
                tag=f"{TAG_PREFIX}{route}/{record['arm']}/{ident}",
                max_body_bytes=BODY_CAP,
                replay=True,
                reservation_usd=RESERVATION,
            )
            row.update(response=response["result"], entry=response["entry"], replayed=response["replayed"])
            row["cost"] = request_cost(
                response["entry"], response["result"].get("usage", {}), prices[record["provider"]][record["model"]]
            )
            row["answer"] = parse_response(response["result"], 1)[0]
            row["status"] = "ok"
        except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
            row.update(
                status="failed", error_type=type(error).__name__, reason="first route failure; no automatic retry"
            )
            retained = _known(_entries(ledger), record)
            if retained is not None:
                row["entry"] = retained
                row.setdefault("cost", request_cost(retained, {}, prices[record["provider"]][record["model"]]))
            stopped[route] = {"identity_sha256": ident, "reason": "failure; explicit investigation required"}
            checkpoint(stop_path, stopped)
        checkpoint(path, results)
    resources = {
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss_bytes(),
        "client_invocations": invoked,
        "fresh_admitted_requests": sum(
            entry["index"] not in prior_indices and entry.get("tag", "").startswith(TAG_PREFIX)
            for entry in _entries(ledger)
        ),
        "measurement": "serial process counters/VmHWM; includes HTTP waiting; remote CPU/RAM unmeasured",
    }
    results["execution_history"].append(resources)
    results.update(
        status="slice_complete" if max_requests is not None and invoked >= max_requests else "complete",
        planned_logical_records=len(manifest["records"]),
        planned_unique_provider_bodies=len({row["identity_sha256"] for row in manifest["records"]}),
        wave_accounted_usd=sum(
            accounted_cost(entry["accounted_usd"])
            for entry in _entries(ledger)
            if entry.get("tag", "").startswith(TAG_PREFIX)
        ),
        wave_limit_usd=WAVE_LIMIT,
        stopped_routes=sorted(stopped),
    )
    checkpoint(path, results)
    return results


def report(directory: Path) -> dict[str, Any]:
    """Score provisional full-source and scope references with complete denominators."""
    directory = guard_path(directory).resolve()
    manifest = verify(directory)
    references = {
        row["id"]: row for row in json.loads((directory / "private-references.json").read_bytes())["references"]
    }
    retained = json.loads((directory / "results.json").read_bytes()) if (directory / "results.json").exists() else {}
    if retained and retained.get("manifest_sha256") != digest((directory / "manifest.json").read_bytes()):
        message = "L011 report results belong to another freeze"
        raise ValueError(message)
    calls = {row["identity_sha256"]: row for row in retained.get("calls", [])}
    summaries: list[dict[str, Any]] = []
    for provider, model in ROUTES:
        for arm in ARMS:
            records = [
                row
                for row in manifest["records"]
                if (row["provider"], row["model"], row["arm"]) == (provider, model, arm)
            ]
            completed, full_matches, scoped_matches = 0, 0, 0
            choices: Counter[str] = Counter()
            statuses: Counter[str] = Counter()
            for record in records:
                call = calls.get(record["identity_sha256"], {})
                statuses[call.get("status", "unattempted")] += 1
                if call.get("status") != "ok":
                    continue
                answer = parse_response(call["response"], 1)[0]
                choice = answer["choice"]
                choices[choice] += 1
                reference = references[record["page_ids"][0]]
                scoped = reference["scope_references"][arm.split("-")[0]]["choice"]
                completed += 1
                full_matches += int(choice == reference["choice"])
                scoped_matches += int(choice == scoped)
            summaries.append(
                {
                    "provider": provider,
                    "model": model,
                    "arm": arm,
                    "planned_pairs": len(records),
                    "completed_pairs": completed,
                    "statuses": dict(statuses),
                    "choices": dict(choices),
                    "full_reference_matches": full_matches,
                    "scope_reference_matches": scoped_matches,
                    "full_reference_agreement_completed": full_matches / completed if completed else None,
                    "scope_reference_agreement_completed": scoped_matches / completed if completed else None,
                }
            )
    unique_entries = {call["entry"]["index"]: call for call in calls.values() if call.get("entry")}
    costs = [
        request_cost(
            call["entry"],
            call.get("response", {}).get("usage", {}),
            json.loads((directory / f"catalog-{call['provider']}.json").read_bytes())["prices"][call["model"]],
        )
        for call in unique_entries.values()
    ]
    complete_cost = (
        sum(cost["effective_usd"] for cost in costs)
        if all(cost["effective_usd"] is not None for cost in costs)
        else None
    )
    effective_known = sum(cost["effective_usd"] for cost in costs if cost["effective_usd"] is not None)
    result = {
        "schema": 1,
        "experiment": "L011",
        "source_pair_count": len(manifest["pages"]),
        "source_bytes": manifest["source_bytes"],
        "planned_logical_records": len(manifest["records"]),
        "request_body_bytes": sum(row["body_bytes"] for row in manifest["records"]),
        "summaries": summaries,
        "costs": costs,
        "effective_usd_complete": complete_cost,
        "known_effective_usd_subtotal": effective_known,
        "unknown_cost_count": sum(cost["effective_usd"] is None for cost in costs),
        "new_entry_indices": [index for index, call in unique_entries.items() if not call.get("replayed", False)],
        "replayed_entry_indices": [index for index, call in unique_entries.items() if call.get("replayed", False)],
        "execution_history": retained.get("execution_history", []),
        "preparation": manifest["preparation"],
        "limitations": "Single source-aware provisional DEV review; 24 overlapping pairs on one page/producer. "
        "Scope changes also change glyph pixel size at fixed image edge. Unknown costs remain unknown.",
    }
    write(directory / "report.json", result)
    lines = [
        "# L011 natural DEV row ownership",
        "",
        result["limitations"],
        "",
        (
            f"Source pairs: {len(manifest['pages'])}; PDF bytes: {manifest['source_bytes']}; "
            f"model inputs: {len(manifest['records'])}; body bytes: {result['request_body_bytes']}."
        ),
        "",
        "| Provider/model | Image | Completed/planned | Full matches | Scope matches | Abstentions |",
        "|---|---|---:|---:|---:|---:|",
    ]
    lines.extend(
        f"| {row['provider']}/{row['model']} | {row['arm']} | {row['completed_pairs']}/{row['planned_pairs']} | "
        f"{row['full_reference_matches']} | {row['scope_reference_matches']} | {row['choices'].get('unresolved', 0)} |"
        for row in summaries
    )
    lines += [
        "",
        (
            f"Complete effective cost: {complete_cost if complete_cost is not None else 'unknown'} USD; "
            f"known subtotal: {effective_known:.6f} USD; unknown entries: {result['unknown_cost_count']}."
        ),
        "Reservations remain ledger admission, separate from charges/estimates. Reported zeros remain in JSON.",
        "",
        "Published frozen rates (USD/token):",
        "",
    ]
    for provider, model in ROUTES:
        rate = json.loads((directory / f"catalog-{provider}.json").read_bytes())["prices"][model]
        lines.append(f"- {provider}/{model}: input={rate.get('input')}, output={rate.get('output')}.")
    lines += [
        "",
        "Local resource measurements (provider CPU/RAM unmeasured):",
        "",
        json.dumps(
            {"preparation": manifest["preparation"], "execution_history": result["execution_history"]},
            separators=(",", ":"),
        ),
    ]
    (directory / "report.md").write_text("\n".join(lines) + "\n")
    return result


def main() -> None:
    """CPU preparation/report by default; explicit hosted mode constructs live clients."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--openrouter-catalog", type=Path)
    parser.add_argument("--gateway-catalog", type=Path)
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--max-requests", type=int)
    args = parser.parse_args()
    if args.source is not None:
        prepare(args.source, args.directory, {"openrouter": args.openrouter_catalog, "vercel": args.gateway_catalog})
    if args.run_hosted:
        GatewayDecisionClient = importlib.import_module("bench.decision_gateway").GatewayDecisionClient  # noqa: N806
        from bench.decision_hosted import DecisionClient  # noqa: PLC0415 - credential-free CPU default.

        run(
            args.directory,
            clients={
                "openrouter": DecisionClient(),
                "vercel": GatewayDecisionClient(catalog_path=args.directory / "catalog-vercel.json"),
            },
            max_requests=args.max_requests,
        )
    print(json.dumps(report(args.directory), separators=(",", ":")))


if __name__ == "__main__":
    main()
