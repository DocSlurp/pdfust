"""Constrained scoring verifies all fresh sources before DEV reference access."""

# ruff: noqa: SLF001 - exercise strict accounting and malformed retained artifacts.
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench import remote_image_size_report as report
from bench import remote_image_sizes as sizes
from tests.test_remote_image_sizes import frozen  # noqa: F401 - shared CPU source-only fixture.


def _response(choice: str) -> dict[str, Any]:
    return {
        "answers": {
            "q0": {
                "type": "choice",
                "choice": choice,
                "probabilities": {option: float(option == choice) for option in ("join", "split", "unresolved")},
            }
        }
    }


def _events(identity: str, digest: str, choice: str = "join") -> list[dict[str, Any]]:
    return [
        {"id": identity, "event": "attempt_started", "attempt": 0},
        {
            "id": identity,
            "event": "attempt_completed",
            "attempt": 0,
            "request_sha256": digest,
            "status": "ok",
            "response": _response(choice),
            "inference_wall_seconds": 0.0,
            "inference_cpu_seconds": 0.0,
            "peak_rss_bytes": 100,
            "cuda": {"peak_allocated_bytes": 50},
        },
    ]


def _write_output(path: Path, events: list[dict[str, Any]], *, status: str = "running") -> None:
    path.mkdir()
    (path / "status.json").write_text(json.dumps({"status": status}))
    (path / "attempts.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events))


@pytest.fixture
def scoring(frozen: tuple[Path, Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:  # noqa: F811
    source, packets, index, destination = frozen
    manifest = json.loads((source / "manifest.json").read_bytes())
    observation = json.loads((source / "observation.json").read_bytes())
    observation.update(
        target_atoms=[[{"id": "a", "text": "Valve"}], [{"id": "b", "text": "Copper"}]],
        all_target_ids=["a", "b"],
        candidates={"join": [["a", "b"]], "split": [["a"], ["b"]], "unresolved": []},
    )
    raw_observation = sizes._encode(observation)
    (source / "observation.json").write_bytes(raw_observation)
    manifest["pages"][0]["observation_sha256"] = sizes._digest(raw_observation)
    target_raw = sizes._encode([{"id": "page", "expected": "join"}])
    (source / "private-targets.json").write_bytes(target_raw)
    manifest["targets_sha256"] = sizes._digest(target_raw)
    (source / "manifest.json").write_bytes(sizes._encode(manifest))
    provenance = sizes.prepare(source, packets, index, destination)
    baseline, output = source.parent / "baseline", source.parent / "worker"
    original = json.loads(index.read_bytes())[0]
    _write_output(baseline, _events(original["id"], original["sha256"], "split"), status="complete")
    first = provenance["mapping"][0]
    _write_output(output, _events(first["id"], first["projected_request_sha256"]))
    verified = {"done": False, "scorer_calls": 0}
    verify = sizes.verify

    def checked_verify(directory: Path) -> dict[str, Any]:
        result = verify(directory)
        verified["done"] = True
        return result

    monkeypatch.setattr(sizes, "verify", checked_verify)
    original_read = report._read

    def guarded_read(path: Path, limit: int) -> bytes:
        if path.name == "private-targets.json":
            assert verified["done"]
        return original_read(path, limit)

    monkeypatch.setattr(report, "_read", guarded_read)

    def baseline_scorer(*_args: object, **_kwargs: object) -> dict[str, Any]:
        assert verified["done"]
        verified["scorer_calls"] += 1
        return {
            "checkpoint": False,
            "source_manifest_sha256": sizes._digest(sizes._encode(manifest)),
            "worker_status": {"status": "complete"},
            "results": [
                {
                    "id": "p0000",
                    "arm": "fresh-rgb-512",
                    "status": "ok",
                    "parsed": {"choice": "split"},
                    "score": {"expected": "join"},
                }
            ],
        }

    monkeypatch.setattr(report.remote_report, "evaluate", baseline_scorer)
    return {
        "directory": destination,
        "output": output,
        "baseline": baseline,
        "provenance": provenance,
        "verified": verified,
        "source": source,
    }


def test_checkpoint_keeps_planned_and_paired_baseline(scoring: dict[str, Any]) -> None:
    result = report.evaluate(
        scoring["directory"], scoring["output"], scoring["baseline"], model=report.MODELS["flash"], hourly_usd=1.275
    )
    assert result["planned_regions"] == 21
    assert result["valid_regions"] == 1
    assert result["checkpoint"]
    assert scoring["verified"]["scorer_calls"] == 1
    first = result["groups"][0]
    assert first["known_correct"] == 1
    assert first["paired_baseline"]["known_improvements"] == 1
    assert first["marginal_inference_usd_estimate"] == 0
    assert first["regions_per_inference_minute"] is None
    assert result["baseline_groups"][0]["wrong_known_decisions"] == 1
    assert sum(row["unattempted_regions"] for row in result["groups"]) == 20


@pytest.mark.parametrize("mutation", ["png", "request_hash", "duplicate_attempt"])
def test_reject_before_scorer_references(scoring: dict[str, Any], mutation: str) -> None:
    directory, output = scoring["directory"], scoring["output"]
    mapping = scoring["provenance"]["mapping"][0]
    if mutation == "png":
        (directory / mapping["image_file"]).write_bytes(b"changed")
    else:
        path = output / "attempts.jsonl"
        events = [json.loads(line) for line in path.read_text().splitlines()]
        if mutation == "request_hash":
            events[1]["request_sha256"] = "wrong"
        else:
            events.append(events[0])
        path.write_text("".join(json.dumps(event) + "\n" for event in events))
    with pytest.raises(ValueError, match=r"changed|hash|Duplicate"):
        report.evaluate(directory, output, scoring["baseline"], model=report.MODELS["flash"])
    assert scoring["verified"]["scorer_calls"] == 0


def test_schema_error_stays_in_known_denominator(scoring: dict[str, Any]) -> None:
    path = scoring["output"] / "attempts.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    events[1]["response"] = {"answers": {"q0": {"type": "choice", "choice": "join", "confidence": 1}}}
    path.write_text("".join(json.dumps(event) + "\n" for event in events))
    result = report.evaluate(scoring["directory"], scoring["output"], scoring["baseline"], model=report.MODELS["flash"])
    assert result["groups"][0]["schema_failures"] == 1
    assert result["groups"][0]["known_denominator"] == 1
    assert result["groups"][0]["known_correct"] == 0
    assert result["valid_regions"] == 0


def test_complete_status_requires_entire_frozen_matrix(scoring: dict[str, Any]) -> None:
    (scoring["output"] / "status.json").write_text('{"status":"complete"}')
    with pytest.raises(ValueError, match="planned completed inventory"):
        report.evaluate(scoring["directory"], scoring["output"], scoring["baseline"], model=report.MODELS["flash"])
    assert scoring["verified"]["scorer_calls"] == 0


@pytest.mark.parametrize("duration", [None, -1, float("nan"), True])
def test_missing_resources_and_latency_are_unknown(duration: object) -> None:
    row = {
        "expected": "unresolved",
        "choice": "unresolved",
        "status": "ok",
        "attempted": True,
        "baseline": {"choice": "split"},
        "event": {"inference_wall_seconds": duration},
    }
    result = report._group("fresh-rgb-128", [row], 1.275)
    assert result["inference_seconds"] is None
    assert result["marginal_inference_usd_estimate"] is None
    assert result["peak_rss_bytes"] is None
    assert result["cuda_peak_allocated_bytes"] is None
    assert result["ambiguous_abstentions"] == 1
    assert result["paired_baseline"]["ambiguous_abstention_gains"] == 1


def test_token_means_never_fill_absent_fields_with_zero() -> None:
    rows = []
    for usage in ({"input_tokens": 512, "output_tokens": 0}, {"input_tokens": 1024}):
        rows.append(  # noqa: PERF401 - keep the two reported-usage cases explicit.
            {
                "expected": "join",
                "choice": "join",
                "status": "ok",
                "attempted": True,
                "baseline": None,
                "png_bytes": 100,
                "event": {"inference_wall_seconds": 2, "inference_cpu_seconds": 1, "response": {"usage": usage}},
            }
        )
    result = report._group("fresh-rgb-128", rows, 1.275)
    assert result["native_input_tokens_mean"] == 768
    assert result["native_output_tokens_mean"] is None
    assert result["native_output_tokens_mean_reported_count"] == 1
    assert result["mean_png_bytes"] == 100
    assert result["regions_per_inference_minute"] == 30
    assert result["marginal_inference_usd_estimate"] == pytest.approx(4 * 1.275 / 3600)
