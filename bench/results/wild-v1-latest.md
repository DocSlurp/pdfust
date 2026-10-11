# Wild-v1 native extraction baseline

Generated 2026-10-11 13:03 UTC from 24 base documents × 10 levels. Synthetic DEV documents; not a real-world quality claim.
Text F1 is character-bigram multiset overlap against the native text truth (order-insensitive).

| Level | Docs | Errors | Text F1 | Text F1 (NFKC) | Markdown F1 | Tables matched / exact / total | Cell recall | Title | Outline |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| L0_tagged | 24 | 0 | 0.961 | 0.961 | 0.919 | 23 / 16 / 27 | 0.834 | 24 | 24 |
| L1_untagged | 24 | 0 | 0.886 | 0.922 | 0.847 | 21 / 5 / 27 | 0.741 | 24 | 0 |
| L2_stripped | 24 | 0 | 0.886 | 0.922 | 0.847 | 21 / 5 / 27 | 0.741 | 0 | 0 |
| L3_outlined | 24 | 0 | 0.000 | 0.000 | 0.000 | 0 / 0 / 27 | 0.000 | 24 | 0 |
| L4_raster | 24 | 0 | 0.000 | 0.000 | 0.000 | 0 / 0 / 27 | 0.000 | 0 | 0 |
| L5_raster_ocr | 24 | 0 | 0.778 | 0.802 | 0.766 | 7 / 1 / 27 | 0.267 | 0 | 0 |
| L6_phone_scan | 24 | 0 | 0.000 | 0.000 | 0.000 | 0 / 0 / 27 | 0.000 | 0 | 0 |
| L7_photocopy | 24 | 0 | 0.000 | 0.000 | 0.000 | 0 / 0 / 27 | 0.000 | 0 | 0 |
| L8_mixed | 24 | 0 | 0.700 | 0.728 | 0.683 | 11 / 2 / 27 | 0.381 | 16 | 0 |
| L9_broken_tounicode | 24 | 0 | 0.003 | 0.003 | 0.003 | 0 / 0 / 27 | 0.000 | 24 | 0 |

## Unicode survival at L0 (born-digital)

| Script | Docs | Exact recall | NFKC recall |
|---|---:|---:|---:|
| ARABIC | 2 | 1.000 | 1.000 |
| CJK | 4 | 1.000 | 1.000 |
| COMBINING | 1 | 1.000 | — |
| CYRILLIC | 1 | 1.000 | 1.000 |
| DEVANAGARI | 2 | 1.000 | 1.000 |
| GREEK | 4 | 1.000 | 1.000 |
| HANGUL | 2 | 1.000 | 1.000 |
| HEBREW | 2 | 1.000 | 1.000 |
| HIRAGANA | 1 | 1.000 | 1.000 |
| KATAKANA | 1 | 1.000 | 1.000 |
| LATIN | 9 | 1.000 | 1.000 |
| OTHER | 3 | 1.000 | 1.000 |
| THAI | 1 | 1.000 | 1.000 |

| Feature | Expected chars | Kept exactly | Rate |
|---|---:|---:|---:|
| bidi_controls | 11 | 10 | 0.909 |
| combining_marks | 910 | 910 | 1.000 |
| currency | 152 | 152 | 1.000 |
| dashes | 100 | 100 | 1.000 |
| emoji | 17 | 17 | 1.000 |
| fullwidth | 158 | 158 | 1.000 |
| ligature | 2 | 2 | 1.000 |
| math_symbols | 29 | 29 | 1.000 |
| narrow_nbsp | 35 | 35 | 1.000 |
| nbsp | 107 | 107 | 1.000 |
| smart_quotes | 41 | 41 | 1.000 |
| soft_hyphen | 3 | 3 | 1.000 |
| superscripts | 17 | 17 | 1.000 |
| unicode_minus | 9 | 9 | 1.000 |
| zero_width | 31 | 5 | 0.161 |

## Extraction fixes, 2026-10-11 13:00 UTC

The audit above uses the fixed build. Compared with the first audit, L0 text
F1 rose from 0.785 to 0.961, exact tables from 7 to 16 of 27 (matched 17 to
23) and cell recall from 0.646 to 0.834. L1 rose from 0.776 to 0.886; it stays
below L0 because Ghostscript re-distillation drops the ActualText spans.

| Document | Before | After | Cause fixed |
|---|---:|---:|---|
| ja spec sheet | 0.186 | 0.971 | Type 3 full-width advance; radical normalization |
| zh-CN lab appendix | 0.289 | 0.931 | same |
| zh-TW plan comparison | 0.348 | 0.933 | same |
| ko grant budget | 0.436 | 0.978 | same |
| vi itinerary | 0.484 | 1.000 | ActualText spans around stacked marks |
| hi research page | 0.750 | 0.973 | ActualText for conjuncts mapped to U+0000 |
| th catering sheet | 0.695 | 0.964 | ActualText for clusters |
| ar memo | 0.121 | 0.658 | ActualText; NUL mappings dropped |

Remaining: Hebrew and Arabic lines that mix in numbers or Latin stay in
producer visual order, as documented, so the Arabic memo and the Hebrew
intake form (0.678) still score low.

## Findings from the first audit (2026-10-11)

Cross-checked against Poppler `pdftotext` and PyMuPDF on the same L0 files.

1. **CJK gets spaces between every glyph and Kangxi radicals.** Japanese,
   Chinese and Korean text from Chromium (Type 3 fonts with ToUnicode)
   extracts as `株 式 会 社 ⻘ 葉`, with U+2F00-block radicals such as `⽇` in
   place of `日`. Poppler and PyMuPDF return clean unified ideographs with no
   spaces. NFKC recovers the radicals (CJK recall 0.81 exact, 0.99 NFKC) but
   not the spacing. These are pylopdf bugs.
2. **Arabic is broken.** The output contains NUL characters, presentation
   forms and scrambled order (exact Arabic recall 0.25, NFKC 0.76). Poppler is
   readable but over-spaced; PyMuPDF has order errors; pylopdf is the worst.
3. **Vietnamese lines split at stacked diacritics** (`Lị\nch`, `nhe ̣`), and
   decomposed (NFD) truth text comes back precomposed (combining-mark survival
   0.40). Poppler and PyMuPDF keep the lines intact, so the line splits are a
   pylopdf bug.
4. **Hebrew lines that mix in numbers or Latin stay in visual order.** This is
   the documented mixed-direction limitation; pure Hebrew lines are correct.
5. Invisible characters are dropped as expected: bidi controls 0/11, soft
   hyphens 0/3, zero-width 5/31.
6. **Tables are the main structural gap**, even born-digital: 7 of 27 exact
   and 17 matched at L0. Re-distilled L1 drops to 4 exact.
7. Image-only levels (L3, L4, L6, L7) and L9 yield no text without OCR. The
   Tesseract OCR layer (L5) reaches text F1 0.78, about the same as native
   extraction because native CJK and Arabic are already poor, but table cell
   recall is only 0.27.
