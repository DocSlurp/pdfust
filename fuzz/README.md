# Public API fuzzing

The scheduled `Fuzz` workflow builds the locked environment, generates malformed
PDF seeds, and runs the public workflow for ten minutes. It retains crash
reproducers before reporting failure. Its thirty-minute job budget also allows
toolchain setup and a cold extension build. `Fuzz health` observes completed runs
without executing their code and reports failed, cancelled, or timed-out runs as
failed checks. Maintainers still need to monitor these workflow results; a check
does not establish that a scheduled run was dispatched.

To run locally:

```bash
uv sync --locked --group fuzz --python 3.13
uv run --no-sync python fuzz/generate_corpus.py --output /tmp/pdfust-corpus
uv run --no-sync python fuzz/fuzz_api.py -max_total_time=600 -timeout=60 \
  -rss_limit_mb=2048 -max_len=1048576 /tmp/pdfust-corpus tests/assets/real_world
```

Expected `PdfError` refusals are handled; crashes, Rust panics, and exceptions
outside the public hierarchy fail the run. Independent readers handle their own
expected refusals so an unsupported feature does not prevent later operations.
Trees, images, vector drawings, tables, Markdown, extraction, rendering, metadata,
serialization, and reopening are exercised. Native OCR model inference is outside
this harness.

The per-input timeout is a hang detector, not a public latency guarantee.
Upstream native work has no cooperative cancellation. Minimize slow or crashing
units before adding a Python regression. Record corpus sources, licenses, and
limitations in `tests/assets/real_world/README.md`; never upload confidential or
non-redistributable documents as seeds.

## Native coverage boundary

`atheris.instrument_imports()` instruments Python. The normal stable Rust build
does **not** deliver Rust parser/interpreter branch coverage to libFuzzer, and
this workflow does not claim native sanitizer coverage. Native failures can still
be detected through the public API, but Python coverage alone provides weak
feedback for mutations that take different paths entirely within Rust.

A dedicated native lane remains necessary. It must use a compatible Rust/LLVM
coverage build and libFuzzer runtime, verify sanitizer-coverage symbols in the
extension, and demonstrate changing native coverage during a corpus run before
being described as native coverage-guided fuzzing. A pinned toolchain and separate
build cache are required so its instrumented binary never becomes a release
artifact. AddressSanitizer additionally requires a compatible runtime loaded
before Python and a smoke test of imports and expected-error paths.

See [Atheris native-extension guidance](https://github.com/google/atheris/blob/master/native_extension_fuzzing.md)
and [Rust sanitizer support](https://doc.rust-lang.org/unstable-book/compiler-flags/sanitizer.html).
Instrumenting or measuring Python coverage does not verify these native
requirements.
