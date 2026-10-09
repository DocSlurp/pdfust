"""Private all-page DEV table-gate targets and source-only image adapter.

This task asks whether a page contains a ruled table grid. It does not test
cell transcription, merged spans, field assembly, or mathematical understanding.
The authored silver labels are not independently reviewed. Models may receive
only the source page image and the fixed question/choices below.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from bench.silver import guard_path, load_manifest, verify_input
from bench.silver_structure import LABEL, prepare_targets

QUESTION = (
    "Does the whole page image contain at least one ruled table grid with at least two rows and two columns? "
    "A ruled table grid has connected outer borders and internal rules that partition tabular cells; merged "
    "cells are allowed. A single rectangle around prose, an image frame, individual form-field boxes or "
    "checkboxes, and aligned text without a grid do not qualify. Choose A if a qualifying grid is visible, "
    "B if none is visible, or unresolved if the supplied image does not let you decide."
)
CHOICES = {
    "A": "Contains a qualifying ruled table grid",
    "B": "No qualifying ruled table grid",
    "unresolved": "Insufficient visible evidence to decide",
}


def model_question() -> dict[str, Any]:
    """Return fixed model-facing instructions with no case identifiers or authored labels."""
    return {"question": QUESTION, "choices": CHOICES.copy()}


def silver_image_cases(directory: Path) -> list[dict[str, Any]]:
    """Return every verified physical DEV page with private gate labels separate from evidence.

    ``pdf_bytes`` and ``page_index`` select the whole source page for rendering.
    All remaining per-case fields are local scoring/provenance metadata and must
    not enter a model prompt. Use ``model_question()`` for model instructions.
    Ten of the current125pages are positive, so report positive precision/recall,
    negative specificity, macro metrics and unresolved counts alongside accuracy.
    Do not describe table-presence performance as full structural extraction.
    """
    directory = guard_path(directory)
    targets = prepare_targets(directory)
    manifest = load_manifest(directory)
    sources = {record["id"]: verify_input(directory, record).read_bytes() for record in manifest["cases"]}
    return [
        {
            "id": f"{page['id']}/page-{page['page_number']}",
            "case_id": f"{page['id']}/page-{page['page_number']}",
            "pdf_bytes": sources[page["id"]],
            "page_index": page["page_number"],
            "page_number": page["page_number"],
            "expected_document": "A" if page["tables"] else "B",
            "family": page["family"],
            "encoding": page["encoding"],
            "source_id": page["id"],
            "pdf_sha256": page["pdf_sha256"],
            "dataset_sha256": targets["dataset_sha256"],
            "split": "DEV",
            "label_status": LABEL,
            "task": "whole-page ruled-table presence only",
        }
        for page in targets["pages"]
    ]
