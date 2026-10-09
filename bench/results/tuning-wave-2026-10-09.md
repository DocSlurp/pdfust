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

## Prompt transfer on the expanded menu

| Model | Prompt | Exact tables | Incorrectly accepted tables | Prose false tables | Pages/USD | Pages/HTTP minute |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| PPLX | Cross-cell relationships | 16/16 | 0 | 0/8 | 2,769 | 32.4 |
| PPLX | Reading order | 16/16 | 0 | 0/8 | 2,768 | 36.4 |
| Luna | Cross-cell relationships | 10/16 | 4 | 0/8 | 785 | 179.4 |
| Luna | Reading order | 8/16 | 6 | 0/8 | 785 | 183.3 |

The two generic prompts were frozen earlier, then transferred by changing only
instructions. Four ambiguous pages remain unscored. Cross-cell relationships
helped Luna by one exact table; reading order reduced exactness and increased
wrong accepts. Both outcomes remain published. See
[cross-cell results](extent-prompt-E002_cross_cell_relations.md) and
[reading-order results](extent-prompt-E003_reading_order.md).

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
The regular matrix completed 936 unique requests; the separate anisotropic matrix completed 624, with no failures. Together they cost USD 0.85793760 for 7,200 transmitted case inputs. Exact geometric aliases share
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
3. Inspect Luna's residual selection errors after the completed prompt transfer;
   cross-cell instructions improved one case, while reading-order instructions
   regressed. Freeze any new rule before measuring another cohort.
4. Use specialist/geometry agreement as a selective route, then investigate its
   nine deferred positive tables. Keep disagreements as evidence for arbitration.
5. Freeze any cross-model arbitration rule before scoring it. Oracle unions of
   correct answers show complementary errors but are not deployable routing gains.

The protected 20-file heldout set remains sealed. No experimental hosted model
is enabled in default extraction.

## Completion, accounting and validation

The 04:27–06:27 UTC wave stopped paid work before its deadline. Original prompt
sweeps completed all 15 variants for both models. Reviewed-set Luna completed all
15; PPLX completed eight and 27/28 calls on a ninth. One interrupted request has
no retained response and keeps its reservation; the persistent guard leaves six
PPLX variants unattempted. These missing results are not observed model errors.

Conservative cumulative accounting is **USD 6.3056201568 / USD 15**: USD
2.7781951488 current provider-reported charges, USD 1.00316290 current catalog
estimates, USD 1.50 unresolved reservations, and USD 1.024262108 prior
provider/rental accounting. Reported/estimated costs excluding reservations total
USD 4.8056201568. No provider-cache savings are inferred from local reuse.

Validation: 2,027 full-suite passes, 16 skips and two expected failures; 40 focused
passes after subsequent changes; final Ruff and mypy pass. The selected 16-page
training derivative revision has no page-bound word violations or metadata
errors. Its research-only provenance and remaining realism limits are retained.
