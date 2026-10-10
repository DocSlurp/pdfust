# P003 source-only availability inventory

The frozen ordinal DEV16 source contains 10,778 words and 53,615 literal codepoints. Detector ownership includes 2,205 words / 10,987 codepoints; the separately authenticated segment geometry control actually assigns 952 words / 4,240 codepoints. These are source-inventory fractions, not table-text availability, OCR correctness, or attainable cell scores. References have not been read.

The detector-owned union covers 20.46% of full-page words. The geometry control assigns 8.83% of full-page words and 43.17% of detector-owned words. Two pages with no detector proposals contain 4,627 words in total. All source text on those pages remains outside this detector acquisition pool. This acquisition gap is distinct from the correctness of text inside an acquired crop.

## Frozen per-page inventory

| Page ID | Full-page words | Detector-owned union | Geometry-assigned |
|---|---:|---:|---:|
| p42049db34e230ce77d75 | 541 | 0 | 0 |
| pc9c4bcc7f4f2a5dc3bab | 617 | 86 | 83 |
| pdb4e1fa3babeca265abb | 365 | 26 | 11 |
| p9cc5ebfad2ee46a13b5e | 208 | 48 | 30 |
| p6ef5d3c5c2edb1c109c4 | 544 | 210 | 202 |
| p1e230b0fd05df7dd5e23 | 247 | 4 | 4 |
| p391ea102f48e27fcdd65 | 65 | 42 | 38 |
| pda95432063a8a20bbe01 | 56 | 39 | 38 |
| pc848c2a56527f81021a7 | 678 | 103 | 91 |
| p98d10ef50dee4b24506a | 2,700 | 1,439 | 289 |
| p656361df32bd7d69a39e | 77 | 69 | 30 |
| p1bfa52a41a5e15015698 | 4,086 | 0 | 0 |
| p27ec5aaca0dd08c90360 | 15 | 14 | 14 |
| pe87ca2d41151f28dc44c | 346 | 81 | 81 |
| p9f92a30432da612d1bcc | 145 | 22 | 22 |
| pf012d6adb9592dab9a13 | 88 | 22 | 19 |

Each page retains complete source IDs, literal strings and display bboxes. Three separately labeled bags are frozen: full page, detector-owned union, and actual geometry-control-assigned IDs. NFC and Unicode-whitespace collapse use the existing `generalization_scoring.normalize_text`; case, punctuation, math and OCR strings are not corrected. Word-string, whitespace-token and nonspace Unicode-character multiplicities are retained. The source inventory has 4,694 repeated normalized word occurrences when summed within pages; detector ownership has 745 and assignment has 389. Repeated source IDs/text occurrences are never deduplicated. A detector union removes repeated *membership* of the same ID while recording additional ownership appearances separately.

Bags ignore word order, geometry, topology and atomic-word constraints. Character bags are especially optimistic: a character may exist in an irrelevant word, and a token may not be independently extractable from a multi-token source word. Assembly can introduce inter-word spaces, so character necessity counts exclude whitespace. The audit does not validate reuse of a word or character across multiple reference cells. Independent scoring must distinguish per-cell optimistic availability, aggregate multiplicity feasibility, and actually attainable source-conserving tables. Blank reference cells also require separate treatment; their lack of text cannot establish topology correctness.

## Geometry observations

Full-page bbox height median is 11.205 points, p10 7.801, p90 14.573, p99 22.274, and maximum 330.856. Width median is 16.716 points, p10 6.956, p90 37.168, p99 107.608, and maximum 371.292. Literal word length median is four codepoints, p10 two, p90 nine, p99 fifteen, and maximum 42. Percentiles use index `floor((n-1)*p)`; median uses the ordinary median. Bbox heights are measurements, not font sizes or confidence values.

An exact x-axis sweep examines 666,711 x-overlapping pairs and finds 10,419 positive-area source bbox pairs involving 8,482 distinct within-page IDs. No exact duplicate bbox occurrences are present. The pair IoU histogram uses edges `0, .01, .1, .25, .5, .75, .9, .99, 1` and counts `1948, 7056, 1404, 8, 3, 0, 0, 0`. Intervals are left-inclusive/right-exclusive, except the final interval includes one. Touching-only boxes are excluded from positive overlap. The histogram is exact and bounded in memory; no pair sampling occurs. These overlaps can indicate geometric ambiguity, but they do not prove extraction errors or semantic relations.

Every page additionally retains source bbox width/height/area distributions, normalized word/token lengths, overlap histograms for each subset, detector ownership IDs, maximum bbox intersection per word, center memberships, and assignment receipts. No reference-derived class or table correctness label is added.

## Authentication and handoff

Final ignored artifacts are `pipeline-p003/source-availability-v2/`. Source authentication uses complete ordinal baseline `screen-ordinal-ocr300-512-r0` and external `trusted-code/b773d57.json`. Geometry assignment uses `segment-topology-v4` and the independently approved Git-`7af212a` map `trusted-code/segment-topology-v4.json`. All geometry plans, 1,190 candidate states and composed controls are rebuilt before extracting assigned IDs. Archived source is never executed. Code and input receipts are frozen before bag preparation; complete intended records remain all16, including no-crop pages.

`pages/<id>.json` contains the full source, detector regions, reconstructed control and audit. Each audit subset has its exact literal/source-ID bag plus geometry diagnostics. `report.json` retains all page hashes and aggregate-ready counts; it records availability score as absent. `frozen.json` retains seven code hashes and external source/control trust receipts. Independent evaluation must authenticate against approved maps, rebuild the source/control/bags, and only then read authorized DEV targets. The source inventory must not change after scoring. No fresh48 confirmation data, references, hosted requests, GPU or credentials are accessed by this preparation.

Preparation took 17.054 seconds wall / 16.965 seconds self CPU, including source authentication, exact geometry replay, bags and overlap diagnostics. Serial CPU Python used OMP/OpenBLAS/MKL environment bounds of one. Peak process-lifetime RSS was 539,156 KiB including imports; timed wall/CPU excludes imports. Native thread counts are unmeasured, RSS is unsampled `getrusage`, and the host is contended. Subsequent diagnostic reconstruction is outside these timings. All16 page receipts were rebuilt and verified; version 1 page receipts are byte-identical to version 2, which only clarified the quantile-method docstring.

Five tests verify NFC/whitespace-only normalization, duplicate multiplicity, exact overlap counts, distinct detector/assigned subsets, invalid partition refusal and explicitly absent empty distributions. Ruff and module mypy pass. The 27 files occupy 7,691,376 bytes before the archival hash manifest.

Final hashes:

- Report: `3876f939f3d871098ffea16b9945d751671938994b42aea78085c2ea7219a672`.
- Frozen source/code receipt: `cfcef7584999cb81996426620f303e0633db45c945abd4762e553cc34a37c7e4`.
- Archival manifest: `3ad6c0061bf9e33f31ec47cdfe73de875dcca53078caa0479e98c5298d893159`.
