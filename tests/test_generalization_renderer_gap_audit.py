"""Pixel differences are diagnostics and record dimension normalization explicitly."""

import io
from pathlib import Path

import pytest
from bench.generalization_renderer_gap_audit import audit, compare_images
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


@pytest.mark.parametrize("dpi", [True, 0, 200, 300.0])
def test_renderer_dpi_refused_before_manifest_access(tmp_path: Path, dpi: object) -> None:
    with pytest.raises(ValueError, match="fixed 150 or 300 DPI"):
        audit(tmp_path / "missing.json", tmp_path / "output", dpi=dpi)  # type: ignore[arg-type]
