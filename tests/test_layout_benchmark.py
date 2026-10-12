from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from runpy import run_path
from typing import Any, cast

import pytest

import pdfust

_BENCHMARK = run_path(str(Path(__file__).parents[1] / "bench" / "layout.py"))
Measurement = cast("type[Any]", _BENCHMARK["Measurement"])
comparison = cast("Callable[[Any, Any], str]", _BENCHMARK["_comparison"])
measure = cast("Callable[[Callable[[], object], int], tuple[float, str, int]]", _BENCHMARK["_measure"])
synthetic_pdf = cast("Callable[..., bytes]", _BENCHMARK["_synthetic_pdf"])


def test_speedup_requires_matching_complete_input_and_output() -> None:
    current = Measurement("sample", "dict", "fresh", 1, "input", "output", 10, 5.0)
    baseline = Measurement("sample", "dict", "fresh", 1, "input", "output", 10, 10.0)
    changed_input = Measurement("sample", "dict", "fresh", 1, "other", "output", 10, 10.0)
    changed_output = Measurement("sample", "dict", "fresh", 1, "input", "other", 10, 10.0)

    assert comparison(current, baseline) == "2.00x"
    assert comparison(baseline, current) == "0.50x"
    assert comparison(current, changed_input) == "input changed"
    assert comparison(current, changed_output) == "output changed"
    assert comparison(current, None) == "n/a"


def test_measurement_rejects_nondeterministic_outputs() -> None:
    outputs = iter([{"text": "first"}, {"text": "second"}])

    with pytest.raises(RuntimeError, match="output changed"):
        measure(lambda: next(outputs), 1)


@pytest.mark.parametrize("unicode_text", [False, True])
def test_synthetic_samples_are_repeatable_and_exercise_tables_and_text(*, unicode_text: bool) -> None:
    data = synthetic_pdf(2, unicode_text=unicode_text)
    assert data == synthetic_pdf(2, unicode_text=unicode_text)
    with pdfust.open(stream=data) as doc:
        assert doc.page_count == 2
        for page in doc:
            tables = page.find_tables()
            assert len(tables) == 1
            assert tables[0].row_count == 4
            assert tables[0].col_count == 3
            assert "Cell 3-2" in tables[0].to_markdown()
            expected = "日本語" if unicode_text else "Positioned text"
            assert expected in page.get_text()
            assert expected in " ".join(word[4] for word in page.get_text("words"))
            assert expected in str(page.get_text("blocks"))
            assert expected in str(page.get_text("dict"))
        markdown = doc.to_markdown()
        assert expected in markdown
        assert "| Cell 0-0 | Cell 0-1 | Cell 0-2 |" in markdown
