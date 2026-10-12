"""Original renderer order and exact regional source evidence regression checks."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import pipeline_run as baseline
from bench.pipeline_regions import split
from bench.pipeline_source_order import render_source


def word(ident: str, text: str, x: int, y: int, line: list[int]) -> dict[str, Any]:
    return {"id": ident, "text": text, "bbox": [x, y, x + 20, y + 10], "line": line}


def snapshot() -> dict[str, Any]:
    return {
        "page_size": [0, 0, 600, 800], "vector_candidates": [], "words": [
            word("w1", "Left first", 20, 20, [0, 0]),
            word("w10", "wrapped continuation", 20, 40, [0, 1]),
            word("w2", "Left second", 20, 60, [0, 2]),
            word("w11", "Right first", 320, 20, [1, 0]),
            word("w3", "Right second", 320, 40, [1, 1]),
            word("w12", "Right third", 320, 60, [1, 2]),
        ],
    }


def test_original_words_and_line_metadata_restore_columns_without_evidence_change() -> None:
    source = snapshot()
    # Simulate the x/lexical-ID ordering used while finding column corridors.
    shuffled = sorted(source["words"], key=lambda w: (w["bbox"][0], w["id"]))
    region = {
        "source_ids": [w["id"] for w in shuffled],
        "source": {**source, "words": [{k: w[k] for k in ("id", "text", "bbox")} for w in shuffled]},
    }
    before = deepcopy(region)
    restored = render_source(source, region)
    assert restored["words"] == source["words"]
    assert region == before
    state = {"tables": [], "unresolved_ids": region["source_ids"], "source_conserved": True}
    rendered = baseline.markdown(restored, state)
    assert rendered.index("wrapped continuation") < rendered.index("Left second")
    assert rendered.index("Left second") < rendered.index("Right first")
    assert rendered.index("Right second") < rendered.index("Right third")
    restored["words"][0]["line"][0] = 999
    assert source["words"][0]["line"] == [0, 0]


@pytest.mark.parametrize("mutation", ["text", "bbox", "missing", "duplicate", "page_size"])
def test_render_projection_refuses_changed_partition_evidence(mutation: str) -> None:
    source = snapshot()
    region: dict[str, Any] = {"source_ids": [w["id"] for w in source["words"]], "source": deepcopy(source)}
    if mutation == "text":
        region["source"]["words"][0]["text"] = "changed"
    elif mutation == "bbox":
        region["source"]["words"][0]["bbox"][0] += 1
    elif mutation == "missing":
        region["source"]["words"].pop()
    elif mutation == "duplicate":
        region["source_ids"].append(region["source_ids"][0])
    else:
        region["source"]["page_size"][2] += 1
    with pytest.raises(ValueError, match=r"Render source"):
        render_source(source, region)


def test_native_table_and_prose_remain_owned_once(tmp_path: Path) -> None:
    from test_pipeline_run import record  # noqa: PLC0415 - generated PDF grid fixture.

    import pdfust  # noqa: PLC0415 - local native extraction only.

    item = record(tmp_path)
    with pdfust.open(item["pdf_path"]) as document:
        document[0].insert_text((40, 50), "Outside table prose")
        source = baseline.source(document[0])
    plan = split(source)
    rendered_parts, owners = [], []
    for region in plan["regions"]:
        projected = render_source(source, region)
        state = baseline.native_state(region["source"])
        rendered_parts.append(baseline.markdown(projected, state))
        owners.extend(region["source_ids"])
    assert Counter(owners) == Counter(w["id"] for w in source["words"])
    output = "".join(rendered_parts)
    assert output.count("Outside table prose") == 1
    assert output.count("Alpha") == 1
    assert output.count("42") == 1


def test_runner_flag_changes_only_markdown_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from bench import generalization_run as runner  # noqa: PLC0415
    from test_pipeline_run import config, record  # noqa: PLC0415

    source = snapshot()
    monkeypatch.setattr(baseline, "source", lambda _page: deepcopy(source))
    item = record(tmp_path)
    results = {}
    outputs = {}
    for mode in ("legacy", "original"):
        output = tmp_path / mode
        output.mkdir()
        results[mode] = runner.process(
            item, {**config("native"), "ocr_empty": False, "source_order": mode}, output, None
        )
        outputs[mode] = (output / "opaque-page.md").read_text()
        assert results[mode]["status"] == "ok"
    for key in ("source", "region_plan", "regions", "tables", "unresolved_ids", "source_conserved", "calls"):
        assert results["original"][key] == results["legacy"][key]
    assert outputs["original"].index("wrapped continuation") < outputs["original"].index("Left second")
    assert outputs["original"].index("Left second") < outputs["original"].index("Right first")
    assert outputs["original"] != outputs["legacy"]
