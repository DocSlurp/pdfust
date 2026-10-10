"""Artificial image controls preserve geometry and unambiguously mark altered evidence."""

import base64
import io

from bench.p003_selector_visibility import transform
from bench.silver import sha
from PIL import Image, ImageDraw, ImageStat


def test_visibility_identity_blank_and_relative_blur() -> None:
    source = Image.new("RGB", (100, 40), "white")
    draw = ImageDraw.Draw(source)
    for x in range(10, 90, 4):
        draw.rectangle((x, 10, x + 1, 30), fill="black")
    stream = io.BytesIO()
    source.save(stream, format="JPEG", quality=90)
    data = stream.getvalue()
    url = "data:image/jpeg;base64," + base64.b64encode(data).decode()
    meta = {
        "image_sha256": sha(data),
        "image_bytes": len(data),
        "image_size": [100, 40],
        "image_edge": 128,
        "image_viewport": [0, 0, 100, 40],
    }
    assert transform(url, meta) == (url, meta)
    before = ImageStat.Stat(Image.open(io.BytesIO(data))).var[0]
    for control in ("blank", "blur"):
        result, metadata = transform(url, meta, control)
        encoded = base64.b64decode(result.split(",", 1)[1])
        with Image.open(io.BytesIO(encoded)) as image:
            assert image.size == (100, 40)
            assert ImageStat.Stat(image).var[0] < before
            if control == "blank":
                assert image.getextrema() == ((255, 255), (255, 255), (255, 255))
        assert metadata["visibility_source_sha256"] == sha(data)
        assert metadata["image_sha256"] == sha(encoded)
        assert metadata["image_viewport"] == meta["image_viewport"]
        assert metadata["blur_radius_pixels"] == (2.0 if control == "blur" else None)
