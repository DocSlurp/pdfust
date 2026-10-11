"""Mocked frozen local execution, atomic failure and source-only scenario admission."""

# ruff: noqa: ANN401, SLF001
from pathlib import Path
from typing import Any

import pytest
from bench import extension_local as local
from bench import extension_local_run as runner
from bench.silver import canonical, sha, write_json


def corpus(root: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    directory = root / "corpus"
    (directory / "menus").mkdir(parents=True)
    (directory / "stress").mkdir()
    words = [
        {
            "id": f"w{i}",
            "text": f"literal{i}",
            "bbox": [i % 2 * 20 + 1, i // 2 * 20 + 1, i % 2 * 20 + 10, i // 2 * 20 + 8],
        }
        for i in range(16)
    ]
    source = {"words": words, "page_size": [40, 160]}
    native = {
        "tables": [
            {
                "row_count": 8,
                "col_count": 2,
                "bbox": [0, 0, 40, 160],
                "cells": [{"source_ids": [w["id"]], "role": "unknown"} for w in words],
                "values": [[f"literal{i}", f"literal{i + 1}"] for i in range(0, 16, 2)],
                "spans": [{"row": i // 2, "column": i % 2, "row_span": 1, "column_span": 1} for i in range(16)],
            }
        ],
        "unresolved_ids": [],
    }
    current = local._move(source, native, "w1", (0, 0))
    current = local._move(source, current, "w13", (0, 12))
    inventory, pages = {}, []
    for ident in ("a", "b"):
        pdf = directory / f"{ident}.pdf"
        pdf.write_bytes(b"Source PDF bytes; edge zero avoids rendering")
        menu = {
            "source": source,
            "source_sha256": sha(canonical(source)),
            "baseline": current,
            "candidates": [{"state": current}, {"state": native}],
        }
        path = directory / "menus" / f"{ident}.json"
        write_json(path, menu)
        inventory[f"menus/{ident}.json"] = sha(path.read_bytes())
        stress = directory / "stress" / f"{ident}.json"
        write_json(
            stress,
            {
                "treatments": [
                    {
                        "treatment": "swapped_cell_values",
                        "raw_baseline": current,
                        "valid_source_ownership": False,
                        "expected_state": "DO NOT TRANSMIT",
                    }
                ]
            },
        )
        inventory[f"stress/{ident}.json"] = sha(stress.read_bytes())
        pages.append({"id": ident, "page_number": 0, "pdf_path": str(pdf), "pdf_sha256": sha(pdf.read_bytes())})
    write_json(directory / "manifest.json", {"split": "DEV", "pages": pages})
    write_json(directory / "source-inventory.json", {"artifacts": inventory})
    return directory, source, current


def arm(root: Path, **config: Any) -> tuple[Path, dict[str, Any]]:
    source_root, _, current = corpus(root)
    output = root / "arm"
    runner.prepare(
        source_root, output, {"run_id": "extension-v1-local-test", "model": "typesafe/jev-1.13", **config}, ["a", "b"]
    )
    return output, current


class Client:
    """Persist provider-like receipts while checking packets predate transmission."""

    def __init__(self, root: Path, output: Path, *, fail: int = 0, invalid: bool = False, choice: str = "keep") -> None:
        """Create an isolated mocked accounting ledger."""
        self.ledger = root / "ledger.json"
        write_json(self.ledger, {"requests": []})
        self.output, self.fail, self.invalid, self.choice = output, fail, invalid, choice
        self.calls = 0

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Check frozen bytes and return a native response without network access."""
        self.calls += 1
        assert kwargs["replay"] is False
        parts = kwargs["tag"].split("/")
        ident, step = parts[-3], parts[-2].split("-")[-1]
        frozen = runner.base.read(self.output / "steps" / f"{ident}-step-{step}-frozen.json")
        assert any(packet["body"] == body for packet in frozen["transmitted_packets"])
        entry = {
            "tag": kwargs["tag"],
            "index": self.calls,
            "accounted_usd": 0.001,
            "provider_reported_usd": 0.001,
            "cost_status": "provider_reported",
        }
        entries = runner.base.read(self.ledger)["requests"]
        if self.calls == self.fail:
            entry.update(cost_status="reserved")
        write_json(self.ledger, {"requests": [*entries, entry]})
        if self.calls == self.fail:
            message = "mock transport timeout"
            raise TimeoutError(message)
        answers = {
            name: {
                "type": "choice",
                "choice": self.choice,
                "probabilities": {a: int(a == self.choice) for a in question["criteria"]},
            }
            for name, question in body["questions"].items()
        }
        if self.invalid:
            answers = {}
        return {
            "entry": entry,
            "result": {
                "model": "typesafe/jev-1.13-20260917",
                "answers": answers,
                "usage": {"prompt_tokens": 50, "completion_tokens": 0},
            },
        }


@pytest.mark.parametrize("mechanism", ["local", "batch", "singles"])
def test_keep_stops_after_one_step_and_archives_exact_requests(tmp_path: Path, mechanism: str) -> None:
    output, current = arm(tmp_path, mechanism=mechanism, max_steps=3)
    client = Client(tmp_path, output)
    report = runner.run(output, client=client)
    assert client.calls == (4 if mechanism == "singles" else 2)
    for result in report["results"]:
        assert result["final_state"] == current
        assert result["model_selected_state"] == current
        assert result["stop_reason"] == "keep"
        assert len(result["steps"]) == 1
        assert result["model_success"]
    assert report["costs"]["effective_usd"] == pytest.approx(client.calls * 0.001)
    with pytest.raises(FileExistsError):
        runner.run(output, client=client)


def test_singles_failure_is_atomic_and_stops_remaining_arm(tmp_path: Path) -> None:
    output, current = arm(tmp_path, mechanism="singles")
    client = Client(tmp_path, output, fail=2, choice="a1")
    report = runner.run(output, client=client)
    assert client.calls == 2
    first, second = report["results"]
    assert first["final_state"] == current
    assert first["model_selected_state"] is None
    assert not first["model_success"]
    assert first["steps"][0]["failure_stage"] == "transport"
    assert second["status"] == "not_attempted"
    assert report["intended_pages"] == 2
    assert report["selected_pages"] == 0
    assert report["costs"]["effective_usd"] is None
    assert report["costs"]["unresolved_reserved_usd"] == 0.001


def test_invalid_response_stops_without_partial_state_credit(tmp_path: Path) -> None:
    output, current = arm(tmp_path, mechanism="batch")
    client = Client(tmp_path, output, invalid=True)
    report = runner.run(output, client=client)
    assert client.calls == 1
    assert report["results"][0]["final_state"] == current
    assert report["results"][0]["steps"][0]["failure_stage"] == "answer_validation"
    assert report["results"][1]["status"] == "not_attempted"


def test_missing_scenario_no_request_and_scenario_metadata_excluded(tmp_path: Path) -> None:
    output, _ = arm(tmp_path, scenario="missing_table_value")
    client = Client(tmp_path, output)
    report = runner.run(output, client=client)
    assert client.calls == 0
    assert report["intended_pages"] == 2
    assert all(r["stop_reason"] == "missing_scenario" for r in report["results"])
    other = tmp_path / "other"
    other.mkdir()
    output, _ = arm(other, scenario="swapped_cell_values")
    packet = runner.base.read(output / "pages/a.json")["packet"]
    wire = canonical(packet["body"]).decode()
    for forbidden in ("swapped_cell_values", "valid_source_ownership", "expected_state", "DO NOT TRANSMIT"):
        assert forbidden not in wire


def test_runtime_and_frozen_page_mutation_rejected_before_admission(tmp_path: Path) -> None:
    output, _ = arm(tmp_path)
    client = Client(tmp_path, output)
    page = output / "pages/a.json"
    original = page.read_bytes()
    page.write_text("{}")
    with pytest.raises(ValueError, match="Frozen page"):
        runner.run(output, client=client)
    page.write_bytes(original)
    (output / "code/extension_local.py").write_text("changed")
    with pytest.raises(ValueError, match="Runtime changed"):
        runner.run(output, client=client)
    assert client.calls == 0
    assert not (output / "started.json").exists()


def test_multiple_steps_do_not_stop_on_complete_ownership(tmp_path: Path) -> None:
    output, _ = arm(tmp_path, max_steps=3)
    client = Client(tmp_path, output, choice="a1")
    report = runner.run(output, client=client)
    assert client.calls > 2
    assert any(len(r["steps"]) > 1 for r in report["results"])
    assert all(len(r["steps"]) <= 3 for r in report["results"])
    assert all(r["stop_reason"] in {"step_cap", "repeated_state", "no_focus"} for r in report["results"])
