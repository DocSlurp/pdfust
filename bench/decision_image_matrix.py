"""Freeze CPU-only image resolution and bit-depth DEV request ablations.

No credentials or hosted client are imported. Labels remain scorer-only metadata.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import time
from pathlib import Path
from typing import Any

from PIL import Image

import pdfust
from bench.decision_context_cases import context_cases, evidence_modes
from bench.decision_context_compact import make_request
from bench.decision_images import MAX_PDF_BYTES, digest
from bench.silver import rss_bytes

SCHEMA = 1
BASE_EDGE = 1200
EDGES = (128, 512, 1200)
MODES = {"rgb8": (8, 2), "gray8": (8, 0), "gray4": (4, 3), "mono1": (1, 0), "pal4": (4, 3)}
MAX_IMAGE_BYTES = 512 * 1024
MAX_RENDER_PIXELS = 8_000_000
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_format(data: bytes) -> tuple[int, int]:
    """Read actual IHDR bit depth and color type rather than Pillow's decoded mode."""
    if len(data) < 33 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":  # noqa: PLR2004
        message = "Invalid PNG IHDR"
        raise ValueError(message)
    return data[24], data[25]


class VariantCache:
    """Render native region pixels at least 1200 before creating smaller variants."""

    def __init__(self, directory: Path) -> None:
        """Identify locally rebuilt renderer and Pillow, and keep artifacts on disk."""
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.renderer = {
            "native_sha256": hashlib.sha256(Path(pdfust.pdfust_core.__file__).read_bytes()).hexdigest(),
            "python_sha256": hashlib.sha256(Path(pdfust.__file__).read_bytes()).hexdigest(),
            "pillow": Image.__version__,
        }

    def _base(self, pdf: bytes, bbox: list[float] | None, page_index: int) -> tuple[Image.Image, dict[str, Any]]:
        if len(pdf) > MAX_PDF_BYTES:
            message = "PDF exceeds experiment input limit"
            raise ValueError(message)
        if isinstance(page_index, bool) or not isinstance(page_index, int) or page_index < 0:
            message = "page_index must be a nonnegative integer"
            raise ValueError(message)
        with pdfust.open(stream=pdf) as document:
            page = document[page_index]
            width, height = page.rect[2:]
            region = bbox if bbox is not None else [0, 0, width, height]
            if len(region) != 4 or any(isinstance(v, bool) or not math.isfinite(v) for v in region):  # noqa: PLR2004
                message = "crop must contain four finite coordinates"
                raise ValueError(message)
            region = [max(0, region[0]), max(0, region[1]), min(width, region[2]), min(height, region[3])]
            if region[0] >= region[2] or region[1] >= region[3]:
                message = "crop has no positive intersection"
                raise ValueError(message)
            scale = float(math.ceil(BASE_EDGE / max(region[2] - region[0], region[3] - region[1])))
            if math.ceil(width * scale) * math.ceil(height * scale) > MAX_RENDER_PIXELS:
                message = "full-page render exceeds experiment pixel admission"
                raise ValueError(message)
            identity = {
                "source_sha256": hashlib.sha256(pdf).hexdigest(),
                "page": page_index,
                "crop": region,
                "scope": "page" if bbox is None else "region",
                "scale": scale,
                "base_edge": BASE_EDGE,
                "renderer": self.renderer,
                "background": "white",
                "schema": SCHEMA,
            }
            key = digest(identity)
            path = self.directory / f"base-{key}.png"
            hit = path.exists()
            if hit:
                with Image.open(path) as opened:
                    raster = opened.convert("RGB")
            else:
                pix = page.get_pixmap(scale=scale, clip=tuple(region), background=(255, 255, 255))
                raster = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples).convert("RGB")
                raster.save(path, format="PNG")
            if max(raster.size) < BASE_EDGE:
                message = "native base raster is too small; upscaling is forbidden"
                raise ValueError(message)
            return raster, {
                "identity": identity,
                "base_key": key,
                "base_pixels": list(raster.size),
                "base_cache": hit,
                "bbox": region,
                "display_to_base": {
                    "scale": scale,
                    "pixel_origin": [math.floor(region[0] * scale), math.floor(region[1] * scale)],
                },
            }

    def make_variant(  # noqa: PLR0913
        self,
        pdf: bytes,
        bbox: list[float] | None = None,
        *,
        edge: int = 128,
        mode: str = "gray8",
        blank: bool = False,
        page_index: int = 0,
    ) -> dict[str, Any]:
        """Produce one admitted PNG plus exact transforms and CPU resource observations."""
        if isinstance(edge, bool) or edge not in EDGES or mode not in MODES:
            message = "Unsupported image edge or mode"
            raise ValueError(message)
        start, cpu = time.perf_counter(), time.process_time()
        raster, meta = self._base(pdf, bbox, page_index)
        identity = {
            "base_key": meta["base_key"],
            "edge": edge,
            "mode": mode,
            "blank": blank,
            "resample": "LANCZOS",
            "dither": "NONE",
            "gray4_palette": "16 equally spaced grayscale levels; nearest rounding",
            "mono_threshold": 128,
            "png_format": MODES[mode],
            "schema": SCHEMA,
        }
        key = digest(identity)
        path = self.directory / f"variant-{key}.png"
        hit = path.exists()
        if hit:
            data = path.read_bytes()
            with Image.open(io.BytesIO(data)) as opened:
                size = list(opened.size)
        else:
            ratio = edge / max(raster.size)
            size = [max(1, round(raster.width * ratio)), max(1, round(raster.height * ratio))]
            raster = raster.resize((size[0], size[1]), Image.Resampling.LANCZOS)
            if blank:
                raster = Image.new("RGB", raster.size, "white")
            if mode not in {"rgb8", "pal4"}:
                raster = raster.convert("L")
            if mode == "gray4":
                indexes = raster.point([min(15, (value + 8) // 17) for value in range(256)])
                raster = Image.frombytes("P", indexes.size, indexes.tobytes())
                raster.putpalette([component for value in range(16) for component in [value * 17] * 3])
            elif mode == "pal4":
                raster = raster.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            elif mode == "mono1":
                raster = raster.convert("1", dither=Image.Dither.NONE)
            buffer = io.BytesIO()
            raster.save(buffer, format="PNG", optimize=True, **({"bits": 4} if mode in {"gray4", "pal4"} else {}))
            data = buffer.getvalue()
            if len(data) > MAX_IMAGE_BYTES:
                message = "PNG exceeds image admission"
                raise ValueError(message)
            path.write_bytes(data)
        if len(data) > MAX_IMAGE_BYTES or png_format(data) != MODES[mode]:
            message = "Cached PNG violates byte or encoded-format admission"
            raise ValueError(message)
        return {
            **meta,
            "identity": {**meta["identity"], "variant": identity},
            "variant_key": key,
            "variant_cache": hit,
            "data": data,
            "mime": "image/png",
            "path": str(path),
            "pixels": size,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "png_bit_depth": png_format(data)[0],
            "png_color_type": png_format(data)[1],
            "mode": mode,
            "blank": blank,
            "wall_ms": (time.perf_counter() - start) * 1000,
            "cpu_ms": (time.process_time() - cpu) * 1000,
            "peak_rss_bytes": rss_bytes(),
            "measurement": "perf_counter/process_time and VmHWM; current process lifetime RSS bytes; no sampling",
        }


def build_request(
    case: dict[str, Any], model: str, variant: dict[str, Any] | None = None, *, native: bool = False
) -> dict[str, Any]:
    """Keep the same compact current state for every image arm, with no gold fields."""
    evidence = evidence_modes(case, "native" if native else "current")
    mapping = {word["id"]: index for index, word in enumerate(evidence["words"])}
    for word in evidence["words"]:
        word["id"] = mapping[word["id"]]
    evidence["candidates"] = {name: [mapping[source] for source in ids] for name, ids in evidence["candidates"].items()}
    body = make_request(evidence, model)
    if variant is not None:
        if len(variant["data"]) > MAX_IMAGE_BYTES:
            message = "Image exceeds request admission"
            raise ValueError(message)
        text = json.dumps(body["state"], separators=(",", ":"))
        text += (
            "\nAttached image maps display rectangle "
            + json.dumps(variant["bbox"])
            + " to pixels "
            + json.dumps(variant["pixels"])
            + ". Use visible boundaries and document notes with exact source words."
        )
        body["state"] = [
            text,
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:"
                    + variant.get("mime", "image/png")
                    + ";base64,"
                    + base64.b64encode(variant["data"]).decode("ascii"),
                    "detail": "high",
                },
            },
        ]
    return body


def expected_evidence(case: dict[str, Any], variant: dict[str, Any] | None, *, native: bool = False) -> str:
    """Scope existing gold for scoring only; blank images supply no visual evidence."""
    if native:
        return str(case["gold"]["mode_choices"]["native"])
    if variant is None or variant["blank"]:
        return str(case["gold"]["mode_choices"]["current"])
    if variant["identity"]["scope"] == "page":
        return str(case["gold"]["choice"])
    evidence = case["evidence"]
    box = variant["bbox"]
    visible = any(
        box[0] <= drawing["bbox"][0]
        and box[1] <= drawing["bbox"][1]
        and box[2] >= drawing["bbox"][2]
        and box[3] >= drawing["bbox"][3]
        for drawing in evidence["native_rules"] + evidence["native_fills"]
    )
    return str(case["gold"]["choice"] if visible else case["gold"]["mode_choices"]["current"])


def default_arms(*, full_page: bool = False) -> list[dict[str, Any]]:
    """Vary size, grayscale and indexed color separately, each with a matched blank."""
    conditions = [(edge, mode) for mode in ("rgb8", "gray8", "pal4") for edge in EDGES]
    return [
        {"edge": edge, "mode": mode, "blank": blank, "scope": "page" if full_page else "region"}
        for edge, mode in conditions
        for blank in (False, True)
    ]


def freeze_manifest(models: list[str], directory: Path, *, full_page: bool = False) -> dict[str, Any]:
    """Write all thirty DEV requests per arm and freeze content hashes without paid calls."""
    cache = VariantCache(directory / "images")
    records = []
    for index, case in enumerate(context_cases()):
        configurations = [{"native": False}, {"native": True}, *default_arms(full_page=full_page)]
        for configuration in configurations:
            native = bool(configuration.get("native", False))
            variant = None
            if "edge" in configuration:
                variant = cache.make_variant(
                    case["pdf_bytes"],
                    None if full_page else case["evidence"]["current_region"],
                    edge=configuration["edge"],
                    mode=configuration["mode"],
                    blank=configuration["blank"],
                )
            for model_index, model in enumerate(models):
                body = build_request(case, model, variant, native=native)
                encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
                request_hash = hashlib.sha256(encoded).hexdigest()
                path = directory / f"request-{index:02d}-{model_index}-{request_hash}.json"
                path.write_bytes(encoded)
                records.append(
                    {
                        "case_index": index,
                        "case_id": case["id"],
                        "model": model,
                        "configuration": configuration,
                        "request_path": str(path),
                        "request_sha256": request_hash,
                        "request_bytes": len(encoded),
                        "source_sha256": hashlib.sha256(case["pdf_bytes"]).hexdigest(),
                        "expected_document": case["gold"]["choice"],
                        "expected_evidence": expected_evidence(case, variant, native=native),
                        "image": {k: v for k, v in variant.items() if k != "data"} if variant else None,
                    }
                )
    manifest = {
        "schema": SCHEMA,
        "status": "DEV; ten correlated templates across three vocabularies; offline freeze only",
        "models": models,
        "records": records,
        "code_sha256": digest(
            {
                str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [
                    Path(__file__),
                    Path("bench/decision_context_compact.py"),
                    Path("bench/decision_context_cases.py"),
                ]
            }
        ),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def main() -> None:
    """Create request artifacts only; model IDs are supplied by the campaign coordinator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--full-page", action="store_true")
    args = parser.parse_args()
    manifest = freeze_manifest(args.models, args.directory, full_page=args.full_page)
    print(json.dumps({"requests": len(manifest["records"]), "directory": str(args.directory)}))


if __name__ == "__main__":
    main()
