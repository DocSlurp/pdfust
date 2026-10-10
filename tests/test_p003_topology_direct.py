"""One-stage native choices never synthesize evidence for unasked owners."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_topology_direct as direct
from bench import p003_topology_run as runner
from test_p003_topology_chunks import MODEL, results
from test_p003_topology_hybrid import conflicted
from test_p003_topology_run import URL, config, fixtures


def test_direct_cells_can_choose_other_row_in_single_stage(tmp_path: Path) -> None:
    mixed = conflicted(tmp_path)
    bodies = direct.batches(mixed, MODEL, URL, image=False)
    criteria = bodies[0]["questions"]["w0"]["criteria"]
    assert "t0r2c1" in criteria
    evidence = json.loads(bodies[0]["state"])
    assert evidence["ownership_stage"] == "direct_cell"
    assert evidence["direct_candidate_policy"]["scores_are_probabilities"] is False
    audit = direct.assemble(mixed, bodies, results(bodies, "t0r2c1"))
    assert audit["assignment_choices"]["id0"] == "t0r2c1"
    assert audit["assignment_choices"]["id1"] == "t0r2c1"
    assert audit["source_conserved"]
    ids = [i for t in audit["state"]["tables"] for c in t["cells"] for i in c["source_ids"]]
    assert set(ids) == {f"id{i}" for i in range(6)}
    assert len(ids) == 6
    assert audit["direct"]["decisions"]["id0"]["raw_probabilities"]["t0r2c1"] == 1


def test_direct_abstention_raw_probabilities_and_tampering(tmp_path: Path) -> None:
    mixed = conflicted(tmp_path)
    bodies = direct.batches(mixed, MODEL, URL, image=False)
    raw = results(bodies, "unresolved")
    audit = direct.assemble(mixed, bodies, raw)
    assert audit["assignment_provenance"]["id0"] == "explicit_baseline_abstention_fallback"
    changed = deepcopy(bodies)
    del changed[0]["questions"]["w0"]["criteria"]["t0r2c1"]
    with pytest.raises(ValueError, match="immutable"):
        direct.assemble(mixed, changed, raw)
    with pytest.raises(ValueError, match="duplicate"):
        direct.collect(mixed, bodies * 2, raw * 2)
    with pytest.raises(ValueError, match="incomplete"):
        direct.collect(mixed, [], [])


def test_direct_runner_prepare_reports_single_stage_bound(tmp_path: Path) -> None:
    source_dir, topo_dir, output = tmp_path / "source", tmp_path / "topology", tmp_path / "output"
    original, topology = fixtures(source_dir, topo_dir)
    # Omit compatible baseline assignments, retaining source words as original prose.
    original["regions"][0]["state"]["tables"] = []
    original["regions"][0]["state"]["unresolved_ids"] = [w["id"] for w in original["source"]["words"]]
    original["tables"] = []
    output.mkdir()
    result = runner.process_page(
        original,
        topology,
        source_dir,
        topo_dir,
        {"generation_provider": "anthropic"},
        output,
        config(chunked_inventory=True, geometry_first=True, ownership_protocol="direct_cell", prepare_only=True),
    )
    assert result["topology_status"] == "prepared_retained_baseline"
    assert result["topology_calls"] == []
