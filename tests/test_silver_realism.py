"""Check authored semantics, source isolation, and immutable freeze boundaries."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from bench import rolling_robustness, silver_realism
from bench.borderless_challenge import score
from bench.silver import sha

import pdfust


def test_shared_furniture_and_opaque_ids_do_not_encode_admission() -> None:
    title_counts: dict[str, Counter[str]] = {}
    for case in silver_realism.generate_cases():
        target = case["target"]
        assert case["id"].startswith("dev-")
        assert b"/EmbeddedFiles" not in case["pdf"]
        assert b"/ActualText" not in case["pdf"]
        assert b"/Info" not in case["pdf"]
        with pdfust.open(stream=case["pdf"]) as document:
            text = document.get_text()
        assert "Read each" not in text
        assert "table" not in text.lower()
        assert "narrative" not in text.lower()
        title = next(title for title in silver_realism.TITLES if title in text)
        title_counts.setdefault(target["kind"], Counter())[title] += 1
    assert title_counts["borderless"] == Counter(dict.fromkeys(silver_realism.TITLES, 4))
    assert title_counts["prose"] == Counter(dict.fromkeys(silver_realism.TITLES, 2))
    assert title_counts["ambiguous"] == Counter(dict.fromkeys(silver_realism.TITLES, 1))


def test_prose_references_are_complete_sentences_and_fully_visible() -> None:
    for case in silver_realism.generate_cases():
        target = case["target"]
        if target["kind"] != "prose":
            continue
        paragraphs = [paragraph for column in target["authored_columns"] for paragraph in column]
        assert all(paragraph.endswith(".") and len(paragraph.split()) >= 35 for paragraph in paragraphs)
        expected = Counter(word for paragraph in paragraphs for word in paragraph.split())
        with pdfust.open(stream=case["pdf"]) as document:
            words = document[0].get_text("words")
        body = [word for word in words if 115 < word[1] < 710]
        assert Counter(word[4] for word in body) == expected
        assert all(0 <= word[0] < word[2] <= 612 and 0 <= word[1] < word[3] <= 792 for word in words)


def test_total_records_add_visible_counts_and_blanks_remain_blank() -> None:
    for case in silver_realism.generate_cases():
        target = case["target"]
        if target["kind"] != "borderless":
            continue
        values = target["tables"][0]["values"]
        if target["total_row"]:
            assert values[-1][0] == "Total"
            for col in range(1, target["columns"]):
                assert int(values[-1][col]) == sum(int(row[col] or 0) for row in values[1:-1])
        if target["blank_cell"]:
            assert values[1][-1] == ""


def test_freeze_retains_inputs_before_scoring_and_excludes_private_fields(tmp_path: Path) -> None:
    output = silver_realism.freeze(tmp_path / "dev")
    audit = json.loads((output / "freeze-audit.json").read_text())
    sources = json.loads((output / "source-evidence.json").read_text())
    targets = json.loads((output / "private-targets.json").read_text())
    assert audit["scoring_performed"] is False
    assert audit["counts"] == {"borderless": 16, "prose": 8, "ambiguous": 4}
    assert not any(row["outside_page_word_ids"] for row in audit["source_observations"])
    assert sha((output / "source-evidence.json").read_bytes()) == audit["source_sha256"]
    for source, target in zip(sources["pages"], targets, strict=True):
        assert source["id"] == target["id"]
        assert set(source) == {"id", "words", "page_size", "image_path", "vector_candidates", "text_candidates"}
        assert all(set(word) == {"id", "text", "bbox"} for word in source["words"])
    before = (output / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        silver_realism.freeze(tmp_path / "dev")
    assert (output / "manifest.json").read_bytes() == before


def test_ambiguous_cases_never_reach_binary_or_exact_scorer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen = []

    def checked_score(target: dict, observed: list) -> dict:
        assert target["binary_admission_eligible"]
        assert target["kind"] != "ambiguous"
        seen.append(target["id"])
        return score(target, observed)

    monkeypatch.setattr(rolling_robustness, "score", checked_score)
    summary = rolling_robustness.run(tmp_path / "scored-dev")
    assert summary["pages"] == 28
    assert summary["unscored_ambiguous_pages"] == 4
    assert len(set(seen)) == 24
    rows = json.loads((Path(summary["corpus"]) / "private-scores.json").read_text())["rows"]
    ambiguous = [row for row in rows if row["kind"] == "ambiguous"]
    assert len(ambiguous) == 4
    assert all(row["scores"] is None and row["truth_status"] == "ambiguous-unscored" for row in ambiguous)
