"""Authored table references, merged-slot topology and ownership scoring tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.silver import sha, write_json
from bench.silver_structure import LABEL, authored_table, prepare_targets, score_page


def test_authored_merged_grid_slots_and_values() -> None:
    table = authored_table(0)
    assert table["row_count"] == 5
    assert table["col_count"] == 3
    assert table["values"] == [
        ["Regional totals", None, "Year"],
        ["East", "West", "Combined"],
        ["R1C1 10", "R1C2 11", "R1C3 12"],
        ["R2C1 20", "R2C2 21", "R2C3 22"],
        ["R3C1 30", "R3C2 31", "R3C3 32"],
    ]
    assert table["cells"][0] == [40, 112, 365, 147]
    assert table["cells"][1] is None
    assert table["cells"][14] == [365, 252, 550, 287]
    assert table["spans"][0] == {"row": 0, "column": 0, "row_span": 1, "column_span": 2}
    assert len(table["spans"]) == 14
    assert authored_table(3)["values"][4] == ["R3C1 33", "R3C2 34", "R3C3 35"]


def test_exact_scores_and_wrong_value_ownership() -> None:
    table = authored_table(0)
    target = {"tables": [table]}
    perfect = score_page(target, [deepcopy(table)])
    assert perfect["exact_page"]
    assert perfect["correct_cell_slots"] == 15
    assert perfect["correct_owned_values"] == 14
    swapped = deepcopy(table)
    swapped["values"][2][0], swapped["values"][2][1] = swapped["values"][2][1], swapped["values"][2][0]
    score = score_page(target, [swapped])
    assert not score["exact_cells"]
    assert score["exact_spans"]
    assert score["correct_owned_values"] == 12


def test_missing_span_and_duplicate_values_separately_fail() -> None:
    table = authored_table(0)
    target = {"tables": [table]}
    wrong_span = deepcopy(table)
    wrong_span["spans"][0]["column_span"] = 1
    score = score_page(target, [wrong_span])
    assert score["exact_cells"]
    assert not score["exact_spans"]
    duplicates = score_page(target, [deepcopy(table), deepcopy(table)])
    assert duplicates["correct_owned_values"] == 0
    assert duplicates["false_positive_tables"] == 1
    assert not duplicates["exact_page"]


def test_non_table_false_positive_and_missing_detection() -> None:
    no_table = score_page({"tables": []}, [])
    assert no_table["exact_page"]
    false_positive = score_page({"tables": []}, [authored_table(0)])
    assert false_positive["false_positive_page"]
    assert false_positive["false_positive_tables"] == 1
    missing = score_page({"tables": [authored_table(0)]}, [])
    assert missing["correct_cell_slots"] == 0
    assert missing["owned_values"] == 14
    assert not missing["exact_page"]


def minimal_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict[str, Any]]:
    """Mock a complete generated cohort to test input linkage independently of extraction."""
    from bench import silver_layouts, silver_math  # noqa: PLC0415

    source: dict[str, Any] = {
        "id": "layout-merged-table-v4",
        "family": "merged-table",
        "encoding": "StandardEncoding",
        "producer_group": "fixture",
        "page_count": 2,
        "pdf": b"authored source bytes",
    }
    monkeypatch.setattr(silver_layouts, "generate_cases", lambda: [source])
    monkeypatch.setattr(silver_math, "generate_cases", list)
    record = {k: v for k, v in source.items() if k != "pdf"}
    record.update(split="DEV", pdf_sha256=sha(source["pdf"]), pdf_path="pdfs/input.pdf")
    (tmp_path / "pdfs").mkdir()
    (tmp_path / "pdfs/input.pdf").write_bytes(source["pdf"])
    manifest = {"split": "DEV", "dataset_sha256": "fixture", "cases": [record]}
    write_json(tmp_path / "manifest.json", manifest)
    return tmp_path, manifest


def test_prepare_targets_all_pages_and_labels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory, _ = minimal_manifest(tmp_path, monkeypatch)
    targets = prepare_targets(directory)
    assert targets["label_status"] == LABEL
    assert [page["page_number"] for page in targets["pages"]] == [0, 1]
    assert targets["pages"][1]["tables"][0]["values"][2] == ["R1C1 13", "R1C2 14", "R1C3 15"]
    assert "not independently reviewed" in targets["label_status"]


@pytest.mark.parametrize("field", ["family", "page_count", "pdf_sha256"])
def test_prepare_targets_reject_stale_metadata_and_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    directory, manifest = minimal_manifest(tmp_path, monkeypatch)
    manifest["cases"][0][field] = "changed"
    write_json(directory / "manifest.json", manifest)
    with pytest.raises(ValueError, match=r"match|differs"):
        prepare_targets(directory)


def test_image_adapter_keeps_fixed_question_separate_from_gold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bench.silver_image_cases import model_question, silver_image_cases  # noqa: PLC0415

    directory, _ = minimal_manifest(tmp_path, monkeypatch)
    cases = silver_image_cases(directory)
    assert len(cases) == 2
    assert [case["page_index"] for case in cases] == [0, 1]
    assert all(case["expected_document"] == "A" for case in cases)
    question = model_question()
    assert set(question) == {"question", "choices"}
    assert set(question["choices"]) == {"A", "B", "unresolved"}
    assert "merged-table" not in str(question)
    assert "Regional totals" not in str(question)
    assert "checkboxes" in question["question"]
    question["choices"]["A"] = "changed"
    assert model_question()["choices"]["A"] != "changed"


def test_peak_rss_excludes_inherited_launcher_high_water(monkeypatch: pytest.MonkeyPatch) -> None:
    from bench import silver_structure  # noqa: PLC0415

    monkeypatch.setattr(Path, "read_text", lambda _self: "VmHWM:\t16384 kB\nVmRSS:\t12000 kB\n")
    monkeypatch.setattr(silver_structure, "rss_bytes", lambda: 900_000_000)
    peak, tool = silver_structure.process_peak_rss()
    assert peak == 16_777_216
    assert "current executable" in tool
