"""CPU image evidence keeps opaque pixels and invalidates complete cache identity."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

pytest.importorskip("PIL")
from bench.decision_images import ImageCache, image_part
from bench.feature_cases import page_pdf, text_op
from PIL import Image


def test_page_crop_cache_and_variants(tmp_path: Path) -> None:
    pdf = page_pdf(text_op("Wrapped description", 40, 700) + "\n0.8 g 40 620 300 40 re f")
    cache = ImageCache(tmp_path)
    first = cache.crop(pdf, [30, 70, 400, 200])
    repeated = cache.crop(pdf, [30, 70, 400, 200])
    assert first["page_cache"] == "miss"
    assert repeated["page_cache"] == "memory"
    assert repeated["crop_cache"]
    assert first["data"] == repeated["data"]
    disk = ImageCache(tmp_path).crop(pdf, [30, 70, 400, 200])
    assert disk["page_cache"] == "disk"
    assert disk["crop_cache"]
    altered = [
        cache.crop(pdf, [30, 70, 400, 200], blur=1),
        cache.crop(pdf, [30, 70, 400, 200], edge=64),
        cache.crop(pdf, [30, 70, 400, 200], blank=True),
        cache.crop(pdf, [30, 80, 400, 210]),
    ]
    assert len({first["crop_key"], *[v["crop_key"] for v in altered]}) == 5
    with Image.open(io.BytesIO(first["data"])) as image:
        assert image.mode == "L"
        assert image.getpixel((0, 0)) == 255
        assert len(set(image.tobytes())) > 1
        assert image.getextrema()[1] == 255
    with Image.open(io.BytesIO(altered[2]["data"])) as image:
        assert image.getextrema() == (255, 255)
    part = image_part(first)
    assert part["type"] == "image_url"
    assert part["image_url"]["url"].startswith("data:image/png;base64,")


def test_snapshot_bytes_and_renderer_configuration_invalidate(tmp_path: Path) -> None:
    cache = ImageCache(tmp_path)
    a = cache.crop(page_pdf(text_op("A", 40, 700)), [30, 70, 400, 200])
    b = cache.crop(page_pdf(text_op("B", 40, 700)), [30, 70, 400, 200])
    c = ImageCache(tmp_path, page_edge=800).crop(page_pdf(text_op("A", 40, 700)), [30, 70, 400, 200])
    assert len({a["crop_key"], b["crop_key"], c["crop_key"]}) == 3


@pytest.mark.parametrize("kwargs", [{"edge": 0}, {"edge": True}, {"blur": float("nan")}, {"blur": 5}, {"codec": "PDF"}])
def test_invalid_transform_rejected(tmp_path: Path, kwargs: dict) -> None:
    with pytest.raises(ValueError, match=r"crop|blur|codec"):
        ImageCache(tmp_path).crop(page_pdf(""), [0, 0, 20, 20], **kwargs)


@pytest.mark.parametrize("box", [[0, 0, float("inf"), 30], [10, 10, 0, 0], [700, 0, 710, 10]])
def test_invalid_crop_rejected(tmp_path: Path, box: list) -> None:
    with pytest.raises(ValueError, match=r"crop|blur|codec"):
        ImageCache(tmp_path).crop(page_pdf(""), box)
