"""Fast checks for the wild-v1 realistic document generator (bench/wild_documents.py)."""

# ruff: noqa: C901, E501, PT018

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

wild = pytest.importorskip("bench.wild_documents")
from bench.wild_templates import model  # noqa: E402
from bench.wild_templates.common import shape  # noqa: E402

TOTAL_TEMPLATES = {"vendor_invoice", "expense_report", "travel_itinerary", "grant_budget", "quarterly_financial_summary"}


@pytest.fixture(scope="module")
def plans() -> list[dict[str, Any]]:
    return wild.load_plans()


@pytest.fixture(scope="module")
def docs(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return wild.compose(plans)


def _plan(plans: list[dict[str, Any]], doc: dict[str, Any]) -> dict[str, Any]:
    return next(p for p in plans if p["id"] == doc["base_plan_id"])


def _tables(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [b for b in model.flatten(doc["blocks"]) if b["kind"] == "table"]


def test_composition_is_deterministic(plans: list[dict[str, Any]], docs: list[dict[str, Any]]) -> None:
    again = wild.compose(plans)
    first = [json.dumps(wild.truth(d, page_count=1, outline=[]), ensure_ascii=False, sort_keys=True) for d in docs]
    second = [json.dumps(wild.truth(d, page_count=1, outline=[]), ensure_ascii=False, sort_keys=True) for d in again]
    assert first == second


def test_plan_structure_is_preserved(plans: list[dict[str, Any]], docs: list[dict[str, Any]]) -> None:
    for doc in docs:
        plan = _plan(plans, doc)
        assert plan["family"] == doc["family"]
        derived = [t for t in _tables(doc) if t.get("plan_table") is not None]
        assert len(derived) == len(plan["tables"]), doc["doc_id"]
        if doc["family"] == "negative":
            assert not _tables(doc)
        for table in derived:
            spec = shape(plan, table["plan_table"])
            values = table["values"]
            assert len(values) == spec["rows"], doc["doc_id"]
            assert len(values) <= plan["tables"][table["plan_table"]]["target"]["row_count"]
            assert all(len(row) == spec["cols"] for row in values)
            assert table["spans"] == model.table_spans(values, spec["merges"])
            source_spans = {(s["row"], s["column"], s["row_span"], s["column_span"])
                            for s in plan["tables"][table["plan_table"]]["target"]["spans"] if s["row"] < len(values)}
            assert {(s["row"], s["column"], s["row_span"], s["column_span"]) for s in table["spans"]} == source_spans
            body = values[table["header_rows"]:]
            for column, kind in enumerate(spec["kinds"]):
                cells = [row[column] for row in body if row[column]]
                if kind == "usd":
                    assert all(any(ch.isdigit() for ch in cell) for cell in cells), (doc["doc_id"], cells)
                if kind == "date":
                    assert all(any(ch.isdigit() for ch in cell) for cell in cells), (doc["doc_id"], cells)
            if doc["family"] == "unnamed":
                assert table["header_rows"] == 0 and values[0] == [""] * spec["cols"]
            if doc["family"] == "merged_headers":
                assert spec["merges"] and table["header_rows"] == 2
            if doc["family"] == "wrapped":
                column = spec["kinds"].index("word2")
                end = table["total_rows"][0] if table["total_rows"] else len(values)
                lengths = [len(row[column].split()) for row in values[table["header_rows"]:end]]
                assert min(lengths) >= 10, doc["doc_id"]
        if doc["family"] == "mixed":
            assert {t["rendering"] for t in _tables(doc)} >= {"ruled", "borderless"}
        if doc["family"] == "borderless":
            assert derived[0]["rendering"] == "borderless"


def test_totals_add_up(docs: list[dict[str, Any]]) -> None:
    checked = 0
    for doc in docs:
        for table in _tables(doc):
            if not table.get("total_rows"):
                continue
            total_row = table["total_rows"][0]
            body = table["values"][table["header_rows"]:total_row]
            for column, align in enumerate(table["align"]):
                total = table["values"][total_row][column]
                if align != "r" or not total or not any(ch.isdigit() for ch in total) or total.endswith("%"):
                    continue
                if "." in total and total.replace(".", "").isdigit():
                    numbers = [float(row[column]) for row in body if row[column].replace(".", "").isdigit()]
                    assert abs(sum(numbers) - float(total)) < 1e-6, doc["doc_id"]
                else:
                    assert sum(model.parse_money(row[column]) for row in body) == model.parse_money(total), doc["doc_id"]
                checked += 1
    assert checked >= 10
    templates = {d["template"] for d in docs if any(t.get("total_rows") for t in _tables(d))}
    assert templates <= TOTAL_TEMPLATES | {"grant_budget"}
    assert {"vendor_invoice", "expense_report"} <= templates


def test_invoice_line_items_follow_rates(docs: list[dict[str, Any]]) -> None:
    invoice = next(d for d in docs if d["doc_id"] == "w-ruled-invoice-01")
    rates = {"Senior engineer": 18500, "Engineer": 14500, "Technician": 9500}
    table = _tables(invoice)[0]
    for date_, amount, description, _package, hours in table["values"][1:table["total_rows"][0]]:
        assert date_
        role = description.split(" — ")[0]
        if role in rates:
            assert model.parse_money(amount) == round(rates[role] * float(hours))
    facture = next(d for d in docs if d["doc_id"] == "w-ruled-facture-03")
    table = _tables(facture)[0]
    for qty, _name, unit, line, *_ in table["values"][1:table["total_rows"][0]]:
        assert int(qty) * model.parse_money(unit) == model.parse_money(line)


def test_every_unicode_feature_is_covered(docs: list[dict[str, Any]]) -> None:
    covered: set[str] = set()
    for doc in docs:
        features = wild.truth(doc, page_count=1, outline=[])["unicode_features"]
        assert features, doc["doc_id"]
        covered |= set(features)
    assert covered == set(model.UNICODE_FEATURES)


def test_feature_detection_is_truthful() -> None:
    assert model.detect_features(["plain ascii text"]) == []
    assert "nfd_text" in model.detect_features(["Việt"])
    assert "emoji" not in model.detect_features(["☐ checkbox"])
    assert set(model.detect_features(["1.234,56 € am 14.03.2026"])) == {"nbsp", "currency", "thousands_separators", "date_formats"}
    assert "rtl_numbers" in model.detect_features(["שלום 123"])


def test_truth_blocks_validate(docs: list[dict[str, Any]]) -> None:
    for doc in docs:
        record = wild.truth(doc, page_count=2, outline=[{"level": 1, "title": "x", "page": 1}])
        assert model.validate_truth(record) == [], doc["doc_id"]
        assert record["languages"] == doc["languages"]
        assert record["metadata"]["lang"] == doc["metadata"]["lang"]
        kinds = [b["kind"] for b in record["blocks"]]
        if doc.get("running_footer"):
            assert kinds.count("footer") == 2 and kinds[-1] == "footer"
        assert all("**" not in json.dumps(b, ensure_ascii=False) for b in record["blocks"])
    broken = wild.truth(docs[0], page_count=1, outline=[])
    broken["blocks"].append({"kind": "table", "id": "x", "rendering": "ruled", "header_rows": 1, "values": [["a"], ["b", "c"]],
                             "spans": [], "caption": ""})
    assert model.validate_truth(broken)


def test_locale_formatting() -> None:
    assert model.money(123456, "de") == "1.234,56 €"
    assert model.money(12345678, "hi") == "₹1,23,456.78"
    assert model.money(-5000, "en-US") == "−$50.00"
    assert model.money(1250000, "vi") == "1.250.000 ₫"
    assert model.parse_money("(€1.234,56)") == -123456


@pytest.mark.skipif(shutil.which("chromium") is None or shutil.which("soffice") is None, reason="chromium/soffice missing")
def test_render_two_documents(tmp_path: Path) -> None:
    report = wild.build(tmp_path, only=["w-ruled-invoice-01", "w-merged-budget-15"])
    assert [d["doc_id"] for d in report["documents"]] == ["w-ruled-invoice-01", "w-merged-budget-15"]
    for entry in report["documents"]:
        assert entry["checks"]["tagged"] and entry["checks"]["title_matches"] and entry["checks"]["outline_present"]
        truth = json.loads((tmp_path / "docs" / entry["doc_id"] / "truth.json").read_text(encoding="utf-8"))
        assert model.validate_truth(truth) == []
        assert truth["page_count"] == entry["page_count"] >= 1
        assert truth["outline"]
