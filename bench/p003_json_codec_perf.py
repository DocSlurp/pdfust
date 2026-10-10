"""Isolated synthetic serialization-only codec comparison with explicit compatibility fallbacks."""

# ruff: noqa: ANN401, EM101, TRY003, E501
from __future__ import annotations

import argparse
import importlib
import json
import math
import re
import struct
import sys
import threading
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from bench import decision_concurrent as concurrent
from bench import decision_hosted as hosted
from bench import p003_sqlite_ledger_perf as comparison
from bench import p003_transport_stage_perf as fixture
from bench.silver import guard_path, sha, write_json

VERSION = "3.13.0"
WHEEL_SHA256 = "58a9619d88f8818d9ab6b39d70d203789457ba13c1ed5d274f33ce9ae7e81a36"
LARGE_DIGITS = re.compile(rb"[0-9]{19,}")


def load_codec(directory: Path) -> Any:
    """Load only the explicitly installed isolated pinned codec; no implicit installation."""
    directory = guard_path(directory).resolve()
    sys.path.insert(0, str(directory))
    try:
        codec = importlib.import_module("orjson")
    finally:
        sys.path.pop(0)
    if codec.__version__ != VERSION or not Path(codec.__file__).resolve().is_relative_to(directory):
        raise ValueError("Explicit isolated pinned orjson installation required")
    return codec


def safe_tree(value: Any) -> bool:
    """Check complete dump input without permitting null substitution or native extended types."""
    kind = type(value)
    if value is None or kind in (bool, str):
        return True
    if kind is int:
        return -(1 << 63) <= value < 1 << 64
    if kind is float:
        return math.isfinite(value)
    if kind is list:
        return all(safe_tree(item) for item in value)
    if kind is dict:
        return all(type(key) is str and safe_tree(item) for key, item in value.items())
    return False


class CodecFacade:
    """Match the used stdlib API while retaining unsafe/unsupported cases explicitly."""

    def __init__(self, codec: Any) -> None:
        """Count native and fallback paths independently across synthetic callers."""
        self.codec, self.counts, self.lock = codec, Counter(), threading.Lock()

    def record(self, name: str) -> None:
        """Record one path without modifying financial state."""
        with self.lock:
            self.counts[name] += 1

    def dumps(self, value: Any, **kwargs: Any) -> str:
        """Accelerate only the exact financial checkpoint format; preserve request byte identity."""
        if kwargs != {"ensure_ascii": False, "indent": 2}:
            self.record("dumps_stdlib_format_or_request")
            return json.dumps(value, **kwargs)
        if not safe_tree(value):
            self.record("dumps_stdlib_unsafe_tree")
            return json.dumps(value, **kwargs)
        try:
            result = self.codec.dumps(value, option=self.codec.OPT_INDENT_2).decode("utf-8")
        except (TypeError, ValueError):
            self.record("dumps_stdlib_native_refusal")
            return json.dumps(value, **kwargs)
        self.record("dumps_native_checkpoint")
        return result

    def loads(self, value: Any, **kwargs: Any) -> Any:
        """Prevent large integers/nonfinite values from silently changing type or value."""
        if kwargs or type(value) not in (str, bytes, bytearray):
            self.record("loads_stdlib_options_or_type")
            return json.loads(value, **kwargs)
        try:
            encoded = value.encode("utf-8") if type(value) is str else value
        except UnicodeError:
            self.record("loads_stdlib_unicode")
            return json.loads(value, **kwargs)
        # Conservative substring refusal may include quoted strings; this affects
        # speed only. It avoids depending on native conversion of >64-bit integers.
        if LARGE_DIGITS.search(encoded) or b"NaN" in encoded or b"Infinity" in encoded:
            self.record("loads_stdlib_numeric_boundary")
            return json.loads(value, **kwargs)
        try:
            result = self.codec.loads(encoded)
        except (TypeError, ValueError):
            self.record("loads_stdlib_native_refusal")
            return json.loads(value, **kwargs)
        self.record("loads_native")
        return result


def exact(a: Any, b: Any) -> bool:
    """Compare JSON values and exact types, including float bits and signed zero."""
    if type(a) is not type(b):
        return False
    if type(a) is float:
        return struct.pack("!d", a) == struct.pack("!d", b)
    if type(a) is dict:
        return a.keys() == b.keys() and all(exact(a[key], b[key]) for key in a)
    if type(a) is list:
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b, strict=True))
    return a == b


@contextmanager
def isolated_override(facade: CodecFacade):  # noqa: ANN201 - scoped research override.
    """Override only two module references in this isolated process; restore them on every exit."""
    previous = hosted.json, concurrent.json
    hosted.json, concurrent.json = facade, facade
    try:
        yield
    finally:
        hosted.json, concurrent.json = previous


def compatibility(codec: Any, count: int) -> dict[str, Any]:
    """Gate the complete synthetic fixture and explicit parser boundaries before timing."""
    facade = CodecFacade(codec)
    values = [None, True, False, 0, 1, -1, 1.0, -0.0, 0.0, 0.3,
              5e-324, 1.7976931348623157e308, 2 ** 53 + 1, -(2 ** 63), 2 ** 64 - 1,
              2 ** 64, -(2 ** 63) - 1, 10 ** 100, "Unicode Δ 漢 😀", "escaped\nstring",
              {"literal": "Infinity 12345678901234567890", "number": 7}, float("inf"), float("nan")]
    rows = []
    for index, value in enumerate(values):
        baseline = json.loads(json.dumps(value, ensure_ascii=False, indent=2))
        proposed = facade.loads(facade.dumps(value, ensure_ascii=False, indent=2))
        if not exact(baseline, proposed):
            raise ValueError("Codec boundary lost exact value or type")
        rows.append({"index": index, "type": type(value).__name__, "exact_stdlib_roundtrip": True})
    ledger = fixture.synthetic_ledger(count)
    raw = facade.dumps(ledger, ensure_ascii=False, indent=2)
    if not exact(ledger, facade.loads(raw)):
        raise ValueError("Complete synthetic financial inventory differs")
    for index in range(30):
        body = comparison.body(index)
        if facade.dumps(body, separators=(",", ":"), allow_nan=False) != json.dumps(
            body, separators=(",", ":"), allow_nan=False
        ):
            raise ValueError("Provider request bytes changed")
    return {"exact_fixture_roundtrip": True, "exact_request_wires": True, "boundary_cases": rows,
            "paths": dict(facade.counts), "scope": "Exact stdlib value/type equivalence; unsafe cases explicitly fallback"}


def measure(output: Path, codec_directory: Path, workers: int, *, count: int = 23000,  # noqa: PLR0913 - matched controls.
            attempts: int = 30, export_delay: float = 0) -> dict[str, Any]:
    """Keep actual JSON reserve/settle/unknown/annotation flow, including complete safety-scan CPU."""
    codec = load_codec(codec_directory)
    audit = compatibility(codec, count)
    facade = CodecFacade(codec)
    with isolated_override(facade):
        report = comparison.measure(output, "json", count, workers=workers,
                                    attempts=attempts, export_delay=export_delay)
    report.update(codec="orjson", codec_version=VERSION, isolated_codec_path=str(codec_directory.resolve()),
                  codec_wheel_sha256=WHEEL_SHA256, codec_module_sha256=sha(Path(codec.__file__).read_bytes()),
                  codec_paths=dict(facade.counts), compatibility=audit,
                  override_scope="Only hosted.json and decision_concurrent.json references in isolated synthetic process; actual financial methods unchanged; stdlib request wire unchanged")
    report["code_sha256"]["p003_json_codec_perf.py"] = sha(Path(__file__).read_bytes())
    write_json(output / "report.json", report)
    return report


def main() -> None:
    """Run only an explicit isolated codec installation and fresh synthetic outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codec-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--export-delay", type=float, default=0)
    args = parser.parse_args()
    output = guard_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for workers in (3, 6):
        result = measure(output / f"orjson-23000-{workers}", guard_path(args.codec_directory), workers,
                         export_delay=args.export_delay)
        row = {key: result[key] for key in ("workers", "metrics", "codec_paths", "summed_stage_seconds")}
        rows.append(row)
        print(json.dumps(row), flush=True)
    write_json(output / "report.json", {"rows": rows, "network_calls": 0, "production_changes": False,
                                       "codec_version": VERSION, "codec_wheel_sha256": WHEEL_SHA256})


if __name__ == "__main__":
    main()
