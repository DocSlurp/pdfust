"""End-to-end CPU seams for source-only regional extraction and metering."""

from __future__ import annotations

import base64
import io
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bench import generalization_run as runner
from bench import pipeline_run as baseline
from bench.pipeline_regions import split
from PIL import Image
from test_pipeline_run import config, pdf_bytes, record

import pylopdf


def test_region_native_output_is_complete_and_has_no_api_calls(tmp_path: Path) -> None:
    settings = {**config("native"), "ocr_empty": False}
    result = runner.process(record(tmp_path), settings, tmp_path, None)
    assert result["status"] == "ok"
    assert len(result["tables"]) == 1
    assert result["calls"] == []
    assert result["source_conserved"]
    assert all("state" in region for region in result["regions"])
    assert (tmp_path / "opaque-page.md").read_text().count("<table>") == 1


def test_invalid_native_topology_retains_all_words_for_rediscovery() -> None:
    with pylopdf.open(stream=pdf_bytes()) as doc:
        source = baseline.source(doc[0])
    source["vector_candidates"][0]["spans"].pop()
    clean, warnings = runner.sanitize_vectors(source)
    assert clean["words"] == source["words"]
    assert clean["vector_candidates"] == []
    assert len(warnings) == 1
    plan = split(clean)
    assert Counter(i for r in plan["regions"] for i in r["source_ids"]) == Counter(w["id"] for w in source["words"])


@pytest.mark.parametrize("edge", [256, 512, 1024])
def test_crop_raster_records_global_viewport(edge: int) -> None:
    box: list[float] = [40, 40, 300, 120]
    with pylopdf.open(stream=pdf_bytes()) as doc:
        url, metadata = runner.region_image(doc[0], box, edge)
    assert url is not None
    assert metadata["image_viewport"] == box
    with Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))) as raster:
        assert max(raster.size) <= edge
        assert raster.width > raster.height
        assert list(raster.size) == metadata["image_size"]


def test_p002_budget_uses_its_own_wave_and_stops_before_request(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps(
            {"requests": [{"tag": "P001/old", "accounted_usd": 49.9}, {"tag": "P002/new", "accounted_usd": 49.8}]}
        )
    )
    client: Any = SimpleNamespace(
        ledger=ledger, request=lambda *_a, **_kw: pytest.fail("Request passed exhausted wave")
    )
    with pytest.raises(RuntimeError, match="P002 reservation"):
        baseline.call(client, {"model": "stub"}, "P002/run/page")


def test_p001_spend_does_not_consume_p002_wave_allowance(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"requests": [{"tag": "P001/old", "accounted_usd": 50}]}))

    def request(*_args: object, **kwargs: object) -> dict[str, Any]:
        assert kwargs["replay"] is False
        return {
            "result": {"answers": {"q0": {"type": "choice", "choice": "x", "probabilities": {"x": 1}}}},
            "entry": {},
            "replayed": False,
        }

    client: Any = SimpleNamespace(ledger=ledger, request=request)
    result = baseline.call(
        client, {"model": "stub", "questions": {"q0": {"criteria": {"x": "choose"}}}}, "P002/run/page"
    )
    assert result["answer"]["choice"] == "x"


def test_unknown_campaign_rejected_before_metering(tmp_path: Path) -> None:
    client: Any = SimpleNamespace(ledger=tmp_path / "absent")
    with pytest.raises(ValueError, match="Unknown"):
        baseline.call(client, {}, "unregistered/run")
