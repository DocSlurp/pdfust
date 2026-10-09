"""CPU mock transport, route identity, cost/denominator and no-retry checks."""

from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench.lowlevel_evidence import digest, encode
from bench.lowlevel_natural import annotate
from bench.lowlevel_natural import prepare as source_prepare
from bench.lowlevel_natural_run import ARMS, ROUTES, identity, prepare, rate_summary, report, request, run, verify

SOURCE = Path(__file__).parent / "assets/real_world/senate-expenditures.pdf"


@pytest.fixture(scope="module")
def source(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("natural-run") / "source"
    manifest = source_prepare(SOURCE, directory, count=12)
    annotate(
        directory,
        [
            {
                "id": page["id"],
                "choice": "join",
                "evidence": "Test reference, not natural gold",
                "uncertainty": "Synthetic scorer check",
                "scope_references": {"record": {"choice": "join"}, "description": {"choice": "unresolved"}},
            }
            for page in manifest["pages"]
        ],
    )
    return directory


@pytest.fixture(scope="module")
def prepared(source: Path) -> Path:
    parent = source.parent
    catalogs = {}
    for provider in ("openrouter", "vercel"):
        path = parent / f"catalog-{provider}.json"
        path.write_text(
            json.dumps(
                {"prices": {model: {"input": 1e-7, "output": 0.0} for serving, model in ROUTES if serving == provider}}
            )
        )
        catalogs[provider] = path
    directory = parent / "matrix"
    prepare(source, directory, catalogs)
    return directory


class Client:
    """Mock a root-owned ledger client without credential reads or network use."""

    def __init__(self, ledger: Path, provider: str, *, fail: bool = False) -> None:
        """Attach only an injected local ledger."""
        self.ledger = ledger
        self.gateway = provider
        self.fail = fail
        self.invocations = 0

    def request(self, body: dict[str, Any], *, tag: str, **options: Any) -> dict[str, Any]:  # noqa: ANN401
        """Simulate admission, replay and reserved transport failure."""
        assert options["replay"] is True
        self.invocations += 1
        data = json.loads(self.ledger.read_bytes()) if self.ledger.exists() else {"requests": []}
        body_hash = digest(encode(body))
        known = next(
            (
                row
                for row in data["requests"]
                if row.get("gateway", "openrouter") == self.gateway and row["request_sha256"] == body_hash
            ),
            None,
        )
        response = {
            "answers": {
                "q0": {
                    "type": "choice",
                    "choice": "join",
                    "probabilities": {"join": 0.8, "split": 0.1, "unresolved": 0.1},
                }
            },
            "usage": {"input_tokens": 100, "output_tokens": 0, "cost": 0.0},
        }
        if known:
            assert known.get("response_file")
            assert not known.get("error")
            return {"result": response, "entry": known, "replayed": True}
        entry = {
            "index": len(data["requests"]),
            "tag": tag,
            "gateway": self.gateway,
            "request_sha256": body_hash,
            "requested_model": body["model"],
            "accounted_usd": options["reservation_usd"] if self.fail else 0.00001,
            "cost_status": "reserved" if self.fail else "catalog estimate",
            "elapsed_ms": 2500.0,
        }
        entry.update({"error": "HTTP 500"} if self.fail else {"response_file": "mock-response.json"})
        data["requests"].append(entry)
        self.ledger.write_text(json.dumps(data))
        if self.fail:
            message = "Test mock failure"
            raise RuntimeError(message)
        return {"result": response, "entry": entry, "replayed": False}


def clients(tmp_path: Path, *, fail: bool = False) -> dict[str, Client]:
    ledger = tmp_path / "ledger.json"
    return {provider: Client(ledger, provider, fail=fail) for provider in ("openrouter", "vercel")}


def copy_matrix(prepared: Path, tmp_path: Path) -> Path:
    directory = tmp_path / "matrix"
    shutil.copytree(prepared, directory)
    return directory


def test_complete_source_matrix_and_exact_gateway_translation(prepared: Path) -> None:
    manifest = verify(prepared)
    assert len(manifest["records"]) == 12 * 4 * 5
    page = manifest["pages"][0]
    observation = json.loads((prepared / page["observation_file"]).read_bytes())
    for arm in ARMS:
        original = request(observation, "openrouter", ROUTES[0][1], arm)
        gateway = request(observation, "vercel", "liquid/d1", arm)
        assert gateway["state"] == original["state"][0]
        assert gateway["images"] == [original["state"][1]["image_url"]["url"]]
        assert gateway["questions"] == original["questions"]
    assert identity("openrouter", "same body") != identity("vercel", "same body")
    summary = report(prepared)
    assert summary["planned_logical_records"] == 240
    assert all(row["completed_pairs"] == 0 and row["planned_pairs"] == 12 for row in summary["summaries"])


def test_bounded_resume_and_scope_scores(prepared: Path, tmp_path: Path) -> None:
    directory = copy_matrix(prepared, tmp_path)
    transport = clients(tmp_path)
    first = run(directory, clients=transport, max_requests=2)
    second = run(directory, clients=transport, max_requests=2)
    assert len(first["calls"]) == 2
    assert len(second["calls"]) == 4
    assert sum(client.invocations for client in transport.values()) == 4
    scored = report(directory)
    assert sum(row["completed_pairs"] for row in scored["summaries"]) == 4
    assert sum(row["full_reference_matches"] for row in scored["summaries"]) == 4
    assert all(
        row["scope_reference_matches"] == 0 for row in scored["summaries"] if row["arm"].startswith("description")
    )
    assert scored["effective_usd_complete"] == pytest.approx(0.00004)
    assert all(cost["reported_usd"] == 0 for cost in scored["costs"])
    assert all(cost["basis"] == "catalog estimate" for cost in scored["costs"])
    with pytest.raises(ValueError, match="shared-ledger"):
        run(directory, clients=transport, max_requests=0)


def test_failed_body_never_retried_and_unknown_reservation_retained(prepared: Path, tmp_path: Path) -> None:
    directory = copy_matrix(prepared, tmp_path)
    transport = clients(tmp_path, fail=True)
    run(directory, clients=transport, max_requests=1)
    first_ledger = json.loads((tmp_path / "ledger.json").read_bytes())
    first_hash = first_ledger["requests"][0]["request_sha256"]
    for client in transport.values():
        client.fail = False
    run(directory, clients=transport, max_requests=2)
    final = json.loads((tmp_path / "ledger.json").read_bytes())
    assert sum(entry["request_sha256"] == first_hash for entry in final["requests"]) == 1
    assert (tmp_path / "L011-model-stops.json").exists()
    scored = report(directory)
    assert scored["effective_usd_complete"] is None
    assert scored["unknown_cost_count"] == 1
    assert scored["known_effective_usd_subtotal"] == pytest.approx(0.00002)
    assert scored["costs"][0]["ledger_accounted_usd"] == pytest.approx(0.3)


def test_persistent_five_dollar_cap_includes_other_freeze_failures(prepared: Path, tmp_path: Path) -> None:
    directory = copy_matrix(prepared, tmp_path)
    transport = clients(tmp_path)
    (tmp_path / "ledger.json").write_text(
        json.dumps(
            {
                "requests": [
                    {
                        "index": 0,
                        "tag": "L011/prior-failure",
                        "accounted_usd": 4.8,
                        "request_sha256": "unrelated",
                        "error": "HTTP500",
                    }
                ]
            }
        )
    )
    result = run(directory, clients=transport, max_requests=2)
    assert result["wave_accounted_usd"] == pytest.approx(4.8)
    assert sum(client.invocations for client in transport.values()) == 0
    assert all(row["status"] == "unattempted" for row in result["calls"])
    scored = report(directory)
    assert all(row["completed_pairs"] == 0 for row in scored["summaries"])


def test_missing_inventory_refused_before_transport(prepared: Path, tmp_path: Path) -> None:
    directory = copy_matrix(prepared, tmp_path)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    manifest["records"].pop()
    (directory / "manifest.json").write_text(json.dumps(manifest))
    transport = clients(tmp_path)
    with pytest.raises(ValueError, match="incomplete"):
        run(directory, clients=transport)
    assert sum(client.invocations for client in transport.values()) == 0


def test_rates_exclude_replays_and_unknowns_preserve_quality_denominators(prepared: Path, tmp_path: Path) -> None:
    directory = copy_matrix(prepared, tmp_path)
    run(directory, clients=clients(tmp_path), max_requests=2)
    initial = report(directory)
    assert initial["fresh_invocation"]["fresh_region_inputs"] == 2
    assert initial["fresh_invocation"]["fresh_regions_per_usd"] == pytest.approx(100000)
    assert initial["fresh_invocation"]["api_only_regions_per_minute"] == pytest.approx(24)
    assert sum(row["fresh_region_inputs"] for row in initial["summaries"]) == 2
    assert initial["source_page_count"] == 1

    # An exact local replay carries historical usage/charges but adds no new API
    # region or duration. Scores still use its returned independent region data.
    path = directory / "results.json"
    saved = json.loads(path.read_bytes())
    saved["calls"][0]["replayed"] = True
    saved["calls"][0]["entry"]["tag"] = "L006/historical"
    path.write_text(json.dumps(saved))
    replayed = report(directory)
    assert replayed["effective_usd_complete"] == pytest.approx(0.00001)
    assert replayed["historical_replay_input_pricing"]["effective_usd_complete"] == pytest.approx(0.00001)
    assert replayed["all_priced_input_entries"]["effective_usd_complete"] == pytest.approx(0.00002)
    assert replayed["fresh_invocation"]["fresh_region_inputs"] == 1
    assert replayed["fresh_invocation"]["api_only_regions_per_minute"] == pytest.approx(24)
    assert sum(row["completed_pairs"] for row in replayed["summaries"]) == 2
    assert sum(row["replayed_region_records"] for row in replayed["summaries"]) == 1

    # No tokens/time means unknown rates, even though both answers still score.
    saved["calls"][1]["response"]["usage"] = {}
    saved["calls"][1]["entry"].update(cost_status="reserved", accounted_usd=0.3, elapsed_ms=None)
    path.write_text(json.dumps(saved))
    unknown = report(directory)
    assert unknown["effective_usd_complete"] is None
    assert unknown["fresh_invocation"]["fresh_regions_per_usd"] is None
    assert unknown["fresh_invocation"]["api_only_regions_per_minute"] is None
    assert unknown["fresh_invocation"]["unknown_api_duration_count"] == 1
    assert unknown["unknown_cost_count"] == 1
    assert sum(row["completed_pairs"] for row in unknown["summaries"]) == 2
    assert sum(row["planned_pairs"] for row in unknown["summaries"]) == 240


def test_rate_zero_cost_is_na_and_duplicate_entries_are_not_inputs() -> None:
    call = {
        "provider": "vercel",
        "entry": {"index": 7, "tag": "L011/test", "elapsed_ms": 1000},
        "page_ids": ["one-region"],
        "status": "ok",
        "replayed": False,
        "cost": {"effective_usd": 0.0},
    }
    result = rate_summary([call, deepcopy(call)])
    assert result["fresh_api_requests"] == result["fresh_region_inputs"] == 1
    assert result["fresh_regions_per_usd"] is None
    assert result["regions_per_usd_status"] == "n/a zero cost"
    assert result["api_only_regions_per_minute"] == pytest.approx(60)
    replay = deepcopy(call)
    replay["replayed"] = True
    assert rate_summary([replay])["fresh_region_inputs"] == 0
