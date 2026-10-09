# Source and collision audit, final evidence revision

Read-only CPU audit of bench/lowlevel_evidence.py. No credentials, hosted calls,
sealed corpora or broad artifact scans. Source projections were constructed from
pdf_bytes and neutral selectors before any expected labels were consulted.
Final analysis hashes complete singleton request bodies, including image data
URLs, instructions, model ID and choices. A fixed admitted model is used within
each arm: Jev for text arms, pplx for image arms. This audits region evidence;
root's three-region batches can differ because of unrelated co-batched regions,
which does not make missing divider evidence identifiable.

## Quantified intrinsic collisions

Initial cohort: 24 logical cases, 72 PDFs, 109,204 source bytes. Labels are eight
logical joins, eight splits and eight unresolved, each crossed with three encodings.

| Arm | Distinct complete request signatures | Conflicting signature buckets | Logical cases in conflicts | Total singleton request bytes |
|---|---:|---:|---:|---:|
| minimal | 16 | 4 | 12 | 86,256 |
| words | 16 | 4 | 12 | 108,735 |
| glyphs | 32 | 8 | 12 | 495,807 |
| canonical | 16 | 4 | 12 | 436,767 |
| operators | 48 | 12 | 12 | 867,355 |
| rolling | 32 | 8 | 12 | 513,447 |
| vectors | 48 | 0 | 0 | 516,267 |
| crop256 | 48 | 0 | 0 | 735,543 |
| crop512 | 48 | 0 | 0 | 1,109,499 |

All conflict buckets contain join/split/unresolved labels. They are exactly the
four wrap templates crossed with three rule variants; text, glyph geometry and
text operators remain identical. Callback order adds encoding-specific nuisance
signatures, not discriminating evidence. Canonical, minimal and words are equal
across all encoding triples. Vector/crop requests still include callback order
and so are not full-request triple-invariant, even though their image pixels and
vector geometry are invariant.

For each text-only wrap bucket no deterministic source-only selector can recover
all three full-source labels. Exact full-source agreement on the entire balanced
basic cohort has a maximum of 16/24 logical cases for singleton evidence: 12
distinct boundary controls plus one of three wrap labels per template. That is
an information ceiling, not measured model quality. Known join/split-only accuracy
has a 12/16 ceiling. The appropriate admitted-evidence answer for missing divider
information is unresolved; penalizing that abstention as an unsafe interpretation
would conflate full-source reconstruction with evidence sufficiency.

History cohort: 12 logical cases, 36 PDFs, 140,484 source bytes; three tentative
joins, three visible-identifier splits and six unresolved. There are zero
opposing-label request collisions in every arm. Canonical has exactly 12
signatures and is invariant across all triples. Words/minimal have 15 signatures
because native word clustering changes on the three reversed-paint split cases.
Glyphs/vectors/crops/rolling have 24 signatures, and operators 36, reflecting
encoding nuisance. No hash collision does not prove answerability: inferred
continuation remains conventional, not unique author intent.

History singleton bytes: minimal 50,835; words 91,383; glyphs 1,055,130;
canonical 911,400; operators 1,922,017; rolling 1,063,941; vectors 1,058,550;
crop256 1,159,710; crop512 1,330,410. These are serialized transmission sizes,
not provider tokens or charges. Root's actual batches reuse some framing.

## Candidate coverage independent of semantic grouping

Mapped each native word bbox to the non-whitespace glyph centers it owns, then
asked whether any indivisible word intersects both selected chunks. This ignores
whitespace positions because native words omit them; it does not establish exact
glyph conservation. All selected non-whitespace glyphs are covered by native
words, so failures below are grouping granularity, not missing transcription.

- Boundary: native word atoms can express the offered split on 6/12 logical
  cases, versus glyph atoms on 12/12. Restricting to the four authored split
  controls gives native coverage 2/4 versus glyph coverage 4/4. The two missing
  options occur at the two smallest gaps, across all three encodings:
  6/12 encoded split controls fail native atom coverage.
- Wrap: native word atoms and glyph atoms both express splits on 12/12 logical
  cases, including all four authored splits.
- History: both atom granularities express splits on 12/12 logical cases,
  including all three authored splits.

The actual words arm already receives glyph-derived exact chunk strings. It can
choose split inside a native word. Consequently these theoretical atom ceilings
are not a measured candidate advantage of the currently shared W/G menus.
The source-only chunk projection does not leak expected labels, but it supplies
an authored boundary location and additional source granularity beyond words.
Call W a word-context ranking arm, not an indivisible native-word baseline.

## Detected and corrected preprocessing faults

The initial crop path converted transparent RGBA directly to RGB. Black text and
black rules on transparent black pixels yielded a single-color black image:
one sampled 256px crop contained 9,728 pixels of (0,0,0), with no other color.
Its image arms had the same twelve logical collision cases as text-only evidence.
Root corrected this with explicit white alpha compositing before freezing paid
requests. Final full-image request hashes now separate all rule variants.
Independent white-background diagnostics also yielded 24 distinct basic
glyph-plus-image signatures and zero opposing labels at both resolutions.

Canonical initially retained source-sensitive native words. Root corrected it
to retain geometry-normalized glyphs/chunks without native words or callback
order. Final canonical history signatures are invariant. Earlier unsigned
diagnostics are retained in scratch for fault provenance, not accepted results.

## Native clustering reproducer for a future regression

Two same-baseline Courier10 runs suffice:

```python
from bench.feature_cases import page_pdf
from bench.lowlevel_cases import _operators
import pylopdf

runs = [("ABCDEFG", 100, 557), ("105", 40, 557)]
for encoding in ("runs", "positioned"):
    with pylopdf.Document(stream=page_pdf(_operators(runs, encoding))) as document:
        print(encoding, [w[4] for w in document[0].get_text("words")])
# runs: ['105', 'ABCDEFG']
# positioned: ['1', 'G', '05', 'ABCDEF']
```

Positioned reverses independent glyph paints. The original cohort verifies
exact pixel equality at 72/144 dpi, and the glyph channel preserves geometry.
This is a source clustering representation bug before model ranking. No Rust
changes or fixture edits were made while root froze the experiment. A future
regression should compare semantic word membership and exact pixels for these
two encodings, then test overprints separately to preserve intentional layers.

## Next model experiment justified by these measurements

First use the current frozen run to compare abstention on the twelve logically
colliding text-only wrap cases versus correct rule-aware grouping. Do not fit a
confidence threshold from mutually contradictory labels over identical evidence.
Compare canonical with source-sensitive glyph/word arms to measure nuisance
encoding flips, including the native word fragmentation cases. A header-only
baseline should precede any claimed boundary-ranking gain.

Then separately freeze an atomic candidate experiment: native word groups cannot
be partitioned, glyph groups can. Its two genuine missing split options measure
candidate recovery; do not credit a selector for options it could already choose.
Rolling history should be studied only on the separate history cohort and scored
as compression of already-present full-page evidence. Conventional joins remain
a descriptive preference slice, with conservative abstention retained.

Final audit resource scope: serial current Python process including rendering and
crops, perf_counter/process_time/getrusage lifetime peak RSS, no sampling.
108 PDFs took 6.630s wall, 6.651s CPU and 375,070,720 bytes peak RSS. This is local
preparation only. Raw audit JSON and scripts stay under this ignored scratch path.
