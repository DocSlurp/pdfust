"""Freeze and execute bounded source-only local repair arms through root transport."""

# ruff: noqa: ANN401, C901, PLR0912, PLR2004, EM101, TRY003, PLC0415, TRY301, SLF001
from __future__ import annotations

import argparse
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import extension_batch as batch
from bench import extension_local as local
from bench import extension_protocol as protocol
from bench import extension_registry as registry
from bench import p003_extension_run as base
from bench import pipeline_repair as repair
from bench.pipeline_run import Resources
from bench.silver import canonical, guard_path, sha, write_json

ROOT = base.ROOT
CODE_FILES = tuple(
    dict.fromkeys(
        (
            *base.CODE_FILES,
            "extension_local_run.py",
            "extension_local.py",
            "extension_batch.py",
            "pipeline_run.py",
            "p003_gate_run.py",
            "p003_candidate_choice.py",
            "pipeline_vision_transcription.py",
            "pipeline_frontier.py",
            "pipeline_native_tables.py",
        )
    )
)
SCENARIOS = {"native", "missing_table_value", "swapped_cell_values", "wrapped_continuation_shift"}


def _config(config: dict[str, Any], ids: list[str]) -> dict[str, Any]:
    result = {
        "provider": "openrouter",
        "mechanism": "local",
        "variant": "arrays",
        "max_steps": 1,
        "scenario": "native",
        "edge": 0,
        "encoding": "rgb",
        **deepcopy(config),
    }
    name = result.get("run_id", "")
    if not name.startswith("extension-v1-") or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in name):
        raise ValueError("New extension namespace required")
    if (
        result["mechanism"] not in {"local", "batch", "singles"}
        or result["variant"] not in {"arrays", "readable"}
        or type(result["max_steps"]) is not int
        or result["max_steps"] not in (1, 3)
        or result["scenario"] not in SCENARIOS
    ):
        raise ValueError("Invalid local arm configuration")
    if not ids or len(ids) > 256 or len(set(ids)) != len(ids) or result.get("page_ids", ids) != ids:
        raise ValueError("Invalid intended page inventory")
    result["page_ids"] = list(ids)
    registry.model_spec(result["model"], result["provider"])
    return result


def _packet(page: dict[str, Any], current: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if config["mechanism"] == "local":
        frozen = local.prepare(
            page["source"],
            current,
            page["candidates"],
            max_alternatives=3,
            max_words=24,
            max_bytes=9000,
            context_rows=1,
            variant=config["variant"],
        )
        packet = local.build_request(frozen, config["model"], provider=config["provider"], image_url=page["image_url"])
    else:
        frozen = batch.prepare(
            page["source"],
            current,
            page["candidates"],
            max_questions=2,
            min_questions=2,
            max_alternatives=3,
            max_words=24,
            max_bytes=9000,
            context_rows=1,
            variant=config["variant"],
        )
        packet = batch.build_request(frozen, config["model"], provider=config["provider"], image_url=page["image_url"])
    if packet["body"] is not None and len(canonical(packet["body"])) > 750_000:
        raise ValueError("Actual wire exceeds shared transport admission")
    return packet


def prepare(corpus: Path, output: Path, config: dict[str, Any], ids: list[str]) -> dict[str, Any]:
    """Freeze source admission, initial packets and complete helper code without labels."""
    corpus, output = guard_path(corpus), guard_path(output)
    config = _config(config, ids)
    if output.exists():
        raise FileExistsError("Experiment directory must be new")
    manifest = base.read(corpus / "manifest.json")
    if manifest.get("split") != "DEV":
        raise ValueError("Explicit DEV corpus required")
    lookup = {p["id"]: p for p in manifest["pages"]}
    if not set(ids) <= set(lookup):
        raise ValueError("Page outside source manifest")
    inventory = base.read(corpus / "source-inventory.json")["artifacts"]
    output.mkdir(parents=True)
    for subdirectory in ("pages", "code", "steps"):
        (output / subdirectory).mkdir()
    rows = []
    with Resources() as resources:
        for ident in ids:
            record = lookup[ident]
            raw = guard_path(corpus / "menus" / f"{ident}.json").read_bytes()
            if sha(raw) != inventory[f"menus/{ident}.json"]:
                raise ValueError("Source menu changed since corpus freeze")
            menu = json.loads(raw)
            if sha(canonical(menu["source"])) != menu["source_sha256"]:
                raise ValueError("Source inventory digest differs")
            pdf = guard_path(Path(record["pdf_path"])).read_bytes()
            if sha(pdf) != record["pdf_sha256"]:
                raise ValueError("Source PDF changed since corpus freeze")
            current = protocol._state(menu["source"], menu["baseline"])
            page = {
                "id": ident,
                "source_parent_id": ident,
                "page_number": record["page_number"],
                "source": menu["source"],
                "candidates": [c["state"] for c in menu["candidates"]],
                "native_state": current,
                "baseline_state": current,
                "pdf_sha256": sha(pdf),
                "menu_sha256": sha(raw),
                "image_url": None,
            }
            try:
                if config["edge"] and record["page_number"] != 0:
                    raise ValueError("Full-page image helper is restricted to source page zero")
                if config["scenario"] != "native":
                    path = corpus / "stress" / f"{ident}.json"
                    if not path.exists():
                        page.update(preparation_status="not_applicable", stop_reason="missing_scenario")
                    else:
                        raw_stress = guard_path(path).read_bytes()
                        if sha(raw_stress) != inventory[f"stress/{ident}.json"]:
                            raise ValueError("Stress source changed since corpus freeze")
                        page["stress_sha256"] = sha(raw_stress)
                        matches = [
                            t for t in json.loads(raw_stress)["treatments"] if t["treatment"] == config["scenario"]
                        ]
                        if not matches:
                            page.update(preparation_status="not_applicable", stop_reason="missing_scenario")
                        elif len(matches) != 1:
                            raise ValueError("Scenario must identify one raw source state")
                        else:
                            # Treatment metadata and saved validity flags never enter packet functions.
                            page["baseline_state"] = protocol._state(page["source"], matches[0]["raw_baseline"])
                if page.get("preparation_status") != "not_applicable":
                    url, image = base.image_evidence(pdf, config["edge"], config["encoding"])
                    page.update(image_url=url, image=image)
                    packet = _packet(page, page["baseline_state"], config)
                    page.update(
                        packet=packet,
                        preparation_status="ready" if packet["body"] is not None else "not_applicable",
                        stop_reason=None if packet["body"] is not None else "no_focus",
                    )
            except (ValueError, TypeError, KeyError) as error:
                page.update(
                    preparation_status="preparation_error",
                    stop_reason="source_or_packet_admission",
                    error=type(error).__name__ + ": " + str(error),
                )
            path = output / "pages" / f"{ident}.json"
            write_json(path, page)
            rows.append(
                {"id": ident, "sha256": sha(path.read_bytes()), "preparation_status": page["preparation_status"]}
            )
    hashes = {}
    for name in CODE_FILES:
        raw = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(raw)
        hashes[name] = sha(raw)
    frozen = {
        "version": 1,
        "config": config,
        "corpus": str(corpus),
        "pages": rows,
        "code_sha256": hashes,
        "manifest_sha256": sha((corpus / "manifest.json").read_bytes()),
        "source_inventory_sha256": sha((corpus / "source-inventory.json").read_bytes()),
        "resources": resources.summary(),
        "prepared_at": time.time(),
        "references_read": False,
        "protocol_limits": {"alternatives": 3, "words": 24, "bytes": 9000, "batch_questions": 2},
    }
    write_json(output / "frozen.json", frozen)
    return frozen


def _admit(output: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    frozen = base.read(output / "frozen.json")
    if set(frozen["code_sha256"]) != set(CODE_FILES):
        raise ValueError("Incomplete runtime inventory")
    for name, digest in frozen["code_sha256"].items():
        if (
            sha(Path(__file__).with_name(name).read_bytes()) != digest
            or sha((output / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Runtime changed after freeze")
    pages = []
    for row in frozen["pages"]:
        path = output / "pages" / f"{row['id']}.json"
        if sha(path.read_bytes()) != row["sha256"]:
            raise ValueError("Frozen page packet changed")
        pages.append(base.read(path))
    return frozen, pages


def _client(config: dict[str, Any]) -> Any:
    if config["provider"] == "openrouter":
        from bench.p003_client import P003ConcurrentClient

        return P003ConcurrentClient(ROOT)
    from bench.decision_gateway import GatewayDecisionClient
    from bench.decision_gateway_vision import GatewayVisionDecisionClient

    constructor = GatewayVisionDecisionClient if config["model"] == "liquid/d1" else GatewayDecisionClient
    return constructor(ROOT)


def run(output: Path, *, client: Any = None) -> dict[str, Any]:
    """Execute exact frozen steps with shared admission, no fallback and no retry."""
    output = guard_path(output)
    frozen, pages = _admit(output)
    config = frozen["config"]
    with (output / "started.json").open("x") as handle:
        json.dump({"started_at": time.time(), "replay": False}, handle)
    prefix = "P003/" + config["run_id"] + "/"
    results, stopped, transmissions = [], False, 0
    with Resources() as resources:
        for page in pages:
            ident = page["id"]
            current = deepcopy(page["baseline_state"])
            result = {
                "id": ident,
                "source_parent_id": page["source_parent_id"],
                "baseline_state": deepcopy(current),
                "native_state": page["native_state"],
                "final_state": current,
                "model_selected_state": None,
                "steps": [],
                "model_success": False,
            }
            if page["preparation_status"] != "ready":
                result.update(status=page["preparation_status"], stop_reason=page["stop_reason"])
                if "error" in page:
                    result["error"] = page["error"]
            elif stopped:
                result.update(status="not_attempted", stop_reason="arm_stopped_after_failure")
            else:
                seen = {protocol.digest(current)}
                for index in range(config["max_steps"]):
                    step = {"index": index, "before_state_sha256": protocol.digest(current), "receipts": []}
                    result["steps"].append(step)
                    failure_stage = "packet_preparation"
                    try:
                        packet = page["packet"] if index == 0 else _packet(page, current, config)
                        if packet["body"] is None:
                            result.update(
                                status="selected" if result["model_success"] else "not_applicable",
                                stop_reason="no_focus",
                            )
                            step["status"] = "not_applicable"
                            break
                        packets = batch.split_requests(packet) if config["mechanism"] == "singles" else [packet]
                        path = output / "steps" / f"{ident}-step-{index}-frozen.json"
                        write_json(path, {"packet": packet, "transmitted_packets": packets, "before_state": current})
                        step.update(
                            frozen_sha256=sha(path.read_bytes()),
                            frozen_path=str(path),
                            question_count=len(packet.get("question_ids", ["q0"])),
                        )
                        parsed, single_choices = None, {}
                        for question_index, transmitted in enumerate(packets):
                            if client is None:
                                client = _client(config)
                            failure_stage = "transport"
                            started = time.perf_counter()
                            try:
                                receipt = client.request(
                                    transmitted["body"],
                                    tag=f"{prefix}{ident}/step-{index}/q-{question_index}",
                                    replay=False,
                                    max_body_bytes=750_000,
                                )
                            except Exception:
                                step["failed_client_wall_seconds"] = time.perf_counter() - started
                                raise
                            client_wall = time.perf_counter() - started
                            transmissions += 1
                            receipt_path = output / "steps" / f"{ident}-step-{index}-q-{question_index}-receipt.json"
                            write_json(receipt_path, receipt)
                            step["receipts"].append(
                                {
                                    "entry": receipt["entry"],
                                    "usage": receipt["result"].get("usage", {}),
                                    "client_wall_seconds": client_wall,
                                    "receipt_sha256": sha(receipt_path.read_bytes()),
                                    "receipt_path": str(receipt_path),
                                }
                            )
                            failure_stage = "answer_validation"
                            if config["mechanism"] == "local":
                                parsed = local.parse_choice(receipt["result"], transmitted)
                            else:
                                parsed = batch.parse_choice(receipt["result"], transmitted)
                                single_choices.update({q: answer["choice"] for q, answer in parsed["answers"].items()})
                        if config["mechanism"] == "singles":
                            selected = batch.compose(packet["frozen"], single_choices)
                            unchanged = all(choice == "keep" for choice in single_choices.values())
                        else:
                            selected = parsed["selected_state"]
                            unchanged = (
                                parsed["unchanged"] if config["mechanism"] == "local" else parsed["all_unchanged"]
                            )
                        repair.validate(page["source"], selected)
                        hashed = protocol.digest(selected)
                        step.update(
                            status="accepted",
                            after_state_sha256=hashed,
                            selected_state=deepcopy(selected),
                            unchanged=unchanged,
                            answers=single_choices if config["mechanism"] != "local" else parsed["choice"],
                        )
                        current = selected
                        result.update(
                            final_state=current,
                            model_selected_state=current,
                            model_success=True,
                            status="unchanged" if unchanged else "selected",
                        )
                        if unchanged or hashed in seen:
                            result["stop_reason"] = "keep" if unchanged else "repeated_state"
                            break
                        seen.add(hashed)
                        result["stop_reason"] = "step_cap"
                    except Exception as error:
                        stopped = True
                        step.update(
                            status="failed", failure_stage=failure_stage, error=type(error).__name__ + ": " + str(error)
                        )
                        result.update(
                            status="failed",
                            stop_reason="arm_stopped_after_failure",
                            model_success=False,
                            error=step["error"],
                        )
                        break
            results.append(result)
            write_json(
                output / "progress.json",
                {
                    "config": config,
                    "results": results,
                    "completed": len(results),
                    "intended": len(pages),
                    "observed_at": time.time(),
                },
            )
    from bench.p003_gate_run import charges

    entries = (
        [e for e in base.read(client.ledger)["requests"] if e.get("tag", "").startswith(prefix)]
        if client is not None
        else []
    )
    accounting = charges(entries)
    measured = resources.summary()
    accepted = sum(r["model_success"] for r in results)
    accepted_questions = sum(
        s.get("question_count", 0) for r in results for s in r["steps"] if s["status"] == "accepted"
    )
    report = {
        "version": 1,
        "config": config,
        "results": results,
        "intended_pages": len(pages),
        "selected_pages": accepted,
        "accepted_questions": accepted_questions,
        "successful_transmissions": transmissions,
        "resources": measured,
        "preparation_resources": frozen["resources"],
        "costs": accounting,
        "frozen_sha256": sha((output / "frozen.json").read_bytes()),
        "completed_at": time.time(),
        "rates": {
            "intended_pages_per_minute": len(pages) * 60 / measured["wall_seconds"],
            "selected_pages_per_minute": accepted * 60 / measured["wall_seconds"],
            "intended_pages_per_dollar": len(pages) / accounting["effective_usd"]
            if accounting["effective_usd"]
            else None,
            "accepted_questions_per_minute": accepted_questions * 60 / measured["wall_seconds"],
            "accepted_questions_per_dollar": accepted_questions / accounting["effective_usd"]
            if accounting["effective_usd"]
            else None,
            "scope": "Whole arm, preparation separate; accepted selection is not scored correctness",
        },
    }
    report["costs"]["cost_scope"] = "Fresh root-owned local arm requests only; local CPU and remote hardware unpriced"
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Require an explicit hosted flag; preparation never makes provider requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    if args.action == "prepare":
        if not args.corpus or not args.config or not args.ids:
            parser.error("Preparation requires corpus, config and IDs")
        result = prepare(args.corpus, args.directory, base.read(args.config), args.ids)
        print(json.dumps({"directory": str(args.directory), "pages": len(result["pages"])}))
    else:
        if not args.run_hosted:
            parser.error("Transmission requires --run-hosted")
        result = run(args.directory)
        print(
            json.dumps(
                {"directory": str(args.directory), "intended": result["intended_pages"], "costs": result["costs"]}
            )
        )


if __name__ == "__main__":
    main()
