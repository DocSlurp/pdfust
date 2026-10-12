"""Check controlled encoding invariance and separation of scorer metadata."""

from collections import Counter, defaultdict
from collections.abc import Callable
from typing import Any

import pytest
from bench.lowlevel_cases import CHOICES, ENCODINGS, cases, history_cases

import pdfust


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
@pytest.mark.parametrize("builder", [cases, history_cases])
def test_identical_visible_pixels_across_operator_encodings(
    dpi: int, builder: Callable[[], list[dict[str, Any]]]
) -> None:
    grouped = defaultdict(list)
    for case in builder():
        grouped[case["logical_id"]].append(case)
    assert len(grouped) == (24 if builder is cases else 12)
    for variants in grouped.values():
        images = []
        for case in variants:
            with pdfust.Document(stream=case["pdf_bytes"]) as document:
                pixmap = document[0].get_pixmap(dpi=dpi)
                images.append((pixmap.width, pixmap.height, pixmap.samples))
        assert images[0] == images[1] == images[2]
        assert variants[0]["evidence"] == variants[1]["evidence"] == variants[2]["evidence"]


def test_history_pairs_preserve_targets_and_distinguish_tentative_gold() -> None:
    cohort = history_cases()
    assert len(cohort) == 36
    assert Counter(case["expected"] for case in cohort) == {"join": 9, "split": 9, "unresolved": 18}
    for index in range(0, len(cohort), 12):
        present, absent, identifier, singleline = [cohort[index + offset] for offset in (0, 3, 6, 9)]
        assert present["evidence"] == absent["evidence"] == identifier["evidence"] == singleline["evidence"]
        assert present["recoverability"] == "conventional"
        assert absent["recoverability"] == singleline["recoverability"] == "unresolved"
        assert identifier["recoverability"] == "visible_identifier"
        with (
            pdfust.Document(stream=present["pdf_bytes"]) as first,
            pdfust.Document(stream=absent["pdf_bytes"]) as second,
        ):
            region = present["evidence"]["bbox"]
            assert first[0].get_pixmap(clip=region).samples == second[0].get_pixmap(clip=region).samples
