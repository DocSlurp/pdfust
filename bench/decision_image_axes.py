"""Freeze aspect-preserving image-axis/representation factorials without inference."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import time
from pathlib import Path
from typing import Any

from PIL import Image

from bench.decision_context_cases import context_cases
from bench.decision_hosted import ARTIFACTS, checkpoint
from bench.decision_image_matrix import MODES, VariantCache, png_format
from bench.decision_image_run import MODELS, admitted_batches, encode, verify_manifest
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss

SIZES = (200, 300, 400, 500, 600, 800)
AXES = ("width", "height", "longest")
REPRESENTATIONS = ("rgb8", "gray8", "pal4")
MAX_PIXELS = 8_000_000
MAX_IMAGE_BYTES = 512 * 1024
DEFAULT_DIRECTORY = ARTIFACTS / "image-axis-context30-v1"


def dimensions(width: int, height: int, target: int, axis: str) -> tuple[int, int]:
    """Scale the declared axis exactly while preserving aspect ratio within rounding."""
    if min(width, height, target) <= 0 or isinstance(target, bool) or axis not in AXES:
        message = "Positive dimensions and a declared target axis are required"
        raise ValueError(message)
    denominator = {"width": width, "height": height, "longest": max(width, height)}[axis]
    ratio = target / denominator
    return max(1, round(width * ratio)), max(1, round(height * ratio))


def variant_image(  # noqa: PLR0913, C901
    raster: Image.Image,
    bbox: list[float],
    directory: Path,
    *,
    target: int,
    axis: str,
    mode: str,
    fixed_partner: int | None = None,
) -> dict[str, Any]:
    """Encode exactly the admitted dimensions; refuse rather than silently resizing."""
    if mode not in REPRESENTATIONS:
        message = "Undeclared image representation"
        raise ValueError(message)
    size = dimensions(raster.width, raster.height, target, axis)
    if fixed_partner is not None:
        if axis not in {"width", "height"} or fixed_partner <= 0:
            message = "Anisotropic arm needs width/height and a positive fixed partner"
            raise ValueError(message)
        size = (target, fixed_partner) if axis == "width" else (fixed_partner, target)
    if math.prod(size) > MAX_PIXELS:
        message = "Requested image exceeds total-pixel admission"
        raise ValueError(message)
    if size[0] > raster.width or size[1] > raster.height:
        message = "Requested axis needs a larger native base; upscaling refused"
        raise ValueError(message)
    image = raster.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    if mode == "gray8":
        image = image.convert("L")
    elif mode == "pal4":
        image = image.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True, **({"bits": 4} if mode == "pal4" else {}))
    data = buffer.getvalue()
    if len(data) > MAX_IMAGE_BYTES:
        message = "Encoded PNG exceeds payload admission"
        raise ValueError(message)
    if png_format(data) != MODES[mode]:
        message = "Encoded PNG representation differs from declared arm"
        raise ValueError(message)
    digest = hashlib.sha256(data).hexdigest()
    path = directory / f"pixels-{digest}.png"
    if not path.exists():
        path.write_bytes(data)
    return {
        "data": data,
        "mime": "image/png",
        "pixels": list(size),
        "total_pixels": math.prod(size),
        "bytes": len(data),
        "sha256": digest,
        "path": str(path),
        "bbox": bbox,
        "source_aspect_ratio": raster.width / raster.height,
        "actual_aspect_ratio": size[0] / size[1],
        "target_axis": axis,
        "target_size": target,
        "mode": mode,
        "blank": False,
        "png_bit_depth": png_format(data)[0],
        "png_color_type": png_format(data)[1],
        "base_pixels": list(raster.size),
        "resample": "LANCZOS; no enlargement",
        "anisotropic": fixed_partner is not None,
        "fixed_partner_pixels": fixed_partner,
        "dither": "NONE",
    }


def prepare(directory: Path, *, scope: str = "page", distort_axis_sweep: bool = False) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Freeze all axis/size/representation requests before postfreeze scoring or paid calls."""
    directory = guard_path(directory)
    if scope not in {"page", "region"}:
        message = "Scope must be page or region"
        raise ValueError(message)
    if (directory / "manifest.json").exists():
        manifest = json.loads((directory / "manifest.json").read_text())
        if manifest["scope"] != scope or manifest.get("distort_axis_sweep", False) != distort_axis_sweep:
            message = "Frozen scope differs; choose a new directory"
            raise ValueError(message)
        verify_manifest(directory, manifest)
        return manifest
    began, cpu = time.perf_counter(), time.process_time()
    directory.mkdir(parents=True, exist_ok=True)
    images_dir = directory / "images"
    cache = VariantCache(images_dir)
    # The existing authored source factory returns scorer metadata alongside evidence.
    # Project it away immediately; this preparation never reads its values.
    cases = [{k: v for k, v in case.items() if k in {"id", "pdf_bytes", "evidence"}} for case in context_cases()]
    source_rows: list[dict[str, Any]] = []
    bases: dict[str, tuple[Image.Image, dict[str, Any]]] = {}
    refusals: list[dict[str, Any]] = []
    for case in cases:
        pdf_hash = hashlib.sha256(case["pdf_bytes"]).hexdigest()
        (directory / f"source-{pdf_hash}.pdf").write_bytes(case["pdf_bytes"])
        source_rows.append({"id": case["id"], "source_sha256": pdf_hash, "evidence": case["evidence"]})
        bbox = None if scope == "page" else case["evidence"]["current_region"]
        try:
            bases[case["id"]] = cache._base(case["pdf_bytes"], bbox, 0)  # noqa: SLF001
        except ValueError as error:
            refusals.append({"case_id": case["id"], "scope": scope, "stage": "native_base", "reason": str(error)})
    checkpoint(directory / "source-frozen.json", {"pages": source_rows})
    batches: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    aliases: list[dict[str, Any]] = []
    actual_images: list[dict[str, Any]] = []
    configurations: list[dict[str, Any]] = [
        {"mode": mode, "target": target, "axis": axis, "fixed_partner": None}
        for mode in REPRESENTATIONS
        for target in SIZES
        for axis in AXES
    ]
    if distort_axis_sweep:
        configurations += [
            {"mode": mode, "target": target, "axis": axis, "fixed_partner": 512}
            for mode in REPRESENTATIONS
            for target in (200, 300, 400, 500)
            for axis in ("width", "height")
        ]
    for configuration in configurations:
        mode, target, axis = configuration["mode"], configuration["target"], configuration["axis"]
        fixed_partner = configuration["fixed_partner"]
        arm = f"{mode}-{axis}-{target}" + (f"-anisotropic-fixed{fixed_partner}" if fixed_partner else "")
        selected, variants = [], []
        for index, case in enumerate(cases):
            if case["id"] not in bases:
                continue
            raster, metadata = bases[case["id"]]
            try:
                image = variant_image(
                    raster,
                    metadata["bbox"],
                    images_dir,
                    target=target,
                    axis=axis,
                    mode=mode,
                    fixed_partner=fixed_partner,
                )
            except ValueError as error:
                refusals.append(
                    {
                        "case_id": case["id"],
                        "arm": arm,
                        "scope": scope,
                        "stage": "variant",
                        "reason": str(error),
                    }
                )
                continue
            image = {**image, "source_sha256": metadata["identity"]["source_sha256"]}
            actual_images.append({"case_id": case["id"], "arm": arm, **{k: v for k, v in image.items() if k != "data"}})
            selected.append((index, case))
            variants.append(image)
        # Provider admission is reused with one observation at a time before batching,
        # so a single honest refusal does not discard other cases in this arm.
        for model in MODELS:
            admitted: list[tuple[int, dict[str, Any]]] = []
            admitted_images: list[dict[str, Any] | None] = []
            for pair, image in zip(selected, variants, strict=True):
                try:
                    admitted_batches([pair[1]], [image], model, silver=False)
                except ValueError as error:
                    refusals.append(
                        {
                            "case_id": pair[1]["id"],
                            "arm": arm,
                            "model": model,
                            "scope": scope,
                            "stage": "provider_payload",
                            "reason": str(error),
                        }
                    )
                    continue
                admitted.append(pair)
                admitted_images.append(image)
            provider = admitted_batches([p[1] for p in admitted], admitted_images, model, silver=False)
            for offset, chosen, encoded_images, body in provider:
                data = encode(body)
                digest = hashlib.sha256(data).hexdigest()
                identity = {
                    "model": model,
                    "scope": scope,
                    "arm": arm,
                    "offset": admitted[offset][0],
                    "case_indices": [p[0] for p in admitted[offset : offset + len(chosen)]],
                    "case_ids": [case["id"] for case in chosen],
                }
                if digest in seen:
                    aliases.append(
                        {
                            **identity,
                            "canonical_arm": seen[digest]["arm"],
                            "request_sha256": digest,
                            "reason": "identical geometry/source/pixels/body; "
                            "one frozen request, not provider cache evidence",
                        }
                    )
                    continue
                name = f"request-{digest}.json"
                (directory / name).write_bytes(data)
                batch = {
                    **identity,
                    "configuration": configuration,
                    "source_sha256": [hashlib.sha256(c["pdf_bytes"]).hexdigest() for c in chosen],
                    "request_sha256": digest,
                    "request_file": name,
                    "request_bytes": len(data),
                    "images": [
                        {k: v for k, v in image.items() if k != "data"} for image in encoded_images if image is not None
                    ],
                }
                batches.append(batch)
                seen[digest] = batch
    rss, rss_tool = process_peak_rss()
    manifest = {
        "schema": 1,
        "models": list(MODELS),
        "scope": scope,
        "silver_directory": None,
        "task": "context-assembly",
        "distort_axis_sweep": distort_axis_sweep,
        "batches": batches,
        "prices": {},
        "pricing_provenance": {},
        "geometric_aliases": aliases,
        "refusals": refusals,
        "declared_sizes": list(SIZES),
        "declared_axes": list(AXES),
        "declared_representations": list(REPRESENTATIONS),
        "source_sha256": hashlib.sha256((directory / "source-frozen.json").read_bytes()).hexdigest(),
        "preparation": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss,
            "measurement": f"{rss_tool}; SELF perf_counter/process_time; "
            "single CPU process; no children or periodic sampling",
        },
        "code_sha256": {str(Path(__file__)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "dev_status": "30 authored DEV cases; ten correlated templates across three vocabularies; "
        "scorer references excluded from freeze",
        "evidence_exact": "not validated for transformed images",
        "admission": {
            "max_pixels": MAX_PIXELS,
            "max_image_bytes": MAX_IMAGE_BYTES,
            "no_implicit_resize": True,
            "no_upscale": True,
        },
    }
    checkpoint(directory / "actual-images.json", {"images": actual_images})
    checkpoint(directory / "manifest.json", manifest)
    verify_manifest(directory, manifest)
    return manifest


def main() -> None:
    """Prepare only; the existing image runner owns explicitly authorized execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--scope", choices=["page", "region"], default="page")
    parser.add_argument("--distort-axis-sweep", action="store_true")
    args = parser.parse_args()
    manifest = prepare(args.directory, scope=args.scope, distort_axis_sweep=args.distort_axis_sweep)
    print(
        json.dumps(
            {
                "directory": str(args.directory),
                "batches": len(manifest["batches"]),
                "geometric_alias_batches": len(manifest["geometric_aliases"]),
                "refusals": len(manifest["refusals"]),
                "preparation": manifest["preparation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
