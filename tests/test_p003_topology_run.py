"""Synthetic retained archives and mocked ownership calls; no PDF or API access."""

from __future__ import annotations

import base64
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import p003_topology_run as runner
from bench import pipeline_run as pipeline
from bench import pipeline_vision_transcription as transcription
from bench.generalization_report import verify_output
from bench.generalization_run import _table_bounds
from bench.pipeline_assembly import _clean_table
from bench.pipeline_regions import _source, compose
from bench.pipeline_source_order import render_source
from bench.silver import sha, write_json

MODEL = "cloudflare/clef-omni"
URL = "data:image/png;base64," + base64.b64encode(b"synthetic-crop-pixels").decode()


def config(**kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
    return {"model": MODEL, "max_questions": 16, "run_id": "mock", "baseline_source_order": "original", **kwargs}


def fixtures(source_dir: Path, topology_dir: Path, *, crops: int = 1) -> tuple[dict[str, Any], dict[str, Any]]:
    source_dir.mkdir()
    topology_dir.mkdir()
    words = []
    tables = []
    proposals = []
    for index in range(crops):
        local = []
        for i, text in enumerate(["Label", "Value", "name", "10", "cont", "20"]):
            ident = f"id{index * 6 + i}"
            word = {
                "id": ident,
                "text": text,
                "bbox": [
                    10 + index * 100 + i % 2 * 60,
                    10 + i // 2 * 25,
                    20 + index * 100 + i % 2 * 60,
                    15 + i // 2 * 25,
                ],
                "line": [i // 2],
            }
            words.append(word)
            local.append(word)
        table = {
            "row_count": 3,
            "col_count": 2,
            "cells": [{"source_ids": [w["id"]], "role": "unknown"} for w in local],
            "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(3) for c in range(2)],
        }
        tables.append(_clean_table(table, {w["id"]: w for w in words}))
        bounds = [index * 100, 0, index * 100 + 100, 100]
        response = {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "answers": {
                                    "q0": {
                                        "tables": [
                                            {
                                                "bbox": [0, 0, 1000, 1000],
                                                "matrix": [["prior-generated-only", "x"], ["y", "z"], ["p", "q"]],
                                                "mergedspans": [],
                                            }
                                        ]
                                    }
                                }
                            }
                        )
                    },
                }
            ]
        }
        body = transcription.request("anthropic/claude-haiku-5.5", URL, bounds, 8192)
        body["provider"] = {"only": ["anthropic"], "allow_fallbacks": False, "require_parameters": True}
        write_json(topology_dir / f"p0-request-{index}.json", body)
        proposals.append(
            {
                "index": index,
                "request_index": index,
                "viewport": bounds,
                "status": "ok",
                "detector_box": {"bbox": bounds, "label": "Table", "confidence": 0.9},
                "transcription_response": response,
                "tables": transcription.parse(response, bounds)["tables"],
                "image": {
                    "image_sha256": sha(base64.b64decode(URL.split(",", 1)[1])),
                    "image_bytes": 21,
                    "image_viewport": bounds,
                },
                "request": {"body_sha256": sha(json.dumps(body, separators=(",", ":")).encode())},
            }
        )
    raw = {"page_size": [200, 200], "words": words, "vector_candidates": []}
    clean = _source(raw)
    old_state = {"id": "c0", "tables": tables, "unresolved_ids": [], "mechanism": "baseline"}
    region = {"id": "r0", "source": clean, "source_ids": [w["id"] for w in words], "bbox": [0, 0, 200, 200]}
    plan = {**clean, "regions": [region], "coordinate_space": "display_global"}
    state = compose(plan, {"r0": old_state})
    _table_bounds(raw, state)
    original = {
        "id": "p0",
        "pdf_sha256": "frozen-pdf",
        "status": "ok",
        "source": raw,
        "region_plan": {k: v for k, v in plan.items() if k != "words"},
        "regions": [{"id": "r0", "state": old_state}],
        "tables": state["tables"],
        "unresolved_ids": [],
        "source_conserved": True,
        "original_rotation": 0,
        "rotation_normalized": False,
        "wall_seconds": 10,
        "calls": [{"entry": {"index": 7, "accounted_usd": 1.0}}],
    }
    _table_bounds(raw, old_state)
    write_json(source_dir / "p0-result.json", original)
    write_json(source_dir / "p0-structure.json", state)
    (source_dir / "p0.md").write_text(pipeline.markdown(render_source(raw, region), old_state))
    topo = {
        "id": "p0",
        "pdf_sha256": "frozen-pdf",
        "status": "ok",
        "viewport": [0, 0, 200, 200],
        "original_rotation": 0,
        "transcription_regions": proposals,
        "source_conserved": False,
        "route": "vision_transcription_regions",
        "coverage": "unverified",
        "proposal_count": crops,
        "unresolved_ids": [],
        "layout_detection": {
            "device": "cpu",
            "type": "result",
            "viewport": [0, 0, 200, 200],
            "boxes": [p["detector_box"] for p in proposals],
        },
        "calls": [{"entry": {"index": 17, "accounted_usd": 2.0}}],
    }
    from bench.generalization_vision_regions import compose as vision_compose  # noqa: PLC0415

    topostate = vision_compose(proposals, topo["viewport"])
    topo["tables"] = topostate["tables"]
    write_json(topology_dir / "p0-result.json", topo)
    write_json(topology_dir / "p0-structure.json", topostate)
    (topology_dir / "p0.md").write_text(transcription.markdown(topostate))
    return original, topo


class Client:
    """Isolated fake shared ledger, with explicit charged malformed/failing attempts."""

    def __init__(self, directory: Path, *, fail_at: int | None = None, malformed_at: int | None = None) -> None:
        """Create a temporary fake ledger and controlled outcome."""
        self.ledger = directory / "mock-ledger.json"
        self.directory = directory
        self.bodies: list[dict[str, Any]] = []
        self.fail_at, self.malformed_at = fail_at, malformed_at
        write_json(self.ledger, {"requests": []})

    def request(self, body: dict[str, Any], **options: Any) -> dict[str, Any]:  # noqa: ANN401
        """Return native choices without any credential or network access."""
        assert options["replay"] is False
        assert len(body["questions"]) <= 16
        self.bodies.append(deepcopy(body))
        data = json.loads(body["state"][0])
        answers = {}
        for key, word in data["words"].items():
            index = int(word["id"][2:]) % 6
            choice = f"t0r{index // 2}" if data["stage"] == "rows" else f"t0r{index // 2}c{index % 2}"
            answers[key] = {
                "type": "choice",
                "choice": choice,
                "probabilities": {opt: float(opt == choice) for opt in body["questions"][key]["criteria"]},
            }
        ledger = json.loads(self.ledger.read_bytes())
        entry = {
            "index": len(ledger["requests"]),
            "tag": options["tag"],
            "accounted_usd": 0.01,
            "provider_reported_usd": 0.01,
            "cost_status": "mock-reported",
        }
        ledger["requests"].append(entry)
        write_json(self.ledger, ledger)
        if len(self.bodies) == self.fail_at:
            message = "synthetic transport failure"
            raise OSError(message)
        if len(self.bodies) == self.malformed_at:
            answers[next(iter(answers))]["choice"] = "invented-owner"
        return {"result": {"answers": answers}, "entry": entry, "replayed": False}


def test_complete_incremental_ownership_source_ids_and_prior_provenance(tmp_path: Path) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology")
    output = tmp_path / "out"
    output.mkdir()
    client = Client(tmp_path)
    result = runner.process_page(
        original,
        topology,
        tmp_path / "source",
        tmp_path / "topology",
        {"generation_provider": "anthropic"},
        output,
        config(),
        client,
    )
    assert result["topology_status"] == "completed"
    assert result["source_conserved"] is True
    assert result["calls"] == original["calls"]
    assert len(result["topology_calls"]) == 2
    assert "prior-generated-only" not in json.dumps(client.bodies)
    assert result["tables"][0]["values"] == [["Label", "Value"], ["name", "10"], ["cont", "20"]]
    assert result["tables"][0]["cells"][0]["source_ids"] == ["id0"]
    assert verify_output(output, result, processor="regions", source_order="original")["conserved"] is True
    audit = json.loads((output / "p0-topology-0-audit.json").read_bytes())
    assert audit["missing_source_text_recoverable"] is False


@pytest.mark.parametrize("mode", ["transport", "malformed"])
def test_late_second_crop_failure_retains_original_bytes(tmp_path: Path, mode: str) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology", crops=2)
    before = {suffix: (tmp_path / "source" / f"p0{suffix}").read_bytes() for suffix in (".md", "-structure.json")}
    output = tmp_path / "out"
    output.mkdir()
    client = Client(
        tmp_path, fail_at=4 if mode == "transport" else None, malformed_at=4 if mode == "malformed" else None
    )
    result = runner.process_page(
        original,
        topology,
        tmp_path / "source",
        tmp_path / "topology",
        {"generation_provider": "anthropic"},
        output,
        config(),
        client,
    )
    assert result["topology_status"] == "failed_retained_baseline"
    assert result["status"] == "ok"
    assert result["tables"] == original["tables"]
    assert result["topology_regions"][0]["status"] == "discarded_atomic_failure"
    assert len(json.loads(client.ledger.read_bytes())["requests"]) == 4
    assert all((output / f"p0{suffix}").read_bytes() == data for suffix, data in before.items())


@pytest.mark.parametrize("mode", ["rotation", "native", "word_boundary", "empty"])
def test_preflight_refusals_do_not_call_model(tmp_path: Path, mode: str) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology")
    if mode == "rotation":
        original["rotation_normalized"] = True
    elif mode == "native":
        original["source"]["vector_candidates"] = [{"bbox": [0, 0, 100, 100]}]
    elif mode == "word_boundary":
        original["source"]["words"][0]["bbox"] = [95, 10, 105, 15]
        original["region_plan"]["regions"][0]["source"]["words"][0]["bbox"] = [95, 10, 105, 15]
    else:
        original["source"]["words"] = []
        original["region_plan"]["regions"][0]["source"]["words"] = []
        original["region_plan"]["regions"][0]["source_ids"] = []
        original["regions"][0]["state"] = {"id": "c0", "tables": [], "unresolved_ids": []}
    output = tmp_path / "out"
    output.mkdir()
    client = Client(tmp_path)
    result = runner.process_page(
        original,
        topology,
        tmp_path / "source",
        tmp_path / "topology",
        {"generation_provider": "anthropic"},
        output,
        config(),
        client,
    )
    assert result["topology_status"] == "unsupported_retained_baseline"
    assert client.bodies == []


def test_prepare_only_and_prior_error_never_make_requests(tmp_path: Path) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology")
    output = tmp_path / "out"
    output.mkdir()
    result = runner.process_page(
        original,
        topology,
        tmp_path / "source",
        tmp_path / "topology",
        {"generation_provider": "anthropic"},
        output,
        config(prepare_only=True),
    )
    assert result["topology_status"] == "prepared_retained_baseline"
    assert result["topology_calls"] == []
    assert (output / "p0-topology-0-row-0-request.json").exists()
    original["status"], original["error"] = "error", "original error"
    result = runner.process_page(
        original, topology, tmp_path / "source", tmp_path / "topology", {}, output, config(), Client(tmp_path)
    )
    assert result["status"] == "error"
    assert result["error"] == "original error"
    assert result["topology_status"] == "baseline_failed_skipped"


def archives(source: Path, topology: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Build complete synthetic16 archives with independently supplied local code maps."""
    original, topo = fixtures(source, topology)
    source_config = {"processor": "regions", "source_order": "original"}
    topology_config = {"processor": "vision_regions", "generation_provider": "anthropic"}
    records, source_rows, topology_rows = [], [], []
    for i in range(16):
        ident = f"p{i}"
        record = {"id": ident, "pdf_path": "unused-synthetic.pdf", "pdf_sha256": "frozen-pdf", "page_number": i}
        records.append(record)
        a, b = deepcopy(original), deepcopy(topo)
        a["id"], b["id"] = ident, ident
        for directory, row in ((source, a), (topology, b)):
            write_json(directory / f"{ident}-result.json", row)
            for suffix in ("-structure.json", ".md"):
                (directory / f"{ident}{suffix}").write_bytes((directory / f"p0{suffix}").read_bytes())
        (topology / f"{ident}-request-0.json").write_bytes((topology / "p0-request-0.json").read_bytes())
        source_rows.append(a)
        topology_rows.append(b)
    maps = []
    root = Path(runner.__file__).parent
    for directory, config_value, rows, files in (
        (
            source,
            source_config,
            source_rows,
            (
                "pipeline_run.py",
                "pipeline_regions.py",
                "pipeline_assembly.py",
                "generalization_run.py",
                "pipeline_source_order.py",
            ),
        ),
        (
            topology,
            topology_config,
            topology_rows,
            (
                "pipeline_run.py",
                "pipeline_frontier.py",
                "generalization_vision_run.py",
                "generalization_vision_regions.py",
                "pipeline_vision_transcription.py",
            ),
        ),
    ):
        (directory / "code").mkdir()
        trusted = {}
        for name in files:
            data = (root / name).read_bytes()
            (directory / "code" / name).write_bytes(data)
            trusted[name] = sha(data)
        write_json(
            directory / "frozen.json",
            {
                "config": config_value,
                "records": records,
                "manifest_sha256": "synthetic16-manifest",
                "code_sha256": trusted,
            },
        )
        write_json(
            directory / "report.json",
            {
                "config": config_value,
                "results": rows,
                "calls": 16,
                "effective_usd": 5.0,
                "metrics": {"wall_seconds": 100},
            },
        )
        maps.append(trusted)
    return maps[0], maps[1]


def test_authenticated_prepare_no_client_and_complete_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, topology = tmp_path / "source", tmp_path / "topology"
    a, b = archives(source, topology)

    def forbidden() -> None:
        pytest.fail("Preparation must not construct a credential-bearing client")

    monkeypatch.setattr(runner, "P003DecisionClient", forbidden)
    output = tmp_path / "prepared"
    report = runner.run(source, topology, a, b, output, config(prepare_only=True))
    assert report["pages_per_minute"] is None
    assert report["incremental_ownership"]["returned_calls"] == 0
    assert report["incremental_ownership"]["status_counts"] == {"prepared_retained_baseline": 16}
    frozen = json.loads((output / "frozen.json").read_bytes())
    assert frozen["manifest_sha256"] == "synthetic16-manifest"
    assert frozen["source_baseline"]["copied_directory"] == "source-baseline"
    assert frozen["topology_baseline"]["copied_directory"] == "topology-baseline"
    assert "decision_concurrent.py" in frozen["code_sha256"]
    assert (output / "source-baseline/p0.md").read_bytes() == (source / "p0.md").read_bytes()
    with pytest.raises(ValueError, match="independent trusted"):
        runner.run(source, topology, {}, b, tmp_path / "untrusted", config(prepare_only=True))


def test_authenticated_hosted_mock_keeps_cost_intervals_separate(tmp_path: Path) -> None:
    source, topology = tmp_path / "source", tmp_path / "topology"
    a, b = archives(source, topology)
    client = Client(tmp_path)
    report = runner.run(source, topology, a, b, tmp_path / "hosted-mock", config(run_hosted=True), client)
    assert report["incremental_ownership"]["returned_calls"] == 32
    assert report["incremental_ownership"]["effective_usd"] == pytest.approx(0.32)
    assert report["source_generation_report"]["effective_usd"] == 5.0
    assert report["topology_generation_report"]["effective_usd"] == 5.0
    assert report["incremental_ownership"]["status_counts"] == {"completed": 16}
    assert report["metrics"]["end_to_end_pipeline_measured"] is False
    assert report["pages_per_minute"] is None


def test_all_crops_preflight_before_first_paid_request(tmp_path: Path) -> None:
    original, topology = fixtures(tmp_path / "source", tmp_path / "topology", crops=2)
    extra = [{"id": f"extra{i}", "text": "x", "bbox": [110, 20, 111, 21]} for i in range(251)]
    original["source"]["words"].extend(extra)
    region = original["region_plan"]["regions"][0]
    region["source"]["words"].extend(deepcopy(extra))
    region["source_ids"].extend(w["id"] for w in extra)
    original["regions"][0]["state"]["unresolved_ids"].extend(w["id"] for w in extra)
    output = tmp_path / "out"
    output.mkdir()
    client = Client(tmp_path)
    result = runner.process_page(
        original,
        topology,
        tmp_path / "source",
        tmp_path / "topology",
        {"generation_provider": "anthropic"},
        output,
        config(),
        client,
    )
    assert result["topology_status"] == "unsupported_retained_baseline"
    assert result["topology_errors"][0]["reason"] == "ownership_inventory_or_menu_capacity"
    assert client.bodies == []
