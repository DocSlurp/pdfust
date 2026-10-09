# Image-only page embedding retrieval DEV design

Prepared 2026-10-08. This is a separate experiment from scalar relationship decisions and native color grouping. No hosted inference was performed while building these fixtures. CPU-generated pages and local scoring do not evaluate embedding quality.

## Corpus and relevance

`bench.decision_retrieval.retrieval_cases()` returns 24 authored MIT PDF pages in invoice, financial, and scientific domains. Six phrase families cover payment terms, invoice subtotal/currency, revenue growth/percentage, cash flow/amount, wavelength/unit, and dosage/frequency.

Each family contains a wrapped positive, a hyphenated positive, a hard negative with the exact same ordered words across independent ruled cells, and a near-phrase negative with a substituted number/unit or reordered words. Other families provide unrelated negatives. The wrapped/separate-cell pair keeps the words and surrounding report context equal while changing physical grouping. Relevance requires the expression to belong to one record; mere word presence across independent records does not qualify. These synthetic assumptions need review before broader use.

There are six matched queries with two positives and two explicit hard negatives each, plus two deliberately unmatched queries. All cases are DEV. There is no fresh holdout and no generalization claim.

## Image inputs

Compare separately labeled 128-pixel longest-edge pages, 512-pixel pages, and 512-pixel longest-edge ROI images. The authored display-space ROI is `[35, 122, 570, 262]`. Oracle ROI selection is supplied by the fixture recipe and is not a demonstrated detector; report it separately from whole-page retrieval. Crop from sufficient-resolution renders, rather than upscaling 128-pixel pages. Root's bounded `ImageCache` records transformations and renderer identity.

`image_embedding_body(model, data_urls)` produces only image content blocks, without extracted text, candidate IDs, labels, or native layout metadata. Queries use separate string inputs through `query_embedding_body`. Retain request/response bodies, item ordering, model identity, image hashes, source hashes, latency, errors, and shared-ledger spend in ignored artifacts. Validate one response embedding per independent input and response indexes before scoring. Model failures are failures, not zero-quality successful runs.

## Provider task handling

[OpenRouter's official embeddings API](https://raw.githubusercontent.com/OpenRouterTeam/docs/main/api_reference/embeddings.mdx) documents `input: [{content: [{type: "image_url", image_url: {url: ...}}]}]` with `encoding_format: "float"`, and plain string lists for text. Its documented request schema does not show `input_type`; the helpers omit undocumented provider fields.

[Voyage's official multimodal guide](https://docs.voyageai.com/docs/multimodal-embeddings) documents native `input_type="query"` or `"document"` for retrieval. These prepend provider prompts. This does not establish support for that parameter through OpenRouter. Treat confirmed task-aware routing as a separately labeled configuration; retain the exact body.

[Google's official Gemini embeddings guide](https://ai.google.dev/gemini-api/docs/embeddings) states that `gemini-embedding-2` does not support `task_type`. For text search queries it recommends a textual prefix of `task: search result | query: ...`. Image-only documents retain image content alone. A raw-query pilot and a documented-prefix pilot are distinct configurations; do not silently compare them as identical. Gemini's native API can aggregate multiple content inputs, so verify that the OpenRouter response preserves independent item vectors rather than assuming batch semantics.

[NVIDIA's official model card](https://build.nvidia.com/nvidia/llama-nemotron-embed-vl-1b-v2/modelcard) describes text queries and text/image documents in a shared retrieval workflow. Native task parameters and routing should be confirmed separately rather than guessed from other providers.

## Scoring and local baseline

`evaluate(document_vectors, query_vectors, cases)` accepts complete ID-to-vector maps. It rejects missing/extra IDs, empty/zero/nonfinite vectors, and dimension mismatches. Cosine normalization rescales before squaring to handle finite extreme magnitudes. Ties sort by document ID deterministically and remain explicit in output; a tied positive/negative comparison is not a pair win.

Report hit@1 and hit@3, true recall@1 and recall@3, MRR, strict within-family positive-versus-hard-negative pair wins/ties, complete rankings and cosine scores. Each matched query has two positives, so maximum recall@1 is 0.5; hit@1 can be 1.0. Do not conflate these metrics.

No-match queries are excluded from matched-query retrieval averages. Forced closed-set top retrieval counts as a false hit for each no-match query. No abstention threshold is calibrated or applied; a later threshold needs independent evidence. Similarity is not a correctness probability.

The separately labeled native normalized literal baseline joins line-wrap hyphens, collapses whitespace, and casefolds extracted text. Local result on pylopdf 0.13.0: six matched queries each produce three literal matches (two positives plus the separate-cell hard negative); two unmatched queries produce zero literal matches. ID-based tie resolution yields hit@1=1.0, recall@1=0.5, recall@3=1.0, MRR=1.0, strict pair-win rate=0.5, and 12 pair ties. That apparently perfect MRR does not resolve the layout hard negative. If forced into closed-set retrieval, both unmatched queries still return false hits; the literal presence gate itself can abstain on them.

Validation: 11 Python tests pass; scoped Ruff and mypy pass. Tests cover fixture/native baseline ambiguity, image-only request shape, deterministic cosine/ties, extreme finite vectors, invalid vector rejection, missing IDs, no-match separation, and wrapped-hyphen normalization. No embedding performance results are claimed here.
