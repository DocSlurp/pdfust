"""Freeze six rolling-row controls on independently authenticated YOLO/TATR1280 sources."""
# ruff: noqa: EM101, TRY003, PLR2004, C901, PLR0912, E501 - explicit complete authentication.
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

import pylopdf
from bench import p003_rolling_tracks as rolling
from bench import p003_structure_geometry as geometry
from bench import p003_yolo_resolution as detector
from bench import p003_yolo_structure as yolo
from bench.p003_gate_run import authenticate as source_authenticate
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

CODE_FILES = ("p003_rolling_tracks.py", "p003_rolling_tracks_prepare.py", "p003_segment_topology.py",
              "pipeline_assembly.py", "pipeline_repair.py", "p003_gate_run.py", "p003_structure_geometry.py",
              "p003_yolo_structure.py", "p003_yolo_resolution.py", "pipeline_run.py", "generalization_report.py", "silver.py")


def read(path: Path) -> dict:
    """Read only explicit guarded source artifacts."""
    return json.loads(guard_path(path).read_bytes())


def archive(directory: Path, frozen: dict, authority: Path) -> None:
    """Authenticate all original archived bytes, executing none of those archive files."""
    approved = read(authority)
    if set(approved) != set(frozen["code_sha256"]):
        raise ValueError("Complete independent code authority required")
    for name, digest in frozen["code_sha256"].items():
        if Path(name).name != name or approved[name] != digest or sha((directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived code identity differs")
    # These pure original helper functions actually execute in this replay.
    for name in ("p003_structure_geometry.py", "p003_yolo_structure.py", "p003_yolo_resolution.py",
                 "pipeline_assembly.py", "pipeline_repair.py", "silver.py"):
        if name in approved and sha(Path(__file__).with_name(name).read_bytes()) != approved[name]:
            raise ValueError("Executed current geometry helpers differ from independent authority")


def authenticate(directory: Path, structure_trust: Path, detector_trust: Path, source_trust: Path) -> tuple[dict, dict]:
    """Replay source identity, detector ownership, and structure projection without crop-helper execution."""
    manifest = read(directory / "source/manifest.json")
    report = read(directory / "geometry/report.json")
    archive(directory, manifest, structure_trust)
    if report["code_sha256"] != manifest["code_sha256"] or report["source_manifest_sha256"] != sha((directory / "source/manifest.json").read_bytes()):
        raise ValueError("Original structure source identity differs")
    baseline = guard_path(Path(manifest["baseline"]))
    original, _ = source_authenticate(baseline, read(source_trust))
    if original["records"] != manifest["records"] or len(original["records"]) != 16:
        raise ValueError("Exact complete original16 source cohort required")
    yolo_directory = guard_path(Path(manifest["yolo_directory"]))
    yf, yr = read(yolo_directory / "frozen.json"), read(yolo_directory / "report.json")
    archive(yolo_directory, yf, detector_trust)
    if (yf["records"] != original["records"] or manifest["yolo_frozen_sha256"] != sha((yolo_directory / "frozen.json").read_bytes())
            or manifest["yolo_report_sha256"] != sha((yolo_directory / "report.json").read_bytes())
            or manifest["trusted_code_sha256"] != sha(source_trust.read_bytes())
            or manifest["yolo_trusted_code_sha256"] != sha(detector_trust.read_bytes())
            or manifest["references_read"] is not False or report["references_read"] is not False):
        raise ValueError("Original source/detector authority identities differ")
    if [p["id"] for p in manifest["pages"]] != [r["id"] for r in original["records"]] or [p["id"] for p in report["pages"]] != [r["id"] for r in original["records"]] or [p["id"] for p in yr["pages"]] != [r["id"] for r in original["records"]]:
        raise ValueError("Complete ordered source/detector/geometry pages required")
    for page, measured, detected in zip(manifest["pages"], report["pages"], yr["pages"], strict=True):
        source_path = directory / "source" / page["source_path"]
        source = read(source_path)
        baseline_path = baseline / (page["id"] + "-result.json")
        baseline_result = read(baseline_path)
        if sha(source_path.read_bytes()) != page["source_sha256"] or source != baseline_result["source"] or sha(baseline_path.read_bytes()) != page["baseline_result_sha256"]:
            raise ValueError("Original complete source snapshot differs")
        receipt = next(r for r in detected["results"] if r["imgsz"] == 1280)
        raw_path = yolo_directory / receipt["path"]
        raw = read(raw_path)
        if (sha(raw_path.read_bytes()) != receipt["sha256"] or raw["status"] != "completed"
                or raw["boxes"] != detector.project(raw["raw_boxes"], raw["viewport"], raw["image_size"])
                or raw["viewport"] != source["page_size"] or raw["configuration"] != detector.configuration(1280)
                or yolo.ownership(source, raw["boxes"], 1280) != page["ownership_by_size"]["1280"]):
            raise ValueError("Raw detector projection or unique ownership differs")
        if len(page["crops"]) != len(measured["crops"]):
            raise ValueError("Original geometry crop inventory differs")
        for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
            if crop["acquisition_size"] != 1280:
                continue
            path = directory / "geometry" / receipt["path"]
            prediction = read(path)
            if sha(path.read_bytes()) != receipt["sha256"] or prediction["crop"] != crop:
                raise ValueError("Raw structure receipt identity differs")
            for view in prediction["views"]:
                projected = geometry.project(prediction["queries"], crop["bbox"], report["labels"], view["threshold"])
                projected["topology"] = geometry.topology(projected)
                if projected != view:
                    raise ValueError("Original structure projection differs")
    return manifest, report


def prepare(directory: Path, output: Path, *, structure_trust: Path, detector_trust: Path, source_trust: Path) -> dict:
    """Prepare all96 complete page treatments before any external quality scoring."""
    directory, output, structure_trust, detector_trust, source_trust = [guard_path(p) for p in
        (directory, output, structure_trust, detector_trust, source_trust)]
    if output.exists():
        raise FileExistsError("Rolling output must be fresh")
    with Resources() as resources:
        manifest, original_geometry = authenticate(directory, structure_trust, detector_trust, source_trust)
        output.mkdir(parents=True)
        shutil.copytree(directory / "source", output / "source")
        (output / "code").mkdir()
        code = {}
        for name in CODE_FILES:
            data = Path(__file__).with_name(name).read_bytes()
            (output / "code" / name).write_bytes(data)
            code[name] = sha(data)
        frozen = {"schema": 1, "processor": "p003_rolling_tracks", "records": manifest["records"],
                  "code_sha256": code, "input_directory": str(directory.resolve()), "policy": rolling.POLICY,
                  "source_manifest_sha256": sha((directory / "source/manifest.json").read_bytes()),
                  "geometry_report_sha256": sha((directory / "geometry/report.json").read_bytes()),
                  "independent_authorities": {name: {"path": str(path.resolve()), "sha256": sha(path.read_bytes())}
                                             for name, path in (("structure", structure_trust), ("detector", detector_trust), ("source", source_trust))},
                  "source_conserved": True, "references_read": False, "new_api_calls": 0,
                  "sizes": [1280], "profiles": [list(p) for p in rolling.PROFILES], "output_sha256": {}}
        rows = []
        for page, measured in zip(manifest["pages"], original_geometry["pages"], strict=True):
            source = read(directory / "source" / page["source_path"])
            record = page["record"]
            pdf = guard_path(Path(record["pdf_path"])).read_bytes()
            if sha(pdf) != record["pdf_sha256"]:
                raise ValueError("Original PDF identity differs")
            with pylopdf.open(stream=pdf) as document:
                p = document[record["page_number"]]
                if list(p.rect) != source["page_size"] or p.rotation != page["original_rotation"] or p.rotation != page["effective_rotation"]:
                    raise ValueError("Original drawing/display coordinate identity differs")
                drawings = p.get_drawings()
            write_json(output / "source" / (page["id"] + "-drawings.json"), drawings)
            frozen["output_sha256"]["source/" + page["id"] + "-drawings.json"] = sha((output / "source" / (page["id"] + "-drawings.json")).read_bytes())
            rules = rolling.horizontal_rules(drawings)
            topologies = {}
            for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
                if crop["acquisition_size"] == 1280:
                    prediction = read(directory / "geometry" / receipt["path"])
                    topologies[crop["region_id"]] = next(v["topology"] for v in prediction["views"] if v["threshold"] == 0.5)
            for ratio, key_count in rolling.PROFILES:
                result = rolling.compose(source, page["ownership_by_size"]["1280"]["proposals"], topologies, rules, ratio, key_count)
                name = f"{page['id']}-ratio-{ratio}-keys-{key_count}.json"
                payload = {"id": page["id"], "size": 1280, "ratio": ratio, "key_columns": key_count,
                           "source": source, "horizontal_rules": rules, **result}
                write_json(output / name, payload)
                digest = sha((output / name).read_bytes())
                frozen["output_sha256"][name] = digest
                rows.append({"id": page["id"], "size": 1280, "ratio": ratio, "key_columns": key_count,
                             "path": name, "sha256": digest, "table_count": len(result["state"]["tables"]),
                             "joined_line_count": sum(r.get("joined_line_count", 0) for r in result["regions"] if r["effective_page_accepted"]),
                             "assigned_word_count": result["assigned_word_count"],
                             "unresolved_word_count": result["unresolved_word_count"], "page_refusal": result["page_refusal"]})
        write_json(output / "frozen.json", frozen)
    report = {"processor": "p003_rolling_tracks", "rows": rows, "resources": resources.summary(),
              "frozen_sha256": sha((output / "frozen.json").read_bytes()), "intended_page_count": 16,
              "page_treatment_count": 96, "references_read": False, "new_api_calls": 0, "source_conserved": True,
              "thread_environment": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
              "scope": "CPU source authentication, new source drawings, six offline row hypotheses; original inference excluded"}
    write_json(output / "report.json", report)
    write_json(output / "resources.json", resources.samples)
    return report


def main() -> None:
    """Explicit independent authorities required; no GPU/model execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("geometry", "structure-trusted-code", "detector-trusted-code", "source-trusted-code", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.geometry, args.output, structure_trust=args.structure_trusted_code,
                     detector_trust=args.detector_trusted_code, source_trust=args.source_trusted_code)
    print(json.dumps({"page_treatments": len(report["rows"]), "resources": report["resources"]}))


if __name__ == "__main__":
    main()
