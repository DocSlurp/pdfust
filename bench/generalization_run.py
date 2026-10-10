"""Source-only region pipeline for P002; scoring references are never loaded."""

# Explicit retained experiment dictionaries are heterogeneous.
# ruff: noqa: ANN401, EM101, TRY003, PLC0415, TRY301, PLR0913, PLR0917, C901
from __future__ import annotations

import argparse
import base64
import io
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench import pipeline_run as baseline
from bench.pipeline_admission import admission_packet
from bench.pipeline_assembly import native_state, packet, propose, validate
from bench.pipeline_column_consensus import propose as column_proposals
from bench.pipeline_readable_packet import packet as readable_packet
from bench.silver import guard_path, sha, write_json

if TYPE_CHECKING:
    from bench.decision_hosted import DecisionClient

MAX_RASTER_EDGE = 2400


def sanitize_vectors(snapshot: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Quarantine invalid native grids while retaining their words for rediscovery."""
    from bench.pipeline_assembly import _native, _span_mask

    kept, warnings = [], []
    for index, vector in enumerate(snapshot.get("vector_candidates", [])):
        try:
            tables = _native({"vector_candidates": [vector]}, [])
            _span_mask(tables[0])
            kept.append(vector)
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            warnings.append({"native_index": index, "reason": str(exc)[:300]})
    return {**snapshot, "vector_candidates": kept}, warnings


def region_image(page: Any, bbox: list[float], edge: int) -> tuple[str | None, dict[str, Any]]:
    """Render a bounded crop with its true global viewport and measured dimensions."""
    from PIL import Image

    if edge == 0:
        return None, {"image": "none"}
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Image viewport must have positive extent")
    scale = min(edge / max(x1 - x0, y1 - y0), MAX_RASTER_EDGE / max(page.rect.width, page.rect.height))
    pixmap = page.get_pixmap(scale=scale, background=(255, 255, 255), clip=bbox)
    with Image.open(io.BytesIO(pixmap.tobytes())) as rendered:
        rgb = rendered.convert("RGB")
        rgb.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        rgb.save(output, format="PNG")
        data = output.getvalue()
        return "data:image/png;base64," + base64.b64encode(data).decode(), {
            "image_edge": edge,
            "image_size": list(rgb.size),
            "image_viewport": bbox,
            "image_sha256": sha(data),
            "image_bytes": len(data),
            "render_scale": scale,
            "full_page_raster_edge_cap": MAX_RASTER_EDGE,
        }


def raster_sources(
    page: Any, snapshot: dict[str, Any], edge: int = 1536
) -> tuple[dict[str, Any], set[str], dict[str, Any]]:
    """Propose pixel-derived physical grids without treating them as admitted tables."""
    from PIL import Image

    from bench.pipeline_dense_candidates import raster_vectors

    began, cpu = time.perf_counter(), time.process_time()
    scale = edge / max(page.rect.width, page.rect.height)
    data = page.render(scale=scale, background=(255, 255, 255))
    with Image.open(io.BytesIO(data)) as image:
        vectors = raster_vectors(image, list(page.rect))
    existing = snapshot.get("vector_candidates", [])

    def bounds(vector: dict[str, Any]) -> list[float]:
        cells = [b for b in vector["cells"] if b is not None]
        return [min(b[0] for b in cells), min(b[1] for b in cells), max(b[2] for b in cells), max(b[3] for b in cells)]

    additions = []
    for vector in vectors:
        box = bounds(vector)
        if not any(
            min(box[2], bounds(v)[2]) > max(box[0], bounds(v)[0])
            and min(box[3], bounds(v)[3]) > max(box[1], bounds(v)[1])
            for v in existing
        ):
            additions.append(vector)
    keys = {vector_identity(v) for v in additions}
    return (
        {**snapshot, "vector_candidates": [*existing, *additions]},
        keys,
        {
            "edge": edge,
            "image_sha256": sha(data),
            "proposed_grids": len(additions),
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "acceptance": "independent semantic gate and candidate selection required",
        },
    )


def vector_identity(vector: dict[str, Any]) -> str:
    """Preserve raster provenance after the region splitter strips extra fields."""
    return sha(
        json.dumps({k: vector[k] for k in ("row_count", "col_count", "cells", "spans")}, sort_keys=True).encode()
    )


def _request(
    client: DecisionClient | None,
    result: dict[str, Any],
    config: dict[str, Any],
    output: Path,
    region_id: str,
    prompt: str,
    choices: dict[str, str],
    url: str | None,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    if client is None:
        raise ValueError("Hosted region selection requires the coordinated metered client")
    request = baseline.body(model or config["model"], prompt, choices, url)
    if config.get("answer_tokens") and request["model"] in baseline.CHAT_MODELS:
        request["max_tokens"] = config["answer_tokens"]
    step = len(result["calls"])
    write_json(output / f"{result['id']}-request-{step}.json", request)
    response = baseline.call(client, request, f"P002/{config['run_id']}/{result['id']}/{region_id}/{step}")
    result["calls"].append(response)
    return response["answer"]


def generate_region(
    snapshot: dict[str, Any],
    bbox: list[float],
    url: str | None,
    config: dict[str, Any],
    output: Path,
    result: dict[str, Any],
    region_id: str,
    client: DecisionClient | None,
) -> dict[str, Any]:
    """Meter a fresh source-ID construction, preserving failed-call charges."""
    from bench.decision_hosted import accounted_cost
    from bench.pipeline_generation import parse, request

    if client is None:
        raise ValueError("Generative assembly requires the coordinated metered client")
    ledger = json.loads(client.ledger.read_bytes())
    spent = sum(accounted_cost(e["accounted_usd"]) for e in ledger["requests"] if e.get("tag", "").startswith("P002/"))
    if spent + 0.30 > baseline.WAVE_LIMIT:
        raise RuntimeError("P002 reservation would exceed its USD 50 wave cap")
    body = request(
        snapshot,
        config.get("generation_model", "anthropic/claude-sonnet-5.5"),
        url=url,
        viewport=bbox,
        max_tokens=config.get("generation_tokens", 8192),
    )
    step = len(result["calls"])
    write_json(output / f"{result['id']}-request-{step}.json", body)
    began, cpu = time.perf_counter(), time.process_time()
    response = client.request(
        body, tag=f"P002/{config['run_id']}/{result['id']}/{region_id}/{step}", max_body_bytes=750_000, replay=False
    )
    result["calls"].append(
        {
            "entry": response["entry"],
            "usage": response["result"].get("usage", {}),
            "replayed": response["replayed"],
            "kind": "source_id_generation",
            "client_wall_seconds": time.perf_counter() - began,
            "client_cpu_seconds": time.process_time() - cpu,
        }
    )
    return parse(snapshot, response["result"])


def select_region(
    region: dict[str, Any],
    page: Any,
    config: dict[str, Any],
    output: Path,
    result: dict[str, Any],
    client: DecisionClient | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Independently admit and assemble one source-derived region."""
    snapshot = region["source"]
    native = native_state(snapshot)
    info: dict[str, Any] = {"id": region["id"], "boundary": region["boundary"], "bbox": region["bbox"]}
    raster = native if region.get("kind") == "raster" else None
    if (native["tables"] and raster is None) or config["policy"] == "native":
        info["route"] = "native"
        return native, info
    if raster is not None:
        snapshot = {**snapshot, "vector_candidates": []}
    method = config.get("assembly_method", "select")
    if method == "generate":
        url, metadata = region_image(page, region["bbox"], config["image_edge"])
        info.update(metadata)
        state = generate_region(snapshot, region["bbox"], url, config, output, result, region["id"], client)
        info["route"] = "generated"
        return state, info
    candidates = propose(snapshot)
    if config.get("column_consensus", True):
        candidates = column_proposals(snapshot, candidates)
    if raster is not None:
        raster = {
            **raster,
            "id": f"c{len(candidates)}",
            "mechanism": "raster_rules",
            "description": "Preserve complete physical cells bounded by visible raster rules.",
        }
        candidates.append(raster)
    info["candidates"] = candidates
    if len(candidates) == 1 and method != "gated_generate":
        info["route"] = "no_alternative"
        return candidates[0], info
    url, metadata = region_image(page, region["bbox"], config["image_edge"])
    info.update(metadata)
    viewport = "Image viewport in global page coordinates: " + json.dumps(region["bbox"]) + ".\n" if url else ""
    prompt = viewport + admission_packet(snapshot, premise="relational", pixels_available=bool(url))
    choices = {
        "table": "This region has a shared record/attribute schema supporting table cells.",
        "prose": "This region contains prose, forms, formulas or other non-table content.",
        "unresolved": "Available source evidence cannot establish whether this region contains a table.",
    }
    answer = _request(client, result, config, output, region["id"], prompt, choices, url)
    probabilities = sorted(answer.get("probabilities", {}).values(), reverse=True)
    if config.get("gate_review_model") and probabilities and probabilities[0] < baseline.GATE_REVIEW_SCORE:
        info["gate_primary"] = answer
        answer = _request(
            client, result, config, output, region["id"], prompt, choices, url, model=config["gate_review_model"]
        )
    info["admission"] = answer
    if answer["choice"] != "table":
        info["route"] = "gated_out"
        return candidates[0], info
    if method == "gated_generate":
        state = generate_region(snapshot, region["bbox"], url, config, output, result, region["id"], client)
        info["route"] = "gated_generated"
        return state, info
    choices = {candidate["id"]: candidate["description"] for candidate in candidates}
    choices["unresolved"] = "No complete candidate faithfully represents this region; retain all source words."
    if config.get("readable_packet", True):
        evidence = readable_packet(snapshot, candidates, max_characters=config.get("packet_characters", 25_000))
    else:
        evidence = packet(snapshot, candidates)
    prompt = viewport + evidence
    answer = _request(client, result, config, output, region["id"], prompt, choices, url)
    info.update(route="selected", selection=answer)
    state = next((candidate for candidate in candidates if candidate["id"] == answer["choice"]), candidates[0])
    validate(snapshot, state)
    return state, info


def _table_bounds(snapshot: dict[str, Any], state: dict[str, Any]) -> None:
    lookup = {word["id"]: word for word in snapshot["words"]}
    for table in state["tables"]:
        boxes = [lookup[ident]["bbox"] for cell in table["cells"] for ident in cell["source_ids"]]
        if boxes:
            table["bbox"] = [
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes),
            ]


def process(
    record: dict[str, Any], config: dict[str, Any], output: Path, client: DecisionClient | None
) -> dict[str, Any]:
    """Extract and compose all regions, rejecting incomplete page output atomically."""
    import pylopdf
    from bench.pipeline_regions import compose, split

    started, cpu = time.perf_counter(), time.process_time()
    result: dict[str, Any] = {
        "id": record["id"],
        "status": "error",
        "tables": [],
        "calls": [],
        "stages": {},
        "regions": [],
    }
    try:
        data = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Frozen source PDF hash changed")
        with pylopdf.open(stream=data) as document:
            page = document[record["page_number"]]
            result["original_rotation"] = page.rotation
            if config.get("normalize_rotation", True) and page.rotation:
                page.set_rotation(0)
            snapshot = baseline.source(page)
            if not snapshot["words"] and config.get("ocr_empty", True):
                began = time.perf_counter()
                recognized = page.apply_ocr(dpi=config.get("ocr_dpi", 150), engine=baseline.ocr_engine())
                result["ocr"] = {
                    "engine": "RTen native CPU",
                    "threads": 4,
                    "dpi": config.get("ocr_dpi", 150),
                    "recognized_regions": len(recognized),
                    "wall_seconds": time.perf_counter() - began,
                }
                snapshot = baseline.source(page)
            if not snapshot["words"]:
                result["status"] = "unsupported_no_text"
                raise ValueError("No extracted or recognized source text")
            result["source"] = snapshot
            snapshot, result["native_warnings"] = sanitize_vectors(snapshot)
            result["stages"]["source_seconds"] = time.perf_counter() - started
            raster_keys: set[str] = set()
            if config.get("raster_rules") and config["policy"] != "native":
                snapshot, raster_keys, result["raster_rules"] = raster_sources(
                    page, snapshot, config.get("raster_edge", 1536)
                )
            plan = split(
                snapshot,
                max_words=config.get("region_words", 256),
                max_characters=config.get("region_characters", 8000),
            )
            for region in plan["regions"]:
                if any(vector_identity(v) in raster_keys for v in region["source"]["vector_candidates"]):
                    region["kind"] = "raster"
            result["region_plan"] = {k: v for k, v in plan.items() if k != "words"}
            states, rendered = {}, []
            order = {word["id"]: n for n, word in enumerate(snapshot["words"])}
            for region in plan["regions"]:
                state, info = select_region(region, page, config, output, result, client)
                states[region["id"]] = state
                info["state"] = state
                result["regions"].append(info)
                rendered.append(
                    (
                        min((order[i] for i in region["source_ids"]), default=len(order)),
                        baseline.markdown(region["source"], state),
                    )
                )
            state = compose(plan, states)
            _table_bounds(snapshot, state)
            result.update(
                tables=state["tables"], unresolved_ids=state["unresolved_ids"], source_conserved=True, route="regions"
            )
            (output / f"{record['id']}.md").write_text("\n".join(text for _, text in sorted(rendered)))
            write_json(output / f"{record['id']}-structure.json", state)
            result["status"] = "ok"
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        if isinstance(exc, (ValueError, KeyError)):
            result["error"] = str(exc)[:500]
    result.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu)
    write_json(output / f"{record['id']}-result.json", result)
    return result


def main() -> None:
    """Run a separately frozen P002 region treatment using the shared ledger."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy", choices=("native", "gated"), default="gated")
    parser.add_argument("--model", choices=baseline.MODELS, default=baseline.MODELS[0])
    parser.add_argument("--gate-review-model", choices=baseline.CHAT_MODELS)
    parser.add_argument("--image-edge", type=int, choices=(0, 128, 256, 400, 512, 768, 1024, 1200), default=512)
    parser.add_argument("--region-words", type=int, default=256)
    parser.add_argument("--region-characters", type=int, default=8000)
    parser.add_argument("--ocr-dpi", type=int, choices=(100, 150, 200, 300), default=150)
    parser.add_argument("--answer-tokens", type=int, choices=(1024, 2048, 4096), default=2048)
    parser.add_argument("--packet-characters", type=int, choices=(25000, 80000, 128000), default=25000)
    parser.add_argument("--assembly-method", choices=("select", "generate", "gated_generate"), default="select")
    parser.add_argument("--generation-model", choices=baseline.CHAT_MODELS, default="anthropic/claude-sonnet-5.5")
    parser.add_argument("--generation-tokens", type=int, choices=(4096, 8192, 16384), default=8192)
    parser.add_argument("--raster-rules", action="store_true")
    parser.add_argument("--raster-edge", type=int, choices=(1024, 1536, 2048), default=1536)
    parser.add_argument("--original-packet", action="store_true")
    parser.add_argument("--no-columns", action="store_true")
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    config = vars(args).copy()
    config.pop("manifest")
    config.pop("output")
    config.update(
        run_id=args.output.name,
        campaign="P002",
        processor="regions",
        order_seed=20261010,
        normalize_rotation=True,
        ocr_empty=True,
        column_consensus=not args.no_columns,
        readable_packet=not args.original_packet,
        context_rows=1,
        legend=True,
    )
    report = baseline.run(args.manifest, args.output, config)
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
