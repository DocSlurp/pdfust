"""Verify declared DEV authoring independently from scorer outcomes."""

from __future__ import annotations

from collections import Counter

from bench.rolling_robustness import DESIGN, generate_cases
from bench.silver import sha


def test_generated_sources_are_deterministic_and_cover_predeclared_topologies() -> None:
    cases = generate_cases()
    repeated = generate_cases()
    assert [sha(c["pdf"]) for c in cases] == [sha(c["pdf"]) for c in repeated]
    assert Counter(c["target"]["kind"] for c in cases) == {"borderless": 16, "prose": 8}
    targets = [c["target"] for c in cases if c["target"]["kind"] == "borderless"]
    assert {t["row_count"] for t in targets} == set(DESIGN["total_rows"])
    assert {t["columns"] for t in targets} == set(DESIGN["columns"])
    assert {t["font_size"] for t in targets} == set(DESIGN["font_sizes"])
    assert {t["wrap"] for t in targets} == {0, 1, 2}
    assert any(t["blank_cell"] for t in targets)
    assert any(t["total_row"] for t in targets)
    assert any(any(t["numeric_alignment"]) for t in targets)
    assert any(not all(t["numeric_alignment"]) for t in targets)


def test_authored_slot_lines_match_reference_text_without_extraction() -> None:
    for case in generate_cases():
        target = case["target"]
        if not target["tables"]:
            assert target["authored_slots"] == []
            continue
        table = target["tables"][0]
        lines: dict[tuple[int, int], list[str]] = {}
        for slot in target["authored_slots"]:
            lines.setdefault((slot["row"], slot["column"]), []).append(slot["text"])
        for row, values in enumerate(table["values"]):
            for col, value in enumerate(values):
                assert " ".join(lines.get((row, col), [])) == value
