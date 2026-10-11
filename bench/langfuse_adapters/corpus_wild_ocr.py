"""Wild-v1 OCR policies (full, adaptive, fill) and the repair-v1 frozen menu corpus.

Sources under ``wild-v1/``:

- ``audit.json`` rows for the ``+ocr``, ``+ocr-adaptive`` and ``+ocr-fill`` levels, joined with
  the per-document OCR counters/resources of ``ocr-report.json``, ``ocr-adaptive-report.json``
  and ``ocr-fill-report.json`` (``bench/wild_corpus.py``; ``bench/results/wild-v1-latest.md``).
  ``langfuse_backfill`` already exports every audit level as ``dev/wild-v1`` runs with Markdown
  F1 only; here each OCR policy is a run with the audit's full metric set, the OCR counters
  and the paired no-OCR base level's scores, so policies compare against their source level.
- ``repair-v1/`` (``bench/wild_repair.py``): 37 frozen L0/L1 pages with authored truth tables
  and source-only candidate menus. It retains no scored results (hosted/pipeline scoring lives
  under ``pipeline-p003``), so its only run is the menu inventory.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from bench.langfuse_adapters.base import Experiment, Item, Row, Run, guard, read_json
from bench.langfuse_adapters.corpus_common import check_metadata, compact_tables, compare, mtime, ref, rel, scalars

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

NAME = "corpus-wild-ocr"
CORPUS = "wild-v1"
REPORTS = {"+ocr": "ocr-report.json", "+ocr-adaptive": "ocr-adaptive-report.json", "+ocr-fill": "ocr-fill-report.json"}
OCR_COUNTERS = ("words", "regions", "full_pages", "recognized", "inserted", "replaced_pages")


def split_level(level: str) -> tuple[str, str | None]:
    """``L8_mixed+ocr-fill`` -> (``L8_mixed``, ``+ocr-fill``); non-OCR levels return ``None``."""
    base, sep, policy = level.partition("+")
    return (base, f"+{policy}") if sep and f"+{policy}" in REPORTS else (level, None)


def audit_scores(row: dict[str, Any]) -> dict[str, Any]:
    """Return the audit's own per-document metrics (failed opens score zero, as in ``summarize``)."""
    if "error" in row:
        return {"completed": False, "text.f1": 0.0, "text_nfkc.f1": 0.0, "markdown.f1": 0.0}
    scores: dict[str, Any] = {"completed": True}
    for group in ("text", "text_nfkc", "markdown"):
        for metric in ("f1", "precision", "recall"):
            scores[f"{group}.{metric}"] = (row.get(group) or {}).get(metric)
    tables = row.get("tables") or []
    scores |= {
        "image_only_text_recovered": row.get("image_only_text_recovered"),
        "tables.expected": len(tables),
        "tables.matched": sum(bool(t.get("matched")) for t in tables),
        "tables.exact": sum(bool(t.get("exact")) for t in tables),
        "tables.mean_cell_recall": sum(t.get("cell_recall") or 0 for t in tables) / len(tables) if tables else None,
        "title_match": (row.get("metadata") or {}).get("title_match"),
        "author_match": (row.get("metadata") or {}).get("author_match"),
        "outline_found": bool((row.get("outline") or {}).get("found")),
        "text_chars": row.get("text_chars"),
    }
    return scores


def summarize(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Recompute ``wild_corpus.summarize`` for one level."""

    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    tables = [t for r in rows for t in r.get("tables", [])]
    return {
        "documents": float(len(rows)),
        "errors": float(sum("error" in r for r in rows)),
        "text_f1": mean([(r.get("text") or {}).get("f1") or 0.0 for r in rows]),
        "text_nfkc_f1": mean([(r.get("text_nfkc") or {}).get("f1") or 0.0 for r in rows]),
        "markdown_f1": mean([(r.get("markdown") or {}).get("f1") or 0.0 for r in rows]),
        "tables": float(len(tables)),
        "table_matched": float(sum(bool(t.get("matched")) for t in tables)),
        "table_exact": float(sum(bool(t.get("exact")) for t in tables)),
        "table_cell_recall": mean([t["cell_recall"] for t in tables]),
        "title_match": float(sum(bool((r.get("metadata") or {}).get("title_match")) for r in rows)),
        "outline_found": float(sum(bool((r.get("outline") or {}).get("found")) for r in rows)),
    }


def _doc_items(directory: Path, doc_ids: list[str]) -> list[Item]:
    items = []
    for doc_id in doc_ids:
        truth_path = directory / "docs" / doc_id / "truth.json"
        truth = read_json(truth_path) if truth_path.is_file() else {}
        items.append(
            Item(
                key=doc_id,
                input={
                    "doc_id": doc_id,
                    "family": truth.get("family"),
                    "languages": truth.get("languages"),
                    "source_pdf": ref(directory / "docs" / doc_id / "source.pdf"),
                },
                expected={
                    "truth": ref(truth_path),
                    "page_count": truth.get("page_count"),
                    "metadata": truth.get("metadata"),
                    "outline_entries": len(truth.get("outline") or []),
                    "unicode_features": truth.get("unicode_features"),
                },
                metadata={"family": truth.get("family")},
            )
        )
    return items


def _policy_runs(directory: Path, audit: dict[str, Any], audit_path: Path) -> list[Run]:
    by_level: dict[str, dict[str, dict[str, Any]]] = {}
    for row in audit.get("audits", []):
        by_level.setdefault(row["level"], {})[row["doc_id"]] = row
    reports = {
        policy: read_json(directory / name) if (directory / name).is_file() else {} for policy, name in REPORTS.items()
    }
    audit_digest = hashlib.sha256(audit_path.read_bytes()).hexdigest()[:12]
    runs = []
    for level, docs in sorted(by_level.items()):
        base, policy = split_level(level)
        if policy is None:
            continue
        report = reports[policy]
        documents = report.get("documents") or {}
        base_rows = by_level.get(base, {})
        rows = []
        for doc_id, record in sorted(docs.items()):
            counters = documents.get(f"{doc_id}/{base}")
            resources = (counters or {}).get("resources") or {}
            base_scores = audit_scores(base_rows[doc_id]) if doc_id in base_rows else {}
            variant = directory / "variants" / doc_id / f"{level}.pdf"
            rows.append(
                Row(
                    item_key=doc_id,
                    output={
                        "tables": [
                            {k: t.get(k) for k in ("id", "matched", "exact", "shape_exact", "cell_recall", "rendering")}
                            for t in record.get("tables") or []
                        ],
                        "scripts": record.get("scripts"),
                        "ocr": {k: counters.get(k) for k in OCR_COUNTERS if k in counters} if counters else None,
                        **({"error": record["error"]} if "error" in record else {}),
                    },
                    scores={
                        **audit_scores(record),
                        **{f"ocr.{k}": counters.get(k) for k in OCR_COUNTERS if counters and k in counters},
                        "ocr.replaced_pages": (counters or {}).get("replaced_pages", 0)
                        if policy == "+ocr-fill"
                        else None,
                        "base.text.f1": base_scores.get("text.f1"),
                        "base.markdown.f1": base_scores.get("markdown.f1"),
                        "base.tables.mean_cell_recall": base_scores.get("tables.mean_cell_recall"),
                    },
                    metadata={
                        "status": "error" if "error" in record else "complete",
                        "ocr_report_entry": counters is not None,
                        "family": record.get("family"),
                        "level": level,
                        "base_level": base,
                        "policy": policy,
                        "variant_path": rel(variant),
                        **scalars(resources, "ocr_resources."),
                        **scalars(record.get("resources") or {}, "audit_resources."),
                    },
                    input={"variant": rel(variant)},
                    wall_ms=(resources.get("wall_seconds") or 0) * 1000 or None,
                    name=f"{CORPUS}/{doc_id}/{level}",
                )
            )
        reported = (audit.get("summary") or {}).get(level, {})
        computed = summarize(list(docs.values()))
        runs.append(
            Run(
                name=f"{level} @ {audit_digest}",
                description=(
                    f"wild_corpus OCR policy {policy!r} applied to {base}; audit metrics (bigram F1, tables, metadata) "
                    "with OCR counters and paired base-level scores. Synthetic DEV documents."
                ),
                rows=rows,
                metadata={
                    "level": level,
                    "base_level": base,
                    "policy": policy,
                    "ocr_report": REPORTS[policy],
                    "dpi": report.get("dpi"),
                    "threads": report.get("threads"),
                    "min_confidence": report.get("min_confidence"),
                    "ocr_report_entries": sum(f"{d}/{base}" in documents for d in docs),
                    **scalars(report.get("resources") or {}, "ocr_report_resources."),
                    **check_metadata(compare(computed, reported)),
                },
                scores={**computed, **{k: v for k, v in reported.items() if isinstance(v, (int, float))}},
                started=mtime(audit_path),
            )
        )
    return runs


def _repair(directory: Path) -> Experiment | None:
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        return None
    manifest = read_json(manifest_path)
    targets_path = directory / "private-targets.json"
    targets = {p["id"]: p for p in read_json(targets_path).get("pages", [])} if targets_path.is_file() else {}
    items = []
    for page in manifest.get("pages", []):
        target = targets.get(page["id"], {})
        items.append(
            Item(
                key=page["id"],
                input={
                    "page": page["id"],
                    "doc_id": page.get("doc_id"),
                    "level": page.get("level"),
                    "page_number": page.get("page_number"),
                    "languages": page.get("languages"),
                    "pdf": ref(directory / "pdfs" / f"{page['id']}.pdf"),
                    "image": ref(directory / "images" / f"{page['id']}.png"),
                    "menu": ref(directory / "menus" / f"{page['id']}.json"),
                },
                expected={
                    "structural_scored": target.get("structural_scored"),
                    "tables": compact_tables(target.get("tables")),
                }
                if target
                else None,
                metadata={"doc_id": page.get("doc_id"), "level": page.get("level"), "family": page.get("family")},
            )
        )
    frozen_path = directory / "frozen.json"
    runs = []
    if frozen_path.is_file():
        frozen = read_json(frozen_path)
        counts = ("candidate_count", "native_table_count", "text_table_count", "truth_table_count", "stress_count")
        rows = [
            Row(
                item_key=menu["id"],
                output={k: menu.get(k) for k in counts},
                scores={k: menu.get(k) for k in counts},
                metadata={"status": "frozen"},
                name=f"{CORPUS}/repair-v1/{menu['id']}/menu",
            )
            for menu in frozen.get("menus", [])
        ]
        runs.append(
            Run(
                name="menu-freeze",
                description=(
                    "Source-only candidate menu inventory per page (candidate, native/text table and stress counts "
                    "beside the authored truth-table count). An inventory, not a scored selection."
                ),
                rows=rows,
                metadata={
                    "hosted_calls": frozen.get("hosted_calls"),
                    "references_read_for_menus": frozen.get("references_read_for_menus"),
                    **scalars(frozen.get("resources") or {}, "resources."),
                    "summary_check": "not-retained",
                },
                scores={
                    "pages": len(rows),
                    **{f"stress.{k}": v for k, v in (frozen.get("synthetic_stress_counts") or {}).items()},
                },
                started=mtime(frozen_path),
            )
        )
    return Experiment(
        dataset=f"exp/{CORPUS}/repair-v1",
        description=(
            "wild-v1 repair-v1: 37 frozen L0/L1 pages with authored truth tables and source-only candidate "
            "menus. Scored repair runs are retained under pipeline-p003, not here."
        ),
        items=items,
        runs=runs,
        source=rel(directory),
        labels={"split": manifest.get("split", "DEV"), "heldout": False},
    )


def collect(artifacts: Path) -> Iterable[Experiment]:
    """OCR policy runs over the 24 wild-v1 documents, then the repair-v1 menu corpus."""
    directory = guard(artifacts / CORPUS)
    audit_path = directory / "audit.json"
    if audit_path.is_file():
        audit = read_json(audit_path)
        doc_ids = (audit.get("manifest") or {}).get("doc_ids") or sorted({r["doc_id"] for r in audit.get("audits", [])})
        yield Experiment(
            dataset=f"exp/{CORPUS}/ocr-policies",
            description=(
                "wild-v1 synthetic DEV documents under native OCR policies (full-page fallback, layer-aware "
                "adaptive, word-level fill). Scores are the wild audit's character-bigram F1, table and metadata "
                "metrics plus OCR counters; base.* are the paired no-OCR level. Not a real-world quality claim."
            ),
            items=_doc_items(directory, doc_ids),
            runs=_policy_runs(directory, audit, audit_path),
            source=rel(directory),
        )
    repair = _repair(directory / "repair-v1") if (directory / "repair-v1").is_dir() else None
    if repair:
        yield repair
