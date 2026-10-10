# P003 complete276: independently verified segmented pipelines

On the existing natural64 DEV subset, Luna crop transcription obtains 1,953 strict cells and 14 complete tables, versus ordinal OCR/Haiku 1,182 cells and nine tables. The full corpus aggregate is dominated by authored layouts: their 5,050 reference cells supply most of both totals. Natural, authored and unadjudicated native diagnostics are therefore reported separately. These are single contended observations, without a treatment selection for fresh confirmation.

The dedicated Luna natural64 run previously scored 1,348 strict cells and 12 complete tables, with one page error. The natural64 portion of this repeat scores 1,953 and 14, with no page errors. This is repeated-run variation, not a stable frontier win: all 64 source records and crop plans match, and all 56 paired crop requests have identical actual compact wire-body hashes and identical encoded image hashes. Both frozen configs declare transport concurrency three. Only seven crop table outputs and 30 complete page table outputs match across observations; the source-only audit found no changed or missing paired requests. No fresh confirmation configuration was selected from these outcomes.

Each run attempted all 276 original source pages. Cell/table quality is defined on 220 scored pages (249 tables, 8,897 cells); 56 native pages remain diagnostic-only. All operational failures remain in 276-page error/rate counts and the relevant scored subset, without inventing diagnostic gold.

| Cohort | Pipeline | Attempted / usable / errors | Scored / diagnostic | Strict / expected cells | Text | Structure | Complete / expected tables | Missing / extra | Negative FP |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| omnidoc | Ordinal OCR / Haiku | 64 / 61 / 3 | 64 / 0 | 1182 / 3847 | 1205 | 1563 | 9 / 93 | 49 / 27 | 0 / 24 |
| omnidoc | Vision crops / Luna | 64 / 64 / 0 | 64 / 0 | 1953 / 3847 | 1973 | 2606 | 14 / 93 | 32 / 4 | 0 / 24 |
| authored | Ordinal OCR / Haiku | 156 / 156 / 0 | 156 / 0 | 5050 / 5050 | 5050 | 5050 | 156 / 156 | 0 / 17 | 11 / 24 |
| authored | Vision crops / Luna | 156 / 156 / 0 | 156 / 0 | 4949 / 5050 | 4949 | 5025 | 152 / 156 | 1 / 8 | 8 / 24 |
| native-diagnostic | Ordinal OCR / Haiku | 56 / 52 / 4 | 0 / 56 | Unadjudicated | — | — | Unadjudicated | — | — |
| native-diagnostic | Vision crops / Luna | 56 / 55 / 1 | 0 / 56 | Unadjudicated | — | — | Unadjudicated | — | — |

| Full corpus pipeline | Strict /8,897 | Text | Structure | Complete /249 | Missing / extra | Negative FP /48 | All failures /276 |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| Ordinal OCR / Haiku | 6232 | 6255 | 6613 | 165 / 249 | 49 / 44 | 11 / 48 | 7 / 276 |
| Vision crops / Luna | 6902 | 6922 | 7631 | 166 / 249 | 33 / 12 | 8 / 48 | 1 / 276 |

| Pipeline | All API attempts | Effective API USD / basis | Preserved reported gateway USD | Supervisor segment wall s | Usable pages/min | Usable pages/APIUSD | Aggregate parent CPU / sampled RSS |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| Ordinal OCR / Haiku | 117 | 0.1205097 / provider-reported USD | 0.1205097 | 3027.625 | 5.33091 | 2232.19 | Unknown / unknown |
| Vision crops / Luna | 240 | 0.08655564 / provider-reported BYOK upstream plus gateway USD | 0 | 3396.271 | 4.85827 | 3177.15 | Unknown / unknown |

These rates apply to all original plus continuation work, including failures. They count usable pipeline outputs, not exact pages or complete tables. Same-arm supervisor intervals include startup/cleanup and exclude queue idle gaps. No cost or latency is allocated to a cohort/family. The stopped original parent lacks CPU/RSS measurements, so aggregate totals stay unknown; measured continuation worker/parent resources remain separately retained. BYOK accounting preserves reported gateway zero and sums positive reported upstream plus gateway charges; it is not an invoice claim.

Independent verification authenticated original and continuation code using external maps, actual PDFs, all completed outputs, copied immutable segment archives, and same-model/config/source equality. It reconstructed the combined report/output bytes and checked no completed/error page was repeated. The one request-only original page was admitted solely by the explicit root-reviewed zero-transmission proof and immutable ledger snapshot; no process IDs were used to signal or alter a process. All 117 ordinal and 240 Luna attempts were reconstructed from exact segment prefixes in captured ledger snapshots, with receipt hashes and supervisor interval hashes checked. No original report or ledger was rewritten.

The ordinary run report lacks complete original attempt counters, so its original accounting remains unknown in the generic score record. The separately verified snapshot totals above are exported as `verified_continuation_measurements`; detailed source/ledger/queue/proof hashes remain in ignored evaluation JSON. The pure continuation helper is independently Git-anchored at `8fd75551`, with no archived code execution. No new API calls, protected heldout access or fresh confirmation tuning occurred.

## Existing manifest family breakdown

Families are taken verbatim from the frozen source manifest. Diagnostic-only families have operational counts and no claimed table/cell quality.

| Family | Pipeline | Attempted / usable / errors | Scored / diagnostic | Strict / expected cells | Complete / expected tables | Missing / extra | Negative FP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| authored/blank | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/blank | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/borderless | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/borderless | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/cropped | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/cropped | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/decorative | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 0 / 0 | 0 / 0 | 0 / 10 | 4 / 12 |
| authored/decorative | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 0 / 0 | 0 / 0 | 0 / 8 | 8 / 12 |
| authored/dense | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 1894 / 1894 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/dense | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 1894 / 1894 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/merged | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 252 / 252 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/merged | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 252 / 252 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/mixed | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 528 / 528 | 24 / 24 | 0 / 0 | 0 / 0 |
| authored/mixed | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 528 / 528 | 24 / 24 | 0 / 0 | 0 / 0 |
| authored/multiple | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 528 / 528 | 24 / 24 | 0 / 0 | 0 / 0 |
| authored/multiple | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 528 / 528 | 24 / 24 | 0 / 0 | 0 / 0 |
| authored/ocr-carrier | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/ocr-carrier | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/prose | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 0 / 0 | 0 / 0 | 0 / 7 | 7 / 12 |
| authored/prose | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 12 |
| authored/rotated | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/rotated | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 163 / 264 | 8 / 12 | 1 / 0 | 0 / 0 |
| authored/ruled | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/ruled | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/wrapped | Ordinal OCR / Haiku | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| authored/wrapped | Vision crops / Luna | 12 / 12 / 0 | 12 / 0 | 264 / 264 | 12 / 12 | 0 / 0 | 0 / 0 |
| native/bill-hr815.pdf | Ordinal OCR / Haiku | 19 / 19 / 0 | 0 / 19 | Unadjudicated | Unadjudicated | — | — |
| native/bill-hr815.pdf | Vision crops / Luna | 19 / 19 / 0 | 0 / 19 | Unadjudicated | Unadjudicated | — | — |
| native/bunka-kokugo-series-019-p4.pdf | Ordinal OCR / Haiku | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/bunka-kokugo-series-019-p4.pdf | Vision crops / Luna | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/f1040.pdf | Ordinal OCR / Haiku | 2 / 2 / 0 | 0 / 2 | Unadjudicated | Unadjudicated | — | — |
| native/f1040.pdf | Vision crops / Luna | 2 / 1 / 1 | 0 / 2 | Unadjudicated | Unadjudicated | — | — |
| native/mhlw-doc.pdf | Ordinal OCR / Haiku | 2 / 2 / 0 | 0 / 2 | Unadjudicated | Unadjudicated | — | — |
| native/mhlw-doc.pdf | Vision crops / Luna | 2 / 2 / 0 | 0 / 2 | Unadjudicated | Unadjudicated | — | — |
| native/nics-background-checks-2015-11.pdf | Ordinal OCR / Haiku | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/nics-background-checks-2015-11.pdf | Vision crops / Luna | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/patent-us223898.pdf | Ordinal OCR / Haiku | 4 / 4 / 0 | 0 / 4 | Unadjudicated | Unadjudicated | — | — |
| native/patent-us223898.pdf | Vision crops / Luna | 4 / 4 / 0 | 0 / 4 | Unadjudicated | Unadjudicated | — | — |
| native/pdf20-simple.pdf | Ordinal OCR / Haiku | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdf20-simple.pdf | Vision crops / Luna | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdfium-jpx-lzw.pdf | Ordinal OCR / Haiku | 1 / 0 / 1 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdfium-jpx-lzw.pdf | Vision crops / Luna | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdfium-links-highlights-annots.pdf | Ordinal OCR / Haiku | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdfium-links-highlights-annots.pdf | Vision crops / Luna | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdfium-smask-blend.pdf | Ordinal OCR / Haiku | 1 / 0 / 1 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdfium-smask-blend.pdf | Vision crops / Luna | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdfium-type3.pdf | Ordinal OCR / Haiku | 1 / 0 / 1 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/pdfium-type3.pdf | Vision crops / Luna | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/senate-expenditures.pdf | Ordinal OCR / Haiku | 1 / 0 / 1 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/senate-expenditures.pdf | Vision crops / Luna | 1 / 1 / 0 | 0 / 1 | Unadjudicated | Unadjudicated | — | — |
| native/usrguide.pdf | Ordinal OCR / Haiku | 19 / 19 / 0 | 0 / 19 | Unadjudicated | Unadjudicated | — | — |
| native/usrguide.pdf | Vision crops / Luna | 19 / 19 / 0 | 0 / 19 | Unadjudicated | Unadjudicated | — | — |
| native/wdl6812-manuscript.pdf | Ordinal OCR / Haiku | 2 / 2 / 0 | 0 / 2 | Unadjudicated | Unadjudicated | — | — |
| native/wdl6812-manuscript.pdf | Vision crops / Luna | 2 / 2 / 0 | 0 / 2 | Unadjudicated | Unadjudicated | — | — |
| omni/multiple-table | Ordinal OCR / Haiku | 16 / 15 / 1 | 16 / 0 | 599 / 2921 | 4 / 69 | 46 / 2 | 0 / 0 |
| omni/multiple-table | Vision crops / Luna | 16 / 16 / 0 | 16 / 0 | 1254 / 2921 | 8 / 69 | 30 / 4 | 0 / 0 |
| omni/no-table | Ordinal OCR / Haiku | 24 / 22 / 2 | 24 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 24 |
| omni/no-table | Vision crops / Luna | 24 / 24 / 0 | 24 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 24 |
| omni/single-table | Ordinal OCR / Haiku | 24 / 24 / 0 | 24 / 0 | 583 / 926 | 5 / 24 | 3 / 25 | 0 / 0 |
| omni/single-table | Vision crops / Luna | 24 / 24 / 0 | 24 / 0 | 699 / 926 | 6 / 24 | 2 / 0 | 0 / 0 |
