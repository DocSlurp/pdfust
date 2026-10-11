"""Color only trusted normalized-character alignment groups, retaining span warnings."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw

from bench.p003_content_visual_review import quality_color
from bench.p003_visual_review import lines, measured_wrap


def group_score(group: dict[str, Any]) -> float | None:
    """Use exact retained match/denominator counts; blank groups have no character score."""
    matched, reference, prediction = (group[k] for k in ("matched", "reference_units", "prediction_units"))
    if any(not isinstance(value, int) or value < 0 for value in (matched, reference, prediction)):
        raise ValueError("Alignment counts must be nonnegative integers")
    if matched > min(reference, prediction):
        raise ValueError("Matched count exceeds an alignment denominator")
    return 2 * matched / (reference + prediction) if reference + prediction else None


def span_warning(row: dict[str, Any], group: dict[str, Any], reference: dict[str, Any], actual: dict[str, Any]) -> bool:
    """Warn where a declared merged anchor differs; never infer physical source cell boxes."""
    signatures = []
    for table, row_key, column_key in (
        (reference, "reference_row", "reference_columns"),
        (actual, "prediction_row", "prediction_columns"),
    ):
        r, bounds = row[row_key], group[column_key]
        merged = set()
        if r is not None and bounds is not None:
            for span in table.get("spans", []):
                sr, sc, rs, cs = (span[k] for k in ("row", "column", "row_span", "column_span"))
                if (rs > 1 or cs > 1) and sr <= r < sr + rs and sc < bounds[1] and sc + cs > bounds[0]:
                    merged.add((r - sr, sc - bounds[0], rs, cs))
        signatures.append(merged)
    return signatures[0] != signatures[1]


def alignment_grid(content: dict[str, Any], reference: dict[str, Any], actual: dict[str, Any]) -> Image.Image:
    """Display actual witness strings in aligned groups, including explicit reference-only rows."""
    width = 980
    height = 140 + sum(105 for _ in content["row_alignment"])
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    lines(draw, (15, 10), "Actual output joined into TRUSTED ALIGNMENT GROUPS", width - 30, 20)
    lines(
        draw,
        (15, 43),
        "Not physical cells. Each group shares its exact F1; M/R/P = matched/reference/predicted "
        "normalized characters. Blank groups gray. Amber border: changed merge membership.",
        width - 30,
        16,
    )
    y = 140
    for row in content["row_alignment"]:
        for group in row["cells"]:
            prediction_bounds = group["prediction_columns"]
            bounds = prediction_bounds or group["reference_columns"]
            count = actual["col_count"] if prediction_bounds else reference["col_count"]
            x1, x2 = (15 + (width - 30) * value / count for value in bounds)
            score = group_score(group)
            color = quality_color(score) if score is not None else (150, 150, 150)
            pale = tuple(round(v * 0.18 + 255 * 0.82) for v in color)
            warning = span_warning(row, group, reference, actual)
            border = (192, 133, 24) if warning else color
            draw.rectangle((x1, y, x2, y + 105), fill=pale, outline=border, width=4 if warning else 2)
            score_label = f"F1 {score:.3f}" if score is not None else "blank / no units"
            missing = row["prediction_row"] is None
            label = f"r {row['reference_row']} / p {row['prediction_row']}: {score_label}"
            lines(draw, (x1 + 5, y + 4), label, int(x2 - x1 - 10), 13)
            actual_text = "NO OUTPUT ROW" if missing else group["prediction_text"]
            lines(draw, (x1 + 5, y + 30), actual_text, int(x2 - x1 - 10), 16)
            if group["prediction_text"] != group["reference_text"]:
                reference_text = group["reference_text"]
                # A bounded first line is labelled as a preview; exact full text stays in trusted evidence.json.
                chunks = measured_wrap(reference_text, x2 - x1 - 50)
                lines(
                    draw,
                    (x1 + 5, y + 57),
                    "Ref: " + chunks[0] + ("…" if len(chunks) > 1 else ""),
                    int(x2 - x1 - 10),
                    13,
                )
            units = f"M/R/P {group['matched']}/{group['reference_units']}/{group['prediction_units']}"
            lines(draw, (x1 + 5, y + 82), units, int(x2 - x1 - 10), 13)
        y += 105
    return image
