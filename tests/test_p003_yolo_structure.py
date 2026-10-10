"""Source-only acquisition ownership preserves complete literal inventories."""

from __future__ import annotations

from bench import p003_yolo_structure as structure


def _source() -> dict:
    return {
        "page_size": [0, 0, 100, 100],
        "words": [
            {"id": "a", "text": "duplicate", "bbox": [1, 1, 5, 5]},
            {"id": "b", "text": "duplicate", "bbox": [6, 1, 10, 5]},
            {"id": "c", "text": "contested", "bbox": [12, 1, 16, 5]},
            {"id": "d", "text": "crossing", "bbox": [25, 1, 35, 5]},
            {"id": "e", "text": "outside", "bbox": [90, 90, 100, 100]},
        ],
    }


def _boxes() -> list[dict]:
    return [
        {"label": "table", "confidence": 0.5, "global_bbox": [0, 0, 20, 20]},
        {"label": "table", "confidence": 0.99, "global_bbox": [11, 0, 31, 20]},
        {"label": "text", "confidence": 0.9, "global_bbox": [0, 0, 100, 100]},
    ]


def test_contested_center_has_no_confidence_winner_and_complete_context() -> None:
    plan = structure.ownership(_source(), _boxes(), 1024)
    assert len(plan["proposals"]) == 2
    assert plan["proposals"][0]["source_ids"] == ["a", "b"]
    assert plan["proposals"][1]["source_ids"] == ["d"]
    assert plan["unowned_source_ids"] == ["c", "e"]
    assert plan["decisions"][2]["reason"] == "contested_center"
    assert "c" in plan["proposals"][0]["context_only_source_ids"]
    assert "c" in plan["proposals"][1]["context_only_source_ids"]
    assert len(plan["overlapping_proposals"]) == 1
    assert plan["proposals"][1]["crossing_owned_word_ids"] == ["d"]


def test_physical_duplicate_strings_keep_distinct_literal_ids() -> None:
    source = _source()
    plan = structure.ownership(source, _boxes(), 640)
    owned = [i for p in plan["proposals"] for i in p["source_ids"]]
    assert sorted(owned + plan["unowned_source_ids"]) == sorted(w["id"] for w in source["words"])
    assert owned.count("a") == 1
    assert owned.count("b") == 1
    assert all(p["region_id"].startswith("s640-") for p in plan["proposals"])


def test_zero_proposals_keeps_all_source_unowned_and_no_invented_crop() -> None:
    source = _source()
    plan = structure.ownership(source, [], 1280)
    assert plan["proposals"] == []
    assert plan["unowned_source_ids"] == [w["id"] for w in source["words"]]
    assert all(d["reason"] == "outside_all_proposals" for d in plan["decisions"])


def test_inclusive_boundary_tie_is_unresolved_without_split_or_merge() -> None:
    source = {"page_size": [0, 0, 100, 100], "words": [{"id": "w", "text": "whole", "bbox": [9, 4, 11, 6]}]}
    boxes = [
        {"label": "table", "confidence": 0.9, "global_bbox": [0, 0, 10, 10]},
        {"label": "table", "confidence": 0.4, "global_bbox": [10, 0, 20, 10]},
    ]
    plan = structure.ownership(source, boxes, 640)
    assert plan["unowned_source_ids"] == ["w"]
    assert all(p["source_ids"] == [] for p in plan["proposals"])
    assert plan["overlapping_proposals"] == []
