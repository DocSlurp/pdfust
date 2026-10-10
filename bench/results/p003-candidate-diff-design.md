# P003 complete-dispute candidate evidence

The opt-in `--evidence-mode differences` treatment reduces redundant selector text while retaining the entire frozen candidate pool locally. Candidate generation, canonical deduplication, seeded opaque aliases, strict parsing, and final exact candidate selection remain unchanged. The default whole-candidate request and config are unchanged.

The projection includes each candidate's complete table count, bounding boxes, row/column counts and merged spans. It compares matrices by table-list ordinal, row and column; every differing slot carries every candidate's exact literal value, covered-slot null, or explicit absence. All first rows appear as context, without claiming they are semantic headers. Unequal shapes and table counts produce explicit missing-slot disputes. Geometry-only differences remain visible through summaries. No changed string is normalized, clipped or excluded, and no model/provider/origin/performance/gold metadata enters the question.

Common non-first-row strings are deliberately omitted and labeled. This can hide shared transcription errors or shared missing content: the selector must not infer their correctness from agreement. It may explicitly abstain. Selection still returns the bytes of one complete frozen candidate; it never reconstructs a table from the projection, blends strings, or fills omissions.

`--evidence-max-bytes N` sets the exact UTF8 evidence limit (default 4096, maximum 131072). This is a byte admission bound on the state text, not a tokenizer measurement or guarantee about any provider's context window. Question instructions, criteria, and image transport add overhead. If complete projection does not fit, `EvidenceCapacityError` stops before a request, the crop records `evidence_capacity_retained_first`, and the entire page retains the predeclared first baseline atomically with `ranking_status=failed_retained_first`. Earlier successfully staged crops are discarded; their actual costs remain included. There is no automatic oversized-prompt fallback or truncation.

Run the existing fresh frozen-pool runner with its explicit baseline/trusted-map/model/image flags, adding:

```console
--evidence-mode differences --evidence-max-bytes 4096
```

Only opt-in runs add frozen config `evidence_mode` and `evidence_max_bytes`, and archive `p003_candidate_diff.py`. Each admitted crop retains the projection at `{id}-selector-{index}-evidence.json`; `ranking_regions[].evidence` records mode, cap, exact bytes, SHA256 and differing slot count. Exact request and response artifacts retain the existing names. Baseline generation costs and incremental selector attempts remain separate; frozen-pool ranking is not a new full-pipeline throughput measurement.

Independent verification authenticates the helper and runner against an external trusted-code map, reconstructs the immutable pool as before, then calls `p003_candidate_run._body(..., evidence_mode=config.get('evidence_mode','whole'), evidence_max_bytes=config.get('evidence_max_bytes',4096))`. It compares the complete request and projection bytes, replays the unchanged typed choice parser and exact candidate selector, and verifies the existing atomic page composition/fallback. Embedded artifact hashes cannot authenticate their own code.

Offline tests cover changed whitespace, absence/blank/covered-slot distinctions, shapes, table count and geometry-only disputes, exact selected bytes and explicit abstention, exact-cap admission, no truncation, unchanged default bodies, text-only controls, runnable mocked treatment and capacity failure before any call. No inference was performed.
