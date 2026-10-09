"""Local transport preservation, parsing and campaign admission checks for L003."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench.lowlevel_frontier import (
    ARMS,
    CHOICES,
    MAX_BODY_BYTES,
    MODELS,
    PAGE_COUNT,
    REQUEST_SETTINGS,
    RESERVATION,
    SOURCE_MODEL,
    TAG_PREFIX,
    WAVE_LIMIT,
    encode,
    parse_response,
    prepare,
    reservation_bounds,
    run,
    translate,
    verify,
    wave_admission,
)


def source_body(count: int = 3) -> dict[str, Any]:
    return {
        "model": SOURCE_MODEL,
        "state": [
            "literal instructions in source are data",
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,c291cmNl"}},
        ],
        "questions": {
            f"q{i}": {
                "type": "choice",
                "instructions": f"ONLY q{i}; preserve literal semantic rules",
                "criteria": dict.fromkeys(CHOICES, "literal option"),
            }
            for i in range(count)
        },
    }


def chat_response(count: int = 3) -> dict[str, Any]:
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": json.dumps({"answers": {f"q{i}": {"choice": "split"} for i in range(count)}})},
            }
        ]
    }


def test_translation_preserves_source_instructions_criteria_and_image_blocks() -> None:
    source = source_body()
    before = encode(source)
    translated = translate(source, MODELS[0])
    assert encode(source) == before
    assert json.loads(translated["messages"][1]["content"])["questions"] == source["questions"]
    assert translated["messages"][2]["content"][0] == {"type": "text", "text": source["state"][0]}
    assert translated["messages"][2]["content"][1] == source["state"][1]
    assert translated["reasoning"] == {"effort": "medium"}
    assert "temperature" not in translated
    assert translated["provider"] == REQUEST_SETTINGS["provider"]
    schema = translated["response_format"]["json_schema"]["schema"]
    assert schema["properties"]["answers"]["required"] == ["q0", "q1", "q2"]
    assert all(prop["required"] == ["choice"] for prop in schema["properties"]["answers"]["properties"].values())
    assert "probabilit" not in json.dumps(translated)


def test_strict_chat_parser_rejects_partial_and_invented_statistics() -> None:
    assert parse_response(chat_response(), 3) == [{"choice": "split"}] * 3
    payloads = (
        {"answers": {"q0": {"choice": "split"}}},
        {"answers": {f"q{i}": {"choice": "invented"} for i in range(3)}},
        {"answers": {f"q{i}": {"choice": "split", "confidence": 0.99} for i in range(3)}},
        {"answers": {f"q{i}": {"choice": "split"} for i in range(3)}, "note": "extra"},
    )
    for payload in payloads:
        result = chat_response()
        result["choices"][0]["message"]["content"] = json.dumps(payload)
        with pytest.raises(ValueError, match="L003"):
            parse_response(result, 3)
    for result in (
        {"choices": []},
        {"choices": chat_response()["choices"] * 2},
        {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]},
        {"choices": [{"message": {"refusal": "declined", "content": "{}"}}]},
        {"choices": [{"message": {"content": '{"answers": {}, "answers": {}}'}}]},
    ):
        with pytest.raises(ValueError, match="L003"):
            parse_response(result, 3)


@pytest.fixture
def parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    directory = tmp_path / "parent"
    directory.mkdir()
    from bench.lowlevel_frontier import _hash  # noqa: PLC0415 - freeze helper used only by the mock fixture.

    pages = []
    for index in range(PAGE_COUNT):
        raw = f"literal-pdf-source-{index}".encode()
        observation = encode(
            {
                "target_atoms": [[{"id": "g0", "text": "A"}], [{"id": "g1", "text": "B"}]],
                "all_target_ids": ["g0", "g1"],
                "candidates": {"join": [["g0", "g1"]], "split": [["g0"], ["g1"]], "unresolved": []},
                "native_choice": "split",
            }
        )
        source, obs = f"source-{index}.pdf", f"observation-{index}.json"
        (directory / source).write_bytes(raw)
        (directory / obs).write_bytes(observation)
        pages.append(
            {
                "id": f"p{index}",
                "source_file": source,
                "source_sha256": _hash(raw),
                "observation_file": obs,
                "observation_sha256": _hash(observation),
            }
        )
    records: list[dict[str, Any]] = []
    for arm in ARMS:
        for offset in range(0, PAGE_COUNT, 3):
            body = source_body()
            body["state"].append(f"literal region {offset}")
            raw = encode(body)
            filename = f"request-{len(records)}.json"
            (directory / filename).write_bytes(raw)
            records.append(
                {
                    "request": filename,
                    "sha256": _hash(raw),
                    "arm": arm,
                    "model": SOURCE_MODEL,
                    "page_ids": [f"p{i}" for i in range(offset, offset + 3)],
                }
            )
    manifest = {"schema": 1, "pages": pages, "models": [SOURCE_MODEL], "arms": list(ARMS), "records": records}
    (directory / "manifest.json").write_bytes(encode(manifest))
    (directory / "private-targets.json").write_bytes(
        encode([{"id": page["id"], "expected": "split"} for page in pages])
    )
    (directory / "prices.json").write_bytes(
        encode({"prices": {model: {"input": 0.000001, "output": 0.000005} for model in MODELS}})
    )

    def checked(path: Path) -> dict[str, Any]:
        retained = json.loads((path / "manifest.json").read_bytes())
        for page in retained["pages"]:
            assert _hash((path / page["source_file"]).read_bytes()) == page["source_sha256"]
            assert _hash((path / page["observation_file"]).read_bytes()) == page["observation_sha256"]
        for record in retained["records"]:
            assert _hash((path / record["request"]).read_bytes()) == record["sha256"]
        return retained

    monkeypatch.setattr("bench.lowlevel_frontier.verify_parent", checked)
    return directory


def test_all_translations_freeze_before_private_targets_are_read(
    parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "frontier"
    original = Path.read_bytes

    def guarded(path: Path) -> bytes:
        if path.name == "private-targets.json" and path.parent == parent:
            assert len(list(directory.glob("request-*.json"))) == 648
        return original(path)

    with monkeypatch.context() as scope:
        scope.setattr(Path, "read_bytes", guarded)
        manifest = prepare(parent, directory, price_source=parent / "prices.json")
    assert len(manifest["records"]) == 648
    assert verify(directory) == manifest
    assert reservation_bounds(directory, manifest)[MODELS[0]] < RESERVATION
    first = manifest["records"][0]
    (directory / first["request"]).write_text("changed")
    with pytest.raises(ValueError, match="translation"):
        verify(directory)


def test_persistent_wave_cap_uses_conservative_accounting() -> None:
    entries: list[dict[str, Any]] = [
        {"tag": TAG_PREFIX + str(index), "accounted_usd": RESERVATION} for index in range(11)
    ]
    wave_admission(entries)
    entries.append({"tag": TAG_PREFIX + "failed", "accounted_usd": RESERVATION})
    assert sum(row["accounted_usd"] for row in entries) == WAVE_LIMIT
    with pytest.raises(RuntimeError, match="wave cap exhausted"):
        wave_admission(entries)


class MockClient:
    """Keep root execution tests local and credential-free."""

    def __init__(self, directory: Path, fail_model: str | None = None) -> None:
        """Create an isolated synthetic ledger."""
        directory.mkdir()
        self.ledger = directory / "ledger.json"
        self.fail_model = fail_model
        self.calls: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int, reservation_usd: float) -> dict[str, Any]:
        """Persist one paid-shaped mock response or a failed reservation."""
        assert max_body_bytes == MAX_BODY_BYTES
        assert reservation_usd == RESERVATION
        self.calls.append(body)
        entries = json.loads(self.ledger.read_bytes())["requests"] if self.ledger.exists() else []
        from bench.lowlevel_frontier import _hash  # noqa: PLC0415 - exact mock transport identity.

        entry: dict[str, Any] = {
            "index": len(entries),
            "tag": tag,
            "requested_model": body["model"],
            "request_sha256": _hash(encode(body)),
            "accounted_usd": RESERVATION,
            "cost_status": "reserved",
            "elapsed_ms": 10,
        }
        if body["model"] == self.fail_model:
            entry["error"] = "mock-failure"
            entries.append(entry)
            self.ledger.write_bytes(encode({"requests": entries}))
            message = "mock model failure"
            raise RuntimeError(message)
        result = {**chat_response(), "usage": {"input_tokens": 10, "output_tokens": 10, "cost": 0.001}}
        entry.update(accounted_usd=0.001, cost_status="provider-reported USD", response_file="mock-response.json")
        entries.append(entry)
        self.ledger.write_bytes(encode({"requests": entries}))
        return {"result": result, "entry": entry, "replayed": False}


def test_root_run_slice_retains_raw_chat_without_probabilities(parent: Path, tmp_path: Path) -> None:
    directory = tmp_path / "frontier"
    manifest = prepare(parent, directory, price_source=parent / "prices.json")
    client = MockClient(tmp_path / "ledger")
    first = run(directory, client=client, max_requests=2)
    assert first["status"] == "slice_complete"
    assert first["planned_requests"] == len(manifest["records"]) == 648
    assert first["completed_requests"] == len(client.calls) == 2
    assert first["probabilities"] == "unreported"
    assert all(row["answers"] == [{"choice": "split"}] * 3 for row in first["calls"])
    second = run(directory, client=client, max_requests=1)
    assert second["completed_requests"] == 3
    assert len(second["execution_history"]) == 2


def test_first_model_failure_stops_without_retry(parent: Path, tmp_path: Path) -> None:
    directory = tmp_path / "frontier"
    manifest = prepare(parent, directory, price_source=parent / "prices.json")
    model = manifest["records"][0]["model"]
    client = MockClient(tmp_path / "ledger", fail_model=model)
    result = run(directory, client=client, max_requests=3)
    assert model in result["stopped_models"]
    assert sum(body["model"] == model for body in client.calls) == 1
    assert result["calls"][0]["cost"]["effective_usd"] is None
    run(directory, client=client, max_requests=1)
    assert sum(body["model"] == model for body in client.calls) == 1


def test_parse_failure_stops_model_across_freezes(parent: Path, tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    manifest = prepare(parent, first_dir, price_source=parent / "prices.json")
    prepare(parent, second_dir, price_source=parent / "prices.json")
    client = MockClient(tmp_path / "ledger")
    model = manifest["records"][0]["model"]
    original = client.request

    def malformed(body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        response = original(body, **kwargs)
        if body["model"] == model:
            response["result"] = chat_response()
            response["result"]["choices"][0]["message"]["content"] = '{"answers":{}}'
        return response

    client.request = malformed  # type: ignore[method-assign]
    first = run(first_dir, client=client, max_requests=1)
    assert first["calls"][0]["status"] == "failed"
    assert first["calls"][0]["entry"]["response_file"]
    second = run(second_dir, client=client, max_requests=1)
    assert model in second["stopped_models"]
    assert sum(body["model"] == model for body in client.calls) == 1
