"""Factorization is bounded by immutable geometry and checked against complete composition."""

from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import Any

import pytest
from bench import p003_segment_oracle as oracle
from tests.test_p003_report import table


def pools() -> tuple[dict, list[list[dict]], dict]:
    source = {"words": [{"id": "a"}, {"id": "b"}]}
    menus = []
    targets = []
    for i, (identifier, text) in enumerate([("a", "A"), ("b", "B")]):
        bbox = [i * 20, 0, i * 20 + 10, 10]
        target = {**table([[text]]), "bbox": bbox}
        targets.append(target)
        menus.append(
            [
                {"state": {"tables": [{**table([[value]]), "bbox": bbox, "cells": [{"source_ids": [identifier]}]}]}}
                for value in ["wrong", text]
            ]
        )
    return source, menus, {"id": "p", "tables": targets}


def test_bbox_or_presence_variation_refuses_factorization() -> None:
    source, menus, _ = pools()
    menus[0][1]["state"]["tables"][0]["bbox"] = [0, 0, 11, 10]
    with pytest.raises(ValueError, match="bbox/presence"):
        oracle.fixed_crop_inventory(source, menus)


def test_cross_crop_ownership_refuses_factorization() -> None:
    source, menus, _ = pools()
    menus[1][0]["state"]["tables"][0]["cells"][0]["source_ids"] = ["a"]
    with pytest.raises(ValueError, match="crosses crops"):
        oracle.fixed_crop_inventory(source, menus)


def test_factorized_objective_matches_exhaustive_tiny_menu(monkeypatch: pytest.MonkeyPatch) -> None:
    source, menus, target = pools()

    def compose(_source: dict, candidates: list[list[dict]], indexes: list[int], ident: str) -> dict[str, Any]:
        return {
            "id": ident,
            "status": "ok",
            "tables": [deepcopy(menu[i]["state"]["tables"][0]) for menu, i in zip(candidates, indexes, strict=True)],
        }

    monkeypatch.setattr(oracle, "prediction", compose)
    result = oracle.oracle_page(target, source, menus)
    exhaustive = [
        oracle.strict_scores([target], [compose(source, menus, list(indexes), "p")])["totals"]
        for indexes in product(range(2), repeat=2)
    ]
    assert result["selected_indexes"] == [1, 1]
    assert result["score"]["strict_exact_cells"] == max(s["strict_exact_cells"] for s in exhaustive) == 2
    assert result["maximum_complete_tables"] == max(s["complete_tables"] for s in exhaustive) == 2
