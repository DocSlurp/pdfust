"""Independent selector encodings of the same decoded, resized JPEG pixels."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image

from bench.silver import sha

MODES = ("rgb", "rgb_png", "grayscale8", "rgb_palette16")
MAX_BYTES = 16 * 1024 * 1024


def transform(url: str, metadata: dict[str, Any], mode: str = "rgb") -> tuple[str, dict[str, Any]]:
    """Keep default JPEG bytes or explicitly encode RGB, luminance or palette PNG."""
    if mode not in MODES:
        raise ValueError("Unknown selector image mode")
    if mode == "rgb":
        return url, dict(metadata)
    prefix = "data:image/jpeg;base64,"
    if not url.startswith(prefix) or len(url) > MAX_BYTES * 2:
        raise ValueError("Selector conversion requires bounded original JPEG")
    data = base64.b64decode(url[len(prefix) :], validate=True)
    if len(data) > MAX_BYTES or sha(data) != metadata["image_sha256"] or len(data) != metadata["image_bytes"]:
        raise ValueError("Selector source pixels differ from retained metadata")
    with Image.open(io.BytesIO(data)) as original:
        if (
            original.mode != "RGB"
            or original.width * original.height > 1200 * 1200
            or list(original.size) != metadata["image_size"]
            or max(original.size) > metadata["image_edge"]
        ):
            raise ValueError("Selector source dimensions or mode differ")
        original.load()
        if mode == "grayscale8":
            image = original.convert("L")
        elif mode == "rgb_palette16":
            image = original.quantize(colors=16, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        else:
            image = original.copy()
        output = io.BytesIO()
        options = {"bits": 4} if mode == "rgb_palette16" else {}
        image.save(output, format="PNG", optimize=False, compress_level=6, **options)
        encoded = output.getvalue()
        if len(encoded) > MAX_BYTES:
            raise ValueError("Selector encoded PNG admission exceeded")
        result = {
            **metadata,
            "selector_image_mode": mode,
            "source_image_sha256": sha(data),
            "source_image_bytes": len(data),
            "source_image_codec": metadata["image_codec"],
            "source_image_quality": metadata["image_quality"],
            "image_quality": None,
            "image_codec": "PNG",
            "image_sha256": sha(encoded),
            "image_bytes": len(encoded),
            "image_mode": image.mode,
            "png_bit_depth": encoded[24],
            "png_color_type": encoded[25],
            "palette_entries": len(image.getpalette() or []) // 3 if mode == "rgb_palette16" else 0,
            "pixel_basis": "Same decoded resized JPEG90 pixels; rgb_png isolates PNG transport encoding",
            "lossy_color_transform": mode != "rgb_png",
        }
    return "data:image/png;base64," + base64.b64encode(encoded).decode(), result
