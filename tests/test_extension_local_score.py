"""Offline replay authenticates local decisions and keeps failures out of model credit."""

# ruff: noqa: ANN401, SLF001
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import extension_local as local
from bench import extension_local_run as runner
from bench import extension_local_score as score
from bench.silver import sha, write_json
from test_extension_local_run import Client, arm, corpus


class AttestedClient(Client):
    """Attach exact-wire identity to isolated mocked provider receipts."""

    def request(self, body: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Return mocked answers attested to the root driver's actual wire order."""
        result = super().request(body, **kwargs)
        result["entry"]["request_sha256"] = sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode())
        result["entry"]["requested_model"] = body["model"]
        return result


def evaluation(output: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    frozen = runner.base.read(output / "frozen.json")
    source = runner.base.read(Path(frozen["corpus"]) / "menus/a.json")["source"]
    current = runner.base.read(output / "pages/a.json")["baseline_state"]
    correct = local._move(source, current, "w1", (0, 1))
    correct = local._move(source, correct, "w13", (0, 13))
    admitted = {
        "manifest": runner.base.read(Path(frozen["corpus"]) / "manifest.json"),
        "menus": {ident: runner.base.read(Path(frozen["corpus"]) / "menus" / f"{ident}.json") for ident in ("a", "b")},
        "stress": {
            ident: runner.base.read(Path(frozen["corpus"]) / "stress" / f"{ident}.json") for ident in ("a", "b")
        },
        "targets": [
            {"id": ident, "structural_scored": True, "tables": deepcopy(correct["tables"])} for ident in ("a", "b")
        ],
        "receipts": {
            "source_artifacts": runner.base.read(Path(frozen["corpus"]) / "source-inventory.json")["artifacts"],
            "pins": {
                "manifest.json": frozen["manifest_sha256"],
                "source-inventory.json": frozen["source_inventory_sha256"],
            },
        },
    }
    monkeypatch.setattr(score.scoring, "load_frozen", lambda _path: admitted)
    return admitted


def rewrite_report(output: Path, report: dict[str, Any]) -> None:
    """Replace only the explicit report in mutation fixtures."""
    write_json(output / "report.json", report)


@pytest.mark.parametrize("mechanism", ["local", "batch", "singles"])
def test_authenticated_native_replay_and_distinct_metric_streams(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mechanism: str
) -> None:
    output, _ = arm(tmp_path, mechanism=mechanism, max_steps=3)
    client = AttestedClient(tmp_path, output, choice="a1")
    runner.run(output, client=client)
    evaluation(output, monkeypatch)
    result = score.score_run(tmp_path / "corpus", output)
    assert result["intended_pages"] == 2
    assert result["receipts"]["authenticated_transmission_receipts"] == client.calls
    assert not result["receipts"]["archived_code_executed"]
    assert set(result["comparisons_by_metric"]) == {"strict", "v2", "wrap"}
    assert all(page["model_credit"] for page in result["pages"])


def test_tampered_receipt_rejected_before_scoring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, _ = arm(tmp_path)
    runner.run(output, client=AttestedClient(tmp_path, output))
    evaluation(output, monkeypatch)
    path = output / "steps/a-step-0-q-0-receipt.json"
    receipt = runner.base.read(path)
    receipt["result"]["answers"]["q0"]["choice"] = "a1"
    write_json(path, receipt)
    with pytest.raises(ValueError, match="artifact changed"):
        score.score_run(tmp_path / "corpus", output)


def test_missing_report_page_remains_in_denominator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, _ = arm(tmp_path, scenario="missing_table_value")
    report = runner.run(output, client=AttestedClient(tmp_path, output))
    evaluation(output, monkeypatch)
    report["results"] = report["results"][:1]
    rewrite_report(output, report)
    result = score.score_run(tmp_path / "corpus", output)
    assert result["intended_pages"] == 2
    assert result["status_counts"] == {"not_applicable": 1, "missing_result": 1}
    assert result["terminal_model_selected_only"]["strict"]["totals"]["all_page_errors"] == 2
    assert all(not page["model_credit"] for page in result["pages"])


def test_failed_second_step_partial_is_diagnostic_not_model_credit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_root, source, initial = corpus(tmp_path)
    initial = local._move(source, initial, "w13", (0, 13))
    inventory = runner.base.read(source_root / "source-inventory.json")
    for ident in ("a", "b"):
        path = source_root / "menus" / f"{ident}.json"
        menu = runner.base.read(path)
        menu["baseline"] = initial
        menu["candidates"].append({"state": initial})
        write_json(path, menu)
        inventory["artifacts"][f"menus/{ident}.json"] = sha(path.read_bytes())
    write_json(source_root / "source-inventory.json", inventory)
    output = tmp_path / "arm"
    runner.prepare(
        source_root,
        output,
        {"run_id": "extension-v1-local-test", "model": "typesafe/jev-1.13", "max_steps": 3},
        ["a", "b"],
    )
    runner.run(output, client=AttestedClient(tmp_path, output, choice="a1", fail=2))
    evaluation(output, monkeypatch)
    result = score.score_run(tmp_path / "corpus", output)
    first = result["pages"][0]
    assert first["accepted_steps"] == 1
    assert first["failed_continuation"]
    assert not first["model_credit"]
    assert first["last_validated_sha256"] != first["baseline_sha256"]
    partial = result["last_validated_partial_diagnostic"]["strict"]["totals"]["strict_exact_cells"]
    baseline = result["baseline_raw_scenario"]["strict"]["totals"]["strict_exact_cells"]
    assert partial > baseline
    assert result["last_validated_partial_diagnostic"]["strict"]["totals"]["exact_page"] == 1
    assert result["terminal_model_selected_only"]["strict"]["totals"]["all_page_errors"] == 2
    assert result["composed_with_baseline_retention"] == result["baseline_raw_scenario"]


def test_wrong_row_and_missing_word_preserve_full_penalties(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, current = arm(tmp_path)
    runner.run(output, client=AttestedClient(tmp_path, output))
    admitted = evaluation(output, monkeypatch)
    source = admitted["menus"]["a"]["source"]
    correct = local._move(source, current, "w1", (0, 1))
    correct = local._move(source, correct, "w13", (0, 13))
    wrong_row = local._move(source, correct, "w1", (0, 3))
    missing = local._move(source, correct, "w1", None)
    target = admitted["targets"][0]
    good = score.scoring.score_predictions([target], [score.scoring.prediction("a", correct)])
    bad = score.scoring.score_predictions([target], [score.scoring.prediction("a", wrong_row)])
    omitted = score.scoring.score_predictions([target], [score.scoring.prediction("a", missing)])
    assert good["strict"]["totals"]["exact_page"] == 1
    assert bad["strict"]["totals"]["exact_page"] == 0
    assert omitted["strict"]["totals"]["exact_page"] == 0
    assert omitted["wrap"]["full_content_recall"] < 1
    assert omitted["v2"]["full_content_recall"] < 1


def test_final_state_cannot_be_invented_even_if_source_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, current = arm(tmp_path)
    report = runner.run(output, client=AttestedClient(tmp_path, output))
    admitted = evaluation(output, monkeypatch)
    report["results"][0]["final_state"] = local._move(admitted["menus"]["a"]["source"], current, "w1", None)
    rewrite_report(output, report)
    with pytest.raises(ValueError, match="final state differs"):
        score.score_run(tmp_path / "corpus", output)


def test_new_local_successor_need_not_belong_to_global_menu(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output, _ = arm(tmp_path, max_steps=1)
    report = runner.run(output, client=AttestedClient(tmp_path, output, choice="a1"))
    admitted = evaluation(output, monkeypatch)
    selected = report["results"][0]["final_state"]
    assert all(
        score.scoring.state_key(c["state"]) != score.scoring.state_key(selected)
        for c in admitted["menus"]["a"]["candidates"]
    )
    result = score.score_run(tmp_path / "corpus", output)
    assert result["pages"][0]["model_credit"]
    assert result["comparisons_by_metric"]["strict"]["selected_improved"] == 2


def test_forged_wire_attestation_rejected_even_with_matching_file_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output, _ = arm(tmp_path)
    report = runner.run(output, client=AttestedClient(tmp_path, output))
    evaluation(output, monkeypatch)
    path = output / "steps/a-step-0-q-0-receipt.json"
    receipt = runner.base.read(path)
    receipt["entry"]["request_sha256"] = "0" * 64
    write_json(path, receipt)
    record = report["results"][0]["steps"][0]["receipts"][0]
    record["entry"] = receipt["entry"]
    record["receipt_sha256"] = sha(path.read_bytes())
    rewrite_report(output, report)
    with pytest.raises(ValueError, match="exact transmitted wire"):
        score.score_run(tmp_path / "corpus", output)
