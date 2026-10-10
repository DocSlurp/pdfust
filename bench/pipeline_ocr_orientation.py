"""Opt-in, bounded source-only right-angle OCR orientation selection.

Confidence is provider evidence, not calibrated correctness. Near ties and weak
text inventories abstain; construction references are unavailable here.
"""

# ruff: noqa: ANN401, EM101, TRY003, PLR2004
from __future__ import annotations

import math
import time
from collections import Counter
from typing import Any

ROTATIONS = (0, 90, 180, 270)
MIN_ALNUM = 16
MIN_BOXES = 3
MIN_CONFIDENCE = 0.75
MIN_MARGIN = 0.15
MAX_CANDIDATE_WORDS = 16_384
MAX_CANDIDATE_TEXT = 1_048_576


def evidence(words: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize recognized character inventory without any language dictionary."""
    characters = 0
    weighted = 0.0
    inventory: Counter[str] = Counter()
    for word in words:
        text, confidence = word["text"], word["confidence"]
        if not isinstance(text, str) or not isinstance(confidence, (float, int)) or not math.isfinite(confidence):
            raise ValueError("Invalid OCR orientation evidence")
        if not 0 <= confidence <= 1:
            raise ValueError("OCR confidence outside unit interval")
        count = sum(character.isalnum() for character in text)
        characters += count
        weighted += confidence * count
        inventory.update(text.split())
    return {
        "alnum_characters": characters,
        "box_count": len(words),
        "score": weighted,
        "mean_confidence": weighted / characters if characters else 0.0,
        "text_inventory": dict(inventory),
    }


def choose(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Rank all four retained passes and abstain below frozen evidence gates."""
    if len(candidates) != 4 or {candidate["rotation"] for candidate in candidates} != set(ROTATIONS):
        raise ValueError("Orientation requires all four distinct right-angle passes")
    ranked = sorted(candidates, key=lambda candidate: (-candidate["evidence"]["score"], candidate["rotation"]))
    best, second = ranked[:2]
    summary = best["evidence"]
    margin = (summary["score"] - second["evidence"]["score"]) / max(1.0, summary["score"])
    selected = (
        summary["alnum_characters"] >= MIN_ALNUM
        and summary["box_count"] >= MIN_BOXES
        and (summary["mean_confidence"] >= MIN_CONFIDENCE and margin >= MIN_MARGIN)
    )
    return {
        "selected_rotation": best["rotation"] if selected else None,
        "status": "selected" if selected else "abstained_uncertain_orientation",
        "relative_margin": margin,
        "best_rotation": best["rotation"],
        "thresholds": {
            "minimum_alnum": MIN_ALNUM,
            "minimum_boxes": MIN_BOXES,
            "minimum_confidence": MIN_CONFIDENCE,
            "minimum_relative_margin": MIN_MARGIN,
        },
    }


def recognize(page: Any, *, dpi: float, engine: Any = None, clip: Any = None) -> dict[str, Any]:
    """Run four CPU passes, retain full evidence and charge every candidate cost."""
    if isinstance(dpi, bool) or not isinstance(dpi, (int, float)) or not math.isfinite(dpi) or dpi <= 0:
        raise ValueError("OCR DPI must be positive and finite")
    bounds = list(page.rect) if clip is None else list(clip)
    if len(bounds) != 4 or any(not math.isfinite(value) for value in bounds):
        raise ValueError("OCR orientation geometry must be finite")
    pixels = math.ceil((bounds[2] - bounds[0]) * dpi / 72) * math.ceil((bounds[3] - bounds[1]) * dpi / 72)
    full = list(page.rect)
    full_pixels = math.ceil(full[2] * dpi / 72) * math.ceil(full[3] * dpi / 72)
    if pixels <= 0 or pixels * 4 > 64_000_000 or full_pixels > 64_000_000:
        raise ValueError("Complete four-pass OCR orientation raster exceeds admission")
    candidates = []
    total_words = total_bytes = 0
    for rotation in ROTATIONS:
        start, cpu = time.perf_counter(), time.process_time()
        words = page.get_text_ocr(dpi=dpi, engine=engine, clip=clip, rotation=rotation)
        total_words += len(words)
        total_bytes += sum(len(word["text"].encode("utf-8")) for word in words)
        if total_words > MAX_CANDIDATE_WORDS or total_bytes > MAX_CANDIDATE_TEXT:
            raise ValueError("Complete OCR orientation candidate evidence exceeds admission")
        retained = [
            {"bbox": list(word["bbox"]), "text": word["text"], "confidence": word["confidence"]} for word in words
        ]
        candidates.append(
            {
                "rotation": rotation,
                "words": retained,
                "evidence": evidence(retained),
                "wall_seconds": time.perf_counter() - start,
                "cpu_seconds": time.process_time() - cpu,
            }
        )
    decision = choose(candidates)
    selected = decision["selected_rotation"]
    return {
        **decision,
        "candidates": candidates,
        "candidate_render_pixels": pixels * 4,
        "candidate_full_page_render_pixels": full_pixels * 4,
        "words": next(candidate["words"] for candidate in candidates if candidate["rotation"] == selected)
        if selected is not None
        else [],
        "all_pass_wall_seconds": sum(candidate["wall_seconds"] for candidate in candidates),
        "all_pass_cpu_seconds": sum(candidate["cpu_seconds"] for candidate in candidates),
    }
