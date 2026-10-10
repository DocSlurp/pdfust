"""Metered image-only table transcription control; no OCR or reference loading."""

# Explicit retained experiment dictionaries are heterogeneous.
# ruff: noqa: ANN401, EM101, TRY003, PLC0415, TRY301
from __future__ import annotations

import argparse
import base64
import io
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench import pipeline_run as baseline
from bench import pipeline_vision_transcription as adapter
from bench.pipeline_frontier import MODELS
from bench.silver import guard_path, sha, write_json

if TYPE_CHECKING:
    from bench.decision_hosted import DecisionClient

MAX_REQUESTS = 32
MAX_BODY_BYTES = 750_000
IMAGE_EDGES = (400, 512, 768, 1024, 1200, 2048)


def image(page: Any, edge: int, quality: int = 90) -> tuple[str, dict[str, Any]]:
    """Render one whole display page as explicit RGB JPEG without changing rotation."""
    from PIL import Image

    if type(edge) is not int or edge not in IMAGE_EDGES:
        raise ValueError("Vision image edge is outside the frozen choices")
    if type(quality) is not int or quality not in (50, 70, 90):
        raise ValueError("Vision JPEG quality is outside the frozen choices")
    viewport = list(page.rect)
    adapter._viewport(viewport)  # noqa: SLF001 - reuse the strict adapter display admission.
    scale = edge / max(page.rect.width, page.rect.height)
    with Image.open(io.BytesIO(page.render(scale=scale, background=(255, 255, 255)))) as rendered:
        rgb = rendered.convert("RGB")
        # Remove at most raster rounding; never adapt edge or quality to body admission.
        rgb.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        stream = io.BytesIO()
        rgb.save(stream, format="JPEG", quality=quality)
        data = stream.getvalue()
        metadata = {
            "image_codec": "JPEG",
            "image_mode": "RGB",
            "image_quality": quality,
            "image_edge": edge,
            "image_size": list(rgb.size),
            "image_viewport": viewport,
            "image_sha256": sha(data),
            "image_bytes": len(data),
            "render_scale": scale,
            "whole_page": True,
            "body_limit_adaptation": False,
        }
    return "data:image/jpeg;base64," + base64.b64encode(data).decode(), metadata


def _ledger(client: DecisionClient) -> list[dict[str, Any]]:
    return json.loads(client.ledger.read_bytes())["requests"] if client.ledger.exists() else []


def _transcribe(  # noqa: PLR0913 - indexed retained transport preserves default behavior
    client: DecisionClient | None,
    body: dict[str, Any],
    config: dict[str, Any],
    result: dict[str, Any],
    output: Path,
    *,
    request_index: int = 0,
) -> dict[str, Any]:
    """Retain metering and the raw response before any transcription parsing."""
    from bench.decision_hosted import accounted_cost

    if type(request_index) is not int or not 0 <= request_index < MAX_REQUESTS:
        raise ValueError("Vision request index exceeds admission")
    write_json(output / f"{result['id']}-request-{request_index}.json", body)
    encoded = json.dumps(body, separators=(",", ":")).encode()
    result["request"] = {
        "body_sha256": sha(encoded),
        "body_bytes": len(encoded),
        "max_body_bytes": MAX_BODY_BYTES,
        "model": body["model"],
        "max_tokens": body["max_tokens"],
        "replay": False,
    }
    if len(encoded) > MAX_BODY_BYTES:
        raise ValueError("Vision request exceeds the frozen 750000-byte body admission; no resize or retry")
    if client is None:
        raise ValueError("Vision transcription requires the coordinated metered client")
    previous = _ledger(client)
    spent = sum(accounted_cost(row["accounted_usd"]) for row in previous if row.get("tag", "").startswith("P002/"))
    reservation = 1.0 if body["model"] == "anthropic/claude-opus-5.5" else 0.30
    if spent + reservation > baseline.WAVE_LIMIT:
        raise RuntimeError("P002 reservation would exceed its USD 50 wave cap")
    tag = f"P002/{config['run_id']}/{result['id']}/vision/{request_index}"
    before_indexes = {row["index"] for row in previous if "index" in row}
    began, cpu = time.perf_counter(), time.process_time()
    try:
        response = client.request(
            body, tag=tag, max_body_bytes=MAX_BODY_BYTES, replay=False, reservation_usd=reservation
        )
    except Exception:
        # The shared client retains charged reservations on transport failure.
        # Preserve them locally without provider error bodies or exception text.
        for entry in _ledger(client):
            if entry.get("tag") == tag and entry.get("index") not in before_indexes:
                result["calls"].append(
                    {
                        "entry": entry,
                        "usage": {},
                        "replayed": False,
                        "kind": "vision_transcription",
                        "status": "transport_error",
                        "client_wall_seconds": time.perf_counter() - began,
                        "client_cpu_seconds": time.process_time() - cpu,
                    }
                )
        write_json(output / f"{result['id']}-result.json", result)
        raise
    result["calls"].append(
        {
            "entry": response["entry"],
            "usage": response["result"].get("usage", {}),
            "replayed": response["replayed"],
            "kind": "vision_transcription",
            "client_wall_seconds": time.perf_counter() - began,
            "client_cpu_seconds": time.process_time() - cpu,
        }
    )
    result["transcription_response"] = response["result"]
    write_json(output / f"{result['id']}-response-{request_index}.json", response["result"])
    write_json(output / f"{result['id']}-result.json", result)
    return response["result"]


def process(
    record: dict[str, Any], config: dict[str, Any], output: Path, client: DecisionClient | None
) -> dict[str, Any]:
    """Transcribe a whole source page's tables and refuse malformed output atomically."""
    import pylopdf

    began, cpu = time.perf_counter(), time.process_time()
    result: dict[str, Any] = {
        "id": record["id"],
        "status": "error",
        "tables": [],
        "calls": [],
        "unresolved_ids": [],
        "route": "vision_transcription",
        "source_conserved": False,
        "text_provenance": adapter.PROVENANCE,
        "output_scope": "table_only",
        "stages": {},
    }
    stage = "input"
    try:
        if config.get("campaign", "P002") != "P002":
            raise ValueError("Vision control belongs to the P002 campaign")
        data = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Frozen source PDF hash changed")
        result["pdf_sha256"] = sha(data)
        stage = "render"
        with pylopdf.open(stream=data) as document:
            page = document[record["page_number"]]
            result.update(original_rotation=page.rotation, rotation_normalized=False, viewport=list(page.rect))
            url, metadata = image(page, config.get("image_edge", 1200), config.get("jpeg_quality", 90))
            result["image"] = metadata
        result["stages"]["render_seconds"] = time.perf_counter() - began
        stage = "request"
        body = adapter.request(
            config.get("generation_model", MODELS[1]),
            url,
            result["viewport"],
            max_tokens=config.get("generation_tokens", 16384),
        )
        response = _transcribe(client, body, config, result, output)
        stage = "parse"
        parsed = adapter.parse(response, result["viewport"])
        rendered = adapter.markdown(parsed)
        # Construct both complete artifacts before publishing any admitted table.
        write_json(output / f"{record['id']}-structure.json", parsed)
        (output / f"{record['id']}.md").write_text(rendered)
        result.update(tables=parsed["tables"], status="ok")
    except Exception as error:
        result.update(error_type=type(error).__name__, error_stage=stage)
        if isinstance(error, ValueError):
            result["error"] = str(error)[:500]
    result.update(wall_seconds=time.perf_counter() - began, cpu_seconds=time.process_time() - cpu)
    write_json(output / f"{record['id']}-result.json", result)
    return result


def main() -> None:
    """Run a separately frozen P002 table-only image comparator through shared metering."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--generation-model", choices=MODELS, default=MODELS[1])
    parser.add_argument("--image-edge", type=int, choices=IMAGE_EDGES, default=1200)
    parser.add_argument("--jpeg-quality", type=int, choices=(50, 70, 90), default=90)
    parser.add_argument("--detector-crops", action="store_true", help="Fixed 400/512/768/1024/2048-pixel table crops")
    parser.add_argument("--generation-tokens", type=int, choices=(4096, 8192, 16384), default=16384)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    if args.detector_crops and args.image_edge not in (400, 512, 768, 1024, 2048):
        parser.error("Detector crops require --image-edge 400/512/768/1024/2048")
    config = vars(args).copy()
    config.pop("manifest")
    config.pop("output")
    config.update(
        run_id=args.output.name,
        processor="vision_regions" if args.detector_crops else "vision",
        layout_detector="yolo" if args.detector_crops else "none",
        campaign="P002",
        policy="gated",
        model=args.generation_model,
        order_seed=20261010,
        normalize_rotation=False,
        ocr_empty=False,
        output_scope="table_only",
    )
    report = baseline.run(args.manifest, args.output, config)
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
