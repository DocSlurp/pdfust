"""Sync newer wild-v1 / real-world-v2 / wild-v2 DEV datasets and runs to the local Langfuse.

Usage::

    uv run python -m bench.langfuse_wild_extras [--only quirks raster real-world-v2 wild-v2 audit-runs vision]

``bench.langfuse_backfill all`` calls :func:`sync_all` as its ``wild-extras`` step.

- ``dev/wild-v1-quirks``: one item per production-quirk case. Document-based
  cases reference their wild-v1 truth (path and SHA-256); raw cases carry the
  exact expected-text SHA-256 and length rather than the text.
- ``dev/wild-v1-raster``: one item per document x ``R??`` raster variant with
  its build parameters and measured facts.
- ``dev/real-world-v2``: one item per licensed document with license, source,
  producer and PDF-version facts; verified truth is the expected output.
- ``dev/wild-v2``: one item per built document with its truth; skipped until
  ``docs/build-report.json`` exists and every listed document has truth and PDF.
- audit runs: every ``wild-v1/audit.json`` level becomes a run named
  ``wild-v1 audit <level> @ <audit digest>`` (the ``bench.langfuse_backfill``
  naming). ``Q:*`` quirk rows link to ``dev/wild-v1-quirks`` by case; all other
  rows link to ``dev/wild-v1`` by document. Runs already exported by the older
  step only receive the additional scores.
- vision runs: each completed ``wild-v1/vision-v1/<arm>/`` becomes run
  ``wild-v1 vision <arm>`` on ``dev/wild-v1``. Langfuse keeps one run item per
  dataset item, so each document is one trace with one child observation per
  intended page (failed and not-attempted pages included) and a
  ``vision.page_ok_rate`` score. Per-document scores from
  ``vision-v1/scores.json`` (when it exists) are attached as
  ``<metric>/<level>`` plus the across-level mean. Page images are never uploaded;
  usage and accounted USD are metadata only, because paid requests already
  export their own cost through ``bench.decision_langfuse``.

All IDs are deterministic and local markers skip unchanged work. PDFs are
referenced by path and SHA-256. Sync errors are reported, never raised to the
experiment that produced the data. Held-out paths and the held-out dataset
prefix are refused.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

from bench import decision_langfuse as transport
from bench import langfuse_backfill as backfill

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

WORKERS = 3
DEV = {"split": "DEV", "heldout": False}
_TRACE_BATCH = 25
STEPS = ("quirks", "raster", "real-world-v2", "wild-v2", "audit-runs", "vision")
# Hosted (base and hard-raster) and open GPU model transcription experiments.
VISION_DIRECTORIES = ("vision-v1", "vision-raster-v1", "vision-open-v1")


def _hex(value: str, length: int = 32) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> Any:  # noqa: ANN401 - arbitrary retained JSON.
    return json.loads(path.read_text(encoding="utf-8"))


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def dataset_name(name: str) -> str:
    """Return ``name`` after refusing the held-out prefix and protected corpus names."""
    if name.startswith(backfill.HELDOUT_PREFIX) or any(part in name for part in backfill.PROTECTED):
        message = "protected held-out dataset refused"
        raise PermissionError(message)
    return name


def _parallel(function: Callable[[Any], Any], items: Iterable[Any]) -> list[Any]:
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return list(pool.map(function, items))


def _upsert_items(
    client: backfill.Client, name: str, items: list[tuple[str, dict[str, Any], dict[str, Any]]], kind: str
) -> dict[str, Any]:
    """Upsert ``(id, payload, metadata)`` items unless this exact content was already synced."""
    digest = _hex(json.dumps([[i, p, m] for i, p, m in items], sort_keys=True, default=str), 40)
    key = f"{name}|{digest}"
    if backfill._done(kind, key):  # noqa: SLF001
        return {"dataset": name, "items": len(items), "status": "replayed"}
    _parallel(lambda entry: client.item(name, entry[0], entry[1], entry[2]), items)
    archived = client.archive_stale(name, {entry[0] for entry in items})
    backfill._mark(kind, key, {"items": len(items)})  # noqa: SLF001
    return {"dataset": name, "items": len(items), "archived": archived, "status": "exported"}


def _post_run_items(client: backfill.Client, bodies: list[dict[str, Any]]) -> None:
    _parallel(lambda body: client.post("/api/public/dataset-run-items", body), bodies)


def _pdf_ref(path: Path) -> dict[str, Any]:
    entry: dict[str, Any] = {"pdf_path": backfill._relative(path)}  # noqa: SLF001
    if path.is_file():
        entry |= {"pdf_sha256": _file_sha(path), "pdf_bytes": path.stat().st_size}
    return entry


def _truth_ref(path: Path) -> dict[str, Any]:
    return {"path": backfill._relative(path), "sha256": _file_sha(path) if path.is_file() else None}  # noqa: SLF001


# --------------------------------------------------------------------------- datasets


def quirk_item_id(case: dict[str, Any]) -> str:
    """Content-addressed quirk item ID (case and measured PDF hash)."""
    return _hex(f"dev/wild-v1-quirks|{case['case_id']}|{(case.get('measured') or {}).get('sha256')}")


def quirk_items(wild: Path) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any], dict[str, Any]]]]:
    """Build quirk dataset metadata and items from ``quirks/manifest.json``."""
    manifest = _json(backfill._guard(wild) / "quirks" / "manifest.json")  # noqa: SLF001
    labels = {**DEV, "corpus": "wild-v1/quirks"}
    items = []
    for case in manifest["cases"]:
        doc_id = case.get("doc_id")
        if doc_id:
            expected: dict[str, Any] = {
                "kind": "document_truth",
                "truth": _truth_ref(wild / "docs" / doc_id / "truth.json"),
                "truth_dataset_item": {"dataset": "dev/wild-v1", "id": _hex(f"dev/wild-v1|{doc_id}")},
            }
        else:
            text = case.get("expected_text") or ""
            expected = {
                "kind": "exact_text",
                "expected_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "expected_text_chars": len(text),
                "expected_lines": len(case.get("expected_lines") or []),
                "hidden_text_count": len(case.get("hidden_text") or []),
            }
        payload = {
            "input": {
                **{key: case.get(key) for key in ("case_id", "quirk_id", "family", "doc_id", "source_doc_id", "tool")},
                **{key: case.get(key) for key in ("params", "facts", "steps", "password", "notes")},
                "measured": case.get("measured"),
                "validation": case.get("validation"),
                **_pdf_ref(wild / case["path"]),
            },
            "expectedOutput": expected,
        }
        metadata = {**labels, "case_id": case["case_id"], "quirk_id": case["quirk_id"], "family": case["family"]}
        items.append((quirk_item_id(case), payload, metadata))
    meta = {
        **labels,
        "case_count": manifest.get("case_count"),
        "families": manifest.get("families"),
        "tools": manifest.get("tools"),
        "summary": manifest.get("summary"),
        "locator": backfill._relative(wild / "quirks"),  # noqa: SLF001
    }
    return meta, items


def raster_items(wild: Path) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any], dict[str, Any]]]]:
    """Build one item per document x R variant from ``variants/*/raster.json``."""
    labels = {**DEV, "corpus": "wild-v1/raster"}
    items, skipped, errors = [], {}, {}
    for path in sorted(backfill._guard(wild / "variants").glob("*/raster.json")):  # noqa: SLF001
        doc_id = path.parent.name
        report = _json(path)
        skipped |= report.get("skipped") or {}
        if report.get("errors"):
            errors[doc_id] = report["errors"]
        for name, variant in sorted((report.get("variants") or {}).items()):
            pdf = path.parent / (variant.get("output") or f"{name}.pdf")
            payload = {
                "input": {
                    "doc_id": doc_id,
                    "variant": name,
                    "description": variant.get("description"),
                    "parameters": variant.get("parameters"),
                    "seed": variant.get("seed"),
                    "steps": variant.get("steps"),
                    "source": report.get("source"),
                    "pdf_path": backfill._relative(pdf),  # noqa: SLF001
                    "pdf_sha256": variant.get("output_sha256"),
                    "pdf_bytes": variant.get("output_bytes"),
                },
                "expectedOutput": {
                    "expected_text_layer": variant.get("expected_text_layer"),
                    "truth": _truth_ref(wild / "docs" / doc_id / "truth.json"),
                    "truth_dataset_item": {"dataset": "dev/wild-v1", "id": _hex(f"dev/wild-v1|{doc_id}")},
                },
            }
            metadata = {
                **labels,
                "doc_id": doc_id,
                "variant": name,
                "text_layer": variant.get("text_layer"),
                "matches_expected": variant.get("matches_expected"),
                "dpi": variant.get("dpi"),
                "filters": variant.get("filters"),
                "colour_modes": variant.get("colour_modes"),
                "page_count": variant.get("page_count"),
                "measured": variant.get("measured"),
                "resources": variant.get("resources"),
            }
            items.append(
                (_hex(f"dev/wild-v1-raster|{doc_id}|{name}|{variant.get('output_sha256')}"), payload, metadata)
            )
    meta = {**labels, "documents": len({i[2]["doc_id"] for i in items}), "skipped_variants": skipped, "errors": errors}
    return meta, items


def real_world_items(directory: Path) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any], dict[str, Any]]]]:
    """Build licensed real-world-v2 items; verified truth becomes the expected output."""
    manifest = _json(backfill._guard(directory) / "manifest.json")  # noqa: SLF001
    labels = {**DEV, "corpus": "real-world-v2"}
    items, verified = [], 0
    for record in manifest["documents"]:
        pdf = _pdf_ref(directory / record["path"])
        truth_path = directory / "truth" / f"{record['id']}.json"
        expected = None
        truth_status = None
        if truth_path.is_file():
            truth = _json(truth_path)
            truth_status = truth.get("truth_status")
            if truth_status == "verified":
                expected = {"truth_sha256": _file_sha(truth_path), "truth": truth}
                verified += 1
        payload = {
            "input": {
                "document": record,
                **pdf,
                "sha256_matches_manifest": pdf.get("pdf_sha256") == record.get("sha256"),
            },
            "expectedOutput": expected,
        }
        metadata = {
            **labels,
            "doc_id": record["id"],
            "license": record.get("license"),
            "kind": record.get("kind"),
            "producer_family": record.get("producer_family"),
            "pdf_version": (record.get("profile") or {}).get("pdf_version"),
            "truth_status": truth_status,
        }
        items.append((_hex(f"dev/real-world-v2|{record['id']}|{record.get('sha256')}"), payload, metadata))
    meta = {
        **labels,
        "documents": len(items),
        "verified_truth": verified,
        "manifest_updated_at": manifest.get("updated_at"),
        "locator": backfill._relative(directory),  # noqa: SLF001
    }
    return meta, items


def wild_v2_items(directory: Path) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any], dict[str, Any]]]] | str:
    """Build wild-v2 items, or return the reason the corpus is not ready."""
    report_path = backfill._guard(directory) / "docs" / "build-report.json"  # noqa: SLF001
    if not report_path.is_file():
        return "wild-v2 build report missing (build not finished)"
    report = _json(report_path)
    labels = {**DEV, "corpus": "wild-v2"}
    items, missing = [], []
    for row in report.get("documents", []):
        folder = directory / "docs" / row["doc_id"]
        truth_path, pdf = folder / "truth.json", folder / "source.pdf"
        if not (truth_path.is_file() and pdf.is_file()):
            missing.append(row["doc_id"])
            continue
        text = truth_path.read_text(encoding="utf-8")
        truth_sha = hashlib.sha256(text.encode()).hexdigest()
        expected: dict[str, Any] = {"truth_sha256": truth_sha}
        if len(text) <= backfill._MAX_TEXT:  # noqa: SLF001
            expected["truth"] = json.loads(text)
        else:
            expected["truth_path"] = backfill._relative(truth_path)  # noqa: SLF001
        payload = {"input": {"doc_id": row["doc_id"], **_pdf_ref(pdf)}, "expectedOutput": expected}
        metadata = {**labels, "doc_id": row["doc_id"], "build": {k: v for k, v in row.items() if k != "media"}}
        items.append((_hex(f"dev/wild-v2|{row['doc_id']}|{truth_sha}"), payload, metadata))
    if missing or not items:
        return f"wild-v2 incomplete: {len(missing)} listed documents lack truth/PDF"
    meta = {**labels, "documents": len(items), "seed": report.get("seed"), "failures": len(report.get("failures", []))}
    return meta, items


def _sync_dataset(
    client: backfill.Client, name: str, description: str, built: tuple[dict[str, Any], list[Any]]
) -> dict[str, Any]:
    meta, items = built
    client.dataset(dataset_name(name), description, meta)
    return _upsert_items(client, name, items, "wild-extras-dataset")


# --------------------------------------------------------------------------- audit runs


def audit_scores(row: dict[str, Any]) -> dict[str, float]:
    """Numeric scores for one audit row; absent metrics are omitted, not zeroed."""
    scores: dict[str, float] = {}
    for metric in ("f1", "precision", "recall"):
        value = _number((row.get("markdown") or {}).get(metric))
        if value is not None:
            scores[f"wild.markdown_{metric}"] = value
    for name, key in (("wild.text_f1", "text"), ("wild.text_nfkc_f1", "text_nfkc")):
        value = _number((row.get(key) or {}).get("f1"))
        if value is not None:
            scores[name] = value
    tables = [t for t in row.get("tables") or [] if isinstance(t, dict)]
    recalls = [v for v in (_number(t.get("cell_recall")) for t in tables) if v is not None]
    if recalls:
        scores["wild.table_cell_recall_mean"] = statistics.fmean(recalls)
    if tables:
        scores["wild.table_exact_count"] = float(sum(bool(t.get("exact")) for t in tables))
    value = _number(row.get("image_only_text_recovered"))
    if value is not None:
        scores["wild.image_only_text_recall"] = value
    return scores


def _score_id(trace: str, name: str) -> str:
    # Markdown scores keep the IDs of bench.langfuse_backfill.sync_wild_runs so they upsert in place.
    legacy = name.removeprefix("wild.markdown_")
    return _hex(f"{trace}|{legacy}") if legacy != name else _hex(f"{trace}|{name}")


def _quirk_cases(wild: Path) -> dict[str, dict[str, Any]]:
    path = wild / "quirks" / "manifest.json"
    return {case["path"]: case for case in _json(path)["cases"]} if path.is_file() else {}


def _quirk_case(row: dict[str, Any], cases: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    row_path = str(row.get("path") or "")
    for relative, case in cases.items():
        if row_path.endswith(relative):
            return case
    quirk = row["level"].removeprefix("Q:")
    for case in cases.values():
        if case["quirk_id"] == quirk and row.get("doc_id") in {case.get("doc_id"), case.get("source_doc_id")}:
            return case
    return None


def audit_plan(wild: Path) -> tuple[str, dict[str, list[tuple[str, str, dict[str, Any], str]]]]:
    """Return the audit digest and ``level -> [(trace, dataset item, row, key)]`` links."""
    audit_path = backfill._guard(wild) / "audit.json"  # noqa: SLF001
    digest = _file_sha(audit_path)[:12]
    cases = _quirk_cases(wild)
    plan: dict[str, list[tuple[str, str, dict[str, Any], str]]] = {}
    for row in _json(audit_path)["audits"]:
        level = row["level"]
        run = f"wild-v1 audit {level} @ {digest}"
        if level.startswith("Q:"):
            case = _quirk_case(row, cases)
            if case is None:
                continue
            key = case["case_id"]
            item = quirk_item_id(case)
        else:
            key = row["doc_id"]
            item = _hex(f"dev/wild-v1|{key}")
        # Level rows reuse the older adapter's trace IDs; quirk rows are keyed by case.
        plan.setdefault(level, []).append((_hex(f"{run}|{key}"), item, row, key))
    return digest, plan


def _audit_span(trace: str, level: str, key: str, row: dict[str, Any], started: float) -> dict[str, Any]:
    resources = row.get("resources") or {}
    return backfill.span(
        trace,
        f"wild {key} {level}",
        started,
        {
            "langfuse.trace.name": f"wild-v1/{key}/{level}",
            "langfuse.trace.tags": ["wild-v1", level],
            "langfuse.trace.input": {"doc_id": row.get("doc_id"), "case": key, "level": level, "path": row.get("path")},
            "langfuse.trace.output": backfill.bound(json.dumps(row, ensure_ascii=False)),
            "langfuse.trace.metadata.family": row.get("family"),
            "langfuse.trace.metadata.quirk_family": row.get("quirk_family"),
            "langfuse.trace.metadata.wall_seconds": resources.get("wall_seconds"),
            "langfuse.trace.metadata.peak_rss_kib_self": resources.get("peak_rss_kib_self"),
        },
        (resources.get("wall_seconds") or 0) * 1000,
    )


def sync_audit_runs(client: backfill.Client, wild: Path) -> list[dict[str, Any]]:
    """Export every audit level not yet synced and add extended scores to already exported runs."""
    digest, plan = audit_plan(wild)
    started = (wild / "audit.json").stat().st_mtime
    results = []
    for level, links in sorted(plan.items()):
        run = f"wild-v1 audit {level} @ {digest}"
        quirk = level.startswith("Q:")
        if backfill._done("wild-extras-run", run):  # noqa: SLF001
            results.append({"run": run, "status": "replayed"})
            continue
        legacy = not quirk and backfill._done("wild-run", run)  # noqa: SLF001
        if not legacy:
            spans = [_audit_span(trace, level, key, row, started) for trace, _, row, key in links]
            for start in range(0, len(spans), _TRACE_BATCH):
                client.traces(spans[start : start + _TRACE_BATCH], "bench.langfuse_wild_extras.audit")
            dataset = "dev/wild-v1-quirks" if quirk else "dev/wild-v1"
            description = f"wild-v1 audit level {level}; audit.json sha256 {digest}"
            _post_run_items(
                client,
                [
                    {
                        "runName": run,
                        "runDescription": description,
                        "metadata": {"level": level, "dataset": dataset},
                        "datasetItemId": item,
                        "traceId": trace,
                    }
                    for trace, item, _, _ in links
                ],
            )
        client.scores(
            [
                {"id": _score_id(trace, name), "traceId": trace, "name": name, "value": value, "dataType": "NUMERIC"}
                for trace, _, row, _ in links
                for name, value in audit_scores(row).items()
            ]
        )
        backfill._mark("wild-extras-run", run, {"rows": len(links)})  # noqa: SLF001
        if not quirk:
            backfill._mark("wild-run", run, {"documents": len(links)})  # noqa: SLF001
        results.append({"run": run, "status": "scored-existing" if legacy else "exported", "rows": len(links)})
    return results


# --------------------------------------------------------------------------- vision runs


def _vision_pages(vision: Path) -> dict[str, dict[tuple[str, str, int], dict[str, Any]]]:
    arms: dict[str, dict[tuple[str, str, int], dict[str, Any]]] = {}
    for arm in sorted(p for p in backfill._guard(vision).iterdir() if p.is_dir()):  # noqa: SLF001
        pages = {}
        for path in sorted(arm.glob("*--p*.json")):
            record = _json(path)
            record["_mtime"] = path.stat().st_mtime
            pages[(record["doc_id"], record["level"], int(record["page"]))] = record
        arms[arm.name] = pages
    return arms


def vision_plan(vision: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Return completed arms with their intended pages, and skipped in-progress arm names."""
    arms = _vision_pages(vision)
    union = {key for pages in arms.values() for key in pages}
    plans, skipped = {}, []
    for arm, pages in arms.items():
        summary_path = vision / arm / "summary.json"
        if not summary_path.is_file():
            skipped.append(arm)
            continue
        summary = _json(summary_path)
        intended = summary.get("intended_pages")
        keys = set(pages)
        # Pages that never ran leave no file; restore them only when the union proves the denominator.
        if isinstance(intended, int) and len(keys) < intended and len(union) == intended:
            keys = union
        plans[arm] = {"summary": summary, "pages": pages, "keys": sorted(keys)}
    return plans, skipped


_MAX_PAGE_MARKDOWN = 64_000


def _page_span(  # noqa: PLR0913, PLR0917 - one page observation inside its trace.
    trace: str, parent: str, arm: str, key: tuple[str, str, int], record: dict[str, Any] | None, default_start: float
) -> dict[str, Any]:
    doc_id, level, page = key
    record = record or {"status": "not_attempted"}
    usage = record.get("usage") or {}
    entry = record.get("entry") or {}
    attributes = {
        "langfuse.observation.input": {
            "doc_id": doc_id,
            "level": level,
            "page": page,
            "model": record.get("model"),
            "image": record.get("image"),
        },
        "langfuse.observation.output": backfill.bound(record["markdown"], _MAX_PAGE_MARKDOWN)
        if record.get("markdown")
        else None,
        "langfuse.observation.metadata.arm": arm,
        "langfuse.observation.metadata.level": level,
        "langfuse.observation.metadata.page": page,
        "langfuse.observation.metadata.model": record.get("model"),
        "langfuse.observation.metadata.status": record["status"],
        "langfuse.observation.metadata.error": backfill.bound(record.get("error") or "", 1000) or None,
        "langfuse.observation.metadata.served_model": entry.get("served_model"),
        "langfuse.observation.metadata.provider": entry.get("provider"),
        "langfuse.observation.metadata.accounted_usd": entry.get("accounted_usd"),
        "langfuse.observation.metadata.provider_reported_usd": entry.get("provider_reported_usd"),
        "langfuse.observation.metadata.cost_status": entry.get("cost_status"),
        "langfuse.observation.metadata.prompt_tokens": usage.get("prompt_tokens"),
        "langfuse.observation.metadata.completion_tokens": usage.get("completion_tokens"),
        "langfuse.observation.metadata.total_tokens": usage.get("total_tokens"),
        "langfuse.observation.metadata.client_seconds": record.get("client_seconds"),
    }
    span = backfill.span(
        trace,
        f"page {level} p{page} {record['status']}",
        record.get("_mtime") or default_start,
        attributes,
        (record.get("client_seconds") or 0) * 1000,
    )
    span["spanId"] = _hex(f"{trace}|{level}|p{page}", 16)
    span["parentSpanId"] = parent
    return span


def _document_spans(  # noqa: PLR0913, PLR0917 - one arm x document trace.
    trace: str,
    arm: str,
    doc_id: str,
    keys: list[tuple[str, str, int]],
    pages: dict[tuple[str, str, int], dict[str, Any]],
    default_start: float,
) -> list[dict[str, Any]]:
    """One trace per arm x document: a root span plus one child observation per intended page."""
    statuses = [(pages.get(key) or {}).get("status", "not_attempted") for key in keys]
    usd = sum(((pages.get(key) or {}).get("entry") or {}).get("accounted_usd") or 0 for key in keys)
    model = next((pages[key].get("model") for key in keys if key in pages), None)
    root = backfill.span(
        trace,
        f"vision {arm} {doc_id}",
        default_start,
        {
            "langfuse.trace.name": f"wild-v1-vision/{arm}/{doc_id}",
            "langfuse.trace.tags": ["wild-v1", "vision-v1", arm],
            "langfuse.trace.input": {
                "doc_id": doc_id,
                "arm": arm,
                "model": model,
                "pages": [f"{level}/p{page}" for _, level, page in keys],
            },
            "langfuse.trace.output": {status: statuses.count(status) for status in sorted(set(statuses))},
            "langfuse.trace.metadata.arm": arm,
            "langfuse.trace.metadata.model": model,
            "langfuse.trace.metadata.intended_pages": len(keys),
            "langfuse.trace.metadata.accounted_usd": usd,
        },
    )
    return [root] + [_page_span(trace, root["spanId"], arm, key, pages.get(key), default_start) for key in keys]


def vision_document_scores(document: dict[str, Any]) -> dict[str, float]:
    """Per-document vision scores from one ``scores.json`` document entry."""
    scores: dict[str, float] = {}
    value = _number((document.get("text") or {}).get("f1"))
    if value is not None:
        scores["vision.text_f1"] = value
    value = _number(document.get("image_only_text_recovered"))
    if value is not None:
        scores["vision.image_text_recall"] = value
    tables = [t for t in document.get("tables") or [] if isinstance(t, dict)]
    recalls = [v for v in (_number(t.get("cell_recall")) for t in tables) if v is not None]
    if recalls:
        scores["vision.table_cell_recall"] = statistics.fmean(recalls)
    if tables:
        scores["vision.table_exact_count"] = float(sum(bool(t.get("exact")) for t in tables))
    return scores


def vision_trace_scores(by_level: dict[str, dict[str, Any]]) -> dict[str, float]:
    """Per-level ``<metric>/<level>`` scores plus the across-level mean under the bare metric name."""
    scores: dict[str, float] = {}
    collected: dict[str, list[float]] = {}
    for level, document in sorted(by_level.items()):
        for name, value in vision_document_scores(document).items():
            scores[f"{name}/{level}"] = value
            collected.setdefault(name, []).append(value)
    scores |= {name: statistics.fmean(values) for name, values in collected.items()}
    return scores


def sync_vision_runs(client: backfill.Client, vision: Path) -> list[dict[str, Any]]:
    """Export each completed vision arm as one dataset run on ``dev/wild-v1`` (one trace per document)."""
    plans, skipped = vision_plan(vision)
    scores_path = vision / "scores.json"
    scores_doc = _json(scores_path) if scores_path.is_file() else {}
    scores_sha = _file_sha(scores_path)[:12] if scores_path.is_file() else None
    results: list[dict[str, Any]] = [
        {"arm": arm, "status": "skipped: in progress (no summary.json)"} for arm in skipped
    ]
    for arm, plan in plans.items():
        # vision-v1 keeps its original run names so earlier syncs stay idempotent.
        run = f"wild-v1 vision {arm}" if vision.name == "vision-v1" else f"wild-v1 {vision.name} {arm}"
        pages, keys, summary = plan["pages"], plan["keys"], plan["summary"]
        by_doc: dict[str, list[tuple[str, str, int]]] = {}
        for key in keys:
            by_doc.setdefault(key[0], []).append(key)
        traces = {doc_id: _hex(f"{run}|doc|{doc_id}") for doc_id in by_doc}
        statuses = json.dumps([[*k, pages.get(k, {}).get("status")] for k in keys])
        content = _hex(statuses + _file_sha(vision / arm / "summary.json"))
        status: dict[str, Any] = {
            "run": run,
            "documents": len(by_doc),
            "pages": len(keys),
            "retained_pages": len(pages),
        }
        if not backfill._done("wild-extras-vision", f"{run}|{content}"):  # noqa: SLF001
            started = (vision / arm / "summary.json").stat().st_mtime
            documents = sorted(by_doc.items())
            for start in range(0, len(documents), 8):
                spans = [
                    span
                    for doc_id, doc_keys in documents[start : start + 8]
                    for span in _document_spans(traces[doc_id], arm, doc_id, doc_keys, pages, started)
                ]
                client.traces(spans, "bench.langfuse_wild_extras.vision")
            body = {
                "runName": run,
                "runDescription": (
                    f"Vision page transcription ({vision.name}), arm {arm}; "
                    "failed and unattempted pages retained"
                ),
                "metadata": {
                    "arm": arm,
                    "model": summary.get("model"),
                    "intended_pages": summary.get("intended_pages"),
                    "status_counts": summary.get("status"),
                    "accounted_usd": summary.get("accounted_usd"),
                    "wall_seconds": summary.get("wall_seconds"),
                },
            }
            _post_run_items(
                client,
                [
                    {**body, "datasetItemId": _hex(f"dev/wild-v1|{doc_id}"), "traceId": traces[doc_id]}
                    for doc_id in by_doc
                ],
            )
            client.scores(
                [
                    {
                        "id": _hex(f"{traces[doc_id]}|vision.page_ok_rate"),
                        "traceId": traces[doc_id],
                        "name": "vision.page_ok_rate",
                        "value": sum((pages.get(k) or {}).get("status") == "ok" for k in doc_keys) / len(doc_keys),
                        "dataType": "NUMERIC",
                        "comment": f"ok pages / {len(doc_keys)} intended pages",
                    }
                    for doc_id, doc_keys in by_doc.items()
                ]
            )
            backfill._mark("wild-extras-vision", f"{run}|{content}", {"documents": len(by_doc)})  # noqa: SLF001
            status["traces"] = "exported"
        else:
            status["traces"] = "replayed"
        arm_scores = (scores_doc.get(arm) or {}).get("documents") or {}
        if not arm_scores:
            status["document_scores"] = "absent (no scores.json entry)"
        elif backfill._done("wild-extras-vision-scores", f"{run}|{scores_sha}|{content}"):  # noqa: SLF001
            status["document_scores"] = "replayed"
        else:
            per_doc: dict[str, dict[str, dict[str, Any]]] = {}
            for level, entries in arm_scores.items():
                for document in entries:
                    per_doc.setdefault(document["doc_id"], {})[level] = document
            bodies = [
                {
                    "id": _hex(f"{traces[doc_id]}|{name}"),
                    "traceId": traces[doc_id],
                    "name": name,
                    "value": value,
                    "dataType": "NUMERIC",
                }
                for doc_id, by_level in per_doc.items()
                if doc_id in traces
                for name, value in vision_trace_scores(by_level).items()
            ]
            client.scores(bodies)
            backfill._mark("wild-extras-vision-scores", f"{run}|{scores_sha}|{content}", {"scores": len(bodies)})  # noqa: SLF001
            status["document_scores"] = len(bodies)
        results.append(status)
    return results


# --------------------------------------------------------------------------- entry points


def _step(client: backfill.Client, step: str, artifacts: Path) -> Any:  # noqa: ANN401, PLR0911 - one return per step.
    wild = artifacts / "wild-v1"
    if step == "quirks":
        return _sync_dataset(
            client,
            "dev/wild-v1-quirks",
            "Production-quirk derivatives of wild-v1 PDFs and raw PDFs.",
            quirk_items(wild),
        )
    if step == "raster":
        return _sync_dataset(
            client, "dev/wild-v1-raster", "wild-v1 raster/scan variants (R01-R22) per document.", raster_items(wild)
        )
    if step == "real-world-v2":
        built = real_world_items(artifacts / "real-world-v2")
        return _sync_dataset(client, "dev/real-world-v2", "Licensed real-world DEV PDFs; verified truth subset.", built)
    if step == "wild-v2":
        directory = artifacts / "wild-v2"
        built_v2 = wild_v2_items(directory) if directory.is_dir() else "wild-v2 directory missing"
        if isinstance(built_v2, str):
            return {"dataset": "dev/wild-v2", "status": "skipped", "reason": built_v2}
        return _sync_dataset(client, "dev/wild-v2", "wild-v2 multi-page DEV documents with authored truth.", built_v2)
    if step == "audit-runs":
        return sync_audit_runs(client, wild)
    results = []
    for name in VISION_DIRECTORIES:
        if (wild / name).is_dir():
            results.extend(sync_vision_runs(client, wild / name))
    return results


def sync_all(client: backfill.Client, artifacts: Path | None = None, steps: Iterable[str] = STEPS) -> dict[str, Any]:
    """Run each step, reporting errors per step instead of raising."""
    artifacts = artifacts or backfill.ARTIFACTS
    results: dict[str, Any] = {}
    for step in steps:
        try:
            results[step] = _step(client, step, artifacts)
        except Exception as error:  # sync failures must never fail an experiment.
            results[step] = {"status": "error", "error": transport._error(error)}  # noqa: SLF001
    return results


def main() -> None:
    """Sync the requested steps and print a compact status."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="+", choices=STEPS, default=list(STEPS))
    args = parser.parse_args()
    config = transport._configuration(backfill.ROOT)  # noqa: SLF001
    if config is None:
        print("Langfuse is not configured in .env; nothing was sent.")
        return
    client = backfill.Client(config)
    for step, result in sync_all(client, steps=args.only).items():
        print(step, json.dumps(result, ensure_ascii=False, default=str)[:4000], flush=True)
    print(f"requests: {client.calls}")


if __name__ == "__main__":
    main()
