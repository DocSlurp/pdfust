"""Freeze OCR1200/overlap0.5 image admission requests without hosted calls."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import resource
import time
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench.ocr_rolling import CORPUS, immutable, literal_recall, sha
from bench.ocr_rolling import OUTPUT as OCR_OUTPUT
from bench.silver import guard_path

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path("/home/dan/code/oss/pylopdf")
OUTPUT = ROOT / "bench/results/pdf-master-artifacts/ocr1200-overlap05-admission-v1"
MODELS = ("perplexity/pplx-decider-v1.1-27b", "openai/gpt-6-luna-decisions")
PAGE_COUNT = 28
MAX_EDGE = 1200


def source_page(observed: dict[str, Any], image: str, native: list[dict[str, Any]]) -> dict[str, Any]:
    """Retain each observed OCR chunk verbatim and map dimensions to a display rect."""
    words = [{key: word[key] for key in ("id", "text", "bbox")} for word in observed["words"]]
    if len({word["id"] for word in words}) != len(words):
        message = "OCR source inventory contains duplicate IDs"
        raise ValueError(message)
    return {
        "id": observed["id"],
        "words": words,
        "page_size": [0.0, 0.0, *observed["page_size"]],
        "image_path": image,
        "vector_candidates": native,
        "source_kind": "frozen_raster_OCR_regions",
        "ocr_observed_sha256": observed.get("observed_sha256"),
    }


def inventory_conserved(page: dict[str, Any], alternative: dict[str, Any]) -> bool:
    """Check retained ownership plus unresolved IDs against the complete OCR inventory."""
    owned = [
        identifier
        for table in alternative["candidates"]
        for cell in table["cells"]
        for identifier in cell["source_ids"]
    ]
    return Counter(owned + alternative["unresolved_ids"]) == Counter(word["id"] for word in page["words"])


def _factory(path: Path) -> ModuleType:
    """Load only the local source-only A002 body factory, without hosted-client imports."""
    spec = importlib.util.spec_from_file_location("ocr_admission_frozen_factory", path)
    if spec is None or spec.loader is None:
        message = "Cannot load frozen source-only admission factory"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(output: Path, source_root: Path = ROOT) -> dict[str, Any]:  # noqa: C901
    """Freeze both models' image512 bodies, retaining native controls separately."""
    output = guard_path(output)
    if (output / "manifest.json").exists():
        message = "Admission already frozen; use retained manifest or a new directory"
        raise ValueError(message)
    output.mkdir(parents=True, exist_ok=True)
    factory_bytes = guard_path(source_root / "bench/rolling_rows.py").read_bytes()
    factory_path = output / "admission-factory.py"
    factory_path.write_bytes(factory_bytes)
    factory = _factory(factory_path)
    source_observations = []
    native = {row["id"]: row["tables"] for row in json.loads((OCR_OUTPUT / "native-vector.json").read_text())}
    overlap = json.loads((OCR_OUTPUT / "overlap-a004-v1/frozen-candidates.json").read_text())
    overlap_map = {row["id"]: row for row in overlap if row["edge"] == MAX_EDGE}
    inputs = {
        row["id"]: row
        for row in json.loads((OCR_OUTPUT / "inputs.json").read_text())["pages"]
        if row["edge"] == MAX_EDGE
    }
    if len(inputs) != PAGE_COUNT or set(inputs) != set(overlap_map) or set(inputs) != set(native):
        message = "Complete original 28-page frozen source cohort is required"
        raise ValueError(message)
    pages, candidate_pages = [], []
    for identifier, image in inputs.items():
        directory = OCR_OUTPUT / "1200" / identifier
        observed_path = directory / "observed.json"
        observed = json.loads(observed_path.read_text())
        if sha(Path(image["image_path"])) != image["image_sha256"]:
            message = "Frozen source image hash mismatch"
            raise ValueError(message)
        if observed["words"] != overlap_map[identifier]["source_words"]:
            message = "A004 candidates differ from exact OCR observations"
            raise ValueError(message)
        observed["observed_sha256"] = sha(observed_path)
        page = source_page(observed, image["image_path"], native[identifier])
        base = json.loads((directory / "candidates.json").read_text())
        if base["observed_sha256"] != sha(observed_path):
            message = "Original candidate observation identity changed"
            raise ValueError(message)
        alternatives = [base["alternatives"]["physical"], overlap_map[identifier]["hypotheses"]["0.5"]]
        if not all(inventory_conserved(page, alternative) for alternative in alternatives):
            message = "Complete OCR source inventory is not conserved"
            raise ValueError(message)
        pages.append(page)
        candidate_pages.append({"id": identifier, "alternatives": alternatives})
        source_observations.append(
            {"id": identifier, "observed_sha256": sha(observed_path), "image_sha256": image["image_sha256"]}
        )
    source = {"pages": pages}
    immutable(output / "source-frozen.json", source)
    candidates = {"source_sha256": sha(output / "source-frozen.json"), "pages": candidate_pages}
    immutable(output / "candidates-frozen.json", candidates)
    began, cpu = time.perf_counter(), time.process_time()
    records = []
    for page, entry in zip(pages, candidate_pages, strict=True):
        if page["vector_candidates"]:
            records.append(
                {
                    "id": page["id"],
                    "route": "native_vector",
                    "calls": 0,
                    "native_selection": vars(factory)["_native_inventory"](page),
                }
            )
            continue
        for model_index, model in enumerate(MODELS):
            body = factory.admission_request(page, entry["alternatives"], model, with_image=True)
            name = f"{page['id']}-model{model_index}-image512.json"
            immutable(output / name, body)
            records.append(
                {
                    "id": page["id"],
                    "route": "hosted_admission",
                    "model": model,
                    "arm": "image512",
                    "request": name,
                    "sha256": sha(output / name),
                    "bytes": (output / name).stat().st_size,
                    "choices": list(body["questions"]["q0"]["criteria"]),
                }
            )
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    manifest = {
        "schema": 1,
        "source_sha256": sha(output / "source-frozen.json"),
        "frozen_candidates_sha256": sha(output / "candidates-frozen.json"),
        "models": list(MODELS),
        "arms": ["image512"],
        "pages": len(pages),
        "records": records,
        "wall_seconds": time.perf_counter() - began,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss,
        "measurement": "source-only request assembly; perf_counter/process_time; "
        "getrusage SELF process-lifetime RSS; single CPU process, no children, no periodic sampling",
        "provenance": {
            "ocr_max_edge": MAX_EDGE,
            "rolling_overlap_heights": 0.5,
            "factory_sha256": hashlib.sha256(factory_bytes).hexdigest(),
            "factory_source": str(source_root / "bench/rolling_rows.py"),
            "observations": source_observations,
            "prompt": "unchanged baseline A002 generic",
            "new_ocr_calls": 0,
            "paid_requests": 0,
        },
    }
    immutable(output / "manifest.json", manifest)
    return manifest


def report(output: Path) -> None:
    """Read original targets only after all bodies and menus have been frozen."""
    manifest = json.loads((output / "manifest.json").read_text())
    sources = json.loads((output / "source-frozen.json").read_text())["pages"]
    targets = {row["id"]: row for row in json.loads((CORPUS / "private-targets.json").read_text())}
    rows = []
    for page in sources:
        target = targets[page["id"]]
        expected = [value for table in target["tables"] for row in table["values"] for value in row if value]
        expected = expected or [target["prose"]]
        rows.append(
            {
                "id": page["id"],
                "kind": target["kind"],
                "original_token_recall": literal_recall(expected, [word["text"] for word in page["words"]]),
            }
        )
    (output / "private-original-token-recall.json").write_text(json.dumps(rows, indent=2))
    hosted = sum(row["route"] == "hosted_admission" for row in manifest["records"])
    native = sum(row["route"] == "native_vector" for row in manifest["records"])
    lines = [
        "# Frozen OCR1200 overlap0.5 admission combination",
        "",
        (
            f"All {manifest['pages']} original DEV pages retained: {native} native-vector zero-call controls "
            f"and {hosted} prepared image512 requests (24 pages × two models). No request has been sent."
        ),
        "",
        (
            "Source inventories are the immutable 1200-pixel OCR regions, with exact text, region IDs and display "
            "bboxes. Physical candidates remain frozen baseline; rolling candidates are the frozen A004 0.5-height "
            "overlap arm. Original whole-page rasters are downsampled to 512 pixels by the unchanged A002 body "
            "factory. The baseline generic q0 prompt and declared complete-candidate menu are unchanged. "
            "Native PDF vectors/text appear only in the four separate native routes, not hosted OCR evidence."
        ),
        "",
        "| Cohort | Original target-token recall |",
        "|---|---|",
    ]
    for kind in ("borderless", "prose", "ruled-control"):
        selected = [row for row in rows if row["kind"] == kind]
        matched = sum(row["original_token_recall"]["matched_tokens"] for row in selected)
        expected = sum(row["original_token_recall"]["expected_tokens"] for row in selected)
        lines.append(f"| {kind} | {matched}/{expected} |")
    lines.extend(
        [
            "",
            (
                "Original-token recall is a case-sensitive whitespace-token bag metric scored only after "
                "freezing. It is not CER, reading order, or independently annotated source-ID gold. Both retained "
                "alternatives conserve each OCR region exactly once across candidate cells and unresolved IDs. "
                "That inventory claim is separate from recall of original intended words or correct row ownership. "
                "The four native routes map OCR region centers to detected cells; ambiguous centers stay unresolved."
            ),
            "",
            (
                "Hosted quality and cost remain unmeasured. The rolling candidate ceiling previously reached 12/12 "
                "borderless tables, but proposed false tables on 12/12 prose pages; this combination measures "
                "whether admission can select or abstain from that frozen menu. Models are "
                "`perplexity/pplx-decider-v1.1-27b` and `openai/gpt-6-luna-decisions`."
            ),
            "",
            (
                f"Frozen manifest SHA256: `{sha(output / 'manifest.json')}`. "
                f"Request preparation: {manifest['wall_seconds']:.3f}s wall / {manifest['cpu_seconds']:.3f}s CPU; "
                f"{manifest['peak_rss_bytes'] / 2**20:.1f} MiB process-lifetime RSS. "
                f"Measurement: {manifest['measurement']}. Prior OCR costs are not included in these assembly timings."
            ),
            "",
            (
                f"Artifacts: `{output}`. Original targets remain at `{CORPUS / 'private-targets.json'}`. "
                "The manifest/source/candidate/request schema is compatible with the existing rolling_row_run "
                "verifier/evaluator. Raw observations, frozen bodies, menus and private recall outputs stay ignored. "
                "No hosted-client import, credentials, network call, training, GPU, or heldout access occurs."
            ),
            "",
        ]
    )
    (Path(__file__).parent / "results/ocr-admission.md").write_text("\n".join(lines))


def main() -> None:
    """Prepare frozen requests and optional separate original-word recall report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        manifest = prepare(args.output, args.source_root)
        print(f"Prepared {len(manifest['records'])} route records at {args.output}")
    if args.report:
        report(args.output)


if __name__ == "__main__":
    main()
