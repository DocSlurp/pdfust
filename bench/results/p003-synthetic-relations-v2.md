# P003 exact synthetic counterfactual twins, v2

2026-10-10. The v1 pool and preflight remain immutable historical artifacts;
they made no hosted calls. Root review caught a protocol error before inference:
native OpenRouter decision image state must contain a plain string part followed
by an image part. The current helper and runner now produce
`state=[STRING, {"type":"image_url","image_url":{"url":URL}}]`.
The image framing notice is JSON inside that string. Typed chat-style text parts
are no longer emitted. This correction is independently tested.

The new source-only authority is
`pipeline-p003/synthetic-micro-relations-v2/frozen.json`, SHA256
`fe51369b77b2f6d45c80713c9ebc8cb71b79659b37db6ae5e94c2e5418cba84e`.
Private generator labels remain separate at `private-gold.json`, SHA256
`db0f5953579379fbf74ffba9faebf8c6acad1e622b70c4fae389d137d357e2ca`,
excluded from runtime source hashes and requests. Report SHA256:
`d635fa2b85ccb49a17f592ccb0b62d2095a724be4beb0440147258e8e0eddc8d`.
Seed: `p003-synthetic-relations-20261010-v2`. All 24 intended cases are ready,
eight/kind with four same/four separate, eight unique words within each page,
192 retained word occurrences. There are 21 unique PDF payloads; three identical
borderless PDF pairs deliberately retain separate cases with opposing hidden
author memberships. These are not deduplicated or silently dropped.

Opaque **case IDs** retain independent same/separate construction identity.
The **literal seed** depends only on kind/family, independent of the hidden
same flag. Each of 12 counterfactual pairs therefore has byte-identical complete
source words, extraction IDs, boxes and `text_geometry` packet. All native
text-only requests are also byte-identical within a pair for the same model.
Words and IDs carry no label encoding. Generator labels are never consulted
by the runner, which does not invoke generation plans or open/enumerate gold.

For nine cued pairs, only actual drawing rules differ: source text positions,
headers, font, physical leading, literal strings and source geometry remain
identical. The enriched `rows_rules` state and actual source pixels differ.
All four image variants (page/crop 128/512) are checked byte-for-byte. For the
three borderless pairs (six cases), observed rules, PDFs, both geometry states,
and every pixel variant remain identical. The preparer enforces these
equivalences before freezing source authority; its12 `counterfactual_twins`
receipts contain case identities, source/text hashes and observed rule/image
equality, without identifying which case has which hidden answer.

This establishes an evidence-conditioned ceiling. A deterministic model giving
the same answer to identical evidence can match at most one opposing hidden
label per pair: at most 12/24 strict author-label matches for text geometry.
Balanced independent hidden-label expectation is 50% for evidence that cannot
distinguish twins. Stochastic repeated calls can fluctuate above or below 50%;
this is not an absolute ceiling on one sampled realization. Choosing unresolved
is a meaningful admission decision and must be reported separately from hidden
author-label agreement. Even enriched geometry and pixels cannot distinguish
the six borderless cases. No model quality has been measured.

The existing pure runner APIs and CLI remain unchanged. Source authentication
requires root's external six-code-file map plus the **v2** source frozen SHA
above; current helper equality intentionally refuses v1. Source images and full
literal packets remain independent factors, preserving all words without
truncation. Root should approve a new source authority after this commit and
prepare each desired v2 treatment before any shared client is constructed.
Do not reuse the v1 typed-text wire bodies. Counterfactual scoring must keep
complete 24 denominators and explicitly separate observed-evidence answerability
from hidden construction labels. Exact same-body repeats are fresh distinct
cases with distinct ledger tags, not automatic retry or fallback.

Seventeen tests pass, including all 12 exact geometry twins, same/opposing
memberships, rule visibility, equality/difference of all pixel variants,
native plain-string image state, source-before-gold freezing, no-gold runner
replay, strict probabilities and malformed/transport behavior. Ruff and Mypy
pass. Generation was one sequential bounded CPU process with OMP/BLAS/MKL=1,
RAYON=2: 2.677 wall seconds, 2.640 process CPU seconds, 539,156 KiB unsampled
lifetime RSS including imports. No requests, credentials, GPU or existing
corpus were used. V1 artifacts were not overwritten.
