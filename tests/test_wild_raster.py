"""Fast checks for the wild-v1 rasterization variants on a tiny generated page."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("numpy")
pytest.importorskip("PIL")
pytest.importorskip("pypdf")

import numpy as np
import pypdf
from bench import wild_raster
from PIL import Image

import pylopdf

pytestmark = pytest.mark.skipif(shutil.which("pdftoppm") is None, reason="Poppler pdftoppm is required")


def _requires(*tools: str) -> None:
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        pytest.skip(f"missing tools: {missing}")


@pytest.fixture(scope="module")
def source(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("raster-source")
    document = pylopdf.open()
    page = document.new_page(width=216, height=144)
    page.insert_text((14, 36), "Invoice 2026-0042", fontsize=16)
    page.insert_text((14, 64), "Total due: 1,234.56 EUR", fontsize=12)
    page.insert_text((14, 88), "Thank you for your order", fontsize=12)
    path = directory / "L0_tagged.pdf"
    document.save(path)
    return path


def _build(source: Path, tmp_path: Path, name: str) -> dict[str, Any]:
    record = wild_raster.rasterize(source, tmp_path, [name], seed="test/doc")
    if name in record["skipped"]:
        pytest.skip(record["skipped"][name])
    assert not record["errors"], record["errors"]
    assert (tmp_path / f"{name}.pdf").is_file()
    result: dict[str, Any] = record["variants"][name]
    assert result["measured"]["render_check"]["pdftoppm"]["ok"]
    return result


def _image_streams(path: Path) -> list[Any]:
    page: Any = pypdf.PdfReader(path).pages[0]
    return [v.get_object() for v in page["/Resources"]["/XObject"].values()]


def test_ccitt_g4_variant_uses_ccittfaxdecode(source: Path, tmp_path: Path) -> None:
    _requires("tiff2pdf", "pdfimages")
    record = _build(source, tmp_path, "R05_bitonal_ccitt_g4")
    (image,) = _image_streams(tmp_path / "R05_bitonal_ccitt_g4.pdf")
    assert image["/Filter"] == "/CCITTFaxDecode"
    assert int(image["/DecodeParms"]["/K"]) == -1
    assert image["/BitsPerComponent"] == 1
    assert record["verification"]["g4_decode_exact"]
    assert record["text_layer"] == "none"


def test_jpx_variant_uses_jpxdecode_and_renders(source: Path, tmp_path: Path) -> None:
    _requires("opj_compress")
    record = _build(source, tmp_path, "R09_jpx")
    (image,) = _image_streams(tmp_path / "R09_jpx.pdf")
    assert image["/Filter"] == "/JPXDecode"
    checks = record["measured"]["render_check"]
    assert checks["pylopdf"]["ok"]
    # Rendered text is visible ink, not a blank page.
    assert checks["pdftoppm"]["dark_fraction"] > 0.001


def test_rotated_scan_content_orientation(source: Path, tmp_path: Path) -> None:
    record = _build(source, tmp_path, "R13_rotated_90_scan")
    clockwise = record["parameters"]["pages"][0]["content_rotation_clockwise_degrees"]
    assert clockwise in {90, 270}
    width, height = record["measured"]["page_sizes"][0]
    assert width < height  # landscape source page becomes portrait
    (image,) = _image_streams(tmp_path / "R13_rotated_90_scan.pdf")
    assert int(image["/Width"]) < int(image["/Height"])
    assert pypdf.PdfReader(tmp_path / "R13_rotated_90_scan.pdf").pages[0].get("/Rotate", 0) == 0

    def gray(document: pylopdf.Document) -> Image.Image:
        pixmap = document[0].get_pixmap(dpi=72)
        array = np.frombuffer(pixmap.samples, np.uint8).reshape(pixmap.height, pixmap.width, 4)[..., :3]
        return Image.fromarray(array).convert("L")

    original = np.asarray(gray(pylopdf.open(source)), np.float32)
    turned = gray(pylopdf.open(tmp_path / "R13_rotated_90_scan.pdf"))
    back = {90: Image.Transpose.ROTATE_90, 270: Image.Transpose.ROTATE_270}  # undo clockwise turn
    errors = {}
    for degrees, transpose in back.items():
        candidate = np.asarray(turned.transpose(transpose).resize(original.shape[::-1]), np.float32)
        errors[degrees] = float(np.abs(candidate - original).mean())
    assert min(errors, key=errors.__getitem__) == clockwise


def test_strip_tiled_has_multiple_images_and_reassembles(source: Path, tmp_path: Path) -> None:
    _requires("pdfimages")
    record = _build(source, tmp_path, "R22_strip_tiled")
    assert record["images_per_page"][0] > 1
    assert len(_image_streams(tmp_path / "R22_strip_tiled.pdf")) == record["images_per_page"][0]
    assert record["verification"]["strips_reassemble_exactly"]
    assert record["verification"]["pylopdf_200dpi"]["max_abs_diff"] <= 2


def test_misaligned_ocr_layer_records_offset(source: Path, tmp_path: Path) -> None:
    _requires("tesseract", "qpdf")
    if "eng" not in wild_raster.tesseract_languages(None):
        pytest.skip("Tesseract English data is not installed")
    record = wild_raster.rasterize(
        source, tmp_path, ["R20_scanner_ocr_layer", "R21_scanner_ocr_misaligned"], seed="test/doc"
    )
    assert not record["errors"], record["errors"]
    aligned, shifted = record["variants"]["R20_scanner_ocr_layer"], record["variants"]["R21_scanner_ocr_misaligned"]
    assert aligned["text_layer"] == "ocr"
    assert shifted["text_layer"] == "ocr"
    transform = shifted["parameters"]["text_layer_transform"]
    dx, dy = transform["offset_pdf_points"]
    assert 2 <= abs(dx) <= 6
    assert 2 <= abs(dy) <= 6
    assert transform["scale"] != 1
    verification = shifted["verification"]
    assert verification["matched_words"] > 0
    assert any(abs(value) >= 1 for value in verification["mean_display_shift_points"])


def test_fax_variant_is_nonsquare_ccitt(source: Path, tmp_path: Path) -> None:
    _requires("pdfimages")
    record = _build(source, tmp_path, "R11_fax_204x98")
    assert record["dpi"] == [204, 98]
    (image,) = _image_streams(tmp_path / "R11_fax_204x98.pdf")
    assert image["/Filter"] == "/CCITTFaxDecode"
    assert record["verification"]["ccitt_decode_exact_page1"]


def test_variants_are_deterministic(source: Path, tmp_path: Path) -> None:
    first = wild_raster.rasterize(source, tmp_path / "a", ["R12_skew_3deg"], seed="test/doc")
    second = wild_raster.rasterize(source, tmp_path / "b", ["R12_skew_3deg"], seed="test/doc")
    assert first["variants"]["R12_skew_3deg"]["output_sha256"] == second["variants"]["R12_skew_3deg"]["output_sha256"]
