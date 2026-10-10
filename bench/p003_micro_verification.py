"""Independent source/request/native-outcome audit of unlabelled micro relation probes."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415, ANN401, SLF001, PLR0913, PLR0917
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from bench.p003_progress import cache_usage
from bench.silver import guard_path, sha

QUESTIONS = 12
INVENTORY_SHA = "eb65bbb38c35c5939165b18588496125f935cfd4f9043d608f6ac69fbb258a3e"
EXECUTED = {
    "p003_micro_relations_run.py", "p003_micro_relations.py", "p003_topology_run.py",
    "p003_topology_ownership.py", "p003_candidate_run.py", "pipeline_row_evidence.py",
    "generalization_report.py", "pipeline_repair.py", "pipeline_regions.py",
    "pipeline_assembly.py", "pipeline_source_order.py", "pipeline_frontier.py",
}


def read(path: Path) -> Any:
    """Read an explicitly named guarded artifact."""
    return json.loads(guard_path(path).read_bytes())


def cost(value: Any) -> float:
    """Unknown or nonfinite accounting cannot become a complete zero charge."""
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("Invalid retained micro accounting")
    return value


def resolved_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only explicit reported charges and labeled estimates resolve an attempt."""
    bases = {"provider-reported USD", "catalog estimate", "provider-reported BYOK upstream plus gateway USD"}
    return [entry for entry in entries if entry.get("cost_status") in bases]


def verify_results(
    directory: Path, config: dict[str, Any], plans: dict[str, Any], selected: list[dict[str, Any]],
    requests: list[dict[str, Any]], report: dict[str, Any],
) -> dict[str, Any]:
    """Require exact fresh native receipts and stop-after-transport semantics, without semantic labels."""
    from bench import p003_micro_relations as micro

    rows = report["results"]
    if len(rows) != QUESTIONS or len(selected) != QUESTIONS:
        raise ValueError("Incomplete full12 micro outcomes")
    stopped = report["client_initialization_error"] is not None
    indexes, pure = set(), {}
    counts, kinds, choices = Counter(), {}, {}
    probabilities, confidences = [], []
    for item, request, row in zip(selected, requests, rows, strict=True):
        index, page_id = item["index"], item["page_id"]
        identity = {"index": index, "page_id": page_id, "pair_id": item["id"], "kind": item["kind"],
                    "source_ids": item["source_ids"], "model": config["model"],
                    "provider": config["provider"], "mode": config["mode"]}
        if (
            any(row.get(k) != v for k, v in identity.items())
            or read(directory / f"question-{index}-result.json") != row
        ):
            raise ValueError("Micro result identity/checkpoint changed")
        response_path = directory / f"question-{index}-response.json"
        status = row["status"]
        counts[status] += 1
        kinds.setdefault(item["kind"], Counter())[status] += 1
        if stopped:
            if status != "not_attempted" or response_path.exists():
                raise ValueError("Micro requests continued after first transport failure")
            continue
        if status == "transport_error":
            if response_path.exists() or not row.get("error"):
                raise ValueError("Micro transport failure contains an answer or lacks evidence")
            stopped = True
        else:
            response = read(response_path)
            entry = response.get("entry")
            if (
                not isinstance(entry, dict) or entry != row.get("entry")
                or response.get("replayed") is not False or row.get("replayed") is not False
                or entry.get("request_sha256") != item["wire_encoded_sha256"]
                or entry.get("requested_model") != config["model"]
                or entry.get("tag") != f"P003/{config['run_id']}/micro-relations/{index}"
                or type(entry.get("index")) is not int or entry["index"] in indexes
                or row.get("usage") != response["result"].get("usage", {})
            ):
                raise ValueError("Micro raw response wire/model/tag/index attribution differs")
            indexes.add(entry["index"])
            try:
                receipt = micro.receipt(plans[page_id], item["id"], request, response["result"], mode=config["mode"])
            except (ValueError, KeyError, TypeError):
                if status != "malformed_response" or "receipt" in row:
                    raise ValueError("Malformed native micro result received valid choice credit") from None
            else:
                expected = "valid_abstention" if receipt["abstained"] else "valid_nonabstaining"
                if row.get("receipt") != receipt or status != expected:
                    raise ValueError("Micro native probability/choice/abstention receipt changed")
                decision = receipt["decision"]
                choices[str(index)] = decision["choice"]
                probabilities.append(decision["probabilities"][decision["choice"]])
                confidence = decision.get("confidence")
                if type(confidence) in (int, float) and math.isfinite(confidence):
                    confidences.append(confidence)
        pure.setdefault(page_id, []).append({
            "pair_id": row["pair_id"], "mode": config["mode"], "model": config["model"],
            "status": "valid" if status.startswith("valid_") else status,
            **({"receipt": row["receipt"]} if "receipt" in row else {}),
        })
    outcomes = {page: micro.outcomes(plans[page], attempts, model=config["model"]) for page, attempts in pure.items()}
    if report["status_counts"] != dict(counts) or report["pure_model_outcomes_by_page"] != outcomes:
        raise ValueError("Micro pure outcome summary differs")
    if read(directory / "results.json") != {"results": rows}:
        raise ValueError("Micro final checkpoint differs from full report")
    return {"status_counts": dict(counts), "kind_outcomes": {k: dict(v) for k, v in kinds.items()},
            "choices_by_question": choices, "raw_chosen_probability_range": [min(probabilities), max(probabilities)]
            if probabilities else None, "numeric_raw_confidence_range": [min(confidences), max(confidences)]
            if confidences else None, "numeric_raw_confidence_observations": len(confidences)}


def verify(directory: Path, trusted_code: dict[str, str], source_trusted_code: dict[str, str]) -> dict[str, Any]:
    """Authenticate producer archives and rebuild complete source/evidence before auditing outcomes."""
    from bench import p003_micro_relations as micro
    from bench import p003_micro_relations_run as runner
    from bench import p003_topology_run as source

    directory = guard_path(directory)
    frozen, report = read(directory / "frozen.json"), read(directory / "report.json")
    archived_code = frozen["code_sha256"]
    if (
        not set(archived_code) >= EXECUTED
        or any(trusted_code.get(name) != digest for name, digest in archived_code.items())
    ):
        raise ValueError("Micro code differs from independent authority")
    for name, digest in archived_code.items():
        if Path(name).name != name or sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Micro archived code differs")
        if name in EXECUTED and sha(Path(__file__).with_name(name).read_bytes()) != digest:
            raise ValueError("Executed micro helper differs from authenticated frozen semantics")
    config = frozen["config"]
    expected = {**runner._configuration(config["model"], config["provider"], config["mode"],
                config["transport_concurrency"], exclusive=config["exclusive_paid_work"]), "run_id": directory.name}
    if config != expected or report["config"] != config or config["provider"] != "openrouter":
        raise ValueError("Micro predeclared independent OpenRouter treatment differs")
    baseline = directory / "baseline"
    authority = frozen["baseline"]
    if (
        authority["trusted_code"] != source_trusted_code
        or sha((baseline / "frozen.json").read_bytes()) != authority["frozen_sha256"]
        or sha((baseline / "report.json").read_bytes()) != authority["report_sha256"]
    ):
        raise ValueError("Micro original source authority changed")
    original, historical = source.authenticate_source(baseline, source_trusted_code)
    if frozen["records"] != original["records"] or frozen["manifest_sha256"] != original["manifest_sha256"]:
        raise ValueError("Micro source inventory changed")
    plans = {p["id"]: micro.freeze(p["source"]) for p in historical["results"] if p["status"] == "ok"}
    chosen = runner.select(plans)
    if sha(micro._dump(chosen).encode()) != INVENTORY_SHA or frozen["question_inventory_sha256"] != INVENTORY_SHA:
        raise ValueError("Micro fixed pair inventory changed")
    if frozen["source_plan_sha256"] != {page: plan["snapshot_sha256"] for page, plan in plans.items()}:
        raise ValueError("Micro source pair plans changed")
    for name, digest in frozen["artifact_sha256"].items():
        if Path(name).name != name or sha((directory / name).read_bytes()) != digest:
            raise ValueError("Micro frozen input bytes changed")
    for page, plan in plans.items():
        if read(directory / f"{page}-micro-plan.json") != plan:
            raise ValueError("Micro complete source plan differs")
    requests, selected = [], []
    for index, pair in enumerate(chosen):
        body = micro.body(plans[pair["page_id"]], pair["id"], config["model"], mode=config["mode"])
        actual = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
        item = {"index": index, **pair, "gateway_native": False,
                "canonical_sha256": sha(micro._dump(body).encode()), "wire_sha256": sha(micro._dump(body).encode()),
                "wire_encoded_sha256": sha(actual)}
        if (
            read(directory / f"question-{index}-canonical-request.json") != body
            or read(directory / f"question-{index}-wire-request.json") != body
            or (directory / f"question-{index}-wire-encoded.json").read_bytes() != actual
        ):
            raise ValueError("Micro exact encoded wire differs from original complete source packet")
        selected.append(item)
        requests.append(body)
    if frozen["selected"] != selected or frozen["no_answers_or_references_in_preparation"] is not True:
        raise ValueError("Micro selected input or source-only preparation differs")
    outcomes = verify_results(directory, config, plans, selected, requests, report)
    for key, value in {"question_count": QUESTIONS, "correctness_measured": False,
                       "table_quality_measured": False, "source_assignments_applied": 0,
                       "model_fallbacks": 0, "retries": 0, "baseline_credit": False,
                       "pages_per_minute": None, "pages_per_dollar": None, "full_pipeline_rate": None}.items():
        if report[key] != value:
            raise ValueError("Micro relation probes claim output correctness or full pipeline credit")
    attempted = QUESTIONS - outcomes["status_counts"].get("not_attempted", 0)
    if report["attempted_question_count"] != attempted:
        raise ValueError("Micro attempted denominator changed")
    charges = report["charges"]
    entries = charges["entries"]
    if len(entries) != attempted or charges["ledger_attempts"] != attempted:
        raise ValueError("Micro cost inventory omits attempts")
    indexes = set()
    for entry in entries:
        index = int(entry["tag"].rsplit("/", 1)[1])
        if (entry["tag"] != f"P003/{config['run_id']}/micro-relations/{index}"
            or not 0 <= index < QUESTIONS or report["results"][index]["status"] == "not_attempted"
            or entry["request_sha256"] != selected[index]["wire_encoded_sha256"]
            or entry.get("requested_model") != config["model"] or index in indexes):
            raise ValueError("Micro ledger attempt identity differs or repeats")
        indexes.add(index)
        returned = report["results"][index].get("entry")
        if returned is not None and returned != entry:
            raise ValueError("Micro charge entry differs from fresh response provenance")
    resolved = resolved_entries(entries)
    effective = sum(cost(e["accounted_usd"]) for e in resolved) if len(resolved) == len(entries) else None
    reported = [cost(e["provider_reported_usd"]) for e in entries if "provider_reported_usd" in e]
    expected_charges = {
        "effective_usd": effective,
        "accounted_usd": sum(cost(e["accounted_usd"]) for e in entries),
        "known_partial_effective_usd": sum(cost(e["accounted_usd"]) for e in resolved),
        "unresolved_reserved_usd": sum(cost(e["accounted_usd"]) for e in entries if e.get("cost_status") == "reserved"),
        "provider_reported_usd": sum(reported) if len(reported) == len(entries) else None,
        "known_partial_provider_reported_usd": sum(reported),
        "missing_provider_charge_count": len(entries) - len(reported),
        "cost_bases": dict(Counter(e.get("cost_status", "unknown") for e in entries)),
    }
    if any(charges.get(k) != v for k, v in expected_charges.items()):
        raise ValueError("Micro accounting math differs")
    wall = report["metrics"]["wall_seconds"]
    if report["questions_per_minute"] != attempted / wall * 60:
        raise ValueError("Micro question throughput differs")
    return {"name": directory.name, "config": config, **outcomes, "attempted_questions": attempted,
            "question_count": QUESTIONS, "question_inventory_sha256": INVENTORY_SHA,
            "report_sha256": sha((directory / "report.json").read_bytes()), "code_sha256": archived_code,
            "resources": report["metrics"], "preprocessing": report["preprocessing"], "costs": charges,
            "questions_per_minute": report["questions_per_minute"], "questions_per_api_usd": attempted / effective
            if effective and effective > 0 else None, "provider_cache_usage": cache_usage(report["results"], attempted),
            "semantic_correctness_measured": False, "table_quality_measured": False, "new_api_calls": 0}
