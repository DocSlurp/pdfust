"""Independent shared-context request/outcome replay and separate synthetic scoring."""

# ruff: noqa: EM101, TRY003, TRY301, C901, PLR0912, E501, SLF001, PLR2004
from __future__ import annotations

import argparse
import json
import resource
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_synthetic_relations as evidence
from bench import p003_synthetic_relations_eval as single_eval
from bench import p003_synthetic_relations_multi as protocol
from bench import p003_synthetic_relations_multi_run as runner
from bench import p003_synthetic_relations_run as single
from bench.silver import guard_path, sha, write_json

PURE_FILES = (*single_eval.PURE_FILES, "p003_synthetic_relations_multi.py", "p003_synthetic_relations_multi_run.py")


def verify_run(directory: Path, runtime_map: Path, context: dict[str, Any]) -> dict[str, Any]:
    """Rebuild all full source packets, group envelopes and atomic raw outcomes without labels."""
    directory, runtime_map = guard_path(directory), guard_path(runtime_map)
    load = single_eval.load
    frozen, report, approved = load(directory / "frozen.json"), load(directory / "report.json"), load(runtime_map)
    if set(frozen["code_sha256"]) != set(runner.CODE_FILES):
        raise ValueError("Unexpected shared-context runtime code inventory")
    for name, digest in frozen["code_sha256"].items():
        if approved.get(name) != digest or sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived runtime bytes differ from independent external authority")
    for name in PURE_FILES:
        if sha(Path(runner.__file__).with_name(name).read_bytes()) != approved[name]:
            raise ValueError("Current pure replay helper differs from independent runtime authority")
    if frozen["gold_read_or_copied"] is not False or frozen["references_read"] is not False:
        raise ValueError("Runtime source-only boundary differs")
    cfg = frozen["config"]
    expected_config = runner.configuration(
        cfg["model"],
        size=cfg["question_group_size"],
        mode=cfg["mode"],
        transport_concurrency=cfg["transport_concurrency"],
    )
    expected_config["run_id"] = directory.name
    if cfg != expected_config or report["config"] != cfg:
        raise ValueError("Reported/frozen shared-context configuration differs")
    receipt = frozen["source_pool"]
    if (
        receipt["frozen_sha256"] != context["frozen_sha256"]
        or receipt["external_map_sha256"] != context["map_sha256"]
        or receipt["trusted_code"] != context["trusted"]
        or frozen["records"] != context["frozen"]["records"]
    ):
        raise ValueError("Hosted source authority differs from independently supplied source")
    if (
        sha((directory / "source/frozen.json").read_bytes()) != context["frozen_sha256"]
        or load(directory / "source/trusted-code.json") != context["trusted"]
    ):
        raise ValueError("Copied source authority changed")
    for name, digest in context["frozen"]["code_sha256"].items():
        if sha((directory / "source/code" / name).read_bytes()) != digest:
            raise ValueError("Copied source code changed")
    for name, digest in context["frozen"]["artifact_sha256"].items():
        if sha(single._path(directory / "source", name).read_bytes()) != digest:
            raise ValueError("Copied actual source artifact changed")
    for name, digest in frozen["artifact_sha256"].items():
        parts = Path(name).parts
        if len(parts) == 3 and parts[0] == "source":
            path = single._path(directory / "source", str(Path(*parts[1:])))
        elif len(parts) == 1 and name.startswith("group-") and name.endswith(("-request.json", "-wire-encoded.json")):
            path = directory / name
        else:
            raise ValueError("Unexpected shared-context artifact path")
        if sha(path.read_bytes()) != digest:
            raise ValueError("Frozen source/request artifact changed")
    groups = protocol.groups(context["records"], cfg["question_group_size"])
    if (
        len(frozen["selected"]) != len(groups)
        or len(report["groups"]) != len(groups)
        or len(report["results"]) != 24
        or report["question_count"] != 24
        or report["group_count"] != len(groups)
        or frozen["group_count"] != len(groups)
        or frozen["question_count"] != 24
        or load(directory / "results.json") != {"groups": report["groups"], "results": report["results"]}
    ):
        raise ValueError("Complete 24-case and exact group denominator required")
    stopped = report.get("client_initialization_error") is not None
    prefix = f"P003/{directory.name}/synthetic-shared-context/"
    rows, requests, verified_groups = [], [], []
    for index, (group, selected, original) in enumerate(zip(groups, frozen["selected"], report["groups"], strict=True)):
        expected: dict[str, Any] = {
            "index": index,
            "case_ids": [r["id"] for r in group],
            "question_keys": [f"q{i}" for i in range(len(group))],
            "question_status": "source_refused",
            "omitted_word_count": 0,
        }
        body, wire_hash = None, None
        if all(r["status"] == "ready" for r in group):
            try:
                body = protocol.request(group, cfg)
                encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
                if len(encoded) > protocol.MAX_BODY_BYTES:
                    raise ValueError("Whole request exceeds 750000 bytes; no truncation")
            except ValueError as error:
                expected.update(question_status="capacity_refused", reason=str(error))
            else:
                wire_hash = sha(encoded)
                expected.update(
                    question_status="ready",
                    wire_encoded_sha256=wire_hash,
                    request_bytes=len(encoded),
                    state_utf8_bytes=len(body["state"].encode()),
                    word_count=sum(len(r["source"]["words"]) for r in group),
                    evidence_sha256=[sha(evidence.dump(evidence.packet(r, mode=cfg["mode"])).encode()) for r in group],
                )
                if (
                    load(directory / f"group-{index}-canonical-request.json") != body
                    or load(directory / f"group-{index}-wire-request.json") != body
                    or (directory / f"group-{index}-wire-encoded.json").read_bytes() != encoded
                ):
                    raise ValueError("Exact scoped native canonical/wire request replay differs")
        if selected != expected:
            raise ValueError("Frozen grouping, literal coverage or evidence receipt differs")
        tag = prefix + str(index)
        identity = {
            "index": index,
            "case_ids": [r["id"] for r in group],
            "model": cfg["model"],
            "provider": "openrouter",
            "tag": tag,
            "wire_encoded_sha256": wire_hash,
        }
        if (
            any(original.get(k) != v for k, v in identity.items())
            or load(directory / f"group-{index}-result.json") != original
        ):
            raise ValueError("Reported group identity or saved outcome differs")
        status, receipts = "not_attempted", None
        response_path = directory / f"group-{index}-response.json"
        if expected["question_status"] != "ready":
            status = expected["question_status"]
            if response_path.exists():
                raise ValueError("Refused group has an unexpected response")
        elif stopped:
            if response_path.exists():
                raise ValueError("Stopped arm has an unexpected later response")
        elif response_path.exists():
            response = load(response_path)
            actual_usage = response["result"].get("usage", {}) if isinstance(response.get("result"), dict) else {}
            if original.get("usage") != actual_usage:
                raise ValueError("Reported usage differs from retained provider response")
            if original.get("entry") != response.get("entry") or original.get("replayed") != response.get("replayed"):
                raise ValueError("Raw and reported response financial receipt differs")
            try:
                entry = response["entry"]
                if (
                    response.get("replayed") is not False
                    or entry["requested_model"] != cfg["model"]
                    or entry["request_sha256"] != wire_hash
                    or entry["tag"] != tag
                ):
                    raise ValueError("Fresh exact model/tag/wire receipt required")
                if body is None:
                    raise ValueError("Refused group cannot return an answer")
                receipts = protocol.parse(group, body, response["result"], cfg)
                status = "valid"
            except (ValueError, KeyError, TypeError):
                status = "malformed_response"
            if original.get("receipts") != receipts:
                raise ValueError("Reported probabilities differ from complete atomic raw replay")
        else:
            if original["status"] != "transport_error" or original.get("error", {}).get("stage") != "transport":
                raise ValueError("Missing fresh response without explicit first transport failure")
            status, stopped = "transport_error", True
        if original["status"] != status:
            raise ValueError("Reported group outcome differs from independent atomic replay")
        verified_groups.append({**identity, "status": status})
        for local, record in enumerate(group):
            row = {
                "id": record["id"],
                "kind": record["kind"],
                "group_index": index,
                "question_key": f"q{local}",
                "status": status,
                "wire_encoded_sha256": wire_hash,
                "shared_charge_scope": "Group request only; no per-case duplicated financial entry",
            }
            if receipts is not None:
                row.update(
                    receipt=receipts[local],
                    status="valid_abstention" if receipts[local]["abstained"] else "valid_nonabstaining",
                )
            rows.append(row)
            # Local packet identity is distinct from full shared request identity for twin interpretation.
            local_hash = (
                sha(evidence.dump(evidence.packet(record, mode=cfg["mode"])).encode())
                if record["status"] == "ready"
                else None
            )
            requests.append(
                {
                    "id": record["id"],
                    "wire_encoded_sha256": wire_hash,
                    "local_evidence_sha256": local_hash,
                    "question_key": f"q{local}",
                    "group_index": index,
                }
            )
    if rows != report["results"]:
        raise ValueError("Individual outcomes differ from complete group envelope replay")
    counts = dict(Counter(r["status"] for r in rows))
    attempted = sum(g["status"] in runner.ATTEMPTED for g in verified_groups)
    attempted_questions = sum(len(g["case_ids"]) for g in verified_groups if g["status"] in runner.ATTEMPTED)
    if (
        counts != report["status_counts"]
        or dict(Counter(g["status"] for g in verified_groups)) != report["group_status_counts"]
        or report["attempted_group_count"] != attempted
        or report["attempted_question_count"] != attempted_questions
        or report["classified_question_count"] != counts.get("valid_nonabstaining", 0)
    ):
        raise ValueError("Shared group/question count differs")
    entries = report["charges"]["entries"]
    by_tag = {g["tag"]: g for g in verified_groups if g["status"] in runner.ATTEMPTED}
    if len({e["tag"] for e in entries}) != len(entries) or len(entries) not in {0, attempted}:
        raise ValueError("Shared financial receipt duplicated or partially omitted")
    for entry in entries:
        g = by_tag.get(entry["tag"])
        if g is None or entry["requested_model"] != cfg["model"] or entry["request_sha256"] != g["wire_encoded_sha256"]:
            raise ValueError("Financial receipt differs from exact attempted shared request")
        original = report["groups"][g["index"]]
        if "entry" in original and original["entry"] != entry:
            raise ValueError("Returned receipt differs from shared financial receipt")
    charges = single_eval.charges(entries, attempted)
    if any(report["charges"].get(k) != v for k, v in charges.items()):
        raise ValueError("Reported shared financial totals differ from receipts counted once")
    wall = single_eval._number(report["metrics"]["wall_seconds"])
    samples = load(directory / "resources.json")
    if report["metrics"]["peak_sampled_rss_bytes"] != max((s["rss_bytes"] for s in samples), default=None):
        raise ValueError("Reported sampled RSS differs")
    effective = charges["effective_usd"]
    rates = {
        "attempted_requests_per_minute": attempted / wall * 60 if wall else None,
        "attempted_questions_per_minute": attempted_questions / wall * 60 if wall else None,
        "valid_nonabstaining_questions_per_minute": counts.get("valid_nonabstaining", 0) / wall * 60 if wall else None,
        "valid_nonabstaining_questions_per_dollar": counts.get("valid_nonabstaining", 0) / effective
        if effective and effective > 0
        else None,
    }
    if (
        any(report[k] != v for k, v in rates.items())
        or any(report[k] is not None for k in ("pages_per_minute", "pages_per_dollar", "full_pipeline_rate"))
        or report["gold_read"] is not False
        or report["correctness_measured"] is not False
        or any(report[k] != 0 for k in ("source_assignments_applied", "model_fallbacks", "retries"))
    ):
        raise ValueError("Reported shared-context rates or scope differs")
    return {
        "config": cfg,
        "rows": rows,
        "requests": requests,
        "groups": verified_groups,
        "charges": charges,
        "rates": rates,
        "source_frozen_sha256": context["frozen_sha256"],
        "runtime_map_sha256": sha(runtime_map.read_bytes()),
        "report_sha256": sha((directory / "report.json").read_bytes()),
        "gold_accessed": False,
        "full_pipeline_rate": None,
    }


def score(verified: dict[str, Any], gold: dict[str, dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    """Score labels separately, distinguishing identical local evidence from different shared contexts."""
    # Reuse aggregate denominators only; full shared request hashes cannot establish twin-local identity.
    local = {
        **verified,
        "requests": [{**r, "wire_encoded_sha256": r["local_evidence_sha256"]} for r in verified["requests"]],
    }
    scored = single_eval.score(local, gold, context)
    scored["evidence_conditioned_control"]["scope"] = (
        "Local packet equality only. Different shared co-contexts and qN positions may yield different answers; "
        "the single-question deterministic identical-request bound is not an enforced bound for this treatment."
    )
    scored["evidence_conditioned_control"].pop("deterministic_identical_response_author_label_maximum")
    scored["evidence_conditioned_control"].pop("deterministic_identical_response_author_label_ceiling_fraction")
    scored["evidence_conditioned_control"]["identical_local_evidence_opposing_label_pairs"] = scored[
        "evidence_conditioned_control"
    ].pop("identical_request_opposing_label_pairs")
    for twin in scored["twins"]:
        twin["identical_local_evidence"] = twin.pop("identical_request_bytes")
    scored["twins_summary"]["identical_local_evidence_pair_count"] = scored["twins_summary"].pop(
        "identical_request_pair_count"
    )
    scored["groups"] = verified["groups"]
    scored["cross_case_interference"] = (
        "Compare source-ID matched choices/probabilities with independently verified single-question arms; no isolation guarantee or paired-label promise"
    )
    return scored


def compare(single_verified: dict[str, Any], multi_verified: dict[str, Any]) -> dict[str, Any]:
    """Measure source-ID matched interference only across equal model/evidence and text-only arms."""
    a, b = single_verified["config"], multi_verified["config"]
    if (
        a["model"] != b["model"]
        or a["mode"] != b["mode"]
        or a["image_edge"] != 0
        or single_verified["source_frozen_sha256"] != multi_verified["source_frozen_sha256"]
    ):
        raise ValueError("Matching authenticated source, model and text-only evidence treatments required")
    before = {r["id"]: r for r in single_verified["rows"]}
    differences = []
    for row in multi_verified["rows"]:
        prior = before[row["id"]]
        valid = all(r["status"].startswith("valid_") for r in (row, prior))
        differences.append(
            {
                "id": row["id"],
                "kind": row["kind"],
                "question_key": row["question_key"],
                "group_index": row["group_index"],
                "single_status": prior["status"],
                "shared_status": row["status"],
                "both_valid": valid,
                "choice_changed": prior["receipt"]["choice"] != row["receipt"]["choice"] if valid else None,
                "raw_probabilities_changed": prior["receipt"]["raw_probabilities"]
                != row["receipt"]["raw_probabilities"]
                if valid
                else None,
                "absolute_raw_probability_deltas": {
                    key: abs(prior["receipt"]["raw_probabilities"][key] - row["receipt"]["raw_probabilities"][key])
                    for key in evidence.CRITERIA[row["kind"]]
                }
                if valid
                else None,
            }
        )
    return {
        "case_count": 24,
        "both_valid_count": sum(r["both_valid"] for r in differences),
        "choice_changed_count": sum(r["choice_changed"] is True for r in differences),
        "raw_probabilities_changed_count": sum(r["raw_probabilities_changed"] is True for r in differences),
        "cases": differences,
        "accuracy_claim": False,
        "interpretation": "Shared-context/instruction/qN-position change versus retained single calls; stochastic repetition and financial contention are uncontrolled",
    }


def main() -> None:
    """Verify every supplied arm before opening separately authorized generator labels."""
    began, cpu = time.perf_counter(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pool", type=Path, required=True)
    parser.add_argument("--source-trusted-code", type=Path, required=True)
    parser.add_argument("--run", action="append", type=Path, required=True)
    parser.add_argument("--runtime-trusted-code", action="append", type=Path, required=True)
    parser.add_argument("--single-run", action="append", type=Path, default=[])
    parser.add_argument("--single-runtime-trusted-code", action="append", type=Path, default=[])
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--gold-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output = guard_path(args.output)
    if args.output.exists() or len(args.run) != len(args.runtime_trusted_code):
        raise ValueError("New output and matching external runtime maps required")
    context = single_eval.source_context(args.source_pool, args.source_trusted_code)
    verified = [verify_run(d, m, context) for d, m in zip(args.run, args.runtime_trusted_code, strict=True)]
    if len(args.single_run) != len(args.single_runtime_trusted_code):
        raise ValueError("Matching optional single-run/runtime maps required")
    controls = [
        single_eval.verify_run(d, m, context)
        for d, m in zip(args.single_run, args.single_runtime_trusted_code, strict=True)
    ]
    comparisons = [
        compare(control, arm)
        for control in controls
        for arm in verified
        if control["config"]["model"] == arm["config"]["model"] and control["config"]["mode"] == arm["config"]["mode"]
    ]
    gold = single_eval.load_gold(args.gold, args.gold_sha256, context)
    args.output.mkdir(parents=True)
    scores = []
    for index, arm in enumerate(verified):
        result = score(arm, gold, context)
        write_json(args.output / f"arm-{index}-verified.json", arm)
        write_json(args.output / f"arm-{index}-score.json", result)
        scores.append(result)
    write_json(
        args.output / "summary.json",
        {
            "scores": scores,
            "single_vs_shared_context": comparisons,
            "new_calls": 0,
            "gold_sha256": args.gold_sha256,
            "evaluator_sha256": sha(Path(__file__).read_bytes()),
            "resources": {
                "wall_seconds": time.perf_counter() - began,
                "cpu_seconds": time.process_time() - cpu,
                "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "measurement": "Offline parent; unsampled lifetime getrusage includes imports",
            },
            "full_pipeline_rate": None,
        },
    )
    print(evidence.dump({"arm_count": len(scores), "new_calls": 0}))


if __name__ == "__main__":
    main()
