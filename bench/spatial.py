"""Fit and evaluate a tiny placement ranker using CPU-only positioned PDF fixtures.

Run ``uv run python -m bench.spatial``. This is a domain-specific feasibility
study, not a pretrained general document model. Training, policy selection, and
evaluation seeds are disjoint; held-out families vary scale, direction, and order.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pylopdf
from bench.feature_cases import page_pdf, text_op

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "bench/results/spatial-artifacts"


@dataclass(frozen=True)
class Example:
    """Independent intended relationship, plus the actual extracted candidates."""

    layout: pylopdf.PageLayout
    spec: pylopdf.FieldSpec
    expected: str | None
    candidates: tuple[pylopdf.FieldCandidate, ...]
    input_sha256: str


def example(seed: int, *, held_out: bool = False, negative: bool = False) -> Example:
    """Create native text PDFs with label/value relationships and nearby decoys."""
    rng = random.Random(seed)  # noqa: S311 - reproducible generated fixtures.
    size = rng.uniform(15, 22) if held_out else rng.uniform(8, 13)
    x, y = rng.uniform(50, 120), rng.uniform(400, 650)
    direction = "right" if seed % 2 else "below"
    label = "Account" if held_out else "Code"
    value = str(1000 + seed % 8000)
    label_width = size * (4.1 if held_out else 2.5)
    if direction == "right":
        intended = (x + label_width + rng.uniform(0.5, 1.2) * size, y)
        distractors = [(x + label_width + 7 * size, y), (x + label_width + size, y - 1.1 * size)]
    else:
        intended = (x, y - rng.uniform(1.5, 2.0) * size)
        distractors = [(x + 7 * size, y - 2 * size), (x, y - 7 * size)]
    objects = [text_op(label + ":", x, y, size=size)]
    if not negative:
        objects.append(text_op(value, *intended, size=size))
    objects.extend(text_op(str(90000 + index), *point, size=size) for index, point in enumerate(distractors))
    if held_out:
        rng.shuffle(objects)
    data = page_pdf("\n".join(objects))
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / f"input-{seed}.pdf").write_bytes(data)
    with pylopdf.open(stream=data) as doc:
        layout = doc[0].get_layout(table_strategy=None)
    spec = pylopdf.FieldSpec("account", anchor=label, direction=direction, max_distance=240, value_type="number")
    candidates = layout.extract_fields([spec])[0].candidates
    return Example(layout, spec, None if negative else value, candidates, hashlib.sha256(data).hexdigest())


def fit(examples: list[Example]) -> tuple[tuple[float, ...], float]:
    """Fit six coefficients using bounded, deterministic logistic SGD on CPU."""
    samples = [
        (candidate.features, float(candidate.text == case.expected))
        for case in examples
        for candidate in case.candidates
    ]
    weights, bias = [0.0] * 6, 0.0
    rng = random.Random(1977)  # noqa: S311 - fixed training order.
    for epoch in range(180):
        rng.shuffle(samples)
        rate = 0.1 / (1 + epoch * 0.02)
        for features, target in samples:
            logit = bias + sum(a * b for a, b in zip(weights, features, strict=True))
            probability = 1 / (1 + math.exp(-max(-40, min(40, logit))))
            error = probability - target
            bias -= rate * error
            for index, value in enumerate(features):
                weights[index] -= rate * (error * value + 0.0001 * weights[index])
    return tuple(weights), bias


def evaluate(examples: list[Example], model: pylopdf.PlacementModel | None) -> dict[str, int]:
    """Count abstentions and wrong accepted values, not just schema validity."""
    result = {
        "cases": len(examples),
        "accepted_correct": 0,
        "accepted_wrong": 0,
        "abstained": 0,
        "negative_rejected": 0,
    }
    for case in examples:
        output = case.layout.extract_fields([case.spec], model=model)[0]
        if output.value is None:
            result["abstained"] += 1
            result["negative_rejected"] += case.expected is None
        else:
            result["accepted_correct" if output.value == case.expected else "accepted_wrong"] += 1
    return result


def median_us(action: Callable[[], object], repetitions: int) -> float:
    """Measure a warm function with setup and validation outside the timer."""
    values = []
    for _ in range(repetitions):
        start = time.perf_counter_ns()
        action()
        values.append((time.perf_counter_ns() - start) / 1000)
    return statistics.median(values)


def geometric_baseline(examples: list[Example], threshold: float, margin: float) -> dict[str, int]:
    """Compare a distance/alignment product without fitting feature weights."""
    result = {
        "cases": len(examples),
        "accepted_correct": 0,
        "accepted_wrong": 0,
        "abstained": 0,
        "negative_rejected": 0,
    }
    for case in examples:
        ranked = sorted(
            ((candidate.features[0] * candidate.features[1], candidate.text) for candidate in case.candidates),
            reverse=True,
        )
        accepted = (
            bool(ranked) and ranked[0][0] >= threshold and (len(ranked) == 1 or ranked[0][0] - ranked[1][0] >= margin)
        )
        if accepted:
            result["accepted_correct" if ranked[0][1] == case.expected else "accepted_wrong"] += 1
        else:
            result["abstained"] += 1
            result["negative_rejected"] += case.expected is None
    return result


def page_timings() -> list[dict[str, float | str]]:
    """Compare first-call public APIs, including Python snapshot materialization."""
    results = []
    for name in ("senate-expenditures.pdf", "nics-background-checks-2015-11.pdf"):
        data = (ROOT / "tests/assets/real_world" / name).read_bytes()
        for mode in ("separate_words_and_tables", "spatial_snapshot"):
            samples = []
            for _ in range(7):
                with pylopdf.open(stream=data) as doc:
                    page = doc[0]
                    start = time.perf_counter_ns()
                    if mode == "spatial_snapshot":
                        layout = page.get_layout()
                        words, tables = len(layout.words), len(layout.tables)
                    else:
                        words, tables = len(page.get_text("words")), len(page.find_tables())
                    samples.append((time.perf_counter_ns() - start) / 1e6)
                    if not words or not tables:
                        msg = "timing input unexpectedly lost its text or tables"
                        raise RuntimeError(msg)
            results.append(
                {
                    "input": name,
                    "input_sha256": hashlib.sha256(data).hexdigest(),
                    "mode": mode,
                    "median_ms": statistics.median(samples),
                }
            )
    return results


def main() -> None:
    """Save fitted coefficients, exact decisions, fixture identities, and timings."""
    start = time.perf_counter()
    training = [example(index, negative=index % 5 == 0) for index in range(240)]
    validation = [example(10_000 + index, negative=index % 5 == 0) for index in range(80)]
    testing = [example(20_000 + index, held_out=True, negative=index % 5 == 0) for index in range(160)]
    fitting_started = time.perf_counter()
    weights, bias = fit(training)
    fit_seconds = time.perf_counter() - fitting_started
    candidates = [
        pylopdf.PlacementModel(weights, bias, threshold=threshold, margin=margin)
        for threshold in (0.7, 0.8, 0.9, 0.95, 0.99)
        for margin in (0.1, 0.2, 0.3)
    ]
    policies = [(model, evaluate(validation, model)) for model in candidates]
    model, validation_result = min(
        policies,
        key=lambda pair: (pair[1]["accepted_wrong"], -pair[1]["accepted_correct"], -pair[0].threshold, -pair[0].margin),
    )
    test_result = evaluate(testing, model)
    baseline = evaluate(testing, None)
    geometric_policies = [
        (threshold, margin, geometric_baseline(validation, threshold, margin))
        for threshold in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
        for margin in (0.05, 0.1, 0.2, 0.3)
    ]
    geo_threshold, geo_margin, _ = min(
        geometric_policies,
        key=lambda policy: (policy[2]["accepted_wrong"], -policy[2]["accepted_correct"], -policy[0], -policy[1]),
    )
    geometric = geometric_baseline(testing, geo_threshold, geo_margin)
    case = next(case for case in testing if case.expected is not None)
    candidate = case.candidates[0]
    timings = {
        "candidate_score_us": median_us(lambda: model.score(candidate), 2000),
        "field_query_with_model_us": median_us(lambda: case.layout.extract_fields([case.spec], model=model), 1000),
        "field_query_without_model_us": median_us(lambda: case.layout.extract_fields([case.spec]), 1000),
        "rectangle_query_us": median_us(lambda: case.layout.select((0, 0, 300, 792)), 1000),
        "fit_seconds": fit_seconds,
        "total_seconds": time.perf_counter() - start,
    }
    cold_timings = page_timings()
    report = {
        "model": asdict(model),
        "training_cases": len(training),
        "validation": validation_result,
        "held_out": test_result,
        "baseline": baseline,
        "geometric_baseline": geometric,
        "geometric_policy": {"threshold": geo_threshold, "margin": geo_margin},
        "timings": timings,
        "cold_public_api_timings": cold_timings,
        "model_bytes_json": len(json.dumps(asdict(model)).encode()),
        "pylopdf_version": pylopdf.__version__,
        "training_inputs": [case.input_sha256 for case in training],
        "validation_inputs": [case.input_sha256 for case in validation],
        "held_out_inputs": [case.input_sha256 for case in testing],
        "held_out_expected": [case.expected for case in testing],
        "held_out_decisions": [asdict(case.layout.extract_fields([case.spec], model=model)[0]) for case in testing],
        "scope": (
            "Synthetic account fields; label, scale, and content-order shift held out. "
            "Not calibrated real-document accuracy."
        ),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "placement-model.json").write_text(json.dumps(report, indent=2) + "\n")
    rows = [
        "# CPU spatial field assignment",
        "",
        report["scope"],
        "",
        "Six-feature logistic ranker; 240 training PDFs, 80 separate policy-selection PDFs,",
        "160 evaluation PDFs (128 values, 32 missing-value controls). All inference and training use CPU.",
        "Model coefficients are opt-in and are not shipped as a general-purpose pretrained model.",
        "",
        "| Method | Correct accepted | Wrong accepted | Abstained | Missing values rejected |",
        "| --- | ---: | ---: | ---: | ---: |",
        *[
            f"| {name} | {result['accepted_correct']} | {result['accepted_wrong']} | "
            f"{result['abstained']} | {result['negative_rejected']}/32 |"
            for name, result in (
                ("Unique candidate only", baseline),
                ("Distance/alignment rule", geometric),
                ("Tiny ranker", test_result),
            )
        ],
        "",
        f"Fitted state: {report['model_bytes_json']} bytes of JSON; no tensor runtime or model download.",
        f"Policy selected on validation only: threshold {model.threshold}, margin {model.margin}.",
        f"Geometric policy also selected on validation only: threshold {geo_threshold}, margin {geo_margin}.",
        "",
        "| Operation | Median |",
        "| --- | ---: |",
        *[
            f"| {name} | {value:.3f} {'microseconds' if name.endswith('_us') else 'seconds'} |"
            for name, value in timings.items()
        ],
        "",
        "Timings are one local CPU run, with warmed query state; they exclude PDF opening and interpretation.",
        "",
        "| First-call public API (opening excluded) | Input | Median milliseconds |",
        "| --- | --- | ---: |",
        *[f"| {row['mode']} | {row['input']} | {row['median_ms']:.3f} |" for row in cold_timings],
        "",
        "Seven repetitions per first-call API. Both include geometry extraction and Python materialization;",
        "the spatial API also constructs the query index and source-word membership for every cell.",
        "These measurements include the extra work; sharing interpretation does not promise a net speedup.",
        "Geometry does not establish semantic truth. A closer, aligned wrong value can defeat this model;",
        "use application validation, explicit regions, and independent document-family evaluation.",
        "Full coefficients, fixture hashes, and decisions are in ignored spatial-artifacts/placement-model.json.",
        "All generated input PDFs are retained alongside that report.",
        "Reproduce with `CUDA_VISIBLE_DEVICES='' uv run python -m bench.spatial`.",
    ]
    (ROOT / "bench/results/spatial-latest.md").write_text("\n".join(rows) + "\n")
    print(json.dumps({"held_out": test_result, "baseline": baseline, "timings": timings}, indent=2))


if __name__ == "__main__":
    main()
