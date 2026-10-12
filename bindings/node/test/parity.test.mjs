// Compares the Node binding with the Python API on the repository's real-world fixtures.
// Skipped when no Python with pdfust is available (set PDFUST_PYTHON to override).
import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const require = createRequire(import.meta.url)
const pdfust = require('../index.js')
const here = dirname(fileURLToPath(import.meta.url))
const assets = join(here, '../../../tests/assets/real_world')
const python = process.env.PDFUST_PYTHON ?? join(here, '../../../.venv/bin/python')
const skip = existsSync(python) ? false : `no Python at ${python}`
const MAX_PAGES = 6

const fixtures = [
  'usrguide.pdf',
  'f1040.pdf',
  'senate-expenditures.pdf',
  'nics-background-checks-2015-11.pdf',
  'bill-hr815.pdf',
  'pdf20-simple.pdf',
  'mhlw-doc.pdf',
  'patent-us223898.pdf',
  'pdfium-links-highlights-annots.pdf',
]

const close = (a, b, tolerance = 0.01) => Math.abs(a - b) <= tolerance

for (const name of fixtures) {
  test(`parity: ${name}`, { skip }, () => {
    const path = join(assets, name)
    const expected = JSON.parse(
      execFileSync(python, [join(here, 'parity.py'), path, String(MAX_PAGES)], {
        maxBuffer: 256 * 1024 * 1024,
        env: { ...process.env, PYTHONPATH: process.env.PDFUST_PYTHONPATH ?? join(here, '../../../src') },
      }),
    )
    const doc = pdfust.openPath(path)
    assert.equal(doc.pageCount(), expected.pageCount)
    expected.pages.forEach((want, index) => {
      const page = doc.page(index)
      const label = `${name} p${index + 1}`
      assert.equal(page.text(), want.text, `${label} text`)
      for (const strategy of ['lines', 'text', 'none']) {
        assert.equal(page.markdown({ tableStrategy: strategy }), want.markdown[strategy], `${label} markdown(${strategy})`)
      }
      const size = page.size()
      assert.ok(close(size.widthPt, want.size[0]) && close(size.heightPt, want.size[1]), `${label} size`)
      assert.equal(size.rotation, want.rotation, `${label} rotation`)
      assert.equal(page.tables().length, want.tables.length, `${label} tables`)
      assert.equal(page.annotations().length, want.annots.length, `${label} annotations`)
      assert.equal(page.links().length, want.links, `${label} links`)
      assert.equal(page.images().length >= want.images ? true : page.images().length === want.images, true, `${label} images`)
      const fonts = doc.fonts(index).map((f) => [f.name, f.type, f.embedded, f.hasToUnicode, f.isType3])
      assert.deepEqual(fonts, want.fonts, `${label} fonts`)
      const widgets = page.widgets().map((w) => [w.kind, w.name ?? '', w.value ?? null, w.filled, w.readOnly, w.required])
      assert.deepEqual(widgets, want.widgets.map((w) => [w[0], w[1] ?? '', w[2] ?? null, w[3], w[4], w[5]]), `${label} widgets`)
      const scan = page.scan()
      assert.deepEqual(
        {
          glyphs: scan.stats.glyphs, mapped: scan.stats.mapped, unmapped: scan.stats.unmapped, invisible: scan.stats.invisible,
          stroke: scan.stats.stroke, type3: scan.stats.type3, control_chars: scan.stats.controlChars, over_image: scan.stats.overImage,
        },
        want.scan.stats, `${label} scan stats`)
      assert.equal(scan.spans.length, want.scan.spans, `${label} scan spans`)
      assert.deepEqual(scan.spans.slice(0, 5).map((s) => [s.text, s.font, s.renderMode, s.glyphs]), want.scan.first, `${label} scan first spans`)
      assert.deepEqual(
        scan.images.map((i) => [i.widthPx, i.heightPx, Math.round(i.dpi * 1000) / 1000, i.stencil]),
        want.scan.images.map((i) => [i[0], i[1], Math.round(i[2] * 1000) / 1000, i[3]]), `${label} scan images`)
    })
    assert.equal(doc.hasJavaScript(), expected.javascript, `${name} javascript`)
    assert.deepEqual(doc.optionalContent().map((g) => [g.name, g.visible]), expected.ocgs, `${name} ocgs`)
    assert.deepEqual(doc.attachments().map((a) => [a.name, a.size]), expected.attachments, `${name} attachments`)
    const fields = doc.pageCount() <= MAX_PAGES
      ? new Set(Array.from({ length: doc.pageCount() }, (_, i) => doc.page(i).widgets()).flat().map((w) => w.name).filter(Boolean))
      : null
    if (fields && expected.formFields.length) {
      for (const [fieldName] of expected.formFields) assert.ok(fields.has(fieldName), `widget for field ${fieldName}`)
    }
  })
}
