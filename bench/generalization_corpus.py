"""Freeze a broad P002 DEV corpus before extraction; public research inputs only."""

# Artifact contracts deliberately use explicit heterogeneous dictionaries.
# ruff: noqa: C901, E501, EM101, TRY003, PLC0415, PLR0912, PLR0913, PERF401
from __future__ import annotations

import argparse
import json
import re
import resource
import time
import zlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from bench.feature_cases import stream_object, text_op
from bench.omnidoc_sample import REVISION, SOURCE, fetch
from bench.omnidoc_training import features
from bench.pipeline_corpus import LABEL, _table
from bench.silver import canonical, guard_path, sha, write_json
from bench.silver_layouts import _pdf, _serialize

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path("/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/pipeline-p002")
SEED = "jev-pdf-p002-generalization-v1"
FAMILIES = (
    "ruled",
    "borderless",
    "mixed",
    "multiple",
    "dense",
    "wrapped",
    "blank",
    "merged",
    "rotated",
    "cropped",
    "decorative",
    "prose",
    "ocr-carrier",
)


def parent_group(identifier: str) -> str | None:
    """Infer numbered filename parents, including dataset PDF-page naming forms."""
    match = re.match(r"^(.*?)(?:_page_|\.pdf_)(\d+)\.[^.]+$", identifier)
    return match[1] if match else None


def excluded_ids() -> tuple[set[str], dict[str, str]]:
    """Read only the explicitly named tracked DEV and TRAINING registries."""
    excluded: set[str] = set()
    hashes = {}
    for name in ("omnidoc-dev", "omnidoc-training"):
        path = ROOT / "bench" / name / "registry.json"
        raw = path.read_bytes()
        hashes[name] = sha(raw)
        excluded.update(row["id"] for row in json.loads(raw)["rows"])
    return excluded, hashes


def select_rows(rows: list[dict[str, Any]], excluded: set[str]) -> list[dict[str, Any]]:
    """Freeze 16 multiple-table, 24 single-table and 24 zero-table metadata selections."""
    groups = {parent_group(identifier) for identifier in excluded} - {None}
    eligible = [
        r
        for r in rows
        if r["page_info"]["image_path"] not in excluded and parent_group(r["page_info"]["image_path"]) not in groups
    ]
    if len({r["page_info"]["image_path"] for r in eligible}) != len(eligible):
        raise ValueError("Duplicate source image identifiers")
    selected = []
    covered: set[str] = set()
    for minimum, maximum, quota in ((2, 1000, 16), (1, 1, 24), (0, 0, 24)):
        pool = sorted(
            [r for r in eligible if minimum <= sum(b["category_type"] == "table" for b in r["layout_dets"]) <= maximum],
            key=lambda r: sha((SEED + r["page_info"]["image_path"]).encode()),
        )
        for _ in range(quota):
            candidates = [r for r in pool if parent_group(r["page_info"]["image_path"]) not in groups]
            if not candidates:
                raise ValueError("Insufficient disjoint rows for fixed metadata quotas")
            winner = max(candidates, key=lambda r: len(features(r) - covered))
            selected.append(winner)
            pool.remove(winner)
            covered.update(features(winner))
            group = parent_group(winner["page_info"]["image_path"])
            if group is not None:
                groups.add(group)
    return selected


def acquire(directory: Path, annotation_path: Path | None = None) -> list[dict[str, Any]]:
    """Freeze selection before public image acquisition; never use recognition answers."""
    directory = guard_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    raw = (
        guard_path(annotation_path).read_bytes()
        if annotation_path
        else fetch("OmniDocBench.json", directory / "OmniDocBench.json")
    )
    (directory / "OmniDocBench.json").write_bytes(raw)
    excluded, registries = excluded_ids()
    rows = select_rows(json.loads(raw), excluded)
    selection = {
        "schema": 1,
        "split": "DEV",
        "seed": SEED,
        "revision": REVISION,
        "annotation_sha256": sha(raw),
        "exclusion_registry_sha256": registries,
        "source_ids": [r["page_info"]["image_path"] for r in rows],
        "recognition_answers_used_for_selection": False,
    }
    frozen = directory / "selection-frozen.json"
    if frozen.exists() and json.loads(frozen.read_bytes()) != selection:
        raise ValueError("Existing frozen selection differs")
    write_json(frozen, selection)
    fetch("README.md", directory / "dataset-card.md")

    def download(row: dict[str, Any]) -> None:
        identifier = row["page_info"]["image_path"]
        if Path(identifier).name != identifier:
            raise ValueError("Source image identifier must be a basename")
        fetch("images/" + identifier, directory / "images" / identifier)

    # Four public downloads only; no CPU inference concurrency or credentials.
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(download, rows))
    return rows


def image_pdf(image_path: Path, width: float, height: float) -> bytes:
    """Wrap RGB pixels losslessly; this is an image carrier, never an original PDF."""
    from PIL import Image

    with Image.open(image_path) as image:
        rgba = image.convert("RGBA")
        rgb = Image.new("RGB", image.size, "white")
        rgb.paste(rgba, mask=rgba.getchannel("A"))
        pixels, dimensions = rgb.tobytes(), rgb.size
    return _serialize(
        [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /XObject << /Im1 5 0 R >> >> /Contents 4 0 R >>",
            stream_object(f"q {width} 0 0 {height} 0 0 cm /Im1 Do Q"),
            stream_object(
                zlib.compress(pixels),
                f"/Type /XObject /Subtype /Image /Width {dimensions[0]} /Height {dimensions[1]} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode",
            ),
        ],
        "1.7",
    )


def authored_cases() -> list[dict[str, Any]]:
    """Declare 156 new operator-level designs and references together, without extraction."""
    cases = []
    for family_index, family in enumerate(FAMILIES):
        for variant in range(12):
            ops = [text_op(f"Operations report {family_index * 100 + variant + 101}", 44, 748, size=17)]
            references = []
            table_count = 2 if family in ("mixed", "multiple") else 1
            if family in ("prose", "decorative"):
                table_count = 0
                for col in range(2 + variant % 2):
                    for row in range(13):
                        ops.append(
                            text_op(
                                f"Field {row + 1} observed {17 + variant} samples",
                                42 + col * 183,
                                695 - row * 29,
                                size=8,
                            )
                        )
                if family == "decorative":
                    ops += ["0.6 G 36 720 m 580 720 l S", "40 200 520 515 re S"]
                    ops += [f"{52 + j * 35} 198 m {75 + j * 35} 716 l S" for j in range(13)]
            for ti in range(table_count):
                rows = 18 + variant % 5 if family == "dense" else 4 + variant % 4
                cols = 7 + variant % 3 if family == "dense" else 3 + variant % 3
                size = 6 if family == "dense" else 8 + variant % 3
                top = 705 - ti * 320
                lead = 23 if family == "dense" else 33
                wrapped = family == "wrapped"
                if wrapped:
                    lead = 48
                width = 510 / cols
                values: list[list[str | None]] = [[f"Column {c + 1}" for c in range(cols)]]
                values += [
                    [f"Record {r + 1}" if c == 0 else f"{(r + 3) * (c + 2) + variant}.{r % 10}" for c in range(cols)]
                    for r in range(rows - 1)
                ]
                if wrapped:
                    for r in range(1, rows):
                        values[r][0] = f"Record {r + 1} extended description"
                if family == "blank":
                    for r in range(1, rows):
                        values[r][(r + variant) % cols] = ""
                merges = ((0, 0, 1, 2),) if family == "merged" else ()
                if merges:
                    values[0][0] = "Combined header"
                target = _table(values, merges)
                target["bbox"] = [44, 792 - top, 554, 792 - top + rows * lead]
                references.append(target)
                ruled = family != "borderless" and not (family == "mixed" and ti == 1)
                if ruled:
                    for r in range(rows + 1):
                        y = top - r * lead
                        ops.append(f"44 {y} m 554 {y} l S")
                    for c in range(cols + 1):
                        x = 44 + c * width
                        start = top - lead if merges and c == 1 else top
                        ops.append(f"{x} {start} m {x} {top - rows * lead} l S")
                for r, cells in enumerate(target["values"]):
                    for c, value in enumerate(cells):
                        if not value:
                            continue
                        fragments = (
                            [value.split(" extended ")[0], "extended description"]
                            if wrapped and r and c == 0
                            else [value]
                        )
                        for line, fragment in enumerate(fragments):
                            ops.append(text_op(fragment, 48 + c * width, top - r * lead - 17 - line * 12, size=size))
            ops.append(text_op("Reviewed figures are provisional.", 44, 80, size=10))
            pdf_family = "rotated-page" if family == "rotated" else "cropped-page" if family == "cropped" else family
            data = _pdf(["\n".join(ops)], variant, pdf_family, "1.7")
            rotation = (variant % 3 + 1) * 90 if family == "rotated" else 0
            # Geometry changes with rotation/crop; omit bbox rather than attach incorrect coordinates.
            if family in ("rotated", "cropped"):
                for target in references:
                    target.pop("bbox")
            cases.append(
                {
                    "name": f"{family}-{variant:02}",
                    "family": family,
                    "pdf": data,
                    "tables": references,
                    "diversity": {
                        "variant": variant,
                        "rotation": rotation,
                        "crop": family == "cropped",
                        "table_count": len(references),
                        "construction": "new P002 operator layouts; shared basic PDF serializer only",
                    },
                }
            )
    return cases


def native_pages(count: int = 56) -> list[dict[str, Any]]:
    """Select native diagnostics round-robin by source; licenses come from bundled attribution."""
    import pylopdf

    base = ROOT / "tests/assets/real_world"
    readme = (base / "README.md").read_text()
    candidates = []
    for line in readme.splitlines():
        match = re.match(r"\| `([^`]+\.pdf)` \| (.*?) \| (.*?) \| (.*?) \|", line)
        if not match:
            continue
        name, source, license_text, coverage = match.groups()
        path = base / name
        with pylopdf.Document(path) as document:
            pages = len(document)
        candidates.append(
            {
                "path": path,
                "name": name,
                "page_count": pages,
                "source": source,
                "license": license_text,
                "coverage": coverage,
            }
        )
    result = []
    for page in range(max(c["page_count"] for c in candidates)):
        for item in candidates:
            if page < item["page_count"]:
                result.append({**item, "page_number": page})
                if len(result) == count:
                    return result
    raise ValueError("Insufficient distinct licensed diagnostic pages")


def build(directory: Path, omni_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Freeze sources, private targets, attribution and identity before any extraction run."""
    import pylopdf
    from bench.generalization_scoring import parse_annotation_html

    directory = guard_path(directory)
    if (directory / "manifest.json").exists():
        raise ValueError("Corpus manifest already frozen; choose a fresh directory")
    pdfs = directory / "pdfs"
    pdfs.mkdir(parents=True, exist_ok=True)
    pages, targets, provenance = [], [], []

    def add(
        data: bytes,
        name: str,
        family: str,
        tables: list[dict[str, Any]],
        *,
        cohort: str,
        input_kind: str,
        scored: bool = True,
        page: int = 0,
        diversity: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        digest = sha(data)
        path = pdfs / (digest + ".pdf")
        path.write_bytes(data)
        identifier = "p" + sha(canonical([SEED, name, page]))[:20]
        pages.append(
            {
                "id": identifier,
                "pdf_path": str(path),
                "pdf_sha256": digest,
                "page_number": page,
                "family": family,
                "cohort": cohort,
                "input_kind": input_kind,
                "label_status": LABEL
                if cohort == "authored"
                else "official public annotation"
                if scored
                else "diagnostic-only incomplete references",
                "diversity": diversity or {},
                "pilot": False,
            }
        )
        targets.append({"id": identifier, "tables": tables, "structural_scored": scored})
        provenance.append({"id": identifier, "source_case": name, **(details or {})})

    for case in authored_cases():
        data = case["pdf"]
        kind = "authored_native_pdf"
        if case["family"] == "ocr-carrier":
            with pylopdf.Document(stream=data) as document:
                png = document[0].render(dpi=120)
            image = directory / (case["name"] + ".png")
            image.write_bytes(png)
            data = image_pdf(image, 612, 792)
            kind = "authored_raster_image_carrier"
        add(
            data,
            "authored/" + case["name"],
            "authored/" + case["family"],
            case["tables"],
            cohort="authored",
            input_kind=kind,
            diversity=case["diversity"],
            details={
                "license": "Repository-authored; repository license",
                "reference_basis": "construction operators and authored cell matrices",
            },
        )
    for item in native_pages():
        add(
            item["path"].read_bytes(),
            "native/" + item["name"],
            "native/" + item["name"],
            [],
            cohort="native-diagnostic",
            input_kind="original_native_pdf_or_original_scan",
            scored=False,
            page=item["page_number"],
            details={key: item[key] for key in ("source", "license", "coverage")},
        )
    annotations = directory / "annotations"
    annotations.mkdir(exist_ok=True)
    for index, row in enumerate(omni_rows):
        info = row["page_info"]
        identifier = info["image_path"]
        image = directory / "images" / identifier
        annotation = annotations / (identifier + ".json")
        write_json(annotation, row)
        tables, errors = [], []
        blocks = [b for b in row["layout_dets"] if b["category_type"] == "table"]
        for block in blocks:
            parsed = parse_annotation_html(block.get("html", ""))
            if not parsed["structural_scored"] or block.get("ignore", False):
                errors.extend(parsed.get("annotation_errors", []) or ["Ignored table annotation"])
            for table in parsed["tables"]:
                poly = block["poly"]
                table["bbox"] = [
                    min(poly[::2]) * 0.36,
                    min(poly[1::2]) * 0.36,
                    max(poly[::2]) * 0.36,
                    max(poly[1::2]) * 0.36,
                ]
                tables.append(table)
        diversity = {
            "attributes": info["page_attribute"],
            "category_counts": dict(Counter(b["category_type"] for b in row["layout_dets"])),
            "table_count": len(blocks),
            "selection_index": index,
        }
        add(
            image_pdf(image, info["width"] * 0.36, info["height"] * 0.36),
            "omni/" + identifier,
            "omni/" + ("multiple-table" if len(blocks) > 1 else "single-table" if blocks else "no-table"),
            tables,
            cohort="omnidoc",
            input_kind="official_page_image_in_lossless_pdf_carrier",
            scored=not errors,
            diversity=diversity,
            details={
                "source": SOURCE,
                "revision": REVISION,
                "source_id": identifier,
                "image_sha256": sha(image.read_bytes()),
                "annotation_sha256": sha(canonical(row)),
                "annotation_path": str(annotation),
                "source_parent_group": parent_group(identifier),
                "parent_separation_limit": "Unknown filename parents cannot establish document-level separation",
                "annotation_errors": errors,
                "license": "Research purposes only; not for commercial use",
                "license_source": f"{SOURCE}/blob/{REVISION}/README.md",
                "original_native_pdf_available": False,
            },
        )
        targets[-1]["annotation_path"] = str(annotation)
        targets[-1]["annotation_errors"] = errors
    # Fixed first occurrences within each authored family plus metadata-ordered Omni quotas.
    family_seen: Counter[str] = Counter()
    for page in pages:
        family = page["family"]
        quota = 2 if page["cohort"] == "authored" else 2 if page["cohort"] == "omnidoc" else 0
        page["pilot"] = family_seen[family] < quota
        family_seen[family] += 1
    identity = sha(
        canonical(
            {
                "schema": 1,
                "pages": [{k: v for k, v in p.items() if k != "pdf_path"} for p in pages],
                "targets": [{k: v for k, v in t.items() if k != "annotation_path"} for t in targets],
            }
        )
    )
    manifest = {
        "schema": 1,
        "split": "DEV",
        "dataset_sha256": identity,
        "path_convention": "absolute",
        "pages": pages,
        "model_fields": ["id", "pdf_path", "pdf_sha256", "page_number"],
        "pilot_policy": "Two first construction variants per authored family and two metadata-selected rows per Omni table-density cohort; 32 pages; source/family/targets excluded from model evidence",
        "selection_seed": SEED,
    }
    write_json(directory / "private-targets.json", {"schema": 1, "dataset_sha256": identity, "pages": targets})
    write_json(directory / "private-provenance.json", provenance)
    write_json(directory / "manifest.json", manifest)
    return manifest


def white_alpha_revision(directory: Path) -> dict[str, Any]:
    """Preserve r1 and freeze r2 correcting only transparent authored carrier compositing."""
    directory = guard_path(directory)
    base = json.loads((directory / "manifest.json").read_bytes())
    references = json.loads((directory / "private-targets.json").read_bytes())
    provenance = json.loads((directory / "private-provenance.json").read_bytes())
    destination = directory / "corpus-r2"
    pdfs = destination / "pdfs"
    pdfs.mkdir(parents=True, exist_ok=True)
    if (destination / "manifest.json").exists():
        raise ValueError("White-alpha corpus revision already frozen")
    source_map = {row["id"]: row for row in provenance}
    changed = []
    for page in base["pages"]:
        if page["family"] != "authored/ocr-carrier":
            continue
        name = source_map[page["id"]]["source_case"].split("/")[-1]
        data = image_pdf(directory / (name + ".png"), 612, 792)
        digest = sha(data)
        path = pdfs / (digest + ".pdf")
        path.write_bytes(data)
        changed.append({"id": page["id"], "previous_pdf_sha256": page["pdf_sha256"], "pdf_sha256": digest})
        page["pdf_path"] = str(path)
        page["pdf_sha256"] = digest
        source_map[page["id"]]["revision_note"] = (
            "r2 composites rendered RGBA onto white before RGB image wrapping; r1 lost transparency against black"
        )
    identity = sha(
        canonical(
            {
                "schema": 1,
                "parent_dataset_sha256": base["dataset_sha256"],
                "pages": [{key: value for key, value in row.items() if key != "pdf_path"} for row in base["pages"]],
                "targets": [
                    {key: value for key, value in row.items() if key != "annotation_path"}
                    for row in references["pages"]
                ],
            }
        )
    )
    manifest = {
        **base,
        "dataset_sha256": identity,
        "parent_dataset_sha256": base["dataset_sha256"],
        "revision": "r2-white-alpha",
        "revision_changes": changed,
    }
    references["dataset_sha256"] = identity
    write_json(destination / "private-targets.json", references)
    write_json(destination / "private-provenance.json", provenance)
    write_json(destination / "manifest.json", manifest)
    return manifest


def natural_screen(directory: Path) -> dict[str, Any]:
    """Freeze a second metadata-only 16-page natural screen without changing the base pilot."""
    directory = guard_path(directory)
    base = json.loads((directory / "manifest.json").read_bytes())
    references = json.loads((directory / "private-targets.json").read_bytes())
    target_map = {row["id"]: row for row in references["pages"]}
    destination = directory / "screens" / "natural16"
    destination.mkdir(parents=True, exist_ok=True)
    if (destination / "manifest.json").exists():
        raise ValueError("Natural screen already frozen")
    selected = []
    covered: set[str] = set()
    for family, quota in (("multiple-table", 6), ("single-table", 6), ("no-table", 4)):
        pool = sorted(
            [row for row in base["pages"] if row["family"] == "omni/" + family],
            key=lambda row: sha((SEED + "/natural16/" + row["id"]).encode()),
        )
        for _ in range(quota):

            def diversity(row: dict[str, Any]) -> set[str]:
                metadata = row["diversity"]
                return {
                    *(f"{key}:{value}" for key, value in metadata["attributes"].items()),
                    *("category:" + category for category in metadata["category_counts"]),
                }

            winner = max(pool, key=lambda row: len(diversity(row) - covered))
            pool.remove(winner)
            covered.update(diversity(winner))
            selected.append({**winner, "pilot": True})
    targets = [target_map[row["id"]] for row in selected]
    identity = sha(
        canonical(
            {
                "schema": 1,
                "source_dataset_sha256": base["dataset_sha256"],
                "screen": "natural16",
                "pages": [{key: value for key, value in row.items() if key != "pdf_path"} for row in selected],
                "targets": [{key: value for key, value in row.items() if key != "annotation_path"} for row in targets],
            }
        )
    )
    manifest = {
        **base,
        "dataset_sha256": identity,
        "source_dataset_sha256": base["dataset_sha256"],
        "pages": selected,
        "pilot_policy": "Second predeclared screen: six multiple-table, six single-table and four no-table Omni pages; greedy metadata diversity; frozen hash ties; no extraction outputs used",
    }
    write_json(destination / "private-targets.json", {"schema": 1, "dataset_sha256": identity, "pages": targets})
    source_provenance = json.loads((directory / "private-provenance.json").read_bytes())
    write_json(
        destination / "private-provenance.json",
        [row for row in source_provenance if row["id"] in {page["id"] for page in selected}],
    )
    write_json(destination / "manifest.json", manifest)
    return manifest


def main() -> None:
    """Acquire and freeze ignored research artifacts with measured CPU-only build usage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ARTIFACTS)
    parser.add_argument("--annotation-path", type=Path)
    parser.add_argument("--acquire-only", action="store_true")
    parser.add_argument("--natural-screen", action="store_true")
    parser.add_argument("--white-alpha-revision", action="store_true")
    args = parser.parse_args()
    if args.natural_screen or args.white_alpha_revision:
        manifest = natural_screen(args.directory) if args.natural_screen else white_alpha_revision(args.directory)
        print(json.dumps({"dataset_sha256": manifest["dataset_sha256"], "pages": len(manifest["pages"])}))
        return
    start, cpu = time.perf_counter(), time.process_time()
    rows = acquire(args.directory, args.annotation_path)
    manifest = None if args.acquire_only else build(args.directory, rows)
    usage = {
        "elapsed_seconds": time.perf_counter() - start,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "measurement": "Linux getrusage RUSAGE_SELF lifetime peak RSS; process_time CPU; one CPU process, four public-download threads, no children/GPU/inference; no utilization sampling",
        "pages": len(manifest["pages"]) if manifest else None,
    }
    write_json(args.directory / "build-usage.json", usage)
    print(json.dumps(usage))


if __name__ == "__main__":
    main()
