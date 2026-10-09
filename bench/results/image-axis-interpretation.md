# Completed image-axis DEV interpretation

These are **conditional synthetic cue-reading probes**, not natural PDF table
extraction. Thirty authored pages reuse ten structures across three vocabularies.
The model receives exact native lead/tail/header/value spans, literal relationship
questions and two declared assembly alternatives; it selects join, split or
unresolved. All six convention-note pages contain visible sentences that directly
state the intended relationship. Full-page images include those notes and a prior
observation band; questions explicitly instruct the model to judge document notes.
A representative RGB width-800 note was visually verified. These outcomes cannot
establish natural-document generalization, candidate discovery, OCR quality or
unconditional image helpfulness. Source conservation follows deterministic
materialization of the supplied alternatives, not independent cell extraction.

The regular matrix is complete: **936/936 unique batches**, no failed batches,
54 declared arms × four models × 30 cases. Another 468 exact-hash geometric aliases
reuse quality only; longest-edge equals height on these portrait pages. Actual
transmissions cover 4,320 page inputs for $0.53657136 effective catalog-estimated
cost; provider-reported zero is preserved. The anisotropic run is separate and
not included in this interpretation. Full cost bases and progress are in the
axis report/ignored JSON, without assigning fresh cost or latency to aliases.

Manifest SHA256: `7deeea36101bba1837659fb53310b1966edc8da1938370f860f0294ba188f1c7`.
Retained results SHA256: `6377334b6526cdc5445bfc593c8d5db1671fd1a7f7ef238cbdb8d21024425757`.

RGB exact relationship counts, each out of 30:

| Model | Axis | 200 | 300 | 400 | 500 | 600 | 800 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Luna | Width | 3 | 4 | 5 | 4 | 7 | 6 |
| Luna | Height | 3 | 3 | 3 | 4 | 3 | 6 |
| PPLX | Width | 19 | 21 | 23 | 25 | 25 | 27 |
| PPLX | Height | 18 | 18 | 21 | 22 | 24 | 25 |
| Clef Flash | Width | 11 | 12 | 15 | 16 | 16 | 17 |
| Clef Flash | Height | 12 | 13 | 12 | 14 | 17 | 15 |
| Clef | Width | 12 | 15 | 19 | 22 | 22 | 22 |
| Clef | Height | 13 | 13 | 13 | 18 | 18 | 23 |

Equal target numbers are **different image sizes**. Width targets produce
200×259, 300×388, 400×518, 500×647, 600×776 and 800×1035 pixels; height targets
produce 155×200, 232×300, 309×400, 386×500, 464×600 and 618×800. A nominal 10-point
cue note scales to approximately 3.3–13.1 pixels under width targets and
2.5–10.1 pixels under height targets. Readability of answer-bearing notes and
thin separators is therefore part of these curves. The larger area of a width
arm prevents interpreting its advantage as a pure axis effect. Improvements are
not universally monotonic: Luna width-600 exceeds width-800; Clef Flash
height-600 exceeds height-800. One observation per case/condition does not measure
run-to-run variance.

Gray8 preserves the same correct-case sets as RGB8 in **46/48** matched
model/axis/size comparisons. Exceptions: Flash height-500 fixes one case, and
Clef width-800 fixes one case, with no losses. This artwork is achromatic by
construction. These comparisons neither reject grayscale for color PDFs nor
establish its safety when source color carries meaning.

Palette4 changes some failures despite equal target geometry. Entries below are
`fixed/lost` cases relative to matching RGB8, preserving turnover even when net
counts are equal:

| Model | Axis | 200 | 300 | 400 | 500 | 600 | 800 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Luna | Width | 0/0 | 1/0 | 2/0 | 1/0 | 0/1 | 2/2 |
| Luna | Height | 0/0 | 0/0 | 0/0 | 0/1 | 1/0 | 1/1 |
| PPLX | Width | 0/4 | 1/0 | 0/1 | 0/2 | 0/0 | 0/0 |
| PPLX | Height | 0/2 | 0/1 | 0/0 | 1/0 | 2/0 | 0/2 |
| Clef Flash | Width | 0/0 | 1/2 | 4/4 | 0/0 | 1/0 | 1/0 |
| Clef Flash | Height | 4/2 | 0/2 | 2/1 | 1/4 | 2/0 | 2/0 |
| Clef | Width | 1/1 | 1/3 | 3/1 | 1/1 | 0/1 | 1/0 |
| Clef | Height | 2/0 | 0/0 | 1/2 | 2/1 | 2/0 | 0/0 |

Selected palette counts: PPLX height-600 reaches 26/30 versus RGB's 24/30;
Flash height-600 reaches 19/30 versus 17/30; Luna width-400 reaches 7/30 versus
5/30. These remain plausible complementary conditions. Quantization is not a
uniform improvement: PPLX width-200 loses four cases, and Flash height-500 fixes
one while losing four. Same aggregate accuracy can conceal different errors.

Prior full-page RGB controls at longest edges 128/512/1200 are strictly matched
for Luna/PPLX: identical source hashes, case IDs, batch membership, question menus
and non-image evidence; only image bytes and declared pixel dimensions vary.
Compared with new RGB width-800 (800×1035), old images are 99×128, 396×512 and
927×1200:

| Model | Prior arm | Prior exact | New width-800 exact | Fixed | Regressed |
| --- | --- | ---: | ---: | ---: | ---: |
| Luna | 128 | 3/30 | 6/30 | 3 | 0 |
| Luna | 512 | 5/30 | 6/30 | 2 | 1 |
| Luna | 1200 | 9/30 | 6/30 | 0 | 3 |
| PPLX | 128 | 17/30 | 27/30 | 11 | 1 |
| PPLX | 512 | 22/30 | 27/30 | 5 | 0 |
| PPLX | 1200 | 27/30 | 27/30 | 1 | 1 |

Prior Clef bounded batches differ from the new grouping, so no strictly paired
whole-cohort resolution delta is claimed for them. Native controls expose richer
explicit source rules/fills/context and are a separate evidence condition, not a
matched image-size baseline. Descriptively, earlier native exact counts were
Luna 10/30, PPLX 30/30, Flash 17/30 and Clef 25/30. Retain native, 128, 512 and
1200 options; this new DEV matrix does not invalidate earlier useful conditions.

Two combinations merit future source-grounded arbitration tests, without more
calls in this window:

1. **PPLX RGB width-800 + Clef RGB width-200.** Their post-hoc correct-case union
   is 30/30, versus 27/30 and 12/30 separately. This is an oracle ceiling, not an
   achieved ensemble. Simply replacing PPLX's six unresolved answers with Clef
   fixes three misses and breaks three justified abstentions: still **27/30**.
   Freeze a disagreement/ambiguity policy before testing it on reviewed natural
   source evidence; confidence scores alone do not identify the correct arm.
2. **PPLX RGB width-800 + Palette height-600 (or RGB width-500).** Each alternative
   contributes one otherwise missed case, giving a 28/30 oracle union. Palette
   changes encoding and footprint while width-500 supplies a cheaper intermediate
   view. Preserve both options; measure complete cost and accepted-wrong structures
   under a predeclared selection rule rather than picking an answer using gold.

Additional exploratory ceilings preserve weaker options: Luna width-600 plus
palette width-400 covers 9/30; Flash gray height-500 plus palette height-600 covers
23/30; Clef width-500 plus palette height-200 covers 28/30. These were selected
post-hoc from correlated DEV cases and are hypotheses only. Across every actual
arm, model-specific oracle ceilings are Luna 11/30, PPLX 28/30, Flash 27/30 and
Clef 29/30. A reviewed-source transfer should test ordinary typography, meaningful
negatives and ambiguous pages without fixture convention sentences. No paid
calls, GPU work, credential access or source-prompt changes were made for this
analysis.

## Completed anisotropic additions

The separate prespecified anisotropic additions finished **624/624 batches**,
with no failed batches: 24 actual arms × four models × 30 cases, 2,880 transmitted
page inputs, $0.32136624 effective catalog-estimated cost. Actual added targets
are **200/300/400/500**, width and height, RGB8/gray8/pal4. Although inherited
manifest declarations list 600/800/longest, this additions-only run has no such
anisotropic requests; none are inferred or scored. Both completed runs together
cost $0.85793760 over 7,200 actual page inputs, excluding quality aliases.

Anisotropic manifest SHA256:
`d708b7b15ec7ed3fbb539d353b5ce9aa8a357786782040642718081926a573e0`.
Retained results SHA256:
`1db2ff2fb03e02d702ec836fc03c861b6feb3e49b423e2a63d88faf40cd657fe`.

The orthogonal dimension is fixed at **512 pixels**. Width sweeps transmit
200×512, 300×512, 400×512 and 500×512; height sweeps transmit 512×200, 512×300,
512×400 and 512×500. These stretch the same full source rectangle rather than
crop it. All convention notes remain included, with the same conditional scope
as above. Width-sweep nominal 10-point notes have about 6.5 vertical pixels at
every target; height-sweep notes have about 2.5/3.8/5.1/6.3 vertical pixels.
Horizontal glyph scale changes separately. These are geometry/encoding probes,
not a controlled comparison at constant image area or natural page aspect ratio.

All **624 batch counterparts were verified** against the regular matrix for
identical source hashes, case IDs, batch membership, complete question menus and
non-image state, normalizing only the explicitly declared pixel dimensions.
RGB entries below show `exact out of 30 (fixed/lost versus matching regular RGB)`:

| Model | Changed axis | 200 | 300 | 400 | 500 |
| --- | --- | --- | --- | --- | --- |
| Luna | Width | 3 (0/0) | 4 (1/1) | 3 (0/2) | 8 (4/0) |
| Luna | Height | 3 (0/0) | 3 (0/0) | 6 (3/0) | 7 (3/0) |
| PPLX | Width | 16 (1/4) | 22 (2/1) | 23 (0/0) | 21 (0/4) |
| PPLX | Height | 19 (3/2) | 20 (4/2) | 23 (2/0) | 21 (0/1) |
| Clef Flash | Width | 11 (3/3) | 14 (6/4) | 14 (2/3) | 14 (4/6) |
| Clef Flash | Height | 9 (1/4) | 13 (2/2) | 13 (5/4) | 11 (1/4) |
| Clef | Width | 13 (2/1) | 16 (3/2) | 19 (1/1) | 18 (2/6) |
| Clef | Height | 12 (3/4) | 13 (3/3) | 14 (3/2) | 20 (4/2) |

Distortion sometimes fixes cases and sometimes loses them; even equal totals
can mask turnover. PPLX width-500 loses four earlier successes without a fix;
Luna width-500 gains four without a loss. Flash width-300 fixes six and loses
four. More pixels or a widened glyph alone therefore does not imply a safe
relationship decision. Earlier aspect-preserving options remain in scope.

Gray8 shares RGB8's correct-case sets in **31/32** anisotropic comparisons;
Clef gray height-500 loses one RGB success (19/30 versus 20/30). This remains an
achromatic fixture observation, not a color-PDF conclusion. Palette4 fix/lost
counts below compare with **matching anisotropic RGB8**, isolating representation
changes at the same distorted dimensions:

| Model | Changed axis | 200 | 300 | 400 | 500 |
| --- | --- | --- | --- | --- | --- |
| Luna | Width | 1/0 | 0/1 | 0/0 | 0/3 |
| Luna | Height | 0/0 | 0/0 | 2/1 | 2/0 |
| PPLX | Width | 2/2 | 0/1 | 0/1 | 0/0 |
| PPLX | Height | 2/1 | 0/0 | 0/1 | 0/0 |
| Clef Flash | Width | 1/1 | 2/3 | 2/0 | 1/2 |
| Clef Flash | Height | 3/2 | 2/1 | 1/1 | 2/1 |
| Clef | Width | 0/1 | 0/0 | 1/0 | 2/1 |
| Clef | Height | 3/1 | 3/0 | 1/0 | 1/2 |

Luna palette height-500 reaches 9/30 versus RGB's 7/30 and regular palette
height-500's 3/30, fixing six regular palette misses without regression. This
condition contributes one success beyond PPLX regular RGB width-800, a 28/30
post-hoc union. Flash anisotropic RGB width-500 or height-500 contributes two
beyond that PPLX arm, a 29/30 union. Clef anisotropic RGB width-200/300 contributes
all three of PPLX's remaining misses, a 30/30 union, preserving the earlier
small regular Clef complementary-view hypothesis rather than replacing it.
These are oracle overlap ceilings; none identifies a safe arbitration policy.

Across regular plus anisotropic actual arms, oracle model-specific coverage
rises from 11 to **13/30** for Luna and from 27 to **28/30** for Flash; PPLX stays
**28/30**, Clef **29/30**. Preserve anisotropic and intermediate palette options
as exploratory mechanisms, including their observed regressions. A frozen
selector and reviewed ordinary-source transfer are needed before recommending
any combination. Analysis used retained outputs only; no additional paid calls,
source mutations, inference or credentials were used.
