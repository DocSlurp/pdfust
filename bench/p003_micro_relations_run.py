"""Root-only independent-model hosted probes on twelve frozen source relationship pairs."""

# ruff: noqa: ANN401, EM101, TRY003, TRY301, SLF001, C901, PLR0913, PLR2004
from __future__ import annotations

import argparse
import json
import shutil
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from bench import p003_micro_relations as micro
from bench import p003_topology_run as source
from bench.decision_gateway import MODELS as GATEWAY_MODELS
from bench.decision_gateway import GatewayDecisionClient
from bench.decision_gateway_vision import GatewayVisionDecisionClient
from bench.decision_hosted import DECISION_MODELS, ROOT
from bench.p003_boundary_run import RESERVATION, _charges, _entries, _error, _identifier
from bench.p003_client import P003ConcurrentClient, P003DecisionClient
from bench.p003_transport import gateway_wire
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

QUOTA = 4
PAGE_CAP = 2
CODE_FILES = (
    "p003_micro_relations_run.py",
    "p003_micro_relations.py",
    "p003_topology_run.py",
    "p003_candidate_run.py",
    "pipeline_row_evidence.py",
    "p003_topology_ownership.py",
    "p003_transport.py",
    "p003_boundary_run.py",
    "p003_client.py",
    "decision_hosted.py",
    "decision_concurrent.py",
    "decision_gateway.py",
    "decision_gateway_vision.py",
    "research_policy.py",
    "decision_langfuse.py",
    "reprice_model_rates.py",
    "pipeline_run.py",
    "generalization_report.py",
    "pipeline_regions.py",
    "pipeline_assembly.py",
    "generalization_run.py",
    "pipeline_source_order.py",
    "pipeline_repair.py",
    "pipeline_frontier.py",
    "pipeline_vision_transcription.py",
    "generalization_vision_regions.py",
    "generalization_vision_run.py",
    "decision_oplog_run.py",
)


def select(plans: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Declare one source-ID hash-ranked quota inventory independent of model and mode."""
    candidates = []
    for page_id in sorted(plans):
        _identifier(page_id)
        plan = plans[page_id]
        micro._check(plan)
        for pair in plan["pairs"]:
            try:
                micro.packet(plan, pair["id"])
            except micro.CapacityError:
                continue
            rank = sha(micro._dump([page_id, pair["kind"], pair["source_ids"]]).encode())
            candidates.append(
                {
                    "page_id": page_id,
                    **deepcopy(pair),
                    "selection_sha256": rank,
                    "snapshot_sha256": plan["snapshot_sha256"],
                }
            )
    candidates.sort(key=lambda pair: (pair["selection_sha256"], pair["page_id"], pair["id"]))
    counts: Counter[str] = Counter()
    page_counts: Counter[str] = Counter()
    selected = []
    for pair in candidates:
        if counts[pair["kind"]] < QUOTA and page_counts[pair["page_id"]] < PAGE_CAP:
            selected.append(pair)
            counts[pair["kind"]] += 1
            page_counts[pair["page_id"]] += 1
    if counts != dict.fromkeys(micro.KINDS, QUOTA):
        raise ValueError("Source-only hash-ranked inventory cannot meet four questions per kind under two per page")
    return selected


def _configuration(model: str, provider: str, mode: str, concurrency: int, *, exclusive: bool) -> dict[str, Any]:
    if mode not in {"micro", "verbose"} or provider not in {"openrouter", "gateway"}:
        raise ValueError("Explicit micro/verbose and openrouter/gateway treatment required")
    if type(concurrency) is not int or concurrency not in {1, 3}:
        raise ValueError("Transport concurrency must be one or three")
    if provider == "gateway" and (model not in GATEWAY_MODELS or concurrency != 1 or not exclusive):
        raise ValueError("Gateway requires an admitted single model, serial transport and exclusive-paid-work")
    if provider == "openrouter" and model not in DECISION_MODELS:
        raise ValueError("OpenRouter requires a registered native decision model")
    return {
        "campaign": "P003",
        "processor": "p003_micro_relations",
        "model": model,
        "provider": provider,
        "mode": mode,
        "transport_concurrency": concurrency,
        "exclusive_paid_work": exclusive,
        "selection": ("SHA256 canonical page ID, kind and original pair source IDs; global ranked greedy quotas"),
        "kind_quota": QUOTA,
        "per_page_cap": PAGE_CAP,
        "max_source_pairs_per_page": micro.MAX_PAIRS_PER_PAGE,
        "max_micro_state_bytes": micro.MAX_STATE_BYTES,
        "run_hosted": True,
        "replay": False,
        "retry": False,
        "model_fallback": False,
        "source_assignments": False,
        "image": False,
        "first_transport_failure": "stop remaining distinct pairs without admission",
    }


def prepare(baseline: Path, trusted: dict[str, str], output: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Authenticate source and freeze every canonical/wire request before constructing a client."""
    baseline, output = guard_path(baseline), guard_path(output)
    frozen, report = source.authenticate_source(baseline, trusted)
    if len(frozen["records"]) != 16:
        raise ValueError("Micro relation pilot requires the explicit ordinal DEV16 baseline")
    plans = {row["id"]: micro.freeze(row["source"]) for row in report["results"] if row["status"] == "ok"}
    chosen = select(plans)
    requests = []
    for index, pair in enumerate(chosen):
        canonical = micro.body(plans[pair["page_id"]], pair["id"], config["model"], mode=config["mode"])
        wire, native = gateway_wire(canonical) if config["provider"] == "gateway" else (canonical, False)
        requests.append(
            {
                "index": index,
                **pair,
                "canonical": canonical,
                "wire": wire,
                "gateway_native": native,
                "canonical_sha256": sha(micro._dump(canonical).encode()),
                "wire_sha256": sha(micro._dump(wire).encode()),
                "wire_encoded_sha256": sha(json.dumps(wire, separators=(",", ":"), allow_nan=False).encode()),
            }
        )
    output.mkdir(parents=True, exist_ok=False)
    (output / "code").mkdir()
    code = {}
    for name in CODE_FILES:
        path = Path(__file__).parent / name
        shutil.copyfile(path, output / "code" / name)
        code[name] = sha(path.read_bytes())
    # Historical source evidence remains immutable; no archived source is executed.
    shutil.copytree(baseline, output / "baseline")
    inventory = {}
    for page_id, plan in plans.items():
        path = output / (page_id + "-micro-plan.json")
        write_json(path, plan)
        inventory[path.name] = sha(path.read_bytes())
    for request in requests:
        for kind in ("canonical", "wire"):
            path = output / f"question-{request['index']}-{kind}-request.json"
            write_json(path, request[kind])
            inventory[path.name] = sha(path.read_bytes())
    for request in requests:
        path = output / f"question-{request['index']}-wire-encoded.json"
        path.write_bytes(json.dumps(request["wire"], separators=(",", ":"), allow_nan=False).encode())
        inventory[path.name] = sha(path.read_bytes())
    retained = {
        "config": config,
        "manifest_sha256": frozen["manifest_sha256"],
        "records": frozen["records"],
        "baseline": {
            "directory": str(baseline.resolve()),
            "frozen_sha256": sha((baseline / "frozen.json").read_bytes()),
            "report_sha256": sha((baseline / "report.json").read_bytes()),
            "trusted_code": trusted,
        },
        "selected": [
            {key: value for key, value in request.items() if key not in {"canonical", "wire"}} for request in requests
        ],
        "question_inventory_sha256": sha(micro._dump(chosen).encode()),
        "code_sha256": code,
        "artifact_sha256": inventory,
        "source_plan_sha256": {page: plan["snapshot_sha256"] for page, plan in plans.items()},
        "no_answers_or_references_in_preparation": True,
    }
    write_json(output / "frozen.json", retained)
    return {"frozen": retained, "plans": plans, "requests": requests}


def client_for(config: dict[str, Any], prepared: dict[str, Any]) -> Any:
    """Construct a single root-owned shared-policy client after inputs are frozen."""
    if config["provider"] == "gateway":
        return GatewayVisionDecisionClient() if prepared["requests"][0]["gateway_native"] else GatewayDecisionClient()
    return P003ConcurrentClient(ROOT) if config["transport_concurrency"] == 3 else P003DecisionClient(ROOT)


def run(
    baseline: Path,
    trusted_code: Path,
    output: Path,
    *,
    model: str,
    provider: str,
    mode: str,
    run_hosted: bool = False,
    transport_concurrency: int = 1,
    exclusive_paid_work: bool = False,
    client_factory: Callable[..., Any] = client_for,
    entries_reader: Callable[..., list[dict[str, Any]]] = _entries,
) -> dict[str, Any]:
    """Attempt each independent question once; transport failure stops the arm immediately."""
    if not run_hosted:
        raise ValueError("Root opt-in --run-hosted is required; use the preparation-only CLI for local inputs")
    output = guard_path(output)
    run_id = _identifier(output.name)
    config = {
        **_configuration(model, provider, mode, transport_concurrency, exclusive=exclusive_paid_work),
        "run_id": run_id,
    }
    prep_start, prep_cpu = time.perf_counter(), time.process_time()
    prepared = prepare(baseline, json.loads(guard_path(trusted_code).read_bytes()), output, config)
    preprocessing = {
        "wall_seconds": time.perf_counter() - prep_start,
        "cpu_seconds": time.process_time() - prep_cpu,
        "scope": "source authentication and complete request/code/source artifact freezing",
        "peak_sampled_rss_bytes": None,
        "measurement": "process_time CPU and perf_counter wall; preprocessing RSS unmeasured",
    }
    initialization_error = None
    try:
        client = client_factory(config, prepared)
    except Exception as error:
        client = None
        initialization_error = _error(error, "client_initialization")
    prefix = f"P003/{run_id}/micro-relations/"
    results = []
    stopped = initialization_error is not None
    with Resources() as resources:
        for request in prepared["requests"]:
            index, page_id, pair_id = request["index"], request["page_id"], request["id"]
            row: dict[str, Any] = {
                "index": index,
                "page_id": page_id,
                "pair_id": pair_id,
                "kind": request["kind"],
                "source_ids": request["source_ids"],
                "model": model,
                "provider": provider,
                "mode": mode,
                "status": "not_attempted",
            }
            if stopped:
                row["reason"] = (
                    "client initialization failed before admission"
                    if initialization_error
                    else "first transport/admission failure stopped this independent model arm"
                )
            else:
                began, cpu = time.perf_counter(), time.process_time()
                try:
                    response = client.request(
                        request["wire"],
                        tag=prefix + str(index),
                        replay=False,
                        reservation_usd=RESERVATION,
                        max_body_bytes=750_000,
                    )
                except Exception as error:
                    row.update(status="transport_error", error=_error(error, "transport"))
                    stopped = True
                else:
                    write_json(output / f"question-{index}-response.json", response)
                    row.update(
                        entry=response.get("entry"),
                        usage=response["result"].get("usage", {}) if isinstance(response.get("result"), dict) else {},
                        replayed=response.get("replayed"),
                        admission_wait_seconds=response.get(
                            "admission_wait_seconds", response.get("entry", {}).get("admission_wait_seconds")
                        ),
                        admission_wait_scope="reported by client if available; otherwise unmeasured",
                    )
                    try:
                        if response.get("replayed"):
                            raise ValueError("Fresh independent micro probe cannot admit a replayed response")
                        receipt = micro.receipt(
                            prepared["plans"][page_id], pair_id, request["canonical"], response["result"], mode=mode
                        )
                        row.update(
                            status="valid_abstention" if receipt["abstained"] else "valid_nonabstaining",
                            receipt=receipt,
                        )
                    except (ValueError, KeyError, TypeError) as error:
                        row.update(status="malformed_response", error=_error(error, "parse"))
                row.update(
                    client_wall_seconds=time.perf_counter() - began, client_cpu_seconds=time.process_time() - cpu
                )
            results.append(row)
            write_json(output / f"question-{index}-result.json", row)
            write_json(output / "results.json", {"results": results})
    entries = entries_reader(client, prefix) if client is not None else []
    charges = _charges(entries)
    charges["cost_scope"] = (
        "Independent micro relationship probe API attempts only; includes failures and unresolved "
        "reservations; source-baseline costs are historical and are not re-paid or credited"
    )
    statuses = Counter(row["status"] for row in results)
    attempted = len(results) - statuses["not_attempted"]
    metrics = resources.summary()
    wall, effective = metrics["wall_seconds"], charges["effective_usd"]
    # Missing accounting cannot be reported as free successful inference.
    if attempted and not entries:
        charges.update(effective_usd=None, provider_reported_usd=None, accounting_status="unmeasured missing attempts")
        effective = None
    pure = {}
    for page_id, plan in prepared["plans"].items():
        attempts = [
            {
                "pair_id": row["pair_id"],
                "mode": mode,
                "model": model,
                "status": "valid" if row["status"].startswith("valid_") else row["status"],
                **({"receipt": row["receipt"]} if "receipt" in row else {}),
            }
            for row in results
            if row["page_id"] == page_id and row["status"] != "not_attempted"
        ]
        if attempts:
            pure[page_id] = micro.outcomes(plan, attempts, model=model)
    report = {
        "config": config,
        "client_initialization_error": initialization_error,
        "pure_model_outcomes_by_page": pure,
        "results": results,
        "status_counts": dict(statuses),
        "question_count": len(results),
        "attempted_question_count": attempted,
        "pages_covered_by_selected_pairs": len({r["page_id"] for r in results}),
        "pages_with_attempted_pairs": len({r["page_id"] for r in results if r["status"] != "not_attempted"}),
        "preprocessing": preprocessing,
        "metrics": metrics,
        "charges": charges,
        "questions_per_minute": attempted / wall * 60 if wall else None,
        "questions_per_dollar": attempted / effective if effective and effective > 0 else None,
        "valid_nonabstaining_questions_per_minute": statuses["valid_nonabstaining"] / wall * 60 if wall else None,
        "pages_per_minute": None,
        "pages_per_dollar": None,
        "full_pipeline_rate": None,
        "scope": "Partial local relationship probes; page coverage is not complete page processing",
        "correctness_measured": False,
        "table_quality_measured": False,
        "source_assignments_applied": 0,
        "model_fallbacks": 0,
        "retries": 0,
        "baseline_credit": False,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Root exclusively coordinates hosted model/provider arms; no inline retry or switch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", choices=("openrouter", "gateway"), required=True)
    parser.add_argument("--mode", choices=("micro", "verbose"), required=True)
    parser.add_argument("--run-hosted", action="store_true")
    parser.add_argument("--transport-concurrency", choices=(1, 3), type=int, default=1)
    parser.add_argument("--exclusive-paid-work", action="store_true")
    args = parser.parse_args()
    report = run(
        args.baseline,
        args.trusted_code,
        args.output,
        model=args.model,
        provider=args.provider,
        mode=args.mode,
        run_hosted=args.run_hosted,
        transport_concurrency=args.transport_concurrency,
        exclusive_paid_work=args.exclusive_paid_work,
    )
    print(json.dumps({key: value for key, value in report.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()
