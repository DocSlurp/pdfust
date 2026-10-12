from __future__ import annotations

import json
import urllib.error
from email.message import Message
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from bench import structure
from bench.feature_cases import FeatureCase, page_pdf, text_op
from bench.structure_cases import StructureCase
from bench.structure_core import markdown_spans, markdown_tables, render_tables, score_tables, validate_patch
from bench.structure_hosted import HostedVision
from bench.structure_summary import summarize

import pdfust


def test_summary_keeps_failed_calls_in_reference_denominators() -> None:
    reference = {
        "table": {
            "score": {"gold_available": True, "expected_tables": 1, "total_cells": 6, "relationship_expected": 7},
            "record_checks": {"total": 3},
        },
        "prose": {"score": {"gold_available": True, "expected_tables": 0}},
    }
    failed: list[dict[str, Any]] = [
        {"case": "table", "adapter": "patch", "error": "invalid JSON"},
        {"case": "prose", "adapter": "patch", "score": {"exact": True}},
    ]
    totals = summarize(failed, reference)
    assert (totals["positive_correct"], totals["positive_total"]) == (0, 1)
    assert (totals["negative_correct"], totals["negative_total"]) == (1, 1)
    assert totals["cells_total"] == 6
    assert totals["relations_total"] == 7
    assert totals["records_total"] == 3
    assert totals["errors"] == 1
    totals = summarize(
        [
            {
                "case": "table",
                "adapter": "retained-docling",
                "error": "retained model output requires identical single-page input",
            }
        ],
        reference,
    )
    assert totals["unsupported"] == 1
    assert totals["positive_total"] == totals["errors"] == 0
    totals = summarize([{"case": "table", "adapter": "retained-docling", "error": "StopIteration: "}], reference)
    assert totals["unsupported"] == 1
    assert totals["positive_total"] == 0


def source_words() -> list[dict[str, Any]]:
    return [{"id": "a", "text": "Heading"}, {"id": "b", "text": "42.00"}]


@pytest.mark.parametrize("adapter", ["native-bullets", "hybrid-bullets"])
def test_neutral_header_fallback_keeps_displaced_source_words(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adapter: str,
) -> None:
    if adapter == "hybrid-bullets":
        pytest.importorskip("markdown_it")
    header = "Unresolved heading Handgun Handgun " + "multiple grouped field labels " * 5
    content = "\n".join(
        [
            text_op(header, 60, 710, size=3),
            text_op("Alpha", 60, 660),
            text_op("42", 310, 660),
            "50 640 500 100 re S 50 690 m 550 690 l S 300 640 m 300 690 l S",
        ]
    )
    directory = tmp_path / "sample"
    directory.mkdir()
    data = page_pdf(content)
    (directory / "input.pdf").write_bytes(data)
    (directory / "yolo-normalized-geometry-wrapped-detections.json").write_text("[]")
    with pdfust.open(stream=data) as document:
        words = [
            {"id": f"p0w{i}", "text": word[4], "bbox": list(word[:4]), "logical_bbox": list(word[:4])}
            for i, word in enumerate(document[0].get_text("words"))
        ]
    monkeypatch.setattr(structure, "ARTIFACTS", tmp_path)
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {"results": [{"case": "sample", "adapter": "yolo-normalized-geometry-wrapped", "sha256": "same-input"}]}
        )
    )
    monkeypatch.setattr(structure, "REPORT", report)
    output = structure.run_adapter(
        {"name": "sample", "sha256": "same-input", "words": words}, MagicMock(adapter=adapter), 4096
    )
    assert output["tables"] == [[["Column 1", "Column 2"], ["Alpha", "42"]]]
    assert header.strip() in output["markdown"]
    assert output["markdown"].count("Handgun") == 2


@pytest.mark.parametrize(
    ("raw", "truncated", "error"), [('{"tables":[]}', True, ValueError), ("{invalid", False, json.JSONDecodeError)]
)
def test_failed_patch_retains_generation_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    raw: str,
    *,
    truncated: bool,
    error: type[Exception],
) -> None:
    image = pytest.importorskip("PIL.Image")
    directory = tmp_path / "sample"
    directory.mkdir()
    image.new("RGB", (20, 20), "white").save(directory / "page.png")
    monkeypatch.setattr(structure, "ARTIFACTS", tmp_path)
    engine = MagicMock(adapter="qwen-patch")
    engine.generate.return_value = (raw, {"truncated": truncated, "output_tokens": 4096})
    bundle = {"name": "sample", "words": [], "width": 20, "height": 20}
    with pytest.raises(error):
        structure.run_adapter(bundle, engine, 4096)
    assert json.loads((directory / "qwen-patch-generation.json").read_text()) == {
        "truncated": truncated,
        "output_tokens": 4096,
        "image_file": "page.png",
        "image_size_pixels": [20, 20],
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"tables": [{"rows": [[["missing"]]]}]},
        {"tables": [{"rows": [[["a"], ["a"]]]}]},
        {"tables": [{"rows": [[["a"]], [["b"], []]]}]},
        {"tables": [{"rows": [[["a"], ["b"]]], "spans": [[0, 0, 1, 2]]}]},
        {"tables": [{"rows": [[["a"]]], "spans": [[0, 0, 2, 1]]}]},
    ],
)
def test_patch_rejects_content_or_geometry_corruption(payload: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r"unknown|duplicated|ragged|span"):
        validate_patch(payload, source_words())


def test_merged_patch_expands_anchor_without_reusing_source_ids() -> None:
    matrix, used = validate_patch(
        {"tables": [{"rows": [[["a"], []], [["b"], []]], "spans": [[0, 0, 1, 2]]}]},
        source_words(),
    )
    assert matrix == [[["Heading", "Heading"], ["42.00", ""]]]
    assert used == {"a", "b"}
    pytest.importorskip("markdown_it")
    rendered = render_tables(matrix, spans=[[[0, 0, 1, 2]]])
    assert 'colspan="2"' in rendered
    assert markdown_tables(rendered) == matrix


def test_table_score_detects_swapped_values_and_extra_tables() -> None:
    gold = ((("Name", "Amount"), ("Alpha", "42"), ("Beta", "7")),)
    swapped = [[["Name", "Amount"], ["Alpha", "7"], ["Beta", "42"]]]
    score = score_tables(swapped, gold)
    assert score["correct_cells"] == 4
    assert not score["exact"]
    assert score["relationship_matches"] < score["relationship_expected"]
    assert not score_tables([[list(row) for row in gold[0]], [["extra"]]], gold)["exact"]
    assert not score_tables(swapped, ())["exact"]


def test_parsing_preserves_literals_empty_cells_and_html_spans() -> None:
    pytest.importorskip("markdown_it")
    markdown = "| Left | Center | Right |\n| --- | --- | --- |\n| Alpha | A\\|B | 42 |\n| Beta | C\\\\D | |"
    assert markdown_tables(markdown) == [
        [["Left", "Center", "Right"], ["Alpha", "A|B", "42"], ["Beta", "C\\D", ""]],
    ]
    table = '<table><tr><th colspan="2">Heading</th></tr><tr><td>A &amp; B</td><td>42</td></tr></table>'
    assert markdown_tables(table) == [[["Heading", "Heading"], ["A & B", "42"]]]
    assert markdown_tables(f"```html\n{table}\n```") == []
    assert markdown_spans(table) == [[0, 0, 1, 2]]
    assert markdown_spans(f"```html\n{table}\n```") == []
    assert markdown_tables("| Heading |\n| --- |\n| First<br>second |") == [[["Heading"], ["First second"]]]


def test_bullet_fallback_preserves_empty_value_and_escaping() -> None:
    assert render_tables([[["Name", "Amount"], ["Alpha", "42.00"], ["Beta", ""]]], bullets=True) == (
        "- Name: Alpha; Amount: 42.00\n- Name: Beta; Amount: "
    )


def test_dense_row_strips_bound_words_without_duplicating_or_losing_rows() -> None:
    words: list[dict[str, Any]] = [
        {"id": f"r{row}c{column}", "bbox": [column * 10, row * 20, column * 10 + 8, row * 20 + 10]}
        for row in range(30)
        for column in range(20)
    ]
    regions = structure.split_row_regions([{"label": "Table", "bbox": [0, 0, 200, 600]}], words)
    selected = [
        [word["id"] for word in words if region["bbox"][1] <= word["bbox"][1] + 5 <= region["bbox"][3]]
        for region in regions
    ]
    flattened = [word_id for strip in selected for word_id in strip]
    assert set(flattened) == {word["id"] for word in words}
    assert len(flattened) == len(set(flattened))
    assert all(len(strip) <= 160 for strip in selected)


def test_hosted_budget_refuses_network_and_retains_unknown_charge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifacts = tmp_path / "bench/results/structure-artifacts"
    artifacts.mkdir(parents=True)
    (tmp_path / ".env.remote-hosts").write_text("OPENROUTER_API_KEY=unit-test-placeholder\n")
    client = HostedVision(tmp_path, router=False)
    calls: list[bool] = []

    def unavailable(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401, ARG001
        calls.append(True)
        url = "https://openrouter.ai/api/test"
        raise urllib.error.HTTPError(url, 503, "Unavailable", Message(), None)

    monkeypatch.setattr("urllib.request.urlopen", unavailable)
    client.checkpoint({"requests": [{"accounted_usd": 1.40}]})
    with pytest.raises(ValueError, match="budget"):
        client.request("test", {"model": "test"})
    assert calls == []
    client.checkpoint({"requests": []})
    with pytest.raises(RuntimeError, match="HTTP 503"):
        client.request("test", {"model": "test"})
    retained = json.loads(client.ledger.read_text())
    assert retained["requests"][0]["accounted_usd"] == 0.25
    assert "unit-test-placeholder" not in client.ledger.read_text()


def test_screenshot_is_opaque_and_orientation_follows_display_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = pytest.importorskip("PIL.Image")
    data = page_pdf("0 1 -1 0 600 200 cm\n" + text_op("Upright display", 40, 200), extra_page="/Rotate 90")
    case = StructureCase(FeatureCase("counter-rotated", data, (), ""))
    monkeypatch.setattr(structure, "ARTIFACTS", tmp_path)
    monkeypatch.setattr(structure, "build_structure_cases", lambda: [case])
    bundle = structure.prepare()[0]
    assert bundle["rotation"] == 90
    assert bundle["orientation"] == 0
    assert bundle["words"]
    screenshot = image.open(tmp_path / "counter-rotated/page.png")
    assert screenshot.getpixel((0, 0)) == (255, 255, 255, 255)
