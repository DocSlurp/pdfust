"""Seeded office-value construction, exact typed contents and runtime/reference isolation."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from bench import p003_random_values_corpus as corpus
from bench.generalization_report import load_corpus
from bench.silver import sha

import pdfust


def test_seeded_plans_variety_and_values_not_identity_derived() -> None:
    plans = corpus.plans()
    assert plans == corpus.plans()
    assert plans != corpus.plans("independent-new-seed")
    assert len(plans) == 40
    assert len({p["id"] for p in plans}) == 40
    assert Counter(p["family"] for p in plans if p["tables"]) == dict.fromkeys(corpus.FAMILIES, 4)
    flavors = Counter()
    for plan in plans:
        for table in plan["tables"]:
            target = table["target"]
            assert 8 <= target["row_count"] <= 24
            assert 3 <= target["col_count"] <= 6
            duplicate = table["deliberate_duplicate"]
            first, second = duplicate["first_row"], duplicate["second_row"]
            column = duplicate["column"]
            assert first != second
            assert target["values"][first][column] not in (None, "")
            assert target["values"][first][column] == target["values"][second][column]
            for row in target["values"][1:]:
                flavors.update(corpus.flavor(v) for v in row if v is not None)
    assert all(
        flavors[k] > 0
        for k in (
            "usd:negative",
            "usd:zero",
            "usd:positive",
            "date:ISO",
            "date:US",
            "date:English",
            "blank",
            "noise:N/A",
            "noise:NULL",
            "noise:\u2014",
            "english:1",
            "english:2",
        )
    )
    plan = plans[2]
    data, targets, _ = corpus.authored(plan)
    renamed = {**plan, "id": "opaque-replacement-identity"}
    other, other_targets, _ = corpus.authored(renamed)
    assert data == other
    assert targets == other_targets
    assert plan["id"].encode() not in data


def test_actual_textbox_wrap_right_alignment_and_source_roundtrip() -> None:
    plan = next(p for p in corpus.plans() if p["family"] == "wrapped")
    data, targets, receipt = corpus.authored(plan)
    assert any(c["unused_vertical_space"] < 8 for c in receipt["construction_cells"] if c["literal"])
    assert any(c["align"] == pdfust.TEXT_ALIGN_RIGHT for c in receipt["construction_cells"])
    with pdfust.Document(stream=data) as document:
        words = [
            {"id": f"w{i}", "bbox": list(w[:4]), "text": w[4]} for i, w in enumerate(document[0].get_text("words"))
        ]
        assert words == receipt["source"]["words"]
        assert not any(plan["id"] in str(v) for v in document.metadata.values())
    assert targets[0]["bbox"][3] < 710


def test_merged_headers_and_continuations_rectangular_coverage() -> None:
    for family in ("merged_headers", "continuations"):
        plan = next(p for p in corpus.plans() if p["family"] == family)
        data, targets, _ = corpus.authored(plan)
        assert data.startswith(b"%PDF")
        for target in targets:
            covered = set()
            for span in target["spans"]:
                for row in range(span["row"], span["row"] + span["row_span"]):
                    for column in range(span["column"], span["column"] + span["column_span"]):
                        assert (row, column) not in covered
                        covered.add((row, column))
            assert len(covered) == target["row_count"] * target["col_count"]
            assert any(s["row_span"] > 1 or s["column_span"] > 1 for s in target["spans"])


def test_complete_frozen40_compatible_loader_gallery_and_gold_separate(tmp_path: Path) -> None:
    output = tmp_path / "new-corpus"
    frozen = corpus.build(output)
    assert frozen["case_count"] == 40
    assert frozen["table_page_count"] == 32
    assert frozen["negative_page_count"] == 8
    manifest, targets = load_corpus(output)
    assert len(manifest["pages"]) == 40
    assert len(targets["pages"]) == 40
    assert sum(len(t["tables"]) for t in targets["pages"]) == 36
    assert sum(not t["tables"] for t in targets["pages"]) == 8
    assert manifest["model_fields"] == ["id", "pdf_path", "pdf_sha256", "page_number"]
    inventory = json.loads((output / "source-inventory.json").read_bytes())
    assert inventory["source_only"] is True
    assert len(inventory["artifacts"]) == 120
    for path, digest in inventory["artifacts"].items():
        assert sha((output / path).read_bytes()) == digest
        assert "private" not in path
    for page in manifest["pages"]:
        source = json.loads((output / "sources" / (page["id"] + ".json")).read_bytes())
        assert "tables" not in source
        assert source["model_confidence"] is None
        assert len({w["id"] for w in source["source"]["words"]}) == len(source["source"]["words"])
        assert page["id"] in (output / "gallery.html").read_text()
    with pytest.raises(FileExistsError, match="New versioned"):
        corpus.build(output)
