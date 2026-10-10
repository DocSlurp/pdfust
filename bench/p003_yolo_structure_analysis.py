"""Independent complete-cohort replay and DEV scoring of YOLO/TATR source-owned placements."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415
from __future__ import annotations

import json
import math
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from bench.generalization_report import load_corpus
from bench.p003_report import strict_scores
from bench.p003_structure_acquisition_verification import source_helper_matches
from bench.p003_yolo_resolution_analysis import verify as verify_yolo
from bench.silver import guard_path, sha

SOURCE_SHA = "78f29990652232e7288ce3f895afbe5ef279385d5fdc7ee0b95feb76c255dd6a"
GEOMETRY_SHA = "9c6419b7549cbd133aae03ef536be8a80f41414cb310b705a157827140c032ec"
PLACEMENT_SHA = "6011fb0ca7540e66f82f7030c8540661b5e3ce67d692543ae86c2623c017f71a"
QUERIES = 125
CLASSES = 7
PAGES = 16
CPU_THREADS = 2


def read(path: Path) -> Any:  # noqa: ANN401
    """Read an explicitly named guarded artifact."""
    return json.loads(guard_path(path).read_bytes())


def validate_logits(prediction: dict[str, Any]) -> None:
    """Bind retained probabilities to complete finite raw logits; tolerate float32 softmax rounding."""
    if len(prediction["raw_logits"]) != QUERIES or len(prediction["queries"]) != QUERIES:
        raise ValueError("Incomplete structure raw query inventory")
    for logits, query in zip(prediction["raw_logits"], prediction["queries"], strict=True):
        if len(logits) != CLASSES or any(type(v) not in (int, float) or not math.isfinite(v) for v in logits):
            raise ValueError("Invalid structure raw logits")
        exps = [math.exp(v - max(logits)) for v in logits]
        expected = [v / sum(exps) for v in exps]
        actual = query["probabilities"]
        if (
            len(actual) != CLASSES
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in actual)
            or any(not math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-7) for a, b in zip(actual, expected, strict=True))
        ):
            raise ValueError("Structure probabilities differ from retained raw logits")


def verify(
    directory: Path,
    *,
    trusted_code: dict[str, str],
    source_trusted_code: dict[str, str],
    yolo_trusted_code: dict[str, str],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Rebuild complete source/pixels/ownership and all432 placements before opening scoring references."""
    from bench import p003_structure_geometry as geometry
    from bench import p003_structure_place as placement
    from bench import p003_yolo_structure as proposal

    directory = guard_path(directory)
    manifest = read(directory / "source/manifest.json")
    report = read(directory / "geometry/report.json")
    placed_report = read(directory / "placement/report.json")
    for path, expected in (
        ("source/manifest.json", SOURCE_SHA),
        ("geometry/report.json", GEOMETRY_SHA),
        ("placement/report.json", PLACEMENT_SHA),
    ):
        if sha((directory / path).read_bytes()) != expected:
            raise ValueError("Announced source-only structure freeze changed")
    if (
        set(trusted_code) != set(proposal.CODE_FILES)
        or manifest["code_sha256"] != trusted_code
        or report["code_sha256"] != trusted_code
        or placed_report["code_sha256"] != trusted_code
    ):
        raise ValueError("Structure acquisition code differs from independent authority")
    reviews = []
    for name, digest in trusted_code.items():
        archived = (directory / "code" / name).read_bytes()
        current = Path(__file__).with_name(name).read_bytes()
        if sha(archived) != digest or not source_helper_matches(name, archived, current):
            raise ValueError("Structure helper differs from authenticated archive/reviewed current functions")
        if archived != current:
            reviews.append(
                {
                    "name": name,
                    "sha256": digest,
                    "scope": "Root-reviewed unused transcription/process differences; "
                    "used functions/constants AST unchanged",
                }
            )
    if (
        read(Path(manifest["independent_trusted_code"])) != source_trusted_code
        or read(Path(manifest["yolo_external_trusted_code"])) != yolo_trusted_code
    ):
        raise ValueError("Recorded source/YOLO authority differs from independent maps")
    verify_yolo(Path(manifest["yolo_directory"]), yolo_trusted_code, source_trusted_code)
    with tempfile.TemporaryDirectory(prefix="p003-yolo-structure-replay-", dir=directory.parent) as temp:
        rebuilt = Path(temp) / "source-replay"
        actual = proposal.prepare(
            Path(manifest["yolo_directory"]),
            Path(manifest["yolo_external_trusted_code"]),
            Path(manifest["baseline"]),
            Path(manifest["independent_trusted_code"]),
            Path(manifest["model_directory"]),
            rebuilt,
        )
        ignored = {"resources", "code_sha256"}
        if {k: v for k, v in actual.items() if k not in ignored} != {
            k: v for k, v in manifest.items() if k not in ignored
        }:
            raise ValueError("Complete source/ownership/model/crop manifest differs from replay")
        for page in manifest["pages"]:
            for name in [page["source_path"], *(c["image_path"] for c in page["crops"])]:
                if (rebuilt / "source" / name).read_bytes() != (directory / "source" / name).read_bytes():
                    raise ValueError("Original full source or crop JPEG pixels changed")
    if (
        report["source_manifest_sha256"] != SOURCE_SHA
        or placed_report["source_manifest_sha256"] != SOURCE_SHA
        or placed_report["geometry_report_sha256"] != GEOMETRY_SHA
        or report["model"] != manifest["model"]
    ):
        raise ValueError("Structure/placement provenance differs from source freeze")
    if (
        report["device"] != "cpu"
        or report["cpu_threads"] != CPU_THREADS
        or report["interop_threads"] != 1
        or report["local_gpu_used"] is not False
        or report["references_read"] is not False
        or report["source_text_model_input"] is not False
        or report["new_api_calls"] != 0
        or report["thresholds"] != list(geometry.THRESHOLDS)
        or report["acquisition_sizes"] != manifest["acquisition_sizes"]
        or report["checkpoint_processor_size"] != {"longest_edge": 800}
        or report["effective_processor_size"] != {"shortest_edge": 800, "longest_edge": 800}
    ):
        raise ValueError("Structure CPU/model-input/threshold contract differs")
    model_config = read(Path(manifest["model_directory"]) / "config.json")
    if report["labels"] != [model_config["id2label"][str(i)] for i in range(CLASSES - 1)]:
        raise ValueError("Structure class labels differ from pinned model configuration")
    ids = [r["id"] for r in manifest["records"]]
    if (
        len(ids) != PAGES
        or len(set(ids)) != PAGES
        or [p["id"] for p in manifest["pages"]] != ids
        or [p["id"] for p in report["pages"]] != ids
    ):
        raise ValueError("Structure complete natural16 inventory differs")
    rows = {(r["id"], r["acquisition_size"], r["threshold"], r["policy"]): r for r in placed_report["rows"]}
    expected_keys = {
        (i, s, t, p)
        for i in ids
        for s in manifest["acquisition_sizes"]
        for t in geometry.THRESHOLDS
        for p in placement.POLICIES
    }
    if len(rows) != len(placed_report["rows"]) or set(rows) != expected_keys:
        raise ValueError("Incomplete/duplicated predeclared structure placement inventory")
    treatments = defaultdict(list)
    crop_metrics = []
    for page, measured in zip(manifest["pages"], report["pages"], strict=True):
        source = read(directory / "source" / page["source_path"])
        if len(page["crops"]) != len(measured["crops"]):
            raise ValueError("Incomplete structure crop inventory")
        pools = {(s, t): [] for s in manifest["acquisition_sizes"] for t in geometry.THRESHOLDS}
        for crop, receipt in zip(page["crops"], measured["crops"], strict=True):
            path = directory / "geometry" / receipt["path"]
            prediction = read(path)
            if (
                sha(path.read_bytes()) != receipt["sha256"]
                or prediction["crop"] != crop
                or prediction["status"] != "completed"
                or receipt["status"] != "completed"
                or prediction["no_retry"] is not True
                or prediction["metrics"] != receipt["metrics"]
                or receipt["acquisition_size"] != crop["acquisition_size"]
            ):
                raise ValueError("Structure raw model output/crop/error receipt differs")
            validate_logits(prediction)
            if len(prediction["views"]) != len(geometry.THRESHOLDS):
                raise ValueError("Structure threshold view missing")
            for threshold, view in zip(geometry.THRESHOLDS, prediction["views"], strict=True):
                expected = geometry.project(prediction["queries"], crop["bbox"], report["labels"], threshold)
                expected["topology"] = geometry.topology(expected)
                if view != expected:
                    raise ValueError("Structure projection/topology differs from raw queries")
                pools[(crop["acquisition_size"], threshold)].append(
                    {"region_id": crop["region_id"], "source_ids": crop["source_ids"], "topology": view["topology"]}
                )
            crop_metrics.append({"size": crop["acquisition_size"], **prediction["metrics"]})
        for (size, threshold), candidates in pools.items():
            for policy in placement.POLICIES:
                row = rows[(page["id"], size, threshold, policy)]
                path = directory / "placement" / row["path"]
                value = read(path)
                replay = {
                    "id": page["id"],
                    "source": source,
                    "acquisition_size": size,
                    "threshold": threshold,
                    **placement.place(source, candidates, policy),
                    "inference_errors": [],
                    "complete_intended_page": True,
                    "prediction_provenance": "literal source IDs only; no generated cell strings",
                }
                if (
                    sha(path.read_bytes()) != row["sha256"]
                    or value != replay
                    or row["tables"] != len(value["state"]["tables"])
                    or row["unresolved_words"] != len(value["state"]["unresolved_ids"])
                    or row["conflict_count"] != len(value["conflicting_table_indices"])
                    or row["inference_error_count"] != 0
                ):
                    raise ValueError("Complete source-owned placement differs from deterministic replay")
                treatments[f"s{size}-t{threshold}-{policy}"].append(
                    {"id": page["id"], "status": "ok", "tables": value["state"]["tables"]}
                )
    if report["intended_crops"] != len(crop_metrics):
        raise ValueError("Structure inference count differs")
    return {
        "source_reviews": reviews,
        "source_manifest_sha256": SOURCE_SHA,
        "geometry_report_sha256": GEOMETRY_SHA,
        "placement_report_sha256": PLACEMENT_SHA,
        "preparation_resources": manifest["resources"],
        "placement_resources": placed_report["resources"],
        "initialization_resources": report["initialization"],
        "crop_metrics": crop_metrics,
    }, dict(treatments)


def analyze(directory: Path, corpus: Path, **authorities: dict[str, str]) -> dict[str, Any]:
    """Score all27 fixed full cohorts only after source-only replay; never choose a per-page winner."""
    verified, treatments = verify(directory, **authorities)
    manifest, targets = load_corpus(guard_path(corpus))
    ids = {p["id"] for p in manifest["pages"]}
    if any({p["id"] for p in rows} != ids for rows in treatments.values()):
        raise ValueError("DEV scoring corpus differs from exact complete intended cohort")
    return {
        **verified,
        "scope": "Matched YOLO acquisition→CPU structure→literal source placement; all27 frozen treatments",
        "new_api_calls": 0,
        "generated_fallback_tables": 0,
        "treatments": {n: strict_scores(targets["pages"], rows) for n, rows in treatments.items()},
    }
