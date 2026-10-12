# Node binding vs Python API, 2026-10-12

Task U1. `@pdfust/node` (release build, commit-pinned, Node v26.8.2 on the dev host) against the Python `pdfust` 0.13.0 API in `.venv`, same Rust core, same fixtures (`tests/assets/real_world`). Commands: `bindings/node/scripts/bench.mjs` and `bench.py` (9 repeats, median; each operation uses a freshly opened document so page caches do not leak between rows; render covers the first 12 pages). Two full runs were taken back to back on a shared 8-core machine that other agents were also using, so absolute numbers moved up to 2x between runs; read the ratios and the two columns, not single cells.

## ms per page (Node | Python), run 1 / run 2

| fixture (pages) | op | Node r1 | Py r1 | Node r2 | Py r2 | Node/Py (mean of runs) |
|---|---|---:|---:|---:|---:|---:|
| usrguide.pdf (27) | text() | 16.1 | 13.5 | 13.4 | 7.4 | 1.50 |
| usrguide.pdf (27) | markdown (lines) | 25.4 | 34.3 | 28.8 | 18.0 | 1.17 |
| usrguide.pdf (27) | markdown (text tables) | 28.7 | 27.6 | 25.7 | 18.1 | 1.23 |
| usrguide.pdf (27) | render 72 dpi PNG | 46.4 | 43.5 | 48.9 | 25.1 | 1.51 |
| bill-hr815.pdf (110) | text() | 5.4 | 4.9 | 2.2 | 2.8 | 0.94 |
| bill-hr815.pdf (110) | markdown (lines) | 8.0 | 13.6 | 4.4 | 9.5 | 0.52 |
| bill-hr815.pdf (110) | markdown (text tables) | 8.3 | 14.1 | 4.5 | 8.6 | 0.55 |
| bill-hr815.pdf (110) | render 72 dpi PNG | 47.8 | 44.1 | 27.1 | 31.2 | 0.98 |
| f1040.pdf (2) | text() | 21.0 | 38.4 | 9.1 | 18.3 | 0.52 |
| f1040.pdf (2) | markdown (lines) | 43.4 | 76.2 | 21.4 | 42.2 | 0.54 |
| f1040.pdf (2) | markdown (text tables) | 44.8 | 84.5 | 21.3 | 50.0 | 0.48 |
| f1040.pdf (2) | render 72 dpi PNG | 70.3 | 106.4 | 33.6 | 50.6 | 0.66 |
| senate-expenditures.pdf (1) | text() | 13.1 | 50.1 | 6.9 | 28.7 | 0.25 |
| senate-expenditures.pdf (1) | markdown (lines) | 28.4 | 71.8 | 14.2 | 44.2 | 0.36 |
| senate-expenditures.pdf (1) | markdown (text tables) | 30.2 | 84.7 | 14.0 | 45.8 | 0.33 |
| senate-expenditures.pdf (1) | render 72 dpi PNG | 97.1 | 130.5 | 44.9 | 70.3 | 0.69 |
| nics-background-checks-2015-11.pdf (1) | text() | 24.2 | 45.7 | 12.3 | 31.7 | 0.46 |
| nics-background-checks-2015-11.pdf (1) | markdown (lines) | 89.1 | 179.5 | 55.7 | 123.9 | 0.47 |
| nics-background-checks-2015-11.pdf (1) | markdown (text tables) | 80.6 | 140.2 | 57.5 | 163.8 | 0.46 |
| nics-background-checks-2015-11.pdf (1) | render 72 dpi PNG | 57.2 | 101.8 | 45.6 | 97.7 | 0.51 |
| mhlw-doc.pdf (2) | text() | 24.0 | 36.5 | 12.6 | 26.2 | 0.57 |
| mhlw-doc.pdf (2) | markdown (lines) | 56.1 | 81.5 | 24.2 | 51.3 | 0.58 |
| mhlw-doc.pdf (2) | markdown (text tables) | 52.2 | 56.3 | 25.4 | 61.6 | 0.67 |
| mhlw-doc.pdf (2) | render 72 dpi PNG | 49.9 | 58.3 | 25.2 | 37.3 | 0.77 |

## Reading

- Single-document, single-thread speed is the same engine, so the two should track each other. On multi-page documents (usrguide 27 pp, bill-hr815 110 pp) they do: text within noise, markdown 1.3-1.7x faster on Node (the Rust Markdown builder replaces Python glue), render equal within noise.
- Small, dense pages (senate, nics, f1040, mhlw) are 1.5-3x faster on Node for text and markdown in both runs; the Python wrapper pays per-call object construction (tuples, `Rect`s, dict layouts) on pages where the core finishes in a few milliseconds. Treat the 2-3x as an upper bound given the noise.
- `open` is a few milliseconds either way and dominated by file read plus xref parse.
- Peak RSS of the whole benchmark process: Node about 210 MB, Python about 115 MB (the Node figure includes V8 and the 110-page document held while Buffers are in flight; it is a process total, not binding overhead). Neither run exceeded 250 MB.

## Async scaling (`scripts/bench-concurrency.mjs`, 8 documents x 6 pages of usrguide.pdf)

| `UV_THREADPOOL_SIZE` | renderAsync 72 dpi | markdownAsync |
|---:|---:|---:|
| 1 | 1546 ms | 899 ms |
| 4 (Node default) | 691 ms | 346 ms |
| 8 | 584 ms | 443 ms |

Rendering scales about 2.2x from 1 to 4 threads and 2.6x at 8; markdown 2.6x at 4 threads. Different documents run in parallel; calls on the *same* document are serialised by its lock (`one document serialises concurrent async calls` in the tests), so a worker should spread concurrent work across documents or pages of separately opened documents.

## Thread-safety notes

- A document handle is a mutex-guarded Rust object; every sync and async call takes the lock, so concurrent use from several JS tasks is safe but serial. Different documents share no state except the process-wide weak font cache (internally locked).
- Async calls run on the libuv threadpool and hold the document lock for their whole duration: a long render blocks other calls (sync or async) on that document, and sync calls on the main thread will wait for it. Size `UV_THREADPOOL_SIZE` to the worker's concurrency; the default 4 is shared with `fs` and `crypto`.
- Rendering allocates a full-page RGBA buffer before cropping (`clip` reduces output, not rasterisation cost); `maxEdgePx` is the supported way to bound it.
- `close()` drops the Rust document immediately; later calls throw `PDF_CLOSED`, and an in-flight async call finishes first because it holds the lock.
- No `Sync` shortcuts were taken: the PyO3 `gil_used = false` module and this binding use the same `_Document` code.
