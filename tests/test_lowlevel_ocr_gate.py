"""No-network natural OCR gate freeze, alias and literal-reference contracts."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest
from bench.lowlevel_ocr_alignment import _digest
from bench.lowlevel_ocr_gate import (
    ARMS,
    CHOICES,
    MAX_CALLS,
    MODELS,
    admission,
    image_variant,
    labels,
    parse_response,
    prepare,
    run,
    verify,
)


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, separators=(",", ":")))


def _png(width: int, height: int) -> bytes:
    image = pytest.importorskip("PIL.Image")
    buffer = io.BytesIO()
    image.new("RGB", (width, height), "white").save(buffer, "PNG")
    return buffer.getvalue()


def _result(choice: str = "agree") -> dict[str, Any]:
    return {
        "answers": {
            "q0": {
                "type": "choice",
                "choice": choice,
                "probabilities": {key: 0.8 if key == choice else 0.1 for key in CHOICES},
            }
        },
        "usage": {"input_tokens": 100, "output_tokens": 5, "cost": 0.001},
        "model": "served",
        "provider": "fake-provider",
    }


class FakeClient:
    """Retain fake successful provider records without using credentials."""

    def __init__(self, path: Path) -> None:
        """Create a fresh shared fake ledger."""
        path.mkdir()
        self.ledger = path / "ledger.json"
        self.calls = 0
        _write(self.ledger, {"requests": []})

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        """Replay known identities and account only fresh fake transmissions."""
        digest = hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest()
        ledger = json.loads(self.ledger.read_text())
        for entry in ledger["requests"]:
            if entry["request_sha256"] == digest:
                return {"entry": entry, "result": _result(), "replayed": True}
        self.calls += 1
        entry = {
            "index": len(ledger["requests"]),
            "request_sha256": digest,
            "tag": kwargs["tag"],
            "response_file": f"response-{self.calls}.json",
            "accounted_usd": 0.001,
            "cost_status": "provider-reported USD",
            "case_count": 1,
            "elapsed_ms": 10,
        }
        _write(self.ledger.parent / entry["response_file"], _result())
        ledger["requests"].append(entry)
        _write(self.ledger, ledger)
        return {"entry": entry, "result": _result(), "replayed": False}


@pytest.fixture
def frozen(tmp_path: Path) -> tuple[Path, Path]:
    parent = tmp_path / "source"
    parent.mkdir()
    sources, refs = [], []
    for i in range(9):
        ident = "edison-date" if i == 1 else f"private-fixture-{i}"
        raw = _png(80 if i < 4 else 600, 30)
        path = parent / f"image-{i}.png"
        path.write_bytes(raw)
        evidence: dict[str, Any] = {
            "fixture_id": ident,
            "native_words_text": f"Visible {i}",
            "image": {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()},
        }
        evidence["evidence_sha256"] = _digest(evidence)
        sources.append(evidence)
        refs.append(
            {
                "fixture_id": ident,
                "visual_text": None if i == 8 else f"Visible {i}",
                "review_note": "Private review text never sent.",
                "review_status": "single-review-source-aware",
            }
        )
    _write(parent / "evidence.json", sources)
    _write(parent / "review-references.json", refs)
    catalog = tmp_path / "catalog.json"
    _write(catalog, {"prices": {m: {"input": 1e-7, "output": 2e-7} for m in MODELS}})
    output = tmp_path / "gate"
    prepare(parent, output, catalog=catalog)
    return parent, output


def test_source_only_payloads_and_deduplicated_actual_resolution(frozen: tuple[Path, Path]) -> None:
    _, output = frozen
    manifest = verify(output)
    assert manifest["configuration_count"] == 108
    assert manifest["unique_body_count"] == 4 * (4 + 5 * 3)
    assert run(output)["status"] == "prepared; no calls"
    for row in manifest["records"]:
        body = json.loads((output / row["request"]).read_text())
        assert set(json.loads(body["state"][0])) == {"native_words_text"}
        assert set(body["questions"]["q0"]["criteria"]) == set(CHOICES)
        serialized = json.dumps(body)
        assert "private-fixture" not in serialized
        assert "review_status" not in serialized
        assert "review_note" not in serialized
        assert str(output) not in serialized
        assert "join" not in body["questions"]["q0"]["criteria"]
    for case in manifest["cases"][:4]:
        assert [v["pixels"] for v in case["variants"]] == [[80, 30]] * 3


def test_no_upscaling_and_native_keeps_actual_pixels() -> None:
    for arm in ARMS:
        _, pixels = image_variant(_png(80, 30), arm)
        assert pixels == [80, 30]
    assert image_variant(_png(600, 30), "rgb128")[1] == [128, 6]
    assert image_variant(_png(600, 30), "rgb512")[1] == [512, 26]
    assert image_variant(_png(600, 30), "native")[1] == [600, 30]


def test_single_review_contextual_and_unavailable_are_separate(frozen: tuple[Path, Path]) -> None:
    _, output = frozen
    reviewed = labels(output, verify(output))
    assert reviewed["edison-date"]["tier"] == "contextual-zero-O"
    assert reviewed["private-fixture-8"]["expected"] is None
    assert reviewed["private-fixture-8"]["tier"] == "unavailable"
    assert reviewed["private-fixture-0"]["expected"] == "agree"


def test_provider_calls_count_unique_bodies_not_configuration_aliases(
    frozen: tuple[Path, Path], tmp_path: Path
) -> None:
    _, output = frozen
    client = FakeClient(tmp_path / "ledger")
    state = run(output, hosted=True, client=client)
    assert state["status"] == "complete"
    assert client.calls == verify(output)["unique_body_count"]
    assert len(state["observations"]) == 108
    assert state["summary"]["physical_transmissions"] == client.calls
    assert state["summary"]["primary_scored_aliases"] == 7 * 12
    assert state["summary"]["effective_usd"] == pytest.approx(client.calls * 0.001)
    run(output, hosted=True, client=client)
    assert client.calls == verify(output)["unique_body_count"]


def test_slices_recover_after_missing_local_checkpoint(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    _, output = frozen
    client = FakeClient(tmp_path / "ledger")
    run(output, hosted=True, client=client, max_requests=2)
    wave = client.ledger.parent / "l008-wave.json"
    state = json.loads(wave.read_text())
    state["calls"] = []
    _write(wave, state)
    resumed = run(output, hosted=True, client=client, max_requests=1)
    assert client.calls == 3
    assert sum(r.get("replayed", False) for r in resumed["calls"]) == 2


@pytest.mark.parametrize(
    "mutation",
    [
        {"choice": "join"},
        {"probabilities": {"agree": True, "disagree": 0, "unresolved": 0}},
        {"probabilities": {"agree": 0.1, "disagree": 0.2, "unresolved": 0.1}},
        {"probabilities": {"agree": 0.1, "disagree": 0.8, "unresolved": 0.1}},
    ],
)
def test_strict_gate_distributions_reject_other_tasks_and_invalid_scores(mutation: dict[str, Any]) -> None:
    response = _result()
    response["answers"]["q0"].update(mutation)
    with pytest.raises(ValueError, match=r"Gate|probability"):
        parse_response(response)


def test_tied_gate_probability_abstains() -> None:
    response = _result()
    response["answers"]["q0"]["probabilities"] = {"agree": 0.5, "disagree": 0.5, "unresolved": 0}
    assert parse_response(response)["choice"] == "unresolved"


def test_changed_review_is_refused_without_changing_model_payload(frozen: tuple[Path, Path]) -> None:
    _, output = frozen
    (output / "review-references.json").write_text("[]")
    with pytest.raises(ValueError, match="reference bytes changed"):
        verify(output)


def test_wave_admission_retains_failed_reservations() -> None:
    with pytest.raises(RuntimeError, match="wave cap"):
        admission([{"tag": "L008/failed", "accounted_usd": 4.8}])
    with pytest.raises(RuntimeError, match="wave cap"):
        admission([{"tag": "L008/old", "accounted_usd": 0.001}] * MAX_CALLS)


def test_alias_dimensions_cannot_claim_false_resolution(frozen: tuple[Path, Path]) -> None:
    _, output = frozen
    manifest = json.loads((output / "manifest.json").read_text())
    manifest["records"][0]["aliases"][0]["pixels"] = [1200, 1200]
    _write(output / "manifest.json", manifest)
    with pytest.raises(ValueError, match="Alias image dimensions"):
        verify(output)


def test_literal_comparison_does_not_use_raw_glyph_text_or_typographic_folding(frozen: tuple[Path, Path]) -> None:
    _, output = frozen
    manifest = verify(output)
    refs = json.loads((output / "review-references.json").read_text())
    refs[0]["visual_text"] = "  Visible\n0  "
    refs[2]["visual_text"] = "visible 2"
    _write(output / "review-references.json", refs)
    # Bind the deliberate local unit-test reference revision; verify() still protects real freezes.
    manifest["references_sha256"] = hashlib.sha256((output / "review-references.json").read_bytes()).hexdigest()
    reviewed = labels(output, manifest)
    assert reviewed["private-fixture-0"]["expected"] == "agree"
    assert reviewed["private-fixture-2"]["expected"] == "disagree"


def test_existing_large_shared_ledger_has_explicit_64mib_admission(tmp_path: Path) -> None:
    from bench.lowlevel_ocr_gate import _entries  # noqa: PLC0415 - isolated admission regression

    client = FakeClient(tmp_path / "ledger")
    client.ledger.write_text('{"requests": [], "padding": "' + "x" * 8_000_001 + '"}')
    assert _entries(client) == []
