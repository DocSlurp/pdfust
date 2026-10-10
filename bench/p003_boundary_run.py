"""Opt-in P003 boundary repair of retained DEV region states, without re-extraction.

Only root invokes hosted inference through its persistent DecisionClient ledger.
Baseline pipeline quality, calls, latency and costs remain historical provenance.
"""

# Explicit retained heterogeneous schemas, isolated benchmark transport and errors.
# ruff: noqa: ANN401, EM101, TRY003, PLC0415, TRY301, C901, PLR0912, PLR0913, PLR0917, PLR2004
from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import Counter
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench import pipeline_run as pipeline
from bench.decision_hosted import DECISION_MODELS, DecisionClient, accounted_cost
from bench.decision_p003_native import apply_decision_batches, decision_batches
from bench.generalization_run import _table_bounds, region_image
from bench.pipeline_regions import compose
from bench.pipeline_source_order import render_source
from bench.silver import guard_path, sha, write_json

if TYPE_CHECKING:
    from collections.abc import Callable

WAVE_LIMIT = 50.0
RESERVATION = 0.30
CODE_FILES = (
    "p003_boundary_run.py",
    "decision_p003_boundaries.py",
    "decision_p003_native.py",
    "decision_hosted.py",
    "pipeline_assembly.py",
    "pipeline_frontier.py",
    "pipeline_run.py",
    "generalization_run.py",
    "pipeline_regions.py",
    "pipeline_source_order.py",
    "pipeline_repair.py",
)


def _identifier(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", value) or value in {".", ".."}:
        raise ValueError("Retained page and region IDs must be filename-safe")
    return value


def _error(error: Exception, stage: str) -> dict[str, Any]:
    # Shared client sanitizes transport/credential errors; do not copy arbitrary exception strings.
    detail = str(error)[:500] if isinstance(error, (ValueError, KeyError)) else None
    return {"stage": stage, "error_type": type(error).__name__, "detail": detail}


def _entries(client: Any, prefix: str) -> list[dict[str, Any]]:
    if client is None or not client.ledger.exists():
        return []
    ledger = json.loads(guard_path(client.ledger).read_bytes())
    return [deepcopy(entry) for entry in ledger["requests"] if entry.get("tag", "").startswith(prefix)]


def _reserve_wave(client: Any) -> None:
    spent = sum(accounted_cost(entry["accounted_usd"]) for entry in _entries(client, "P003/"))
    if spent + RESERVATION > WAVE_LIMIT:
        raise RuntimeError("P003 repair reservation would exceed the USD 50 wave ceiling")


def _charges(entries: list[dict[str, Any]]) -> dict[str, Any]:
    resolved = [e for e in entries if e.get("cost_status") != "reserved"]
    reservations = [e for e in entries if e.get("cost_status") == "reserved"]
    complete = len(resolved) == len(entries)
    reported = [e["provider_reported_usd"] for e in entries if "provider_reported_usd" in e]
    return {
        "ledger_attempts": len(entries),
        "accounted_usd": sum(accounted_cost(e["accounted_usd"]) for e in entries),
        "effective_usd": sum(accounted_cost(e["accounted_usd"]) for e in resolved) if complete else None,
        "known_partial_effective_usd": sum(accounted_cost(e["accounted_usd"]) for e in resolved),
        "unresolved_reserved_usd": sum(accounted_cost(e["accounted_usd"]) for e in reservations),
        "provider_reported_usd": sum(reported) if len(reported) == len(entries) else None,
        "known_partial_provider_reported_usd": sum(reported),
        "missing_provider_charge_count": len(entries) - len(reported),
        "cost_bases": dict(Counter(e.get("cost_status", "unknown") for e in entries)),
        "entries": entries,
        "cost_scope": "Incremental boundary-repair API attempts only; baseline API costs retained separately. "
        "Unresolved reservations are separate from reported charges and effective estimates.",
    }


def process_retained(
    record: dict[str, Any],
    original: dict[str, Any],
    baseline_directory: Path,
    output: Path,
    config: dict[str, Any],
    client: Any,
    *,
    image_factory: Callable[..., tuple[str | None, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Repair all region states atomically; any failure retains complete baseline output."""
    started, cpu = time.perf_counter(), time.process_time()
    identifier = _identifier(record["id"])
    result = deepcopy(original)
    result.update(repair_status="not_applicable", repair_calls=[], repair_errors=[], repair_regions=[])
    result["baseline_provenance"] = {
        "directory": str(baseline_directory),
        "result_sha256": sha((baseline_directory / f"{identifier}-result.json").read_bytes()),
        "status": original["status"],
        "wall_seconds": original.get("wall_seconds"),
        "cpu_seconds": original.get("cpu_seconds"),
        "calls": deepcopy(original.get("calls", [])),
        "source_order": config["baseline_source_order"],
    }
    for suffix in ("-structure.json", ".md"):
        prior = baseline_directory / f"{identifier}{suffix}"
        if prior.exists():
            (output / prior.name).write_bytes(prior.read_bytes())
    prefix = f"P003/{config['run_id']}/{identifier}/"
    stage, attempted = "baseline_validation", False
    try:
        if original["status"] != "ok":
            result["repair_status"] = "baseline_failed_skipped"
            return result
        snapshot = original["source"]
        plan = {**deepcopy(original["region_plan"]), "words": deepcopy(snapshot["words"])}
        original_states = {info["id"]: deepcopy(info["state"]) for info in original["regions"]}
        composed = compose(plan, original_states)
        _table_bounds(snapshot, composed)
        retained_structure = json.loads((baseline_directory / f"{identifier}-structure.json").read_bytes())
        if composed != retained_structure:
            raise ValueError("Retained baseline region states disagree with complete structure")
        updated_states, repaired_count = deepcopy(original_states), 0
        with ExitStack() as stack:
            page = None
            for region in plan["regions"]:
                region_id = _identifier(region["id"])
                stage = f"region/{region_id}/evidence"
                source, state = region["source"], original_states[region_id]
                menu, _ = decision_batches(source, state, config["model"], max_questions=config["max_questions"])
                local_info = {"id": region_id, "repair_status": "not_applicable", "original_state": deepcopy(state)}
                result["repair_regions"].append(local_info)
                if not menu["boundaries"]:
                    continue
                attempted = True
                url, image_metadata = None, {"image": "none"}
                if config["image_edge"]:
                    stage = f"region/{region_id}/image"
                    if image_factory:
                        url, image_metadata = image_factory(record, original, region, config["image_edge"])
                    else:
                        if page is None:
                            import pylopdf

                            data = guard_path(Path(record["pdf_path"])).read_bytes()
                            if sha(data) != record["pdf_sha256"]:
                                raise ValueError("Frozen source PDF hash changed")
                            document = stack.enter_context(pylopdf.open(stream=data))
                            page = document[record["page_number"]]
                            effective = original.get(
                                "effective_rotation", original.get("original_rotation", page.rotation)
                            )
                            if page.rotation != effective:
                                page.set_rotation(effective)
                            if list(page.rect) != snapshot["page_size"]:
                                raise ValueError("Retained display viewport differs from repair raster")
                        url, image_metadata = region_image(page, region["bbox"], config["image_edge"])
                local_info["image"] = image_metadata
                menu, bodies = decision_batches(
                    source,
                    state,
                    config["model"],
                    url,
                    max_questions=config["max_questions"],
                    image_viewport=region["bbox"] if url else None,
                )
                write_json(output / f"{identifier}-{region_id}-boundary-menu.json", menu)
                responses = []
                for batch_index, body in enumerate(bodies):
                    stage = f"region/{region_id}/batch/{batch_index}"
                    stem = f"{identifier}-{region_id}-boundary-{batch_index}"
                    write_json(output / f"{stem}-request.json", body)
                    if client is None:
                        raise ValueError("Opt-in hosted repair requires root's coordinated metered client")
                    _reserve_wave(client)
                    began, began_cpu = time.perf_counter(), time.process_time()
                    response = client.request(
                        body,
                        tag=f"{prefix}{region_id}/{batch_index}",
                        max_body_bytes=750_000,
                        replay=False,
                        reservation_usd=RESERVATION,
                    )
                    write_json(output / f"{stem}-response.json", response)
                    if response.get("replayed"):
                        raise ValueError("Fresh boundary repair cannot count a replayed provider response")
                    responses.append(response["result"])
                    result["repair_calls"].append(
                        {
                            "entry": response["entry"],
                            "usage": response["result"].get("usage", {}),
                            "replayed": False,
                            "kind": "p003_boundary_choice",
                            "region_id": region_id,
                            "batch_index": batch_index,
                            "client_wall_seconds": time.perf_counter() - began,
                            "client_cpu_seconds": time.process_time() - began_cpu,
                        }
                    )
                stage = f"region/{region_id}/decode"
                updated, audit = apply_decision_batches(
                    source,
                    state,
                    menu,
                    bodies,
                    responses,
                    minimum_join=config["minimum_join"],
                    minimum_margin=config["minimum_margin"],
                )
                local_info.update(repair_status="staged", updated_state=updated, audit=audit)
                updated_states[region_id] = updated
                repaired_count += 1
                write_json(output / f"{identifier}-{region_id}-updated-state.json", updated)
        stage = "atomic_page_composition"
        state = compose(plan, updated_states)
        _table_bounds(snapshot, state)
        order = {word["id"]: index for index, word in enumerate(snapshot["words"])}
        rendered = []
        for region in plan["regions"]:
            render_snapshot = (
                render_source(snapshot, region) if config["baseline_source_order"] == "original" else region["source"]
            )
            rendered.append(
                (
                    min((order[i] for i in region["source_ids"]), default=len(order)),
                    pipeline.markdown(render_snapshot, updated_states[region["id"]]),
                )
            )
        # No output mutation occurs until all regions, composition and rendering pass.
        if repaired_count:
            for info in result["repair_regions"]:
                if info["repair_status"] == "staged":
                    info["repair_status"] = "completed"
            result.update(
                tables=state["tables"],
                unresolved_ids=state["unresolved_ids"],
                source_conserved=True,
                repair_status="completed",
                status="ok",
            )
            result["regions"] = [
                {**deepcopy(info), "state": updated_states[info["id"]]} for info in original["regions"]
            ]
            (output / f"{identifier}.md").write_text("\n".join(text for _, text in sorted(rendered)))
            write_json(output / f"{identifier}-structure.json", state)
    except Exception as error:
        for suffix in ("-structure.json", ".md"):
            prior = baseline_directory / f"{identifier}{suffix}"
            if prior.exists():
                (output / prior.name).write_bytes(prior.read_bytes())
        for info in result["repair_regions"]:
            if info["repair_status"] in {"staged", "completed"}:
                info["repair_status"] = "discarded_atomic_failure"
        result["repair_status"] = "failed_retained_baseline"
        result["repair_errors"].append(_error(error, stage))
        # Always keep original page tables/regions/status and copied complete output.
        result.update(
            tables=deepcopy(original.get("tables", [])),
            regions=deepcopy(original.get("regions", [])),
            status=original["status"],
        )
        result["unresolved_ids"] = deepcopy(original.get("unresolved_ids", []))
        write_json(
            output / f"{identifier}-repair-error.json", {"errors": result["repair_errors"], "retained_original": True}
        )
    finally:
        result["incremental_repair"] = {
            "scope": "incremental repair on retained artifacts",
            "attempted": attempted,
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            **_charges(_entries(client, prefix)),
        }
        write_json(output / f"{identifier}-result.json", result)
    return result


def run(
    baseline_directory: Path,
    output: Path,
    config: dict[str, Any],
    client: Any = None,
    *,
    image_factory: Callable[..., tuple[str | None, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Freeze immutable baseline provenance before explicitly authorized hosted repair."""
    if not config.get("run_hosted"):
        raise ValueError("Repair inference is opt-in; root must explicitly set run_hosted")
    if config["model"] not in DECISION_MODELS or config["image_edge"] not in (0, 256, 512, 1024):
        raise ValueError("Unknown native repair model or independent image edge")
    baseline_directory, output = guard_path(baseline_directory), guard_path(output)
    original_frozen = json.loads((baseline_directory / "frozen.json").read_bytes())
    original_report = json.loads((baseline_directory / "report.json").read_bytes())
    if original_frozen["config"].get("processor") != "regions":
        raise ValueError("Boundary repair requires retained source-only region pipeline outputs")
    records = original_frozen["records"]
    if len({_identifier(record["id"]) for record in records}) != len(records):
        raise ValueError("Duplicate retained page IDs")
    config = {
        "max_questions": 16,
        "minimum_join": 0.8,
        "minimum_margin": 0.25,
        **config,
        "campaign": "P003",
        "processor": "p003_boundary_repair",
        "run_id": output.name,
        "baseline_source_order": original_frozen["config"].get("source_order", "legacy"),
        "repair_scope": "incremental repair on retained artifacts",
    }
    if type(config["max_questions"]) is not int or not 1 <= config["max_questions"] <= 16:
        raise ValueError("Native repair requires 1-16 questions per batch")
    if any(
        type(config[k]) not in (int, float) or not math.isfinite(config[k]) or not 0 <= config[k] <= 1
        for k in ("minimum_join", "minimum_margin")
    ):
        raise ValueError("Invalid repair decoder thresholds")
    _identifier(output.name)
    output.mkdir(parents=True, exist_ok=False)
    copied = output / "baseline"
    copied.mkdir()
    hashes = {}
    names = ["report.json", "frozen.json"]
    for record in records:
        identifier = record["id"]
        names.extend(
            f"{identifier}{suffix}"
            for suffix in ("-result.json", "-structure.json", ".md")
            if (baseline_directory / f"{identifier}{suffix}").exists()
        )
    for name in names:
        data = (baseline_directory / name).read_bytes()
        hashes[name] = sha(data)
        (copied / name).write_bytes(data)
    if original_frozen.get("code_sha256"):
        (copied / "code").mkdir()
        for name, expected in original_frozen["code_sha256"].items():
            _identifier(name)
            data = guard_path(baseline_directory / "code" / name).read_bytes()
            if sha(data) != expected:
                raise ValueError("Baseline code archive hash changed")
            (copied / "code" / name).write_bytes(data)
            hashes["code/" + name] = sha(data)
    root = Path(__file__).resolve().parent
    fingerprints = {name: sha((root / name).read_bytes()) for name in CODE_FILES}
    (output / "code").mkdir()
    for name in CODE_FILES:
        (output / "code" / name).write_bytes((root / name).read_bytes())
    frozen = {
        "config": config,
        "manifest_sha256": original_frozen["manifest_sha256"],
        "records": deepcopy(records),
        "code_sha256": fingerprints,
        "baseline": {
            "directory": str(baseline_directory),
            "copied_directory": "baseline",
            "file_sha256": hashes,
            "source_order": config["baseline_source_order"],
            "original_config": original_frozen["config"],
        },
        "concurrency": 1,
        "local_replay": False,
    }
    write_json(output / "frozen.json", frozen)
    if client is None:
        client = DecisionClient()
    if _entries(client, f"P003/{config['run_id']}/"):
        raise ValueError("Repair run ID already exists in the persistent ledger; choose a fresh run ID")
    with pipeline.Resources() as resources:
        results = []
        for record in records:
            identifier = record["id"]
            original = json.loads((copied / f"{identifier}-result.json").read_bytes())
            results.append(
                process_retained(record, original, copied, output, config, client, image_factory=image_factory)
            )
    charges = _charges(_entries(client, f"P003/{config['run_id']}/"))
    metrics = {
        **resources.summary(),
        "scope": "incremental repair on retained artifacts",
        "interval": "After baseline/code copying: region images, request waits, decoding, composition and output",
        "baseline_freezing_resources": "unmeasured separately",
        "concurrency": 1,
        "end_to_end_pipeline_measured": False,
        "baseline_work_repeated": False,
    }
    report = {
        "config": config,
        "page_count": len(results),
        "complete_output_pages": sum(r["status"] == "ok" for r in results),
        "baseline_report": deepcopy(original_report),
        "metrics": metrics,
        "incremental_repair": {
            "metrics": metrics,
            "returned_calls": sum(len(r["repair_calls"]) for r in results),
            "repair_status_counts": dict(Counter(r["repair_status"] for r in results)),
            **charges,
        },
        "calls": sum(len(r["repair_calls"]) for r in results),
        "results": results,
        "pages_per_minute": None,
        "pages_per_dollar": None,
        "measurement_scope": "Incremental repair only. Original full-pipeline timing/cost retained in baseline_report.",
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Expose an explicit opt-in root-only hosted repair command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=DECISION_MODELS, required=True)
    parser.add_argument("--image-edge", type=int, choices=(0, 256, 512, 1024), default=0)
    parser.add_argument("--max-questions", type=int, choices=range(1, 17), default=16)
    parser.add_argument("--minimum-join", type=float, default=0.8)
    parser.add_argument("--minimum-margin", type=float, default=0.25)
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    config = vars(args).copy()
    config.pop("baseline")
    config.pop("output")
    report = run(args.baseline, args.output, config)
    print(json.dumps({k: v for k, v in report.items() if k not in {"results", "baseline_report"}}, indent=2))


if __name__ == "__main__":
    main()
