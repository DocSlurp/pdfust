# PDF extraction tuning wave — 2026-10-09

The strongest new reviewed-DEV result combines source-derived row/extent candidates,
a semantic selection prompt and a 512 px page image: PPLX recovered 16/16 tables
exactly and rejected all eight prose controls. This is an authored development
sample, not independent natural-document or production validation. Four ambiguous
pages are excluded from accuracy; their decisions and charges remain recorded.

## Model-stage comparison on the same reviewed pages

| Model | Candidate menu | Exact tables | Incorrectly accepted tables | Prose false tables | Pages/USD | Pages/HTTP minute |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PPLX | Seed corridors and continuation union | 12/16 | 2 | 0/8 | 2,793 | 36.5 |
| PPLX | Union plus local-gap extent alternatives | **16/16** | **0** | **0/8** | 2,771 | 36.3 |
| Luna | Seed corridors and continuation union | 8/16 | 5 | 0/8 | 794 | 178.9 |
| Luna | Union plus local-gap extent alternatives | 9/16 | 4 | 0/8 | 786 | 154.1 |

Rates count all 28 transmitted pages per model, including four unscored ambiguous
pages. HTTP minutes sum request durations; they exclude local extraction and are
not end-to-end throughput. Positive reported charges take precedence; zero or
missing charges fall back to retained catalog prices and reported tokens.
See the [earlier union](rolling-topology-admission.md) and
[extent union](rolling-extent-admission.md) for all decisions, source conservation,
preparation CPU/RSS and cost provenance.

## Older techniques retained and combined

The [CPU SLANet sweep](specialist-resolution.md) completed 336 outputs across three
DPIs and four crop/padding modes. Its best observed arm, 72 DPI with 12 pt padding,
recovered 7/16 tables exactly. Every arm proposed tables on all eight prose pages.
Higher rendering DPI did not consistently improve this sample.

[Strict source agreement](specialist-agreement.md) between that specialist and
T005 geometry accepted seven correct tables, no incorrect scored tables and no
prose false tables. It deferred nine positive tables; two ambiguous acceptances
remain unscored. The additional retained PPLX gate conjunction is an offline
routing simulation, with no measured new latency or cache savings.

[Prompt tuning](prompt-tuning.md) keeps all 15 generic variants, including losses.
The original borderless/prose set and revised reviewed set are reported separately.
The earlier fresh set contained source answer cues and is quarantined; simply
removing those cues left ambiguous negative labels, so that arm is diagnostic too.

## Image-size evidence and its limits

The [axis matrix](image-axes-progress.md) covers 200, 300, 400, 500, 600 and 800 px;
width, height and longest-edge limits; RGB8, gray8 and palette4; and four models.
The regular matrix completed 936 unique requests. Exact geometric aliases share
quality observations only. They receive no new cost, throughput or provider-cache
credit. Anisotropic fixed-partner dimensions form a separate matrix.

These 30 synthetic cases explicitly test document-specific conventions. Their
page images contain convention notes, so the scores measure conditional reading
and assembly, not natural-table extraction. The source artwork is achromatic;
matched grayscale results cannot establish behavior on colored documents.
Actual width, height, pixels and bytes accompany every arm. A nominal 400 px width
and 400 px height are different evidence budgets.

## Additional training references

The [training registry](../omnidoc-training/README.md) adds 16 OmniDocBench
references, separate by exact source ID from the existing DEV16, across ten source
genres, five language categories and five layout categories. Geometry and visible
style guide newly authored synthetic derivatives. Parent references and descendants
remain one TRAINING group, never independent evaluation examples. Unknown original
document identity is explicit.

Astra reviewed every source/derivative pair and corrected masks, line density,
fonts, vertical CJK, code, formula placement and rotated credits. Photographs,
handwriting and exact internal table geometry remain labeled approximations.
The source dataset's research-only restriction is retained; this is not a
commercially cleared training corpus. Raw reference assets remain local and
ignored; registries, code, tests and reports are tracked in Git.

## Next experiments guided by the failures

1. Transfer the size/axis sweep unchanged to the reviewed table/prose set and
   additional natural pages; include genuinely colored sources before concluding
   anything about grayscale or reduced bit depth.
2. Combine source-only presence gating with expanded extent selection, measuring
   actual two-stage latency and cost rather than adding historical rates.
3. Test generic cross-cell and reading-order prompts on the expanded menu to
   investigate Luna's residual selection errors without changing source evidence.
4. Use specialist/geometry agreement as a selective route, then investigate its
   nine deferred positive tables. Keep disagreements as evidence for arbitration.
5. Freeze any cross-model arbitration rule before scoring it. Oracle unions of
   correct answers show complementary errors but are not deployable routing gains.

The protected 20-file heldout set remains sealed. No experimental hosted model
is enabled in default extraction.
