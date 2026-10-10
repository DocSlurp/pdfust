"""CPU-only rotation, CropBox, later-page and strict-failure integration checks."""

# Mock JSON transport and display-coordinate fixtures are deliberately explicit.
# ruff: noqa: ANN401
from __future__ import annotations

import base64
import io
import json
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from bench import generalization_vision_multiscale as multi
from bench.pipeline_assembly import native_state
from bench.pipeline_hybrid_composition import compose, native_boxes
from bench.pipeline_vision_transcription import _canonical
from bench.silver import sha
from PIL import Image

import pylopdf


class CapturingDetector:
    """Keep every actual submitted raster, with one whole-page proposal."""

    def __init__(self) -> None:
        """Start an empty per-page request capture."""
        self.images: list[bytes] = []

    def detect(self, image: bytes, *, viewport: list[float]) -> dict[str, Any]:
        """Return one exact pixel-to-display whole-page proposal."""
        self.images.append(image)
        with Image.open(io.BytesIO(image)) as raster:
            width, height = raster.size
        pixel = [0.15 * width, 0.2 * height, 0.8 * width, 0.85 * height]
        normalized = [pixel[0] / width, pixel[1] / height, pixel[2] / width, pixel[3] / height]
        bounds = [viewport[i % 2] + normalized[i] * (viewport[i % 2 + 2] - viewport[i % 2]) for i in range(4)]
        return {
            "type": "result",
            "device": "cpu",
            "viewport": viewport,
            "image_size": [width, height],
            "boxes": [
                {
                    "label": "Table",
                    "confidence": 0.9,
                    "pixel_bbox": pixel,
                    "normalized_bbox": normalized,
                    "bbox": bounds,
                }
            ]
            if len(self.images) == 1
            else [],
        }


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("cropped", [False, True])
def test_multiscale_later_page_rotation_crop_and_global_transcription(  # noqa: PLR0915
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, rotation: int, cropped: bool
) -> None:
    pixels = Image.new("RGB", (120, 200), "red")
    pixels.paste("blue", (60, 0, 120, 100))
    pixels.paste("green", (0, 100, 60, 200))
    stream = io.BytesIO()
    pixels.save(stream, format="PNG")
    with pylopdf.Document() as document:
        document.new_page(width=70, height=70)  # Different first page catches page-index mistakes.
        page = document.new_page(width=120, height=200)
        page.insert_image((0, 0, 120, 200), stream=stream.getvalue())
        if cropped:
            page.set_cropbox((10, 20, 110, 180))
        page.set_rotation(rotation)
        data = document.tobytes()
    pdf = tmp_path / "rotated.pdf"
    pdf.write_bytes(data)
    detector = CapturingDetector()
    request_images = []

    def fake(_client: Any, body: dict, _config: dict, result: dict, _output: Path, *, request_index: int) -> dict:
        url = body["messages"][1]["content"][0]["image_url"]["url"]
        request_images.append(base64.b64decode(url.split(",", 1)[1]))
        response = {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(
                            {
                                "answers": {
                                    "q0": {
                                        "tables": [
                                            {"bbox": [250, 250, 750, 750], "matrix": [["literal"]], "mergedspans": []}
                                        ]
                                    }
                                }
                            }
                        )
                    },
                }
            ]
        }
        result["calls"].append({"request_index": request_index, "mock_charge": 0.01})
        result["request"] = {"request_index": request_index}
        return response

    monkeypatch.setattr(multi.vision, "_transcribe", fake)
    output = tmp_path / "output"
    record = {"id": "rotated", "pdf_path": str(pdf), "pdf_sha256": sha(data), "page_number": 1}
    result = multi.process(record, {"layout_detector": "yolo", "_layout_detector": detector}, output, None)
    assert result["status"] == "ok", result
    assert result["original_rotation"] == result["multiscale_image"]["original_rotation"] == rotation
    assert result["rotation_normalized"] is False
    assert pdf.read_bytes() == data
    assert len(detector.images) == 5
    with pylopdf.open(stream=data) as document:
        page = document[1]
        assert result["viewport"] == list(page.rect)
        source_bytes = page.render(scale=3071 / max(page.rect.width, page.rect.height), background=(255, 255, 255))
    assert sha(source_bytes) == result["multiscale_image"]["sha256"]
    with Image.open(io.BytesIO(source_bytes)) as source_image:
        source_rgb = source_image.convert("RGB")
        for index, (raw, submitted) in enumerate(zip(result["multiscale_raw_calls"], detector.images, strict=True)):
            window = raw["tile_pixel_bbox"]
            expected = source_rgb.copy() if index == 0 else source_rgb.crop(tuple(window))
            if index == 0:
                expected.thumbnail((1536, 1536))
            with Image.open(io.BytesIO(submitted)) as actual:
                assert actual.size == expected.size
                assert actual.tobytes() == expected.tobytes()
            assert sha(submitted) == raw["image"]["sha256"]
    bounds = result["transcription_regions"][0]["viewport"]
    expected_bounds = [
        bounds[i % 2] + (0.25 if i < 2 else 0.75) * (bounds[i % 2 + 2] - bounds[i % 2]) for i in range(4)
    ]
    assert result["tables"][0]["bbox"] == pytest.approx(expected_bounds)
    assert result["tables"][0]["values"] == [["literal"]]
    assert len(request_images) == len(result["calls"]) == 1
    with Image.open(io.BytesIO(request_images[0])) as request_image:
        assert max(request_image.size) == 1024
    assert result["layout_detection"] == multi.replay(
        result["multiscale_raw_calls"], result["viewport"], result["multiscale_image"]["image_size"]
    )


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_hybrid_affine_display_geometry_preserves_ownership_and_touching_edges(rotation: int) -> None:
    def transform(box: Sequence[float]) -> list[float]:
        corners = [(box[x], box[y]) for x in (0, 2) for y in (1, 3)]
        for _ in range(rotation // 90):
            corners = [(200 - y, x) for x, y in corners]
        return [
            min(x for x, _ in corners) + 17,
            min(y for _, y in corners) - 23,
            max(x for x, _ in corners) + 17,
            max(y for _, y in corners) - 23,
        ]

    cells = [[10, 10, 30, 30], [30, 10, 50, 30], [10, 30, 30, 50], [30, 30, 50, 50]]
    source = {
        "page_size": [17, -23, 217, 177],
        "words": [
            {"id": "native", "text": "exact native", "bbox": transform([12, 12, 20, 18])},
            {"id": "replaced", "text": "OCR text", "bbox": transform([52, 12, 58, 18])},
            {"id": "crossing", "text": "keep crossing", "bbox": transform([85, 12, 95, 18])},
        ],
        "vector_candidates": [
            {
                "row_count": 2,
                "col_count": 2,
                "cells": [transform(b) for b in cells],
                "bbox": transform([10, 10, 50, 50]),
                "spans": [{"row": r, "column": c, "row_span": 1, "column_span": 1} for r in range(2) for c in range(2)],
            }
        ],
    }
    state = native_state(source)
    bounds = transform([50, 10, 90, 50])
    table, _, _ = _canonical(
        {"bbox": [0, 0, 1000, 1000], "matrix": [["replacement"]], "mergedspans": []},
        (bounds[0], bounds[1], bounds[2], bounds[3]),
    )
    transcribed = {"tables": [table], "text_provenance": "model-transcribed", "source_conserved": False}
    before = deepcopy((source, state, transcribed))
    result = compose(source, state, transcribed)
    assert result["status"] == "ok"
    assert result["superseded_ids"] == ["replaced"]
    assert result["unresolved_ids"] == ["crossing"]
    assert result["source_inventory_complete"] is result["accounting_complete"] is True
    assert result["tables"][1] == table
    assert native_boxes(source, state) == [transform([10, 10, 50, 50])]
    assert (source, state, transcribed) == before


@pytest.mark.parametrize("finish", ["length", "content_filter"])
def test_multiscale_abnormal_finish_preserves_charge_and_raw_detection_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, finish: str
) -> None:
    with pylopdf.Document() as document:
        document.new_page(width=120, height=100)
        data = document.tobytes()
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(data)
    output = tmp_path / "output"
    output.mkdir()
    (output / "failed.md").write_text("stale success")
    (output / "failed-structure.json").write_text("{}")
    response = {
        "choices": [
            {
                "finish_reason": finish,
                "message": {
                    "content": json.dumps(
                        {
                            "answers": {
                                "q0": {
                                    "tables": [{"bbox": [0, 0, 1000, 1000], "matrix": [["prefix"]], "mergedspans": []}]
                                }
                            }
                        }
                    )
                },
            }
        ]
    }

    def fake(_client: Any, _body: dict, _config: dict, result: dict, _output: Path, *, request_index: int) -> dict:
        result["calls"].append({"request_index": request_index, "mock_charge": 0.01})
        result["request"] = {"request_index": request_index}
        return response

    monkeypatch.setattr(multi.vision, "_transcribe", fake)
    record = {"id": "failed", "pdf_path": str(pdf), "pdf_sha256": sha(data), "page_number": 0}
    result = multi.process(record, {"layout_detector": "yolo", "_layout_detector": CapturingDetector()}, output, None)
    assert result["status"] == "error"
    assert result["tables"] == []
    assert len(result["multiscale_raw_calls"]) == 5
    assert result["calls"] == [{"request_index": 0, "mock_charge": 0.01}]
    assert result["transcription_regions"][0]["transcription_response"] == response
    assert not (output / "failed.md").exists()
    assert not (output / "failed-structure.json").exists()


@pytest.mark.parametrize("reversed_proposals", [False, True])
def test_hybrid_no_owned_word_tables_precede_following_prose_in_spatial_order(*, reversed_proposals: bool) -> None:
    source = {
        "page_size": [200, 200],
        "vector_candidates": [],
        "words": [{"id": "footer", "text": "Footer", "bbox": [10, 150, 40, 160]}],
    }
    tables = []
    for text, bounds in (("Z upper table", (10, 10, 70, 40)), ("A lower table", (10, 60, 70, 90))):
        table, _, _ = _canonical({"bbox": [0, 0, 1000, 1000], "matrix": [[text]], "mergedspans": []}, bounds)
        tables.append(table)
    if reversed_proposals:
        tables.reverse()
    source["render_version"] = 1  # Untrusted source metadata cannot select historical rendering.
    result = compose(
        source,
        native_state(source),
        {"tables": tables, "text_provenance": "model-transcribed", "source_conserved": False},
    )
    assert result["status"] == "ok"
    assert result["superseded_ids"] == []
    markup = result["markdown"]
    assert markup.index("Z upper table") < markup.index("A lower table") < markup.index("Footer")


def test_hybrid_empty_native_grid_uses_geometry_before_following_footer() -> None:
    source = {
        "page_size": [200, 200],
        "words": [{"id": "footer", "text": "Footer", "bbox": [10, 150, 40, 160]}],
        "vector_candidates": [
            {
                "row_count": 1,
                "col_count": 1,
                "cells": [[10, 10, 70, 40]],
                "spans": [{"row": 0, "column": 0, "row_span": 1, "column_span": 1}],
            }
        ],
    }
    state = native_state(source)
    empty = {"tables": [], "text_provenance": "model-transcribed", "source_conserved": False}
    current = compose(source, state, empty)
    legacy = compose(source, state, empty, render_version=1)
    assert current["markdown"].index("<table>") < current["markdown"].index("Footer")
    assert legacy["markdown"].index("Footer") < legacy["markdown"].index("<table>")
    assert current["rules"]["renderer_version"] == 2
    assert legacy["rules"]["version"] == 1
    assert "renderer_version" not in legacy["rules"]
    assert {k: v for k, v in current.items() if k not in {"markdown", "rules"}} == {
        k: v for k, v in legacy.items() if k not in {"markdown", "rules"}
    }


@pytest.mark.parametrize("version", [True, False, 0, 3, "1"])
def test_hybrid_renderer_version_is_explicit_typed_caller_policy(version: Any) -> None:
    with pytest.raises(ValueError, match="renderer version"):
        compose({}, {}, {}, render_version=version)
