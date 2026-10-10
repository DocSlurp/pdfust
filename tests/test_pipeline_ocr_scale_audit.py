"""CPU construction tests; no OCR model inference required."""

import json
from pathlib import Path

import pytest
from bench.pipeline_ocr_scale_audit import compare_geometry, digest, dpi_for, freeze, normalize, run, sources

import pylopdf


def test_arm_scale_invariance() -> None:
    for scale in (0.5, 1, 2):
        box = [0, 0, 600 * scale, 800 * scale]
        assert dpi_for("dpi150", box) == 150
        assert max(box) * dpi_for("edge2048", box) / 72 == 2048
        assert normalize([60 * scale, 80 * scale, 300 * scale, 400 * scale], box) == [0.1, 0.1, 0.5, 0.5]
    with pytest.raises(ValueError, match="Unknown frozen arm"):
        dpi_for("unknown", [0, 0, 600, 800])


def test_source_construction_retains_same_target_and_rotates_geometry() -> None:
    upright, rotated, negative = sources()
    assert upright["target"] == rotated["target"]
    assert len(upright["cells"]) == 84
    assert negative["target"] == ""
    assert negative["cells"] == []
    assert rotated["image"].size == (1600, 1200)
    assert rotated["rotation"] == 270
    box = upright["cells"][0]["pixel_bbox"]
    assert rotated["cells"][0]["pixel_bbox"] == [1600 - box[3], box[0], 1600 - box[1], box[2]]


def test_freeze_sources_and_pdfs(tmp_path: Path) -> None:
    plan = freeze(tmp_path)
    assert len(plan["cases"]) == 3
    assert json.loads((tmp_path / "plan.json").read_text()) == plan
    for case in plan["cases"]:
        assert digest((tmp_path / f"{case['id']}.png").read_bytes()) == case["source_png_sha256"]
        assert [p["scale"] for p in case["pdfs"]] == [0.5, 1, 2]


def test_geometry_abstains_when_text_sequence_changes() -> None:
    rows = [
        {"case": "a", "arm": "edge2048", "scale": s, "words": [{"text": t, "normalized_bbox": [0, 0, 0.5, 0.5]}]}
        for s, t in [(1, "hello"), (0.5, "hello"), (2, "world")]
    ]
    compare_geometry(rows)
    assert rows[1]["max_normalized_box_delta_vs_scale1"] == 0
    assert rows[2]["max_normalized_box_delta_vs_scale1"] is None


def test_run_retains_native_mapping_results_and_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    freeze(tmp_path)
    monkeypatch.setattr(pylopdf, "OcrEngine", lambda **_kwargs: object())
    calls = []

    def mocked_ocr(self: pylopdf.Page, **kwargs: object) -> list[pylopdf.OcrWord]:
        calls.append(kwargs)
        if len(calls) == 1:
            msg = "mock recognition failure"
            raise RuntimeError(msg)
        return [{"text": "ITEM", "bbox": (0, 0, self.rect[2] / 2, self.rect[3] / 2), "confidence": 0.9}]

    monkeypatch.setattr(pylopdf.Page, "get_text_ocr", mocked_ocr)
    result = run(tmp_path)
    assert len(calls) == 18
    assert result["rows"][0]["status"] == "error"
    assert result["rows"][0]["same_text_sequence_as_scale1"] is False
    assert result["rows"][1]["words"][0]["normalized_bbox"] == [0, 0, 0.5, 0.5]
    assert all(c["engine"] is calls[0]["engine"] for c in calls)
    assert all(c["tile_size"] == 1408 for c in calls)
    assert (tmp_path / "report.json").is_file()
