"""Bounded source-only OCR-track and incomplete-raster-rule region hypotheses.

Candidates are overlapping work proposals, never table labels, cell topology or
exclusive source ownership. A separate semantic gate must choose or abstain.
"""

# Heterogeneous experimental evidence uses existing dictionary protocols.
# ruff: noqa: ANN401, EM101, TRY003, PLR2004, PLC0415
from __future__ import annotations

from copy import deepcopy
from itertools import pairwise
from statistics import median
from typing import Any

from bench.pipeline_dense_candidates import MAX_PIXELS, MAX_RULES, _lines
from bench.pipeline_regions import _bands, _bounds, _box, _source
from bench.silver import canonical, sha

MAX_CANDIDATES = 64
MAX_RAW_CANDIDATES = 2048
MAX_SEGMENTS = 4096
MAX_TRACK_ROWS = 4096
MAX_PACKET_WORDS = 256
MAX_PACKET_CHARACTERS = 8000
WINDOW_ROWS = (4, 8, 16, 32)
PROTOCOL = "p003-region-candidates-v3"


def union_plans(
    yolo: dict[str, Any], fixed2: dict[str, Any], source: dict[str, Any], *, max_candidates: int = 32
) -> dict[str, Any]:
    """Alternate two source inventories, preserving first boxes and complete omissions."""
    if type(max_candidates) is not int or not 1 <= max_candidates <= 32:
        raise ValueError("Union candidate cap must be between one and 32")
    inputs = {"yolo": deepcopy(yolo), "tracks_fixed2": deepcopy(fixed2)}
    if any(len(plan["candidates"]) > 32 for plan in inputs.values()):
        raise ValueError("Union input inventories exceed their complete admission")
    words = _source({"page_size": source["page_size"], "words": source["words"]})["words"]
    ranked = [
        (arm, plan["candidates"][index])
        for index in range(max((len(p["candidates"]) for p in inputs.values()), default=0))
        for arm, plan in inputs.items()
        if index < len(plan["candidates"])
    ]
    unique: list[dict[str, Any]] = []
    for arm, original in ranked:
        provenance = {
            "arm": arm,
            "proposal_id": original["id"],
            "bbox": deepcopy(original["bbox"]),
            "mechanisms": deepcopy(original["mechanisms"]),
            "evidence_records": deepcopy(original["evidence_records"]),
            "packet_sha256": sha(canonical(original["packet"])),
        }
        old = next(
            (
                p
                for p in unique
                if (intersection := _intersection(p["bbox"], original["bbox"]))
                / (_area(p["bbox"]) + _area(original["bbox"]) - intersection)
                >= 0.9
            ),
            None,
        )
        if old is None:
            item = deepcopy(original)
            item["union_provenance"] = [provenance]
            unique.append(item)
        else:
            old["union_provenance"].append(provenance)
            old["mechanisms"] = sorted({*old["mechanisms"], *original["mechanisms"]})
            old["evidence_records"].extend(deepcopy(original["evidence_records"]))
            old["warnings"] = sorted({*old["warnings"], *original["warnings"]})
    retained = unique[:max_candidates]
    for index, item in enumerate(retained):
        item.update(id=f"r{index:03d}", packet=_packet(item, words))
    return {
        "protocol": "p003-yolo-fixed2-union-v1",
        "input_plans": inputs,
        "candidates": retained,
        "source_word_count": len(words),
        "diagnostics": {
            "input_candidate_counts": {arm: len(plan["candidates"]) for arm, plan in inputs.items()},
            "raw_candidates": len(ranked),
            "deduplicated_candidates": len(unique),
            "retained_candidates": len(retained),
            "omitted_candidates": len(unique) - len(retained),
            "candidate_cap": max_candidates,
            "omitted_inventory": [
                {"bbox": item["bbox"], "union_provenance": item["union_provenance"]} for item in unique[max_candidates:]
            ],
        },
        "configuration": {"ranking": "YOLO/fixed2 alternating, YOLO first", "near_duplicate_iou": 0.9},
        "source_ownership": "Overlapping proposals; no exclusive assignment or inferred cells",
    }


def _intersection(a: list[float], b: list[float]) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def _area(box: list[float]) -> float:
    return (box[2] - box[0]) * (box[3] - box[1])


def _padded(box: list[float], viewport: list[float], padding: float) -> list[float]:
    return [
        max(viewport[0], box[0] - padding),
        max(viewport[1], box[1] - padding),
        min(viewport[2], box[2] + padding),
        min(viewport[3], box[3] + padding),
    ]


def _segments(band: list[dict[str, Any]], height: float) -> list[list[float]]:
    groups: list[list[dict[str, Any]]] = []
    right = float("-inf")
    for word in sorted(band, key=lambda word: (word["bbox"][0], word["bbox"][2], word["id"])):
        if not groups or word["bbox"][0] - right >= 0.8 * height:
            groups.append([])
        groups[-1].append(word)
        right = max(right, word["bbox"][2])
    return [_bounds(group) for group in groups]


def _aligned(a: list[list[float]], b: list[list[float]], height: float) -> int:
    # One-to-one monotonic matching avoids counting one broad prose segment as
    # evidence for several columns. Left OR right edges accommodate numbers.
    cursor = 0
    matched = 0
    for box in a:
        for index in range(cursor, len(b)):
            other = b[index]
            if min(abs(box[0] - other[0]), abs(box[2] - other[2])) <= height:
                cursor = index + 1
                matched += 1
                break
    return matched


def _ocr_regions(words: list[dict[str, Any]], viewport: list[float]) -> list[dict[str, Any]]:  # noqa: C901, PLR0912 - bounded track and window admission.
    if not words:
        return []
    height = median(max(1.0, word["bbox"][3] - word["bbox"][1]) for word in words)
    bands = _bands(words)
    if len(bands) > MAX_TRACK_ROWS:
        raise ValueError("OCR physical row admission exceeded")
    tracks: list[list[dict[str, Any]]] = []
    segment_count = 0
    barrier = True
    for band in bands:
        segments = _segments(band, height)
        segment_count += len(segments)
        if segment_count > MAX_SEGMENTS:
            raise ValueError("OCR segment admission exceeded")
        # Single connected lines break tracks rather than becoming evidence for
        # table rows. This deliberately loses some wrapped-cell continuations.
        if len(segments) < 2:
            barrier = True
            continue
        row: dict[str, Any] = {"bbox": _bounds(band), "segments": segments, "word_count": len(band)}
        previous = tracks[-1][-1] if tracks else None
        separated = barrier or previous is None or row["bbox"][1] - previous["bbox"][3] > 2.5 * height
        if not separated and previous is not None:
            overlap = max(0.0, min(row["bbox"][2], previous["bbox"][2]) - max(row["bbox"][0], previous["bbox"][0]))
            separated = overlap < 0.5 * min(row["bbox"][2] - row["bbox"][0], previous["bbox"][2] - previous["bbox"][0])
            separated |= _aligned(previous["segments"], segments, height) < 2
        if separated:
            tracks.append([])
        tracks[-1].append(row)
        barrier = False
    candidates: list[dict[str, Any]] = []
    for track in tracks:
        if len(track) < 3:
            continue
        windows = [(0, len(track))]
        for size in WINDOW_ROWS:
            if len(track) > size:
                # Fixed half-window overlap provides alternatives when distinct
                # nearby tables share tracks. Final window covers the tail.
                starts = sorted({*range(0, len(track) - size + 1, size // 2), len(track) - size})
                windows.extend((start, start + size) for start in starts)
        for start, stop in windows:
            rows = track[start:stop]
            box = [
                min(r["bbox"][0] for r in rows),
                rows[0]["bbox"][1],
                max(r["bbox"][2] for r in rows),
                rows[-1]["bbox"][3],
            ]
            support = sum(_aligned(a["segments"], b["segments"], height) for a, b in pairwise(rows))
            candidates.append(
                {
                    "bbox": _padded(box, viewport, 0.5 * height),
                    "mechanism": "ocr_aligned_tracks",
                    "evidence": {
                        "physical_rows": len(rows),
                        "segment_counts": [len(row["segments"]) for row in rows],
                        "aligned_adjacent_segments": support,
                        "median_word_height": height,
                        "track_row_range": [start, stop],
                        "track_total_rows": len(track),
                        "row_bboxes": [row["bbox"] for row in rows[:32]],
                        "row_bboxes_omitted": max(0, len(rows) - 32),
                    },
                    "priority": min(1.0, support / (2 * max(1, len(rows) - 1))),
                    "capacity_window": start != 0 or stop != len(track),
                    "warnings": ["Aligned prose, lists and charts may resemble tables; physical completeness unknown"],
                }
            )
            if len(candidates) > MAX_RAW_CANDIDATES:
                raise ValueError("Raw OCR region admission exceeded")
    return candidates


def _raster_regions(image: Any, viewport: list[float]) -> list[dict[str, Any]]:  # noqa: C901
    import numpy as np

    width, height = image.size
    if min(width, height) < 16 or width * height > MAX_PIXELS:
        raise ValueError("Raster pixel admission exceeded")
    # Composite alpha onto white so transparent backgrounds cannot become rules.
    from PIL import Image

    rgba = image.convert("RGBA")
    opaque = Image.new("RGB", image.size, "white")
    opaque.paste(rgba, mask=rgba.getchannel("A"))
    gray = np.asarray(opaque.convert("L"))
    background = float(np.median(gray))
    mask = gray > background + 24 if background < 128 else gray < background - 24
    gap = min(8, max(2, round(min(width, height) * 0.006)))
    horizontal = _lines(mask, 0, max(20, round(width * 0.04)), max_gap=gap, thickness_ratio=0.012)
    vertical = _lines(mask, 1, max(20, round(height * 0.04)), max_gap=gap, thickness_ratio=0.012)
    if len(horizontal) + len(vertical) > MAX_RULES:
        raise ValueError("Raster rule admission exceeded")
    parents = list(range(len(horizontal) + len(vertical)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    tolerance = max(2.0, min(width, height) * 0.004)
    intersections: list[tuple[int, int]] = []
    for hi, (y, left, right) in enumerate(horizontal):
        for vi, (x, top, bottom) in enumerate(vertical):
            if left - tolerance <= x <= right + tolerance and top - tolerance <= y <= bottom + tolerance:
                parents[find(len(horizontal) + vi)] = find(hi)
                intersections.append((hi, len(horizontal) + vi))
    groups: dict[int, tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]] = {}
    for index, line in enumerate([*horizontal, *vertical]):
        group = groups.setdefault(find(index), ([], []))
        group[0 if index < len(horizontal) else 1].append(line)
    candidates = []
    for key, (hs, vs) in groups.items():
        # Require an internal partition on at least one axis, but allow missing
        # outer boundaries: this is region evidence, not complete-grid inference.
        if len(hs) < 2 or len(vs) < 2 or len(hs) + len(vs) < 5:
            continue
        contacts = sum(find(a) == key for a, _ in intersections)
        px = [
            min(left for _, left, _ in hs),
            min(top for _, top, _ in vs),
            max(right for _, _, right in hs),
            max(bottom for _, _, bottom in vs),
        ]
        # Retain complete physical component extents, including attached rules.
        px[0], px[2] = min(px[0], *(x for x, _, _ in vs)), max(px[2], *(x for x, _, _ in vs))
        px[1], px[3] = min(px[1], *(y for y, _, _ in hs)), max(px[3], *(y for y, _, _ in hs))
        box = [
            viewport[0] + px[0] / width * (viewport[2] - viewport[0]),
            viewport[1] + px[1] / height * (viewport[3] - viewport[1]),
            viewport[0] + px[2] / width * (viewport[2] - viewport[0]),
            viewport[1] + px[3] / height * (viewport[3] - viewport[1]),
        ]
        candidates.append(
            {
                "bbox": _padded(
                    box, viewport, 2 * max((viewport[2] - viewport[0]) / width, (viewport[3] - viewport[1]) / height)
                ),
                "mechanism": "raster_rule_component",
                "evidence": {
                    "horizontal_rules": len(hs),
                    "vertical_rules": len(vs),
                    "intersections": contacts,
                    "pixel_bbox": px,
                    "image_size": [width, height],
                    "gap_closing_pixels": gap,
                    "threshold_background": background,
                    "required_luminance_contrast": 24,
                    "outer_edge_completeness": "not_required_or_inferred",
                },
                "priority": min(1.0, contacts / (len(hs) * len(vs))),
                "capacity_window": False,
                "warnings": ["Open borders and chart axes may produce proposals; no cell topology inferred"],
            }
        )
    return candidates


def _raster_arm(image: Any, viewport: list[float], grid: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Admit each declared raster view independently; retain every refusal."""
    width, height = image.size
    if min(width, height) < 16 or width * height > MAX_PIXELS:
        raise ValueError("Raster pixel admission exceeded")
    if grid == 2 and min(width, height) < 32:
        raise ValueError("Fixed raster quadrants require both dimensions at least 32")
    views = [("whole", [0, 0, width, height])]
    if grid == 2:
        # Fixed quadrants have no learned or reference-informed localization.
        # Their interior edges are explicit physical-completeness risks.
        views.extend(
            (
                f"g2-{row}-{column}",
                [column * width // 2, row * height // 2, (column + 1) * width // 2, (row + 1) * height // 2],
            )
            for row in range(2)
            for column in range(2)
        )
    proposals: list[dict[str, Any]] = []
    admissions = []
    for name, pixels in views:
        bounds = [
            viewport[0] + pixels[0] / width * (viewport[2] - viewport[0]),
            viewport[1] + pixels[1] / height * (viewport[3] - viewport[1]),
            viewport[0] + pixels[2] / width * (viewport[2] - viewport[0]),
            viewport[1] + pixels[3] / height * (viewport[3] - viewport[1]),
        ]
        try:
            regions = _raster_regions(image if name == "whole" else image.crop(pixels), bounds)
        except ValueError as error:
            # A rule-inventory refusal is an independently failed mechanism,
            # not a partial region result. Invalid rasters still fail globally.
            if "rule inventory" not in str(error) and "rule admission" not in str(error):
                raise
            admissions.append(
                {"view": name, "status": "rule_inventory_refused", "pixel_bbox": pixels, "candidate_count": 0}
            )
            continue
        admissions.append({"view": name, "status": "ok", "pixel_bbox": pixels, "candidate_count": len(regions)})
        for region in regions:
            region["evidence"].update(raster_view=name, view_display_bbox=bounds)
            region["raster_boundary_risk"] = name != "whole" and any(
                abs(region["bbox"][i] - bounds[i]) <= 1e-6
                and pixels[i] != (0 if i < 2 else (width if i == 2 else height))
                for i in range(4)
            )
            region["evidence"]["raster_boundary_risk"] = region["raster_boundary_risk"]
            if region["raster_boundary_risk"]:
                region["warnings"].append("Proposal touches an interior raster-view boundary; context may cut a table")
            proposals.append(region)
    return proposals, admissions


def _packet(candidate: dict[str, Any], words: list[dict[str, Any]]) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    characters = 0
    total = 0
    crossing = 0
    for word in words:
        if _intersection(candidate["bbox"], word["bbox"]) <= 0:
            continue
        total += 1
        crossing += int(_intersection(candidate["bbox"], word["bbox"]) < _area(word["bbox"]))
        size = len(word["id"]) + len(word["text"])
        if len(selected) < MAX_PACKET_WORDS and characters + size <= MAX_PACKET_CHARACTERS:
            selected.append(dict(word))
            characters += size
    return {
        "words": selected,
        "source_ids": [word["id"] for word in selected],
        "source_word_count": total,
        "source_text_available": total > 0,
        "omitted_source_words": total - len(selected),
        "boundary_crossing_words": crossing,
        "source_context_complete": total == len(selected) and crossing == 0,
        "physical_table_completeness": "unknown",
    }


def propose(  # noqa: C901 - independent bounded mechanism admission and packet assembly.
    page: dict[str, Any], *, image: Any = None, max_candidates: int = 32, raster_grid: int = 0
) -> dict[str, Any]:
    """Return deterministic region hypotheses and literal bounded gate packets.

    Reads only page_size/words. Optional PIL image must cover the entire display
    viewport exactly; no PDF references, detector labels or candidate topology
    are used. Near-identical boxes (IoU >= .9) merge evidence. Ranked candidate
    omission is explicit; omitted candidates are never implicitly rejected.
    Mechanisms alternate in ranked output so raster evidence is not starved by
    many high-support OCR windows; rank is a screen order, not acceptance.
    Source IDs can occur in multiple proposals and do not confer cell ownership.
    raster_grid=2 adds four fixed quadrants. Rule-budget refusal is recorded per
    raster view and never erases successful OCR or other-view proposals.
    """
    if type(max_candidates) is not int or not 1 <= max_candidates <= MAX_CANDIDATES:
        raise ValueError("Region candidate cap must be between one and 64")
    if type(raster_grid) is not int or raster_grid not in (0, 2):
        raise ValueError("Raster grid must be zero or two")
    source = _source({"page_size": page["page_size"], "words": page["words"]})
    viewport = _box([0, 0, *source["page_size"]] if len(source["page_size"]) == 2 else source["page_size"])
    words = source["words"]
    for word in words:
        if _area(word["bbox"]) <= 0 or len(word["id"]) > 256:
            raise ValueError("Source word geometry or ID exceeds admission")
        if any(word["bbox"][axis] < viewport[axis] for axis in (0, 1)) or any(
            word["bbox"][axis] > viewport[axis] for axis in (2, 3)
        ):
            raise ValueError("Source word lies outside display viewport")
    raw = _ocr_regions(words, viewport)
    raster_admissions: list[dict[str, Any]] = []
    if image is not None:
        raster, raster_admissions = _raster_arm(image, viewport, raster_grid)
        raw.extend(raster)
    if len(raw) > MAX_RAW_CANDIDATES:
        raise ValueError("Complete raw region admission exceeded")
    ordered = sorted(
        raw,
        key=lambda c: (
            -c["priority"],
            c["capacity_window"],
            -_area(c["bbox"]),
            c["bbox"][1],
            c["bbox"][0],
            c["mechanism"],
        ),
    )
    fused: list[dict[str, Any]] = []
    for candidate in ordered:
        old = next(
            (
                item
                for item in fused
                if (overlap := _intersection(item["bbox"], candidate["bbox"]))
                / (_area(item["bbox"]) + _area(candidate["bbox"]) - overlap)
                >= 0.9
            ),
            None,
        )
        if old is not None:
            old["mechanisms"] = sorted({*old["mechanisms"], candidate["mechanism"]})
            old["evidence_records"].append({"mechanism": candidate["mechanism"], **candidate["evidence"]})
            old["warnings"] = sorted({*old["warnings"], *candidate["warnings"]})
        else:
            fused.append(
                {
                    "bbox": candidate["bbox"],
                    "mechanisms": [candidate["mechanism"]],
                    "evidence_records": [{"mechanism": candidate["mechanism"], **candidate["evidence"]}],
                    "priority": candidate["priority"],
                    "capacity_window": candidate["capacity_window"],
                    "warnings": candidate["warnings"],
                }
            )
    # Keep both independently acquired mechanisms in a bounded screen rather
    # than letting many high-support OCR windows starve raster evidence.
    queues = [
        [item for item in fused if item["mechanisms"][0] == mechanism]
        for mechanism in ("ocr_aligned_tracks", "raster_rule_component")
    ]
    ranked = [
        queue[index] for index in range(max(map(len, queues), default=0)) for queue in queues if index < len(queue)
    ]
    retained = ranked[:max_candidates]
    for index, candidate in enumerate(retained):
        candidate.update(id=f"r{index:03d}", semantic_status="proposal_only", packet=_packet(candidate, words))
    return {
        "protocol": PROTOCOL,
        "page_size": source["page_size"],
        "source_word_count": len(words),
        "candidates": retained,
        "diagnostics": {
            "raw_candidates": len(raw),
            "deduplicated_candidates": len(fused),
            "retained_candidates": len(retained),
            "omitted_candidates": len(fused) - len(retained),
            "candidate_cap": max_candidates,
            "raster_supplied": image is not None,
            "raster_views": raster_admissions,
            "refused_raster_views": sum(view["status"] != "ok" for view in raster_admissions),
        },
        "priority_scope": (
            "Mechanism-diverse roundrobin of geometric support ordering; not table probability or semantic confidence"
        ),
        "source_ownership": "Overlapping proposals; no exclusive assignment or inferred cells",
        "configuration": {
            "word_gap_em": 0.8,
            "row_gap_em": 2.5,
            "alignment_em": 1.0,
            "min_track_rows": 3,
            "window_rows": list(WINDOW_ROWS),
            "near_duplicate_iou": 0.9,
            "packet_word_cap": MAX_PACKET_WORDS,
            "packet_character_cap": MAX_PACKET_CHARACTERS,
            "raster_grid": raster_grid,
            "ranking": "OCR/raster alternating; support, whole-track, area, geometry ties within mechanism",
        },
    }
