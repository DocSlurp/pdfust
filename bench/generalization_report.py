"""Verify and report complete P002 natural-PDF runs offline."""

# Retained experiment schemas have heterogeneous dictionaries.
# ruff: noqa: C901, PLR0912, EM101, TRY003, PLC0415
from __future__ import annotations

import argparse
import ast
import importlib
import json
import math
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from bench import pipeline_hybrid_composition as hybrid
from bench import pipeline_native_orientation as orientation
from bench.generalization_run import sanitize_vectors
from bench.generalization_scoring import audit_model_body, normalize_text, score_dataset, score_page
from bench.generalization_vision_multiscale import RULES as MULTISCALE_RULES
from bench.generalization_vision_multiscale import replay as multiscale_replay
from bench.generalization_vision_regions import compose as vision_regions_compose
from bench.generalization_vision_regions import proposals as vision_region_proposals
from bench.generalization_vision_regions import transcription_parse, transcription_request
from bench.pipeline_layout_detector import _box
from bench.pipeline_regions import compose, validate_composed
from bench.pipeline_report import _render_markdown, _verify_markdown_renderer
from bench.pipeline_scoring import score_dataset as authored_score_dataset
from bench.pipeline_source_order import render_source
from bench.pipeline_vision_transcription import markdown as vision_markdown
from bench.pipeline_vision_transcription import parse as vision_parse
from bench.silver import canonical, guard_path, sha

LOCALIZATION_IOU = 0.5
NATURAL_SCREEN_PAGES = 16
CONCURRENT_VISION_WORKERS = 4
HYBRID_LEGACY_RENDERER_SHA256 = "6e1edda5cd94b675611e30cef8c228f87968c3b9ffdf8f9b7b135d544e18ae68"
HYBRID_PHYSICAL_RUNNER_SHA256 = "7d15c3032bd1d532c5ee590ad121861c3d0fe3519422cb12cb8b4892bc9f04de"

SOURCE_FIELDS = ("id", "pdf_path", "pdf_sha256", "page_number")


# Reviewed repository sources, never digests supplied by an artifact.
# Runner 7395782 retains local region states and uses the verified baseline
# renderer, source-order sorting and a single newline between region renderings.
TRUSTED_HISTORICAL_CODE = {
    "generalization_run.py": {
        "fa51763aa571aedd12f3b625174e80b2fc57f4485b0898bb2d1bef225f8a8449": "3745e7e reviewed pre-image/rubric runner",
        "944e10e8670b57b4f4067e4abc54015d45ded6198eb757f75c5d9875ac4f10b7": "42bf028",
        "a4ff7678b279a875935ce5f989eb81f92544873bab4974f510c343c70aab4964": "69f2d81",
        "baae56a9e99eb624502b1238a51a25f4751bd755752ad7499ae5187d98dfca2a": "1185a06",
        "8c51ca5295c8c9e27cf4cad0f5a7e957c36be94c1739ac616d2aa1cd9f7dd865": "1083b53",
        "b65ce79aef238bceed439bca6998dd003130bb190b4b2c85feb1eaf67eb04456": "0cc3b3f",
        "4c02938d7abea98dbc070944aa0b962f85ef5069e2b07c9f801a80c308b40b80": "01273f1",
        "4a88118faa12c6dfd92ce692daf04e215c3ff848335f66ddd57b073ffda87d0b": "ac1f842",
        "e9cfae5504773e6ee5e2e0265fcaa447ce4786e2bc015ead37c548593419180f": "119a9ca",
        "a5bc281951becd59633a78d00bdeae125405789e09b3368617ff85ecbd191b26": "7395782",
        "3945a5efaace0c02d80866460e32f67d7f2acb1c9c35500376a32edf0f151f38": "6afe326",
        "a6127f74c8054db3ec9483a6e46d70a9dd18eb0f3b892941cc47dbbf5f1deaad": "efaddcc",
        "10639663e5dc17bd5628baba232fbc5321209d7132a6f66f6deab33742a41a5d": "082ea9a",
        "8a87e312643ffc97e63448b8ef9c7b2fbaa169c28431eb177417c34f64ab5386": "b0775e2",
    },
    "generalization_vision_run.py": {
        "a3543f1f8bb0b40032c93defe7f54925ece2449fff45cdbaaef910a707683516": "5424ee7",
        "4b049ab18bf32cc05a1be620a7a68962fdc36600f7fffd9e22ffe10d803d7a87": "3abf651",
        "365ec686584641896364a9daf1ad8f83e9e06a5fb8ac38a3b651f5c85dec9c91": "fc49724",
        "5d39813c50ece7844659081af76ee87c34e75d7c6a6bd3b949e900865755b106": "4bf4dc6",
        "132239db5e40a247e0044b2c0df7fc1d7208725bf092e5beb6f04919ff314896": "53aa05b",
        "7308db108bd043d6542c1dc7e767c9247ce6553bf50efb46c4172ced657f45a9": "30aa87b",
        "6043f2e9590d8caeb0262223b6fd0a48a737b75685c11b0f346cd9ec140f4ac4": "01273f1",
    },
    "generalization_vision_regions.py": {
        "7ebafcad7872e73ad08a8e7acf789b582556c3d52f87732f31e291f9f929405f": "4de6318 reviewed legacy crop composition",
        "a47235e0aad3c1789d460c924f273865cb911fb75fec4fb36a0f5eb39ad5d802": "3abf651",
        "a4dbfc283488edd60ee3877e5acb74de1e9263626d567ef5d73a719810339325": "fc49724",
        "d6a481f585c8baf09eca6d724b1f0311c1a02ce8c1fe9e3371dd16a99ea4154a": "be05820",
    },
    "pipeline_hybrid_composition.py": {
        HYBRID_LEGACY_RENDERER_SHA256: "c821fa3",
    },
    "pipeline_regions.py": {
        "66c6ec07d91753ec9a8885124e18a3d0a64f929be5f29682e1050ea826894d2a": "83bd9a6",
        "f31b4e3b8579fb4676512104db7f5d6c8d81e36e3e6319272f1ea14aad82b494": "35cb3f2",
    },
}
REGION_VALIDATION_FUNCTIONS = {"_box", "_characters", "_source", "compose", "validate_composed"}
REGION_VALIDATION_CONSTANTS = {"MAX_PAGE_WORDS", "MAX_PAGE_CHARACTERS", "MAX_REGIONS"}


VISION_REGION_FUNCTIONS = {"_contained", "proposals", "compose"}
VISION_REGION_CONSTANTS = {"MAX_REGIONS", "MAX_PAGE_SLOTS", "DETECTOR_CONFIDENCE"}


def _vision_region_validation_ast(source: bytes) -> str:
    """Fingerprint strict crop selection/composition independently of image controls."""
    selected: list[ast.stmt] = []
    found = set()
    tree = ast.parse(source)
    if any(isinstance(n, ast.FunctionDef) and n.name == "_compose_legacy" for n in tree.body):
        tree.body = [n for n in tree.body if not (isinstance(n, ast.FunctionDef) and n.name == "compose")]
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "_compose_legacy":
                node.name = "compose"
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in VISION_REGION_FUNCTIONS:
            selected.append(node)
            found.add(node.name)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in VISION_REGION_CONSTANTS for target in node.targets
        ):
            selected.append(node)
            found.update(target.id for target in node.targets if isinstance(target, ast.Name))
    if not found >= VISION_REGION_FUNCTIONS | VISION_REGION_CONSTANTS:
        raise ValueError("Vision region archive lacks strict composition dependencies")
    return ast.dump(ast.Module(body=selected, type_ignores=[]), include_attributes=False)


def _region_validation_ast(source: bytes) -> str:
    """Fingerprint only trusted composition validators and their local limits."""
    module = ast.parse(source)
    selected: list[ast.stmt] = []
    names = set()
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name in REGION_VALIDATION_FUNCTIONS:
            selected.append(node)
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            assigned = {target.id for target in node.targets if isinstance(target, ast.Name)}
            if assigned & REGION_VALIDATION_CONSTANTS:
                selected.append(node)
                names.update(assigned & REGION_VALIDATION_CONSTANTS)
    if names != REGION_VALIDATION_FUNCTIONS | REGION_VALIDATION_CONSTANTS:
        raise ValueError("Region code lacks complete trusted validation dependencies")
    return sha(ast.dump(ast.Module(body=selected, type_ignores=[])).encode())


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("Expected JSON object")
    return value


def _ratio(numerator: float, denominator: object, factor: float = 1) -> float | None:
    if isinstance(denominator, bool) or not isinstance(denominator, (float, int)):
        return None
    if denominator <= 0 or not math.isfinite(denominator):
        return None
    return numerator / denominator * factor


def load_corpus(directory: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify complete DEV identity, independent references and input PDF bytes."""
    manifest, targets = _read(directory / "manifest.json"), _read(directory / "private-targets.json")
    if manifest.get("split") != "DEV":
        raise ValueError("Only DEV may be evaluated")
    records, references = manifest["pages"], targets["pages"]
    ids, target_ids = [r["id"] for r in records], [r["id"] for r in references]
    if len(ids) != len(set(ids)) or len(target_ids) != len(set(target_ids)) or set(ids) != set(target_ids):
        raise ValueError("Manifest and reference IDs must match uniquely")
    identity_metadata: dict[str, Any] = {}
    if "source_dataset_sha256" in manifest:
        identity_metadata = {"source_dataset_sha256": manifest["source_dataset_sha256"], "screen": "natural16"}
    elif "parent_dataset_sha256" in manifest:
        identity_metadata = {"parent_dataset_sha256": manifest["parent_dataset_sha256"]}
    identity = sha(
        canonical(
            {
                "schema": manifest["schema"],
                **identity_metadata,
                "pages": [{k: v for k, v in row.items() if k != "pdf_path"} for row in records],
                "targets": [{k: v for k, v in row.items() if k != "annotation_path"} for row in references],
            }
        )
    )
    if manifest["dataset_sha256"] != identity or targets["dataset_sha256"] != identity:
        raise ValueError("Frozen dataset identity mismatch")
    checked = set()
    for record in records:
        path = guard_path(Path(record["pdf_path"]))
        if not path.is_absolute():
            raise ValueError("Source PDF path must be absolute")
        pair = (str(path), record["pdf_sha256"])
        if pair not in checked:
            if sha(path.read_bytes()) != record["pdf_sha256"]:
                raise ValueError("Frozen source PDF changed")
            checked.add(pair)
    return manifest, targets


def verify_code(directory: Path, frozen: dict[str, Any], *, processor: str) -> dict[str, Any]:
    """Hash archive bytes without importing or executing artifact Python."""
    hashes = frozen["code_sha256"]
    representation = frozen.get("config", {}).get("transcription_representation", "legacy")
    if representation not in {"legacy", "matrix_strict", "atomic_cells"}:
        raise ValueError("Unknown frozen transcription representation")
    if representation != "legacy" and processor not in {"vision_regions", "hybrid"}:
        raise ValueError("Unsupported frozen transcription representation processor")
    local = Path(__file__).parent
    comparison = {}
    required = (
        {"generalization_vision_run.py", "pipeline_vision_transcription.py", "pipeline_frontier.py"}
        if processor in {"vision", "vision_regions", "vision_multiscale"}
        else {"pipeline_run.py", "pipeline_assembly.py"}
    )
    if frozen.get("config", {}).get("gate_image_mode", "rgb") != "rgb":
        required.add("p003_gate_image.py")
    if frozen.get("config", {}).get("gate_instructions", "legacy") not in ("legacy", "region"):
        required.add("p003_prompt_variants.py")
    if representation != "legacy":
        required.add("p003_transcription_design.py")
    if frozen.get("config", {}).get("transcription_wire_schema", "strict") != "strict":
        required.add("p003_wire_schema.py")
    if processor in {"vision_regions", "vision_multiscale"}:
        required.add("generalization_vision_regions.py")
    if processor == "vision_multiscale":
        required |= {
            "generalization_vision_multiscale.py",
            "pipeline_layout_tiles.py",
            "pipeline_layout_fusion.py",
            "pipeline_layout_detector.py",
        }
    if processor == "hybrid":
        orientation_mode = frozen.get("config", {}).get("native_table_orientation", "physical")
        if orientation_mode not in {"physical", "logical"}:
            raise ValueError("Unsupported frozen native table orientation")
        if orientation_mode == "logical":
            required.add("pipeline_native_orientation.py")
            _verify_orientation_runtime(frozen)
        required |= {
            "generalization_hybrid_run.py",
            "pipeline_hybrid_composition.py",
            "generalization_run.py",
            "pipeline_regions.py",
            "generalization_vision_run.py",
            "generalization_vision_regions.py",
            "pipeline_vision_transcription.py",
            "pipeline_frontier.py",
        }
    if processor == "regions":
        required |= {"pipeline_regions.py", "generalization_run.py"}
        if frozen.get("config", {}).get("assembly_method") in {"generate", "gated_generate"}:
            required.add("pipeline_generation.py")
            if frozen["config"].get("generation_format") in {"matrix", "indices"}:
                required.add("pipeline_matrix_generation.py")
            if frozen["config"].get("generation_format") == "indices":
                required |= {
                    "pipeline_index_matrix_generation.py",
                    "pipeline_generation_evidence.py",
                    "pipeline_frontier.py",
                }
        if frozen.get("config", {}).get("raster_rules"):
            required.add("pipeline_dense_candidates.py")
        if frozen.get("config", {}).get("ocr_source", "legacy") != "legacy":
            required.add("pipeline_ocr_sources.py")
    if frozen.get("config", {}).get("detector_fusion", "none") != "none":
        required.add("pipeline_layout_fusion.py")
    row_evidence = any(frozen.get("config", {}).get(flag) for flag in ("generation_row_evidence", "gate_row_evidence"))
    if row_evidence:
        required |= {"pipeline_row_context.py", "pipeline_row_evidence.py"}
    source_order = frozen.get("config", {}).get("source_order", "legacy")
    if source_order not in {"legacy", "original"}:
        raise ValueError("Unsupported frozen regional source order")
    if source_order == "original":
        required.add("pipeline_source_order.py")
    concurrent = frozen.get("config", {}).get("workers", 1) > 1
    concurrent_dependencies = {
        "decision_concurrent.py",
        "decision_hosted.py",
        "decision_gateway.py",
        "decision_langfuse.py",
        "reprice_model_rates.py",
    }
    if concurrent:
        if (
            processor != "vision"
            or frozen["config"]["workers"] != CONCURRENT_VISION_WORKERS
            or frozen.get("concurrency") != CONCURRENT_VISION_WORKERS
        ):
            raise ValueError("Concurrent comparison requires fixed four-worker whole-page vision")
        required |= concurrent_dependencies
    if not required <= hashes.keys():
        raise ValueError("Frozen code lacks required verifier dependencies")
    for name, digest in hashes.items():
        if Path(name).name != name or not name.endswith(".py"):
            raise ValueError("Unsafe archived code filename")
        if sha(guard_path(directory / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived code hash mismatch")
        local_path = local / name
        comparison[name] = (
            "identical" if local_path.is_file() and sha(local_path.read_bytes()) == digest else "different"
        )
    if concurrent and any(comparison[name] != "identical" for name in concurrent_dependencies):
        raise ValueError("Trusted concurrent request accounting differs from frozen code")
    if representation != "legacy" and any(comparison[n] != "identical" for n in (
        "p003_transcription_design.py", "generalization_vision_regions.py", "pipeline_vision_transcription.py",
    )):
        raise ValueError("Trusted transcription representation helpers differ from frozen code")
    if "p003_gate_image.py" in required and comparison["p003_gate_image.py"] != "identical":
        raise ValueError("Trusted gate image encoder differs from frozen code")
    if "p003_prompt_variants.py" in required and comparison["p003_prompt_variants.py"] != "identical":
        raise ValueError("Trusted semantic gate instruction helper differs from frozen code")
    if (
        frozen.get("config", {}).get("gate_image_mode", "rgb") != "rgb"
        or frozen.get("config", {}).get("gate_instructions", "legacy") not in ("legacy", "region")
    ) and any(comparison.get(name) != "identical" for name in (
        "generalization_run.py", "pipeline_run.py", "pipeline_frontier.py",
    )):
        raise ValueError("Trusted gate treatment runtime or request builder differs from frozen code")
    historical_helpers = {}
    if processor == "hybrid" and comparison["generalization_hybrid_run.py"] != "identical":
        if (
            hashes["generalization_hybrid_run.py"] != HYBRID_PHYSICAL_RUNNER_SHA256
            or frozen.get("config", {}).get("native_table_orientation", "physical") != "physical"
        ):
            raise ValueError("Unreviewed historical hybrid runner or logical orientation")
        historical_helpers["generalization_hybrid_run.py"] = "reviewed physical runner before 14dbc99"
    helper_name = "generalization_vision_regions.py"
    if helper_name in required and comparison[helper_name] != "identical":
        reviewed = TRUSTED_HISTORICAL_CODE[helper_name].get(hashes[helper_name])
        if reviewed is None or _vision_region_validation_ast(
            guard_path(directory / "code" / helper_name).read_bytes()
        ) != _vision_region_validation_ast((local / helper_name).read_bytes()):
            raise ValueError("Unreviewed or incompatible historical vision region composition")
        historical_helpers[helper_name] = reviewed
    if processor == "hybrid" and comparison["pipeline_hybrid_composition.py"] != "identical":
        digest = hashes["pipeline_hybrid_composition.py"]
        reviewed = TRUSTED_HISTORICAL_CODE["pipeline_hybrid_composition.py"].get(digest)
        if digest != HYBRID_LEGACY_RENDERER_SHA256 or reviewed is None:
            raise ValueError("Unreviewed historical hybrid composition or renderer")
        historical_helpers["pipeline_hybrid_composition.py"] = reviewed
    if "pipeline_layout_fusion.py" in required and comparison["pipeline_layout_fusion.py"] != "identical":
        raise ValueError("Trusted source-only detector fusion differs from frozen code")
    if row_evidence and any(
        comparison[name] != "identical" for name in ("pipeline_row_context.py", "pipeline_row_evidence.py")
    ):
        raise ValueError("Trusted source-derived row evidence differs from frozen code")
    if source_order == "original" and comparison["pipeline_source_order.py"] != "identical":
        raise ValueError("Trusted original source-order rendering differs from frozen code")
    if (
        source_order == "original"
        and processor in {"regions", "hybrid"}
        and comparison["generalization_run.py"] != "identical"
        and not (
            hashes["generalization_run.py"] == "fa51763aa571aedd12f3b625174e80b2fc57f4485b0898bb2d1bef225f8a8449"
            and frozen.get("config", {}).get("gate_image_mode", "rgb") == "rgb"
            and frozen.get("config", {}).get("gate_instructions", "legacy") in ("legacy", "region")
        )
    ):
        raise ValueError("Original source order requires the exact current regional runner")
    if processor in {"regions", "hybrid"} and frozen.get("config", {}).get("generation_format") == "indices" and any(
        comparison.get(name) != "identical"
        for name in (
            "pipeline_index_matrix_generation.py",
            "pipeline_matrix_generation.py",
            "pipeline_generation.py",
            "pipeline_generation_evidence.py",
            "pipeline_frontier.py",
        )
    ):
        raise ValueError("Trusted ordinal expansion or matrix parser differs from frozen code")
    if processor in {"vision", "vision_regions", "vision_multiscale"}:
        if any(
            comparison[name] != "identical"
            for name in required - {"generalization_vision_run.py"} - historical_helpers.keys()
        ):
            raise ValueError("Trusted local vision adapter differs from frozen code")
        historical_runner = dict(historical_helpers)
        if comparison["generalization_vision_run.py"] != "identical":
            reviewed = TRUSTED_HISTORICAL_CODE["generalization_vision_run.py"].get(
                hashes["generalization_vision_run.py"]
            )
            if reviewed is None:
                raise ValueError("Trusted local vision runner differs from unreviewed frozen code")
            historical_runner["generalization_vision_run.py"] = reviewed
        return {
            "archive_hashes_verified": True,
            "local_comparison": comparison,
            "trusted_historical_commits": historical_runner,
            "renderer": "identical trusted vision transcription adapter",
            "region_validator_ast_compatible": False,
            "vision_region_validator_ast_compatible": helper_name in required,
        }
    if processor == "hybrid":
        exact = required - {
            "pipeline_run.py",
            "generalization_run.py",
            "generalization_vision_run.py",
            "pipeline_regions.py",
        }
        if any(comparison[name] != "identical" for name in exact - historical_helpers.keys()):
            raise ValueError("Trusted hybrid composition or child parser differs from frozen code")
    # Whole-run renderer compatibility is established through its approved AST.
    renderer = _verify_markdown_renderer(directory, frozen)
    validation_modules = {"pipeline_assembly.py"}
    if processor in {"regions", "hybrid"}:
        validation_modules |= {"pipeline_regions.py", "generalization_run.py"}
    if processor == "hybrid":
        validation_modules.add("generalization_vision_run.py")
    trusted_history = dict(historical_helpers)
    for name in validation_modules:
        if comparison[name] != "identical":
            reviewed = TRUSTED_HISTORICAL_CODE.get(name, {}).get(hashes[name])
            if reviewed is None:
                raise ValueError("Trusted local ownership validator differs from unreviewed frozen code")
            trusted_history[name] = reviewed
    if processor in {"regions", "hybrid"}:
        archived = (directory / "code" / "pipeline_regions.py").read_bytes()
        if _region_validation_ast(archived) != _region_validation_ast((local / "pipeline_regions.py").read_bytes()):
            raise ValueError("Historical region composition validators differ from trusted local AST")
    return {
        "archive_hashes_verified": True,
        "local_comparison": comparison,
        "trusted_historical_commits": trusted_history,
        "renderer": renderer,
        "hybrid_renderer_version": _hybrid_render_version(directory, frozen) if processor == "hybrid" else None,
        "region_validator_ast_compatible": processor in {"regions", "hybrid"},
        "vision_region_validator_ast_compatible": helper_name in required,
    }


def _bounds(source: dict[str, Any], state: dict[str, Any]) -> None:
    lookup = {w["id"]: w for w in source["words"]}
    for table in state["tables"]:
        boxes = [lookup[i]["bbox"] for cell in table["cells"] for i in cell["source_ids"]]
        if boxes:
            table["bbox"] = [
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes),
            ]


def _hybrid_render_version(directory: Path, frozen: dict[str, Any] | None = None) -> int:
    """Select legacy markup solely from exact reviewed frozen helper bytes."""
    if frozen is None:
        frozen_path = directory / "frozen.json"
        if not frozen_path.is_file():
            return 2
        frozen = _read(frozen_path)
    digest = frozen["code_sha256"].get("pipeline_hybrid_composition.py")
    if digest == HYBRID_LEGACY_RENDERER_SHA256:
        if sha(guard_path(directory / "code" / "pipeline_hybrid_composition.py").read_bytes()) != digest:
            raise ValueError("Legacy hybrid renderer archive hash mismatch")
        return 1
    current = sha((Path(__file__).parent / "pipeline_hybrid_composition.py").read_bytes())
    if digest != current:
        raise ValueError("Unreviewed hybrid renderer hash")
    return 2


def _verify_orientation_runtime(frozen: dict[str, Any]) -> None:
    """Require exact installed extraction and baseline-orientation implementation."""
    recorded = frozen.get("runtime", {}).get("extraction_modules", {})
    for name in ("pdfust", "pdfust.pdfust_core", "pdfust._spatial", "pdfust._markdown"):
        module = importlib.import_module(name)
        path = Path(module.__file__) if module.__file__ is not None else None
        expected = {"filename": path.name, "sha256": sha(path.read_bytes())} if path is not None else None
        if expected is None or recorded.get(name) != expected:
            raise ValueError("Logical native orientation extraction/runtime fingerprint mismatch")


def _source_order_mode(directory: Path) -> str:
    frozen_path = directory / "frozen.json"
    config = _read(frozen_path).get("config", {}) if frozen_path.is_file() else {}
    mode = config.get("source_order", "legacy")
    if not isinstance(mode, str) or mode not in {"legacy", "original"}:
        raise ValueError("Unsupported frozen regional source order")
    return mode


def _verify_hybrid_output(
    directory: Path, prediction: dict[str, Any], *, config: dict[str, Any],
) -> dict[str, Any]:
    """Replay child artifacts, source-only detector exclusion and mixed composition."""
    ident = prediction["id"]
    children = {}
    for name, processor in (("native", "regions"), ("vision", "vision_regions")):
        child = prediction.get(name + "_result")
        if child is not None:
            if not isinstance(child, dict) or child.get("id") != ident:
                raise ValueError("Hybrid child identity differs from parent")
            children[name] = verify_output(
                directory / name, child, processor=processor, source_order=_source_order_mode(directory), config=config
            )
    native = prediction.get("native_result") or {}
    vision = prediction.get("vision_result") or {}
    if native.get("calls", []) != [] or prediction.get("calls", []) != vision.get("calls", []):
        raise ValueError("Hybrid calls differ from complete native and vision child accounting")
    if prediction.get("status") != "ok":
        if prediction.get("tables") != []:
            raise ValueError("Atomic failed hybrid output must have no admitted tables")
        return {"operational": False, "conserved": False}
    if (
        prediction.get("route") != "hybrid"
        or prediction.get("output_atomic") is not True
        or prediction.get("child_artifacts") != {"native": "native", "vision": "vision"}
        or set(children) != {"native", "vision"}
        or any(not child["operational"] for child in children.values())
    ):
        raise ValueError("Hybrid success requires both complete children and fixed artifact paths")
    native_clean, native_warnings = sanitize_vectors(native["source"])
    source = hybrid.sanitize_vectors(native_clean)
    if prediction.get("native_warnings") != native_warnings:
        raise ValueError("Hybrid native warnings differ from trusted source quarantine")
    native_state = _read(directory / "native" / f"{ident}-structure.json")
    native_boxes = hybrid.native_boxes(source, native_state)
    if source != prediction.get("source") or native_state != prediction.get("native_state"):
        raise ValueError("Hybrid source or native state differs from trusted native child")
    filtered, excluded = hybrid.exclude_native_proposals(prediction["raw_layout_detection"], native_boxes)
    if (
        prediction.get("native_boxes") != native_boxes
        or prediction.get("filtered_layout_detection") != filtered
        or prediction.get("excluded_native_proposals") != excluded
        or vision.get("layout_detection") != filtered
    ):
        raise ValueError("Hybrid detector exclusion differs from trusted native geometry replay")
    transcription = _read(directory / "vision" / f"{ident}-structure.json")
    frozen_path = directory / "frozen.json"
    frozen = _read(frozen_path) if frozen_path.is_file() else {}
    if frozen.get("config", {}).get("native_table_orientation", "physical") == "logical":
        _verify_orientation_runtime(frozen)
        record = next((r for r in frozen["records"] if r["id"] == ident), None)
        if record is None:
            raise ValueError("Logical orientation lacks a frozen original source record")
        data = guard_path(Path(record["pdf_path"])).read_bytes()
        if sha(data) != record["pdf_sha256"]:
            raise ValueError("Original source PDF changed before orientation replay")
        with importlib.import_module("pdfust").open(stream=data) as document:
            evidence = orientation.evidence(document[record["page_number"]], native_boxes)
        if evidence != prediction.get("native_orientation_evidence"):
            raise ValueError("Native orientation evidence differs from exact original PDF replay")
        if _hybrid_render_version(directory, frozen) != 2:  # noqa: PLR2004
            raise ValueError("Logical orientation requires the current renderer")
        rebuilt = orientation.compose(source, native_state, transcription, evidence)
    else:
        if "native_orientation_evidence" in prediction:
            raise ValueError("Physical hybrid output must not select orientation evidence")
        rebuilt = hybrid.compose(source, native_state, transcription, render_version=_hybrid_render_version(directory))
    if rebuilt.get("status") != "ok" or rebuilt != prediction.get("composition"):
        raise ValueError("Hybrid composition differs from trusted complete replay")
    if _read(directory / f"{ident}-structure.json") != rebuilt:
        raise ValueError("Hybrid retained structure differs from trusted complete replay")
    for key in rebuilt.keys() - {"markdown", "status", "route"}:
        if prediction.get(key) != rebuilt[key]:
            raise ValueError("Hybrid parent accounting or tables differs from complete composition")
    if guard_path(directory / f"{ident}.md").read_bytes() != hybrid.markdown(rebuilt).encode():
        raise ValueError("Hybrid Markdown differs from trusted complete composition")
    return {"operational": True, "conserved": rebuilt["source_conserved"]}


def _verify_multiscale_detection(prediction: dict[str, Any]) -> None:
    """Replay all fixed CPU source windows before strict crop composition."""
    viewport = prediction["viewport"]
    image = prediction["multiscale_image"]
    bounds = _box(viewport)
    size = image["image_size"]
    if (
        prediction.get("processor") != "vision_multiscale"
        or prediction.get("multiscale_rules") != MULTISCALE_RULES
        or image.get("viewport") != viewport
        or image.get("rotation_normalized") is not False
        or image.get("original_rotation") not in (0, 90, 180, 270)
        or image.get("original_rotation") != prediction.get("original_rotation")
        or prediction.get("rotation_normalized") is not False
        or image.get("render_scale") != 3071 / max(bounds[2] - bounds[0], bounds[3] - bounds[1])
        or not isinstance(size, list)
        or len(size) != 2  # noqa: PLR2004
        or any(type(value) is not int or value < 3 or value > 3072 for value in size)  # noqa: PLR2004
        or max(size) < 3070  # noqa: PLR2004
        or abs(size[0] / size[1] - (bounds[2] - bounds[0]) / (bounds[3] - bounds[1])) > 2 / min(size)
    ):
        raise ValueError("Multiscale source rendering or fixed rules differ from trusted acquisition")
    base = prediction.get("multiscale_received_base_image")
    if (
        not isinstance(base, dict)
        or base.get("used_for_inference") is not False
        or base.get("sha256") != prediction.get("detector_image", {}).get("sha256")
        or base.get("bytes") != prediction.get("detector_image", {}).get("bytes")
    ):
        raise ValueError("Multiscale unused base raster differs from retained crop detector input")
    rebuilt = multiscale_replay(prediction["multiscale_raw_calls"], viewport, size)
    if rebuilt != prediction.get("layout_detection"):
        raise ValueError("Multiscale retained detector proposals differ from complete trusted raw replay")



def _verify_transcription_requests(
    directory: Path, prediction: dict[str, Any], config: dict[str, Any],
) -> None:
    """Authenticate the treatment against actual bodies, including failed pages."""
    representation = config.get("transcription_representation", "legacy")
    wire_schema = config.get("transcription_wire_schema", "strict")
    if wire_schema not in ("strict", "simple"):
        raise ValueError("Unknown frozen transcription wire schema")
    if representation not in {"legacy", "matrix_strict", "atomic_cells"}:
        raise ValueError("Unknown frozen transcription representation")
    if prediction.get("transcription_representation", "legacy") != representation:
        raise ValueError("Prediction representation differs from frozen treatment")
    for region in prediction.get("transcription_regions", []):
        if region.get("transcription_representation", "legacy") != representation:
            raise ValueError("Region representation differs from frozen treatment")
        # Existing legacy archives did not retain this treatment's body seam.
        if representation == "legacy" and wire_schema == "strict":
            continue
        metadata = region.get("request")
        if metadata is None and region.get("status") == "not_requested":
            continue
        if not isinstance(metadata, dict) or metadata.get("transcription_representation") != representation:
            raise ValueError("Request representation differs from frozen treatment")
        body = _read(directory / f"{prediction['id']}-request-{region['request_index']}.json")
        try:
            url = body["messages"][1]["content"][0]["image_url"]["url"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("Missing transcription request pixels") from error
        rebuilt = transcription_request(
            config["generation_model"], url, region["viewport"],
            max_tokens=config.get("generation_tokens", 16384), representation=representation,
            wire_schema=wire_schema,
        )
        if config.get("generation_provider"):
            rebuilt["provider"] = {"only": [config["generation_provider"]], "allow_fallbacks": False,
                                   "require_parameters": True}
        encoded = json.dumps(rebuilt, separators=(",", ":")).encode()
        if body != rebuilt or metadata.get("body_sha256") != sha(encoded) or metadata.get("body_bytes") != len(encoded):
            raise ValueError("Actual transcription body differs from frozen representation")



def _gate_urls(value: Any) -> list[Any]:  # noqa: ANN401 - recursive JSON image parts.
    urls = []
    if isinstance(value, dict):
        if value.get("type") == "image_url" and isinstance(value.get("image_url"), dict):
            urls.append(value["image_url"].get("url"))
        for child in value.values():
            urls.extend(_gate_urls(child))
    elif isinstance(value, list):
        for child in value:
            urls.extend(_gate_urls(child))
    return urls

def _verify_gate_instructions(directory: Path, prediction: dict[str, Any], config: dict[str, Any]) -> None:
    """Rebuild the gate template around retained literal evidence, using frozen rubric."""
    from bench.generalization_run import GATE_CHOICES, gate_instructions
    from bench.pipeline_frontier import MODELS
    from bench.pipeline_run import body as gate_body

    style = config["gate_instructions"]
    evidence = prediction.get("gate_instruction_evidence", [])
    indexes = [entry["request_index"] for entry in evidence]
    required = {i for i, call in enumerate(prediction.get("calls", []))
                if call.get("kind") != "source_id_generation"}
    if len(indexes) != len(set(indexes)) or not required <= set(indexes):
        raise ValueError("Semantic gate evidence omits or duplicates an actual gate attempt")
    regions = {region["id"] for region in prediction.get("region_plan", {}).get("regions", [])}
    primary_regions: set[str] = set()
    for entry in evidence:
        if entry["variant"] != style or entry["region_id"] not in regions:
            raise ValueError("Semantic gate evidence differs from frozen variant or source region")
        model = config["gate_review_model"] if entry["region_id"] in primary_regions else config["model"]
        primary_regions.add(entry["region_id"])
        actual = _read(directory / f"{prediction['id']}-request-{entry['request_index']}.json")
        if model in MODELS:
            state = actual["messages"][2]["content"]
            prompt = state if isinstance(state, str) else state[0]["text"]
        else:
            state = actual["state"]
            prompt = state if isinstance(state, str) else state[0]
        urls = _gate_urls(actual)
        if not isinstance(prompt, str) or len(urls) > 1:
            raise ValueError("Semantic gate literal evidence is malformed")
        expected = gate_body(model, prompt, GATE_CHOICES, urls[0] if urls else None,
                             instructions=gate_instructions(config))
        if config.get("answer_tokens") and model in MODELS:
            expected["max_tokens"] = config["answer_tokens"]
        if actual != expected:
            raise ValueError("Actual gate body differs from frozen semantic instructions")


def _verify_gate_images(
    directory: Path, prediction: dict[str, Any], config: dict[str, Any]) -> None:
    """Replay encoded gate payloads from frozen source, including failed attempts."""
    import pdfust
    from bench.generalization_run import region_image
    from bench.p003_gate_image import transform

    frozen = _read(directory / "frozen.json")
    records = [r for r in frozen["records"] if r["id"] == prediction["id"]]
    if len(records) != 1:
        raise ValueError("Gate encoding source record identity mismatch")
    record = records[0]
    data = guard_path(Path(record["pdf_path"])).read_bytes()
    if sha(data) != record["pdf_sha256"]:
        raise ValueError("Gate encoding source PDF changed")
    evidence = prediction.get("gate_image_evidence", [])
    indexes = [e["request_index"] for e in evidence]
    required = {i for i, call in enumerate(prediction.get("calls", []))
                if call.get("kind") != "source_id_generation"}
    if len(indexes) != len(set(indexes)) or not required <= set(indexes):
        raise ValueError("Gate image evidence omits or duplicates an actual gate attempt")
    regions = {r["id"]: r for r in prediction.get("region_plan", {}).get("regions", [])}
    with pdfust.open(stream=data) as document:
        page = document[record["page_number"]]
        normalize = config.get("normalize_rotation", True) and config.get("rotation_mode", "always") != "preserve"
        if normalize and config.get("rotation_mode", "always") == "native":
            normalize = bool(page.get_text("words"))
        if normalize and page.rotation:
            page.set_rotation(0)
        if prediction.get("effective_rotation", page.rotation) != page.rotation:
            raise ValueError("Gate source rotation differs from frozen acquisition")
        for entry in evidence:
            region = regions[entry["region_id"]]
            url, metadata = region_image(page, region["bbox"], config.get("gate_image_edge", config["image_edge"]))
            expected_url, expected_metadata = transform(url, metadata, config["gate_image_mode"])
            if entry["image"] != expected_metadata:
                raise ValueError("Gate encoding metadata differs from deterministic source replay")
            body = _read(directory / f"{prediction['id']}-request-{entry['request_index']}.json")
            urls = _gate_urls(body)
            if urls != [expected_url]:
                raise ValueError("Actual gate pixels differ from frozen source encoding")

def verify_output(
    directory: Path, prediction: dict[str, Any], *, processor: str, source_order: str | None = None,
    config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Revalidate source ownership and exact retained Markdown for successful pages."""
    ident = prediction["id"]
    if not isinstance(ident, str) or Path(ident).name != ident or ident in {".", ".."}:
        raise ValueError("Unsafe page ID")
    retained = _read(directory / f"{ident}-result.json")
    if retained != prediction:
        raise ValueError("Per-page retained result differs from report")
    if config is None:
        frozen_path = directory / "frozen.json"
        config = _read(frozen_path).get("config", {}) if frozen_path.is_file() else {}
    representation = config.get("transcription_representation", "legacy")
    if processor == "regions" and config.get("gate_instructions", "legacy") not in ("legacy", "region"):
        _verify_gate_instructions(directory, prediction, config)
    if processor == "regions" and config.get("gate_image_mode", "rgb") != "rgb":
        _verify_gate_images(directory, prediction, config)
    if processor == "hybrid":
        return _verify_hybrid_output(directory, prediction, config=config)
    if processor == "vision_regions":
        _verify_transcription_requests(directory, prediction, config)
    if prediction.get("status") != "ok":
        return {"operational": False, "conserved": False}
    state = _read(directory / f"{ident}-structure.json")
    if processor in {"vision", "vision_regions", "vision_multiscale"}:
        if (
            prediction.get("route")
            != (
                "vision_transcription_regions"
                if processor in {"vision_regions", "vision_multiscale"}
                else "vision_transcription"
            )
            or prediction.get("source_conserved") is not False
            or prediction.get("unresolved_ids") != []
            or "source" in prediction
        ):
            raise ValueError("Vision output must be labeled model transcription without source ownership")
        if processor in {"vision_regions", "vision_multiscale"}:
            if processor == "vision_multiscale":
                _verify_multiscale_detection(prediction)
            regions = prediction["transcription_regions"]
            if prediction.get("coverage") != "unverified" or prediction.get("proposal_count") != len(regions):
                raise ValueError("Vision region proposal count or unverified coverage label differs")
            selected = vision_region_proposals(prediction["layout_detection"], prediction["viewport"])
            proposal_fields = ("index", "request_index", "viewport", "detector_box")
            if [{key: region.get(key) for key in proposal_fields} for region in regions] != [
                {key: region[key] for key in proposal_fields} for region in selected
            ]:
                raise ValueError("Vision regions differ from complete retained detector proposals")
            rebuilt = vision_regions_compose(regions, prediction["viewport"], representation=representation)
            for region in regions:
                parsed = transcription_parse(
                    region["transcription_response"], region["viewport"], representation=representation,
                )
                if parsed["tables"] != region.get("tables"):
                    raise ValueError("Vision region tables differ from reparsed retained response")
        else:
            rebuilt = vision_parse(prediction["transcription_response"], prediction["viewport"])
        if rebuilt != state or rebuilt["tables"] != prediction["tables"]:
            raise ValueError("Vision transcription differs from reparsed retained response")
        if guard_path(directory / f"{ident}.md").read_bytes() != vision_markdown(rebuilt).encode():
            raise ValueError("Retained Markdown differs from trusted vision rendering")
        return {"operational": True, "conserved": False}
    source = prediction["source"]
    if state["tables"] != prediction["tables"] or state["unresolved_ids"] != prediction["unresolved_ids"]:
        raise ValueError("Retained complete structure differs from report")
    if processor == "regions":
        source_order = _source_order_mode(directory) if source_order is None else source_order
        if source_order not in {"legacy", "original"}:
            raise ValueError("Unsupported trusted regional source order")
        plan = {**prediction["region_plan"], "page_size": source["page_size"], "words": source["words"]}
        region_outputs = prediction["regions"]
        ids = [r["id"] for r in region_outputs]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate retained region state")
        states = {r["id"]: r["state"] for r in region_outputs}
        rebuilt = compose(plan, states)
        _bounds(source, rebuilt)
        if rebuilt != state:
            raise ValueError("Region composition differs from retained complete state")
        validate_composed(source, state)
        order = {w["id"]: i for i, w in enumerate(source["words"])}
        rendered = [
            (
                min((order[i] for i in r["source_ids"]), default=len(order)),
                _render_markdown(
                    render_source(source, r) if source_order == "original" else r["source"], states[r["id"]]
                ),
            )
            for r in plan["regions"]
        ]
        markdown = "\n".join(text for _, text in sorted(rendered))
    else:
        markdown = _render_markdown(source, state)
    if guard_path(directory / f"{ident}.md").read_bytes() != markdown.encode():
        raise ValueError("Retained Markdown differs from trusted exact rendering")
    assigned = state["unresolved_ids"] + [i for t in state["tables"] for c in t["cells"] for i in c["source_ids"]]
    if Counter(assigned) != Counter(w["id"] for w in source["words"]):
        raise ValueError("Output does not conserve complete page source")
    return {"operational": True, "conserved": True}


def _ceiling(target: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
    source = prediction.get("source")
    result: dict[str, Any] = {"source_available": source is not None, "ocr_text_recall": None}
    if source is not None and target.get("structural_scored", True):
        gold = Counter(
            "".join(normalize_text(v) for t in target.get("tables", []) for row in t["values"] for v in row if v)
        )
        words = Counter("".join(normalize_text(w["text"]) for w in source["words"]))
        result.update(
            source_character_count=sum(words.values()),
            reference_character_count=sum(gold.values()),
            source_reference_character_inventory_overlap=sum((gold & words).values()),
            source_character_inventory_scope=(
                "whole-page characters; geometry/order/cell identity ignored; not OCR recall"
            ),
        )
    candidates = prediction.get("candidates")
    if candidates:
        scores = [score_page(target, candidate["tables"]) for candidate in candidates]
        scored = [s for s in scores if s["structural_scored"]]
        result["candidate_count"] = len(candidates)
        result["candidate_exact_page_ceiling"] = max((int(s["exact_page"]) for s in scored), default=None)
        result["candidate_complete_tables_ceiling"] = max((s["complete_tables"] for s in scored), default=None)
    else:
        result["candidate_exact_page_ceiling"] = None
        result["candidate_ceiling_reason"] = "not retained, or region cross-product not enumerated"
    return result


def _evaluate(targets: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    result = score_dataset(targets, predictions)
    localized = 0
    for page in result["pages"]:
        count = sum(match["iou"] is not None and match["iou"] >= LOCALIZATION_IOU for match in page.get("matches", []))
        page["localized_tables_iou_ge_0_5"] = count
        localized += count
    result["totals"]["localized_tables_iou_ge_0_5"] = localized
    return result


def _positive_macro(page_scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Average exact recalls over all scored positive pages, including failures."""
    pages = [p for p in page_scores if p.get("structural_scored") and p.get("positive_page")]
    cells = sum(0.0 if p.get("error") else p["correct_text_cells"] / p["expected_cells"] for p in pages)
    tables = sum(0.0 if p.get("error") else p["complete_tables"] / p["expected_tables"] for p in pages)
    return {
        "positive_pages": len(pages),
        "exact_cell_recall": cells / len(pages) if pages else None,
        "complete_table_recall": tables / len(pages) if pages else None,
        "scope": "Supplementary arithmetic mean of per-positive-page recalls. Every scored positive page "
        "has equal weight; failed/missing pages contribute zero. Negative and unscored diagnostic pages "
        "are excluded here and remain in their existing metrics. Primary micro denominators are unchanged. "
        "These recalls do not penalize extra tables; existing false-positive metrics remain required.",
    }


def _macro_line(macro: dict[str, Any]) -> str:
    cells, tables = macro["exact_cell_recall"], macro["complete_table_recall"]
    cell_label = "undefined" if cells is None else f"{cells:.2%}"
    table_label = "undefined" if tables is None else f"{tables:.2%}"
    return (
        f"Supplementary positive-page macro recall ({macro['positive_pages']} pages): "
        f"exact cells {cell_label}; complete tables {table_label}. "
        "Equal page weights; failures contribute zero; negatives remain separately scored. "
        "Primary cell/table totals and false-positive metrics remain unchanged."
    )


def _costs(report: dict[str, Any]) -> dict[str, Any]:
    bases = report.get("cost_bases", {})
    effective = report.get("effective_usd")
    if bases.get("reserved", 0) or bases.get("unknown", 0) or report.get("ledger_attempts") is None:
        effective = None
    return {
        "scope": "all ledger attempts attributed to the run, including failed attempts; API only",
        "ledger_attempts": report.get("ledger_attempts"),
        "successful_calls": report.get("calls"),
        "provider_reported_subtotal_usd": report.get("provider_reported_usd"),
        "missing_provider_charge_count": report.get("missing_provider_charge_count"),
        "accounted_usd_including_reservations": report.get("accounted_usd"),
        "effective_usd": effective,
        "cost_bases": bases,
        "reservation_usd": None if bases.get("reserved", 0) else 0,
        "estimated_usd": None if any("estimate" in str(k) for k in bases) else 0,
        "breakdown_note": (
            "Reported zero preserved. Estimate/reservation amounts unavailable in summary; not inferred from tokens."
        ),
    }


USAGE_FIELDS = (
    "prompt_tokens",
    "completion_tokens",
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "prompt_tokens_details.cached_tokens",
    "input_tokens_details.cached_tokens",
)


def _numeric_observations(values: list[Any]) -> dict[str, Any]:
    valid = [
        v for v in values if not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v) and v >= 0
    ]
    return {
        "observations": len(values),
        "reported_positive": sum(v > 0 for v in valid),
        "reported_zero": sum(v == 0 for v in valid),
        "missing_or_invalid": len(values) - len(valid),
        "known_subtotal": sum(valid) if valid else None,
        "complete_total": sum(valid) if len(valid) == len(values) and values else None,
    }


def _usage_value(usage: dict[str, Any], field: str) -> object:
    value: object = usage
    for component in field.split("."):
        if not isinstance(value, dict) or component not in value:
            return None
        value = value[component]
    return value


def _model_breakdown(predictions: list[dict[str, Any]], audits: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep body model identity distinct from configuration and ledger totals."""
    requests = {a["path"]: a.get("model", "unknown") for a in audits}
    request_counts = Counter(requests.values())
    calls: dict[str, list[dict[str, Any]]] = defaultdict(list)
    discrepancies = []
    for prediction in predictions:
        for step, call in enumerate(prediction.get("calls", [])):
            prefix = "vision/" if prediction.get("route") == "hybrid" else ""
            body_model = requests.get(f"{prefix}{prediction['id']}-request-{step}.json", "unknown")
            entry_model = call.get("entry", {}).get("requested_model")
            if entry_model is not None and entry_model != body_model:
                discrepancies.append({"page": prediction["id"], "step": step, "body": body_model, "entry": entry_model})
            calls[body_model].append(call)
    models = {}
    for model in request_counts.keys() | calls.keys():
        returned = calls[model]
        entries = [c.get("entry", {}) for c in returned]
        models[model] = {
            "retained_request_bodies": request_counts[model],
            "returned_calls": len(returned),
            "returned_provider_reported_usd": _numeric_observations([e.get("provider_reported_usd") for e in entries]),
            "returned_accounted_usd": _numeric_observations([e.get("accounted_usd") for e in entries]),
            "returned_cost_bases": dict(Counter(e.get("cost_status", "unknown") for e in entries)),
            "usage": {
                field: _numeric_observations([_usage_value(c.get("usage", {}), field) for c in returned])
                for field in USAGE_FIELDS
            },
        }
    return {
        "models": models,
        "request_entry_model_discrepancies": discrepancies,
        "scope": "Retained request bodies and returned calls, including calls on failed pages. "
        "Per-model charges are returned-call subtotals; all-attempt charges remain ledger-authoritative. "
        "A request body can represent multiple transport attempts; "
        "no missing usage/cache field is imputed zero. "
        "Provider cache fields are reported literally; there is no local inference cache.",
    }


def _failure_taxonomy(directory: Path, predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify failed pages from retained API finishes separately from parser errors.

    Read only response filenames explicitly retained in those pages' calls.
    Generic completion errors do not prove token-budget exhaustion.
    """
    response_directory = directory.parent.parent / "decisions"
    failures = []
    for prediction in predictions:
        if prediction.get("status") == "ok":
            continue
        error = str(prediction.get("error", "unclassified failure"))
        responses: list[dict[str, Any]] = []
        raw_prediction = prediction.get("vision_result") or prediction
        direct = raw_prediction.get("transcription_response")
        if isinstance(direct, dict):
            responses.append({"source": "transcription_response", "payload": direct})
        for region in raw_prediction.get("transcription_regions", []):
            raw = region.get("transcription_response")
            if isinstance(raw, dict):
                responses.append({"source": f"transcription_region_{region.get('index')}", "payload": raw})
        for call in prediction.get("calls", []):
            filename = call.get("entry", {}).get("response_file")
            if filename is not None:
                if not isinstance(filename, str) or Path(filename).name != filename or filename in {".", ".."}:
                    raise ValueError("Unsafe retained API response filename")
                path = guard_path(response_directory / filename)
                if path.is_file():
                    responses.append({"source": filename, "sha256": sha(path.read_bytes()), "payload": _read(path)})
            elif isinstance(call.get("finish_reason"), str):
                responses.append({"source": "retained_call_metadata", "finish_reason": call["finish_reason"]})
        observations = []
        for response in responses:
            raw = response.pop("payload", None)
            if raw is not None:
                choices = raw.get("choices")
                if isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict):
                    response["finish_reason"] = choices[0].get("finish_reason")
                    message = choices[0].get("message", {})
                    response["content_missing"] = not isinstance(message, dict) or message.get("content") is None
            observations.append(response)
        finish = observations[-1].get("finish_reason") if observations else None
        if not isinstance(finish, str):
            finish = None
        child_errors = [
            str(prediction[key].get("error", ""))
            for key in ("native_result", "vision_result")
            if isinstance(prediction.get(key), dict)
        ]
        lower = " ".join([error, *child_errors]).lower()
        if finish == "content_filter":
            category = "provider_content_filter"
        elif finish in {"length", "max_tokens"}:
            category = "provider_output_length"
        elif "no extracted or recognized source text" in lower:
            category = "missing_source_text"
        elif any(word in lower for word in ("normalized image coordinates", "table bounds", "viewport")):
            category = "invalid_table_geometry"
        elif "anchor" in lower:
            category = "invalid_anchor_collection"
        elif "source id" in lower or "source_id" in lower or "unknown id" in lower:
            category = "invalid_source_ids"
        elif any(
            word in lower for word in ("span", "topology", "rectangular", "overlap", "tiling", "covered merge slots")
        ):
            category = "invalid_table_topology"
        elif any(word in lower for word in ("admission", "exceeds", "over-limit", "budget")):
            category = "local_input_or_output_admission"
        elif "finish" in lower or "truncat" in lower:
            category = "unclassified_completion_failure"
        else:
            category = "other_failure"
        failures.append(
            {"id": prediction["id"], "category": category, "error": error, "response_observations": observations}
        )
    return {
        "counts": dict(Counter(f["category"] for f in failures)),
        "pages": failures,
        "scope": "Failed retained pages only; missing pages are counted separately in run statuses. "
        "Provider finish codes come from retained responses or explicit call metadata; generic parser "
        "messages never imply output-token exhaustion. No response content is copied into this summary.",
    }


def _posthoc_density(
    records: list[dict[str, Any]], targets: list[dict[str, Any]], predictions: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Report a labeled posthoc two-newspaper contrast without changing primary gold."""
    dense = {"p1bfa52a41a5e15015698", "p98d10ef50dee4b24506a"}
    if len(records) != NATURAL_SCREEN_PAGES or not dense <= {r["id"] for r in records}:
        return None
    groups = {}
    for name, include_dense in (("two_dense_newspapers", True), ("remaining_fourteen", False)):
        members = [t for t in targets if (t["id"] in dense) == include_dense]
        ids = {t["id"] for t in members}
        evaluation = _evaluate(members, [p for p in predictions if p["id"] in ids])
        groups[name] = evaluation["totals"]
        groups[name]["exact_positive_page"] = sum(
            bool(page.get("positive_page") and page.get("exact_page")) for page in evaluation["pages"]
        )
    return {
        "scope": "Posthoc density diagnostic only; all sixteen pages and all targets remain primary. "
        "The remaining fourteen include four negative pages; this is not a new selected evaluation cohort.",
        "dense_page_ids": sorted(dense),
        "groups": groups,
    }


def score_run(
    directory: Path, manifest_path: Path, manifest: dict[str, Any], targets: dict[str, Any]
) -> dict[str, Any]:
    """Include every frozen intended page; reject outcome-selected inventories."""
    report, frozen = _read(directory / "report.json"), _read(directory / "frozen.json")
    config = report["config"]
    if config != frozen["config"] or frozen["manifest_sha256"] != sha(guard_path(manifest_path).read_bytes()):
        raise ValueError("Frozen config or manifest changed")
    records = [r for r in manifest["pages"] if not config.get("pilot", False) or r["pilot"]]
    expected = {r["id"]: {k: r[k] for k in SOURCE_FIELDS} for r in records}
    actual = {r["id"]: r for r in frozen["records"]}
    if actual != expected or len(actual) != len(frozen["records"]):
        raise ValueError("Frozen records differ from complete intended manifest cohort")
    processor = config.get("processor", "whole")
    if processor not in {"whole", "regions", "vision", "vision_regions", "vision_multiscale", "hybrid"}:
        raise ValueError("Unsupported processor")
    code = verify_code(directory, frozen, processor=processor)
    predictions = report["results"]
    private = [t for t in targets["pages"] if t["id"] in expected]
    scoring_predictions = deepcopy(predictions)
    derived_boxes = 0
    for prediction in scoring_predictions:
        if prediction.get("status") == "ok" and prediction.get("source") is not None:
            state = {"tables": [t for t in prediction["tables"] if "bbox" not in t]}
            _bounds(prediction["source"], state)
            derived_boxes += sum("bbox" in t for t in state["tables"])
    scored = _evaluate(private, scoring_predictions)
    by_id, by_target = {p["id"]: p for p in scoring_predictions}, {t["id"]: t for t in private}
    verified_outputs = [verify_output(directory, p, processor=processor, config=config) for p in predictions]
    operational = sum(output["operational"] for output in verified_outputs)
    conserved = sum(output["conserved"] for output in verified_outputs)
    groups: dict[str, Any] = {}
    for field in ("cohort", "family"):
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in records:
            buckets[r.get(field, "unknown")].append(by_target[r["id"]])
        groups[field] = {
            key: _evaluate(members, [by_id[t["id"]] for t in members if t["id"] in by_id])["totals"]
            for key, members in buckets.items()
        }
    authored = [by_target[r["id"]] for r in records if r.get("cohort") == "authored"]
    authored_legacy = authored_score_dataset(
        authored, [p for p in predictions if p["id"] in {t["id"] for t in authored}]
    )
    request_audits = []
    request_prefix = "vision/" if processor == "hybrid" else ""
    expected_requests = {
        f"{request_prefix}{p['id']}-request-{step}.json"
        for p in predictions
        for step, _call in enumerate(p.get("calls", []))
    }
    request_paths = sorted(guard_path(directory / request_prefix).glob("*-request-*.json"))
    if not expected_requests <= {str(p.relative_to(directory)) for p in request_paths}:
        raise ValueError("Successful call lacks a retained request body")
    for body_path in request_paths:
        owner = body_path.name.rsplit("-request-", 1)[0]
        if owner not in expected:
            raise ValueError("Retained request belongs to an unknown page")
        body = _read(body_path)
        audit = audit_model_body(body)
        if not audit["explicit_reference_fields_absent"]:
            raise ValueError("Explicit reference fields in retained model body")
        request_audits.append(
            {
                "path": str(body_path.relative_to(directory)),
                "sha256": sha(body_path.read_bytes()),
                "model": body.get("model", "unknown"),
                **audit,
            }
        )
    positive_targets = [t for t in private if t.get("structural_scored", True) and t.get("tables")]
    negative_targets = [t for t in private if t.get("structural_scored", True) and not t.get("tables")]
    positive = _evaluate(positive_targets, [by_id[t["id"]] for t in positive_targets if t["id"] in by_id])["totals"]
    negative = _evaluate(negative_targets, [by_id[t["id"]] for t in negative_targets if t["id"] in by_id])["totals"]
    costs = _costs(report)
    metrics = dict(report.get("metrics", {}))
    if report.get("layout_detector_initialization") is not None:
        metrics["layout_detector_worker"] = {
            "initialization": report["layout_detector_initialization"],
            "requests": [
                p[key]["metrics"]
                for p in predictions
                for key in ("layout_detector", "layout_detection")
                if isinstance(p.get(key), dict) and "metrics" in p[key]
            ]
            + [
                p["vision_result"]["layout_detection"]["metrics"]
                for p in predictions
                if isinstance(p.get("vision_result"), dict)
                and isinstance(p["vision_result"].get("layout_detection"), dict)
                and "metrics" in p["vision_result"]["layout_detection"]
            ],
            "multiscale_raw_requests": [
                call["result"]["metrics"]
                for p in predictions
                for call in p.get("multiscale_raw_calls", [])
                if isinstance(call.get("result"), dict) and "metrics" in call["result"]
            ],
            "scope": "Separate CPU subprocess measurements; parent CPU/RSS excludes this worker. "
            "Parent elapsed time includes initialization and requests; RSS peaks are not summed.",
        }
    metrics["run_interval_scope"] = (
        "Page-processing run interval, excluding freeze/client setup and command startup. "
        "Includes page PDF processing and retained outputs; use parent process CPU/RSS/wall. "
        "Concurrent per-page process CPU intervals overlap and must not be summed."
    )
    for field in ("wall_seconds", "cpu_seconds", "cpu_utilization_percent", "peak_sampled_rss_bytes", "measurement"):
        metrics.setdefault(field, None)
    if report.get("page_count", len(predictions)) != len(predictions):
        raise ValueError("Report page count differs from retained result inventory")
    if report.get("complete_output_pages", operational) != operational:
        raise ValueError("Report successful count differs from verified complete outputs")
    statuses = Counter(p.get("status", "missing") for p in predictions)
    statuses["missing"] += len(expected) - len(predictions)
    return {
        "name": directory.name,
        "report_sha256": sha(guard_path(directory / "report.json").read_bytes()),
        "config": config,
        "manifest_sha256": frozen["manifest_sha256"],
        "dataset_sha256": manifest["dataset_sha256"],
        "intended_pages": len(expected),
        "scores": scored["totals"],
        "positive": positive,
        "positive_macro": _positive_macro(scored["pages"]),
        "negative": negative,
        "page_scores": scored["pages"],
        "groups": groups,
        "authored_legacy_exact": authored_legacy["totals"],
        "statuses": dict(statuses),
        "failure_taxonomy": _failure_taxonomy(directory, predictions),
        "posthoc_density": _posthoc_density(records, private, scoring_predictions),
        "operational_pages": operational,
        "all_errors": len(expected) - operational,
        "markdown_bytes_verified_pages": operational,
        "conserved_pages": conserved,
        "output_scope": (
            "table-only image transcription comparator"
            if processor in {"vision", "vision_regions", "vision_multiscale"}
            else (
                "complete retained-source assembly with explicit mixed text provenance"
                if processor == "hybrid"
                else "complete source assembly"
            )
        ),
        "text_provenance": (
            "mixed native-source/model-transcribed"
            if processor == "hybrid"
            else (
                "model-transcribed"
                if processor in {"vision", "vision_regions", "vision_multiscale"}
                else "source-owned"
            )
        ),
        "source_candidate_ceilings": [{"id": t["id"], **_ceiling(t, by_id.get(t["id"], {}))} for t in private],
        "costs": costs,
        "resources": metrics,
        "frozen_runtime": {
            k: frozen.get(k)
            for k in (
                "runtime",
                "python",
                "platform",
                "logical_cpus",
                "concurrency",
                "local_replay",
            )
        },
        "pages_per_minute": _ratio(operational, metrics.get("wall_seconds"), 60),
        "resource_scope": metrics.get("measurement", "unmeasured"),
        "pages_per_dollar": _ratio(operational, costs["effective_usd"]),
        "exact_pages_per_minute": _ratio(scored["totals"].get("exact_page", 0), metrics.get("wall_seconds"), 60),
        "exact_pages_per_dollar": _ratio(scored["totals"].get("exact_page", 0), costs["effective_usd"]),
        "exact_positive_pages_per_minute": _ratio(positive.get("exact_page", 0), metrics.get("wall_seconds"), 60),
        "exact_positive_pages_per_dollar": _ratio(positive.get("exact_page", 0), costs["effective_usd"]),
        "derived_prediction_bboxes": derived_boxes,
        "localization_policy": {
            "assignment_iou_threshold": 0.1,
            "localization_iou_threshold": 0.5,
            "description": "Low-threshold correspondence is not detection recall or AP. Strict count is IoU >= 0.5.",
        },
        "code_verification": code,
        "request_body_audits": request_audits,
        "actual_model_breakdown": _model_breakdown(predictions, request_audits),
        "model_configuration": {
            k: config.get(k)
            for k in (
                "policy",
                "assembly_method",
                "model",
                "gate_review_model",
                "generation_model",
            )
        },
        "comparison_caveats": [
            "Authored DEV silver and independently annotated natural tables are reported separately.",
            "Pilot/full runs and different OCR/rotation/region policies are not matched causal comparisons.",
            (
                "Low-threshold assignments are correspondences, not detection recall or AP. "
                "Text-assisted matching is not independent geometric detection; "
                "OCR recall is unavailable without aligned OCR gold."
            ),
            "Body field audits do not prove semantic absence of leaked answers inside arbitrary strings.",
            (
                "Vision is a table-only model transcription comparator; it neither conserves OCR source "
                "nor produces complete page prose. Every intended table target remains scored."
                if processor in {"vision", "vision_regions", "vision_multiscale"}
                else (
                    "Hybrid accounts every original source word, with superseded words retained in its ledger; "
                    "accepted transcription has no original source ownership and makes source_conserved false."
                    if processor == "hybrid"
                    else "Source ownership conservation verifies retained words, not raster OCR completeness."
                )
            ),
            "Legacy predicted bboxes derive from owned text extents; annotation boxes may include borders or padding.",
        ],
    }


def markdown_report(runs: list[dict[str, Any]]) -> str:
    """Render concise aggregate and cohort/family metrics with explicit limits."""
    lines = [
        "# P002 complete natural-PDF pipeline",
        "",
        "All intended pages, including missing and failed outputs, remain in denominators.",
        "OCR text recall is unmeasured without aligned OCR references. JSON null means unmeasured or undefined.",
        "Timing/throughput cover the page-processing interval, excluding freeze/client setup and command startup.",
        "",
    ]
    lines += [
        (
            "| Run | Pages | Verified outputs | Errors | Exact pages | Missing tables | "
            "Extra tables | Pages/min | Effective USD |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for run in runs:
        s = run["scores"]
        values = [
            run["name"],
            run["intended_pages"],
            run["operational_pages"],
            run["all_errors"],
            s.get("exact_page", 0),
            s.get("missing_tables", 0),
            s.get("false_positive_tables", 0),
            run["pages_per_minute"],
            run["costs"]["effective_usd"],
        ]
        lines.append("| " + " | ".join(_fmt(v) for v in values) + " |")
    for run in runs:
        lines += ["", f"## {run['name']}", "", "Statuses: `" + json.dumps(run["statuses"], sort_keys=True) + "`.", ""]
        lines += [
            (
                f"Scope: {run['output_scope']}; text: {run['text_provenance']}; "
                f"source-conserved pages: {run['conserved_pages']}."
            ),
            "",
        ]
        lines += [
            (
                "| Group | Pages | Scored | Exact | Structure cells / expected | "
                "Text edits / reference chars | IoU >= 0.5 tables | Negative false-positive pages |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for field, groups in run["groups"].items():
            for name, s in groups.items():
                lines.append(
                    f"| {field}: {name} | {s['pages']} | {s['scored_pages']} | {s.get('exact_page', 0)} | "
                    f"{s.get('correct_structure_cells', 0)}/{s.get('expected_cells', 0)} | "
                    f"{s.get('text_edit_distance', 0)}/{s.get('reference_characters', 0)} | "
                    f"{s.get('localized_tables_iou_ge_0_5', 0)} | "
                    f"{s.get('false_positive_page', 0)}/{s.get('negative_page', 0)} |"
                )
        lines += [
            "",
            "Resources: `" + json.dumps(run["resources"], sort_keys=True) + "`.",
            "",
            "All-attempt API accounting: `" + json.dumps(run["costs"], sort_keys=True) + "`.",
            "",
        ]
        lines += [
            "",
            "Model configuration: `" + json.dumps(run["model_configuration"], sort_keys=True) + "`.",
            "",
            "| Actual request model | Retained bodies | Returned calls | Returned reported USD subtotal |",
            "|---|---:|---:|---:|",
        ]
        breakdown = run["actual_model_breakdown"]
        for model, values in breakdown["models"].items():
            subtotal = values["returned_provider_reported_usd"]["known_subtotal"]
            lines.append(
                f"| {model} | {values['retained_request_bodies']} | {values['returned_calls']} | {_fmt(subtotal)} |"
            )
            cache = {k: v for k, v in values["usage"].items() if "cache" in k}
            lines += ["", f"Provider cache fields for `{model}`: `" + json.dumps(cache, sort_keys=True) + "`.", ""]
        lines += ["", breakdown["scope"], ""]
        positive, negative = run["positive"], run["negative"]
        lines += [
            "",
            (
                f"Exact positive pages: {positive.get('exact_page', 0)}/{positive['scored_pages']}; "
                f"exact negative pages: {negative.get('exact_page', 0)}/{negative['scored_pages']}. "
                "All-page exact counts include successful empty outputs on negative pages."
            ),
            "",
        ]
        lines += [_macro_line(run["positive_macro"]), ""]
        legacy = run["authored_legacy_exact"]
        lines += [
            (
                f"Authored legacy exact pages: {legacy.get('exact_page', 0)}/{legacy['scored_pages']}. "
                "This scorer is applied only to authored references."
            ),
            "",
        ]
        lines += ["- " + caveat for caveat in run["comparison_caveats"]]
    return "\n".join(lines) + "\n"


def protocol_report(protocols: dict[str, list[dict[str, Any]]], *, pending: list[str] | None = None) -> str:
    """Keep reviewed protocol datasets separate in a compact progress artifact."""
    lines = [
        "# P002 natural-PDF generalization progress",
        "",
        (
            "Frozen runs with independently verified successful states, exact Markdown "
            "and explicit text provenance appear below. Missing/error pages remain in every scored denominator. "
            "Protocol groups use different frozen datasets and must not be pooled into one quality score. "
            "Timing/throughput cover page processing, excluding freeze/client setup and command startup; "
            "overlapping concurrent per-page CPU intervals are not additive."
        ),
        "",
    ]
    for label, runs in protocols.items():
        identities = {r["dataset_sha256"] for r in runs}
        if len(identities) > 1:
            raise ValueError("A progress protocol cannot combine different frozen datasets")
        lines += ["## " + label, "", "Dataset SHA-256: `" + next(iter(identities), "unmeasured") + "`.", ""]
        lines += [
            (
                "| Run | Verified / intended | Errors | Exact positive pages | Complete tables | Exact topology | "
                "Structure cells / expected | Exact text cells / expected | "
                "Text edits / reference chars | IoU >= 0.5 tables | "
                "Extra tables | Pages/min | Pages/API USD | Effective API USD |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in runs:
            s, positive = r["scores"], r["positive"]
            cells = f"{s.get('correct_structure_cells', 0)}/{s.get('expected_cells', 0)}"
            edits = f"{s.get('text_edit_distance', 0)}/{s.get('reference_characters', 0)}"
            values = [
                r["name"],
                f"{r['operational_pages']}/{r['intended_pages']}",
                r["all_errors"],
                f"{positive.get('exact_page', 0)}/{positive['scored_pages']}",
                s.get("complete_tables", 0),
                s.get("exact_table_spans", 0),
                cells,
                f"{s.get('correct_text_cells', 0)}/{s.get('expected_cells', 0)}",
                edits,
                s.get("localized_tables_iou_ge_0_5", 0),
                s.get("false_positive_tables", 0),
                r["pages_per_minute"],
                r["pages_per_dollar"],
                r["costs"]["effective_usd"],
            ]
            lines.append("| " + " | ".join(_fmt(v) for v in values) + " |")
        for r in runs:
            lines += ["", "### " + r["name"], ""]
            lines += [
                (
                    f"Scope: {r['output_scope']}; text: {r['text_provenance']}; "
                    f"source-conserved pages: {r['conserved_pages']}/{r['intended_pages']}."
                ),
                "",
            ]
            lines += [
                "Failure categories: `" + json.dumps(r["failure_taxonomy"]["counts"], sort_keys=True) + "`.",
                "",
            ]
            lines += [_macro_line(r["positive_macro"]), ""]
            density = r["posthoc_density"]
            if density is not None:
                lines += [
                    density["scope"],
                    "",
                    (
                        "| Posthoc group | Complete tables / expected | "
                        "Exact positive pages / positive pages | Exact text cells |"
                    ),
                    "|---|---:|---:|---:|",
                ]
                for density_label, ds in density["groups"].items():
                    lines.append(
                        f"| {density_label} | {ds.get('complete_tables', 0)}/{ds.get('expected_tables', 0)} | "
                        f"{ds.get('exact_positive_page', 0)}/{ds.get('positive_page', 0)} | "
                        f"{ds.get('correct_text_cells', 0)} |"
                    )
                lines += [""]
            config = r["config"]
            method = config.get("assembly_method", "select" if config.get("policy") == "gated" else "native")
            lines += [
                (
                    f"Policy `{config.get('policy')}`; assembly `{method}`; configured gate/selector "
                    f"`{config.get('model', 'unmeasured')}`; review `{config.get('gate_review_model', 'unmeasured')}`; "
                    f"generation `{config.get('generation_model', 'unmeasured')}`. "
                    "Actual request models are listed below; "
                    "a configured default does not prove it was called."
                ),
                "",
                (
                    "| Actual model | Retained request bodies | Returned calls | Returned reported USD subtotal | "
                    "Cached prompt observations: positive / zero / missing |"
                ),
                "|---|---:|---:|---:|---:|",
            ]
            for model, data in r["actual_model_breakdown"]["models"].items():
                cache = data["usage"]["prompt_tokens_details.cached_tokens"]
                subtotal = data["returned_provider_reported_usd"]["known_subtotal"]
                lines.append(
                    f"| {model} | {data['retained_request_bodies']} | {data['returned_calls']} | {_fmt(subtotal)} | "
                    f"{cache['reported_positive']} / {cache['reported_zero']} / {cache['missing_or_invalid']} |"
                )
            if not r["actual_model_breakdown"]["models"]:
                lines.append("| No retained remote requests | 0 | 0 | unmeasured | unmeasured |")
            lines += [
                "",
                (
                    "Per-model usage/cost are returned-call observations, including calls on failed pages. "
                    "All-attempt ledger costs in the summary include failures; per-model failed-attempt charges "
                    "remain unattributed when unavailable. Provider cache fields are literal observations, "
                    "with absent fields marked missing and no local inference cache."
                ),
                "",
                (
                    "| Cohort | Pages / scored | Complete tables | Exact topology | Structure cells / expected | "
                    "Text edits / reference chars | Negative false-positive pages |"
                ),
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
            for cohort, s in r["groups"]["cohort"].items():
                lines.append(
                    f"| {cohort} | {s['pages']}/{s['scored_pages']} | {s.get('complete_tables', 'unscored')} | "
                    f"{s.get('exact_table_spans', 'unscored')} | "
                    f"{s.get('correct_structure_cells', 'unscored')}/{s.get('expected_cells', 'unscored')} | "
                    f"{s.get('text_edit_distance', 'unscored')}/{s.get('reference_characters', 'unscored')} | "
                    f"{s.get('false_positive_page', 'unscored')}/{s.get('negative_page', 'unscored')} |"
                )
            m, costs = r["resources"], r["costs"]
            lines += [
                "",
                (
                    "Page-processing run wall (excludes freeze/client setup) "
                    f"{_fmt(m.get('wall_seconds'))}s; CPU {_fmt(m.get('cpu_seconds'))}s; "
                    f"sampled RSS {_fmt(m.get('peak_sampled_rss_bytes'))} bytes; "
                    f"verified output pages/min {_fmt(r['pages_per_minute'])}; "
                    f"exact positive pages/min {_fmt(r['exact_positive_pages_per_minute'])}. "
                    f"Measurement: {m.get('measurement', 'unmeasured')}. "
                    f"Per-run concurrency {_fmt(r['frozen_runtime'].get('concurrency'))}; "
                    f"logical CPUs {_fmt(r['frozen_runtime'].get('logical_cpus'))}."
                ),
                "",
                (
                    f"Ledger attempts {_fmt(costs['ledger_attempts'])}; reported USD subtotal "
                    f"{_fmt(costs['provider_reported_subtotal_usd'])}; missing reported charges "
                    f"{_fmt(costs['missing_provider_charge_count'])}; cost bases `{json.dumps(costs['cost_bases'])}`. "
                    f"Reservation amount {_fmt(costs['reservation_usd'])}; "
                    f"estimate amount {_fmt(costs['estimated_usd'])}."
                ),
                "",
            ]
            worker = m.get("layout_detector_worker")
            if worker is not None:
                initialization = worker["initialization"]["initialization"]
                requests = worker["requests"]
                cpu = _numeric_observations([request.get("cpu_seconds") for request in requests])["complete_total"]
                peaks = [request.get("peak_sampled_rss_bytes") for request in requests]
                valid_peaks = [v for v in peaks if isinstance(v, (int, float)) and not isinstance(v, bool)]
                lines += [
                    (
                        "Separate CPU detector worker: initialization wall "
                        f"{_fmt(initialization.get('wall_seconds'))}s, "
                        f"CPU {_fmt(initialization.get('cpu_seconds'))}s; "
                        f"{len(requests)} per-page measurement entries, "
                        f"request CPU total {_fmt(cpu)}s; maximum sampled request RSS "
                        f"{_fmt(max(valid_peaks) if valid_peaks else None)} bytes. " + worker["scope"]
                    ),
                    "",
                ]
    if pending:
        lines += ["## Pending completed reports", "", *["- " + name for name in pending], ""]
    lines += [
        "## Interpretation",
        "",
        (
            "Exact topology and character edits separate structural assembly from text agreement. "
            "Text edits are positional table text errors, not independent raster OCR CER; character "
            "inventory observations are diagnostics only. Low IoU >= 0.1 correspondences are not "
            "detection recall or AP. The stricter localization count uses IoU >= 0.5; legacy prediction "
            "boxes derive from owned text extents and can lie inside annotated table borders."
        ),
        "",
        (
            "Complete tables and exact positive pages use different units and denominators: "
            "two complete tables may occupy only one exact positive page. "
            "Negative-page empty outputs can be exact without recovering a positive table. "
            "Authored DEV silver, independently annotated Omni pages, and unscored native diagnostics "
            "remain separate. A protocol screen is a predeclared DEV experiment, not a heldout estimate. "
            "Runs with different packet, OCR, generation, image or region settings are not isolated "
            "causal comparisons. Concurrent background workloads may affect timings."
        ),
        "",
    ]
    return "\n".join(lines) + "\n"


def _fmt(value: object) -> str:
    if value is None:
        return "unmeasured"
    return f"{value:.6g}" if isinstance(value, float) else str(value).replace("|", "\\|")


def main() -> None:
    """Score explicitly named complete runs and write private JSON plus Markdown."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True, help="Output stem; writes .json and .md")
    args = parser.parse_args()
    manifest, targets = load_corpus(args.corpus)
    runs = [score_run(guard_path(path), args.corpus / "manifest.json", manifest, targets) for path in args.run]
    destination = guard_path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.with_suffix(".json").write_text(json.dumps({"schema": 1, "runs": runs}, indent=2) + "\n")
    destination.with_suffix(".md").write_text(markdown_report(runs))


if __name__ == "__main__":
    main()
