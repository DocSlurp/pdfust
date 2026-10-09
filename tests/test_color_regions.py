"""Python integration tests for the isolated CPU Rust color-region experiment."""

import subprocess
from pathlib import Path

import pytest
from bench.color_regions import build_executable, extract_regions, pixmap_rgb, vector_regions
from bench.feature_cases import page_pdf, text_op

import pylopdf


@pytest.fixture(scope="module")
def binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_executable(tmp_path_factory.mktemp("color-regions") / "regions")


def extract(binary: Path, pixels: list[tuple[int, int, int]], width: int, **kwargs: int) -> list[dict]:
    return extract_regions(
        bytes(c for p in pixels for c in p), width, len(pixels) // width, executable=binary, min_area=1, **kwargs
    )


def test_threshold_merge_and_luminance_gate(binary: Path) -> None:
    pixels = [(120, 120, 120), (130, 130, 130)]
    assert len(extract(binary, pixels, 2, color_distance=16)) == 2
    regions = extract(binary, pixels, 2, color_distance=18)
    assert len(regions) == 1
    assert regions[0]["area"] == 2
    assert regions[0]["mean_rgb"] == [125, 125, 125]
    assert len(extract(binary, pixels, 2, color_distance=18, luminance_distance=9)) == 2


def test_diagonal_connectivity(binary: Path) -> None:
    black, white = (0, 0, 0), (255, 255, 255)
    pixels = [black, white, white, black]
    assert len(extract(binary, pixels, 2, connectivity=4)) == 2
    assert len(extract(binary, pixels, 2, connectivity=8)) == 1


def test_outlined_white_interior_and_text_hole(binary: Path) -> None:
    pixels = [(255, 255, 255)] * 121
    for y in range(2, 9):
        for x in range(2, 9):
            pixels[y * 11 + x] = (0, 0, 0) if x in (2, 8) or y in (2, 8) else (250, 250, 250)
    pixels[5 * 11 + 5] = (0, 0, 0)
    regions = extract(binary, pixels, 11)
    interior = next(r for r in regions if r["mean_rgb"] == [250, 250, 250])
    assert interior["bbox"] == [3, 3, 8, 8]
    assert interior["area"] == 24
    assert interior["dark_boundary_fraction"] == 1
    assert not interior["touches_border"]
    assert all(r["area"] < 72 for r in regions)


def test_empty_and_white_background(binary: Path) -> None:
    assert extract_regions(b"", 0, 0, executable=binary) == []
    assert extract(binary, [(255, 255, 255)] * 4, 2) == []
    assert len(extract(binary, [(255, 255, 255)] * 4, 2, background_white=256)) == 1


@pytest.mark.parametrize(("limit", "value"), [("max_components", 5), ("max_regions", 3), ("max_pixels", 10)])
def test_checkerboard_limits_reject_complete_result(binary: Path, limit: str, value: int) -> None:
    pixels = [(0, 0, 0) if (x + y) % 2 else (200, 200, 200) for y in range(4) for x in range(4)]
    with pytest.raises(ValueError, match="limit"):
        extract(binary, pixels, 4, **{limit: value})


def test_rust_refusal_has_no_partial_stdout(binary: Path) -> None:
    result = subprocess.run(  # noqa: S603 - freshly compiled local executable.
        [str(binary), "--width", "2", "--height", "1", "--min-area", "1", "--max-regions", "1"],
        input=bytes([0, 0, 0, 200, 200, 200]),
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == b""
    assert b"region limit" in result.stderr


def test_bad_payload_and_parameters(binary: Path) -> None:
    for payload, width, height, kwargs in [
        (b"", 1, 1, {}),
        (b"", -1, 0, {}),
        (b"", 0, 0, {"connectivity": 6}),
        (b"", 0, 0, {"color_distance": 443}),
    ]:
        with pytest.raises(ValueError, match=r"parameters|payload|connectivity|threshold"):
            extract_regions(payload, width, height, executable=binary, **kwargs)


def test_background_with_antialiased_text_edge(binary: Path) -> None:
    pixels = [(255, 255, 255)] * 100
    pixels[45] = (245, 245, 245)
    pixels[46] = (0, 0, 0)
    regions = extract(binary, pixels, 10)
    assert len(regions) == 1
    assert regions[0]["area"] == 1


def test_transitive_component_perimeter(binary: Path) -> None:
    # The diagonal values differ beyond the gate, but other neighbors link them.
    pixels = [(100, 100, 100), (110, 110, 110), (110, 110, 110), (120, 120, 120)]
    regions = extract(binary, pixels, 2, color_distance=18)
    assert len(regions) == 1
    assert regions[0]["perimeter"] == 8


def test_native_fill_grouping_and_raster_text_holes(binary: Path) -> None:

    data = page_pdf(
        "0.5 0.7 0.9 rg 40 650 100 40 re f 140 650 100 40 re f\n" + "0 0 0 rg " + text_op("Header text", 50, 665)
    )
    with pylopdf.Document(stream=data) as document:
        groups = vector_regions(document[0])
        assert len(groups) == 1
        assert groups[0]["paint_count"] == 2
        assert groups[0]["bbox"] == [40, 102, 240, 142]
        pixmap = document[0].get_pixmap(dpi=72, background=(255, 255, 255))
        regions = extract_regions(pixmap_rgb(pixmap), pixmap.width, pixmap.height, min_area=300, executable=binary)
        assert any(r["bbox"] == [40, 102, 240, 142] for r in regions)


def test_native_vector_cap_rejects_all() -> None:

    data = page_pdf("0.5 0.7 0.9 rg 40 650 100 40 re f 200 650 100 40 re f")
    with pylopdf.Document(stream=data) as document, pytest.raises(ValueError, match="vector candidate limit"):
        vector_regions(document[0], max_candidates=1)
