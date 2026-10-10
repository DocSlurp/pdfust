"""Root-only pure model admission of authenticated source-owned structure proposals."""

# ruff: noqa: ANN401, EM101, TRY003, TRY301, C901, PLR0913, PLR0912, PLR2004
from __future__ import annotations

import argparse
import base64
import html
import json
import shutil
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench import p003_structure_admission as admission
from bench.decision_hosted import ROOT
from bench.p003_boundary_run import RESERVATION, _charges, _entries, _error, _identifier
from bench.p003_client import P003ConcurrentClient, P003DecisionClient
from bench.p003_gate_run import authenticate as authenticate_source
from bench.p003_micro_relations_run import CODE_FILES as COMMON_CODE
from bench.p003_topology_ownership import _choices
from bench.pipeline_repair import MAX_PACKET_BYTES, validate
from bench.pipeline_run import Resources
from bench.silver import canonical, guard_path, sha, write_json

if TYPE_CHECKING:
    from collections.abc import Callable

ARMS = ("detector", "fullpage", "residual", "density")
EDGES = (0, 128, 512)
CODE_FILES = tuple(
    dict.fromkeys(
        (
            "p003_structure_admission_run.py",
            "p003_structure_admission.py",
            "p003_structure_geometry.py",
            "p003_structure_acquisition_infer.py",
            "p003_structure_density_infer.py",
            "p003_gate_run.py",
            *COMMON_CODE,
        )
    )
)


def read(path: Path) -> Any:
    """Read only explicitly selected guarded evidence paths."""
    return json.loads(guard_path(path).read_bytes())


def configuration(model: str, acquisition: str, threshold: float, edge: int, concurrency: int) -> dict[str, Any]:
    """Declare one model and one source-only treatment; prohibit implicit switching."""
    if model not in admission.MODELS or acquisition not in ARMS or threshold not in (0.3, 0.5, 0.7):
        raise ValueError("Explicit admitted model/acquisition/threshold required")
    if type(edge) is not int or edge not in EDGES or type(concurrency) is not int or concurrency not in (1, 3):
        raise ValueError("Explicit image edge 0/128/512 and transport capacity 1/3 required")
    return {
        "processor": "p003_structure_admission",
        "campaign": "P003",
        "model": model,
        "provider": "openrouter",
        "acquisition": acquisition,
        "threshold": threshold,
        "image_edge": edge,
        "treatment": "text" if edge == 0 else f"rgb{edge}",
        "transport_concurrency": concurrency,
        "workers": 1,
        "replay": False,
        "retry": False,
        "model_fallback": False,
        "baseline_credit": False,
        "pure_model": True,
        "page_atomic_failure": True,
        "full_page_denominator": 16,
        "scope": "Incremental table-admission decisions on retained OCR/TATR evidence; excludes acquisition",
    }


def authenticate_pool(pool: Path, trusted: dict[str, str], source_trusted: dict[str, str]) -> dict[str, Any]:
    """Rebuild all source-only candidates, pixels and exact bodies under external trust."""
    pool = guard_path(pool)
    frozen, report = read(pool / "frozen.json"), read(pool / "report.json")
    if frozen.get("references_read") is not False or frozen.get("hosted_calls") != 0:
        raise ValueError("Admission pool must be frozen source-only evidence without hosted answers")
    if not trusted or not source_trusted:
        raise ValueError("Independent pool and source trusted code maps required")
    if set(frozen["code_sha256"]) != {
        "p003_structure_admission.py",
        "p003_structure_geometry.py",
        "pipeline_assembly.py",
        "pipeline_repair.py",
        "generalization_vision_regions.py",
    }:
        raise ValueError("Frozen pool lacks the complete explicit replay code inventory")
    for name, digest in frozen["code_sha256"].items():
        _identifier(name)
        if (
            trusted.get(name) != digest
            or sha((pool / "code" / name).read_bytes()) != digest
            or (
                name != "generalization_vision_regions.py"
                and sha(Path(__file__).with_name(name).read_bytes()) != digest
            )
        ):
            raise ValueError("Admission pool code differs from external trust or local replay code")
    sources = read(pool / report["source_inventory_path"])
    if sha((pool / report["source_inventory_path"]).read_bytes()) != report["source_inventory_sha256"]:
        raise ValueError("Complete source inventory changed")
    if sources["intended_page_count"] != 16 or len(sources["pages"]) != 16:
        raise ValueError("Admission treatment requires complete explicit DEV16 inventory")
    ids = [p["id"] for p in sources["pages"]]
    if len(set(ids)) != 16:
        raise ValueError("Duplicate intended page")
    authenticated = {}
    for receipt in report["source_trust_receipts"]:
        baseline = guard_path(Path(receipt["baseline_directory"]))
        if receipt["intended_page_ids"] != ids:
            raise ValueError("Acquisition source inventory differs")
        if baseline not in authenticated:
            authenticated[baseline] = authenticate_source(baseline, source_trusted)
        # The externally supplied source map authorizes embedded map content, never conversely.
        if read(Path(receipt["trusted_map_path"])) != source_trusted:
            raise ValueError("Embedded acquisition source trust differs from external authority")
        for kind in ("source_manifest", "geometry_report"):
            if sha(guard_path(Path(receipt[kind + "_path"])).read_bytes()) != receipt[kind + "_sha256"]:
                raise ValueError("Acquisition provenance changed")
    pages = {}
    for page in sources["pages"]:
        ident = _identifier(page["id"])
        baseline = guard_path(Path(page["baseline_directory"]))
        original_frozen, original_report = authenticated[baseline]
        records = {r["id"]: r for r in original_frozen["records"]}
        rows = {r["id"]: r for r in original_report["results"]}
        raw = (pool / page["source_path"]).read_bytes()
        if (
            records.get(ident) != page["record"]
            or sha(raw) != page["source_sha256"]
            or json.loads(raw) != rows[ident]["source"]
            or sha((baseline / (ident + "-result.json")).read_bytes()) != page["baseline_result_sha256"]
        ):
            raise ValueError("Complete original source differs")
        pages[ident] = {**page, "source": json.loads(raw)}
    # Never execute archived code: use authenticated current pure helpers on retained raw geometry.
    with tempfile.TemporaryDirectory(prefix="p003-admission-rebuild-", dir=pool.parent) as temp:
        rebuilt = Path(temp) / "pool"
        replay = admission.prepare(
            {
                receipt["arm"]: guard_path(Path(frozen["arms"][receipt["arm"]]))
                for receipt in report["source_trust_receipts"]
            },
            rebuilt,
        )
        for key in ("entries", "excluded", "source_trust_receipts", "source_inventory_sha256"):
            if replay[key] != report[key]:
                raise ValueError("Source-only admission replay differs")
        # All prepared images, full literals and provider request artifacts remain byte-identical.
        for path in rebuilt.rglob("*"):
            if (
                path.is_file()
                and path.name not in {"report.json", "frozen.json"}
                and "code" not in path.relative_to(rebuilt).parts
            ):
                relative = path.relative_to(rebuilt)
                if path.read_bytes() != (pool / relative).read_bytes():
                    raise ValueError("Frozen admission artifact differs from source-only reconstruction")
    return {"frozen": frozen, "report": report, "pages": pages, "baselines": authenticated}


def prepare(
    pool: Path, trusted: dict[str, str], source_trusted: dict[str, str], output: Path, config: dict[str, Any]
) -> dict[str, Any]:
    """Freeze every selected input and request before any hosted client is constructed."""
    pool, output = guard_path(pool), guard_path(output)
    if output.exists():
        raise FileExistsError("Admission output must be fresh")
    prepared = authenticate_pool(pool, trusted, source_trusted)
    selected = []
    for entry in prepared["report"]["entries"]:
        if entry["arm"] != config["acquisition"] or entry["threshold"] != config["threshold"]:
            continue
        candidate = read(pool / entry["folder"] / "candidate.json")
        variant = next(v for v in entry["variants"] if v["treatment"] == config["treatment"])
        candidate["question_status"] = variant["packet"]["status"]
        body = None
        if candidate["question_status"] == "prepared":
            text = (pool / entry["folder"] / (config["treatment"] + "-packet.json")).read_text()
            url = None
            if config["image_edge"]:
                raw = (pool / entry["folder"] / (config["treatment"] + ".png")).read_bytes()
                url = "data:image/png;base64," + base64.b64encode(raw).decode()
            body = admission.request(config["model"], text, url)
            receipt = next(r for r in variant["requests"] if r["model"] == config["model"])
            encoded = json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
            if sha(encoded) != receipt["request_sha256"] or body != read(pool / entry["folder"] / receipt["path"]):
                raise ValueError("Selected request wire bytes differ")
        selected.append({"page_id": entry["page_id"], "candidate": candidate, "variant": variant, "body": body})
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(pool, output / "pool")
    for name, arm in prepared["frozen"]["arms"].items():
        _identifier(name)
        for kind in ("source", "geometry"):
            shutil.copytree(guard_path(Path(arm)) / kind, output / "acquisition" / name / kind)
    (output / "code").mkdir()
    code = {}
    for name in CODE_FILES:
        path = Path(__file__).with_name(name)
        shutil.copyfile(path, output / "code" / name)
        code[name] = sha(path.read_bytes())
    for i, item in enumerate(selected):
        item["index"] = i
        if item["body"] is not None:
            write_json(output / f"candidate-{i}-request.json", item["body"])
            (output / f"candidate-{i}-wire.json").write_bytes(
                json.dumps(item["body"], separators=(",", ":"), allow_nan=False).encode()
            )
    for i, baseline in enumerate(prepared["baselines"]):
        shutil.copytree(baseline, output / "baselines" / str(i))
    inventory = {str(p.relative_to(output)): sha(p.read_bytes()) for p in output.rglob("*") if p.is_file()}
    frozen = {
        "config": config,
        "records": [p["record"] for p in prepared["pages"].values()],
        "manifest_sha256": next(iter(prepared["baselines"].values()))[0]["manifest_sha256"],
        "pool": {
            "directory": str(pool.resolve()),
            "frozen_sha256": sha((pool / "frozen.json").read_bytes()),
            "report_sha256": sha((pool / "report.json").read_bytes()),
            "trusted_code": trusted,
        },
        "source_trusted_code": source_trusted,
        "baselines": [
            {
                "directory": str(baseline),
                "archive": f"baselines/{i}",
                "frozen_sha256": sha((baseline / "frozen.json").read_bytes()),
                "report_sha256": sha((baseline / "report.json").read_bytes()),
                "config": original[0]["config"],
                "historical_effective_usd": original[1].get("effective_usd"),
                "historical_metrics": original[1].get("metrics"),
                "scope": "Historical source extraction only; excluded from incremental admission totals",
            }
            for i, (baseline, original) in enumerate(prepared["baselines"].items())
        ],
        "code_sha256": code,
        "artifact_sha256": inventory,
        "selected": [{k: v for k, v in item.items() if k != "body"} for item in selected],
        "all_inputs_frozen_before_client": True,
        "references_read": False,
    }
    write_json(output / "frozen.json", frozen)
    return {**prepared, "selected": selected, "run_frozen": frozen}


def markdown(page: dict[str, Any], state: dict[str, Any]) -> str:
    """Emit literal cells with spans and all outside words, without inventing headers."""
    if len(canonical(page)) > MAX_PACKET_BYTES:
        raise ValueError("Complete source exceeds 2MiB rendering admission; no truncation")
    validate(page, state)
    lookup = {w["id"]: w for w in page["words"]}
    entries: list[tuple[int, str]] = []
    order = {w["id"]: i for i, w in enumerate(page["words"])}
    for table in state["tables"]:
        spans = {(s["row"], s["column"]): s for s in table["spans"]}
        text = ["<table>"]
        for r, row in enumerate(table["values"]):
            text.append("<tr>")
            for c, value in enumerate(row):
                if value is None:
                    continue
                span = spans.get((r, c), {"row_span": 1, "column_span": 1})
                attrs = f' rowspan="{span["row_span"]}" colspan="{span["column_span"]}"'
                text.append(f"<td{attrs}>{html.escape(value)}</td>")
            text.append("</tr>")
        text.append("</table>")
        owned = [i for cell in table["cells"] for i in cell["source_ids"]]
        entries.append((min((order[i] for i in owned), default=len(order)), "\n".join(text)))
    lines: dict[tuple[Any, ...], list[str]] = {}
    for ident in state["unresolved_ids"]:
        word = lookup[ident]
        line = tuple(word.get("line", [round(word["bbox"][1], 1)]))
        lines.setdefault(line, []).append(ident)
    entries.extend(
        (min(order[i] for i in ids), "<p>" + html.escape(" ".join(lookup[i]["text"] for i in ids)) + "</p>")
        for ids in lines.values()
    )
    return "\n\n".join(text for _, text in sorted(entries)) + "\n"


def receipt(result: Any) -> dict[str, Any]:
    """Require one exact native answer and complete raw, uncalibrated menu probabilities."""
    if not isinstance(result, dict) or not isinstance(result.get("answers"), dict) or set(result["answers"]) != {"q0"}:
        raise ValueError("Expected exact native admission question q0")
    return _choices(result["answers"]["q0"], admission.CHOICES)


def client_for(config: dict[str, Any], _prepared: dict[str, Any]) -> Any:
    """Root constructs the single shared-policy OpenRouter client after freezing inputs."""
    return P003ConcurrentClient(ROOT) if config["transport_concurrency"] == 3 else P003DecisionClient(ROOT)


def execute(
    prepared: dict[str, Any],
    output: Path,
    config: dict[str, Any],
    *,
    client_factory: Callable[..., Any] = client_for,
    entries_reader: Callable[..., list[dict[str, Any]]] = _entries,
) -> dict[str, Any]:
    """Perform independent distinct admissions once, then source-safe atomic page assembly."""
    prefix = f"P003/{config['run_id']}/structure-admission/"
    error = None
    try:
        client = client_factory(config, prepared)
    except Exception as exc:
        client, error = None, _error(exc, "client_initialization")
    stopped, decisions = client is None, []
    with Resources() as resources:
        for item in prepared["selected"]:
            i = item["index"]
            row = {
                "index": i,
                "candidate_id": item["candidate"]["id"],
                "page_id": item["page_id"],
                "model": config["model"],
                "status": "not_attempted",
            }
            if item["body"] is None:
                row["status"] = "no_question_refusal"
            elif stopped:
                row["reason"] = "first transport failure or initialization failure; no further admission"
            else:
                began, cpu = time.perf_counter(), time.process_time()
                try:
                    response = client.request(
                        item["body"],
                        tag=prefix + str(i),
                        replay=False,
                        reservation_usd=RESERVATION,
                        max_body_bytes=750_000,
                    )
                except Exception as exc:
                    row.update(status="transport_error", error=_error(exc, "transport"))
                    stopped = True
                else:
                    write_json(output / f"candidate-{i}-response.json", response)
                    returned = response.get("result")
                    returned_entry = response.get("entry")
                    row.update(
                        entry=response.get("entry"),
                        replayed=response.get("replayed"),
                        usage=returned.get("usage", {}) if isinstance(returned, dict) else {},
                        admission_wait_seconds=response.get(
                            "admission_wait_seconds",
                            returned_entry.get("admission_wait_seconds") if isinstance(returned_entry, dict) else None,
                        ),
                    )
                    try:
                        if response.get("replayed"):
                            raise ValueError("Fresh pure admission cannot use replayed answers")
                        parsed = receipt(response["result"])
                        row.update(status=parsed["choice"], receipt=parsed)
                    except (ValueError, KeyError, TypeError) as exc:
                        row.update(status="malformed_response", error=_error(exc, "parse"))
                row.update(
                    client_wall_seconds=time.perf_counter() - began, client_cpu_seconds=time.process_time() - cpu
                )
            decisions.append(row)
            write_json(output / f"candidate-{i}-result.json", row)
            write_json(output / "decision-results.json", {"decisions": decisions})
        results = []
        for ident, page in prepared["pages"].items():
            items = [x for x in prepared["selected"] if x["page_id"] == ident]
            rows = [r for r in decisions if r["page_id"] == ident]
            failed = any(r["status"] not in admission.CHOICES for r in rows)
            choices = {
                r["candidate_id"]: r["status"] if r["status"] in admission.CHOICES and not failed else None
                for r in rows
            }
            applied = admission.apply(page["source"], [x["candidate"] for x in items], choices)
            state = applied["state"]
            row = {
                "id": ident,
                "status": "error" if failed else "ok",
                "source": page["source"],
                "state": state,
                "tables": state["tables"],
                "unresolved_ids": state["unresolved_ids"],
                "admission_receipts": applied["admission_receipts"],
                "decision_results": rows,
                "decision_status": "failed_closed" if failed else "evaluated" if rows else "no_candidate",
                "source_conserved": True,
                "baseline_credit": False,
                "model": config["model"],
                "pure_model": True,
                "predicted_table_count": len(state["tables"]),
            }
            write_json(output / (ident + "-state.json"), state)
            write_json(output / (ident + "-structure.json"), row["tables"])
            (output / (ident + ".md")).write_text(markdown(page["source"], state))
            write_json(output / (ident + "-result.json"), row)
            results.append(row)
    entries = entries_reader(client, prefix) if client is not None else []
    charges = _charges(entries)
    charges["cost_scope"] = (
        "Incremental structure-admission API attempts only, including failures; "
        "excludes OCR/TATR and historical baseline costs"
    )
    attempted = sum(r["status"] not in {"not_attempted", "no_question_refusal"} for r in decisions)
    if attempted and not entries:
        charges.update(effective_usd=None, provider_reported_usd=None, accounting_status="unmeasured missing attempts")
    metrics = resources.summary()
    measured, cost = metrics["wall_seconds"], charges["effective_usd"]
    complete = sum(r["status"] == "ok" for r in results)
    report = {
        "config": config,
        "results": results,
        "decisions": decisions,
        "client_initialization_error": error,
        "historical_baseline_provenance": prepared.get("run_frozen", {}).get("baselines", []),
        "decision_status_counts": dict(Counter(r["status"] for r in decisions)),
        "page_status_counts": dict(Counter(r["status"] for r in results)),
        "intended_page_count": 16,
        "valid_completed_page_count": complete,
        "attempted_question_count": attempted,
        "incremental_admission": {
            "metrics": metrics,
            "charges": charges,
            "scope": config["scope"],
            "denominator": 16,
            "intended_pages_per_minute": 16 / measured * 60 if measured else None,
            "valid_completed_pages_per_minute": complete / measured * 60 if measured else None,
            "intended_pages_per_dollar": 16 / cost if cost and cost > 0 else None,
            "valid_completed_pages_per_dollar": complete / cost if cost and cost > 0 else None,
        },
        "full_pipeline_pages_per_minute": None,
        "full_pipeline_pages_per_dollar": None,
        "model_fallbacks": 0,
        "retries": 0,
        "baseline_credit": False,
        "references_read": False,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def run(
    pool: Path,
    trusted_code: Path,
    source_trusted_code: Path,
    output: Path,
    *,
    model: str,
    acquisition: str,
    threshold: float,
    image_edge: int,
    transport_concurrency: int = 3,
    run_hosted: bool = False,
    client_factory: Callable[..., Any] = client_for,
    entries_reader: Callable[..., list[dict[str, Any]]] = _entries,
) -> dict[str, Any]:
    """Require explicit root opt-in; preparation completes before client construction."""
    if not run_hosted:
        raise ValueError("Root-only --run-hosted required")
    config = {
        **configuration(model, acquisition, threshold, image_edge, transport_concurrency),
        "run_id": _identifier(output.name),
    }
    with Resources() as preparation_resources:
        prepared = prepare(pool, read(trusted_code), read(source_trusted_code), output, config)
    preprocessing = {
        **preparation_resources.summary(),
        "scope": "source authentication and all input/code freezing",
    }
    write_json(output / "preprocessing-resources.json", preparation_resources.samples)
    report = execute(prepared, output, config, client_factory=client_factory, entries_reader=entries_reader)
    report["preprocessing"] = preprocessing
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Explicit independent root-paid arms, OpenRouter only, no fallback or retry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--trusted-code", type=Path, required=True)
    parser.add_argument("--source-trusted-code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=admission.MODELS, required=True)
    parser.add_argument("--acquisition", choices=ARMS, required=True)
    parser.add_argument("--threshold", type=float, choices=(0.3, 0.5, 0.7), required=True)
    parser.add_argument("--image-edge", type=int, choices=EDGES, required=True)
    parser.add_argument("--transport-concurrency", type=int, choices=(1, 3), default=3)
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    report = run(
        args.input,
        args.trusted_code,
        args.source_trusted_code,
        args.output,
        model=args.model,
        acquisition=args.acquisition,
        threshold=args.threshold,
        image_edge=args.image_edge,
        transport_concurrency=args.transport_concurrency,
        run_hosted=args.run_hosted,
    )
    print(
        json.dumps(
            {
                "page_status_counts": report["page_status_counts"],
                "decision_status_counts": report["decision_status_counts"],
                "incremental_admission": report["incremental_admission"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
