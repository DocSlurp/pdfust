"""Exact geometric aliases expand quality without inventing cost or timing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from bench.image_axes_report import markdown, snapshot, transmission_stats


def artifacts(path: Path) -> Path:
    path.mkdir()
    base = {
        "model": "model",
        "scope": "page",
        "arm": "gray8-height-200",
        "offset": 0,
        "case_ids": ["opaque0", "opaque1"],
        "request_sha256": "samebody",
        "request_bytes": 10,
        "configuration": {"mode": "gray8", "axis": "height", "target": 200},
        "images": [
            {"pixels": [155, 200], "total_pixels": 31000, "bytes": 200, "png_bit_depth": 8, "png_color_type": 0}
        ],
    }
    pending = {
        **base,
        "arm": "gray8-height-300",
        "request_sha256": "otherbody",
        "configuration": {"mode": "gray8", "axis": "height", "target": 300},
    }
    alias = {
        "model": "model",
        "scope": "page",
        "arm": "gray8-longest-200",
        "offset": 0,
        "canonical_arm": "gray8-height-200",
        "case_ids": base["case_ids"],
        "request_sha256": "samebody",
    }
    manifest = {
        "models": ["model"],
        "batches": [base, pending],
        "geometric_aliases": [alias],
        "prices": {},
        "refusals": [],
        "declared_sizes": [200, 300],
        "declared_axes": ["height", "longest"],
        "declared_representations": ["gray8"],
        "preparation": {"cpu_seconds": 0.1},
    }
    retained = {
        **base,
        "status": "ok",
        "replayed": False,
        "entry": {
            "index": 1,
            "provider_reported_usd": 0,
            "elapsed_ms": 1000,
            "catalog_rates": {"input": 0.000001, "output": 0},
        },
        "usage": {"cost": 0, "input_tokens": 1000, "output_tokens": 0},
        "observations": [
            {
                "case_id": "opaque0",
                "answer": {"choice": "A"},
                "score": {"region_exact": True, "source_conservation": True, "record_f1": 1.0, "slot_exact": True},
            },
            {
                "case_id": "opaque1",
                "answer": {"choice": "unresolved"},
                "score": {"region_exact": False, "source_conservation": True, "record_f1": 0.0, "slot_exact": False},
            },
        ],
    }
    (path / "manifest.json").write_text(json.dumps(manifest))
    (path / "results.json").write_text(json.dumps({"batches": [retained]}))
    return path


def test_alias_quality_and_unmeasured_cost_timing(tmp_path: Path) -> None:
    result = snapshot(artifacts(tmp_path / "data"))
    rows = {r["arm"]: r for r in result["rows"]}
    original = rows["gray8-height-200"]
    alias = rows["gray8-longest-200"]
    pending = rows["gray8-height-300"]
    assert alias["metrics"] == original["metrics"]
    assert alias["alias_cases"] == 2
    assert alias["configuration"]["axis"] == "longest"
    assert alias["transmissions"]["unique_requests"] == 0
    assert alias["transmissions"]["effective_usd"] is None
    assert alias["transmissions"]["http_elapsed_ms"] is None
    assert pending["measured_cases"] == 0
    assert pending["declared_cases"] == pending["unmeasured_cases"] == 2
    assert result["completed_unique_batches"] == 1
    assert result["provider_observations"]["unique_requests"] == 1
    assert result["provider_observations"]["effective_usd"] == 0.001
    assert original["transmissions"]["pages_per_usd"] == 2000
    assert original["transmissions"]["pages_per_http_minute"] == 120
    assert alias["metrics"]["slot_exact"] == {"n": 2, "sum": 1, "mean": 0.5}
    assert "gray8-height-300" in markdown([result])
    assert "provider-cache evidence" in markdown([result])


def test_changed_alias_or_retained_inventory_is_rejected(tmp_path: Path) -> None:
    path = artifacts(tmp_path / "data")
    manifest = json.loads((path / "manifest.json").read_bytes())
    manifest["geometric_aliases"][0]["request_sha256"] = "differentbody"
    (path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="identical"):
        snapshot(path)


def test_replay_keeps_quality_but_no_new_paid_observation(tmp_path: Path) -> None:
    path = artifacts(tmp_path / "data")
    retained = json.loads((path / "results.json").read_bytes())
    retained["batches"][0]["replayed"] = True
    (path / "results.json").write_text(json.dumps(retained))
    result = snapshot(path)
    original = next(r for r in result["rows"] if r["arm"] == "gray8-height-200")
    assert original["measured_cases"] == original["replayed_cases"] == 2
    assert result["provider_observations"]["unique_requests"] == 0
    assert result["provider_observations"]["effective_usd"] is None


def test_missing_usage_is_unknown_and_positive_reported_cost_wins() -> None:
    row: dict[str, Any] = {"model": "model", "arm": "arm", "case_ids": ["id"], "entry": {"index": 1}}
    result = transmission_stats([row], {})
    assert result["effective_usd"] is None
    assert result["unknown_cost_requests"] == 1
    assert result["http_elapsed_ms"] is None
    row["entry"]["provider_reported_usd"] = 0.02
    assert transmission_stats([row], {})["effective_usd"] == 0.02


def test_heldout_directory_is_guarded(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"[Hh]eld|[Pp]rotected"):
        snapshot(tmp_path / "heldout-silver")
