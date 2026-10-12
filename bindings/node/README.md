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
`PdfustError` with `code` in `PDF_LOCKED`, `PDF_LIMIT` (plus `limit`, e.g. `decompressed_size`),
`PDF_ERROR`, `INVALID_ARGUMENT`, `PDF_CLOSED`, `NATIVE_PDF_UNSUPPORTED` (`NotImplementedError`).

## Coverage of `ADAPTER-INTERFACE.md`

| Interface member | Status | Notes |
|---|---|---|
| `version()` | done | `{version, gitSha, features}`; sha comes from the commit the tarball was packed from |
| `openPath`, `openBuffer` + `password` | done | wrong or missing password throws `PDF_LOCKED`; extra `limits` option (`profile: 'web'` or individual byte/page caps, `PDF_LIMIT`) |
| `pageCount`, `metadata` | done | adds author/subject/keywords/dates/pdfVersion/repaired; `permissions` are lopdf flag names |
| `hasJavaScript` | done | any `/JS` entry or `/S /JavaScript` action anywhere in the file |
| `optionalContent` | done | OCG names and default visibility (`/D` `BaseState`, `/ON`, `/OFF`) |
| `attachments` | done | name and decoded size (decodes each attachment to measure it) |
| `fonts(page?)` | done | from page (and form XObject) resources; `embedded`, `hasToUnicode`, `isType3` |
| `page(i)`, `close()` | done | closed documents throw `PDF_CLOSED` |
| `size()` | done | displayed size in points, plus `/Rotate` |
| `text()` | done | identical to Python `get_text("text")` on the parity fixtures |
| `markdown`, `markdownAsync` | done | `tableStrategy` `lines`/`text`/`none`; Rust port of the Python builder, byte-identical on the parity fixtures |
| `spans()` | done | reading-order spans; `renderMode`/`invisible` come from the page's glyphs (OCR text layers show `invisible`). `unmapped` is always 0 per span, use `glyphStats()` |
| `images()` | done | placements only, nothing decoded; `effectiveDpi` is the lower of x/y |
| `drawings()` | done | counts of line segments, rectangles, long rules (probe thresholds), plus union `vectorArea` in pt² |
| `widgets()` | done | AcroForm widgets with kind, qualified name, value |
| `annotations()`, `links()` | done | `links()` adds `kind` and 0-based `destPage` |
| `tables()` | done | `lines` and `text` strategies; adds `rowCount`, `colCount`, `confidence` |
| `render`, `renderAsync` | done | `dpi`, `maxEdgePx`, `clip` (points), `format` png/jpeg/webp, `gray`, `quality` |
| `ocrFillAsync` | **unsupported** | throws `NATIVE_PDF_UNSUPPORTED` |
| `glyphStats()` (extra) | done | `{glyphs, invisible, stroke, unmapped, fonts}` for text-layer probes |
| `takeWarnings()` (extra) | done | engine warnings, e.g. repaired cross-reference table |

### TODO / known gaps

- `ocrFillAsync`: the OCR engine and model data are not wired into this binding (OCR work belongs to the core
  extraction track). Callers must treat `NATIVE_PDF_UNSUPPORTED` as "fall back".
- CJK fallback fonts: the Python wrapper auto-loads installed locale font packages; this binding does not, so
  non-embedded CJK glyphs may render differently.
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
