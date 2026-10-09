"""Source-only deterministic controls without answer metadata in request prompts."""

import base64
import hashlib
import io

from bench.lowlevel_gateway_sanity import EDGE, controls
from PIL import Image


def test_controls_are_deterministic_opposite_pixels_and_identical_prompts() -> None:
    rows = controls()
    assert rows == controls()
    assert [row["expected"] for row in rows] == ["circle", "square", "unresolved", "unresolved"]
    bodies = [row["canonical_body"] for row in rows]
    assert all(body["questions"] == bodies[0]["questions"] and body["state"] == bodies[0]["state"] for body in bodies)
    hashes = []
    for row in rows[:3]:
        raw = base64.b64decode(row["canonical_body"]["images"][0].split(",", 1)[1], validate=True)
        assert len(raw) == row["png_bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["png_sha256"]
        hashes.append(row["png_sha256"])
        with Image.open(io.BytesIO(raw)) as bitmap:
            assert bitmap.size == (EDGE, EDGE)
            assert bitmap.getpixel((0, 0)) == (255, 255, 255)
            assert bitmap.getpixel((EDGE // 2, EDGE // 2)) == (
                (255, 255, 255) if row["control"] == "blank" else (0, 0, 0)
            )
    assert len(set(hashes)) == len(hashes)
    assert "images" not in bodies[-1]
    for row in rows:
        for body in (row["canonical_body"], row["native_body"]):
            assert "expected" not in body
            assert "control" not in body
            assert "scope" not in body
