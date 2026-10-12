import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const pdfust = require('../index.js')
const assets = join(dirname(fileURLToPath(import.meta.url)), '../../../tests/assets')
const real = (name) => join(assets, 'real_world', name)
const encrypted = (name) => join(assets, 'encrypted', name)

test('version reports package version, git sha and features', () => {
  const info = pdfust.version()
  assert.match(info.version, /^\d+\.\d+\.\d+/)
  assert.ok(info.gitSha.length >= 7)
  assert.ok(info.features.includes('markdown'))
})

test('open path and buffer agree', () => {
  const a = pdfust.openPath(real('usrguide.pdf'))
  const b = pdfust.openBuffer(readFileSync(real('usrguide.pdf')))
  assert.equal(a.pageCount(), 27)
  assert.equal(b.pageCount(), 27)
  assert.equal(a.page(3).text(), b.page(3).text())
})

test('metadata, size and rotation', () => {
  const doc = pdfust.openPath(real('senate-expenditures.pdf'))
  const meta = doc.metadata()
  assert.equal(meta.encrypted, false)
  assert.equal(typeof meta.pdfVersion, 'string')
  const size = doc.page(0).size()
  assert.ok(size.widthPt > 0 && size.heightPt > 0)
  assert.ok([0, 90, 180, 270].includes(size.rotation))
})

test('encrypted documents throw PDF_LOCKED and open with the password', () => {
  assert.throws(() => pdfust.openPath(encrypted('user-aes-256.pdf')), { code: 'PDF_LOCKED' })
  assert.throws(() => pdfust.openPath(encrypted('user-aes-256.pdf'), { password: 'wrong' }), {
    code: 'PDF_LOCKED',
  })
  for (const name of ['user-aes-256.pdf', 'user-aes-128.pdf', 'user-rc4-128.pdf', 'user-rc4-40.pdf']) {
    const doc = pdfust.openPath(encrypted(name), { password: 'userpw' })
    assert.equal(doc.pageCount(), 2, name)
    assert.match(doc.page(0).text(), /Encrypted page one/, name)
    assert.equal(doc.metadata().encrypted, true)
  }
  const owner = pdfust.openPath(encrypted('owneronly-aes-256.pdf'))
  assert.match(owner.page(1).text(), /Encrypted page two/)
})

test('garbage input throws PDF_ERROR', () => {
  assert.throws(() => pdfust.openBuffer(Buffer.from('not a pdf')), { code: 'PDF_ERROR' })
})

test('limits surface as PDF_LIMIT with a stable limit code', () => {
  assert.throws(() => pdfust.openPath(real('usrguide.pdf'), { limits: { maxPages: 3 } }), (error) => {
    assert.equal(error.code, 'PDF_LIMIT')
    assert.ok(error.limit)
    return true
  })
  assert.throws(() => pdfust.openPath(real('usrguide.pdf'), { limits: { profile: 'nope' } }), {
    code: 'INVALID_ARGUMENT',
  })
})

test('out of range pages and closed documents', () => {
  const doc = pdfust.openPath(real('pdf20-simple.pdf'))
  assert.throws(() => doc.page(99), { code: 'INVALID_ARGUMENT' })
  const page = doc.page(0)
  doc.close()
  assert.throws(() => page.text(), { code: 'PDF_CLOSED' })
  assert.throws(() => doc.pageCount(), { code: 'PDF_CLOSED' })
})

test('markdown has headings and tables; async matches sync', async () => {
  const doc = pdfust.openPath(real('usrguide.pdf'))
  const page = doc.page(0)
  const markdown = page.markdown()
  assert.ok(markdown.length > 100)
  assert.equal(await page.markdownAsync(), markdown)
  assert.equal(page.markdown({ tableStrategy: 'none' }).length > 0, true)
  assert.throws(() => page.markdown({ tableStrategy: 'bogus' }), { code: 'INVALID_ARGUMENT' })
})

test('spans, glyph stats, images, drawings, tables on a scanned page', () => {
  const doc = pdfust.openPath(real('patent-us223898.pdf'))
  const page = doc.page(0)
  const images = page.images()
  assert.ok(images.length >= 1)
  assert.ok(images[0].widthPx > 100 && images[0].effectiveDpi > 50)
  assert.equal(images[0].bbox.length, 4)
  const stats = page.glyphStats()
  assert.ok(stats.glyphs > 0)
  assert.ok(stats.invisible > 0, 'OCR text layer is invisible text')
  assert.ok(page.spans().some((span) => span.invisible && span.renderMode === 3))
  assert.equal(typeof page.drawings().vectorArea, 'number')
  assert.ok(Array.isArray(page.tables()))
})

test('words keep their own boxes and cover the span text', () => {
  const doc = pdfust.openPath(real('patent-us223898.pdf'))
  const page = doc.page(0)
  const words = page.words()
  assert.ok(words.length > 0)
  for (const word of words) {
    assert.equal(word.bbox.length, 4)
    assert.ok(word.text.length > 0)
    assert.ok(word.bbox[2] >= word.bbox[0] && word.bbox[3] >= word.bbox[1])
  }
  const spanWords = page.spans().flatMap((span) => span.text.split(/\s+/).filter(Boolean)).length
  assert.ok(words.length >= spanWords * 0.8, 'words are not fewer than span tokens by a wide margin')
})

test('annotations, links and widgets', () => {
  const doc = pdfust.openPath(real('pdfium-links-highlights-annots.pdf'))
  let annotations = 0
  let widgets = 0
  let links = 0
  for (let i = 0; i < doc.pageCount(); i++) {
    annotations += doc.page(i).annotations().length
    widgets += doc.page(i).widgets().length
    links += doc.page(i).links().length
  }
  assert.ok(annotations >= 3)
  assert.ok(widgets >= 1)
  assert.ok(links >= 1)
  const form = pdfust.openPath(real('f1040.pdf'))
  const fields = form.page(0).widgets()
  assert.ok(fields.length > 20)
  assert.ok(fields.some((field) => field.name && field.kind === 'text'))
})

test('document-level facts: fonts, javascript, layers, attachments', () => {
  const doc = pdfust.openPath(real('usrguide.pdf'))
  const fonts = doc.fonts(0)
  assert.ok(fonts.length > 0)
  assert.ok(fonts.every((font) => typeof font.embedded === 'boolean'))
  assert.equal(doc.hasJavaScript(), false)
  assert.deepEqual(doc.optionalContent(), [])
  assert.deepEqual(doc.attachments(), [])
  assert.ok(pdfust.openPath(real('pdfium-type3.pdf')).fonts().some((font) => font.isType3))
})

test('render: png, jpeg, webp, gray, clip, maxEdgePx, dpi', async () => {
  const doc = pdfust.openPath(real('usrguide.pdf'))
  const page = doc.page(0)
  const png = page.render({ dpi: 36 })
  assert.deepEqual([...png.subarray(0, 4)], [0x89, 0x50, 0x4e, 0x47])
  const jpeg = page.render({ dpi: 36, format: 'jpeg' })
  assert.deepEqual([...jpeg.subarray(0, 2)], [0xff, 0xd8])
  const webp = page.render({ dpi: 36, format: 'webp' })
  assert.equal(webp.subarray(0, 4).toString('latin1'), 'RIFF')
  assert.equal(webp.subarray(8, 12).toString('latin1'), 'WEBP')
  const widthOf = (buf) => buf.readUInt32BE(16)
  const heightOf = (buf) => buf.readUInt32BE(20)
  const edge = page.render({ maxEdgePx: 300 })
  assert.equal(Math.max(widthOf(edge), heightOf(edge)), 300)
  const clipped = page.render({ dpi: 72, clip: [0, 0, 100, 50] })
  assert.equal(widthOf(clipped), 100)
  assert.equal(heightOf(clipped), 50)
  const gray = page.render({ dpi: 36, gray: true })
  assert.equal(gray[25], 0, 'PNG colour type 0 is grayscale')
  assert.ok(gray.length < png.length)
  const viaAsync = await page.renderAsync({ dpi: 36 })
  assert.ok(viaAsync.equals(png))
})

test('scan returns runs, placements and glyph stats in one pass', () => {
  const scanned = pdfust.openPath(real('patent-us223898.pdf')).page(0).scan()
  assert.ok(scanned.stats.invisible > 0 && scanned.stats.overImage > 0, 'OCR layer over a page image')
  assert.ok(scanned.spans.some((span) => span.invisible && span.renderMode === 3 && span.overImage > 0))
  assert.equal(scanned.images.length >= 1, true)
  assert.ok(scanned.images[0].dpi > 50 && scanned.images[0].dpi <= Math.min(scanned.images[0].dpiX, scanned.images[0].dpiY) + 1e-9)
  const text = pdfust.openPath(real('usrguide.pdf')).page(3)
  const full = text.scan()
  assert.equal(full.stats.glyphs, text.glyphStats().glyphs)
  assert.equal(full.stats.mapped + full.stats.unmapped, full.stats.glyphs)
  assert.equal(full.spans[0].dir.length, 2)
  assert.equal(text.scan({ spans: false }).spans.length, 0)
  assert.equal(text.scan({ images: false }).images.length, 0)
  assert.throws(() => text.scan({ hostCoverage: 2 }), { code: 'INVALID_ARGUMENT' })
})

test('fonts carry subset, encoding and pages; javascript lists locations', () => {
  const doc = pdfust.openPath(real('usrguide.pdf'))
  const fonts = doc.fonts(3)
  assert.ok(fonts.length > 0 && fonts.every((font) => font.pages.includes(3)))
  assert.ok(fonts.some((font) => font.subset && /^[A-Z]{6}\+/.test(font.name)))
  assert.equal(doc.hasJavaScript(), doc.javaScript().length > 0)
  const type3 = pdfust.openPath(real('pdfium-type3.pdf')).fonts()
  assert.ok(type3.some((font) => font.isType3 && font.type === 'Type3'))
})

const modelDir = process.env.PDFUST_OCR_MODEL_DIR ?? join(dirname(fileURLToPath(import.meta.url)), '../../../models/pdfust-ocr-models/src/pdfust_ocr_models')
const hasModels = existsSync(join(modelDir, 'PP-OCRv6_det_small.rten'))

test('ocrFillAsync without models is NATIVE_PDF_UNSUPPORTED', async () => {
  const page = pdfust.openPath(real('usrguide.pdf')).page(0)
  await assert.rejects(page.ocrFillAsync({ modelDir: '/nonexistent-ocr-models' }), (error) => {
    assert.ok(error instanceof pdfust.NotImplementedError)
    assert.equal(error.code, 'NATIVE_PDF_UNSUPPORTED')
    return true
  })
  await assert.rejects(page.ocrFillAsync({ policy: 'bogus', modelDir }), { code: 'INVALID_ARGUMENT' })
})

test('ocrFillAsync fills a page without a text layer and leaves native text alone', { skip: !hasModels && 'no OCR models', timeout: 600_000 }, async () => {
  const scan = pdfust.openPath(real('bunka-kokugo-series-019-p4.pdf')).page(0)
  assert.equal(scan.text().trim(), '')
  const first = await scan.ocrFillAsync({ policy: 'fill', dpi: 150, modelDir, threads: 2 })
  assert.equal(first.engine, 'pp-ocrv6-small-rten')
  assert.ok(first.filledRegions > 0 && first.text.trim().length > 0)
  assert.equal(first.text, scan.text(), 'the layer is part of later extraction')
  assert.equal(first.markdown, scan.markdown())
  const again = await scan.ocrFillAsync({ policy: 'fill', dpi: 150, modelDir, threads: 2 })
  assert.equal(again.filledRegions, 0, 'recognized words are already covered by the inserted layer')
  const native = pdfust.openPath(real('usrguide.pdf')).page(3)
  const before = native.text()
  const adaptive = await native.ocrFillAsync({ policy: 'adaptive', modelDir })
  assert.equal(adaptive.filledRegions, 0)
  assert.equal(adaptive.text, before)
})

test('render does not retain memory: RSS stays bounded across many renders', { skip: typeof global.gc !== 'function' && 'run with --expose-gc' }, async () => {
  const doc = pdfust.openPath(real('usrguide.pdf'))
  const rss = () => process.memoryUsage().rss / 1048576
  for (let i = 0; i < 6; i += 1) await doc.page(i).renderAsync({ dpi: 144, format: 'jpeg' })
  global.gc()
  const settled = rss()
  for (let round = 0; round < 12; round += 1) {
    await Promise.all(Array.from({ length: 4 }, (_, k) => doc.page((round * 4 + k) % doc.pageCount()).renderAsync({ dpi: 144, format: 'png' })))
  }
  global.gc()
  await new Promise((resolve) => setTimeout(resolve, 200))
  global.gc()
  const growth = rss() - settled
  assert.ok(growth < 120, `RSS grew ${growth.toFixed(0)} MB across 48 renders`)
})

const here = dirname(fileURLToPath(import.meta.url))
const python = process.env.PDFUST_PYTHON ?? join(here, '../../../.venv/bin/python')
const matrix = join(assets, 'encrypted', 'matrix')

test('invisible text is included by default and setSkipInvisibleText leaves it out', { skip: !existsSync(python) && 'no Python' }, () => {
  const dir = mkdtempSync(join(tmpdir(), 'pdfust-ocr-layer-'))
  const path = join(dir, 'layer.pdf')
  execFileSync(python, [join(here, 'make_ocr_layer.py'), path], { env: { ...process.env, PYTHONPATH: join(here, '../../../src') } })
  const doc = pdfust.openBuffer(readFileSync(path))
  const page = doc.page(0)
  assert.match(page.markdown(), /Quarterly report summary/)
  assert.deepEqual(page.text().split(/\s+/).filter(Boolean), ['Quarterly', 'report', 'summary'])
  assert.ok(page.spans().every((span) => span.invisible))
  doc.setSkipInvisibleText(true)
  assert.equal(page.text(), '')
  assert.equal(page.markdown(), '')
  assert.ok(page.spans().length > 0, 'spans still report the layer')
  doc.setSkipInvisibleText(false)
  assert.match(page.markdown(), /Quarterly report summary/)
  rmSync(dir, { recursive: true })
})

test('encryption matrix: user, empty and owner passwords on every cipher and container', () => {
  const cases = [
    ['mu-aes-256-user-xrefstm.pdf', 'userpw'],
    ['mu-aes-128-user-classic.pdf', 'ownerpw'],
    ['mu-rc4-128-empty-xrefstm.pdf', undefined],
    ['q-aes-256-r6-user-enc-objstm.pdf', 'userpw'],
    ['q-rc4-40-user-enc-classic.pdf', 'ownerpw'],
  ]
  for (const [name, password] of cases) {
    const doc = pdfust.openPath(join(matrix, name), password ? { password } : undefined)
    assert.equal(doc.pageCount(), 2, name)
    assert.match(doc.page(0).text(), /page (1|one)/i, name)
  }
  assert.throws(() => pdfust.openPath(join(matrix, 'mu-aes-256-user-xrefstm.pdf')), { code: 'PDF_LOCKED' })
})

test('unsupported security handlers are PDF_UNSUPPORTED_ENCRYPTION, not a password problem', () => {
  const source = readFileSync(join(matrix, 'mu-aes-256-user-classic.pdf'))
  const handler = Buffer.from(source.toString('latin1').replace('/Filter/Standard', '/Filter/Standar2'), 'latin1')
  for (const options of [undefined, { password: 'userpw' }]) {
    assert.throws(() => pdfust.openBuffer(handler, options), { code: 'PDF_UNSUPPORTED_ENCRYPTION' })
  }
  const revision = readFileSync(join(matrix, 'q-aes-128-user-enc-classic.pdf')).toString('latin1').replace('/R 4', '/R 9')
  assert.throws(() => pdfust.openBuffer(Buffer.from(revision, 'latin1'), { password: 'userpw' }), { code: 'PDF_UNSUPPORTED_ENCRYPTION' })
})

test('limits: the worker profile opens what web rejects, and re-reads never exhaust a page budget', () => {
  const path = real('usrguide.pdf')
  const worker = pdfust.openPath(path, { limits: { profile: 'worker' } })
  for (let i = 0; i < worker.pageCount(); i += 1) worker.page(i).markdown()
  // Every reader of an admitted page must keep working under a tight cumulative budget.
  const glyphs = pdfust.openPath(path).page(3).glyphStats().glyphs
  const tight = pdfust.openPath(path, { limits: { maxTextGlyphs: glyphs } }).page(3)
  for (const method of ['text', 'markdown', 'spans', 'glyphStats', 'words', 'scan', 'text', 'markdown']) {
    assert.doesNotThrow(() => tight[method](), method)
  }
  assert.throws(() => pdfust.openPath(path, { limits: { profile: 'nope' } }), { code: 'INVALID_ARGUMENT' })
})

test('drawings report horizontal and vertical rules, path boxes and truncation', () => {
  const page = pdfust.openPath(real('f1040.pdf')).page(0)
  const drawings = page.drawings()
  assert.equal(drawings.longRuleCount, drawings.hRuleCount + drawings.vRuleCount)
  assert.equal(drawings.paths.length, drawings.pathCount)
  assert.equal(drawings.truncated, false)
  assert.ok(drawings.paths.every((path) => path.bbox.length === 4 && /^(f|s|fs)$/.test(path.paint)))
  assert.ok(drawings.hRuleCount + drawings.vRuleCount + drawings.rectCount > 0)
})

test('spans carry line direction and writing mode', () => {
  const span = pdfust.openPath(real('usrguide.pdf')).page(3).spans()[0]
  assert.deepEqual(span.dir.map(Math.round), [1, 0])
  assert.equal(span.writingMode, 0)
  const vertical = pdfust.openPath(real('bunka-kokugo-series-019-p4.pdf')).page(0).spans()
  assert.ok(vertical.every((s) => s.dir.length === 2 && (s.writingMode === 0 || s.writingMode === 1)))
})

test('concurrent async work on different documents', async () => {
  const docs = ['usrguide.pdf', 'bill-hr815.pdf', 'f1040.pdf', 'senate-expenditures.pdf'].map((name) =>
    pdfust.openPath(real(name)),
  )
  const results = await Promise.all(
    docs.flatMap((doc) => [doc.page(0).markdownAsync(), doc.page(0).renderAsync({ dpi: 36 })]),
  )
  assert.equal(results.length, 8)
  assert.ok(results.every((value) => value.length > 0))
})

test('one document serialises concurrent async calls', async () => {
  const doc = pdfust.openPath(real('usrguide.pdf'))
  const expected = doc.page(1).markdown()
  const results = await Promise.all(Array.from({ length: 8 }, () => doc.page(1).markdownAsync()))
  assert.ok(results.every((value) => value === expected))
})
