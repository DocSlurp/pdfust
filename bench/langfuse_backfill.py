"""Backfill experiments, reports, and corpora into the local Langfuse.

Usage::

    uv run python -m bench.langfuse_backfill all
    uv run python -m bench.langfuse_backfill datasets|runs|experiments|reports
    uv run python -m bench.langfuse_backfill heldout --custodian-release   # see below

- ``datasets``: DEV corpora become Langfuse datasets named ``dev/<corpus>/<version>``.
  Items carry the PDF identity (and the PDF itself as base64 when small) as
  input and the authored targets as expected output.
- ``runs``: per-document benchmark rows (silver anchor recall, wild-v1 Markdown
  F1) become dataset runs with numeric scores.
- ``experiments``: one registry trace per artifact directory with a content
  digest, file/byte counts, and bounded top-level reports; it is re-sent only
  when the directory changes.
- ``reports``: one trace per committed ``bench/results/*.md`` summary and
  ``EXPERIMENTS_LOG.md`` version.
- ``heldout``: custodian-only upload of the protected silver held-out set,
  authorized by explicit user release on 2026-10-11. It is stored as
  ``HELD-OUT-NOT-FOR-TRAINING/...`` and labeled on the dataset and every item as
  prohibited for training, tuning, and development feedback. The command
  prints only counts and identity hashes, as ``bench/heldout-silver/AGENTS.md``
  requires. Every other command refuses the protected prefix.

All IDs are deterministic, so re-running is idempotent. Credential-like strings
are scrubbed from uploaded text. Transport and configuration are shared with
``bench.decision_langfuse``; missing keys disable the backfill.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from bench import decision_langfuse as transport
from bench.langfuse_adapters import discover
from bench.langfuse_adapters.base import collect_all, export, validate

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "bench" / "results" / "pdf-master-artifacts"
PROTECTED = ("silver-heldout-v1", "heldout-silver")
HELDOUT_REGISTRY = ROOT / "bench" / "heldout-silver" / "registry.json"
HELDOUT_PREFIX = "HELD-OUT-NOT-FOR-TRAINING"
HELDOUT_LABEL = {
    "split": "HELD_OUT",
    "training_use": "PROHIBITED",
    "tuning_use": "PROHIBITED",
    "development_feedback": "PROHIBITED",
    "access": "Custodian or an authorized evaluator of a frozen candidate only; see bench/heldout-silver/AGENTS.md",
    "release": "Stored by explicit user release on 2026-10-11",
}
_INLINE_PDF = 512 * 1024
_MAX_TEXT = 256_000
_MAX_REPORT_FILES = 12
_REPORT_BATCH = 10
_RETRIES = 5
_SCORE_BATCH = 250
_SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|pk-lf-[A-Za-z0-9-]+|sk-lf-[A-Za-z0-9-]+|hf_[A-Za-z0-9]{20,}|"
    r"(?i:bearer)\s+[A-Za-z0-9._-]{16,}|(?i:api[_-]?key|secret|token|password)[\"']?\s*[:=]\s*[\"']?[^\s\"',}]{8,})"
)
MARKERS = ARTIFACTS / "langfuse-backfill"


def _hex(value: str, length: int = 32) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scrub(text: str) -> str:
    """Remove credential-like substrings before upload."""
    return _SECRET.sub("[redacted]", text)


def bound(text: str, limit: int = _MAX_TEXT) -> str:
    """Scrub and truncate text to a bounded upload size."""
    text = scrub(text)
    return text if len(text) <= limit else text[:limit] + f"\n[truncated {len(text) - limit} chars]"


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def _guard(path: Path) -> Path:
    if any(part in PROTECTED for part in path.parts):
        message = "protected held-out path refused outside the custodian command"
        raise PermissionError(message)
    return path


class Client:
    """Thin wrapper over the shared stdlib transport."""

    def __init__(self, config: dict[str, str]) -> None:
        """Bind validated configuration."""
        self.config = config
        self.calls = 0

    def post(self, path: str, body: object) -> dict[str, Any]:
        """Send one JSON POST, retrying transient failures (all writes are idempotent upserts)."""
        return self._retry(lambda: transport._http(self.config["LANGFUSE_BASE_URL"] + path, "POST", body, self.config))  # noqa: SLF001

    def _retry(self, call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        for attempt in range(_RETRIES):
            self.calls += 1
            try:
                return call()
            except urllib.error.HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt == _RETRIES - 1:
                    raise
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == _RETRIES - 1:
                    raise
            time.sleep(0.5 * 2**attempt)
        message = "unreachable"
        raise AssertionError(message)

    def get(self, path: str) -> dict[str, Any]:
        """Send one GET, retrying transient failures."""
        return self._retry(lambda: transport._http(self.config["LANGFUSE_BASE_URL"] + path, config=self.config))  # noqa: SLF001

    def dataset(self, name: str, description: str, metadata: dict[str, Any]) -> None:
        """Upsert a dataset by name."""
        self.post("/api/public/v2/datasets", {"name": name, "description": description, "metadata": metadata})

    def item(self, dataset: str, item_id: str, payload: dict[str, Any], metadata: dict[str, Any]) -> None:
        """Upsert one dataset item by ID."""
        self.post(
            "/api/public/dataset-items",
            {"datasetName": dataset, "id": item_id, **payload, "metadata": metadata, "status": "ACTIVE"},
        )

    def archive_stale(self, dataset: str, current: set[str]) -> int:
        """Archive active items of a dataset that are not in the current content-addressed set."""
        archived, page = 0, 1
        quoted = urllib.parse.quote(dataset, safe="")
        while True:
            listing = self.get(f"/api/public/dataset-items?datasetName={quoted}&page={page}&limit=100")
            for item in listing.get("data", []):
                if item["id"] not in current and item.get("status") != "ARCHIVED":
                    fields = {key: item.get(key) for key in ("id", "input", "expectedOutput", "metadata")}
                    self.post("/api/public/dataset-items", {"datasetName": dataset, **fields, "status": "ARCHIVED"})
                    archived += 1
            if page >= int(listing.get("meta", {}).get("totalPages", 1)):
                return archived
            page += 1

    def traces(self, spans: list[dict[str, Any]], scope: str) -> None:
        """Export spans through OTLP HTTP/JSON."""
        payload = {
            "resourceSpans": [
                {
                    "resource": {"attributes": [transport._attribute("service.name", "pdf-master-bench")]},  # noqa: SLF001
                    "scopeSpans": [{"scope": {"name": scope, "version": "1"}, "spans": spans}],
                }
            ]
        }
        response = self.post("/api/public/otel/v1/traces", payload)
        if int(response.get("partialSuccess", {}).get("rejectedSpans", 0) or 0):
            message = "Langfuse rejected spans"
            raise ValueError(message)

    def scores(self, bodies: list[dict[str, Any]]) -> None:
        """Upsert many numeric scores through batched ingestion, falling back to single requests."""
        stamp = datetime.now(UTC).isoformat()
        for start in range(0, len(bodies), _SCORE_BATCH):
            chunk = bodies[start : start + _SCORE_BATCH]
            events = [
                {"id": _hex(f"event|{body['id']}", 32), "type": "score-create", "timestamp": stamp, "body": body}
                for body in chunk
            ]
            try:
                result = self.post("/api/public/ingestion", {"batch": events})
            except urllib.error.HTTPError as error:
                if error.code not in {404, 405, 410}:
                    raise
                for body in chunk:
                    self.post("/api/public/scores", body)
                continue
            if result.get("errors"):
                message = f"Langfuse rejected {len(result['errors'])} batched scores"
                raise ValueError(message)

    def score(self, score_id: str, target: dict[str, str], name: str, value: float, comment: str = "") -> None:
        """Upsert one numeric score by ID."""
        body = {"id": score_id, **target, "name": name, "value": value, "dataType": "NUMERIC"}
        if comment:
            body["comment"] = comment
        self.post("/api/public/scores", body)


def span(trace_id: str, name: str, started: float, attributes: dict[str, Any], elapsed_ms: float = 0) -> dict[str, Any]:
    """Build one OTLP span whose ID derives from its trace."""
    start = int(started * 1_000_000_000)
    return {
        "traceId": trace_id,
        "spanId": _hex(trace_id, 16),
        "name": name,
        "kind": 1,
        "startTimeUnixNano": str(start),
        "endTimeUnixNano": str(start + int(elapsed_ms * 1_000_000)),
        "attributes": [transport._attribute(k, v) for k, v in attributes.items() if v is not None],  # noqa: SLF001
        "status": {"code": 1},
    }


def _marker(kind: str, key: str) -> Path:
    return MARKERS / kind / (_hex(key, 40) + ".json")


def _done(kind: str, key: str) -> bool:
    return _marker(kind, key).exists()


def _mark(kind: str, key: str, value: dict[str, Any]) -> None:
    path = _marker(kind, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"key": key, **value, "synced_at": time.time()}), encoding="utf-8")


# --------------------------------------------------------------------------- datasets


def _targets(directory: Path) -> dict[str, Any]:
    for name in ("gold.json", "private-targets.json"):
        path = directory / name
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return {str(row["id"]): row for row in data if isinstance(row, dict) and "id" in row}
            if isinstance(data, dict):
                return {str(key): value for key, value in data.items()}
    return {}


def _pdf_input(directory: Path, record: dict[str, Any]) -> dict[str, Any]:
    path = directory / record.get("pdf_path", f"pdfs/{record['id']}.pdf")
    entry: dict[str, Any] = {"pdf_path": _relative(path)}
    if path.is_file():
        data = path.read_bytes()
        entry |= {"pdf_sha256": _sha(data), "pdf_bytes": len(data)}
        if len(data) <= _INLINE_PDF:
            entry["pdf_base64"] = base64.b64encode(data).decode()
    return entry


def sync_manifest_corpus(  # noqa: PLR0913 - one corpus version and its labels.
    client: Client,
    directory: Path,
    dataset: str,
    description: str,
    labels: dict[str, Any],
    *,
    emit: bool = True,
) -> dict[str, Any]:
    """Upsert one ``manifest.json`` + targets corpus version as a dataset."""
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    targets = _targets(directory)
    cases = manifest.get("cases", [])
    client.dataset(
        dataset,
        description,
        {
            **labels,
            "dataset_sha256": manifest.get("dataset_sha256"),
            "label_status": manifest.get("label_status"),
            "case_count": len(cases),
            "locator": _relative(directory),
        },
    )
    matched = 0
    current = set()
    for record in cases:
        case_id = str(record["id"])
        target = targets.get(case_id)
        matched += target is not None
        pdf = _pdf_input(directory, record)
        record_fields = {k: v for k, v in record.items() if k != "pdf_path"}
        item_id = _hex(f"{dataset}|{case_id}|{pdf.get('pdf_sha256') or record.get('pdf_sha256')}")
        current.add(item_id)
        client.item(
            dataset,
            item_id,
            {"input": {"case": record_fields, **pdf}, "expectedOutput": target},
            {**labels, "case_id": case_id},
        )
    archived = client.archive_stale(dataset, current)
    status = {"dataset": dataset, "items": len(cases), "targets_matched": matched, "archived": archived}
    if emit:
        print(json.dumps(status))
    return status


def sync_dev_datasets(client: Client) -> list[dict[str, Any]]:
    """Upsert every DEV corpus version with a manifest."""
    results: list[dict[str, Any]] = []
    dev = {"split": "DEV", "heldout": False}
    for corpus, description in (
        ("silver-v1", "Generated DEV silver challenge: literal anchors and reference math (not structural gold)."),
        ("borderless-dev-v1", "Generated DEV borderless-table corpus with private authored table targets."),
        ("silver-realism-v2", "Generated DEV realism corpus with authored column/table targets."),
    ):
        for manifest in sorted(_guard(ARTIFACTS / corpus).glob("*/manifest.json")):
            directory = manifest.parent
            name = f"dev/{corpus}/{directory.name}"
            results.append(sync_manifest_corpus(client, directory, name, description, {**dev, "corpus": corpus}))
    results.append(sync_wild(client))
    results.append(sync_omnidoc(client))
    return results


def sync_wild(client: Client) -> dict[str, Any]:
    """Wild-v1 documents; per-level variants are runs, not items."""
    directory = _guard(ARTIFACTS / "wild-v1")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    name = "dev/wild-v1"
    labels = {"split": "DEV", "heldout": False, "corpus": "wild-v1"}
    client.dataset(
        name,
        "Wild-style DEV documents audited across degradation levels (see wild-v1/audit.md).",
        {**labels, "documents": manifest["documents"], "levels": manifest["level_names"]},
    )
    build = directory / "docs" / "build-report.json"
    build_report = json.loads(build.read_text(encoding="utf-8")) if build.exists() else {}
    build_rows = {row["doc_id"]: row for row in build_report.get("documents", [])}
    for doc_id in manifest["doc_ids"]:
        doc_dir = directory / "docs" / doc_id
        files = sorted(p for p in doc_dir.rglob("*") if p.is_file()) if doc_dir.is_dir() else []
        pdfs = [p for p in files if p.name == "source.pdf"] or [p for p in files if p.suffix == ".pdf"]
        payload: dict[str, Any] = {
            "doc_id": doc_id,
            "files": [
                {"path": str(p.relative_to(ROOT)), "sha256": _sha(p.read_bytes()), "bytes": p.stat().st_size}
                for p in files
            ][:64],
        }
        if pdfs and pdfs[0].stat().st_size <= _INLINE_PDF:
            payload["pdf_base64"] = base64.b64encode(pdfs[0].read_bytes()).decode()
        expected = {
            p.name: json.loads(p.read_text(encoding="utf-8"))
            for p in files
            if p.suffix == ".json" and p.stat().st_size <= _MAX_TEXT
        }
        if doc_id in build_rows:
            expected["build_report"] = build_rows[doc_id]
        client.item(
            name,
            _hex(f"{name}|{doc_id}"),
            {"input": payload, "expectedOutput": expected or None},
            {**labels, "doc_id": doc_id},
        )
    return {"dataset": name, "items": len(manifest["doc_ids"])}


def sync_omnidoc(client: Client) -> dict[str, Any]:
    """Upsert the retained 16-page OmniDocBench DEV subset with its page annotations."""
    directory = _guard(ARTIFACTS / "omnidoc-dev")
    name = "dev/omnidoc-dev"
    labels = {"split": "DEV", "heldout": False, "corpus": "omnidoc-dev", "license": "OmniDocBench upstream terms"}
    client.dataset(name, "OmniDocBench pages retained for DEV (third-party; see omnidoc-dev/README.md).", labels)
    count = 0
    for annotation in sorted((directory / "annotations").glob("*.json")):
        image = directory / "images" / annotation.name.removesuffix(".json")
        payload = {
            "page": annotation.name.removesuffix(".json"),
            "image_path": str(image.relative_to(ROOT)),
            "image_sha256": _sha(image.read_bytes()) if image.is_file() else None,
        }
        client.item(
            name,
            _hex(f"{name}|{annotation.name}"),
            {"input": payload, "expectedOutput": json.loads(annotation.read_text(encoding="utf-8"))},
            {**labels, "page": payload["page"]},
        )
        count += 1
    return {"dataset": name, "items": count}


def sync_heldout(client: Client) -> dict[str, Any]:
    """Custodian-only: upload the protected held-out set, labeled. Returns counts and hashes only."""
    registry = json.loads(HELDOUT_REGISTRY.read_text(encoding="utf-8"))
    directory = ROOT / registry["dataset_root"]
    name = f"{HELDOUT_PREFIX}/silver-heldout-v1/{directory.name[:16]}"
    description = (
        "HELD OUT - NOT FOR TRAINING, TUNING, OR DEVELOPMENT FEEDBACK. Independent silver held-out set "
        "(20 documents, 26 pages). Access only per bench/heldout-silver/AGENTS.md."
    )
    labels = {**HELDOUT_LABEL, "inventory_sha256": registry["inventory_sha256"]}
    status = sync_manifest_corpus(client, directory, name, description, labels, emit=False)
    hashes = {case["pdf_sha256"] for case in registry["cases"]}
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    uploaded = {_pdf_input(directory, case).get("pdf_sha256") for case in manifest.get("cases", [])}
    return {
        "dataset": name,
        "items": status["items"],
        "targets_matched": status["targets_matched"],
        "archived_stale_items": status["archived"],
        "registry_documents": registry["document_count"],
        "registry_hashes_matched": len(hashes & uploaded),
        "inventory_sha256": registry["inventory_sha256"],
    }


# --------------------------------------------------------------------------- runs


def sync_silver_runs(client: Client) -> list[dict[str, Any]]:
    """Each retained silver-v1 benchmark directory becomes one scored dataset run."""
    results: list[dict[str, Any]] = []
    for manifest_path in sorted(_guard(ARTIFACTS / "silver-v1").glob("*/manifest.json")):
        version = manifest_path.parent
        dataset = f"dev/silver-v1/{version.name}"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = {str(r["id"]): r for r in manifest["cases"]}
        for run_dir in sorted((version / "runs").glob("*/")):
            rows = [
                json.loads(p.read_text(encoding="utf-8")) for p in sorted(run_dir.glob("*.json")) if p.stem in records
            ]
            if not rows:
                continue
            summary_path = run_dir / "summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
            run_name = f"silver-anchors {run_dir.name}"
            if _done("silver-run", run_name):
                results.append({"run": run_name, "status": "replayed"})
                continue
            started = summary_path.stat().st_mtime if summary_path.exists() else time.time()
            spans, traces = [], {}
            for row in rows:
                trace = _hex(f"{run_name}|{row['id']}")
                traces[row["id"]] = (trace, row)
                markdown = run_dir / f"{row['id']}.md"
                attributes = {
                    "langfuse.trace.name": f"silver-v1/{row['id']}",
                    "langfuse.trace.tags": ["silver-v1", "anchor-recall"],
                    "langfuse.trace.input": {"case": row["id"], "pdf_sha256": row.get("pdf_sha256")},
                    "langfuse.trace.output": bound(markdown.read_text(encoding="utf-8")) if markdown.exists() else None,
                    "langfuse.trace.metadata.status": row.get("status"),
                    "langfuse.trace.metadata.process_wall_ms": row.get("process_wall_ms"),
                    "langfuse.trace.metadata.runner_sha256": summary.get("runner_sha256"),
                }
                spans.append(span(trace, f"silver {row['id']}", started, attributes, row.get("process_wall_ms") or 0))
            for start in range(0, len(spans), 25):
                client.traces(spans[start : start + 25], "bench.langfuse_backfill.silver")
            recalls = []
            for case_id, (trace, row) in traces.items():
                record = records[case_id]
                client.post(
                    "/api/public/dataset-run-items",
                    {
                        "runName": run_name,
                        "runDescription": "bench.silver --benchmark: visible literal anchor recall, not layout",
                        "metadata": {
                            "run_directory": str(run_dir.relative_to(ROOT)),
                            **{k: v for k, v in summary.items() if not isinstance(v, dict)},
                        },
                        "datasetItemId": _hex(f"{dataset}|{case_id}|{record.get('pdf_sha256')}"),
                        "traceId": trace,
                    },
                )
                anchors = row.get("silver_anchor_score") or {}
                if row.get("status") == "ok" and anchors.get("total"):
                    recall = anchors["found"] / anchors["total"]
                    recalls.append(recall)
                    client.score(_hex(f"{trace}|anchor"), {"traceId": trace}, "silver.anchor_recall", recall)
                client.score(
                    _hex(f"{trace}|ok"), {"traceId": trace}, "silver.completed", float(row.get("status") == "ok")
                )
            _mark("silver-run", run_name, {"documents": len(rows)})
            mean = sum(recalls) / len(recalls) if recalls else None
            results.append({"run": run_name, "status": "exported", "documents": len(rows), "mean_anchor_recall": mean})
    return results


def sync_wild_runs(client: Client) -> list[dict[str, Any]]:
    """wild-v1 audit rows: one dataset run per degradation level, scored by Markdown F1."""
    directory = _guard(ARTIFACTS / "wild-v1")
    audit_path = directory / "audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    digest = _sha(audit_path.read_bytes())[:12]
    by_level: dict[str, list[dict[str, Any]]] = {}
    for row in audit["audits"]:
        by_level.setdefault(row["level"], []).append(row)
    started = audit_path.stat().st_mtime
    results: list[dict[str, Any]] = []
    for level, rows in sorted(by_level.items()):
        run_name = f"wild-v1 audit {level} @ {digest}"
        if level.startswith("Q:"):  # Quirk rows link to dev/wild-v1-quirks by case (bench.langfuse_wild_extras).
            continue
        if _done("wild-run", run_name):
            results.append({"run": run_name, "status": "replayed"})
            continue
        spans, traces = [], []
        for row in rows:
            trace = _hex(f"{run_name}|{row['doc_id']}")
            traces.append((trace, row))
            resources = row.get("resources") or {}
            spans.append(
                span(
                    trace,
                    f"wild {row['doc_id']} {level}",
                    started,
                    {
                        "langfuse.trace.name": f"wild-v1/{row['doc_id']}/{level}",
                        "langfuse.trace.tags": ["wild-v1", level],
                        "langfuse.trace.input": {"doc_id": row["doc_id"], "level": level, "path": row.get("path")},
                        "langfuse.trace.output": bound(json.dumps(row, ensure_ascii=False)),
                        "langfuse.trace.metadata.family": row.get("family"),
                        "langfuse.trace.metadata.wall_seconds": resources.get("wall_seconds"),
                        "langfuse.trace.metadata.peak_rss_kib_self": resources.get("peak_rss_kib_self"),
                    },
                    (resources.get("wall_seconds") or 0) * 1000,
                )
            )
        for start in range(0, len(spans), 25):
            client.traces(spans[start : start + 25], "bench.langfuse_backfill.wild")
        for trace, row in traces:
            client.post(
                "/api/public/dataset-run-items",
                {
                    "runName": run_name,
                    "runDescription": f"wild-v1 audit level {level}; audit.json sha256 {digest}",
                    "metadata": {"level": level},
                    "datasetItemId": _hex(f"dev/wild-v1|{row['doc_id']}"),
                    "traceId": trace,
                },
            )
            for metric in ("f1", "precision", "recall"):
                value = (row.get("markdown") or {}).get(metric)
                if isinstance(value, (int, float)):
                    client.score(_hex(f"{trace}|{metric}"), {"traceId": trace}, f"wild.markdown_{metric}", float(value))
        _mark("wild-run", run_name, {"documents": len(rows)})
        results.append({"run": run_name, "status": "exported", "documents": len(rows)})
    return results


# --------------------------------------------------------------------------- registry


def _directory_digest(directory: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    files = size = 0
    for current, dirs, names in os.walk(directory):
        dirs.sort()
        for name in sorted(names):
            path = Path(current) / name
            stat = path.stat()
            files += 1
            size += stat.st_size
            digest.update(f"{path.relative_to(directory)}\0{stat.st_size}\0{int(stat.st_mtime)}\n".encode())
    return digest.hexdigest(), files, size


def sync_experiments(client: Client) -> list[dict[str, Any]]:
    """One registry trace per artifact directory, re-sent when its contents change."""
    results: list[dict[str, Any]] = []
    for directory in sorted(p for p in ARTIFACTS.iterdir() if p.is_dir()):
        if directory.name in PROTECTED or directory.name == MARKERS.name:
            continue
        digest, files, size = _directory_digest(directory)
        key = f"{directory.name}|{digest}"
        if _done("experiment", key):
            results.append({"experiment": directory.name, "status": "replayed"})
            continue
        top = sorted(
            (p for p in directory.iterdir() if p.is_file() and p.suffix in {".json", ".md"}),
            key=lambda p: (p.suffix != ".md", p.stat().st_size),
        )[:_MAX_REPORT_FILES]
        budget = _MAX_TEXT
        reports = {}
        for path in top:
            text = bound(path.read_text(encoding="utf-8", errors="replace"), max(budget, 0))
            reports[path.name] = text
            budget -= len(text)
            if budget <= 0:
                break
        trace = _hex(f"experiment|{key}")
        attributes = {
            "langfuse.trace.name": f"experiment/{directory.name}",
            "langfuse.trace.tags": ["experiment-registry", directory.name],
            "langfuse.trace.input": {
                "artifact_directory": str(directory.relative_to(ROOT)),
                "content_digest": digest,
                "files": files,
                "bytes": size,
                "top_level_files": sorted(p.name for p in directory.iterdir() if p.is_file())[:200],
            },
            "langfuse.trace.output": reports,
            "langfuse.trace.metadata.content_digest": digest,
            "langfuse.trace.metadata.files": files,
            "langfuse.trace.metadata.bytes": size,
        }
        client.traces(
            [span(trace, f"experiment {directory.name}", directory.stat().st_mtime, attributes)],
            "bench.langfuse_backfill.experiments",
        )
        _mark("experiment", key, {"trace_id": trace})
        results.append({"experiment": directory.name, "status": "exported", "files": files, "bytes": size})
    return results


def sync_reports(client: Client) -> dict[str, int]:
    """Export committed result summaries and the experiment log, one trace per content version."""
    paths = [*sorted((ROOT / "bench" / "results").glob("*.md")), ROOT / "EXPERIMENTS_LOG.md"]
    exported = replayed = 0
    batch: list[dict[str, Any]] = []
    keys: list[tuple[str, str]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        digest = _sha(text.encode())
        key = f"{path.relative_to(ROOT)}|{digest}"
        if _done("report", key):
            replayed += 1
            continue
        trace = _hex(f"report|{key}")
        relative = str(path.relative_to(ROOT))
        batch.append(
            span(
                trace,
                f"report {path.name}",
                path.stat().st_mtime,
                {
                    "langfuse.trace.name": f"report/{relative}",
                    "langfuse.trace.tags": ["experiment-report"],
                    "langfuse.trace.input": {"path": relative, "sha256": digest, "bytes": len(text.encode())},
                    "langfuse.trace.output": bound(text),
                },
            )
        )
        keys.append((key, trace))
        if len(batch) >= _REPORT_BATCH:
            client.traces(batch, "bench.langfuse_backfill.reports")
            for done_key, done_trace in keys:
                _mark("report", done_key, {"trace_id": done_trace})
            exported += len(batch)
            batch, keys = [], []
    if batch:
        client.traces(batch, "bench.langfuse_backfill.reports")
        for done_key, done_trace in keys:
            _mark("report", done_key, {"trace_id": done_trace})
        exported += len(batch)
    return {"exported": exported, "replayed": replayed}


def main() -> None:  # noqa: C901, PLR0912 - one dispatch per step.
    """Run the requested backfill steps and print a compact status."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "step", choices=["all", "datasets", "wild-extras", "runs", "experiments", "reports", "adapters", "heldout"]
    )
    parser.add_argument("--custodian-release", action="store_true", help="Required for the held-out upload")
    parser.add_argument("--only", action="append", help="Adapters step: run only these adapter NAMEs")
    parser.add_argument("--dry-run", action="store_true", help="Adapters step: collect and validate without network")
    parser.add_argument("--force", action="store_true", help="Adapters step: re-send runs already exported")
    parser.add_argument("--repair", action="store_true", help="Adapters step: re-post missing run-item links")
    args = parser.parse_args()
    if args.step == "adapters" and args.dry_run:
        for name, experiment in collect_all(discover(), set(args.only or []) or None):
            print(name, json.dumps(validate(experiment), ensure_ascii=False))
        return
    config = transport._configuration(ROOT)  # noqa: SLF001
    if config is None:
        sys.exit("Langfuse is not configured in .env; nothing was sent.")
    client = Client(config)
    if args.step == "heldout":
        if not args.custodian_release:
            sys.exit("The held-out upload requires --custodian-release (explicit user release).")
        print(json.dumps(sync_heldout(client)))
        return
    everything = ["datasets", "wild-extras", "runs", "adapters", "experiments", "reports"]
    steps = everything if args.step == "all" else [args.step]
    for step in steps:
        if step == "datasets":
            result: Any = sync_dev_datasets(client)
        elif step == "wild-extras":
            from bench.langfuse_wild_extras import sync_all  # noqa: PLC0415 - it imports this module.

            result = sync_all(client)
        elif step == "runs":
            result = sync_silver_runs(client) + sync_wild_runs(client)
        elif step == "adapters":
            result = []
            for name, experiment in collect_all(discover(), set(args.only or []) or None):
                status = export(client, experiment, force=args.force, repair=args.repair)
                status.pop("score_names", None)
                print(name, json.dumps(status, ensure_ascii=False), flush=True)
                result.append({"adapter": name, "dataset": experiment.dataset, "runs": status["runs"]})
        elif step == "experiments":
            result = sync_experiments(client)
        else:
            result = sync_reports(client)
        print(step, json.dumps(result, ensure_ascii=False)[:4000])
    print(f"requests: {client.calls}")


if __name__ == "__main__":
    main()
