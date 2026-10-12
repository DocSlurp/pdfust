"""Matched pixels/criteria with complete richer source evidence and isolated adapters."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_synthetic_resolution as pixels
from bench import p003_synthetic_rules_resolution as rules
from bench import p003_synthetic_rules_resolution_eval as verifier
from bench import p003_synthetic_rules_resolution_run as runner
from bench.feature_cases import page_pdf, text_op
from bench.silver import sha

# ruff: noqa: PT012, EM101, TRY003, SLF001


@pytest.fixture
def record() -> tuple[dict, bytes]:
    pdf = page_pdf("\n".join([text_op("Amber", 42, 720), text_op("Birch", 190, 720), "40 700 m 300 700 l S"]))
    source, pair, drawings = pixels.evidence.extract(pdf, ["Amber", "Birch"])
    return {
        "id": "opaque",
        "kind": "cell",
        "status": "ready",
        "source": source,
        "pair_source_ids": pair,
        "drawings": drawings,
        "pdf_sha256": sha(pdf),
        "images": [{"scope": "crop", "edge": edge, "viewport": [20, 30, 280, 150]} for edge in (128, 512)],
    }, pdf


@pytest.mark.parametrize("edge", rules.EDGES)
def test_matched_native_pixels_scope_criteria_and_all_literal_rows_rules(record: tuple, edge: int) -> None:
    source, pdf = record
    before = deepcopy(source)
    raw, item = pixels.render(source, pdf, edge)
    plain = pixels.request(source, pixels.MODELS[0], item, raw)
    rich = rules.request(source, pixels.MODELS[0], item, raw)
    plain_state, rich_state = [json.loads(body["state"][0]) for body in (plain, rich)]
    assert isinstance(rich["state"][0], str)
    assert rich["state"][1] == plain["state"][1]
    assert rich["questions"] == plain["questions"]
    assert rich_state["pixel_scope"] == plain_state["pixel_scope"]
    assert rich_state["source"] == plain_state["source"] == source["source"]
    assert rich_state["observed_drawings"] == source["drawings"]
    assert "physical_observations" in rich_state
    assert "physical_observations" not in plain_state
    assert rich_state["omitted_word_count"] == 0
    assert source == before


def test_adapter_restores_all_frozen_functions_and_rejects_other_modes(
    tmp_path: Path, record: tuple, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = record
    (tmp_path / "frozen.json").write_text("{}")
    monkeypatch.setattr(
        runner.base.evaluator,
        "source_context",
        lambda *_: {"records": [source], "frozen_sha256": "source", "map_sha256": "map"},
    )
    monkeypatch.setattr(pixels, "authenticate_images", lambda *_: {source["id"]: {"images": []}})
    names = ("configuration", "rebuild_request", "prepare", "CODE_FILES")
    original = {name: getattr(runner.legacy, name) for name in names}
    original_charges = runner.billing._charges
    with pytest.raises(RuntimeError, match="owned test"), runner.adapter(tmp_path, tmp_path, tmp_path, tmp_path):
        config = runner.legacy.configuration(rules.MODELS[0], image_edge=400)
        assert config["mode"] == "rows_rules"
        assert config["rows_rules_resolution"]["version"] == rules.VERSION
        assert len(runner.legacy.CODE_FILES) == 31
        with pytest.raises(ValueError, match="fixed 400/768"):
            runner.legacy.configuration(rules.MODELS[0], image_edge=500)
        with pytest.raises(ValueError, match="Complete rows/rules"):
            runner.legacy.configuration(rules.MODELS[0], mode="text_geometry", image_edge=400)
        raise RuntimeError("owned test")
    assert pixels.evidence.EDGES == (128, 512)
    assert runner.base._ACTIVE is False
    assert runner.billing._charges is original_charges
    assert all(getattr(runner.legacy, name) is value for name, value in original.items())


def test_richer_mock_hosted_freezes_before_client_and_keeps_circuit(
    tmp_path: Path, record: tuple, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, pdf = record
    pool = tmp_path / "pixels"
    pool.mkdir()
    (pool / "frozen.json").write_text(json.dumps({"code_sha256": {}, "image_sha256": {}}))
    (pool / "images.json").write_text("{}")
    authority = tmp_path / "map.json"
    authority.write_text("{}")
    records = [{**deepcopy(source), "id": f"opaque{i}"} for i in range(24)]
    context = {"records": records, "frozen_sha256": "source", "map_sha256": "map"}
    monkeypatch.setattr(runner.base.evaluator, "source_context", lambda *_: context)
    monkeypatch.setattr(pixels, "authenticate_images", lambda *_: {})
    raw, image = pixels.render(source, pdf, 400)
    bodies = [rules.request(r, "cloudflare/clef", image, raw) for r in records]

    def original_prepare(_source: Path, _map: Path, output: Path, config: dict) -> dict:
        output.mkdir()
        prepared = {
            "frozen": {"config": config},
            "records": records,
            "requests": [
                {
                    "index": i,
                    "question_status": "ready",
                    "canonical": b,
                    "wire": b,
                    "wire_encoded_sha256": sha(json.dumps(b, separators=(",", ":"), allow_nan=False).encode()),
                }
                for i, b in enumerate(bodies)
            ],
        }
        (output / "frozen.json").write_text(json.dumps(prepared["frozen"]))
        return prepared

    monkeypatch.setattr(runner.legacy, "prepare", original_prepare)
    output = tmp_path / "mock-r0"

    class Client:
        def __init__(self) -> None:
            self.entries: list[dict] = []
            self.calls = 0

        def request(self, body: dict, *, tag: str, replay: bool, **_kwargs: object) -> dict:
            assert replay is False
            assert body == bodies[self.calls]
            self.calls += 1
            entry = {
                "requested_model": "cloudflare/clef",
                "tag": tag,
                "request_sha256": sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()),
                "accounted_usd": 0.30 if self.calls == 3 else 0.001,
                "cost_status": "reserved" if self.calls == 3 else "provider-reported USD",
            }
            self.entries.append(entry)
            if self.calls == 3:
                raise RuntimeError("transport stop")
            result = {
                "model": "cloudflare/clef",
                "answers": {
                    "q0": {
                        "type": "choice",
                        "choice": "wrong" if self.calls == 1 else "same",
                        "probabilities": {"same": 0.7, "separate": 0.3, "unresolved": 0.0},
                    }
                },
            }
            return {"result": result, "entry": entry, "replayed": False}

    client = Client()

    def factory(_config: dict, prepared: dict) -> Client:
        assert len(prepared["requests"]) == 24
        assert (output / "resolution-input.json").is_file()
        assert (output / "resolution-source/trusted-code.json").is_file()
        return client

    report = runner.execute(
        pool,
        authority,
        pool,
        authority,
        output,
        "cloudflare/clef",
        400,
        run_hosted=True,
        client_factory=factory,
        entries_reader=lambda _client, _prefix: client.entries,
    )
    assert client.calls == 3
    assert len(report["results"]) == 24
    assert [r["status"] for r in report["results"][:3]] == [
        "malformed_response",
        "valid_nonabstaining",
        "transport_error",
    ]
    assert all(r["status"] == "not_attempted" for r in report["results"][3:])
    assert report["charges"]["unresolved_reserved_usd"] == 0.30
    assert report["charges"]["effective_usd"] is None
    assert report["full_pipeline_rate"] is None
    assert pixels.evidence.EDGES == (128, 512)


@pytest.mark.parametrize(
    "entries",
    [
        [{"cost_status": "unknown", "accounted_usd": 0.01}],
        [{"cost_status": "reserved", "accounted_usd": 0.03}],
        [{"cost_status": "provider-reported USD", "accounted_usd": None, "provider_reported_usd": None}],
        [{"cost_status": "catalog estimate", "accounted_usd": 0.02, "provider_reported_usd": 0}],
        [{"cost_status": "provider-reported USD", "accounted_usd": 0.01, "provider_reported_usd": 0.01}],
        [
            {
                "cost_status": "provider-reported BYOK upstream plus gateway USD",
                "accounted_usd": 0.04,
                "provider_reported_usd": 0.04,
            }
        ],
        [{"accounted_usd": 0.02, "provider_reported_usd": None}],
        [{"cost_status": "reserved", "accounted_usd": None}],
    ],
)
def test_financial_bases_missing_null_and_raw_zero_are_preserved(entries: list[dict]) -> None:
    original = deepcopy(entries)
    producer = runner.charges(entries)
    independent = verifier.charges(entries, len(entries))
    assert {k: v for k, v in producer.items() if k != "entries"} == independent
    assert entries == original
    if entries[0].get("cost_status") in (None, "unknown", "reserved") or entries[0].get("accounted_usd") is None:
        assert producer["effective_usd"] is None
    if entries[0].get("provider_reported_usd") is None:
        assert producer["provider_reported_usd"] is None
        assert producer["missing_provider_charge_count"] == 1
    if entries[0].get("provider_reported_usd") == 0:
        assert producer["provider_reported_usd"] == 0
        assert producer["missing_provider_charge_count"] == 0


@pytest.mark.parametrize("invalid", [True, -0.01, float("nan"), float("inf"), "0.01"])
def test_invalid_financial_numbers_refused_in_both_implementations(invalid: object) -> None:
    entries = [{"cost_status": "provider-reported USD", "accounted_usd": invalid}]
    with pytest.raises(ValueError, match="Financial amounts"):
        runner.charges(entries)
    with pytest.raises(ValueError, match="Invalid retained financial"):
        verifier.charges(entries, 1)


def test_missing_attempt_receipts_remain_unknown() -> None:
    result = verifier.charges([], 1)
    assert result["effective_usd"] is None
    assert result["provider_reported_usd"] is None
    assert result["accounting_status"] == "Missing attempt accounting; costs unknown"
