"""Header opportunity analysis guards original complete source before any target lookup."""

from pathlib import Path

import pytest
from bench import p003_header_oracle as oracle
from bench.silver import sha


def test_changed_original_pdf_rejected_before_crop_reconstruction(tmp_path: Path) -> None:
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"changed source")
    record = {"pdf_path": str(pdf), "pdf_sha256": sha(b"original source"), "page_number": 0}
    with pytest.raises(ValueError, match="PDF changed"):
        oracle.verify_page_inputs(tmp_path, record, {}, {})


def test_missing_acquisition_crop_rejected_before_hypothesis_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"unchanged source")
    record = {"pdf_path": str(pdf), "pdf_sha256": sha(pdf.read_bytes()), "page_number": 0, "id": "p"}
    page = {"layout_detection": {}, "viewport": [0, 0, 100, 100], "transcription_regions": []}
    monkeypatch.setattr(
        oracle.regions,
        "proposals",
        lambda *_: [{"index": 0, "request_index": 0, "viewport": [0, 0, 100, 100], "detector_box": [0, 0, 100, 100]}],
    )
    with pytest.raises(ValueError, match="acquisition inventory"):
        oracle.verify_page_inputs(tmp_path, record, page, {})
