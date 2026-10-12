"""Evidence and leakage boundaries for the authored decision benchmark."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.decision_cases import baseline, build_cases, model_payload, write_cases

import pdfust


@pytest.fixture(scope="module")
def cases() -> list[dict[str, Any]]:
    """Extract all compact authored PDFs once for this test module."""
    return build_cases()


def test_balanced_frozen_cases(cases: list[dict[str, Any]]) -> None:
    assert len(cases) == 96
    assert Counter(case["family"] for case in cases) == {"financial": 32, "invoice": 32, "scientific": 32}
    assert Counter(case["task"] for case in cases) == {"table": 24, "wrap": 24, "header": 24, "assignment": 24}
    assert Counter(case["split"] for case in cases) == {"calibration": 48, "test": 48}
    assert Counter(case["gold"] for case in cases) == {True: 36, False: 36, None: 24}
    assert build_cases() == cases
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        assert 8 <= len(case["state"]["words"]) <= 25
        assert len(json.dumps(model_payload(case), separators=(",", ":"))) < 2200
        assert 0 <= case["baseline_probability"] <= 1
        assert 0 <= case["baseline_answerable"] <= 1


def test_no_evaluator_metadata_in_model_input(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        payload = model_payload(case)
        assert set(payload) == {"id", "question", "state"}
        assert set(payload["state"]) == {"task", "page", "words", "candidate", "context_ids"}
        changed = deepcopy(case)
        changed.update(gold=not case["gold"], family="changed", split="changed", source_note="changed")
        assert model_payload(changed) == payload
        assert baseline(changed["state"]) == (case["baseline_probability"], case["baseline_answerable"])


def test_source_word_references_are_complete(cases: list[dict[str, Any]]) -> None:
    def references(value: Any) -> list[int]:  # noqa: ANN401 - recursive JSON candidate data
        if isinstance(value, int):
            return [value]
        return [wid for part in value for wid in references(part)]

    for case in cases:
        state = case["state"]
        ids = {word["id"] for word in state["words"]}
        assert len(ids) == len(state["words"])
        for value in state["candidate"].values():
            assert references(value)
            assert set(references(value)) <= ids
        for word in state["words"]:
            x0, y0, x1, y1 = word["bbox"]
            assert 0 <= x0 < x1 <= state["page"][0]
            assert 0 <= y0 < y1 <= state["page"][1]


def test_disjoint_templates(cases: list[dict[str, Any]]) -> None:
    headings: dict[str, set[str]] = {"calibration": set(), "test": set()}
    for case in cases:
        if case["gold"] is None:
            continue
        state = case["state"]
        words = {word["id"]: word for word in state["words"]}
        headings[case["split"]].add(" ".join(words[wid]["text"] for wid in state["context_ids"]))
    assert headings["calibration"].isdisjoint(headings["test"])


def test_preserved_pdf_extraction_and_hashes(tmp_path: Path, cases: list[dict[str, Any]]) -> None:
    assert write_cases(tmp_path) == cases
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert len(manifest["pdfs"]) == 96
    assert json.loads((tmp_path / "cases.json").read_text()) == cases
    for case in cases:
        data = (tmp_path / f"{case['id']}.pdf").read_bytes()
        assert hashlib.sha256(data).hexdigest() == manifest["pdfs"][case["id"]]
        with pdfust.open(stream=data) as document:
            layout = document[0].get_layout(table_strategy=None)
        assert [word.text for word in layout.words] == [word["text"] for word in case["state"]["words"]]
        assert [word.id for word in layout.words] == [word["id"] for word in case["state"]["words"]]
        assert [[round(c, 2) for c in word.bbox] for word in layout.words] == [
            word["bbox"] for word in case["state"]["words"]
        ]
