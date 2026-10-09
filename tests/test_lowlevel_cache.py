"""No-network exact-body cache probe, persistent admission and unknown accounting."""

from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest
from bench.lowlevel_cache import ARMS, MAX_CALLS, MODELS, PREFIX, admission, prepare, run, summarize, verify


def _write(path: Path, value: object) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _result(*, cost: float = 0.01, trial: int = 0) -> dict[str, Any]:
    usage: dict[str, Any] = {"input_tokens": 100, "output_tokens": 10, "cost": cost}
    if trial:
        usage["input_tokens_details"] = {"cached_tokens": 50, "cache_write_tokens": 0}
    return {
        "answers": {
            "q0": {"type": "choice", "choice": "join", "probabilities": {"join": 0.8, "split": 0.1, "unresolved": 0.1}}
        },
        "model": "served",
        "provider": "provider-b" if trial == 2 else "provider-a",
        "usage": usage,
    }


class FakeClient:
    """In-memory provider substitute with a persistent fake shared ledger."""

    def __init__(self, directory: Path, parent: Path) -> None:
        """Seed prior successful parent responses without credentials."""
        self.ledger = directory / "ledger.json"
        directory.mkdir()
        self.calls: list[tuple[bytes, dict[str, Any]]] = []
        records = json.loads((parent / "manifest.json").read_text())["records"]
        entries, completed = [], []
        for index, record in enumerate(records):
            name = f"response-{index}.json"
            _write(directory / name, _result())
            entry = {
                "index": index,
                "request_sha256": record["sha256"],
                "response_file": name,
                "tag": "L006/original",
                "accounted_usd": 0.01,
                "cost_status": "provider-reported USD",
                "served_model": "served",
                "provider": "provider-a",
            }
            entries.append(entry)
            completed.append({"request_sha256": record["sha256"], "status": "ok", "entry": entry})
        _write(self.ledger, {"requests": entries})
        _write(parent / "results.json", {"calls": completed})

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        """Record actual submissions and vary cache counters/routing."""
        assert kwargs["replay"] is False
        raw = json.dumps(body, separators=(",", ":")).encode()
        self.calls.append((raw, kwargs))
        ledger = json.loads(self.ledger.read_text())
        index = len(ledger["requests"])
        trial = int(kwargs["tag"].rsplit("-", 1)[1])
        result = _result(cost=0.02 if trial == 0 else 0.0, trial=trial)
        name = f"response-{index}.json"
        _write(self.ledger.parent / name, result)
        entry = {
            "index": index,
            "request_sha256": hashlib.sha256(raw).hexdigest(),
            "response_file": name,
            "tag": kwargs["tag"],
            "accounted_usd": 0.02 if trial == 0 else 8.5e-6,
            "cost_status": "provider-reported USD" if trial == 0 else "catalog estimate",
            "case_count": 1,
            "elapsed_ms": 100,
            "force_transmission": True,
            "provider": result["provider"],
            "served_model": result["model"],
        }
        ledger["requests"].append(entry)
        _write(self.ledger, ledger)
        return {"entry": entry, "result": result, "replayed": False}


@pytest.fixture
def frozen(tmp_path: Path) -> tuple[Path, Path]:
    image = pytest.importorskip("PIL.Image")
    parent = tmp_path / "parent"
    parent.mkdir()
    pages = []
    for index, (task, drawings) in enumerate(
        [("character_boundary", []), ("line_ownership", []), ("line_ownership", [{"type": "s"}])]
    ):
        name = f"obs{index}.json"
        digest = _write(parent / name, {"pixel_sha256": str(index), "selector": {"task": task}, "drawings": drawings})
        source_digest = hashlib.sha256(f"source-{index}".encode()).hexdigest()
        (parent / f"source{index}.pdf").write_bytes(f"source-{index}".encode())
        pages.append(
            {
                "id": f"p{index}",
                "observation_file": name,
                "observation_sha256": digest,
                "source_file": f"source{index}.pdf",
                "source_sha256": source_digest,
            }
        )
    records: list[dict[str, Any]] = []
    for model in MODELS:
        for arm in ARMS:
            size = int(arm.rsplit("-", 1)[1])
            buffer = io.BytesIO()
            image.new("RGB", (size, 32), "white").save(buffer, "PNG")
            url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
            for page in pages:
                name = f"request{len(records)}.json"
                body = {
                    "model": model,
                    "state": [page["id"], {"type": "image_url", "image_url": {"url": url}}],
                    "questions": {"q0": {"type": "choice"}},
                }
                digest = _write(parent / name, body)
                records.append(
                    {"request": name, "sha256": digest, "model": model, "arm": arm, "page_ids": [page["id"]]}
                )
    rates = {model: {"input": 1e-7, "output": 2e-7, "input_cache_read": 3e-8} for model in MODELS}
    catalog = _write(parent / "catalog-prices.json", {"prices": rates})
    _write(
        parent / "manifest.json",
        {
            "experiment": "L006",
            "kind": "focus",
            "models": list(MODELS),
            "pages": pages,
            "records": records,
            "catalog_sha256": catalog,
        },
    )
    output = tmp_path / "probe"
    prepare(parent, output)
    return parent, output


def test_offline_prepare_copies_exact_body_without_credentials(frozen: tuple[Path, Path]) -> None:
    parent, output = frozen
    manifest = verify(output)
    assert len(manifest["records"]) == 24
    assert not (parent / "results.json").exists()
    assert run(output)["status"] == "prepared; no calls"
    for row in manifest["records"]:
        assert (output / row["request"]).read_bytes() == (parent / row["parent_request"]).read_bytes()


def test_72_transmissions_repeat_exact_bodies_and_preserve_unknown_cache(
    frozen: tuple[Path, Path], tmp_path: Path
) -> None:
    parent, output = frozen
    client = FakeClient(tmp_path / "ledger", parent)
    state = run(output, hosted=True, client=client)
    assert len(client.calls) == MAX_CALLS == 72
    assert state["status"] == "complete"
    assert state["summary"]["cache_read_unknown"] == 24
    assert state["summary"]["cache_positive_read_transmissions"] == 48
    assert state["summary"]["reported_zero_cost_transmissions"] == 48
    assert state["summary"]["consistent_triplets"] == 24
    assert state["summary"]["effective_usd"] > 0.48
    for offset in range(0, 72, 3):
        assert len({raw for raw, _ in client.calls[offset : offset + 3]}) == 1
    before = len(client.calls)
    run(output, hosted=True, client=client)
    assert len(client.calls) == before


def test_missing_parent_success_is_explicitly_unattempted(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    parent, output = frozen
    client = FakeClient(tmp_path / "ledger", parent)
    (parent / "results.json").unlink()
    state = run(output, hosted=True, client=client)
    assert not client.calls
    assert state["summary"]["unattempted"] == 72
    assert state["summary"]["pages_per_usd"] is None


def test_resume_reconciles_transmission_from_ledger_not_local_replay(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    parent, output = frozen
    client = FakeClient(tmp_path / "ledger", parent)
    run(output, hosted=True, client=client, max_requests=1)
    wave = client.ledger.parent / "l007-wave.json"
    state = json.loads(wave.read_text())
    state["records"] = []
    _write(wave, state)
    recovered = run(output, hosted=True, client=client, max_requests=1)
    assert recovered["records"][0]["ledger_recovered"] is True
    assert recovered["records"][0]["local_replayed"] is False
    assert len(client.calls) == 2


@pytest.mark.parametrize(
    "entries",
    [
        [{"tag": PREFIX + "failure", "accounted_usd": 4.8}],
        [{"tag": PREFIX + str(i), "accounted_usd": 0.001} for i in range(72)],
    ],
)
def test_persistent_wave_counts_failed_reservations_and_call_cap(entries: list[dict[str, Any]]) -> None:
    with pytest.raises(RuntimeError, match="cap exhausted"):
        admission(entries)


def test_unknown_cost_never_becomes_complete_total() -> None:
    state = {
        "records": [
            {
                "request_sha256": "body",
                "status": "failed",
                "entry": {"index": 1, "tag": PREFIX + "failure", "accounted_usd": 0.3, "cost_status": "reserved"},
            }
        ]
    }
    summary = summarize(state)
    assert summary["effective_usd"] is None
    assert summary["unknown_cost_transmissions"] == 1
    assert summary["known_effective_subtotal_usd"] == 0


def test_changed_body_is_refused(frozen: tuple[Path, Path]) -> None:
    _, output = frozen
    record = verify(output)["records"][0]
    (output / record["request"]).write_text("{}")
    with pytest.raises(ValueError, match="Frozen body"):
        verify(output)


def test_missing_cache_rate_keeps_repeated_charge_estimate_unknown(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    parent, _output = frozen
    client = FakeClient(tmp_path / "ledger", parent)
    # Mutate the fake pricing before a fresh freeze, preserving the source manifest hash.
    catalog = json.loads((parent / "catalog-prices.json").read_text())
    for price in catalog["prices"].values():
        price.pop("input_cache_read")
    digest = _write(parent / "catalog-prices.json", catalog)
    manifest = json.loads((parent / "manifest.json").read_text())
    manifest["catalog_sha256"] = digest
    _write(parent / "manifest.json", manifest)
    fresh = tmp_path / "missing-rate"
    prepare(parent, fresh)
    state = run(fresh, hosted=True, client=client, max_requests=3)
    assert state["summary"]["effective_usd"] is None
    assert state["summary"]["unknown_cost_transmissions"] == 2
    assert state["summary"]["known_effective_subtotal_usd"] == 0.02


def test_selected_source_change_is_refused(frozen: tuple[Path, Path]) -> None:
    parent, output = frozen
    (parent / "source0.pdf").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source PDF changed"):
        verify(output)
