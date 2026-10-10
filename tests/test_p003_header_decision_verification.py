"""Header receipts cannot borrow historical tables or continue after transport failure."""

import json
from pathlib import Path

import pytest
from bench import p003_header_packets as packets
from bench import p003_header_proposals as headers
from bench.p003_header_decision_verification import quality_predictions, verify_decisions
from bench.silver import canonical, sha


def fixture(tmp_path: Path, choice: str = "A") -> tuple[dict, dict, dict, dict]:
    table = {"bbox": [0, 0, 1000, 1000], "matrix": [["head"], ["body", "other"]], "mergedspans": []}
    original = {
        "transcription_regions": [
            {
                "index": 0,
                "request_index": 0,
                "transcription_response": {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": canonical({"answers": {"q0": {"tables": [table]}}}).decode()},
                        }
                    ],
                },
            }
        ]
    }
    plan = {
        "id": "page",
        "original_page": original,
        "original_page_status": "error",
        "original_page_sha256": sha(canonical(original)),
        "crop_plans": [
            {
                "index": 0,
                "viewport": [10, 20, 110, 120],
                "table_menus": [headers.table_alternatives(table, [10, 20, 110, 120])],
            }
        ],
    }
    menu = packets.menu_records(plan)[0]
    body, evidence = packets.request(menu, "m")
    item = {"index": 0, "page_id": "page", "menu": menu, "body": body, "evidence": evidence}
    config = {"model": "m", "run_id": "run"}
    answer = {
        "answers": {
            "q0": {
                "type": "choice",
                "choice": choice,
                "probabilities": {k: int(k == choice) for k in ["A", "B", "C", "unresolved"]},
            }
        }
    }
    response = {
        "entry": {
            "index": 2,
            "requested_model": "m",
            "tag": "P003/run/header-decision/0",
            "request_sha256": sha(json.dumps(body, separators=(",", ":")).encode()),
        },
        "result": answer,
        "replayed": False,
    }
    row = {
        "index": 0,
        "page_id": "page",
        "menu_id": menu["id"],
        "model": "m",
        "status": "unresolved" if choice == "unresolved" else "selected",
        "entry": response["entry"],
        "replayed": False,
        "receipt": packets.parse(menu, answer),
        "usage": {},
    }
    if choice != "unresolved":
        row["selected_table_sha256"] = next(o["table_sha256"] for o in menu["options"] if o["alias"] == choice)
    (tmp_path / "menu-0-result.json").write_text(json.dumps(row))
    (tmp_path / "menu-0-response.json").write_text(json.dumps(response))
    return item, config, row, response


@pytest.mark.parametrize("choice", ["A", "unresolved"])
def test_exact_native_selection_and_abstention(tmp_path: Path, choice: str) -> None:
    item, config, row, _ = fixture(tmp_path, choice)
    verify_decisions(tmp_path, [item], config, [row], initialization_failed=False)


def test_sorted_archive_hash_is_not_actual_wire_hash(tmp_path: Path) -> None:
    item, config, row, response = fixture(tmp_path)
    response["entry"]["request_sha256"] = sha(json.dumps(item["body"], sort_keys=True, separators=(",", ":")).encode())
    (tmp_path / "menu-0-result.json").write_text(json.dumps(row))
    (tmp_path / "menu-0-response.json").write_text(json.dumps(response))
    with pytest.raises(ValueError, match="attribution"):
        verify_decisions(tmp_path, [item], config, [row], initialization_failed=False)


def test_first_error_stop_rejects_followup_selection(tmp_path: Path) -> None:
    item, config, row, _ = fixture(tmp_path)
    with pytest.raises(ValueError, match="first transport"):
        verify_decisions(tmp_path, [item], config, [row], initialization_failed=True)


def test_refused_menu_cannot_receive_model_credit(tmp_path: Path) -> None:
    item, config, row, _ = fixture(tmp_path)
    item["body"] = None
    with pytest.raises(ValueError, match="no-question"):
        verify_decisions(tmp_path, [item], config, [row], initialization_failed=False)


def test_malformed_raw_receipt_cannot_keep_selected_tables(tmp_path: Path) -> None:
    item, config, row, response = fixture(tmp_path)
    del response["result"]["answers"]["q0"]["probabilities"]["C"]
    (tmp_path / "menu-0-response.json").write_text(json.dumps(response))
    with pytest.raises(ValueError, match="Malformed"):
        verify_decisions(tmp_path, [item], config, [row], initialization_failed=False)


def test_partial_selected_primary_ignores_fixed_tables() -> None:
    page = {"status": "error", "tables": [{"chosen": True}], "fixed_state": {"tables": [{"historical": True}]}}
    output = quality_predictions({"results": [page]})
    assert output[0]["status"] == "ok"
    assert output[0]["tables"] == [{"chosen": True}]
    assert page["status"] == "error"
