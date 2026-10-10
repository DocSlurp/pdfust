"""Micro audits separate transport stop, malformed answers and unknown accounting."""

from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_micro_relations as micro
from bench.p003_micro_verification import QUESTIONS, cost, resolved_entries, verify_results
from bench.silver import write_json


def fixture() -> tuple:
    plan = micro.freeze({"page_size": [100, 100], "words": [
        {"id": "a", "text": "Literal A", "bbox": [10, 10, 40, 20]},
        {"id": "b", "text": "Literal B", "bbox": [45, 10, 60, 20]},
    ]})
    pair = plan["pairs"][0]
    config = {"model": "liquid/d1", "provider": "openrouter", "mode": "micro", "run_id": "fixture"}
    selected, rows, plans, requests = [], [], {}, []
    for index in range(QUESTIONS):
        page = f"page-{index}"
        plans[page] = plan
        selected.append({"index": index, "page_id": page, **pair, "wire_encoded_sha256": "wire"})
        requests.append(micro.body(plan, pair["id"], config["model"]))
        rows.append({"index": index, "page_id": page, "pair_id": pair["id"], "kind": pair["kind"],
                     "source_ids": pair["source_ids"], "model": config["model"], "provider": "openrouter",
                     "mode": "micro", "status": "not_attempted"})
    report = {"client_initialization_error": None, "results": rows}
    return config, plans, selected, requests, report


def checkpoints(tmp_path: Path, rows: list) -> None:
    for row in rows:
        write_json(tmp_path / f"question-{row['index']}-result.json", row)


def test_transport_error_stops_later_admission(tmp_path: Path) -> None:
    config, plans, selected, requests, report = fixture()
    report["results"][0].update(status="transport_error", error={"stage": "transport"})
    report["results"][1].update(status="transport_error", error={"stage": "transport"})
    checkpoints(tmp_path, report["results"])
    with pytest.raises(ValueError, match="continued after"):
        verify_results(tmp_path, config, plans, selected, requests, report)


def test_extra_native_name_cannot_get_valid_choice_credit(tmp_path: Path) -> None:
    config, plans, selected, requests, report = fixture()
    entry = {"index": 7, "request_sha256": "wire", "requested_model": config["model"],
             "tag": "P003/fixture/micro-relations/0"}
    raw = {"answers": {"q0": {"type": "choice", "name": "q0", "choice": "same",
           "probabilities": {"same": 0.8, "separate": 0.1, "unresolved": 0.1}}}}
    report["results"][0].update(status="valid_nonabstaining", entry=entry, replayed=False, usage={})
    checkpoints(tmp_path, report["results"])
    write_json(tmp_path / "question-0-response.json", {"entry": entry, "result": raw, "replayed": False})
    with pytest.raises(ValueError, match="Malformed native"):
        verify_results(tmp_path, config, plans, selected, requests, report)


def test_returned_replay_is_not_fresh_native_evidence(tmp_path: Path) -> None:
    config, plans, selected, requests, report = fixture()
    entry = {"index": 7, "request_sha256": "wire", "requested_model": config["model"],
             "tag": "P003/fixture/micro-relations/0"}
    report["results"][0].update(status="valid_nonabstaining", entry=entry, replayed=True, usage={})
    checkpoints(tmp_path, report["results"])
    write_json(tmp_path / "question-0-response.json", {"entry": deepcopy(entry), "result": {}, "replayed": True})
    with pytest.raises(ValueError, match="attribution"):
        verify_results(tmp_path, config, plans, selected, requests, report)


@pytest.mark.parametrize("value", [None, True, -0.1, float("nan")])
def test_unknown_accounting_cannot_become_free(value: object) -> None:
    with pytest.raises(ValueError, match="accounting"):
        cost(value)


def test_unknown_status_cannot_become_fully_priced() -> None:
    entries = [{"cost_status": status, "accounted_usd": 0.3} for status in
               ("unknown", "unknown: missing usage or catalog price", "reserved", None)]
    assert resolved_entries(entries) == []
    reported = {"cost_status": "provider-reported USD", "accounted_usd": 0.001}
    estimate = {"cost_status": "catalog estimate", "accounted_usd": 0.002}
    assert resolved_entries([*entries, reported, estimate]) == [reported, estimate]
