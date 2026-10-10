"""Authenticate frozen YOLO regions and freeze every regional track control before scoring."""

# ruff: noqa: ANN401, EM101, TRY003, C901, PLR0912, PLR2004, E501
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from bench import p003_regional_tracks as regional
from bench import p003_structure_geometry as geometry
from bench import p003_yolo_structure as yolo
from bench.pipeline_run import Resources
from bench.silver import guard_path, sha, write_json

CODE_FILES = (*yolo.CODE_FILES, "p003_regional_tracks.py", "p003_regional_tracks_prepare.py",
              "p003_fullsource_tracks.py", "p003_segment_topology.py", "p003_gate_run.py",
              "generalization_report.py", "pipeline_run.py")


def read(path: Path) -> Any:
    """Read only an explicitly selected guarded artifact."""
    return json.loads(guard_path(path).read_bytes())


def authenticate(directory: Path, structure_trust: Path, detector_trust: Path,
                 source_trust: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Replay complete original source preparation using authenticated current pure code."""
    manifest = read(directory / "source/manifest.json")
    report = read(directory / "geometry/report.json")
    approved = read(structure_trust)
    if set(approved) != set(manifest["code_sha256"]) or manifest["code_sha256"] != report["code_sha256"]:
        raise ValueError("Complete independent geometry/source code authority required")
    for name, digest in manifest["code_sha256"].items():
        if (Path(name).name != name or approved.get(name) != digest
                or sha((directory / "code" / name).read_bytes()) != digest
                or sha(Path(__file__).with_name(name).read_bytes()) != digest):
            raise ValueError("Frozen/current regional input helpers differ from independent Git authority")
    if (manifest["references_read"] is not False or manifest["inference_calls"] != 0
            or report["references_read"] is not False or report["new_api_calls"] != 0
            or report["source_manifest_sha256"] != sha((directory / "source/manifest.json").read_bytes())
            or len(manifest["records"]) != 16 or manifest["acquisition_sizes"] != [640, 1024, 1280]
            or sha(source_trust.read_bytes()) != manifest["trusted_code_sha256"]
            or sha(detector_trust.read_bytes()) != manifest["yolo_trusted_code_sha256"]):
        raise ValueError("Complete source-only cohort/authority identities required")
    with tempfile.TemporaryDirectory(prefix="p003-regional-auth-", dir=directory.parent) as temporary:
        rebuilt = Path(temporary) / "rebuilt"
        replay = yolo.prepare(guard_path(Path(manifest["yolo_directory"])), detector_trust,
                              guard_path(Path(manifest["baseline"])), source_trust,
                              guard_path(Path(manifest["model_directory"])), rebuilt)
        if {k: v for k, v in replay.items() if k != "resources"} != {
            k: v for k, v in manifest.items() if k != "resources"
        }:
            raise ValueError("Replayed whole-source ownership/crop identities differ")
        for page in manifest["pages"]:
            for name in [page["source_path"], *[crop["image_path"] for crop in page["crops"]]]:
                if (rebuilt / "source" / name).read_bytes() != (directory / "source" / name).read_bytes():
                    raise ValueError("Replayed complete source or original region pixels differ")
    if [p["id"] for p in manifest["pages"]] != [p["id"] for p in report["pages"]]:
        raise ValueError("Geometry page inventory differs")
    for page, measured in zip(manifest["pages"], report["pages"], strict=True):
        if len(page["crops"]) != len(measured["crops"]):
            raise ValueError("Geometry region inventory differs")
        for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
            raw = (directory / "geometry" / receipt["path"]).read_bytes()
            prediction = json.loads(raw)
            if sha(raw) != receipt["sha256"] or prediction["crop"] != crop:
                raise ValueError("Raw structure receipt changed")
            for view in prediction["views"]:
                projected = geometry.project(prediction["queries"], crop["bbox"], report["labels"], view["threshold"])
                projected["topology"] = geometry.topology(projected)
                if view != projected:
                    raise ValueError("Frozen structure projection differs")
    return manifest, report


def prepare(directory: Path, output: Path, *, structure_trust: Path,
            detector_trust: Path, source_trust: Path) -> dict[str, Any]:
    """Create all 27 gutter and nine TATR-column treatments with complete output inventories."""
    directory, output, structure_trust, detector_trust, source_trust = [guard_path(p) for p in
        (directory, output, structure_trust, detector_trust, source_trust)]
    if output.exists():
        raise FileExistsError("Regional output must be fresh")
    with Resources() as resources:
        manifest, geometry_report = authenticate(directory, structure_trust, detector_trust, source_trust)
        output.mkdir(parents=True)
        shutil.copytree(directory / "source", output / "source")
        (output / "code").mkdir()
        code = {}
        for name in dict.fromkeys(CODE_FILES):
            raw = Path(__file__).with_name(name).read_bytes()
            (output / "code" / name).write_bytes(raw)
            code[name] = sha(raw)
        frozen = {"schema": 1, "processor": "p003_regional_tracks", "records": manifest["records"],
                  "code_sha256": code, "input_directory": str(directory.resolve()),
                  "source_manifest_sha256": sha((directory / "source/manifest.json").read_bytes()),
                  "geometry_report_sha256": sha((directory / "geometry/report.json").read_bytes()),
                  "independent_authorities": {name: {"path": str(path.resolve()), "sha256": sha(path.read_bytes())}
                      for name, path in (("structure", structure_trust), ("detector", detector_trust), ("source", source_trust))},
                  "sizes": [640, 1024, 1280], "profiles": [list(p) for p in regional.PROFILES],
                  "hybrid_thresholds": list(regional.HYBRID_THRESHOLDS), "references_read": False,
                  "new_api_calls": 0, "source_conserved": True, "local_gpu_used": False,
                  "fresh_confirmation_accessed": False,
                  "policy": "All regional profiles frozen before scoring; no wrap/merged-span inference; no source text edits"}
        write_json(output / "frozen.json", frozen)
        rows = []
        for page, measured in zip(manifest["pages"], geometry_report["pages"], strict=True):
            source = read(directory / "source" / page["source_path"])
            topologies = {}
            for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
                prediction = read(directory / "geometry" / receipt["path"])
                topologies[crop["region_id"]] = {view["threshold"]: view["topology"] for view in prediction["views"]}
            for size in frozen["sizes"]:
                regions = page["ownership_by_size"][str(size)]["proposals"]
                treatments = [(f"gap-{gap}-support-{support}", gap, support, None)
                              for gap, support in regional.PROFILES]
                treatments += [(f"tatr-columns-{threshold}-physical-rows", 0.5, 0.1,
                                {region["region_id"]: topologies[region["region_id"]][threshold] for region in regions})
                               for threshold in regional.HYBRID_THRESHOLDS]
                for treatment, gap, support, topology in treatments:
                    result = regional.compose(source, regions, gap, support, topology)
                    name = f"{page['id']}-s{size}-{treatment}"
                    payload = {"id": page["id"], "size": size, "treatment": treatment, "source": source, **result}
                    write_json(output / (name + ".json"), payload)
                    rows.append({"id": page["id"], "size": size, "treatment": treatment, "path": name + ".json",
                                 "sha256": sha((output / (name + ".json")).read_bytes()),
                                 "table_count": len(result["state"]["tables"]),
                                 "page_refusal": result["page_refusal"],
                                 "region_status_counts": {status: sum(r["status"] == status for r in result["regions"])
                                                         for status in ("decoded", "refused")},
                                 "source_word_count": result["source_word_count"],
                                 "assigned_word_count": result["assigned_word_count"],
                                 "unresolved_word_count": result["unresolved_word_count"]})
        frozen["output_sha256"] = {row["path"]: row["sha256"] for row in rows}
        write_json(output / "frozen.json", frozen)
    report = {"processor": frozen["processor"], "rows": rows, "resources": resources.summary(),
              "frozen_sha256": sha((output / "frozen.json").read_bytes()),
              "intended_page_count": 16, "page_treatment_count": len(rows),
              "references_read": False, "new_api_calls": 0, "source_conserved": True,
              "thread_environment": {name: os.environ.get(name) for name in
                                     ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
              "scope": "Offline authenticated source/region replay and all regional track controls; original inference excluded"}
    write_json(output / "report.json", report)
    write_json(output / "resources.json", resources.samples)
    return report


def main() -> None:
    """Root supplies independently reviewed input authorities; no model execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("geometry", "structure-trusted-code", "detector-trusted-code", "source-trusted-code", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.geometry, args.output, structure_trust=args.structure_trusted_code,
                     detector_trust=args.detector_trusted_code, source_trust=args.source_trusted_code)
    print(json.dumps({"page_treatments": len(result["rows"]), "resources": result["resources"]}))


if __name__ == "__main__":
    main()
