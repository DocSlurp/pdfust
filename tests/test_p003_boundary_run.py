"""Retained-state repair never reruns extraction or loses atomic fallback outputs."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import p003_boundary_run as repair
from bench.generalization_run import _table_bounds
from bench.pipeline_regions import compose
from bench.pipeline_run import markdown
from bench.silver import sha, write_json
from test_pipeline_repair import fixture


class MockClient:
    """Record actual typed request shapes in an isolated fake ledger; no inference."""

    def __init__(self, directory: Path, *, fail_at: int | None = None) -> None:
        """Create a separate fake ledger without credentials or network activity."""
        self.ledger = directory / "mock-ledger.json"
        write_json(self.ledger, {"requests": []})
        self.bodies: list[dict[str, Any]] = []
        self.fail_at = fail_at

    def request(self, body: dict[str, Any], **options: Any) -> dict[str, Any]:  # noqa: ANN401 - mimic root client.
        """Return deterministic typed choices and retain failed reservations."""
        assert set(body) == {"model", "state", "questions"}
        assert options["replay"] is False
        assert options["tag"].startswith("P003/")
        ledger = json.loads(self.ledger.read_bytes())
        index = len(ledger["requests"])
        entry = {
            "index": index,
            "tag": options["tag"],
            "accounted_usd": 0.01,
            "provider_reported_usd": 0.01,
            "cost_status": "provider-reported USD",
        }
        self.bodies.append(deepcopy(body))
        if index == self.fail_at:
            entry.update(accounted_usd=0.3, cost_status="reserved")
            entry.pop("provider_reported_usd")
        ledger["requests"].append(entry)
        write_json(self.ledger, ledger)
        if index == self.fail_at:
            message = "sanitized simulated provider failure"
            raise RuntimeError(message)
        result = {
            "answers": {
                ident: {
                    "type": "choice",
                    "choice": "join",
                    "probabilities": {"join": 0.9, "split": 0.1, "unresolved": 0},
                    "confidence": 0.123,
                }
                for ident in body["questions"]
            },
            "usage": {"cost": 0.01},
        }
        return {"entry": entry, "result": result, "replayed": False}


def baseline(directory: Path, *, failed: bool = False, native: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    directory.mkdir()
    page, state = fixture([["Record", "20"], ["wrap", ""], ["Last", "30"]])
    if native:
        page["vector_candidates"] = deepcopy(state["tables"])
    region = {
        "id": "r0",
        "boundary": "geometry",
        "bbox": [0, 0, 300, 300],
        "source_ids": [w["id"] for w in page["words"]],
        "source": deepcopy(page),
    }
    plan = {**deepcopy(page), "regions": [region], "coordinate_space": "display_global"}
    composed = compose(plan, {"r0": state})
    _table_bounds(page, composed)
    original = {
        "id": "p0",
        "status": "error" if failed else "ok",
        "source": page,
        "region_plan": {k: v for k, v in plan.items() if k != "words"},
        "regions": [{"id": "r0", "state": state}],
        "tables": composed["tables"],
        "unresolved_ids": [],
        "wall_seconds": 12.0,
        "cpu_seconds": 3.0,
        "source_conserved": True,
        "calls": [{"entry": {"accounted_usd": 0.75, "cost_status": "provider-reported USD"}}],
    }
    if failed:
        original.update(error_type="ValueError", error="original baseline failure")
    record = {"id": "p0", "pdf_path": "does-not-exist.pdf", "pdf_sha256": "unused", "page_number": 0}
    write_json(
        directory / "frozen.json",
        {
            "records": [record],
            "config": {"processor": "regions", "source_order": "original"},
            "manifest_sha256": "frozen-dev-manifest",
            "code_sha256": {},
        },
    )
    write_json(
        directory / "report.json",
        {
            "config": {"processor": "regions"},
            "results": [original],
            "metrics": {"wall_seconds": 12.0},
            "calls": 1,
            "effective_usd": 0.75,
        },
    )
    write_json(directory / "p0-result.json", original)
    if not failed:
        write_json(directory / "p0-structure.json", composed)
        (directory / "p0.md").write_text(markdown(page, state))
    return record, original


def configuration(**overrides: Any) -> dict[str, Any]:  # noqa: ANN401
    return {"run_hosted": True, "model": "typesafe/jev-1.13", "image_edge": 0, "max_questions": 1, **overrides}


def test_retained_repair_preserves_baseline_and_separates_incremental_accounting(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    baseline(prior)
    before = {p.name: p.read_bytes() for p in prior.iterdir()}
    output, client = tmp_path / "repaired", MockClient(tmp_path)
    report = repair.run(prior, output, configuration(), client)
    row = report["results"][0]
    assert row["status"] == "ok"
    assert row["repair_status"] == "completed"
    assert row["tables"][0]["values"] == [["Record wrap", "20"], ["Last", "30"]]
    assert row["calls"] == row["baseline_provenance"]["calls"]
    assert row["wall_seconds"] == 12.0
    assert report["incremental_repair"]["ledger_attempts"] == 2
    assert report["incremental_repair"]["effective_usd"] == pytest.approx(0.02)
    assert report["baseline_report"]["effective_usd"] == 0.75
    assert report["metrics"]["end_to_end_pipeline_measured"] is False
    assert report["pages_per_minute"] is None
    assert {p.name: p.read_bytes() for p in prior.iterdir()} == before
    frozen = json.loads((output / "frozen.json").read_bytes())
    assert frozen["manifest_sha256"] == "frozen-dev-manifest"
    assert frozen["baseline"]["file_sha256"]["p0-result.json"] == sha(before["p0-result.json"])
    assert (output / "baseline/p0-result.json").read_bytes() == before["p0-result.json"]
    assert "Record wrap" in (output / "p0.md").read_text()
    assert len(list(output.glob("*-request.json"))) == 2
    assert len(list(output.glob("*-response.json"))) == 2


def test_failure_after_successful_batch_retains_complete_original(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    _, original = baseline(prior)
    client = MockClient(tmp_path, fail_at=1)
    output = tmp_path / "failed-repair"
    report = repair.run(prior, output, configuration(), client)
    row = report["results"][0]
    assert row["status"] == "ok"
    assert row["repair_status"] == "failed_retained_baseline"
    assert row["tables"] == original["tables"]
    assert row["regions"] == original["regions"]
    assert row["repair_errors"][0]["error_type"] == "RuntimeError"
    assert report["incremental_repair"]["effective_usd"] is None
    assert report["incremental_repair"]["known_partial_effective_usd"] == 0.01
    assert report["incremental_repair"]["unresolved_reserved_usd"] == 0.3
    assert report["incremental_repair"]["ledger_attempts"] == 2
    assert (output / "p0-structure.json").read_bytes() == (prior / "p0-structure.json").read_bytes()
    assert (output / "p0.md").read_bytes() == (prior / "p0.md").read_bytes()
    assert (output / "p0-repair-error.json").exists()


@pytest.mark.parametrize("failed", [False, True])
def test_empty_eligible_menu_and_baseline_errors_never_claim_repair_success(tmp_path: Path, *, failed: bool) -> None:
    prior = tmp_path / "prior"
    _, original = baseline(prior, failed=failed, native=True)
    client = MockClient(tmp_path)
    report = repair.run(prior, tmp_path / "output", configuration(), client)
    row = report["results"][0]
    assert row["status"] == original["status"]
    assert row["repair_status"] == ("baseline_failed_skipped" if failed else "not_applicable")
    assert report["incremental_repair"]["ledger_attempts"] == 0
    assert client.bodies == []
    if failed:
        assert row["error"] == "original baseline failure"


def test_independent_region_image_viewport_without_pdf_reprocessing(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    baseline(prior)
    client = MockClient(tmp_path)
    calls = []

    def fake_image(
        record: dict[str, Any], original: dict[str, Any], region: dict[str, Any], edge: int
    ) -> tuple[str, dict[str, Any]]:
        calls.append((record["id"], edge))
        assert original["source"] == region["source"]
        return "data:image/png;base64,fixture", {"image_edge": edge, "image_viewport": region["bbox"]}

    report = repair.run(prior, tmp_path / "image", configuration(image_edge=512), client, image_factory=fake_image)
    assert report["results"][0]["repair_status"] == "completed"
    assert calls == [("p0", 512)]
    packet = json.loads(client.bodies[0]["state"][0])
    assert packet["image_viewport"] == [0, 0, 300, 300]
    assert client.bodies[0]["state"][1]["type"] == "image_url"


def test_opt_in_and_original_structure_integrity(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    baseline(prior)
    client = MockClient(tmp_path)
    with pytest.raises(ValueError, match="opt-in"):
        repair.run(prior, tmp_path / "unauthorized", configuration(run_hosted=False), client)
    state = json.loads((prior / "p0-structure.json").read_bytes())
    state["tables"][0]["values"][0][0] = "changed"
    write_json(prior / "p0-structure.json", state)
    report = repair.run(prior, tmp_path / "bad", configuration(), client)
    assert report["results"][0]["repair_status"] == "failed_retained_baseline"
    assert client.bodies == []


def test_completed_first_region_is_discarded_when_later_region_fails(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    _, original = baseline(prior)
    region = deepcopy(original["region_plan"]["regions"][0])
    region["id"] = "r1"
    region["bbox"] = [0, 100, 300, 200]
    mapping = {word["id"]: word["id"] + "other" for word in region["source"]["words"]}
    for word in region["source"]["words"]:
        word["id"] = mapping[word["id"]]
        word["bbox"][1] += 100
        word["bbox"][3] += 100
    region["source_ids"] = [word["id"] for word in region["source"]["words"]]
    state = deepcopy(original["regions"][0]["state"])
    for table in state["tables"]:
        for cell in table["cells"]:
            cell["source_ids"] = [mapping[ident] for ident in cell["source_ids"]]
    original["source"]["words"].extend(deepcopy(region["source"]["words"]))
    original["region_plan"]["regions"].append(region)
    original["regions"].append({"id": "r1", "state": state})
    composed = compose(
        {**original["region_plan"], "words": original["source"]["words"]},
        {info["id"]: info["state"] for info in original["regions"]},
    )
    _table_bounds(original["source"], composed)
    original["tables"] = composed["tables"]
    write_json(prior / "p0-result.json", original)
    write_json(prior / "p0-structure.json", composed)
    report = json.loads((prior / "report.json").read_bytes())
    report["results"] = [original]
    write_json(prior / "report.json", report)
    (prior / "p0.md").write_text(
        "\n".join(
            markdown(r["source"], i["state"])
            for r, i in zip(original["region_plan"]["regions"], original["regions"], strict=True)
        )
    )
    output = tmp_path / "atomic"
    repaired = repair.run(prior, output, configuration(), MockClient(tmp_path, fail_at=2))
    row = repaired["results"][0]
    assert row["repair_status"] == "failed_retained_baseline"
    assert row["repair_regions"][0]["repair_status"] == "discarded_atomic_failure"
    assert row["tables"] == original["tables"]
    assert row["regions"] == original["regions"]
    assert repaired["incremental_repair"]["ledger_attempts"] == 3
    assert (output / "p0-structure.json").read_bytes() == (prior / "p0-structure.json").read_bytes()


def test_budget_reservation_refuses_before_transmission(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    baseline(prior)
    client = MockClient(tmp_path)
    write_json(
        client.ledger,
        {"requests": [{"tag": "P003/earlier/page/region/0", "accounted_usd": 49.8, "cost_status": "reserved"}]},
    )
    report = repair.run(prior, tmp_path / "capped", configuration(), client)
    assert report["results"][0]["repair_status"] == "failed_retained_baseline"
    assert client.bodies == []
    assert report["incremental_repair"]["ledger_attempts"] == 0
    assert json.loads(client.ledger.read_bytes())["requests"][0]["accounted_usd"] == 49.8
