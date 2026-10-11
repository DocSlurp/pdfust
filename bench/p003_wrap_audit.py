"""Retrospective wrap diagnostics from immutable, previously reviewed score witnesses."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from bench.p003_content_alignment import LIMITS, compare_content
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

# ruff: noqa: EM101, TRY003
VERSION = "p003-wrap-audit-v1"
KEYS = ("matched", "substituted", "missing", "extra", "reference_units", "prediction_units")
SOURCES = {
    "continuation-oplog-evaluation-v1/report.json": "1636cd97b5e177f83f31a5c2b492c2a06b61cde014e0a4d7fdf40797803e3bdd",
    "continuation-rolling28-rescore-v1/report.json": "0520c657f375aceac2c2dabfc112110cb2011b385a17ae2fdf6e85e8408e8949",
    "continuation-admission96-rescore-v1/report.json": (
        "e489e337ff56973f61f3d55537feb8ab39701add834fb2f6ef61de0093cd7da0"
    ),
}


def anchor_matrix(receipt: dict[str, Any]) -> list[list[str]]:
    """Recover each retained anchor literal once, retaining covered blanks as placeholders."""
    rows, columns = receipt["row_count"], receipt["col_count"]
    if not 1 <= rows <= LIMITS["rows"] or not 1 <= columns <= LIMITS["columns"] or rows * columns > LIMITS["slots"]:
        raise ValueError("Bounded original dimensions required")
    matrix = [[""] * columns for _ in range(rows)]
    seen: set[tuple[int, int]] = set()
    for anchor in receipt["anchors"]:
        row, column = anchor["row"], anchor["column"]
        if (row, column) in seen or not 0 <= row < rows or not 0 <= column < columns:
            raise ValueError("Unique in-range anchor coordinates required")
        seen.add((row, column))
        matrix[row][column] = anchor["literal"]
    if sum(len(value) for row in matrix for value in row) != receipt["literal_characters"]:
        raise ValueError("Original literal conservation differs")
    return matrix


def residual_counts(total: dict[str, int], pairs: list[dict[str, Any]]) -> dict[str, int]:
    """Preserve all existing unmatched-table penalties in the new full-cohort denominator."""
    result = {key: total.get(key, 0) - sum(pair["counts"][key] for pair in pairs) for key in KEYS}
    if any(value < 0 for value in result.values()):
        raise ValueError("Matched counts exceed complete cohort")
    if result["matched"] + result["substituted"] + result["missing"] != result["reference_units"]:
        raise ValueError("Reference residual conservation differs")
    if result["matched"] + result["substituted"] + result["extra"] != result["prediction_units"]:
        raise ValueError("Prediction residual conservation differs")
    return result


def prepare(directory: Path, output: Path) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Freeze all declared reviewed pairs; read no original private-target files."""
    directory, output = guard_path(directory), guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh preparation required")
    artifacts, cases, cohorts = [], [], []

    def admitted(path: Path, expected: str | None = None) -> dict[str, Any]:
        data = guard_path(path).read_bytes()
        digest = sha(data)
        if expected is not None and digest != expected:
            raise ValueError("Reviewed source report differs")
        artifacts.append({"path": str(path), "sha256": digest})
        return json.loads(data)

    oplog = admitted(directory / next(iter(SOURCES)), next(iter(SOURCES.values())))
    for model in oplog["models"]:
        name = "oplog/" + model["model"]
        members = [row for row in oplog["records"] if row["model"] == model["model"]]
        selected = []
        for record in members:
            if record["exclusion"]:
                continue
            key = name + "/" + record["case_id"]
            selected.append(key)
            cases.append(
                {
                    "id": key,
                    "cohort": name,
                    "source_case": record["case_id"],
                    "reference": record["reference_body"]["values"],
                    "prediction": record["body_table"]["values"],
                    "old_content": record["content"],
                    "original_strict": record["strict_body_complete"],
                    "finished": record["stop_reason"] == "finished",
                    "original_stop_reason": record["stop_reason"],
                }
            )
        cohorts.append(
            {
                "id": name,
                "kind": "conditional_region_body",
                "intended": len(members),
                "known": len(selected),
                "case_ids": selected,
                "old_counts": model["counts"],
                "old_content_recovered": model["emitted_content_recovered_bodies"],
                "original_primary": model,
                "unmatched_counts": dict.fromkeys(KEYS, 0),
            }
        )
    for relative, expected in list(SOURCES.items())[1:]:
        report = admitted(directory / relative, expected)
        family = "candidate" if "rolling28" in relative else "admission"
        for run in report["runs"]:
            data = admitted(directory / Path(relative).parent / (run["name"] + ".json"))
            if data["summary"] != run:
                raise ValueError("Per-run witness differs from pinned report")
            name = family + "/" + run["name"]
            selected, contents = [], []
            for page in data["secondary"]["pages"]:
                for pair in page["pairs"]:
                    content = pair["content"]
                    if not content["supported"]:
                        raise ValueError("This bounded input family requires supported original witnesses")
                    key = name + "/" + page["id"] + "/" + str(pair["target"]) + ":" + str(pair["prediction"])
                    selected.append(key)
                    contents.append(content)
                    cases.append(
                        {
                            "id": key,
                            "cohort": name,
                            "source_case": page["id"],
                            "reference": anchor_matrix(content["span_coverage"]["reference"]),
                            "prediction": anchor_matrix(content["span_coverage"]["prediction"]),
                            "old_content": content,
                            "original_strict": pair["strict_complete"],
                            "original_schema": pair["schema"],
                            "original_span_topology_equal": content["span_topology_equal"],
                        }
                    )
            cohorts.append(
                {
                    "id": name,
                    "kind": run.get("scope", "unaccepted_candidate"),
                    "intended": run["strict"]["pages"],
                    "case_ids": selected,
                    "old_counts": run["secondary"]["counts"],
                    "old_content_recovered": run["secondary"]["counts"]["content_recovered_tables"],
                    "original_primary": run,
                    "unmatched_counts": residual_counts(run["secondary"]["counts"], contents),
                }
            )
    ids = [row["id"] for row in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Unique complete comparison identities required")
    for case in cases:
        replay = compare_content(case["reference"], case["prediction"])
        if not replay["supported"] or replay["counts"] != case["old_content"]["counts"]:
            raise ValueError("Retained matrix projection does not reproduce old content counts")
    result = {
        "version": VERSION,
        "scope": "Post-hoc diagnostic revision after user identified formatting over-penalization; no blind claim",
        "source_artifacts": artifacts,
        "cases": cases,
        "cohorts": cohorts,
        "new_api_calls": 0,
        "original_target_files_read": False,
        "original_scores_changed": False,
    }
    write_json(output, result)
    return result


def audit(source: Path, expected_sha256: str, output: Path) -> dict[str, Any]:
    """Evaluate every frozen pair, preserving strict scores and unmatched-table content."""
    from bench.p003_wrap_content import compare_wrap_content  # noqa: PLC0415

    source, output = guard_path(source), guard_path(output)
    if output.exists():
        raise FileExistsError("Fresh wrap evaluation required")
    raw = source.read_bytes()
    if sha(raw) != expected_sha256:
        raise ValueError("Frozen input bytes differ")
    frozen = json.loads(raw)
    for artifact in frozen["source_artifacts"]:
        if sha(guard_path(Path(artifact["path"])).read_bytes()) != artifact["sha256"]:
            raise ValueError("Original reviewed evidence changed")
    with Resources() as resources:
        records = [
            {**case, "wrap_content": compare_wrap_content(case["reference"], case["prediction"])}
            for case in frozen["cases"]
        ]
        by_id = {row["id"]: row for row in records}
        summaries = []
        for cohort in frozen["cohorts"]:
            members = [by_id[key] for key in cohort["case_ids"]]
            unsupported = [row["id"] for row in members if not row["wrap_content"]["supported"]]
            counts = Counter(cohort["unmatched_counts"])
            for row in members:
                if row["wrap_content"]["supported"]:
                    counts.update(row["wrap_content"]["counts"])
            precision = counts["matched"] / counts["prediction_units"] if counts["prediction_units"] else None
            recall = counts["matched"] / counts["reference_units"] if counts["reference_units"] else None
            recovered = [
                row for row in members if row["wrap_content"].get("content_recovered_with_row_order") is True
            ]
            summaries.append(
                {
                    **cohort,
                    "counts": dict(counts),
                    "full_content_precision": precision if not unsupported else None,
                    "full_content_recall": recall if not unsupported else None,
                    "unsupported_ids": unsupported,
                    "wrap_content_recovered": len(recovered),
                    "finished_wrap_recovered": sum(row.get("finished", False) for row in recovered),
                    "schema_correctness": None,
                    "unit_policy": (
                        "Normalized Unicode characters plus declared wrap-join spaces in matched pairs; "
                        "unmatched penalties retain normalized anchor literal characters only"
                    ),
                    "join_separator_units": {
                        side: sum(
                            row["wrap_content"].get("coverage", {}).get(side + "_join_separator_units", 0)
                            for row in members
                            if row["wrap_content"]["supported"]
                        )
                        for side in ("reference", "prediction")
                    },
                }
            )
    result = {
        "version": VERSION,
        "frozen_sha256": expected_sha256,
        "new_api_calls": 0,
        "original_scores_changed": False,
        "records": records,
        "cohorts": summaries,
        "resources": resources.summary(),
        "runtime_sha256": {
            name: sha(Path(__file__).with_name(name).read_bytes())
            for name in ("p003_wrap_audit.py", "p003_wrap_content.py", "p003_content_alignment.py")
        },
    }
    write_json(output, result)
    return result


def main() -> None:
    """Prepare first, then score an explicitly approved frozen input digest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "score"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.input, args.output)
    elif not args.sha256:
        parser.error("score requires --sha256")
    else:
        audit(args.input, args.sha256, args.output)


if __name__ == "__main__":
    main()
