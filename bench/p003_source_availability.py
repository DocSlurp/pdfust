"""Source-only literal bags and geometry diagnostics, never reference availability scores."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

from collections import Counter
from statistics import median
from typing import Any

from bench.generalization_scoring import normalize_text
from bench.pipeline_repair import _sources, validate
from bench.silver import canonical, sha


def distribution(values: list[float]) -> dict[str, Any]:
    """Use floor((n-1)*p) quantiles and the ordinary median; empty data stays absent."""
    ordered = sorted(values)
    if not ordered:
        return {"count": 0, "min": None, "p10": None, "median": None, "p90": None, "p99": None, "max": None}
    return {
        "count": len(ordered),
        "min": ordered[0],
        "p10": ordered[(len(ordered) - 1) // 10],
        "median": median(ordered),
        "p90": ordered[(len(ordered) - 1) * 9 // 10],
        "p99": ordered[(len(ordered) - 1) * 99 // 100],
        "max": ordered[-1],
    }


def _counter(values: list[str]) -> list[list[Any]]:
    return [[value, count] for value, count in sorted(Counter(values).items())]


def bag(source: dict[str, Any], source_ids: list[str]) -> dict[str, Any]:
    """Preserve every selected literal ID and multiset count without OCR correction."""
    lookup = _sources(source)
    if (
        len(canonical(source)) > 2 * 1024 * 1024
        or len(source_ids) != len(set(source_ids))
        or set(source_ids) - set(lookup)
    ):
        raise ValueError("Invalid complete source bag admission")
    selected = set(source_ids)
    words = [w for w in source["words"] if w["id"] in selected]
    normalized = [normalize_text(w["text"]) for w in words]
    tokens = [token for text in normalized for token in text.split()]
    characters = Counter(char for text in normalized for char in text if not char.isspace())
    word_bag = _counter(normalized)
    return {
        "source_sha256": sha(canonical(source)),
        "selected_source_ids": [w["id"] for w in words],
        "selected_source_ids_sha256": sha(canonical([w["id"] for w in words])),
        "word_count": len(words),
        "raw_codepoint_count": sum(len(w["text"]) for w in words),
        "raw_utf8_bytes": sum(len(w["text"].encode()) for w in words),
        "normalized_codepoint_count": sum(map(len, normalized)),
        "nonspace_codepoint_count": sum(characters.values()),
        "whitespace_token_count": len(tokens),
        "normalized_empty_word_count": sum(not v for v in normalized),
        "distinct_normalized_word_strings": len(word_bag),
        "duplicate_normalized_word_occurrences": sum(count - 1 for _, count in word_bag),
        "normalized_word_string_bag": word_bag,
        "whitespace_token_bag": _counter(tokens),
        "nonspace_character_bag": [[value, count] for value, count in sorted(characters.items())],
        "normalization": "generalization_scoring.normalize_text: NFC and Unicode whitespace collapse only; "
        "no case/punctuation/OCR changes",
        "literal_word_array_columns": ["source_id", "literal_text", "normalized_text", "x0", "y0", "x1", "y1"],
        "literal_words": [[w["id"], w["text"], text, *w["bbox"]] for w, text in zip(words, normalized, strict=True)],
        "literal_ids_omitted_count": 0,
        "other_page_ids_omitted_count": len(source["words"]) - len(words),
        "availability_score": None,
        "limitations": "Bags ignore order, geometry, topology and complete-word atomicity. "
        "Character bags are especially optimistic. Inter-word whitespace can be introduced by assembly; "
        "it is excluded from character necessity counts. Reusing available text across multiple reference cells "
        "is not validated here. No reference correctness or attainable-table claim.",
    }


def _intersection(a: list[float], b: list[float]) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def diagnostics(source: dict[str, Any], source_ids: list[str]) -> dict[str, Any]:
    """Measure literal length and bbox geometry with a bounded exact overlap sweep."""
    lookup = _sources(source)
    selected = set(source_ids)
    if len(selected) != len(source_ids) or selected - set(lookup):
        raise ValueError("Invalid diagnostic source ownership")
    words = [w for w in source["words"] if w["id"] in selected]
    widths = [w["bbox"][2] - w["bbox"][0] for w in words]
    heights = [w["bbox"][3] - w["bbox"][1] for w in words]
    areas = [width * height for width, height in zip(widths, heights, strict=True)]
    active: list[dict[str, Any]] = []
    positive_pairs = 0
    examined_pairs = 0
    overlap_ids: set[str] = set()
    edges = [0.0, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 1.0]
    ious = [0] * (len(edges) - 1)
    smaller_cover = [0] * (len(edges) - 1)
    for word in sorted(words, key=lambda w: (w["bbox"][0], w["bbox"][2], w["id"])):
        b = word["bbox"]
        active = [other for other in active if other["bbox"][2] > b[0]]
        area = (b[2] - b[0]) * (b[3] - b[1])
        for other in active:
            examined_pairs += 1
            intersection = _intersection(b, other["bbox"])
            if intersection <= 0:
                continue
            a = other["bbox"]
            other_area = (a[2] - a[0]) * (a[3] - a[1])
            positive_pairs += 1
            overlap_ids.update((word["id"], other["id"]))
            values = (intersection / (area + other_area - intersection), intersection / min(area, other_area))
            for counts, value in zip((ious, smaller_cover), values, strict=True):
                bin_index = min(len(counts) - 1, sum(value >= edge for edge in edges[1:]))
                counts[bin_index] += 1
        active.append(word)
    boxes = Counter(tuple(w["bbox"]) for w in words)
    return {
        "word_count": len(words),
        "bbox_width_points": distribution(widths),
        "bbox_height_points": distribution(heights),
        "bbox_area_square_points": distribution(areas),
        "width_divided_by_positive_height": distribution(
            [width / height for width, height in zip(widths, heights, strict=True) if height > 0]
        ),
        "normalized_word_codepoint_length": distribution([float(len(normalize_text(w["text"]))) for w in words]),
        "normalized_word_token_length": distribution([float(len(normalize_text(w["text"]).split())) for w in words]),
        "nonpositive_bbox_word_count": sum(a <= 0 for a in areas),
        "exact_duplicate_bbox_extra_occurrences": sum(count - 1 for count in boxes.values()),
        "source_overlap": {
            "examined_x_overlapping_pairs": examined_pairs,
            "positive_area_pairs": positive_pairs,
            "words_with_any_positive_overlap": len(overlap_ids),
            "histogram_edges": edges,
            "histogram_intervals": "left-inclusive/right-exclusive; final interval includes one",
            "pair_iou_histogram_counts": ious,
            "intersection_divided_by_smaller_area_histogram_counts": smaller_cover,
            "pairs_omitted_count": 0,
            "method": "exact x-axis sweep, <=4096 words; fixed-size exact histogram, "
            "no pair sampling or confidence interpretation",
        },
        "height_is_font_size": False,
        "ocr_correctness_measured": False,
    }


def audit(source: dict[str, Any], regions: list[dict[str, Any]], control: dict[str, Any]) -> dict[str, Any]:
    """Freeze full, detector-owned and actual geometry-assigned source inventories."""
    lookup = _sources(source)
    validate(source, control)
    detector = [r for r in regions if r["kind"] == "detector_proposal"]
    owned = [i for r in detector for i in r["source_ids"]]
    if set(owned) - set(lookup) or any(len(r["source_ids"]) != len(set(r["source_ids"])) for r in detector):
        raise ValueError("Detector source ownership is invalid")
    assigned = [i for t in control["tables"] for c in t["cells"] for i in c["source_ids"]]
    assigned_set, owned_set = set(assigned), set(owned)
    groups = {
        "full_page": list(lookup),
        "detector_owned_union": list(dict.fromkeys(owned)),
        "geometry_control_assigned": assigned,
    }
    subsets = {name: {"bag": bag(source, ids), "geometry": diagnostics(source, ids)} for name, ids in groups.items()}
    membership = []
    for word in source["words"]:
        b = word["bbox"]
        area = (b[2] - b[0]) * (b[3] - b[1])
        overlaps = [_intersection(b, r["bbox"]) / area if area > 0 else 0.0 for r in detector]
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        membership.append(
            {
                "source_id": word["id"],
                "detector_owner_region_ids": [r["id"] for r in detector if word["id"] in r["source_ids"]],
                "geometry_control_assigned": word["id"] in assigned_set,
                "max_detector_bbox_word_area_overlap": max(overlaps, default=0.0),
                "positive_detector_bbox_intersection_count": sum(v > 0 for v in overlaps),
                "detector_bbox_center_membership_count": sum(
                    r["bbox"][0] <= cx <= r["bbox"][2] and r["bbox"][1] <= cy <= r["bbox"][3] for r in detector
                ),
            }
        )
    return {
        "source_sha256": sha(canonical(source)),
        "control_sha256": sha(canonical(control)),
        "subsets": subsets,
        "detector_crop_count": len(detector),
        "detector_owned_word_appearances": len(owned),
        "detector_owned_unique_ids": len(set(owned)),
        "detector_multiple_owner_extra_occurrences": len(owned) - len(set(owned)),
        "detector_ownership_fraction": len(set(owned)) / len(lookup) if lookup else None,
        "geometry_assignment_fraction": len(assigned) / len(lookup) if lookup else None,
        "geometry_assigned_outside_detector_union_ids": [i for i in assigned if i not in owned_set],
        "source_membership_receipts": membership,
        "max_detector_word_overlap_distribution": distribution(
            [m["max_detector_bbox_word_area_overlap"] for m in membership]
        ),
        "references_read": False,
        "availability_or_ceiling_score": None,
    }
