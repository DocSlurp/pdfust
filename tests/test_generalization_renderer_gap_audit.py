"""Pixel differences are diagnostics and record dimension normalization explicitly."""

import io

from bench.generalization_renderer_gap_audit import compare_images
from PIL import Image


def raster(color: str, size: tuple[int, int] = (10, 10)) -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", size, color).save(stream, format="PNG")
    return stream.getvalue()


def test_identical_pixels_have_zero_difference() -> None:
    result = compare_images(raster("white"), raster("white"))
    assert result["mean_absolute_channel_difference"] == 0
    assert result["different_pixel_fraction"] == 0
    assert result["second_nearest_resized_for_metric"] is False


def test_full_difference_and_size_adjustment_remain_explicit() -> None:
    result = compare_images(raster("white"), raster("black", (11, 11)))
    assert result["mean_absolute_channel_difference"] == 255
    assert result["different_pixel_fraction"] == 1
    assert result["second_nearest_resized_for_metric"] is True
    assert result["dimensions"] == [[10, 10], [11, 11]]
