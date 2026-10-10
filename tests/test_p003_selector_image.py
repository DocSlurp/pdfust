"""Selector image variants preserve source geometry and expose color/codec changes."""

import base64
import io

import pytest
from bench.p003_selector_image import transform
from bench.silver import sha
from PIL import Image


def test_separate_png_color_controls_and_exact_default() -> None:
    source = Image.new("RGB", (20, 10), (200, 30, 80))
    stream = io.BytesIO()
    source.save(stream, format="JPEG", quality=90)
    data = stream.getvalue()
    url = "data:image/jpeg;base64," + base64.b64encode(data).decode()
    metadata = {
        "image_sha256": sha(data),
        "image_bytes": len(data),
        "image_size": [20, 10],
        "image_edge": 128,
        "image_codec": "JPEG",
        "image_quality": 90,
        "image_viewport": [1, 2, 21, 12],
    }
    assert transform(url, metadata) == (url, metadata)
    with Image.open(io.BytesIO(data)) as decoded:
        expected = decoded.tobytes()
    for mode, pil_mode, bit_depth in (("rgb_png", "RGB", 8), ("grayscale8", "L", 8), ("rgb_palette16", "P", 4)):
        changed, info = transform(url, metadata, mode)
        with Image.open(io.BytesIO(base64.b64decode(changed.split(",", 1)[1]))) as image:
            assert image.mode == pil_mode
            assert image.size == (20, 10)
            if mode == "rgb_png":
                assert image.tobytes() == expected
        assert info["png_bit_depth"] == bit_depth
        assert info["image_viewport"] == metadata["image_viewport"]
        assert info["image_quality"] is None
    with pytest.raises(ValueError, match="metadata"):
        transform(url, {**metadata, "image_bytes": 1}, "rgb_png")
