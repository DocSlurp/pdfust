"""Sync the Markdown element-score dataset and experiment runs to Langfuse.

Uses the stdlib transport and ``.env`` configuration of ``bench.decision_langfuse``
(missing keys disable sync). Each scored fixture becomes a dataset item whose
expected output is its ground truth; each converter becomes a dataset run whose
traces hold the complete Markdown output (embedded image data replaced by its
SHA-256) and per-category numeric scores. IDs are deterministic, so re-syncing
the same outputs is idempotent; changed fixtures get new items and stale items
are archived. Only synthetic, repository-authored fixtures are sent.
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import time
from typing import TYPE_CHECKING, Any

from bench import decision_langfuse as transport

if TYPE_CHECKING:
    from pathlib import Path

DATASET = "pdf-markdown-elements-v1"
SCORE_PREFIX = "md."
_MAX_OUTPUT = 64_000
_MAX_BATCH = 2_000_000
_MARKERS = "bench/results/pdf-master-artifacts/markdown-scores/langfuse"


def _hex(value: str, length: int) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def _redact(markdown: str) -> str:
    """Replace inline base64 payloads with their hash and bound the retained text."""

    def digest(match: re.Match[str]) -> str:
        return f"data:{match.group(1)};sha256={hashlib.sha256(match.group(2).encode()).hexdigest()}"

    text = re.sub(r"data:([\w/+.-]+);base64,([A-Za-z0-9+/=]+)", digest, markdown)
    return text if len(text) <= _MAX_OUTPUT else text[:_MAX_OUTPUT] + f"\n[truncated {len(text) - _MAX_OUTPUT} chars]"


def item_id(name: str, case: dict[str, Any], pdf_sha256: str) -> str:
    """Content-addressed item ID: a changed fixture or truth creates a new item."""
    return f"{DATASET}-{name}-" + _hex(pdf_sha256 + json.dumps(case["truth"], sort_keys=True), 12)


def run_name(tool: str, meta: dict[str, Any], outputs: dict[str, str]) -> str:
    """Identify one converter run by its exact outputs and the checkout that produced them."""
    source = meta.get("source") or {}
    commit = (source.get("commit") or "unknown")[:12]
    dirty = "-dirty" if source.get("dirty") else ""
    return f"{tool} @ {commit}{dirty} out:{_hex(json.dumps(outputs, sort_keys=True), 10)}"


def _case_scores(checks: dict[str, list[float]]) -> dict[str, float]:
    scores = {category: statistics.fmean(values) for category, values in checks.items() if values}
    if scores:
        scores["case_mean"] = statistics.fmean(v for values in checks.values() for v in values)
    return scores


def _span(trace: str, name: str, started: float, elapsed_ms: float, attributes: dict[str, Any]) -> dict[str, Any]:
    start = int(started * 1_000_000_000)
    return {
        "traceId": trace,
        "spanId": _hex(trace, 16),
        "name": name,
        "kind": 1,
        "startTimeUnixNano": str(start),
        "endTimeUnixNano": str(start + int(elapsed_ms * 1_000_000)),
        "attributes": [transport._attribute(key, value) for key, value in attributes.items()],  # noqa: SLF001
        "status": {"code": 1},
    }


def _post(config: dict[str, str], path: str, body: object) -> dict[str, Any]:
    return transport._http(config["LANGFUSE_BASE_URL"] + path, "POST", body, config)  # noqa: SLF001


def _get(config: dict[str, str], path: str) -> dict[str, Any]:
    return transport._http(config["LANGFUSE_BASE_URL"] + path, config=config)  # noqa: SLF001


def _sync_dataset(config: dict[str, str], truth: dict[str, Any], hashes: dict[str, str]) -> dict[str, str]:
    _post(
        config,
        "/api/public/v2/datasets",
        {
            "name": DATASET,
            "description": "Synthetic PDFs with exact Markdown element ground truth (bench/markdown_score_cases.py).",
            "metadata": {"generator": "bench.markdown_scores", "categories": "text..links"},
        },
    )
    ids = {}
    for name, case in truth.items():
        ids[name] = item_id(name, case, hashes[name])
        _post(
            config,
            "/api/public/dataset-items",
            {
                "datasetName": DATASET,
                "id": ids[name],
                "input": {"case": name, "pdf_sha256": hashes[name], "source": case["source"], "notes": case["notes"]},
                "expectedOutput": case["truth"],
                "metadata": {"case": name},
                "status": "ACTIVE",
            },
        )
    current = set(ids.values())
    page = 1
    while True:
        listing = _get(config, f"/api/public/dataset-items?datasetName={DATASET}&page={page}&limit=100")
        for item in listing.get("data", []):
            if item["id"] not in current and item.get("status") != "ARCHIVED":
                archived = {key: item.get(key) for key in ("id", "input", "expectedOutput", "metadata")}
                _post(config, "/api/public/dataset-items", {"datasetName": DATASET, **archived, "status": "ARCHIVED"})
        if page >= int(listing.get("meta", {}).get("totalPages", 1)):
            break
        page += 1
    return ids


def _sync_run(  # noqa: PLR0913, PLR0917 - one converter run with its retained context.
    config: dict[str, str],
    tool: str,
    result: dict[str, Any],
    outputs: dict[str, str],
    ids: dict[str, str],
    name: str,
    started: float,
) -> int:
    meta = result["meta"]
    spans, traces = [], {}
    cursor = started
    for case, markdown in outputs.items():
        timing = meta["cases"].get(case, {})
        trace = _hex(f"{name}|{case}", 32)
        traces[case] = trace
        attributes = {
            "langfuse.trace.name": f"markdown-elements/{case}",
            "langfuse.trace.tags": ["markdown-scores", tool],
            "langfuse.trace.input": {"case": case, "tool": tool, "options": meta["options"]},
            "langfuse.trace.output": _redact(markdown),
            "langfuse.trace.metadata.tool": tool,
            "langfuse.trace.metadata.versions": json.dumps(meta["versions"], sort_keys=True),
            "langfuse.trace.metadata.wall_ms": timing.get("wall_ms"),
            "langfuse.trace.metadata.cpu_ms": timing.get("cpu_ms"),
            "langfuse.trace.metadata.error": timing.get("error") or "",
            "langfuse.observation.metadata.peak_rss_mib_process": meta["peak_rss_mib"],
        }
        spans.append(_span(trace, f"convert {case}", cursor, timing.get("wall_ms") or 0, attributes))
        cursor += (timing.get("wall_ms") or 0) / 1000
    payload = {
        "resourceSpans": [
            {
                "resource": {"attributes": [transport._attribute("service.name", "pdf-master-bench")]},  # noqa: SLF001
                "scopeSpans": [{"scope": {"name": "bench.markdown_score_langfuse", "version": "1"}, "spans": spans}],
            }
        ]
    }
    if len(transport._canonical(payload)) > _MAX_BATCH:  # noqa: SLF001
        message = "telemetry batch exceeds bounded admission"
        raise ValueError(message)
    response = _post(config, "/api/public/otel/v1/traces", payload)
    if int(response.get("partialSuccess", {}).get("rejectedSpans", 0) or 0):
        message = "Langfuse rejected telemetry spans"
        raise ValueError(message)
    description = f"{meta['options']}; " + ", ".join(f"{k} {v}" for k, v in meta["versions"].items())
    sent = 0
    for case, trace in traces.items():
        _post(
            config,
            "/api/public/dataset-run-items",
            {
                "runName": name,
                "runDescription": description,
                "metadata": {"tool": tool, "overall": result["overall"]},
                "datasetItemId": ids[case],
                "traceId": trace,
            },
        )
        for score, value in _case_scores(result["cases"][case]).items():
            _post(
                config,
                "/api/public/scores",
                {
                    "id": _hex(f"{trace}|{score}", 32),
                    "traceId": trace,
                    "name": SCORE_PREFIX + score.lower(),
                    "value": value,
                    "dataType": "NUMERIC",
                },
            )
            sent += 1
    return sent


def _sync_run_scores(config: dict[str, str], name: str, result: dict[str, Any]) -> bool:
    """Attach the report's check-weighted category scores to the dataset run itself."""
    from urllib.parse import quote  # noqa: PLC0415

    run = _get(config, f"/api/public/datasets/{quote(DATASET)}/runs/{quote(name, safe='')}")
    if not run.get("id"):
        return False
    values = {k: v["score"] for k, v in result["categories"].items() if v["score"] is not None}
    values["overall"] = result["overall"]
    for score, value in values.items():
        _post(
            config,
            "/api/public/scores",
            {
                "id": _hex(f"{run['id']}|{score}", 32),
                "datasetRunId": run["id"],
                "name": SCORE_PREFIX + score.lower(),
                "value": value,
                "dataType": "NUMERIC",
            },
        )
    return True


def sync(root: Path, artifacts: Path, report: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    """Upsert the dataset and every converter run; return a sanitized status."""
    try:
        config = transport._configuration(root)  # noqa: SLF001
        if config is None:
            return {"status": "disabled"}
        truth = json.loads((artifacts / "truth.json").read_text(encoding="utf-8"))
        hashes = {
            name: hashlib.sha256((artifacts / "inputs" / f"{name}.pdf").read_bytes()).hexdigest() for name in truth
        }
        ids = _sync_dataset(config, truth, hashes)
        markers = root / _MARKERS
        markers.mkdir(parents=True, exist_ok=True)
        runs: dict[str, dict[str, Any]] = {}
        for tool, result in report["tools"].items():
            directory = artifacts / "outputs" / tool
            outputs = {case: (directory / f"{case}.md").read_text(encoding="utf-8") for case in truth}
            name = run_name(tool, result["meta"], outputs)
            marker = markers / (_hex(name, 24) + ".json")
            if marker.exists() and not force:
                runs[tool] = {"run": name, "status": "replayed"}
                continue
            started = (directory / "run.json").stat().st_mtime
            scores = _sync_run(config, tool, result, outputs, ids, name, started)
            run_scores = _sync_run_scores(config, name, result)
            marker.write_text(json.dumps({"run": name, "synced_at": time.time()}), encoding="utf-8")
            runs[tool] = {"run": name, "status": "exported", "trace_scores": scores, "run_scores": run_scores}
        return {"status": "ok", "dataset": DATASET, "items": len(ids), "runs": runs}
    except Exception as error:
        return {"status": "error", "error": transport._error(error)}  # noqa: SLF001
