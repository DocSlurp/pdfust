"""Grounded controls preserve original-page evidence and keep references private."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from bench.decision_assembly import assemble_case
from bench.decision_cases import model_payload
from bench.decision_controls import build_controls, write_controls

import pylopdf


@pytest.fixture(scope="module")
def controls() -> list[dict[str, Any]]:
    """Collect fixed native regional observations once."""
    return build_controls()


def test_grounded_scope_and_determinism(controls: list[dict[str, Any]]) -> None:
    assert len(controls) == 8
    assert Counter(case["gold"] for case in controls) == {True: 4, False: 4}
    assert {case["task"] for case in controls} == {"table"}
    assert {case["split"] for case in controls} == {"test"}
    assert Counter(case["family"] for case in controls) == {"public-report": 6, "existing-synthetic": 2}
    assert len({case["id"] for case in controls}) == 8
    assert build_controls() == controls
    for case in controls:
        assert case["state"]["words"]
        assert 2 <= len(case["state"]["candidate"]["rows"]) <= 6
        assert all(len(row) >= 2 for row in case["state"]["candidate"]["rows"])
        assert case["provenance"]["source_ids"] == [word["id"] for word in case["state"]["words"]]
        assert "clipped subset" in case["provenance"]["reference_criterion"]
        assert "provenance" not in model_payload(case)
        assert "source_note" not in model_payload(case)
        assert len(json.dumps(model_payload(case), separators=(",", ":"))) < 6000


def test_original_source_words_and_page_clips(controls: list[dict[str, Any]]) -> None:
    public = [case for case in controls if case["family"] == "public-report"]
    for case in public:
        provenance = case["provenance"]
        original = Path(provenance["pdf"]).read_bytes()
        assert hashlib.sha256(original).hexdigest() == provenance["pdf_sha256"]
        with pylopdf.open(stream=original) as document:
            snapshot = document[provenance["page_zero_based"]].get_layout(table_strategy=None)
        selected = snapshot.select(provenance["clip_display"])
        assert [word.id for word in selected] == provenance["source_ids"]
        assert [word.text for word in selected] == [word["text"] for word in case["state"]["words"]]
        assert [[round(c, 2) for c in word.bbox] for word in selected] == [
            word["bbox"] for word in case["state"]["words"]
        ]
    assert any(min(case["provenance"]["source_ids"]) > 0 for case in public)
    for filename in ("nics-background-checks-2015-11.pdf", "senate-expenditures.pdf"):
        regions = [case for case in public if case["provenance"]["pdf"].endswith(filename)]
        assert len(regions) == 2
        assert set(regions[0]["provenance"]["source_ids"]).isdisjoint(regions[1]["provenance"]["source_ids"])


def test_declared_source_content(controls: list[dict[str, Any]]) -> None:
    texts = [{word["text"] for word in case["state"]["words"]} for case in controls]
    assert {"Alabama", "18,870", "23,022", "Arkansas"} <= texts[0]
    assert {"BAIN,", "SMITH,", "ARMER,", "37,499.96"} <= texts[2]
    assert {"DHAW20190001", "DHAW20190002", "DHAW20190003", "920.68"} <= texts[3]
    assert {"Treasury", "appropriated,", "2024,"} <= texts[4]
    assert {"LATEX2ε", "1994"} <= texts[5]
    assert {"LEFT0", "RIGHT0"} <= texts[6]
    assert {"1900", "1901", "1902", "1903"} <= texts[7]


def test_reference_application_uses_retained_ids(controls: list[dict[str, Any]]) -> None:
    for case in controls:
        result = assemble_case(case, case["gold"])
        assert result["words"] == case["state"]["words"]
        assert len(result["accepted"]) == int(case["gold"])
        if result["accepted"]:
            retained = {word["id"] for word in result["words"]}
            assert {wid for row in result["accepted"][0]["rows"] for wid in row} <= retained


def test_preserved_original_inputs(tmp_path: Path, controls: list[dict[str, Any]]) -> None:
    assert write_controls(tmp_path) == controls
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert len(manifest["pdfs"]) == 6
    assert json.loads((tmp_path / "cases.json").read_text()) == controls
    for filename, expected in manifest["pdfs"].items():
        data = (tmp_path / filename).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
    for case in controls:
        provenance = case["provenance"]
        data = (tmp_path / Path(provenance["pdf"]).name).read_bytes()
        with pylopdf.open(stream=data) as document:
            selected = (
                document[provenance["page_zero_based"]]
                .get_layout(table_strategy=None)
                .select(provenance["clip_display"])
            )
        assert [word.id for word in selected] == provenance["source_ids"]
