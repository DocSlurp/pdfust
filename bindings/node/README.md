# @pdfust/node

In-process Node binding (N-API, napi-rs) of the pdfust Rust core. DocSlurp's worker calls it
directly: no Python, no subprocess. **Private and unpublished** (`"private": true`); it ships as a
tarball pinned by version and sha256.

```js
const pdfust = require('@pdfust/node')
const doc = pdfust.openPath('report.pdf', { password: 'optional', limits: { profile: 'web' } })
const page = doc.page(0)                       // 0-based
page.markdown({ tableStrategy: 'lines' })      // same output as Python Page.to_markdown()
await page.renderAsync({ dpi: 144, format: 'jpeg' })   // Buffer
doc.close()
```

Types: [`index.d.ts`](index.d.ts) re-exports the generated [`native.d.ts`](native.d.ts). Errors are
`PdfustError` with `code` in `PDF_LOCKED`, `PDF_UNSUPPORTED_ENCRYPTION` (unknown security handler or unsupported /V or /R: not a password
problem), `PDF_LIMIT` (plus `limit`, e.g. `decompressed_size`), `PDF_ERROR`, `INVALID_ARGUMENT`, `PDF_CLOSED`,
`NATIVE_PDF_UNSUPPORTED` (`NotImplementedError`).

## Coverage of `ADAPTER-INTERFACE.md`

| Interface member | Status | Notes |
|---|---|---|
| `version()` | done | `{version, gitSha, features}`; sha comes from the commit the tarball was packed from |
| `openPath`, `openBuffer` + `password` | done | wrong or missing password throws `PDF_LOCKED`; unknown handlers throw `PDF_UNSUPPORTED_ENCRYPTION`; extra `limits` option (`profile: 'web'` for untrusted uploads, `'worker'` for server ingestion, or individual byte/page caps, `PDF_LIMIT`). Text and glyph limits are cumulative per document; a page already admitted is never charged again |
| `pageCount`, `metadata` | done | adds author/subject/keywords/dates/pdfVersion/repaired; `permissions` are lopdf flag names |
| `hasJavaScript`, `javaScript()` | done | shared `inspect` module (same as Python `get_javascript`): scope, zero-based page and trigger event per action |
| `optionalContent` | done | `inspect` module: `xref`, name, default visibility (`/D` `BaseState`, `/ON`, `/OFF`), `intent` |
| `attachments` | done | `inspect` module: name, stored `size`, `declaredSize`, `mime`, `description` (nothing is decoded) |
| `fonts(page?)` | done | `inspect` module: `xref`, subset-tagged `name`, `type`, `descendantType`, `embedded`, `hasToUnicode`, `isType3`, `subset`, `encoding`, zero-based `pages`; includes Form XObject resources |
| `page(i)`, `close()` | done | closed documents throw `PDF_CLOSED` |
| `size()` | done | displayed size in points, plus `/Rotate` |
| `text()` | done | identical to Python `get_text("text")` on the parity fixtures |
| `markdown`, `markdownAsync` | done | `tableStrategy` `lines`/`text`/`none`; Rust port of the Python builder, byte-identical on the parity fixtures |
| `spans()` | done | reading-order spans; `renderMode`/`invisible` come from the page's glyphs (OCR text layers show `invisible`); `dir`/`writingMode` give the line direction (vertical CJK). Always includes invisible text, even after `setSkipInvisibleText(true)`. `unmapped` is always 0 per span, use `scan()`/`glyphStats()` |
| `scan(opts?)` | done | one interpretation pass: raw runs (`font`, `size`, `flags`, `renderMode`, `unmapped`, `glyphs`, `type3`, `controlChars`, `overImage`, `dir`, `writingMode`), image placements with `dpiX`/`dpiY`/`dpi`/`stencil` (no pixels decoded) and `stats`. Parity-tested against Python `Page.scan()` |
| `images()` | done | placements only, nothing decoded; `effectiveDpi` is the lower of x/y |
| `drawings()` | done | `lineCount`, `rectCount`, `hRuleCount`/`vRuleCount` (`longRuleCount` is their sum), union `vectorArea` in pt², one `{bbox, paint}` per path, and `truncated: true` instead of an error when a drawing safety limit (8192 paths, 131,072 commands) cuts collection short |
| `widgets()` | done | `inspect` module: kind, qualified name, value, `filled`, `readOnly`, `required` |
| `annotations()`, `links()` | done | `links()` adds `kind` and 0-based `destPage` |
| `tables()` | done | `lines` and `text` strategies; adds `rowCount`, `colCount`, `confidence` |
| `render`, `renderAsync` | done | `dpi`, `maxEdgePx`, `clip` (points), `format` png/jpeg/webp, `gray`, `quality` |
| `ocrFillAsync` | done | port of Python `Page.ocr_fill` on the pure-Rust PP-OCRv6 (RTen) engine; see below. Rejects with `NATIVE_PDF_UNSUPPORTED` when no model directory is configured |
| `setSkipInvisibleText(bool)` (extra) | done | leaves render-mode-3 text out of `text()`/`markdown()`/`tables()` (default: included) |
| `words()` (extra) | done | `{text, bbox}` per word; unlike `spans()` it never merges text that shares a baseline across side-by-side columns, so callers can detect gutters |
| `glyphStats()` (extra) | done | `{glyphs, invisible, stroke, unmapped, fonts}` for text-layer probes |
| `takeWarnings()` (extra) | done | engine warnings, e.g. repaired cross-reference table |

### OCR fill

```js
const result = await page.ocrFillAsync({ policy: 'fill', dpi: 200, modelDir: '/models/ppocrv6', threads: 4 })
// { text, markdown, filledRegions, engine, policy, recognized, replacedPages, regions, unmappedNative }
```

Behaviour and defaults match Python `Page.ocr_fill` (`fill` 0.7 confidence, `adaptive` 0.5, 2 pt slack, same word
selection) and the outputs were checked for exact equality against it on scanned, mixed and outlined-text pages.
The recognized words become an invisible text layer in the in-memory document, so `text` and `markdown` (and later
`text()`/`markdown()` calls) include them; nothing is saved. `filledRegions` is the number of OCR words inserted.

- **Models are not in the tarball.** Point `modelDir` (or `PDFUST_OCR_MODEL_DIR`) at a directory holding
  `PP-OCRv6_det_small.rten`, `PP-OCRv6_rec_small.rten` and `ppocrv6_dict.txt` (the contents of `models/pdfust-ocr-models`,
  30 MB). Without them the call rejects with `NATIVE_PDF_UNSUPPORTED`.
- Engines are cached per `(modelDir, threads)`. `threads` defaults to min(4, CPUs). Concurrent recognitions across the
  process are bounded by `PDFUST_OCR_MAX_CONCURRENT` (default 1; each holds a page raster and detector tensors).
- `lang` is accepted for interface parity; the bundled model set is multilingual and not language-selected.
- Use a release build: a debug build runs the model ~80x slower.

### Runtime assets and build requirements

The tarball carries only the addon. Two optional asset sets are supplied by the host, both located through
process environment variables read once per process (set them before the first render or OCR call):

| Asset | Env var | Size | Needed for |
|---|---|---|---|
| OCR models: `PP-OCRv6_det_small.rten`, `PP-OCRv6_rec_small.rten`, `ppocrv6_dict.txt` (from `models/pdfust-ocr-models`) | `PDFUST_OCR_MODEL_DIR` (or the `modelDir` option) | ~30 MB | `ocrFillAsync`; without it the call rejects with `NATIVE_PDF_UNSUPPORTED` |
| CJK fallback fonts: the 8 `Noto{Sans,Serif}{JP,KR,SC,TC}-Regular.otf` files from `fonts/pdfust-fonts-*/` (OFL), flat in one directory or in a site-packages-style layout with `pdfust_fonts_*/` | `PDFUST_FONTS_DIR` | ~42 MB | rendering pages whose CJK fonts are not embedded (they render blank otherwise); loaded lazily |

Also: `PDFUST_OCR_MAX_CONCURRENT` bounds concurrent OCR calls (default 1). Always run a **release** build
(`npm run build`, or the packed tarball): the debug addon runs OCR about 80x slower and renders much slower too.
`npm test` uses whichever addon is built; the OCR tests need the models and a release build.

### Memory

`render()`/`renderAsync()` convert the raster straight to encoder samples (no intermediate RGBA copy) and, on glibc,
call `malloc_trim` after each async render/OCR task, because glibc otherwise keeps multi-megabyte rasters in the
per-thread arenas of the libuv workers. Rendering 200 dpi JPEGs from an 8 MB scan, peak RSS fell from about 147 MB to about 106 MB for one
document (Node itself is ~50 MB) and from about 370 MB to about 260-300 MB for four documents rendering in parallel
(`test/binding.test.mjs` has a bounded-RSS regression test; run `npm test`, which passes `--expose-gc`). Output
`Buffer`s are released by V8's GC, so RSS can sit a few output sizes above the floor until it runs.

### TODO / known gaps

- CJK fallback fonts are found only through `PDFUST_FONTS_DIR` (no programmatic option yet).
- A span's `font` can still be empty for glyphs the core synthesizes itself (for example emoji fallback runs).
- WebP output is lossless only (large and slow); prefer `jpeg` or `png`.
- Not exposed yet: batch multi-page render, SVG render, image pixel extraction, search, editing/saving.
- Only `x86_64-unknown-linux-gnu` is built. macOS/arm64/musl need their own build targets.
- `spans()` caps at 65,536 glyphs per page (`PDF_LIMIT`), like the Python glyph snapshot.

## Concurrency

Documents are `Send` but one document is used by one task at a time: every call locks that document, so
concurrent async calls on the same document run one after another, while different documents run in
parallel on the libuv threadpool (`UV_THREADPOOL_SIZE`, default 4). Sync calls block the event loop; use the
`*Async` variants for large pages. See `bench/results/node-binding-2026-10-12.md`.

## Build, test, pack

```sh
npm ci
npm run build:debug      # local addon (needs Rust 1.99)
npm test                 # unit tests + parity tests against the Python API (needs ../../.venv with pdfust built)
scripts/pack.sh          # reproducible release tarball via Docker; prints sha256
```

`pack.sh` builds from `git archive HEAD` inside `node:22-trixie` (the generation `worker/Dockerfile.lean`
uses; glibc 2.41, binary needs at most GLIBC_2.35) and runs `npm pack`. It never publishes.
The Cargo layout: `rust/` is the core (feature `python` = wheel, feature `native` = `document::native`), and
`bindings/node` is its own Cargo workspace root (the `[patch]` for the vendored hayro-interpret is repeated there).
