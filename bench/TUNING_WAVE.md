# Larger-corpus tuning wave

Started **2026-10-09 04:27 UTC**; stop new experiments by **06:27 UTC**.
The user authorized a private push and up to two hours of iterative experiments.
Available capacity is three parallel agents plus the coordinator, despite the
requested upper bound of eight agents. Each builder uses a separate worktree.

## Contract

- **Quality first:** preserve exact source ownership and cell/header relationships;
  report table-presence classification separately from full reconstruction.
- **Workloads:** the frozen 104-file / 125-page silver DEV corpus, a reproducible
  16-row public OmniDocBench DEV sample, and separately versioned DEV extensions
  when existing positive coverage cannot test a hypothesis.
- **Protected data:** the separate 20-file holdout stays unopened and untuned.
  Public benchmark familiarity/pretraining contamination is unknown.
- **Budget:** cumulative $15 authorization remains. All hosted calls use the
  shared reservation ledger. Positive reported charges take precedence; missing
  or zero charges use published prices and reported tokens, marked estimates.
- **Resources:** CPU by default; the user subsequently authorized bounded local
  GPU comparison points. Health check passed on RTX 3090. Record CPU time, wall
  time, current-exec RSS, GPU allocated/reserved VRAM and sampled utilization.
  API timing excludes local work unless explicitly measured end to end.
- **Cache:** test actual provider retransmissions and returned cache counters.
  Local replay and faster repeats are not evidence of provider cache hits.
- **Acceptance:** do not change production defaults in this screening wave.
  A candidate must retain source conservation and report every attempted input,
  error and false positive. Prefer the simpler baseline when quality ties.
  A DEV win needs fresh, preplanned confirmation before a generalization claim.
- **Artifacts:** raw images, annotations, requests, responses and traces remain
  ignored. Commit compact reports, reproducible code and source/license manifests.

## First-round priorities

| Track | Hypothesis | Evidence needed | Rejection condition |
| --- | --- | --- | --- |
| OmniDocBench sample | Real page images expose missing layout diversity | 16 metadata-stratified rows with pinned provenance and coverage | Missing license/provenance, or treating image-wrapped pages as native PDFs |
| CPU routes | Native geometry can reject prose without a model call | Exact table ownership/spans and false positives over all 125 pages | Any lost baseline grid or unsupported borderless recall claim |
| Evidence designs | Compact source geometry, neighbors or a schematic can improve decisions cheaply | Paired model results with fixed labels and body hashes | Gold-derived inputs, lost source IDs or lower quality at higher cost |
| Image matrix | Larger images recover information missing at 128 px | All sizes/color arms plus matched blanks on the same pages | Gains explained by text/batching changes or incomplete denominators |
| Row/oplog pilots | Smaller assembly decisions beat single whole-region choices | Exact records, candidate ceilings, steps, costs and failures | Source conservation confused with semantic accuracy |

The Council of Dans runs three distinct proposals: **Architect**, **Ruthless
Minimalist** and **Genius Inventor**. Preserve all three artifacts and their
rationales; the coordinator then selects the next experiments using measured
results, as the user requested.

## Progress

- Initial code and reports are local at `eeb23e5`; private push pending the sample.
- The prior full-test errors came from the unset `rustc` mise shim. Selecting the
  installed Rust 1.99 toolchain explicitly passes all 13 color-region tests;
  this is an environment repair, not an extraction change.
- Provider retransmission probe completed 18 calls. None returned cache-read or
  cache-write counters, so **no provider-cache saving is established**.
- Existing vector-grid baseline is already 10/10 exact on the silver positives.
  This corpus has no authored positive borderless targets; add a separately
  labeled DEV extension before claiming borderless recall improvement.
