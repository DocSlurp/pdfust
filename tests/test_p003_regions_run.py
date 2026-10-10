"""Offline staged integration, semantic abstention and page-atomic crop output."""

# Fake native and metered transport records use the real experimental protocols.
# ruff: noqa: ANN401
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_run as native
from bench import generalization_vision_run as vision
from bench import p003_region_candidates as candidates
from bench import p003_regions_run as run
from bench import pipeline_run as baseline
from bench.silver import sha

import pylopdf


def raw(matrix: list[list[str]] | None = None, bbox: list[float] | None = None) -> dict[str, Any]:
    tables = [] if matrix is None else [{"bbox": bbox or [0, 0, 1000, 1000], "matrix": matrix, "mergedspans": []}]
    return {
        "choices": [
            {"finish_reason": "stop", "message": {"content": json.dumps({"answers": {"q0": {"tables": tables}}})}}
        ]
    }


def proposal(index: int, box: list[float]) -> dict[str, Any]:
    return {
        "id": f"r{index:03d}",
        "bbox": box,
        "mechanisms": ["ocr_aligned_tracks"],
        "evidence_records": [{"physical_rows": 4}],
        "warnings": ["Physical completeness unknown"],
        "capacity_window": True,
        "packet": {
            "words": [],
            "source_context_complete": False,
            "omitted_source_words": 8,
            "source_text_available": False,
        },
        "page_viewport": [0, 0, 600, 800],
    }


def accepted(index: int, box: list[float], probability: float | None) -> dict[str, Any]:
    value = proposal(index, box)
    value["gate_answer"] = {"choice": "table"}
    if probability is not None:
        value["gate_answer"]["probabilities"] = {"table": probability, "prose": 1 - probability, "unresolved": 0}
    return value


def test_declared_small_area_policy_changes_conflict_order_without_geometry_changes() -> None:
    values = [accepted(0, [10, 10, 200, 200], 0.99), accepted(1, [20, 20, 80, 80], 0.6)]
    assert run.select_nonoverlapping(values)["selected_ids"] == ["r000"]
    result = run.select_nonoverlapping(values, policy=run.SMALL_AREA_POLICY)
    assert result["selected_ids"] == ["r001"]
    assert result["conflicts"][0]["conflicts_with"] == ["r001"]
    assert values[0]["bbox"] == [10, 10, 200, 200]
    with pytest.raises(ValueError, match="Unknown overlap"):
        run.select_nonoverlapping(values, policy="undeclared")


def record(tmp_path: Path, *, rotation: int = 0) -> dict[str, Any]:
    with pylopdf.Document() as document:
        page = document.new_page(width=600, height=800)
        page.set_rotation(rotation)
        data = document.tobytes()
    path = tmp_path / "source.pdf"
    path.write_bytes(data)
    return {"id": "fixture", "pdf_path": str(path), "pdf_sha256": sha(data), "page_number": 0}


def configuration(**kwargs: Any) -> dict[str, Any]:
    return {"campaign": "P003", "run_id": "test", "model": "perplexity/pplx-decider-v1.1-27b", **kwargs}


def setup(
    monkeypatch: pytest.MonkeyPatch,
    *,
    boxes: list[list[float]] | None = None,
    answers: list[str] | None = None,
    responses: list[dict[str, Any]] | None = None,
    rotation: int = 0,
) -> dict[str, Any]:
    boxes = boxes if boxes is not None else [[10, 20, 100, 150], [200, 20, 400, 150]]
    state: dict[str, Any] = {"gate_requests": [], "transcriptions": [], "child_configs": []}
    size = [800, 600] if rotation in (90, 270) else [600, 800]

    def child(_record: dict[str, Any], config: dict[str, Any], _output: Path, client: Any) -> dict[str, Any]:
        assert client is None
        state["child_configs"].append(config)
        return {
            "id": "fixture",
            "status": "ok",
            "calls": [],
            "original_rotation": rotation,
            "source": {"page_size": size, "words": [{"id": "w0", "text": "literal", "bbox": [20, 30, 50, 40]}]},
        }

    def proposals(_source: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        state["proposal_settings"] = kwargs
        return {
            "candidates": [proposal(i, box) for i, box in enumerate(boxes)],
            "diagnostics": {"omitted_candidates": 3},
        }

    def call(_client: Any, body: dict[str, Any], tag: str) -> dict[str, Any]:
        index = len(state["gate_requests"])
        state["gate_requests"].append({"body": body, "tag": tag})
        choice = answers[index] if answers is not None else "table"
        return {
            "answer": {"choice": choice},
            "entry": {"index": index, "tag": tag, "accounted_usd": 0.001},
            "usage": {"input_tokens": 10},
            "replayed": False,
        }

    def transcribe(
        _client: Any,
        body: dict[str, Any],
        config: dict[str, Any],
        result: dict[str, Any],
        _output: Path,
        *,
        request_index: int,
    ) -> dict[str, Any]:
        assert config["campaign"] == "P003"
        state["transcriptions"].append(body)
        value = responses[request_index] if responses is not None else raw([[f"literal-{request_index}"]])
        result["calls"].append({"kind": "vision_transcription", "entry": {"accounted_usd": 0.002}, "usage": {}})
        result["transcription_response"] = value
        result["request"] = {"request_index": request_index}
        return value

    monkeypatch.setattr(native, "process", child)
    monkeypatch.setattr(candidates, "propose", proposals)
    monkeypatch.setattr(baseline, "call", call)
    monkeypatch.setattr(vision, "_transcribe", transcribe)
    monkeypatch.setattr(vision, "_ledger", lambda _client: [])
    return state


def test_gate_packet_preserves_partial_context_and_declared_image_contract() -> None:
    candidate = proposal(0, [10, 20, 100, 150])
    request = run.gate_request("liquid/d1", candidate, "data:image/jpeg;base64,AA==")
    assert request["questions"]["q0"]["criteria"] == run.GATE_CHOICES
    assert "does not assert complete bounds" in request["questions"]["q0"]["instructions"]
    data = json.loads(request["state"][0])
    assert data["proposed_region"]["packet"]["omitted_source_words"] == 8
    assert not data["proposed_region"]["packet"]["source_context_complete"]
    assert request["state"][1]["type"] == "image_url"
    text = run.gate_request("typesafe/jev-1.13", candidate, None)
    assert isinstance(text["state"], str)


def test_disjoint_acceptance_retains_calls_and_exact_global_bounds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = setup(monkeypatch)
    result = run.process(record(tmp_path), configuration(region_proposal_arm="tracks_fixed2"), tmp_path, object())
    assert result["status"] == "ok"
    assert result["source_conserved"] is False
    assert result["output_scope"] == "table_only"
    assert result["text_provenance"] == "model-transcribed"
    assert [table["bbox"] for table in result["tables"]] == [[10, 20, 100, 150], [200, 20, 400, 150]]
    assert len(result["calls"]) == 4
    assert all(request["tag"].startswith("P003/test/fixture/gate/") for request in state["gate_requests"])
    assert state["proposal_settings"]["raster_grid"] == 2
    child = state["child_configs"][0]
    assert child["policy"] == "native"
    assert child["layout_detector"] == "none"
    assert child["ocr_dpi"] == 300
    assert child["ocr_source"] == "whitespace"
    assert child["rotation_mode"] == "preserve"
    assert not child["normalize_rotation"]
    assert result["proposal_plan"]["diagnostics"]["omitted_candidates"] == 3
    assert (tmp_path / "fixture.md").exists()
    assert (tmp_path / "fixture-gate-request-r000.json").exists()


def test_prose_and_abstention_never_transcribe_or_become_source_conservation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = setup(monkeypatch, answers=["prose", "unresolved"])
    result = run.process(record(tmp_path), configuration(gate_image=False), tmp_path, object())
    assert result["status"] == "ok"
    assert result["tables"] == []
    assert len(result["calls"]) == 2
    assert state["transcriptions"] == []
    assert result["conflict_selection"]["abstained_ids"] == ["r001"]
    assert result["coverage"] == "unverified"
    assert not result["source_conserved"]
    assert all(isinstance(r["body"]["state"], str) for r in state["gate_requests"])


def test_overlap_probability_selection_preserves_every_conflict() -> None:
    proposals = [
        accepted(0, [10, 20, 200, 150], 0.6),
        accepted(1, [50, 20, 250, 150], 0.8),
        accepted(2, [250, 20, 400, 150], None),
    ]
    plan = run.select_nonoverlapping(proposals)
    assert plan["selected_ids"] == ["r001", "r002"]
    assert plan["conflicts"] == [
        {"id": "r000", "conflicts_with": ["r001"], "table_probability": 0.6, "disposition": "not_transcribed_overlap"}
    ]
    assert "None" not in json.dumps(plan)


def test_missing_probabilities_use_proposal_order_without_fabricated_confidence() -> None:
    proposals = [accepted(0, [10, 20, 200, 150], None), accepted(1, [50, 20, 250, 150], None)]
    plan = run.select_nonoverlapping(proposals)
    assert plan["selected_ids"] == ["r000"]
    assert plan["conflicts"][0]["table_probability"] is None


@pytest.mark.parametrize("problem", ["bbox", "matrix", "length"])
def test_transcription_failure_rejects_atomic_page_and_retains_paid_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    broken = raw([["B"]])
    if problem == "bbox":
        broken = raw([["B"]], [-1, 0, 1000, 1000])
    elif problem == "matrix":
        broken = raw([["B"], ["C", "D"]])
    else:
        broken["choices"][0]["finish_reason"] = "length"
    setup(monkeypatch, responses=[raw([["A"]]), broken])
    result = run.process(record(tmp_path), configuration(), tmp_path, object())
    assert result["status"] == "error"
    assert result["tables"] == []
    assert len(result["calls"]) == 4
    assert result["transcription_regions"][0]["status"] == "ok"
    assert result["transcription_regions"][1]["status"] == "error"
    assert result["transcription_regions"][1]["transcription_response"] == broken
    assert not (tmp_path / "fixture.md").exists()
    assert not (tmp_path / "fixture-structure.json").exists()


def test_native_failure_propagates_without_empty_success_or_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = setup(monkeypatch)
    monkeypatch.setattr(
        native, "process", lambda *_args: {"status": "unsupported_no_text", "calls": [], "error": "No source"}
    )
    result = run.process(record(tmp_path), configuration(), tmp_path, object())
    assert result["status"] == "unsupported_no_text"
    assert result["error_stage"] == "native_source"
    assert result["native_child"]["error"] == "No source"
    assert result["calls"] == []
    assert state["gate_requests"] == []


def test_gate_failure_preserves_ledger_charge_and_stops_before_transcription(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = setup(monkeypatch)
    entries: list[dict[str, Any]] = []
    monkeypatch.setattr(vision, "_ledger", lambda _client: entries)

    def fail(_client: Any, _body: dict[str, Any], tag: str) -> dict[str, Any]:
        entries.append({"index": 1, "tag": tag, "accounted_usd": 0.3, "error": "HTTP 500"})
        msg = "Transport failed"
        raise RuntimeError(msg)

    monkeypatch.setattr(baseline, "call", fail)
    result = run.process(record(tmp_path), configuration(), tmp_path, object())
    assert result["status"] == "error"
    assert len(result["calls"]) == 1
    assert result["calls"][0]["entry"]["accounted_usd"] == 0.3
    assert result["gate_regions"][0]["gate_status"] == "error"
    assert state["transcriptions"] == []


def test_rotation_is_preserved_between_native_source_and_raster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup(monkeypatch, rotation=90, boxes=[], answers=[])
    result = run.process(record(tmp_path, rotation=90), configuration(), tmp_path, object())
    assert result["status"] == "ok"
    assert result["original_rotation"] == 90
    assert not result["rotation_normalized"]
    assert result["viewport"] == [0, 0, 800, 600]


@pytest.mark.parametrize(
    "setting",
    [{"campaign": "P002"}, {"gate_enabled": False}, {"candidate_cap": 33}, {"workers": 4}, {"image_edge": 512}],
)
def test_configuration_refuses_before_source_or_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, setting: dict[str, Any]
) -> None:
    state = setup(monkeypatch)
    result = run.process(record(tmp_path), configuration(**setting), tmp_path, object())
    assert result["status"] == "error"
    assert result["error_stage"] == "configuration"
    assert state["child_configs"] == []
    assert result["calls"] == []


def test_ordinary_yolo_control_bypasses_gate_in_separate_arm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = setup(monkeypatch)

    class Detector:
        def detect(self, _pixels: bytes, *, viewport: list[float]) -> dict[str, Any]:
            return {
                "type": "result",
                "device": "cpu",
                "viewport": viewport,
                "boxes": [{"label": "Table", "confidence": 0.9, "bbox": [10, 20, 100, 150]}],
            }

    result = run.process(
        record(tmp_path),
        configuration(region_proposal_arm="yolo", gate_enabled=False, _layout_detector=Detector()),
        tmp_path,
        object(),
    )
    assert result["status"] == "ok"
    assert len(result["tables"]) == 1
    assert result["proposal_arm"] == "yolo"
    assert result["gate_model"] is None
    assert result["gate_regions"][0]["gate_status"] == "bypassed_ordinary_yolo"
    assert state["gate_requests"] == []
    assert len(state["transcriptions"]) == 1


def test_union_runtime_keeps_source_inventory_and_gates_every_retained_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = setup(monkeypatch)

    class Detector:
        def detect(self, _pixels: bytes, *, viewport: list[float]) -> dict[str, Any]:
            return {
                "type": "result",
                "device": "cpu",
                "viewport": viewport,
                "boxes": [{"label": "Table", "confidence": 0.9, "bbox": [10, 20, 100, 150]}],
            }

    result = run.process(
        record(tmp_path),
        configuration(
            region_proposal_arm="yolo_fixed2", _layout_detector=Detector(), conflict_policy=run.SMALL_AREA_POLICY
        ),
        tmp_path,
        object(),
    )
    assert result["status"] == "ok"
    plan = result["proposal_plan"]
    assert plan["diagnostics"]["raw_candidates"] == 3
    assert plan["diagnostics"]["retained_candidates"] == 2
    assert set(plan["input_plans"]) == {"yolo", "tracks_fixed2"}
    assert state["proposal_settings"]["raster_grid"] == 2
    assert len(state["gate_requests"]) == 2
    assert len(state["transcriptions"]) == 2
    assert result["conflict_selection"]["policy"] == run.SMALL_AREA_POLICY
    assert len(plan["candidates"][0]["union_provenance"]) == 2


def test_real_native_source_child_and_proposal_acquisition_without_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pylopdf.Document() as document:
        page = document.new_page(width=400, height=500)
        for row in range(4):
            for column in range(3):
                page.insert_text((20 + column * 110, 40 + row * 30), f"R{row}C{column}", fontsize=12)
        data = document.tobytes()
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(data)
    item = {"id": "fixture", "pdf_path": str(pdf), "pdf_sha256": sha(data), "page_number": 0}
    tags: list[str] = []

    def call(_client: Any, _body: dict[str, Any], tag: str) -> dict[str, Any]:
        tags.append(tag)
        return {"answer": {"choice": "unresolved"}, "entry": {"tag": tag}, "usage": {}, "replayed": False}

    monkeypatch.setattr(baseline, "call", call)
    monkeypatch.setattr(vision, "_ledger", lambda _client: [])
    result = run.process(item, configuration(gate_image=False), tmp_path, object())
    assert result["status"] == "ok"
    assert result["native_child"]["status"] == "ok"
    assert len(result["source"]["words"]) == 12
    assert result["proposal_count"] > 0
    assert len(tags) == result["proposal_count"]
    assert result["transcription_regions"] == []
    assert all("gate_answer" not in c for c in result["proposal_plan"]["candidates"])
    assert (tmp_path / "native/fixture-result.json").exists()
