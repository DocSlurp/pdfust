"""Shared shape and writer for Langfuse experiment adapters.

An adapter turns one experiment's retained artifacts into ``Experiment``
objects: a dataset of ``Item``s (inputs plus expected outputs) and one or more
``Run``s whose ``Row``s hold each item's output and numeric scores. The writer
upserts everything with deterministic IDs, so re-running is idempotent and a
changed run (different rows or scores) is exported under the same run name
with new content.

Rules for adapters:

- Report the experiment's own metrics; never invent a score. Failed, errored,
  and abstained rows stay in the run, scored as the experiment scored them
  (usually 0 or omitted with ``metadata["status"]``), so denominators match
  the retained report.
- Booleans become 1.0/0.0. Leave a metric out rather than guessing it.
- Never read ``silver-heldout-v1`` or ``bench/heldout-silver`` (``guard``).
- Keep inputs/outputs compact. The writer scrubs and bounds text, but adapters
  should reference large files by path and SHA-256 instead of inlining them.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

if TYPE_CHECKING:
    from collections.abc import Iterable

    from bench.langfuse_backfill import Client

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "bench" / "results" / "pdf-master-artifacts"
PROTECTED = ("silver-heldout-v1", "heldout-silver")
MAX_FIELD = 64_000
SPAN_BATCH = 25
WORKERS = int(os.environ.get("LANGFUSE_WORKERS", "8"))
RUN_WORKERS = int(os.environ.get("LANGFUSE_RUN_WORKERS", "4"))


@dataclass
class Item:
    """One dataset entry. ``key`` must be unique within the dataset."""

    key: str
    input: Any
    expected: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Row:
    """One item's result within a run."""

    item_key: str
    output: Any
    scores: dict[str, float | bool | int | None] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    input: Any = None
    wall_ms: float | None = None
    started: float | None = None
    name: str | None = None


@dataclass
class Run:
    """One configuration/model/variant evaluated over the dataset."""

    name: str
    description: str
    rows: list[Row]
    metadata: dict[str, Any] = field(default_factory=dict)
    scores: dict[str, float | bool | int | None] = field(default_factory=dict)
    started: float | None = None


@dataclass
class Experiment:
    """A dataset plus its runs, sourced from one retained artifact location."""

    dataset: str
    description: str
    items: list[Item]
    runs: list[Run]
    source: str
    labels: dict[str, Any] = field(default_factory=lambda: {"split": "DEV", "heldout": False})


def guard(path: Path) -> Path:
    """Refuse protected held-out paths."""
    if any(part in PROTECTED for part in path.parts):
        message = "protected held-out path refused"
        raise PermissionError(message)
    return path


def read_json(path: Path) -> Any:  # noqa: ANN401 - arbitrary retained JSON.
    """Read JSON from a guarded path."""
    return json.loads(guard(path).read_text(encoding="utf-8"))


def file_ref(path: Path) -> dict[str, Any]:
    """Return a path, size, and SHA-256 reference instead of inlining file content."""
    data = guard(path).read_bytes()
    relative = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    return {"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def canonical(value: object) -> str:
    """Return deterministic JSON for hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def digest(value: object, length: int = 32) -> str:
    """Hash any JSON-serializable value."""
    return hashlib.sha256(canonical(value).encode()).hexdigest()[:length]


def clean_scores(scores: dict[str, Any]) -> dict[str, float]:
    """Keep finite numeric scores; booleans become 1.0/0.0."""
    cleaned = {}
    for name, value in scores.items():
        if isinstance(value, bool) or (isinstance(value, (int, float)) and math.isfinite(value)):
            cleaned[name] = float(value)
    return cleaned


def _compact(value: Any) -> Any:  # noqa: ANN401 - arbitrary JSON.
    """Return JSON unchanged when small and credential-free; otherwise scrubbed, bounded text."""
    from bench.langfuse_backfill import bound, scrub  # noqa: PLC0415 - avoid an import cycle.

    if value is None:
        return None
    if isinstance(value, str):
        return bound(value, MAX_FIELD)
    text = canonical(value)
    if len(text) <= MAX_FIELD and scrub(text) == text:
        return json.loads(text)
    return bound(text, MAX_FIELD)


def _scalar(value: Any) -> Any:  # noqa: ANN401 - arbitrary metadata.
    """Keep scalars; JSON-encode structured metadata instead of dropping it."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return _compact(canonical(value))


def item_id(dataset: str, item: Item) -> str:
    """Content-addressed dataset item ID."""
    return digest([dataset, item.key, item.input, item.expected])


def validate(experiment: Experiment) -> dict[str, Any]:
    """Check internal consistency and return counts without any network access."""
    keys = [item.key for item in experiment.items]
    if len(keys) != len(set(keys)):
        message = f"{experiment.dataset}: duplicate item keys"
        raise ValueError(message)
    known = set(keys)
    names = [run.name for run in experiment.runs]
    if len(names) != len(set(names)):
        message = f"{experiment.dataset}: duplicate run names"
        raise ValueError(message)
    rows = scores = 0
    for run in experiment.runs:
        for row in run.rows:
            if row.item_key not in known:
                message = f"{experiment.dataset}/{run.name}: row for unknown item {row.item_key!r}"
                raise ValueError(message)
            rows += 1
            scores += len(clean_scores(row.scores))
    canonical([item.input for item in experiment.items])
    return {
        "dataset": experiment.dataset,
        "items": len(experiment.items),
        "runs": len(experiment.runs),
        "rows": rows,
        "row_scores": scores,
        "score_names": sorted({n for run in experiment.runs for row in run.rows for n in clean_scores(row.scores)}),
    }


def export(client: Client, experiment: Experiment, *, force: bool = False, repair: bool = False) -> dict[str, Any]:  # noqa: C901
    """Upsert the dataset, items, runs, traces, and scores for one experiment.

    With ``repair``, already-exported runs re-post only the run-item links that
    Langfuse is missing (traces and scores are written independently).
    """
    from bench.langfuse_backfill import _done, _mark, span  # noqa: PLC0415 - avoid an import cycle.

    counts = validate(experiment)
    labels = {**experiment.labels, "source": experiment.source}
    client.dataset(experiment.dataset, experiment.description, labels)
    ids = {item.key: item_id(experiment.dataset, item) for item in experiment.items}

    def put_item(item: Item) -> None:
        client.item(
            experiment.dataset,
            ids[item.key],
            {"input": _compact(item.input), "expectedOutput": _compact(item.expected)},
            {**labels, **item.metadata, "item_key": item.key},
        )

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(put_item, experiment.items))
    archived = client.archive_stale(experiment.dataset, set(ids.values()))

    dataset_id: list[str] = []

    def existing_links(run: Run) -> set[str]:
        if not dataset_id:
            dataset_id.append(client.get(f"/api/public/v2/datasets/{quote(experiment.dataset, safe='')}")["id"])
        found: set[str] = set()
        page = 1
        while True:
            listing = client.get(
                f"/api/public/dataset-run-items?datasetId={dataset_id[0]}&runName={quote(run.name, safe='')}"
                f"&page={page}&limit=100"
            )
            found.update(entry["traceId"] for entry in listing.get("data", []))
            if page >= int(listing.get("meta", {}).get("totalPages", 1) or 1):
                return found
            page += 1

    def run_links(run: Run, content: str) -> list[tuple[str, Row]]:
        return [
            (digest([experiment.dataset, run.name, content, row.item_key, index]), row)
            for index, row in enumerate(run.rows)
        ]

    def post_links(run: Run, pairs: list[tuple[str, Row]]) -> None:
        run_meta = {k: _scalar(v) for k, v in run.metadata.items()}

        def link(pair: tuple[str, Row]) -> None:
            trace, row = pair
            client.post(
                "/api/public/dataset-run-items",
                {
                    "runName": run.name,
                    "runDescription": run.description[:1000],
                    "metadata": run_meta,
                    "datasetItemId": ids[row.item_key],
                    "traceId": trace,
                },
            )

        if not pairs:
            return
        # The first run item creates the dataset run; posting it alone avoids a
        # create race that makes Langfuse drop concurrent links.
        link(pairs[0])
        with ThreadPoolExecutor(WORKERS) as pool:
            list(pool.map(link, pairs[1:]))

    def export_run(run: Run) -> str:
        content = digest([run.name, run.metadata, run.scores, [(r.item_key, r.output, r.scores) for r in run.rows]])
        marker = f"{experiment.dataset}|{run.name}|{content}"
        if not force and _done("adapter-run", marker):
            if not repair:
                return "replayed"
            present = existing_links(run)
            missing = [pair for pair in run_links(run, content) if pair[0] not in present]
            post_links(run, missing)
            return f"repaired:{len(missing)}" if missing else "replayed"
        started = run.started or time.time()
        traces = run_links(run, content)
        spans = []
        for trace, row in traces:
            attributes = {
                "langfuse.trace.name": row.name or f"{experiment.dataset}/{row.item_key}",
                "langfuse.trace.tags": ["experiment-run", experiment.dataset.split("/")[0]],
                "langfuse.trace.input": _compact({"item": row.item_key, **({"input": row.input} if row.input else {})}),
                "langfuse.trace.output": _compact(row.output),
                **{f"langfuse.trace.metadata.{k}": _scalar(v) for k, v in row.metadata.items() if v is not None},
                "langfuse.trace.metadata.run": run.name,
            }
            spans.append(span(trace, run.name, row.started or started, attributes, row.wall_ms or 0))
        for start in range(0, len(spans), SPAN_BATCH):
            client.traces(spans[start : start + SPAN_BATCH], "bench.langfuse_adapters")
        post_links(run, traces)
        client.scores(
            [
                {"id": digest([trace, name]), "traceId": trace, "name": name, "value": value, "dataType": "NUMERIC"}
                for trace, row in traces
                for name, value in clean_scores(row.scores).items()
            ]
        )
        run_scores = clean_scores(run.scores)
        if run_scores:
            path = f"/api/public/datasets/{quote(experiment.dataset, safe='')}/runs/{quote(run.name, safe='')}"
            try:
                found = client.get(path)
            except OSError:
                found = {}
            if found.get("id"):
                client.scores(
                    [
                        {
                            "id": digest([found["id"], name]),
                            "datasetRunId": found["id"],
                            "name": name,
                            "value": value,
                            "dataType": "NUMERIC",
                        }
                        for name, value in run_scores.items()
                    ]
                )
        _mark("adapter-run", marker, {"rows": len(run.rows)})
        return "exported"

    with ThreadPoolExecutor(RUN_WORKERS) as runs_pool:
        outcomes = list(runs_pool.map(export_run, experiment.runs))
    exported, replayed = outcomes.count("exported"), outcomes.count("replayed")
    repaired = sum(int(outcome.split(":", 1)[1]) for outcome in outcomes if outcome.startswith("repaired:"))
    return {
        **counts,
        "archived": archived,
        "runs_exported": exported,
        "runs_replayed": replayed,
        "links_repaired": repaired,
    }


def collect_all(adapters: Iterable[Any], only: set[str] | None = None) -> Iterable[tuple[str, Experiment]]:
    """Yield experiments from every registered adapter module."""
    for module in adapters:
        if only and module.NAME not in only:
            continue
        for experiment in module.collect(ARTIFACTS):
            yield module.NAME, experiment
