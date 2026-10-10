"""Strict crop-level admission across matched frozen generation attempts.

No invalid table is repaired or salvaged. Whole-page completion requires one
complete valid state for every original detector crop and atomic composition.
"""

# ruff: noqa: EM101, TRY003, SLF001, PLR2004, C901, PLR0912
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pylopdf
from bench import generalization_vision_regions as regions
from bench import p003_candidate_choice as choice
from bench import p003_candidate_run as candidate
from bench import pipeline_vision_transcription as transcription
from bench.silver import guard_path, sha


def freeze_page(
    record: dict[str, Any],
    pages: list[dict[str, Any]],
    directories: list[Path],
    configs: list[dict[str, Any]],
    *,
    seed: int,
) -> dict[str, Any]:
    """Freeze validity before any scoring or model choice, including invalid attempts."""
    if (
        not 2 <= len(pages) <= 4
        or len(pages) != len(directories)
        or len(pages) != len(configs)
        or type(seed) is not int
    ):
        raise ValueError("Valid-region admission requires 2-4 complete frozen baseline inventories")
    raw = guard_path(Path(record["pdf_path"])).read_bytes()
    if sha(raw) != record["pdf_sha256"]:
        raise ValueError("Frozen source PDF hash differs")
    first = pages[0]
    metadata = ("id", "pdf_sha256", "viewport", "original_rotation", "rotation_normalized", "layout_detection")

    def source_metadata(page: dict[str, Any]) -> dict[str, Any]:
        value = {k: deepcopy(page[k]) for k in metadata}
        # Runtime measurements are historical provenance, not detector geometry.
        value["layout_detection"].pop("metrics", None)
        return value

    expected = source_metadata(first)
    with pylopdf.open(stream=raw) as document:
        page = document[record["page_number"]]
        if list(page.rect) != expected["viewport"] or page.rotation != expected["original_rotation"]:
            raise ValueError("Actual source PDF page geometry differs from generation metadata")
    if expected["id"] != record["id"] or expected["pdf_sha256"] != record["pdf_sha256"]:
        raise ValueError("Generation page differs from frozen source identity")
    proposal = regions.proposals(first["layout_detection"], first["viewport"])
    proposal_keys = ("index", "request_index", "viewport", "detector_box")
    geometry = [{k: c[k] for k in proposal_keys} for c in proposal]
    for page in pages:
        if source_metadata(page) != expected:
            raise ValueError("Generation detector/page metadata differs; no matched crop pool")
        if [{k: c[k] for k in proposal_keys} for c in page["transcription_regions"]] != geometry:
            raise ValueError("Generation complete crop inventories differ")
    frozen = {
        "version": 1,
        "id": record["id"],
        "record": deepcopy(record),
        "page_metadata": expected,
        "seed": seed,
        "policy": "valid_regions",
        "source_conserved": False,
        "original_page_statuses": [p["status"] for p in pages],
        "historical_page_failure_gate_blocks": any(p["status"] != "ok" for p in pages),
        "generation_provenance": [{"baseline_index": i, "page": deepcopy(p)} for i, p in enumerate(pages)],
        "crops": [],
    }
    for index, bounds in enumerate(geometry):
        attempts, valid, origins, image_hashes, image_urls = [], [], [], [], []
        for origin, (page, directory, config) in enumerate(zip(pages, directories, configs, strict=True)):
            crop = page["transcription_regions"][index]
            attempt = {
                "baseline_index": origin,
                "original_page_status": page["status"],
                "original_crop_status": crop["status"],
                "crop": deepcopy(crop),
                "valid": False,
            }
            request_path = guard_path(directory / f"{record['id']}-request-{crop['request_index']}.json")
            if not request_path.exists():
                attempt["invalid_reason"] = "missing_complete_generation_request"
                attempts.append(attempt)
                continue
            # Request/image mismatch is provenance corruption, not a parser-invalid alternative.
            body = candidate._read(request_path)
            url, image = candidate._crop_bytes(body)
            expected_body = transcription.request(body["model"], url, crop["viewport"], body["max_tokens"])
            provider = config.get("generation_provider")
            if provider:
                expected_body["provider"] = {"only": [provider], "allow_fallbacks": False, "require_parameters": True}
            encoded_body = json.dumps(expected_body, separators=(",", ":")).encode()
            if body != expected_body or sha(encoded_body) != crop["request"]["body_sha256"]:
                raise ValueError("Retained generation request differs from strict original request")
            if (
                sha(image) != crop["image"]["image_sha256"]
                or len(image) != crop["image"]["image_bytes"]
                or crop["image"]["image_viewport"] != crop["viewport"]
            ):
                raise ValueError("Actual generation image provenance differs")
            image_hashes.append(sha(image))
            image_urls.append(url)
            attempt.update(request_sha256=sha(encoded_body), image_sha256=sha(image), request=body)
            try:
                state = transcription.parse(crop["transcription_response"], crop["viewport"])
                choice._validate(tuple(crop["viewport"]), state)
            except (ValueError, KeyError, TypeError) as error:
                attempt.update(invalid_reason=str(error), invalid_error_type=type(error).__name__)
            else:
                if crop["status"] == "ok" and state["tables"] != crop["tables"]:
                    raise ValueError("Parsed complete candidate differs from retained region tables")
                encoded = choice.canonical_json(state)
                attempt.update(valid=True, canonical_json=encoded.decode(), state_sha256=sha(encoded))
                valid.append(state)
                origins.append(origin)
            attempts.append(attempt)
        if len(set(image_hashes)) > 1:
            raise ValueError("Generation crops are not byte-identical across all retained requests")
        unique = {choice.canonical_json(state) for state in valid}
        crop_seed = int(sha(f"{seed}/{record['id']}/{index}".encode())[:16], 16)
        item = {
            **bounds,
            "attempts": attempts,
            "valid_baseline_indexes": origins,
            "valid_count": len(valid),
            "unique_valid_count": len(unique),
            "seed": crop_seed,
            "image_sha256": image_hashes[0] if image_hashes else None,
            "status": "uncovered" if not valid else "sole_valid" if len(unique) == 1 else "choice_required",
        }
        if len(valid) >= 2:
            item["pool"] = choice.pool_record(choice.freeze_pool(bounds["viewport"], valid, seed=crop_seed))
        if len(unique) == 1:
            item["deterministic_baseline_index"] = origins[0]
            item["deterministic_state_sha256"] = sha(choice.canonical_json(valid[0]))
        frozen["crops"].append(item)
    frozen["complete_crop_coverage"] = all(c["valid_count"] > 0 for c in frozen["crops"])
    frozen["snapshot_sha256"] = sha(choice.canonical_json(frozen))
    return frozen


def compose_selection(frozen: dict[str, Any], selected: dict[int, int] | None = None) -> dict[str, Any]:
    """Compose only exact valid baseline states; no model blending or partial page success."""
    fingerprint = {k: v for k, v in frozen.items() if k != "snapshot_sha256"}
    if sha(choice.canonical_json(fingerprint)) != frozen["snapshot_sha256"]:
        raise ValueError("Frozen valid-region admission changed")
    selected = {} if selected is None else selected
    if not set(selected) <= {c["index"] for c in frozen["crops"]}:
        raise ValueError("Unknown selected crop identity")
    staged = []
    for item in frozen["crops"]:
        origin = selected.get(item["index"], item.get("deterministic_baseline_index"))
        if origin is None or type(origin) is not int or origin not in item["valid_baseline_indexes"]:
            raise ValueError("Complete page needs an admitted exact state for every crop")
        attempt = next(a for a in item["attempts"] if a["baseline_index"] == origin)
        state = json.loads(attempt["canonical_json"])
        region = deepcopy(attempt["crop"])
        region.update(status="ok", tables=state["tables"], selection_origin_baseline=origin)
        staged.append(region)
    state = regions.compose(staged, frozen["page_metadata"]["viewport"])
    return {
        "status": "ok",
        "state": state,
        "markdown": transcription.markdown(state),
        "transcription_regions": staged,
        "source_conserved": False,
        "text_provenance": "model-transcribed; exact complete retained crop candidates",
    }
