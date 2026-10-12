// Per-page timings of the Node binding. Mirrors scripts/bench.py (Python API).
// Usage: node scripts/bench.mjs <repeats> <pdf...>  -> JSON on stdout
import { createRequire } from 'node:module'
import { performance } from 'node:perf_hooks'
import { basename } from 'node:path'

const require = createRequire(import.meta.url)
const pdfust = require('../index.js')
const repeats = Number(process.argv[2])
const files = process.argv.slice(3)
const median = (values) => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)]
const RENDER_PAGES = 12

const out = { engine: 'node', version: pdfust.version(), node: process.version, files: {} }
for (const file of files) {
  const rows = { open: [], text: [], markdown: [], markdownText: [], render72: [] }
  let pages = 0
  for (let r = 0; r < repeats; r++) {
    let t = performance.now()
    let doc = pdfust.openPath(file)
    rows.open.push(performance.now() - t)
    pages = doc.pageCount()
    // A fresh document per operation keeps the per-document page caches from leaking between rows.
    const timed = (count, run) => {
      doc.close()
      doc = pdfust.openPath(file)
      const start = performance.now()
      for (let i = 0; i < count; i++) run(doc.page(i))
      return (performance.now() - start) / count
    }
    rows.text.push(timed(pages, (page) => page.text()))
    rows.markdown.push(timed(pages, (page) => page.markdown()))
    rows.markdownText.push(timed(pages, (page) => page.markdown({ tableStrategy: 'text' })))
    rows.render72.push(timed(Math.min(pages, RENDER_PAGES), (page) => page.render({ dpi: 72 })))
    doc.close()
  }
  out.files[basename(file)] = { pages, ...Object.fromEntries(Object.entries(rows).map(([k, v]) => [k, +median(v).toFixed(3)])) }
}
out.maxRssMb = +(process.resourceUsage().maxRSS / 1024).toFixed(1)
console.log(JSON.stringify(out))
