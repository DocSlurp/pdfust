"""Blind numeric source-geometry qualifiers for a pair of supplied text regions.

Typography and repeated adjacency are observations, not cell identity. Only
unconflicted interpreted structural support chooses a relation. No case IDs,
literal strings, producer labels or references enter qualifier logic.
"""

# ruff: noqa: C901, PLR0912, PLR0913, PLR2004 - bounded geometry and numeric validation.
from __future__ import annotations

import argparse
import importlib
import json
import math
import resource
import statistics
import time
from copy import deepcopy
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

from bench.lowlevel_geometry import _box, _rectangle
from bench.remote_prompt_packets import _digest, _encode, _fail, _inside, _read, _safe

CONFIG: dict[str, Any] = {
    "schema": "blind-geometry-config-v2",
    "baseline_tolerance_em": 0.3,
    "horizontal_tolerance_em": 0.025,
    "neighbor_column_tolerance_em": 0.8,
    "context_radius_em": 6.0,
    "separator_coverage": 0.98,
    "partial_separator_coverage": 0.3,
    "enclosure_max_padding_em": 1.5,
    "local_leading_relative_tolerance": 0.15,
    "max_words": 16384,
    "max_paths": 8192,
    "max_commands": 131072,
    "max_pdf_bytes": 16777216,
    "max_glyphs": 65536,
    "max_glyph_text_bytes": 65536,
    "policy": "structural support only; spacing/overlap/anchors are advisory; conflicts retain alternatives",
}
FEATURE_KEYS = (
    "font_scale",
    "baseline_gap_em",
    "ink_gap_em",
    "horizontal_overlap",
    "indent_em",
    "within_line_gap_em",
    "local_row_leading_em",
    "local_leading_variation",
    "neighboring_column_anchor_counts",
    "shared_neighbor_columns",
    "repeated_neighbor_columns",
    "rule_separator_coverage",
    "partial_rule_coverage",
    "shared_small_enclosure",
    "same_explicit_cell",
    "different_explicit_cells",
    "vertical_internal_boundary",
    "targets_distinct_lines",
    "relation_axis_inline",
    "inline_gap_em",
    "target_direction",
    "vertical_separator_coverage",
    "neighboring_row_alignment_count",
)


def _center(box: list[float] | tuple[float, ...]) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def _contains(outer: list[float] | tuple[float, ...], inner: list[float] | tuple[float, ...]) -> bool:
    return outer[0] <= inner[0] and outer[1] <= inner[1] and outer[2] >= inner[2] and outer[3] >= inner[3]


def _selected(box: tuple[float, ...], word: dict[str, Any]) -> bool:
    x, y = _center(word["bbox"])
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def _median(values: list[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def _union(boxes: Sequence[Sequence[float]]) -> list[float]:
    return [
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    ]


def _coverage(intervals: list[tuple[float, float]], left: float, right: float) -> float:
    clipped = sorted((max(left, a), min(right, b)) for a, b in intervals if b > left and a < right)
    total, end = 0.0, left
    for a, b in clipped:
        total += max(0.0, b - max(a, end))
        end = max(end, b)
    return total / (right - left)


def describe(
    words: list[dict[str, Any]],
    spans: list[dict[str, Any]],
    drawings: list[dict[str, Any]],
    cells: list[dict[str, Any]],
    target_boxes: list[list[float]],
    *,
    scope_bbox: list[float] | None = None,
    target_glyphs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute numeric features from source records, without inspecting their text/IDs."""
    if len(target_boxes) != 2 or len(words) > CONFIG["max_words"] or len(drawings) > CONFIG["max_paths"]:
        _fail("Unadmitted source geometry inventory")
    if sum(len(drawing.get("items", [])) for drawing in drawings) > CONFIG["max_commands"]:
        _fail("Drawing commands exceed admission")
    boxes = sorted((_box(box) for box in target_boxes), key=lambda box: (_center(box)[1], box[0]))
    scope = _box(scope_bbox) if scope_bbox is not None else None
    if scope is not None and any(not _contains(scope, box) for box in boxes):
        _fail("Admitted scope must contain both target selectors")
    admitted = [word for word in words if scope is None or _contains(scope, _box(word["bbox"]))]
    chunks = [[word for word in admitted if _selected(box, word)] for box in boxes]
    if target_glyphs is not None:
        if len(target_glyphs) > CONFIG["max_glyphs"]:
            _fail("Glyph geometry exceeds admission")
        admitted_glyphs = [glyph for glyph in target_glyphs if scope is None or _contains(scope, glyph["bbox"])]
        glyph_chunks = [[glyph for glyph in admitted_glyphs if _selected(box, glyph)] for box in boxes]
        if all(glyph_chunks):
            chunks = glyph_chunks
    selected_spans = [[span for span in spans if _selected(box, span)] for box in boxes]
    sizes = [
        float(span["size"])
        for group in selected_spans
        for span in group
        if isinstance(span.get("size"), (int, float))
        and not isinstance(span["size"], bool)
        and math.isfinite(span["size"])
        and span["size"] > 0
    ]
    glyph_sizes = [float(glyph["size"]) for chunk in chunks for glyph in chunk if "size" in glyph]
    if glyph_sizes:
        sizes = glyph_sizes
    font = _median(sizes)
    font_source = "measured_glyph_size" if glyph_sizes else "measured_span_size"
    if font is None:
        font = _median([word["bbox"][3] - word["bbox"][1] for chunk in chunks for word in chunk])
        font_source = "word_height_surrogate"
    features: dict[str, Any] = dict.fromkeys(FEATURE_KEYS)
    insufficiency = []
    if font is None or font <= 0 or not all(chunks):
        insufficiency.append("target_text_geometry_unavailable")
        return {
            "schema": "source-ambiguity-geometry-v2",
            "features": features,
            "qualifiers": {
                "supports": {"join": [], "split": []},
                "choice": "unresolved",
                "alternatives": ["join", "split"],
                "insufficiency": insufficiency,
            },
            "scope": {
                "target_boxes": target_boxes,
                "scope_bbox": scope_bbox,
                "boundary_corridor": None,
                "font_scale_source": font_source,
            },
        }
    ink = [_union([word["bbox"] for word in chunk]) for chunk in chunks]
    baselines = [
        _median([float(glyph["origin"][1]) for glyph in chunk if "origin" in glyph])
        or _median([float(span["origin"][1]) for span in group])
        for chunk, group in zip(chunks, selected_spans, strict=True)
    ]
    y = [baseline if baseline is not None else _center(box)[1] for baseline, box in zip(baselines, ink, strict=True)]
    gap = y[1] - y[0]
    distinct = gap > CONFIG["baseline_tolerance_em"] * font
    inline = not distinct
    if any(abs(word.get("direction", [1, 0])[1]) > 0.05 for chunk in chunks for word in chunk):
        insufficiency.append("nonhorizontal_text_axis")
    within = []
    for chunk in chunks:
        ordered = sorted(chunk, key=lambda word: word["bbox"][0])
        within.append(
            _median([max(0.0, right["bbox"][0] - left["bbox"][2]) / font for left, right in pairwise(ordered)])
        )
    left, right = min(box[0] for box in boxes), max(box[2] for box in boxes)
    overlap = max(0.0, min(ink[0][2], ink[1][2]) - max(ink[0][0], ink[1][0]))
    min_width = min(box[2] - box[0] for box in ink)
    local = [
        word
        for word in admitted
        if min(y) - CONFIG["context_radius_em"] * font
        <= _center(word["bbox"])[1]
        <= max(y) + CONFIG["context_radius_em"] * font
    ]
    bands: list[list[dict[str, Any]]] = []
    for word in sorted(local, key=lambda item: (_center(item["bbox"])[1], item["bbox"][0])):
        if (
            not bands
            or abs(_center(word["bbox"])[1] - _center(bands[-1][0]["bbox"])[1]) > CONFIG["baseline_tolerance_em"] * font
        ):
            bands.append([])
        bands[-1].append(word)
    band_y = [float(statistics.median(_center(word["bbox"])[1] for word in band)) for band in bands]
    leading_values = [(b - a) / font for a, b in pairwise(band_y) if b > a]
    leading = _median(leading_values)
    variation = _median([abs(value - leading) / leading for value in leading_values]) if leading else None
    anchors: list[dict[str, Any]] = []
    for band_index, band in enumerate(bands):
        for word in band:
            box = word["bbox"]
            if not (box[2] < left or box[0] > right):
                continue
            x = box[0]
            matches = [
                anchor for anchor in anchors if abs(anchor["x"] - x) <= CONFIG["neighbor_column_tolerance_em"] * font
            ]
            if matches:
                matches[0]["rows"].add(band_index)
            else:
                anchors.append({"x": x, "rows": {band_index}})
    target_bands = [
        min(range(len(band_y)), key=lambda index: abs(band_y[index] - _center(box)[1])) if band_y else None
        for box in ink
    ]
    repeated = [anchor for anchor in anchors if len(anchor["rows"]) >= 2]
    anchor_counts = [sum(index in anchor["rows"] for anchor in repeated) for index in target_bands]
    shared = sum(all(index in anchor["rows"] for index in target_bands) for anchor in repeated)
    horizontal: list[tuple[float, float, float]] = []
    rectangles = []
    vertical_internal = False
    vertical_segments = []
    for drawing in drawings:
        items = drawing.get("items", [])
        segments = []
        for item in items:
            if len(item) != 3 or item[0] != "l":
                continue
            start, end = item[1], item[2]
            if not all(math.isfinite(float(value)) for value in [*start, *end]):
                _fail("Nonfinite source path geometry")
            if scope is not None and not _contains(
                scope, [min(start[0], end[0]), min(start[1], end[1]), max(start[0], end[0]), max(start[1], end[1])]
            ):
                continue
            segments.append((tuple(start), tuple(end)))
        if (
            drawing.get("type") not in ("s", "fs")
            or drawing.get("color") is None
            or drawing.get("stroke_opacity", 1) <= 0
        ):
            continue
        for start, end in segments:
            if abs(start[1] - end[1]) <= CONFIG["horizontal_tolerance_em"] * font:
                line_y = (start[1] + end[1]) / 2
                if (
                    y[0] + CONFIG["horizontal_tolerance_em"] * font
                    < line_y
                    < y[1] - CONFIG["horizontal_tolerance_em"] * font
                ):
                    horizontal.append((line_y, min(start[0], end[0]), max(start[0], end[0])))
            elif abs(start[0] - end[0]) <= CONFIG["horizontal_tolerance_em"] * font:
                vertical_internal |= (
                    left < start[0] < right and min(start[1], end[1]) < y[1] and max(start[1], end[1]) > y[0]
                )
                x = (start[0] + end[0]) / 2
                if _center(ink[0])[0] < x < _center(ink[1])[0]:
                    vertical_segments.append((x, min(start[1], end[1]), max(start[1], end[1])))
        if drawing.get("close_path") is True and len(segments) == len(items):
            rectangle = _rectangle(segments)
            if rectangle is not None:
                rectangles.append(rectangle)
    coverage = max(
        (
            _coverage(
                [(a, b) for y2, a, b in horizontal if abs(y2 - y1) <= CONFIG["horizontal_tolerance_em"] * font],
                left,
                right,
            )
            for y1, _, _ in horizontal
        ),
        default=0.0,
    )
    common_enclosure = any(
        _contains(rectangle, _union(ink))
        and min(ink[0][1], ink[1][1]) - rectangle[1] <= CONFIG["enclosure_max_padding_em"] * font
        and rectangle[3] - max(ink[0][3], ink[1][3]) <= CONFIG["enclosure_max_padding_em"] * font
        for rectangle in rectangles
    )
    vertical_coverage = max(
        (
            _coverage(
                [(a, b) for x2, a, b in vertical_segments if abs(x2 - x1) <= CONFIG["horizontal_tolerance_em"] * font],
                min(box[1] for box in ink),
                max(box[3] for box in ink),
            )
            for x1, _, _ in vertical_segments
        ),
        default=0.0,
    )
    neighboring_rows = sum(
        any(abs(word["bbox"][0] - ink[0][0]) <= CONFIG["neighbor_column_tolerance_em"] * font for word in band)
        and any(abs(word["bbox"][0] - ink[1][0]) <= CONFIG["neighbor_column_tolerance_em"] * font for word in band)
        for index, band in enumerate(bands)
        if index not in target_bands
    )
    containing = [
        [cell for cell in cells if (scope is None or _contains(scope, cell["bbox"])) and _contains(cell["bbox"], box)]
        for box in ink
    ]
    same_cell = len(containing[0]) == len(containing[1]) == 1 and containing[0][0]["key"] == containing[1][0]["key"]
    different_cells = (
        len(containing[0]) == len(containing[1]) == 1 and containing[0][0]["key"] != containing[1][0]["key"]
    )
    features.update(
        font_scale=font,
        baseline_gap_em=gap / font,
        ink_gap_em=(ink[1][1] - ink[0][3]) / font,
        horizontal_overlap=overlap / min_width,
        indent_em=(ink[1][0] - ink[0][0]) / font,
        within_line_gap_em=within,
        local_row_leading_em=leading,
        local_leading_variation=variation,
        neighboring_column_anchor_counts=anchor_counts,
        shared_neighbor_columns=shared,
        repeated_neighbor_columns=len(repeated),
        rule_separator_coverage=coverage,
        partial_rule_coverage=coverage if coverage < CONFIG["separator_coverage"] else 0.0,
        shared_small_enclosure=common_enclosure,
        same_explicit_cell=same_cell,
        different_explicit_cells=different_cells,
        vertical_internal_boundary=vertical_internal,
        targets_distinct_lines=distinct,
        relation_axis_inline=inline,
        inline_gap_em=(ink[1][0] - ink[0][2]) / font if inline else None,
        target_direction=[
            _median([word.get("direction", [1, 0])[axis] for chunk in chunks for word in chunk]) for axis in (0, 1)
        ],
        vertical_separator_coverage=vertical_coverage,
        neighboring_row_alignment_count=neighboring_rows,
    )
    supports: dict[str, list[str]] = {"join": [], "split": []}
    if distinct and not insufficiency:
        if coverage >= CONFIG["separator_coverage"] or different_cells:
            supports["split"].append("interpreted_separator_or_distinct_bordered_cells")
        if same_cell or (
            common_enclosure and coverage < CONFIG["partial_separator_coverage"] and not vertical_internal
        ):
            supports["join"].append("interpreted_shared_local_enclosure_or_bordered_cell")
    elif inline and not insufficiency:
        if vertical_coverage >= CONFIG["separator_coverage"]:
            supports["split"].append("interpreted_vertical_boundary")
        # Shared cell membership does not establish the intended literal space
        # between adjacent character chunks. Inline gaps alone remain ambiguous.
        if not supports["split"]:
            insufficiency.append("inline_spacing_does_not_establish_literal_boundary")
    if 0 < coverage < CONFIG["separator_coverage"]:
        insufficiency.append("fragmentary_interpreted_boundary")
    if not any(supports.values()):
        insufficiency.append("spacing_and_anchor_patterns_do_not_establish_identity")
    if supports["join"] and supports["split"]:
        insufficiency.append("conflicting_interpreted_structure")
    choice = (
        next((key for key in supports if supports[key]), "unresolved")
        if sum(bool(value) for value in supports.values()) == 1 and not insufficiency
        else "unresolved"
    )
    return {
        "schema": "source-ambiguity-geometry-v2",
        "features": features,
        "qualifiers": {
            "supports": supports,
            "choice": choice,
            "alternatives": [choice] if choice != "unresolved" else ["join", "split"],
            "insufficiency": insufficiency,
            "semantics": "interpreted geometry support; pixel visibility and semantic uniqueness unproven",
        },
        "scope": {
            "target_boxes": target_boxes,
            "scope_bbox": scope_bbox,
            "boundary_corridor": [
                _center(ink[0])[0],
                min(box[1] for box in ink),
                _center(ink[1])[0],
                max(box[3] for box in ink),
            ]
            if inline
            else [left, y[0], right, y[1]],
            "font_scale_source": font_source,
        },
    }


def extract(
    source_pdf: Path, target_boxes: list[list[float]], *, page_index: int = 0, scope_bbox: list[float] | None = None
) -> dict[str, Any]:
    """Extract fresh bounded native layout, font spans and interpreted paths on CPU."""
    import pdfust  # noqa: PLC0415

    source_pdf = _safe(source_pdf)
    raw = _read(source_pdf, CONFIG["max_pdf_bytes"])
    with pdfust.Document(stream=raw, limits=pdfust.DocumentLimits.web()) as document:
        page = document[page_index]
        layout = page.get_layout()
        words = [{"bbox": list(word.bbox), "direction": list(word.direction)} for word in layout.words]
        spans = [
            dict(span)
            for block in page.get_text("dict")["blocks"]
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ]
        cells = [
            {"key": [table_index, cell.id], "bbox": list(cell.bbox)}
            for table_index, table in enumerate(layout.tables)
            if table.strategy == "lines"
            for cell in table.cells
        ]
        drawings = [dict(drawing, close_path=drawing.get("closePath", False)) for drawing in page.get_drawings()]
        snapshot = document._doc.extract_glyph_snapshot(  # noqa: SLF001 - source-only native position hook.
            page_index + 1, max_glyphs=CONFIG["max_glyphs"], max_text_bytes=CONFIG["max_glyph_text_bytes"]
        )
        document._emit_warnings()  # noqa: SLF001 - preserve the public source warning contract.
        glyphs = []
        for row in snapshot[2]:
            if not row[1] or row[1].isspace():
                continue
            origin, size, advance, direction = row[2], row[3], row[4], row[5]
            x1 = origin[0] + advance * direction[0]
            glyphs.append(
                {
                    "bbox": [min(origin[0], x1), origin[1] - size * 0.8, max(origin[0], x1), origin[1] + size * 0.2],
                    "origin": list(origin),
                    "size": size,
                    "direction": list(direction),
                }
            )
        result = describe(words, spans, drawings, cells, target_boxes, scope_bbox=scope_bbox, target_glyphs=glyphs)
    result["scope"]["page_index"] = page_index
    return result


def compact(result: dict[str, Any]) -> dict[str, Any]:
    """Return only frozen numeric/source structural flags, never decision or IDs."""
    return {key: result["features"][key] for key in FEATURE_KEYS}


def freeze(source: Path, destination: Path) -> dict[str, Any]:
    """Freeze numerical policy and fresh features before any reference access."""
    source, destination = _safe(source), _safe(destination)
    started, cpu = time.perf_counter(), time.process_time()
    manifest_raw = _read(source / "manifest.json", 16 * 1024 * 1024)
    manifest = json.loads(manifest_raw)
    if manifest.get("experiment") not in ("L015", "L011-source"):
        _fail("Only explicit authored/natural DEV source freezes admitted")
    if manifest["experiment"] == "L011-source":
        importlib.import_module("bench.lowlevel_natural").verify(source)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "config.json").write_bytes(_encode(CONFIG))
    rows = []
    for page in manifest["pages"]:
        obs_raw = _read(_inside(source, page["observation_file"]), 16 * 1024 * 1024)
        pdf = _inside(source, page["source_file"])
        if (
            _digest(obs_raw) != page["observation_sha256"]
            or _digest(_read(pdf, CONFIG["max_pdf_bytes"])) != page["source_sha256"]
        ):
            _fail("Source PDF/observation hashes differ")
        obs = json.loads(obs_raw)
        boxes = obs["selector"]["target"]["boxes"]
        contexts = {"full-source": None}
        if manifest["experiment"] == "L011-source":
            contexts.update({arm: image["requested_bbox"] for arm, image in obs["images"].items()})
        for arm, bbox in contexts.items():
            rows.append(
                {
                    "id": page["id"],
                    "arm": arm,
                    "source_sha256": page["source_sha256"],
                    "observation_sha256": page["observation_sha256"],
                    "descriptor": extract(pdf, boxes, page_index=page.get("page_index", 0), scope_bbox=bbox),
                }
            )
    result = {
        "schema": 1,
        "source_directory": str(source),
        "source_manifest_sha256": _digest(manifest_raw),
        "config_sha256": _digest(_encode(CONFIG)),
        "config": deepcopy(CONFIG),
        "extractor_sha256": _digest(_read(Path(__file__), 16 * 1024 * 1024)),
        "records": rows,
        "annotation_status": "source-only features/configuration frozen before reference access",
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "scope": "one serial CPU process; perf_counter/process_time; Linux lifetime RSS peak",
        },
    }
    (destination / "features.json").write_bytes(_encode(result))
    return result


def main() -> None:
    """Freeze source-only numerical evidence locally with no reference access."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    result = freeze(args.source, args.destination)
    print(json.dumps({"records": len(result["records"]), "config_sha256": result["config_sha256"]}))


if __name__ == "__main__":
    main()
