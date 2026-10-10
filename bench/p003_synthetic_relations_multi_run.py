"""Root-only cross-page shared-context multi-question synthetic treatments."""

# ruff: noqa: EM101, TRY003, TRY301, C901, PLR0912, PLR0913, E501, PLC0415, SLF001
from __future__ import annotations

import argparse
import json
import resource
import shutil
import time
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from bench import p003_synthetic_relations as evidence
from bench import p003_synthetic_relations_multi as protocol
from bench import p003_synthetic_relations_run as single
from bench.silver import guard_path, sha, write_json

CODE_FILES = tuple(
    dict.fromkeys(("p003_synthetic_relations_multi.py", "p003_synthetic_relations_multi_run.py", *single.CODE_FILES))
)
ATTEMPTED = {"valid", "malformed_response", "transport_error"}


def configuration(
    model: str, *, size: int, mode: str = "text_geometry", transport_concurrency: int = 3
) -> dict[str, Any]:
    """Retain one explicit model and text-only treatment, with no provider fallback."""
    if type(size) is not int or size not in protocol.SIZES:
        raise ValueError("Shared question group size must be 4 or 8")
    config = single.configuration(model, mode=mode, transport_concurrency=transport_concurrency)
    config.update(
        processor="p003_synthetic_relations_multi",
        question_group_size=size,
        group_order_seed=protocol.ORDER_SEED,
        group_order_policy="SHA256(seed/source_id), then source_id; no labels or twin metadata",
        treatment="cross_page_shared_context_multi_question",
        isolation_guaranteed=False,
        group_atomic_validation=True,
        scope="24 distinct synthetic pages; scoped shared state, not server batching or complete extraction",
        first_transport_failure="stop remaining groups; malformed groups continue distinct groups",
    )
    return config


def prepare(pool: Path, trusted_code: Path, output: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Replay all source evidence and freeze complete group requests before any client exists."""
    pool, trusted_code, output = [guard_path(p) for p in (pool, trusted_code, output)]
    if output.exists():
        raise FileExistsError("New independent shared-context treatment directory required")
    trusted = json.loads(trusted_code.read_bytes())
    source_frozen, records = single.authenticate(pool, trusted)
    requests = []
    for index, group in enumerate(protocol.groups(records, config["question_group_size"])):
        row: dict[str, Any] = {
            "index": index,
            "case_ids": [r["id"] for r in group],
            "question_keys": [f"q{i}" for i in range(len(group))],
            "question_status": "source_refused",
            "omitted_word_count": 0,
        }
        if all(r["status"] == "ready" for r in group):
            try:
                body = protocol.request(group, config)
                encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
                if len(encoded) > protocol.MAX_BODY_BYTES:
                    raise ValueError("Whole request exceeds 750000 bytes; no truncation")
            except ValueError as error:
                row.update(question_status="capacity_refused", reason=str(error))
            else:
                row.update(
                    question_status="ready",
                    canonical=body,
                    wire=body,
                    encoded=encoded,
                    wire_encoded_sha256=sha(encoded),
                    request_bytes=len(encoded),
                    state_utf8_bytes=len(body["state"].encode()),
                    word_count=sum(len(r["source"]["words"]) for r in group),
                    evidence_sha256=[
                        sha(evidence.dump(evidence.packet(r, mode=config["mode"])).encode()) for r in group
                    ],
                )
        requests.append(row)
    output.mkdir(parents=True)
    (output / "code").mkdir()
    (output / "source/code").mkdir(parents=True)
    code = {}
    for name in CODE_FILES:
        path = Path(__file__).with_name(name)
        shutil.copyfile(path, output / "code" / name)
        code[name] = sha(path.read_bytes())
    shutil.copyfile(pool / "frozen.json", output / "source/frozen.json")
    shutil.copyfile(trusted_code, output / "source/trusted-code.json")
    for name in source_frozen["code_sha256"]:
        shutil.copyfile(pool / "code" / name, output / "source/code" / name)
    artifacts = {}
    # Explicit source whitelist only: no directory enumeration, gold copying or generator execution.
    for name in source_frozen["artifact_sha256"]:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(single._path(pool, name), target)
        artifacts[str(target.relative_to(output))] = sha(target.read_bytes())
    for row in requests:
        if row["question_status"] == "ready":
            for kind in ("canonical", "wire"):
                path = output / f"group-{row['index']}-{kind}-request.json"
                write_json(path, row[kind])
                artifacts[path.name] = sha(path.read_bytes())
            path = output / f"group-{row['index']}-wire-encoded.json"
            path.write_bytes(row["encoded"])
            artifacts[path.name] = sha(row["encoded"])
    frozen = {
        "config": config,
        "source_pool": {
            "directory": str(pool.resolve()),
            "frozen_sha256": sha((pool / "frozen.json").read_bytes()),
            "external_map_path": str(trusted_code.resolve()),
            "external_map_sha256": sha(trusted_code.read_bytes()),
            "trusted_code": trusted,
        },
        "records": source_frozen["records"],
        "selected": [{k: v for k, v in r.items() if k not in {"canonical", "wire", "encoded"}} for r in requests],
        "code_sha256": code,
        "artifact_sha256": artifacts,
        "gold_read_or_copied": False,
        "references_read": False,
        "question_count": 24,
        "group_count": len(requests),
    }
    write_json(output / "frozen.json", frozen)
    return {"frozen": frozen, "records": records, "requests": requests}


def run(
    pool: Path,
    trusted_code: Path,
    output: Path,
    *,
    model: str,
    size: int,
    mode: str = "text_geometry",
    transport_concurrency: int = 3,
    run_hosted: bool = False,
    client_factory: Callable[..., Any] = single.client_for,
    entries_reader: Callable[..., list[dict[str, Any]]] = single.read_entries,
) -> dict[str, Any]:
    """One fresh call per group; charge once, fail closed per group and preserve all 24 outcomes."""
    from bench.p003_boundary_run import _charges, _error, _identifier
    from bench.pipeline_run import Resources

    if not run_hosted:
        raise ValueError("Explicit root --run-hosted required")
    config = configuration(model, size=size, mode=mode, transport_concurrency=transport_concurrency)
    config["run_id"] = _identifier(output.name)
    began, cpu = time.perf_counter(), time.process_time()
    prepared = prepare(pool, trusted_code, output, config)
    preprocessing = {
        "wall_seconds": time.perf_counter() - began,
        "cpu_seconds": time.process_time() - cpu,
        "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "measurement": "Unsampled parent lifetime RSS including imports; source replay/freezing excluded from API rates",
    }
    initialization_error = None
    try:
        client = client_factory(config, prepared)
    except Exception as error:
        client = None
        initialization_error = _error(error, "client_initialization")
    prefix = f"P003/{config['run_id']}/synthetic-shared-context/"
    stopped = initialization_error is not None
    by_id = {r["id"]: r for r in prepared["records"]}
    outcomes, group_results = [], []
    with Resources() as resources:
        for request in prepared["requests"]:
            row = {
                "index": request["index"],
                "case_ids": request["case_ids"],
                "model": model,
                "provider": "openrouter",
                "status": "not_attempted",
                "wire_encoded_sha256": request.get("wire_encoded_sha256"),
                "tag": prefix + str(request["index"]),
            }
            receipts = None
            if request["question_status"] != "ready":
                row.update(
                    status=request["question_status"], reason=request.get("reason", "Whole group source refusal")
                )
            elif stopped:
                row["reason"] = "First transport/client initialization failure stopped remaining distinct groups"
            else:
                start, start_cpu = time.perf_counter(), time.process_time()
                try:
                    response = client.request(
                        request["wire"],
                        tag=row["tag"],
                        replay=False,
                        reservation_usd=single.RESERVATION,
                        max_body_bytes=protocol.MAX_BODY_BYTES,
                    )
                except Exception as error:
                    row.update(status="transport_error", error=_error(error, "transport"))
                    stopped = True
                else:
                    write_json(output / f"group-{request['index']}-response.json", response)
                    row.update(
                        entry=response.get("entry"),
                        replayed=response.get("replayed"),
                        usage=response["result"].get("usage", {}) if isinstance(response.get("result"), dict) else {},
                    )
                    try:
                        entry = response["entry"]
                        if (
                            response.get("replayed") is not False
                            or entry["requested_model"] != model
                            or entry["request_sha256"] != request["wire_encoded_sha256"]
                            or entry["tag"] != row["tag"]
                        ):
                            raise ValueError("Fresh exact model/tag/wire receipt required")
                        receipts = protocol.parse(
                            [by_id[i] for i in request["case_ids"]], request["canonical"], response["result"], config
                        )
                        row.update(status="valid", receipts=receipts)
                    except (ValueError, KeyError, TypeError) as error:
                        row.update(status="malformed_response", error=_error(error, "parse"))
                row.update(
                    client_wall_seconds=time.perf_counter() - start, client_cpu_seconds=time.process_time() - start_cpu
                )
            for local, identity in enumerate(request["case_ids"]):
                case = {
                    "id": identity,
                    "kind": by_id[identity]["kind"],
                    "group_index": request["index"],
                    "question_key": f"q{local}",
                    "status": row["status"],
                    "wire_encoded_sha256": row["wire_encoded_sha256"],
                    "shared_charge_scope": "Group request only; no per-case duplicated financial entry",
                }
                if receipts is not None:
                    case.update(
                        receipt=receipts[local],
                        status="valid_abstention" if receipts[local]["abstained"] else "valid_nonabstaining",
                    )
                outcomes.append(case)
            group_results.append(row)
            write_json(output / f"group-{request['index']}-result.json", row)
            write_json(output / "results.json", {"groups": group_results, "results": outcomes})
    entries = entries_reader(client, prefix) if client is not None else []
    charges = _charges(entries)
    attempted = sum(r["status"] in ATTEMPTED for r in group_results)
    if attempted and not entries:
        charges.update(
            effective_usd=None,
            provider_reported_usd=None,
            accounting_status="Missing attempt accounting; costs unknown",
        )
    charges["cost_scope"] = (
        "Fresh shared-context group API attempts; each request charged once, including failed reservations"
    )
    counts = Counter(r["status"] for r in outcomes)
    metrics = resources.summary()
    wall, effective = metrics["wall_seconds"], charges["effective_usd"]
    attempted_questions = sum(len(r["case_ids"]) for r in group_results if r["status"] in ATTEMPTED)
    report = {
        "config": config,
        "client_initialization_error": initialization_error,
        "results": outcomes,
        "groups": group_results,
        "status_counts": dict(counts),
        "group_status_counts": dict(Counter(r["status"] for r in group_results)),
        "question_count": 24,
        "group_count": len(group_results),
        "attempted_group_count": attempted,
        "attempted_question_count": attempted_questions,
        "classified_question_count": counts["valid_nonabstaining"],
        "preprocessing": preprocessing,
        "metrics": metrics,
        "charges": charges,
        "attempted_requests_per_minute": attempted / wall * 60 if wall else None,
        "attempted_questions_per_minute": attempted_questions / wall * 60 if wall else None,
        "valid_nonabstaining_questions_per_minute": counts["valid_nonabstaining"] / wall * 60 if wall else None,
        "valid_nonabstaining_questions_per_dollar": counts["valid_nonabstaining"] / effective
        if effective and effective > 0
        else None,
        "question_rate_scope": "Scoped cross-page shared-context questions; no server batching/isolation claim",
        "pages_per_minute": None,
        "pages_per_dollar": None,
        "full_pipeline_rate": None,
        "correctness_measured": False,
        "gold_read": False,
        "source_assignments_applied": 0,
        "model_fallbacks": 0,
        "retries": 0,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Prepare only by default; root alone opts into shared-client hosted transport."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=single.DECISION_MODELS, required=True)
    parser.add_argument("--group-size", choices=protocol.SIZES, type=int, required=True)
    parser.add_argument("--evidence", choices=evidence.MODES, default="text_geometry")
    parser.add_argument("--transport-concurrency", choices=(1, 3), type=int, default=3)
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    cfg = configuration(
        args.model, size=args.group_size, mode=args.evidence, transport_concurrency=args.transport_concurrency
    )
    if args.run_hosted:
        value = run(
            args.input,
            args.trusted_code,
            args.output,
            model=args.model,
            size=args.group_size,
            mode=args.evidence,
            transport_concurrency=args.transport_concurrency,
            run_hosted=True,
        )
        print(evidence.dump({k: v for k, v in value.items() if k not in {"results", "groups"}}))
    else:
        value = prepare(args.input, args.trusted_code, args.output, cfg)
        print(
            evidence.dump(
                {
                    "prepared_group_count": len(value["requests"]),
                    "question_count": 24,
                    "hosted_calls": 0,
                    "gold_read": False,
                }
            )
        )


if __name__ == "__main__":
    main()
