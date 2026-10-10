"""Independent offline request/source replay and exact native-name normalization audit."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415, SLF001, E501
from __future__ import annotations

import argparse
import json
import math
import resource
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench.silver import canonical, guard_path, sha, write_json

RUNS = ("laya-micro-r0", "laya-verbose-r0", "d1-micro-r0", "d1-verbose-r0")
PURE_CODE = (
    "p003_micro_relations.py",
    "pipeline_row_evidence.py",
    "p003_topology_ownership.py",
    "p003_transport.py",
    "decision_gateway_vision.py",
    "decision_gateway.py",
    "pipeline_regions.py",
)


def name_only_delta(original: dict[str, Any], normalized: dict[str, Any], question_ids: set[str]) -> dict[str, Any]:
    """Prove exact name removal without permitting any rank/probability/confidence alteration."""
    expected = deepcopy(original)
    if not isinstance(expected.get("answers"), dict) or set(expected["answers"]) != question_ids:
        raise ValueError("Unexpected answer inventory")
    removed = []
    for identifier in sorted(question_ids):
        answer = expected["answers"][identifier]
        if not isinstance(answer, dict) or answer.get("name") != identifier:
            raise ValueError("Only exact native question-name echo is removable")
        del answer["name"]
        removed.append(f"answers.{identifier}.name")
    if normalized != expected:
        raise ValueError("Normalization changed content beyond exact echoed name")
    return {
        "removed_fields": removed,
        "other_fields_unchanged": True,
        "probabilities_unchanged": True,
        "choice_unchanged": True,
        "raw_confidence_unchanged": True,
        "ordering_or_ranking_changed": False,
        "original_sha256": sha(canonical(original)),
        "normalized_sha256": sha(canonical(normalized)),
    }


def margins(decision: dict[str, Any]) -> dict[str, Any]:
    """Describe retained raw margins without normalization or calibrated correctness claims."""
    values = decision["raw_probabilities"]
    choice = decision["choice"]
    if (
        not isinstance(values, dict)
        or choice not in values
        or any(type(v) not in (int, float) or not math.isfinite(v) for v in values.values())
    ):
        raise ValueError("Finite declared raw decision probabilities required")
    others = [v for k, v in values.items() if k != choice]
    return {
        "choice": choice,
        "chosen_raw_probability": values[choice],
        "runner_up_raw_probability": max(others),
        "chosen_minus_runner_up": values[choice] - max(others),
        "raw_mass": sum(values.values()),
        "argmax_tie": sum(v == max(values.values()) for v in values.values()) > 1,
        "raw_probabilities": deepcopy(values),
        "uncalibrated": True,
    }


def paired(micro: list[dict[str, Any]], verbose: list[dict[str, Any]]) -> dict[str, Any]:
    """Match exact source pair identities; missing/failed responses never become valid comparisons."""

    def identity(row: dict[str, Any]) -> tuple[str, str, str, tuple[str, ...]]:
        return row["page_id"], row["pair_id"], row["kind"], tuple(row["source_ids"])

    left = {identity(r): r for r in micro}
    right = {identity(r): r for r in verbose}
    if len(left) != len(micro) or len(right) != len(verbose) or set(left) != set(right):
        raise ValueError("Pair inventories differ or duplicate")
    rows = []
    for key, a in left.items():
        b = right[key]
        row = {
            "page_id": key[0],
            "pair_id": key[1],
            "kind": key[2],
            "source_ids": list(key[3]),
            "micro_status": a["offline_status"],
            "verbose_status": b["offline_status"],
            "paired_valid": False,
        }
        if "receipt" in a and "receipt" in b:
            am, bm = margins(a["receipt"]["decision"]), margins(b["receipt"]["decision"])
            row.update(
                paired_valid=True,
                micro=am,
                verbose=bm,
                choice_disagreement=am["choice"] != bm["choice"],
                chosen_margin_delta=bm["chosen_minus_runner_up"] - am["chosen_minus_runner_up"],
            )
        rows.append(row)
    valid = [r for r in rows if r["paired_valid"]]
    return {
        "intended_pair_count": len(rows),
        "valid_pair_count": len(valid),
        "choice_disagreement_count": sum(r["choice_disagreement"] for r in valid),
        "unpaired_or_failed_count": len(rows) - len(valid),
        "rows": rows,
        "accuracy_measured": False,
        "scope": "Within-model evidence-format disagreement, not correctness or complete extraction",
    }


def audit_run(directory: Path, trusted_code: Path, source_trust: Path, normalizer_sha256: str) -> dict[str, Any]:
    """Require operator-supplied independent authorities; replay all source plans and wire bytes locally."""
    from bench import p003_gateway_answer as native
    from bench import p003_micro_relations as micro  # type: ignore[attr-defined]
    from bench import p003_micro_relations_run as runner  # type: ignore[attr-defined]
    from bench.p003_transport import gateway_wire

    directory, trusted_code, source_trust = [guard_path(p) for p in (directory, trusted_code, source_trust)]
    frozen = json.loads((directory / "frozen.json").read_bytes())
    original = json.loads((directory / "report.json").read_bytes())
    approved = json.loads(trusted_code.read_bytes())
    if sha(Path(native.__file__).read_bytes()) != normalizer_sha256:
        raise ValueError("Normalizer differs from independently reviewed digest")
    for name, digest in frozen["code_sha256"].items():
        if (
            Path(name).name != name
            or approved.get(name) != digest
            or sha((directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Archived code differs from independent operator map")
    for name in PURE_CODE:
        if sha(Path(micro.__file__).with_name(name).read_bytes()) != approved.get(name):
            raise ValueError("Current pure replay implementation differs from independently approved code")
    for name, digest in frozen["artifact_sha256"].items():
        if Path(name).name != name or sha((directory / name).read_bytes()) != digest:
            raise ValueError("Frozen source/request artifact changed")
    source_map = json.loads(source_trust.read_bytes())
    source_frozen, source_report = runner.source.authenticate_source(directory / "baseline", source_map)
    if (
        source_map != frozen["baseline"]["trusted_code"]
        or frozen["records"] != source_frozen["records"]
        or sha((directory / "baseline/frozen.json").read_bytes()) != frozen["baseline"]["frozen_sha256"]
        or sha((directory / "baseline/report.json").read_bytes()) != frozen["baseline"]["report_sha256"]
    ):
        raise ValueError("Archived source differs from independently authorized source baseline")
    plans = {
        ident: json.loads((directory / f"{ident}-micro-plan.json").read_bytes())
        for ident in frozen["source_plan_sha256"]
    }
    successful = {r["id"]: r for r in source_report["results"] if r["status"] == "ok"}
    if set(plans) != set(successful):
        raise ValueError("Frozen source plan omits or adds intended source pages")
    for ident, plan in plans.items():
        if (
            plan["source"] != successful[ident]["source"]
            or micro.freeze(plan["source"]) != plan
            or plan["snapshot_sha256"] != frozen["source_plan_sha256"][ident]
        ):
            raise ValueError("Complete source evidence/pair freeze changed")
    chosen = runner.select(plans)
    if (
        sha(micro._dump(chosen).encode()) != frozen["question_inventory_sha256"]
        or len(chosen) != len(frozen["selected"])
        or len(original["results"]) != len(chosen)
    ):
        raise ValueError("Hash-ranked question selection changed")
    outcomes = []
    for index, selected in enumerate(frozen["selected"]):
        if {k: selected[k] for k in chosen[index]} != chosen[index]:
            raise ValueError("Pair identity/order differs")
        plan = plans[selected["page_id"]]
        body = micro.body(plan, selected["id"], frozen["config"]["model"], mode=frozen["config"]["mode"])
        wire, is_native = gateway_wire(body)
        encoded = json.dumps(wire, separators=(",", ":"), allow_nan=False).encode()
        if (
            body != json.loads((directory / f"question-{index}-canonical-request.json").read_bytes())
            or wire != json.loads((directory / f"question-{index}-wire-request.json").read_bytes())
            or encoded != (directory / f"question-{index}-wire-encoded.json").read_bytes()
            or sha(encoded) != selected["wire_encoded_sha256"]
        ):
            raise ValueError("Exact canonical/native wire request changed")
        prior = original["results"][index]
        row = {
            "index": index,
            "page_id": selected["page_id"],
            "pair_id": selected["id"],
            "kind": selected["kind"],
            "source_ids": selected["source_ids"],
            "original_status": prior["status"],
            "offline_status": prior["status"],
            "state_utf8_bytes": len(body["state"].encode()),
            "wire_bytes": len(encoded),
            "wire_sha256": sha(encoded),
            "normalization": "none",
        }
        response_path = directory / f"question-{index}-response.json"
        if response_path.exists():
            response = json.loads(response_path.read_bytes())
            entry = response["entry"]
            result = response["result"]
            if (
                response["replayed"] is not False
                or entry != prior["entry"]
                or entry["requested_model"] != frozen["config"]["model"]
                or entry["request_sha256"] != sha(encoded)
            ):
                raise ValueError("Returned response/fresh transmission receipt differs")
            adjusted = (
                native.normalize(result, model=body["model"], question_ids=set(body["questions"]))
                if is_native
                else deepcopy(result)
            )
            if is_native:
                row.update(
                    normalization="exact native name echo removed",
                    normalization_delta=name_only_delta(result, adjusted, set(body["questions"])),
                )
            elif adjusted != result:
                raise ValueError("Non-native Gateway response must remain unchanged")
            receipt = micro.receipt(plan, selected["id"], body, adjusted, mode=frozen["config"]["mode"])
            if (
                receipt["decision"]["raw_probabilities"] != adjusted["answers"]["q0"]["probabilities"]
                or receipt["decision"]["choice"] != adjusted["answers"]["q0"]["choice"]
            ):
                raise ValueError("Strict parser changed raw probabilities or declared choice")
            row.update(
                offline_status="valid_abstention" if receipt["abstained"] else "valid_nonabstaining",
                receipt=receipt,
                raw_response_sha256=sha(response_path.read_bytes()),
            )
        outcomes.append(row)
    errors = []
    for entry in original.get("charges", {}).get("entries", []):
        if "error" in entry:
            matched = next((r for r in outcomes if r["wire_sha256"] == entry.get("request_sha256")), None)
            if (
                matched is None
                or matched["wire_bytes"] != entry.get("request_bytes")
                or entry.get("requested_model") != frozen["config"]["model"]
            ):
                raise ValueError("Retained error receipt does not match frozen wire bytes/model")
            errors.append(
                {
                    "request_index": matched["index"],
                    "error": entry["error"],
                    "endpoint": entry.get("endpoint"),
                    "request_bytes": entry["request_bytes"],
                    "state_utf8_bytes": matched["state_utf8_bytes"],
                    "diagnostic": entry.get("http_error_diagnostic"),
                    "server_error_body_retained": False,
                    "causal_reason_identified": False,
                    "further_reason": "Available categorical receipt contains no server validation reason",
                    "reserved_usd": entry.get("reservation_usd"),
                    "cost_status": entry.get("cost_status"),
                }
            )
    return {
        "run": directory.name,
        "model": frozen["config"]["model"],
        "mode": frozen["config"]["mode"],
        "directory": str(directory),
        "frozen_sha256": sha((directory / "frozen.json").read_bytes()),
        "original_report_sha256": sha((directory / "report.json").read_bytes()),
        "external_code_map": str(trusted_code),
        "external_code_map_sha256": sha(trusted_code.read_bytes()),
        "external_source_map": str(source_trust),
        "external_source_map_sha256": sha(source_trust.read_bytes()),
        "normalizer_sha256": normalizer_sha256,
        "original_status_counts": original["status_counts"],
        "offline_status_counts": dict(Counter(r["offline_status"] for r in outcomes)),
        "results": outcomes,
        "errors": errors,
        "new_calls": 0,
        "accuracy_measured": False,
        "original_outcomes_modified": False,
        "ledger_accessed": False,
    }


def audit(
    root: Path, trust_directory: Path, source_trust: Path, normalizer_sha256: str, output: Path
) -> dict[str, Any]:
    """Freeze reproducible four-arm diagnostics without client construction or original outcome mutation."""
    started, cpu = time.perf_counter(), time.process_time()
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("Independent audit requires a new output directory")
    reports = [
        audit_run(root / name, trust_directory / f"{name}-trusted-code.json", source_trust, normalizer_sha256)
        for name in RUNS
    ]
    comparisons = {
        model: paired(
            next(r["results"] for r in reports if r["model"] == model and r["mode"] == "micro"),
            next(r["results"] for r in reports if r["model"] == model and r["mode"] == "verbose"),
        )
        for model in ("liquid/d1", "convaiinnovations/laya")
    }
    output.mkdir(parents=True)
    for report in reports:
        write_json(output / f"{report['run']}.json", report)
    summary = {
        "reports": [{k: v for k, v in r.items() if k != "results"} for r in reports],
        "comparisons": comparisons,
        "analyzer_sha256": sha(Path(__file__).read_bytes()),
        "normalizer_sha256": normalizer_sha256,
        "references_read": False,
        "new_calls": 0,
        "accuracy_measured": False,
        "ledger_accessed": False,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "One offline parent; process_time/perf_counter; getrusage lifetime peak includes imports; no sampling",
        },
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    """Audit only explicit retained DEV micro runs with separately supplied external code/source authorities."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "trust_directory", "source_trust", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--normalizer-sha256", required=True)
    args = parser.parse_args()
    result = audit(args.root, args.trust_directory, args.source_trust, args.normalizer_sha256, args.output)
    print(
        json.dumps(
            {
                "comparisons": {
                    k: {x: y for x, y in v.items() if x != "rows"} for k, v in result["comparisons"].items()
                },
                "resources": result["resources"],
            }
        )
    )


if __name__ == "__main__":
    main()
