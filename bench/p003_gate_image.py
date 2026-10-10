"""Independent CPU gate-image encodings; RGB preserves the exact input payload."""

# Explicit pixel metadata contains heterogeneous JSON values.
# ruff: noqa: EM101, TRY003, PLC0415
from __future__ import annotations

import base64
import binascii
import hashlib
import io
from typing import Any

MODES = ("rgb", "grayscale8", "rgb_palette16")
EDGES = (128, 256, 400, 512, 768, 1024)
MAX_PIXELS = 1024 * 1024
MAX_BYTES = 16 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def transform(  # noqa: C901, PLR0912 - bounded explicit encoding admissions.
    url: str | None, metadata: dict[str, Any], mode: str = "rgb") -> tuple[str | None, dict[str, Any]]:
    """Encode after resizing; preserve dimensions, viewport, and the RGB generation URL."""
    from PIL import Image

    if mode not in MODES:
        raise ValueError("Unknown gate image mode")
    if mode == "rgb":
        return url, dict(metadata)
    prefix = "data:image/png;base64,"
    if not isinstance(url, str) or not url.startswith(prefix) or len(url) > MAX_BYTES * 2:
        raise ValueError("Gate conversion requires bounded source PNG pixels")
    try:
        data = base64.b64decode(url[len(prefix):], validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("Invalid gate PNG payload") from error
    if len(data) > MAX_BYTES or not data.startswith(PNG_SIGNATURE):
        raise ValueError("Gate PNG byte admission exceeded or invalid signature")
    source_sha = hashlib.sha256(data).hexdigest()
    if metadata.get("image_sha256") != source_sha or metadata.get("image_bytes") != len(data):
        raise ValueError("Source gate PNG differs from retained RGB metadata")
    if metadata.get("image_edge") not in EDGES:
        raise ValueError("Gate encoding requires a declared fixed image edge")
    with Image.open(io.BytesIO(data)) as image:
        if (image.mode != "RGB" or image.width * image.height > MAX_PIXELS
                or max(image.size) > metadata["image_edge"] or list(image.size) != metadata.get("image_size")):
            raise ValueError("Gate RGB dimensions or mode differ from bounded metadata")
        image.load()
        if mode == "grayscale8":
            converted = image.convert("L")
            quantization = "Pillow RGB to 8-bit luminance; no palette or dithering"
        else:
            converted = image.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            quantization = "Pillow RGB median-cut, at most 16 palette entries, no dithering"
        output = io.BytesIO()
        if mode == "rgb_palette16":
            converted.save(output, format="PNG", bits=4, optimize=False, compress_level=6)
        else:
            converted.save(output, format="PNG", optimize=False, compress_level=6)
        encoded = output.getvalue()
        if len(encoded) > MAX_BYTES:
            raise ValueError("Encoded gate PNG byte admission exceeded")
        result = {
            **metadata, "gate_image_mode": mode, "image_codec": "PNG", "image_mode": converted.mode,
            "png_bit_depth": encoded[24], "png_color_type": encoded[25],
            "image_sha256": hashlib.sha256(encoded).hexdigest(), "image_bytes": len(encoded),
            "source_rgb_sha256": source_sha, "source_rgb_image_bytes": len(data),
            "palette_entries": len(converted.getpalette() or []) // 3 if mode == "rgb_palette16" else 0,
            "quantization": quantization, "lossy_color_transform": True,
        }
    return prefix + base64.b64encode(encoded).decode(), result
