"""L007 exact-body provider cache repeats from source-selected L006 focus RGB arms.

Preparation and reports are offline. Root-owned explicit hosted execution uses
one shared DecisionClient ledger, never local response replay or automatic retry.
Provider counters alone describe cache use; repeated bodies imply no warmth.
"""

# Heterogeneous frozen provider artifacts and injected fake transports.
# ruff: noqa: ANN401, EM101, TRY003, PLR2004, C901, PLR0912
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from bench.decision_cache_probe import body_sha, successful, trial_record
from bench.decision_hosted import (
    MAX_IMAGE_BODY_BYTES,
    RESERVATION,
    DecisionClient,
    accounted_cost,
    checkpoint,
    exclusive_lock,
)
from bench.lowlevel_run import parse_response
from bench.reprice_model_rates import number
from bench.silver import guard_path, rss_bytes

MODELS = ("perplexity/pplx-decider-v1.1-27b", "openai/gpt-6-luna-decisions", "cloudflare/clef-flash", "cloudflare/clef")
ARMS = ("focus-rgb-128", "focus-rgb-512")
TRIALS = 3
REPRESENTATIVES = 3
MAX_CALLS = len(MODELS) * len(ARMS) * REPRESENTATIVES * TRIALS
PREFIX = "L007/"
WAVE_LIMIT = 5.0


def _file(directory: Path, name: str) -> Path:
    if not isinstance(name, str) or Path(name).name != name:
        raise ValueError("Artifact name must be a basename")
    base = guard_path(directory).resolve()
    path = guard_path(base / name).resolve()
    if not path.is_relative_to(base):
        raise ValueError("Artifact symlink escapes directory")
    return path


def _read(path: Path, limit: int = 8_000_000) -> dict[str, Any]:
    with guard_path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("Artifact exceeds byte admission")
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise TypeError("Artifact must be a JSON object")
    return result


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _body(path: Path, expected: str) -> dict[str, Any]:
    if path.stat().st_size > MAX_IMAGE_BODY_BYTES:
        raise ValueError("Request exceeds body admission")
    raw = path.read_bytes()
    body = json.loads(raw)
    if _sha(raw) != expected or body_sha(body) != expected:
        raise ValueError("Frozen body differs from exact client serialization")
    return body


def _rgb(body: dict[str, Any], edge: int) -> None:
    stack, urls, visited = [body], [], 0
    while stack:
        value = stack.pop()
        visited += 1
        if visited > 4096:
            raise ValueError("Request structure exceeds admission")
        if isinstance(value, dict):
            if value.get("type") == "image_url":
                urls.append(value["image_url"]["url"])
            else:
                stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    if len(urls) != 1 or not urls[0].startswith("data:image/png;base64,"):
        raise ValueError("Probe needs exactly one inline PNG image")
    raw = base64.b64decode(urls[0].split(",", 1)[1], validate=True)
    if len(raw) < 33 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        raise ValueError("Inline image is not a PNG")
    width, height, depth, color = struct.unpack(">IIBB", raw[16:26])
    if not width or not height or max(width, height) != edge or (depth, color) != (8, 2):
        raise ValueError("Probe image must have the exact longest edge and RGB8 pixels")


def _representatives(parent: Path, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_pixels = set()
    for page in sorted(pages, key=lambda p: p["id"]):
        raw = _file(parent, page["observation_file"]).read_bytes()
        if _sha(raw) != page["observation_sha256"]:
            raise ValueError("Source observation changed")
        obs = json.loads(raw)
        pixel = obs["pixel_sha256"]
        if pixel in seen_pixels:
            continue
        seen_pixels.add(pixel)
        task = obs["selector"]["task"]
        group = (
            "boundary" if task == "character_boundary" else "wrap-drawings" if obs["drawings"] else "wrap-no-drawings"
        )
        if task not in ("character_boundary", "line_ownership"):
            raise ValueError("Unknown source task")
        groups[group].append(page)
    names = ("boundary", "wrap-no-drawings", "wrap-drawings")
    if any(not groups[name] for name in names):
        raise ValueError("Need three source-only representative strata")
    return [groups[name][0] for name in names]


def prepare(parent: Path, directory: Path) -> dict[str, Any]:
    """Choose three source strata before any response, target or credential access."""
    parent, directory = guard_path(parent).resolve(), guard_path(directory).resolve()
    start, cpu = time.perf_counter(), time.process_time()
    original = _read(_file(parent, "manifest.json"))
    if (
        original.get("experiment") != "L006"
        or original.get("kind") != "focus"
        or set(original["models"]) != set(MODELS)
    ):
        raise ValueError("Probe requires the four-model L006 focus freeze")
    selected = _representatives(parent, original["pages"])
    for page in selected:
        source = _file(parent, page["source_file"])
        if source.stat().st_size > 10_000_000 or _sha(source.read_bytes()) != page["source_sha256"]:
            raise ValueError("Selected source PDF changed or exceeds admission")
    ids = {p["id"] for p in selected}
    records = [r for r in original["records"] if r["arm"] in ARMS and r["page_ids"] in [[ident] for ident in ids]]
    wanted = {(m, a, ident) for m in MODELS for a in ARMS for ident in ids}
    seen = {(r["model"], r["arm"], r["page_ids"][0]) for r in records}
    if seen != wanted or len(records) != len(wanted):
        raise ValueError("Selected parent body inventory is incomplete or duplicated")
    bodies = []
    for record in sorted(records, key=lambda r: (r["model"], r["arm"], r["page_ids"])):
        body = _body(_file(parent, record["request"]), record["sha256"])
        if body["model"] != record["model"] or set(body.get("questions", {})) != {"q0"}:
            raise ValueError("Parent body is not an admitted singleton")
        _rgb(body, int(record["arm"].rsplit("-", 1)[1]))
        bodies.append((record, body))
    if len({r["sha256"] for r, _ in bodies}) != len(bodies):
        raise ValueError("Distinct representative conditions must have distinct bodies")
    if directory.exists():
        raise ValueError("Preserve existing probe freeze")
    directory.mkdir(parents=True)
    frozen = []
    for index, (record, _body_value) in enumerate(bodies):
        raw = _file(parent, record["request"]).read_bytes()
        name = f"request-{index:03d}.json"
        _file(directory, name).write_bytes(raw)
        frozen.append({**record, "request": name, "parent_request": record["request"], "body_bytes": len(raw)})
    catalog = _file(parent, "catalog-prices.json").read_bytes()
    if _sha(catalog) != original["catalog_sha256"]:
        raise ValueError("Parent catalog changed")
    _file(directory, "catalog-prices.json").write_bytes(catalog)
    manifest = {
        "experiment": "L007",
        "schema": 1,
        "split": "DEV",
        "models": list(MODELS),
        "arms": list(ARMS),
        "parent_directory": str(parent),
        "parent_manifest_sha256": _sha(_file(parent, "manifest.json").read_bytes()),
        "representatives": selected,
        "records": frozen,
        "catalog_sha256": _sha(catalog),
        "maximum_calls": MAX_CALLS,
        "trials": TRIALS,
        "wave_limit_usd": WAVE_LIMIT,
        "selection": (
            "Lexicographic minimum source ID per unique pixel hash, then boundary/wrap without drawings/"
            "wrap with drawings; no responses or targets"
        ),
        "preparation_resources": {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "measurement": "serial CPU; current-exec VmHWM; no sampling, no rendering/network",
        },
    }
    checkpoint(_file(directory, "manifest.json"), manifest)
    verify(directory)
    return manifest


def verify(directory: Path) -> dict[str, Any]:
    """Verify complete lineage and unchanged body bytes without scoring gold."""
    manifest = _read(_file(directory, "manifest.json"))
    if (
        manifest.get("experiment") != "L007"
        or manifest.get("split") != "DEV"
        or manifest["models"] != list(MODELS)
        or tuple(manifest["arms"]) != ARMS
        or manifest["maximum_calls"] != MAX_CALLS
        or manifest["trials"] != TRIALS
        or manifest["wave_limit_usd"] != WAVE_LIMIT
    ):
        raise ValueError("Probe policy changed")
    parent = guard_path(Path(manifest["parent_directory"]))
    if _sha(_file(parent, "manifest.json").read_bytes()) != manifest["parent_manifest_sha256"]:
        raise ValueError("Parent manifest changed")
    original = _read(_file(parent, "manifest.json"))
    if manifest["representatives"] != _representatives(parent, original["pages"]):
        raise ValueError("Source selection changed")
    for page in manifest["representatives"]:
        source = _file(parent, page["source_file"])
        if source.stat().st_size > 10_000_000 or _sha(source.read_bytes()) != page["source_sha256"]:
            raise ValueError("Selected source PDF changed or exceeds admission")
    by_name = {r["request"]: r for r in original["records"]}
    seen = set()
    for record in manifest["records"]:
        source = by_name[record["parent_request"]]
        if any(record[k] != source[k] for k in ("model", "arm", "page_ids", "sha256")):
            raise ValueError("Parent request identity changed")
        body = _body(_file(directory, record["request"]), record["sha256"])
        if _file(directory, record["request"]).stat().st_size != record["body_bytes"]:
            raise ValueError("Frozen request byte metadata changed")
        if _file(directory, record["request"]).read_bytes() != _file(parent, source["request"]).read_bytes():
            raise ValueError("Copied body changed")
        _rgb(body, int(record["arm"].rsplit("-", 1)[1]))
        key = (record["model"], record["arm"], record["page_ids"][0])
        if key in seen:
            raise ValueError("Duplicate probe condition")
        seen.add(key)
    wanted = {(m, a, p["id"]) for m in MODELS for a in ARMS for p in manifest["representatives"]}
    if seen != wanted or _sha(_file(directory, "catalog-prices.json").read_bytes()) != manifest["catalog_sha256"]:
        raise ValueError("Probe inventory or catalog changed")
    return manifest


def admission(entries: list[dict[str, Any]]) -> None:
    """Count all persistent prefix charges/reservations, never reset by output path."""
    wave = [e for e in entries if e.get("tag", "").startswith(PREFIX)]
    if (
        len(wave) >= MAX_CALLS
        or sum(accounted_cost(e["accounted_usd"]) for e in wave) + RESERVATION > WAVE_LIMIT + 1e-12
    ):
        raise RuntimeError("L007 persistent wave call/reservation cap exhausted")


def _entries(client: Any) -> list[dict[str, Any]]:
    return _read(client.ledger)["requests"] if client.ledger.exists() else []


def _response(client: Any, entry: dict[str, Any]) -> dict[str, Any]:
    return _read(_file(client.ledger.parent, entry["response_file"]), 2_000_000)


def _original(parent: Path, record: dict[str, Any], client: Any) -> dict[str, Any] | None:
    path = _file(parent, "results.json")
    if not path.exists():
        return None
    parent_results = _read(path)
    if parent_results.get("manifest_sha256") is not None and parent_results["manifest_sha256"] != _sha(
        _file(parent, "manifest.json").read_bytes()
    ):
        raise ValueError("Parent results identify another freeze")
    completed = [
        r
        for r in parent_results.get("calls", [])
        if r.get("request_sha256") == record["sha256"] and r.get("status") == "ok"
    ]
    if not completed:
        return None
    for entry in _entries(client):
        if (
            entry.get("request_sha256") == record["sha256"]
            and entry.get("response_file")
            and successful(_response(client, entry))
        ):
            try:
                parse_response(_response(client, entry), 1)
            except (ValueError, KeyError, TypeError):
                continue
            return entry
    return None


def summarize(state: dict[str, Any]) -> dict[str, Any]:
    """Report complete/partial costs, throughput and choice consistency separately."""
    rows = state["records"]
    transmissions = {r["entry"]["index"]: r for r in rows if r.get("entry", {}).get("tag", "").startswith(PREFIX)}
    physical = list(transmissions.values())
    costs = [r.get("effective_pricing", {}).get("effective_usd") for r in physical]
    total = sum(c for c in costs if c is not None) if physical and all(c is not None for c in costs) else None
    valid = [r for r in physical if r["status"] == "ok"]
    elapsed = [number(r.get("elapsed_ms")) for r in physical]
    http_ms = sum(t for t in elapsed if t is not None) if all(t is not None for t in elapsed) else None
    wall = sum(r["wall_seconds"] for r in state.get("execution_history", []))
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["request_sha256"]].append(row)
    complete = [g for g in groups.values() if len(g) == TRIALS and all(r["status"] == "ok" for r in g)]
    strata = []
    for model in MODELS:
        for arm in ARMS:
            for trial in range(TRIALS):
                subset = [r for r in physical if (r.get("model"), r.get("arm"), r.get("trial")) == (model, arm, trial)]
                amounts = [r.get("effective_pricing", {}).get("effective_usd") for r in subset]
                usd = (
                    sum(a for a in amounts if a is not None) if subset and all(a is not None for a in amounts) else None
                )
                times = [number(r.get("elapsed_ms")) for r in subset]
                ms = sum(t for t in times if t is not None) if times and all(t is not None for t in times) else None
                pages = sum(r["status"] == "ok" for r in subset)
                strata.append(
                    {
                        "model": model,
                        "arm": arm,
                        "trial": trial,
                        "transmissions": len(subset),
                        "successful_page_choices": pages,
                        "effective_usd": usd,
                        "pages_per_usd": pages / usd if usd is not None and usd > 0 else None,
                        "pages_per_minute_http": 60000 * pages / ms if ms is not None and ms > 0 else None,
                    }
                )
    return {
        "strata": strata,
        "actual_transmissions": len(physical),
        "successful_page_choices": len(valid),
        "local_replays": sum(bool(r.get("local_replayed")) for r in rows),
        "unattempted": sum(r["status"] == "unattempted" for r in rows),
        "effective_usd": total,
        "known_effective_subtotal_usd": sum(c for c in costs if c is not None),
        "unknown_cost_transmissions": sum(c is None for c in costs),
        "pages_per_usd": len(valid) / total if total is not None and total > 0 else None,
        "pages_per_minute_http": 60000 * len(valid) / http_ms if http_ms is not None and http_ms > 0 else None,
        "pages_per_minute_wall": 60 * len(valid) / wall if wall > 0 else None,
        "complete_triplets": len(complete),
        "consistent_triplets": sum(len({r["choice"] for r in g}) == 1 for g in complete),
        "provider_reported_positive_usd": sum(number(r.get("provider_reported_usd")) or 0 for r in physical),
        "reported_zero_cost_transmissions": sum(number(r.get("provider_reported_usd")) == 0 for r in physical),
        "unsettled_reservations_usd": sum(
            accounted_cost(r["entry"]["accounted_usd"]) for r in physical if r["entry"].get("cost_status") == "reserved"
        ),
        "cache_read_unknown": sum(
            not r.get("cache_read_counter_present") or not r.get("cache_counters_valid") for r in physical
        ),
        "cache_positive_read_transmissions": sum(
            r.get("cache_counters_valid", False) and (number(r.get("cache_read_tokens")) or 0) > 0 for r in physical
        ),
        "quality": "choice consistency only; no gold, accuracy, cache warmth or semantic-quality claim",
    }


def report(state: dict[str, Any], directory: Path) -> None:
    """Write locally retained metrics without additional provider requests."""
    state["summary"] = summarize(state)
    checkpoint(_file(directory, "results.json"), state)
    lines = [
        "# L007 provider cache repeat probe",
        "",
        (
            "Exact L006 RGB bodies, three actual transmissions each; replay=False. Initial does not mean cold "
            "and repeats do not mean warm. Local artifact reuse is body preparation, not free response replay. "
            "Missing cache counters remain unknown. Costs prefer positive provider charges, otherwise separately "
            "labeled published-rate token estimates; incomplete totals stay unknown. No gold was read."
        ),
        "",
        "```json",
        json.dumps(state["summary"], indent=2),
        "```",
        "",
        (
            "| Model | Arm | Page | Trial | Status | Provider | Served model | Cached read | Reported USD | "
            "Effective USD |"
        ),
        "|---|---|---|---:|---|---|---|---:|---:|---:|",
    ]
    for row in state["records"]:
        values = [
            row["model"],
            row["arm"],
            row["page_id"],
            row["trial"],
            row["status"],
            row.get("provider"),
            row.get("served_model"),
            row.get("cache_read_tokens"),
            row.get("provider_reported_usd"),
            row.get("effective_pricing", {}).get("effective_usd"),
        ]
        lines.append("| " + " | ".join("unknown" if v is None else str(v) for v in values) + " |")
    _file(directory, "report.md").write_text("\n".join(lines) + "\n")


def run(
    directory: Path, *, hosted: bool = False, client: Any = None, max_requests: int | None = None
) -> dict[str, Any]:
    """Execute only under explicit root opt-in; injected fake clients need no key."""
    manifest = verify(directory)
    if not hosted:
        return {"status": "prepared; no calls", "bodies": len(manifest["records"]), "maximum_calls": MAX_CALLS}
    if max_requests is not None and (type(max_requests) is not int or max_requests < 1):
        raise ValueError("max_requests must be a positive integer")
    client = DecisionClient() if client is None else client
    parent = guard_path(Path(manifest["parent_directory"]))
    identity = _sha(_file(directory, "manifest.json").read_bytes())
    with exclusive_lock(client.ledger.parent / "run.lock"):
        verify(directory)
        wave_path = _file(client.ledger.parent, "l007-wave.json")
        state: dict[str, Any] = (
            _read(wave_path)
            if wave_path.exists()
            else {"schema": 1, "manifest_sha256": identity, "records": [], "execution_history": []}
        )
        if state["manifest_sha256"] != identity:
            raise ValueError("Persistent L007 wave belongs to another freeze; output changes cannot reset it")
        start, cpu, attempted = time.perf_counter(), time.process_time(), 0
        prices = _read(_file(directory, "catalog-prices.json")).get("prices", {})
        stopped = {r["model"] for r in state["records"] if r["status"] == "failed"}
        for item in manifest["records"]:
            for trial in range(TRIALS):
                tag = f"{PREFIX}{item['model']}/{item['arm']}/{item['page_ids'][0]}/trial-{trial}"
                existing = next((r for r in state["records"] if r["tag"] == tag), None)
                if existing and existing["status"] in {"ok", "failed"}:
                    continue
                if max_requests is not None and attempted >= max_requests:
                    break
                row = {
                    "tag": tag,
                    "model": item["model"],
                    "arm": item["arm"],
                    "page_id": item["page_ids"][0],
                    "trial": trial,
                    "request_sha256": item["sha256"],
                    "status": "pending",
                    "body_artifact_reused": True,
                }
                if existing:
                    state["records"].remove(existing)
                state["records"].append(row)
                known = next((e for e in _entries(client) if e.get("tag") == tag), None)
                original = _original(parent, item, client)
                if original is None or item["model"] in stopped:
                    row.update(
                        status="unattempted",
                        reason="no completed successful parent response"
                        if original is None
                        else "model stopped; no retry",
                    )
                    continue
                row["original_index"] = original["index"]
                row["original_route"] = {
                    "provider": original.get("provider"),
                    "served_model": original.get("served_model"),
                }
                checkpoint(wave_path, state)
                try:
                    if known:
                        if known.get("request_sha256") != item["sha256"] or not known.get("response_file"):
                            raise RuntimeError("Interrupted or failed retained transmission; no retry")  # noqa: TRY301
                        response: dict[str, Any] = {
                            "entry": known,
                            "result": _response(client, known),
                            "replayed": False,
                        }
                        row["ledger_recovered"] = True
                    else:
                        admission(_entries(client))
                        price = prices.get(item["model"], {})
                        rate = number(price.get("input"))
                        if rate is None or item["body_bytes"] * rate > RESERVATION:
                            raise ValueError("Frozen catalog byte-token forecast exceeds reservation or lacks rates")  # noqa: TRY301
                        attempted += 1
                        response = client.request(
                            _body(_file(directory, item["request"]), item["sha256"]),
                            tag=tag,
                            replay=False,
                            max_body_bytes=MAX_IMAGE_BODY_BYTES,
                            reservation_usd=RESERVATION,
                        )
                    prepared = {
                        "model": item["model"],
                        "condition": item["arm"],
                        "request_sha256": item["sha256"],
                        "original_index": original["index"],
                    }
                    row.update(trial_record(prepared, trial, response, prices.get(item["model"], {})))
                    row["choice"] = parse_response(response["result"], 1)[0]["choice"]
                    if row["status"] != "ok" or row["local_replayed"]:
                        raise ValueError("Provider response failed or unexpectedly replayed locally")  # noqa: TRY301
                except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
                    retained = next((e for e in _entries(client) if e.get("tag") == tag), None)
                    row.update(
                        status="unattempted" if retained is None else "failed",
                        error_type=type(error).__name__,
                        reason=str(error),
                    )
                    if retained is not None:
                        row.setdefault("entry", retained)
                        row.setdefault("elapsed_ms", retained.get("elapsed_ms"))
                        stopped.add(item["model"])
                checkpoint(wave_path, state)
        state["execution_history"].append(
            {
                "wall_seconds": time.perf_counter() - start,
                "cpu_seconds": time.process_time() - cpu,
                "peak_rss_bytes": rss_bytes(),
                "attempted_requests": attempted,
                "measurement": (
                    "serial CPU process; VmHWM no sampling; includes HTTP waiting; provider CPU/RAM unmeasured"
                ),
            }
        )
        state["status"] = (
            "complete"
            if len(state["records"]) == MAX_CALLS and all(r["status"] == "ok" for r in state["records"])
            else "partial"
        )
        report(state, directory)
        checkpoint(wave_path, state)
        return state


def main() -> None:
    """Freeze offline by default; hosted calls require the explicit root flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--max-requests", type=int)
    args = parser.parse_args()
    if args.prepare:
        if args.parent is None:
            parser.error("--parent is required for preparation")
        result = prepare(args.parent, args.directory)
    elif args.report_only:
        result = _read(_file(args.directory, "results.json"))
        report(result, args.directory)
    else:
        result = run(args.directory, hosted=args.run_hosted, max_requests=args.max_requests)
    print(
        json.dumps(
            result.get("summary", {"status": result.get("status", "prepared"), "maximum_calls": MAX_CALLS}), indent=2
        )
    )


if __name__ == "__main__":
    main()
