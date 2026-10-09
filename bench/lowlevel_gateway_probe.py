"""L014 source-only matched Laya compact/expanded compatibility probe.

No private references are opened. Only explicit root-owned hosted execution reads
credentials. Prior Gateway failures remain immutable and are never retried.
"""

from __future__ import annotations

import argparse
import importlib
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, NoReturn

from bench.decision_gateway import GATEWAY, LAYA_MODELS, GatewayDecisionClient, request_identity
from bench.decision_hosted import checkpoint, exclusive_lock
from bench.lowlevel_compact import compact, encoded, expand
from bench.lowlevel_run import parse_response, persistent_stops, wave_admission
from bench.reprice_model_rates import request_cost
from bench.silver import guard_path, rss_bytes

EXPERIMENT = "L014"
PREFIX = "L014/"
CAP = 1.5
BYTE_CAP = 7500
ARMS = ("expanded-string", "compact-string")
MAX_BODIES = len(LAYA_MODELS) * len(ARMS)


def _fail(reason: str) -> NoReturn:
    message = "L014: " + reason
    raise ValueError(message)


def _file(directory: Path, name: str) -> Path:
    if Path(name).name != name:
        _fail("artifact must be a basename")
    base = guard_path(directory).resolve()
    path = guard_path(base / name).resolve()
    if not path.is_relative_to(base):
        _fail("artifact escapes the source freeze")
    return path


def _hash(raw: bytes) -> str:
    import hashlib  # noqa: PLC0415 - pure local provenance.

    return hashlib.sha256(raw).hexdigest()


def verify_parent(directory: Path) -> dict[str, Any]:
    """Verify source/body lineage without opening private targets."""
    return importlib.import_module("bench.lowlevel_gateway").verify(directory)


def _failures(parent: Path) -> tuple[set[str], list[dict[str, Any]]]:
    """Inspect only mechanical failures in the two explicitly retained cohorts."""
    failed: set[str] = set()
    snapshots = []
    for directory in (parent, parent.parent / "gateway-serialized"):
        path = _file(directory, "results.json")
        if not path.exists():
            if directory == parent:
                _fail("parent failure inventory is unavailable")
            continue
        raw = path.read_bytes()
        rows = json.loads(raw)["calls"]
        ids = sorted(
            {
                ident
                for row in rows
                if row.get("status") == "failed"
                and row.get("arm") in {"canonical-compact", "canonical-compact-serialized"}
                for ident in row["page_ids"]
            }
        )
        failed.update(ids)
        snapshots.append({"directory": str(directory), "results_sha256": _hash(raw), "failed_canonical_ids": ids})
    return failed, snapshots


def representations(body: dict[str, Any], observation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Prove ordinary source equality and preserve every question/routing value."""
    state = body["state"]
    if not isinstance(state, dict) or set(state) != {"observations"} or set(state["observations"]) != {"q0"}:
        _fail("expected a singleton canonical packet")
    if set(body["questions"]) != {"q0"}:
        _fail("question aliases are not singleton")
    packet = state["observations"]["q0"]
    ordinary = expand(packet)
    source = importlib.import_module("bench.lowlevel_evidence").project(observation, "canonical")
    if encoded(ordinary) != encoded(source) or encoded(expand(compact(ordinary))) != encoded(ordinary):
        _fail("canonical values/order fail independent source round trip")
    variants = {}
    for arm, projection in (("expanded-string", ordinary), ("compact-string", packet)):
        changed = deepcopy(body)
        changed["state"] = encoded({"observations": {"q0": projection}}).decode()
        if changed["questions"] != body["questions"]:
            _fail("question content changed")
        variants[arm] = changed
    return variants


def select_source(
    parent: Path, original: dict[str, Any], failed: set[str]
) -> tuple[dict[str, Any] | None, dict[str, dict[str, dict[str, Any]]]]:
    """Select by source ID and transport eligibility only."""
    selected = None
    bodies: dict[str, dict[str, dict[str, Any]]] = {}
    for page in sorted(original["pages"], key=lambda row: row["id"]):
        if page["id"] in failed:
            continue
        candidates: dict[str, dict[str, dict[str, Any]]] = {}
        observation = json.loads(_file(parent, page["observation_file"]).read_bytes())
        for model in LAYA_MODELS:
            record = next(
                row
                for row in original["records"]
                if row["model"] == model and row["arm"] == "canonical-compact" and row["page_ids"] == [page["id"]]
            )
            body = json.loads(_file(parent, record["request"]).read_bytes())
            candidates[model] = representations(body, observation)
        if any(len(encoded(body)) > BYTE_CAP for variants in candidates.values() for body in variants.values()):
            continue
        selected, bodies = page, candidates
        break
    return selected, bodies


def prepare(parent: Path, directory: Path) -> dict[str, Any]:
    """Select the first eligible source ID and freeze at most four matched bodies."""
    start, cpu = time.perf_counter(), time.process_time()
    parent, directory = guard_path(parent).resolve(), guard_path(directory).resolve()
    original = verify_parent(parent)
    if original.get("experiment") != "L009" or original.get("kind") != "text":
        _fail("parent must be the original Gateway text freeze")
    if directory.exists():
        _fail("preserve existing probe freezes")
    failed, history = _failures(parent)
    selected, bodies = select_source(parent, original, failed)
    directory.mkdir(parents=True)
    catalog = _file(parent, "catalog-prices.json").read_bytes()
    _file(directory, "catalog-prices.json").write_bytes(catalog)
    records: list[dict[str, Any]] = []
    if selected is not None:
        for field in ("source_file", "observation_file"):
            _file(directory, selected[field]).write_bytes(_file(parent, selected[field]).read_bytes())
        for arm in ARMS:  # Test expanded controls before a compact refusal can stop its model.
            for model in LAYA_MODELS:
                raw = encoded(bodies[model][arm])
                name = f"request-{len(records):04d}.json"
                _file(directory, name).write_bytes(raw)
                records.append(
                    {
                        "request": name,
                        "sha256": _hash(raw),
                        "model": model,
                        "arm": arm,
                        "page_ids": [selected["id"]],
                        "body_bytes": len(raw),
                    }
                )
    manifest = {
        "schema": 1,
        "experiment": EXPERIMENT,
        "gateway": GATEWAY,
        "status": "prepared" if selected is not None else "refused",
        "reason": None if selected is not None else "No unfailed source fits the full expanded body byte admission",
        "parent_directory": str(parent),
        "parent_manifest_sha256": _hash(_file(parent, "manifest.json").read_bytes()),
        "pages": [selected] if selected is not None else [],
        "models": list(LAYA_MODELS),
        "arms": list(ARMS),
        "records": records,
        "catalog_sha256": _hash(catalog),
        "failure_snapshots": history,
        "excluded_source_ids": sorted(failed),
        "selection": (
            "First source-ID-sorted canonical page not previously failed, "
            "full expanded and compact bodies <=7500 bytes; no gold/results quality selection"
        ),
        "request_settings": {"max_body_bytes": BYTE_CAP, "batch_size": 1, "wave_limit_usd": CAP, "prefix": PREFIX},
        "preparation": {
            "wall_seconds": time.perf_counter() - start,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "measurement": "serial current process counters and lifetime VmHWM; no sampling or inference",
        },
    }
    checkpoint(_file(directory, "manifest.json"), manifest)
    verify(directory)
    return manifest


def verify(directory: Path) -> dict[str, Any]:  # noqa: C901
    """Reconstruct source-equivalent requests; never open private reference files."""
    directory = guard_path(directory)
    manifest = json.loads(_file(directory, "manifest.json").read_bytes())
    if (
        manifest["experiment"] != EXPERIMENT
        or manifest["models"] != list(LAYA_MODELS)
        or manifest["arms"] != list(ARMS)
        or manifest["gateway"] != GATEWAY
        or manifest["request_settings"]
        != {"max_body_bytes": BYTE_CAP, "batch_size": 1, "wave_limit_usd": CAP, "prefix": PREFIX}
    ):
        _fail("probe identity changed")
    parent = guard_path(Path(manifest["parent_directory"]))
    original = verify_parent(parent)
    if (
        _hash(_file(parent, "manifest.json").read_bytes()) != manifest["parent_manifest_sha256"]
        or _hash(_file(directory, "catalog-prices.json").read_bytes()) != manifest["catalog_sha256"]
    ):
        _fail("parent or catalog changed")
    if manifest["status"] == "refused":
        if manifest["records"] or manifest["pages"]:
            _fail("refused probe contains requests")
        return manifest
    if len(manifest["pages"]) != 1 or len(manifest["records"]) != MAX_BODIES:
        _fail("probe must contain one source and four matched bodies")
    page = manifest["pages"][0]
    selected, _ = select_source(parent, original, set(manifest["excluded_source_ids"]))
    if selected != page or page not in original["pages"] or page["id"] in _failures(parent)[0]:
        _fail("selected source changed or now has a canonical failure")
    for field, digest in (("source_file", "source_sha256"), ("observation_file", "observation_sha256")):
        if _hash(_file(directory, page[field]).read_bytes()) != page[digest]:
            _fail("source bytes changed")
    observation = json.loads(_file(directory, page["observation_file"]).read_bytes())
    seen = set()
    for record in manifest["records"]:
        original_record = next(
            row
            for row in original["records"]
            if row["model"] == record["model"] and row["arm"] == "canonical-compact" and row["page_ids"] == [page["id"]]
        )
        variants = representations(json.loads(_file(parent, original_record["request"]).read_bytes()), observation)
        raw = _file(directory, record["request"]).read_bytes()
        identity = (record["model"], record["arm"])
        if (
            identity in seen
            or record["page_ids"] != [page["id"]]
            or len(raw) > BYTE_CAP
            or _hash(raw) != record["sha256"]
            or len(raw) != record["body_bytes"]
            or raw != encoded(variants[record["arm"]])
        ):
            _fail("matched probe body changed")
        seen.add(identity)
    if seen != {(model, arm) for model in LAYA_MODELS for arm in ARMS}:
        _fail("matched probe inventory changed")
    return manifest


def run(directory: Path, *, client: Any = None) -> dict[str, Any]:  # noqa: ANN401, C901
    """Root-only explicit execution; retain choices/diagnostics without scoring gold."""
    manifest = verify(directory)
    if manifest["status"] == "refused":
        return {"status": "refused", "reason": manifest["reason"], "calls": []}
    rates = json.loads(_file(directory, "catalog-prices.json").read_bytes())["prices"]
    client = GatewayDecisionClient(rates=rates) if client is None else client
    path = _file(directory, "results.json")
    with exclusive_lock(client.ledger.parent / "run.lock"):
        verify(directory)
        digest = _hash(_file(directory, "manifest.json").read_bytes())
        results: dict[str, Any] = (
            json.loads(path.read_bytes()) if path.exists() else {"schema": 1, "manifest_sha256": digest, "calls": []}
        )
        if results["manifest_sha256"] != digest:
            _fail("retained results belong to another freeze")
        stopped = persistent_stops(client, list(LAYA_MODELS), results["calls"], tag_prefix=PREFIX)
        results["status"] = "running"
        checkpoint(path, results)
        done = {row["request_sha256"] for row in results["calls"] if row["status"] in {"ok", "failed"}}
        budget_exhausted = False
        started, cpu = time.perf_counter(), time.process_time()
        for record in manifest["records"]:
            if record["sha256"] in done:
                continue
            row = next((row for row in results["calls"] if row["request_sha256"] == record["sha256"]), None)
            if row is None:
                row = {
                    "request_sha256": record["sha256"],
                    "model": record["model"],
                    "arm": record["arm"],
                    "status": "pending",
                }
                results["calls"].append(row)
            if record["model"] in stopped or budget_exhausted:
                row.update(
                    status="unattempted", reason="wave cap" if budget_exhausted else "persistent L014 model stop"
                )
                checkpoint(path, results)
                continue
            body_raw = _file(directory, record["request"]).read_bytes()
            identity = request_identity(body_raw)
            try:
                entries = json.loads(client.ledger.read_bytes())["requests"] if client.ledger.exists() else []
                known = next(
                    (
                        e
                        for e in entries
                        if e.get("gateway") == GATEWAY
                        and e.get("request_sha256") == record["sha256"]
                        and e.get("request_identity_sha256") == identity
                    ),
                    None,
                )
                if known is None:
                    wave_admission(entries, tag_prefix=PREFIX, wave_limit=CAP)
                response = client.request(
                    json.loads(body_raw),
                    tag=f"{PREFIX}{record['model']}/{record['arm']}/{record['sha256']}",
                    max_body_bytes=BYTE_CAP,
                )
                row.update(response=response["result"], entry=response["entry"], replayed=response["replayed"])
                row["cost"] = request_cost(
                    response["entry"],
                    response["result"].get("usage", {}),
                    response["entry"].get("catalog_rates", rates[record["model"]]),
                )
                row["answers"] = parse_response(response["result"], 1)
                row["status"] = "ok"
            except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
                row.update(status="failed", error=type(error).__name__)
                entries = json.loads(client.ledger.read_bytes())["requests"] if client.ledger.exists() else []
                retained = next(
                    (
                        e
                        for e in entries
                        if e.get("gateway") == GATEWAY
                        and e.get("request_sha256") == record["sha256"]
                        and e.get("request_identity_sha256") == identity
                    ),
                    None,
                )
                if retained:
                    row.setdefault("entry", retained)
                    row.setdefault("cost", request_cost(retained, {}, retained.get("catalog_rates", {})))
                if "persistent wave cap exhausted" in str(error):
                    budget_exhausted = True
                    row.update(status="unattempted", reason="wave cap before transmission")
                else:
                    stopped = persistent_stops(client, list(LAYA_MODELS), results["calls"], tag_prefix=PREFIX)
            if row["status"] in {"ok", "failed"}:
                done.add(record["sha256"])
            checkpoint(path, results)
        results.update(
            status="complete",
            planned_bodies=len(manifest["records"]),
            completed_bodies=sum(row["status"] in {"ok", "failed"} for row in results["calls"]),
            model_stops=stopped,
            budget_exhausted=budget_exhausted,
            execution_resources={
                "wall_seconds": time.perf_counter() - started,
                "cpu_seconds": time.process_time() - cpu,
                "peak_rss_bytes": rss_bytes(),
                "measurement": (
                    "serial process counters; lifetime VmHWM; HTTP waiting included; provider CPU/RAM unmeasured"
                ),
            },
        )
        checkpoint(path, results)
        return results


def main() -> None:
    """Prepare/verify locally; root must explicitly enable the hosted probe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        if args.parent is None:
            parser.error("--prepare requires --parent")
        prepare(args.parent, args.directory)
    result = run(args.directory) if args.run_hosted else verify(args.directory)
    print(
        json.dumps(
            {key: result.get(key) for key in ("status", "reason", "records", "planned_bodies", "completed_bodies")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
