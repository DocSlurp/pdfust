"""New crop edges preserve native protocol and isolate every process-local patch."""

from __future__ import annotations

import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_synthetic_resolution as images
from bench import p003_synthetic_resolution_plan as plan
from bench import p003_synthetic_resolution_run as runner
from bench.feature_cases import page_pdf, text_op
from bench.silver import sha
from PIL import Image

# ruff: noqa: SLF001, PT012, EM101, TRY003


@pytest.fixture
def record() -> tuple[dict, bytes]:
    pdf = page_pdf("\n".join([text_op("Amber", 42, 720), text_op("Birch", 190, 720)]))
    source, pair, drawings = images.evidence.extract(pdf, ["Amber", "Birch"])
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


@pytest.mark.parametrize("edge", images.EDGES)
def test_exact_source_rgb_native_string_scope_and_rounding(record: tuple, edge: int) -> None:
    source, pdf = record
    before = deepcopy(source)
    raw, receipt = images.render(source, pdf, edge)
    assert images.evidence.EDGES == (128, 512)
    with Image.open(io.BytesIO(raw)) as pixels:
        assert pixels.mode == "RGB"
        assert list(pixels.size) == receipt["dimensions"]
        assert pixels.size[0] == round(280 * edge / 260) - round(20 * edge / 260)
    body = images.request(source, images.MODELS[0], {"status": "ready", **receipt}, raw)
    assert isinstance(body["state"][0], str)
    assert body["state"][1]["type"] == "image_url"
    packet = json.loads(body["state"][0])
    assert packet["source"] == source["source"]
    assert packet["omitted_word_count"] == 0
    assert packet["pixel_scope"]["dimensions"] == receipt["dimensions"]
    assert body["questions"]["q0"]["instructions"] == images.evidence.INSTRUCTIONS
    assert source == before
    with pytest.raises(ValueError, match="digest"):
        images.request(source, images.MODELS[0], receipt, b"changed")


def test_controls_not_admitted_and_full_render_bound_no_implicit_downscale(record: tuple) -> None:
    source, pdf = record
    for edge in (128, 512):
        with pytest.raises(ValueError, match="declared edge"):
            images.render(source, pdf, edge)
    for item in source["images"]:
        item["viewport"] = [10, 10, 11, 11]
    with pytest.raises(ValueError, match="full-page render"):
        images.render(source, pdf, 1024)


def test_adapter_restore_on_failure_rejects_controls_text_models_and_nested(
    tmp_path: Path, record: tuple, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _ = record
    pool = tmp_path / "pool"
    pool.mkdir()
    (pool / "frozen.json").write_text("{}")
    context = {"records": [source], "frozen_sha256": "source", "map_sha256": "map"}
    monkeypatch.setattr(runner.evaluator, "source_context", lambda *_: context)
    monkeypatch.setattr(images, "authenticate_images", lambda *_: {source["id"]: {"images": []}})
    original = {
        name: getattr(runner.legacy, name) for name in ("configuration", "rebuild_request", "prepare", "CODE_FILES")
    }
    with pytest.raises(RuntimeError, match="injected"), runner.adapter(pool, pool, pool, pool):
        assert runner.legacy.configuration(images.MODELS[0], image_edge=256)["image_edge"] == 256
        for edge in (0, 128, 512):
            with pytest.raises(ValueError, match="new crop edges"):
                runner.legacy.configuration(images.MODELS[0], image_edge=edge)
        with pytest.raises(ValueError, match="new crop edges"):
            runner.legacy.configuration("typesafe/jev-1.13", image_edge=256)
        with pytest.raises(ValueError, match="Nested"), runner.adapter(pool, pool, pool, pool):
            pass
        raise RuntimeError("injected")
    assert images.evidence.EDGES == (128, 512)
    assert runner._ACTIVE is False
    assert all(getattr(runner.legacy, name) is value for name, value in original.items())


def test_mock_hosted_freezes_before_client_malformed_continues_then_transport_stops(
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
    monkeypatch.setattr(runner.evaluator, "source_context", lambda *_: context)
    monkeypatch.setattr(images, "authenticate_images", lambda *_: {})
    raw, image = images.render(source, pdf, 256)
    bodies = [images.request(r, "cloudflare/clef", image, raw) for r in records]

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
        256,
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
    assert images.evidence.EDGES == (128, 512)


def test_plan_all25_independent_models_edges_without_controls_or_hosted_flag(tmp_path: Path) -> None:
    rows = plan.arms(tmp_path, tmp_path, tmp_path, tmp_path)
    assert len(rows) == 25
    assert len({r["name"] for r in rows}) == 25
    assert {(r["model"], r["image_edge"]) for r in rows} == {
        (model, edge) for model in images.MODELS for edge in images.EDGES
    }
    assert all("--run-hosted" not in r["args"] for r in rows)
    assert sum(r["question_count"] for r in rows) == 600
    assert not any(r["image_edge"] in (128, 512) for r in rows)
