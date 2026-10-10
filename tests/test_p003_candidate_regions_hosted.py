"""Mocked valid-region native selector retains whole-crop and whole-page atomicity."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_candidate_regions as admission
from bench import p003_candidate_regions_hosted as hosted
from bench.silver import sha, write_json
from conftest import build_pdf
from test_p003_candidate_regions import matched
from test_p003_candidate_run import baseline


class Client:
    """Only a temporary fake ledger; no credentials or network transport."""

    def __init__(self, directory: Path, *, abstain: bool = False, malformed: bool = False) -> None:
        """Create isolated fake accounting and controlled native outcomes."""
        self.ledger = directory / "fake-ledger.json"
        write_json(self.ledger, {"requests": []})
        self.abstain, self.malformed = abstain, malformed
        self.bodies = []

    def request(self, body: dict, **kwargs: object) -> dict:
        """Select one exact alias or explicitly abstain with typed probabilities."""
        self.bodies.append(deepcopy(body))
        options = list(body["questions"]["q0"]["criteria"])
        selected = "unresolved" if self.abstain else options[0]
        entry = {
            "index": len(self.bodies),
            "tag": kwargs["tag"],
            "accounted_usd": 0.01,
            "cost_status": "provider-reported USD",
            "provider_reported_usd": 0.01,
            "request_sha256": sha(json.dumps(body, separators=(",", ":")).encode()),
        }
        ledger = json.loads(self.ledger.read_bytes())
        ledger["requests"].append(entry)
        write_json(self.ledger, ledger)
        answer = {
            "type": "choice",
            "choice": "invented" if self.malformed else selected,
            "probabilities": {k: int(k == selected) for k in options},
        }
        return {"entry": entry, "result": {"answers": {"q0": answer}}, "replayed": False}


def config() -> dict:
    return {"model": "typesafe/jev-1.13", "image_edge": 0, "run_id": "mock", "run_hosted": True}


def test_native_selection_has_only_valid_candidates_and_complete_outputs(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    frozen = admission.freeze_page(record, pages, dirs, configs, seed=7)
    output = tmp_path / "output"
    output.mkdir()
    client = Client(tmp_path)
    result = hosted.process(record, frozen, dirs[0], output, config(), client)
    assert result["status"] == "ok"
    assert result["ranking_status"] == "completed"
    assert len(client.bodies) == 1
    assert result["source_conserved"] is False
    assert result["calls"] == pages[0]["calls"]
    assert (output / "p0.md").exists()
    assert result["tables"] in [p["tables"] for p in pages]


def test_invalid_first_candidate_sole_valid_needs_no_selector_call(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    pages[0]["status"] = "error"
    pages[0]["error"] = "original generation failure"
    pages[0]["transcription_regions"][0]["transcription_response"] = {}
    frozen = admission.freeze_page(record, pages, dirs, configs, seed=7)
    output = tmp_path / "output"
    output.mkdir()
    client = Client(tmp_path)
    result = hosted.process(record, frozen, dirs[0], output, config(), client)
    assert result["ranking_status"] == "completed"
    assert result["status"] == "ok"
    assert result["original_baseline_status"] == "error"
    assert result["selected_origins"] == {"0": 1}
    assert not client.bodies
    assert frozen["generation_provenance"][0]["page"]["error"] == "original generation failure"


def test_abstention_predeclared_first_valid_and_malformed_atomic_fallback(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    frozen = admission.freeze_page(record, pages, dirs, configs, seed=7)
    output = tmp_path / "output"
    output.mkdir()
    abstain = Client(tmp_path, abstain=True)
    result = hosted.process(record, frozen, dirs[0], output, config(), abstain)
    assert result["selected_origins"] == {"0": 0}
    assert result["ranking_regions"][0]["ranking_status"] == "unresolved_first_valid_fallback"
    malformed = Client(tmp_path, malformed=True)
    result = hosted.process(record, frozen, dirs[0], output, config(), malformed)
    assert result["ranking_status"] == "failed_retained_first"
    assert result["status"] == pages[0]["status"]
    assert len(result["ranking_calls"]) == 1
    assert (output / "p0.md").read_bytes() == (dirs[0] / "p0.md").read_bytes()
    assert (output / "p0-structure.json").read_bytes() == (dirs[0] / "p0-structure.json").read_bytes()


def test_corrupted_pool_fails_before_paid_request_and_invalid_mode_refused(tmp_path: Path) -> None:
    record, pages, dirs, configs = matched(tmp_path)
    frozen = admission.freeze_page(record, pages, dirs, configs, seed=7)
    frozen["crops"][0]["valid_baseline_indexes"] = [0]
    output = tmp_path / "output"
    output.mkdir()
    client = Client(tmp_path)
    result = hosted.process(record, frozen, dirs[0], output, config(), client)
    assert result["ranking_status"] == "failed_retained_first"
    assert not client.bodies
    with pytest.raises(ValueError, match="opt-in"):
        hosted.run(dirs, [], tmp_path / "fresh", {}, client)


def test_full_offline_freeze_then_mocked_root_adapter_accounting(tmp_path: Path) -> None:
    data = build_pdf(["original"] * 16, page_size=(200, 100))
    pdf = tmp_path / "original.pdf"
    pdf.write_bytes(data)
    dirs, maps = [], []
    for i in range(2):
        directory = tmp_path / f"baseline-{i}"
        _, _, trusted = baseline(directory, f"text-{i}")
        frozen = json.loads((directory / "frozen.json").read_bytes())
        report = json.loads((directory / "report.json").read_bytes())
        for record in frozen["records"]:
            record.update(pdf_path=str(pdf), pdf_sha256=sha(data))
        for page in report["results"]:
            page.update(pdf_sha256=sha(data), rotation_normalized=False)
            write_json(directory / f"{page['id']}-result.json", page)
        write_json(directory / "frozen.json", frozen)
        write_json(directory / "report.json", report)
        mapping = tmp_path / f"trusted-{i}.json"
        write_json(mapping, trusted)
        dirs.append(directory)
        maps.append(mapping)
    client = Client(tmp_path)
    output = tmp_path / "fresh"
    report = hosted.run(dirs, maps, output, config(), client)
    assert report["complete_output_pages"] == 16
    assert report["incremental_ranking"]["returned_calls"] == 1
    assert report["incremental_ranking"]["effective_usd"] == 0.01
    assert report["pages_per_minute"] is None
    assert report["candidate_generation_reports"][0]["calls"] == 16
    frozen = json.loads((output / "frozen.json").read_bytes())
    assert frozen["config"]["processor"] == "p003_candidate_valid_regions"
    assert "decision_concurrent.py" in frozen["code_sha256"]
    assert "p003_candidate_regions.py" in frozen["code_sha256"]
    assert (output / "admission/frozen.json").exists()
    with pytest.raises(ValueError, match="fresh"):
        hosted.run(dirs, maps, output, config(), client)
