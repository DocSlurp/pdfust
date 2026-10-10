"""Root-only independent model selection from synthetic source-geometry diagrams."""

# ruff: noqa: ANN001, C408, SIM102, ANN401, EM101, TRY003, TRY301, PLR0913, PLR0912, C901, PLR2004, E501, SLF001
from __future__ import annotations

import argparse
import base64
import json
import resource
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench import p003_candidate_choice as chooser
from bench import p003_geometry_diagram as diagram
from bench import p003_geometry_diagram_prepare as preparer
from bench import pipeline_vision_transcription as transcription
from bench.decision_hosted import ROOT
from bench.p003_boundary_run import RESERVATION, _charges, _entries, _error, _identifier
from bench.p003_client import P003ConcurrentClient, P003DecisionClient
from bench.p003_micro_relations_run import CODE_FILES as COMMON_CODE
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

MODELS = ("perplexity/pplx-decider-v1.1-27b", "openai/gpt-6-luna-decisions", "cloudflare/clef-omni")
CODE_FILES = tuple(
    dict.fromkeys(
        (
            "p003_geometry_diagram_run.py",
            "p003_geometry_diagram.py",
            "p003_geometry_diagram_prepare.py",
            "p003_candidate_choice.py",
            "p003_candidate_run.py",
            "p003_gate_run.py",
            "pipeline_vision_transcription.py",
            *COMMON_CODE,
        )
    )
)


def read(path: Path) -> Any:
    """Read an explicitly selected guarded artifact."""
    return json.loads(guard_path(path).read_bytes())


def configuration(model: str, mode: str, edge: int, concurrency: int) -> dict[str, Any]:
    """Declare one independent treatment without implicit fallback."""
    if model not in MODELS or mode not in diagram.STYLES or type(edge) is not int or edge not in diagram.EDGES:
        raise ValueError("Explicit admitted model, diagram mode and edge required")
    if type(concurrency) is not int or concurrency not in (1, 3):
        raise ValueError("Transport capacity must be 1 or 3; Gateway is unsupported")
    return dict(
        processor="p003_geometry_diagram",
        campaign="P003",
        provider="openrouter",
        model=model,
        mode=mode,
        image_edge=edge,
        transport_concurrency=concurrency,
        workers=1,
        replay=False,
        retry=False,
        model_fallback=False,
        baseline_credit=False,
        pure_model=True,
        source_pixels_supplied=False,
        instruction_treatment_changed=True,
        pure_pixel_causal_control=False,
        source_conserved=False,
        composition_policy="selected_complete_crops; zero credit for uncovered crops; atomically reject conflicting positive composition",
        page_atomic_failure=False,
        full_page_denominator=16,
        scope="Incremental synthetic geometry-diagram crop selection; excludes OCR/TATR, generation and historical selector",
    )


def hydrate(record: dict[str, Any]) -> chooser.Pool:
    """Rehydrate immutable candidate bytes; strict helper validates identity."""
    pool = chooser.Pool(
        tuple(record["viewport"]),
        tuple(
            chooser.Candidate(c["alias"], c["canonical_json"].encode(), tuple(c["input_indexes"]))
            for c in record["candidates"]
        ),
        record["seed"],
        record["snapshot_sha256"],
    )
    if chooser.pool_record(pool) != record:
        raise ValueError("Candidate pool changed")
    return pool


def authenticate_pool(
    pool: Path, pool_trust: Path, selector_trust: Path, source_trust: Path, input_trust: list[Path]
) -> dict[str, Any]:
    """Authenticate every parent independently and reconstruct all diagrams, not archived code."""
    pool = guard_path(pool)
    pool_trust, selector_trust, source_trust = (guard_path(p) for p in (pool_trust, selector_trust, source_trust))
    input_trust = [guard_path(p) for p in input_trust]
    frozen, report = read(pool / "frozen.json"), read(pool / "report.json")
    preparer._archive(pool, frozen, pool_trust)
    for name, digest in frozen["code_sha256"].items():
        if sha(Path(__file__).with_name(name).read_bytes()) != digest:
            raise ValueError("Current diagram replay code differs from independently trusted freeze")
    if len(frozen["records"]) != 16 or len(report["pages"]) != 16 or frozen.get("references_read") is not False:
        raise ValueError("Complete source-only DEV16 freeze required")
    receipts = {r["name"]: r for r in frozen["trust_receipts"]}
    if set(receipts) != {"selector", "source", "input-0", "input-1"} or len(input_trust) != 2:
        raise ValueError("Independent selector/source/two-generation authorities required")
    authorities = {
        "selector": selector_trust,
        "source": source_trust,
        "input-0": input_trust[0],
        "input-1": input_trust[1],
    }
    for name, receipt in receipts.items():
        directory = guard_path(Path(receipt["directory"]))
        if sha(authorities[name].read_bytes()) != receipt["external_trusted_code_sha256"]:
            raise ValueError("External parent authority differs")
        for kind in ("frozen", "report"):
            if sha((directory / (kind + ".json")).read_bytes()) != receipt[kind + "_sha256"]:
                raise ValueError("Parent artifact changed")
    with tempfile.TemporaryDirectory(prefix="p003-diagram-auth-", dir=pool.parent) as temp:
        rebuilt = Path(temp) / "pool"
        result = preparer.prepare(
            Path(receipts["selector"]["directory"]),
            selector_trust,
            Path(receipts["source"]["directory"]),
            source_trust,
            [Path(receipts[f"input-{i}"]["directory"]) for i in range(2)],
            input_trust,
            rebuilt,
        )
        if read(rebuilt / "frozen.json") != frozen:
            raise ValueError("Complete frozen diagram contract changed")
        if result["pages"] != report["pages"]:
            raise ValueError("Complete diagram inventory differs from authenticated source replay")
        for path in rebuilt.rglob("*"):
            if (
                path.is_file()
                and path.name not in {"frozen.json", "report.json"}
                and "code" not in path.relative_to(rebuilt).parts
            ):
                if path.read_bytes() != (pool / path.relative_to(rebuilt)).read_bytes():
                    raise ValueError("Diagram, source or request bytes changed")
    return {"frozen": frozen, "report": report}


def prepare(
    pool: Path,
    output: Path,
    config: dict[str, Any],
    *,
    pool_trust: Path,
    selector_trust: Path,
    source_trust: Path,
    input_trust: list[Path],
) -> dict[str, Any]:
    """Freeze all complete requests and immutable history before client construction."""
    started, cpu_started = time.perf_counter(), time.process_time()
    pool, output = guard_path(pool), guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh output required")
    authenticated = authenticate_pool(pool, pool_trust, selector_trust, source_trust, input_trust)
    selected = []
    for page in authenticated["report"]["pages"]:
        for crop in page["crops"]:
            item = {
                "index": len(selected),
                "page_id": page["id"],
                "crop_index": crop["index"],
                "crop": crop,
                "body": None,
                "status": crop["status"],
            }
            if crop["status"] == "prepared":
                variant = next(
                    v for v in crop["variants"] if v["edge"] == config["image_edge"] and v["style"] == config["mode"]
                )
                image = (pool / variant["image_path"]).read_bytes()
                if sha(image) != variant["image_sha256"]:
                    raise ValueError("Selected diagram bytes changed")
                candidate_pool = hydrate(read(pool / crop["folder"] / "pool.json"))
                body, evidence = diagram.request(
                    candidate_pool, config["model"], "data:image/png;base64," + base64.b64encode(image).decode()
                )
                item.update(
                    body=body, pool=candidate_pool, evidence=evidence, status=evidence["status"], variant=variant
                )
            selected.append(item)
    output.mkdir()
    shutil.copytree(pool, output / "pool")
    (output / "code").mkdir()
    code = {}
    for name in CODE_FILES:
        path = Path(__file__).with_name(name)
        shutil.copyfile(path, output / "code" / name)
        code[name] = sha(path.read_bytes())
    histories = []
    for receipt in authenticated["frozen"]["trust_receipts"]:
        directory = guard_path(Path(receipt["directory"]))
        shutil.copytree(directory, output / "history" / receipt["name"])
        histories.append(
            {
                **receipt,
                "archive": "history/" + receipt["name"],
                "scope": "Historical only; excluded from incremental geometry-selection accounting",
            }
        )
    for item in selected:
        if item["body"] is not None:
            write_json(output / f"crop-{item['index']}-request.json", item["body"])
            raw = json.dumps(item["body"], separators=(",", ":"), allow_nan=False).encode()
            (output / f"crop-{item['index']}-wire.json").write_bytes(raw)
            if len(raw) > 750_000:
                raise ValueError("Complete selected request exceeds explicit body cap; no truncation")
            item["request_sha256"] = sha(raw)
    frozen = {
        "config": config,
        "records": authenticated["frozen"]["records"],
        "manifest_sha256": read(output / "history" / "source" / "frozen.json")["manifest_sha256"],
        "pool_frozen_sha256": sha((pool / "frozen.json").read_bytes()),
        "pool_report_sha256": sha((pool / "report.json").read_bytes()),
        "historical_provenance": histories,
        "code_sha256": code,
        "selected": [{k: v for k, v in i.items() if k not in {"pool", "body"}} for i in selected],
        "artifact_sha256": {str(p.relative_to(output)): sha(p.read_bytes()) for p in output.rglob("*") if p.is_file()},
        "all_inputs_frozen_before_client": True,
        "references_read": False,
        "preparation_resources": {
            "wall_seconds": time.perf_counter() - started,
            "self_cpu_seconds": time.process_time() - cpu_started,
            "peak_self_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "scope": "Authentication, reconstruction and archive preparation; separate from incremental hosted selection",
            "measurement": "process_time/perf_counter; lifetime getrusage RSS includes imports; no sampling; process scope only",
        },
        "independent_authorities": {
            "pool": str(pool_trust),
            "selector": str(selector_trust),
            "source": str(source_trust),
            "inputs": [str(p) for p in input_trust],
        },
    }
    write_json(output / "frozen.json", frozen)
    return {**authenticated, "selected": selected, "run_frozen": frozen}


def client_for(config: dict[str, Any], _prepared: dict[str, Any]) -> Any:
    """Construct shared-policy root client only after freezing."""
    return P003ConcurrentClient(ROOT) if config["transport_concurrency"] == 3 else P003DecisionClient(ROOT)


def assemble(page: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Retain only exact selected complete crops; reject conflicting positive composition atomically."""
    state = {"tables": [], "source_conserved": False, "text_provenance": "model-transcribed"}
    if page.get("status") == "not_applicable_baseline_failure":
        return {"state": state, "status": "error", "decision_status": "not_applicable_baseline_failure"}
    if not page["crops"]:
        return {"state": state, "status": "ok", "decision_status": "no_detector_crops"}
    if len(rows) != len(page["crops"]) or [r["crop_index"] for r in rows] != [c["index"] for c in page["crops"]]:
        raise ValueError("Complete crop outcome inventory is required")
    selected_rows = [r for r in rows if r["status"] == "selected"]
    complete = len(selected_rows) == len(page["crops"])
    tables = [t for row in selected_rows for t in json.loads(row["selected_canonical_json"])["tables"]]
    staged = {**state, "tables": tables}
    try:
        source_size = page.get("page_size")
        if source_size is None:
            source_size = page["source"]["page_size"]
        bounds = tuple(source_size) if len(source_size) == 4 else (0, 0, *source_size)
        chooser._validate(bounds, staged)
        if sum(t["row_count"] * t["col_count"] for t in tables) > 4096:
            raise ValueError("Complete page slot cap exceeded")
    except (ValueError, KeyError, TypeError) as exc:
        return {
            "state": state,
            "status": "error",
            "decision_status": "composition_failed",
            "error": _error(exc, "compose"),
        }
    return {
        "state": staged,
        "status": "ok" if complete else "error",
        "decision_status": "selected_complete_crops"
        if complete
        else "selected_partial_crops"
        if selected_rows
        else "failed_closed",
        "complete_crop_coverage": complete,
        "selected_crop_count": len(selected_rows),
        "uncovered_crop_count": len(rows) - len(selected_rows),
    }


def execute(
    prepared: dict[str, Any],
    output: Path,
    config: dict[str, Any],
    *,
    client_factory=client_for,
    entries_reader=_entries,
) -> dict[str, Any]:
    """Ask each distinct crop once; first transport failure stops further reservations."""
    prefix = f"P003/{config['run_id']}/geometry-diagram/"
    client, initialization_error = None, None
    try:
        client = client_factory(config, prepared)
    except Exception as exc:
        initialization_error = _error(exc, "client_initialization")
    stopped, decisions = client is None, []
    with Resources() as resources:
        for item in prepared["selected"]:
            row = {
                "index": item["index"],
                "page_id": item["page_id"],
                "crop_index": item["crop_index"],
                "model": config["model"],
                "status": "not_attempted",
            }
            if item["body"] is None:
                row["status"] = item["status"]
            elif not stopped:
                began, cpu_began = time.perf_counter(), time.process_time()
                try:
                    response = client.request(
                        item["body"],
                        tag=prefix + str(item["index"]),
                        replay=False,
                        reservation_usd=RESERVATION,
                        max_body_bytes=750_000,
                    )
                except Exception as exc:
                    row.update(status="transport_error", error=_error(exc, "transport"))
                    stopped = True
                else:
                    write_json(output / f"crop-{item['index']}-response.json", response)
                    try:
                        if not isinstance(response, dict):
                            raise TypeError("Invalid client response envelope")
                        row.update(
                            entry=response.get("entry"),
                            usage=(
                                response.get("result", {}).get("usage", {})
                                if isinstance(response.get("result"), dict)
                                else {}
                            ),
                            admission_wait_seconds=response.get("admission_wait_seconds"),
                            replayed=response.get("replayed"),
                        )
                        if response.get("replayed"):
                            raise ValueError("Fresh selection cannot replay answers")
                        parsed = chooser.parse(item["pool"], response["result"])
                        selected, audit = chooser.select(item["pool"], parsed)
                        row.update(status=audit["selection_status"], audit=audit)
                        if selected is not None:
                            row.update(selected_canonical_json=selected.decode(), selected_sha256=sha(selected))
                    except (ValueError, KeyError, TypeError) as exc:
                        row.update(status="malformed_response", error=_error(exc, "parse"))
                row["client_wall_seconds"] = time.perf_counter() - began
                row["client_cpu_seconds"] = time.process_time() - cpu_began
            decisions.append(row)
            write_json(output / "decision-results.json", {"decisions": decisions})
            write_json(output / f"crop-{item['index']}-result.json", row)
        results = []
        for page in prepared["report"]["pages"]:
            source = read(output / "pool" / page["source_path"])
            rows = [r for r in decisions if r["page_id"] == page["id"]]
            assembled = assemble({**page, "source": source}, rows)
            row = {
                "id": page["id"],
                "record": page.get("record"),
                "viewport": source["page_size"],
                "original_rotation": page.get("original_rotation"),
                "effective_rotation": page.get("effective_rotation"),
                **assembled,
                "tables": assembled["state"]["tables"],
                "selection_status": assembled["decision_status"],
                "crop_count": len(page["crops"]),
                "selected_decision_crop_count": sum(r["status"] == "selected" for r in rows),
                "accepted_crop_count": sum(r["status"] == "selected" for r in rows)
                if assembled["decision_status"] in {"selected_complete_crops", "selected_partial_crops"}
                else 0,
                "complete_crop_coverage": assembled["decision_status"]
                in {"selected_complete_crops", "no_detector_crops"},
                "decision_results": rows,
                "model": config["model"],
                "pure_model": True,
                "baseline_credit": False,
                "source_conserved": False,
                "predicted_table_count": len(assembled["state"]["tables"]),
            }
            write_json(output / (page["id"] + "-state.json"), row["state"])
            write_json(output / (page["id"] + "-structure.json"), row["tables"])
            (output / (page["id"] + ".md")).write_text(transcription.markdown(row["state"]))
            write_json(output / (page["id"] + "-result.json"), row)
            results.append(row)
    entries = entries_reader(client, prefix) if client is not None else []
    charges = _charges(entries)
    charges["cost_scope"] = (
        "Incremental geometry-diagram selection API attempts including failures; excludes all historical acquisition/generation/selector costs"
    )
    attempted = sum(
        r["status"] in {"selected", "unresolved", "malformed_response", "transport_error"} for r in decisions
    )
    if attempted and not entries:
        charges.update(effective_usd=None, provider_reported_usd=None, accounting_status="unmeasured missing attempts")
    metrics = resources.summary()
    wall, cost = metrics["wall_seconds"], charges["effective_usd"]
    complete = sum(r["status"] == "ok" for r in results)
    report = {
        "config": config,
        "results": results,
        "decisions": decisions,
        "intended_page_count": 16,
        "valid_completed_page_count": complete,
        "model_credited_page_count": sum(r["predicted_table_count"] > 0 for r in results),
        "no_detector_crop_page_count": sum(r["selection_status"] == "no_detector_crops" for r in results),
        "attempted_question_count": attempted,
        "decision_status_counts": dict(Counter(r["status"] for r in decisions)),
        "client_initialization_error": initialization_error,
        "historical_provenance": prepared.get("run_frozen", {}).get("historical_provenance", []),
        "incremental_selection": {
            "metrics": metrics,
            "charges": charges,
            "scope": config["scope"],
            "denominator": 16,
            "intended_pages_per_minute": 960 / wall if wall else None,
            "valid_completed_pages_per_minute": 60 * complete / wall if wall else None,
            "intended_pages_per_dollar": 16 / cost if cost and cost > 0 else None,
            "valid_completed_pages_per_dollar": complete / cost if cost and cost > 0 else None,
        },
        "full_pipeline_pages_per_minute": None,
        "full_pipeline_pages_per_dollar": None,
        "baseline_credit": False,
        "model_fallbacks": 0,
        "retries": 0,
        "references_read": False,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Freeze-only by default; paid execution requires explicit root opt-in."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pool", "pool-trusted-code", "selector-trusted-code", "source-trusted-code", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--input-trusted-code", type=Path, action="append", required=True)
    parser.add_argument("--model", choices=MODELS, default=MODELS[0])
    parser.add_argument("--mode", choices=diagram.STYLES, required=True)
    parser.add_argument("--image-edge", choices=diagram.EDGES, type=int, required=True)
    parser.add_argument("--transport-concurrency", choices=(1, 3), type=int, default=3)
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    config = configuration(args.model, args.mode, args.image_edge, args.transport_concurrency)
    config["run_id"] = _identifier(args.output.name)
    prepared = prepare(
        args.pool,
        args.output,
        config,
        pool_trust=args.pool_trusted_code,
        selector_trust=args.selector_trusted_code,
        source_trust=args.source_trusted_code,
        input_trust=args.input_trusted_code,
    )
    if args.run_hosted:
        execute(prepared, args.output, config)
    else:
        write_json(
            args.output / "prepare-report.json",
            {
                "status": "prepared_only",
                "intended_page_count": 16,
                "prepared_question_count": sum(i["body"] is not None for i in prepared["selected"]),
                "rates": None,
                "hosted_calls": 0,
            },
        )


if __name__ == "__main__":
    main()
