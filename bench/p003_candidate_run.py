"""Opt-in whole-crop ranking of authenticated frozen vision_regions repeats.

No generation, detector, extraction, reference lookup or inference occurs on import.
Root owns the shared P003 client; frozen pool costs remain historical provenance.
"""

# Isolated retained benchmark dictionaries and explicit trust/transport boundaries.
# ruff: noqa: ANN401, EM101, TRY003, PLC0415, C901, PLR0912, PLR0913, PLR2004, PLR0917, TRY301, TRY004
from __future__ import annotations

import argparse
import base64
import binascii
import io
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bench import generalization_vision_regions as regions
from bench import p003_candidate_choice as chooser
from bench import p003_candidate_diff as differences
from bench import p003_selector_image as selector_image
from bench import p003_selector_visibility as selector_visibility
from bench import pipeline_run
from bench import pipeline_vision_transcription as transcription
from bench.decision_hosted import DECISION_MODELS
from bench.generalization_report import verify_output
from bench.p003_boundary_run import _charges, _entries, _error, _identifier, _reserve_wave
from bench.silver import guard_path, sha, write_json

if TYPE_CHECKING:
    from collections.abc import Callable

IMAGE_MODELS = (
    "openai/gpt-6-luna-decisions",
    "perplexity/pplx-decider-v1.1-27b",
    "cloudflare/clef-flash",
    "cloudflare/clef",
    "cloudflare/clef-omni",
)
EDGES = (0, 128, 256, 400, 500, 512, 768, 1024, 1200)
ROOT_REVIEWED_PARSER_SHA256 = frozenset(
    {
        "8188aca8439f7c4bf455bf81b55a7a3e9f0789ca3590abbd3042d050b784591e",
    }
)
CODE_FILES = (
    "decision_concurrent.py",
    "decision_hosted.py",
    "decision_gateway.py",
    "decision_langfuse.py",
    "reprice_model_rates.py",
    "research_policy.py",
    "p003_client.py",
    "p003_candidate_run.py",
    "p003_candidate_choice.py",
    "p003_boundary_run.py",
    "pipeline_vision_transcription.py",
    "pipeline_frontier.py",
    "generalization_vision_regions.py",
    "generalization_report.py",
    "pipeline_run.py",
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(guard_path(path).read_bytes())
    if not isinstance(value, dict):
        raise ValueError("Retained artifact must be a JSON object")
    return value


def _crop_bytes(body: dict[str, Any]) -> tuple[str, bytes]:
    images = [
        part["image_url"]["url"]
        for message in body.get("messages", [])
        for part in (message.get("content") if isinstance(message.get("content"), list) else [])
        if isinstance(part, dict) and part.get("type") == "image_url"
    ]
    if len(images) != 1:
        raise ValueError("Candidate generation request must retain exactly one original crop")
    url = images[0]
    if (
        not isinstance(url, str)
        or not url.startswith("data:image/")
        or ";base64," not in url
        or len(url) > 16 * 1024 * 1024
    ):
        raise ValueError("Candidate crop must be bounded inline base64 pixels")
    try:
        data = base64.b64decode(url.split(";base64,", 1)[1], validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("Invalid retained crop encoding") from error
    if not data:
        raise ValueError("Candidate crop cannot be empty")
    return url, data


def authenticate(
    directory: Path,
    trusted: dict[str, str],
    *,
    reviewed_parser_sha256: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """Authenticate all archived code against an independent operator-supplied map."""
    if any(
        not isinstance(digest, str) or digest not in ROOT_REVIEWED_PARSER_SHA256 for digest in reviewed_parser_sha256
    ):
        raise ValueError("Historical parser digest lacks an explicit root compatibility review")
    frozen, report = _read(directory / "frozen.json"), _read(directory / "report.json")
    if frozen["config"].get("processor") != "vision_regions" or report["config"].get("processor") != "vision_regions":
        raise ValueError("Candidate ranking targets vision_regions baseline format only")
    hashes = frozen.get("code_sha256")
    required = {
        "pipeline_vision_transcription.py",
        "pipeline_frontier.py",
        "generalization_vision_run.py",
        "generalization_vision_regions.py",
        "pipeline_run.py",
    }
    if not isinstance(hashes, dict) or not required <= set(hashes):
        raise ValueError("Baseline lacks complete required authenticated vision-region code")
    for name, digest in hashes.items():
        _identifier(name)
        if (
            not name.endswith(".py")
            or trusted.get(name) != digest
            or sha(guard_path(directory / "code" / name).read_bytes()) != digest
        ):
            raise ValueError("Baseline archived code differs from independent trusted map")
    # No archived source is executed. Require the strict local adapter to match its authenticated version.
    parser_digest = hashes.get("pipeline_vision_transcription.py")
    if parser_digest != sha(Path(transcription.__file__).read_bytes()) and parser_digest not in reviewed_parser_sha256:
        raise ValueError("Authenticated candidate parser differs from current strict replay adapter")
    records = frozen["records"]
    results = {row["id"]: row for row in report["results"]}
    if len(results) != len(report["results"]) or set(results) != {record["id"] for record in records}:
        raise ValueError("Baseline report differs from frozen source inventory")
    for record in records:
        _identifier(record["id"])
        page = results[record["id"]]
        if page["status"] == "ok" and page.get("pdf_sha256") != record["pdf_sha256"]:
            raise ValueError("Retained generation source differs from frozen PDF hash")
        verify_output(directory, page, processor="vision_regions")
    return frozen, report, hashes


def _rerender(
    record: dict[str, Any], page_result: dict[str, Any], crop: dict[str, Any], edge: int
) -> tuple[str, dict[str, Any]]:
    """Render exact global crop geometry at an independently declared image edge."""
    from PIL import Image

    import pylopdf

    data = guard_path(Path(record["pdf_path"])).read_bytes()
    if sha(data) != record["pdf_sha256"]:
        raise ValueError("Frozen selector source PDF hash changed")
    with pylopdf.open(stream=data) as document:
        page = document[record["page_number"]]
        if list(page.rect) != page_result["viewport"] or page.rotation != page_result["original_rotation"]:
            raise ValueError("Selector rerender geometry differs from frozen generation source")
        scale = 4095 / max(page.rect.width, page.rect.height)
        pixels = page.render(scale=scale, background=(255, 255, 255))
    with Image.open(io.BytesIO(pixels)) as rendered:
        image = rendered.convert("RGB")
        x0, y0, x1, y1 = page_result["viewport"]
        a, b, c, d = crop["viewport"]
        pixel_box = [
            (a - x0) * image.width / (x1 - x0),
            (b - y0) * image.height / (y1 - y0),
            (c - x0) * image.width / (x1 - x0),
            (d - y0) * image.height / (y1 - y0),
        ]
        ratio = edge / max(pixel_box[2] - pixel_box[0], pixel_box[3] - pixel_box[1])
        size = (
            max(1, round((pixel_box[2] - pixel_box[0]) * ratio)),
            max(1, round((pixel_box[3] - pixel_box[1]) * ratio)),
        )
        crop_image = image.transform(size, Image.Transform.EXTENT, pixel_box, resample=Image.Resampling.BICUBIC)
        encoded = io.BytesIO()
        crop_image.save(encoded, format="JPEG", quality=90)
        payload = encoded.getvalue()
    return "data:image/jpeg;base64," + base64.b64encode(payload).decode(), {
        "image_edge": edge,
        "image_size": list(size),
        "image_viewport": crop["viewport"],
        "image_sha256": sha(payload),
        "image_bytes": len(payload),
        "image_codec": "JPEG",
        "image_quality": 90,
        "rerendered": True,
    }


def _body(
    pool: chooser.Pool,
    model: str,
    url: str,
    edge: int,
    *,
    evidence_mode: str = "whole",
    evidence_max_bytes: int = differences.DEFAULT_MAX_BYTES,
) -> dict[str, Any]:
    if evidence_mode not in {"whole", "differences"}:
        raise ValueError("Unknown candidate evidence mode")
    body = (
        differences.request(pool, model, url, max_bytes=evidence_max_bytes)
        if evidence_mode == "differences"
        else chooser.request(pool, model, url)
    )
    if not edge:
        body["state"] = body["state"][0]
        body["questions"]["q0"]["instructions"] = (
            "This is a text-only control: source pixels are unavailable. Compare supplied alternatives only, "
            "and choose unresolved when literal comparison cannot establish faithfulness. "
            + body["questions"]["q0"]["instructions"].replace(
                "against the attached source crop", "with the original source image unavailable"
            )
        )
    return body


def process(
    record: dict[str, Any],
    page_results: list[dict[str, Any]],
    inputs: list[Path],
    output: Path,
    config: dict[str, Any],
    client: Any,
    *,
    image_factory: Callable[..., tuple[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Stage same-crop selections and compose once; failures keep first baseline bytes."""
    started, cpu = time.perf_counter(), time.process_time()
    identifier = _identifier(record["id"])
    first = page_results[0]
    result = deepcopy(first)
    result.update(ranking_status="not_applicable", ranking_calls=[], ranking_errors=[], ranking_regions=[])
    result["candidate_generation_provenance"] = [
        {
            "baseline_index": i,
            "status": page["status"],
            "calls": deepcopy(page.get("calls", [])),
            "wall_seconds": page.get("wall_seconds"),
            "cpu_seconds": page.get("cpu_seconds"),
        }
        for i, page in enumerate(page_results)
    ]
    for suffix in ("-structure.json", ".md"):
        source = inputs[0] / f"{identifier}{suffix}"
        if source.exists():
            (output / source.name).write_bytes(source.read_bytes())
    prefix = f"P003/{config['run_id']}/{identifier}/"
    stage = "baseline_eligibility"
    try:
        if first["status"] != "ok":
            result["ranking_status"] = "baseline_failed_skipped"
            return result
        if any(page["status"] != "ok" for page in page_results):
            result["ranking_status"] = "not_applicable_baseline_failure"
            return result
        if any(page["viewport"] != first["viewport"] for page in page_results):
            raise ValueError("Same-crop generation page viewports differ")
        proposal_keys = ("index", "request_index", "viewport", "detector_box")
        expected = [{k: region[k] for k in proposal_keys} for region in first["transcription_regions"]]
        for page in page_results[1:]:
            if [{k: region[k] for k in proposal_keys} for region in page["transcription_regions"]] != expected:
                raise ValueError("Frozen generation crop inventories differ; no matched pool")
        staged, choices = deepcopy(first["transcription_regions"]), 0
        for index, original in enumerate(first["transcription_regions"]):
            stage = f"crop/{index}/pool"
            crops = [page["transcription_regions"][index] for page in page_results]
            candidates, urls, image_hashes = [], [], []
            for baseline_index, crop in enumerate(crops):
                body = _read(inputs[baseline_index] / f"{identifier}-request-{crop['request_index']}.json")
                url, image_bytes = _crop_bytes(body)
                expected_body = transcription.request(body["model"], url, crop["viewport"], body["max_tokens"])
                provider = _read(inputs[baseline_index] / "frozen.json")["config"].get("generation_provider")
                if provider:
                    expected_body["provider"] = {
                        "only": [provider],
                        "allow_fallbacks": False,
                        "require_parameters": True,
                    }
                encoded_body = json.dumps(expected_body, separators=(",", ":")).encode()
                if body != expected_body or sha(encoded_body) != crop["request"]["body_sha256"]:
                    raise ValueError("Retained generation request differs from strict original request")
                if (
                    sha(image_bytes) != crop["image"]["image_sha256"]
                    or crop["image"]["image_viewport"] != crop["viewport"]
                    or crop["image"]["image_bytes"] != len(image_bytes)
                ):
                    raise ValueError("Actual generation crop bytes differ from recorded hash or viewport")
                urls.append(url)
                image_hashes.append(sha(image_bytes))
                candidates.append(transcription.parse(crop["transcription_response"], crop["viewport"]))
            if len(set(image_hashes)) != 1:
                raise ValueError("Generation candidate crops are not byte-identical")
            crop_seed = int(sha(f"{config['seed']}/{identifier}/{index}".encode())[:16], 16)
            pool = chooser.freeze_pool(original["viewport"], candidates, seed=crop_seed)
            info = {
                "index": index,
                "viewport": original["viewport"],
                "original_crop_sha256": image_hashes[0],
                "pool": chooser.pool_record(pool),
                "ranking_status": "not_applicable_duplicates",
            }
            result["ranking_regions"].append(info)
            write_json(output / f"{identifier}-pool-{index}.json", info["pool"])
            if len(pool.candidates) < 2:
                continue
            stage = f"crop/{index}/image"
            url, metadata = (
                urls[0],
                {"image_edge": 0, "source_pixels_supplied": False, "original_crop_sha256": image_hashes[0]},
            )
            if config["image_edge"]:
                url, metadata = (image_factory or _rerender)(record, first, original, config["image_edge"])
                actual_url, actual = _crop_bytes(
                    {"messages": [{"content": [{"type": "image_url", "image_url": {"url": url}}]}]}
                )
                if (
                    sha(actual) != metadata["image_sha256"]
                    or metadata["image_viewport"] != original["viewport"]
                    or metadata["image_bytes"] != len(actual)
                    or metadata["image_edge"] != config["image_edge"]
                ):
                    raise ValueError("Selector pixels do not match declared same-crop image provenance")
                url = actual_url
                url, metadata = selector_visibility.transform(url, metadata, config.get("image_visibility", "source"))
                url, metadata = selector_image.transform(url, metadata, config.get("image_mode", "rgb"))
            info["selector_image"] = metadata
            stage = f"crop/{index}/evidence"
            try:
                body = _body(
                    pool,
                    config["model"],
                    url,
                    config["image_edge"],
                    evidence_mode=config.get("evidence_mode", "whole"),
                    evidence_max_bytes=config.get("evidence_max_bytes", differences.DEFAULT_MAX_BYTES),
                )
            except differences.EvidenceCapacityError:
                info["ranking_status"] = "evidence_capacity_retained_first"
                raise
            if config.get("evidence_mode") == "differences":
                projection = json.loads(body["state"][0] if isinstance(body["state"], list) else body["state"])
                info["evidence"] = {
                    "mode": "differences",
                    "max_bytes": config.get("evidence_max_bytes", differences.DEFAULT_MAX_BYTES),
                    "bytes": len(chooser.canonical_json(projection)),
                    "sha256": sha(chooser.canonical_json(projection)),
                    "differing_slots": len(projection["differing_slots"]),
                }
                write_json(output / f"{identifier}-selector-{index}-evidence.json", projection)
            stage = f"crop/{index}/request"
            write_json(output / f"{identifier}-selector-{index}-request.json", body)
            _reserve_wave(client)
            response = client.request(
                body, tag=f"{prefix}{index}", replay=False, reservation_usd=0.30, max_body_bytes=750_000
            )
            write_json(output / f"{identifier}-selector-{index}-response.json", response)
            result["ranking_calls"].append(
                {
                    "entry": response["entry"],
                    "usage": response["result"].get("usage", {}),
                    "replayed": response.get("replayed"),
                    "crop_index": index,
                }
            )
            if response.get("replayed"):
                raise ValueError("Frozen-pool ranking requires a fresh selector response")
            stage = f"crop/{index}/selection"
            answer = chooser.parse(pool, response["result"])
            selected, audit = chooser.select(pool, answer)
            info["audit"] = audit
            info["ranking_status"] = "unresolved_retained_first" if selected is None else "staged"
            choices += 1
            if selected is None:
                continue
            origin = audit["original_input_indexes"][0]
            canonical = json.loads(selected)
            if canonical != candidates[origin]:
                raise ValueError("Selected structure differs from exactly one frozen candidate")
            info.update(selected_baseline_index=origin, selected_sha256=sha(selected))
            staged[index] = deepcopy(crops[origin])
            staged[index]["selection_origin_baseline"] = origin
            staged[index]["selection_audit"] = audit
        stage = "atomic_page_composition"
        state = regions.compose(staged, first["viewport"])
        text = transcription.markdown(state)
        if choices:
            write_json(output / f"{identifier}-structure.json", state)
            (output / f"{identifier}.md").write_text(text)
            result.update(
                status="ok",
                tables=state["tables"],
                transcription_regions=staged,
                source_conserved=False,
                ranking_status="completed",
                text_provenance="model-transcribed",
            )
            for info in result["ranking_regions"]:
                if info["ranking_status"] == "staged":
                    info["ranking_status"] = "selected"
    except Exception as error:
        result["ranking_status"] = "failed_retained_first"
        result["ranking_errors"].append(_error(error, stage))
        result.update(
            status=first["status"],
            tables=deepcopy(first["tables"]),
            transcription_regions=deepcopy(first["transcription_regions"]),
        )
        for suffix in ("-structure.json", ".md"):
            source = inputs[0] / f"{identifier}{suffix}"
            if source.exists():
                (output / source.name).write_bytes(source.read_bytes())
        for info in result["ranking_regions"]:
            if info["ranking_status"] in {"staged", "selected"}:
                info["ranking_status"] = "discarded_atomic_failure"
    finally:
        result["incremental_ranking"] = {
            "scope": "ranking retained frozen candidates only",
            "wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu,
            **_charges(_entries(client, prefix)),
        }
        write_json(output / f"{identifier}-result.json", result)
    return result


def run(
    inputs: list[Path],
    trusted_code: list[dict[str, str]],
    output: Path,
    config: dict[str, Any],
    client: Any = None,
    *,
    image_factory: Callable[..., tuple[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Authenticate and freeze declared generation inputs before opt-in ranking calls."""
    if not config.get("run_hosted") or not 2 <= len(inputs) <= 4 or len(inputs) != len(trusted_code):
        raise ValueError("Ranking needs 2-4 explicit baseline/trust-map pairs and run_hosted opt-in")
    image_mode = config.get("image_mode", "rgb")
    visibility = config.get("image_visibility", "source")
    if visibility not in selector_visibility.CONTROLS or (visibility != "source" and not config.get("image_edge")):
        raise ValueError("Selector visibility control requires an image")
    if image_mode not in selector_image.MODES or (image_mode != "rgb" and not config.get("image_edge")):
        raise ValueError("Selector image encoding requires an admitted mode and nonzero image edge")
    mode = config.get("evidence_mode", "whole")
    if mode not in {"whole", "differences"}:
        raise ValueError("Unknown candidate evidence mode")
    if "evidence_max_bytes" in config and mode != "differences":
        raise ValueError("Difference evidence cap requires differences mode")
    if mode == "differences":
        cap = config.get("evidence_max_bytes", differences.DEFAULT_MAX_BYTES)
        if type(cap) is not int or not 1 <= cap <= chooser.MAX_COMPARISON_BYTES:
            raise ValueError("Difference evidence cap must be 1..128KiB UTF8 bytes")
        config = {**config, "evidence_max_bytes": cap}
    transport = config.get("transport_concurrency", 1)
    if type(transport) is not int or transport not in (1, 3):
        raise ValueError("P003 ranking transport concurrency must be 1 or 3")
    reviewed = config.get("reviewed_parser_sha256", [])
    if not isinstance(reviewed, list) or any(
        not isinstance(digest, str) or digest not in ROOT_REVIEWED_PARSER_SHA256 for digest in reviewed
    ):
        raise ValueError("Historical parser allowlist requires explicit root-reviewed digests")
    edge, model = config["image_edge"], config["model"]
    if (
        type(edge) is not int
        or edge not in EDGES
        or model not in (*DECISION_MODELS, "cloudflare/clef-omni")
        or (edge and model not in IMAGE_MODELS)
    ):
        raise ValueError("Selector model lacks admitted text/image support for requested edge")
    if type(config.get("seed", 20261010)) is not int:
        raise ValueError("Alias order seed must be an integer")
    inputs, output = [guard_path(path) for path in inputs], guard_path(output)
    authenticated = [
        authenticate(directory, trusted, reviewed_parser_sha256=tuple(reviewed))
        for directory, trusted in zip(inputs, trusted_code, strict=True)
    ]
    frozen_inputs, reports = [row[0] for row in authenticated], [row[1] for row in authenticated]
    records = frozen_inputs[0]["records"]

    def keyed(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {r["id"]: {k: r[k] for k in ("id", "pdf_path", "pdf_sha256", "page_number")} for r in rows}

    expected = keyed(records)
    if (
        len(expected) != 16
        or len(records) != 16
        or any(keyed(frozen["records"]) != expected for frozen in frozen_inputs)
    ):
        raise ValueError("Frozen selector inputs must match the same complete natural16 source inventory")
    if any(frozen["manifest_sha256"] != frozen_inputs[0]["manifest_sha256"] for frozen in frozen_inputs):
        raise ValueError("Frozen source manifests differ")
    config = {
        "seed": 20261010,
        **config,
        "campaign": "P003",
        "processor": "p003_candidate_choice",
        "run_id": _identifier(output.name),
        "fallback": "predeclared input baseline zero; no reference-dependent rescue",
        "scope": "incremental ranking on retained whole-crop candidates",
    }
    output.mkdir(parents=True, exist_ok=False)
    inventories = []
    for index, (directory, frozen, report) in enumerate(zip(inputs, frozen_inputs, reports, strict=True)):
        copy = output / f"baseline-{index}"
        copy.mkdir()
        files = {"frozen.json", "report.json"}
        for record in records:
            identifier = record["id"]
            row = next(p for p in report["results"] if p["id"] == identifier)
            files.update(
                f"{identifier}{suffix}"
                for suffix in ("-result.json", "-structure.json", ".md")
                if (directory / f"{identifier}{suffix}").exists()
            )
            files.update(
                f"{identifier}-request-{crop['request_index']}.json"
                for crop in row.get("transcription_regions", [])
                if (directory / f"{identifier}-request-{crop['request_index']}.json").exists()
            )
        hashes = {}
        for name in sorted(files):
            data = guard_path(directory / name).read_bytes()
            (copy / name).write_bytes(data)
            hashes[name] = sha(data)
        (copy / "code").mkdir()
        for name in frozen["code_sha256"]:
            data = guard_path(directory / "code" / name).read_bytes()
            (copy / "code" / name).write_bytes(data)
            hashes["code/" + name] = sha(data)
        inventories.append(
            {
                "directory": str(directory),
                "copied_directory": copy.name,
                "file_sha256": hashes,
                "trusted_code": trusted_code[index],
                "original_config": frozen["config"],
            }
        )
    root = Path(__file__).resolve().parent
    available_code = CODE_FILES + (("p003_candidate_diff.py",) if mode == "differences" else ())
    if image_mode != "rgb":
        available_code += ("p003_selector_image.py",)
    if visibility != "source":
        available_code += ("p003_selector_visibility.py",)
    (output / "code").mkdir()
    code = {}
    for name in available_code:
        data = (root / name).read_bytes()
        (output / "code" / name).write_bytes(data)
        code[name] = sha(data)
    write_json(
        output / "frozen.json",
        {
            "config": config,
            "records": records,
            "manifest_sha256": frozen_inputs[0]["manifest_sha256"],
            "code_sha256": code,
            "candidate_inputs": inventories,
            "concurrency": 1,
            "local_replay": False,
        },
    )
    if client is None:
        from bench.p003_client import P003ConcurrentClient, P003DecisionClient

        client = (P003ConcurrentClient if transport == 3 else P003DecisionClient)()
    if _entries(client, f"P003/{config['run_id']}/"):
        raise ValueError("Ranking run ID already exists in persistent ledger")
    maps = [{row["id"]: row for row in report["results"]} for report in reports]
    copied_inputs = [output / inventory["copied_directory"] for inventory in inventories]
    with pipeline_run.Resources() as resources:
        results = [
            process(
                record,
                [pages[record["id"]] for pages in maps],
                copied_inputs,
                output,
                config,
                client,
                image_factory=image_factory,
            )
            for record in records
        ]
    metrics = {
        **resources.summary(),
        "scope": "incremental ranking on retained frozen candidates",
        "concurrency": 1,
        "transport_concurrency": transport,
        "end_to_end_pipeline_measured": False,
        "generation_repeated": False,
        "input_authentication_resources": "unmeasured separately",
    }
    report = {
        "config": config,
        "page_count": len(results),
        "complete_output_pages": sum(row["status"] == "ok" for row in results),
        "candidate_generation_reports": reports,
        "candidate_generation_cost_scope": "All declared baselines, including invalid candidates and failed attempts. "
        "Overlapping ledger entries must be deduplicated before deriving combined costs.",
        "incremental_ranking": {
            "metrics": metrics,
            "returned_calls": sum(len(row["ranking_calls"]) for row in results),
            **_charges(_entries(client, f"P003/{config['run_id']}/")),
        },
        "metrics": metrics,
        "results": results,
        "pages_per_minute": None,
        "pages_per_dollar": None,
    }
    write_json(output / "resources.json", resources.samples)
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Run root-authorized fresh selector calls against explicit authenticated inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, action="append", required=True)
    parser.add_argument("--trusted-code", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--image-edge", type=int, choices=EDGES, default=512)
    parser.add_argument("--seed", type=int, default=20261010)
    parser.add_argument("--transport-concurrency", type=int, choices=(1, 3), default=1)
    parser.add_argument("--reviewed-parser-sha256", action="append", default=[])
    parser.add_argument("--evidence-mode", choices=("whole", "differences"), default="whole")
    parser.add_argument("--evidence-max-bytes", type=int)
    parser.add_argument("--image-mode", choices=selector_image.MODES, default="rgb")
    parser.add_argument("--image-visibility", choices=selector_visibility.CONTROLS, default="source")
    parser.add_argument("--run-hosted", action="store_true")
    args = parser.parse_args()
    config = {"model": args.model, "image_edge": args.image_edge, "seed": args.seed, "run_hosted": args.run_hosted}
    if args.image_mode != "rgb":
        config["image_mode"] = args.image_mode
    if args.image_visibility != "source":
        config["image_visibility"] = args.image_visibility
    if args.evidence_mode == "differences":
        config["evidence_mode"] = "differences"
        if args.evidence_max_bytes is not None:
            config["evidence_max_bytes"] = args.evidence_max_bytes
    elif args.evidence_max_bytes is not None:
        parser.error("--evidence-max-bytes requires --evidence-mode differences")
    if args.transport_concurrency == 3:
        config["transport_concurrency"] = 3
    if args.reviewed_parser_sha256:
        config["reviewed_parser_sha256"] = args.reviewed_parser_sha256
    report = run(args.baseline, [_read(path) for path in args.trusted_code], args.output, config)
    print(
        json.dumps({k: v for k, v in report.items() if k not in {"results", "candidate_generation_reports"}}, indent=2)
    )


if __name__ == "__main__":
    main()
