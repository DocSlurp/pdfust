# Wild-v1 native extraction baseline

Generated 2026-10-11 08:05 UTC from 24 base documents × 10 levels. Synthetic DEV documents; not a real-world quality claim.
Text F1 is character-bigram multiset overlap against the native text truth (order-insensitive).

| Level | Docs | Errors | Text F1 | Text F1 (NFKC) | Markdown F1 | Tables matched / exact / total | Cell recall | Title | Outline |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| L0_tagged | 24 | 0 | 0.785 | 0.827 | 0.752 | 17 / 7 / 27 | 0.646 | 24 | 24 |
| L1_untagged | 24 | 0 | 0.776 | 0.818 | 0.744 | 17 / 4 / 27 | 0.640 | 24 | 0 |
| L2_stripped | 24 | 0 | 0.776 | 0.818 | 0.744 | 17 / 4 / 27 | 0.640 | 0 | 0 |
| L3_outlined | 24 | 0 | 0.000 | 0.000 | 0.000 | 0 / 0 / 27 | 0.000 | 24 | 0 |
| L4_raster | 24 | 0 | 0.000 | 0.000 | 0.000 | 0 / 0 / 27 | 0.000 | 0 | 0 |
| L5_raster_ocr | 24 | 0 | 0.778 | 0.802 | 0.766 | 7 / 1 / 27 | 0.267 | 0 | 0 |
| L6_phone_scan | 24 | 0 | 0.000 | 0.000 | 0.000 | 0 / 0 / 27 | 0.000 | 0 | 0 |
| L7_photocopy | 24 | 0 | 0.000 | 0.000 | 0.000 | 0 / 0 / 27 | 0.000 | 0 | 0 |
| L8_mixed | 24 | 0 | 0.604 | 0.635 | 0.588 | 11 / 2 / 27 | 0.379 | 16 | 0 |
| L9_broken_tounicode | 24 | 0 | 0.003 | 0.003 | 0.003 | 0 / 0 / 27 | 0.000 | 24 | 0 |

## Unicode survival at L0 (born-digital)

| Script | Docs | Exact recall | NFKC recall |
|---|---:|---:|---:|
| ARABIC | 2 | 0.252 | 0.762 |
| CJK | 4 | 0.809 | 0.992 |
| COMBINING | 1 | 0.040 | — |
| CYRILLIC | 1 | 1.000 | 1.000 |
| DEVANAGARI | 2 | 0.917 | 0.940 |
| GREEK | 4 | 1.000 | 1.000 |
| HANGUL | 2 | 1.000 | 1.000 |
| HEBREW | 2 | 1.000 | 1.000 |
| HIRAGANA | 1 | 1.000 | 1.000 |
| KATAKANA | 1 | 1.000 | 1.000 |
| LATIN | 9 | 1.000 | 0.999 |
| OTHER | 3 | 1.000 | 1.000 |
| THAI | 1 | 0.934 | 0.935 |

| Feature | Expected chars | Kept exactly | Rate |
|---|---:|---:|---:|
| bidi_controls | 11 | 0 | 0.000 |
| combining_marks | 910 | 366 | 0.402 |
| currency | 152 | 152 | 1.000 |
| dashes | 100 | 99 | 0.990 |
| emoji | 17 | 17 | 1.000 |
| fullwidth | 158 | 137 | 0.867 |
| ligature | 2 | 2 | 1.000 |
| math_symbols | 29 | 29 | 1.000 |
| narrow_nbsp | 35 | 35 | 1.000 |
| nbsp | 107 | 107 | 1.000 |
| smart_quotes | 41 | 41 | 1.000 |
| soft_hyphen | 3 | 0 | 0.000 |
| superscripts | 17 | 17 | 1.000 |
| unicode_minus | 9 | 9 | 1.000 |
| zero_width | 31 | 5 | 0.161 |

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
