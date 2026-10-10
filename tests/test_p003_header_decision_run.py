"""Header decisions expose exact selected credit and separate unchanged background."""

# ruff: noqa: ANN001, ANN002, ANN003, ANN201, ANN202, ANN204, D101, D102, D107
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_header_decision_run as runner
from bench import p003_header_packets as packets
from bench import p003_header_proposals as headers
from bench.silver import canonical, sha


def plan(ident: str, *, ambiguous: bool = True):
    table = {"bbox": [0, 0, 400, 1000], "matrix": [[f"head-{ident}"], ["whole body", "other"]], "mergedspans": []}
    if not ambiguous:
        table["matrix"][0].append("already rectangular")
    fixed = {"bbox": [500, 0, 1000, 1000], "matrix": [["fixed", "header"], ["historical", "text"]], "mergedspans": []}
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": canonical({"answers": {"q0": {"tables": [table, fixed]}}}).decode()},
            }
        ]
    }
    original = {
        "id": ident,
        "status": "error" if ambiguous else "ok",
        "viewport": [0, 0, 200, 200],
        "transcription_regions": [
            {
                "index": 0,
                "request_index": 0,
                "viewport": [10, 20, 110, 120],
                "status": "error" if ambiguous else "ok",
                "transcription_response": response,
            }
        ],
    }
    frozen = headers.freeze_page(original)
    frozen["record"] = {"id": ident}
    return frozen


def fixture(count: int = 16, active: int = 1):
    config = runner.configuration("typesafe/jev-1.13", "full", 0, 3)
    config["run_id"] = "offline-header-mock"
    pages, selected = [], []
    for index in range(count):
        frozen = plan(f"p{index}", ambiguous=index < active)
        menus = packets.menu_records(frozen)
        pages.append({"id": frozen["id"], "record": frozen["record"], "plan": frozen, "menus": menus})
        for menu in menus:
            body, evidence = packets.request(menu, config["model"])
            selected.append(
                {"index": len(selected), "page_id": frozen["id"], "menu": menu, "body": body, "evidence": evidence}
            )
    return {"pages": pages, "selected": selected}, config


class Client:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = []

    def request(self, body, **kwargs):
        self.calls.append((body, kwargs))
        answer = next(self.answers)
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, dict) or answer is None:
            result = answer
        else:
            result = {
                "answers": {
                    "q0": {
                        "type": "choice",
                        "choice": answer,
                        "probabilities": {
                            option: float(option == answer) for option in body["questions"]["q0"]["criteria"]
                        },
                        "confidence": 0.01,
                    }
                }
            }
        return {
            "result": result,
            "replayed": False,
            "entry": {
                "tag": kwargs["tag"],
                "requested_model": body["model"],
                "request_sha256": sha(json.dumps(body, separators=(",", ":"), allow_nan=False).encode()),
                "index": len(self.calls) - 1,
            },
        }


def execute(tmp_path: Path, prepared, config, answers):
    client = Client(answers)
    report = runner.execute(prepared, tmp_path, config, client_factory=lambda *_: client, entries_reader=lambda *_: [])
    return report, client


def test_all16_primary_has_only_exact_chosen_hypothesis(tmp_path):
    prepared, config = fixture()
    before = deepcopy(prepared["pages"][0]["plan"])
    report, client = execute(tmp_path, prepared, config, ["A"])
    assert len(report["results"]) == 16
    assert report["selected_header_count"] == 1
    chosen = prepared["selected"][0]["menu"]["options"][0]
    page = report["results"][0]
    assert page["tables"] == [chosen["table"]]
    assert page["decision_results"][0]["selected_table_sha256"] == chosen["table_sha256"]
    assert len(page["fixed_state"]["tables"]) == 1
    assert len(page["combined_state"]["tables"]) == 2
    assert page["original_page_status"] == "error"
    assert prepared["pages"][0]["plan"] == before
    assert all(not p["tables"] and p["fixed_historical_table_count"] == 2 for p in report["results"][1:])
    assert report["incremental_header_selection"]["charges"]["effective_usd"] is None
    assert report["full_pipeline_pages_per_minute"] is None
    assert client.calls[0][1]["replay"] is False


def test_unresolved_and_no_question_receive_no_primary_credit(tmp_path):
    prepared, config = fixture(count=2, active=2)
    prepared["selected"][1].update(body=None, evidence={"question_status": "no_question_refusal"})
    report, client = execute(tmp_path, prepared, config, ["unresolved"])
    assert [r["status"] for r in report["decisions"]] == ["unresolved", "no_question_refusal"]
    assert all(not p["tables"] for p in report["results"])
    assert all(p["original_page_status"] == "error" for p in report["results"])
    assert len(client.calls) == 1


def test_transport_failure_stops_remaining_without_admission(tmp_path):
    prepared, config = fixture(count=4, active=4)
    report, client = execute(tmp_path, prepared, config, ["A", RuntimeError("offline"), "A", "A"])
    assert [r["status"] for r in report["decisions"]] == [
        "selected",
        "transport_error",
        "not_attempted",
        "not_attempted",
    ]
    assert len(client.calls) == 2
    assert all(not p["tables"] for p in report["results"][1:])


def test_malformed_reply_proceeds_to_next_distinct_table(tmp_path):
    prepared, config = fixture(count=2, active=2)
    report, client = execute(tmp_path, prepared, config, [None, "A"])
    assert [r["status"] for r in report["decisions"]] == ["malformed_response", "selected"]
    assert len(client.calls) == 2


def test_explicit_models_modes_and_caps():
    for model in runner.MODELS:
        for mode in runner.EVIDENCE_MODES:
            for edge in (0,) if model == "typesafe/jev-1.13" else (0, 128, 512):
                assert runner.configuration(model, mode, edge, 3)["model"] == model
    with pytest.raises(ValueError, match="text-only"):
        runner.configuration("typesafe/jev-1.13", "full", 128, 3)
    with pytest.raises(ValueError, match="capacity"):
        runner.configuration(runner.MODELS[0], "full", 128, 6)


def test_prepare_only_cli_never_constructs_client(tmp_path, monkeypatch):
    output = tmp_path / "prepared"

    def prepared(*_, **__):
        output.mkdir()
        return {"selected": []}

    def forbidden(*_, **__):
        pytest.fail("Prepare-only CLI must not execute inference")

    monkeypatch.setattr(runner, "prepare", prepared)
    monkeypatch.setattr(runner, "execute", forbidden)
    monkeypatch.setattr(
        "sys.argv",
        [
            "header-run",
            "--pool",
            "pool",
            "--pool-trusted-code",
            "pool-map",
            "--header-trusted-code",
            "header-map",
            "--generation-trusted-code",
            "generation-map",
            "--output",
            str(output),
            "--model",
            "typesafe/jev-1.13",
            "--evidence-mode",
            "local_header",
            "--image-edge",
            "0",
        ],
    )
    runner.main()
    assert runner.read(output / "prepare-report.json")["hosted_calls"] == 0
