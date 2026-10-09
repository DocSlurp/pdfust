"""Source-only deterministic controls without answer metadata in request prompts."""

import base64
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest
from bench.decision_gateway import ENDPOINT as TYPESAFE_ENDPOINT
from bench.decision_gateway import request_identity
from bench.decision_gateway_vision import ENDPOINT as NATIVE_ENDPOINT
from bench.lowlevel_gateway_sanity import EDGE, MAX_BODY_BYTES, WAVE_LIMIT, controls, prepare, report, run, verify
from PIL import Image


def test_controls_are_deterministic_opposite_pixels_and_identical_prompts() -> None:
    rows = controls()
    assert rows == controls()
    assert [row["expected"] for row in rows] == ["circle", "square", "unresolved", "unresolved"]
    bodies = [row["canonical_body"] for row in rows]
    assert all(body["questions"] == bodies[0]["questions"] and body["state"] == bodies[0]["state"] for body in bodies)
    hashes = []
    for row in rows[:3]:
        raw = base64.b64decode(row["canonical_body"]["images"][0].split(",", 1)[1], validate=True)
        assert len(raw) == row["png_bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["png_sha256"]
        hashes.append(row["png_sha256"])
        with Image.open(io.BytesIO(raw)) as bitmap:
            assert bitmap.size == (EDGE, EDGE)
            assert bitmap.getpixel((0, 0)) == (255, 255, 255)
            assert bitmap.getpixel((EDGE // 2, EDGE // 2)) == (
                (255, 255, 255) if row["control"] == "blank" else (0, 0, 0)
            )
    assert len(set(hashes)) == len(hashes)
    assert "images" not in bodies[-1]
    for row in rows:
        for body in (row["canonical_body"], row["native_body"]):
            assert "expected" not in body
            assert "control" not in body
            assert "scope" not in body


@pytest.fixture
def frozen(tmp_path: Path) -> Path:
    catalog = tmp_path / "prices.json"
    catalog.write_text(json.dumps({"prices": {"liquid/d1": {"input": 0.04e-6, "output": 0}}}))
    directory = tmp_path / "sanity"
    prepare(directory, catalog=catalog)
    return directory


def test_prepare_matches_original_driver_bytes_and_refuses_overwrite(frozen: Path) -> None:
    manifest = verify(frozen)
    expected = []
    for control in controls():
        for protocol, field in (("typesafe", "canonical_body"), ("native", "native_body")):
            raw = json.dumps(control[field], separators=(",", ":"), allow_nan=False).encode()
            index = len(expected)
            assert (frozen / f"request-{index:02d}.json").read_bytes() == raw
            expected.append((control["control"], protocol))
    assert [(row["control"], row["protocol"]) for row in manifest["records"]] == expected
    result_path = frozen / "results.json"
    result_path.write_text('{"calls":[]}')
    before = result_path.read_bytes()
    prepare(frozen)
    assert result_path.read_bytes() == before
    (frozen / "request-00.json").write_text("different")
    with pytest.raises(ValueError, match="bytes changed"):
        prepare(frozen)
    assert (frozen / "request-00.json").read_text() == "different"
    assert result_path.read_bytes() == before


class MockClient:
    """Shared-ledger protocol mock retaining one unknown HTTP failure."""

    def __init__(self, ledger: Path, protocol: str, *, fail: bool = False) -> None:
        """Declare the exact endpoint without credentials."""
        self.ledger = ledger
        self.endpoint = TYPESAFE_ENDPOINT if protocol == "typesafe" else NATIVE_ENDPOINT
        self.fail = fail
        self.sent: list[dict[str, Any]] = []

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int) -> dict[str, Any]:
        """Retain protocol-independent errors with endpoint identities."""
        self.sent.append(body)
        assert max_body_bytes == MAX_BODY_BYTES
        raw = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
        entries = json.loads(self.ledger.read_bytes())["requests"] if self.ledger.exists() else []
        entry: dict[str, Any] = {
            "index": len(entries),
            "tag": tag,
            "gateway": "vercel",
            "endpoint": self.endpoint,
            "request_sha256": hashlib.sha256(raw).hexdigest(),
            "request_identity_sha256": request_identity(raw, endpoint=self.endpoint),
            "accounted_usd": 0.3,
            "cost_status": "reserved",
            "catalog_rates": {"input": 0.04e-6, "output": 0},
            "elapsed_ms": 0,
        }
        if self.fail:
            entry.update(error="HTTP400", http_error_diagnostic={"error_types": ["invalid_request_error"]})
            entries.append(entry)
            self.ledger.write_text(json.dumps({"requests": entries}))
            message = "mock transmission failure"
            raise RuntimeError(message)
        choice = "unresolved"
        entry.update(
            accounted_usd=0.001,
            provider_reported_usd=0.001,
            cost_status="provider-reported USD",
            response_file="mock.json",
        )
        entries.append(entry)
        self.ledger.write_text(json.dumps({"requests": entries}))
        result = {
            "answers": {
                "q0": {"type": "choice", "choice": choice, "probabilities": {"circle": 0, "square": 0, "unresolved": 1}}
            },
            "usage": {"input_tokens": 20, "cost": 0.001},
        }
        return {"result": result, "entry": entry, "replayed": False}


def test_run_protocol_stops_unknown_reservations_and_resume_are_independent(frozen: Path, tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    clients = {
        protocol: MockClient(ledger, protocol, fail=protocol == "typesafe") for protocol in ("typesafe", "native")
    }
    results = run(frozen, clients=clients)
    assert len(clients["typesafe"].sent) == 1
    assert len(clients["native"].sent) == 4
    assert results["protocol_stops"] == ["typesafe"]
    assert results["calls"][0]["cost"]["effective_usd"] is None
    assert results["calls"][0]["entry"]["accounted_usd"] == 0.3
    run(frozen, clients=clients)
    assert len(clients["typesafe"].sent) == 1
    assert len(clients["native"].sent) == 4
    assert len(json.loads((frozen / "results.json").read_bytes())["execution_sessions"]) == 2
    summary = report(frozen)
    assert summary["completed_bodies"] == 5
    assert all(value == "image consumption remains unverified" for value in summary["protocol_outcomes"].values())
    assert summary["rows"][1]["elapsed_ms"] == 0


def test_report_defaults_cpu_only_and_rejects_wrong_menu(frozen: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(**_: Any) -> None:  # noqa: ANN401
        pytest.fail("A report must never create a credentialed client")

    monkeypatch.setattr("bench.lowlevel_gateway_sanity.GatewayDecisionClient", forbidden)
    monkeypatch.setattr("bench.lowlevel_gateway_sanity.GatewayVisionDecisionClient", forbidden)
    manifest = verify(frozen)
    row = {
        **manifest["records"][0],
        "status": "ok",
        "choice": "circle",
        "result": {
            "answers": {
                "q0": {"type": "choice", "choice": "join", "probabilities": {"join": 1, "split": 0, "unresolved": 0}}
            }
        },
    }
    (frozen / "results.json").write_text(json.dumps({"calls": [row], "resources": {"cpu_seconds": 1}}))
    before = (frozen / "results.json").read_bytes()
    summary = report(frozen)
    assert summary["rows"][0]["status"] == "parser refusal"
    assert summary["rows"][0]["elapsed_ms"] is None
    assert (frozen / "results.json").read_bytes() == before
    assert "not PDF extraction quality" in (frozen / "report.md").read_text()


def test_persistent_wave_cap_prevents_all_transmission(frozen: Path, tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps({"requests": [{"tag": "L017/older", "accounted_usd": WAVE_LIMIT, "response_file": "retained.json"}]})
    )
    clients = {protocol: MockClient(ledger, protocol) for protocol in ("typesafe", "native")}
    results = run(frozen, clients=clients)
    assert results["budget_exhausted"]
    assert all(not client.sent for client in clients.values())
    assert results["completed_bodies"] == 0


def test_retained_endpoint_identity_tampering_refuses_report(frozen: Path, tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    clients = {protocol: MockClient(ledger, protocol) for protocol in ("typesafe", "native")}
    run(frozen, clients=clients)
    path = frozen / "results.json"
    results = json.loads(path.read_bytes())
    results["calls"][0]["entry"]["request_identity_sha256"] = "wrong endpoint"
    path.write_text(json.dumps(results))
    with pytest.raises(ValueError, match="endpoint identity"):
        report(frozen)
