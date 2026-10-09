"""Check controlled encoding invariance and separation of scorer metadata."""

from collections import Counter, defaultdict

import pytest
from bench.lowlevel_cases import CHOICES, ENCODINGS, cases

import pylopdf


def test_balanced_crossed_encodings_and_evidence() -> None:
    cohort = cases()
    assert len(cohort) == 72
    assert len({case["id"] for case in cohort}) == 72
    assert Counter((case["family"], case["expected"], case["encoding"]) for case in cohort) == {
        (family, choice, encoding): 4 for family in ("boundary", "wrap") for choice in CHOICES for encoding in ENCODINGS
    }
    for case in cohort:
        evidence = case["evidence"]
        assert evidence["choices"] == list(CHOICES)
        assert set(evidence) == {"task", "question", "bbox", "target", "choices"}
        assert "text" not in evidence["target"]
        assert set(evidence["target"]) == {"boxes", "boundary_index"}


@pytest.mark.parametrize("dpi", [72, 144])
def test_identical_visible_pixels_across_operator_encodings(dpi: int) -> None:
    grouped = defaultdict(list)
    for case in cases():
        grouped[case["logical_id"]].append(case)
    assert len(grouped) == 24
    for variants in grouped.values():
        images = []
        for case in variants:
            with pylopdf.Document(stream=case["pdf_bytes"]) as document:
                pixmap = document[0].get_pixmap(dpi=dpi)
                images.append((pixmap.width, pixmap.height, pixmap.samples))
        assert images[0] == images[1] == images[2]
        assert variants[0]["evidence"] == variants[1]["evidence"] == variants[2]["evidence"]
