"""Freeze source-only SLANet/T005 agreement before reference coverage/risk scoring."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from bench.borderless_challenge import score
from bench.silver import guard_path
from bench.silver_structure import process_peak_rss
from bench.specialist_resolution import CORPUS
from bench.specialist_resolution import OUTPUT as SPECIALIST

GEOMETRY = Path(
    "/home/dan/code/oss/pdf-master-designs/bench/results/pdf-master-artifacts/rolling-extent-v1/original-realism-v2/candidates.json"
)
OUTPUT = SPECIALIST.parent / "agreement-v1"
DPI = 72
GATES = CORPUS.parent.parent / "source-table-gate-realistic28-v2"
RULES = {
    "strict": (
        "Unique complete geometry candidate must match SLANet shape, explicit spans, every anchor "
        "source-ID set and unresolved IDs. Missing cell/anchor association defers. Both source "
        "inventories must agree verbatim before ID mapping."
    ),
    "text_matrix": (
        "Separately weaker rule: unique complete geometry candidate must match shape, explicit spans "
        "and whitespace-normalized text at every row/column. No source-ID equality requirement."
    ),
    "ambiguity": (
        "Multiple distinct agreeing candidates defer; duplicates with identical partition/matrix/spans "
        "are one source hypothesis. No target fields, confidence, or per-case thresholds."
    ),
    "gate": (
        "Optional routing simulation accepts only agreement plus retained PPLX G001 table_present. "
        "Missing/error/nonpresent answers defer; no inference or fresh latency/cost claim."
    ),
}


def sha(path: Path) -> str:
    """Hash retained exact bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shape(table: dict[str, Any]) -> tuple[int, int]:
    """Read explicit matrix dimensions."""
    return table["row_count"], table["col_count"]


def spans(table: dict[str, Any]) -> tuple[tuple[int, int, int, int], ...]:
    """Canonicalize explicit spans without guessing missing annotations."""
    return tuple(sorted((s["row"], s["column"], s["row_span"], s["column_span"]) for s in table["spans"]))


def matrix(table: dict[str, Any]) -> list[list[str | None]]:
    """Normalize whitespace only, retaining covered None slots and case."""
    return [[None if value is None else " ".join(value.split()) for value in row] for row in table["values"]]


def text_agrees(first: dict[str, Any], second: dict[str, Any]) -> bool:
    """Require complete same-shape, same-span, same-slot literal text."""
    return shape(first) == shape(second) and spans(first) == spans(second) and matrix(first) == matrix(second)


def predicted_partitions(row: dict[str, Any]) -> dict[tuple[int, int], tuple[str, ...]] | None:
    """Use decoder cell order only when one explicit HTML table maps one-to-one to boxes."""
    if len(row["matrices"]) != 1 or len(row["observed"]["outputs"]) != 1:
        return None
    anchors = row["matrices"][0]["anchors"]
    cells = [c for c in row["ownership"]["cells"] if c["output"] == 0]
    if len(cells) != len(anchors) or [c["cell"] for c in cells] != list(range(len(anchors))):
        return None
    return {
        tuple(anchor): tuple(sorted(identifier.split("-", maxsplit=2)[-1] for identifier in cell["source_ids"]))
        for anchor, cell in zip(anchors, cells, strict=True)
    }


def geometric_partitions(table: dict[str, Any]) -> dict[tuple[int, int], tuple[str, ...]] | None:
    """Associate frozen row-major cells with their explicit noncovered slots."""
    rows, cols = shape(table)
    if len(table["cells"]) != rows * cols:
        return None
    return {
        (r, c): tuple(sorted(table["cells"][r * cols + c]["source_ids"]))
        for r in range(rows)
        for c in range(cols)
        if table["values"][r][c] is not None
    }


def strict_agrees(row: dict[str, Any], table: dict[str, Any]) -> bool:
    """Require literal table agreement plus exact conservative source-ID ownership."""
    predicted = predicted_partitions(row)
    geometry = geometric_partitions(table)
    unresolved = tuple(sorted(i.split("-", maxsplit=2)[-1] for i in row["ownership"]["unresolved_ids"]))
    return (
        predicted is not None
        and geometry is not None
        and predicted == geometry
        and len(row["matrices"]) == 1
        and text_agrees(row["matrices"][0], table)
        and unresolved == tuple(sorted(table["unresolved_ids"]))
    )


def unique_selection(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Defer conflicts while deduplicating identical source hypotheses."""
    identities = {
        json.dumps(
            {
                "matrix": matrix(t),
                "spans": spans(t),
                "partitions": sorted((str(k), v) for k, v in (geometric_partitions(t) or {}).items()),
            },
            sort_keys=True,
        ): t
        for t in candidates
    }
    return next(iter(identities.values())) if len(identities) == 1 else None


def freeze(output: Path) -> dict[str, Any]:
    """Freeze agreement rules, inputs and all decisions without reading private references."""
    output = guard_path(output)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "agreement-frozen.json").exists():
        message = "Agreement already frozen; choose a new directory"
        raise ValueError(message)
    (output / "rules.json").write_text(json.dumps(RULES, indent=2))
    began, cpu = time.perf_counter(), time.process_time()
    geometry = json.loads(GEOMETRY.read_text())["cohorts"][1]
    source_path = guard_path(Path(geometry["source_path"]))
    if sha(source_path) != geometry["source_sha256"]:
        message = "T005 source evidence changed"
        raise ValueError(message)
    sources = {p["id"]: p for p in json.loads(source_path.read_text())["pages"]}
    specialist_sources = {p["id"]: p for p in json.loads((SPECIALIST / "source-frozen.json").read_text())["pages"]}
    specialist_frozen = json.loads((SPECIALIST / "outputs-frozen.json").read_text())
    if specialist_frozen["source_sha256"] != sha(SPECIALIST / "source-frozen.json") or set(sources) != set(
        specialist_sources
    ):
        message = "Matched specialist source cohort changed"
        raise ValueError(message)
    for identifier, page in sources.items():
        left = [(w["id"], w["text"], w["bbox"]) for w in page["words"]]
        right = [
            (w["id"].split("-", maxsplit=2)[-1], w["text"], w["bbox"]) for w in specialist_sources[identifier]["words"]
        ]
        if left != right:
            message = "Exact source inventory identity cannot map across engines"
            raise ValueError(message)
    specialist_rows = {r["id"]: r for r in specialist_frozen["rows"] if r["dpi"] == DPI and r["route"] == "crop-pad12"}
    rows = []
    for page in geometry["pages"]:
        observed = specialist_rows[page["id"]]
        for alternative in page["alternatives"]:
            for rule in ("strict", "text_matrix"):
                candidates = [
                    t
                    for t in alternative["candidates"]
                    if (
                        strict_agrees(observed, t)
                        if rule == "strict"
                        else len(observed["matrices"]) == 1 and text_agrees(observed["matrices"][0], t)
                    )
                ]
                selected = unique_selection(candidates)
                rows.append(
                    {
                        "id": page["id"],
                        "config": alternative["config"],
                        "rule": rule,
                        "accepted": selected is not None,
                        "candidate": selected,
                        "agreeing_candidates": len(candidates),
                        "source_inventory_validated": True,
                    }
                )
    rss, tool = process_peak_rss()
    frozen = {
        "rows": rows,
        "rules_sha256": sha(output / "rules.json"),
        "source_sha256": sha(source_path),
        "geometry_sha256": sha(GEOMETRY),
        "specialist_output_sha256": sha(SPECIALIST / "outputs-frozen.json"),
        "preparation": {
            "wall_seconds": time.perf_counter() - began,
            "cpu_seconds": time.process_time() - cpu,
            "peak_rss_bytes": rss,
            "measurement": tool + "; SELF CPU; serial math only; no sampling",
        },
    }
    (output / "agreement-frozen.json").write_text(json.dumps(frozen, indent=2))
    return frozen


def evaluate(output: Path) -> dict[str, Any]:
    """Score complete frozen decisions only after source-only rules/outputs are retained."""
    frozen = json.loads((output / "agreement-frozen.json").read_text())
    if sha(output / "rules.json") != frozen["rules_sha256"]:
        message = "Frozen agreement rules changed"
        raise ValueError(message)
    targets = {t["id"]: t for t in json.loads((CORPUS / "private-targets.json").read_text())}
    gates_path = GATES / "hosted-results.json"
    gates = json.loads(gates_path.read_text())["calls"] if gates_path.exists() else []
    gate_lookup = {
        r["id"]: r
        for r in gates
        if r["model"] == "perplexity/pplx-decider-v1.1-27b" and r["variant"] == "G001-record-schema"
    }
    summary = []
    configs = sorted({r["config"] for r in frozen["rows"]})
    for config in configs:
        for rule in ("strict", "text_matrix"):
            base = [r for r in frozen["rows"] if r["config"] == config and r["rule"] == rule]
            for gate in (False, True):
                counts: Counter[str] = Counter()
                scored = []
                for row in base:
                    identifier = row["id"]
                    target = targets[identifier]
                    gate_row = gate_lookup.get(identifier)
                    present = bool(
                        gate_row and gate_row["status"] == "ok" and gate_row["answer"]["choice"] == "table_present"
                    )
                    accepted = row["accepted"] and (present if gate else True)
                    kind = target["kind"]
                    if kind == "ambiguous":
                        counts["ambiguous_pages"] += 1
                        counts["ambiguous_accepted_unscored"] += accepted
                        continue
                    tables = [row["candidate"]] if accepted else []
                    result = score(target, tables)
                    counts["accepted_correct_tables"] += accepted and result["exact_page"]
                    counts["accepted_wrong_tables"] += accepted and not result["exact_page"]
                    counts["prose_false_positive"] += kind == "prose" and accepted
                    counts["deferred_positives"] += kind == "borderless" and not accepted
                    counts["positive_pages"] += kind == "borderless"
                    counts["prose_pages"] += kind == "prose"
                    scored.append({"id": identifier, "accepted": accepted, "scores": result})
                summary.append(
                    {
                        "config": config,
                        "rule": rule,
                        "gate_simulated": gate,
                        "pages": len(base),
                        "counts": dict(counts),
                        "rows": scored,
                        "gate_measured_pages": len(gate_lookup) if gate else None,
                    }
                )
    result = {
        "cohorts": summary,
        "frozen_sha256": sha(output / "agreement-frozen.json"),
        "gate_results_sha256": sha(gates_path) if gates_path.exists() else None,
        "preparation": frozen["preparation"],
    }
    (output / "private-evaluation.json").write_text(json.dumps(result, indent=2))
    return result


def report(result: dict[str, Any], output: Path) -> None:
    """Publish acceptance coverage/risk and clearly separate weaker/conditional rules."""
    lines = [
        "# Offline source-only specialist/geometry agreement",
        "",
        (
            "Rules and agreement decisions were frozen before private targets were read. All 28 reviewed DEV pages "
            "Every configuration retains 16 borderless, 8 prose and 4 ambiguous pages. Nonagreement defers; it is not "
            "a successful extraction. Strict compares source-ID partitions, shape, explicit spans and complete text "
            "matrix; the weaker text-matrix arm omits ownership equality. All three T005 source configurations "
            "are retained. Missing predicted-cell/HTML anchor correspondence defers."
        ),
        "",
        (
            "| Config/rule | Gate AND (offline) | Accepted correct tables | Accepted wrong tables | "
            "Prose FP | Deferred positives | Ambiguous accepted (unscored) |"
        ),
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for cohort in result["cohorts"]:
        c = cohort["counts"]
        lines.append(
            f"| {cohort['config']}/{cohort['rule']} | {cohort['gate_simulated']} | "
            f"{c.get('accepted_correct_tables', 0)} | {c.get('accepted_wrong_tables', 0)} | "
            f"{c.get('prose_false_positive', 0)}/{c['prose_pages']} | "
            f"{c.get('deferred_positives', 0)}/{c['positive_pages']} | "
            f"{c.get('ambiguous_accepted_unscored', 0)}/{c['ambiguous_pages']} |"
        )
    lines += [
        "",
        (
            "Source-ID mapping is validated against exact text/bbox inventory equality; specialist IDs are "
            "mapped to the identical native word IDs. Cell center ownership is source-only and conservative. "
            "Text matrix equality is a weaker agreement observation, not a substitute for that identity check."
        ),
        "",
        (
            "The PPLX G001 conjunction uses retained actual source-gate answers only as an offline routing simulation. "
            "All model calls were already charged. No fresh inference, cost saving, provider cache, end-to-end latency "
            "or generalization claim is made. Missing/failed gate outputs defer. No confidence is calibrated."
        ),
        "",
        "CPU preparation: `" + json.dumps(result["preparation"]) + "`. Raw source matrices/partitions and scored "
        "outputs remain ignored. Frozen agreement SHA256: `" + result["frozen_sha256"] + "`.",
        "",
        f"Artifacts: `{output}`. Reproduce: `python -m bench.specialist_agreement --freeze --report`.",
        "",
    ]
    (Path(__file__).parent / "results/specialist-agreement.md").write_text("\n".join(lines))


def main() -> None:
    """Freeze offline agreement or report its retained postfreeze reference scores."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    output = guard_path(args.output)
    if args.freeze:
        freeze(output)
    if args.report:
        report(evaluate(output), output)


if __name__ == "__main__":
    main()
