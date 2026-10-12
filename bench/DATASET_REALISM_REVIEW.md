# DEV dataset realism and diversity review

Reviewed 2026-10-11. Scope: DEV benchmark datasets only. No held-out silver
path or `HELD-OUT-NOT-FOR-TRAINING/` Langfuse dataset was read, listed or
searched. Every search used explicit DEV include paths. No inference or GPU was
used.

**Method.** A pypdf one-off profiled the header version, xref kind, object
streams, `%%EOF` count, linearization, encryption, Info producer, StructTreeRoot,
AcroForm, page fonts (subtype, encoding, embedding, ToUnicode), content filters,
image XObjects, `3 Tr`, rotation, CropBox and annotations on the first three
pages of each file. Corpora with more than 100 files were sampled with seed 1.
pymupdf measured effective raster DPI and sampled page text. A raw-byte marker
scan covered 1,205 DEV PDFs; it can miss dictionaries stored inside compressed
object streams. The counts below are measured; ratings are judgments.

## Scorecard

| Dataset | Text realism | Layout diversity | Producer / version | Encoding / font | Raster | Scripts | Truth quality |
|---|---|---|---|---|---|---|---|
| Silver DEV 104 (`silver-v1`) | **Poor**: `Column 1 3: clear body text`, `R1C1 11` | Fair: 16 families × 4 siblings | Poor: one hand-written serializer, no producer, all classic xref | Fair: Type 3 mapped/unmapped, ActualText; otherwise unembedded Std14 | Poor: Flate RGB insets only | Poor: ASCII + `café £` | Fair: exact anchors, silver |
| Silver realism v2 (28) | Fair: coherent depot prose, totals add up | Poor: one memo template | Poor: one writer, 1.7, uncompressed | Poor: Helvetica only, no `/Encoding` | None | Poor: English | Good: ambiguous pages excluded from scoring |
| Borderless DEV (28) | Poor: `North depot received 24 units this quarter` ×N | Poor: one design, 14 settings × 2 | Poor: all 1.4, one writer | Poor: Std14 | Poor: Flate RGB inset | Poor | Fair: authored silver |
| P002 authored (156) | **Poor**: `Column 1`, `Record 1`, `Field 3 observed 17 samples`, arithmetic progressions `9.0 12.0 15.0` | Fair: 13 families | Poor: one writer, no producer | Poor: Std14 Type1, WinAnsi/none | Poor: 12 OCR carriers, ~120 dpi RGB, clean | Poor: English | Good for structure; synthetic |
| P002 OmniDocBench (64) | Good: real pages | Good: 10 genres, 5 layout classes | N/A: pixels re-wrapped as Flate RGB carriers | N/A | Fair: 200 dpi RGB, no native/scanner codecs | Fair: 35 en, 24 zh-CN, 3 mixed, 2 zh-TW | Fair: official HTML; contamination unknown |
| P002 native diagnostics (56) | Good | Fair: 38/56 pages from `usrguide` + `bill-hr815` | Good: Distiller, pdfTeX, Quartz, iText, ImageMagick, Designer | Good: MacRoman, CFF, Type 3, CID | Fair: CCITT, JBIG2, JPX once each | Fair: en, ja | Poor: incomplete, unscored |
| P003 extension 64 (`extension64-inventor-v3`) | **Poor**: `plum ticket`, `elm cobalt`, `($89,824.27) NULL`, title `Willow Elm` | Fair: 8 families × 8 | Poor: all 1.7, uncompressed, no producer | Poor: Helvetica, `/WinAnsiEncoding` or none, no ToUnicode | None | Poor | Good: exact construction; semantics meaningless |
| wild-v1 (24 docs, ~24 levels) | **Good**: invoice `$1,202.50` = 6.5 h × $185 | Good: 13 templates, photos, charts, screenshots | Fair: Skia/Chromium, LibreOffice, Ghostscript, Tesseract | Fair: CID Identity-H, Type 3, TrueType, L9 without ToUnicode | Good: 200/300 dpi, phone-scan JPEG, 1-bit photocopy, OCR layers | **Good**: 23 tags, RTL, Indic, Thai, CJK | Good: authored exact truth; only 24 sources |
| Markdown scores (27) | Fair: plausible sentences; `A\|B`, `C\D` escape probes | Fair: one element per case | Poor: 25 hand-written, 1 LibreOffice | Fair: Std14 mostly; one CID, one Type 3 | Poor: two tiny images | Fair: one Unicode/emoji/RTL case each | Good: exact element truth |
| Decision / low-level / context cases | Fair: `Revenue account 120 / Expenses 85 / Margin 35` adds up; low-level renders glyph soup | Poor: snippets, not pages | Poor: hand-written 1.7 | Poor: Std14 | None | Poor | Good: authored labels; controls only |
| Real-world assets (14) | Good | Good: forms, legislation, manuals, tables, scans | Good: 9 producers, PDF 1.3–2.0, xref streams, linearized, incremental | Good but singletons | Fair: CCITT+OCR, JBIG2, JPX, gray scan | Fair: en, ja | Poor: assertions and spot checks; one OCR transcript |

## Per-dataset findings

### 1. Silver DEV challenge (104) and realism v2 (28)

Evidence: `layout-two-column-v1` extracts as `Column 1 1: clear body text` …
`Full width conclusion`; `layout-merged-table-v2` has cells `R1C1 11`, `R2C3 23`
and the probe line `Encoding sample: café £ 25`. Headers are 1.7 (56), 1.3, 1.4
and 1.5 (16 each), but every file uses the same hand-written classic-xref
serializer with no `/Producer`. Fonts are unembedded Type1 with no `/Encoding`
(72) or WinAnsi (32). Type 3 appears 12 times, without ToUnicode in four. Images
are all Flate DeviceRGB/Gray. There are four AcroForm widgets, four rotations,
four CropBox offsets and four `3 Tr` invisible-text math cases. The 40 math
probes repeat four ASCII expressions.

Realism v2 fixes the label leakage. Its tables are arithmetically consistent:
`North 144 … Total 789`. However, all 28 pages share one title pool and masthead, one writer,
Helvetica only, no compression and an identical header/footer.

Actions:
1. Keep silver-v1 as an encoding/geometry regression suite and label it as such
   in every report. Do not regenerate the frozen bytes.
2. Build a silver-v3 cohort by reusing the 16 layout interventions with
   wild-v1-style content packs, such as real section prose and named columns.
   Emit each family through two or three real producers: Chromium, LibreOffice
   and `pdfust.insert_text` with embedded OpenType.
3. Replace the four math expressions with 20 or more natural formulas typeset by
   pdfTeX/LuaLaTeX (Type1 CM fonts and Differences) and LibreOffice Math. Keep
   the 10 encoding transforms as a separate axis.

### 2. P002 generalization corpus

Authored (156): the text is pure scaffolding. Ruled pages say
`Operations report 101 / Column 1 / Record 1 / 9.0 12.0`. Values are linear
progressions: `Record n` = `9.0 + 3.1(n-1)`. Prose pages repeat
`Field 1 observed 17 samples`. Wrapped cells say `extended description`. Of the
223 sampled files, 216 use the authored 1.7 classic-xref writer with no producer
and Type1 Standard 14 fonts. The 12 OCR carriers are about 120 dpi clean RGB.

OmniDocBench (64): real pages, but every page is a Flate RGB carrier at about
200 dpi. Native producer quirks, scan codecs and existing OCR layers are absent.
Contamination with public training data is unknown.

Native diagnostics (56): this cohort has the best producer diversity, but 38
pages come from two documents. Its references are incomplete, and these files
are also the library's own regression fixtures, so tuning leakage is high.

Actions:
1. Regenerate authored content with realistic headers, units, row labels and
   independently drawn non-progression values, keeping the geometry plan.
   Replace prose pages with real paragraphs that keep aligned numerals as the
   adversarial feature.
2. Render OCR carriers through wild-v1's L6/L7 degradations instead of clean
   120 dpi RGB.
3. Balance native pages to at most eight per source, and add complete cell
   references for the `nics` and `senate` tables.

### 3. P003 extension corpus (64)

Generated from `p003_random_values_corpus.WORDS`, a 40-word list such as
`amber`, `cedar`, `ledger` and `ticket`. Cells read `plum ticket`,
`cedar receipt`, `elm olive`, `($78,620.73)` and `TBD 09/29/2030`. Headers
duplicate (`Amount Amount Date Date`). One date column mixes ISO, US and
`Jul 12 2027` formats, and dates range from 2018 to 2031. About 14% of cells
are `N/A`, `NULL`, `TBD`, `draft` or `hold`. Negative pages are random word
paragraphs. All 64 files are 1.7, uncompressed, with Helvetica WinAnsi/none and
no producer. The structural plan is valuable, but the text gives a model no
semantic signal, and the noise is uniform rather than column-typed.

Actions:
1. Treat wild-v1 as the realistic rewrite of these plans. For model work,
   retire the word-salad text, or label it explicitly as a semantic-free control.
2. Make any new extension cohort draw values from typed generators per column:
   currency in one format, dates in one locale and monotone where natural, and
   totals that sum.

### 4. wild-v1 (24 documents)

Text is realistic: a Polish travel claim (`Rozliczenie delegacji krajowej
nr 14/2026`, `289,00 zł Bilet PKP Intercity`), a board pre-read (`Hot desk,
unlimited $319.00`) and an invoice whose hours times rate equal the amounts.
The truth covers 23 language tags and 20 Unicode features, such as
`thousands_separators` (21) and `bidi_controls` (3). The L0 producers are
Skia/PDF m152 (16) and LibreOffice 26.8 (8). Fonts are CID Identity-H (13),
Type 3 with ToUnicode (9, Chromium) and TrueType (8). L1–L3 and L9 pass through
Ghostscript 10.07.1. The rasters are well spread: L4 at 200 dpi Flate RGB, L5
at 300 dpi DCT with a Tesseract `3 Tr` CID layer, L6 at about 220 dpi phone-scan
DCT, and L7 at 300 dpi gray or 1-bit stored as **Flate**. The Arabic memo
extracts as broken visual-order glyph runs (`ة م ذ كر ة دا خ ل ي`), which is a
realistic stressor.

Problems:
- Only 24 sources: 16 one-page and 8 two-page documents. The levels are
  correlated siblings, not independent samples.
- No producer emits Type1/CFF, xref streams, object streams, AcroForm values
  (even `intake_form` is static), CCITT/JBIG2 for bitonal pages, or encryption.
- The plans are P003 extension structure, so table shapes are shared with the
  extension cohort.

Actions:
1. Grow the corpus to 80 or more documents with longer documents of 3–15 pages.
2. Add Word/`docx2pdf`, pdfTeX, ReportLab and a print-to-PDF (Quartz-like or
   cairo) producer.
3. Add an L7b level that recompresses bitonal scans as CCITT G4 and JBIG2 via
   `img2pdf`/`jbig2enc`, and an OCRmyPDF/hOCR layer that mimics scanner OCR.
4. Make `intake_form` a real AcroForm with filled `/V` values and appearances.

### 5. Markdown element cases (27)

The prose is plausible (`Revenue grew steadily during the year…`), and the
sales table is consistent: `North 1,200 + 1,350 = 2,550`. Scaffolding remains in
the inherited feature cases: `Left/Center/Right`, `Alpha A|B 42`,
`Merged header`. Production is 25 hand-written classic-xref PDFs plus one
LibreOffice tagged file. Each element appears once, so a score is effectively a
pass/fail per element type.

Actions:
1. Add three to five instances per element from real producers, such as a
   LibreOffice or Chromium document per element with lists, code and headings.
2. Add a pdfTeX paper page for math and footnotes.
3. Keep the escape-probe cells, but separate them from the realistic table rows.

### 6. Smaller authored suites

`borderless_challenge` repeats one story (`North depot received 24 units this
quarter`) across 28 cases. `decision_cases` uses coherent financial, invoice and
scientific vocabularies whose arithmetic holds (`120 − 85 = 35`).
`decision_context_cases` uses plausible line items (`Deferred revenue`,
`Reserve assets`). The lowlevel-v1 sources are character-per-operator probes
whose extraction order is reversed (`yrt elbaC`) by design. `structure_cases`
references real `senate`/`nics` rows (`DHAW20190001`,
`CITIBANK - TRAVEL CBA CARD`). All 96 decision PDFs share one hand-written 1.7
writer with Std14 fonts. These suites are appropriate as controls only, not for
realism claims.

### 7. Real-world regression assets (14 + 5 encrypted)

This is the only producer-diverse set. It spans PDF 1.3, 1.4, 1.5, 1.7 and 2.0.
It includes xref streams with object streams (f1040, usrguide, mhlw, bunka),
linearized plus incremental files (f1040, wdl6812), MacRoman TrueType (Quartz,
iText), CFF/FontFile3 (Distiller, iText), pdfTeX Type1 with Differences, CID
Identity-H (mhlw), CCITT with an ImageMagick `3 Tr` OCR layer, JBIG2+DCT, and an
ASCIIHex→LZW→JPX chain. Every quirk is a singleton, and only `bunka` has a
transcript. The encrypted fixtures (RC4-40/128, AES-128/256) are generated and
used by unit tests but appear in no benchmark corpus.

Actions:
1. Add 10–20 more documents under 1 MB with redistributable licenses: a
   Word-exported report, a bank-statement-style public-sector ledger, a
   slide-deck PDF, an arXiv-licensed (CC BY) two-column paper, a vertical-CJK
   Identity-V document and a multi-page bitonal fax.
2. Write complete text and table truth for at least five of them.

## Coverage gaps (no DEV benchmark corpus exercises these)

The raw-byte scan of 1,205 DEV PDFs found zero files with any of the following
markers:

| Quirk | Status |
|---|---|
| `Identity-V` vertical CJK CID fonts | 0 files; `mhlw` vertical text uses another path |
| `CIDFontType0` / CFF CID (Adobe-Japan1 OTF), `/OpenType` FontFile3 | 0 |
| ASCII85Decode, RunLengthDecode content/image filters | 0 |
| Encryption (`/Encrypt`) inside any benchmark | 0; only in unit-test fixtures |
| FreeText, Ink, Stamp annotations with appearance text | 0 |
| Optional content (`/OCProperties`) hiding or showing text layers | 0 |
| Article threads, PieceInfo, signed (`/Sig` values) forms | 0 or 1 incidental |
| Filled AcroForm values in a benchmark with truth | 0 (f1040 is unfilled) |
| MacRomanEncoding, Type1 with custom Differences and no ToUnicode (old Distiller/TeX) | only 2 real-world singletons each |
| Incremental updates that change text (redaction, edits, appended pages) | 0; existing incremental files do not change content |
| CCITT G4, JBIG2 and JPX bitonal/colour scans | one file each; wild-v1 L7 uses Flate 1-bit |
| Scanner-produced OCR layers (ABBYY/Acrobat ClearScan, misaligned `3 Tr` boxes) | Only ImageMagick and Tesseract layers |
| Skewed or rotated scans inside a rotated `/Rotate` page, mixed per-page rotation | 0 |
| Form XObject text, nested 3+ levels | wild L1 only (Ghostscript), 6 files |
| Type 3 fonts from real producers without ToUnicode | Only PDFium fixture and silver authored glyphs |
| Multi-page tables continuing across pages; documents longer than 2 pages with truth | 0 with truth (wild-v1 is at most 2 pages) |
| Slides (16:9 pages), bank statements, receipts and narrow POS rolls | 0 |
| Damaged/repair-needed files beyond `startxref` (broken xref, missing `endobj`) | runtime-only unit test |

## Recommended rewrite order (synthetic rows)

1. **P002 authored 156**: replace `Column n`/`Record n`/progression values and
   `Field n observed 17 samples` prose; this is the largest scored synthetic
   cohort.
2. **P003 extension 64**: retire the WORDS-based cells for any semantic or model
   evaluation; regenerate typed, arithmetically consistent values or defer to
   wild-v1.
3. **Silver DEV layout 64**: build a realistic sibling cohort (silver-v3) with
   multi-producer output; keep v1 frozen as a probe.
4. **Borderless DEV 28**: vary the story, vocabulary and producer; one template
   cannot support a realism claim.
5. **Silver math 40**: replace four ASCII formulas with natural TeX and
   LibreOffice Math output.
6. **Markdown feature-case cells** (`Alpha A|B 42`, `Left/Center/Right`): keep
   as an escape probe and add realistic tables beside them.
7. **Realism v2 28**: add second and third producers and fonts; the content is
   already acceptable.

## Leakage notes

- Native diagnostics in P002 and the structure references are the same files
  that `tests/test_real_world.py` tunes against. Any improvement measured on
  them is in-sample.
- wild-v1 and the P003 extension share plans, so do not report them as two
  independent corpora.
- OmniDocBench is public; pretraining contamination for hosted models is
  unknown.
- Template siblings (silver families, wild levels) must remain in one split.
