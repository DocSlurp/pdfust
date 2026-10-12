"""CPU-only fresh PDF crop size treatments; never reads scorer references."""

# ruff: noqa: C901, PLR0912 - complete frozen inventories are verified explicitly.

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import resource
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from PIL import Image
from PIL import __version__ as pillow_version

from bench.remote_prompt_packets import MAX_BODY_BYTES, _digest, _encode, _fail, _inside, _read, _safe

EDGES = (128, 256, 384, 400, 448, 500, 640)
MODES = ("rgb", "gray", "lowbit")
SOURCE_COUNT = 24
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_RASTER_PIXELS = 32_000_000
BBOX_COORDINATES = 4
ALLOWED_METADATA = ("image_pixels", "image_mode", "png_bit_depth")


def renderer_runtime() -> dict[str, str]:
    """Pin the installed native renderer bytes alongside published versions."""
    import pdfust  # noqa: PLC0415

    native_file = sys.modules[pdfust._Document.__module__].__file__  # noqa: SLF001
    if native_file is None:
        _fail("Native renderer module has no reproducible source file")
    native = Path(cast("str", native_file))
    return {
        "pdfust_version": pdfust.__version__,
        "native_module_sha256": _digest(_read(native, 128 * 1024 * 1024)),
        "pillow_version": pillow_version,
    }


def raster(source: Path, bbox: list[float], edge: int) -> tuple[Image.Image, dict[str, Any]]:
    """Fresh hayro clip and downsample with the same L015 raster contract."""
    import pdfust  # noqa: PLC0415

    if edge not in EDGES or len(bbox) != BBOX_COORDINATES or not all(math.isfinite(value) for value in bbox):
        _fail("Unadmitted fresh crop size/coordinates")
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if min(width, height) <= 0:
        _fail("Empty source crop")
    scale = (edge + 2) / max(width, height)
    with pdfust.Document(_safe(source)) as document:
        page = document[0]
        rect = page.rect
        if math.ceil(rect.width * scale) * math.ceil(rect.height * scale) > MAX_RASTER_PIXELS:
            _fail("Fresh source render exceeds pixel admission")
        pix = page.get_pixmap(scale=scale, clip=bbox)
        rgba = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    rgb = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")
    pixels = [max(1, round(width / max(width, height) * edge)), max(1, round(height / max(width, height) * edge))]
    if rgb.width < pixels[0] or rgb.height < pixels[1]:
        _fail("Fresh source crop would require upscaling")
    metadata = {
        "bbox": bbox,
        "page_index": 0,
        "requested_edge": edge,
        "render_scale": scale,
        "render_pixels": list(rgb.size),
        "pixels": pixels,
        "render_display_bbox": [
            math.floor(bbox[0] * scale) / scale,
            math.floor(bbox[1] * scale) / scale,
            math.ceil(bbox[2] * scale) / scale,
            math.ceil(bbox[3] * scale) / scale,
        ],
        "resampling": "fresh hayro crop at (edge+2)/longest bbox edge; white alpha composite; LANCZOS downsample",
    }
    return rgb.resize((pixels[0], pixels[1]), Image.Resampling.LANCZOS), metadata


def variant(rgb: Image.Image, mode: str) -> bytes:
    """Encode the same RGB8/gray8/four-level two-bit PNG treatments as L015."""
    if mode not in MODES:
        _fail("Unadmitted image mode")
    bitmap = rgb if mode == "rgb" else rgb.convert("L")
    if mode == "lowbit":
        bitmap = bitmap.point([(value * 3 + 127) // 255 for value in range(256)]).convert("P")
        bitmap.putpalette([channel for index in range(256) for channel in [min(index, 3) * 85] * 3])
    output = io.BytesIO()
    bitmap.save(output, format="PNG", optimize=True, **({"bits": 2} if mode == "lowbit" else {}))
    return output.getvalue()


def project(template: dict[str, Any], png: bytes, pixels: list[int], mode: str) -> dict[str, Any]:
    """Change only explicitly admitted image metadata and image transport."""
    result = deepcopy(template)
    state = json.loads(result["state"][0])
    state.update(image_pixels=pixels, image_mode=mode, png_bit_depth=png[24])
    result["state"] = [
        json.dumps(state, separators=(",", ":")),
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}},
    ]
    assert_projection(template, result)
    if len(_encode(result)) > MAX_BODY_BYTES:
        _fail("Fresh image request exceeds admission; no truncation")
    return result


def assert_projection(original: dict[str, Any], projected: dict[str, Any]) -> None:
    """Reject modified literal observations, questions or any unlisted metadata."""
    if len(original["state"]) != 2 or len(projected["state"]) != 2:  # noqa: PLR2004
        _fail("Exactly one literal state and image required")
    before, after = json.loads(original["state"][0]), json.loads(projected["state"][0])
    for key in ALLOWED_METADATA:
        if key not in before or key not in after:
            _fail("Source image metadata is incomplete")
        after[key] = before[key]
    probe = deepcopy(projected)
    probe["state"] = original["state"]
    if after != before or probe != original:
        _fail("Fresh image projection changed source text/questions or unlisted metadata")


def _sources(source: Path, packets: Path, index_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Verify complete public source artifacts, then bind the first 24 RGB512 packets."""
    manifest = json.loads(_read(source / "manifest.json", MAX_ARTIFACT_BYTES))
    if manifest.get("experiment") != "L015" or len(manifest["pages"]) != SOURCE_COUNT:
        _fail("Fresh sizes require the exact 24-source L015 freeze")
    pages = {page["id"]: page for page in manifest["pages"]}
    for page in pages.values():
        for key, digest in (("source_file", "source_sha256"), ("observation_file", "observation_sha256")):
            if _digest(_read(_inside(source, page[key]), MAX_ARTIFACT_BYTES)) != page[digest]:
                _fail("Frozen source PDF/observation hash mismatch")
    for record in manifest["records"]:
        if _digest(_read(_inside(source, record["request"]), MAX_BODY_BYTES)) != record["sha256"]:
            _fail("Frozen source request hash mismatch")
        if _digest(_read(_inside(source, record["image_file"]), MAX_BODY_BYTES)) != record["image_sha256"]:
            _fail("Frozen source image hash mismatch")
    staged = json.loads(_read(packets / "manifest.json", MAX_ARTIFACT_BYTES))["records"][:SOURCE_COUNT]
    indexed = json.loads(_read(index_path, MAX_ARTIFACT_BYTES))[:SOURCE_COUNT]
    if len(staged) != SOURCE_COUNT or len(indexed) != SOURCE_COUNT:
        _fail("Incomplete first-24 source packet inventory")
    sources = []
    for worker, entry in zip(staged, indexed, strict=True):
        originals = [{key: value for key, value in entry.items() if key != "id"}]
        if worker["id"] != entry["id"] or entry["arm"] != "fresh-rgb-512" or originals[0] not in manifest["records"]:
            _fail("Source index differs from original RGB512 records")
        raw = _read(_inside(packets, worker["request_file"]), MAX_BODY_BYTES)
        image = _read(_inside(packets, worker["image_files"][0]), MAX_BODY_BYTES)
        if _digest(raw) != entry["sha256"] or _digest(image) != entry["image_sha256"]:
            _fail("Staged source request/image differs from freeze")
        template = json.loads(raw)
        if template["state"][1] != {
            "type": "image_url",
            "image_url": {"url": "data:image/png;base64," + base64.b64encode(image).decode()},
        }:
            _fail("Original source image transport mismatch")
        page = pages[entry["page_ids"][0]]
        observation = json.loads(_read(_inside(source, page["observation_file"]), MAX_ARTIFACT_BYTES))
        sources.append(
            {
                "worker": worker,
                "entry": entry,
                "page": page,
                "template": template,
                "bbox": observation["images"]["crop512"]["bbox"],
            }
        )
    if len({item["page"]["id"] for item in sources}) != SOURCE_COUNT:
        _fail("Duplicate source page selection")
    return manifest, sources


def prepare(source: Path, packets: Path, index: Path, destination: Path) -> dict[str, Any]:
    """Freeze a complete source-major matrix without reading references or answers."""
    started, cpu = time.perf_counter(), time.process_time()
    source, packets, index, destination = map(_safe, (source, packets, index, destination))
    if destination in (source, packets):
        _fail("Projection cannot replace an original freeze")
    _, sources = _sources(source, packets, index)
    files: dict[str, bytes] = {}
    records, mapping = [], []
    for item in sources:
        entry, page = item["entry"], item["page"]
        for edge in EDGES:
            rgb, metadata = raster(_inside(source, page["source_file"]), item["bbox"], edge)
            for mode in MODES:
                png = variant(rgb, mode)
                request = project(item["template"], png, metadata["pixels"], mode)
                raw = _encode(request)
                identity = _digest(_encode(["fresh-size-v1", entry["id"], edge, mode, _digest(raw)]))[:24]
                image_name, request_name = identity + ".png", identity + ".json"
                files[image_name], files[request_name] = png, raw
                records.append({"id": identity, "request_file": request_name, "image_files": [image_name]})
                mapping.append(
                    {
                        "id": identity,
                        "source_id": entry["id"],
                        "page_id": page["id"],
                        "arm": f"fresh-{mode}-{edge}",
                        "source_request_sha256": entry["sha256"],
                        "source_pdf_sha256": page["source_sha256"],
                        "source_observation_sha256": page["observation_sha256"],
                        "original_image_sha256": entry["image_sha256"],
                        "projected_request_sha256": _digest(raw),
                        "image_file": image_name,
                        "image_sha256": _digest(png),
                        "png_bytes": len(png),
                        "png_bit_depth": png[24],
                        "image_mode": mode,
                        "body_bytes": len(raw),
                        **metadata,
                    }
                )
    worker_manifest = {"records": records}
    provenance = {
        "schema": 1,
        "experiment": "source-only-fresh-size-screen",
        "source_directory": str(source),
        "source_packets": str(packets),
        "source_index": str(index),
        "source_manifest_sha256": _digest(_read(source / "manifest.json", MAX_ARTIFACT_BYTES)),
        "source_packet_manifest_sha256": _digest(_read(packets / "manifest.json", MAX_ARTIFACT_BYTES)),
        "source_index_sha256": _digest(_read(index, MAX_ARTIFACT_BYTES)),
        "worker_manifest_sha256": _digest(_encode(worker_manifest)),
        "builder_sha256": _digest(_read(Path(__file__), MAX_ARTIFACT_BYTES)),
        "pillow_version": pillow_version,
        "renderer_runtime": renderer_runtime(),
        "edges": list(EDGES),
        "modes": list(MODES),
        "source_selection": "exact first24 original staged RGB512 records; no quality selection",
        "allowed_changed_fields": [*ALLOWED_METADATA, "state image_url bytes"],
        "source_count": SOURCE_COUNT,
        "body_count": len(records),
        "mapping": mapping,
        "scoring": "requires separately approved constrained source-image projection; no references read",
    }
    files.update({"manifest.json": _encode(worker_manifest), "provenance.json": _encode(provenance)})
    if destination.exists():
        if not (destination / "manifest.json").exists() and any(destination.iterdir()):
            _fail("Destination is not empty or an existing matching freeze")
        for name, raw in files.items():
            path = _inside(destination, name)
            if path.exists() and _read(path, MAX_ARTIFACT_BYTES) != raw:
                _fail("Refuse to overwrite differing frozen artifacts")
    destination.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        path = _inside(destination, name)
        if not path.exists():
            path.write_bytes(raw)
    # Resource observations are a sidecar, separate from deterministic frozen bytes.
    preparation_path = destination / "preparation.json"
    if not preparation_path.exists():
        preparation_path.write_text(
            json.dumps(
                {
                    "wall_seconds": time.perf_counter() - started,
                    "cpu_seconds": time.process_time() - cpu,
                    "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                    "scope": "serial CPU process; perf_counter/process_time; Linux getrusage lifetime RSS, no sampling",
                },
                indent=2,
            )
            + "\n"
        )
    return provenance


def verify(directory: Path) -> dict[str, Any]:
    """Verify full source/image/request provenance before any scorer may read gold."""
    directory = _safe(directory)
    provenance = json.loads(_read(directory / "provenance.json", MAX_ARTIFACT_BYTES))
    if (
        provenance["edges"] != list(EDGES)
        or provenance["modes"] != list(MODES)
        or provenance["allowed_changed_fields"] != [*ALLOWED_METADATA, "state image_url bytes"]
        or provenance["source_count"] != SOURCE_COUNT
        or provenance["body_count"] != SOURCE_COUNT * len(EDGES) * len(MODES)
        or provenance["pillow_version"] != pillow_version
        or provenance["renderer_runtime"] != renderer_runtime()
    ):
        _fail("Projection policy or raster runtime differs from frozen contract")
    source, packets, index = map(
        _safe, (Path(provenance[key]) for key in ("source_directory", "source_packets", "source_index"))
    )
    for path, key in (
        (source / "manifest.json", "source_manifest_sha256"),
        (packets / "manifest.json", "source_packet_manifest_sha256"),
        (index, "source_index_sha256"),
    ):
        if _digest(_read(path, MAX_ARTIFACT_BYTES)) != provenance[key]:
            _fail("Parent freeze hash changed")
    _, sources = _sources(source, packets, index)
    originals = {item["entry"]["id"]: item for item in sources}
    raw_manifest = _read(directory / "manifest.json", MAX_ARTIFACT_BYTES)
    if _digest(raw_manifest) != provenance["worker_manifest_sha256"]:
        _fail("Projected worker manifest changed")
    records = json.loads(raw_manifest)["records"]
    expected = [(item["entry"]["id"], edge, mode) for item in sources for edge in EDGES for mode in MODES]
    if len(records) != len(expected) or len(provenance["mapping"]) != len(expected):
        _fail("Incomplete projected matrix")
    rendered_key = None
    rgb = None
    metadata: dict[str, Any] = {}
    for record, mapping, (source_id, edge, mode) in zip(records, provenance["mapping"], expected, strict=True):
        if (
            record["id"] != mapping["id"]
            or mapping["source_id"] != source_id
            or mapping["arm"] != f"fresh-{mode}-{edge}"
        ):
            _fail("Projected inventory/order differs from declared source matrix")
        png = _read(_inside(directory, record["image_files"][0]), MAX_BODY_BYTES)
        raw = _read(_inside(directory, record["request_file"]), MAX_BODY_BYTES)
        if _digest(png) != mapping["image_sha256"] or _digest(raw) != mapping["projected_request_sha256"]:
            _fail("Projected request/image changed")
        with Image.open(io.BytesIO(png)) as bitmap:
            if list(bitmap.size) != mapping["pixels"] or max(bitmap.size) != edge or bitmap.format != "PNG":
                _fail("Projected pixels mismatch")
        item = originals[source_id]
        page, entry = item["page"], item["entry"]
        if (
            mapping["bbox"] != item["bbox"]
            or mapping["source_pdf_sha256"] != page["source_sha256"]
            or mapping["source_observation_sha256"] != page["observation_sha256"]
            or mapping["source_request_sha256"] != entry["sha256"]
            or mapping["original_image_sha256"] != entry["image_sha256"]
            or mapping["page_id"] != page["id"]
        ):
            _fail("Source crop provenance changed")
        if rendered_key != (source_id, edge):
            rgb, metadata = raster(_inside(source, page["source_file"]), item["bbox"], edge)
            rendered_key = (source_id, edge)
        if rgb is None:
            message = "Fresh raster cache is unexpectedly empty"
            raise ValueError(message)
        if any(mapping[key] != value for key, value in metadata.items()) or png != variant(rgb, mode):
            _fail("Projected PNG differs from fresh source rendering")
        if raw != _encode(project(item["template"], png, mapping["pixels"], mode)):
            _fail("Projection changed source text/questions or image metadata")
        identity = _digest(_encode(["fresh-size-v1", source_id, edge, mode, _digest(raw)]))[:24]
        if record != {"id": identity, "request_file": identity + ".json", "image_files": [identity + ".png"]}:
            _fail("Projected opaque identity/file inventory changed")
        if (
            mapping["image_file"] != identity + ".png"
            or mapping["png_bit_depth"] != png[24]
            or mapping["png_bytes"] != len(png)
            or mapping["body_bytes"] != len(raw)
            or mapping["image_mode"] != mode
        ):
            _fail("Projected payload metadata changed")
    return provenance


def main() -> None:
    """Prepare or verify locally; no inference entry point exists."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--packets", type=Path)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = (
        verify(args.destination) if args.verify else prepare(args.source, args.packets, args.index, args.destination)
    )
    print(json.dumps({key: result[key] for key in ("source_count", "body_count")}))


if __name__ == "__main__":
    main()
