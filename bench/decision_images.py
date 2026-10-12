"""Bounded CPU page/crop caches for opt-in decision-model DEV experiments."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter

import pdfust

SCHEMA = 1
MIN_PAGE_EDGE = 64
MAX_PAGE_EDGE = 1400
MIN_CROP_EDGE = 32
MAX_CROP_EDGE = 512
MAX_BLUR = 4
MAX_MEMORY_PAGES = 4
BOX_COORDS = 4
MAX_PIXELS = 2_000_000
MAX_IMAGE_BYTES = 20_000
MAX_PDF_BYTES = 8_000_000


def digest(value: object) -> str:
    """Hash complete canonical JSON, including renderer and transformation identity."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ImageCache:
    """Cache immutable PDFs by content; retain at most four decoded page rasters."""

    def __init__(self, directory: Path, *, page_edge: int = 1024) -> None:
        """Keep all generated images under an ignored artifact directory."""
        if (
            isinstance(page_edge, bool)
            or not isinstance(page_edge, int)
            or not MIN_PAGE_EDGE <= page_edge <= MAX_PAGE_EDGE
        ):
            message = "page_edge must be an integer from 64 through 1400"
            raise ValueError(message)
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.page_edge = page_edge
        self.pages: OrderedDict[str, tuple[Image.Image, dict[str, Any]]] = OrderedDict()
        # Version alone is insufficient for a locally rebuilt extension.
        native_path = Path(pdfust.pdfust_core.__file__)
        self.renderer = {
            "native_sha256": hashlib.sha256(native_path.read_bytes()).hexdigest(),
            "python_sha256": hashlib.sha256(Path(pdfust.__file__).read_bytes()).hexdigest(),
            "pillow": Image.__version__,
            "schema": SCHEMA,
        }

    def page(self, pdf: bytes, page_index: int = 0) -> tuple[Image.Image, dict[str, Any]]:
        """Render opaque white once, measuring disk/memory hits separately from misses."""
        start = time.perf_counter()
        if len(pdf) > MAX_PDF_BYTES:
            message = "PDF exceeds experiment input limit"
            raise ValueError(message)
        if isinstance(page_index, bool) or not isinstance(page_index, int) or page_index < 0:
            message = "page_index must be a nonnegative integer"
            raise ValueError(message)
        identity = {
            "pdf": hashlib.sha256(pdf).hexdigest(),
            "page": page_index,
            "edge": self.page_edge,
            "renderer": self.renderer,
            "background": "white",
        }
        key = digest(identity)
        if key in self.pages:
            raster, metadata = self.pages.pop(key)
            self.pages[key] = raster, metadata
            return raster, {**metadata, "page_cache": "memory", "page_ms": (time.perf_counter() - start) * 1000}
        path = self.directory / f"page-{key}.png"
        meta_path = self.directory / f"page-{key}.json"
        if path.exists() and meta_path.exists():
            metadata = json.loads(meta_path.read_text())
            if metadata["identity"] != identity:
                message = "page cache identity mismatch"
                raise ValueError(message)
            with Image.open(path) as opened:
                if opened.width * opened.height > MAX_PIXELS:
                    message = "cached raster exceeds pixel limit"
                    raise ValueError(message)
                raster = opened.convert("RGB")
            status = "disk"
        else:
            with pdfust.open(stream=pdf) as document:
                page = document[page_index]
                width, height = page.rect[2:]
                scale = self.page_edge / max(width, height)
                if math.ceil(width * scale) * math.ceil(height * scale) > MAX_PIXELS:
                    message = "raster exceeds pixel limit"
                    raise ValueError(message)
                pix = page.get_pixmap(scale=scale, background=(255, 255, 255))
                raster = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples).convert("RGB")
            metadata = {
                "identity": identity,
                "key": key,
                "display_size": [width, height],
                "scale": scale,
                "pixels": list(raster.size),
            }
            raster.save(path, format="PNG")
            meta_path.write_text(json.dumps(metadata, sort_keys=True))
            status = "miss"
        self.pages[key] = raster, metadata
        while len(self.pages) > MAX_MEMORY_PAGES:
            self.pages.popitem(last=False)
        return raster, {**metadata, "page_cache": status, "page_ms": (time.perf_counter() - start) * 1000}

    def crop(  # noqa: PLR0913, C901
        self,
        pdf: bytes,
        bbox: list[float] | tuple[float, ...],
        *,
        edge: int = 128,
        blur: float = 0,
        blank: bool = False,
        grayscale: bool = True,
        codec: str = "PNG",
        page_index: int = 0,
    ) -> dict[str, Any]:
        """Return encoded bytes and display transform; crop from a cached full page."""
        start = time.perf_counter()
        if isinstance(edge, bool) or not isinstance(edge, int) or not MIN_CROP_EDGE <= edge <= MAX_CROP_EDGE:
            message = "crop edge must be an integer from 32 through 512"
            raise ValueError(message)
        if isinstance(blur, bool) or not math.isfinite(blur) or not 0 <= blur <= MAX_BLUR:
            message = "blur must be finite and between zero and four pixels"
            raise ValueError(message)
        if codec not in {"PNG", "WEBP"}:
            message = "unsupported experiment codec"
            raise ValueError(message)
        if len(bbox) != BOX_COORDS or any(isinstance(v, bool) or not math.isfinite(v) for v in bbox):
            message = "crop must contain four finite display coordinates"
            raise ValueError(message)
        raster, metadata = self.page(pdf, page_index)
        width, height = metadata["display_size"]
        clipped = [max(0, bbox[0]), max(0, bbox[1]), min(width, bbox[2]), min(height, bbox[3])]
        if clipped[0] >= clipped[2] or clipped[1] >= clipped[3]:
            message = "crop has no positive intersection"
            raise ValueError(message)
        scale = metadata["scale"]
        pixel_box = [
            math.floor(clipped[0] * scale),
            math.floor(clipped[1] * scale),
            min(raster.width, math.ceil(clipped[2] * scale)),
            min(raster.height, math.ceil(clipped[3] * scale)),
        ]
        identity = {
            "page_key": metadata["key"],
            "pixel_box": pixel_box,
            "edge": edge,
            "blur": blur,
            "blank": blank,
            "gray": grayscale,
            "codec": codec,
            "resample": "LANCZOS",
            "schema": SCHEMA,
        }
        key = digest(identity)
        path = self.directory / f"crop-{key}.{codec.lower()}"
        crop_hit = path.exists()
        if crop_hit:
            data = path.read_bytes()
            with Image.open(io.BytesIO(data)) as opened:
                size = list(opened.size)
        else:
            crop = raster.crop((pixel_box[0], pixel_box[1], pixel_box[2], pixel_box[3]))
            ratio = edge / max(crop.size)
            size = [max(1, round(crop.width * ratio)), max(1, round(crop.height * ratio))]
            crop = crop.resize((size[0], size[1]), Image.Resampling.LANCZOS)
            if grayscale:
                crop = crop.convert("L")
            if blur:
                crop = crop.filter(ImageFilter.GaussianBlur(blur))
            if blank:
                crop = Image.new(crop.mode, crop.size, "white")
            buffer = io.BytesIO()
            crop.save(buffer, format=codec, **({"lossless": True} if codec == "WEBP" else {"optimize": True}))
            data = buffer.getvalue()
            if len(data) > MAX_IMAGE_BYTES:
                message = "encoded crop exceeds image admission; use a smaller declared condition"
                raise ValueError(message)
            path.write_bytes(data)
        if len(data) > MAX_IMAGE_BYTES:
            message = "cached crop exceeds image admission"
            raise ValueError(message)
        return {
            "data": data,
            "mime": "image/" + codec.lower(),
            "path": str(path),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "pixels": size,
            "bbox": [v / scale for v in pixel_box],
            "crop_key": key,
            "identity": identity,
            "page_cache": metadata["page_cache"],
            "crop_cache": crop_hit,
            "page_ms": metadata["page_ms"],
            "total_ms": (time.perf_counter() - start) * 1000,
        }


def image_part(crop: dict[str, Any]) -> dict[str, Any]:
    """Build the documented top-level alpha Decisions image part."""
    if len(crop["data"]) > MAX_IMAGE_BYTES:
        message = "image exceeds admission"
        raise ValueError(message)
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{crop['mime']};base64," + base64.b64encode(crop["data"]).decode("ascii"),
            "detail": "low",
        },
    }
