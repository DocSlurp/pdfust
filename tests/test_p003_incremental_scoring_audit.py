"""Incremental attribution stays separate from inherited pipeline output."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_vision_regions as vision
from bench.p003_incremental_scoring_audit import admit, primary
from bench.silver import canonical, sha, write_json


def fixture(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    table = {"row_count": 1, "col_count": 1, "values": [["literal"]], "spans": []}
    rows = [
        {"id": "a", "status": "ok", "topology_status": "completed", "tables": [table]},
        {"id": "b", "status": "ok", "topology_status": "not_applicable", "tables": [table]},
    ]
    report = {"config": {"processor": "p003_topology_source"}, "results": rows}
    manifest = {"pages": [{"id": "a"}, {"id": "b"}]}
    write_json(tmp_path / "manifest.json", manifest)
    manifest_sha = sha((tmp_path / "manifest.json").read_bytes())
    frozen = {"config": report["config"], "manifest_sha256": manifest_sha, "records": manifest["pages"]}
    artifacts = []
    for row in rows:
        write_json(tmp_path / (row["id"] + "-result.json"), row)
        artifacts.append(
            {
                "id": row["id"],
                "result_sha256": sha((tmp_path / (row["id"] + "-result.json")).read_bytes()),
                "tables_sha256": sha(canonical(row["tables"])),
                "source_sha256": None,
            }
        )
    write_json(tmp_path / "report.json", report)
    evaluation = {
        "runs": [
            {
                "evaluation_scope": "incremental ownership conditional on frozen topology and source",
                "report_sha256": sha((tmp_path / "report.json").read_bytes()),
                "manifest_sha256": manifest_sha,
                "artifacts": artifacts,
                "successful_incremental_composition_quality": {"page_scores": [{"id": "a"}, {"id": "b"}]},
            }
        ]
    }
    for name, value in [("frozen", frozen), ("evaluation", evaluation)]:
        write_json(tmp_path / (name + ".json"), value)
    entry = {"primary_predictions_sha256": sha(canonical(primary(report)[0]))}
    for key, name in [
        ("report", "report"),
        ("evaluation", "evaluation"),
        ("frozen", "frozen"),
        ("run_manifest", "manifest"),
    ]:
        entry[key] = str(tmp_path / (name + ".json"))
        entry[key + "_sha256"] = sha((tmp_path / (name + ".json")).read_bytes())
    return entry, report


def test_ownership_skipped_baseline_gets_no_credit(tmp_path: Path) -> None:
    entry, _ = fixture(tmp_path)
    _, _, predictions, key = admit(entry)
    assert key == "successful_incremental_composition_quality"
    assert len(predictions) == 2
    assert len(predictions[0]["tables"]) == 1
    assert predictions[1]["tables"] == []


def test_changed_actual_output_rejected(tmp_path: Path) -> None:
    entry, _ = fixture(tmp_path)
    (tmp_path / "a-result.json").write_text("{}")
    with pytest.raises(ValueError, match="Actual page output"):
        admit(entry)


def test_no_fullpipeline_scope_admission(tmp_path: Path) -> None:
    entry, _ = fixture(tmp_path)

    value = json.loads((tmp_path / "evaluation.json").read_bytes())
    value["runs"][0]["evaluation_scope"] = "complete pipeline"
    write_json(tmp_path / "evaluation.json", value)
    entry["evaluation_sha256"] = sha((tmp_path / "evaluation.json").read_bytes())
    with pytest.raises(ValueError, match="Incremental scope"):
        admit(entry)


def test_header_partial_keeps_selected_but_not_fixed_tables() -> None:
    report = {
        "config": {"processor": "p003_header_decision"},
        "results": [
            {
                "id": "a",
                "status": "error",
                "tables": [{"values": [["chosen"]]}],
                "fixed_state": {"tables": [{"values": [["old"]]}]},
                "model_credited_table_count": 1,
            }
        ],
    }
    before = deepcopy(report)
    rows, _ = primary(report)
    assert rows[0]["status"] == "ok"
    assert rows[0]["tables"] == [{"values": [["chosen"]]}]
    assert report == before


def test_unknown_processor_refused() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        primary({"config": {"processor": "p003_gate"}})


def test_candidate_only_selected_regions_and_failed_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[list[dict[str, Any]]] = []

    def compose(regions: list[dict[str, Any]], _viewport: list[int]) -> dict[str, Any]:
        observed.append(regions)
        return {"tables": [{"values": [[r["literal"]]]} for r in regions]}

    monkeypatch.setattr(vision, "compose", compose)
    page = {
        "id": "a",
        "status": "ok",
        "ranking_status": "completed",
        "viewport": [0, 0, 100, 100],
        "ranking_regions": [
            {"index": 0, "ranking_status": "selected"},
            {"index": 1, "ranking_status": "unresolved"},
            {"index": 2, "ranking_status": "duplicate"},
        ],
        "transcription_regions": [{"literal": "selected"}, {"literal": "old unresolved"}, {"literal": "old duplicate"}],
    }
    failed = {**page, "id": "b", "status": "error", "ranking_status": "failed"}
    rows, _ = primary({"config": {"processor": "p003_candidate_choice"}, "results": [page, failed]})
    assert rows[0]["tables"] == [{"values": [["selected"]]}]
    assert rows[1]["tables"] == []
    assert len(observed) == 1
    assert [r["literal"] for r in observed[0]] == ["selected"]


def test_failed_and_skipped_ownership_omit_inherited_tables() -> None:
    rows = [
        {"id": str(i), "status": status, "topology_status": outcome, "tables": [{"values": [["old"]]}]}
        for i, (status, outcome) in enumerate([("ok", "not_applicable"), ("error", "failed"), ("error", "completed")])
    ]
    predictions, _ = primary({"config": {"processor": "p003_topology_source"}, "results": rows})
    assert len(predictions) == 3
    assert all(not p["tables"] for p in predictions)
