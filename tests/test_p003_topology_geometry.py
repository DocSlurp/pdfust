"""Geometry control abstains without fabricating probabilities or source strings."""

import json
from pathlib import Path

import pytest
from bench import p003_topology_geometry as geometry
from bench import p003_topology_ownership as ownership
from bench import p003_topology_run as runner
from test_p003_topology_run import archives, config, fixtures


def test_geometry_same_frozen_inventory_single_owner_and_scores(tmp_path: Path) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology")
    work = runner.prepare_page(
        original, topology, tmp_path / "topology", {"generation_provider": "anthropic"}, config()
    )
    audit = geometry.place(work["crops"][0]["snapshot"])
    assert audit["geometry_policy"]["scores_are_probabilities"] is False
    assert audit["geometry_policy"]["quality_verified"] is False
    ids = [i for t in audit["state"]["tables"] for c in t["cells"] for i in c["source_ids"]]
    ids += audit["state"]["unresolved_ids"]
    assert sorted(ids) == sorted(w["id"] for w in original["source"]["words"])
    assert len(set(ids)) == len(ids)
    assert '"probabilities":' not in json.dumps(audit)
    assert "prior-generated-only" not in json.dumps(audit)
    assert geometry.place(work["crops"][0]["snapshot"]) == audit


def test_geometry_tie_and_boundary_abstain_outside_remains_literal(tmp_path: Path) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology")
    work = runner.prepare_page(
        original, topology, tmp_path / "topology", {"generation_provider": "anthropic"}, config()
    )
    crop = work["crops"][0]
    packet = json.loads(crop["snapshot"].packet_json)
    packet["source"]["words"] = [
        {"id": "tie", "text": "whole tie", "bbox": [45, 5, 55, 15]},
        {"id": "boundary", "text": "whole boundary", "bbox": [5, -1, 15, 1]},
        {"id": "outside", "text": "whole outside", "bbox": [110, 5, 120, 15]},
    ]
    plan = ownership.Plan(ownership._dump(packet))  # noqa: SLF001
    audit = geometry.place(plan)
    assert audit["abstained_ids"] == ["tie", "boundary"]
    assert audit["outside_ids"] == ["outside"]
    assert audit["state"]["unresolved_ids"] == ["tie", "boundary", "outside"]
    assert audit["assignments"][0]["margin"] == 0


def test_geometry_run_requires_no_client_and_preserves_historical_cost(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, topology = tmp_path / "source", tmp_path / "topology"
    a, b = archives(source, topology)

    def forbidden() -> None:
        pytest.fail("Geometry must not construct a credential-bearing client")

    monkeypatch.setattr(runner, "P003DecisionClient", forbidden)
    output = tmp_path / "geometry"
    report = runner.run(source, topology, a, b, output, config(geometry_only=True))
    assert report["incremental_ownership"]["returned_calls"] == 0
    assert report["incremental_ownership"]["attempts"] == []
    assert report["incremental_ownership"]["maximum_new_ownership_calls_from_preflight"] == 0
    assert report["source_generation_report"]["effective_usd"] == 5
    assert report["pages_per_minute"] is None
    assert report["incremental_ownership"]["status_counts"] == {"completed": 16}
    assert (output / "p0-topology-0-geometry-audit.json").exists()
    assert "p003_topology_geometry.py" in json.loads((output / "frozen.json").read_bytes())["code_sha256"]


def test_residual_region_order_can_differ_from_global_source_order(tmp_path: Path) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology")
    extra = [
        {"id": "z", "text": "literal z", "bbox": [110, 120, 120, 130]},
        {"id": "a", "text": "literal a", "bbox": [130, 120, 140, 130]},
    ]
    original["source"]["words"].extend(extra)
    region = original["region_plan"]["regions"][0]
    region["source_ids"].extend(["a", "z"])
    region["source"]["words"].extend(reversed(extra))
    original["regions"][0]["state"]["unresolved_ids"].extend(["a", "z"])
    work = runner.prepare_page(
        original, topology, tmp_path / "topology", {"generation_provider": "anthropic"}, config()
    )
    assert [w["id"] for w in work["plan"]["regions"][0]["source"]["words"]] == ["a", "z"]
    states = work["states"]
    states[work["crops"][0]["id"]] = geometry.place(work["crops"][0]["snapshot"])["state"]
    assert runner.compose(work["plan"], states)["unresolved_ids"] == ["z", "a"]


def test_source_bands_are_explicit_and_uniform_control_stays_unchanged(tmp_path: Path) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology")
    work = runner.prepare_page(
        original, topology, tmp_path / "topology", {"generation_provider": "anthropic"}, config()
    )
    snapshot = work["crops"][0]["snapshot"]
    uniform = geometry.place(snapshot)
    adaptive = geometry.place(snapshot, band_mode="source")
    assert geometry.place(snapshot, band_mode="uniform") == uniform
    assert "band_mode" not in uniform["geometry_policy"]
    assert adaptive["geometry_policy"]["band_mode"] == "source"
    assert len(adaptive["geometry_policy"]["bands"]) == 1
    assert adaptive["geometry_policy"]["bands"][0]["y_edges"] != [0, 100 / 3, 200 / 3, 100]
    assert adaptive["snapshot_sha256"] == uniform["snapshot_sha256"]
    assert sorted(a["source_id"] for a in adaptive["assignments"]) == sorted(
        a["source_id"] for a in uniform["assignments"]
    )
