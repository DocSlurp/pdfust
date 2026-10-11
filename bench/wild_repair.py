"""Freeze a wild-v1 local-repair corpus in the P003 extension format.

Each born-digital (L0) and re-distilled (L1) wild-v1 page that carries a
native truth table becomes one single-page case. Sources, candidate menus and
controlled stress states are built from the PDF alone with the same functions
as the authored extension corpus; truth tables are written only to
``private-targets.json``. After freezing, the corpus file hashes are recorded
in ``WILD_PINS`` before any model run so scoring can authenticate them.
"""

# ruff: noqa: PLR2004, EM101, TRY003
from __future__ import annotations

import argparse
import json
import resource
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pylopdf
from bench import p003_extension_cases as cases
from bench import p003_extension_score as scoring
from bench.silver import canonical, guard_path, sha, write_json

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOT = Path(__file__).resolve().parents[1]
WILD = ROOT / "bench/results/pdf-master-artifacts/wild-v1"
LEVELS = ("L0_tagged", "L1_untagged")
NATIVE_RENDERINGS = {"ruled", "borderless"}
# Frozen corpus hashes, recorded after `build` and before any hosted run.
WILD_PINS: dict[str, str] = {
    "frozen.json": "9b5aadcad8952d666ebab4f5f31df6f3a75de83f4e727503d32c803cf771158e",
    "manifest.json": "a449599ff4390ec9777ad005bb6e1a4341424641ce4ff22746fb933b515fb423",
    "private-targets.json": "06e1ea71f56a2bcee50e6bd9ee21287a6c608920c8d7a3a901894761de9b9588",
    "source-inventory.json": "9da760b21fb1b93b89f0a1edf0ef918df628045eef21db7f1a6ea81acf71e351",
}


def _cell_tokens(table: dict[str, Any]) -> list[str]:
    return [" ".join(str(cell).split()) for row in table["values"] for cell in row if cell and str(cell).strip()]


def _target(table: dict[str, Any]) -> dict[str, Any]:
    """Truth table in the extension target schema; covered merge slots are None."""
    values = [list(row) for row in table["values"]]
    anchors = {(span["row"], span["column"]) for span in table["spans"]}
    for span in table["spans"]:
        for row in range(span["row"], span["row"] + span["row_span"]):
            for column in range(span["column"], span["column"] + span["column_span"]):
                if (row, column) not in anchors:
                    values[row][column] = None
    return {"row_count": len(values), "col_count": len(values[0]), "values": values, "spans": table["spans"]}


def _assign(tables: list[dict[str, Any]], page_texts: list[str]) -> dict[int, list[dict[str, Any]]]:
    """Place each truth table on the page containing most of its cell text."""
    placed: dict[int, list[dict[str, Any]]] = {}
    for table in tables:
        tokens = _cell_tokens(table)
        if not tokens:
            continue
        scores = [sum(token in text for token in tokens) / len(tokens) for text in page_texts]
        best = max(range(len(scores)), key=scores.__getitem__)
        if scores[best] >= 0.5:
            placed.setdefault(best, []).append(table)
    return placed


@contextmanager
def _single_page(path: Path, index: int) -> Iterator[bytes]:
    with pylopdf.Document(str(path)) as document:
        document.select([index])
        yield document.tobytes()


def build(output: Path) -> dict[str, Any]:
    """Freeze source-only menus and stress states, then targets, for every case."""
    output = guard_path(output)
    if output.exists():
        raise FileExistsError("New versioned corpus directory required")
    start, cpu = time.perf_counter(), time.process_time()
    output.mkdir(parents=True)
    for name in ("pdfs", "sources", "images", "menus", "stress"):
        (output / name).mkdir()
    pages, targets, inventory, counts, stress_counts = [], [], {}, [], Counter()
    for truth_path in sorted((WILD / "docs").glob("*/truth.json")):
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        tables = [b for b in truth["blocks"] if b["kind"] == "table" and b.get("rendering") in NATIVE_RENDERINGS]
        if not tables:
            continue
        for level in LEVELS:
            variant = guard_path(WILD / "variants" / truth["doc_id"] / f"{level}.pdf")
            with pylopdf.Document(str(variant)) as document:
                page_texts = [page.get_text() for page in document]
            for index, page_tables in sorted(_assign(tables, page_texts).items()):
                ident = "x" + sha(f"wild-v1-repair/{truth['doc_id']}/{level}/{index}".encode())[:24]
                with _single_page(variant, index) as data:
                    pdf_path = output / "pdfs" / f"{ident}.pdf"
                    pdf_path.write_bytes(data)
                    source, rules, states = cases.extract_source(data, ident)
                    with pylopdf.Document(stream=data) as single:
                        (output / "images" / f"{ident}.png").write_bytes(single[0].render(scale=768 / 792))
                write_json(output / "sources" / f"{ident}.json", {"id": ident, "source": source, "rules": rules})
                menu = cases.candidate_menu(source, states, ident)
                write_json(output / "menus" / f"{ident}.json", {**menu, "source": source, "rules": rules})
                stress = cases.stress_baselines(source, states[0], ident)
                stress_counts.update(item["treatment"] for item in stress)
                write_json(output / "stress" / f"{ident}.json",
                           {"id": ident, "synthetic_stress_only": True, "treatments": stress})
                pages.append({"id": ident, "pdf_path": str(pdf_path), "pdf_sha256": sha(data), "page_number": 0,
                              "family": f"wild/{truth['family']}/{level}", "cohort": "wild-v1",
                              "input_kind": "realistic_born_digital_pdf",
                              "label_status": "Authored truth tables; menus built from the PDF alone", "pilot": False,
                              "doc_id": truth["doc_id"], "level": level, "source_page": index,
                              "languages": truth.get("languages", [])})
                targets.append({"id": ident, "tables": [_target(t) for t in page_tables], "structural_scored": True})
                counts.append({"id": ident, "native_table_count": len(states[0]["tables"]),
                               "text_table_count": len(states[1]["tables"]), "truth_table_count": len(page_tables),
                               "candidate_count": len(menu["candidates"]), "stress_count": len(stress)})
                for name, suffix in (("pdfs", ".pdf"), ("sources", ".json"), ("images", ".png"),
                                     ("menus", ".json"), ("stress", ".json")):
                    path = output / name / (ident + suffix)
                    inventory[str(path.relative_to(output))] = sha(path.read_bytes())
    identity = sha(canonical({"schema": 1, "pages": [{k: v for k, v in p.items() if k != "pdf_path"} for p in pages],
                              "targets": targets}))
    write_json(output / "manifest.json", {"schema": 1, "split": "DEV", "dataset_sha256": identity,
                                          "path_convention": "absolute", "pages": pages,
                                          "model_fields": ["id", "pdf_path", "pdf_sha256", "page_number"],
                                          "selection_seed": "wild-v1-repair"})
    write_json(
        output / "source-inventory.json", {"source_only": True, "artifacts": inventory, "case_count": len(pages)}
    )
    write_json(output / "private-targets.json", {"schema": 1, "dataset_sha256": identity, "pages": targets})
    frozen = {"schema": 1, "dataset_sha256": identity, "case_count": len(pages), "menus": counts,
              "synthetic_stress_counts": dict(stress_counts), "levels": list(LEVELS), "hosted_calls": 0,
              "references_read_for_menus": False,
              "resources": {"wall_seconds": time.perf_counter() - start, "cpu_seconds": time.process_time() - cpu,
                            "lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            "measurement": "Single process; unsampled getrusage lifetime peak includes imports"}}
    write_json(output / "frozen.json", frozen)
    return frozen


def pins(corpus: Path) -> dict[str, str]:
    """Hash the four pinned corpus files."""
    corpus = guard_path(corpus)
    return {name: sha((corpus / name).read_bytes()) for name in WILD_PINS}


@contextmanager
def wild_pins() -> Iterator[None]:
    """Score against the wild-v1 pins instead of the authored extension pins."""
    if not all(WILD_PINS.values()):
        raise RuntimeError("Record WILD_PINS before scoring")
    original = scoring.PINS
    scoring.PINS = dict(WILD_PINS)
    try:
        yield
    finally:
        scoring.PINS = original


def score(corpus: Path, run: Path) -> dict[str, Any]:
    """Authenticate and replay one local-repair run against the wild-v1 targets."""
    from bench import extension_local_score  # noqa: PLC0415 - scoring-only dependency.

    with wild_pins():
        result = extension_local_score.score_run(corpus, run)
    write_json(guard_path(run) / "local-score-v1.json", result)
    return result


def main() -> None:
    """Build the corpus, print its pins, or score a run."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=WILD / "repair-v1")
    parser.add_argument("--pins", action="store_true", help="Print pins of an existing corpus")
    parser.add_argument("--score", type=Path, nargs="+", help="Score local-repair run directories")
    args = parser.parse_args()
    if args.score:
        for run in args.score:
            result = score(args.output, run)
            print(run.name, json.dumps(result["status_counts"]))
        return
    if args.pins:
        print(json.dumps(pins(args.output), indent=2))
        return
    frozen = build(args.output)
    print(json.dumps({k: v for k, v in frozen.items() if k != "menus"}, indent=2))
    print(json.dumps(pins(args.output), indent=2))


if __name__ == "__main__":
    main()
