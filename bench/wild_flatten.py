"""Derive wild-v1 flattening levels L0-L9 from one born-digital PDF, using CPU only.

Every level is deterministic for a given source PDF, seed and tool versions.
External tools (Ghostscript, Poppler, Tesseract, qpdf) run as subprocesses
whose CPU time and peak RSS are collected individually through ``os.wait4``;
in-process Pillow/NumPy/pypdf/pylopdf work is measured with ``RUSAGE_SELF``
deltas and a per-level reset of the Linux ``VmHWM`` high-water mark.
See ``bench/WILD_CORPUS.md`` for the level contract.
"""

# Heterogeneous artifact dictionaries retain tool observations and parameters.
# ruff: noqa: EM102, TRY003, PLR2004, PLR0913, PLR0912, C901, S603, SLF001, PLC0415, D102, ANN401, PLR0911, S607

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import resource
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import warnings
import zlib
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench.silver import guard_path

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    import numpy as np
    from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "bench/results/pdf-master-artifacts/wild-v1"
SCHEMA = 1
SOURCE_DATE_EPOCH = "1767225600"  # 2026-01-01T00:00:00Z, fixed producer timestamps.

LEVELS: dict[str, str] = {
    "L0_tagged": "native",
    "L1_untagged": "native",
    "L2_stripped": "native",
    "L3_outlined": "none",
    "L4_raster": "none",
    "L5_raster_ocr": "ocr",
    "L6_phone_scan": "none",
    "L7_photocopy": "none",
    "L8_mixed": "partial",
    "L9_broken_tounicode": "broken",
}
# Measured outcomes that satisfy each expectation. A ToUnicode-free font may
# still decode through its encoding, or yield nothing at all.
ACCEPTED: dict[str, set[str]] = {
    "native": {"native"},
    "none": {"none"},
    "ocr": {"ocr"},
    "partial": {"partial"},
    "broken": {"broken", "none"},
}
TESSERACT_LANGUAGES = {
    "en": "eng", "ja": "jpn", "zh-cn": "chi_sim", "zh-hans": "chi_sim", "zh-tw": "chi_tra",
    "zh-hant": "chi_tra", "zh": "chi_sim", "ko": "kor", "ar": "ara", "he": "heb", "hi": "hin",
    "th": "tha", "ru": "rus", "uk": "ukr", "el": "ell", "de": "deu", "fr": "fra", "es": "spa",
    "pl": "pol", "vi": "vie", "tr": "tur", "it": "ita", "pt": "por", "nl": "nld",
}  # fmt: skip
PAGE_TEXT_MIN_CHARS = 5
# Prerequisites are built (and measured) separately before a dependent level starts.
DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "L2_stripped": ("L1_untagged",),
    "L3_outlined": ("L1_untagged",),
    "L8_mixed": ("L1_untagged", "L4_raster"),
    "L9_broken_tounicode": ("L1_untagged",),
}


def sha256_file(path: Path) -> str:
    """Hash one file in chunks."""
    digest = hashlib.sha256()
    with guard_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rng(seed: str, *parts: object) -> np.random.Generator:
    """Derive an independent deterministic generator for one level/page."""
    import numpy as np

    material = "\x1f".join([seed, *map(str, parts)]).encode()
    return np.random.default_rng(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _pdf_module() -> Any:
    """Prefer the ``jev_pdf`` import, falling back to the ``pylopdf`` compatibility name."""
    import importlib

    try:
        return importlib.import_module("jev_pdf")
    except ImportError:  # pragma: no cover - compatibility import
        return importlib.import_module("pylopdf")


def _open_pdf(path: Path) -> Any:
    return _pdf_module().open(guard_path(path))


# ---------------------------------------------------------------------------
# Resource accounting


def _reset_hwm() -> bool:
    """Reset this process's VmHWM so the next read is a per-level peak (Linux only)."""
    try:
        Path("/proc/self/clear_refs").write_text("5")
    except OSError:
        return False
    return True


def _read_hwm_kib() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    except OSError:
        return None
    return None


@dataclass
class Recorder:
    """Run subprocesses while recording argv, CPU time and peak RSS per command."""

    replacements: dict[str, str] = field(default_factory=dict)
    commands: list[dict[str, Any]] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)

    def display(self, argv: Sequence[str | Path]) -> list[str]:
        """Replace temporary and output prefixes with stable placeholders."""
        shown = []
        for arg in map(str, argv):
            text = arg
            for prefix, label in self.replacements.items():
                text = text.replace(prefix, label)
            shown.append(text)
        return shown

    def run(self, argv: Sequence[str | Path], *, env: dict[str, str] | None = None) -> str:
        """Run one command to completion and return its stdout."""
        merged = {**os.environ, "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH, "OMP_THREAD_LIMIT": "1", "LC_ALL": "C"}
        merged.update(env or {})
        start = time.perf_counter()
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            process = subprocess.Popen([str(a) for a in argv], stdout=out, stderr=err, env=merged)
            _, status, usage = os.wait4(process.pid, 0)
            process.returncode = os.waitstatus_to_exitcode(status)
            out.seek(0)
            err.seek(0)
            stdout = out.read().decode(errors="replace")
            stderr = err.read().decode(errors="replace")
        self.commands.append(
            {
                "argv": self.display(argv),
                "returncode": process.returncode,
                "wall_seconds": round(time.perf_counter() - start, 4),
                "cpu_user_seconds": round(usage.ru_utime, 4),
                "cpu_system_seconds": round(usage.ru_stime, 4),
                "peak_rss_kib": usage.ru_maxrss,
            }
        )
        if process.returncode != 0:
            raise RuntimeError(f"{argv[0]} failed ({process.returncode}): {stderr.strip()[-800:]}")
        return stdout


def tool_versions() -> dict[str, str | None]:
    """Record versions of every external tool and library used by the levels."""

    def first_line(argv: list[str]) -> str | None:
        if shutil.which(argv[0]) is None:
            return None
        try:
            result = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=30)
        except OSError:
            return None
        text = (result.stdout or result.stderr).strip().splitlines()
        return text[0] if text else None

    import numpy as np
    import PIL
    import pypdf

    pdf = _pdf_module()
    return {
        "ghostscript": first_line(["gs", "--version"]),
        "pdftoppm": first_line(["pdftoppm", "-v"]),
        "tesseract": first_line(["tesseract", "--version"]),
        "qpdf": first_line(["qpdf", "--version"]),
        "python": sys.version.split()[0],
        "pypdf": pypdf.__version__,
        "pillow": PIL.__version__,
        "numpy": np.__version__,
        pdf.__name__: getattr(pdf, "__version__", None),
    }


def tesseract_languages() -> set[str]:
    """List installed Tesseract language data."""
    if shutil.which("tesseract") is None:
        return set()
    result = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, check=False)
    lines = (result.stdout + result.stderr).splitlines()
    return {line.strip() for line in lines[1:] if line.strip() and " " not in line.strip()}


def select_ocr_languages(bcp47: Sequence[str], installed: set[str]) -> dict[str, Any]:
    """Map BCP 47 tags to installed Tesseract codes, recording anything missing explicitly."""
    wanted: list[str] = []
    unmapped: list[str] = []
    for tag in bcp47 or ["en"]:
        key = tag.lower()
        code = TESSERACT_LANGUAGES.get(key) or TESSERACT_LANGUAGES.get(key.split("-")[0])
        if code is None:
            unmapped.append(tag)
        elif code not in wanted:
            wanted.append(code)
    available = [code for code in wanted if code in installed]
    missing = [code for code in wanted if code not in installed]
    used = available or ["eng"]
    return {
        "requested_bcp47": list(bcp47),
        "wanted": wanted,
        "used": used,
        "missing_traineddata": missing,
        "unmapped_tags": unmapped,
        "fallback_to_eng": not available,
    }


# ---------------------------------------------------------------------------
# PDF helpers


def page_display_sizes(path: Path) -> list[tuple[float, float]]:
    """Return rotation-resolved CropBox sizes in points."""
    import pypdf

    sizes = []
    for page in pypdf.PdfReader(guard_path(path)).pages:
        box = page.cropbox
        width, height = float(box.width), float(box.height)
        if int(page.get("/Rotate", 0) or 0) % 180 == 90:
            width, height = height, width
        sizes.append((width, height))
    return sizes


@dataclass
class RasterImage:
    """One encoded PDF image XObject."""

    filter: str
    colorspace: str
    bits: int
    width: int
    height: int
    data: bytes
    decode_parms: str | None = None


def flate_image(image: PILImage.Image) -> RasterImage:
    """Encode a Pillow image losslessly with Flate, storing gray when channels agree."""
    import numpy as np

    if image.mode == "1":
        return RasterImage("FlateDecode", "DeviceGray", 1, *image.size, zlib.compress(image.tobytes(), 6))
    if image.mode == "RGB":
        array = np.asarray(image)
        if np.array_equal(array[..., 0], array[..., 1]) and np.array_equal(array[..., 1], array[..., 2]):
            image = image.convert("L")
    if image.mode == "L":
        return RasterImage("FlateDecode", "DeviceGray", 8, *image.size, zlib.compress(image.tobytes(), 6))
    image = image.convert("RGB")
    return RasterImage("FlateDecode", "DeviceRGB", 8, *image.size, zlib.compress(image.tobytes(), 6))


def jpeg_image(image: PILImage.Image, quality: int) -> RasterImage:
    """Encode a Pillow image as baseline JPEG for DCT passthrough."""
    buffer = io.BytesIO()
    image = image.convert("RGB") if image.mode not in {"RGB", "L"} else image
    image.save(buffer, "JPEG", quality=quality, subsampling=2, optimize=False)
    colorspace = "DeviceGray" if image.mode == "L" else "DeviceRGB"
    return RasterImage("DCTDecode", colorspace, 8, *image.size, buffer.getvalue())


def write_image_pdf(pages: Sequence[tuple[float, float, RasterImage]], out: Path, identity: str) -> None:
    """Write a minimal untagged PDF with one full-page image per page and no Info/XMP."""
    objects: list[bytes] = []
    kids = []
    for index, (width, height, image) in enumerate(pages):
        page_id, content_id, image_id = 3 + 3 * index, 4 + 3 * index, 5 + 3 * index
        kids.append(f"{page_id} 0 R")
        parms = f" /DecodeParms {image.decode_parms}" if image.decode_parms else ""
        image_head = (
            f"<< /Type /XObject /Subtype /Image /Width {image.width} /Height {image.height} "
            f"/ColorSpace /{image.colorspace} /BitsPerComponent {image.bits} /Filter /{image.filter}{parms} "
            f"/Length {len(image.data)} >>\nstream\n"
        ).encode()
        content = f"q {width:.4f} 0 0 {height:.4f} 0 0 cm /Im0 Do Q".encode()
        objects.extend(
            [
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.4f} {height:.4f}] "
                    f"/Resources << /XObject << /Im0 {image_id} 0 R >> >> /Contents {content_id} 0 R >>"
                ).encode(),
                b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
                image_head + image.data + b"\nendstream",
            ]
        )
    pages_dict = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>"
    header = [b"<< /Type /Catalog /Pages 2 0 R >>", pages_dict.encode()]
    body = header + objects
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


def _strip_marked_content(operations: list[tuple[Any, bytes]]) -> list[tuple[Any, bytes]]:
    """Drop structural BDC/BMC/EMC markers while keeping optional-content markers."""
    kept: list[tuple[Any, bytes]] = []
    stack: list[bool] = []
    for operands, operator in operations:
        if operator in {b"BDC", b"BMC"}:
            keep = bool(operands) and operands[0] == "/OC"
            stack.append(keep)
            if keep:
                kept.append((operands, operator))
        elif operator == b"EMC":
            if stack.pop() if stack else True:
                kept.append((operands, operator))
        else:
            kept.append((operands, operator))
    return kept


def _font_dicts(writer: Any) -> list[Any]:
    """Collect every font dictionary, including descendants, direct fonts and Type3 resources."""
    from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

    found: dict[int, Any] = {}
    seen: set[int] = set()

    def visit(node: Any, depth: int = 0) -> None:
        if depth > 64:
            return
        if isinstance(node, IndirectObject):
            key = (node.idnum << 16) | node.generation
            if key in seen:
                return
            seen.add(key)
            node = node.get_object()
        if isinstance(node, DictionaryObject):
            if node.get("/Type") == "/Font" or "/ToUnicode" in node or "/DescendantFonts" in node:
                found[id(node)] = node
            for key, value in node.items():
                if key not in {"/Parent", "/P"}:
                    visit(value, depth + 1)
        elif isinstance(node, ArrayObject):
            for value in node:
                visit(value, depth + 1)

    for page in writer.pages:
        visit(page.get("/Resources"))
    for obj in writer._objects:
        if obj is not None:
            visit(obj)
    return list(found.values())


def rewrite_pdf(
    source: Path,
    out: Path,
    identity: str,
    *,
    strip_structure: bool = False,
    strip_metadata: bool = False,
    strip_tounicode: bool = False,
) -> dict[str, Any]:
    """Rewrite with pypdf, removing structure, metadata or ToUnicode, with a deterministic /ID."""
    import pypdf
    from pypdf.generic import ArrayObject, ByteStringObject, ContentStream, NameObject

    writer = pypdf.PdfWriter(clone_from=guard_path(source))
    root = writer._root_object
    report: dict[str, Any] = {}
    if strip_structure:
        removed = [key for key in ("/StructTreeRoot", "/MarkInfo", "/Outlines", "/Lang", "/PageMode") if key in root]
        for key in removed:
            del root[key]
        names = root.get("/Names")
        if names is not None and "/Dests" in names.get_object():
            del names.get_object()["/Dests"]
        markers = 0
        for page in writer.pages:
            for key in ("/StructParents", "/Tabs"):
                if key in page:
                    del page[key]
            contents = page.get_contents()
            if contents is None:
                continue
            stream = ContentStream(contents, writer)
            before = len(stream.operations)
            stream.operations = _strip_marked_content(stream.operations)
            markers += before - len(stream.operations)
            page.replace_contents(stream)
            page.compress_content_streams()
        report["removed_catalog_keys"] = removed
        report["removed_marked_content_operators"] = markers
    if strip_metadata:
        report["removed_xmp"] = "/Metadata" in root
        if "/Metadata" in root:
            del root["/Metadata"]
        writer.metadata = None
    if strip_tounicode:
        deleted = 0
        fonts = _font_dicts(writer)
        for font in fonts:
            if "/ToUnicode" in font:
                del font[NameObject("/ToUnicode")]
                deleted += 1
        report["fonts_seen"] = len(fonts)
        report["tounicode_deleted"] = deleted
    digest = hashlib.md5(identity.encode(), usedforsecurity=False).digest()
    writer._ID = ArrayObject([ByteStringObject(digest), ByteStringObject(digest)])
    writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
    with guard_path(out).open("wb") as handle:
        writer.write(handle)
    return report


# ---------------------------------------------------------------------------
# Region filtering for L8 single-page documents


def _mul(a: Sequence[float], b: Sequence[float]) -> list[float]:
    """Multiply two PDF matrices [a b c d e f] in row-vector order (a then b)."""
    return [
        a[0] * b[0] + a[1] * b[2],
        a[0] * b[1] + a[1] * b[3],
        a[2] * b[0] + a[3] * b[2],
        a[2] * b[1] + a[3] * b[3],
        a[4] * b[0] + a[5] * b[2] + b[4],
        a[4] * b[1] + a[5] * b[3] + b[5],
    ]


def _apply(m: Sequence[float], x: float, y: float) -> tuple[float, float]:
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


PATH_CONSTRUCTION = {b"m", b"l", b"c", b"v", b"y", b"h", b"re"}
PATH_PAINT = {b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*", b"n"}
TEXT_SHOW = {b"Tj", b"TJ", b"'", b'"'}


def filter_region(
    operations: list[tuple[Any, bytes]], region: tuple[float, float, float, float], to_display: Callable
) -> tuple[list[tuple[Any, bytes]], dict[str, int]]:
    """Remove text runs, paths and images that lie inside a display-space region.

    Text is judged by its run origin; paths and images only when their whole
    bounding box is inside. TJ advances are not tracked, which is adequate for
    full-width regions where a removed run cannot shift text outside the region.
    """
    x0, y0, x1, y1 = region

    def inside(points: list[tuple[float, float]]) -> bool:
        shown = [to_display(*point) for point in points]
        return all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in shown)

    ctm = [1.0, 0, 0, 1, 0, 0]
    stack: list[list[float]] = []
    tm = [1.0, 0, 0, 1, 0, 0]
    tlm = tm[:]
    leading = 0.0
    pending: list[tuple[Any, bytes]] = []
    points: list[tuple[float, float]] = []
    kept: list[tuple[Any, bytes]] = []
    counts = {"text_runs": 0, "paths": 0, "images": 0}

    def next_line() -> None:
        nonlocal tm, tlm
        tlm = _mul([1, 0, 0, 1, 0, -leading], tlm)
        tm = tlm[:]

    for operands, operator in operations:
        if operator in PATH_CONSTRUCTION:
            values = [float(v) for v in operands]
            if operator == b"re":
                x, y, w, h = values
                points += [_apply(ctm, x, y), _apply(ctm, x + w, y), _apply(ctm, x, y + h), _apply(ctm, x + w, y + h)]
            else:
                points += [_apply(ctm, values[i], values[i + 1]) for i in range(0, len(values) - 1, 2)]
            pending.append((operands, operator))
            continue
        if operator in PATH_PAINT and pending:
            if points and inside(points) and operator != b"n":
                counts["paths"] += 1
            else:
                kept.extend(pending)
                kept.append((operands, operator))
            pending, points = [], []
            continue
        if pending:  # clipping operators W/W* sit between construction and painting.
            pending.append((operands, operator))
            continue
        if operator == b"q":
            stack.append(ctm[:])
        elif operator == b"Q":
            ctm = stack.pop() if stack else ctm
        elif operator == b"cm":
            ctm = _mul([float(v) for v in operands], ctm)
        elif operator == b"BT":
            tm, tlm = [1.0, 0, 0, 1, 0, 0], [1.0, 0, 0, 1, 0, 0]
        elif operator == b"Tm":
            tm = [float(v) for v in operands]
            tlm = tm[:]
        elif operator in {b"Td", b"TD"}:
            tx, ty = float(operands[0]), float(operands[1])
            if operator == b"TD":
                leading = -ty
            tlm = _mul([1, 0, 0, 1, tx, ty], tlm)
            tm = tlm[:]
        elif operator == b"TL":
            leading = float(operands[0])
        elif operator == b"T*":
            next_line()
        elif operator in TEXT_SHOW:
            if operator in {b"'", b'"'}:
                next_line()
            origin = _apply(_mul(tm, ctm), 0, 0)
            if inside([origin]):
                counts["text_runs"] += 1
                if operator == b'"':  # keep its spacing side effects
                    kept.append(([operands[0]], b"Tw"))
                    kept.append(([operands[1]], b"Tc"))
                continue
        elif operator == b"Do":
            corners = [_apply(ctm, 0, 0), _apply(ctm, 1, 0), _apply(ctm, 0, 1), _apply(ctm, 1, 1)]
            if inside(corners):
                counts["images"] += 1
                continue
        kept.append((operands, operator))
    kept.extend(pending)
    return kept, counts


# ---------------------------------------------------------------------------
# Image degradation


def _smooth_field(rng: np.random.Generator, shape: tuple[int, int], cells: tuple[int, int]) -> np.ndarray:
    """Low-frequency noise in [0, 1], bicubically upsampled from a coarse grid."""
    import numpy as np
    from PIL import Image

    coarse = rng.random((cells[1], cells[0])).astype(np.float32)
    image = Image.fromarray((coarse * 255).astype(np.uint8)).resize((shape[1], shape[0]), Image.Resampling.BICUBIC)
    return np.asarray(image, dtype=np.float32) / 255.0


def _perspective_coeffs(dst: Sequence[tuple[float, float]], src: Sequence[tuple[float, float]]) -> list[float]:
    """Pillow PERSPECTIVE coefficients mapping output points ``dst`` to input points ``src``."""
    import numpy as np

    rows, rhs = [], []
    for (x, y), (u, v) in zip(dst, src, strict=True):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        rhs += [u, v]
    return [float(c) for c in np.linalg.solve(np.array(rows, float), np.array(rhs, float))]


def phone_scan(page: PILImage.Image, rng: np.random.Generator) -> tuple[PILImage.Image, dict[str, Any]]:
    """Simulate a hand-held phone capture of a printed page."""
    import numpy as np
    from PIL import Image, ImageFilter

    width, height = page.size
    paper = np.array([0.965, 0.95, 0.91]) + rng.uniform(-0.015, 0.015, 3)
    tinted = np.asarray(page.convert("RGB"), dtype=np.float32) / 255.0 * paper.astype(np.float32)
    page = Image.fromarray((tinted * 255).astype(np.uint8))

    angle = float(rng.choice([-1, 1]) * rng.uniform(0.6, 2.0))
    margin = rng.uniform(0.02, 0.04)
    keystone = rng.uniform(0.005, 0.02)
    top_heavy = bool(rng.random() < 0.5)
    corners = np.array([[0, 0], [width, 0], [width, height], [0, height]], float)
    inset = np.array([[margin, margin], [-margin, margin], [-margin, -margin], [margin, -margin]]) * [width, height]
    shrink = keystone * width * np.array([1, -1, 0, 0] if top_heavy else [0, 0, -1, 1], float)
    corners = corners + inset + rng.uniform(-0.006, 0.006, (4, 2)) * [width, height]
    corners[:, 0] += shrink
    centre = corners.mean(axis=0)
    theta = math.radians(angle)
    rotation = np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
    corners = (corners - centre) @ rotation.T + centre
    source = [(0, 0), (width, 0), (width, height), (0, height)]
    coeffs = _perspective_coeffs([tuple(c) for c in corners], source)
    warped = page.transform((width, height), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    mask = Image.new("L", page.size, 255).transform(
        (width, height), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC, fillcolor=0
    )
    desk_base = np.array([0.42, 0.33, 0.25]) if rng.random() < 0.6 else np.array([0.32, 0.33, 0.35])
    grain = (
        _smooth_field(rng, (height, width), (5, 7)) * 0.14
        + _smooth_field(rng, (height, width), (3, 90)) * 0.05  # streaky wood/fabric grain
        - 0.095
    )[..., None]
    desk = np.clip(desk_base.astype(np.float32) + grain, 0, 1).astype(np.float32)
    page_array = np.asarray(warped, dtype=np.float32) / 255.0
    alpha = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32)[..., None] / 255.0
    photo = page_array * alpha + desk * (1 - alpha)

    blur = float(rng.uniform(0.55, 1.0))
    photo = (
        np.asarray(
            Image.fromarray((np.clip(photo, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)),
            dtype=np.float32,
        )
        / 255.0
    )

    # Lighting is smooth, so compute it at quarter resolution and upsample.
    small_w, small_h = max(8, width // 4), max(8, height // 4)
    yy, xx = np.mgrid[0:small_h, 0:small_w].astype(np.float32)
    nx, ny = xx / small_w - 0.5, yy / small_h - 0.5
    direction = rng.uniform(0, 2 * math.pi)
    gradient_strength = rng.uniform(0.08, 0.2)
    gradient = 1 - gradient_strength * (0.5 + nx * math.cos(direction) + ny * math.sin(direction))
    vignette_strength = rng.uniform(0.12, 0.25)
    vignette = 1 - vignette_strength * (nx**2 + ny**2) * 2
    shadow_angle = rng.uniform(0, 2 * math.pi)
    shadow_offset = rng.uniform(0.25, 0.4)
    shadow_strength = rng.uniform(0.12, 0.28)
    half_plane = ((nx * math.cos(shadow_angle) + ny * math.sin(shadow_angle)) > shadow_offset).astype(np.uint8) * 255
    soft = (
        np.asarray(Image.fromarray(half_plane).filter(ImageFilter.GaussianBlur(small_w * 0.035)), dtype=np.float32)
        / 255.0
    )
    small_light = (gradient * vignette * (1 - shadow_strength * soft)).astype(np.float32)
    light_image = Image.fromarray(small_light).resize((width, height), Image.Resampling.BILINEAR)
    lighting = np.asarray(light_image, dtype=np.float32)[..., None]
    warm = bool(rng.random() < 0.6)
    cast = np.array([1.04, 1.0, 0.92] if warm else [0.95, 0.99, 1.05]) + rng.uniform(-0.01, 0.01, 3)
    photo = photo * lighting * cast.astype(np.float32)
    sigma = float(rng.uniform(0.012, 0.022))
    photo += rng.standard_normal((height, width, 1), dtype=np.float32) * np.float32(sigma)
    photo += rng.standard_normal((height, width, 3), dtype=np.float32) * np.float32(sigma * 0.45)
    result = Image.fromarray((np.clip(photo, 0, 1) * 255).astype(np.uint8))
    quality = int(rng.integers(55, 66))
    return result, {
        "rotation_degrees": round(angle, 3),
        "margin_fraction": round(float(margin), 4),
        "keystone_fraction": round(float(keystone), 4),
        "keystone_top": top_heavy,
        "blur_radius_px": round(blur, 3),
        "gradient_strength": round(float(gradient_strength), 3),
        "vignette_strength": round(float(vignette_strength), 3),
        "shadow_strength": round(float(shadow_strength), 3),
        "colour_cast": "warm" if warm else "cool",
        "noise_sigma": round(sigma, 4),
        "jpeg_quality": quality,
    }


def photocopy(page: PILImage.Image, rng: np.random.Generator) -> tuple[PILImage.Image, dict[str, Any]]:
    """Simulate a worn office photocopier: contrast, toner variation, skew, streaks and speckle."""
    import numpy as np
    from PIL import Image, ImageFilter

    gray = np.asarray(page.convert("L"), dtype=np.float32) / 255.0
    height, width = gray.shape
    black, white = rng.uniform(0.2, 0.32), rng.uniform(0.78, 0.88)
    gamma = rng.uniform(1.1, 1.45)
    gray = np.clip((gray - black) / (white - black), 0, 1) ** gamma
    toner = 0.72 + 0.28 * _smooth_field(rng, (height, width), (6, 8))
    ink = (1 - gray) * toner
    background = rng.uniform(0.0, 0.05)
    gray = 1 - np.clip(ink + background * _smooth_field(rng, (height, width), (4, 5)), 0, 1)

    streaks = int(rng.integers(1, 4))
    for _ in range(streaks):
        x = int(rng.integers(0, width - 4))
        thickness = int(rng.integers(1, 4))
        strength = rng.uniform(0.05, 0.16)
        profile = 0.6 + 0.4 * _smooth_field(rng, (height, 1), (1, 12))[:, 0]
        gray[:, x : x + thickness] -= (strength * profile)[:, None]
    edge = str(rng.choice(["left", "top", "right"]))
    band = int(width * rng.uniform(0.006, 0.018))
    ramp = np.linspace(0.55, 0.0, band, dtype=np.float32)
    if edge == "left":
        gray[:, :band] -= ramp[None, :]
    elif edge == "right":
        gray[:, -band:] -= ramp[::-1][None, :]
    else:
        gray[:band, :] -= ramp[:, None]
    speckles = int(height * width * rng.uniform(1.5e-5, 6e-5))
    ys, xs = rng.integers(0, height - 2, speckles), rng.integers(0, width - 2, speckles)
    gray[ys, xs] = 0.1
    gray[ys + 1, xs] = np.minimum(gray[ys + 1, xs], 0.4)
    dust = int(rng.integers(4, 14))
    for _ in range(dust):
        cy, cx, radius = int(rng.integers(6, height - 6)), int(rng.integers(6, width - 6)), int(rng.integers(1, 4))
        gray[cy - radius : cy + radius + 1, cx - radius : cx + radius + 1] *= 0.25
    gray += rng.standard_normal(gray.shape, dtype=np.float32) * np.float32(0.015)
    # Copiers clip near-white paper and reproduce few tones; this also keeps Flate output compact.
    gray = np.where(gray > 0.9, 1.0, np.round(np.clip(gray, 0, 1) * 31) / 31)
    image = Image.fromarray((gray * 255).astype(np.uint8))
    angle = float(rng.choice([-1, 1]) * rng.uniform(0.3, 1.0))
    dark_corners = bool(rng.random() < 0.5)
    image = image.rotate(angle, Image.Resampling.BICUBIC, expand=False, fillcolor=45 if dark_corners else 245)
    bitonal = bool(rng.random() < 0.5)
    threshold = int(rng.integers(130, 165))
    if bitonal:
        image = image.filter(ImageFilter.GaussianBlur(0.6)).point(lambda v: 255 if v > threshold else 0).convert("1")
    return image, {
        "black_point": round(float(black), 3),
        "white_point": round(float(white), 3),
        "gamma": round(float(gamma), 3),
        "streaks": streaks,
        "edge_shadow": edge,
        "speckles": speckles,
        "dust": dust,
        "rotation_degrees": round(angle, 3),
        "dark_corners": dark_corners,
        "bitonal": bitonal,
        "threshold": threshold if bitonal else None,
    }


# ---------------------------------------------------------------------------
# Measurement


def _visible_chars(text: str) -> Counter[str]:
    return Counter(char for char in text if not char.isspace())


def measure(path: Path, reference: str | None = None) -> dict[str, Any]:
    """Measure the text layer with pylopdf and structure presence with pypdf."""
    import pypdf
    from pypdf.generic import DictionaryObject

    started = time.perf_counter()
    document = _open_pdf(path)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        texts = [page.get_text() for page in document]
    chars = [sum(not c.isspace() for c in text) for text in texts]
    reader = pypdf.PdfReader(guard_path(path))
    root: Any = reader.trailer["/Root"]

    def count_outline(items: list[Any]) -> int:
        return sum(count_outline(item) if isinstance(item, list) else 1 for item in items)

    try:
        outline_count = count_outline(reader.outline)
    except Exception:
        outline_count = -1
    info = reader.trailer.get("/Info")
    info_keys = sorted(info.get_object().keys()) if info is not None else []
    images, fonts, glyphless, links = [], [], False, 0
    for page in reader.pages:
        resources = page.get("/Resources")
        resources = resources.get_object() if resources is not None else DictionaryObject()
        xobjects = resources.get("/XObject")
        xobjects = xobjects.get_object() if xobjects is not None else {}
        images.append(sum(1 for value in xobjects.values() if value.get_object().get("/Subtype") == "/Image"))
        font_map = resources.get("/Font")
        font_map = font_map.get_object() if font_map is not None else {}
        names = [str(value.get_object().get("/BaseFont", "")) for value in font_map.values()]
        glyphless |= any("GlyphLess" in name for name in names)
        fonts.append(len(names))
        links += sum(1 for annot in page.get("/Annots", []) or [] if annot.get_object().get("/Subtype") == "/Link")
    pages_with_text = [count >= PAGE_TEXT_MIN_CHARS for count in chars]
    full_text = "\n".join(texts)
    result: dict[str, Any] = {
        "page_count": len(texts),
        "chars_per_page": chars,
        "total_chars": sum(chars),
        "pages_with_text": sum(pages_with_text),
        "image_xobjects_per_page": images,
        "fonts_per_page": fonts,
        "tesseract_glyphless_font": glyphless,
        "extraction_warnings": sorted({str(w.message) for w in caught}),
        "structure": {
            "struct_tree_root": "/StructTreeRoot" in root,
            "mark_info": "/MarkInfo" in root,
            "outline_count": outline_count,
            "info_present": bool(info_keys),
            "info_keys": info_keys,
            "xmp_present": "/Metadata" in root,
            "lang": str(root.get("/Lang")) if "/Lang" in root else None,
            "link_annotations": links,
        },
        "page_sizes": [[round(w, 2), round(h, 2)] for w, h in page_display_sizes(path)],
    }
    if reference is not None:
        ref, got = _visible_chars(reference), _visible_chars(full_text)
        overlap = sum((ref & got).values())
        ref_nfkc = _visible_chars(unicodedata.normalize("NFKC", reference))
        got_nfkc = _visible_chars(unicodedata.normalize("NFKC", full_text))
        result["reference_char_recall"] = round(overlap / max(1, sum(ref.values())), 4)
        result["reference_char_precision"] = round(overlap / max(1, sum(got.values())), 4)
        result["reference_char_recall_nfkc"] = round(
            sum((ref_nfkc & got_nfkc).values()) / max(1, sum(ref_nfkc.values())), 4
        )
    result["text_layer"] = classify(result)
    result["measure_seconds"] = round(time.perf_counter() - started, 4)
    return result


def text_survival(before: Path, after: Path) -> dict[str, Any]:
    """Compare extracted text before and after ToUnicode removal with pylopdf and pypdf."""
    import pypdf

    result: dict[str, Any] = {}
    for name, extract in (
        ("pylopdf", lambda path: "\n".join(page.get_text() for page in _open_pdf(path))),
        ("pypdf", lambda path: "\n".join(page.extract_text() or "" for page in pypdf.PdfReader(path).pages)),
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                original, broken = extract(before), extract(after)
            except Exception as error:
                result[name] = {"error": f"{type(error).__name__}: {error}"}
                continue
        ref, got = _visible_chars(original), _visible_chars(broken)
        result[name] = {
            "chars_before": sum(ref.values()),
            "chars_after": sum(got.values()),
            "char_recall": round(sum((ref & got).values()) / max(1, sum(ref.values())), 4),
            "sample_after": broken.strip()[:160],
        }
    return result


def classify(measured: dict[str, Any]) -> str:
    """Classify a measured text layer as native, none, ocr, partial or broken."""
    pages, with_text = measured["page_count"], measured["pages_with_text"]
    if with_text == 0:
        return "none"
    if with_text < pages:
        return "partial"
    if measured["tesseract_glyphless_font"]:  # heuristic: Tesseract's invisible text font
        return "ocr"
    recall = measured.get("reference_char_recall")
    precision = measured.get("reference_char_precision")
    if recall is None:
        return "native"
    if (precision or 0) < 0.6 or recall < 0.3:
        return "broken"
    if recall < 0.92:
        return "partial"
    return "native"


def render_gray(recorder: Recorder, pdf: Path, dpi: int, prefix: Path) -> list[Path]:
    """Render grayscale PNG pages with Poppler."""
    recorder.run(["pdftoppm", "-r", str(dpi), "-gray", "-png", pdf, prefix])
    return sorted(prefix.parent.glob(prefix.name + "-*.png"))


def pixel_difference(recorder: Recorder, first: Path, second: Path, work: Path, dpi: int = 50) -> dict[str, Any]:
    """Compare low-resolution grayscale renders of two PDFs page by page."""
    import numpy as np
    from PIL import Image, ImageFilter

    work.mkdir(parents=True, exist_ok=True)
    a = render_gray(recorder, first, dpi, work / "a")
    b = render_gray(recorder, second, dpi, work / "b")
    pages: list[dict[str, Any]] = []
    for left, right in zip(a, b, strict=True):
        x = np.asarray(Image.open(left), dtype=np.int16)
        y = np.asarray(Image.open(right), dtype=np.int16)
        if x.shape != y.shape:
            pages.append({"shape_mismatch": [list(x.shape), list(y.shape)]})
            continue
        diff = np.abs(x - y)
        # Glyph and path rasterizers anti-alias edges differently; a 1 px blur keeps
        # missing or moved content visible while discounting edge-only differences.
        blurred = np.abs(
            np.asarray(Image.open(left).filter(ImageFilter.GaussianBlur(1)), dtype=np.int16)
            - np.asarray(Image.open(right).filter(ImageFilter.GaussianBlur(1)), dtype=np.int16)
        )
        pages.append(
            {
                "mean_abs_diff": round(float(diff.mean()), 3),
                "fraction_over_64": round(float((diff > 64).mean()), 5),
                "blurred_mean_abs_diff": round(float(blurred.mean()), 3),
                "blurred_fraction_over_64": round(float((blurred > 64).mean()), 5),
            }
        )
    unchanged = len(a) == len(b) and all(
        "blurred_mean_abs_diff" in page
        and page["blurred_mean_abs_diff"] < 2.0
        and page["blurred_fraction_over_64"] < 0.002
        for page in pages
    )
    return {"dpi": dpi, "pages": pages, "visually_unchanged": unchanged}


# ---------------------------------------------------------------------------
# Level builders


# ColorConversionStrategy=RGB avoids Ghostscript 10.07 writing empty ICCBased streams for
# Chromium's sRGB-tagged images, which Poppler then reports as unreadable profiles.
GS_PDFWRITE = [
    "gs", "-q", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.7",
    "-dAutoRotatePages=/None", "-dPassThroughJPEGImages=true", "-dDetectDuplicateImages=true",
    "-sColorConversionStrategy=RGB",
]  # fmt: skip


@dataclass
class Flattener:
    """Build requested levels for one source PDF, materializing dependencies on demand."""

    source: Path
    out_dir: Path
    requested: list[str]
    seed: str
    work: Path
    languages: list[str]
    built: dict[str, Path] = field(default_factory=dict)
    records: dict[str, dict[str, Any]] = field(default_factory=dict)
    renders: dict[tuple[int, str], list[Path]] = field(default_factory=dict)

    def target(self, level: str) -> Path:
        directory = self.out_dir if level in self.requested else self.work
        return guard_path(directory / f"{level}.pdf")

    def identity(self, level: str) -> str:
        return f"{self.seed}\x1f{level}"

    def render(self, recorder: Recorder, dpi: int, kind: str) -> list[Path]:
        """Render the source once per resolution and format (png, gray, jpeg)."""
        key = (dpi, kind)
        if key not in self.renders:
            prefix = self.work / f"render-{dpi}-{kind}" / "page"
            prefix.parent.mkdir(parents=True, exist_ok=True)
            flags = {"png": ["-png"], "gray": ["-gray", "-png"], "jpeg": ["-jpeg", "-jpegopt", "quality=90"]}[kind]
            recorder.run(["pdftoppm", "-r", str(dpi), *flags, self.source, prefix])
            self.renders[key] = sorted(prefix.parent.glob("page-*.*"))
            recorder.steps.append(f"rendered source at {dpi} dpi ({kind}) with pdftoppm")
        return self.renders[key]

    def ensure(self, level: str) -> Path:
        """Build one level (and any prerequisite) once, recording its resources."""
        if level in self.built:
            return self.built[level]
        for dependency in DEPENDENCIES.get(level, ()):
            self.ensure(dependency)
        builder = getattr(self, "build_" + level.split("_", 1)[0].lower())
        out = self.target(level)
        recorder = Recorder({str(self.work): "$WORK", str(self.out_dir): "$OUT", str(self.source): "$SOURCE"})
        hwm_reset = _reset_hwm()
        self_before = resource.getrusage(resource.RUSAGE_SELF)
        children_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        started = time.perf_counter()
        details: dict[str, Any] = builder(recorder, out) or {}
        wall = time.perf_counter() - started
        self_after = resource.getrusage(resource.RUSAGE_SELF)
        children_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        self.built[level] = out
        child_cpu = sum(c["cpu_user_seconds"] + c["cpu_system_seconds"] for c in recorder.commands)
        self.records[level] = {
            "commands": recorder.commands,
            "steps": recorder.steps,
            **details,
            "resources": {
                "wall_seconds": round(wall, 4),
                "cpu_self_seconds": round(
                    self_after.ru_utime - self_before.ru_utime + self_after.ru_stime - self_before.ru_stime, 4
                ),
                "cpu_children_seconds": round(child_cpu, 4),
                "cpu_children_rusage_delta_seconds": round(
                    children_after.ru_utime
                    - children_before.ru_utime
                    + children_after.ru_stime
                    - children_before.ru_stime,
                    4,
                ),
                "peak_rss_self_kib": _read_hwm_kib() if hwm_reset else None,
                "peak_rss_self_scope": "level (VmHWM reset)" if hwm_reset else "unmeasured",
                "peak_rss_children_kib": max((c["peak_rss_kib"] for c in recorder.commands), default=None),
            },
        }
        return out

    # L0 -----------------------------------------------------------------
    def build_l0(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        shutil.copyfile(self.source, out)
        recorder.steps.append("byte copy of source.pdf")
        return {"inputs": {"source": sha256_file(self.source)}}

    # L1 -----------------------------------------------------------------
    def build_l1(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        distilled = self.work / "l1-gs.pdf"
        recorder.run([*GS_PDFWRITE, "-o", distilled, self.source])
        report = rewrite_pdf(distilled, out, self.identity("L1_untagged"), strip_structure=True)
        recorder.steps.append("pypdf: removed StructTreeRoot/MarkInfo/Outlines/Lang, StructParents, BDC/BMC/EMC")
        return {"inputs": {"source": sha256_file(self.source)}, "rewrite": report}

    # L2 -----------------------------------------------------------------
    def build_l2(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        l1 = self.ensure("L1_untagged")
        report = rewrite_pdf(l1, out, self.identity("L2_stripped"), strip_structure=True, strip_metadata=True)
        recorder.steps.append("pypdf: removed trailer /Info and catalog /Metadata (XMP)")
        return {"inputs": {"L1_untagged": sha256_file(l1)}, "rewrite": report}

    # L3 -----------------------------------------------------------------
    def build_l3(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        l1 = self.ensure("L1_untagged")
        outlined = self.work / "l3-gs.pdf"
        recorder.run([*GS_PDFWRITE, "-dNoOutputFonts", "-o", outlined, l1])
        report = rewrite_pdf(outlined, out, self.identity("L3_outlined"), strip_structure=True)
        recorder.steps.append("gs -dNoOutputFonts converted glyphs to paths; pypdf normalized /ID")
        verification = pixel_difference(recorder, l1, out, self.work / "l3-compare")
        return {"inputs": {"L1_untagged": sha256_file(l1)}, "rewrite": report, "verification": verification}

    # L4 -----------------------------------------------------------------
    def build_l4(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        from PIL import Image

        sizes = page_display_sizes(self.source)
        renders = self.render(recorder, 200, "png")
        pages = []
        for (width, height), path in zip(sizes, renders, strict=True):
            with Image.open(path) as image:
                pages.append((width, height, flate_image(image.convert("RGB"))))
        write_image_pdf(pages, out, self.identity("L4_raster"))
        recorder.steps.append("wrapped one lossless Flate image per page at the original display size")
        return {"inputs": {"source": sha256_file(self.source)}, "parameters": {"dpi": 200, "encoding": "Flate"}}

    # L5 -----------------------------------------------------------------
    def build_l5(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        selection = select_ocr_languages(self.languages, tesseract_languages())
        renders = self.render(recorder, 300, "jpeg")
        parts = []
        for index, image in enumerate(renders):
            base = self.work / f"ocr-{index + 1:04d}"
            recorder.run(
                ["tesseract", image, base, "-l", "+".join(selection["used"]), "--dpi", "300", "--psm", "3", "pdf"]
            )
            parts.append(base.with_suffix(".pdf"))
        recorder.run(["qpdf", "--empty", "--deterministic-id", "--pages", *parts, "--", out])
        recorder.steps.append("tesseract per-page image+invisible-text PDF, merged by qpdf")
        return {
            "inputs": {"source": sha256_file(self.source)},
            "parameters": {"dpi": 300, "image": "JPEG q90 passthrough", "psm": 3},
            "ocr_languages": selection,
        }

    # L6 -----------------------------------------------------------------
    def build_l6(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        from PIL import Image

        sizes = page_display_sizes(self.source)
        pages, parameters = [], []
        for index, ((width, height), path) in enumerate(zip(sizes, self.render(recorder, 220, "png"), strict=True)):
            with Image.open(path) as image:
                photo, params = phone_scan(image.convert("RGB"), _rng(self.seed, "L6_phone_scan", index))
            pages.append((width, height, jpeg_image(photo, params["jpeg_quality"])))
            parameters.append(params)
        write_image_pdf(pages, out, self.identity("L6_phone_scan"))
        recorder.steps.append("Pillow/NumPy phone-capture simulation, JPEG (DCT) per page")
        return {"inputs": {"source": sha256_file(self.source)}, "parameters": {"dpi": 220, "pages": parameters}}

    # L7 -----------------------------------------------------------------
    def build_l7(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        from PIL import Image

        sizes = page_display_sizes(self.source)
        pages, parameters = [], []
        for index, ((width, height), path) in enumerate(zip(sizes, self.render(recorder, 300, "gray"), strict=True)):
            with Image.open(path) as image:
                copy, params = photocopy(image, _rng(self.seed, "L7_photocopy", index))
            encoded = flate_image(copy)
            params["storage"] = f"{encoded.bits}-bit {encoded.colorspace} Flate"
            pages.append((width, height, encoded))
            parameters.append(params)
        write_image_pdf(pages, out, self.identity("L7_photocopy"))
        recorder.steps.append("Pillow/NumPy photocopier simulation; 1-bit or 8-bit gray Flate")
        return {"inputs": {"source": sha256_file(self.source)}, "parameters": {"dpi": 300, "pages": parameters}}

    # L8 -----------------------------------------------------------------
    def build_l8(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        l1 = self.ensure("L1_untagged")
        if len(page_display_sizes(l1)) > 1:
            l4 = self.ensure("L4_raster")
            recorder.run(["qpdf", "--empty", "--deterministic-id", "--pages", l1, "1", l4, "2-z", "--", out])
            recorder.steps.append("page 1 native from L1, later pages raster from L4")
            return {
                "inputs": {"L1_untagged": sha256_file(l1), "L4_raster": sha256_file(l4)},
                "mode": "multi_page",
                "native_pages": [1],
                "hidden_text_under_overlay": False,
            }
        return self._l8_region(recorder, l1, out)

    def _l8_region(self, recorder: Recorder, l1: Path, out: Path) -> dict[str, Any]:
        import pypdf
        from pypdf.generic import ArrayObject, ByteStringObject, ContentStream

        document = _open_pdf(l1)
        page = document[0]
        page_rect = page.rect
        width, height = page_rect.x1 - page_rect.x0, page_rect.y1 - page_rect.y0
        candidates: list[tuple[str, Any]] = []
        for strategy in ("lines", "text"):
            tables = list(page.find_tables(strategy=strategy).tables) if strategy == "lines" or not candidates else []
            candidates += [(strategy, t.bbox) for t in tables]
        dpi = 120  # screen-like resolution for a pasted screenshot
        words = page.get_text("words")
        if words:
            left = max(0.0, min(w[0] for w in words) - 6)
            right = min(width, max(w[2] for w in words) + 6)
            content_top, content_bottom = min(w[1] for w in words), max(w[3] for w in words)
        else:
            left, right, content_top, content_bottom = 0.0, width, 0.0, height
        if candidates:
            strategy, bbox = max(candidates, key=lambda c: (c[1].x1 - c[1].x0) * (c[1].y1 - c[1].y0))
            region_source = f"find_tables(strategy={strategy!r})"
            top, bottom = max(0.0, bbox.y0 - 6), min(height, bbox.y1 + 6)
            left, right = min(left, max(0.0, bbox.x0 - 6)), max(right, min(width, bbox.x1 + 6))
        else:
            region_source = "lower_half_of_content"
            middle = (content_top + content_bottom) / 2
            gaps = sorted(
                (abs(y - middle), y) for y in {w[3] + 1 for w in words} if not any(w[1] < y < w[3] for w in words)
            )
            top = gaps[0][1] if gaps else middle
            bottom = min(height, content_bottom + 6)
        for _ in range(8):  # grow until no word straddles the horizontal edges
            straddling = [w for w in words if (w[1] < top < w[3]) or (w[1] < bottom < w[3])]
            if not straddling:
                break
            top = min([top] + [w[1] - 1 for w in straddling if w[1] < top < w[3]])
            bottom = max([bottom] + [w[3] + 1 for w in straddling if w[1] < bottom < w[3]])
        step = 72 / dpi
        top, bottom = max(0.0, math.floor(top / step) * step), min(height, math.ceil(bottom / step) * step)
        left, right = max(0.0, math.floor(left / step) * step), min(width, math.ceil(right / step) * step)
        region = (left, top, right, bottom)
        screenshot = _screenshot_png(page.get_pixmap(dpi=dpi, background=(255, 255, 255), clip=region))
        recorder.steps.append(
            f"region from {region_source}; rendered at {dpi} dpi with pylopdf get_pixmap, 1 px grey border"
        )

        reader = pypdf.PdfReader(guard_path(l1))
        writer = pypdf.PdfWriter(clone_from=reader)
        target = writer.pages[0]
        rotate = int(target.get("/Rotate", 0) or 0) % 360
        box = target.cropbox
        counts: dict[str, int] = {}
        limitations = []
        if rotate == 0:

            def to_display(x: float, y: float) -> tuple[float, float]:
                return x - float(box.left), float(box.top) - y

            stream = ContentStream(target.get_contents(), writer)
            stream.operations, counts = filter_region(stream.operations, region, to_display)
            target.replace_contents(stream)
            target.compress_content_streams()
            recorder.steps.append("pypdf: removed text runs, paths and images inside the region")
        else:
            limitations.append("rotated page: native content under the overlay was not removed")
        digest = hashlib.md5(self.identity("L8_mixed").encode(), usedforsecurity=False).digest()
        writer._ID = ArrayObject([ByteStringObject(digest), ByteStringObject(digest)])
        filtered = self.work / "l8-filtered.pdf"
        with filtered.open("wb") as handle:
            writer.write(handle)
        composed = _open_pdf(filtered)
        composed[0].insert_image(region, stream=screenshot, keep_proportion=False)
        composed.save(out, garbage=True, deflate=True)
        recorder.steps.append("pylopdf insert_image placed the opaque screenshot over the region")

        def in_region(word: Sequence[Any]) -> bool:
            return left <= (word[0] + word[2]) / 2 <= right and top <= (word[1] + word[3]) / 2 <= bottom

        remaining = [w for w in _open_pdf(out)[0].get_text("words") if in_region(w)]
        reference_words = [w for w in words if in_region(w)]
        if remaining:
            limitations.append("some extractable text remains under the overlay (Form XObject or untracked run)")
        return {
            "inputs": {"L1_untagged": sha256_file(l1)},
            "mode": "single_page_region",
            "region": [round(v, 3) for v in region],
            "region_source": region_source,
            "region_dpi": dpi,
            "removed_under_overlay": counts,
            "region_words_before": len(reference_words),
            "region_words_after": len(remaining),
            "hidden_text_under_overlay": bool(remaining),
            "tables_lines_after": len(_open_pdf(out)[0].find_tables().tables),
            "limitations": limitations,
        }

    # L9 -----------------------------------------------------------------
    def build_l9(self, recorder: Recorder, out: Path) -> dict[str, Any]:
        l1 = self.ensure("L1_untagged")
        report = rewrite_pdf(l1, out, self.identity("L9_broken_tounicode"), strip_structure=True, strip_tounicode=True)
        recorder.steps.append("pypdf: deleted /ToUnicode from every font, descendant and Type3 font")
        return {"inputs": {"L1_untagged": sha256_file(l1)}, "rewrite": report, "survival": text_survival(l1, out)}


def _screenshot_png(pixmap: Any) -> bytes:
    """Turn an opaque RGBA pixmap into a PNG with a thin grey frame, like a pasted screenshot."""
    import numpy as np
    from PIL import Image

    pixels = np.frombuffer(pixmap.samples, np.uint8).reshape(pixmap.height, pixmap.width, 4)[..., :3].copy()
    pixels[[0, -1], :, :] = 178
    pixels[:, [0, -1], :] = 178
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, "PNG", optimize=False)
    return buffer.getvalue()


def _languages_for(source: Path) -> list[str]:
    truth = source.parent / "truth.json"
    if truth.is_file():
        languages = json.loads(guard_path(truth).read_text()).get("languages")
        if isinstance(languages, list) and all(isinstance(tag, str) for tag in languages):
            return languages
    return ["en"]


def flatten(source_pdf: Path, out_dir: Path, levels: Sequence[str] | None = None, *, seed: str) -> dict[str, Any]:
    """Write ``out_dir/{level}.pdf`` for each level plus ``variants.json``, and return the record."""
    source = guard_path(Path(source_pdf))
    out_dir = guard_path(Path(out_dir))
    requested = list(levels) if levels is not None else list(LEVELS)
    unknown = [level for level in requested if level not in LEVELS]
    if unknown:
        raise ValueError(f"Unknown levels: {unknown}")
    out_dir.mkdir(parents=True, exist_ok=True)
    languages = _languages_for(source)
    reference = "\n".join(page.get_text() for page in _open_pdf(source))
    with tempfile.TemporaryDirectory(prefix="wild-flatten-") as temporary:
        flattener = Flattener(source, out_dir, requested, seed, Path(temporary), languages)
        level_records: dict[str, Any] = {}
        for level in requested:
            out = flattener.ensure(level)
            record = flattener.records[level]
            measured = measure(out, reference)
            expected = LEVELS[level]
            level_records[level] = {
                "output": out.name,
                "output_sha256": sha256_file(out),
                "output_bytes": out.stat().st_size,
                "page_count": measured["page_count"],
                "expected_text_layer": expected,
                "measured_text_layer": measured["text_layer"],
                "matches_expected": measured["text_layer"] in ACCEPTED[expected],
                "measured": measured,
                **record,
            }
    variants = {
        "version": SCHEMA,
        "seed": seed,
        "source": {"path": source.name, "sha256": sha256_file(source), "languages": languages},
        "tools": tool_versions(),
        "measurement": {
            "text": "jev_pdf/pylopdf Page.get_text(); non-whitespace characters per page; "
            f"a page has text at >= {PAGE_TEXT_MIN_CHARS} chars; reference = L0 text, raw and NFKC char-multiset",
            "structure": "pypdf catalog/trailer inspection",
            "resources": "wall: perf_counter; self CPU: RUSAGE_SELF delta (all threads); child CPU and peak "
            "RSS: os.wait4 per subprocess; self peak RSS: /proc/self VmHWM reset per level; "
            "measurement time is excluded from level resources",
            "host": {"cpus": os.cpu_count(), "platform": sys.platform},
        },
        "levels": level_records,
    }
    temporary_json = out_dir / "variants.json.tmp"
    temporary_json.write_text(json.dumps(variants, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    temporary_json.replace(out_dir / "variants.json")
    return variants


def _flatten_doc(arguments: tuple[str, str, list[str] | None, str]) -> tuple[str, dict[str, Any] | str]:
    source, out_dir, levels, seed = arguments
    try:
        return source, flatten(Path(source), Path(out_dir), levels, seed=seed)
    except Exception as error:
        return source, f"{type(error).__name__}: {error}"


def main(argv: Sequence[str] | None = None) -> int:
    """Flatten every ``docs/*/source.pdf`` under a wild-v1 directory into ``variants/{doc_id}/``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--docs", nargs="*", help="document IDs (default: all)")
    parser.add_argument("--levels", nargs="*", choices=list(LEVELS), help="levels (default: all)")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", default="wild-v1")
    args = parser.parse_args(argv)
    directory = guard_path(args.directory)
    sources = sorted(guard_path(path) for path in (directory / "docs").glob("*/source.pdf"))
    if args.docs:
        sources = [path for path in sources if path.parent.name in set(args.docs)]
    if not sources:
        print("no docs/*/source.pdf found", file=sys.stderr)
        return 1
    jobs = [
        (str(path), str(guard_path(directory / "variants" / path.parent.name)), args.levels,
         f"{args.seed}/{path.parent.name}")
        for path in sources
    ]  # fmt: skip
    failures = 0
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for source, result in pool.map(_flatten_doc, jobs):
            doc_id = Path(source).parent.name
            if isinstance(result, str):
                failures += 1
                print(f"{doc_id}: FAILED {result}", file=sys.stderr)
                continue
            summary = ", ".join(
                f"{level}={record['measured_text_layer']}{'' if record['matches_expected'] else '(!)'}"
                for level, record in result["levels"].items()
            )
            print(f"{doc_id}: {summary}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
