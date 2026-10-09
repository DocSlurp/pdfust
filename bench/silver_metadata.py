"""Bounded, CPU-only descriptive measurements of controlled silver PDFs.

These are observations, not quality labels. pypdf may allocate while parsing or
inflating streams before our decoded-size check; this is not a hostile-input
sandbox. Image/text coverage uses clipped axis-aligned display bounding boxes,
not polygons, clipping paths, alpha masks, occlusion, or visible pixel coverage.
"""

# PDF dictionaries and JSON results are heterogeneous; parser internals expose
# original encoded bytes required by these descriptive metrics.
# ruff: noqa: ANN401, PLR0912, PLR2004, SLF001, C901, TRY301

from __future__ import annotations

import io
import re
import unicodedata
from collections import Counter
from itertools import pairwise
from typing import Any

from pypdf import PdfReader
from pypdf.generic import ByteStringObject, ContentStream, IndirectObject, TextStringObject

import pylopdf

MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_PAGES = 64
MAX_DECODED_BYTES = 64 * 1024 * 1024
MAX_OPERATIONS = 200_000
MAX_DEPTH = 16

LIMITS = {
    "file_bytes": MAX_FILE_BYTES,
    "pages": MAX_PAGES,
    "unique_decoded_content_bytes": MAX_DECODED_BYTES,
    "executed_content_operations": MAX_OPERATIONS,
    "form_depth": MAX_DEPTH,
}

DEFINITIONS = {
    "clipped_bbox_coverage_percent": (
        "For each drawn image placement: 100 * area of its axis-aligned display bbox intersected "
        "with page display bounds / page display area. Placements of a reused image are separate. "
        "This ignores polygon shape, clipping paths, alpha and occlusion; it is not pixel visibility."
    ),
    "image_placement_coverage_bins": (
        "Per-page counts of individual drawn image placements by clipped bbox coverage, including "
        "zero-area placements: [0,10), [10,25), [25,50), [50,75), [75,100]. Empty pages have zero "
        "counts in every bin; failed measurement or zero page area gives null. Counts describe "
        "placements, whereas document image_coverage_bins describe page-level union coverage."
    ),
    "percent_pages_with_images": (
        "100 * pages with at least one successfully measured drawn image placement / all document pages. "
        "Null if any page placement measurement failed or the document has no pages."
    ),
    "image_coverage_bins": (
        "Counts across all document pages, including zero-image pages: [0,10), [10,25), [25,50), "
        "[50,75), [75,100] percent union bbox coverage. Null if any page coverage is unavailable."
    ),
    "bbox_effective_dpi": (
        "Image source pixels * 72 / full un-clipped placement axis-aligned bbox width or height. "
        "Rotation/shear makes this an approximate bbox-based resolution, not source-axis DPI."
    ),
    "image_coverage_percent": (
        "Union area of drawn image placement axis-aligned display bboxes intersected with page "
        "display bounds / page area; approximate geometry, not visible pixels or clip-path "
        "coverage."
    ),
    "image_individual_sum_percent": (
        "Sum of individually page-clipped image bbox areas / page area; overlaps count repeatedly and may exceed 100%."
    ),
    "raw_string_token_fraction": (
        "Literal and hexadecimal PDF string source-token bytes, including delimiters/escapes, "
        "outside stream payloads / complete file bytes. Compressed-object strings are not "
        "visible and are excluded."
    ),
    "decoded_content_string_fraction": (
        "Original decoded PDF string operand payload bytes in unique reachable page/Form "
        "content streams / their total decoded bytes. Includes strings outside text-showing "
        "operators; excludes dictionaries and stream metadata."
    ),
    "text_showing_operand_bytes_executed": (
        "Original string payload bytes in Tj, TJ, single-quote and double-quote operators, "
        "counting repeated Form execution. Not Unicode characters or unique stream bytes."
    ),
    "content_encoded_to_decoded_ratio": (
        "Encoded payload bytes / decoded bytes for unique reachable page/Form content streams; "
        "smaller values mean greater compression. Null with zero decoded bytes."
    ),
    "adjacent_repeated_characters": (
        "Adjacent equal non-whitespace Unicode character pairs in extracted text. Valid "
        "repeated letters count; this is not evidence of corruption."
    ),
    "duplicate_positioned_words": (
        "Extra word occurrences with identical Unicode text and bboxes rounded to 0.01 display "
        "points; diagnostic proxy, not a noise/quality label."
    ),
    "duplicate_positioned_spans": (
        "Extra span occurrences with identical Unicode text and bboxes rounded to 0.01 display "
        "points; glyph-level duplicates are unavailable from this API."
    ),
    "font_resources": (
        "Font resource entries reached through page/Form resources; resource declarations do "
        "not establish use or visibility."
    ),
    "actual_text_properties": (
        "Parsed ActualText strings in marked-content BDC dictionaries or named Properties "
        "resources during execution; replacements are declarations, not validated extraction "
        "fidelity."
    ),
    "image_resource_payload_bytes": (
        "Original encoded image XObject stream payload bytes where available, distinct from "
        "rendered-placement PNG/JPEG materialization bytes."
    ),
}


def _resolve(value: Any) -> Any:
    return value.get_object() if isinstance(value, IndirectObject) else value


def _identity(value: Any) -> tuple[int, int] | int:
    return (value.idnum, value.generation) if isinstance(value, IndirectObject) else id(value)


def _string_bytes(value: Any) -> int:
    if isinstance(value, TextStringObject):
        return len(value.original_bytes)
    if isinstance(value, ByteStringObject):
        return len(value)
    if isinstance(value, list):
        return sum(_string_bytes(item) for item in value)
    if isinstance(value, dict):
        return sum(_string_bytes(item) for item in value.values())
    return 0


def union_area(boxes: list[tuple[float, float, float, float]]) -> float:
    """Measure the exact union area of already clipped axis-aligned boxes."""
    boxes = [box for box in boxes if box[2] > box[0] and box[3] > box[1]]
    xs = sorted({x for box in boxes for x in (box[0], box[2])})
    area = 0.0
    for left, right in pairwise(xs):
        intervals = sorted((b[1], b[3]) for b in boxes if b[0] < right and b[2] > left)
        length = 0.0
        end = float("-inf")
        for low, high in intervals:
            length += max(0.0, high - max(low, end))
            end = max(end, high)
        area += (right - left) * length
    return area


def _coverage_bins(values: list[float]) -> dict[str, int]:
    bins = {"0-10": 0, "10-25": 0, "25-50": 0, "50-75": 0, "75-100": 0}
    for value in values:
        key = (
            "0-10"
            if value < 10
            else "10-25"
            if value < 25
            else "25-50"
            if value < 50
            else "50-75"
            if value < 75
            else "75-100"
        )
        bins[key] += 1
    return bins


def _clip(box: Any, width: float, height: float) -> tuple[float, float, float, float]:
    coords = (box.x0, box.y0, box.x1, box.y1) if hasattr(box, "x0") else box
    return (
        min(width, max(0.0, coords[0])),
        min(height, max(0.0, coords[1])),
        min(width, max(0.0, coords[2])),
        min(height, max(0.0, coords[3])),
    )


def raw_string_token_bytes(data: bytes, reader: PdfReader) -> int:
    """Lex strings outside streams; skip payloads using declared stream Length.

    Fail rather than searching compressed bytes for a guessed endstream marker.
    Comments and names are skipped; escaped/nested literals count as one token.
    """
    pos = total = 0
    dictionary_lengths: list[int | None] = []
    last_dictionary_length: int | None = None
    while pos < len(data):
        byte = data[pos]
        if byte == 37:
            end = data.find(b"\n", pos)
            pos = len(data) if end < 0 else end + 1
        elif byte == 47:
            start = pos
            pos += 1
            while pos < len(data) and data[pos] not in b" \t\r\n\x00\x0c()<>[]{}/%":
                pos += 1
            if data[start:pos] == b"/Length" and dictionary_lengths:
                match = re.compile(rb"\s+(\d+)(?:\s+(\d+)\s+R)?").match(data, pos)
                if match is None:
                    msg = "unsupported stream length syntax"
                    raise ValueError(msg)
                size = int(match[1])
                if match[2] is not None:
                    value: Any = reader.get_object(IndirectObject(size, int(match[2]), reader))
                    size = int(value)
                dictionary_lengths[-1] = size
        elif byte == 40:
            start = pos
            depth = 1
            pos += 1
            while pos < len(data) and depth:
                if data[pos] == 92:
                    pos += 2
                    continue
                depth += (data[pos] == 40) - (data[pos] == 41)
                pos += 1
            if depth:
                msg = "unterminated literal string"
                raise ValueError(msg)
            total += pos - start
        elif data[pos : pos + 2] == b"<<":
            dictionary_lengths.append(None)
            pos += 2
        elif data[pos : pos + 2] == b">>":
            if dictionary_lengths:
                last_dictionary_length = dictionary_lengths.pop()
            pos += 2
        elif byte == 60:
            end = data.find(b">", pos + 1)
            if end < 0:
                msg = "unterminated hexadecimal string"
                raise ValueError(msg)
            total += end + 1 - pos
            pos = end + 1
        elif data[pos : pos + 6] == b"stream" and (pos == 0 or data[pos - 1] in b"\r\n \t\x00\x0c>"):
            if last_dictionary_length is None:
                msg = "cannot locate declared stream length"
                raise ValueError(msg)
            size = last_dictionary_length
            pos += 6
            if data[pos : pos + 2] == b"\r\n":
                pos += 2
            elif data[pos : pos + 1] in (b"\n", b"\r"):
                pos += 1
            else:
                msg = "stream missing required line ending"
                raise ValueError(msg)
            pos += size
            if size < 0 or pos > len(data) or not data[pos : pos + 16].lstrip().startswith(b"endstream"):
                msg = "declared stream length does not reach endstream"
                raise ValueError(msg)
        else:
            pos += 1
    return total


def _text_metrics(page: Any, width: float, height: float) -> dict[str, Any]:
    text = page.get_text()
    words = page.get_text("words")
    layout = page.get_text("dict")
    lines = [line for block in layout["blocks"] for line in block["lines"]]
    spans = [span for line in lines for span in line["spans"]]
    word_keys = [(w[4], *(round(float(v), 2) for v in w[:4])) for w in words]
    span_keys = [(s["text"], *(round(float(v), 2) for v in s["bbox"])) for s in spans]
    boxes = [_clip(s["bbox"], width, height) for s in spans if s["text"].strip()]
    area = width * height
    return {
        "characters": len(text),
        "utf8_bytes": len(text.encode("utf-8")),
        "unicode_replacement_characters": text.count("\ufffd"),
        "unicode_control_characters": sum(unicodedata.category(c) == "Cc" and not c.isspace() for c in text),
        "whitespace_characters": sum(c.isspace() for c in text),
        "non_ascii_characters": sum(ord(c) > 127 for c in text),
        "adjacent_repeated_characters": sum(a == b and not a.isspace() for a, b in pairwise(text)),
        "duplicate_positioned_words": len(word_keys) - len(set(word_keys)),
        "duplicate_positioned_spans": len(span_keys) - len(set(span_keys)),
        "duplicate_positioned_glyphs": None,
        "word_count": len(words),
        "line_count": len(lines),
        "span_count": len(spans),
        "text_bbox_coverage_percent": 100 * union_area(boxes) / area if area else None,
    }


class _ContentInventory:
    def __init__(self, reader: PdfReader) -> None:
        self.reader = reader
        self.streams: set[Any] = set()
        self.fonts: dict[Any, dict[str, Any]] = {}
        self.images: dict[Any, dict[str, Any]] = {}
        self.decoded = self.encoded = self.string_bytes = self.operations = 0
        self.text_bytes = 0
        self.operators: Counter[str] = Counter()
        self.text_modes: Counter[str] = Counter()
        self.actual_text: list[str] = []

    def walk(self, source: Any, resources: Any, ancestors: tuple[Any, ...] = ()) -> None:
        token = _identity(source)
        if len(ancestors) >= MAX_DEPTH or token in ancestors:
            msg = "content Form depth/cycle limit"
            raise ValueError(msg)
        stream = _resolve(source)
        resources = _resolve(resources) or {}
        for name, ref in (_resolve(resources.get("/Font")) or {}).items():
            font = _resolve(ref)
            self.fonts[_identity(ref)] = {
                "resource_name": str(name),
                "subtype": str(font.get("/Subtype")) if font.get("/Subtype") is not None else None,
                "base_font": str(font.get("/BaseFont")) if font.get("/BaseFont") is not None else None,
                "encoding": str(font.get("/Encoding")) if font.get("/Encoding") is not None else None,
                "has_to_unicode": "/ToUnicode" in font,
                "descendant_subtypes": [
                    str(_resolve(f).get("/Subtype")) for f in _resolve(font.get("/DescendantFonts", []))
                ],
            }
        xobjects = _resolve(resources.get("/XObject")) or {}
        for name, ref in xobjects.items():
            obj = _resolve(ref)
            if obj.get("/Subtype") == "/Image":
                self.images[_identity(ref)] = {
                    "resource_name": str(name),
                    "width_pixels": int(obj.get("/Width", 0)),
                    "height_pixels": int(obj.get("/Height", 0)),
                    "bits_per_component": obj.get("/BitsPerComponent"),
                    "color_space": str(obj.get("/ColorSpace")),
                    "filter": str(obj.get("/Filter")),
                    "encoded_payload_bytes": len(obj._data) if hasattr(obj, "_data") else None,
                }
        if stream is None:
            return
        # Each physical stream contributes once even if invoked repeatedly.
        streams = stream if isinstance(stream, list) else [source]
        for ref in streams:
            key = _identity(ref)
            if key not in self.streams:
                decoded = _resolve(ref).get_data()
                self.decoded += len(decoded)
                if self.decoded > MAX_DECODED_BYTES:
                    msg = "decoded content byte limit"
                    raise ValueError(msg)
                self.encoded += len(_resolve(ref)._data)
                self.streams.add(key)
                parsed = ContentStream(ref, self.reader)
                self.string_bytes += sum(_string_bytes(operands) for operands, _ in parsed.operations)
        content = ContentStream(source, self.reader)
        for operands, operator in content.operations:
            self.operations += 1
            if self.operations > MAX_OPERATIONS:
                msg = "executed content operation limit"
                raise ValueError(msg)
            op = operator.decode("ascii")
            self.operators[op] += 1
            if operator in (b"Tj", b"TJ", b"'", b'"'):
                self.text_bytes += _string_bytes(operands)
            elif operator == b"Tr":
                self.text_modes[str(operands[0])] += 1
            elif operator == b"BDC" and len(operands) > 1:
                props = operands[1]
                if not isinstance(props, dict):
                    props = (_resolve(resources.get("/Properties")) or {}).get(props)
                props = _resolve(props)
                if isinstance(props, dict) and "/ActualText" in props:
                    self.actual_text.append(str(props["/ActualText"]))
            elif operator == b"Do":
                ref = xobjects.get(operands[0])
                obj = _resolve(ref)
                if obj is not None and obj.get("/Subtype") == "/Form":
                    self.walk(ref, obj.get("/Resources", resources), (*ancestors, token))

    def result(self) -> dict[str, Any]:
        return {
            "decoded_content_bytes": self.decoded,
            "encoded_content_bytes": self.encoded,
            "content_encoded_to_decoded_ratio": self.encoded / self.decoded if self.decoded else None,
            "decoded_content_string_operand_bytes": self.string_bytes,
            "decoded_content_string_fraction": self.string_bytes / self.decoded if self.decoded else None,
            "text_showing_operand_bytes_executed": self.text_bytes,
            "executed_operations": self.operations,
            "operators": dict(self.operators),
            "text_render_mode_operator_counts": dict(self.text_modes),
            "clipping_operator_count": self.operators["W"] + self.operators["W*"],
            "inline_image_operator_count": self.operators["INLINE IMAGE"],
            "vector_paint_operator_count": sum(
                self.operators[k] for k in ("S", "s", "f", "F", "f*", "B", "B*", "b", "b*")
            ),
            "font_resources": list(self.fonts.values()),
            "image_resources": list(self.images.values()),
            "image_resource_count": len(self.images),
            "actual_text_properties": self.actual_text,
            "form_xobjects_descended": True,
        }


def analyze_pdf(data: bytes) -> dict[str, Any]:
    """Return JSON-safe measured fields and explicit per-scope failure records."""
    result: dict[str, Any] = {
        "file_bytes": len(data),
        "errors": [],
        "pages": None,
        "declared_pdf_version": None,
        "catalog_pdf_version": None,
        "effective_pdf_version": None,
        "page_count": None,
        "raw_string_token_bytes": None,
        "raw_string_token_fraction": None,
        "content": None,
        "percent_pages_with_images": None,
        "image_coverage_bins": None,
    }
    errors = result["errors"]
    if len(data) > MAX_FILE_BYTES:
        errors.append({"scope": "document", "type": "limit", "message": "file byte limit"})
        return result
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
        count = len(reader.pages)
        if count > MAX_PAGES:
            msg = "page count limit"
            raise ValueError(msg)
        catalog = _resolve(reader.trailer["/Root"])
        declared = reader.pdf_header.removeprefix("%PDF-")
        override = str(catalog["/Version"]).removeprefix("/") if "/Version" in catalog else None
        result.update(
            {
                "declared_pdf_version": declared,
                "catalog_pdf_version": override,
                "effective_pdf_version": max(declared, override) if override else declared,
                "page_count": count,
            }
        )
    except Exception as exc:
        errors.append({"scope": "document", "type": type(exc).__name__, "message": str(exc)})
        return result
    result["raw_string_token_bytes"] = result["raw_string_token_fraction"] = None
    try:
        raw = raw_string_token_bytes(data, reader)
        result.update({"raw_string_token_bytes": raw, "raw_string_token_fraction": raw / len(data) if data else None})
    except Exception as exc:
        errors.append({"scope": "raw_strings", "type": type(exc).__name__, "message": str(exc)})
    inventory = _ContentInventory(reader)
    result["content"] = None
    try:
        for page in reader.pages:
            inventory.walk(page.get("/Contents"), page.get("/Resources"))
        result["content"] = inventory.result()
    except Exception as exc:
        errors.append({"scope": "content", "type": type(exc).__name__, "message": str(exc)})
    pages: list[dict[str, Any]] = []
    document = None
    try:
        document = pylopdf.Document(stream=data)
    except Exception as exc:
        errors.append({"scope": "geometry", "type": type(exc).__name__, "message": str(exc)})
    for index, page in enumerate(reader.pages):
        details: dict[str, Any] = {
            "page_number": index,
            "media_box": [float(v) for v in page.mediabox],
            "crop_box": [float(v) for v in page.cropbox],
            "rotation_degrees": int(page.rotation),
            "images": None,
            "image_placement_count": None,
            "image_placement_coverage_bins": None,
            "image_coverage_percent": None,
            "image_individual_sum_percent": None,
            "text": None,
        }
        if document is not None:
            view = document[index]
            width, height = view.rect.width, view.rect.height
            details.update({"display_width_points": width, "display_height_points": height})
            try:
                placements = view.get_images()
                boxes = [_clip(image["bbox"], width, height) for image in placements]
                area = width * height
                coverage = [100 * max(0, b[2] - b[0]) * max(0, b[3] - b[1]) / area if area else None for b in boxes]
                details["images"] = [
                    {
                        "bbox": list(image["bbox"]),
                        "clipped_bbox": list(box),
                        "clipped_bbox_coverage_percent": fraction,
                        "width_pixels": image["width"],
                        "height_pixels": image["height"],
                        "format": image["ext"],
                        "materialized_payload_bytes": len(image["image"]),
                        "bbox_effective_dpi_x": 72 * image["width"] / image["bbox"].width
                        if image["bbox"].width
                        else None,
                        "bbox_effective_dpi_y": 72 * image["height"] / image["bbox"].height
                        if image["bbox"].height
                        else None,
                    }
                    for image, box, fraction in zip(placements, boxes, coverage, strict=True)
                ]
                details["image_placement_coverage_bins"] = (
                    _coverage_bins([value for value in coverage if value is not None]) if area else None
                )
                details["image_placement_count"] = len(placements)
                details["image_coverage_percent"] = 100 * union_area(boxes) / area if area else None
                details["image_individual_sum_percent"] = (
                    100 * sum(max(0, b[2] - b[0]) * max(0, b[3] - b[1]) for b in boxes) / area if area else None
                )
            except Exception as exc:
                for key in (
                    "images",
                    "image_placement_count",
                    "image_placement_coverage_bins",
                    "image_coverage_percent",
                    "image_individual_sum_percent",
                ):
                    details[key] = None
                errors.append({"scope": f"page:{index}:images", "type": type(exc).__name__, "message": str(exc)})
            try:
                details["text"] = _text_metrics(view, width, height)
            except Exception as exc:
                errors.append({"scope": f"page:{index}:text", "type": type(exc).__name__, "message": str(exc)})
        pages.append(details)
    if document is not None:
        document.close()
    result["pages"] = pages
    measured = all(p["image_placement_count"] is not None for p in pages)
    result["percent_pages_with_images"] = (
        100 * sum(p["image_placement_count"] > 0 for p in pages) / count if measured and count else None
    )
    result["image_coverage_bins"] = None
    if measured and all(p["image_coverage_percent"] is not None for p in pages):
        result["image_coverage_bins"] = _coverage_bins([p["image_coverage_percent"] for p in pages])
    return result
