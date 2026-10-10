"""Independent source-only admission and pixel replay for frozen TATR acquisition arms."""

# ruff: noqa: EM101, TRY003, C901, PLR0912, PLC0415
from __future__ import annotations

import ast
import base64
import io
import json
from pathlib import Path
from typing import Any

from PIL import Image

import pylopdf
from bench.generalization_vision_regions import _crop
from bench.p003_gate_run import authenticate
from bench.silver import guard_path, sha

ACQUISITION_HASHES = {
    "fullpage": (
        "5a522394e5fcdcf9ad32e8169f98db26d572e3d7b44cfc4a694b70e008aea221",
        "e14e449415797ae702436281dda68fde6e8a047b51df440c87b9576123c19cf4",
    ),
    "residual": (
        "e37d0438b9a53fd42bf786c85550ac890a762df657ce82724c80be2c00729483",
        "8ff0566a319fcf287bdfdd0b3b345f2b5ce97cd6e5c90b2560bf8f5536f6fe70",
    ),
    "density": (
        "4e10577137bfc152e711efa6c7239863b4e6455eac4eed7783314e9b6792f063",
        "607e5a33e5795959d92e6b2a04eb0bdce26e2a6fec061d0f06f5b8d74ed95bd8",
    ),
}


REVIEWED_SOURCE_HELPERS = {
    "generalization_vision_regions.py": (
        "20ea20232c0fc3076293ed3c74a2018dcf7f02bada86da81c36c3ed238345230",
        {"transcription_request", "process"},
    ),
    "p003_region_candidates.py": (
        "450ecb92f5fd3d9a68e571159037f2f0df574770695d4595988ff74448b94d44",
        {"union_plans"},
    ),
}


def source_helper_matches(name: str, archived: bytes, current: bytes) -> bool:
    """Allow only root-reviewed unused branches from independently Git-anchored b11d896."""
    if archived == current:
        return True
    if name not in REVIEWED_SOURCE_HELPERS or sha(archived) != REVIEWED_SOURCE_HELPERS[name][0]:
        return False
    ignored_functions = REVIEWED_SOURCE_HELPERS[name][1]
    ignored_imports = (
        {
            ast.dump(ast.parse(statement).body[0], include_attributes=False)
            for statement in ("from copy import deepcopy", "from bench.silver import canonical, sha")
        }
        if name == "p003_region_candidates.py"
        else set()
    )

    def relevant(payload: bytes) -> list[str]:
        return [
            ast.dump(node, include_attributes=False)
            for node in ast.parse(payload).body
            if not (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ignored_functions)
            and ast.dump(node, include_attributes=False) not in ignored_imports
        ]

    return relevant(archived) == relevant(current)


def verify_acquisition(directory: Path, trusted_code: dict[str, str]) -> tuple[str, str, list[dict[str, Any]]]:
    """Recreate every crop's exact source membership, omitted proposals and JPEG bytes."""
    from bench import p003_structure_acquisition as acquisition
    from bench import p003_structure_density as density

    directory = guard_path(directory)
    source_path, report_path = directory / "source/manifest.json", directory / "geometry/report.json"
    manifest, report = json.loads(source_path.read_bytes()), json.loads(report_path.read_bytes())
    arm = manifest.get("acquisition_arm")
    if arm not in ACQUISITION_HASHES:
        raise ValueError("Unknown source-frozen acquisition arm")
    source_digest, report_digest = ACQUISITION_HASHES[arm]
    if sha(source_path.read_bytes()) != source_digest or sha(report_path.read_bytes()) != report_digest:
        raise ValueError("Independently announced acquisition hashes differ")
    required = {"p003_structure_geometry.py", "generalization_vision_regions.py"}
    required |= (
        {
            "p003_structure_density.py",
            "p003_structure_density_infer.py",
            "p003_region_candidates.py",
            "pipeline_regions.py",
        }
        if arm == "density"
        else {"p003_structure_acquisition.py", "p003_structure_acquisition_infer.py"}
    )
    if set(manifest["code_sha256"]) != required:
        raise ValueError("Incomplete source acquisition dependency inventory")
    code_directory = directory / "source/code" if arm == "density" else directory.parent / "code"
    reviews = []
    for name, digest in manifest["code_sha256"].items():
        archived = (code_directory / name).read_bytes()
        current = Path(__file__).with_name(name).read_bytes()
        if sha(archived) != digest or not source_helper_matches(name, archived, current):
            raise ValueError("Source acquisition replay helper differs from trusted working source")
        if archived != current:
            reviews.append(
                {
                    "helper": name,
                    "archived_sha256": digest,
                    "git_anchor": "b11d896",
                    "scope": "Root-reviewed unused branches; all used functions/constants retain exact AST",
                }
            )
    wrapper = "p003_structure_density_infer.py" if arm == "density" else "p003_structure_acquisition_infer.py"
    if report["inference_wrapper_sha256"] != manifest["code_sha256"][wrapper]:
        raise ValueError("Inference wrapper provenance differs")
    if sha((directory / "geometry/frozen-wrapper.py").read_bytes()) != report["inference_wrapper_sha256"]:
        raise ValueError("Archived inference wrapper differs")
    if (
        sha((directory / "geometry/inference-report-original.json").read_bytes())
        != report["original_inference_report_sha256"]
    ):
        raise ValueError("Historical geometry inference report differs")
    baseline = guard_path(Path(manifest["baseline"]))
    frozen, original = authenticate(baseline, trusted_code)
    records = {row["id"]: row for row in frozen["records"]}
    outputs = {row["id"]: row for row in original["results"]}
    ids = [page["id"] for page in manifest["pages"]]
    if ids != [row["id"] for row in frozen["records"]] or ids != [row["id"] for row in report["pages"]]:
        raise ValueError("Acquisition omits or changes source pages")
    inventories = []
    for page in manifest["pages"]:
        if page["record"] != records[page["id"]]:
            raise ValueError("Acquisition source record changed")
        source_bytes = (directory / "source" / page["source_path"]).read_bytes()
        source = json.loads(source_bytes)
        result = outputs[page["id"]]
        if sha(source_bytes) != page["source_sha256"] or source != result["source"]:
            raise ValueError("Acquisition source words differ from authenticated extraction")
        original_path = baseline / (page["id"] + "-result.json")
        if sha(original_path.read_bytes()) != page["baseline_result_sha256"]:
            raise ValueError("Acquisition baseline result provenance differs")
        if page["effective_rotation"] != result["effective_rotation"]:
            raise ValueError("Acquisition image rotation differs from authenticated source")
        if arm == "density":
            residuals = acquisition.proposals(source, result["region_plan"]["regions"], "residual")
            residual_ids = [identifier for proposal in residuals for identifier in proposal["source_ids"]]
            inventory = density.select(source, residual_ids)
            inventories.append({"id": page["id"], **inventory})
            proposals = [
                {
                    "region_id": proposal["proposal_id"],
                    "bbox": proposal["bbox"],
                    "source_ids": proposal["source_ids"],
                    "source_kind": "residual_source_line_gap_density",
                    "source_only_proposal_sha256": density.digest(density.encode(proposal)),
                }
                for proposal in inventory["accepted"]
            ]
            if page["no_candidate_reason"] != ("no retained aligned source tracks" if not proposals else None):
                raise ValueError("Density no-candidate evidence differs")
        else:
            proposals = acquisition.proposals(source, result["region_plan"]["regions"], arm)
            omitted = [proposal for proposal in proposals if proposal.get("status") == "no_owned_source_words"]
            if page["omitted_regions"] != omitted:
                raise ValueError("Residual no-word omission inventory differs")
            proposals = [proposal for proposal in proposals if proposal.get("status") != "no_owned_source_words"]
        if len(proposals) != len(page["crops"]):
            raise ValueError("Source acquisition crop inventory differs")
        if not proposals:
            continue
        pdf = guard_path(Path(page["record"]["pdf_path"]))
        if sha(pdf.read_bytes()) != page["record"]["pdf_sha256"]:
            raise ValueError("Acquisition PDF changed")
        with pylopdf.open(stream=pdf.read_bytes()) as document:
            pdf_page = document[page["record"]["page_number"]]
            pdf_page.set_rotation(page["effective_rotation"])
            raster = pdf_page.render(
                scale=4095 / max(pdf_page.rect.width, pdf_page.rect.height), background=(255, 255, 255)
            )
        with Image.open(io.BytesIO(raster)) as image:
            rgb = image.convert("RGB")
        for proposal, crop in zip(proposals, page["crops"], strict=True):
            url, metadata = _crop(rgb, list(source["page_size"]), proposal["bbox"], 1024, 90)
            name = f"{page['id']}-{proposal['region_id']}.jpg"
            expected = {**proposal, "image_path": name, **metadata}
            if crop != expected:
                raise ValueError(
                    "Source crop ownership or image coordinates differ from reconstruction: "
                    + str([key for key in crop.keys() | expected.keys() if crop.get(key) != expected.get(key)])
                )
            image_bytes = base64.b64decode(url.split(",", 1)[1], validate=True)
            if sha(image_bytes) != crop["image_sha256"] or image_bytes != (directory / "source" / name).read_bytes():
                raise ValueError("Source crop image pixels differ from independent rendering")
    if arm == "density" and json.loads((directory / "inventories.json").read_bytes()) != inventories:
        raise ValueError("Density raw proposal/order/overlap/cap omissions differ")
    return source_digest, report_digest, reviews
