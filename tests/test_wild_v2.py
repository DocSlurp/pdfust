"""Checks for the wild-v2 DEV corpus builder (composition, truth schema, arithmetic and producers)."""

# ruff: noqa: PLC0415, E501
from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pypdf")
pytest.importorskip("reportlab")
pytest.importorskip("PIL")

from bench import wild_v2
from bench.wild_v2_templates import core

ROOT = Path(__file__).resolve().parents[1]
BUILT = ROOT / "bench/results/pdf-master-artifacts/wild-v2/docs"


@pytest.fixture(scope="module")
def docs() -> list[dict[str, Any]]:
    return wild_v2.compose()


def _truth(doc: dict[str, Any]) -> dict[str, Any]:
    """Project an unrendered document onto truth (no tools needed)."""
    doc = deepcopy(doc)
    for block in wild_v2._figures(doc):  # noqa: SLF001 - test-only access to the composition helper
        block.setdefault("text_in_image", [])
        block.setdefault("photo_id", None)
    facts = {"tagged": doc["producer"] in {"chromium", "libreoffice"} and doc["tagged"], "producer_detail": {}}
    return core.truth(doc, page_count=len(doc["pages"]), outline=[], pdf_facts=facts)


def test_registry_shape(docs: list[dict[str, Any]]) -> None:
    ids = [d["doc_id"] for d in docs]
    assert len(ids) == len(set(ids)) == 64
    pages = sorted(len(d["pages"]) for d in docs)
    assert pages[0] >= 3
    assert pages[-1] <= 15
    assert 4 <= pages[len(pages) // 2] <= 6
    producers = {d["producer"] for d in docs}
    assert producers == set(core.PRODUCERS)
    primary = {d["languages"][0].split("-")[0] if not d["languages"][0].startswith("zh") else d["languages"][0] for d in docs}
    expected = {"ja", "zh-CN", "zh-TW", "ko", "ar", "he", "hi", "th", "ru", "el", "de", "fr", "es", "pl", "vi", "tr", "en"}
    assert expected <= primary
    for doc in docs:
        assert doc["metadata"]["lang"] == doc["languages"][0]
        if doc["producer"] == "reportlab":
            assert doc["languages"][0].split("-")[0] not in {"ar", "he", "hi", "th"}


def test_composition_is_deterministic(docs: list[dict[str, Any]]) -> None:
    again = wild_v2.compose()
    first = json.dumps([wild_v2._authored_json(d) for d in docs], ensure_ascii=False, sort_keys=True)  # noqa: SLF001
    second = json.dumps([wild_v2._authored_json(d) for d in again], ensure_ascii=False, sort_keys=True)  # noqa: SLF001
    assert first == second


def test_truth_schema_and_arithmetic(docs: list[dict[str, Any]]) -> None:
    for doc in docs:
        record = _truth(doc)
        assert core.validate(record) == [], doc["doc_id"]
        assert core.check_arithmetic(record) == [], doc["doc_id"]


def test_totals_are_declared_for_financial_documents(docs: list[dict[str, Any]]) -> None:
    kinds_by_template: dict[str, set[str]] = {}
    for doc in docs:
        kinds_by_template.setdefault(doc["template"], set()).update(c["kind"] for c in doc.get("arithmetic", []))
    assert "running_balance" in kinds_by_template["bank_statement"]
    for template in ("bank_statement", "credit_card_statement", "retail_receipts", "utility_bill", "purchase_order"):
        assert kinds_by_template.get(template), template
    assert any("line_items" in kinds for kinds in kinds_by_template.values())


def test_continued_tables_repeat_headers_on_following_pages(docs: list[dict[str, Any]]) -> None:
    continued = 0
    for doc in docs:
        record = _truth(doc)
        tables = {b["id"]: b for b in record["blocks"] if b["kind"] == "table"}
        for segment in record["continued_tables"]:
            continued += 1
            block, previous = tables[segment["segment"]], tables[segment["continues_from"]]
            assert block["page"] == previous["page"] + 1, doc["doc_id"]
            assert block["values"][: block["header_rows"]] == previous["values"][: previous["header_rows"]]
            assert block["repeated_header"] is True
            assert block["logical_id"] == previous.get("logical_id", previous["id"])
    assert continued >= 20


def test_form_values_are_recorded(docs: list[dict[str, Any]]) -> None:
    forms = [d for d in docs if d["template"] == "government_form"]
    assert len(forms) == 4
    for doc in forms:
        fields = [b for b in _truth(doc)["blocks"] if b["kind"] == "form_field"]
        assert len(fields) >= 8, doc["doc_id"]
        assert len({f["name"] for f in fields}) == len(fields)
        assert {f["field_type"] for f in fields} >= {"text", "checkbox"}
        for field in fields:
            if field["field_type"] == "checkbox":
                assert isinstance(field["value"], bool)
            else:
                assert isinstance(field["value"], str)
                assert field["value"]
            if field["field_type"] == "choice":
                assert field["value"] in field["options"]


def test_arithmetic_checks_detect_errors() -> None:
    rows = [["01/03", "Opening", "", "", "100.00"], ["02/03", "Shop", "10.00", "", "90.00"], ["03/03", "Pay", "", "50.00", "140.00"]]
    segments = core.continued("t1", [["Date", "Details", "Out", "In", "Balance"]], rows, [2, 1])
    record = {"blocks": [{**s, "page": i + 1} for i, s in enumerate(segments)],
              "arithmetic": [{"kind": "running_balance", "table": "t1", "debit": 2, "credit": 3, "balance": 4}]}
    assert core.check_arithmetic(record) == []
    record["blocks"][1]["values"][1][4] = "141.00"
    assert core.check_arithmetic(record)
    items = {"blocks": [{"kind": "table", "id": "t2", "header_rows": 1, "page": 1,
                         "values": [["Qty", "Unit", "Amount"], ["3", "1,25", "3,75"], ["2,5", "4,10", "10,25"]]}],
             "arithmetic": [{"kind": "line_items", "table": "t2", "quantity": 0, "unit_price": 1, "amount": 2, "decimal": ","}]}
    assert core.check_arithmetic(items) == []
    items["blocks"][0]["values"][2][2] = "10,20"
    assert core.check_arithmetic(items)
    assert core.amount("△1,234") == -1234
    assert core.amount("١٬٢٣٤٫٥٠") == 123450


def _small(producer: str) -> dict[str, Any]:
    rows = [[f"2026-03-{i:02d}", f"Order {i:03d} for Harbor Café", f"{i * 1.5:.2f}"] for i in range(1, 9)]
    segments = core.continued("t1", [["Date", "Description", "Amount"]], rows, [5, 3], align=["l", "l", "r"])
    pages = [[core.H(1, "Delivery log"), core.P("Deliveries to Harbor Café in March."), segments[0]],
             [segments[1], core.code("print('ok')", "python")], [core.P("Closing note.")]]
    if producer == "reportlab":
        pages[2].append(core.form("Sign-off", [[core.field("name", "Name", "Zoë Ångström"), core.field("ok", "Approved", True, field_type="checkbox")]]))
    return {"doc_id": f"t-{producer}", "producer": producer, "template": "test", "page_size": "A4", "languages": ["en-US"],
            "dir": "ltr", "tagged": producer != "reportlab",
            "metadata": {"title": "Delivery log", "author": "Test", "subject": "Test", "keywords": ["test"], "lang": "en-US",
                         "created": "2026-03-31T12:00:00Z"},
            "theme": {}, "running_footer": "Page {page} of {pages}", "pages": pages}


@pytest.mark.parametrize("producer", ["reportlab", "pylopdf"])
def test_python_producers_are_deterministic(producer: str, tmp_path: Path) -> None:
    from bench.wild_v2_templates import render_pylopdf, render_reportlab

    render = render_reportlab.render if producer == "reportlab" else render_pylopdf.render
    first, second = tmp_path / "a.pdf", tmp_path / "b.pdf"
    assert render(_small(producer), tmp_path, first) == 3
    assert render(_small(producer), tmp_path, second) == 3
    assert first.read_bytes() == second.read_bytes()


def test_reportlab_form_filled_by_pylopdf(tmp_path: Path) -> None:
    from bench.wild_v2_templates import render_reportlab

    import pylopdf

    doc = _small("reportlab")
    pdf = tmp_path / "source.pdf"
    render_reportlab.render(doc, tmp_path, pdf)
    detail = wild_v2.fill_form(doc, pdf)
    assert detail["fields"] == 2
    values = {f["name"]: f["value"] for f in pylopdf.Document(str(pdf)).get_form_fields()}
    assert values["name"] == "Zoë Ångström"
    assert values["ok"] not in {None, "", "Off"}


@pytest.mark.parametrize(("producer", "tool"), [("chromium", "chromium"), ("libreoffice", "soffice")])
def test_external_producers_keep_authored_pages(producer: str, tool: str, tmp_path: Path) -> None:
    if shutil.which(tool) is None:
        pytest.skip(f"{tool} not installed")
    doc = _small(producer)
    record = wild_v2.build_one(doc, tmp_path, {"chromium": "", "soffice": ""})
    assert record["page_count"] == 3
    assert record["page_check"].get("elsewhere", 0) == 0
    truth = json.loads((tmp_path / doc["doc_id"] / "truth.json").read_text())
    assert truth["continued_tables"] == [{"logical_id": "t1", "segment": "t1-2", "continues_from": "t1", "page": 2}]


def test_built_corpus_truth_when_present() -> None:
    files = sorted(BUILT.glob("*/truth.json"))
    if not files:
        pytest.skip("wild-v2 corpus not built")
    for path in files:
        record = json.loads(path.read_text())
        assert core.validate(record) == [], path.parent.name
        assert core.check_arithmetic(record) == [], path.parent.name
        assert (path.parent / "source.pdf").is_file()
