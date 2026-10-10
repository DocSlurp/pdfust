"""Complete strict crop candidates may rescue page failures without partial salvage."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_candidate_regions as regions
from bench.silver import sha
from conftest import build_pdf
from test_p003_candidate_run import baseline


def matched(tmp_path: Path) -> tuple[dict, list[dict], list[Path], list[dict]]:
    dirs = [tmp_path / "first", tmp_path / "second"]
    records = []
    pages = []
    configs = []
    data = build_pdf(["Original page"], page_size=(200, 100))
    path = tmp_path / "original.pdf"
    path.write_bytes(data)
    for i, directory in enumerate(dirs):
        baseline(directory, f"text-{i}")
        frozen = json.loads((directory / "frozen.json").read_bytes())
        report = json.loads((directory / "report.json").read_bytes())
        record = {**frozen["records"][0], "pdf_path": str(path), "pdf_sha256": sha(data), "page_number": 0}
        page = deepcopy(report["results"][0])
        page.update(pdf_sha256=sha(data), rotation_normalized=False)
        records.append(record)
        pages.append(page)
        configs.append(frozen["config"])
    return records[0], pages, dirs, configs


def test_failed_page_valid_crop_still_admitted_and_costs_retained(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    pages[1]["status"] = "error"
    pages[1]["error"] = "late page composition failure"
    frozen = regions.freeze_page(record, pages, dirs, configs, seed=7)
    assert frozen["historical_page_failure_gate_blocks"]
    assert frozen["complete_crop_coverage"]
    assert frozen["crops"][0]["valid_baseline_indexes"] == [0, 1]
    assert frozen["generation_provenance"][1]["page"]["calls"] == pages[1]["calls"]
    picked = regions.compose_selection(frozen, {0: 1})
    assert picked["status"] == "ok"
    assert picked["state"]["tables"][0]["values"][1][0] == "text-1"
    assert picked["source_conserved"] is False
    changed = deepcopy(frozen)
    changed["crops"][0]["valid_baseline_indexes"] = [0]
    with pytest.raises(ValueError, match="changed"):
        regions.compose_selection(changed, {0: 0})


def test_invalid_complete_candidate_excluded_and_sole_valid_chosen(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    pages[0]["status"] = "error"
    pages[0]["transcription_regions"][0]["transcription_response"]["choices"][0]["message"]["content"] = (
        "malformed JSON"
    )
    frozen = regions.freeze_page(record, pages, dirs, configs, seed=7)
    item = frozen["crops"][0]
    assert item["status"] == "sole_valid"
    assert item["valid_baseline_indexes"] == [1]
    assert not item["attempts"][0]["valid"]
    assert regions.compose_selection(frozen)["state"]["tables"][0]["values"][1][0] == "text-1"
    pages[1]["transcription_regions"][0]["transcription_response"] = {}
    empty = regions.freeze_page(record, pages, dirs, configs, seed=7)
    assert not empty["complete_crop_coverage"]
    with pytest.raises(ValueError, match="every crop"):
        regions.compose_selection(empty)


def test_request_or_image_mismatch_is_fatal_not_excluded_candidate(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    pages[1]["transcription_regions"][0]["image"]["image_sha256"] = "changed"
    with pytest.raises(ValueError, match="provenance"):
        regions.freeze_page(record, pages, dirs, configs, seed=7)


def test_overlapping_tables_invalidates_entire_candidate(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    crop = pages[0]["transcription_regions"][0]
    response = crop["transcription_response"]
    content = json.loads(response["choices"][0]["message"]["content"])
    content["answers"]["q0"]["tables"] *= 2
    response["choices"][0]["message"]["content"] = json.dumps(content)
    pages[0]["status"] = "error"
    frozen = regions.freeze_page(record, pages, dirs, configs, seed=7)
    assert frozen["crops"][0]["valid_baseline_indexes"] == [1]
    assert "overlapping" in frozen["crops"][0]["attempts"][0]["invalid_reason"]
    assert frozen["crops"][0]["attempts"][0]["crop"]["transcription_response"] == response


def test_complete_page_overlap_rejected_atomically_even_with_valid_crops(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    for page, directory in zip(pages, dirs, strict=True):
        duplicate = deepcopy(page["transcription_regions"][0])
        duplicate.update(index=1, request_index=1)
        page["transcription_regions"].append(duplicate)
        page["layout_detection"]["boxes"].append(deepcopy(duplicate["detector_box"]))
        (directory / "p0-request-1.json").write_bytes((directory / "p0-request-0.json").read_bytes())
    frozen = regions.freeze_page(record, pages, dirs, configs, seed=7)
    assert frozen["complete_crop_coverage"]
    with pytest.raises(ValueError, match="overlap"):
        regions.compose_selection(frozen, {0: 0, 1: 1})
    assert all(c["valid_count"] == 2 for c in frozen["crops"])
