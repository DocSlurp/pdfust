"""Keep the continuous character display meaningful and independent of structural acceptance."""

import pytest
from bench.p003_content_visual_review import content_f1, quality_color


@pytest.mark.parametrize("value", [-0.01, 1.01, float("nan"), float("inf")])
def test_unknown_or_invalid_scores_cannot_become_green(value: float) -> None:
    """Missing/invalid evidence must never silently receive a favorable color."""
    with pytest.raises(ValueError, match="finite"):
        quality_color(value)


def test_content_f1_does_not_replace_separate_precision_and_recall() -> None:
    """Exact content and a low-recall output retain different numeric summaries."""
    assert content_f1(1, 1) == 1
    assert content_f1(0, 0) == 0
    assert content_f1(1, 0.5) == pytest.approx(2 / 3)
