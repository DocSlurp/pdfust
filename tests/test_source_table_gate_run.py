"""Gate execution uses fake transport and excludes ambiguous reference correctness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from bench.ocr_rolling import immutable
from bench.source_table_gate import CRITERIA, MODELS, gate_body, variants
from bench.source_table_gate_run import TAG_PREFIX, evaluate, run, sha, verify


@pytest.fixture
def frozen(tmp_path: Path) -> tuple[Path, Path]:
    """Freeze presence-only bodies and postfreeze labels without native OCR or transport."""
    directory = tmp_path / "gates"
    directory.mkdir()
    pages: list[dict[str, Any]] = [
        {"id": name, "words": []} for name in ("positive", "negative", "ambiguous", "native")
    ]
    immutable(directory / "source-frozen.json", {"pages": pages})
    records: list[dict[str, Any]] = [{"id": "native", "route": "native_vector", "calls": 0}]
    for page in pages[:-1]:
        visible = {
            "coordinates": "display",
            "page_size": [0, 0, 1, 1],
            "source_words": [],
            "image_mapping": {"pixels": [1, 1]},
            "candidate_tables": {},
        }
        for model_index, model in enumerate(MODELS):
            for variant in variants():
                body = gate_body(
                    {"model": model, "state": [json.dumps(visible), {"image_url": {"url": "pixels"}}]}, variant
                )
                name = f"{page['id']}-{model_index}-{variant['name']}.json"
                immutable(directory / name, body)
                records.append(
                    {
                        "id": page["id"],
                        "route": "hosted_presence_gate",
                        "model": model,
                        "variant": variant["name"],
                        "arm": "image512",
                        "request": name,
                        "sha256": sha(directory / name),
                        "choices": list(CRITERIA),
                    }
                )
    immutable(
        directory / "manifest.json",
        {
            "pages": len(pages),
            "source_sha256": sha(directory / "source-frozen.json"),
            "models": list(MODELS),
            "records": records,
            "wall_seconds": 0,
            "cpu_seconds": 0,
            "peak_rss_bytes": 0,
            "measurement": "test",
        },
    )
    targets = tmp_path / "targets.json"
    targets.write_text(
        json.dumps(
            [
                {"id": p["id"], "kind": kind}
                for p, kind in zip(pages, ("borderless", "prose", "ambiguous", "ruled-control"), strict=True)
            ]
        )
    )
    return directory, targets


class Client:
    """Keep a fake persistent ledger without credentials or networking."""

    def __init__(self, directory: Path, *, fail: bool = False) -> None:
        """Configure transport success or a charged failed request."""
        self.ledger = directory / "ledger.json"
        self.calls = 0
        self.fail = fail

    def request(self, body: dict[str, Any], *, tag: str, max_body_bytes: int) -> dict[str, Any]:
        """Retain synthetic measured charges, including failures."""
        assert max_body_bytes == 750_000
        self.calls += 1
        entries = json.loads(self.ledger.read_text())["requests"] if self.ledger.exists() else []
        entry = {
            "index": len(entries),
            "tag": tag,
            "requested_model": body["model"],
            "accounted_usd": 0.000001,
            "provider_reported_usd": 0.000001,
            "elapsed_ms": 2,
            "request_sha256": hashlib.sha256(json.dumps(body, separators=(",", ":")).encode()).hexdigest(),
        }
        if not self.fail:
            entry["response_file"] = "mock"
        entries.append(entry)
        self.ledger.write_text(json.dumps({"requests": entries}))
        if self.fail:
            message = "Simulated charged transport error"
            raise RuntimeError(message)
        return {
            "entry": entry,
            "replayed": False,
            "result": {
                "usage": {"cost": 0.000001},
                "answers": {
                    "q0": {
                        "type": "choice",
                        "choice": "table_present",
                        "probabilities": {key: float(key == "table_present") for key in CRITERIA},
                    }
                },
            },
        }


def test_complete_run_and_no_retries(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    """Retain all gate costs, unscored decisions, and unchanged repeat results."""
    directory, targets = frozen
    client = Client(tmp_path)
    result = run(directory, targets, client)
    assert client.calls == 12
    assert result["unique_requests"] == 12
    assert result["effective_usd"] == pytest.approx(0.000012)
    for cohort in result["cohorts"].values():
        assert cohort["slices"]["borderless"]["correct"] == 1
        assert cohort["slices"]["prose"]["table_present"] == 1
        assert cohort["ambiguous_unscored_pages"] == 1
        assert cohort["native_zero_call_pages"] == 1
        assert all(row["correct"] is None for row in cohort["rows"] if row["kind"] == "ambiguous")
    run(directory, targets, client)
    assert client.calls == 12


def test_failure_stops_models_and_retains_charge(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    """A charged failure is accounted once and prevents further calls for its model."""
    directory, targets = frozen
    client = Client(tmp_path, fail=True)
    result = run(directory, targets, client)
    assert client.calls == len(MODELS)
    assert result["effective_usd"] == pytest.approx(0.000002)
    assert set(result["stopped_models"]) == set(MODELS)
    run(directory, targets, client)
    assert client.calls == len(MODELS)


def test_hash_tampering_refused_upfront(frozen: tuple[Path, Path]) -> None:
    """Changed source bodies fail before transport or reference scoring."""
    directory, targets = frozen
    manifest = verify(directory)
    record = next(r for r in manifest["records"] if r["route"] == "hosted_presence_gate")
    (directory / record["request"]).write_text("{}")
    with pytest.raises(ValueError, match="hash"):
        evaluate(directory, targets, [])


def test_persistent_prefix_cap_refuses_before_transport(frozen: tuple[Path, Path], tmp_path: Path) -> None:
    """A prior reservation under the gate prefix prevents an over-cap request."""
    directory, targets = frozen
    client = Client(tmp_path)
    client.ledger.write_text(
        json.dumps(
            {"requests": [{"tag": TAG_PREFIX + "prior", "accounted_usd": 0.30, "response_file": "prior-success"}]}
        )
    )
    result = run(directory, targets, client)
    assert client.calls == 0
    assert result["budget_stopped"]
    assert result["unique_requests"] == 0
