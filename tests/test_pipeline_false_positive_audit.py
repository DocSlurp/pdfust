"""Source observations remain independent of outcomes and preserve unavailable data."""

from copy import deepcopy

from bench.pipeline_false_positive_audit import source_features


def test_source_features_are_literal_geometry_only_and_do_not_mutate() -> None:
    source = {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "r:w0", "text": "Sentence.", "bbox": [10, 10, 30, 20], "line": [0, 0]},
            {"id": "w1", "text": "12.5", "bbox": [50, 10, 60, 20], "line": [0, 0]},
            {"id": "w2", "text": "Next", "bbox": [10, 30, 25, 40], "line": [0, 1]},
        ],
        "vector_candidates": [],
        "gold": "irrelevant",
        "family": "irrelevant",
    }
    detection = {"boxes": [{"label": "Table", "bbox": [0, 0, 50, 50], "confidence": 0.9}]}
    original = deepcopy(source)
    result = source_features(source, detection)
    assert source == original
    assert result["words"] == 3
    assert result["sentence_terminal_fraction"] == 1 / 3
    assert result["numeric_word_fraction"] == 1 / 3
    assert result["source_line_id_count"] == 2
    assert result["row_bin_count"] == 2
    assert result["detector_median_area_fraction"] == 0.25
    source["gold"], source["family"] = "other", "other"
    assert source_features(source, detection) == result


def test_unavailable_source_and_detector_are_explicit() -> None:
    assert source_features(None, None) == {"source_available": False}
    source = {"page_size": [100, 100], "words": [], "vector_candidates": []}
    result = source_features(source, None)
    assert result["detector_available"] is False
    assert result["detector_table_boxes"] is None
    assert result["row_gap_cv"] is None
    assert result["sentence_terminal_fraction"] is None
