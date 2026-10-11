"""Freeze source-only decision experiments and transmit through the shared ledger."""

# Research artifacts preserve heterogeneous source, transport and timing receipts.
# ruff: noqa: ANN401, EM101, TRY003, PLC0415, C901, PLR0912, PLR2004, TRY301
from __future__ import annotations

import argparse
import base64
import io
import json
import time
from pathlib import Path
from typing import Any

from bench import extension_protocol as protocol
from bench.pipeline_run import Resources
from bench.silver import canonical, guard_path, sha, write_json

ROOT = Path(__file__).resolve().parents[1]
CODE_FILES = (
    "p003_extension_run.py", "extension_protocol.py", "extension_registry.py",
    "research_policy.py", "p003_client.py", "decision_hosted.py", "decision_concurrent.py",
    "decision_gateway.py", "decision_gateway_vision.py", "p003_gateway_answer.py",
    "p003_transport.py", "decision_oplog_run.py", "pipeline_repair.py",
    "pipeline_assembly.py", "decision_langfuse.py", "reprice_model_rates.py", "silver.py",
)


def read(path: Path) -> dict[str, Any]:
    """Admit a local JSON object without touching protected corpus paths."""
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise TypeError("Expected object artifact")
    return value


def image_evidence(pdf: bytes, edge: int, encoding: str) -> tuple[str | None, dict[str, Any]]:
    """Render the original PDF at each declared edge, never upscale a small preview."""
    if edge == 0:
        return None, {"image_edge": 0, "encoding": "none"}
    if edge not in (128, 256, 400, 500, 512, 768, 1024, 1200):
        raise ValueError("Unregistered image edge")
    if encoding not in {"rgb", "gray", "palette16", "blank"}:
        raise ValueError("Unregistered image encoding")
    from PIL import Image

    import pylopdf

    with pylopdf.Document(stream=pdf) as document:
        page = document[0]
        raw = page.render(scale=edge / max(page.rect.width, page.rect.height), background=(255, 255, 255))
    with Image.open(io.BytesIO(raw)) as original:
        pixels = original.convert("RGB")
    if encoding == "gray":
        pixels = pixels.convert("L")
    elif encoding == "palette16":
        pixels = pixels.quantize(colors=16)
    elif encoding == "blank":
        pixels = Image.new("RGB", pixels.size, "white")
    output = io.BytesIO()
    pixels.save(output, format="PNG")
    data = output.getvalue()
    return "data:image/png;base64," + base64.b64encode(data).decode(), {
        "image_edge": edge, "encoding": encoding, "size": list(pixels.size),
        "image_sha256": sha(data), "encoded_bytes": len(data), "codec": "PNG",
    }


def prepare(corpus: Path, output: Path, config: dict[str, Any], ids: list[str]) -> dict[str, Any]:
    """Freeze complete menus and actual wire bodies before any target evaluation."""
    corpus, output = guard_path(corpus), guard_path(output)
    if output.exists():
        raise FileExistsError("Experiment directory must be new")
    run_id = config["run_id"]
    if not run_id.startswith("extension-v1-") or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in run_id):
        raise ValueError("New extension namespace required")
    manifest = read(corpus / "manifest.json")
    if manifest.get("split") != "DEV":
        raise ValueError("Explicit DEV manifest required")
    if len(set(ids)) != len(ids) or not ids or len(ids) > 256:
        raise ValueError("Invalid intended page inventory")
    lookup = {p["id"]: p for p in manifest["pages"]}
    if not set(ids) <= set(lookup):
        raise ValueError("Page is outside source manifest")
    inventory = read(corpus / "source-inventory.json")["artifacts"]
    output.mkdir(parents=True)
    (output / "pages").mkdir()
    (output / "code").mkdir()
    rows = []
    with Resources() as resources:
        for ident in ids:
            record = lookup[ident]
            path = corpus / "menus" / (ident + ".json")
            raw = guard_path(path).read_bytes()
            if sha(raw) != inventory[f"menus/{ident}.json"]:
                raise ValueError("Source menu changed since corpus freeze")
            menu = json.loads(raw)
            if sha(canonical(menu["source"])) != menu["source_sha256"]:
                raise ValueError("Menu source digest mismatch")
            pdf = guard_path(Path(record["pdf_path"])).read_bytes()
            if sha(pdf) != record["pdf_sha256"]:
                raise ValueError("Source PDF changed since corpus freeze")
            row = {"id": ident, "pdf_sha256": record["pdf_sha256"], "menu_sha256": sha(raw),
                   "baseline_state": menu["baseline"], "source": menu["source"]}
            try:
                url, image = image_evidence(pdf, config["edge"], config["encoding"])
                packet = protocol.build_request(
                    menu["source"], [c["state"] for c in menu["candidates"]],
                    model=config["model"], provider=config["provider"], mode=config["mode"],
                    max_words=config["max_words"], max_bytes=config["max_bytes"], image_url=url,
                )
                if len(canonical(packet["body"])) > 750_000:
                    raise ValueError("Actual wire exceeds shared transport admission")
                row.update(packet=packet, image=image, preparation_status="ready")
            except (ValueError, TypeError, KeyError) as error:
                row.update(preparation_status="preparation_error", error=type(error).__name__ + ": " + str(error))
            write_json(output / "pages" / (ident + ".json"), row)
            rows.append({"id": ident, "sha256": sha((output / "pages" / (ident + ".json")).read_bytes()),
                         "preparation_status": row["preparation_status"]})
    code = {}
    for name in CODE_FILES:
        raw = Path(__file__).with_name(name).read_bytes()
        (output / "code" / name).write_bytes(raw)
        code[name] = sha(raw)
    frozen = {
        "version": 1, "config": config, "corpus": str(corpus),
        "manifest_sha256": sha((corpus / "manifest.json").read_bytes()),
        "source_inventory_sha256": sha((corpus / "source-inventory.json").read_bytes()),
        "pages": rows, "code_sha256": code, "prepared_at": time.time(),
        "resources": resources.summary(), "references_read": False,
    }
    write_json(output / "frozen.json", frozen)
    return frozen


def run(output: Path, *, client: Any = None) -> dict[str, Any]:
    """Transmit once per ready page, with no fallback, replay or inline retry."""
    output = guard_path(output)
    frozen = read(output / "frozen.json")
    for name, digest in frozen["code_sha256"].items():
        if name not in CODE_FILES or sha(Path(__file__).with_name(name).read_bytes()) != digest:
            raise ValueError("Runtime changed after request freeze")
        if sha((output / "code" / name).read_bytes()) != digest:
            raise ValueError("Archived runtime changed")
    if set(frozen["code_sha256"]) != set(CODE_FILES):
        raise ValueError("Incomplete runtime inventory")
    pages = []
    for row in frozen["pages"]:
        path = output / "pages" / (row["id"] + ".json")
        if sha(path.read_bytes()) != row["sha256"]:
            raise ValueError("Frozen page packet changed")
        pages.append(read(path))
    # Exclusive marker rejects re-entry before constructing clients or admitting money.
    with (output / "started.json").open("x") as handle:
        json.dump({"started_at": time.time(), "replay": False}, handle)
    config = frozen["config"]
    if client is None:
        if config["provider"] == "openrouter":
            from bench.p003_client import P003ConcurrentClient
            client = P003ConcurrentClient(ROOT)
        else:
            from bench.decision_gateway import GatewayDecisionClient
            from bench.decision_gateway_vision import GatewayVisionDecisionClient
            client_type = GatewayVisionDecisionClient if config["model"] == "liquid/d1" else GatewayDecisionClient
            client = client_type(ROOT)
    prefix = "P003/" + config["run_id"] + "/"
    results, stopped = [], False
    with Resources() as resources:
        for page in pages:
            ident = page["id"]
            result = {"id": ident, "baseline_state": page["baseline_state"], "selected_state": None}
            if page["preparation_status"] != "ready":
                result.update(status="preparation_error", error=page["error"])
            elif stopped:
                result.update(status="not_attempted", error="Arm stopped after transport failure")
            else:
                packet = page["packet"]
                started = time.perf_counter()
                try:
                    receipt = client.request(packet["body"], tag=prefix + ident, replay=False, max_body_bytes=750_000)
                except Exception as error:
                    stopped = True
                    result.update(status="transport_error", error=type(error).__name__)
                else:
                    write_json(output / (ident + "-receipt.json"), receipt)
                    result.update(entry=receipt["entry"], usage=receipt["result"].get("usage", {}),
                                  receipt_sha256=sha((output / (ident + "-receipt.json")).read_bytes()))
                    try:
                        parsed = protocol.parse_choice(receipt["result"], packet)
                        result.update(parsed, status="abstained" if parsed["abstained"] else "selected")
                    except (ValueError, TypeError, KeyError) as error:
                        result.update(status="invalid", error=type(error).__name__ + ": " + str(error))
                result["client_wall_seconds"] = time.perf_counter() - started
            results.append(result)
            write_json(output / "progress.json", {"config": config, "completed": len(results),
                       "intended": len(pages), "results": results, "observed_at": time.time()})
    from bench.p003_gate_run import charges
    entries = [e for e in read(client.ledger)["requests"] if e.get("tag", "").startswith(prefix)]
    accounting = charges(entries)
    accounting["cost_scope"] = "Fresh extension arm API attempts only; local preparation and remote hardware unpriced"
    measured = resources.summary()
    effective = accounting["effective_usd"]
    selected = sum(r["status"] == "selected" for r in results)
    report = {"version": 1, "config": config, "frozen_sha256": sha((output / "frozen.json").read_bytes()),
              "results": results, "resources": measured, "preparation_resources": frozen["resources"],
              "costs": accounting, "intended_pages": len(pages), "selected_pages": selected,
              "rates": {"intended_pages_per_minute": len(pages) * 60 / measured["wall_seconds"],
                        "selected_pages_per_minute": selected * 60 / measured["wall_seconds"],
                        "intended_pages_per_dollar": len(pages) / effective if effective else None,
                        "selected_pages_per_dollar": selected / effective if effective else None,
                        "scope": "Whole arm execution excluding measured preparation; selected is not quality success"},
              "completed_at": time.time()}
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Require an explicit hosted flag; preparation is always CPU-only."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    if args.action == "prepare":
        if not args.corpus or not args.config or not args.ids:
            parser.error("Preparation requires corpus, config and explicit page IDs")
        result = prepare(args.corpus, args.directory, read(args.config), args.ids)
        print(json.dumps({"directory": str(args.directory), "pages": len(result["pages"])}))
    else:
        if not args.run_hosted:
            parser.error("Transmission requires --run-hosted")
        result = run(args.directory)
        print(json.dumps({"directory": str(args.directory), "intended": result["intended_pages"],
                          "selected": result["selected_pages"], "costs": result["costs"]}))


if __name__ == "__main__":
    main()
