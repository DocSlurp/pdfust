"""Previously grounded table/prose controls independent of frozen decision templates.

These eight regional gates contain four positive table fragments and four
negative prose regions. Two clips share each dense report producer, so eight
regions are not eight independent documents. Public PDFs and existing synthetic
fixtures were used by earlier geometry studies; held out means unused in the
96-case decision experiment, not unseen in all repository research. Sparse
record annotations do not support full table, header, assignment, or wrap gold.
No model outputs or inferred table detections determine reference labels.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pylopdf
from bench.decision_cases import baseline
from bench.feature_cases import ROOT, build_cases
from bench.geometry_cascade import derivative

_ASSETS = ROOT / "tests/assets/real_world"
_CRITERION = (
    "The retained region contains multiple records organized in repeated rows and columns, "
    "rather than continuous prose. A clipped subset of a larger table counts; this does not "
    "label a complete grid, individual cell ownership, or inferred missing content."
)
# Original display-coordinate clips, chosen from source content before any model evaluation.
_PUBLIC_REGIONS = (
    (
        "nics-background-checks-2015-11.pdf",
        0,
        (40, 70, 265, 108),
        True,
        "State rows Alabama through Arkansas; left six source columns of the FBI NICS report.",
    ),
    (
        "nics-background-checks-2015-11.pdf",
        0,
        (40, 109, 265, 138),
        True,
        "Following state records in the same six original NICS columns; disjoint from first clip.",
    ),
    (
        "senate-expenditures.pdf",
        0,
        (80, 101, 705, 156),
        True,
        "Report header and first three Senate payee/description/amount records.",
    ),
    (
        "senate-expenditures.pdf",
        0,
        (80, 204, 705, 244),
        True,
        "Three travel records DHAW20190001 through DHAW20190003, including description continuations.",
    ),
    (
        "bill-hr815.pdf",
        1,
        (190, 239, 520, 272),
        False,
        "Original page 2 appropriation preamble: one prose sentence wrapping across three lines.",
    ),
    (
        "usrguide.pdf",
        1,
        (120, 278, 473, 353),
        False,
        "Original page 2 Introduction body paragraphs below the contents and section title.",
    ),
)


def _observe(data: bytes, page: int, clip: tuple[int, int, int, int]) -> dict[str, Any]:
    """Select native word centers in an original-page display-coordinate region."""
    with pylopdf.open(stream=data) as document:
        layout = document[page].get_layout(table_strategy=None)
    selected = layout.select(clip)
    words = [
        {"id": word.id, "text": word.text, "bbox": [round(c, 2) for c in word.bbox], "line": word.line}
        for word in selected
    ]
    # Candidate physical bands use geometry only, not table detection or references.
    bands: list[tuple[float, list[int]]] = []
    for word in sorted(selected, key=lambda word: (word.bbox[1], word.bbox[0], word.id)):
        if bands and abs(word.bbox[1] - bands[-1][0]) <= 1.0:
            bands[-1][1].append(word.id)
        else:
            bands.append((word.bbox[1], [word.id]))
    rows = [ids for _baseline, ids in bands if len(ids) >= 2]  # noqa: PLR2004
    return {
        "task": "table",
        "page": [layout.width, layout.height],
        "words": words,
        "candidate": {"rows": rows, "region": list(clip)},
        "context_ids": [],
    }


def _build() -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    cases: list[dict[str, Any]] = []
    sources: dict[str, bytes] = {}
    inputs = [
        (name, (_ASSETS / name).read_bytes(), page, clip, gold, note, "public-report")
        for name, page, clip, gold, note in _PUBLIC_REGIONS
    ]
    two_column = next(case for case in build_cases() if case.name == "two-column-order")
    numeric = derivative("numeric-prose", reverse=True).feature
    inputs.extend(
        (
            (
                two_column.name + ".pdf",
                two_column.data,
                0,
                (35, 80, 600, 156),
                False,
                "Existing two-column-order fixture: four physical prose bands from independent left/right paragraphs.",
                "existing-synthetic",
            ),
            (
                numeric.name + ".pdf",
                numeric.data,
                0,
                (40, 100, 570, 266),
                False,
                "Existing geometry-cascade numeric-prose fixture: sentence fragments beside years, not record fields.",
                "existing-synthetic",
            ),
        )
    )
    for name, data, page, clip, gold, note, family in inputs:
        state = _observe(data, page, clip)
        digest = hashlib.sha256(data).hexdigest()
        identifier = "control-" + hashlib.sha256(data + json.dumps([page, clip]).encode()).hexdigest()[:12]
        probability, answerable = baseline(state)
        provenance = {
            "pdf": str(_ASSETS / name) if family == "public-report" else name,
            "pdf_sha256": digest,
            "page_zero_based": page,
            "clip_display": list(clip),
            "selection": "half-open clip contains word centers; Page.get_layout(table_strategy=None)",
            "source_ids": [word["id"] for word in state["words"]],
            "reference_criterion": _CRITERION,
            "license": "Source/license in tests/assets/real_world/README.md"
            if family == "public-report"
            else "Repository-authored synthetic PDF; repository MIT license",
            "prior_source": "bench/feature_cases.py and bench/specialist_cpu.py"
            if name == two_column.name + ".pdf"
            else "bench/geometry_cascade.py: derivative(numeric-prose, reverse=True)"
            if family == "existing-synthetic"
            else "Bundled original corpus PDF",
        }
        cases.append(
            {
                "id": identifier,
                "family": family,
                "task": "table",
                "split": "test",
                "question": "Does the candidate region contain rows and columns of records rather than prose?",
                "state": state,
                "gold": gold,
                "baseline_probability": probability,
                "baseline_answerable": answerable,
                "source_note": note,
                "provenance": provenance,
            }
        )
        sources[name] = data
    return cases, sources


def build_controls() -> list[dict[str, Any]]:
    """Return eight independent regional controls without artifact writes."""
    return _build()[0]


def write_controls(directory: str | Path) -> list[dict[str, Any]]:
    """Preserve original PDFs, selected native words, region criteria, and hashes."""
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    cases, sources = _build()
    for name, data in sources.items():
        (destination / name).write_bytes(data)
    manifest = {
        "source_scope": __doc__,
        "criterion": _CRITERION,
        "pdfs": {name: hashlib.sha256(data).hexdigest() for name, data in sources.items()},
        "extraction": "Original full PDFs; original page numbers; native source IDs before clipping",
    }
    (destination / "cases.json").write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return cases
