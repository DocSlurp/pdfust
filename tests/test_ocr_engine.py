"""Tests for the optional native PP-OCR engine."""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event, Lock

import pytest

import pdfust
from pdfust.pdfust_core import _OcrEngine

MODEL_ROOT = Path(__file__).parents[1] / "models" / "pdfust-ocr-models" / "src" / "pdfust_ocr_models"
FONT_ROOT = Path(__file__).parents[1] / "fonts" / "pdfust-fonts-jp" / "src" / "pdfust_fonts_jp"


@pytest.fixture(scope="module")
def ocr_engine() -> pdfust.OcrEngine:
    """Load the bundled model set once for OCR integration tests."""
    return pdfust.OcrEngine(
        MODEL_ROOT / "PP-OCRv6_det_small.rten",
        MODEL_ROOT / "PP-OCRv6_rec_small.rten",
        MODEL_ROOT / "ppocrv6_dict.txt",
    )


def test_ocr_model_artifact_hashes() -> None:
    checksums = (MODEL_ROOT / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    for entry in checksums:
        expected, filename = entry.split("  ", maxsplit=1)
        assert hashlib.sha256((MODEL_ROOT / filename).read_bytes()).hexdigest() == expected


def test_ocr_engine_recognizes_rendered_text(ocr_engine: pdfust.OcrEngine) -> None:
    doc = pdfust.Document()
    doc.new_page(width=360, height=120)
    doc[0].insert_text((20, 75), "Invoice 123", fontsize=36)

    words = ocr_engine.recognize(doc[0], dpi=150, tile_size=512, overlap=64)

    assert [word["text"] for word in words] == ["Invoice 123"]
    assert words[0]["confidence"] > 0.99
    assert words[0]["bbox"].x0 < 20 < words[0]["bbox"].x1
    assert words[0]["bbox"].y0 < 60 < words[0]["bbox"].y1


def test_ocr_engine_recognizes_japanese(ocr_engine: pdfust.OcrEngine) -> None:
    doc = pdfust.Document()
    doc.new_page(width=400, height=120)
    doc[0].insert_text(
        (20, 75),
        "請求書 123",
        fontsize=36,
        fontfile=FONT_ROOT / "NotoSansJP-Regular.otf",
    )

    words = ocr_engine.recognize(doc[0], dpi=150, tile_size=512, overlap=64)

    assert [word["text"] for word in words] == ["請求書 123"]
    assert words[0]["confidence"] > 0.9


def test_ocr_engine_orders_sustained_columns(ocr_engine: pdfust.OcrEngine) -> None:
    doc = pdfust.Document()
    doc.new_page(width=500, height=180)
    page = doc[0]
    page.insert_text((20, 60), "Left one", fontsize=24)
    page.insert_text((20, 120), "Left two", fontsize=24)
    page.insert_text((290, 60), "Right one", fontsize=24)
    page.insert_text((290, 120), "Right two", fontsize=24)

    words = ocr_engine.recognize(page, dpi=150, tile_size=512, overlap=64)

    assert [word["text"] for word in words] == ["Left one", "Left two", "Right one", "Right two"]


def test_ocr_engine_is_reusable_across_concurrent_documents(ocr_engine: pdfust.OcrEngine) -> None:
    documents = []
    for text in ("Alpha 123", "Beta 456"):
        document = pdfust.Document()
        document.new_page(width=280, height=100)
        document[0].insert_text((20, 65), text, fontsize=30)
        documents.append(document)

    def recognize(document: pdfust.Document) -> list[str]:
        words = document[0].get_text_ocr(
            engine=ocr_engine,
            dpi=150,
            tile_size=512,
            overlap=64,
        )
        return [word["text"] for word in words]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(recognize, documents))

    assert results == [["Alpha 123"], ["Beta 456"]]


def test_ocr_engine_bounds_complete_concurrent_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    class ProbeEngine:
        def __init__(self) -> None:
            self.active = 0
            self.calls = 0
            self.max_active = 0
            self.lock = Lock()
            self.first_entered = Event()
            self.second_entered = Event()
            self.release_first = Event()

        def recognize_pixmap(self, *_args: object, **_kwargs: object) -> list[object]:
            with self.lock:
                self.calls += 1
                call = self.calls
                self.active += 1
                self.max_active = max(self.max_active, self.active)
            if call == 1:
                self.first_entered.set()
                assert self.release_first.wait(timeout=5)
            else:
                self.second_entered.set()
            with self.lock:
                self.active -= 1
            return []

    engine = pdfust.OcrEngine(
        MODEL_ROOT / "PP-OCRv6_det_small.rten",
        MODEL_ROOT / "PP-OCRv6_rec_small.rten",
        MODEL_ROOT / "ppocrv6_dict.txt",
        threads=1,
    )
    probe = ProbeEngine()
    monkeypatch.setattr(engine, "_engine", probe)
    documents = []
    for _ in range(2):
        document = pdfust.Document()
        document.new_page(width=100, height=100)
        documents.append(document)

    second_started = Event()

    def second_call() -> list[pdfust.OcrWord]:
        second_started.set()
        return engine.recognize(documents[1][0], dpi=72, tile_size=256, overlap=32)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(engine.recognize, documents[0][0], dpi=72, tile_size=256, overlap=32)
        assert probe.first_entered.wait(timeout=5)
        second = pool.submit(second_call)
        assert second_started.wait(timeout=5)
        assert not probe.second_entered.wait(timeout=0.2)
        probe.release_first.set()
        assert first.result(timeout=5) == []
        assert second.result(timeout=5) == []

    assert probe.second_entered.is_set()
    assert probe.max_active == 1
    assert engine.max_concurrent == 1


def test_ocr_engine_can_raise_measured_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    class ProbeEngine:
        def __init__(self) -> None:
            self.active = 0
            self.max_active = 0
            self.lock = Lock()
            self.barrier = Barrier(2)

        def recognize_pixmap(self, *_args: object, **_kwargs: object) -> list[object]:
            with self.lock:
                self.active += 1
                self.max_active = max(self.max_active, self.active)
            self.barrier.wait(timeout=5)
            with self.lock:
                self.active -= 1
            return []

    engine = pdfust.OcrEngine(
        MODEL_ROOT / "PP-OCRv6_det_small.rten",
        MODEL_ROOT / "PP-OCRv6_rec_small.rten",
        MODEL_ROOT / "ppocrv6_dict.txt",
        threads=1,
        max_concurrent=2,
    )
    probe = ProbeEngine()
    monkeypatch.setattr(engine, "_engine", probe)
    documents = []
    for _ in range(2):
        document = pdfust.Document()
        document.new_page(width=100, height=100)
        documents.append(document)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda document: engine.recognize(document[0], dpi=72, tile_size=256, overlap=32),
                documents,
            )
        )

    assert results == [[], []]
    assert probe.max_active == 2
    assert engine.max_concurrent == 2


def test_apply_ocr_adds_searchable_invisible_text(ocr_engine: pdfust.OcrEngine) -> None:
    source = pdfust.Document()
    source.new_page(width=360, height=120)
    source[0].insert_text((20, 75), "Search 456", fontsize=36)
    raster = source[0].get_pixmap(dpi=150, background=(255, 255, 255))

    target = pdfust.Document()
    target.new_page(width=360, height=120)
    target[0].insert_image(target[0].rect, stream=raster.tobytes())
    before = target[0].get_pixmap(background=(255, 255, 255)).samples

    words = target[0].apply_ocr(dpi=150, engine=ocr_engine, tile_size=512, overlap=64)

    assert [word["text"] for word in words] == ["Search 456"]
    assert target[0].search_for("Search 456")
    assert target[0].get_pixmap(background=(255, 255, 255)).samples == before
    reopened = pdfust.open(stream=target.tobytes())
    assert reopened[0].search_for("Search 456")
    assert reopened[0].get_pixmap(background=(255, 255, 255)).samples == before


def test_apply_ocr_clip_handles_mixed_content(ocr_engine: pdfust.OcrEngine) -> None:
    source = pdfust.Document()
    source.new_page(width=360, height=120)
    source[0].insert_text((20, 75), "Region 789", fontsize=36)
    raster = source[0].get_pixmap(dpi=150, background=(255, 255, 255))

    target = pdfust.Document()
    target.new_page(width=360, height=220)
    target[0].insert_text((20, 30), "Digital header", fontsize=14)
    target[0].insert_image((0, 80, 360, 200), stream=raster.tobytes())
    before = target[0].get_pixmap(background=(255, 255, 255)).samples

    words = target[0].apply_ocr(
        dpi=150,
        engine=ocr_engine,
        tile_size=512,
        overlap=64,
        clip=(0, 70, 360, 210),
    )

    assert [word["text"] for word in words] == ["Region 789"]
    assert words[0]["bbox"].y0 > 70
    assert target[0].search_for("Region 789")
    assert target[0].get_pixmap(background=(255, 255, 255)).samples == before


@pytest.mark.parametrize(
    ("page_rotation", "ocr_rotation"),
    [(90, 270), (180, 180), (270, 90)],
)
def test_apply_ocr_corrects_rotated_scan_without_rotating_page(
    ocr_engine: pdfust.OcrEngine,
    page_rotation: int,
    ocr_rotation: pdfust.OcrRotation,
) -> None:
    source = pdfust.Document()
    source.new_page(width=360, height=200)
    source[0].insert_text((20, 65), "First line 111", fontsize=28)
    source[0].insert_text((20, 145), "Second line 222", fontsize=28)
    raster = source[0].get_pixmap(dpi=150, background=(255, 255, 255))

    target = pdfust.Document()
    target.new_page(width=360, height=200)
    target[0].insert_image(target[0].rect, stream=raster.tobytes())
    target[0].set_rotation(page_rotation)
    before = target[0].get_pixmap(background=(255, 255, 255)).samples

    words = target[0].apply_ocr(
        dpi=150,
        engine=ocr_engine,
        tile_size=512,
        overlap=64,
        rotation=ocr_rotation,
    )

    assert [word["text"] for word in words] == ["First line 111", "Second line 222"]
    assert target[0].get_text() == "First line 111\nSecond line 222\n"
    for word in words:
        if page_rotation in (90, 270):
            assert word["bbox"].height > word["bbox"].width
        else:
            assert word["bbox"].width > word["bbox"].height
        hits = target[0].search_for(word["text"])
        assert len(hits) == 1
        assert tuple(hits[0]) == pytest.approx(tuple(word["bbox"]), abs=0.2)
    assert target[0].rotation == page_rotation
    assert target[0].get_pixmap(background=(255, 255, 255)).samples == before
    reopened = pdfust.open(stream=target.tobytes())
    assert reopened[0].get_text() == "First line 111\nSecond line 222\n"
    assert reopened[0].search_for("First line 111")
    assert reopened[0].search_for("Second line 222")
    assert reopened[0].rotation == page_rotation
    assert reopened[0].get_pixmap(background=(255, 255, 255)).samples == before


def test_apply_ocr_skips_existing_text_by_default() -> None:
    doc = pdfust.Document()
    doc.new_page(width=200, height=100)
    doc[0].insert_text((20, 50), "Already searchable")

    assert doc[0].apply_ocr() == []
    with pytest.raises(TypeError, match="skip_existing"):
        doc[0].apply_ocr(skip_existing=1)  # type: ignore[arg-type]


@pytest.mark.parametrize("dpi", [0, -1, float("inf"), float("nan"), "bad"])
def test_ocr_engine_rejects_invalid_dpi(ocr_engine: pdfust.OcrEngine, dpi: object) -> None:
    doc = pdfust.Document()
    doc.new_page(width=100, height=100)
    with pytest.raises(pdfust.OcrError, match="dpi"):
        ocr_engine.recognize(doc[0], dpi=dpi)  # type: ignore[arg-type]


def test_ocr_engine_rejects_incomplete_or_missing_model_paths(tmp_path: Path) -> None:
    with pytest.raises(pdfust.OcrError, match="provided together"):
        pdfust.OcrEngine(tmp_path / "det.onnx", None, tmp_path / "dict.txt")
    with pytest.raises(pdfust.OcrError, match="failed to load OCR detector"):
        pdfust.OcrEngine(tmp_path / "det.onnx", tmp_path / "rec.onnx", tmp_path / "dict.txt")


def test_ocr_engine_bounds_cumulative_model_input(tmp_path: Path) -> None:
    detector = tmp_path / "det.rten"
    recognizer = tmp_path / "rec.rten"
    dictionary = tmp_path / "dict.txt"
    detector.write_bytes(b"det!")
    recognizer.write_bytes(b"rec!")
    dictionary.write_bytes(b"x\n")

    with pytest.raises(pdfust.LimitError) as caught:
        pdfust.OcrEngine(detector, recognizer, dictionary, max_model_size=9)
    assert caught.value.code == "ocr_model_size"

    with pytest.raises(pdfust.OcrError, match="failed to load OCR detector"):
        pdfust.OcrEngine(detector, recognizer, dictionary, max_model_size=10)
    with pytest.raises(pdfust.OcrError, match="failed to load OCR detector"):
        pdfust.OcrEngine(detector, recognizer, dictionary, max_model_size=None)


def test_ocr_core_repeats_cumulative_model_limit(tmp_path: Path) -> None:
    detector = tmp_path / "det.rten"
    recognizer = tmp_path / "rec.rten"
    dictionary = tmp_path / "dict.txt"
    detector.write_bytes(b"det!")
    recognizer.write_bytes(b"rec!")
    dictionary.write_bytes(b"x\n")

    with pytest.raises(pdfust.LimitError) as caught:
        _OcrEngine(str(detector), str(recognizer), str(dictionary), 1, 9)
    assert caught.value.code == "ocr_model_size"


def test_ocr_engine_bounds_dictionary_entries(tmp_path: Path) -> None:
    detector = tmp_path / "det.rten"
    recognizer = tmp_path / "rec.rten"
    dictionary = tmp_path / "dict.txt"
    detector.write_bytes(b"x")
    recognizer.write_bytes(b"x")
    dictionary.write_text("x\n" * 65_537, encoding="utf-8")

    with pytest.raises(pdfust.LimitError) as caught:
        pdfust.OcrEngine(detector, recognizer, dictionary, max_model_size=None)
    assert caught.value.code == "ocr_dictionary_entries"


def test_ocr_engine_rejects_mismatched_dictionary(tmp_path: Path) -> None:
    dictionary = tmp_path / "mismatched.txt"
    dictionary.write_text("x\n", encoding="utf-8")
    engine = pdfust.OcrEngine(
        MODEL_ROOT / "PP-OCRv6_det_small.rten",
        MODEL_ROOT / "PP-OCRv6_rec_small.rten",
        dictionary,
    )
    doc = pdfust.Document()
    doc.new_page(width=200, height=100)
    doc[0].insert_text((20, 60), "Text", fontsize=30)

    with pytest.raises(pdfust.OcrError, match="dictionary requires"):
        engine.recognize(doc[0], dpi=150, tile_size=512, overlap=64)


@pytest.mark.parametrize(
    ("threads", "error"),
    [(0, pdfust.OcrError), (17, pdfust.OcrError), (True, TypeError), (1.5, TypeError)],
)
def test_ocr_engine_validates_threads(threads: object, error: type[Exception]) -> None:
    with pytest.raises(error, match="threads"):
        pdfust.OcrEngine(threads=threads)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("max_concurrent", "error"),
    [(0, pdfust.OcrError), (17, pdfust.OcrError), (True, TypeError), (1.5, TypeError)],
)
def test_ocr_engine_validates_max_concurrent(max_concurrent: object, error: type[Exception]) -> None:
    with pytest.raises(error, match="max_concurrent"):
        pdfust.OcrEngine(max_concurrent=max_concurrent)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("max_model_size", "error"),
    [(0, ValueError), (-1, ValueError), (True, TypeError), (1.5, TypeError)],
)
def test_ocr_engine_validates_max_model_size(max_model_size: object, error: type[Exception]) -> None:
    with pytest.raises(error, match="max_model_size"):
        pdfust.OcrEngine(max_model_size=max_model_size)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("rotation", "error"),
    [(45, pdfust.OcrError), (-90, pdfust.OcrError), (360, pdfust.OcrError), (True, TypeError), (1.5, TypeError)],
)
def test_ocr_engine_validates_input_rotation(
    ocr_engine: pdfust.OcrEngine,
    rotation: object,
    error: type[Exception],
) -> None:
    doc = pdfust.Document()
    doc.new_page(width=100, height=100)
    with pytest.raises(error, match="rotation"):
        ocr_engine.recognize(doc[0], dpi=72, rotation=rotation)  # type: ignore[arg-type]


def test_ocr_engine_validates_runtime_options(ocr_engine: pdfust.OcrEngine) -> None:
    doc = pdfust.Document()
    doc.new_page(width=100, height=100)
    with pytest.raises(pdfust.OcrError, match="tile_size"):
        ocr_engine.recognize(doc[0], dpi=72, tile_size=500)
    with pytest.raises(pdfust.OcrError, match="overlap"):
        ocr_engine.recognize(doc[0], dpi=72, tile_size=512, overlap=16)
    with pytest.raises(pdfust.OcrError, match="min_confidence"):
        ocr_engine.recognize(doc[0], dpi=72, tile_size=512, overlap=64, min_confidence=2)
    with pytest.raises(TypeError, match="tile_size"):
        ocr_engine.recognize(doc[0], dpi=72, tile_size=512.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="overlap"):
        ocr_engine.recognize(doc[0], dpi=72, tile_size=512, overlap=True)
    with pytest.raises(TypeError, match="dpi"):
        ocr_engine.recognize(doc[0], dpi=True)
    with pytest.raises(TypeError, match="min_confidence"):
        ocr_engine.recognize(doc[0], dpi=72, min_confidence=True)
    with pytest.raises(pdfust.PdfError, match="clip does not intersect"):
        ocr_engine.recognize(doc[0], dpi=72, clip=(200, 200, 300, 300))


