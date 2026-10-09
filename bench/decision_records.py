"""Source-linked record materialization and exact DEV experiment scoring."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from math import isfinite
from typing import Any


def _reject(message: str) -> None:
    raise ValueError(message)


def validate_assembly(case: dict[str, Any], result: dict[str, Any]) -> None:  # noqa: C901, PLR0912
    """Reject omitted, duplicate or fabricated owners and invalid references."""
    expected = {word["id"] for word in case["evidence"]["words"]}
    owners = [source for cell in result["cells"] for source in cell["source_ids"]]
    owners.extend(result["unresolved_ids"])
    if Counter(owners) != Counter(expected):
        _reject("Source ownership must cover each admitted word exactly once")
    cell_ids = [cell["id"] for cell in result["cells"]]
    if len(cell_ids) != len(set(cell_ids)):
        _reject("Duplicate cell ID")
    words = {word["id"]: word for word in case["evidence"]["words"]}
    cells = {cell["id"]: cell for cell in result["cells"]}
    record_keys = [_record_key(record) for record in result["records"]]
    if len(record_keys) != len(set(record_keys)):
        _reject("Duplicate record")
    for record in result["records"]:
        for field in ("row_key_ids", "value_ids", "unit_ids"):
            if len(record[field]) != len(set(record[field])):
                _reject("Duplicate record source reference")
            if not set(record[field]) <= expected:
                _reject("Unknown record source ID")
        for header in record["header_path"]:
            if len(header) != len(set(header)):
                _reject("Duplicate header reference")
            if not any(cell["role"] == "header" and cell["source_ids"] == header for cell in result["cells"]):
                _reject("Header path must reference an owned header cell")
            if not set(header) <= expected:
                _reject("Unknown header source ID")
        if not set(record["cell_ids"]) <= set(cell_ids):
            _reject("Unknown record cell")
        if len(record["cell_ids"]) != len(set(record["cell_ids"])):
            _reject("Duplicate record cell reference")
        owned_key = [
            source
            for cell_id in record["cell_ids"]
            if cells[cell_id]["role"] == "row_key"
            for source in cells[cell_id]["source_ids"]
        ]
        owned_value = [
            source
            for cell_id in record["cell_ids"]
            if cells[cell_id]["role"] == "value"
            for source in cells[cell_id]["source_ids"]
        ]
        if owned_key != record["row_key_ids"] or owned_value != record["value_ids"]:
            _reject("Record references disagree with cell ownership")
        for field, reference in (("row_key", "row_key_ids"), ("value", "value_ids")):
            if field in record and record[field] != " ".join(words[source]["text"] for source in record[reference]):
                _reject("Record text disagrees with source IDs")
        if "headers" in record and record["headers"] != [
            " ".join(words[source]["text"] for source in header) for header in record["header_path"]
        ]:
            _reject("Header text disagrees with source IDs")
    if "unresolved_words" in result and result["unresolved_words"] != [
        word for word in case["evidence"]["words"] if word["id"] in result["unresolved_ids"]
    ]:
        _reject("Unresolved words disagree with source IDs")
    for cell in result["cells"]:
        if "text" in cell and cell["text"] != " ".join(words[source]["text"] for source in cell["source_ids"]):
            _reject("Cell text disagrees with source IDs")
        if (
            len(cell["bbox"]) != len((0, 0, 0, 0))
            or not all(isfinite(value) for value in cell["bbox"])
            or cell["bbox"][0] > cell["bbox"][2]
            or cell["bbox"][1] > cell["bbox"][3]
        ):
            _reject("Invalid cell bounds")


def materialize(case: dict[str, Any], choice: str) -> dict[str, Any]:
    """Select existing cells and derive exact text without model-generated text."""
    if choice not in ("A", "B", "unresolved"):
        _reject("Unknown assembly choice")
    if choice == "unresolved":
        result = {
            "choice": choice,
            "cells": [],
            "records": [],
            "unresolved_ids": [word["id"] for word in case["evidence"]["words"]],
        }
    else:
        result = deepcopy(case["evidence"]["assemblies"][choice])
        result["choice"] = choice
    validate_assembly(case, result)
    text = {word["id"]: word["text"] for word in case["evidence"]["words"]}
    for cell in result["cells"]:
        cell["text"] = " ".join(text[source] for source in cell["source_ids"])
    for record in result["records"]:
        record["row_key"] = " ".join(text[source] for source in record["row_key_ids"])
        record["value"] = " ".join(text[source] for source in record["value_ids"])
        record["headers"] = [" ".join(text[source] for source in header) for header in record["header_path"]]
    result["unresolved_words"] = [
        deepcopy(word) for word in case["evidence"]["words"] if word["id"] in result["unresolved_ids"]
    ]
    return result


def _record_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        tuple(record["row_key_ids"]),
        tuple(record["value_ids"]),
        tuple(tuple(header) for header in record["header_path"]),
        tuple(record["unit_ids"]),
    )


def score_records(case: dict[str, Any], result: dict[str, Any], mode: str | None = None) -> dict[str, Any]:
    """Score source ownership, complete record references and whole-region exactness."""
    try:
        validate_assembly(case, result)
    except (ValueError, KeyError, TypeError):
        return {
            "valid": False,
            "source_conservation": False,
            "region_exact": False,
            "record_precision": 0.0,
            "record_recall": 0.0,
            "record_f1": 0.0,
        }
    choice = case["gold"]["choice"] if mode is None else case["gold"]["mode_choices"][mode]
    gold = materialize(case, choice)
    predicted = Counter(_record_key(record) for record in result["records"])
    expected = Counter(_record_key(record) for record in gold["records"])
    matched = sum((predicted & expected).values())
    precision = matched / sum(predicted.values()) if predicted else float(not expected)
    recall = matched / sum(expected.values()) if expected else float(not predicted)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    def cell_key(cell: dict[str, Any]) -> tuple[Any, ...]:
        return (tuple(cell["source_ids"]), tuple(cell["bbox"]), cell["role"])

    exact = (
        predicted == expected
        and Counter(cell_key(cell) for cell in result["cells"]) == Counter(cell_key(cell) for cell in gold["cells"])
        and sorted(result["unresolved_ids"]) == sorted(gold["unresolved_ids"])
    )
    return {
        "valid": True,
        "source_conservation": True,
        "region_exact": exact,
        "record_precision": precision,
        "record_recall": recall,
        "record_f1": f1,
    }
