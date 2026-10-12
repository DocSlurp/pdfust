"""Derive rasterization-diversity variants R01-R22 for the wild-v1 DEV corpus, CPU only.

Each variant rasterizes ``variants/{doc_id}/L0_tagged.pdf`` the way scanned PDFs
appear in the wild: a resolution sweep, bitonal CCITT G3/G4 and Flate, heavy and
light JPEG, JPEG 2000, fax resolution, skew, misfed rotation, halftone moire,
faded toner, bleed-through, scanner-lid shadow, phone "share as PDF" compression,
scanner-software OCR layers (aligned and misaligned), and strip-tiled images.

Outputs go to ``variants/{doc_id}/R??_{name}.pdf`` plus ``raster.json``, so the
wild-v1 audit (``bench/wild_corpus.py``) scores them with the other levels.
Every variant is deterministic per (seed, doc, variant, page) and tool versions.
Subprocess CPU and peak RSS come from ``os.wait4``; in-process work uses
``RUSAGE_SELF``/``RUSAGE_CHILDREN`` deltas and a per-variant ``VmHWM`` reset.
See ``bench/WILD_CORPUS.md`` for the corpus contract.
"""

# Heterogeneous artifact dictionaries retain tool observations and parameters.
# ruff: noqa: EM101, EM102, TRY003, PLR2004, PLR0913, S603, SLF001, PLC0415, ANN401, S607, D102, D103, D105, FBT001, FBT003

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import shutil
import subprocess
import sys
import tempfile
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench.silver import guard_path
from bench.wild_flatten import (
    SOURCE_DATE_EPOCH,
    RasterImage,
    Recorder,
    _open_pdf,
    _read_hwm_kib,
    _reset_hwm,
    _rng,
    _smooth_field,
    flate_image,
    jpeg_image,
    page_display_sizes,
    select_ocr_languages,
    sha256_file,
    tool_versions,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    import numpy as np
    from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "bench/results/pdf-master-artifacts/wild-v1"
SCHEMA = 1
SOURCE_LEVEL = "L0_tagged"
PAGE_TEXT_MIN_CHARS = 5
STRIP_OVERLAP_ROWS = 0  # exact tiling, as scanner firmware writes it

VARIANTS: dict[str, str] = {
    "R01_72dpi": "clean colour scan at 72 dpi, lossless Flate",
    "R02_100dpi": "clean colour scan at 100 dpi, lossless Flate",
    "R03_150dpi": "clean colour scan at 150 dpi, lossless Flate",
    "R04_600dpi": "clean 8-bit grayscale scan at 600 dpi, lossless Flate",
    "R05_bitonal_ccitt_g4": "300 dpi 1-bit scan, CCITT Group 4 (via libtiff tiff2pdf)",
    "R06_bitonal_flate": "300 dpi 1-bit scan, Flate",
    "R07_gray_jpeg_q35": "200 dpi grayscale scan, JPEG q35 with heavy block artifacts",
    "R08_color_jpeg_q90": "300 dpi colour scan, JPEG q90",
    "R09_jpx": "200 dpi scan, lossy JPEG 2000 (opj_compress) embedded with JPXDecode",
    "R10_jbig2": "300 dpi 1-bit scan, JBIG2 generic region (jbig2enc)",
    "R11_fax_204x98": "standard-resolution fax: 204x98 dpi bitonal CCITT G3, stretch, noise, TTI banner",
    "R12_skew_3deg": "200 dpi flatbed scan skewed about 3 degrees",
    "R13_rotated_90_scan": "misfed scan: content rotated 90 degrees on a landscape page, /Rotate 0",
    "R14_upside_down": "misfed scan: content rotated 180 degrees, /Rotate 0",
    "R15_halftone_moire": "clustered-dot halftone print rescanned at 200 dpi, producing moire",
    "R16_low_contrast_faded": "faded toner on yellowed paper, low contrast colour JPEG",
    "R17_bleedthrough": "thin paper: mirrored ghost of the reverse side at low opacity",
    "R18_crop_margin_shadow": "uneven crop with dark scanner-bed band and lid shadow",
    "R19_mobile_pdf_compression": "phone 'share as PDF': 1200 px long edge, JPEG q50",
    "R20_scanner_ocr_layer": "300 dpi gray JPEG plus invisible Tesseract text layer (render mode 3)",
    "R21_scanner_ocr_misaligned": "R20 with the invisible text layer offset by a few points and slightly scaled",
    "R22_strip_tiled": "200 dpi page image split into horizontal strip image XObjects",
}
EXPECTED_TEXT_LAYER = {name: ("ocr" if name.startswith(("R20", "R21")) else "none") for name in VARIANTS}


# ---------------------------------------------------------------------------
# PDF writing


@dataclass
class XImage:
    """One encoded image XObject; ``None`` omits optional keys (JPX colour data lives in the codestream)."""

    filter: str | None
    colorspace: str | None
    bits: int | None
    width: int
    height: int
    data: bytes
    decode_parms: str | None = None

    @classmethod
    def of(cls, image: RasterImage) -> XImage:
        return cls(
            image.filter, image.colorspace, image.bits, image.width, image.height, image.data, image.decode_parms
        )


@dataclass
class PageSpec:
    """A page of ``width`` x ``height`` points with images placed at PDF-space rectangles (x, y, w, h)."""

    width: float
    height: float
    images: list[tuple[XImage, tuple[float, float, float, float]]]


def full_page(width: float, height: float, image: XImage) -> PageSpec:
    return PageSpec(width, height, [(image, (0.0, 0.0, width, height))])


def write_pdf(pages: Sequence[PageSpec], out: Path, identity: str) -> None:
    """Write a minimal untagged image-only PDF with no Info/XMP and a deterministic /ID."""
    import hashlib

    body: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    kids = []
    for page in pages:
        page_id = len(body) + 1
        content_id = page_id + 1
        image_ids = range(content_id + 1, content_id + 1 + len(page.images))
        kids.append(f"{page_id} 0 R")
        names = " ".join(f"/Im{i} {obj} 0 R" for i, obj in enumerate(image_ids))
        content = "\n".join(
            f"q {w:.4f} 0 0 {h:.4f} {x:.4f} {y:.4f} cm /Im{i} Do Q" for i, (_, (x, y, w, h)) in enumerate(page.images)
        ).encode()
        body.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page.width:.4f} {page.height:.4f}] "
                f"/Resources << /XObject << {names} >> >> /Contents {content_id} 0 R >>"
            ).encode()
        )
        body.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        for image, _ in page.images:
            keys = [f"/Type /XObject /Subtype /Image /Width {image.width} /Height {image.height}"]
            if image.colorspace:
                keys.append(f"/ColorSpace /{image.colorspace}")
            if image.bits:
                keys.append(f"/BitsPerComponent {image.bits}")
            if image.filter:
                keys.append(f"/Filter /{image.filter}")
            if image.decode_parms:
                keys.append(f"/DecodeParms {image.decode_parms}")
            head = f"<< {' '.join(keys)} /Length {len(image.data)} >>\nstream\n".encode()
            body.append(head + image.data + b"\nendstream")
    body[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode()
    output = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, obj in enumerate(body, start=1):
        offsets.append(len(output))
        output += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(output)
    output += f"xref\n0 {len(body) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        output += f"{offset:010d} 00000 n \n".encode()
    file_id = hashlib.md5(identity.encode(), usedforsecurity=False).hexdigest()
    output += (
        f"trailer\n<< /Size {len(body) + 1} /Root 1 0 R /ID [<{file_id}> <{file_id}>] >>\nstartxref\n{xref}\n%%EOF\n"
    ).encode()
    guard_path(out).write_bytes(bytes(output))


# ---------------------------------------------------------------------------
# Encoders


def _is_neutral(image: PILImage.Image, tolerance: int = 6) -> bool:
    import numpy as np

    if image.mode != "RGB":
        return image.mode in {"L", "1"}
    array = np.asarray(image)
    return int((array.max(axis=2).astype(np.int16) - array.min(axis=2)).max()) <= tolerance


def auto_jpeg(image: PILImage.Image, quality: int) -> XImage:
    """JPEG as gray when the scan is colour-neutral, otherwise RGB 4:2:0."""
    return XImage.of(jpeg_image(image.convert("L") if _is_neutral(image) else image.convert("RGB"), quality))


def auto_flate(image: PILImage.Image) -> XImage:
    """Lossless Flate; ``flate_image`` stores gray only when all channels are exactly equal."""
    return XImage.of(flate_image(image))


def bitonal(gray: PILImage.Image, threshold: int, blur: float = 0.0) -> PILImage.Image:
    from PIL import ImageFilter

    if blur:
        gray = gray.filter(ImageFilter.GaussianBlur(blur))
    return gray.point(lambda v: 255 if v > threshold else 0).convert("1")


def _decode_check_bitonal(recorder: Recorder, pdf: Path, expected: PILImage.Image, work: Path) -> bool:
    """Decode the single image of ``pdf`` with pdfimages and compare it bit-exactly to ``expected``."""
    import numpy as np
    from PIL import Image

    prefix = work / "decode-check"
    for old in work.glob("decode-check-*"):
        old.unlink()
    recorder.run(["pdfimages", "-png", "-f", "1", "-l", "1", pdf, prefix])
    found = sorted(work.glob("decode-check-*.png"))
    if not found:
        return False
    with Image.open(found[0]) as decoded:
        got = np.asarray(decoded.convert("L")) > 127
    want = np.asarray(expected.convert("L")) > 127
    return got.shape == want.shape and bool(np.array_equal(got, want))


def ccitt_g4(recorder: Recorder, image: PILImage.Image, work: Path, tag: str) -> XImage:
    """Encode 1-bit pixels as CCITT G4 through a libtiff TIFF and tiff2pdf, keeping its stream verbatim."""
    import pypdf

    tiff, pdf = work / f"{tag}.tif", work / f"{tag}.pdf"
    image.save(tiff, compression="group4")
    recorder.run(["tiff2pdf", "-o", pdf, tiff])
    resources: Any = pypdf.PdfReader(pdf).pages[0]["/Resources"]
    xobjects = resources["/XObject"]
    stream = next(iter(xobjects.values())).get_object()
    if stream.get("/Filter") != "/CCITTFaxDecode":
        raise RuntimeError(f"tiff2pdf wrote {stream.get('/Filter')} instead of CCITTFaxDecode")
    parms = stream["/DecodeParms"]
    text = "<< " + " ".join(f"{key} {_pdf_value(value)}" for key, value in parms.items()) + " >>"
    return XImage("CCITTFaxDecode", "DeviceGray", 1, int(stream["/Width"]), int(stream["/Height"]), stream._data, text)


def _pdf_value(value: Any) -> str:
    from pypdf.generic import BooleanObject

    if isinstance(value, (bool, BooleanObject)):
        return "true" if bool(value) else "false"
    return str(value)


def ccitt_g3_1d(recorder: Recorder, image: PILImage.Image, work: Path, tag: str) -> XImage:
    """Encode 1-bit pixels as CCITT G3 1-D (Modified Huffman, /K 0) from a single-strip libtiff TIFF."""
    from PIL import Image

    tiff = work / f"{tag}.tif"
    image.save(tiff, compression="group3", strip_size=1 << 30)
    with Image.open(tiff) as parsed:
        tags = parsed.tag_v2  # type: ignore[attr-defined]
        offsets, counts = tags[273], tags[279]
        options = int(tags.get(292, 0) or 0)
        photometric = int(tags[262])
    if len(offsets) != 1 or options & 1:
        raise RuntimeError(f"unexpected G3 TIFF layout: strips={len(offsets)} T4Options={options}")
    data = tiff.read_bytes()[offsets[0] : offsets[0] + counts[0]]
    recorder.steps.append(f"Pillow/libtiff G3 1-D single strip ({len(data)} bytes), T4Options={options}")
    black_is_1 = "true" if photometric == 1 else "false"
    parms = (
        f"<< /K 0 /Columns {image.width} /Rows {image.height} /EndOfLine true "
        f"/EncodedByteAlign {'true' if options & 4 else 'false'} /BlackIs1 {black_is_1} >>"
    )
    return XImage("CCITTFaxDecode", "DeviceGray", 1, image.width, image.height, data, parms)


# ---------------------------------------------------------------------------
# Image effects


def rotate_fill(image: PILImage.Image, angle: float, fill: int | tuple[int, int, int]) -> PILImage.Image:
    from PIL import Image

    return image.rotate(angle, Image.Resampling.BICUBIC, expand=False, fillcolor=fill)


def halftone(gray: PILImage.Image, lpi: float, dpi: float, angle_degrees: float) -> PILImage.Image:
    """Clustered-dot (Euclidean spot) AM screen producing a 1-bit image at ``dpi``."""
    import numpy as np
    from PIL import Image

    values = np.asarray(gray, dtype=np.float32) / 255.0
    height, width = values.shape
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    theta = math.radians(angle_degrees)
    cells = lpi / dpi
    u = (xx * math.cos(theta) + yy * math.sin(theta)) * cells
    v = (-xx * math.sin(theta) + yy * math.cos(theta)) * cells
    spot = (np.cos(2 * math.pi * u) + np.cos(2 * math.pi * v)) / 4 + 0.5  # in [0, 1]
    return Image.fromarray(((values > spot) * 255).astype(np.uint8))


# ---------------------------------------------------------------------------
# Measurement


def _image_records(path: Path) -> list[list[dict[str, Any]]]:
    import pypdf

    reader = pypdf.PdfReader(guard_path(path))
    pages: list[list[dict[str, Any]]] = []
    for page in reader.pages:
        resources = page.get("/Resources")
        resources = resources.get_object() if resources is not None else {}
        xobjects = resources.get("/XObject")
        xobjects = xobjects.get_object() if xobjects is not None else {}
        images = []
        for value in xobjects.values():
            obj = value.get_object()
            if obj.get("/Subtype") != "/Image":
                continue
            filters = obj.get("/Filter")
            filters = [str(f) for f in filters] if isinstance(filters, list) else ([str(filters)] if filters else [])
            colorspace = obj.get("/ColorSpace")
            if colorspace is not None:
                colorspace = colorspace.get_object()
                colorspace = str(colorspace[0]) if isinstance(colorspace, list) else str(colorspace)
            images.append(
                {
                    "filters": filters,
                    "colorspace": colorspace,
                    "bits_per_component": int(obj["/BitsPerComponent"]) if "/BitsPerComponent" in obj else None,
                    "width": int(obj["/Width"]),
                    "height": int(obj["/Height"]),
                    "encoded_bytes": len(obj._data),
                }
            )
        pages.append(images)
    return pages


def _pdfimages_ppi(path: Path) -> list[dict[str, Any]]:
    """Effective placement resolution per image from Poppler's ``pdfimages -list``."""
    result = subprocess.run(["pdfimages", "-list", str(path)], capture_output=True, text=True, check=False)
    rows = []
    for line in result.stdout.splitlines()[2:]:
        parts = line.split()
        if len(parts) >= 14 and parts[0].isdigit():
            rows.append({"page": int(parts[0]), "enc": parts[8], "x_ppi": int(parts[12]), "y_ppi": int(parts[13])})
    return rows


def _render_check(path: Path) -> dict[str, Any]:
    """Confirm page 1 renders in Poppler and pdfust (hayro) at a low resolution."""
    import numpy as np

    result: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="wild-raster-check-") as temporary:
        prefix = Path(temporary) / "page"
        run = subprocess.run(
            ["pdftoppm", "-r", "30", "-f", "1", "-l", "1", "-gray", "-png", str(path), str(prefix)],
            capture_output=True,
            text=True,
            check=False,
        )
        rendered = sorted(Path(temporary).glob("page-*.png"))
        ink = None
        if rendered:
            from PIL import Image

            with Image.open(rendered[0]) as image:
                ink = round(float((np.asarray(image.convert("L")) < 128).mean()), 5)
        result["pdftoppm"] = {
            "returncode": run.returncode,
            "stderr": run.stderr.strip()[-400:],
            "dark_fraction": ink,
            "ok": run.returncode == 0 and bool(rendered) and not run.stderr.strip(),
        }
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            pixmap = _open_pdf(path)[0].get_pixmap(dpi=30)
        samples = np.frombuffer(pixmap.samples, np.uint8).reshape(pixmap.height, pixmap.width, 4)[..., :3]
        result["pdfust"] = {
            "ok": True,
            "size": [pixmap.width, pixmap.height],
            "dark_fraction": round(float((samples.mean(axis=2) < 128).mean()), 5),
            "warnings": sorted({str(w.message) for w in caught}),
        }
    except Exception as error:
        result["pdfust"] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
    return result


def measure(path: Path) -> dict[str, Any]:
    """Measure structure (pypdf), codecs, resolution, text layer (pdfust) and renderability."""
    started = time.perf_counter()
    images = _image_records(path)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        texts = [page.get_text() for page in _open_pdf(path)]
    chars = [sum(not c.isspace() for c in text) for text in texts]
    with_text = sum(count >= PAGE_TEXT_MIN_CHARS for count in chars)
    filters = sorted({"+".join(image["filters"]) or "none" for page in images for image in page})
    colorspaces = sorted({str(image["colorspace"]) for page in images for image in page})
    bits = sorted({image["bits_per_component"] or 0 for page in images for image in page})
    ppi = _pdfimages_ppi(path)
    return {
        "page_count": len(texts),
        "page_sizes": [[round(w, 2), round(h, 2)] for w, h in page_display_sizes(path)],
        "images_per_page": [len(page) for page in images],
        "images": images,
        "filters": filters,
        "colorspaces": colorspaces,
        "bits_per_component": bits,
        "pdfimages_ppi": ppi,
        "chars_per_page": chars,
        "text_layer": "none" if with_text == 0 else ("ocr" if with_text == len(texts) else "partial"),
        "extraction_warnings": sorted({str(w.message) for w in caught}),
        "render_check": _render_check(path),
        "measure_seconds": round(time.perf_counter() - started, 4),
    }


# ---------------------------------------------------------------------------
# Tesseract


def tesseract_env(tessdata: Path | None) -> dict[str, str]:
    return {"TESSDATA_PREFIX": str(tessdata)} if tessdata is not None else {}


def tesseract_languages(tessdata: Path | None) -> set[str]:
    if shutil.which("tesseract") is None:
        return set()
    result = subprocess.run(
        ["tesseract", "--list-langs"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **tesseract_env(tessdata)},
    )
    lines = (result.stdout + result.stderr).splitlines()
    return {line.strip() for line in lines[1:] if line.strip() and " " not in line.strip()} - {"osd"}


def extra_tool_versions() -> dict[str, str | None]:
    def grep(argv: list[str], needle: str) -> str | None:
        if shutil.which(argv[0]) is None:
            return None
        result = subprocess.run(argv, capture_output=True, text=True, check=False)
        for line in (result.stdout + result.stderr).splitlines():
            if needle.lower() in line.lower():
                return line.strip()
        return "present"

    return {
        "tiff2pdf": grep(["tiff2pdf"], "libtiff"),
        "opj_compress": grep(["opj_compress", "-h"], "library v"),
        "pdfimages": grep(["pdfimages", "-v"], "version"),
        "jbig2": grep(["jbig2", "--version"], "jbig2"),
    }


# ---------------------------------------------------------------------------
# Variant builder


@dataclass
class Rasterizer:
    """Build requested raster variants for one source PDF, caching renders and the shared OCR pass."""

    source: Path
    out_dir: Path
    seed: str
    work: Path
    languages: list[str]
    tessdata: Path | None = None
    renders: dict[tuple[int, int, bool], list[Path]] = field(default_factory=dict)
    ocr_pages: list[Path] | None = None
    ocr_record: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.sizes = page_display_sizes(self.source)

    def identity(self, name: str) -> str:
        return f"{self.seed}\x1f{name}"

    def rng(self, name: str, page: int) -> np.random.Generator:
        return _rng(self.seed, name, page)

    def render(self, recorder: Recorder, dpi: int, *, gray: bool = False, dpi_y: int | None = None) -> list[Path]:
        """Render the source once per resolution and colour mode with pdftoppm."""
        key = (dpi, dpi_y or dpi, gray)
        if key not in self.renders:
            prefix = self.work / f"render-{dpi}x{dpi_y or dpi}-{'gray' if gray else 'rgb'}" / "page"
            prefix.parent.mkdir(parents=True, exist_ok=True)
            resolution = ["-r", str(dpi)] if dpi_y is None else ["-rx", str(dpi), "-ry", str(dpi_y)]
            recorder.run(["pdftoppm", *resolution, *(["-gray"] if gray else []), "-png", self.source, prefix])
            self.renders[key] = sorted(prefix.parent.glob("page-*.png"))
            recorder.steps.append(f"rendered source at {dpi}x{dpi_y or dpi} dpi ({'gray' if gray else 'rgb'})")
        return self.renders[key]

    def images(self, recorder: Recorder, dpi: int, *, gray: bool = False) -> list[PILImage.Image]:
        from PIL import Image

        loaded = []
        for path in self.render(recorder, dpi, gray=gray):
            with Image.open(path) as image:
                loaded.append(image.convert("L" if gray else "RGB"))
        return loaded

    def per_page(
        self, recorder: Recorder, name: str, dpi: int, gray: bool, effect: Callable[..., tuple[XImage, dict[str, Any]]]
    ) -> tuple[list[PageSpec], list[dict[str, Any]]]:
        pages, parameters = [], []
        for index, image in enumerate(self.images(recorder, dpi, gray=gray)):
            width, height = self.sizes[index]
            encoded, params = effect(image, self.rng(name, index), index)
            pages.append(full_page(width, height, encoded))
            parameters.append(params)
        return pages, parameters

    def build(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        builder = getattr(self, "build_" + name.split("_", 1)[0].lower())
        return builder(name, recorder, out) or {}

    # Resolution sweep -------------------------------------------------------
    def _clean(self, name: str, recorder: Recorder, out: Path, dpi: int, gray: bool) -> dict[str, Any]:
        pages, _ = self.per_page(recorder, name, dpi, gray, lambda image, _rng, _i: (auto_flate(image), {}))
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [dpi, dpi], "encoding": "Flate", "gray_when_neutral": not gray}}

    def build_r01(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        return self._clean(name, recorder, out, 72, gray=False)

    def build_r02(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        return self._clean(name, recorder, out, 100, gray=False)

    def build_r03(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        return self._clean(name, recorder, out, 150, gray=False)

    def build_r04(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        return self._clean(name, recorder, out, 600, gray=True)

    # Codecs -----------------------------------------------------------------
    def _bitonal_pages(self, name: str, recorder: Recorder) -> tuple[list[PILImage.Image], list[dict[str, Any]]]:
        pages, parameters = [], []
        for index, gray in enumerate(self.images(recorder, 300, gray=True)):
            threshold = int(self.rng(name, index).integers(140, 176))
            pages.append(bitonal(gray, threshold, blur=0.4))
            parameters.append({"threshold": threshold, "pre_blur_px": 0.4})
        return pages, parameters

    def build_r05(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        bitmaps, parameters = self._bitonal_pages(name, recorder)
        pages = [
            full_page(*self.sizes[i], ccitt_g4(recorder, bitmap, self.work, f"r05-{i}"))
            for i, bitmap in enumerate(bitmaps)
        ]
        write_pdf(pages, out, self.identity(name))
        exact = _decode_check_bitonal(recorder, out, bitmaps[0], self.work)
        recorder.steps.append("libtiff G4 TIFF -> tiff2pdf; CCITT stream and DecodeParms copied verbatim")
        return {"parameters": {"dpi": [300, 300], "pages": parameters}, "verification": {"g4_decode_exact": exact}}

    def build_r06(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        bitmaps, parameters = self._bitonal_pages(name, recorder)
        pages = [full_page(*self.sizes[i], XImage.of(flate_image(b))) for i, b in enumerate(bitmaps)]
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [300, 300], "pages": parameters}}

    def build_r07(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        pages, _ = self.per_page(
            recorder, name, 200, True, lambda image, _rng, _i: (XImage.of(jpeg_image(image, 35)), {})
        )
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [200, 200], "jpeg_quality": 35, "colour": "gray"}}

    def build_r08(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        pages, _ = self.per_page(
            recorder, name, 300, False, lambda image, _rng, _i: (XImage.of(jpeg_image(image, 90)), {})
        )
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [300, 300], "jpeg_quality": 90, "colour": "rgb", "subsampling": "4:2:0"}}

    def build_r09(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        if shutil.which("opj_compress") is None:
            raise SkipVariantError("opj_compress (OpenJPEG) is not installed")

        def encode(image: PILImage.Image, rng: np.random.Generator, index: int) -> tuple[XImage, dict[str, Any]]:
            neutral = _is_neutral(image)
            raw = self.work / f"r09-{index}.{'pgm' if neutral else 'ppm'}"
            (image.convert("L") if neutral else image).save(raw)
            ratio = int(rng.integers(20, 41))
            jp2 = self.work / f"r09-{index}.jp2"
            recorder.run(["opj_compress", "-i", raw, "-o", jp2, "-r", str(ratio), "-n", "6"])
            data = jp2.read_bytes()
            # ColorSpace/BitsPerComponent are omitted, as in many JPX producers: the JP2 colr box applies.
            return XImage("JPXDecode", None, None, image.width, image.height, data), {
                "compression_ratio": ratio,
                "components": 1 if neutral else 3,
                "jp2_bytes": len(data),
            }

        pages, parameters = self.per_page(recorder, name, 200, False, encode)
        write_pdf(pages, out, self.identity(name))
        recorder.steps.append("opj_compress lossy JP2 (6 resolution levels) wrapped as JPXDecode")
        return {"parameters": {"dpi": [200, 200], "pages": parameters}}

    def build_r10(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        if shutil.which("jbig2") is None:
            raise SkipVariantError(
                "no JBIG2 encoder (jbig2enc 'jbig2') is installed; Pillow, ImageMagick and libtiff cannot encode JBIG2"
            )
        bitmaps, parameters = self._bitonal_pages(name, recorder)
        pages = []
        for index, bitmap in enumerate(bitmaps):
            pbm = self.work / f"r10-{index}.png"
            bitmap.save(pbm)
            # Generic-region coding with PDF-ready output (no global symbol dictionary).
            data = subprocess.run(["jbig2", "-p", str(pbm)], capture_output=True, check=True).stdout
            pages.append(full_page(*self.sizes[index], XImage("JBIG2Decode", "DeviceGray", 1, *bitmap.size, data)))
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [300, 300], "pages": parameters, "mode": "generic region"}}

    # Scanner realism -------------------------------------------------------------
    def build_r11(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont

        renders = self.render(recorder, 204, gray=True, dpi_y=196)
        pages, parameters = [], []
        count = len(renders)
        for index, path in enumerate(renders):
            rng = self.rng(name, index)
            width_pt, height_pt = self.sizes[index]
            with Image.open(path) as opened:
                fine = opened.convert("L")
            # The sending machine stamps its TTI banner into the top margin at transmission time.
            draw = ImageDraw.Draw(fine)
            banner_h = int(0.16 * 196)
            draw.rectangle([0, 0, fine.width, banner_h], fill=255)
            day, hour, minute = int(rng.integers(2, 28)), int(rng.integers(8, 18)), int(rng.integers(0, 60))
            number = f"+1 {rng.integers(200, 990)} {rng.integers(200, 990)} {rng.integers(1000, 9999)}"
            banner = (
                f"MAR-{day:02d}-2026  {hour:02d}:{minute:02d}   FROM: {number}   "
                f"TO: OFFICE FAX          P.{index + 1:03d}/{count:03d}"
            )
            draw.text((int(0.25 * 204), int(0.03 * 196)), banner, fill=0, font=ImageFont.load_default(size=22))
            stretch = float(rng.uniform(1.01, 1.03))
            rows = round(height_pt / 72 * 98)
            coarse = fine.resize((fine.width, round(rows * stretch)), Image.Resampling.BOX).crop(
                (0, 0, fine.width, rows)
            )
            threshold = int(rng.integers(135, 165))
            pixels = np.asarray(coarse) > threshold
            flips = int(pixels.size * rng.uniform(1e-4, 3e-4))
            ys, xs = rng.integers(0, rows, flips), rng.integers(0, fine.width, flips)
            pixels[ys, xs] = ~pixels[ys, xs]
            dropouts = int(rng.integers(1, 4))
            dropout_rows = sorted(int(r) for r in rng.integers(banner_h // 2, rows, dropouts))
            for row in dropout_rows:
                pixels[row, :] = True  # a lost scan line arrives as white
            bitmap = Image.fromarray((pixels * 255).astype(np.uint8)).convert("1")
            if index == 0:
                first_bitmap = bitmap
            try:
                encoded = ccitt_g3_1d(recorder, bitmap, self.work, f"r11-{index}")
                codec = "CCITT G3 1-D (/K 0)"
            except Exception as error:
                recorder.steps.append(f"G3 encode failed ({error}); falling back to G4")
                encoded, codec = ccitt_g4(recorder, bitmap, self.work, f"r11-{index}"), "CCITT G4 (fallback)"
            pages.append(full_page(width_pt, height_pt, encoded))
            parameters.append(
                {
                    "vertical_stretch": round(stretch, 4),
                    "threshold": threshold,
                    "pixel_flips": flips,
                    "dropout_rows": dropout_rows,
                    "banner": banner,
                    "codec": codec,
                }
            )
        write_pdf(pages, out, self.identity(name))
        exact = _decode_check_bitonal(recorder, out, first_bitmap, self.work)
        return {
            "parameters": {"dpi": [204, 98], "pages": parameters},
            "verification": {"ccitt_decode_exact_page1": exact},
            "added_text_not_in_truth": [p["banner"] for p in parameters],
        }

    def build_r12(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        def effect(image: PILImage.Image, rng: np.random.Generator, _index: int) -> tuple[XImage, dict[str, Any]]:
            angle = float(rng.choice([-1, 1]) * rng.uniform(2.6, 3.4))
            return auto_jpeg(rotate_fill(image, angle, (250, 250, 250)), 82), {"rotation_degrees": round(angle, 3)}

        pages, parameters = self.per_page(recorder, name, 200, False, effect)
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [200, 200], "jpeg_quality": 82, "pages": parameters}}

    def _rotated(self, name: str, recorder: Recorder, out: Path, quarter_turns: list[int]) -> dict[str, Any]:
        from PIL import Image

        pages, parameters = [], []
        for index, image in enumerate(self.images(recorder, 200)):
            width, height = self.sizes[index]
            clockwise = int(self.rng(name, index).choice(quarter_turns)) * 90
            transpose = {
                90: Image.Transpose.ROTATE_270,
                180: Image.Transpose.ROTATE_180,
                270: Image.Transpose.ROTATE_90,
            }[clockwise]
            turned = image.transpose(transpose)
            if clockwise % 180:
                width, height = height, width
            pages.append(full_page(width, height, auto_jpeg(turned, 85)))
            parameters.append({"content_rotation_clockwise_degrees": clockwise, "page_rotate_key": 0})
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [200, 200], "jpeg_quality": 85, "pages": parameters}}

    def build_r13(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        return self._rotated(name, recorder, out, [1, 3])

    def build_r14(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        return self._rotated(name, recorder, out, [2])

    def build_r15(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        import numpy as np
        from PIL import Image, ImageFilter

        pages, parameters = [], []
        for index, gray in enumerate(self.images(recorder, 300, gray=True)):
            rng = self.rng(name, index)
            lpi = float(rng.uniform(85, 110))
            angle = float(rng.choice([45.0, 15.0, 75.0]))
            screened = halftone(gray, lpi, 300, angle)
            width_pt, height_pt = self.sizes[index]
            size = (round(width_pt / 72 * 200), round(height_pt / 72 * 200))
            # A rescan blurs slightly and resamples onto the 200 dpi grid; the beat with the screen is moire.
            rescanned = screened.filter(ImageFilter.GaussianBlur(0.6)).resize(size, Image.Resampling.BILINEAR)
            noisy = np.asarray(rescanned, np.float32) + rng.standard_normal(size[::-1], dtype=np.float32) * 3
            final = Image.fromarray(np.clip(noisy, 0, 255).astype(np.uint8))
            pages.append(full_page(width_pt, height_pt, XImage.of(jpeg_image(final, 80))))
            parameters.append({"screen_lpi": round(lpi, 2), "screen_angle_degrees": angle, "screen_dpi": 300})
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [200, 200], "jpeg_quality": 80, "colour": "gray", "pages": parameters}}

    def build_r16(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        import numpy as np
        from PIL import Image, ImageFilter

        def effect(image: PILImage.Image, rng: np.random.Generator, _index: int) -> tuple[XImage, dict[str, Any]]:
            pixels = np.asarray(image, np.float32) / 255.0
            height, width = pixels.shape[:2]
            strength = float(rng.uniform(0.5, 0.7))
            toner = strength * (0.75 + 0.25 * _smooth_field(rng, (height, width), (5, 7)))[..., None]
            paper = np.array([0.96, 0.92, 0.78], np.float32) + rng.uniform(-0.02, 0.02, 3).astype(np.float32)
            stain = 1 - 0.06 * _smooth_field(rng, (height, width), (3, 4))[..., None]
            faded = paper * stain * (1 - (1 - pixels) * toner)
            faded += rng.standard_normal((height, width, 1), dtype=np.float32) * np.float32(0.01)
            result = Image.fromarray((np.clip(faded, 0, 1) * 255).astype(np.uint8)).filter(
                ImageFilter.GaussianBlur(0.5)
            )
            return XImage.of(jpeg_image(result, 75)), {
                "toner_strength": round(strength, 3),
                "paper": paper.round(3).tolist(),
            }

        pages, parameters = self.per_page(recorder, name, 200, False, effect)
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [200, 200], "jpeg_quality": 75, "pages": parameters}}

    def build_r17(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        import numpy as np
        from PIL import Image, ImageFilter, ImageOps

        images = self.images(recorder, 200)
        pages, parameters = [], []
        for index, image in enumerate(images):
            rng = self.rng(name, index)
            # The reverse side is the next sheet's page when one exists, otherwise this page (duplex copy).
            back_index = index + 1 if index + 1 < len(images) else index
            back = ImageOps.mirror(images[back_index]).convert("L").resize(image.size)
            shift = (int(rng.integers(-12, 13)), int(rng.integers(-12, 13)))
            back = back.transform(back.size, Image.Transform.AFFINE, (1, 0, -shift[0], 0, 1, -shift[1]), fillcolor=255)
            back = back.filter(ImageFilter.GaussianBlur(float(rng.uniform(1.5, 2.5))))
            opacity = float(rng.uniform(0.10, 0.18))
            front = np.asarray(image, np.float32) / 255.0
            ghost = 1 - opacity * (1 - np.asarray(back, np.float32)[..., None] / 255.0)
            paper = np.array([0.975, 0.97, 0.955], np.float32)
            result = Image.fromarray((np.clip(front * ghost * paper, 0, 1) * 255).astype(np.uint8))
            pages.append(full_page(*self.sizes[index], XImage.of(jpeg_image(result, 80))))
            parameters.append({"reverse_page": back_index + 1, "opacity": round(opacity, 3), "shift_px": list(shift)})
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [200, 200], "jpeg_quality": 80, "pages": parameters}}

    def build_r18(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        import numpy as np
        from PIL import Image

        def effect(image: PILImage.Image, rng: np.random.Generator, _index: int) -> tuple[XImage, dict[str, Any]]:
            width, height = image.size
            dx, dy = int(rng.integers(-40, 41)), int(rng.integers(-30, 31))
            angle = float(rng.uniform(-0.6, 0.6))
            bed = int(rng.integers(30, 70))  # scanner bed/lid seen past the paper edge
            moved = image.transform(image.size, Image.Transform.AFFINE, (1, 0, -dx, 0, 1, -dy), fillcolor=bed)
            moved = rotate_fill(moved, angle, bed)
            gray = np.asarray(moved, np.float32)
            edges = [str(e) for e in rng.choice(["left", "right", "top", "bottom"], size=2, replace=False)]
            for edge in edges:
                band = int((width if edge in {"left", "right"} else height) * rng.uniform(0.015, 0.04))
                ramp = np.linspace(float(rng.uniform(0.25, 0.45)), 1.0, band, dtype=np.float32) ** 0.6
                if edge == "left":
                    gray[:, :band] *= ramp[None, :]
                elif edge == "right":
                    gray[:, -band:] *= ramp[::-1][None, :]
                elif edge == "top":
                    gray[:band, :] *= ramp[:, None]
                else:
                    gray[-band:, :] *= ramp[::-1][:, None]
            gray += rng.standard_normal(gray.shape, dtype=np.float32) * 2.0
            result = Image.fromarray(np.clip(gray, 0, 255).astype(np.uint8))
            return XImage.of(jpeg_image(result, 80)), {
                "crop_offset_px": [dx, dy],
                "rotation_degrees": round(angle, 3),
                "bed_gray": bed,
                "shadow_edges": edges,
            }

        pages, parameters = self.per_page(recorder, name, 200, True, effect)
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": [200, 200], "jpeg_quality": 80, "colour": "gray", "pages": parameters}}

    def build_r19(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        from PIL import Image, ImageEnhance, ImageFilter

        dpis = []

        def effect(image: PILImage.Image, rng: np.random.Generator, index: int) -> tuple[XImage, dict[str, Any]]:
            scale = 1200 / max(image.size)
            small = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
            contrast = float(rng.uniform(1.1, 1.25))
            small = ImageEnhance.Contrast(small).enhance(contrast).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
            width_pt, height_pt = self.sizes[index]
            dpi = (round(small.width / width_pt * 72, 1), round(small.height / height_pt * 72, 1))
            dpis.append(dpi)
            return XImage.of(jpeg_image(small, 50)), {"size_px": list(small.size), "contrast": round(contrast, 3)}

        pages, parameters = self.per_page(recorder, name, 200, False, effect)
        write_pdf(pages, out, self.identity(name))
        return {"parameters": {"dpi": list(dpis[0]), "jpeg_quality": 50, "long_edge_px": 1200, "pages": parameters}}

    # Scanner-software OCR ---------------------------------------------------------
    def ensure_ocr(self, name: str, recorder: Recorder) -> Path:
        """Run Tesseract once per page on a 300 dpi gray JPEG and merge the image+text PDFs with qpdf."""
        merged = self.work / "ocr-merged.pdf"
        if self.ocr_pages is not None:
            return merged
        if shutil.which("tesseract") is None:
            raise SkipVariantError("tesseract is not installed")
        selection = select_ocr_languages(self.languages, tesseract_languages(self.tessdata))
        parts = []
        for index, gray in enumerate(self.images(recorder, 300, gray=True)):
            jpeg = self.work / f"ocr-{index + 1:04d}.jpg"
            gray.save(jpeg, "JPEG", quality=75, dpi=(300, 300))
            base = self.work / f"ocr-{index + 1:04d}"
            recorder.run(
                ["tesseract", jpeg, base, "-l", "+".join(selection["used"]), "--dpi", "300", "--psm", "3", "pdf"],
                env=tesseract_env(self.tessdata),
            )
            parts.append(base.with_suffix(".pdf"))
        recorder.run(["qpdf", "--empty", "--deterministic-id", "--pages", *parts, "--", merged])
        recorder.steps.append("tesseract per-page image+invisible-text PDF (JPEG q75 gray passthrough), qpdf merge")
        self.ocr_pages = parts
        self.ocr_record = {
            "built_by": name,
            "ocr_languages": selection,
            "tessdata_prefix": str(self.tessdata) if self.tessdata else None,
            "psm": 3,
        }
        return merged

    def build_r20(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        merged = self.ensure_ocr(name, recorder)
        shutil.copyfile(merged, out)
        return {"parameters": {"dpi": [300, 300], "jpeg_quality": 75, "colour": "gray", **self.ocr_record}}

    def build_r21(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        import hashlib

        import pypdf
        from pypdf.generic import ArrayObject, ByteStringObject, DecodedStreamObject, NameObject

        merged = self.ensure_ocr(name, recorder)
        rng = self.rng(name, 0)  # cheap firmware applies one constant error to every page
        dx = float(rng.choice([-1, 1]) * rng.uniform(2.0, 6.0))
        dy = float(rng.choice([-1, 1]) * rng.uniform(2.0, 6.0))
        scale = float(rng.choice([rng.uniform(0.98, 0.993), rng.uniform(1.007, 1.02)]))
        writer = pypdf.PdfWriter(clone_from=merged)
        rewritten = 0
        for page in writer.pages:
            contents = page.get_contents()
            if contents is None:
                continue
            data = contents.get_data()
            start = data.find(b"BT")
            if start < 0:
                continue
            new = data[:start] + f"q {scale:.5f} 0 0 {scale:.5f} {dx:.3f} {dy:.3f} cm\n".encode() + data[start:]
            stream = DecodedStreamObject()
            stream.set_data(new + b"\nQ\n")
            page[NameObject("/Contents")] = writer._add_object(stream)
            page.compress_content_streams()
            rewritten += 1
        digest = hashlib.md5(self.identity(name).encode(), usedforsecurity=False).digest()
        writer._ID = ArrayObject([ByteStringObject(digest), ByteStringObject(digest)])
        with guard_path(out).open("wb") as handle:
            writer.write(handle)
        recorder.steps.append("pypdf: wrapped each page's text objects in 'q s 0 0 s dx dy cm ... Q'")
        return {
            "parameters": {
                "dpi": [300, 300],
                "text_layer_transform": {
                    "scale": round(scale, 5),
                    "offset_pdf_points": [round(dx, 3), round(dy, 3)],
                    "origin": "PDF bottom-left; display offset is (dx, -dy) plus (scale-1) x position",
                },
                "pages_rewritten": rewritten,
                **self.ocr_record,
            },
            "verification": word_displacement(merged, out),
        }

    # Mixed multi-image pages ---------------------------------------------------------
    def build_r22(self, name: str, recorder: Recorder, out: Path) -> dict[str, Any]:
        pages, single, parameters = [], [], []
        for index, image in enumerate(self.images(recorder, 200)):
            # Scanner firmware sizes the page from the pixel grid, so strip edges land on whole pixels.
            width_pt, height_pt = image.width * 72 / 200, image.height * 72 / 200
            strip = int(self.rng(name, index).choice([64, 100, 128, 256]))
            overlap = STRIP_OVERLAP_ROWS
            placements = []
            for top in range(0, image.height, strip):
                # A positive overlap would repaint shared rows to hide renderer seams; scanners do not.
                bottom = min(image.height, top + strip + overlap)
                tile = auto_flate(image.crop((0, top, image.width, bottom)))
                y = height_pt * (1 - bottom / image.height)
                placements.append((tile, (0.0, y, width_pt, height_pt * (bottom - top) / image.height)))
            pages.append(PageSpec(width_pt, height_pt, placements))
            single.append(full_page(width_pt, height_pt, auto_flate(image)))
            parameters.append({"strip_rows": strip, "overlap_rows": overlap, "strips": len(placements)})
        write_pdf(pages, out, self.identity(name))
        reference = self.work / "r22-single.pdf"
        write_pdf(single, reference, self.identity(name + "-reference"))
        verification: dict[str, Any] = {
            "strips_reassemble_exactly": strips_reassemble(recorder, out, self.render(recorder, 200)[0], self.work),
            "pdfust_200dpi": compare_pdfust(out, reference, 200),
        }
        for dpi in (100, 200):
            verification[f"pdftoppm_{dpi}dpi"] = compare_renders(
                recorder, out, reference, self.work / f"r22-{dpi}", dpi
            )
        return {"parameters": {"dpi": [200, 200], "encoding": "Flate", "pages": parameters},
                "verification": verification}  # fmt: skip


class SkipVariantError(RuntimeError):
    """A variant cannot be produced on this host (for example a missing encoder)."""


def strips_reassemble(recorder: Recorder, pdf: Path, expected_png: Path, work: Path) -> bool:
    """Decode page 1's strips with pdfimages and check they stack into the source raster bit-exactly."""
    import numpy as np
    from PIL import Image

    directory = work / "r22-strips"
    directory.mkdir(parents=True, exist_ok=True)
    recorder.run(["pdfimages", "-png", "-f", "1", "-l", "1", pdf, directory / "s"])
    strips = []
    for path in sorted(directory.glob("s-*.png")):
        with Image.open(path) as strip:
            strips.append(np.asarray(strip.convert("RGB")))
    if STRIP_OVERLAP_ROWS:  # every strip but the last carries rows that the next strip repaints
        strips = [strip[:-STRIP_OVERLAP_ROWS] for strip in strips[:-1]] + strips[-1:]
    with Image.open(expected_png) as source:
        expected = np.asarray(source.convert("RGB"))
    stacked = np.concatenate(strips)
    return stacked.shape == expected.shape and bool(np.array_equal(stacked, expected))


def compare_pdfust(first: Path, second: Path, dpi: int) -> dict[str, Any]:
    """Render page 1 of two PDFs with pdfust (hayro) and report pixel differences."""
    import numpy as np

    def pixels(path: Path) -> np.ndarray:
        pixmap = _open_pdf(path)[0].get_pixmap(dpi=dpi)
        return np.frombuffer(pixmap.samples, np.uint8).reshape(pixmap.height, pixmap.width, 4)[..., :3]

    a, b = pixels(first).astype(np.int16), pixels(second).astype(np.int16)
    diff = np.abs(a - b)
    return {
        "max_abs_diff": int(diff.max()),
        "mean_abs_diff": round(float(diff.mean()), 4),
        "fraction_over_32": round(float((diff.max(axis=2) > 32).mean()), 6),
    }


def compare_renders(recorder: Recorder, first: Path, second: Path, work: Path, dpi: int) -> dict[str, Any]:
    """Render two PDFs with pdftoppm and report per-page pixel differences."""
    import numpy as np
    from PIL import Image

    work.mkdir(parents=True, exist_ok=True)
    recorder.run(["pdftoppm", "-r", str(dpi), "-png", first, work / "a"])
    recorder.run(["pdftoppm", "-r", str(dpi), "-png", second, work / "b"])
    pages = []
    for left, right in zip(sorted(work.glob("a-*.png")), sorted(work.glob("b-*.png")), strict=True):
        with Image.open(left) as a, Image.open(right) as b:
            x, y = np.asarray(a.convert("RGB"), np.int16), np.asarray(b.convert("RGB"), np.int16)
        diff = np.abs(x - y)
        pages.append(
            {
                "max_abs_diff": int(diff.max()),
                "mean_abs_diff": round(float(diff.mean()), 4),
                "fraction_over_32": round(float((diff.max(axis=2) > 32).mean()), 6),
            }
        )
    identical = all(page["max_abs_diff"] == 0 for page in pages)
    near = all(page["fraction_over_32"] < 0.001 for page in pages)
    return {"pages": pages, "identical": identical, "visually_identical": near}


def word_displacement(before: Path, after: Path) -> dict[str, Any]:
    """Measure the display-space shift of OCR word boxes between two PDFs (page 1, matched by order)."""
    import numpy as np

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        original = _open_pdf(before)[0].get_text("words")
        moved = _open_pdf(after)[0].get_text("words")
    pairs = [(a, b) for a, b in zip(original, moved, strict=False) if a[4] == b[4]]
    if not pairs:
        return {"matched_words": 0}
    shift = np.array([[(b[0] + b[2] - a[0] - a[2]) / 2, (b[1] + b[3] - a[1] - a[3]) / 2] for a, b in pairs])
    return {
        "matched_words": len(pairs),
        "words_before": len(original),
        "words_after": len(moved),
        "mean_display_shift_points": [round(float(v), 3) for v in shift.mean(axis=0)],
        "min_display_shift_points": [round(float(v), 3) for v in shift.min(axis=0)],
        "max_display_shift_points": [round(float(v), 3) for v in shift.max(axis=0)],
    }


# ---------------------------------------------------------------------------
# Orchestration


def _resources(
    recorder: Recorder, wall: float, hwm_reset: bool, before: tuple[Any, Any], after: tuple[Any, Any]
) -> dict[str, Any]:
    (self_before, children_before), (self_after, children_after) = before, after
    return {
        "wall_seconds": round(wall, 4),
        "cpu_self_seconds": round(
            self_after.ru_utime - self_before.ru_utime + self_after.ru_stime - self_before.ru_stime, 4
        ),
        "cpu_children_seconds": round(
            sum(c["cpu_user_seconds"] + c["cpu_system_seconds"] for c in recorder.commands), 4
        ),
        "cpu_children_rusage_delta_seconds": round(
            children_after.ru_utime - children_before.ru_utime + children_after.ru_stime - children_before.ru_stime,
            4,
        ),
        "peak_rss_self_kib": _read_hwm_kib() if hwm_reset else None,
        "peak_rss_self_scope": "variant (VmHWM reset)" if hwm_reset else "unmeasured",
        "peak_rss_children_kib": max((c["peak_rss_kib"] for c in recorder.commands), default=None),
    }


def _languages_for(doc_dir: Path) -> list[str]:
    truth = doc_dir / "truth.json"
    if truth.is_file():
        languages = json.loads(guard_path(truth).read_text()).get("languages")
        if isinstance(languages, list) and all(isinstance(tag, str) for tag in languages):
            return languages
    return ["en"]


def rasterize(
    source_pdf: Path,
    out_dir: Path,
    variants: Sequence[str] | None = None,
    *,
    seed: str,
    languages: Sequence[str] = ("en",),
    tessdata: Path | None = None,
) -> dict[str, Any]:
    """Write ``out_dir/{variant}.pdf`` for each requested variant plus ``raster.json``; return the record."""
    source = guard_path(Path(source_pdf))
    out_dir = guard_path(Path(out_dir))
    requested = list(variants) if variants is not None else list(VARIANTS)
    unknown = [name for name in requested if name not in VARIANTS]
    if unknown:
        raise ValueError(f"Unknown variants: {unknown}")
    out_dir.mkdir(parents=True, exist_ok=True)
    records: dict[str, Any] = {}
    skipped: dict[str, str] = {}
    errors: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="wild-raster-") as temporary:
        work = Path(temporary)
        rasterizer = Rasterizer(source, out_dir, seed, work, list(languages), tessdata)
        for name in requested:
            out = guard_path(out_dir / f"{name}.pdf")
            recorder = Recorder({str(work): "$WORK", str(out_dir): "$OUT", str(source): "$SOURCE"})
            hwm_reset = _reset_hwm()
            before = (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN))
            started = time.perf_counter()
            try:
                details = rasterizer.build(name, recorder, out)
            except SkipVariantError as reason:
                skipped[name] = str(reason)
                out.unlink(missing_ok=True)
                continue
            except Exception as error:
                errors[name] = f"{type(error).__name__}: {error}"
                out.unlink(missing_ok=True)
                continue
            wall = time.perf_counter() - started
            after = (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN))
            resources = _resources(recorder, wall, hwm_reset, before, after)
            try:
                measured = measure(out)
            except Exception as error:
                measured = {"error": f"{type(error).__name__}: {error}"}
            parameters = details.pop("parameters", {})
            dpi = parameters.get("dpi")
            records[name] = {
                "name": name,
                "description": VARIANTS[name],
                "output": out.name,
                "output_sha256": sha256_file(out),
                "output_bytes": out.stat().st_size,
                "seed": f"{seed}/{name}",
                "dpi": dpi,
                "colour_modes": measured.get("colorspaces"),
                "filters": measured.get("filters"),
                "images_per_page": measured.get("images_per_page"),
                "page_count": measured.get("page_count"),
                "text_layer": measured.get("text_layer"),
                "expected_text_layer": EXPECTED_TEXT_LAYER[name],
                "matches_expected": measured.get("text_layer") == EXPECTED_TEXT_LAYER[name],
                "parameters": parameters,
                **details,
                "measured": measured,
                "commands": recorder.commands,
                "steps": recorder.steps,
                "resources": resources,
            }
    record: dict[str, Any] = {
        "version": SCHEMA,
        "seed": seed,
        "source": {"path": source.name, "sha256": sha256_file(source), "languages": list(languages)},
        "tools": {**tool_versions(), **extra_tool_versions()},
        "measurement": {
            "codecs": "pypdf image XObject /Filter, /ColorSpace, /BitsPerComponent; ppi from pdfimages -list",
            "text": f"pdfust Page.get_text(); a page has text at >= {PAGE_TEXT_MIN_CHARS} non-space chars",
            "render_check": "page 1 at 30 dpi with pdftoppm and pdfust get_pixmap",
            "resources": "wall: perf_counter; self CPU: RUSAGE_SELF delta; child CPU and peak RSS: os.wait4 per "
            "subprocess (plus RUSAGE_CHILDREN delta); self peak RSS: /proc/self VmHWM reset per variant; "
            "renders cached across variants are charged to the first variant that needs them; "
            "measurement time is excluded",
            "host": {"cpus": os.cpu_count(), "platform": sys.platform},
            "source_date_epoch": SOURCE_DATE_EPOCH,
        },
        "variants": records,
        "skipped": skipped,
        "errors": errors,
    }
    path = out_dir / "raster.json"
    previous: dict[str, Any] = {}
    if variants is not None and path.is_file():  # partial runs merge into the existing record
        previous = json.loads(path.read_text())
        for key in ("variants", "skipped", "errors"):
            merged = {k: v for k, v in previous.get(key, {}).items() if k not in requested}
            merged.update(record[key])
            record[key] = dict(sorted(merged.items()))
    temporary_json = out_dir / "raster.json.tmp"
    temporary_json.write_text(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    temporary_json.replace(path)
    return record


def _rasterize_doc(arguments: tuple[str, str, list[str] | None, str, list[str], str | None]) -> tuple[str, Any]:
    source, out_dir, variants, seed, languages, tessdata = arguments
    try:
        return source, rasterize(
            Path(source),
            Path(out_dir),
            variants,
            seed=seed,
            languages=languages,
            tessdata=Path(tessdata) if tessdata else None,
        )
    except Exception as error:
        return source, f"{type(error).__name__}: {error}"


def main(argv: Sequence[str] | None = None) -> int:
    """Rasterize every ``variants/*/L0_tagged.pdf`` under a wild-v1 directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--docs", nargs="*", help="document IDs (default: all)")
    parser.add_argument("--variants", nargs="*", choices=list(VARIANTS), help="variants (default: all)")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", default="wild-v1-raster")
    args = parser.parse_args(argv)
    directory = guard_path(args.directory)
    sources = sorted(guard_path(path) for path in (directory / "variants").glob(f"*/{SOURCE_LEVEL}.pdf"))
    if args.docs:
        sources = [path for path in sources if path.parent.name in set(args.docs)]
    if not sources:
        print(f"no variants/*/{SOURCE_LEVEL}.pdf found", file=sys.stderr)
        return 1
    tessdata = directory / "tessdata"
    jobs = [
        (
            str(path),
            str(path.parent),
            args.variants,
            f"{args.seed}/{path.parent.name}",
            _languages_for(directory / "docs" / path.parent.name),
            str(tessdata) if tessdata.is_dir() else None,
        )
        for path in sources
    ]
    failures = 0
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for source, result in pool.map(_rasterize_doc, jobs):
            doc_id = Path(source).parent.name
            if isinstance(result, str):
                failures += 1
                print(f"{doc_id}: FAILED {result}", file=sys.stderr)
                continue
            built = result["variants"]
            size = sum(record["output_bytes"] for record in built.values())
            mismatched = [name for name, record in built.items() if not record["matches_expected"]]
            print(
                f"{doc_id}: {len(built)} built, {len(result['skipped'])} skipped, {len(result['errors'])} errors, "
                f"{size / 1e6:.1f} MB" + (f", text-layer mismatch {mismatched}" if mismatched else "")
            )
            for name, error in result["errors"].items():
                print(f"  {name}: {error}", file=sys.stderr)
            failures += bool(result["errors"])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
