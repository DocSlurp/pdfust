"""Synthetic image-transport controls, explicitly separate from PDF quality scores."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import time
from pathlib import Path
from typing import Any, NoReturn

from PIL import Image, ImageDraw

from bench.decision_gateway import ENDPOINT as TYPESAFE_ENDPOINT
from bench.decision_gateway import GatewayDecisionClient, request_identity
from bench.decision_gateway_vision import ENDPOINT as NATIVE_ENDPOINT
from bench.decision_gateway_vision import MODEL, GatewayVisionDecisionClient, translate
from bench.decision_hosted import ROOT, checkpoint, exclusive_lock
from bench.lowlevel_run import wave_admission
from bench.reprice_model_rates import number, request_cost
from bench.silver import guard_path, rss_bytes

EDGE = 512


def controls() -> list[dict[str, Any]]:
    """Return identical-prompt circle/square/blank/no-image protocol controls.

    The control name and expected shape stay local. Each native wire request is
    derived losslessly from the same canonical body used by the old protocol.
    This tests transport consumption; these are not PDF extraction test scores.
    """
    records = []
    for control in ("circle", "square", "blank", "no-image"):
        body: dict[str, Any] = {
            "model": MODEL,
            "state": "Inspect the provided image.",
            "questions": {
                "q0": {
                    "type": "choice",
                    "instructions": "What large black shape is visible? Use unresolved when no shape can be seen.",
                    "criteria": {"circle": "A circle", "square": "A square", "unresolved": "No visible shape"},
                }
            },
        }
        raster = None
        if control != "no-image":
            bitmap = Image.new("RGB", (EDGE, EDGE), "white")
            painter = ImageDraw.Draw(bitmap)
            bounds = (EDGE // 4, EDGE // 4, EDGE * 3 // 4, EDGE * 3 // 4)
            if control == "circle":
                painter.ellipse(bounds, fill="black")
            elif control == "square":
                painter.rectangle(bounds, fill="black")
            output = io.BytesIO()
            bitmap.save(output, format="PNG", optimize=True)
            raster = output.getvalue()
            body["images"] = ["data:image/png;base64," + base64.b64encode(raster).decode()]
        records.append(
            {
                "control": control,
                "expected": control if control in {"circle", "square"} else "unresolved",
                "scope": "synthetic image transport validation; not PDF quality",
                "pixels": [EDGE, EDGE] if raster is not None else None,
                "png_bytes": len(raster) if raster is not None else None,
                "png_sha256": hashlib.sha256(raster).hexdigest() if raster is not None else None,
                "canonical_body": body,
                "native_body": translate(body),
            }
        )
    return records


EXPERIMENT = "L017"
PREFIX = "L017/"
WAVE_LIMIT = 3.0
MAX_BODY_BYTES = 200_000
PROBABILITY_TOLERANCE = 1e-6
PROTOCOLS = ("typesafe", "native")


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _encoded(value: Any) -> bytes:  # noqa: ANN401
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode()


def _file(directory: Path, name: str) -> Path:
    if Path(name).name != name:
        _fail("Sanity artifact must be a basename")
    directory = guard_path(directory).resolve()
    path = guard_path(directory / name).resolve()
    if not path.is_relative_to(directory):
        _fail("Sanity artifact escapes the freeze")
    return path


def _inventory() -> tuple[dict[str, Any], dict[str, bytes]]:
    records: list[dict[str, Any]] = []
    bodies: dict[str, bytes] = {}
    for control in controls():
        for protocol, field in (("typesafe", "canonical_body"), ("native", "native_body")):
            raw = _encoded(control[field])
            filename = f"request-{len(records):02d}.json"
            bodies[filename] = raw
            records.append(
                {
                    "protocol": protocol,
                    "control": control["control"],
                    "expected": control["expected"],
                    "request": filename,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
    return {
        "experiment": EXPERIMENT,
        "records": records,
        "scope": "synthetic protocol validation, not PDF quality",
        "wave_limit_usd": WAVE_LIMIT,
    }, bodies


def verify(directory: Path) -> dict[str, Any]:
    """Require the exact original driver order, manifest and request bytes."""
    manifest, bodies = _inventory()
    frozen = json.loads(_file(directory, "manifest.json").read_bytes())
    if frozen != manifest:
        _fail("Sanity manifest differs from the original frozen control matrix")
    for name, expected in bodies.items():
        if _file(directory, name).read_bytes() != expected:
            _fail("Sanity request bytes changed")
    provenance = _file(directory, "freeze.json")
    if provenance.exists():
        metadata = json.loads(provenance.read_bytes())
        if metadata["manifest_sha256"] != hashlib.sha256(_file(directory, "manifest.json").read_bytes()).hexdigest():
            _fail("Sanity manifest provenance changed")
        if (
            metadata["catalog_sha256"]
            != hashlib.sha256(_file(directory, "catalog-prices.json").read_bytes()).hexdigest()
        ):
            _fail("Sanity frozen catalog changed")
    return frozen


def prepare(directory: Path, *, catalog: Path | None = None) -> dict[str, Any]:
    """Freeze locally; reuse identical artifacts without overwriting retained results."""
    started, cpu = time.perf_counter(), time.process_time()
    directory = guard_path(directory)
    manifest, bodies = _inventory()
    manifest_path = _file(directory, "manifest.json")
    if manifest_path.exists():
        return verify(directory)
    if _file(directory, "results.json").exists():
        _fail("Refuse results without their original manifest")
    for name, raw in bodies.items():
        if _file(directory, name).exists() and _file(directory, name).read_bytes() != raw:
            _fail("Refuse differing existing request bytes")
    catalog = guard_path(
        catalog or ROOT / "bench/results/pdf-master-artifacts/decisions/langfuse/gateway-catalog-prices.json"
    )
    prices = catalog.read_bytes()
    if MODEL not in json.loads(prices)["prices"]:
        _fail("Sanity Gateway catalog lacks d1")
    directory.mkdir(parents=True, exist_ok=True)
    for name, raw in bodies.items():
        _file(directory, name).write_bytes(raw)
    checkpoint(manifest_path, manifest)
    _file(directory, "catalog-prices.json").write_bytes(prices)
    checkpoint(
        _file(directory, "freeze.json"),
        {
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "catalog_sha256": hashlib.sha256(prices).hexdigest(),
            "catalog_source": str(catalog),
            "preparation_resources": _resources(started, cpu),
        },
    )
    return verify(directory)


def _results(directory: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    path = _file(directory, "results.json")
    results = json.loads(path.read_bytes()) if path.exists() else {"calls": []}
    digest = hashlib.sha256(_file(directory, "manifest.json").read_bytes()).hexdigest()
    if results.get("manifest_sha256", digest) != digest:
        _fail("Sanity retained results belong to a different manifest")
    inventory = {(row["protocol"], row["sha256"]): row for row in manifest["records"]}
    seen = set()
    for row in results["calls"]:
        identity = (row["protocol"], row["sha256"])
        record = inventory.get(identity)
        if identity in seen or record is None or any(row.get(key) != value for key, value in record.items()):
            _fail("Sanity retained result inventory changed")
        seen.add(identity)
        entry = row.get("entry")
        if isinstance(entry, dict):
            endpoint = TYPESAFE_ENDPOINT if row["protocol"] == "typesafe" else NATIVE_ENDPOINT
            raw = _file(directory, record["request"]).read_bytes()
            if (
                entry.get("request_sha256") != record["sha256"]
                or entry.get("endpoint") != endpoint
                or entry.get("request_identity_sha256") != request_identity(raw, endpoint=endpoint)
            ):
                _fail("Sanity retained ledger endpoint identity changed")
    return results


def _resources(started: float, cpu: float) -> dict[str, Any]:
    return {
        "wall_seconds": time.perf_counter() - started,
        "cpu_seconds": time.process_time() - cpu,
        "peak_rss_bytes": rss_bytes(),
        "scope": "serial current process counters and lifetime VmHWM; no sampling; provider CPU/RAM unmeasured",
    }


def _choice(result: dict[str, Any]) -> str:
    answers = result.get("answers")
    if not isinstance(answers, dict) or set(answers) != {"q0"}:
        _fail("Sanity response must answer q0 only")
    answer = answers["q0"]
    if not isinstance(answer, dict) or answer.get("type") != "choice":
        _fail("Sanity response must contain a Choice")
    probabilities = answer.get("probabilities")
    menu = {"circle", "square", "unresolved"}
    if not isinstance(probabilities, dict) or set(probabilities) != menu:
        _fail("Sanity probabilities do not match the control menu")
    values = [number(probabilities[key]) for key in menu]
    if any(value is None or value > 1 for value in values):
        _fail("Sanity probability values are invalid")
    if abs(sum(value for value in values if value is not None) - 1) > PROBABILITY_TOLERANCE:
        _fail("Sanity probability sum is invalid")
    choice = answer.get("choice")
    if choice not in menu or probabilities[choice] != max(probabilities.values()):
        _fail("Sanity choice is outside the menu or is not maximal")
    return choice


def _entries(client: Any) -> list[dict[str, Any]]:  # noqa: ANN401
    return json.loads(client.ledger.read_bytes())["requests"] if client.ledger.exists() else []


def _cost(row: dict[str, Any], rates: dict[str, Any]) -> dict[str, Any] | None:
    entry = row.get("entry")
    if not isinstance(entry, dict):
        return row.get("cost")
    return request_cost(entry, row.get("result", {}).get("usage", {}), entry.get("catalog_rates", rates))


def run(directory: Path, *, clients: dict[str, Any] | None = None) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Explicit root-only execution with independent stops and one persistent wave cap."""
    manifest = verify(directory)
    catalog = _file(directory, "catalog-prices.json")
    if clients is None:
        if not catalog.exists():
            _fail("Legacy freeze execution requires a retained catalog; report remains available")
        clients = {
            "typesafe": GatewayDecisionClient(catalog_path=catalog),
            "native": GatewayVisionDecisionClient(catalog_path=catalog),
        }
    if set(clients) != set(PROTOCOLS) or clients["typesafe"].ledger != clients["native"].ledger:
        _fail("Sanity protocols must share the same budget ledger")
    for protocol in PROTOCOLS:
        if clients[protocol].endpoint != (TYPESAFE_ENDPOINT if protocol == "typesafe" else NATIVE_ENDPOINT):
            _fail("Sanity client endpoint differs from the frozen protocol")
    path = _file(directory, "results.json")
    with exclusive_lock(clients["native"].ledger.parent / "run.lock"):
        verify(directory)
        results = _results(directory, manifest)
        manifest_hash = hashlib.sha256(_file(directory, "manifest.json").read_bytes()).hexdigest()
        if results.get("manifest_sha256", manifest_hash) != manifest_hash:
            _fail("Sanity retained results belong to a different manifest")
        results.update(manifest_sha256=manifest_hash, status="running")
        done = {(row["protocol"], row["sha256"]) for row in results["calls"] if row["status"] in {"ok", "failed"}}
        stopped = {row["protocol"] for row in results["calls"] if row["status"] == "failed"}
        entries = _entries(clients["native"])
        for protocol in PROTOCOLS:
            if any(
                entry.get("tag", "").startswith(PREFIX + protocol + "/")
                and (entry.get("error") or not entry.get("response_file"))
                for entry in entries
            ):
                stopped.add(protocol)
        started, cpu = time.perf_counter(), time.process_time()
        exhausted = False
        checkpoint(path, results)
        for record in manifest["records"]:
            identity = (record["protocol"], record["sha256"])
            if identity in done:
                continue
            row = next((r for r in results["calls"] if (r["protocol"], r["sha256"]) == identity), None)
            if row is None:
                row = dict(record)
                results["calls"].append(row)
            protocol = record["protocol"]
            if protocol in stopped or exhausted:
                row.update(
                    status="unattempted", reason="persistent protocol stop" if protocol in stopped else "wave cap"
                )
                checkpoint(path, results)
                continue
            client = clients[protocol]
            raw = _file(directory, record["request"]).read_bytes()
            endpoint_hash = request_identity(raw, endpoint=client.endpoint)
            tag = PREFIX + protocol + "/" + record["sha256"]
            try:
                entries = _entries(client)
                known = next(
                    (
                        e
                        for e in entries
                        if e.get("gateway") == "vercel" and e.get("request_identity_sha256") == endpoint_hash
                    ),
                    None,
                )
                if known is None:
                    wave_admission(entries, tag_prefix=PREFIX, wave_limit=WAVE_LIMIT)
                answer = client.request(json.loads(raw), tag=tag, max_body_bytes=MAX_BODY_BYTES)
                row.update(status="ok", **answer)
                row["choice"] = _choice(answer["result"])
                row["cost"] = _cost(row, {})
            except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
                row.update(status="failed", error_type=type(error).__name__)
                retained: dict[str, Any] | None = next(
                    (
                        e
                        for e in reversed(_entries(client))
                        if e.get("gateway") == "vercel" and e.get("request_identity_sha256") == endpoint_hash
                    ),
                    None,
                )
                if retained:
                    row.setdefault("entry", retained)
                    row["cost"] = _cost(row, {})
                if "persistent wave cap exhausted" in str(error):
                    exhausted = True
                    row.update(status="unattempted", reason="wave cap before transmission")
                else:
                    stopped.add(protocol)
            if row["status"] in {"ok", "failed"}:
                done.add(identity)
            checkpoint(path, results)
        results.setdefault("execution_sessions", []).append(_resources(started, cpu))
        results.update(
            status="complete",
            planned_bodies=len(manifest["records"]),
            completed_bodies=len(done),
            protocol_stops=sorted(stopped),
            budget_exhausted=exhausted,
        )
        checkpoint(path, results)
        return results


def report(directory: Path) -> dict[str, Any]:
    """Render retained controls locally; never instantiate a client or score PDF quality."""
    manifest = verify(directory)
    results = _results(directory, manifest)
    catalog = _file(directory, "catalog-prices.json")
    rates = json.loads(catalog.read_bytes())["prices"].get(MODEL, {}) if catalog.exists() else {}
    rows = []
    for record in manifest["records"]:
        retained: dict[str, Any] = next(
            (
                row
                for row in results["calls"]
                if row["protocol"] == record["protocol"] and row["sha256"] == record["sha256"]
            ),
            {},
        )
        status, choice = retained.get("status", "unattempted"), None
        if status == "ok":
            try:
                choice = _choice(retained["result"])
            except (ValueError, TypeError, KeyError):
                status = "parser refusal"
        cost = _cost(retained, rates)
        entry = retained.get("entry") or {}
        rows.append(
            {
                **record,
                "status": status,
                "choice": choice,
                "correct": choice == record["expected"] if choice else None,
                "input_tokens": retained.get("result", {}).get("usage", {}).get("input_tokens"),
                "cost": cost,
                "reservation_usd": entry.get("accounted_usd") if entry.get("cost_status") == "reserved" else None,
                "elapsed_ms": number(entry.get("elapsed_ms")),
                "replayed": retained.get("replayed", False),
                "request_identity_sha256": request_identity(
                    _file(directory, record["request"]).read_bytes(),
                    endpoint=TYPESAFE_ENDPOINT if record["protocol"] == "typesafe" else NATIVE_ENDPOINT,
                ),
                "safe_diagnostics": entry.get("http_error_diagnostic"),
            }
        )
    lines = [
        "# Gateway image-consumption sanity controls",
        "",
        (
            "Synthetic transport validation; not PDF extraction quality. "
            "HTTP acceptance alone does not establish image consumption."
        ),
        "",
        (
            "| Protocol | Control | Expected | Choice | Status | Input tokens | "
            "Effective USD | Reserved USD | Retained HTTP ms |"
        ),
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in rows:
        cost = row["cost"]["effective_usd"] if row["cost"] else None
        lines.append(
            "| "
            + " | ".join(
                str(value) if value is not None else "unmeasured"
                for value in [
                    row["protocol"],
                    row["control"],
                    row["expected"],
                    row["choice"],
                    row["status"],
                    row["input_tokens"],
                    cost,
                    row["reservation_usd"],
                    row["elapsed_ms"],
                ]
            )
            + " |"
        )
    outcomes = {}
    for protocol in PROTOCOLS:
        cohort = [row for row in rows if row["protocol"] == protocol]
        passed = all(row["status"] == "ok" and row["correct"] for row in cohort)
        outcomes[protocol] = "sanity passed" if passed else "image consumption remains unverified"
        lines.extend(
            [
                "",
                (
                    f"{protocol}: {outcomes[protocol]}. All four controls must match, "
                    "including opposite shape choices and blank/no-image abstention."
                ),
            ]
        )
    completed = sum(row["status"] in {"ok", "failed", "parser refusal"} for row in rows)
    lines.extend(
        [
            "",
            (
                f"Planned bodies: {len(rows)}; completed: {completed}. "
                f"Wave cap: ${WAVE_LIMIT:.2f}, including unknown reservations."
            ),
            "",
            (
                "Reported charges and catalog estimates remain separate from unknown reservations. "
                "Replays incur no fresh HTTP transmission; absent latency stays unmeasured."
            ),
            "",
            "Local resources: "
            + json.dumps({key: results.get(key) for key in ("resources", "execution_sessions")}, sort_keys=True),
            "",
        ]
    )
    summary = {
        "experiment": EXPERIMENT,
        "planned_bodies": len(rows),
        "completed_bodies": completed,
        "rows": rows,
        "protocol_outcomes": outcomes,
    }
    _file(directory, "report.md").write_text("\n".join(lines))
    checkpoint(_file(directory, "evaluation.json"), summary)
    return summary


def main() -> None:
    """Default to a CPU-only retained report; enable preparation/transmission explicitly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory",
        type=Path,
        default=ROOT / "bench/results/pdf-master-artifacts/decisions/lowlevel-v1/gateway-sanity",
    )
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare(args.directory, catalog=args.catalog)
    if args.run_hosted:
        run(args.directory)
    summary = report(args.directory)
    print(
        json.dumps(
            {key: summary[key] for key in ("experiment", "planned_bodies", "completed_bodies", "protocol_outcomes")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
