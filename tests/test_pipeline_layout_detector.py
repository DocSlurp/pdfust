"""CPU worker framing, lifecycle, geometry, and complete source partitions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from bench.pipeline_assembly import native_state
from bench.pipeline_layout_detector import LayoutDetector, detector_regions
from bench.pipeline_regions import compose, unresolved_region


@pytest.fixture
def fake_worker(tmp_path: Path) -> tuple[Path, Path]:
    model = tmp_path / "local.pt"
    model.write_bytes(b"unit test weights")
    script = tmp_path / "worker.py"
    script.write_text("""import json, os, sys
assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
assert os.environ['YOLO_OFFLINE'] == 'true'
print(json.dumps({'type':'ready','device':'cpu','model_sha256':'test','cpu_threads':4}),flush=True)
for line in sys.stdin:
    request=json.loads(line)
    assert set(request)=={'image_base64'}
    print(json.dumps({'type':'result','device':'cpu','model_sha256':'test','image_size':[100,200],
      'boxes':[{'label':'Table','confidence':0.9,'pixel_bbox':[10,20,50,100]}],
      'metrics':{'cpu_seconds':0.01,'peak_sampled_rss_bytes':1000}}),flush=True)
""")
    return model, script


def test_persistent_cpu_worker_maps_global_viewport_and_reaps(fake_worker: tuple[Path, Path]) -> None:
    model, script = fake_worker
    with LayoutDetector(model=model, python=Path(sys.executable), worker_script=script) as detector:
        first = detector.detect(b"inline unit test source pixels", viewport=[20, 40, 220, 440])
        second = detector.detect(b"second frame", viewport=[0, 0, 100, 200])
        assert first["boxes"][0]["normalized_bbox"] == [0.1, 0.1, 0.5, 0.5]
        assert first["boxes"][0]["bbox"] == [40, 80, 120, 240]
        assert second["boxes"][0]["bbox"] == [10, 20, 50, 100]
        assert detector.process.poll() is None
    assert detector.process.poll() is not None
    detector.close()
    with pytest.raises(RuntimeError, match="closed"):
        detector.detect(b"frame", viewport=[0, 0, 1, 1])


def test_worker_timeout_closes_and_reaps(tmp_path: Path) -> None:
    model, script = tmp_path / "local.pt", tmp_path / "blocked.py"
    model.write_bytes(b"weights")
    script.write_text("""import json, sys, time
print(json.dumps({'type':'ready','device':'cpu'}),flush=True)
for line in sys.stdin:
    time.sleep(10)
""")
    detector = LayoutDetector(model=model, python=Path(sys.executable), worker_script=script, request_timeout=0.03)
    with pytest.raises(TimeoutError, match="timed out"):
        detector.detect(b"frame", viewport=[0, 0, 100, 100])
    assert detector.closed
    assert detector.process.poll() is not None


def test_invalid_geometry_and_body_boundaries_reject_before_exchange(fake_worker: tuple[Path, Path]) -> None:
    model, script = fake_worker
    with LayoutDetector(model=model, python=Path(sys.executable), worker_script=script) as detector:
        with pytest.raises(ValueError, match="positive extent"):
            detector.detect(b"frame", viewport=[0, 0, 0, 100])
        with pytest.raises(ValueError, match="frame boundary"):
            detector.detect(b"a" * (8 * 1024 * 1024 + 1), viewport=[0, 0, 100, 100])
        assert detector.process.poll() is None


def snapshot() -> dict[str, Any]:
    return {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "w0", "text": "A", "bbox": [10, 10, 20, 20]},
            {"id": "w1", "text": "B", "bbox": [25, 10, 35, 20]},
            {"id": "w2", "text": "outside", "bbox": [10, 70, 40, 80]},
        ],
        "vector_candidates": [],
    }


def test_overlapping_detector_proposals_assign_every_word_once_and_preserve_residual() -> None:
    page = snapshot()
    detections = [
        {"label": "table", "confidence": 0.8, "bbox": [0, 0, 50, 50]},
        {"label": "Table", "confidence": 0.9, "bbox": [0, 0, 60, 60]},
        {"label": "Title", "confidence": 1.0, "bbox": [0, 60, 100, 100]},
    ]
    plan = detector_regions(page, detections)
    diagnostic = plan["detector_diagnostics"]
    assert diagnostic["overlapping_word_candidates"] == 2
    assert diagnostic["empty_table_proposals"] == 1
    ids = [i for r in plan["regions"] for i in r["source_ids"]]
    assert sorted(ids) == ["w0", "w1", "w2"]
    proposed = next(r for r in plan["regions"] if r["kind"] == "detector_proposal")
    assert proposed["source_ids"] == ["w0", "w1"]
    assert proposed["detector"]["semantic_status"] == "proposal_only"
    states = {r["id"]: unresolved_region(r) for r in plan["regions"]}
    assert compose(plan, states)["unresolved_ids"] == ["w0", "w1", "w2"]


def test_capacity_chunks_explicitly_abstain_on_complete_context() -> None:
    plan = detector_regions(snapshot(), [{"label": "table", "confidence": 0.9, "bbox": [0, 0, 100, 100]}], max_words=1)
    assert len(plan["regions"]) == 3
    assert all(r["boundary"] == "detector_capacity" for r in plan["regions"])
    assert all(not r["context_complete"] for r in plan["regions"])


def test_no_detection_preserves_all_source_and_low_confidence_is_not_a_label() -> None:
    page = snapshot()
    plan = detector_regions(page, [{"label": "table", "confidence": 0.1, "bbox": [0, 0, 100, 100]}])
    assert plan["detector_diagnostics"]["table_proposals"] == 0
    assert sorted(i for r in plan["regions"] for i in r["source_ids"]) == ["w0", "w1", "w2"]


def test_nonfinite_detection_refuses_complete_partition() -> None:
    with pytest.raises(ValueError, match="Nonfinite"):
        detector_regions(snapshot(), [{"label": "table", "confidence": 0.9, "bbox": [0, 0, float("nan"), 100]}])


def test_duplicate_source_ids_refuse_partition() -> None:
    page = snapshot()
    page["words"].append(page["words"][0])
    with pytest.raises(ValueError, match="Duplicate global"):
        detector_regions(page, [])


def test_native_grid_has_priority_over_covering_detector_box() -> None:
    page = snapshot()
    page["vector_candidates"] = [
        {
            "row_count": 2,
            "col_count": 2,
            "cells": [[0, 0, 22, 25], [22, 0, 50, 25], [0, 25, 22, 50], [22, 25, 50, 50]],
            "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)],
        }
    ]
    plan = detector_regions(page, [{"label": "Table", "confidence": 0.99, "bbox": [0, 0, 100, 100]}])
    assert [r["kind"] for r in plan["regions"]] == ["native", "detector_proposal"]
    assert plan["regions"][0]["source_ids"] == ["w0", "w1"]
    assert plan["regions"][1]["source_ids"] == ["w2"]
    states = {
        r["id"]: native_state(r["source"]) if r["kind"] == "native" else unresolved_region(r) for r in plan["regions"]
    }
    assert compose(plan, states)["unresolved_ids"] == ["w2"]
