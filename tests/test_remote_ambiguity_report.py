"""Matched controls remain source-verified before local DEV references."""

# ruff: noqa: ANN001, ANN201, ANN202, SLF001 - pytest mock interfaces.
import pytest
from bench import remote_ambiguity_report as report


def test_identity_control_hash_failure_blocks_reference_admission(tmp_path, monkeypatch):
    source = {
        "source_directory": str(tmp_path),
        "source_index": str(tmp_path / "index.json"),
        "source_packets": str(tmp_path / "packets"),
        "mapping": [],
    }
    monkeypatch.setattr(report, "_verify_matrix", lambda _: (source, {}))
    monkeypatch.setattr(report, "verify_prompts", lambda _: (source, {}))
    monkeypatch.setattr(report, "verify_sources", lambda *_: ({}, {}))
    calls = []

    def returned(path, _inventory):
        calls.append(path.name)
        if path.name == "identity":
            message = "forged identity request hash"
            raise ValueError(message)
        return {}, {}

    monkeypatch.setattr(report, "events", returned)
    reads = []
    monkeypatch.setattr(report, "_read", reads.append)
    with pytest.raises(ValueError, match="forged"):
        report.evaluate(
            tmp_path,
            tmp_path,
            {"flash": tmp_path / "run"},
            {"flash": tmp_path / "original"},
            {"flash": tmp_path / "identity"},
        )
    assert calls == ["run", "original", "identity"]
    assert reads == []


def test_mismatched_source_freeze_blocks_controls_and_refs(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "_verify_matrix", lambda _: ({"source": "one"}, {}))
    monkeypatch.setattr(report, "verify_prompts", lambda _: ({"source": "different"}, {}))
    reads = []
    monkeypatch.setattr(report, "_read", reads.append)
    with pytest.raises(ValueError, match="freezes differ"):
        report.evaluate(tmp_path, tmp_path, {}, {}, {})
    assert reads == []


def test_stock_client_resources_do_not_claim_server_allocation():
    observation = {
        "target_atoms": [[{"id": "a", "text": "a"}], [{"id": "b", "text": "b"}]],
        "all_target_ids": ["a", "b"],
        "candidates": {"join": [["a", "b"]], "split": [["a"], ["b"]], "unresolved": []},
    }
    event = {
        "status": "ok",
        "response": {"backend": "stock-vllm-json", "answers": {"q0": {"type": "choice", "choice": "unresolved"}}},
        "inference_wall_seconds": 1,
        "inference_cpu_seconds": 0.1,
        "cuda": {"peak_allocated_bytes": 0, "peak_reserved_bytes": 0},
    }
    case = report.matrix.scored_case(event, observation, {"expected": "unresolved"})
    metric = report._metrics([case])
    assert metric["inference_cpu_seconds"] is None
    assert metric["cuda_peak_allocated_bytes"] is None
    assert metric["tie_abstentions"] is None
    assert metric["ambiguous_abstentions"] == 1
