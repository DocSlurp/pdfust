"""Independent full-cohort audit of source-only rolling-row controls."""

# ruff: noqa: ANN401, EM101, TRY003, PLC0415, PLR0913, C901, PLR0912
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from bench.generalization_report import load_corpus
from bench.p003_report import strict_scores
from bench.silver import guard_path, sha

SIZE = 1280
THRESHOLD = 0.5
FROZEN_SHA = "8dc277c7efa3c17b7d25b98234e5bbf8058b6de10ee9b87bff13a0eaf79d91f4"


def read(path: Path) -> Any:
    """Read an explicitly guarded artifact."""
    return json.loads(guard_path(path).read_bytes())


def inventory(rows: list[dict[str, Any]], ids: set[str], profiles: list[list[float]]) -> None:
    """Retain all six fixed controls and every intended page, including refusals."""
    actual = [(r["id"], r["ratio"], r["key_columns"]) for r in rows]
    expected = {(ident, ratio, keys) for ident in ids for ratio, keys in profiles}
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError("Rolling control page/treatment inventory differs")


def analyze(directory: Path, corpus: Path, *, rolling_trusted_code: dict[str, str],
            trusted_code: dict[str, str], source_trusted_code: dict[str, str],
            yolo_trusted_code: dict[str, str]) -> dict[str, Any]:
    """Rebuild source drawings, row hypotheses and complete states before references."""
    import pdfust
    from bench import p003_rolling_tracks as rolling
    from bench import p003_rolling_tracks_prepare as prepare
    from bench.p003_yolo_structure_analysis import verify

    directory = guard_path(directory)
    frozen, report = read(directory / "frozen.json"), read(directory / "report.json")
    if sha((directory / "frozen.json").read_bytes()) != FROZEN_SHA or report["frozen_sha256"] != FROZEN_SHA:
        raise ValueError("Announced rolling source-only freeze changed")
    if set(rolling_trusted_code) != set(prepare.CODE_FILES) or frozen["code_sha256"] != rolling_trusted_code:
        raise ValueError("Rolling code differs from independent authority")
    for name, digest in rolling_trusted_code.items():
        if (sha((directory / "code" / name).read_bytes()) != digest
                or sha(Path(rolling.__file__).with_name(name).read_bytes()) != digest):
            raise ValueError("Archived or executed rolling helper differs")
    input_directory = guard_path(Path(frozen["input_directory"]))
    verified, _ = verify(input_directory, trusted_code=trusted_code, source_trusted_code=source_trusted_code,
                         yolo_trusted_code=yolo_trusted_code)
    manifest, geometry = read(input_directory / "source/manifest.json"), read(input_directory / "geometry/report.json")
    maps = {"structure": trusted_code, "detector": yolo_trusted_code, "source": source_trusted_code}
    for name, authority in frozen["independent_authorities"].items():
        path = guard_path(Path(authority["path"]))
        if sha(path.read_bytes()) != authority["sha256"] or read(path) != maps[name]:
            raise ValueError("Original independent source authority differs")
    if (set(frozen["independent_authorities"]) != set(maps) or frozen["records"] != manifest["records"]
            or frozen["policy"] != json.loads(json.dumps(rolling.POLICY))
            or frozen["profiles"] != [list(p) for p in rolling.PROFILES]
            or frozen["sizes"] != [SIZE]
            or frozen["source_manifest_sha256"] != sha((input_directory / "source/manifest.json").read_bytes())
            or frozen["geometry_report_sha256"] != sha((input_directory / "geometry/report.json").read_bytes())
            or frozen["references_read"] is not False or report["references_read"] is not False
            or frozen["new_api_calls"] != 0 or report["new_api_calls"] != 0
            or frozen["source_conserved"] is not True or report["source_conserved"] is not True):
        raise ValueError("Rolling source/treatment identity differs")
    for name, digest in frozen["output_sha256"].items():
        p = Path(name)
        if p.is_absolute() or ".." in p.parts or sha(guard_path(directory / p).read_bytes()) != digest:
            raise ValueError("Frozen rolling output bytes differ")
    ids = {p["id"] for p in manifest["pages"]}
    inventory(report["rows"], ids, frozen["profiles"])
    rows = {(r["id"], r["ratio"], r["key_columns"]): r for r in report["rows"]}
    treatments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    refusals = defaultdict(int)
    for page, measured in zip(manifest["pages"], geometry["pages"], strict=True):
        source = read(input_directory / "source" / page["source_path"])
        if read(directory / "source" / page["source_path"]) != source:
            raise ValueError("Copied rolling source differs")
        record = page["record"]
        pdf = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(pdf) != record["pdf_sha256"]:
            raise ValueError("Rolling source PDF differs")
        with pdfust.open(stream=pdf) as document:
            p = document[record["page_number"]]
            if list(p.rect) != source["page_size"] or p.rotation != page["original_rotation"]:
                raise ValueError("Rolling drawing coordinates differ")
            drawings = p.get_drawings()
        if read(directory / "source" / f"{page['id']}-drawings.json") != drawings:
            raise ValueError("Rolling source vector rules differ")
        rules = rolling.horizontal_rules(drawings)
        topologies = {}
        for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
            if crop["acquisition_size"] == SIZE:
                prediction = read(input_directory / "geometry" / receipt["path"])
                topologies[crop["region_id"]] = next(
                    v["topology"] for v in prediction["views"] if v["threshold"] == THRESHOLD
                )
        for ratio, keys in rolling.PROFILES:
            value = rolling.compose(
                source, page["ownership_by_size"][str(SIZE)]["proposals"], topologies, rules, ratio, keys
            )
            payload = {"id": page["id"], "size": SIZE, "ratio": ratio, "key_columns": keys,
                       "source": source, "horizontal_rules": rules, **value}
            row = rows[(page["id"], ratio, keys)]
            path = f"{page['id']}-ratio-{ratio}-keys-{keys}.json"
            if (row["path"] != path or read(directory / path) != payload
                    or row["sha256"] != frozen["output_sha256"][path]
                    or row["table_count"] != len(value["state"]["tables"])
                    or row["assigned_word_count"] != value["assigned_word_count"]
                    or row["unresolved_word_count"] != value["unresolved_word_count"]
                    or row["page_refusal"] != value["page_refusal"]
                    or row["joined_line_count"] != sum(r.get("joined_line_count", 0) for r in value["regions"]
                                                        if r["effective_page_accepted"])):
                raise ValueError("Rolling complete composition or refusal differs")
            key = f"gap{ratio}-keys{keys}"
            refusals[key] += bool(value["page_refusal"])
            treatments[key].append({"id": page["id"], "status": "ok", "tables": value["state"]["tables"]})
    if report["intended_page_count"] != len(ids) or report["page_treatment_count"] != len(rows):
        raise ValueError("Rolling complete denominator differs")
    corpus_manifest, targets = load_corpus(guard_path(corpus))
    if {p["id"] for p in corpus_manifest["pages"]} != ids:
        raise ValueError("Rolling DEV scoring corpus differs")
    return {"frozen_sha256": FROZEN_SHA, "report_sha256": sha((directory / "report.json").read_bytes()),
            "source_verification": verified, "resources": report["resources"], "page_refusals": dict(refusals),
            "scope": "Six source-only rolling controls; no model or historical fallback credit",
            "new_api_calls": 0, "treatments": {k: strict_scores(targets["pages"], v) for k, v in treatments.items()}}
