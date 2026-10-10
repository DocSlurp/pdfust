"""Bounded residual source-line/gap acquisition, independent of quality labels."""

# ruff: noqa: EM101, TRY003
from __future__ import annotations

import argparse
import base64
import io
import json
import resource
import time
from pathlib import Path
from typing import Any

from PIL import Image

import pylopdf
from bench.generalization_vision_regions import _crop
from bench.p003_region_candidates import _ocr_regions
from bench.p003_structure_geometry import digest, encode
from bench.pipeline_repair import _sources
from bench.silver import guard_path

CAP = 8


def select(source: dict[str, Any], residual_ids: list[str]) -> dict[str, Any]:
    """Retain all proposals and bounded disjoint choices, never silently merge overlaps."""
    lookup = _sources(source)
    allowed = set(residual_ids)
    if len(allowed) != len(residual_ids) or allowed - set(lookup):
        raise ValueError("Invalid residual source ownership")
    words = [w for w in source["words"] if w["id"] in allowed]
    raw = _ocr_regions(words, source["page_size"])
    rows = []
    for index, candidate in enumerate(raw):
        box = candidate["bbox"]
        ids = [
            w["id"]
            for w in words
            if box[0] <= (w["bbox"][0] + w["bbox"][2]) / 2 < box[2]
            and box[1] <= (w["bbox"][1] + w["bbox"][3]) / 2 < box[3]
        ]
        rows.append({"proposal_id": f"g{index}", "source_ids": ids, **candidate})
    ordered = sorted(
        rows,
        key=lambda r: (
            -r["priority"],
            -r["evidence"]["physical_rows"],
            -len(r["source_ids"]),
            r["bbox"][1],
            r["bbox"][0],
            r["proposal_id"],
        ),
    )
    accepted: list[dict[str, Any]] = []
    decisions = []
    owned: set[str] = set()
    for row in ordered:
        box = row["bbox"]
        conflicts = [
            r["proposal_id"]
            for r in accepted
            if min(box[2], r["bbox"][2]) > max(box[0], r["bbox"][0])
            and min(box[3], r["bbox"][3]) > max(box[1], r["bbox"][1])
        ]
        reason = "accepted"
        if not row["source_ids"]:
            reason = "no_owned_words"
        elif conflicts or owned & set(row["source_ids"]):
            reason = "overlap_with_retained_proposal"
        elif len(accepted) >= CAP:
            reason = "page_cap8"
        else:
            accepted.append(row)
            owned.update(row["source_ids"])
        decisions.append(
            {"proposal_id": row["proposal_id"], "reason": reason, "conflicting_retained_proposals": conflicts}
        )
    return {
        "raw_proposals": rows,
        "ordering": [r["proposal_id"] for r in ordered],
        "decisions": decisions,
        "accepted": accepted,
        "residual_word_count": len(words),
        "owned_word_count": len(owned),
        "uncovered_residual_ids": [w["id"] for w in words if w["id"] not in owned],
        "cap": CAP,
        "selection_uses_references": False,
        "negative_cases": "Aligned prose/lists/charts can pass physical tracks; no semantic table gate is applied",
    }


def prepare(acquisition: Path, output: Path) -> dict[str, Any]:
    """Reuse independently authenticated residual snapshot and freeze density crops."""
    acquisition, output = guard_path(acquisition), guard_path(output)
    manifest_raw = (acquisition / "residual/source/manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest["acquisition_arm"] != "residual":
        raise ValueError("Expected full original residual acquisition")
    # Original source authentication/hash proof is archived by the parent preparation.
    proof = json.loads((acquisition / "report.json").read_bytes())
    if digest(manifest_raw) != proof["arms"]["residual"]["sha256"]:
        raise ValueError("Residual inventory differs from source freeze")
    output.mkdir(parents=True, exist_ok=False)
    directory = output / "source"
    directory.mkdir()
    code = directory / "code"
    code.mkdir()
    code_hashes = {}
    for name in (
        "p003_structure_density.py",
        "p003_structure_density_infer.py",
        "p003_structure_geometry.py",
        "p003_region_candidates.py",
        "pipeline_regions.py",
        "generalization_vision_regions.py",
    ):
        raw = Path(__file__).with_name(name).read_bytes()
        (code / name).write_bytes(raw)
        code_hashes[name] = digest(raw)
    (output / "frozen.json").write_bytes(
        encode(
            {
                "cap": CAP,
                "residual_manifest_sha256": digest(manifest_raw),
                "ranking": "priority,physicalrows,ownedwords descending; geometry/proposalID ties",
                "overlaps": "reject bbox orsourceID overlaps retaining fullreceipt",
                "line_gap_policy": (
                    "existing source-only OCR aligned tracks; >=3 physical rows, "
                    ">=2 aligned segments; windows4/8/16/32 plus complete track"
                ),
                "code_sha256": code_hashes,
                "references_read": False,
            }
        )
    )
    pages = []
    inventories = []
    started, cpu = time.perf_counter(), time.process_time()
    for page in manifest["pages"]:
        raw = (acquisition / "residual/source" / page["source_path"]).read_bytes()
        if digest(raw) != page["source_sha256"]:
            raise ValueError("Source snapshot differs")
        source = json.loads(raw)
        (directory / page["source_path"]).write_bytes(raw)
        ids = [i for crop in page["crops"] for i in crop["source_ids"]]
        inventory = select(source, ids)
        inventories.append({"id": page["id"], **inventory})
        crops = []
        if inventory["accepted"]:
            pdf_bytes = Path(page["record"]["pdf_path"]).read_bytes()
            if digest(pdf_bytes) != page["record"]["pdf_sha256"]:
                raise ValueError("Original source PDF changed")
            with pylopdf.open(stream=pdf_bytes) as doc:
                pdfpage = doc[page["record"]["page_number"]]
                pdfpage.set_rotation(page["effective_rotation"])
                raster = pdfpage.render(
                    scale=4095 / max(pdfpage.rect.width, pdfpage.rect.height), background=(255, 255, 255)
                )
            with Image.open(io.BytesIO(raster)) as image:
                rgb = image.convert("RGB")
            for candidate in inventory["accepted"]:
                url, meta = _crop(rgb, source["page_size"], candidate["bbox"], 1024, 90)
                data = base64.b64decode(url.split(",", 1)[1], validate=True)
                if digest(data) != meta["image_sha256"]:
                    raise ValueError("Crop bytes differ")
                name = f"{page['id']}-{candidate['proposal_id']}.jpg"
                (directory / name).write_bytes(data)
                crops.append(
                    {
                        "region_id": candidate["proposal_id"],
                        "bbox": candidate["bbox"],
                        "source_ids": candidate["source_ids"],
                        "image_path": name,
                        "source_kind": "residual_source_line_gap_density",
                        "source_only_proposal_sha256": digest(encode(candidate)),
                        **meta,
                    }
                )
        pages.append(
            {
                **{k: v for k, v in page.items() if k not in ("crops", "omitted_regions", "acquisition_arm")},
                "crops": crops,
                "acquisition_arm": "density",
                "no_candidate_reason": "no retained aligned source tracks" if not crops else None,
            }
        )
    value = {
        **{k: v for k, v in manifest.items() if k not in ("pages", "code_sha256", "selection", "acquisition_arm")},
        "pages": pages,
        "code_sha256": code_hashes,
        "selection": (
            "source-only residual aligned track proposals; max8 disjoint candidates/page; "
            "all raw overlap receipts retained"
        ),
        "acquisition_arm": "density",
        "parent_residual_manifest_sha256": digest(manifest_raw),
    }
    (directory / "manifest.json").write_bytes(encode(value))
    (output / "inventories.json").write_bytes(encode(inventories))
    report = {
        "pages": len(pages),
        "crops": sum(len(p["crops"]) for p in pages),
        "raw_proposals": sum(len(p["raw_proposals"]) for p in inventories),
        "owned_words": sum(p["owned_word_count"] for p in inventories),
        "residual_words": sum(p["residual_word_count"] for p in inventories),
        "source_manifest_sha256": digest(encode(value)),
        "references_read": False,
        "resources": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": "Linux selfgetrusage/process_time; oneCPUprocess; no RSSsampling; contended",
        },
    }
    (output / "report.json").write_bytes(encode(report))
    return report


def main() -> None:
    """Prepare only source-owned density proposals before local inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.acquisition, args.output)))


if __name__ == "__main__":
    main()
