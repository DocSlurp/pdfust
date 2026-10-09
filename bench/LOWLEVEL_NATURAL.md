# Natural DEV row-ownership source protocol

`bench.lowlevel_natural` freezes 24 adjacent description-line pairs from the
bundled public-domain US Senate expenditure excerpt. This is a source-aware DEV
experiment on one existing document and producer, not independent validation or
an extension of authored synthetic gold. The fixture previously appeared in
region controls, whose references do not label row ownership.

The source SHA-256 is
`16921f0fc9b2c6039b23b694e0317917118ad7dd2b3a95a88518b7e144df527c`
(53,481 bytes). [The fixture inventory](../tests/assets/real_world/README.md)
documents its US-government public-domain source and MIT-licensed pdfplumber
mirror. Original104 silver sources are repository-authored encoding and geometry
controls; they are not natural documents.

## Source selection and image factors

Selection uses word geometry only: description column x=425..680, body
y=130..540, word-top clustering tolerance 0.35 points, consecutive line-top gap
at most eight points. Keep the first 24 qualifying adjacent pairs in page/top
order, inspecting at most three pages. This fixture contains one page. No
identifier, amount, lexical category, semantic label or model result influences
selection. Pairs overlap, so 24 pairs are not 24 independent documents.

The exact source glyph characters and two selector rectangles define a common
join/split/unresolved menu. Candidate groups reference retained geometric glyph
IDs; source paint order does not define the decision menu. Many apparent word
spaces are advances without space glyphs. Literal menu strings consequently
contain concatenated words. Rendering preserves their visible spacing; an
inferred-spaces text representation would be a separate future prompt factor.

Four predeclared image treatments cross description-only context x=423..682 and
record context x=80..710 with fresh source renders at requested horizontal edges
512 and 1200. Both contexts extend 18 points above/below the selected pair.
Record context retains printed payee/voucher identifiers and amounts;
description context removes those fields. The larger images are fresh renders,
not enlargement of retained crop512. RGB PNGs, source-render scale/DPI, requested
and actual outward-rounded clip rectangles, dimensions and hashes are retained.
Changing crop width also changes effective text pixel size at fixed horizontal
edge: this is a joint context/resolution treatment, not a pure context factor.
For a pure-context comparison, render both widths at an equal scale in a later
predeclared experiment.

## Freezing and annotations

```sh
.venv/bin/python -m bench.lowlevel_natural \
  --source tests/assets/real_world/senate-expenditures.pdf \
  --directory .scratch/natural-dev-source
```

`prepare(source, directory, count=24)` writes a `L011-source` manifest, source
PDF, source-only selection and observations, and 96 singleton PPLX request
templates before any annotation file is created. These templates are CPU
artifacts, not inference. `request(observation, model, arm)` rebuilds the exact
L006-style literal-state multimodal contract for all four admitted OpenRouter
vision model IDs plus `liquid/d1`; Gateway transport adaptation belongs in the
parent experiment runner. Source literal chunks/actions stay identical across
models and image treatments. Full non-image JSON must fit 1800 UTF-8 bytes and
complete bodies 200,000 bytes; excess evidence is refused without truncation.
There are no provider calls, credentials, catalogs or paid-request code here.

After all templates are frozen, `annotate(directory, references)` verifies the
source freeze and writes a separate `private-references.json`. It preserves the
source manifest. Each reference requires a choice, source evidence and explicit
uncertainty. Reviewers should inspect source screenshots and cite ordinary
record fields, not derive reference choices mechanically from the construction
policy. References carry the source-manifest hash and are explicitly single
source-aware review, not independently adjudicated structural gold.

The initial review found nine within-record joins and 15 cross-record splits
with full record context. Description-only scope was annotated as uncertain for
22 pairs; two itinerary continuations have tentative semantic support for join.
No full-context unresolved example was manufactured to balance the cohort.
Scope annotations do not guarantee that low-resolution pixels remain legible.
Report full-source reference agreement separately from agreement with admitted
scope evidence, and publish uncertain cases/abstentions. Independent human
review is needed before using these references as firm natural-quality scores.

`verify(directory)` checks source hashes and reconstructs the source-only
geometry selection, target-box inventory, retained observation hashes, and all
96 singleton templates. Tests cover all-model evidence equality, no scorer
metadata in requests, fresh PNG provenance/nonblank pixels, exact scope/menu
preservation, complete inventory and separate annotation admission. Verification
uses retained image hashes; it does not claim to independently adjudicate
business records or inspect hosted provider image consumption.
