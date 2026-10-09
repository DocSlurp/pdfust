"""Native resolution, actual PNG depth and model-label separation checks."""

from __future__ import annotations

import io
import json
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest

pytest.importorskip("PIL")
from bench.decision_context_cases import context_cases
from bench.decision_image_matrix import MODES, VariantCache, build_request, default_arms, expected_evidence, png_format
from PIL import Image


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    """Reuse thirty CPU-authored DEV PDFs without accessing retained campaign data."""
    return context_cases()


@pytest.mark.parametrize("edge", [128, 512, 1200])
@pytest.mark.parametrize("mode", list(MODES))
def test_native_base_and_actual_png_depth(tmp_path: Path, cases: list[dict], edge: int, mode: str) -> None:
    case = cases[2]
    variant = VariantCache(tmp_path).make_variant(
        case["pdf_bytes"], case["evidence"]["current_region"], edge=edge, mode=mode
    )
    assert variant["base_pixels"] == [1500, 210]
    assert variant["pixels"] == [edge, round(edge * 70 / 500)]
    assert variant["identity"]["scale"] == 3.0
    assert png_format(variant["data"]) == MODES[mode]
    with Image.open(io.BytesIO(variant["data"])) as image:
        assert list(image.size) == variant["pixels"]
        assert cast("tuple[int, int]", image.convert("L").getextrema())[0] < 255
        if mode == "gray4":
            palette = image.getpalette()
            assert palette is not None
            assert all(palette[index] == palette[index + 1] == palette[index + 2] for index in range(0, 48, 3))
            assert len(image.getcolors() or []) <= 16
        if mode == "mono1":
            assert image.mode == "1"
    assert variant["cpu_ms"] >= 0
    assert variant["peak_rss_bytes"] > 0


def test_cache_identity_and_matched_blank(tmp_path: Path, cases: list[dict]) -> None:
    case = cases[0]
    cache = VariantCache(tmp_path)
    args = (case["pdf_bytes"], case["evidence"]["current_region"])
    original = cache.make_variant(*args, edge=1200)
    repeated = cache.make_variant(*args, edge=1200)
    blank = cache.make_variant(*args, edge=1200, blank=True)
    assert repeated["base_cache"]
    assert repeated["variant_cache"]
    assert original["data"] == repeated["data"]
    assert blank["pixels"] == original["pixels"]
    assert blank["png_bit_depth"] == original["png_bit_depth"]
    assert blank["variant_key"] != original["variant_key"]
    with Image.open(io.BytesIO(blank["data"])) as image:
        assert image.convert("L").getextrema() == (255, 255)
    cache.renderer["test_change"] = "new-version"
    changed = cache.make_variant(*args, edge=1200)
    assert changed["base_key"] != original["base_key"]
    assert len(default_arms()) == 18
    assert sum(arm["blank"] for arm in default_arms()) == 9


def test_gold_separation_and_current_state_identity(tmp_path: Path, cases: list[dict]) -> None:
    case = cases[0]
    cache = VariantCache(tmp_path)
    image = cache.make_variant(case["pdf_bytes"], case["evidence"]["current_region"], edge=512)
    body = build_request(case, "test-model", image)
    altered = deepcopy(case)
    altered["gold"] = {"secret_label": "SHOULD_NEVER_ENTER_REQUEST"}
    altered["family"] = "SHOULD_NEVER_ENTER_REQUEST"
    altered["id"] = "SHOULD_NEVER_ENTER_REQUEST"
    assert body == build_request(altered, "test-model", image)
    assert "SHOULD_NEVER_ENTER_REQUEST" not in json.dumps(body)
    state = json.loads(body["state"][0].split("\nAttached image")[0])
    assert state == build_request(case, "test-model")["state"]
    assert state == build_request(cases[1], "test-model")["state"]
    assert state["rules"] == state["fills"] == []
    assert body["state"][1]["image_url"]["detail"] == "high"
    assert expected_evidence(case, image) == "A"
    blank = cache.make_variant(case["pdf_bytes"], case["evidence"]["current_region"], edge=512, blank=True)
    assert expected_evidence(case, blank) == "unresolved"


def test_full_page_includes_conventions_and_native_comparator(tmp_path: Path, cases: list[dict]) -> None:
    case = cases[8]
    cache = VariantCache(tmp_path)
    region = cache.make_variant(case["pdf_bytes"], case["evidence"]["current_region"], edge=1200)
    page = cache.make_variant(case["pdf_bytes"], edge=1200)
    assert page["identity"]["scope"] == "page"
    assert max(page["pixels"]) == 1200
    assert region["base_key"] != page["base_key"]
    assert expected_evidence(case, region) == "unresolved"
    assert expected_evidence(case, page) == "A"
    native = build_request(case, "test-model", native=True)
    assert "share the amount" in native["state"]["prior_text"]
    assert expected_evidence(case, None, native=True) == "A"
    current = build_request(case, "test-model")
    assert current["state"]["source_spans"] == native["state"]["source_spans"]
    ids = [source for span in current["state"]["source_spans"].values() for source in span["ids"]]
    assert sorted(ids) == list(range(len(ids)))


@pytest.mark.parametrize("kwargs", [{"edge": 1024}, {"edge": True}, {"mode": "gray2"}, {"page_index": -1}])
def test_invalid_variants_rejected(tmp_path: Path, cases: list[dict], kwargs: dict) -> None:
    with pytest.raises(ValueError, match=r"image|page_index"):
        VariantCache(tmp_path).make_variant(cases[0]["pdf_bytes"], **kwargs)


def test_color_palette_preserved(tmp_path: Path) -> None:
    from bench.feature_cases import page_pdf  # noqa: PLC0415

    pdf = page_pdf("1 0 0 rg 40 574 250 40 re f 0 0 1 rg 290 574 250 40 re f")
    variant = VariantCache(tmp_path).make_variant(pdf, [40, 155, 540, 225], mode="pal4")
    assert png_format(variant["data"]) == (4, 3)
    with Image.open(io.BytesIO(variant["data"])) as image:
        palette = image.getpalette()
        assert palette is not None
        assert any(palette[i] != palette[i + 1] or palette[i] != palette[i + 2] for i in range(0, 48, 3))
    real = [arm for arm in default_arms() if not arm["blank"]]
    assert [(arm["edge"], arm["mode"]) for arm in real] == [
        (edge, mode) for mode in ("rgb8", "gray8", "pal4") for edge in (128, 512, 1200)
    ]
