// Wall time for N independent documents rendered/converted through the async API.
// Run with different UV_THREADPOOL_SIZE values to see scaling.
import { createRequire } from 'node:module'
import { performance } from 'node:perf_hooks'

const require = createRequire(import.meta.url)
const pdfust = require('../index.js')
const file = process.argv[2]
const docsCount = Number(process.argv[3] ?? 8)
const pagesEach = 6
const docs = Array.from({ length: docsCount }, () => pdfust.openPath(file))

async function run(label, work) {
  const start = performance.now()
  await Promise.all(docs.map((doc) => work(doc)))
  console.log(`${label}: ${(performance.now() - start).toFixed(0)} ms for ${docsCount} docs x ${pagesEach} pages (threadpool=${process.env.UV_THREADPOOL_SIZE ?? 4})`)
}
await run('renderAsync 72dpi', async (doc) => {
  for (let i = 0; i < pagesEach; i++) await doc.page(i).renderAsync({ dpi: 72 })
})
await run('markdownAsync', async (doc) => {
  for (let i = 0; i < pagesEach; i++) await doc.page(i).markdownAsync()
})
