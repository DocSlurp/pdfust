"""Independent synthetic relationship replay; gold is opened only after verification."""

# ruff: noqa: ANN401, EM101, TRY003, C901, PLR0912, PLR0913, PLR2004, E501, SLF001, TRY301, PLR0917
from __future__ import annotations

import argparse
import json
import math
import resource
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_synthetic_relations as evidence
from bench import p003_synthetic_relations_run as runner
from bench.silver import guard_path, sha, write_json

PURE_FILES = (
    "p003_synthetic_relations_run.py",
    "p003_synthetic_relations.py",
    "feature_cases.py",
    "pipeline_row_evidence.py",
    "pipeline_regions.py",
    "silver.py",
)
ATTEMPTED = {"valid_nonabstaining", "valid_abstention", "malformed_response", "transport_error"}


def load(path: Path) -> Any:
    """Read only an explicitly supplied authorized artifact."""
    return json.loads(guard_path(path).read_bytes())


def source_context(pool: Path, trusted_code: Path) -> dict[str, Any]:
    """Authenticate complete source evidence without accessing labels."""
    pool, trusted_code = guard_path(pool), guard_path(trusted_code)
    trusted = load(trusted_code)
    frozen, records = runner.authenticate(pool, trusted)
    return {
        "pool": pool,
        "trusted": trusted,
        "map_sha256": sha(trusted_code.read_bytes()),
        "frozen": frozen,
        "frozen_sha256": sha((pool / "frozen.json").read_bytes()),
        "records": records,
    }


def _number(value: Any) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("Finite nonnegative reported measurement required")
    return float(value)


def charges(entries: list[dict[str, Any]], attempted: int) -> dict[str, Any]:
    """Rebuild retained financial totals, preserving reported zeros and unresolved reservations."""
    resolved = [e for e in entries if e.get("cost_status") != "reserved"]
    reserved = [e for e in entries if e.get("cost_status") == "reserved"]
    reported = [_number(e["provider_reported_usd"]) for e in entries if "provider_reported_usd" in e]
    complete = len(resolved) == len(entries)
    output: dict[str, Any] = {
        "ledger_attempts": len(entries),
        "accounted_usd": sum(_number(e["accounted_usd"]) for e in entries),
        "effective_usd": sum(_number(e["accounted_usd"]) for e in resolved) if complete else None,
        "known_partial_effective_usd": sum(_number(e["accounted_usd"]) for e in resolved),
        "unresolved_reserved_usd": sum(_number(e["accounted_usd"]) for e in reserved),
        "provider_reported_usd": sum(reported) if len(reported) == len(entries) else None,
        "known_partial_provider_reported_usd": sum(reported),
        "missing_provider_charge_count": len(entries) - len(reported),
        "cost_bases": dict(Counter(e.get("cost_status", "unknown") for e in entries)),
    }
    if attempted and not entries:
        output.update(
            effective_usd=None,
            provider_reported_usd=None,
            accounting_status="Missing attempt accounting; costs unknown",
        )
    return output


def verify_run(directory: Path, trusted_runtime: Path, context: dict[str, Any]) -> dict[str, Any]:
    """Replay external authorities, exact requests and raw outcomes before any gold access."""
    directory, trusted_runtime = guard_path(directory), guard_path(trusted_runtime)
    frozen, report, approved = load(directory / "frozen.json"), load(directory / "report.json"), load(trusted_runtime)
    if set(frozen["code_sha256"]) != set(runner.CODE_FILES):
        raise ValueError("Unexpected runtime archive inventory")
    for name, digest in frozen["code_sha256"].items():
        if (
            Path(name).name != name
            or approved.get(name) != digest
            or sha((directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Runtime archived bytes differ from independent authority")
    for name in PURE_FILES:
        if sha(Path(runner.__file__).with_name(name).read_bytes()) != approved[name]:
            raise ValueError("Current pure replay helper differs from authenticated runtime")
    cfg = frozen["config"]
    expected_config = runner.configuration(
        cfg["model"],
        mode=cfg["mode"],
        image_edge=cfg["image_edge"],
        viewport=cfg["viewport"],
        transport_concurrency=cfg["transport_concurrency"],
    )
    expected_config["run_id"] = directory.name
    if cfg != expected_config or report["config"] != cfg:
        raise ValueError("Frozen/reported treatment configuration differs")
    source_receipt = frozen["source_pool"]
    if (
        source_receipt["frozen_sha256"] != context["frozen_sha256"]
        or source_receipt["external_map_sha256"] != context["map_sha256"]
        or source_receipt["trusted_code"] != context["trusted"]
        or frozen["records"] != context["frozen"]["records"]
    ):
        raise ValueError("Hosted source authority differs from independently supplied source")
    # Copy integrity is checked explicitly; no directory enumeration or gold read.
    if (
        sha((directory / "source/frozen.json").read_bytes()) != context["frozen_sha256"]
        or load(directory / "source/trusted-code.json") != context["trusted"]
    ):
        raise ValueError("Copied source authority changed")
    for name, digest in context["frozen"]["code_sha256"].items():
        if sha((directory / "source/code" / name).read_bytes()) != digest:
            raise ValueError("Copied source code changed")
    for name, digest in context["frozen"]["artifact_sha256"].items():
        if sha(runner._path(directory / "source", name).read_bytes()) != digest:
            raise ValueError("Copied source artifact changed")
    for name, digest in frozen["artifact_sha256"].items():
        parts = Path(name).parts
        if len(parts) == 3 and parts[0] == "source":
            path = runner._path(directory / "source", str(Path(*parts[1:])))
        elif (
            len(parts) == 1 and name.startswith("question-") and name.endswith(("-request.json", "-wire-encoded.json"))
        ):
            path = directory / name
        else:
            raise ValueError("Unexpected runtime source/request artifact path")
        if sha(path.read_bytes()) != digest:
            raise ValueError("Frozen runtime source/request artifact changed")
    if (
        len(frozen["selected"]) != 24
        or len(report["results"]) != 24
        or report["question_count"] != 24
        or load(directory / "results.json")["results"] != report["results"]
    ):
        raise ValueError("Complete 24-case report denominator required")
    rows, requests = [], []
    stopped = report.get("client_initialization_error") is not None
    prefix = f"P003/{cfg['run_id']}/synthetic-relations/"
    for index, (selected, record, original) in enumerate(
        zip(frozen["selected"], context["records"], report["results"], strict=True)
    ):
        expected = {"index": index, "id": record["id"], "kind": record["kind"], "question_status": "source_refused"}
        body, wire_hash = None, None
        if record["status"] == "ready":
            body, image_receipt = runner.rebuild_request(context["pool"], record, cfg)
            encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
            if len(encoded) > 750_000:
                expected.update(
                    question_status="capacity_refused", reason="Whole request exceeds750000B; no truncation"
                )
            else:
                wire_hash = sha(encoded)
                expected.update(
                    question_status="ready",
                    image_receipt=image_receipt,
                    wire_encoded_sha256=wire_hash,
                    request_bytes=len(encoded),
                    source_ids=record["pair_source_ids"],
                )
                if (
                    load(directory / f"question-{index}-canonical-request.json") != body
                    or load(directory / f"question-{index}-wire-request.json") != body
                    or (directory / f"question-{index}-wire-encoded.json").read_bytes() != encoded
                ):
                    raise ValueError("Exact native canonical/wire request replay differs")
        if selected != expected:
            raise ValueError("Frozen case selection or request metadata differs")
        tag = prefix + str(index)
        identity = {
            "index": index,
            "id": record["id"],
            "kind": record["kind"],
            "model": cfg["model"],
            "provider": "openrouter",
            "tag": tag,
            "wire_encoded_sha256": wire_hash,
        }
        if (
            any(original.get(k) != v for k, v in identity.items())
            or load(directory / f"question-{index}-result.json") != original
        ):
            raise ValueError("Reported case identity or saved outcome differs")
        row = {**identity, "status": "not_attempted", "source_ids": record.get("pair_source_ids", [])}
        response_path = directory / f"question-{index}-response.json"
        if expected["question_status"] != "ready":
            row["status"] = expected["question_status"]
        elif stopped:
            if response_path.exists():
                raise ValueError("A stopped arm retains an unexpected later response")
        elif response_path.exists():
            response = load(response_path)
            row["response_sha256"] = sha(response_path.read_bytes())
            if original.get("entry") != response.get("entry") or original.get("replayed") != response.get("replayed"):
                raise ValueError("Raw response receipt differs from reported receipt")
            try:
                entry = response["entry"]
                if (
                    response.get("replayed") is not False
                    or entry["requested_model"] != cfg["model"]
                    or entry["request_sha256"] != wire_hash
                    or entry["tag"] != tag
                ):
                    raise ValueError("Fresh exact response model/tag/request receipt required")
                if body is None:
                    raise ValueError("No-question case cannot return a native answer")
                receipt = runner.parse_response(record, body, response["result"], cfg)
                row.update(
                    status="valid_abstention" if receipt["abstained"] else "valid_nonabstaining", receipt=receipt
                )
            except (ValueError, KeyError, TypeError):
                row["status"] = "malformed_response"
            if original.get("receipt") != row.get("receipt"):
                raise ValueError("Reported choice/probabilities differ from strict raw replay")
        else:
            if original["status"] != "transport_error" or original.get("error", {}).get("stage") != "transport":
                raise ValueError("Missing fresh response without explicit first transport failure")
            row["status"] = "transport_error"
            stopped = True
        if original["status"] != row["status"]:
            raise ValueError("Reported outcome differs from independent replay")
        rows.append(row)
        requests.append({"id": record["id"], "wire_encoded_sha256": wire_hash})
    counts = dict(Counter(r["status"] for r in rows))
    attempted = sum(r["status"] in ATTEMPTED for r in rows)
    if (
        counts != report["status_counts"]
        or attempted != report["attempted_question_count"]
        or counts.get("valid_nonabstaining", 0) != report["classified_question_count"]
    ):
        raise ValueError("Reported status/attempt/classification counts differ")
    entries = report["charges"]["entries"]
    by_tag = {r["tag"]: r for r in rows if r["status"] in ATTEMPTED}
    if len({e["tag"] for e in entries}) != len(entries) or len(entries) not in {0, attempted}:
        raise ValueError("Financial receipts duplicate or omit only part of attempts")
    for entry in entries:
        financial_row = by_tag.get(entry["tag"])
        if (
            financial_row is None
            or entry["requested_model"] != cfg["model"]
            or entry["request_sha256"] != financial_row["wire_encoded_sha256"]
        ):
            raise ValueError("Financial receipt differs from exact attempted request")
        original = report["results"][financial_row["index"]]
        if "entry" in original and original["entry"] != entry:
            raise ValueError("Returned receipt differs from financial receipt")
    rebuilt_charges = charges(entries, attempted)
    for key, value in rebuilt_charges.items():
        if report["charges"].get(key) != value:
            raise ValueError("Reported financial aggregate differs from retained receipts")
    wall = _number(report["metrics"]["wall_seconds"])
    samples = load(directory / "resources.json")
    peak = max((s["rss_bytes"] for s in samples), default=None)
    if report["metrics"]["peak_sampled_rss_bytes"] != peak:
        raise ValueError("Reported sampled RSS peak differs from retained samples")
    effective = rebuilt_charges["effective_usd"]
    rates = {
        "attempted_questions_per_minute": attempted / wall * 60 if wall else None,
        "valid_nonabstaining_questions_per_minute": counts.get("valid_nonabstaining", 0) / wall * 60 if wall else None,
        "valid_nonabstaining_questions_per_dollar": counts.get("valid_nonabstaining", 0) / effective
        if effective and effective > 0
        else None,
    }
    if (
        any(report[k] != v for k, v in rates.items())
        or any(report[k] is not None for k in ("pages_per_minute", "pages_per_dollar", "full_pipeline_rate"))
        or report["gold_read"] is not False
    ):
        raise ValueError("Reported question scope/rates or source-only boundary differs")
    return {
        "directory": str(directory),
        "config": cfg,
        "rows": rows,
        "requests": requests,
        "status_counts": counts,
        "charges": rebuilt_charges,
        "rates": rates,
        "reported_metrics": report["metrics"],
        "reported_preprocessing": report["preprocessing"],
        "runtime_map_sha256": sha(trusted_runtime.read_bytes()),
        "source_map_sha256": context["map_sha256"],
        "source_frozen_sha256": context["frozen_sha256"],
        "report_sha256": sha((directory / "report.json").read_bytes()),
        "runtime_frozen_sha256": sha((directory / "frozen.json").read_bytes()),
        "gold_accessed": False,
        "full_pipeline_rate": None,
    }


def load_gold(path: Path, expected_sha256: str, context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Evaluation-only explicit label authority, separate from all model input reconstruction."""
    path = guard_path(path)
    if sha(path.read_bytes()) != expected_sha256:
        raise ValueError("Private generator gold differs from separately supplied authority")
    value = load(path)
    if value["source_frozen_sha256"] != context["frozen_sha256"]:
        raise ValueError("Gold belongs to a different immutable source freeze")
    gold = {r["id"]: r for r in value["cases"]}
    if len(gold) != 24 or len(value["cases"]) != 24 or set(gold) != {r["id"] for r in context["records"]}:
        raise ValueError("Complete unique 24-case gold inventory required")
    indistinguishable = {
        i
        for pair in context["frozen"]["counterfactual_twins"]
        if pair["observed_drawings_byte_identical"]
        for i in pair["case_ids"]
    }
    for record in context["records"]:
        target = gold[record["id"]]
        a, b = target["memberships"]
        same = all(a[k] == b[k] for k in ("table", "row"))
        if target["kind"] != "row":
            same = same and a["cell"] == b["cell"]
        if target["kind"] == "wrap":
            same = same and b["physical_sequence"] > a["physical_sequence"]
        words = {w["id"]: w["text"] for w in record["source"]["words"]}
        if (
            target["kind"] != record["kind"]
            or target["pdf_sha256"] != record["pdf_sha256"]
            or target["pair_source_ids"] != record["pair_source_ids"]
            or target["pair_literals"] != [words[i] for i in record["pair_source_ids"]]
            or target["actual_source_sha256"] != sha(evidence.dump(record["source"]).encode())
            or target["expected_choice"] != ("same" if same else "separate")
            or target["evidence_limitation"] != (record["id"] in indistinguishable)
        ):
            raise ValueError("Construction membership, literal identity or limitation receipt differs")
    for pair in context["frozen"]["counterfactual_twins"]:
        if {gold[i]["expected_choice"] for i in pair["case_ids"]} != {"same", "separate"}:
            raise ValueError("Counterfactual labels must be opposing generator memberships")
    return gold


def score(verified: dict[str, Any], gold: dict[str, dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    """Keep full operational denominators and hidden-label agreement separate from answerability."""
    rows = [
        {
            **r,
            "expected_choice": gold[r["id"]]["expected_choice"],
            "indeterminate": gold[r["id"]]["evidence_limitation"],
        }
        for r in verified["rows"]
    ]

    def aggregate(selected: list[dict[str, Any]]) -> dict[str, Any]:
        decisive = [r for r in selected if r["status"] == "valid_nonabstaining"]
        correct = sum(r["receipt"]["choice"] == r["expected_choice"] for r in decisive)
        confusion = Counter((r["expected_choice"], r.get("receipt", {}).get("choice", r["status"])) for r in selected)
        return {
            "intended_count": len(selected),
            "status_counts": dict(Counter(r["status"] for r in selected)),
            "valid_nonabstaining_count": len(decisive),
            "author_label_matches": correct,
            "strict_author_label_fraction": correct / len(selected) if selected else None,
            "conditional_decisive_author_label_fraction": correct / len(decisive) if decisive else None,
            "confusion": [
                {"expected": a, "observed": b, "count": count} for (a, b), count in sorted(confusion.items())
            ],
            "interpretation": "Hidden generator-label agreement; not a claim every label is recoverable from this treatment",
        }

    by_id = {r["id"]: r for r in rows}
    bodies = {r["id"]: r["wire_encoded_sha256"] for r in verified["requests"]}
    twins = []
    for pair in context["frozen"]["counterfactual_twins"]:
        a, b = [by_id[i] for i in pair["case_ids"]]
        both_valid = all(r["status"].startswith("valid_") for r in (a, b))
        same_evidence = bodies[a["id"]] is not None and bodies[a["id"]] == bodies[b["id"]]
        twins.append(
            {
                "case_ids": pair["case_ids"],
                "kind": pair["kind"],
                "identical_request_bytes": same_evidence,
                "both_valid": both_valid,
                "choice_consistent": a["receipt"]["choice"] == b["receipt"]["choice"] if both_valid else None,
                "raw_probabilities_consistent": a["receipt"]["raw_probabilities"] == b["receipt"]["raw_probabilities"]
                if both_valid
                else None,
                "both_abstained": all(r["status"] == "valid_abstention" for r in (a, b)),
                "author_label_matches": sum(r.get("receipt", {}).get("choice") == r["expected_choice"] for r in (a, b)),
            }
        )
    identical = sum(t["identical_request_bytes"] for t in twins)
    return {
        "config": verified["config"],
        "all_24": aggregate(rows),
        "visually_cued_18": aggregate([r for r in rows if not r["indeterminate"]]),
        "indeterminate_6": aggregate([r for r in rows if r["indeterminate"]]),
        "per_kind": {kind: aggregate([r for r in rows if r["kind"] == kind]) for kind in evidence.KINDS},
        "twins": twins,
        "twins_summary": {
            "intended_pair_count": 12,
            "both_valid_count": sum(t["both_valid"] for t in twins),
            "consistent_choice_count": sum(t["choice_consistent"] is True for t in twins),
            "identical_request_pair_count": identical,
            "both_abstained_count": sum(t["both_abstained"] for t in twins),
        },
        "evidence_conditioned_control": {
            "identical_request_opposing_label_pairs": identical,
            "deterministic_identical_response_author_label_maximum": 24 - identical,
            "deterministic_identical_response_author_label_ceiling_fraction": (24 - identical) / 24,
            "scope": "Deterministic identical answers cannot match opposing labels; stochastic realized outcomes may fluctuate, so this is not an absolute sampled accuracy ceiling",
        },
        "charges": verified["charges"],
        "question_rates": verified["rates"],
        "full_pipeline_rate": None,
        "source_assignments": False,
        "gold_access": "Evaluation only, after independent source/request/response verification",
    }


def evaluate(
    pool: Path,
    source_trust: Path,
    runs: list[Path],
    runtime_maps: list[Path],
    gold_path: Path,
    gold_sha256: str,
    output: Path,
) -> dict[str, Any]:
    """Verify all explicitly supplied runs first, then score separate generator-owned labels."""
    began, cpu = time.perf_counter(), time.process_time()
    output = guard_path(output)
    if output.exists() or len(runs) != len(runtime_maps) or not runs:
        raise ValueError("New output and matching explicit run/runtime-authority lists required")
    context = source_context(pool, source_trust)
    verified = [verify_run(directory, trusted, context) for directory, trusted in zip(runs, runtime_maps, strict=True)]
    gold = load_gold(gold_path, gold_sha256, context)
    output.mkdir(parents=True)
    scores = []
    for index, run in enumerate(verified):
        result = score(run, gold, context)
        write_json(output / f"arm-{index}-verified.json", run)
        write_json(output / f"arm-{index}-score.json", result)
        scores.append(result)
    summary = {
        "scores": scores,
        "source_frozen_sha256": context["frozen_sha256"],
        "external_source_map_sha256": context["map_sha256"],
        "gold_sha256": gold_sha256,
        "gold_path": str(guard_path(gold_path)),
        "evaluator_sha256": sha(Path(__file__).read_bytes()),
        "new_calls": 0,
        "ledger_accessed": False,
        "full_pipeline_rate": None,
        "resources": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "One offline parent; perf_counter/process_time; unsampled lifetime getrusage including imports",
        },
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    """Read labels only in this separate evaluator, never in a model-input runner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pool", type=Path, required=True)
    parser.add_argument("--source-trusted-code", type=Path, required=True)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--runtime-trusted-code", type=Path, action="append", required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--gold-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(
        args.source_pool,
        args.source_trusted_code,
        args.run,
        args.runtime_trusted_code,
        args.gold,
        args.gold_sha256,
        args.output,
    )
    print(
        evidence.dump(
            {
                "arm_count": len(result["scores"]),
                "new_calls": 0,
                "full_pipeline_rate": None,
                "resources": result["resources"],
            }
        )
    )


if __name__ == "__main__":
    main()
