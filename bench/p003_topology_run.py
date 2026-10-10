"""Root-only retained topology/source ownership experiment, with atomic page fallback."""

# Explicit experiment artifact schemas and reuse of strict trusted replay helpers.
# ruff: noqa: ANN401, EM101, TRY003, SLF001, C901, PLR0912, PLR0913, PLR0917, PLR2004, TRY301
from __future__ import annotations

import argparse
import json
import shutil
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import p003_candidate_run as candidate
from bench import p003_topology_geometry as geometry
from bench import p003_topology_ownership as ownership
from bench import pipeline_run as pipeline
from bench import pipeline_vision_transcription as transcription
from bench.generalization_report import verify_output
from bench.generalization_run import _table_bounds
from bench.p003_boundary_run import RESERVATION, _charges, _entries, _error, _identifier
from bench.p003_client import P003ConcurrentClient, P003DecisionClient
from bench.pipeline_regions import _source, compose
from bench.pipeline_source_order import render_source
from bench.silver import guard_path, sha, write_json

MAX_BODY_BYTES = 750_000
CODE_FILES = (
    "p003_topology_run.py",
    "p003_topology_ownership.py",
    "p003_transcription_design.py",
    "p003_candidate_run.py",
    "p003_candidate_choice.py",
    "p003_boundary_run.py",
    "pipeline_vision_transcription.py",
    "pipeline_frontier.py",
    "pipeline_assembly.py",
    "pipeline_regions.py",
    "pipeline_source_order.py",
    "pipeline_run.py",
    "generalization_run.py",
    "generalization_report.py",
    "generalization_vision_regions.py",
    "p003_client.py",
    "decision_concurrent.py",
    "decision_hosted.py",
    "decision_gateway.py",
    "research_policy.py",
    "decision_langfuse.py",
    "reprice_model_rates.py",
)


class UnsupportedError(ValueError):
    """An explicit preflight limitation retaining the original complete page."""


def authenticate_source(directory: Path, trusted: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Authenticate archived source-only regions independently, without archived execution."""
    frozen, report = candidate._read(directory / "frozen.json"), candidate._read(directory / "report.json")
    if frozen["config"].get("processor") != "regions" or report["config"].get("processor") != "regions":
        raise ValueError("Topology ownership requires a source-only regions baseline")
    hashes = frozen["code_sha256"]
    required = {"pipeline_run.py", "pipeline_regions.py", "pipeline_assembly.py", "generalization_run.py"}
    if not isinstance(hashes, dict) or not required <= set(hashes):
        raise ValueError("Source baseline lacks required authenticated code")
    for name, digest in hashes.items():
        _identifier(name)
        if (
            not name.endswith(".py")
            or trusted.get(name) != digest
            or sha(guard_path(directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Source baseline archive differs from independent trusted map")
    rows = {row["id"]: row for row in report["results"]}
    if len(rows) != len(report["results"]) or set(rows) != {r["id"] for r in frozen["records"]}:
        raise ValueError("Source baseline report differs from frozen inventory")
    for record in frozen["records"]:
        _identifier(record["id"])
        row = rows[record["id"]]
        if candidate._read(directory / f"{record['id']}-result.json") != row:
            raise ValueError("Source per-page result differs from report")
        if sha(guard_path(Path(record["pdf_path"])).read_bytes()) != record["pdf_sha256"]:
            raise ValueError("Source baseline PDF identity differs")
        verify_output(
            directory,
            row,
            processor="regions",
            source_order=frozen["config"].get("source_order", "legacy"),
        )
    return frozen, report


def _inside(box: list[float], bounds: list[float]) -> bool:
    return box[0] >= bounds[0] and box[1] >= bounds[1] and box[2] <= bounds[2] and box[3] <= bounds[3]


def _overlap(a: list[float], b: list[float]) -> bool:
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def prepare_page(
    original: dict[str, Any],
    topology_page: dict[str, Any],
    topology_directory: Path,
    topology_config: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Preflight the entire crop/source partition before making any paid request."""
    raw = original["source"]
    source = _source(raw)
    viewport = [0, 0, *source["page_size"]] if len(source["page_size"]) == 2 else source["page_size"]
    if (
        viewport != topology_page["viewport"]
        or original.get("rotation_normalized", False)
        or original.get("original_rotation", 0) != topology_page["original_rotation"]
    ):
        raise UnsupportedError("coordinate_or_rotation_mismatch")
    original_plan = {**deepcopy(original["region_plan"]), "words": deepcopy(raw["words"])}
    original_states = {info["id"]: deepcopy(info["state"]) for info in original["regions"]}
    prior = compose(original_plan, original_states)
    _table_bounds(raw, prior)
    crops = []
    for crop in topology_page["transcription_regions"]:
        parsed = transcription.parse(crop["transcription_response"], crop["viewport"])
        if not parsed["tables"]:
            continue  # No positive topology: retain original baseline, explicitly no choice.
        body = candidate._read(topology_directory / f"{original['id']}-request-{crop['request_index']}.json")
        url, image = candidate._crop_bytes(body)
        expected = transcription.request(body["model"], url, crop["viewport"], body["max_tokens"])
        provider = topology_config.get("generation_provider")
        if provider:
            expected["provider"] = {"only": [provider], "allow_fallbacks": False, "require_parameters": True}
        if (
            body != expected
            or sha(json.dumps(expected, separators=(",", ":")).encode()) != crop["request"]["body_sha256"]
        ):
            raise ValueError("Topology crop request does not match strict retained evidence")
        if (
            sha(image) != crop["image"]["image_sha256"]
            or crop["image"]["image_viewport"] != crop["viewport"]
            or len(image) != crop["image"]["image_bytes"]
        ):
            raise ValueError("Actual topology crop bytes/viewport differ from provenance")
        payload, _ = ownership.scaffold._payload(crop["transcription_response"])
        tables = [
            {
                "bbox": t["bbox"],
                "row_count": len(t["matrix"]),
                "col_count": len(t["matrix"][0]),
                "mergedspans": t["mergedspans"],
            }
            for t in payload["answers"]["q0"]["tables"]
        ]
        response = {
            "choices": [
                {"finish_reason": "stop", "message": {"content": json.dumps({"answers": {"q0": {"tables": tables}}})}}
            ]
        }
        crops.append(
            {
                "id": f"topology-{crop['index']}",
                "crop_index": crop["index"],
                "viewport": crop["viewport"],
                "topology_response": response,
                "url": url,
            }
        )
    if not crops:
        return {"plan": original_plan, "states": original_states, "crops": []}
    for native in raw.get("vector_candidates", []):
        if any(_overlap(native["bbox"], crop["viewport"]) for crop in crops):
            raise UnsupportedError("native_grid_overlap")
    assigned: dict[str, str | None] = {}
    boundary_ids = []
    boundary_mode = config.get("boundary_words", "strict")
    if boundary_mode not in {"strict", "residual"}:
        raise ValueError("Unknown boundary word treatment")
    for word in source["words"]:
        owners = [crop["id"] for crop in crops if _inside(word["bbox"], crop["viewport"])]
        partial = any(
            _overlap(word["bbox"], crop["viewport"]) and not _inside(word["bbox"], crop["viewport"]) for crop in crops
        )
        if len(owners) > 1 or partial:
            if boundary_mode == "strict":
                raise UnsupportedError("ambiguous_or_straddling_source_word")
            boundary_ids.append(word["id"])
            assigned[word["id"]] = None
        else:
            assigned[word["id"]] = owners[0] if owners else None
    regions, states = [], {}
    source_lookup = {w["id"]: w for w in source["words"]}
    for old in original_plan["regions"]:
        remaining = [identifier for identifier in old["source_ids"] if assigned[identifier] is None]
        tables = []
        for table in original_states[old["id"]]["tables"]:
            ids = [i for cell in table["cells"] for i in cell["source_ids"]]
            destinations = {assigned[i] for i in ids}
            if len(destinations) > 1:
                raise UnsupportedError("original_table_crosses_crop_partition")
            if not destinations or destinations == {None}:
                tables.append(deepcopy(table))
        region = {
            **deepcopy(old),
            "source_ids": remaining,
            "source": {
                "page_size": source["page_size"],
                "words": [source_lookup[identifier] for identifier in remaining],
            },
        }
        kept = {i for table in tables for cell in table["cells"] for i in cell["source_ids"]}
        state = {
            "id": "c0",
            "tables": tables,
            "unresolved_ids": [i for i in remaining if i not in kept],
            "mechanism": "retained_source_residual",
        }
        regions.append(region)
        states[region["id"]] = state
    for crop in crops:
        words = [word for word in source["words"] if assigned[word["id"]] == crop["id"]]
        if not words:
            raise UnsupportedError("empty_source_inventory_cannot_transcribe")
        local = {"page_size": source["page_size"], "words": words}
        try:
            frozen = ownership.freeze(local, crop["topology_response"], crop["viewport"], crop["url"])
            row_bodies = ownership.batches(
                frozen,
                config["model"],
                crop["url"],
                max_questions=config["max_questions"],
                image=config.get("image", True),
            )
            if any(
                len(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()) > MAX_BODY_BYTES
                for body in row_bodies
            ):
                raise ValueError("body capacity")
        except ValueError as error:
            raise UnsupportedError("ownership_inventory_or_menu_capacity") from error
        crop.update(snapshot=frozen, row_bodies=row_bodies)
        regions.append(
            {
                "id": crop["id"],
                "bbox": crop["viewport"],
                "boundary": "frozen_positive_topology",
                "source_ids": [w["id"] for w in words],
                "source": local,
            }
        )
    return {
        "plan": {
            **source,
            "regions": regions,
            "coordinate_space": "display_global",
            **(
                {
                    "boundary_words": {
                        "mode": "residual",
                        "retained_original_region_ids": boundary_ids,
                        "boxes_and_strings": "Original complete words retained; never clipped",
                    }
                }
                if boundary_mode == "residual"
                else {}
            ),
        },
        "states": states,
        "crops": crops,
    }


def _request(client: Any, body: dict[str, Any], output: Path, stem: str, tag: str) -> dict[str, Any]:
    write_json(output / f"{stem}-request.json", body)
    try:
        response = client.request(
            body, tag=tag, replay=False, max_body_bytes=MAX_BODY_BYTES, reservation_usd=RESERVATION
        )
    except Exception as error:
        write_json(output / f"{stem}-response.json", {"status": "failed", "error": _error(error, "transport")})
        raise
    write_json(output / f"{stem}-response.json", response)
    return response


def process_page(
    original: dict[str, Any],
    topology_page: dict[str, Any],
    source_directory: Path,
    topology_directory: Path,
    topology_config: dict[str, Any],
    output: Path,
    config: dict[str, Any],
    client: Any = None,
) -> dict[str, Any]:
    """Stage every crop and commit all source edits once; every failure retains baseline bytes."""
    started, cpu = time.perf_counter(), time.process_time()
    ident = _identifier(original["id"])
    result = deepcopy(original)
    result.update(topology_status="not_applicable", topology_calls=[], topology_errors=[], topology_regions=[])
    for suffix in ("-structure.json", ".md"):
        path = source_directory / f"{ident}{suffix}"
        if path.exists():
            (output / path.name).write_bytes(path.read_bytes())
    stage = "preflight"
    try:
        if original["status"] != "ok":
            result["topology_status"] = "baseline_failed_skipped"
            return result
        if topology_page["status"] != "ok":
            result["topology_status"] = "topology_baseline_failed_skipped"
            return result
        work = prepare_page(original, topology_page, topology_directory, topology_config, config)
        write_json(output / f"{ident}-ownership-plan.json", work["plan"])
        if not work["crops"]:
            return result
        states = deepcopy(work["states"])
        for crop in work["crops"]:
            stage = f"{crop['id']}/rows"
            stem = f"{ident}-{crop['id']}"
            write_json(output / f"{stem}-snapshot.json", json.loads(crop["snapshot"].packet_json))
            info = {
                "id": crop["id"],
                "crop_index": crop["crop_index"],
                "snapshot_sha256": crop["snapshot"].sha256,
                "snapshot_file": f"{stem}-snapshot.json",
                "status": "prepared",
                "word_count": len(json.loads(crop["snapshot"].packet_json)["source"]["words"]),
                "maximum_new_ownership_calls": 0
                if config.get("geometry_only") or config.get("transcript_replay")
                else 2 * len(crop["row_bodies"]),
                "rows": [],
                "cells": [],
            }
            result["topology_regions"].append(info)
            if config.get("prepare_only"):
                for i, body in enumerate(crop["row_bodies"]):
                    write_json(output / f"{stem}-row-{i}-request.json", body)
                    info["rows"].append(f"{stem}-row-{i}")
                continue
            if config.get("geometry_only"):
                audit = geometry.place(crop["snapshot"], band_mode=config.get("band_mode", "uniform"))
                states[crop["id"]] = audit["state"]
                write_json(output / f"{stem}-geometry-audit.json", audit)
                write_json(output / f"{stem}-updated-state.json", audit["state"])
                info["status"] = "staged"
                info["placement_mechanism"] = (
                    "source_band_geometry" if config.get("band_mode") == "source" else "uniform_geometry"
                )
                continue
            responses = []
            for i, body in enumerate(crop["row_bodies"]):
                request_stem = f"{stem}-row-{i}"
                info["rows"].append(request_stem)
                response = _request(
                    client, body, output, request_stem, f"P003/{config['run_id']}/{ident}/{crop['id']}/row/{i}"
                )
                result["topology_calls"].append(response)
                responses.append(response["result"])
            rows = ownership.collect(crop["snapshot"], crop["row_bodies"], responses)
            write_json(output / f"{stem}-row-receipt.json", rows)
            cell_bodies = ownership.batches(
                crop["snapshot"],
                config["model"],
                crop["url"],
                rows=rows,
                max_questions=config["max_questions"],
                image=config.get("image", True),
            )
            stage = f"{crop['id']}/cells"
            cell_responses = []
            for i, body in enumerate(cell_bodies):
                request_stem = f"{stem}-cell-{i}"
                info["cells"].append(request_stem)
                response = _request(
                    client, body, output, request_stem, f"P003/{config['run_id']}/{ident}/{crop['id']}/cell/{i}"
                )
                result["topology_calls"].append(response)
                cell_responses.append(response["result"])
            audit = ownership.assemble(crop["snapshot"], crop["row_bodies"], responses, cell_bodies, cell_responses)
            states[crop["id"]] = audit["state"]
            write_json(output / f"{stem}-audit.json", audit)
            write_json(output / f"{stem}-updated-state.json", audit["state"])
            info["status"] = "staged"
        if config.get("prepare_only"):
            result["topology_status"] = "prepared_retained_baseline"
            return result
        stage = "atomic_page_composition"
        composed = compose(work["plan"], states)
        _table_bounds(original["source"], composed)
        for i, table in enumerate(composed["tables"]):
            if any(_overlap(table["bbox"], other["bbox"]) for other in composed["tables"][:i]):
                raise ValueError("Source-owned composed tables overlap")
        order = {word["id"]: i for i, word in enumerate(original["source"]["words"])}
        texts = []
        for region in work["plan"]["regions"]:
            rendering = (
                render_source(original["source"], region)
                if config["baseline_source_order"] == "original"
                else region["source"]
            )
            texts.append(
                (
                    min((order[i] for i in region["source_ids"]), default=len(order)),
                    pipeline.markdown(rendering, states[region["id"]]),
                )
            )
        text = "\n".join(value for _, value in sorted(texts))
        result.update(
            tables=composed["tables"],
            unresolved_ids=composed["unresolved_ids"],
            source_conserved=True,
            region_plan={k: v for k, v in work["plan"].items() if k != "words"},
            regions=[{"id": ident, "state": state} for ident, state in states.items()],
            topology_status="completed",
            status="ok",
            text_provenance="literal-source-words",
        )
        for info in result["topology_regions"]:
            info["status"] = "completed"
        write_json(output / f"{ident}-structure.json", composed)
        (output / f"{ident}.md").write_text(text)
    except Exception as error:
        # Effective status/tables remain original, even after late composition/render failures.
        for suffix in ("-structure.json", ".md"):
            path = source_directory / f"{ident}{suffix}"
            if path.exists():
                (output / path.name).write_bytes(path.read_bytes())
        retained = {key: result[key] for key in ("topology_calls", "topology_errors", "topology_regions")}
        result.clear()
        result.update(deepcopy(original))
        result.update(retained)
        result["topology_status"] = (
            "unsupported_retained_baseline" if isinstance(error, UnsupportedError) else "failed_retained_baseline"
        )
        result["topology_errors"].append(
            {**_error(error, stage), **({"reason": str(error)} if isinstance(error, UnsupportedError) else {})}
        )
        for info in result["topology_regions"]:
            info["status"] = "discarded_atomic_failure" if info["status"] in {"staged", "completed"} else "failed"
    finally:
        result["incremental_ownership"] = {
            "scope": "retained page artifacts through processing, before final result write",
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "returned_calls": 0 if config.get("transcript_replay") else len(result["topology_calls"]),
            **({"retained_response_count": len(result["topology_calls"])} if config.get("transcript_replay") else {}),
        }
        write_json(output / f"{ident}-result.json", result)
    return result


def _copy(directory: Path, target: Path, frozen: dict[str, Any], trusted: dict[str, str]) -> dict[str, Any]:
    target.mkdir(parents=True)
    ids = [_identifier(row["id"]) for row in frozen["records"]]
    files = {"report.json", "frozen.json"}
    for ident in ids:
        files.update(
            p.name
            for p in directory.glob(f"{ident}*")
            if p.is_file()
            and (
                p.name in {f"{ident}.md", f"{ident}-result.json", f"{ident}-structure.json"}
                or p.name.startswith(f"{ident}-request")
                or p.name.startswith(f"{ident}-response")
            )
        )
    hashes = {}
    for name in sorted(files):
        data = guard_path(directory / name).read_bytes()
        (target / name).write_bytes(data)
        hashes[name] = sha(data)
    (target / "code").mkdir()
    for name in frozen["code_sha256"]:
        data = guard_path(directory / "code" / name).read_bytes()
        (target / "code" / name).write_bytes(data)
        hashes[f"code/{name}"] = sha(data)
    return {
        "directory": str(directory),
        "copied_directory": str(target.name),
        "file_sha256": hashes,
        "trusted_code": trusted,
        "original_config": frozen["config"],
    }


def run(
    source_directory: Path,
    topology_directory: Path,
    source_trusted: dict[str, str],
    topology_trusted: dict[str, str],
    output: Path,
    config: dict[str, Any],
    client: Any = None,
) -> dict[str, Any]:
    """Authenticate exact retained sources and freeze provenance before root opt-in calls."""
    if sum(bool(config.get(k)) for k in ("run_hosted", "prepare_only", "geometry_only", "transcript_replay")) != 1:
        raise ValueError("Choose exactly one explicit hosted, preparation, geometry, or transcript mode")
    if config.get("transcript_replay") and client is None:
        raise ValueError("Transcript replay requires an injected offline exact-body transport")
    if config.get("band_mode", "uniform") not in {"uniform", "source"} or (
        config.get("band_mode") == "source" and not config.get("geometry_only")
    ):
        raise ValueError("Source bands require explicit geometry-only treatment")
    if config.get("boundary_words", "strict") not in {"strict", "residual"}:
        raise ValueError("Unknown boundary word treatment")
    transport = config.get("transport_concurrency", 1)
    if type(config.get("image", True)) is not bool:
        raise ValueError("Ownership image flag must be boolean")
    admitted_models = candidate.IMAGE_MODELS if config.get("image", True) else ownership.DECISION_MODELS
    if type(transport) is not int or transport not in (1, 3) or config.get("model") not in admitted_models:
        raise ValueError("Unknown admitted image decision model or transport concurrency")
    if type(config.get("max_questions", 16)) is not int or not 1 <= config.get("max_questions", 16) <= 16:
        raise ValueError("Native ownership batches require 1-16 questions")
    source_directory, topology_directory, output = map(guard_path, (source_directory, topology_directory, output))
    sf, sr = authenticate_source(source_directory, source_trusted)
    tf, tr, _ = candidate.authenticate(
        topology_directory, topology_trusted, reviewed_parser_sha256=tuple(config.get("reviewed_parser_sha256", []))
    )

    def identity(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {r["id"]: {k: r[k] for k in ("id", "pdf_path", "pdf_sha256", "page_number")} for r in rows}

    if (
        len(sf["records"]) != 16
        or len(tf["records"]) != 16
        or len(identity(sf["records"])) != 16
        or identity(sf["records"]) != identity(tf["records"])
        or sf["manifest_sha256"] != tf["manifest_sha256"]
    ):
        raise ValueError("Ownership baselines must match complete same16 PDF/manifest inventory")
    config = {
        "max_questions": 16,
        **config,
        "campaign": "P003",
        "run_id": _identifier(output.name),
        "processor": "p003_topology_source",
        "baseline_source_order": sf["config"].get("source_order", "legacy"),
        "scope": "incremental topology ownership on retained source words and crops",
        "source_conserved": True,
    }
    output.mkdir(parents=True, exist_ok=False)
    inventories = {
        "source_baseline": _copy(source_directory, output / "source-baseline", sf, source_trusted),
        "topology_baseline": _copy(topology_directory, output / "topology-baseline", tf, topology_trusted),
    }
    (output / "code").mkdir()
    code = {}
    root = Path(__file__).parent
    for name in (
        CODE_FILES
        + (("p003_topology_geometry.py",) if config.get("geometry_only") else ())
        + (("p003_topology_replay.py",) if config.get("transcript_replay") else ())
        + (("p003_spatial_bands.py",) if config.get("band_mode") == "source" else ())
    ):
        data = (root / name).read_bytes()
        (output / "code" / name).write_bytes(data)
        code[name] = sha(data)
    write_json(
        output / "frozen.json",
        {
            "config": config,
            "records": sf["records"],
            "manifest_sha256": sf["manifest_sha256"],
            "code_sha256": code,
            **inventories,
            "concurrency": 1,
            "local_replay": False,
        },
    )
    if config.get("run_hosted") and client is None:
        client = (P003ConcurrentClient if transport == 3 else P003DecisionClient)()
    prefix = f"P003/{config['run_id']}/"
    if _entries(None if config.get("transcript_replay") else client, prefix):
        raise ValueError("Run ID already retained in shared ledger; no automatic retry")
    sm, tm = ({row["id"]: row for row in report["results"]} for report in (sr, tr))
    with pipeline.Resources() as resources:
        results = [
            process_page(
                sm[r["id"]],
                tm[r["id"]],
                output / "source-baseline",
                output / "topology-baseline",
                tf["config"],
                output,
                config,
                client,
            )
            for r in sf["records"]
        ]
    attempts = _entries(None if config.get("transcript_replay") else client, prefix)
    # Retain shared transport evidence for every attempt, including failed reservations.
    transport_dir = output / "transport"
    transport_dir.mkdir()
    client_dir = getattr(client, "directory", None)
    if client_dir is not None:
        for entry in attempts:
            for name in {
                f"request-{entry['index']:03d}.json",
                entry.get("response_file"),
                entry.get("response_prefix_file"),
            } - {None}:
                _identifier(name)
                path = guard_path(client_dir / name)
                if path.exists():
                    shutil.copyfile(path, transport_dir / path.name)
    metrics = {
        **resources.summary(),
        "scope": config["scope"],
        "concurrency": 1,
        "transport_concurrency": transport,
        "end_to_end_pipeline_measured": False,
        "baseline_authentication_and_copying": "unmeasured separately",
    }
    report = {
        "config": config,
        "page_count": len(results),
        "complete_output_pages": sum(r["status"] == "ok" for r in results),
        "source_generation_report": sr,
        "topology_generation_report": tr,
        "metrics": metrics,
        "generation_cost_scope": (
            "Historical baselines retained separately, including invalid/failed attempts; not repaid or blindly summed"
        ),
        "incremental_ownership": {
            "metrics": metrics,
            "returned_calls": 0 if config.get("transcript_replay") else sum(len(r["topology_calls"]) for r in results),
            **(
                {"retained_response_count": sum(len(r["topology_calls"]) for r in results)}
                if config.get("transcript_replay")
                else {}
            ),
            "status_counts": dict(Counter(r["topology_status"] for r in results)),
            "maximum_new_ownership_calls_from_preflight": sum(
                info["maximum_new_ownership_calls"] for row in results for info in row["topology_regions"]
            ),
            "attempts": attempts,
            **_charges(attempts),
            "cost_scope": (
                "Incremental topology ownership API attempts only; historical source/topology generation "
                "costs retained separately. Unresolved reservations remain separate from charges and estimates."
            ),
        },
        "results": results,
        "pages_per_minute": None,
        "pages_per_dollar": None,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Require explicit root input/trust maps and fresh output; preparation creates no client."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-baseline", type=Path, required=True)
    parser.add_argument("--topology-baseline", type=Path, required=True)
    parser.add_argument("--source-trusted-code", type=Path, required=True)
    parser.add_argument("--topology-trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=ownership.DECISION_MODELS, required=True)
    parser.add_argument("--text-only", action="store_true")
    parser.add_argument("--band-mode", choices=("uniform", "source"), default="uniform")
    parser.add_argument("--boundary-words", choices=("strict", "residual"), default="strict")
    parser.add_argument("--max-questions", type=int, choices=range(1, 17), default=16)
    parser.add_argument("--transport-concurrency", type=int, choices=(1, 3), default=1)
    parser.add_argument("--reviewed-parser-sha256", action="append", default=[])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run-hosted", action="store_true")
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--geometry-only", action="store_true")
    args = parser.parse_args()
    config = {
        k: getattr(args, k) for k in ("model", "max_questions", "run_hosted", "prepare_only", "reviewed_parser_sha256")
    }
    if args.band_mode == "source":
        config["band_mode"] = "source"
    if args.text_only:
        config["image"] = False
    if args.geometry_only:
        config["geometry_only"] = True
    if args.boundary_words == "residual":
        config["boundary_words"] = "residual"
    if args.transport_concurrency == 3:
        config["transport_concurrency"] = 3
    report = run(
        args.source_baseline,
        args.topology_baseline,
        candidate._read(args.source_trusted_code),
        candidate._read(args.topology_trusted_code),
        args.output,
        config,
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in {"results", "source_generation_report", "topology_generation_report"}
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
