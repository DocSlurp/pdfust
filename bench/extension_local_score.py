"""Authenticate and replay local repair receipts before pinned offline evaluation."""

# ruff: noqa: ANN401, C901, PLR0912, EM101, TRY003, SLF001
from __future__ import annotations

import argparse
import json
import resource
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import extension_batch as batch
from bench import extension_local as local
from bench import extension_local_run as runner
from bench import extension_protocol as protocol
from bench import p003_extension_score as scoring
from bench.pipeline_repair import validate
from bench.silver import canonical, guard_path, sha, write_json

MAX_CORPUS_CACHE = 2
MAX_METRIC_CACHE = 512
_CORPUS_CACHE: dict[Path, dict[str, Any]] = {}
_METRIC_CACHE: dict[str, dict[str, Any]] = {}


def _load_corpus(path: Path) -> dict[str, Any]:
    """Reuse admitted snapshots only after rechecking every frozen source byte."""
    path = path.resolve()
    if path not in _CORPUS_CACHE:
        admitted = scoring.load_frozen(path)
        if admitted["receipts"]["pins"] == scoring.PINS:
            if len(_CORPUS_CACHE) >= MAX_CORPUS_CACHE:
                _CORPUS_CACHE.clear()
            _CORPUS_CACHE[path] = admitted
        return admitted
    admitted = _CORPUS_CACHE[path]
    for name in ("manifest.json", "frozen.json", "source-inventory.json"):
        _read(path / name, scoring.PINS[name])
    for name, digest in admitted["receipts"]["source_artifacts"].items():
        if sha(guard_path(path / name).read_bytes()) != digest:
            raise ValueError("Cached corpus source artifact changed: " + name)
    _read(path / "private-targets.json", scoring.PINS["private-targets.json"])
    return admitted


def _same(left: Any, right: Any, message: str) -> None:
    if canonical(left) != canonical(right):
        raise ValueError(message)


def _read(path: Path, digest: str | None = None) -> dict[str, Any]:
    raw = guard_path(path).read_bytes()
    if digest is not None and sha(raw) != digest:
        raise ValueError("Authenticated artifact changed: " + path.name)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise TypeError("Artifact must be an object")
    return value


def _source_run(directory: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    frozen = _read(directory / "frozen.json")
    report = _read(directory / "report.json")
    if report["frozen_sha256"] != sha((directory / "frozen.json").read_bytes()):
        raise ValueError("Run freeze differs from report receipt")
    _same(report["config"], frozen["config"], "Report config differs from freeze")
    ids = frozen["config"]["page_ids"]
    if not ids or len(set(ids)) != len(ids) or [p["id"] for p in frozen["pages"]] != ids:
        raise ValueError("Complete unique frozen intended inventory required")
    runner._config(frozen["config"], ids)
    if set(frozen["code_sha256"]) != set(runner.CODE_FILES):
        raise ValueError("Incomplete archived helper inventory")
    for name, digest in frozen["code_sha256"].items():
        if sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived helper changed")
    # Only reviewed, imported code runs. Historical transport helpers stay data.
    for name in (
        "extension_local_run.py",
        "extension_local.py",
        "extension_batch.py",
        "extension_protocol.py",
        "extension_registry.py",
        "pipeline_repair.py",
        "decision_oplog_run.py",
        "p003_gateway_answer.py",
        "p003_transport.py",
    ):
        if sha(Path(runner.__file__).with_name(name).read_bytes()) != frozen["code_sha256"][name]:
            raise ValueError("Pure replay helper differs from reviewed freeze: " + name)
    pages = {p["id"]: _read(directory / "pages" / f"{p['id']}.json", p["sha256"]) for p in frozen["pages"]}
    result_ids = [row["id"] for row in report["results"]]
    if len(set(result_ids)) != len(result_ids) or not set(result_ids) <= set(ids):
        raise ValueError("Duplicate or outside-intended report rows")
    if report.get("intended_pages") != len(ids):
        raise ValueError("Report intended denominator changed")
    return frozen, pages, report


def _initial(corpus: dict[str, Any], frozen: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    ident = page["id"]
    menu = corpus["menus"][ident]
    record = next(p for p in corpus["manifest"]["pages"] if p["id"] == ident)
    if page["pdf_sha256"] != record["pdf_sha256"] or page["page_number"] != record["page_number"]:
        raise ValueError("Run PDF source receipt differs from pinned manifest")
    artifacts = corpus["receipts"]["source_artifacts"]
    if page["menu_sha256"] != artifacts[f"menus/{ident}.json"]:
        raise ValueError("Run menu receipt differs from pinned source")
    if "stress_sha256" in page and page["stress_sha256"] != artifacts[f"stress/{ident}.json"]:
        raise ValueError("Run stress receipt differs from pinned source")
    _same(page["source"], menu["source"], "Run source differs from pinned menu")
    _same(page["candidates"], [c["state"] for c in menu["candidates"]], "Run candidate hypotheses changed")
    native = protocol._state(menu["source"], menu["baseline"])
    _same(page["native_state"], native, "Native source state changed")
    if page["source_parent_id"] != ident:
        raise ValueError("Source parent identity changed")
    if (
        frozen["manifest_sha256"] != corpus["receipts"]["pins"]["manifest.json"]
        or frozen["source_inventory_sha256"] != corpus["receipts"]["pins"]["source-inventory.json"]
    ):
        raise ValueError("Run corpus receipts differ from evaluation pins")
    scenario = frozen["config"]["scenario"]
    expected = native
    if scenario != "native":
        matches = [t for t in corpus["stress"][ident]["treatments"] if t["treatment"] == scenario]
        if matches:
            if len(matches) != 1:
                raise ValueError("Scenario source inventory ambiguous")
            expected = protocol._state(menu["source"], matches[0]["raw_baseline"])
        elif page.get("stop_reason") != "missing_scenario":
            raise ValueError("Missing scenario was not preserved as inapplicable")
    _same(page["baseline_state"], expected, "Starting state differs from pinned source scenario")
    validate(menu["source"], expected)
    return expected


def _replay(
    directory: Path, page: dict[str, Any], config: dict[str, Any], row: dict[str, Any], referenced: set[Path]
) -> dict[str, Any]:
    current = deepcopy(page["baseline_state"])
    _same(row["baseline_state"], current, "Reported baseline changed")
    _same(row["native_state"], page["native_state"], "Reported native baseline changed")
    if row.get("source_parent_id") != page["source_parent_id"]:
        raise ValueError("Reported source parent changed")
    steps = row["steps"]
    if len(steps) > config["max_steps"] or [s["index"] for s in steps] != list(range(len(steps))):
        raise ValueError("Step inventory exceeds frozen controller")
    seen, accepted, terminal, failed = {protocol.digest(current)}, 0, None, False
    for index, step in enumerate(steps):
        if terminal is not None or failed:
            raise ValueError("Requests continued after controller stop")
        if step["before_state_sha256"] != protocol.digest(current):
            raise ValueError("Step starting state differs from replay")
        try:
            expected = page["packet"] if index == 0 else runner._packet(page, current, config)
        except (ValueError, TypeError, KeyError):
            if step["status"] != "failed" or step.get("failure_stage") != "packet_preparation" or step["receipts"]:
                raise ValueError("Packet refusal was not preserved") from None
            failed = True
            break
        if expected["body"] is None:
            if step["status"] != "not_applicable" or step["receipts"]:
                raise ValueError("No-focus step claimed a transmission")
            terminal = "no_focus"
            continue
        rebuilt = runner._packet(page, current, config)
        _same(expected, rebuilt, "Initial packet differs from pure source preparation")
        packets = batch.split_requests(expected) if config["mechanism"] == "singles" else [expected]
        path = directory / "steps" / f"{page['id']}-step-{index}-frozen.json"
        saved = _read(path, step["frozen_sha256"])
        _same(
            saved,
            {"packet": expected, "transmitted_packets": packets, "before_state": current},
            "Frozen step packet differs from replay",
        )
        if Path(step["frozen_path"]).resolve() != path.resolve():
            raise ValueError("Step receipt path escapes expected artifact")
        receipts = step["receipts"]
        if len(receipts) > len(packets):
            raise ValueError("Too many transmissions for frozen step")
        choices, parsed, invalid = {}, None, False
        for question_index, item in enumerate(receipts):
            receipt_path = directory / "steps" / f"{page['id']}-step-{index}-q-{question_index}-receipt.json"
            if Path(item["receipt_path"]).resolve() != receipt_path.resolve():
                raise ValueError("Transmission receipt path changed")
            receipt = _read(receipt_path, item["receipt_sha256"])
            referenced.add(receipt_path.resolve())
            _same(item["entry"], receipt["entry"], "Ledger entry differs from persisted receipt")
            _same(item["usage"], receipt["result"].get("usage", {}), "Usage differs from persisted receipt")
            body = packets[question_index]["body"]
            encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
            entry = receipt["entry"]
            if entry.get("request_sha256") != sha(encoded):
                raise ValueError("Provider receipt does not attest exact transmitted wire bytes")
            tag = f"P003/{config['run_id']}/{page['id']}/step-{index}/q-{question_index}"
            if (
                entry.get("tag") != tag
                or entry.get("requested_model", body["model"]) != body["model"]
                or receipt.get("replayed", False)
            ):
                raise ValueError("Receipt tag/model/replay differs from frozen request")
            try:
                if config["mechanism"] == "local":
                    parsed = local.parse_choice(receipt["result"], packets[question_index])
                else:
                    parsed = batch.parse_choice(receipt["result"], packets[question_index])
                    choices.update({name: answer["choice"] for name, answer in parsed["answers"].items()})
            except (ValueError, TypeError, KeyError):
                invalid = True
                if question_index != len(receipts) - 1:
                    raise ValueError("Requests continued after invalid native response") from None
        if step["status"] == "failed":
            stage = step.get("failure_stage")
            if (stage == "answer_validation" and not invalid) or (
                stage == "transport" and len(receipts) >= len(packets)
            ):
                raise ValueError("Reported failed step differs from replayed evidence")
            if stage not in {"transport", "answer_validation", "packet_preparation"}:
                raise ValueError("Unknown failed-step stage")
            failed = True
            continue
        if invalid or len(receipts) != len(packets) or step["status"] != "accepted":
            raise ValueError("Accepted step lacks complete valid answers")
        if config["mechanism"] == "singles":
            selected = batch.compose(expected["frozen"], choices)
            unchanged = all(choice == "keep" for choice in choices.values())
        else:
            selected = parsed["selected_state"]
            unchanged = parsed["unchanged"] if config["mechanism"] == "local" else parsed["all_unchanged"]
        validate(page["source"], selected)
        hashed = protocol.digest(selected)
        if step["after_state_sha256"] != hashed or step["unchanged"] != unchanged:
            raise ValueError("Reported accepted state differs from native replay")
        _same(step["selected_state"], selected, "Step selected state differs from replay")
        _same(
            step["answers"],
            parsed["choice"] if config["mechanism"] == "local" else choices,
            "Recorded choices differ from replay",
        )
        current, accepted = selected, accepted + 1
        if unchanged or hashed in seen:
            terminal = "keep" if unchanged else "repeated_state"
        seen.add(hashed)
    _same(row["final_state"], current, "Reported final state differs from validated replay")
    if failed:
        if row["status"] != "failed" or row["model_success"] or row["stop_reason"] != "arm_stopped_after_failure":
            raise ValueError("Failed continuation was credited as successful")
        _same(
            row["model_selected_state"],
            current if accepted else None,
            "Failed continuation selected annotation changed",
        )
        selected = None
    elif accepted:
        if terminal is None and len(steps) != config["max_steps"]:
            raise ValueError("Controller stopped before its frozen step cap")
        terminal = terminal or "step_cap"
        if row["status"] not in {"selected", "unchanged"} or not row["model_success"] or row["stop_reason"] != terminal:
            raise ValueError("Successful controller outcome differs from replay")
        _same(row["model_selected_state"], current, "Terminal selected state differs from replay")
        selected = current
    else:
        if (
            row["model_success"]
            or row["model_selected_state"] is not None
            or row["status"] not in {"not_applicable", "preparation_error", "not_attempted"}
        ):
            raise ValueError("Unattempted baseline credited as selection")
        if not steps and row["status"] != "not_attempted" and row["status"] != page["preparation_status"]:
            raise ValueError("Untouched outcome differs from preparation status")
        if steps and terminal != "no_focus":
            raise ValueError("Empty outcome has unexpected step inventory")
        selected = None
    return {
        "status": row["status"],
        "stop_reason": row["stop_reason"],
        "selected": selected,
        "partial": current,
        "accepted_steps": accepted,
        "failed_continuation": failed and accepted > 0,
    }


def score_run(corpus: Path, directory: Path) -> dict[str, Any]:
    """Replay owned states and score all intended pages using pinned references only offline."""
    started, cpu = time.perf_counter(), time.process_time()
    directory = guard_path(directory)
    run_frozen, pages, report = _source_run(directory)
    admitted = _load_corpus(guard_path(corpus))
    ids = run_frozen["config"]["page_ids"]
    if not set(ids) <= set(admitted["menus"]):
        raise ValueError("Intended page lies outside pinned source corpus")
    references = {t["id"]: t for t in admitted["targets"]}
    targets = [references[ident] for ident in ids]
    observed = {r["id"]: r for r in report["results"]}
    predictions = {
        name: [] for name in ("baseline", "native", "terminal_selected", "last_validated_partial", "composed")
    }
    outcomes, referenced = [], set()
    stopped = False
    for ident in ids:
        page = pages[ident]
        initial = _initial(admitted, run_frozen, page)
        row = observed.get(ident)
        if row is None:
            replay = {
                "status": "missing_result",
                "stop_reason": "missing_result",
                "selected": None,
                "partial": initial,
                "accepted_steps": 0,
                "failed_continuation": False,
            }
        else:
            if not stopped and row["status"] == "not_attempted":
                raise ValueError("Arm skipped a ready page before any failure")
            if stopped and row["steps"]:
                raise ValueError("Arm continued after a previous page failure")
            replay = _replay(directory, page, run_frozen["config"], row, referenced)
            if replay["status"] == "failed":
                stopped = True
        selected = replay["selected"]
        predictions["baseline"].append(scoring.prediction(ident, initial))
        predictions["native"].append(scoring.prediction(ident, page["native_state"]))
        predictions["terminal_selected"].append(
            scoring.prediction(ident, selected, status="ok" if selected is not None else replay["status"])
        )
        predictions["last_validated_partial"].append(scoring.prediction(ident, replay["partial"]))
        predictions["composed"].append(scoring.prediction(ident, selected if selected is not None else initial))
        outcomes.append(
            {
                "id": ident,
                "source_parent_id": ident,
                "status": replay["status"],
                "stop_reason": replay["stop_reason"],
                "accepted_steps": replay["accepted_steps"],
                "failed_continuation": replay["failed_continuation"],
                "model_credit": selected is not None,
                "baseline_retained_in_composed": selected is None,
                "baseline_sha256": protocol.digest(initial),
                "last_validated_sha256": protocol.digest(replay["partial"]),
                "selected_sha256": protocol.digest(selected) if selected is not None else None,
            }
        )
    saved_receipts = {p.resolve() for p in (directory / "steps").glob("*-receipt.json")}
    if saved_receipts != referenced:
        raise ValueError("Unreported or missing transmission receipt inventory")
    cache_counts = Counter()

    def metrics(predicted: list[dict[str, Any]], refs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        refs = targets if refs is None else refs
        key = protocol.digest({"targets": refs, "predictions": predicted})
        if key not in _METRIC_CACHE:
            cache_counts["misses"] += 1
            if len(_METRIC_CACHE) >= MAX_METRIC_CACHE:
                _METRIC_CACHE.clear()
            _METRIC_CACHE[key] = scoring.score_predictions(refs, predicted)
        else:
            cache_counts["hits"] += 1
        return deepcopy(_METRIC_CACHE[key])

    scored = {name: metrics(predicted) for name, predicted in predictions.items()}
    changes = {name: Counter() for name in ("strict", "v2", "wrap")}
    for index, outcome in enumerate(outcomes):
        before = metrics([predictions["baseline"][index]], [targets[index]])
        after = metrics([predictions["composed"][index]], [targets[index]])
        outcome["changes"] = {}
        for name, counts in changes.items():
            left, right = scoring._rank(before, name), scoring._rank(after, name)
            label = "improved" if right > left else "regressed" if right < left else "unchanged"
            counts[label] += 1
            counts["selected_" + label] += outcome["model_credit"]
            outcome["changes"][name] = label
    return {
        "version": 1,
        "config": deepcopy(run_frozen["config"]),
        "intended_pages": len(ids),
        "status_counts": dict(Counter(o["status"] for o in outcomes)),
        "scoring_cache": {
            **dict(cache_counts),
            "limit": MAX_METRIC_CACHE,
            "corpus_reuse_rechecks_all_source_bytes": True,
        },
        "pages": outcomes,
        "baseline_raw_scenario": scored["baseline"],
        "native_baseline": scored["native"],
        "terminal_model_selected_only": scored["terminal_selected"],
        "last_validated_partial_diagnostic": scored["last_validated_partial"],
        "composed_with_baseline_retention": scored["composed"],
        "comparisons_by_metric": {k: dict(v) for k, v in changes.items()},
        "receipts": {
            "corpus": admitted["receipts"],
            "run_frozen_sha256": report["frozen_sha256"],
            "report_sha256": sha((directory / "report.json").read_bytes()),
            "authenticated_transmission_receipts": len(referenced),
            "archived_code_executed": False,
        },
        "costs": deepcopy(report["costs"]),
        "run_resources": deepcopy(report["resources"]),
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": (
                "Single parent CPU scoring; unsampled lifetime getrusage including imports; no inference/GPU"
            ),
        },
        "scope": (
            "All intended pages; terminal successful selections only receive model credit. "
            "Failed continuation partial states are diagnostics. Source completeness does not establish correctness. "
            "Strict/v2/wrap remain distinct."
        ),
    }


def main() -> None:
    """Write a fresh offline scoring report without changing frozen run artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = guard_path(args.output)
    if output.exists():
        raise FileExistsError("Fresh scoring output required")
    result = score_run(args.corpus, args.directory)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    print(json.dumps({"intended_pages": result["intended_pages"], "status_counts": result["status_counts"]}))


if __name__ == "__main__":
    main()
