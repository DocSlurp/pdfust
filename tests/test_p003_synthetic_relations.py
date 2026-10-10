"""Generator membership, literal conservation and separated synthetic evidence."""

from __future__ import annotations

import io
import json
from collections import Counter
from pathlib import Path

import pytest
from bench import p003_synthetic_relations as cases
from bench import p003_synthetic_relations_prepare as preparation
from bench.silver import sha
from PIL import Image


def test_balanced_designs_unique_unlabeled_literals_and_membership() -> None:
    plans = cases.plans()
    assert len(plans) == 24
    assert len({p["id"] for p in plans}) == 24
    assert Counter((p["kind"], p["same"]) for p in plans) == Counter(
        {(k, b): 4 for k in cases.KINDS for b in (True, False)}
    )
    hashes = set()
    for plan in plans:
        data, gold = cases.authored(plan)
        assert data == cases.authored(plan)[0]
        hashes.add(sha(data))
        a, b = gold["memberships"]
        equal = a["table"] == b["table"] and a["row"] == b["row"]
        if plan["kind"] != "row":
            equal = equal and a["cell"] == b["cell"]
        assert equal == plan["same"]
        assert all(len(t) == 7 and t.isalpha() and t.islower() for t in plan["literals"])
    assert len(hashes) == 24


def test_actual_extraction_identity_and_full_evidence_no_gold() -> None:
    for plan in cases.plans():
        pdf, gold = cases.authored(plan)
        source, pair, drawings = cases.extract(pdf, plan["literals"])
        words = {w["id"]: w for w in source["words"]}
        assert [words[i]["text"] for i in pair] == gold["pair_literals"]
        assert len(words) == 8
        record = {
            "status": "ready",
            "kind": plan["kind"],
            "source": source,
            "pair_source_ids": pair,
            "drawings": drawings,
        }
        for mode in cases.MODES:
            body = cases.request(record, "explicit/model", mode=mode)
            packet = json.loads(body["state"])
            assert packet["source"] == source
            assert packet["omitted_word_count"] == 0
            assert packet["word_count"] == 8
            assert "expected_choice" not in body["state"]
            assert "memberships" not in body["state"]
            assert "family" not in body["state"]
            assert set(body["questions"]["q0"]["criteria"]) == {"same", "separate", "unresolved"}
            assert ("observed_drawings" in packet) == (mode == "rows_rules")


def test_duplicate_or_missing_extraction_refuses() -> None:
    plan = cases.plans()[0]
    pdf, _ = cases.authored(plan)
    duplicate = plan["literals"].copy()
    duplicate[1] = duplicate[0]
    with pytest.raises(ValueError, match="ambiguous"):
        cases.extract(pdf, duplicate)
    with pytest.raises(ValueError, match="unmatched"):
        cases.extract(pdf, plan["literals"][:-1])


def test_actual_pixels_explicit_page_and_crop_provenance() -> None:
    pdf, _ = cases.authored(cases.plans()[0])
    for bounds in (None, [55, 80, 470, 320]):
        for edge in cases.EDGES:
            first = cases.image(pdf, edge=edge, viewport=bounds)
            assert first == cases.image(pdf, edge=edge, viewport=bounds)
            with Image.open(io.BytesIO(first)) as image:
                assert image.mode == "RGB"
                assert max(image.size) <= edge + 1
    with pytest.raises(ValueError, match="Predeclared"):
        cases.image(pdf, edge=256)


def test_complete_pool_freezes_before_gold_and_refuses_reuse(tmp_path: Path) -> None:
    output = tmp_path / "micro"
    report = preparation.prepare(output)
    frozen = json.loads((output / "frozen.json").read_bytes())
    gold = json.loads((output / "private-gold.json").read_bytes())
    assert report["statuses"] == {"ready": 24}
    assert report["deliberately_underdetermined_cases"] == 6
    assert len(gold["cases"]) == len(frozen["records"]) == 24
    assert "private-gold.json" not in frozen["artifact_sha256"]
    assert gold["source_frozen_sha256"] == sha((output / "frozen.json").read_bytes())
    assert report["hosted_calls"] == 0
    for name, digest in frozen["artifact_sha256"].items():
        assert sha((output / name).read_bytes()) == digest
    assert len(list((output / "images").iterdir())) == 96
    assert len(list((output / "packets").iterdir())) == 96
    with pytest.raises(FileExistsError, match="new directory"):
        preparation.prepare(output)
