"""CPU-only integration checks for complete pipeline outputs and routing."""

from __future__ import annotations

import base64
import io
import json
import sys
from collections import Counter
from contextlib import nullcontext
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast

import pytest
from bench import pipeline_column_consensus, pipeline_repair, pipeline_routing
from bench import pipeline_run as runner
from bench.pipeline_assembly import native_state
from conftest import build_raw_pdf
from PIL import Image

import pdfust


def pdf_bytes(*, bordered: bool = True, third_row: bool = False) -> bytes:
    stream = (
        "q 0 G 1 w 40 260 m 300 260 l 40 220 m 300 220 l 40 180 m 300 180 l "
        "40 180 m 40 260 l 170 180 m 170 260 l 300 180 m 300 260 l S Q\n"
        "BT /F1 12 Tf 50 235 Td (Name) Tj ET\n"
        "BT /F1 12 Tf 180 235 Td (Value) Tj ET\n"
        "BT /F1 12 Tf 50 195 Td (Alpha) Tj ET\n"
        "BT /F1 12 Tf 180 195 Td (42) Tj ET"
    )
    if third_row:
        stream += "\nBT /F1 12 Tf 50 165 Td (Beta) Tj ET\nBT /F1 12 Tf 178 165 Td (7) Tj ET"
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


def record(tmp_path: Path, *, bordered: bool = True, third_row: bool = False) -> dict:
    pdf = tmp_path / "source.pdf"
    data = pdf_bytes(bordered=bordered, third_row=third_row)
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

    def find_tables(**kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        return SimpleNamespace(tables=[table])

    page = SimpleNamespace(
        rect=[0, 0, 100, 100],
        family="SECRET",
        gold="SECRET",
        filename="SECRET",
        get_text=lambda _mode: [(1, 2, 3, 4, "literal", 8, 9, "SECRET")],
        find_tables=find_tables,
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
    with pdfust.open(stream=pdf_bytes()) as document:
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
    page: dict[str, Any] = {
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
    result = runner.process(record(tmp_path), config(policy), tmp_path, cast("Any", object()))
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

    client: Any = SimpleNamespace(ledger=ledger, request=request)
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
    with pdfust.open(stream=raw) as baseline:
        expected_source = runner.source(baseline[0])
        _, expected_image = runner.image(baseline[0], 256)
    with pdfust.open(stream=raw) as owned:
        owned[0].set_rotation(rotation)
        rotated_bytes = owned.tobytes()
    frozen_hash = runner.sha(rotated_bytes)
    with pdfust.open(stream=rotated_bytes) as owned:
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
    with pdfust.open(stream=pdf.read_bytes()) as document:
        document[0].set_rotation(rotation)
        rotated = document.tobytes()
    pdf.write_bytes(rotated)
    row["pdf_sha256"] = runner.sha(rotated)
    original_source, original_image = runner.source, runner.image
    observed_rotations = []

    def source(page: pdfust.Page, **kwargs: object) -> dict:
        observed_rotations.append(("source", page.rotation))
        return original_source(page, **cast("Any", kwargs))

    def image(page: pdfust.Page, edge: int) -> tuple:
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
        outputs.append(runner.process(row, settings, output, cast("Any", object())))
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
    result = runner.process(record(tmp_path, bordered=False), config("gated"), tmp_path, cast("Any", object()))
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
    result = runner.process(record(tmp_path, bordered=False), config("gated"), tmp_path, cast("Any", object()))
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
    observed: dict[str, Any] = {}

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
    result = runner.process(record(tmp_path, bordered=False), config("adaptive"), tmp_path, cast("Any", object()))
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
    result = runner.process(record(tmp_path, bordered=False), config("adaptive"), tmp_path, cast("Any", object()))
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


@pytest.mark.parametrize("initial_empty", [False, True])
@pytest.mark.parametrize("enabled", [False, True])
def test_ocr_only_attempts_empty_pages_when_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, initial_empty: bool, enabled: bool
) -> None:
    page = SimpleNamespace(rotation=0, rect=[0, 0, 100, 100])
    words = [] if initial_empty else [(5, 5, 25, 15, "Native", 0, 0)]
    calls = []
    engine = object()
    page.get_text = lambda _mode: words
    page.find_tables = lambda **_kwargs: SimpleNamespace(tables=[])

    def apply_ocr(*, dpi: int, engine: object) -> list:
        calls.append((dpi, engine))
        words.append((5, 5, 25, 15, "Recognized", 0, 0))
        return [{"text": "Recognized", "bbox": [5, 5, 25, 15]}]

    page.apply_ocr = apply_ocr
    monkeypatch.setattr(pdfust, "open", lambda **_kwargs: nullcontext([page]))
    engine_calls = []

    def load_engine() -> object:
        engine_calls.append(True)
        return engine

    monkeypatch.setattr(runner, "ocr_engine", load_engine)
    settings = config("native")
    settings["ocr_empty"] = enabled
    result = runner.process(record(tmp_path), settings, tmp_path, None)
    attempted = initial_empty and enabled
    assert len(calls) == int(attempted)
    assert len(engine_calls) == int(attempted)
    if attempted:
        assert calls == [(150, engine)]
        assert result["ocr"]["recognized_regions"] == 1
        assert result["ocr"]["threads"] == 4
        assert result["ocr"]["dpi"] == 150
        assert result["ocr"]["engine"] == "RTen native CPU"
        assert result["ocr"]["wall_seconds"] >= 0
        assert result["ocr"]["cpu_seconds"] >= 0
        assert result["source"]["words"][0]["text"] == "Recognized"
        assert result["source_conserved"]
    else:
        assert "ocr" not in result
    assert result["status"] == ("unsupported_no_text" if initial_empty and not enabled else "ok")


@pytest.mark.parametrize("opaque_id", ["empty-0", "empty-1", "empty-2"])
def test_zero_recognition_remains_explicitly_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, opaque_id: str
) -> None:
    page = SimpleNamespace(
        rotation=0,
        rect=[0, 0, 100, 100],
        get_text=lambda _mode: [],
        find_tables=lambda **_kwargs: SimpleNamespace(tables=[]),
        apply_ocr=lambda **_kwargs: [],
    )
    monkeypatch.setattr(pdfust, "open", lambda **_kwargs: nullcontext([page]))
    monkeypatch.setattr(runner, "ocr_engine", object)
    row = record(tmp_path)
    row["id"] = opaque_id
    settings = config("native")
    settings["ocr_empty"] = True
    result = runner.process(row, settings, tmp_path, None)
    assert result["status"] == "unsupported_no_text"
    assert result["ocr"]["recognized_regions"] == 0
    assert result["tables"] == []
    assert result["calls"] == []
    assert "source" not in result
    assert not (tmp_path / f"{opaque_id}.md").exists()
    assert not (tmp_path / f"{opaque_id}-structure.json").exists()


@pytest.mark.parametrize("policy", ["adaptive", "gated"])
def test_single_candidate_skips_hosted_decisions_without_fabricating_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, policy: str
) -> None:
    monkeypatch.setattr(runner, "propose", lambda page: [native_state(page)])
    monkeypatch.setattr(
        pipeline_routing, "route", lambda *_args: {"action": "assemble", "image_edge": 512, "context_rows": 3}
    )

    def unexpected(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Single-candidate policy performed unnecessary hosted call or rendering")

    monkeypatch.setattr(runner, "call", unexpected)
    monkeypatch.setattr(runner, "image", unexpected)
    result = runner.process(record(tmp_path, bordered=False), config(policy), tmp_path, cast("Any", object()))
    assert result["status"] == "ok"
    assert result["route"] == "no_alternative"
    assert result["calls"] == []
    assert result["tables"] == []
    assert result["source_conserved"]
    assert set(result["unresolved_ids"]) == {w["id"] for w in result["source"]["words"]}
    assert not (tmp_path / "opaque-page-request-0.json").exists()


@pytest.mark.parametrize(
    "probabilities",
    [
        {"table": 0.7, "prose": 0.2, "unresolved": 0.1},
        {"table": 0.55, "prose": 0.4, "unresolved": 0.05},
    ],
)
@pytest.mark.parametrize("review_choice", ["prose", "table"])
def test_uncertain_gate_review_is_independent_and_uses_distinct_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, probabilities: dict, review_choice: str
) -> None:
    requests = []
    primary = {"choice": "table", "probabilities": probabilities, "diagnostic": "PRIMARY_ANSWER_ONLY_SECRET"}

    def decision(_client: object, request: dict, tag: str) -> dict:
        requests.append((request, tag))
        if len(requests) == 1:
            return {"answer": primary}
        if len(requests) == 2:
            return {"answer": {"choice": review_choice}}
        return {"answer": {"choice": "unresolved"}}

    monkeypatch.setattr(runner, "call", decision)
    settings = config("gated")
    settings.update(image_edge=0, gate_review_model="anthropic/claude-sonnet-5.5")
    row = record(tmp_path, bordered=False)
    row.update(family="REFERENCE_ONLY_SECRET", expected="REFERENCE_ONLY_SECRET")
    result = runner.process(row, settings, tmp_path, cast("Any", object()))
    assert result["status"] == "ok"
    assert result["gate_review"]["primary_answer"] == primary
    assert result["admission_choice"] == review_choice
    expected_calls = 2 if review_choice == "prose" else 3
    assert len(requests) == expected_calls
    primary_request, review_request = requests[0][0], requests[1][0]
    assert review_request["model"] == settings["gate_review_model"]
    assert review_request["messages"][-1]["role"] == "user"
    assert review_request["messages"][-1]["content"] == primary_request["state"]
    assert json.loads(review_request["messages"][1]["content"])["questions"] == primary_request["questions"]
    assert "PRIMARY_ANSWER_ONLY_SECRET" not in json.dumps(review_request)
    assert "REFERENCE_ONLY_SECRET" not in json.dumps(review_request)
    for step in range(expected_calls):
        assert requests[step][1].endswith(f"/{step}")
        saved = json.loads((tmp_path / f"opaque-page-request-{step}.json").read_text())
        assert saved == requests[step][0]
    assert not (tmp_path / f"opaque-page-request-{expected_calls}.json").exists()
    if review_choice == "prose":
        assert result["route"] == "gated_out"
        assert result["tables"] == []
    else:
        assert "c0" in requests[2][0]["questions"]["q0"]["criteria"]
    assert result["source_conserved"]


@pytest.mark.parametrize(
    "probabilities",
    [
        {"table": 0.95, "prose": 0.04, "unresolved": 0.01},
        {"table": 0.8, "prose": 0.1, "unresolved": 0.1},
        {"table": 0.95},
    ],
)
def test_strong_gate_score_skips_review(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, probabilities: dict) -> None:
    requests = []

    def decision(_client: object, request: dict, tag: str) -> dict:
        requests.append((request, tag))
        return (
            {"answer": {"choice": "table", "probabilities": probabilities}}
            if len(requests) == 1
            else {"answer": {"choice": "unresolved"}}
        )

    monkeypatch.setattr(runner, "call", decision)
    settings = config("gated")
    settings.update(image_edge=0, gate_review_model="anthropic/claude-sonnet-5.5")
    result = runner.process(record(tmp_path, bordered=False), settings, tmp_path, cast("Any", object()))
    assert result["status"] == "ok"
    assert len(requests) == 2
    assert all(request["model"] == settings["model"] for request, _tag in requests)
    assert "gate_review" not in result
    assert result["source_conserved"]
    assert "c0" in requests[1][0]["questions"]["q0"]["criteria"]
    assert not (tmp_path / "opaque-page-request-2.json").exists()


@pytest.fixture
def compact_module(monkeypatch: pytest.MonkeyPatch) -> list:
    calls = []
    module: Any = ModuleType("bench.pipeline_compact_packet")

    def packet(page: dict, candidates: list) -> str:
        calls.append((deepcopy(page), deepcopy(candidates)))
        return "COMPLETE_COMPACT_SOURCE_PACKET"

    module.packet = packet
    monkeypatch.setitem(sys.modules, "bench.pipeline_compact_packet", module)
    return calls


def test_optional_consensus_preserves_existing_prefix_and_raw_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compact_module: list
) -> None:
    captured: dict[str, Any] = {}
    original = pipeline_column_consensus.propose

    def consensus(page: dict, existing: list) -> list:
        captured["source"] = deepcopy(page)
        captured["existing"] = deepcopy(existing)
        combined = original(page, existing)
        assert combined[: len(existing)] == captured["existing"]
        return combined

    requests = []

    def decision(_client: object, request: dict, _tag: str) -> dict:
        requests.append(request)
        return {"answer": {"choice": "unresolved"}}

    monkeypatch.setattr(pipeline_column_consensus, "propose", consensus)
    monkeypatch.setattr(runner, "call", decision)
    row = record(tmp_path, bordered=False, third_row=True)
    frozen_bytes = Path(row["pdf_path"]).read_bytes()
    row.update(expected="REFERENCE_SECRET", family="REFERENCE_SECRET")
    settings = config("assembly")
    settings.update(column_consensus=True, compact_packet=True, image_edge=0)
    result = runner.process(row, settings, tmp_path, cast("Any", object()))
    assert result["status"] == "ok"
    assert result["candidates"][: len(captured["existing"])] == captured["existing"]
    assert len(result["candidates"]) >= len(captured["existing"])
    assert len(compact_module) == 1
    assert requests[0]["state"] == "COMPLETE_COMPACT_SOURCE_PACKET"
    assert captured["source"] == result["source"]
    assert compact_module[0][0] == result["source"]
    assert compact_module[0][1] == result["candidates"]
    assert "REFERENCE_SECRET" not in repr(captured)
    assert set(captured["source"]) == {"page_size", "words", "vector_candidates"}
    assert result["source_conserved"]
    assert Path(row["pdf_path"]).read_bytes() == frozen_bytes
    assert runner.sha(frozen_bytes) == row["pdf_sha256"]


@pytest.mark.parametrize("policy", ["native", "cascade", "gated", "adaptive"])
def test_optional_flags_preserve_native_fast_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compact_module: list, policy: str
) -> None:
    def unexpected(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Native fast path invoked optional proposals, packet, image or host")

    monkeypatch.setattr(runner, "propose", unexpected)
    monkeypatch.setattr(pipeline_column_consensus, "propose", unexpected)
    monkeypatch.setattr(runner, "image", unexpected)
    monkeypatch.setattr(runner, "call", unexpected)
    settings = config(policy)
    settings.update(column_consensus=True, compact_packet=True)
    result = runner.process(record(tmp_path), settings, tmp_path, cast("Any", object()))
    assert result["status"] == "ok"
    assert compact_module == []
    assert result["calls"] == []
    assert len(result["tables"]) == 1
    assert result["source_conserved"]


@pytest.mark.parametrize("policy", ["gated", "repair"])
def test_compact_packet_skipped_for_admission_rejection_and_local_repair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compact_module: list, policy: str
) -> None:
    requests = []

    def decision(_client: object, request: dict, _tag: str) -> dict:
        requests.append(request)
        return {"answer": {"choice": "prose" if policy == "gated" else "keep"}}

    monkeypatch.setattr(runner, "call", decision)
    monkeypatch.setattr(pipeline_repair, "operations", lambda *_args: [{"id": "o0", "description": "Source edit"}])
    monkeypatch.setattr(pipeline_repair, "packet", lambda *_args, **_kwargs: "SOURCE_REPAIR_PACKET")
    settings = config(policy)
    settings.update(compact_packet=True, image_edge=0)
    result = runner.process(record(tmp_path, bordered=False), settings, tmp_path, cast("Any", object()))
    assert result["status"] == "ok"
    assert compact_module == []
    assert len(requests) == 1
    assert result["source_conserved"]


def test_optional_flags_disabled_use_original_packet_and_proposals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compact_module: list
) -> None:
    def unexpected(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Disabled consensus proposer was invoked")

    monkeypatch.setattr(pipeline_column_consensus, "propose", unexpected)
    requests = []

    def decision(_client: object, request: dict, _tag: str) -> dict:
        requests.append(request)
        return {"answer": {"choice": "unresolved"}}

    monkeypatch.setattr(runner, "call", decision)
    settings = config("assembly")
    settings.update(column_consensus=False, compact_packet=False, image_edge=0)
    result = runner.process(record(tmp_path, bordered=False), settings, tmp_path, cast("Any", object()))
    assert result["status"] == "ok"
    assert compact_module == []
    assert "Choose one complete page assembly" in requests[0]["state"]
    assert result["source_conserved"]


@pytest.mark.parametrize(("policy", "bordered", "expected_calls"), [("assembly", False, 1), ("gated", True, 0)])
def test_readable_packet_is_optional_and_keeps_native_fast_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, policy: str, *, bordered: bool, expected_calls: int
) -> None:
    packets: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    module: Any = ModuleType("bench.pipeline_readable_packet")

    def readable(page: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
        packets.append({"source": deepcopy(page), "candidates": deepcopy(candidates)})
        return "READABLE_COMPLETE_EVIDENCE"

    def decision(_client: object, request: dict[str, Any], _tag: str) -> dict[str, Any]:
        requests.append(request)
        return {"answer": {"choice": "unresolved"}}

    module.packet = readable
    monkeypatch.setitem(sys.modules, "bench.pipeline_readable_packet", module)
    monkeypatch.setattr(runner, "call", decision)
    settings = config(policy)
    settings.update(readable_packet=True, image_edge=0)
    row = record(tmp_path, bordered=bordered, third_row=True)
    row.update(expected="REFERENCE_SECRET", family="REFERENCE_SECRET")
    result = runner.process(row, settings, tmp_path, cast("Any", object()))
    assert result["status"] == "ok"
    assert result["source_conserved"]
    assert len(packets) == len(requests) == expected_calls
    if expected_calls:
        assert packets[0]["source"] == result["source"]
        assert packets[0]["candidates"] == result["candidates"]
        assert requests[0]["state"] == "READABLE_COMPLETE_EVIDENCE"
        assert "REFERENCE_SECRET" not in repr(packets)


def test_packet_encodings_are_mutually_exclusive_before_source_loading(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="only one optional packet"):
        runner.run(tmp_path / "missing.json", tmp_path / "output", {"compact_packet": True, "readable_packet": True})
    assert not (tmp_path / "output").exists()


def test_cli_rejects_multiple_packet_encodings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pipeline_run",
            "--manifest",
            str(tmp_path / "missing.json"),
            "--output",
            str(tmp_path / "output"),
            "--policy",
            "assembly",
            "--compact-packet",
            "--readable-packet",
        ],
    )
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("matching", [False, True])
def test_explicit_retry_is_scoped_to_the_original_request_hash(tmp_path: Path, *, matching: bool) -> None:
    request = runner.body("perplexity/pplx-decider-v1.1-27b", "literal source", {"unresolved": "keep"}, None)
    request_hash = runner.sha(json.dumps(request, separators=(",", ":")).encode())
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "requests": [
                    {
                        "index": 7,
                        "tag": "P001/earlier",
                        "accounted_usd": 0.3,
                        "request_sha256": request_hash if matching else "f" * 64,
                    }
                ]
            }
        )
    )
    transmissions: list[dict[str, Any]] = []

    def transmit(_request: dict[str, Any], **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401 - capture the client contract.
        transmissions.append(kwargs)
        message = "Test transport reached"
        raise RuntimeError(message)

    client = cast("Any", SimpleNamespace(ledger=ledger, request=transmit))
    with pytest.raises(RuntimeError, match="Test transport reached"):
        runner.call(client, request, "P001/new", retry_failed_index=7, retry_reason="Inspected transient HTTP 500")
    assert len(transmissions) == 1
    assert transmissions[0]["replay"] is False
    if matching:
        assert transmissions[0]["retry_failed_index"] == 7
        assert transmissions[0]["retry_reason"] == "Inspected transient HTTP 500"
    else:
        assert "retry_failed_index" not in transmissions[0]
        assert "retry_reason" not in transmissions[0]


def test_retry_requires_index_and_reason_before_source_loading(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="both a ledger index"):
        runner.run(tmp_path / "missing.json", tmp_path / "output", {"retry_failed_index": 7})
    assert not (tmp_path / "output").exists()
