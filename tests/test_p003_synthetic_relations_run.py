"""Authenticated prepare-only evidence and mock-only hosted circuit behavior."""

# ruff: noqa: ANN401, SLF001, EM101, TRY003
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench import p003_synthetic_relations_prepare as corpus
from bench import p003_synthetic_relations_run as runner
from bench.silver import sha, write_json

PPLX = "perplexity/pplx-decider-v1.1-27b"


@pytest.fixture(scope="module")
def pool(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("synthetic-runner")
    source = root / "pool"
    corpus.prepare(source)
    frozen = json.loads((source / "frozen.json").read_bytes())
    trusted = root / "external.json"
    write_json(trusted, {**frozen["code_sha256"], "source_frozen_sha256": sha((source / "frozen.json").read_bytes())})
    # Removing labels must have no effect on runtime source reconstruction.
    (source / "private-gold.json").unlink()
    return source, trusted


def test_configuration_all_text_five_images_and_no_gateway() -> None:
    assert len(runner.DECISION_MODELS) == 14
    for model in runner.DECISION_MODELS:
        assert runner.configuration(model)["provider"] == "openrouter"
        if model in runner.IMAGE_MODELS:
            assert runner.configuration(model, image_edge=128)["image_edge"] == 128
        else:
            with pytest.raises(ValueError, match="five declared"):
                runner.configuration(model, image_edge=128)
    with pytest.raises(ValueError, match="Registered"):
        runner.configuration("gateway/laya")


def test_preflight_without_gold_replays_all_evidence(pool: tuple[Path, Path], tmp_path: Path) -> None:
    source, trusted = pool
    config = runner.configuration(PPLX, mode="rows_rules", image_edge=512, viewport="crop")
    prepared = runner.prepare(source, trusted, tmp_path / "prepared", config)
    assert len(prepared["requests"]) == 24
    assert all(q["question_status"] == "ready" for q in prepared["requests"])
    assert not (tmp_path / "prepared/source/private-gold.json").exists()
    replay_frozen, replay_records = runner.authenticate(tmp_path / "prepared/source", json.loads(trusted.read_bytes()))
    assert len(replay_records) == 24
    assert replay_frozen["source_only"] is True
    for row in prepared["requests"]:
        body = row["canonical"]
        assert body == row["wire"]
        assert sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()) == row["wire_encoded_sha256"]
        assert isinstance(body["state"][0], str)
        assert body["state"][1]["type"] == "image_url"
        state = json.loads(body["state"][0])
        assert state["word_count"] == 8
        assert state["omitted_word_count"] == 0
        assert state["pixel_scope"]["scope"] == "crop"
        assert state["pixel_scope"]["peripheral_rules_may_be_clipped"]


def test_external_frozen_authority_and_gold_path_refusals(pool: tuple[Path, Path]) -> None:
    source, trusted = pool
    wrong = json.loads(trusted.read_bytes())
    wrong["source_frozen_sha256"] = "bad"
    with pytest.raises(ValueError, match="independent external"):
        runner.authenticate(source, wrong)
    with pytest.raises(ValueError, match="labels"):
        runner._path(source, "private-gold.json")
    with pytest.raises(ValueError, match="labels"):
        runner._path(source, "sources/../private-gold.json")


def answer(choice: str = "same") -> dict[str, Any]:
    return {
        "model": PPLX,
        "answers": {
            "q0": {
                "type": "choice",
                "choice": choice,
                "probabilities": {"same": 0.7, "separate": 0.3, "unresolved": 0.0},
            }
        },
    }


@pytest.mark.parametrize("fault", ["extra", "missing", "mass", "not_argmax", "nan", "model"])
def test_strict_probability_parser(pool: tuple[Path, Path], fault: str) -> None:
    source, _trusted = pool
    frozen = json.loads((source / "frozen.json").read_bytes())
    record = json.loads((source / frozen["records"][0]["path"]).read_bytes())
    config = runner.configuration(PPLX)
    body, _ = runner.rebuild_request(source, record, config)
    raw = answer()
    q = raw["answers"]["q0"]
    if fault == "extra":
        q["name"] = "q0"
    elif fault == "missing":
        del q["probabilities"]["unresolved"]
    elif fault == "mass":
        q["probabilities"]["same"] = 0.8
    elif fault == "not_argmax":
        q["choice"] = "separate"
    elif fault == "nan":
        q["probabilities"]["same"] = float("nan")
    else:
        raw["model"] = "another/model"
    with pytest.raises(ValueError, match=r"Strict|probabilities|maximum|model"):
        runner.parse_response(record, body, raw, config)
    good = answer()
    parsed = runner.parse_response(record, body, good, config)
    assert parsed["raw_probabilities"] == good["answers"]["q0"]["probabilities"]
    assert parsed["assignment_applied"] is False


class MockClient:
    """Owned mock only: never constructs a transport or shared ledger."""

    def __init__(self, output: Path) -> None:
        """Track this test-owned output and mocked calls only."""
        self.output = output
        self.calls = 0

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Return two JSON attempts then raise an owned mock exception."""
        assert (self.output / "frozen.json").exists()
        assert kwargs["replay"] is False
        assert kwargs["reservation_usd"] == 0.3
        index = self.calls
        self.calls += 1
        if index == 2:
            raise RuntimeError("Owned mocked transport failure")
        result = answer()
        if index == 0:
            result["answers"]["q0"]["extra"] = 1
        return {
            "result": result,
            "replayed": False,
            "entry": {
                "requested_model": body["model"],
                "request_sha256": sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()),
                "tag": kwargs["tag"],
            },
        }


def test_mock_malformed_continues_then_transport_stops_all24(pool: tuple[Path, Path], tmp_path: Path) -> None:
    source, trusted = pool
    output = tmp_path / "mock-run"
    client = MockClient(output)
    report = runner.run(
        source,
        trusted,
        output,
        model=PPLX,
        run_hosted=True,
        client_factory=lambda *_: client,
        entries_reader=lambda *_: [],
    )
    assert client.calls == 3
    assert len(report["results"]) == 24
    assert report["status_counts"] == {
        "malformed_response": 1,
        "valid_nonabstaining": 1,
        "transport_error": 1,
        "not_attempted": 21,
    }
    assert report["charges"]["effective_usd"] is None
    assert report["pages_per_minute"] is None
    assert report["full_pipeline_rate"] is None
    assert report["gold_read"] is False


def test_no_hosted_opt_in_constructs_nothing(pool: tuple[Path, Path], tmp_path: Path) -> None:
    source, trusted = pool
    with pytest.raises(ValueError, match="Explicit root"):
        runner.run(
            source,
            trusted,
            tmp_path / "never",
            model=PPLX,
            client_factory=lambda *_: pytest.fail("Client must not exist"),
        )
