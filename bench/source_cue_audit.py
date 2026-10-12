"""Freeze a source-only DEV ablation removing generator explanatory bands.

No scoring references, provider client, or label-dependent substitutions are used.
"""

# ruff: noqa: EM101, TRY003, PLC0415
from __future__ import annotations

import argparse
import json
import re
import time
import zlib
from collections import Counter
from pathlib import Path
from typing import Any

from bench.feature_cases import stream_object
from bench.silver import canonical, guard_path, sha, write_json
from bench.silver_layouts import _serialize
from bench.silver_structure import observed_table, process_peak_rss

REMOVALS = (
    "Read each row as one station record.",
    "Read each column downward as an independent narrative.",
    "Station observations",
    "Quarterly observations",
    "Review complete",
)
DESIGN = {
    "version": 1,
    "arm": "explanatory-band-deletion",
    "removals": REMOVALS,
    "replacement": "equal-byte ASCII spaces inside decoded exact PDF literal strings",
    "body_policy": "all other decoded content operators unchanged; rewrite compression/xref only as needed",
    "scope": "DEV source-only ablation; no scoring or private reference access",
}


def neutralize_pdf(data: bytes) -> tuple[bytes, dict[str, int]]:
    """Blank declared literal strings; preserve decoded body operators and geometry."""
    counts = dict.fromkeys(REMOVALS, 0)
    objects = []
    matches = list(re.finditer(rb"(?m)^(\d+) 0 obj\n(.*?)\nendobj", data, re.DOTALL))
    if not matches or [int(m[1]) for m in matches] != list(range(1, len(matches) + 1)):
        raise ValueError("Only authored sequential-object PDFs are supported")
    for match in matches:
        body = match[2]
        if b"\nstream\n" in body:
            header, payload = body.split(b"\nstream\n", 1)
            payload = payload.removesuffix(b"\nendstream")
            compressed = b"/Filter /FlateDecode" in header
            decoded = zlib.decompress(payload) if compressed else payload
            changed = decoded
            for phrase in REMOVALS:
                literal = b"(" + phrase.encode("ascii") + b")"
                counts[phrase] += changed.count(literal)
                changed = changed.replace(literal, b"(" + b" " * len(phrase) + b")")
            if changed != decoded:
                body = (
                    stream_object(zlib.compress(changed), "/Filter /FlateDecode")
                    if compressed
                    else stream_object(changed)
                )
        objects.append(body)
    if not any(counts.values()):
        raise ValueError("No declared explanatory bands found; unsupported source PDF")
    return _serialize(objects, data.splitlines()[0][5:].decode("ascii")), counts


def audit_source(source: dict[str, Any]) -> dict[str, Any]:
    """Find direct authored instructions using only literal extracted source words."""
    rows = []
    for page in source["pages"]:
        # Words may be in column order: direct statement itself remains contiguous.
        text = " ".join(word["text"] for word in page["words"])
        rows.append({"id": page["id"], "phrases": [phrase for phrase in REMOVALS if phrase in text]})
    return {"pages": len(rows), "rows": rows}


def freeze(source_path: Path, pdf_directory: Path, output: Path) -> dict[str, Any]:
    """Freeze PDFs, source evidence and provenance before any external scoring."""
    import pdfust

    source_path, pdf_directory, output = (guard_path(p) for p in (source_path, pdf_directory, output))
    source_raw = source_path.read_bytes()
    source = json.loads(source_raw)
    ids = [page["id"] for page in source["pages"]]
    if len(set(ids)) != len(ids) or any(Path(i).name != i for i in ids):
        raise ValueError("Source identifiers must be unique plain filenames")
    authored = []
    for identifier in ids:
        original = (pdf_directory / f"{identifier}.pdf").read_bytes()
        changed, counts = neutralize_pdf(original)
        authored.append((identifier, original, changed, counts))
    identity = sha(canonical({"design": DESIGN, "pdfs": [sha(row[2]) for row in authored]}))
    if output.exists():
        raise ValueError("Ablation directory already exists; never overwrite a frozen cohort")
    output.mkdir(parents=True)
    (output / "pdfs").mkdir()
    # All intervention PDFs and manifest are retained before extraction.
    for identifier, _, changed, _ in authored:
        (output / "pdfs" / f"{identifier}.pdf").write_bytes(changed)
    manifest = {
        "split": "DEV",
        "design": DESIGN,
        "generator_sha256": sha(Path(__file__).read_bytes()),
        "parent_source_sha256": sha(source_raw),
        "dataset_sha256": identity,
        "pages": len(ids),
        "cases": [
            {"id": i, "original_pdf_sha256": sha(old), "pdf_sha256": sha(new), "removed": counts}
            for i, old, new, counts in authored
        ],
    }
    write_json(output / "manifest.json", manifest)
    began, cpu = time.perf_counter(), time.process_time()
    sources = []
    for identifier, original, changed, _ in authored:
        with pdfust.open(stream=original) as before, pdfust.open(stream=changed) as after:
            old_words = before[0].get_text("words")
            page = after[0]
            words = page.get_text("words")
            # Body words must preserve their exact source geometry and multiplicity.
            original_inventory = Counter(tuple(w[:5]) for w in old_words)
            if Counter(tuple(w[:5]) for w in words) - original_inventory:
                raise ValueError("Intervention changed retained source text or geometry")
            image = output / f"{identifier}.png"
            image.write_bytes(page.render(dpi=120, background=(255, 255, 255)))
            sources.append({
                "id": identifier,
                "words": [{"id": f"w{n}", "text": w[4], "bbox": list(w[:4])} for n, w in enumerate(words)],
                "page_size": list(page.rect),
                "image_path": str(image),
                "vector_candidates": [observed_table(t) for t in page.find_tables().tables],
                "text_candidates": [observed_table(t) for t in page.find_tables(strategy="text").tables],
            })
    write_json(output / "source-evidence.json", {"pages": sources})
    rss, tool = process_peak_rss()
    summary = {
        "pages": len(sources), "dataset_sha256": identity,
        "source_sha256": sha((output / "source-evidence.json").read_bytes()),
        "wall_seconds": time.perf_counter() - began, "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss, "measurement": f"sequential CPU; {tool}; no periodic sampling",
        "scoring": "not performed; private targets never opened",
    }
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    """Prepare a new source-only cohort, with no inference or reference scoring."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pdf-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.source, args.pdf_directory, args.output), indent=2))


if __name__ == "__main__":
    main()
