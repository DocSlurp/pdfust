"""Source geometry baseline: divider coverage, enclosure and bounded refusal."""

from itertools import pairwise
from typing import Any

import pytest
from bench.lowlevel_geometry import MAX_COMMANDS, MAX_PATHS, grouping

BOXES = [[50, 180, 200, 196], [50, 198, 200, 214]]


def stroke(items: list[Any], *, closed: bool = False) -> dict[str, Any]:
    return {"type": "s", "color": [0, 0, 0], "width": 0.8, "close_path": closed, "items": items}


def rectangle() -> dict[str, Any]:
    points = [(40, 175), (210, 175), (210, 220), (40, 220), (40, 175)]
    return stroke([("l", left, right) for left, right in pairwise(points)], closed=True)


def test_split_join_and_unresolved_are_based_on_source_geometry() -> None:
    outer = rectangle()
    divider = stroke([("l", (40, 201), (210, 201))])
    assert grouping([outer], BOXES, task="line_ownership") == "join"
    assert grouping([outer, divider], BOXES, task="line_ownership") == "split"
    assert grouping([divider], BOXES, task="line_ownership") == "split"
    assert grouping([], BOXES, task="line_ownership") == "unresolved"
    assert grouping([outer, divider], BOXES, task="character_boundary") == "unresolved"


def test_partial_rules_and_unclosed_or_malformed_rectangles_do_not_join() -> None:
    outer = rectangle()
    partial = stroke([("l", (40, 201), (125, 201))])
    assert grouping([outer, partial], BOXES, task="line_ownership") == "unresolved"
    outer["close_path"] = False
    assert grouping([outer], BOXES, task="line_ownership") == "unresolved"
    outer = rectangle()
    outer["items"][-1] = outer["items"][0]
    assert grouping([outer], BOXES, task="line_ownership") == "unresolved"


def test_unrelated_rules_and_nonstroke_paints_do_not_supply_dividers() -> None:
    outside = stroke([("l", (40, 250), (210, 250))])
    diagonal = stroke([("l", (40, 190), (210, 205))])
    invisible = stroke([("l", (40, 201), (210, 201))])
    invisible["color"] = None
    assert grouping([outside, diagonal, invisible], BOXES, task="line_ownership") == "unresolved"
    fill = rectangle()
    fill["type"] = "f"
    assert grouping([fill], BOXES, task="line_ownership") == "unresolved"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, 1e20])
def test_nonfinite_or_unreasonable_geometry_refuses(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        grouping([stroke([("l", (40, value), (210, 201))])], BOXES, task="line_ownership")


def test_limits_and_target_shapes_refuse_atomically() -> None:
    with pytest.raises(ValueError, match="admission"):
        grouping([stroke([])] * (MAX_PATHS + 1), BOXES, task="line_ownership")
    with pytest.raises(ValueError, match="commands"):
        grouping([stroke([("l", (0, 0), (1, 1))] * (MAX_COMMANDS + 1))], BOXES, task="line_ownership")
    with pytest.raises(ValueError, match="positive"):
        grouping([], [[1, 1, 0, 0], BOXES[1]], task="line_ownership")
