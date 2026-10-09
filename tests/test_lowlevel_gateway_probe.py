"""CPU-only source eligibility and matched Gateway probe checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from bench.decision_gateway import GATEWAY, LAYA_MODELS, request_identity
from bench.lowlevel_compact import compact, encoded
from bench.lowlevel_gateway_probe import BYTE_CAP, CAP, PREFIX, prepare, representations, run, verify


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    parent = tmp_path / "gateway-text"
    parent.mkdir()
    manifest: dict[str, Any] = {"experiment": "L009", "kind": "text", "pages": [], "records": []}
    for ident, text in (("a", "Alpha"), ("b", "x" * BYTE_CAP), ("c", "Charlie")):
        source = {
            "task": "character_boundary",
            "glyphs": [{"id": "g0", "text": text, "origin": [10, 20], "font": "f0", "font_name": "", "font_flags": 0}],
        }
        obs = encoded({"source": source})
        pdf = b"source " + ident.encode()
        page = {
            "id": ident,
            "source_file": f"source-{ident}.pdf",
            "source_sha256": digest(pdf),
            "observation_file": f"obs-{ident}.json",
            "observation_sha256": digest(obs),
        }
        (parent / page["source_file"]).write_bytes(pdf)
        (parent / page["observation_file"]).write_bytes(obs)
        manifest["pages"].append(page)
        for model in LAYA_MODELS:
            body = {
                "model": model,
                "state": {"observations": {"q0": compact(source)}},
                "questions": {
                    "q0": {
                        "type": "choice",
                        "instructions": "Preserve the exact source",
                        "criteria": {"join": "One", "split": "Two", "unresolved": "Unknown"},
                    }
                },
                "providerOptions": {"gateway": {"only": ["boundless"]}},
            }
            raw = encoded(body)
            name = f"request-{len(manifest['records'])}.json"
            (parent / name).write_bytes(raw)
            manifest["records"].append(
                {
                    "model": model,
                    "arm": "canonical-compact",
                    "page_ids": [ident],
                    "request": name,
                    "sha256": digest(raw),
                }
            )
    (parent / "manifest.json").write_bytes(encoded(manifest))
    (parent / "results.json").write_bytes(
        encoded({"calls": [{"status": "failed", "arm": "canonical-compact", "page_ids": ["a"]}]})
    )
    (parent / "catalog-prices.json").write_bytes(
        encoded({"prices": {model: {"input": 0, "output": 0} for model in LAYA_MODELS}})
    )
    (parent / "private-targets.json").write_text("private references must never be opened")
    monkeypatch.setattr(
        "bench.lowlevel_gateway_probe.verify_parent",
        lambda directory: json.loads((directory / "manifest.json").read_bytes()),
    )
    monkeypatch.setattr("bench.lowlevel_evidence.project", lambda obs, _arm: obs["source"])
    return parent


def test_probe_selects_unfailed_bounded_source_and_preserves_questions_without_gold(
    parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path.read_bytes

    def guarded(path: Path) -> bytes:
        assert path.name != "private-targets.json"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    before = (parent / "results.json").read_bytes()
    directory = tmp_path / "probe"
    manifest = prepare(parent, directory)
    assert manifest["pages"][0]["id"] == "c"
    assert len(manifest["records"]) == 4
    assert manifest["records"][0]["arm"] == "expanded-string"
    assert all(row["body_bytes"] <= BYTE_CAP for row in manifest["records"])
    assert (parent / "results.json").read_bytes() == before
    assert not (directory / "private-targets.json").exists()
    assert verify(directory) == manifest
    bodies = [json.loads((directory / row["request"]).read_bytes()) for row in manifest["records"]]
    assert all(body["questions"] == bodies[0]["questions"] for body in bodies)
    assert isinstance(json.loads(bodies[0]["state"])["observations"]["q0"]["glyphs"], list)
    assert isinstance(json.loads(bodies[2]["state"])["observations"]["q0"]["glyphs"], dict)
    (directory / manifest["records"][0]["request"]).write_text("changed")
    with pytest.raises(ValueError, match="body changed"):
        verify(directory)


def test_no_eligible_source_refuses_without_client(
    parent: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sibling = tmp_path / "gateway-serialized"
    sibling.mkdir()
    (sibling / "results.json").write_bytes(
        encoded({"calls": [{"status": "failed", "arm": "canonical-compact-serialized", "page_ids": ["c"]}]})
    )
    directory = tmp_path / "probe"
    manifest = prepare(parent, directory)
    assert manifest["status"] == "refused"
    assert manifest["records"] == []

    def forbidden(**_: Any) -> None:  # noqa: ANN401
        message = "Credentials must remain untouched"
        raise AssertionError(message)

    monkeypatch.setattr("bench.lowlevel_gateway_probe.GatewayDecisionClient", forbidden)
    assert run(directory)["status"] == "refused"


class MockClient:
    """Ledger-backed CPU mock with one retained model failure."""

    gateway = GATEWAY

    def __init__(self, directory: Path, *, fail: bool = False) -> None:
        """Create an isolated mock ledger."""
        directory.mkdir()
        self.ledger = directory / "ledger.json"
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int) -> dict[str, Any]:
        """Retain success or safe failure without network access."""
        assert tag.startswith(PREFIX)
        assert max_body_bytes == BYTE_CAP
        self.calls.append(body)
        entries = json.loads(self.ledger.read_bytes())["requests"] if self.ledger.exists() else []
        entry: dict[str, Any] = {
            "index": len(entries),
            "tag": tag,
            "requested_model": body["model"],
            "gateway": GATEWAY,
            "request_sha256": digest(encoded(body)),
            "request_identity_sha256": request_identity(encoded(body)),
            "accounted_usd": 0.3,
            "cost_status": "reserved",
        }
        if self.fail and body["model"] == LAYA_MODELS[0]:
            entry.update(
                error="HTTP 422", http_error_diagnostic={"error_types": ["invalid_request"], "locations": [["state"]]}
            )
            entries.append(entry)
            self.ledger.write_bytes(encoded({"requests": entries}))
            message = "mock HTTP failure"
            raise RuntimeError(message)
        result = {
            "answers": {
                "q0": {"type": "choice", "choice": "join", "probabilities": {"join": 1, "split": 0, "unresolved": 0}}
            },
            "usage": {"cost": 0.002},
        }
        entry.update(response_file="mock.json", accounted_usd=0.002, cost_status="provider-reported USD")
        entries.append(entry)
        self.ledger.write_bytes(encoded({"requests": entries}))
        return {"result": result, "entry": entry, "replayed": False}


def test_probe_preserves_failed_reservation_diagnostics_and_never_retries(parent: Path, tmp_path: Path) -> None:
    directory = tmp_path / "probe"
    prepare(parent, directory)
    client = MockClient(tmp_path / "ledger", fail=True)
    results = run(directory, client=client)
    assert len(client.calls) == 3
    first = results["calls"][0]
    assert first["entry"]["http_error_diagnostic"]["locations"] == [["state"]]
    assert first["cost"]["effective_usd"] is None
    assert first["entry"]["accounted_usd"] == 0.3
    assert results["completed_bodies"] == 3
    run(directory, client=client)
    assert len(client.calls) == 3


def test_probe_respects_persistent_wave_cap_without_transmission(parent: Path, tmp_path: Path) -> None:
    directory = tmp_path / "probe"
    prepare(parent, directory)
    client = MockClient(tmp_path / "ledger")
    client.ledger.write_bytes(
        encoded({"requests": [{"tag": PREFIX + "old", "accounted_usd": CAP, "response_file": "old.json"}]})
    )
    results = run(directory, client=client)
    assert not client.calls
    assert results["budget_exhausted"]
    assert results["completed_bodies"] == 0
    assert all(row["status"] == "unattempted" for row in results["calls"])


@pytest.mark.usefixtures("parent")
def test_round_trip_preserves_numeric_unicode_values_and_glyph_order() -> None:
    source: dict[str, Any] = {
        "task": "character_boundary",
        "glyphs": [
            {"id": "g1", "text": "Ω", "origin": [1.25, -2], "font": "f0"},
            {"id": "g0", "text": "0", "origin": [3, 4], "font": "f0"},
        ],
    }
    body = {"state": {"observations": {"q0": compact(source)}}, "questions": {"q0": {"instructions": "same"}}}
    variants = representations(body, {"source": source})
    expanded = json.loads(variants["expanded-string"]["state"])["observations"]["q0"]
    assert encoded(expanded) == encoded(source)
    source["glyphs"].reverse()
    with pytest.raises(ValueError, match="independent source round trip"):
        representations(body, {"source": source})
