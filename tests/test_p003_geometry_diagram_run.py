"""Pure diagram selection gives no credit to missing or invalid model decisions."""

# ruff: noqa: ANN001, ANN003, ANN201, ANN204, D101, D102, D107
import json
from pathlib import Path

import pytest
from bench import p003_candidate_choice as choice
from bench import p003_geometry_diagram_run as runner
from bench.pipeline_vision_transcription import parse
from bench.silver import write_json


def pool():
    states = []
    for literal in ("whole Alpha", "whole Beta"):
        raw = {
            "answers": {
                "q0": {
                    "tables": [
                        {"bbox": [0, 0, 1000, 1000], "matrix": [["Header", "B"], [literal, "20"]], "mergedspans": []}
                    ]
                }
            }
        }
        states.append(
            parse({"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(raw)}}]}, [0, 0, 100, 100])
        )
    return choice.freeze_pool([0, 0, 100, 100], states, seed=1)


def response(selected="A"):
    return {
        "result": {
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": selected,
                    "probabilities": {k: 0.8 if k == selected else 0.1 for k in ("A", "B", "unresolved")},
                }
            }
        },
        "entry": {"cost": 0.001},
        "replayed": False,
    }


def fixture(tmp_path: Path, count=16):
    frozen_pool = pool()
    pages, selected = [], []
    (tmp_path / "pool" / "sources").mkdir(parents=True)
    for i in range(count):
        ident = f"p{i}"
        source_path = f"sources/{ident}.json"
        write_json(tmp_path / "pool" / source_path, {"page_size": [100, 100], "words": []})
        pages.append({"id": ident, "status": "prepared", "source_path": source_path, "crops": [{"index": 0}]})
        selected.append(
            {
                "index": i,
                "page_id": ident,
                "crop_index": 0,
                "body": {"model": runner.MODELS[0]},
                "pool": frozen_pool,
                "status": "prepared",
            }
        )
    config = runner.configuration(runner.MODELS[0], "filled", 128, 3)
    config["run_id"] = "offline-mock"
    return {"report": {"pages": pages}, "selected": selected}, config


class Client:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def request(self, body, **kwargs):
        self.calls.append((body, kwargs))
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


def execute(prepared, config, tmp_path, responses):
    client = Client(responses)
    report = runner.execute(prepared, tmp_path, config, client_factory=lambda *_: client, entries_reader=lambda *_: [])
    return report, client


def test_all16_exact_bytes_and_scope(tmp_path):
    prepared, config = fixture(tmp_path)
    report, client = execute(prepared, config, tmp_path, [response()] * 16)
    assert report["valid_completed_page_count"] == 16
    assert report["attempted_question_count"] == 16
    assert report["incremental_selection"]["charges"]["effective_usd"] is None
    assert report["full_pipeline_pages_per_minute"] is None
    assert all(call[1]["replay"] is False for call in client.calls)
    for row in report["decisions"]:
        assert row["selected_canonical_json"].encode() == prepared["selected"][0]["pool"].candidates[0].canonical_bytes


def test_abstain_malformed_duplicate_atomic_and_transport_stop(tmp_path):
    prepared, config = fixture(tmp_path, 5)
    prepared["selected"][2].update(body=None, status="not_applicable_duplicates")
    malformed = response()
    malformed["result"]["answers"]["q0"]["probabilities"]["A"] = 0.2
    report, client = execute(
        prepared, config, tmp_path, [response("unresolved"), malformed, RuntimeError("offline"), response()]
    )
    assert [r["status"] for r in report["decisions"]] == [
        "unresolved",
        "malformed_response",
        "not_applicable_duplicates",
        "transport_error",
        "not_attempted",
    ]
    assert len(client.calls) == 3
    assert all(not r["tables"] for r in report["results"])
    assert not report["baseline_credit"]


def test_composition_overlapping_crops_and_failed_original_are_closed():
    candidate = pool().candidates[0].canonical_bytes.decode()
    page = {"crops": [{"index": 0}, {"index": 1}], "page_size": [100, 100]}
    rows = [
        {"status": "selected", "selected_canonical_json": candidate, "crop_index": 0},
        {"status": "selected", "selected_canonical_json": candidate, "crop_index": 1},
    ]
    assert runner.assemble(page, rows)["decision_status"] == "composition_failed"
    assert runner.assemble({"crops": [], "status": "not_applicable_baseline_failure"}, [])["status"] == "error"
    assert runner.assemble({"crops": []}, [])["decision_status"] == "no_detector_crops"


def test_configuration_and_pool_identity():
    for model in runner.MODELS:
        for mode in ("filled", "outline"):
            for edge in (128, 400, 512):
                assert runner.configuration(model, mode, edge, 3)["model"] == model
    with pytest.raises(ValueError, match="capacity"):
        runner.configuration(runner.MODELS[0], "filled", 128, 6)
    record = choice.pool_record(pool())
    assert runner.hydrate(record) == pool()
    record["candidates"][0]["canonical_json"] += " "
    with pytest.raises(ValueError, match="changed"):
        runner.hydrate(record)


def test_display_viewport_is_already_four_coordinates():
    candidate = pool().candidates[0].canonical_bytes.decode()
    page = {"crops": [{"index": 0}], "page_size": [0, 0, 100, 100]}
    result = runner.assemble(page, [{"status": "selected", "selected_canonical_json": candidate, "crop_index": 0}])
    assert result["status"] == "ok"
    assert len(result["state"]["tables"]) == 1


def test_invalid_client_envelope_is_retained_and_next_pair_runs(tmp_path):
    prepared, config = fixture(tmp_path, 2)
    report, client = execute(prepared, config, tmp_path, [None, response()])
    assert [r["status"] for r in report["decisions"]] == ["malformed_response", "selected"]
    assert len(client.calls) == 2


def test_partial_page_retains_only_independent_complete_chosen_crop():
    candidate = pool().candidates[0].canonical_bytes.decode()
    page = {"crops": [{"index": 0}, {"index": 1}], "page_size": [0, 0, 100, 100]}
    rows = [
        {"status": "selected", "selected_canonical_json": candidate, "crop_index": 0},
        {"status": "unresolved", "crop_index": 1},
    ]
    result = runner.assemble(page, rows)
    assert result["status"] == "error"
    assert result["decision_status"] == "selected_partial_crops"
    assert len(result["state"]["tables"]) == 1
    assert result["uncovered_crop_count"] == 1
