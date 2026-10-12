"""Source interventions preserve body evidence and ignore private metadata."""
from __future__ import annotations

from copy import deepcopy

import pytest
from bench.feature_cases import text_op
from bench.silver_layouts import _pdf
from bench.source_cue_audit import REMOVALS, audit_source, neutralize_pdf

import pdfust


def test_exact_literal_deletion_retains_body_geometry_and_pdf_length() -> None:
    for index, phrase in enumerate(REMOVALS):
        pdf = _pdf([text_op(phrase, 48, 718) + "\n" + text_op("Harbor 37 12", 48, 674)], index, "neutral", "1.4")
        neutral, counts = neutralize_pdf(pdf)
        assert counts[phrase] == 1
        with pdfust.open(stream=pdf) as before, pdfust.open(stream=neutral) as after:
            expected = [w for w in before[0].get_text("words") if w[1] > 100]
            assert after[0].get_text("words") == expected
            assert after[0].get_text().strip() == "Harbor 37 12"


def test_substrings_and_body_semantics_remain_unchanged() -> None:
    pdf = _pdf([text_op("Review complete tomorrow", 48, 500)], 0, "neutral", "1.4")
    with pytest.raises(ValueError, match="No declared"):
        neutralize_pdf(pdf)


def test_audit_ignores_metadata_labels() -> None:
    source = {"pages": [{"id": "x", "words": [{"text": "Read each row as one station record."}]}]}
    changed = deepcopy(source)
    changed["pages"][0]["private_kind"] = "prose"
    assert audit_source(changed) == audit_source(source)
