"""CPU-only, opt-in OCR source inventory and fixed natural-page DPI audit."""

# Bounded retained artifact schemas intentionally use explicit JSON dictionaries.
# ruff: noqa: C901, EM101, TRY003, PLC0415, PLR0912, PLR2004, ANN401
from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import platform
import resource
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any, Literal, cast

from bench.silver import guard_path, sha, write_json

ARTIFACTS = Path("/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002")
MAX_REGIONS = 8
MAX_REGION_PIXELS = 16_000_000
MAX_EMPTY_PIXELS = 64_000_000
MAX_CLONE_BYTES = 32 * 1024 * 1024
MAX_PARENT_PAGES = 4096
MAX_WORDS = 4096
SEED = "p002-ocr-natural-four-v1"


def _box(value: Any) -> list[float]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 4
        or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value)
        or value[2] <= value[0]
        or value[3] <= value[1]
    ):
        raise ValueError("Invalid positive display bbox")
    return list(value)


def _intersects(a: list[float], b: list[float]) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def _pixels(box: list[float], dpi: float) -> int:
    return math.ceil((box[2] - box[0]) * dpi / 72) * math.ceil((box[3] - box[1]) * dpi / 72)


def discover_regions(
    page_size: list[float], native: list[dict[str, Any]], placements: list[dict[str, Any]], dpi: float
) -> dict[str, Any]:
    """Admit only disjoint raster placements free of any retained native text."""
    if isinstance(dpi, bool) or not isinstance(dpi, (int, float)) or not math.isfinite(dpi) or dpi <= 0:
        raise ValueError("OCR DPI must be positive and finite")
    if len(native) > MAX_WORDS:
        raise ValueError("Native geometry collection exceeds admission")
    page = _box(page_size)
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    if len(placements) > 4096:
        raise ValueError("Image placement collection exceeds admission")
    for index, placement in enumerate(placements):
        box = _box(list(placement["bbox"]))
        clipped = [max(box[0], page[0]), max(box[1], page[1]), min(box[2], page[2]), min(box[3], page[3])]
        if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
            rejected.append({"placement": index, "reason": "outside_page"})
            continue
        if any(_intersects(clipped, word["bbox"]) for word in native):
            rejected.append({"placement": index, "reason": "native_text_intersection"})
            continue
        candidates.append({"placement": index, "bbox": clipped, "render_pixels": _pixels(clipped, dpi)})
    overlaps = {
        i
        for i, a in enumerate(candidates)
        for j, b in enumerate(candidates)
        if i != j and _intersects(a["bbox"], b["bbox"])
    }
    regions: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        if index in overlaps:
            rejected.append({"placement": candidate["placement"], "reason": "overlapping_image_placements"})
        else:
            regions.append(candidate)
    if len(regions) > MAX_REGIONS or sum(region["render_pixels"] for region in regions) > MAX_REGION_PIXELS:
        raise ValueError("Complete uncovered image regions exceed admission; no partial subset")
    return {"regions": regions, "rejected": rejected, "pixel_budget": MAX_REGION_PIXELS}


def whitespace_projection(recognized: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ablation only: split whitespace tokens using explicitly approximate geometry."""
    import re

    output: list[dict[str, Any]] = []
    for line, word in enumerate(recognized):
        text, box = word["text"], word["bbox"]
        for token in re.finditer(r"\S+", text):
            rotation = word.get("rotation", 0)
            start, end = token.start() / max(1, len(text)), token.end() / max(1, len(text))
            if rotation == 0:
                token_box = [box[0] + start * (box[2] - box[0]), box[1], box[0] + end * (box[2] - box[0]), box[3]]
            elif rotation == 180:
                token_box = [box[2] - end * (box[2] - box[0]), box[1], box[2] - start * (box[2] - box[0]), box[3]]
            elif rotation == 90:
                token_box = [box[0], box[3] - end * (box[3] - box[1]), box[2], box[3] - start * (box[3] - box[1])]
            else:
                token_box = [box[0], box[1] + start * (box[3] - box[1]), box[2], box[1] + end * (box[3] - box[1])]
            output.append(
                {
                    "id": f"w{len(output)}",
                    "text": token.group(),
                    "bbox": token_box,
                    "rotation": rotation,
                    "line": [0, line],
                    "geometry": "approximate uniform character advance; not recognized word boxes",
                }
            )
    return output


def _native_words(page: Any) -> list[dict[str, Any]]:
    return [
        {"id": f"w{i}", "text": word[4], "bbox": list(word[:4]), "line": list(word[5:7])}
        for i, word in enumerate(page.get_text("words"))
    ]


def _key(word: dict[str, Any]) -> tuple[Any, ...]:
    return (word["text"], *(round(float(coordinate), 3) for coordinate in word["bbox"]))


def extract(  # noqa: PLR0913 - experimental controls are explicit
    page: Any,
    mode: str = "empty",
    dpi: float = 150,
    *,
    engine: Any = None,
    tokenization: str = "reextract",
    orientation: str = "fixed",
) -> dict[str, Any]:
    """Return global source words and diagnostics, preserving the supplied document."""
    import pylopdf

    if orientation not in ("fixed", "candidates"):
        raise ValueError("Unknown OCR orientation mode")
    if tokenization not in ("reextract", "whitespace"):
        raise ValueError("Unknown OCR tokenization mode")
    if mode not in ("empty", "uncovered_images"):
        raise ValueError("Unknown OCR source mode")
    if isinstance(dpi, bool) or not isinstance(dpi, (int, float)) or not math.isfinite(dpi) or dpi <= 0:
        raise ValueError("OCR DPI must be positive and finite")
    native = _native_words(page)
    size = list(page.rect)
    if len(native) > MAX_WORDS:
        raise ValueError("Complete native word source exceeds admission")
    diagnostics: dict[str, Any] = {
        "orientation": orientation,
        "orientation_passes": [],
        "mode": mode,
        "tokenization": tokenization,
        "dpi": dpi,
        "native_word_count": len(native),
        "document_mutated": False,
        "recognized": [],
        "regions": [],
        "rejected_regions": [],
        "clone_serialized_bytes": 0,
    }
    source = {"page_size": size, "words": native}
    if mode == "empty" and native:
        diagnostics["status"] = "skipped_existing_native_text"
        return {"source": source, "diagnostics": diagnostics}
    regions: list[dict[str, Any]]
    if mode == "empty":
        if _pixels(size, dpi) > MAX_EMPTY_PIXELS:
            raise ValueError("Complete empty-page raster exceeds 64M pixel admission")
        regions = [{"bbox": size, "render_pixels": _pixels(size, dpi)}]
    else:
        discovered = discover_regions(size, native, page.get_images(), dpi)
        regions = discovered["regions"]
        diagnostics["rejected_regions"] = discovered["rejected"]
    diagnostics["regions"] = regions
    if not regions:
        diagnostics["status"] = "abstained_no_uncovered_image_regions"
        return {"source": source, "diagnostics": diagnostics}
    if orientation == "candidates" and sum(region["render_pixels"] for region in regions) * 4 > MAX_EMPTY_PIXELS:
        raise ValueError("Complete orientation region passes exceed pixel admission")
    if _pixels(size, dpi) > MAX_EMPTY_PIXELS:
        raise ValueError("Full-page render cost exceeds 64M pixel admission even for clipped regions")
    if len(page.parent) > MAX_PARENT_PAGES:
        raise ValueError("Parent document exceeds OCR clone page admission")
    # Import only the selected page; merge materializes inherited page attributes.
    clone_started = time.perf_counter()
    with pylopdf.Document() as owned:
        owned.insert_pdf(page.parent, from_page=page.number, to_page=page.number)
        diagnostics["clone_serialized_bytes"] = len(owned.tobytes(max_size=MAX_CLONE_BYTES))
        diagnostics["clone_seconds"] = time.perf_counter() - clone_started
        if list(owned[0].rect) != size or owned[0].rotation != page.rotation:
            raise ValueError("Selected-page clone changed display geometry")
        if Counter(_key(word) for word in _native_words(owned[0])) != Counter(_key(word) for word in native):
            raise ValueError("Selected-page clone changed native text inventory")
        recognized: list[dict[str, Any]] = []
        oriented_groups: list[tuple[int, list[dict[str, Any]]]] = []
        for region in regions:
            clip = None if mode == "empty" else region["bbox"]
            selected_rotation = 0
            if orientation == "candidates":
                from bench.pipeline_ocr_orientation import recognize

                trial = recognize(owned[0], dpi=dpi, engine=engine, clip=clip)
                diagnostics["orientation_passes"].append(trial)
                selected_rotation = trial["selected_rotation"]
                words = trial["words"]
            else:
                words = owned[0].get_text_ocr(dpi=dpi, engine=engine, clip=clip)
            admitted: list[dict[str, Any]] = []
            for ocr_word in words:
                box = _box(list(ocr_word["bbox"]))
                if any(_intersects(box, word["bbox"]) for word in native):
                    raise ValueError("OCR recognized box intersects retained native text")
                recognized.append(
                    {
                        "id": f"r{len(recognized)}",
                        "bbox": box,
                        "text": ocr_word["text"],
                        "confidence": ocr_word["confidence"],
                        "rotation": selected_rotation,
                    }
                )
                admitted.append(recognized[-1])
            if admitted:
                oriented_groups.append((selected_rotation, admitted))
        if len(recognized) > MAX_WORDS:
            raise ValueError("Complete recognized source exceeds admission")
        diagnostics["recognized"] = recognized
        if recognized and tokenization == "reextract":
            for rotation, group in oriented_groups:
                owned[0].insert_ocr_text_layer(
                    [(*word["bbox"], word["text"]) for word in group], rotation=cast(Literal[0, 90, 180, 270], rotation)
                )
        complete = _native_words(owned[0])
        if tokenization == "whitespace":
            block = max((word["line"][0] for word in native), default=-1) + 1
            for word in whitespace_projection(recognized):
                word["id"] = f"w{len(complete)}"
                word["recognized_line_id"] = f"r{word['line'][1]}"
                word["line"][0] = block
                complete.append(word)
    if len(complete) > MAX_WORDS:
        raise ValueError("Complete re-extracted source exceeds admission")
    native_counts = Counter(_key(word) for word in native)
    for word in complete:
        key = _key(word)
        if native_counts[key]:
            native_counts[key] -= 1
            word["origin"] = "native"
        else:
            word["origin"] = "ocr_reextracted" if tokenization == "reextract" else "ocr_whitespace_projection"
            if any(_intersects(word["bbox"], original["bbox"]) for original in native):
                raise ValueError("Re-extracted OCR geometry intersects native text")
    if any(native_counts.values()):
        raise ValueError("OCR insertion changed native source ownership")
    diagnostics.update(
        status="recognized" if recognized else "recognized_no_text",
        recognized_box_count=len(recognized),
        reextracted_word_count=len(complete) - len(native) if tokenization == "reextract" else None,
        ocr_source_word_count=len(complete) - len(native),
        whitespace_ablation=whitespace_projection(recognized),
        geometry_note=(
            "Whitespace mode uses approximate character-proportional boxes. "
            "Recognized boxes are line/text-run boxes; re-extracted word geometry comes from "
            "the constructed invisible layer, not independent OCR word localization."
        ),
    )
    source["words"] = complete
    return {"source": source, "diagnostics": diagnostics}


def select_four(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """One each of four layout strata, prioritizing new language then source metadata."""
    selected = []
    languages: set[str] = set()
    sources: set[str] = set()
    for layout in ("other_layout", "1andmore_column", "double_column", "single_column"):
        pool = sorted(
            [row for row in manifest["pages"] if row["diversity"]["attributes"]["layout"] == layout],
            key=lambda row: sha((SEED + row["id"]).encode()),
        )
        if not pool:
            raise ValueError("Required predeclared layout stratum unavailable")
        winner = max(
            pool,
            key=lambda row: (
                row["diversity"]["attributes"]["language"] not in languages,
                row["diversity"]["attributes"].get("data_source") not in sources,
            ),
        )
        languages.add(winner["diversity"]["attributes"]["language"])
        sources.add(winner["diversity"]["attributes"].get("data_source"))
        selected.append(winner)
    return selected


class Measurement:
    """Sample one CPU process's RSS at 100 ms; wall/CPU include clone and extraction."""

    def __enter__(self) -> Any:
        """Start process-only accounting and RSS sampling."""
        self.process = importlib.import_module("psutil").Process()
        self.samples = [self.process.memory_info().rss]
        self.stop = threading.Event()

        def sample() -> None:
            while not self.stop.wait(0.1):
                self.samples.append(self.process.memory_info().rss)

        self.thread = threading.Thread(target=sample, daemon=True)
        self.wall, self.cpu = time.perf_counter(), time.process_time()
        self.thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        """Stop sampling and retain complete extraction usage."""
        self.samples.append(self.process.memory_info().rss)
        self.stop.set()
        self.thread.join()
        self.summary = {
            "wall_seconds": time.perf_counter() - self.wall,
            "cpu_seconds": time.process_time() - self.cpu,
            "peak_sampled_rss_bytes": max(self.samples),
            "process_lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "measurement": (
                "psutil process RSS every100ms; process_time CPU; same process including four RTen threads, "
                "no child workers/GPU; lifetime RSS separate from sampled call peak"
            ),
        }
        self.summary["cpu_utilization_percent"] = self.summary["cpu_seconds"] / self.summary["wall_seconds"] * 100


def audit(directory: Path, dpi: int) -> None:
    """Freeze metadata selection before OCR; retain complete outputs without scoring input."""
    import pylopdf

    directory = guard_path(directory)
    output = directory / "ocr-evidence"
    output.mkdir(exist_ok=True)
    manifest = json.loads((directory / "screens/natural16/manifest.json").read_bytes())
    selected = select_four(manifest)
    frozen = {
        "schema": 1,
        "source_dataset_sha256": manifest["dataset_sha256"],
        "seed": SEED,
        "pages": selected,
        "selection": (
            "one each other/1andmore/double/single layout; prefer unseen language then source; "
            "frozen hash ties; no output/annotation selection"
        ),
    }
    path = output / "selection-frozen.json"
    if path.exists() and json.loads(path.read_bytes()) != frozen:
        raise ValueError("Existing OCR selection differs")
    write_json(path, frozen)
    result_path = output / f"cpu-{dpi}.json"
    if result_path.exists():
        raise ValueError("OCR measurement already retained")
    with Measurement() as initialization:
        engine = pylopdf.OcrEngine(threads=4, max_concurrent=1)
    rows = []
    for row in selected:
        try:
            with Measurement() as measured, pylopdf.Document(row["pdf_path"]) as document:
                result = extract(document[row["page_number"]], dpi=dpi, engine=engine)
            rows.append({"id": row["id"], "status": "ok", "output": result, "measurement": measured.summary})
        except Exception as error:
            rows.append({"id": row["id"], "status": "error", "error": str(error), "measurement": measured.summary})
        write_json(
            result_path,
            {
                "schema": 1,
                "dpi": dpi,
                "threads": 4,
                "max_concurrent": 1,
                "initialization": initialization.summary,
                "machine": platform.platform(),
                "logical_cpus": os.cpu_count(),
                "cpu_affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
                "rows": rows,
            },
        )


def main() -> None:
    """Run only the explicitly requested local CPU OCR audit scale."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ARTIFACTS)
    parser.add_argument("--dpi", type=int, choices=(150, 300), required=True)
    args = parser.parse_args()
    audit(args.directory, args.dpi)


if __name__ == "__main__":
    main()
