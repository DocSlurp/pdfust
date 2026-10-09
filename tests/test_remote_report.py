"""CPU fixtures verify root-only references, exact evidence, and honest rates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from bench.remote_report import evaluate, markdown


def write(path: Path, value: Any) -> str:  # noqa: ANN401
    """Write a unit fixture and return its exact artifact digest."""
    payload = value if isinstance(value, bytes) else json.dumps(value).encode()
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


@pytest.fixture
def fixture(tmp_path: Path) -> dict[str, Any]:
    """Freeze source records first, then separately create test-only references."""
    source = tmp_path / "source"
    packets = tmp_path / "packets"
    output = tmp_path / "output"
    for directory in (source, packets, output):
        directory.mkdir()
    pages, records, index, staged = [], [], [], []
    events: list[dict[str, Any]] = []
    for number in range(24):
        source_id = f"source-{number}"
        record_id = f"p{number:04}"
        observation = {
            "target_atoms": [[{"id": "a", "text": "literal"}], [{"id": "b", "text": "source"}]],
            "all_target_ids": ["a", "b"],
            "candidates": {"join": [["a", "b"]], "split": [["a"], ["b"]], "unresolved": []},
        }
        pdf_name, observation_name = source_id + ".pdf", source_id + ".json"
        pages.append(
            {
                "id": source_id,
                "source_file": pdf_name,
                "source_sha256": write(source / pdf_name, ("unit source " + source_id).encode()),
                "observation_file": observation_name,
                "observation_sha256": write(source / observation_name, observation),
            }
        )
        request_name, image_name = record_id + ".json", record_id + ".png"
        request = {"model": "transport-model", "state": "literal source", "questions": {"q0": {"type": "choice"}}}
        request_sha = write(source / request_name, request)
        image_sha = write(source / image_name, ("unit crop " + source_id).encode())
        (packets / request_name).write_bytes((source / request_name).read_bytes())
        (packets / image_name).write_bytes((source / image_name).read_bytes())
        row = {
            "request": request_name,
            "sha256": request_sha,
            "model": "transport-model",
            "arm": "fresh-rgb-512",
            "page_ids": [source_id],
            "image_file": image_name,
            "image_sha256": image_sha,
        }
        records.append(row)
        index.append(dict(row, id=record_id))
        staged.append({"id": record_id, "request_file": request_name, "image_files": [image_name]})
        events.append({"id": record_id, "event": "attempt_started"})
        events.append(
            {
                "id": record_id,
                "event": "attempt_completed",
                "status": "ok",
                "request_sha256": request_sha,
                "inference_wall_seconds": 2,
                "peak_rss_bytes": 1024,
                "response": {"backend": "stock-vllm-json", "answers": {"q0": {"type": "choice", "choice": "join"}}},
            }
        )
    index_path = tmp_path / "source-index.json"
    write(index_path, index)
    packets_path = packets / "manifest.json"
    write(packets_path, {"records": staged})
    # Source generation is complete; reference distinctions never affect source content.
    targets = [
        {"id": page["id"], "expected": "join" if number < 16 else "unresolved"} for number, page in enumerate(pages)
    ]
    target_sha = write(source / "private-targets.json", targets)
    write(
        source / "manifest.json",
        {"experiment": "L015", "pages": pages, "records": records, "targets_sha256": target_sha},
    )
    (output / "attempts.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events))
    write(output / "status.json", {"status": "complete", "initialization": {"wall_seconds": 10}})
    return {
        "source_dir": source,
        "source_index": index_path,
        "worker_output": output,
        "packets": packets_path,
        "model": "unit-model",
    }


def test_choice_only_scoring_and_measured_rates(fixture: dict[str, Any]) -> None:
    result = evaluate(**fixture)
    row = result["groups"][0]
    assert row["known_correct"] == row["known_denominator"] == 16
    assert row["ambiguous_abstentions"] == 0
    assert row["ambiguous_denominator"] == 8
    assert row["completed_regions"] == 24
    assert row["regions_per_inference_minute"] == 30
    assert row["regions_per_allocated_usd"] is None
    assert result["results"][0]["parsed"]["probabilities"] is None
    assert result["full_page_pages_per_minute"] is None
    assert "16/16" in markdown(result)


def test_native_distribution_ties_use_shared_parser(fixture: dict[str, Any]) -> None:
    path = fixture["worker_output"] / "attempts.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    for event in events:
        if event["event"] == "attempt_completed":
            event["response"] = {
                "answers": {
                    "q0": {
                        "type": "choice",
                        "choice": "join",
                        "probabilities": {"join": 0.5, "split": 0.5, "unresolved": 0.0},
                    }
                }
            }
    path.write_text("".join(json.dumps(event) + "\n" for event in events))
    result = evaluate(**fixture)
    assert result["groups"][0]["known_correct"] == 0
    assert result["groups"][0]["ambiguous_abstentions"] == 8
    assert result["results"][0]["parsed"]["tie_abstention"] is True


def test_source_verification_precedes_reference_access(fixture: dict[str, Any]) -> None:
    (fixture["source_dir"] / "p0000.png").write_bytes(b"changed")
    (fixture["source_dir"] / "private-targets.json").unlink()
    with pytest.raises(ValueError, match="artifact hash differs"):
        evaluate(**fixture)


def test_declared_transport_override_only(fixture: dict[str, Any]) -> None:
    packet = fixture["packets"].parent / "p0000.json"
    body = json.loads(packet.read_text())
    body["model"] = "strict-model"
    digest = write(packet, body)
    log = fixture["worker_output"] / "attempts.jsonl"
    events = [json.loads(line) for line in log.read_text().splitlines()]
    events[1]["request_sha256"] = digest
    log.write_text("".join(json.dumps(event) + "\n" for event in events))
    with pytest.raises(ValueError, match="transport override"):
        evaluate(**fixture)
    assert evaluate(**fixture, transport_model="strict-model")["groups"][0]["completed_regions"] == 24
    body["state"] = "extra prompt"
    write(packet, body)
    with pytest.raises(ValueError, match="transport override"):
        evaluate(**fixture, transport_model="strict-model")


def test_unknown_time_invalidates_rate_and_cost_share(fixture: dict[str, Any]) -> None:
    path = fixture["worker_output"] / "attempts.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[1].pop("inference_wall_seconds")
    path.write_text("".join(json.dumps(event) + "\n" for event in events))
    result = evaluate(**fixture, rental_cost_usd=7, allocated_cost_usd=2, allocation_method="inference-wall-share")
    assert result["groups"][0]["regions_per_inference_minute"] is None
    assert result["groups"][0]["allocated_usd"] is None


def test_whole_run_cost_not_automatically_attributed(fixture: dict[str, Any]) -> None:
    result = evaluate(**fixture, rental_cost_usd=7)
    assert result["groups"][0]["allocated_usd"] is None
    result = evaluate(**fixture, allocated_cost_usd=2, allocation_method="inference-wall-share")
    assert result["groups"][0]["regions_per_allocated_usd"] == 12


def test_partial_final_line_checkpoint_only(fixture: dict[str, Any]) -> None:
    path = fixture["worker_output"] / "attempts.jsonl"
    with path.open("a") as handle:
        handle.write('{"unfinished":')
    with pytest.raises(json.JSONDecodeError):
        evaluate(**fixture)
    write(fixture["worker_output"] / "status.json", {"status": "running"})
    result = evaluate(**fixture)
    assert result["checkpoint"]
    assert result["incomplete_final_log_line"]


def test_protected_path_refused_before_read(fixture: dict[str, Any]) -> None:
    fixture["source_dir"] = Path("/never-open/heldout-silver")
    with pytest.raises(ValueError, match="protected"):
        evaluate(**fixture)


def test_schema_failure_keeps_planned_denominators(fixture: dict[str, Any]) -> None:
    path = fixture["worker_output"] / "attempts.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[1]["response"] = {"answers": {"q0": {"type": "choice", "choice": "join"}}}
    path.write_text("".join(json.dumps(event) + "\n" for event in events))
    row = evaluate(**fixture)["groups"][0]
    assert row["schema_failures"] == 1
    assert row["known_correct"] == 15
    assert row["known_denominator"] == 16
    assert row["ambiguous_denominator"] == 8


def test_duplicate_attempt_not_counted_as_fresh(fixture: dict[str, Any]) -> None:
    path = fixture["worker_output"] / "attempts.jsonl"
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines + lines[:2]) + "\n")
    with pytest.raises(ValueError, match="duplicate fresh attempt"):
        evaluate(**fixture)
