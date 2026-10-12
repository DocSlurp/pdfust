import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
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

test('ocrFillAsync is unsupported', async () => {
  const page = pdfust.openPath(real('usrguide.pdf')).page(0)
  await assert.rejects(page.ocrFillAsync(), (error) => {
    assert.ok(error instanceof pdfust.NotImplementedError)
    assert.equal(error.code, 'NATIVE_PDF_UNSUPPORTED')
    return true
  })
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
