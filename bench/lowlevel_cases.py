"""Authored DEV controls for conditional pre-word boundaries and cell grouping.

Gold fields are scorer-only. Encodings change text operator granularity/order,
never visible content. These controls are not independent producer evidence.
"""

from __future__ import annotations

import hashlib
from typing import Any

from bench.feature_cases import page_pdf

ENCODINGS = ("runs", "array", "positioned")
CHOICES = ("join", "split", "unresolved")
_SIZE = 10
_ADVANCE = 6.0


def _literal(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _operators(runs: list[tuple[str, float, float]], encoding: str) -> str:
    ops = []
    if encoding == "positioned":
        glyphs = [(char, x + index * _ADVANCE, y) for text, x, y in runs for index, char in enumerate(text)]
        # Reverse painting order without changing independent glyph placements.
        runs = list(reversed(glyphs))
    for text, x, y in runs:
        show = (
            "[" + " ".join(f"({_literal(char)})" for char in text) + "] TJ"
            if encoding == "array"
            else f"({_literal(text)}) Tj"
        )
        ops.append(f"BT /F4 {_SIZE} Tf 1 0 0 1 {x:.4f} {y:.4f} Tm {show} ET")
    return "\n".join(ops)


def _boundary(index: int, choice: str) -> tuple[list[tuple[str, float, float]], str, dict[str, Any], list[list[str]]]:
    left, right = ("12", "EA") if index == 0 else (("34", "KG"), ("56", "HR"), ("78", "KM"))[index - 1]
    gap = (0.0, 1.2, 3.6, 7.2)[index]
    x_right = 50 + 2 * _ADVANCE + gap
    target: list[tuple[str, float, float]] = [(left, 50, 600), (right, x_right, 600)]
    headers: list[tuple[str, float, float]]
    if choice == "join":
        headers = [("Item code", 50, 630)]
        grouping = [[left + right]]
    elif choice == "split":
        headers = [("Qty / Unit", 50, 630)]
        grouping = [[left], [right]]
    else:
        headers = [("Entry", 50, 630)]
        grouping = []
    evidence = {
        "task": "character_boundary",
        "question": "Choose the field grouping supported by the visible region.",
        "bbox": [40, 125, 250, 215],
        "target": {
            "boxes": [
                [49, 179, round(50 + 2 * _ADVANCE, 4), 196],
                [round(x_right, 4), 179, round(x_right + 2 * _ADVANCE, 4), 196],
            ],
            "boundary_index": 2,
        },
        "choices": list(CHOICES),
    }
    return headers + target, "", evidence, grouping


def _wrap(index: int, choice: str) -> tuple[list[tuple[str, float, float]], str, dict[str, Any], list[list[str]]]:
    first, second = (
        ("Valve set", "Copper fitting"),
        ("Inspection", "Travel charge"),
        ("Filter unit", "Seal kit"),
        ("Panel wiring", "Cable tray"),
    )[index]
    target: list[tuple[str, float, float]] = [(first, 50, 600), (second, 50, 582), ("120", 440, 600)]
    headers: list[tuple[str, float, float]] = [("Description", 50, 630), ("Amount", 440, 630)]
    rules = ""
    if choice != "unresolved":
        rules = "0 G 0.8 w 40 570 500 45 re S 420 570 m 420 615 l S"
        if choice == "split":
            rules += " 40 591 m 540 591 l S"
    grouping = [[first, second, "120"]] if choice == "join" else [[first, "120"], [second]]
    if choice == "unresolved":
        grouping = []
    evidence = {
        "task": "line_ownership",
        "question": "Choose whether the description lines occupy one table row or separate rows.",
        "bbox": [35, 150, 545, 225],
        "target": {
            "boxes": [[49, 179, 200, 196], [49, 197, 200, 214]],
            "boundary_index": None,
        },
        "choices": list(CHOICES),
    }
    return headers + target, rules, evidence, grouping


def cases() -> list[dict[str, Any]]:
    """Return 24 logical DEV cases crossed with three content encodings.

    Only ``evidence`` and source-derived observations belong in model input.
    Header labels are imperfect business cues, not externally verified gold;
    boundary labels are hypotheses to audit, unlike explicit ruled cell splits.
    """
    output = []
    for family, builder in (("boundary", _boundary), ("wrap", _wrap)):
        for index in range(4):
            for choice in CHOICES:
                runs, rules, evidence, grouping = builder(index, choice)
                logical = hashlib.sha256(repr((runs, rules)).encode()).hexdigest()[:16]
                for encoding in ENCODINGS:
                    data = page_pdf(rules + "\n" + _operators(runs, encoding))
                    output.append(
                        {
                            "id": hashlib.sha256(data).hexdigest()[:16],
                            "logical_id": logical,
                            "family": family,
                            "encoding": encoding,
                            "expected": choice,
                            "expected_groups": grouping,
                            "pdf_bytes": data,
                            "evidence": evidence,
                        }
                    )
    return output


def history_cases() -> list[dict[str, Any]]:
    """Return separate DEV history controls; inferred joins are tentative gold.

    The entire page remains available to extraction. A history summary therefore
    compresses existing evidence rather than acquiring additional information.
    """
    output = []
    contents = (
        ("Valve assembly", "pressure-rated fittings"),
        ("Site inspection", "weekend service hours"),
        ("Cable replacement", "weather-resistant conduit"),
    )
    for first, second in contents:
        for variant in ("multiline", "absent", "new_identifier", "singleline"):
            runs: list[tuple[str, float, float]] = [
                ("Item", 40, 745),
                ("Description", 100, 745),
                ("Amount", 450, 745),
            ]
            if variant != "absent":
                for row, (description, tail) in enumerate(
                    (
                        ("Filter unit", "fine mesh screen"),
                        ("Pump assembly", "stainless steel housing"),
                        ("Control panel", "wall mounting kit"),
                    )
                ):
                    baseline = 715 - row * 40
                    runs.extend(
                        [
                            (str(101 + row), 40, baseline),
                            (description, 100, baseline),
                            (str(65 + row * 15), 450, baseline),
                        ]
                    )
                    if variant != "singleline":
                        runs.append((tail, 100, baseline - 18))
            runs.extend([("104", 40, 575), (first, 100, 575), ("120", 450, 575), (second, 100, 557)])
            if variant == "new_identifier":
                runs.append(("105", 40, 557))
            expected = "join" if variant == "multiline" else "split" if variant == "new_identifier" else "unresolved"
            recoverability = (
                "conventional"
                if variant == "multiline"
                else "visible_identifier"
                if variant == "new_identifier"
                else "unresolved"
            )
            grouping = (
                [[first, second, "120"]]
                if expected == "join"
                else [[first, "120"], [second]]
                if expected == "split"
                else []
            )
            evidence = {
                "task": "line_ownership",
                "question": "Choose whether the description lines occupy one table row or separate rows.",
                "bbox": [35, 205, 530, 245],
                "target": {"boxes": [[99, 205, 310, 224], [99, 223, 310, 242]], "boundary_index": None},
                "choices": list(CHOICES),
            }
            logical = hashlib.sha256(repr(runs).encode()).hexdigest()[:16]
            for encoding in ENCODINGS:
                data = page_pdf(_operators(runs, encoding))
                output.append(
                    {
                        "id": hashlib.sha256(data).hexdigest()[:16],
                        "logical_id": logical,
                        "family": "history",
                        "encoding": encoding,
                        "expected": expected,
                        "expected_groups": grouping,
                        "recoverability": recoverability,
                        "history_variant": variant,
                        "pdf_bytes": data,
                        "evidence": evidence,
                    }
                )
    return output
