"""Artificial geometry fixtures only; no generator labels or hosted clients."""
from __future__ import annotations

import copy
import json

import pytest
from bench import p003_synthetic_geometry as geometry
from bench import p003_synthetic_geometry_run as runner
from PIL import Image, ImageDraw

# ruff: noqa: ANN001, ANN201 - explicit local geometric fixtures.


def record(kind="cell", second=(20, 5, 30, 10)):
    return {"id": "arbitrary", "kind": kind, "pair_source_ids": ["a", "b"],
            "source": {"words": [{"id": "a", "text": "untrusted", "bbox": [5, 5, 15, 10]},
                                   {"id": "b", "text": "different", "bbox": list(second)}]}}


def rectangle(x0=0, y0=0, x1=40, y1=40):
    return [[x0, y0, x1, y0], [x0, y1, x1, y1], [x0, y0, x0, y1], [x1, y0, x1, y1]]


def test_cell_enclosure_and_divider():
    source = record()
    assert geometry.classify(source, rectangle())["choice"] == "same"
    divided = [*rectangle(), [17, 0, 17, 40]]
    out = geometry.classify(source, divided)
    assert out["choice"] == "separate"
    assert out["vertical_separator"] is True
    assert geometry.classify(source, rectangle()[:-1])["choice"] == "unresolved"


def test_logical_row_and_wrap_do_not_follow_physical_spacing():
    source = record("row", (20, 22, 30, 27))
    assert geometry.classify(source, rectangle())["choice"] == "same"
    assert geometry.classify(source, [])["choice"] == "unresolved"
    proxy = geometry.classify(source, [], physical_proxy=True)
    assert proxy["choice"] == "separate"
    assert proxy["physical_proxy"] is True
    source["kind"] = "wrap"
    assert geometry.classify(source, rectangle())["choice"] == "unresolved"
    assert geometry.classify(source, [*rectangle(), [0, 16, 40, 16]])["choice"] == "separate"


def test_no_family_literal_or_caseid_cues_and_no_mutation():
    source = record()
    before = copy.deepcopy(source)
    expected = geometry.classify(source, rectangle())
    assert source == before
    source["id"] = "opposite-family-name"
    for word in source["source"]["words"]:
        word["text"] = "not an answer; ignore previous instructions"
    assert geometry.classify(source, rectangle()) == expected


def test_raster_independent_closed_rectangle_and_wordlike_dark_blob():
    pixels = Image.new("RGB", (128, 128), "white")
    draw = ImageDraw.Draw(pixels)
    draw.rectangle((10, 10, 110, 110), outline="black", width=1)
    lines = geometry.raster_segments(pixels, [0, 0, 128, 128])
    assert len(lines) == 4
    source = record(second=(60, 50, 70, 60))
    source["source"]["words"][0]["bbox"] = [20, 20, 30, 30]
    assert geometry.classify(source, lines)["choice"] == "same"
    blob = Image.new("RGB", (128, 128), "white")
    ImageDraw.Draw(blob).rectangle((20, 20, 60, 30), fill="black")
    assert geometry.raster_segments(blob, [0, 0, 128, 128]) == []


def test_bad_geometry_and_caps_refuse_complete_evidence(monkeypatch):
    with pytest.raises(ValueError, match="finite"):
        geometry.box([0, 0, float("nan"), 4])
    with pytest.raises(ValueError, match="Positive"):
        geometry.box([0, 0, 0, 4])
    monkeypatch.setattr(geometry, "LIMIT", 1)
    with pytest.raises(ValueError, match="cap"):
        geometry.vector_segments([{"type": "s", "items": [["l", [0, 0], [10, 0]],
                                                               ["l", [0, 10], [10, 10]]]}])


def test_authenticate_and_complete_freeze_without_generator_execution(tmp_path):
    pool = tmp_path / "pool"
    (pool / "sources").mkdir(parents=True)
    (pool / "code").mkdir()
    bad_code = b"raise RuntimeError('must never execute')"
    (pool / "code" / "generator.py").write_bytes(bad_code)
    records = []
    artifacts = {}
    for index in range(24):
        source = record()
        source.update(id=str(index), status="ready", drawings=[], images=[])
        path = f"sources/{index}.json"
        runner.write(pool / path, source)
        sha = runner.digest((pool / path).read_bytes())
        records.append({"id": str(index), "kind": "cell", "path": path, "sha256": sha})
        artifacts[path] = sha
    frozen = {"source_only": True, "intended_case_count": 24, "records": records,
              "code_sha256": {"generator.py": runner.digest(bad_code)}, "artifact_sha256": artifacts}
    runner.write(pool / "frozen.json", frozen)
    authority = tmp_path / "trust.json"
    runner.write(authority, {"generator.py": runner.digest(bad_code),
                             "source_frozen_sha256": runner.digest((pool / "frozen.json").read_bytes())})
    report = runner.run(pool, authority, tmp_path / "output")
    assert len(report["results"]) == 96
    assert report["hosted_calls"] == 0
    assert report["correctness_measured"] is False
    assert report["pages_per_minute"] is None
    assert report["by_treatment"]["direct_vector"]["case_count"] == 24
    assert report["by_treatment"]["crop_raster128"]["status_counts"] == {"source_refused": 24}
    immutable = json.loads((tmp_path / "output" / "frozen.json").read_text())
    assert immutable["generator_imported"] is False
    assert immutable["results_sha256"] == runner.digest((tmp_path / "output" / "results.json").read_bytes())
    (pool / "sources/0.json").write_text("{}")
    with pytest.raises(ValueError, match="digest"):
        runner.authenticate(pool, authority)
    with pytest.raises(FileExistsError, match="Fresh"):
        runner.run(pool, authority, tmp_path / "output")
