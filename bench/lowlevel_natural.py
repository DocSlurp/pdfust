"""Source-first natural DEV row ownership, with separately reviewed references."""

# ruff: noqa: ANN401, PLR2004
from __future__ import annotations

import argparse
import base64
import io
import json
import math
import time
from itertools import pairwise
from pathlib import Path
from typing import Any

from PIL import Image
from PIL import __version__ as pillow_version

import pdfust
from bench.lowlevel_evidence import _glyphs, digest, encode, write
from bench.lowlevel_evidence import request as original_request
from bench.lowlevel_images import MODELS, non_image_bytes
from bench.lowlevel_packets import _file
from bench.lowlevel_prompts import transform
from bench.silver import guard_path, rss_bytes

SCOPES = {"record": (80.0, 710.0), "description": (423.0, 682.0)}
EDGES = (512, 1200)
ARMS = tuple(f"{scope}-{edge}" for scope in SCOPES for edge in EDGES)
POLICY: dict[str, Any] = {
    "description_left": 425.0,
    "description_right": 680.0,
    "body_top": 130.0,
    "body_bottom": 540.0,
    "line_tolerance": 0.35,
    "maximum_adjacent_top_gap": 8.0,
    "context_vertical_padding": 18.0,
    "maximum_source_pages": 3,
    "selection": "first qualifying adjacent description baselines in page/top order; no semantic filter",
}
SOURCE_NOTE = {
    "source": "US Senate expenditure-report excerpt; bundled senate-expenditures.pdf",
    "license": "US government work, public domain; pdfplumber mirror repository MIT",
    "mirror": "https://github.com/jsvine/pdfplumber/blob/stable/tests/pdfs/senate-expenditures.pdf",
    "limitations": "Existing DEV fixture, one producer/document; prior region controls are not row-ownership gold",
}


def _lines(words: list[tuple]) -> list[list[tuple]]:
    selected = sorted(
        (
            word
            for word in words
            if POLICY["description_left"] <= word[0] < POLICY["description_right"]
            and POLICY["body_top"] <= word[1] <= POLICY["body_bottom"]
        ),
        key=lambda word: (word[1], word[0], word[4]),
    )
    lines: list[list[tuple]] = []
    for word in selected:
        if not lines or abs(word[1] - lines[-1][0][1]) > POLICY["line_tolerance"]:
            lines.append([])
        lines[-1].append(word)
    return lines


def select(pdf_bytes: bytes, *, count: int = 24) -> dict[str, Any]:
    """Select bounded pairs by geometry and sequence, never source semantics."""
    if not 12 <= count <= 24:
        message = "Natural DEV selection requires 12 to 24 pairs"
        raise ValueError(message)
    pairs = []
    source_hash = digest(pdf_bytes)
    with pdfust.Document(stream=pdf_bytes) as document:
        for page_index in range(min(len(document), POLICY["maximum_source_pages"])):
            lines = _lines(document[page_index].get_text("words"))
            for index, (first, second) in enumerate(pairwise(lines)):
                if second[0][1] - first[0][1] > POLICY["maximum_adjacent_top_gap"]:
                    continue
                boxes = [
                    [
                        POLICY["description_left"],
                        min(w[1] for w in line) - 0.15,
                        POLICY["description_right"],
                        max(w[3] for w in line) + 0.15,
                    ]
                    for line in (first, second)
                ]
                identity = digest(encode([source_hash, page_index, boxes]))[:16]
                pairs.append(
                    {
                        "id": identity,
                        "page_index": page_index,
                        "line_indices": [index, index + 1],
                        "target_boxes": boxes,
                    }
                )
                if len(pairs) == count:
                    break
            if len(pairs) == count:
                break
    if len(pairs) != count:
        message = "Complete geometry-selected cohort unavailable; refuse rather than fill from labels"
        raise ValueError(message)
    return {"schema": 1, "source_sha256": source_hash, "source_bytes": len(pdf_bytes), "policy": POLICY, "pairs": pairs}


def _atoms(glyphs: list[dict[str, Any]], boxes: list[list[float]]) -> list[list[dict[str, Any]]]:
    chunks = [
        [
            glyph
            for glyph in glyphs
            if box[0] <= glyph["origin"][0] + glyph["advance"] * 0.5 <= box[2]
            and box[1] <= glyph["origin"][1] <= box[3]
        ]
        for box in boxes
    ]
    ids = [glyph["id"] for chunk in chunks for glyph in chunk]
    if not all(chunks) or len(ids) != len(set(ids)):
        message = "Natural target chunks must be nonempty and disjoint"
        raise ValueError(message)
    return chunks


def _raster(page: Any, bbox: list[float], edge: int) -> dict[str, Any]:
    scale = edge / (bbox[2] - bbox[0])
    pixmap = page.get_pixmap(scale=scale, background=(255, 255, 255), clip=bbox)
    rgba = Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples)
    rgb = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")
    buffer = io.BytesIO()
    rgb.save(buffer, format="PNG", optimize=True)
    raw = buffer.getvalue()
    # The renderer rounds the clip outward; expose the actual pixel viewport.
    actual = [
        math.floor(bbox[0] * scale) / scale,
        math.floor(bbox[1] * scale) / scale,
        math.ceil(bbox[2] * scale) / scale,
        math.ceil(bbox[3] * scale) / scale,
    ]
    return {
        "bbox": actual,
        "requested_bbox": bbox,
        "pixels": list(rgb.size),
        "png_base64": base64.b64encode(raw).decode(),
        "sha256": digest(raw),
        "pixel_sha256": digest(rgb.tobytes()),
        "render_scale": scale,
        "render_dpi": scale * 72,
        "requested_horizontal_edge": edge,
        "method": "fresh source render; outward clip rounding; RGB PNG",
        "pillow_version": pillow_version,
    }


def _question(observation: dict[str, Any]) -> dict[str, Any]:
    # A tiny source-only temporary projection avoids materializing full-page text
    # into a bounded vision question. Chunks retain the actual glyph characters.
    source = {
        "selector": observation["selector"],
        "page_size": observation["page_size"],
        "words": [],
        "target_atoms": observation["target_atoms"],
    }
    return transform(original_request([source], MODELS[0], "minimal"), [source], "both")["questions"]["q0"]


def request(observation: dict[str, Any], model: str, arm: str) -> dict[str, Any]:
    """Build one matched multimodal source packet, with no scorer metadata."""
    if arm not in ARMS or model not in (*MODELS, "liquid/d1"):
        message = "Natural source request model or image treatment unadmitted"
        raise ValueError(message)
    image = observation["images"][arm]
    png = base64.b64decode(image["png_base64"], validate=True)
    if digest(png) != image["sha256"]:
        message = "Natural retained PNG changed"
        raise ValueError(message)
    source = {
        "task": "line_ownership",
        "target_boxes": observation["selector"]["target"]["boxes"],
        "chunks": [{"text": "".join(glyph["text"] for glyph in chunk)} for chunk in observation["target_atoms"]],
    }
    state = {"observations": {"q0": source}, "image_bbox": image["bbox"], "image_pixels": image["pixels"]}
    body = {
        "model": model,
        "state": [
            json.dumps(state, separators=(",", ":")),
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image["png_base64"]}},
        ],
        "questions": {"q0": _question(observation)},
    }
    if non_image_bytes(body) > 1800 or len(encode(body)) > 200000:
        message = "Natural complete source request exceeds byte admission; no truncation"
        raise ValueError(message)
    return body


def prepare(source: Path, directory: Path, *, count: int = 24) -> dict[str, Any]:
    """Freeze source selection, observations and question templates before labels."""
    source, directory = guard_path(source).resolve(), guard_path(directory).resolve()
    if directory.exists():
        message = "Preserve the existing natural source freeze"
        raise ValueError(message)
    started, cpu = time.perf_counter(), time.process_time()
    raw = source.read_bytes()
    selection = select(raw, count=count)
    directory.mkdir(parents=True)
    (directory / "source.pdf").write_bytes(raw)
    selection_hash = write(directory / "selection.json", selection)
    pages: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    with pdfust.Document(stream=raw) as document:
        cache = {}
        for pair in selection["pairs"]:
            page_index = pair["page_index"]
            page = document[page_index]
            if page_index not in cache:
                document._ensure_fallback_fonts()  # noqa: SLF001 - experiment hook.
                width, height, rows, skipped = document._doc.extract_glyph_snapshot(  # noqa: SLF001
                    page_index + 1, max_glyphs=16384, max_text_bytes=65536
                )
                document._emit_warnings()  # noqa: SLF001 - repeat public warning behavior.
                cache[page_index] = (width, height, _glyphs(rows), skipped)
            width, height, glyphs, skipped = cache[page_index]
            boxes = pair["target_boxes"]
            top = max(0.0, boxes[0][1] - POLICY["context_vertical_padding"])
            bottom = min(height, boxes[1][3] + POLICY["context_vertical_padding"])
            chunks = _atoms(glyphs, boxes)
            ids = [[glyph["id"] for glyph in chunk] for chunk in chunks]
            observation = {
                "page_size": [width, height],
                "selector": {"task": "line_ownership", "target": {"boxes": boxes}},
                "target_atoms": chunks,
                "candidates": {"join": [ids[0] + ids[1]], "split": ids, "unresolved": []},
                "skipped_no_unicode": skipped,
                "images": {
                    f"{scope}-{edge}": _raster(page, [left, top, right, bottom], edge)
                    for scope, (left, right) in SCOPES.items()
                    for edge in EDGES
                },
            }
            obsfile = f"observation-{pair['id']}.json"
            pages.append(
                {
                    "id": pair["id"],
                    "page_index": page_index,
                    "source_file": "source.pdf",
                    "source_sha256": selection["source_sha256"],
                    "observation_file": obsfile,
                    "observation_sha256": write(directory / obsfile, observation),
                }
            )
            for arm in ARMS:
                body = request(observation, MODELS[0], arm)
                filename = f"request-{len(records):04d}.json"
                records.append(
                    {
                        "request": filename,
                        "sha256": write(directory / filename, body),
                        "model": MODELS[0],
                        "arm": arm,
                        "page_ids": [pair["id"]],
                        "body_bytes": len(encode(body)),
                        "non_image_bytes": non_image_bytes(body),
                    }
                )
    manifest = {
        "schema": 1,
        "experiment": "L011-source",
        "pages": pages,
        "records": records,
        "source": SOURCE_NOTE,
        "source_sha256": selection["source_sha256"],
        "source_bytes": len(raw),
        "selection_sha256": selection_hash,
        "arms": list(ARMS),
        "annotation_status": "No labels read or constructed during source freezing",
        "code_sha256": digest(Path(__file__).read_bytes()),
        "preparation": {
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss_bytes(),
            "measurement": "serial current-process counters and VmHWM; no provider call",
        },
    }
    write(directory / "manifest.json", manifest)
    return manifest


def verify(directory: Path) -> dict[str, Any]:
    """Verify source-only selection, evidence integrity and exact template coverage."""
    directory = guard_path(directory).resolve()
    manifest = json.loads((directory / "manifest.json").read_bytes())
    raw = (directory / "source.pdf").read_bytes()
    selection_raw = (directory / "selection.json").read_bytes()
    selection = json.loads(selection_raw)
    if (
        digest(raw) != manifest["source_sha256"]
        or len(raw) != manifest["source_bytes"]
        or digest(selection_raw) != manifest["selection_sha256"]
        or select(raw, count=len(selection["pairs"])) != selection
    ):
        message = "Natural source or geometric selection changed"
        raise ValueError(message)
    expected_ids = [pair["id"] for pair in selection["pairs"]]
    if [page["id"] for page in manifest["pages"]] != expected_ids or manifest["arms"] != list(ARMS):
        message = "Natural source inventory changed"
        raise ValueError(message)
    observations = {}
    for page in manifest["pages"]:
        obsraw = _file(directory, page["observation_file"]).read_bytes()
        if (
            digest(obsraw) != page["observation_sha256"]
            or page["source_file"] != "source.pdf"
            or page["source_sha256"] != manifest["source_sha256"]
        ):
            message = "Natural observation changed"
            raise ValueError(message)
        observation = json.loads(obsraw)
        pair = selection["pairs"][expected_ids.index(page["id"])]
        if (
            page["page_index"] != pair["page_index"]
            or observation["selector"]["target"]["boxes"] != pair["target_boxes"]
        ):
            message = "Natural target selector differs from frozen source geometry"
            raise ValueError(message)
        observations[page["id"]] = observation
    seen = set()
    for record in manifest["records"]:
        if len(record["page_ids"]) != 1:
            message = "Natural templates require singleton question scope"
            raise ValueError(message)
        ident = record["page_ids"][0]
        identity = (ident, record["arm"])
        body = request(observations[ident], MODELS[0], record["arm"])
        raw_body = _file(directory, record["request"]).read_bytes()
        if (
            identity in seen
            or record["model"] != MODELS[0]
            or raw_body != encode(body)
            or digest(raw_body) != record["sha256"]
            or len(raw_body) != record["body_bytes"]
        ):
            message = "Natural source template changed or repeated"
            raise ValueError(message)
        seen.add(identity)
    if seen != {(ident, arm) for ident in expected_ids for arm in ARMS}:
        message = "Natural source templates incomplete"
        raise ValueError(message)
    return manifest


def annotate(directory: Path, references: list[dict[str, Any]]) -> dict[str, Any]:
    """Store separate source-aware reviewer labels after verifying frozen templates."""
    manifest = verify(directory)
    ids = {page["id"] for page in manifest["pages"]}
    if (
        len(references) != len(ids)
        or {ref.get("id") for ref in references} != ids
        or any(
            ref.get("choice") not in ("join", "split", "unresolved")
            or not ref.get("evidence")
            or not ref.get("uncertainty")
            for ref in references
        )
    ):
        message = "References require complete separate choices, evidence and uncertainty"
        raise ValueError(message)
    path = _file(guard_path(directory).resolve(), "private-references.json")
    if path.exists():
        message = "Preserve existing reviewed references"
        raise ValueError(message)
    result = {
        "schema": 1,
        "source_manifest_sha256": digest((directory / "manifest.json").read_bytes()),
        "annotation": "Single source-aware screenshot review; DEV references, not independently adjudicated gold",
        "references": references,
    }
    write(path, result)
    return result


def main() -> None:
    """Prepare and verify CPU-only source evidence; annotation is a separate step."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--count", type=int, default=24)
    args = parser.parse_args()
    manifest = prepare(args.source, args.directory, count=args.count)
    verify(args.directory)
    print(json.dumps({"pairs": len(manifest["pages"]), "templates": len(manifest["records"])}))


if __name__ == "__main__":
    main()
