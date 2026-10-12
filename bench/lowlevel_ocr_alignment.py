"""Bounded, opt-in source-versus-visible text experiment on reviewed DEV crops.

Manual visual references are local scorer data, never candidate evidence. A
visual proposal is a separate provenance record; it never changes a Document,
source glyph, native word, or public extraction default. These source-aware,
single-review references are reviewable observations, not independent gold.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfust

MAX_FIXTURES = 12
MAX_CROP_GLYPHS = 1024
MAX_TEXT_BYTES = 8192
MAX_ACTION_FILE_BYTES = 65536
MAX_PAGE_PIXELS = 8_000_000
DPI = 216
ROOT = Path(__file__).resolve().parents[1]
PATENT_HASH = "e6f4d7747a8af8451d81aa3d5fe564aed5c8091091cb408c752b8a3cd7c28764"


@dataclass(frozen=True)
class VisualFixture:
    """Explicit source selector and separately reviewed visible transcription."""

    id: str
    filename: str
    source_sha256: str
    page: int
    bbox: tuple[float, float, float, float]
    visual_text: str | None
    review_note: str
    license: str = "US government work, public domain"


def fixtures() -> tuple[VisualFixture, ...]:
    """Return fixed paths only; never discover corpus or heldout artifacts."""
    patent = "patent-us223898.pdf"
    return (
        VisualFixture(
            "edison-name",
            patent,
            PATENT_HASH,
            0,
            (248, 64, 355, 88),
            "T. A. EDISON.",
            "Printed heading; encoded OCR spaces and final comma differ.",
        ),
        VisualFixture(
            "edison-date",
            patent,
            PATENT_HASH,
            0,
            (296, 108, 460, 130),
            "Patented Jan. 27, 1880.",
            "Digit zero is read from the year context; the shape alone does not distinguish zero/O.",
        ),
        VisualFixture(
            "edison-electric-agreement",
            patent,
            PATENT_HASH,
            0,
            (248, 86, 357, 108),
            "Electric-Lamp.",
            "Printed subtitle, including the visible hyphen and period.",
        ),
        VisualFixture(
            "edison-electric-corruption",
            patent,
            PATENT_HASH,
            1,
            (205, 150, 330, 174),
            "ELECTRIC LAMP.",
            "Printed uppercase heading; substantial OCR substitutions/fragmentation.",
        ),
        VisualFixture(
            "edison-watermark",
            patent,
            PATENT_HASH,
            2,
            (284, 7, 404, 62),
            "BEST AVAILABLE COPY",
            "Tilted scan watermark; all three words are legible.",
        ),
        VisualFixture(
            "edison-department",
            patent,
            PATENT_HASH,
            3,
            (185, 138, 364, 154),
            "DEPARTMENT OF THE INTERIOR,",
            "Printed agency heading; edge pixels below are not transcribed.",
        ),
        VisualFixture(
            "edison-degraded-body",
            patent,
            PATENT_HASH,
            1,
            (61, 571, 263, 602),
            None,
            "Clipped lines, scan damage and touching ink prevent an exact complete transcription.",
        ),
        VisualFixture(
            "irs-label-agreement",
            "f1040.pdf",
            "3d31c226df0d189ced80e039d01cf0f8820c1019681a0f0ca6264de277b7e982",
            0,
            (108, 230, 321, 241),
            "Married filing separately (MFS). Enter spouse’s SSN above",
            "One printed label line; retain the typographic apostrophe.",
        ),
        VisualFixture(
            "nics-numeric-agreement",
            "nics-background-checks-2015-11.pdf",
            "4f0ae6e017b0e97de211da8fd97316e55bd927af5740d6ce95e1b7b1539f9407",
            0,
            (118, 79, 179, 88),
            "18,870 23,022",
            "Two neighboring ruled cells; one space represents the cell boundary, not a printed glyph.",
        ),
    )


def _digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def comparison_text(text: str) -> str:
    """Collapse whitespace only; preserve case, punctuation and Unicode."""
    return " ".join(text.split())


def character_edits(left: str, right: str) -> int:
    """Count Unicode edit operations with bounded linear scratch memory."""
    if max(len(left), len(right)) > MAX_CROP_GLYPHS:
        msg = "comparison exceeds the 1024-character metric bound"
        raise ValueError(msg)
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, char in enumerate(left, 1):
        current = [i]
        for j, other in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (char != other)))
        previous = current
    return previous[-1]


def build_evidence(fixture: VisualFixture, output: Path) -> dict[str, Any]:
    """Render and freeze source evidence without exposing visual references."""
    path = ROOT / "tests/assets/real_world" / fixture.filename
    if path.stat().st_size > 10 * 1024 * 1024:
        msg = "source exceeds the experiment file cap"
        raise ValueError(msg)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != fixture.source_sha256:
        msg = f"source hash changed for {fixture.id}"
        raise ValueError(msg)
    with pdfust.open(stream=raw, limits=pdfust.DocumentLimits.web()) as doc:
        doc._ensure_fallback_fonts()  # noqa: SLF001 - match public extraction setup
        width, height, rows, skipped = doc._doc.extract_glyph_snapshot(fixture.page + 1)  # noqa: SLF001
        doc._emit_warnings()  # noqa: SLF001 - preserve interpretation warnings
        x0, y0, x1, y1 = fixture.bbox
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            msg = "crop must lie inside the display page"
            raise ValueError(msg)
        if math.ceil(width * DPI / 72) * math.ceil(height * DPI / 72) > MAX_PAGE_PIXELS:
            msg = "full-page raster exceeds the experiment pixel cap"
            raise ValueError(msg)
        selected = [r for r in rows if x0 <= r[2][0] <= x1 and y0 <= r[2][1] <= y1]
        if len(selected) > MAX_CROP_GLYPHS:
            msg = "crop exceeds the experiment glyph cap"
            raise ValueError(msg)
        source_text = "".join(r[1] for r in selected)
        if len(source_text.encode()) > MAX_TEXT_BYTES:
            msg = "crop exceeds the experiment text cap"
            raise ValueError(msg)
        words = [
            r
            for r in doc[fixture.page].get_text("words")
            if x0 <= (r[0] + r[2]) / 2 <= x1 and y0 <= (r[1] + r[3]) / 2 <= y1
        ]
        image_path = output / f"{fixture.id}.png"
        doc[fixture.page].get_pixmap(dpi=DPI, background=(255, 255, 255), clip=fixture.bbox).save(str(image_path))
    evidence: dict[str, Any] = {
        "schema": "source-visible-alignment-v1",
        "fixture_id": fixture.id,
        "source": {
            "path": str(path),
            "sha256": fixture.source_sha256,
            "page": fixture.page,
            "bbox": fixture.bbox,
            "license": fixture.license,
        },
        "image": {
            "path": str(image_path),
            "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
            "dpi": DPI,
            "background": [255, 255, 255],
        },
        "source_glyph_rows": selected,
        "source_ids": [r[0] for r in selected],
        "source_text": source_text,
        "native_words": words,
        "native_words_text": " ".join(r[4] for r in words),
        "skipped_no_unicode_page": skipped,
        "selection": "baseline origin inside display crop; not glyph visibility or clipping",
        "question": "Retain the source text, propose a separate visible transcription, or abstain.",
        "allowed_actions": ["retain_source", "propose_visual_transcription", "abstain"],
    }
    evidence["evidence_sha256"] = _digest(evidence)
    return evidence


def validate_action(evidence: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    """Bind a bounded action to exact frozen evidence and preserve its source."""
    allowed = {"fixture_id", "evidence_sha256", "source_ids", "decision", "proposed_text", "reason"}
    if set(action) != allowed:
        msg = "action must contain exactly the documented fields"
        raise ValueError(msg)
    frozen = {key: value for key, value in evidence.items() if key != "evidence_sha256"}
    if _digest(frozen) != evidence["evidence_sha256"]:
        msg = "evidence content does not match its fingerprint"
        raise ValueError(msg)
    if action["fixture_id"] != evidence["fixture_id"] or action["evidence_sha256"] != evidence["evidence_sha256"]:
        msg = "action identifies different evidence"
        raise ValueError(msg)
    ids = action["source_ids"]
    if not isinstance(ids, list) or any(type(i) is not int for i in ids) or ids != evidence["source_ids"]:
        msg = "action must retain the complete ordered source ID sequence"
        raise ValueError(msg)
    decision, proposed, reason = action["decision"], action["proposed_text"], action["reason"]
    if decision not in evidence["allowed_actions"]:
        msg = "unsupported visual alignment action"
        raise ValueError(msg)
    if not isinstance(reason, str) or not reason.strip() or len(reason.encode()) > MAX_TEXT_BYTES:
        msg = "action needs a bounded nonempty reason"
        raise ValueError(msg)
    if decision == "propose_visual_transcription":
        if not isinstance(proposed, str) or not proposed.strip() or len(proposed.encode()) > MAX_TEXT_BYTES:
            msg = "visual proposal needs bounded nonempty text"
            raise ValueError(msg)
    elif proposed is not None:
        msg = "retain and abstain actions cannot supply replacement text"
        raise ValueError(msg)
    return {
        "fixture_id": evidence["fixture_id"],
        "source": copy.deepcopy(evidence["source"]),
        "evidence_sha256": evidence["evidence_sha256"],
        "source_ids": list(ids),
        "original_source_text": evidence["source_text"],
        "native_words_text": evidence["native_words_text"],
        "decision": decision,
        "visual_text_proposal": proposed,
        "reason": reason,
        "status": "proposal-sidecar-only",
        "source_modified": False,
    }


def score_action(evidence: dict[str, Any], fixture: VisualFixture, action: dict[str, Any]) -> dict[str, Any]:
    """Compare with a separate single-review reference; unknown stays unknown."""
    result = validate_action(evidence, action)
    if fixture.id != evidence["fixture_id"]:
        msg = "reference belongs to a different fixture"
        raise ValueError(msg)
    source = evidence["source"]
    if (
        source.get("sha256") != fixture.source_sha256
        or source.get("page") != fixture.page
        or tuple(source.get("bbox", ())) != fixture.bbox
    ):
        msg = "reference provenance does not match the frozen source"
        raise ValueError(msg)
    reference = fixture.visual_text
    result["reference_status"] = "unavailable" if reference is None else "single-review-source-aware"
    result["reference_note"] = fixture.review_note
    result["proposal_exact_match"] = None
    result["source_character_edits"] = None
    result["words_character_edits"] = None
    if reference is not None:
        expected = comparison_text(reference)
        result["source_character_edits"] = character_edits(comparison_text(evidence["source_text"]), expected)
        result["words_character_edits"] = character_edits(comparison_text(evidence["native_words_text"]), expected)
        if action["decision"] == "propose_visual_transcription":
            result["proposal_exact_match"] = comparison_text(action["proposed_text"]) == expected
    return result


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def _memory_measurements() -> dict[str, object]:
    """Separate Linux process HWM from a possibly inherited getrusage peak."""
    reported = None
    try:
        resource = importlib.import_module("resource")
        reported = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except ModuleNotFoundError:
        pass
    try:
        lines = Path("/proc/self/status").read_text().splitlines()
    except OSError:
        return {
            "peak_rss_kib": None,
            "getrusage_ru_maxrss": reported,
            "rss_measurement": "Linux /proc unavailable; getrusage raw units retained separately",
        }
    peak = next((int(line.split()[1]) for line in lines if line.startswith("VmHWM:")), None)
    return {
        "peak_rss_kib": peak,
        "getrusage_ru_maxrss": reported,
        "rss_measurement": "Linux /proc/self/status VmHWM, process scope; no sampling",
    }


def run(output: Path, actions_path: Path | None = None) -> dict[str, Any]:
    """Generate independent candidate evidence, reviewer references and scores."""
    selected = fixtures()
    if len(selected) > MAX_FIXTURES:
        msg = "fixture count exceeds experiment cap"
        raise ValueError(msg)
    output.mkdir(parents=True, exist_ok=True)
    wall, cpu = time.perf_counter(), time.process_time()
    evidence = [build_evidence(fixture, output) for fixture in selected]
    _write(output / "evidence.json", evidence)
    _write(
        output / "review-references.json",
        [
            {
                "fixture_id": f.id,
                "visual_text": f.visual_text,
                "review_note": f.review_note,
                "review_status": "unavailable" if f.visual_text is None else "single-review-source-aware",
            }
            for f in selected
        ],
    )
    templates = [
        {
            "fixture_id": e["fixture_id"],
            "evidence_sha256": e["evidence_sha256"],
            "source_ids": e["source_ids"],
            "decision": "abstain",
            "proposed_text": None,
            "reason": "No independent visual repair submitted.",
        }
        for e in evidence
    ]
    _write(output / "action-template.json", templates)
    _write(
        output / "native-comparison.json",
        [score_action(e, f, action) for e, f, action in zip(evidence, selected, templates, strict=True)],
    )
    actions = []
    if actions_path is not None:
        with actions_path.open("rb") as stream:
            data = stream.read(MAX_ACTION_FILE_BYTES + 1)
        if len(data) > MAX_ACTION_FILE_BYTES:
            msg = "action file exceeds experiment byte cap"
            raise ValueError(msg)
        actions = json.loads(data)
        if not isinstance(actions, list) or len(actions) > MAX_FIXTURES:
            msg = "actions must be a bounded list"
            raise ValueError(msg)
    by_id = {e["fixture_id"]: (e, f) for e, f in zip(evidence, selected, strict=True)}
    results = []
    seen = set()
    for action in actions:
        if not isinstance(action, dict) or action.get("fixture_id") not in by_id:
            msg = "action references an unknown fixture"
            raise ValueError(msg)
        ident = action["fixture_id"]
        if ident in seen:
            msg = "duplicate fixture actions are not allowed"
            raise ValueError(msg)
        seen.add(ident)
        e, f = by_id[ident]
        results.append(score_action(e, f, action))
    _write(output / "action-results.json", results)
    summary = {
        "fixtures": len(selected),
        "reviewed": sum(f.visual_text is not None for f in selected),
        "unavailable": sum(f.visual_text is None for f in selected),
        "scored_actions": len(results),
        "unsubmitted_actions": len(selected) - len(results),
        "wall_s": time.perf_counter() - wall,
        "cpu_s": time.process_time() - cpu,
        **_memory_measurements(),
        "measurement": "perf_counter/process_time; no workers; Linux VmHWM process peak RSS",
        "model_calls": 0,
        "source_edits": 0,
        "limitations": "Convenience sample; source-aware single review; no quality or generalization claim.",
    }
    _write(output / "summary.json", summary)
    return summary


def main() -> None:
    """Run the explicit CPU-only benchmark without hosted inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".scratch/ocr-alignment")
    parser.add_argument("--actions", type=Path, help="Optional locally produced action JSON; no model calls")
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.actions), indent=2))


if __name__ == "__main__":
    main()
