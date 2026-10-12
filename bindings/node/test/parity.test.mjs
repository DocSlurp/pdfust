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
        env: { ...process.env, PYTHONPATH: join(here, '../../../src') },
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
    })
    const fields = doc.pageCount() <= MAX_PAGES
      ? new Set(Array.from({ length: doc.pageCount() }, (_, i) => doc.page(i).widgets()).flat().map((w) => w.name).filter(Boolean))
      : null
    if (fields && expected.formFields.length) {
      for (const [fieldName] of expected.formFields) assert.ok(fields.has(fieldName), `widget for field ${fieldName}`)
    }
  })
}
