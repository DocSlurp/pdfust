"""Source-only admission and strict generated-label regression controls."""

# ruff: noqa: ANN001, ANN201, ANN202, SLF001 - pytest fixture and mock interfaces.
import json

import pytest
from bench import remote_ambiguity_evidence as matrix
from bench.remote_prompt_packets import _encode
from test_remote_prompt_sizes import fixture as fresh_fixture


def fixture(tmp_path, monkeypatch):
    fresh, _, _ = fresh_fixture(tmp_path, monkeypatch)
    source = json.loads((fresh / "provenance.json").read_bytes())
    source["source_directory"] = str(tmp_path / "original")
    monkeypatch.setattr(matrix, "verify_fresh", lambda _: source)
    measured = {
        f"p{number:04d}": {
            "geometry": {
                "features": {"font_scale": 12, "same_explicit_cell": False},
                "qualifiers": {"choice": "join", "case_id": "must never upload"},
            },
            "pixels": {
                "features": {"available": True, "axis_inline": False, "normalization_scale": 12},
                "qualifiers": {"choice": "unresolved", "visible_boundary_support": ["unknown semantic advice"]},
            },
        }
        for number in range(24)
    }
    monkeypatch.setattr(matrix, "_features", lambda _: measured)
    output = tmp_path / "evidence"
    matrix.prepare(fresh, output)
    return output


def test_complete_matrix_preserves_literal_sources_and_omits_choices(tmp_path, monkeypatch):
    output = fixture(tmp_path, monkeypatch)
    _, admitted = matrix.verify(output)
    assert len(admitted) == 288
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert set(manifest) == {"records"}
    assert len(list(output.glob("*.png"))) == 48
    for row in admitted.values():
        body = json.loads((output / (row["id"] + ".json")).read_bytes())
        assert body["state"][0].startswith("literal source ")
        evidence = json.loads(body["state"][2])["supplemental_evidence"]
        assert "choice" not in body["state"][2]
        assert "case_id" not in body["state"][2]
        assert "must never upload" not in body["state"][2]
        assert all(matrix._numeric(value) for value in evidence.values())
        assert row["pack"] in matrix.PACKS


def test_non_numeric_whitelisted_evidence_is_refused():
    with pytest.raises(ValueError, match="nonnumeric"):
        matrix.evidence({"features": {"font_scale": "text label"}}, {"features": {}}, "geometry")
    assert not matrix._numeric({"case_id": 1})
    assert not matrix._numeric([1] * 33)


def test_rehashed_source_state_or_added_advice_refused(tmp_path, monkeypatch):
    output = fixture(tmp_path, monkeypatch)
    row = json.loads((output / "manifest.json").read_bytes())["records"][0]
    path = output / row["request_file"]
    body = json.loads(path.read_bytes())
    body["state"][2] = '{"suggested_choice":"join"}'
    path.write_bytes(_encode(body))
    with pytest.raises(ValueError, match="Evidence projection"):
        matrix.verify(output)


def test_changed_feature_code_blocks_source_admission(tmp_path, monkeypatch):
    output = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(matrix, "_code_hashes", lambda: {"geometry": "modified"})
    with pytest.raises(ValueError, match="policy/code"):
        matrix.verify(output)


def test_bad_source_blocks_reference_read(tmp_path, monkeypatch):
    def refuse(_):
        message = "unverified sources"
        raise ValueError(message)

    monkeypatch.setattr(matrix, "verify", refuse)
    reads = []
    monkeypatch.setattr(matrix, "_read", reads.append)
    with pytest.raises(ValueError, match="unverified"):
        matrix.evaluate(tmp_path, {"flash": tmp_path})
    assert reads == []


def test_stock_label_has_no_invented_probability_or_tie_measurement():
    observation = {
        "target_atoms": [[{"id": "a", "text": "a"}], [{"id": "b", "text": "b"}]],
        "all_target_ids": ["a", "b"],
        "candidates": {"join": [["a", "b"]], "split": [["a"], ["b"]], "unresolved": []},
    }
    event = {
        "status": "ok",
        "response": {"backend": "stock-vllm-json", "answers": {"q0": {"type": "choice", "choice": "unresolved"}}},
    }
    case = matrix.scored_case(event, observation, {"expected": "unresolved"})
    assert case["status"] == "ok"
    assert case["parsed"]["probabilities"] is None
    assert matrix.metrics([case])["tie_abstentions"] is None
    event["response"]["answers"]["q0"]["confidence"] = 0.9
    assert matrix.scored_case(event, observation, {"expected": "unresolved"})["status"] == "schema_error"
