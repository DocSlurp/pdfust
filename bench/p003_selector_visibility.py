"""Blinded source-image ablations for frozen candidate selection, never production."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image, ImageFilter

from bench.silver import sha

CONTROLS = ("source", "blank", "blur")
MAX_BYTES = 16 * 1024 * 1024


def transform(url: str, metadata: dict[str, Any], control: str = "source") -> tuple[str, dict[str, Any]]:
    """Return exact default pixels or a labeled blank/relative-blur JPEG ablation."""
    if control not in CONTROLS:
        raise ValueError("Unknown selector visibility control")
    if control == "source":
        return url, dict(metadata)
    prefix = "data:image/jpeg;base64,"
    if not url.startswith(prefix) or len(url) > MAX_BYTES * 2:
        raise ValueError("Visibility control requires bounded original JPEG")
    data = base64.b64decode(url[len(prefix) :], validate=True)
    if len(data) > MAX_BYTES or sha(data) != metadata["image_sha256"] or len(data) != metadata["image_bytes"]:
        raise ValueError("Visibility source pixels differ from metadata")
    with Image.open(io.BytesIO(data)) as original:
        if (
            original.mode != "RGB"
            or original.width * original.height > 1200 * 1200
            or list(original.size) != metadata["image_size"]
            or max(original.size) > metadata["image_edge"]
        ):
            raise ValueError("Visibility source geometry differs")
        original.load()
        radius = 0.02 * max(original.size) if control == "blur" else None
        changed = (
            original.filter(ImageFilter.GaussianBlur(radius=radius))
            if radius is not None
            else Image.new("RGB", original.size, "white")
        )
        stream = io.BytesIO()
        changed.save(stream, format="JPEG", quality=90)
        encoded = stream.getvalue()
        if len(encoded) > MAX_BYTES:
            raise ValueError("Visibility control exceeds byte admission")
    return "data:image/jpeg;base64," + base64.b64encode(encoded).decode(), {
        **metadata,
        "image_visibility": control,
        "visibility_source_sha256": sha(data),
        "visibility_source_bytes": len(data),
        "image_sha256": sha(encoded),
        "image_bytes": len(encoded),
        "blur_radius_pixels": radius,
        "visibility_scope": "Artificial blinded ablation; this image is not a faithful source rendering",
    }
