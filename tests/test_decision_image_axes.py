"""Actual axis sizing, representation encoding, refusals, and geometric identity."""

from pathlib import Path

import pytest
from bench import decision_image_axes as axes
from PIL import Image


@pytest.mark.parametrize(("axis", "expected"), [("width", (400, 200)), ("height", (800, 400)), ("longest", (400, 200))])
def test_axis_targets_preserve_aspect(axis: str, expected: tuple[int, int]) -> None:
    """Width and height target distinct dimensions without hidden longest-edge clamping."""
    assert axes.dimensions(1200, 600, 400, axis) == expected


@pytest.mark.parametrize("mode", axes.REPRESENTATIONS)
def test_actual_representation_and_geometric_identity(tmp_path: Path, mode: str) -> None:
    """Equal axis geometries have identical encoded pixels, not inferred provider cache behavior."""
    image = Image.new("RGB", (1200, 600), (10, 30, 70))
    first = axes.variant_image(image, [0, 0, 600, 300], tmp_path, target=400, axis="width", mode=mode)
    second = axes.variant_image(image, [0, 0, 600, 300], tmp_path, target=400, axis="longest", mode=mode)
    assert first["pixels"] == [400, 200]
    assert first["total_pixels"] == 80_000
    assert first["sha256"] == second["sha256"]
    assert first["bytes"] == len(first["data"])
    assert (first["png_bit_depth"], first["png_color_type"]) == axes.MODES[mode]
    assert first["source_aspect_ratio"] == 2
    assert not first["anisotropic"]


def test_thin_region_height_is_refused_without_upscale(tmp_path: Path) -> None:
    """Requested tall scale is refused instead of silently lowering the target axis."""
    with pytest.raises(ValueError, match="upscaling refused"):
        axes.variant_image(
            Image.new("RGB", (1200, 120)), [0, 0, 100, 10], tmp_path, target=200, axis="height", mode="rgb8"
        )


def test_total_pixel_admission_before_resize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Actual width-times-height cap is independent of target-axis size."""
    monkeypatch.setattr(axes, "MAX_PIXELS", 100)
    with pytest.raises(ValueError, match="total-pixel"):
        axes.variant_image(
            Image.new("RGB", (1200, 600)), [0, 0, 600, 300], tmp_path, target=200, axis="width", mode="rgb8"
        )


def test_separate_anisotropic_arm_is_explicit(tmp_path: Path) -> None:
    """The optional distortion arm deliberately changes shape and reports both dimensions."""
    image = Image.new("RGB", (1200, 1600), "white")
    result = axes.variant_image(
        image, [0, 0, 600, 800], tmp_path, target=200, axis="width", mode="gray8", fixed_partner=512
    )
    assert result["pixels"] == [200, 512]
    assert result["anisotropic"]
    assert result["source_aspect_ratio"] != result["actual_aspect_ratio"]
    assert result["fixed_partner_pixels"] == 512
