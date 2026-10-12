# Preserving PDF tables and records

The strongest result in this exploratory study is a layered recovery path:
native vector cells and spans first, bounded geometry inside detected table
regions next, and OCR when there is no extracted text. Render a grid as Markdown
or HTML when its structure is known; use labeled record bullets when a complex
header cannot be represented faithfully. Screenshot-plus-text generation is a
useful optional repair, but its output needs validation and a fallback.

This recommendation comes from 28 preserved first-page inputs, including nine
independently defined positive table grids, six negative table controls, and
35 visually checked cells on two corpus pages. These are small, exploratory
cohorts. The geometry/hybrid heuristics were developed while inspecting these
inputs, so their success is not held-out production accuracy. Corpus spot checks
are not complete-page annotations. Full denominators, relationships, failures,
and report snapshot hashes are in [the comparison](structure-comparison.md).
The protocol and reproduction commands are in
[STRUCTURE_BENCHMARKS.md](../STRUCTURE_BENCHMARKS.md).

## Geometry, detection, and the bullet fallback

| Path | Positive grids | Negative controls | Corpus cells |
| --- | --- | --- | --- |
| Existing pdfust Markdown | 2/9 | 6/6 | 12/35 |
| Wrapped geometry | 7/9 | 4/6 | 29/35 |
| Normalized YOLO26m-DocLayNet plus wrapped geometry | 7/9 | 6/6 | 29/35 |
| Native header-guided record bullets | 1/9 | 6/6 | 35/35 |
| Combined native/detector/geometry/OCR HTML or bullets | 9/9 | 6/6 | 35/35 |

Geometry alone can mistake multicolumn prose for a table. YOLO's role here is
to gate regions, not to predict cells; it removed the observed false positives
without fixing merged cells or the raster-only table. Normalize by the dominant
display baseline, since page rotation metadata alone can be misleading. Native
cells preserve merged spans, and OCR supplies source words for the scan.

The record fallback is particularly useful for the Senate's ruled header and
unruled wrapped body. It retains all 23 checked Senate cells, while neutral
column labels preserve all 12 checked NICS cells without pretending to understand
its large merged header. Bullets are scored on recovered cell matrices, not on
the semantic correctness of their labels. Inferred first-row labels and header
extensions still need scrutiny; unrelated prose below a header can be absorbed.
The original neutral-label prototype dropped 65 extracted NICS header tokens.
Cell spot checks did not reveal that loss. The corrected adapters retain those
source words once as prose, including repeated labels, and rerunning all affected
CPU cohorts kept the grid/record scores while reducing NICS missing-source tokens
from 65 to zero. Prior outputs and timings remain archived. This token agreement
does not establish correct header hierarchy or complete-page reading order.

## Screenshots plus source text

The 7B olmOCR image-only baseline recovered 4/9 positive grids. Normalizing the
three rotated fixtures recovered all three. YOLO-guided crops recovered all four
small-table grids tested and the one negative control; those seven cases include
two corpus pages with only 11/35 checked cells recovered and one truncation.
Geometry crops recovered 3/4 small-table grids. Cropping helps, but the crop
selection and assembly policies are part of the result.

Dense row strips did not establish reliable record recovery: olmOCR recovered
7/35 corpus cells, with one truncation. The Senate output changed column layouts
between strips. Concatenating plausible tables is insufficient when their column
semantics disagree. Its custom whole-page source-ID patch prompt failed schema
validation on all 28 inputs. This is a failed experimental prompt, not a claim
about the complete upstream olmOCR pipeline.

The local 3B Qwen baseline frequently enclosed HTML in a Markdown code fence.
The original rendered-table score correctly counted that as code. Removing only
the outer fence recovered 0/9 image-only grids and 2/9 screenshot-plus-text grids;
there were also incorrect cells and prose represented as tables.

The larger hosted Qwen3-VL-235B-A22B control benefited much more from the same
explicit fence repair:

| Hosted path | Positive grids | Negative controls | Corpus cells |
| --- | --- | --- | --- |
| Image only, repaired whole-response fence | 6/9 | 6/6 | 23/35 |
| Screenshot plus compact source text, repaired fence | 7/9 | 6/6 | 23/35 |
| Validated compact source-ID patches | 7/9 | 5/6 | 0/35 |

The repaired prose/table conversion retained all checked Senate cells but none
of the checked NICS cells. The dense patch responses were incomplete JSON at the
4,096-token limit. Row-patch derivatives failed span/ragged-grid validation.
Keep the repair separate from the original response so both behaviors remain
visible, and validate structure before replacing source blocks.

## Jev and bounded assembly

Direct Jev is a typed text/coordinate decision in this experiment: it classifies
geometry candidates and preserves their source IDs. At an uncalibrated 0.5 cutoff
it recovered 7/9 positive grids and rejected all six negative controls. It cannot
recover missing Unicode/OCR words or fix a wrong candidate's cell relationships.

The distinct Jev Router screenshot-plus-text control recovered 8/9 positive
grids and 4/6 negative controls. Its patch variant recovered 5/9 and 5/6, with
seven failed calls. The router actually served DeepSeek and Gemini models; its
Qwen preference did not restrict it to Qwen. These results therefore do not prove
that Jev itself is a screenshot-to-Markdown model or that routing improves Qwen.
The dense row-patch router outputs exhausted their output-token boundaries.

Source-ID patches are an effective rejection boundary: refuse invented or
duplicated IDs, ragged cells, overlapping spans, and truncation. Validate every
region before appending same-width grids. IDs protect source text, but do not
prove correct columns, headers, reading order, or OCR. Preserve unassigned words
and the original candidate instead of committing a partial replacement.

## Training and memory controls

The 64-step Qwen3B NF4/LoRA pilot trained on 36 generated pages. On 12 other
generated pages, schema-valid exact recovery rose from 0/12 to 12/12. Training
took 134.95 seconds; the templates are shared across training and validation,
so this demonstrates learning the response format and simple layouts rather
than general PDF accuracy. None of the original 28 study inputs entered training.
The first attempt ended after nine steps with NVIDIA Xid 79; its losses and
kernel log are preserved separately from model-quality failures.

The 48 GiB control completed all nine full/compact text calls on Senate, NICS,
and Form 1040 without allocation failures. Both olmOCR text variants and Qwen3B
text retained 0/35 checked corpus cells; a separate Qwen fence repair also retained
0/35. Larger memory therefore removed an execution limit without establishing
correct recovery. The verbose NICS prompt occupied about 116,000 input tokens;
olmOCR's 4,096-token response truncated, while Qwen emitted only one token.
Compact dumps reduced NICS to about 52,700 input tokens, but olmOCR returned only
the page notes. These prompt/input effects are separate from weight quantization.

Increasing the image-only output boundary to 16,384 tokens retained 0/35 checked
corpus cells. Senate finished with 3,182 output tokens in 144.66 seconds; NICS used
the complete 16,384-token boundary in 745.28 seconds and produced no parsed table.
More output capacity alone therefore did not fix these dense inputs.

On the matched 17-input remote study cohort, the NF4 base failed all 17 calls.
The adapter reduced rejected calls to seven, but still recovered 0/9 exact positive
grids, rejected tables correctly on only 2/6 negative controls, and retained 0/35
checked corpus cells. Only 1/83 synthetic cells matched their exact grid positions.
The baseline and adapted row-patch variants both failed on both dense corpus pages.
The generated-page validation win therefore did not generalize to this study's
layouts. Wider training needs diverse independently labeled documents and a
template-family holdout; this pilot does not justify a production trained converter.

The fresh 2,048-by-1,243-pixel NICS image increased the model input from 1,418 to
3,342 tokens. At the original 4,096-token output boundary it still truncated,
produced no parsed table, and recovered 0/12 checked cells. More image detail alone
did not solve this example under the tested settings. The output-budget and
resolution controls are separate interventions, not a combined best-case run.

The local GPU coordinator was stopped and disabled at the user's instruction.
All remaining GPU work ran on the remote A6000. The remote jobs are complete,
the full artifact archive was downloaded and hash-verified, and the instance was
destroyed. The provider's instance-specific endpoint subsequently returned null;
the temporary SSH key pair was removed.

## Costs and implementation decision

The completed hosted controls made 138 requests for provider-reported charges
of $0.340262108, with no unsettled reservations. The provider's post-destruction
rental snapshot reports $0.684: $0.630 GPU and $0.054 storage, with transfer rows
rounded to $0.000. Combined reported spend is **$1.024262108 (about $1.02)** against
the user's $15 cap. Rental rows are rounded to three decimals; this is a billing
snapshot rather than a promise about any later invoice adjustment. The rental
watchdog was extended from two to three hours within that cap, and collection
finished before the original two-hour deadline.

Model initialization, prepared native replays, reused
detector inference, API latency, and GPU generation are different cost scopes;
their elapsed times do not support a cross-tool throughput ranking.

All 28 original PDF, screenshot, and positioned-word bundle hashes match across
the local and remote workers. The 28 downloaded model/tokenizer file hashes also
match, and all 25 successful remote output hashes were verified before rescoring.
The original remote archive is retained with SHA-256
`31a21270168baa6d283aaea4c40ea2aa2b1ea227d798a9a0657a4f66c047c825`.
Final reports remove inherited parent-run entries and retain the original archived
report hashes and run indexes. No model response was regenerated or retimed for
that provenance cleanup. CPU header-retention reruns are separately identified.

Validation: 31 benchmark tests, Ruff checks/format, and mypy on 48 source files
passed with local GPU inference disabled. Full native CI gates accompany the fork
pull request; model weights, trained adapters, full JSON, PDFs, images, and logs
remain ignored local artifacts rather than additions to the library wheel.

For an implementation, start with native structure plus conservative detected
geometry and a record-bullet fallback. Retain HTML for known merged cells and
neutral labels when header meaning is unresolved. Use a model on uncertain
regions only, with bounded images/source dumps and validated replacement patches.
The next production-quality evaluation needs independently annotated unseen
documents, mixed text/scan pages, complex headers, and complete-page reading order.
The study code and artifacts support that evaluation; these exploratory wins
alone do not justify silently enabling the hybrid heuristics for every document.
