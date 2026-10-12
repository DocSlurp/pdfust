"""Exact rerender equivalence and bounded lifecycle on a synthetic PDF."""

from copy import deepcopy
from pathlib import Path

import pytest
from bench import p003_candidate_run as candidate
from bench.p003_render_reuse import EDGES, PageRender
from bench.silver import sha
from conftest import build_pdf

import pdfust


def source(tmp_path: Path, rotation: int) -> tuple[dict, dict]:
    data = build_pdf(["Complete source text"])
    if rotation:
        with pdfust.open(stream=data) as document:
            document[0].set_rotation(rotation)
            data = document.tobytes()
    path = tmp_path / "page.pdf"
    path.write_bytes(data)
    with pdfust.open(stream=data) as document:
        page = document[0]
        result = {"viewport": list(page.rect), "original_rotation": page.rotation}
    return {"pdf_path": str(path), "pdf_sha256": sha(data), "page_number": 0}, result


@pytest.mark.parametrize("rotation", [0, 90])
def test_every_crop_edge_has_exact_original_bytes_and_metadata(tmp_path: Path, rotation: int) -> None:
    record, page = source(tmp_path, rotation)
    x0, y0, x1, y1 = page["viewport"]
    crops = [{"viewport": [x0, y0, x1, y1]}, {"viewport": [x0 + 21.25, y0 + 17.5, x1 - 63.75, y1 - 29.5]}]
    resident = PageRender(record, page)
    try:
        for crop in crops:
            for edge in EDGES:
                assert resident.crop(crop, edge) == candidate._rerender(record, page, crop, edge)  # noqa: SLF001
    finally:
        resident.close()
    assert resident.image is None
    with pytest.raises(ValueError, match="closed"):
        resident.crop(crops[0], 512)


def test_hash_rotation_viewport_and_memory_admission(tmp_path: Path) -> None:
    record, page = source(tmp_path, 0)
    changed = deepcopy(record)
    changed["pdf_sha256"] = "changed"
    with pytest.raises(ValueError, match="hash"):
        PageRender(changed, page)
    changedpage = {**page, "original_rotation": 90}
    with pytest.raises(ValueError, match="geometry"):
        PageRender(record, changedpage)
    with pytest.raises(ValueError, match="memory admission"):
        PageRender(record, page, max_rgb_bytes=1)
    resident = PageRender(record, page)
    try:
        with pytest.raises(ValueError, match="inside"):
            resident.crop({"viewport": [-1, 0, 100, 100]}, 512)
        with pytest.raises(ValueError, match="edge"):
            resident.crop({"viewport": page["viewport"]}, 0)
    finally:
        resident.close()
