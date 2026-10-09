"""CPU-only integration checks for complete pipeline outputs and routing."""

from __future__ import annotations

import base64
import io
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

import pytest
from bench import pipeline_repair, pipeline_routing
from bench import pipeline_run as runner
from bench.pipeline_assembly import native_state
from conftest import build_raw_pdf
from PIL import Image

import pylopdf


def pdf_bytes(*, bordered: bool = True) -> bytes:
    stream = (
        "q 0 G 1 w 40 260 m 300 260 l 40 220 m 300 220 l 40 180 m 300 180 l "
        "40 180 m 40 260 l 170 180 m 170 260 l 300 180 m 300 260 l S Q\n"
        "BT /F1 12 Tf 50 235 Td (Name) Tj ET\n"
        "BT /F1 12 Tf 180 235 Td (Value) Tj ET\n"
        "BT /F1 12 Tf 50 195 Td (Alpha) Tj ET\n"
        "BT /F1 12 Tf 180 195 Td (42) Tj ET"
    )
    if not bordered:
        stream = "BT" + stream.split("BT", 1)[1]
    return build_raw_pdf(
        {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            2: "<< /Type /Pages /Kids [4 0 R] /Count 1 /MediaBox [0 0 340 300] "
            "/Resources << /Font << /F1 3 0 R >> >> >>",
            3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            4: "<< /Type /Page /Parent 2 0 R /Contents 5 0 R >>",
            5: f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        }
    )


def record(tmp_path: Path, *, bordered: bool = True) -> dict:
    pdf = tmp_path / "source.pdf"
    data = pdf_bytes(bordered=bordered)
    pdf.write_bytes(data)
    return {"id": "opaque-page", "pdf_path": str(pdf), "pdf_sha256": runner.sha(data), "page_number": 0}


def config(policy: str) -> dict:
    return {
        "policy": policy,
        "run_id": "stub-run",
        "image_edge": 256,
        "model": "stub-model",
        "context_rows": 1,
        "legend": True,
    }


def test_source_projection_cannot_include_page_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    table = object()
    native = {
        "row_count": 1,
        "col_count": 1,
        "cells": [[0, 0, 50, 20]],
        "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1}],
        "values": [["literal"]],
    }
    monkeypatch.setattr(runner, "observed_table", lambda observed: native if observed is table else None)
    calls = []
    page = SimpleNamespace(
        rect=[0, 0, 100, 100],
        family="SECRET",
        gold="SECRET",
        filename="SECRET",
        get_text=lambda _mode: [(1, 2, 3, 4, "literal", 8, 9, "SECRET")],
        find_tables=lambda **kwargs: calls.append(kwargs) or SimpleNamespace(tables=[table]),
    )
    projected = runner.source(page)
    assert set(projected) == {"page_size", "words", "vector_candidates"}
    assert projected["words"] == [{"id": "w0", "text": "literal", "bbox": [1, 2, 3, 4], "line": [8, 9]}]
    assert "SECRET" not in repr(projected)
    assert calls == [{"strategy": "lines"}]
    runner.source(page, text_tables=True)
    assert calls[-1] == {"strategy": "text"}


@pytest.mark.parametrize("edge", [256, 512, 1024])
def test_actual_full_page_image_edge_matches_record(edge: int) -> None:
    with pylopdf.open(stream=pdf_bytes()) as document:
        url, metadata = runner.image(document[0], edge)
    assert url is not None
    png = base64.b64decode(url.split(",", 1)[1])
    with Image.open(io.BytesIO(png)) as decoded:
        assert max(decoded.size) == edge
        assert list(decoded.size) == metadata["image_size"]
    assert runner.sha(png) == metadata["image_sha256"]
    assert len(png) == metadata["image_bytes"]
    assert runner.image(None, 0) == (None, {"image": "none"})


class VisibleText(HTMLParser):
    """Collect actual rendered text after decoding HTML escapes."""

    def __init__(self) -> None:
        """Initialize HTML text collection."""
        super().__init__(convert_charrefs=True)
        self.values: list[str] = []

    def handle_data(self, data: str) -> None:
        """Retain nonempty visible strings."""
        if data.strip():
            self.values.append(data.strip())


def test_markdown_preserves_spans_visible_literals_and_outside_words() -> None:
    page = {
        "page_size": [100, 100],
        "words": [
            {"id": "w0", "text": "A<&", "bbox": [5, 5, 15, 15]},
            {"id": "w1", "text": "B", "bbox": [5, 25, 15, 35]},
            {"id": "w2", "text": "C", "bbox": [55, 25, 65, 35]},
            {"id": "w3", "text": "Outside>", "bbox": [5, 70, 45, 80]},
        ],
        "vector_candidates": [
            {
                "row_count": 2,
                "col_count": 2,
                "cells": [[0, 0, 100, 20], None, [0, 20, 50, 40], [50, 20, 100, 40]],
                "spans": [
                    {"row": 0, "column": 0, "row_span": 1, "column_span": 2},
                    {"row": 1, "column": 0, "row_span": 1, "column_span": 1},
                    {"row": 1, "column": 1, "row_span": 1, "column_span": 1},
                ],
            }
        ],
    }
    state = native_state(page)
    text = runner.markdown(page, state)
    assert 'colspan="2"' in text
    assert text.count("<td") == 3
    assert "A&lt;&amp;" in text
    assert "Outside&gt;" in text
    parsed = VisibleText()
    parsed.feed(text)
    assert Counter(parsed.values) == Counter(w["text"] for w in page["words"])
    assert state["unresolved_ids"] == ["w3"]


@pytest.mark.parametrize("policy", ["native", "cascade"])
def test_native_and_vector_cascade_make_no_hosted_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, policy: str
) -> None:
    def unexpected(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Native route attempted hosted calls or heuristic proposals")

    monkeypatch.setattr(runner, "call", unexpected)
    monkeypatch.setattr(runner, "propose", unexpected)
    monkeypatch.setattr(runner, "image", unexpected)
    result = runner.process(record(tmp_path), config(policy), tmp_path, object())
    assert result["status"] == "ok"
    assert result["route"] == "native"
    assert result["calls"] == []
    assert result["source_conserved"]
    assert len(result["tables"]) == 1


def test_failed_structure_write_returns_error_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = runner.write_json

    def fail_structure(path: Path, value: object) -> None:
        if path.name.endswith("-structure.json"):
            message = "Simulated final structure write failure"
            raise OSError(message)
        original(path, value)

    monkeypatch.setattr(runner, "write_json", fail_structure)
    result = runner.process(record(tmp_path), config("native"), tmp_path, None)
    assert result["status"] == "error"
    assert result["error_type"] == "OSError"
    assert (tmp_path / "opaque-page-result.json").is_file()


def test_stubbed_assembly_response_abstains_without_losing_source(tmp_path: Path) -> None:
    ledger = tmp_path / "stub-ledger.json"
    ledger.write_text('{"requests":[]}')
    requests = []

    def request(payload: dict, **kwargs: object) -> dict:
        requests.append((payload, kwargs))
        choices = payload["questions"]["q0"]["criteria"]
        probabilities = {key: float(key == "unresolved") for key in choices}
        return {
            "result": {"answers": {"q0": {"type": "choice", "choice": "unresolved", "probabilities": probabilities}}},
            "entry": {"accounted_usd": 0},
            "replayed": False,
        }

    client = SimpleNamespace(ledger=ledger, request=request)
    settings = config("assembly")
    settings["image_edge"] = 0
    row = record(tmp_path)
    row.update(family="SECRET", gold="SECRET", expected="SECRET")
    result = runner.process(row, settings, tmp_path, client)
    assert result["status"] == "ok"
    assert len(requests) == 1
    assert requests[0][1]["replay"] is False
    assert "SECRET" not in json.dumps(requests[0][0])
    assert result["tables"] == []
    assert result["source_conserved"]
    assert set(result["unresolved_ids"]) == {w["id"] for w in result["source"]["words"]}
    assert len(result["calls"]) == 1
    markdown = (tmp_path / "opaque-page.md").read_text()
    for text in ("Name", "Value", "Alpha", "42"):
        assert text in markdown


@pytest.mark.parametrize("rotation", [90, 180, 270])
def test_source_rotation_normalization_aligns_complete_words_and_raster(rotation: int) -> None:
    raw = pdf_bytes()
    with pylopdf.open(stream=raw) as baseline:
        expected_source = runner.source(baseline[0])
        _, expected_image = runner.image(baseline[0], 256)
    with pylopdf.open(stream=raw) as owned:
        owned[0].set_rotation(rotation)
        rotated_bytes = owned.tobytes()
    frozen_hash = runner.sha(rotated_bytes)
    with pylopdf.open(stream=rotated_bytes) as owned:
        page = owned[0]
        assert page.rotation == rotation
        # Interpret and render rotated state first to exercise both cache invalidations.
        before = runner.source(page)
        runner.image(page, 256)
        page.set_rotation(0)
        after = runner.source(page)
        _, actual_image = runner.image(page, 256)
        assert Counter(w["text"] for w in before["words"]) == Counter(w["text"] for w in after["words"])
        assert after == expected_source
        assert actual_image["image_sha256"] == expected_image["image_sha256"]
        assert actual_image["image_size"] == expected_image["image_size"]
        assert page.rotation == 0
    assert runner.sha(rotated_bytes) == frozen_hash


@pytest.mark.parametrize("rotation", [90, 180, 270])
def test_process_normalizes_rotation_before_extraction_and_render(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rotation: int
) -> None:
    row = record(tmp_path, bordered=False)
    pdf = Path(row["pdf_path"])
    with pylopdf.open(stream=pdf.read_bytes()) as document:
        document[0].set_rotation(rotation)
        rotated = document.tobytes()
    pdf.write_bytes(rotated)
    row["pdf_sha256"] = runner.sha(rotated)
    original_source, original_image = runner.source, runner.image
    observed_rotations = []

    def source(page: object, **kwargs: object) -> dict:
        observed_rotations.append(("source", page.rotation))
        return original_source(page, **kwargs)

    def image(page: object, edge: int) -> tuple:
        observed_rotations.append(("image", page.rotation))
        return original_image(page, edge)

    def decision(*_args: object, **_kwargs: object) -> dict:
        return {"answer": {"choice": "unresolved"}}

    monkeypatch.setattr(runner, "source", source)
    monkeypatch.setattr(runner, "image", image)
    monkeypatch.setattr(runner, "call", decision)
    outputs = []
    for normalize in (False, True):
        output = tmp_path / str(normalize)
        output.mkdir()
        settings = config("assembly")
        settings["normalize_rotation"] = normalize
        outputs.append(runner.process(row, settings, output, object()))
    assert all(result["status"] == "ok" for result in outputs)
    assert observed_rotations == [("source", rotation), ("image", rotation), ("source", 0), ("image", 0)]
    assert outputs[0]["original_rotation"] == rotation
    assert outputs[1]["original_rotation"] == rotation
    assert not outputs[0]["rotation_normalized"]
    assert outputs[1]["rotation_normalized"]
    assert outputs[0]["source"]["words"][0]["bbox"] != outputs[1]["source"]["words"][0]["bbox"]
    assert pdf.read_bytes() == rotated
    assert runner.sha(pdf.read_bytes()) == row["pdf_sha256"]


@pytest.mark.parametrize("gate_choice", ["prose", "unresolved"])
def test_gated_out_skips_assembly_and_preserves_all_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gate_choice: str
) -> None:
    calls = []

    def decision(_client: object, request: dict, tag: str) -> dict:
        calls.append((request, tag))
        return {"answer": {"choice": gate_choice}}

    def unexpected(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Gated prose reached assembly packet")

    monkeypatch.setattr(runner, "call", decision)
    monkeypatch.setattr(runner, "packet", unexpected)
    result = runner.process(record(tmp_path, bordered=False), config("gated"), tmp_path, object())
    assert result["status"] == "ok"
    assert result["route"] == "gated_out"
    assert result["admission_choice"] == gate_choice
    assert len(calls) == 1
    assert result["tables"] == []
    assert result["source_conserved"]
    assert set(result["unresolved_ids"]) == {w["id"] for w in result["source"]["words"]}
    assert (tmp_path / "opaque-page-request-0.json").exists()
    assert not (tmp_path / "opaque-page-request-1.json").exists()


def test_gated_table_writes_two_distinct_requests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def decision(_client: object, request: dict, tag: str) -> dict:
        calls.append((request, tag))
        return {"answer": {"choice": "table" if len(calls) == 1 else "unresolved"}}

    monkeypatch.setattr(runner, "call", decision)
    result = runner.process(record(tmp_path, bordered=False), config("gated"), tmp_path, object())
    assert result["status"] == "ok"
    assert len(calls) == 2
    assert calls[0][1].endswith("/0")
    assert calls[1][1].endswith("/1")
    first = json.loads((tmp_path / "opaque-page-request-0.json").read_text())
    second = json.loads((tmp_path / "opaque-page-request-1.json").read_text())
    assert set(first["questions"]["q0"]["criteria"]) == {"table", "prose", "unresolved"}
    assert "table" not in second["questions"]["q0"]["criteria"]
    assert "c0" in second["questions"]["q0"]["criteria"]
    assert result["source_conserved"]


def test_adaptive_uses_source_route_image_and_repair_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    observed = {}

    def route(page: dict, seed: dict, candidates: list) -> dict:
        assert set(page) == {"words", "page_size", "vector_candidates"}
        assert seed in candidates
        observed["routing"] = True
        return {"action": "repair", "image_edge": 512, "context_rows": 3, "reason": "source geometry"}

    def image(_page: object, edge: int) -> tuple:
        observed["edge"] = edge
        return None, {"image_edge": edge}

    def repair_packet(_page: dict, _state: dict, _ops: list, **kwargs: object) -> str:
        observed["context"] = kwargs
        return "Literal source-only repair packet"

    def decision(*_args: object, **_kwargs: object) -> dict:
        return {"answer": {"choice": "keep"}}

    monkeypatch.setattr(pipeline_routing, "route", route)
    monkeypatch.setattr(pipeline_repair, "operations", lambda *_args: [{"id": "o0", "description": "Source edit"}])
    monkeypatch.setattr(pipeline_repair, "packet", repair_packet)
    monkeypatch.setattr(runner, "image", image)
    monkeypatch.setattr(runner, "call", decision)
    result = runner.process(record(tmp_path, bordered=False), config("adaptive"), tmp_path, object())
    assert result["status"] == "ok"
    assert result["route"] == "repair"
    assert observed == {"routing": True, "edge": 512, "context": {"context_rows": 3, "availability_legend": True}}
    assert result["routing"]["action"] == "repair"
    assert len(result["calls"]) == 1
    assert result["source_conserved"]


@pytest.mark.parametrize("action", ["keep_native", "assemble"])
def test_adaptive_respects_source_only_action(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, action: str) -> None:
    calls = []
    images = []
    monkeypatch.setattr(
        pipeline_routing, "route", lambda *_args: {"action": action, "image_edge": 1024, "context_rows": 1}
    )

    def image(_page: object, edge: int) -> tuple:
        images.append(edge)
        return None, {"image_edge": edge}

    def decision(*_args: object, **_kwargs: object) -> dict:
        calls.append(True)
        return {"answer": {"choice": "unresolved"}}

    monkeypatch.setattr(runner, "image", image)
    monkeypatch.setattr(runner, "call", decision)
    result = runner.process(record(tmp_path, bordered=False), config("adaptive"), tmp_path, object())
    assert result["status"] == "ok"
    assert result["source_conserved"]
    if action == "keep_native":
        assert result["route"] == "native"
        assert calls == []
        assert images == []
    else:
        assert result["route"] == "assembly"
        assert calls == [True]
        assert images == [1024]
