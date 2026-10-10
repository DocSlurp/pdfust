"""Conservative deterministic ownership and exact native dispute replay."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_topology_chunks as chunks
from bench import p003_topology_hybrid as hybrid
from bench import p003_topology_run as runner
from bench.pipeline_assembly import _clean_table
from test_p003_topology_chunks import MODEL, results
from test_p003_topology_run import URL, config, fixtures


def prepared(tmp_path: Path) -> hybrid.Hybrid:
    source_dir, topo_dir = tmp_path / "source", tmp_path / "topology"
    source, topo = fixtures(source_dir, topo_dir)
    plan = runner.prepare_page(
        source, topo, topo_dir, {"generation_provider": "anthropic"}, config(chunked_inventory=True)
    )
    crop = plan["crops"][0]
    return hybrid.prepare(crop["snapshot"], source["tables"])


def conflicted(tmp_path: Path) -> hybrid.Hybrid:
    mixed = prepared(tmp_path)
    value = chunks.packet(mixed.snapshot)
    tables = deepcopy(json.loads(mixed.audit_json)["baseline_state"]["tables"])
    tables[0]["cells"][0]["source_ids"], tables[0]["cells"][1]["source_ids"] = (
        tables[0]["cells"][1]["source_ids"],
        tables[0]["cells"][0]["source_ids"],
    )
    box = tables[0]["bbox"]
    tables[0] = _clean_table(tables[0], {w["id"]: w for w in value["source"]["words"]})
    tables[0]["bbox"] = box
    return hybrid.prepare(mixed.snapshot, tables)


def test_clear_words_need_no_model_or_probability_receipts(tmp_path: Path) -> None:
    mixed = prepared(tmp_path)
    admission = json.loads(mixed.audit_json)
    assert len(admission["locked"]) == 6
    assert not admission["disputed_ids"]
    assert hybrid.batches(mixed, MODEL, URL, image=False) == []
    audit = hybrid.assemble(mixed, [], [], [], [])
    assert audit["state"]["tables"][0]["values"] == admission["baseline_state"]["tables"][0]["values"]
    assert audit["geometry_locked_count"] == 6
    assert audit["source_conserved"]
    assert all("probabilities" not in d for d in admission["locked"].values())
    assert admission["policy"]["scores_are_probabilities"] is False


def test_baseline_conflict_disputed_and_abstention_explicitly_retains_it(tmp_path: Path) -> None:
    mixed = conflicted(tmp_path)
    admission = json.loads(mixed.audit_json)
    assert admission["disputed_ids"] == ["id0", "id1"]
    assert len(admission["locked"]) == 4
    bodies = hybrid.batches(mixed, MODEL, URL, image=False)
    assert len(bodies) == 1
    assert len(bodies[0]["questions"]) == 2
    raw = results(bodies, "unresolved")
    rows = hybrid.collect(mixed, bodies, raw)
    assert hybrid.batches(mixed, MODEL, URL, rows=rows, image=False) == []
    audit = hybrid.assemble(mixed, bodies, raw, [], [])
    assert audit["state"]["tables"][0]["values"] == admission["baseline_state"]["tables"][0]["values"]
    assert audit["assignment_provenance"]["id0"] == "explicit_baseline_abstention_fallback"
    assert audit["rows"]["decisions"]["id0"]["raw_probabilities"]["unresolved"] == 1


def test_changed_missing_duplicate_and_corrupted_receipts_refused(tmp_path: Path) -> None:
    mixed = conflicted(tmp_path)
    bodies = hybrid.batches(mixed, MODEL, URL, image=False)
    raw = results(bodies, "t0r0")
    rows = hybrid.collect(mixed, bodies, raw)
    changed = deepcopy(rows)
    changed["decisions"]["id0"]["raw_probabilities"]["t0r0"] = 0
    with pytest.raises(ValueError, match="raw evidence"):
        hybrid.batches(mixed, MODEL, URL, rows=changed, image=False)
    with pytest.raises(ValueError, match="incomplete"):
        hybrid.collect(mixed, [], [])
    with pytest.raises(ValueError, match="duplicate"):
        hybrid.collect(mixed, bodies * 2, raw * 2)
    cells = hybrid.batches(mixed, MODEL, URL, rows=rows, image=False)
    cellraw = results(cells, "t0r0c0")
    cellraw[-1]["answers"]["w1"]["choice"] = "invented"
    before = mixed.audit_json
    with pytest.raises(ValueError, match="raw maximum"):
        hybrid.assemble(mixed, bodies, raw, cells, cellraw)
    assert mixed.audit_json == before


def test_unexpressible_original_topology_preserved_without_calls(tmp_path: Path) -> None:
    mixed = prepared(tmp_path)
    value = chunks.packet(mixed.snapshot)
    baseline = json.loads(mixed.audit_json)["baseline_state"]["tables"]
    topology = {"tables": [{"bbox": [0, 0, 1000, 1000], "row_count": 2, "col_count": 3, "mergedspans": []}]}
    response = {
        "choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"answers": {"q0": topology}})}}]
    }
    changed = chunks.freeze(value["source"], response, [0, 0, 100, 100], URL)
    guarded = hybrid.prepare(changed, baseline)
    assert hybrid.batches(guarded, MODEL, URL, image=False) == []
    audit = hybrid.assemble(guarded, [], [], [], [])
    assert audit["baseline_structure_retained"]
    assert audit["state"]["tables"] == baseline


def test_runnable_hybrid_avoids_client_and_preserves_baseline_provenance(tmp_path: Path) -> None:
    source_dir, topo_dir, output = tmp_path / "source", tmp_path / "topology", tmp_path / "output"
    original, topology = fixtures(source_dir, topo_dir)
    output.mkdir()

    class NoRequests:
        def request(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError

    result = runner.process_page(
        original,
        topology,
        source_dir,
        topo_dir,
        {"generation_provider": "anthropic"},
        output,
        config(chunked_inventory=True, geometry_first=True),
        NoRequests(),
    )
    assert result["topology_status"] == "completed"
    assert result["topology_calls"] == []
    assert result["calls"] == original["calls"]
    assert result["source_conserved"]
    assert result["tables"][0]["values"] == original["tables"][0]["values"]
    retained = json.loads((output / "p0-topology-0-hybrid-admission.json").read_bytes())
    assert len(retained["locked"]) == 6
