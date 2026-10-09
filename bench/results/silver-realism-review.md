# DEV silver realism and label validity review

Reviewed on 2026-10-09 by the requested Astra review agent. Scope: repository
generators, source/target boundaries, visible DEV content, and binary table
admission labels. No held-out inputs were accessed. No hosted inference or
credentials were used. The fixes below were explicitly requested by the user.

## Findings

| Evidence | Diagnosis | Action | Confidence / effort |
| --- | --- | --- | --- |
| Rolling v1 prints different instructions for records and narratives. Its nominal prose consists of aligned station names and numbers. | Removing the instruction does not establish a correct negative label. Admission accuracy is invalid for this cohort. | Quarantine all v1 admission comparisons; preserve bytes. Replace semantics in a new version. | High / small |
| Original104 comprises 16 layout templates with four variants and four expressions with ten encodings. Visible text includes `Column 1`, `Full width conclusion`, `R1C1`, and paint-order descriptions. | These are controlled implementation probes, not representative natural documents or independent semantic examples. | Retain for PDF regressions and encoding diagnosis. Exclude from natural-document quality claims. | High / small |
| Original28 uses coherent sentence continuation for its negative pages and common furniture across classes. | Its negative semantics are stronger than rolling v1, but vocabulary, geometry, and producer ancestry remain narrow. | Keep as a separately named authored DEV slice; do not pool siblings as independent documents. | High / small |
| Original math references are four repeated ASCII expressions, including custom block glyphs and authored invisible text. | Anchor extraction cannot measure formula structure, natural mathematical typography, or OCR quality. | Keep encoding observations separate from formula and OCR evaluation. | High / small |
| Existing runners retain source bytes, private targets, exact hashes, and resource scope. | The provenance mechanism is useful; generator-derived semantics still need review. | Preserve frozen artifacts and add explicit ambiguity exclusion. | High / small |

The official [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices),
accessed 2026-10-09, recommends task-specific and representative evaluation data,
calibration against human judgment, and retaining typical, edge, and adversarial
cases. This review applies those principles to the local dataset. It is not a
provider SDK, pricing, or account audit.

## Corrected rolling v2 construction

`bench/silver_realism.py` declares 28 fictional operations documents with fixed
seed 813208: 16 borderless tables, eight continuous-prose pages, and four
ambiguous pages. `bench/rolling_robustness.py` now uses this construction.

Tables preserve the earlier geometry interventions: 2/3/6/8 total rows including
the header, 2/3/5 columns, 8/10/14 pt text, zero/one/two continuation lines,
mixed numeric alignment, header/data edge mismatch, blanks, and totals. Depot
names and named count measures replace generic station/metric labels. Total
records sum their preceding visible nonblank values. Blank values remain blank.

The negative pages contain complete paragraphs about delivery delays,
maintenance, and inventory reconciliation. Sentences continue down each of two
or three columns; numerical details occur within the grammar. Independent
columns use different stories. The 14 pt/three-column layout uses fewer complete
paragraphs so it remains inside the page. These are source semantics, not
instructions telling a decider how to classify the page.

The four ambiguous pages deliberately retain short aligned name/value
fragments. Their private references have `kind="ambiguous"`,
`truth_status="ambiguous-unscored"`, `binary_admission_eligible=false`, and
`tables=[]`. That empty array **does not mean no table**. Scorers must skip
binary admission, false-positive, and exact-structure metrics for these pages.
Their predictions, source conservation, runtime, and inference charges may
still be recorded. The local rolling scorer tests this exclusion explicitly.

All classes use the same title pool, date, footer, font resources, and PDF
producer. Every title has the same relative frequency in each class. Opaque
`dev-NNN` identifiers are assigned after a deterministic shuffle. Source
evidence exposes only word IDs/text/boxes, page bounds, image location, and
native geometric candidates. Class, rationale, setting, authored ownership,
and reference paragraphs remain in `private-targets.json`; no PDF metadata,
hidden text, or attachment carries these references.

## Freeze and verification

```sh
CUDA_VISIBLE_DEVICES='' .venv/bin/python -m bench.silver_realism \
  --output bench/results/pdf-master-artifacts/silver-realism-v2
```

The builder writes exact generator dependencies, design, PDFs, targets, and
manifest before interpretation. It then exports words, native observations,
and 120 dpi images. It never runs a semantic scorer. Content identity includes
design, PDFs, targets, and generator hashes; an existing identity is refused
rather than overwritten. `freeze-audit.json` records source hash, out-of-page
word checks, class counts, and CPU/RSS measurements. Keep prompt and candidate
configurations frozen before evaluating these inputs.

Tests check the full source word multiset against each reference paragraph,
page bounds, title balance, deterministic geometry coverage, totals arithmetic,
target isolation, overwrite refusal, and exclusion of ambiguous pages from
the scorer. Actual rendered pages are reviewed separately from those checks;
test success does not certify document realism or table extraction correctness.

The generator was committed as `cbef3bd` before the retained v2 freeze. Its
dataset SHA256 is
`124953db381d4aa6e08e138410c20a9cfbdfc74428358530b9e7d45da3f6fda4`,
under `bench/results/pdf-master-artifacts/silver-realism-v2/124953db381d4aa6/`.
The source-evidence SHA256 is
`c1002c0fbbb3332a2ce7a47567f01666f45a7a1dcb91abde54a1e983988f4b8d`.
No model admission or semantic extraction score was run by this review agent.

All 294 authored table body/header words map to source placement references
without an ambiguous ownership match. All prose reference words survive source
extraction, and no extracted word is outside its page. Visual review covered
the small two-by-two case (`dev-003`), an ambiguity control (`dev-004`), two
14 pt wrapped five-column tables including a blank and total (`dev-017`,
`dev-018`), and two-/three-column prose (`dev-019`, `dev-020`). The final frozen
prose renders confirm different continuous stories in adjacent columns; no
clipping or inter-column overlap was observed in these reviewed examples.

The CPU-only freeze took 1.233 wall seconds and 1.240 process CPU seconds with
104.12 MiB lifetime peak RSS. Measurement used `perf_counter`, `process_time`,
and `/proc/self/status` VmHWM in one sequential process, without periodic
sampling; imports are outside the timed freeze but inside lifetime RSS.
The generation/realism/rolling/borderless suite passed 29 tests, and Ruff passed.

## Remaining limits

This is a repaired synthetic DEV cohort, not an independent test set or a
sample of natural production documents. All text is newly repository-authored,
fictional, English-only, and distributed under the repository MIT license.
There are no external source documents or independently adjudicated labels.
Common story templates, one low-level producer, unembedded Helvetica, clean
rendering, and deliberately sparse small tables remain artificial. The large
font/three-column and heavily wrapped table cases are stress cases rather than
claims about typical office typography. The cohort provides no scan noise,
handwriting, camera distortion, multilingual, or natural OCR evidence.

The title balance and source projection remove known answer-bearing channels;
they do not establish training-data independence or eliminate every statistical
cue. Dense prose will naturally differ from sparse tables. Report these slices
separately and add licensed natural documents plus independent human review
before making generalization claims. No authored target should be changed
because a model or extractor disagrees with it; unclear cases remain unscored.
