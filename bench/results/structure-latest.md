# Structured PDF recovery experiments

Run: 2026-10-08T03:18:26.318705+00:00

Page 0 of each preserved input is evaluated. Full inputs, screenshots, positioned words, prompts,
raw responses, validated patches, and errors are retained locally in `structure-artifacts/`.
Reference cells are independent fixture definitions; corpus cells without a reference remain unscored.
Source agreement is not ground truth, especially for missing Unicode, scans, or OCR corrections.
Geometry bullet results score their underlying recovered cells, not reparsed bullet labels.
Timing covers the adapter after preparation, excluding fixture extraction/rendering; prepared baselines
are replayed, so their timing is not a conversion measurement. Process RSS is cumulative high-water RSS.
Model repetitions include the first inference; initialization is reported separately. No throughput claims.
CUDA figures are observed peak allocated bytes for retained generation calls, not reserved VRAM.
The provenance device is the requested backend; native geometry/OCR and replay/repair adapters use CPU.

| Case | Adapter | Exact grid | Cells | Relations recalled | Record cells | Seconds | CUDA GiB | Result |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| text-structure-and-literals | pdfust | True | — | — | — | 0.000 | — | ok |
| positioned-math | pdfust | True | — | — | — | 0.000 | — | ok |
| math-actualtext | pdfust | True | — | — | — | 0.000 | — | ok |
| accessible-actualtext | pdfust | unscored | — | — | — | 0.000 | — | ok |
| two-column-order | pdfust | True | — | — | — | 0.000 | — | ok |
| unicode-cmap-and-emoji | pdfust | unscored | — | — | — | 0.000 | — | ok |
| table-bordered | pdfust | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless | pdfust | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-merged | pdfust | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| links-and-outline | pdfust | unscored | — | — | — | 0.000 | — | ok |
| images-and-vectors | pdfust | unscored | — | — | — | 0.000 | — | ok |
| image-only | pdfust | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-aligned | pdfust | False | 0/8 | 0/10 | — | 0.001 | — | ok |
| rotated-columns | pdfust | True | — | — | — | 0.000 | — | ok |
| footnotes-and-page-furniture | pdfust | True | — | — | — | 0.000 | — | ok |
| rtl-visual-glyph-order | pdfust | unscored | — | — | — | 0.000 | — | ok |
| tagged-reading-order | pdfust | unscored | — | — | — | 0.000 | — | ok |
| corpus-usrguide | pdfust | unscored | — | — | — | 0.001 | — | ok |
| corpus-senate-expenditures | pdfust | unscored | — | — | 0/23 | 0.001 | — | ok |
| corpus-nics-background-checks-2015-11 | pdfust | unscored | — | — | 12/12 | 0.019 | — | ok |
| corpus-pdfium-type3 | pdfust | unscored | — | — | — | 0.000 | — | ok |
| corpus-f1040 | pdfust | unscored | — | — | — | 0.001 | — | ok |
| omml-equations | pdfust | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-rotate-90 | pdfust | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-borderless-rotate-180 | pdfust | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-borderless-rotate-270 | pdfust | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-borderless-scanned | pdfust | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-wrapped-records | pdfust | False | 0/12 | 0/17 | — | 0.000 | — | ok |
| text-structure-and-literals | pdfust-text | True | — | — | — | 0.000 | — | ok |
| positioned-math | pdfust-text | True | — | — | — | 0.000 | — | ok |
| math-actualtext | pdfust-text | True | — | — | — | 0.000 | — | ok |
| accessible-actualtext | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| two-column-order | pdfust-text | False | — | — | — | 0.000 | — | ok |
| unicode-cmap-and-emoji | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| table-bordered | pdfust-text | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless | pdfust-text | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-merged | pdfust-text | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| links-and-outline | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| images-and-vectors | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| image-only | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-aligned | pdfust-text | True | 8/8 | 10/10 | — | 0.000 | — | ok |
| rotated-columns | pdfust-text | True | — | — | — | 0.000 | — | ok |
| footnotes-and-page-furniture | pdfust-text | True | — | — | — | 0.000 | — | ok |
| rtl-visual-glyph-order | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| tagged-reading-order | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| corpus-usrguide | pdfust-text | unscored | — | — | — | 0.001 | — | ok |
| corpus-senate-expenditures | pdfust-text | unscored | — | — | 0/23 | 0.001 | — | ok |
| corpus-nics-background-checks-2015-11 | pdfust-text | unscored | — | — | 12/12 | 0.017 | — | ok |
| corpus-pdfium-type3 | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| corpus-f1040 | pdfust-text | unscored | — | — | — | 0.002 | — | ok |
| omml-equations | pdfust-text | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-rotate-90 | pdfust-text | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-borderless-rotate-180 | pdfust-text | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-borderless-rotate-270 | pdfust-text | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-borderless-scanned | pdfust-text | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-wrapped-records | pdfust-text | False | 0/12 | 0/17 | — | 0.000 | — | ok |
| text-structure-and-literals | yolo-geometry | True | — | — | — | 2.317 | — | ok |
| positioned-math | yolo-geometry | True | — | — | — | 0.041 | — | ok |
| math-actualtext | yolo-geometry | True | — | — | — | 0.039 | — | ok |
| accessible-actualtext | yolo-geometry | unscored | — | — | — | 0.038 | — | ok |
| two-column-order | yolo-geometry | True | — | — | — | 0.042 | — | ok |
| unicode-cmap-and-emoji | yolo-geometry | unscored | — | — | — | 0.093 | — | ok |
| table-bordered | yolo-geometry | True | 9/9 | 12/12 | — | 0.041 | — | ok |
| table-borderless | yolo-geometry | True | 9/9 | 12/12 | — | 0.040 | — | ok |
| table-merged | yolo-geometry | False | 8/9 | 9/12 | — | 0.040 | — | ok |
| links-and-outline | yolo-geometry | unscored | — | — | — | 0.040 | — | ok |
| images-and-vectors | yolo-geometry | unscored | — | — | — | 0.040 | — | ok |
| image-only | yolo-geometry | unscored | — | — | — | 0.039 | — | ok |
| table-borderless-aligned | yolo-geometry | True | 8/8 | 10/10 | — | 0.040 | — | ok |
| rotated-columns | yolo-geometry | True | — | — | — | 0.114 | — | ok |
| footnotes-and-page-furniture | yolo-geometry | True | — | — | — | 0.041 | — | ok |
| rtl-visual-glyph-order | yolo-geometry | unscored | — | — | — | 0.035 | — | ok |
| tagged-reading-order | yolo-geometry | unscored | — | — | — | 0.040 | — | ok |
| corpus-usrguide | yolo-geometry | unscored | — | — | — | 0.046 | — | ok |
| corpus-senate-expenditures | yolo-geometry | unscored | — | — | 0/23 | 0.049 | — | ok |
| corpus-nics-background-checks-2015-11 | yolo-geometry | unscored | — | — | 6/12 | 0.107 | — | ok |
| corpus-pdfium-type3 | yolo-geometry | unscored | — | — | — | 0.101 | — | ok |
| corpus-f1040 | yolo-geometry | unscored | — | — | — | 0.056 | — | ok |
| omml-equations | yolo-geometry | unscored | — | — | — | 0.040 | — | ok |
| table-borderless-rotate-90 | yolo-geometry | False | 0/9 | 0/12 | — | 0.041 | — | ok |
| table-borderless-rotate-180 | yolo-geometry | False | 0/9 | 0/12 | — | 0.041 | — | ok |
| table-borderless-rotate-270 | yolo-geometry | False | 0/9 | 0/12 | — | 0.041 | — | ok |
| table-borderless-scanned | yolo-geometry | False | 0/9 | 0/12 | — | 0.040 | — | ok |
| table-wrapped-records | yolo-geometry | False | 0/12 | 0/17 | — | 0.039 | — | ok |
| text-structure-and-literals | yolo-geometry-wrapped | True | — | — | — | 0.194 | — | ok |
| positioned-math | yolo-geometry-wrapped | True | — | — | — | 0.040 | — | ok |
| math-actualtext | yolo-geometry-wrapped | True | — | — | — | 0.040 | — | ok |
| accessible-actualtext | yolo-geometry-wrapped | unscored | — | — | — | 0.038 | — | ok |
| two-column-order | yolo-geometry-wrapped | True | — | — | — | 0.042 | — | ok |
| unicode-cmap-and-emoji | yolo-geometry-wrapped | unscored | — | — | — | 0.035 | — | ok |
| table-bordered | yolo-geometry-wrapped | True | 9/9 | 12/12 | — | 0.041 | — | ok |
| table-borderless | yolo-geometry-wrapped | True | 9/9 | 12/12 | — | 0.039 | — | ok |
| table-merged | yolo-geometry-wrapped | False | 8/9 | 9/12 | — | 0.040 | — | ok |
| links-and-outline | yolo-geometry-wrapped | unscored | — | — | — | 0.039 | — | ok |
| images-and-vectors | yolo-geometry-wrapped | unscored | — | — | — | 0.039 | — | ok |
| image-only | yolo-geometry-wrapped | unscored | — | — | — | 0.038 | — | ok |
| table-borderless-aligned | yolo-geometry-wrapped | True | 8/8 | 10/10 | — | 0.040 | — | ok |
| rotated-columns | yolo-geometry-wrapped | True | — | — | — | 0.043 | — | ok |
| footnotes-and-page-furniture | yolo-geometry-wrapped | True | — | — | — | 0.041 | — | ok |
| rtl-visual-glyph-order | yolo-geometry-wrapped | unscored | — | — | — | 0.036 | — | ok |
| tagged-reading-order | yolo-geometry-wrapped | unscored | — | — | — | 0.039 | — | ok |
| corpus-usrguide | yolo-geometry-wrapped | unscored | — | — | — | 0.045 | — | ok |
| corpus-senate-expenditures | yolo-geometry-wrapped | unscored | — | — | 0/23 | 0.049 | — | ok |
| corpus-nics-background-checks-2015-11 | yolo-geometry-wrapped | unscored | — | — | 6/12 | 0.049 | — | ok |
| corpus-pdfium-type3 | yolo-geometry-wrapped | unscored | — | — | — | 0.037 | — | ok |
| corpus-f1040 | yolo-geometry-wrapped | unscored | — | — | — | 0.056 | — | ok |
| omml-equations | yolo-geometry-wrapped | unscored | — | — | — | 0.041 | — | ok |
| table-borderless-rotate-90 | yolo-geometry-wrapped | False | 0/9 | 0/12 | — | 0.041 | — | ok |
| table-borderless-rotate-180 | yolo-geometry-wrapped | False | 0/9 | 0/12 | — | 0.040 | — | ok |
| table-borderless-rotate-270 | yolo-geometry-wrapped | False | 0/9 | 0/12 | — | 0.041 | — | ok |
| table-borderless-scanned | yolo-geometry-wrapped | False | 0/9 | 0/12 | — | 0.040 | — | ok |
| table-wrapped-records | yolo-geometry-wrapped | True | 12/12 | 17/17 | — | 0.040 | — | ok |
| text-structure-and-literals | olmocr-image | True | — | — | — | 4.322 | 15.84 | ok |
| positioned-math | olmocr-image | True | — | — | — | 2.026 | 15.84 | ok |
| math-actualtext | olmocr-image | True | — | — | — | 1.549 | 15.84 | ok |
| accessible-actualtext | olmocr-image | unscored | — | — | — | 1.546 | 15.84 | ok |
| two-column-order | olmocr-image | True | — | — | — | 5.033 | 15.84 | ok |
| unicode-cmap-and-emoji | olmocr-image | unscored | — | — | — | 1.402 | 15.79 | ok |
| table-bordered | olmocr-image | False | 8/9 | 9/12 | — | 4.092 | 15.84 | ok |
| table-borderless | olmocr-image | True | 9/9 | 12/12 | — | 4.343 | 15.84 | ok |
| table-merged | olmocr-image | False | 8/9 | 9/12 | — | 4.729 | 15.84 | ok |
| links-and-outline | olmocr-image | unscored | — | — | — | 1.995 | 15.84 | ok |
| images-and-vectors | olmocr-image | unscored | — | — | — | 2.702 | 15.84 | ok |
| image-only | olmocr-image | unscored | — | — | — | 1.610 | 15.84 | ok |
| table-borderless-aligned | olmocr-image | True | 8/8 | 10/10 | — | 4.567 | 15.84 | ok |
| rotated-columns | olmocr-image | True | — | — | — | 5.661 | 15.84 | ok |
| footnotes-and-page-furniture | olmocr-image | True | — | — | — | 2.333 | 15.84 | ok |
| rtl-visual-glyph-order | olmocr-image | unscored | — | — | — | 1.674 | 15.79 | ok |
| tagged-reading-order | olmocr-image | unscored | — | — | — | 1.993 | 15.84 | ok |
| corpus-usrguide | olmocr-image | unscored | — | — | — | 19.079 | 15.79 | ok |
| corpus-senate-expenditures | olmocr-image | unscored | — | — | 0/23 | 93.437 | 15.84 | ok |
| corpus-nics-background-checks-2015-11 | olmocr-image | unscored | — | — | 0/12 | 119.902 | 15.78 | truncated |
| corpus-pdfium-type3 | olmocr-image | unscored | — | — | — | 1.995 | 15.82 | ok |
| corpus-f1040 | olmocr-image | unscored | — | — | — | 49.383 | 15.84 | ok |
| omml-equations | olmocr-image | unscored | — | — | — | 4.013 | 15.84 | ok |
| table-borderless-rotate-90 | olmocr-image | False | 8/9 | 9/12 | — | 5.052 | 15.84 | ok |
| table-borderless-rotate-180 | olmocr-image | False | 0/9 | 6/12 | — | 5.412 | 15.84 | ok |
| table-borderless-rotate-270 | olmocr-image | False | 3/9 | 6/12 | — | 5.752 | 15.84 | ok |
| table-borderless-scanned | olmocr-image | True | 9/9 | 12/12 | — | 5.085 | 15.84 | ok |
| table-wrapped-records | olmocr-image | True | 12/12 | 17/17 | — | 6.142 | 15.84 | ok |
| text-structure-and-literals | olmocr-text | True | — | — | — | 3.723 | 16.33 | ok |
| positioned-math | olmocr-text | True | — | — | — | 2.484 | 15.95 | ok |
| math-actualtext | olmocr-text | True | — | — | — | 1.816 | 15.86 | ok |
| accessible-actualtext | olmocr-text | unscored | — | — | — | 1.840 | 15.87 | ok |
| two-column-order | olmocr-text | True | — | — | — | 8.389 | 17.33 | ok |
| unicode-cmap-and-emoji | olmocr-text | unscored | — | — | — | 2.859 | 15.93 | ok |
| table-bordered | olmocr-text | False | 8/9 | 9/12 | — | 4.745 | 15.95 | ok |
| table-borderless | olmocr-text | False | 8/9 | 9/12 | — | 4.814 | 15.95 | ok |
| table-merged | olmocr-text | False | 8/9 | 9/12 | — | 4.892 | 15.96 | ok |
| links-and-outline | olmocr-text | unscored | — | — | — | 2.326 | 15.94 | ok |
| images-and-vectors | olmocr-text | unscored | — | — | — | 3.044 | 15.89 | ok |
| image-only | olmocr-text | unscored | — | — | — | 1.926 | 15.84 | ok |
| table-borderless-aligned | olmocr-text | True | 8/8 | 10/10 | — | 4.781 | 15.95 | ok |
| rotated-columns | olmocr-text | True | — | — | — | 9.365 | 17.34 | ok |
| footnotes-and-page-furniture | olmocr-text | True | — | — | — | 2.747 | 16.02 | ok |
| rtl-visual-glyph-order | olmocr-text | unscored | — | — | — | 2.299 | 15.87 | ok |
| tagged-reading-order | olmocr-text | unscored | — | — | — | 2.257 | 15.91 | ok |
| corpus-usrguide | olmocr-text | unscored | — | — | — | 29.877 | 21.75 | ok |
| corpus-senate-expenditures | olmocr-text | unscored | — | — | — | 0.782 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 2.26 GiB. GPU 0 has a total capacity of 23.56 GiB of which 1.66 GiB is free. Process |
| corpus-nics-background-checks-2015-11 | olmocr-text | unscored | — | — | — | 1.959 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 4.09 GiB. GPU 0 has a total capacity of 23.56 GiB of which 1.25 GiB is free. Process |
| corpus-pdfium-type3 | olmocr-text | unscored | — | — | — | 4.923 | 15.82 | ok |
| corpus-f1040 | olmocr-text | unscored | — | — | — | 2.424 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 3.04 GiB. GPU 0 has a total capacity of 23.56 GiB of which 1.26 GiB is free. Process |
| omml-equations | olmocr-text | unscored | — | — | — | 4.819 | 16.33 | ok |
| table-borderless-rotate-90 | olmocr-text | False | 0/9 | 9/12 | — | 5.735 | 15.95 | ok |
| table-borderless-rotate-180 | olmocr-text | False | 0/9 | 9/12 | — | 5.519 | 15.95 | ok |
| table-borderless-rotate-270 | olmocr-text | False | 8/9 | 9/12 | — | 4.932 | 15.95 | ok |
| table-borderless-scanned | olmocr-text | True | 9/9 | 12/12 | — | 4.916 | 15.84 | ok |
| table-wrapped-records | olmocr-text | True | 12/12 | 17/17 | — | 6.426 | 16.05 | ok |
| text-structure-and-literals | olmocr-patch | unscored | — | — | — | 1.534 | — | AttributeError: 'list' object has no attribute 'get' |
| positioned-math | olmocr-patch | unscored | — | — | — | 1.191 | — | AttributeError: 'list' object has no attribute 'get' |
| math-actualtext | olmocr-patch | unscored | — | — | — | 0.997 | — | AttributeError: 'list' object has no attribute 'get' |
| accessible-actualtext | olmocr-patch | unscored | — | — | — | 1.010 | — | AttributeError: 'list' object has no attribute 'get' |
| two-column-order | olmocr-patch | unscored | — | — | — | 8.557 | — | AttributeError: 'list' object has no attribute 'get' |
| unicode-cmap-and-emoji | olmocr-patch | unscored | — | — | — | 1.150 | — | AttributeError: 'list' object has no attribute 'get' |
| table-bordered | olmocr-patch | unscored | — | — | — | 2.638 | — | AttributeError: 'list' object has no attribute 'get' |
| table-borderless | olmocr-patch | unscored | — | — | — | 1.217 | — | AttributeError: 'list' object has no attribute 'get' |
| table-merged | olmocr-patch | unscored | — | — | — | 2.666 | — | AttributeError: 'list' object has no attribute 'get' |
| links-and-outline | olmocr-patch | unscored | — | — | — | 1.230 | — | AttributeError: 'list' object has no attribute 'get' |
| images-and-vectors | olmocr-patch | unscored | — | — | — | 1.091 | — | AttributeError: 'list' object has no attribute 'get' |
| image-only | olmocr-patch | unscored | — | — | — | 1.027 | — | AttributeError: 'list' object has no attribute 'get' |
| table-borderless-aligned | olmocr-patch | unscored | — | — | — | 2.650 | — | AttributeError: 'list' object has no attribute 'get' |
| rotated-columns | olmocr-patch | unscored | — | — | — | 6.242 | — | AttributeError: 'list' object has no attribute 'get' |
| footnotes-and-page-furniture | olmocr-patch | unscored | — | — | — | 1.354 | — | AttributeError: 'list' object has no attribute 'get' |
| rtl-visual-glyph-order | olmocr-patch | unscored | — | — | — | 1.027 | — | AttributeError: 'list' object has no attribute 'get' |
| tagged-reading-order | olmocr-patch | unscored | — | — | — | 1.173 | — | AttributeError: 'list' object has no attribute 'get' |
| corpus-usrguide | olmocr-patch | unscored | — | — | — | 9.892 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 1.18 GiB. GPU 0 has a total capacity of 23.56 GiB of which 490.19 MiB is free. Proce |
| corpus-senate-expenditures | olmocr-patch | unscored | — | — | — | 1.655 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 2.26 GiB. GPU 0 has a total capacity of 23.56 GiB of which 2.16 GiB is free. Process |
| corpus-nics-background-checks-2015-11 | olmocr-patch | unscored | — | — | — | 3.184 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 4.09 GiB. GPU 0 has a total capacity of 23.56 GiB of which 1.54 GiB is free. Process |
| corpus-pdfium-type3 | olmocr-patch | unscored | — | — | — | 1.059 | — | AttributeError: 'list' object has no attribute 'get' |
| corpus-f1040 | olmocr-patch | unscored | — | — | — | 2.090 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 3.04 GiB. GPU 0 has a total capacity of 23.56 GiB of which 1.54 GiB is free. Process |
| omml-equations | olmocr-patch | unscored | — | — | — | 1.934 | — | AttributeError: 'list' object has no attribute 'get' |
| table-borderless-rotate-90 | olmocr-patch | unscored | — | — | — | 1.319 | — | AttributeError: 'list' object has no attribute 'get' |
| table-borderless-rotate-180 | olmocr-patch | unscored | — | — | — | 1.344 | — | AttributeError: 'list' object has no attribute 'get' |
| table-borderless-rotate-270 | olmocr-patch | unscored | — | — | — | 3.843 | — | AttributeError: 'list' object has no attribute 'get' |
| table-borderless-scanned | olmocr-patch | unscored | — | — | — | 1.291 | — | JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| table-wrapped-records | olmocr-patch | unscored | — | — | — | 1.358 | — | AttributeError: 'list' object has no attribute 'get' |
| text-structure-and-literals | geometry | True | — | — | — | 0.000 | — | ok |
| positioned-math | geometry | True | — | — | — | 0.000 | — | ok |
| math-actualtext | geometry | True | — | — | — | 0.000 | — | ok |
| accessible-actualtext | geometry | unscored | — | — | — | 0.000 | — | ok |
| two-column-order | geometry | False | — | — | — | 0.000 | — | ok |
| unicode-cmap-and-emoji | geometry | unscored | — | — | — | 0.000 | — | ok |
| table-bordered | geometry | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless | geometry | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-merged | geometry | False | 8/9 | 9/12 | — | 0.000 | — | ok |
| links-and-outline | geometry | unscored | — | — | — | 0.000 | — | ok |
| images-and-vectors | geometry | unscored | — | — | — | 0.000 | — | ok |
| image-only | geometry | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-aligned | geometry | True | 8/8 | 10/10 | — | 0.000 | — | ok |
| rotated-columns | geometry | False | — | — | — | 0.000 | — | ok |
| footnotes-and-page-furniture | geometry | True | — | — | — | 0.000 | — | ok |
| rtl-visual-glyph-order | geometry | unscored | — | — | — | 0.000 | — | ok |
| tagged-reading-order | geometry | unscored | — | — | — | 0.000 | — | ok |
| corpus-usrguide | geometry | unscored | — | — | — | 0.000 | — | ok |
| corpus-senate-expenditures | geometry | unscored | — | — | 6/23 | 0.001 | — | ok |
| corpus-nics-background-checks-2015-11 | geometry | unscored | — | — | 6/12 | 0.006 | — | ok |
| corpus-pdfium-type3 | geometry | unscored | — | — | — | 0.000 | — | ok |
| corpus-f1040 | geometry | unscored | — | — | — | 0.002 | — | ok |
| omml-equations | geometry | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-rotate-90 | geometry | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-rotate-180 | geometry | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-rotate-270 | geometry | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-scanned | geometry | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-wrapped-records | geometry | False | 0/12 | 0/17 | — | 0.000 | — | ok |
| text-structure-and-literals | geometry-bullets | True | — | — | — | 0.000 | — | ok |
| positioned-math | geometry-bullets | True | — | — | — | 0.000 | — | ok |
| math-actualtext | geometry-bullets | True | — | — | — | 0.000 | — | ok |
| accessible-actualtext | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| two-column-order | geometry-bullets | False | — | — | — | 0.000 | — | ok |
| unicode-cmap-and-emoji | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| table-bordered | geometry-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless | geometry-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-merged | geometry-bullets | False | 8/9 | 9/12 | — | 0.000 | — | ok |
| links-and-outline | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| images-and-vectors | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| image-only | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-aligned | geometry-bullets | True | 8/8 | 10/10 | — | 0.000 | — | ok |
| rotated-columns | geometry-bullets | False | — | — | — | 0.000 | — | ok |
| footnotes-and-page-furniture | geometry-bullets | True | — | — | — | 0.000 | — | ok |
| rtl-visual-glyph-order | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| tagged-reading-order | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| corpus-usrguide | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| corpus-senate-expenditures | geometry-bullets | unscored | — | — | 6/23 | 0.001 | — | ok |
| corpus-nics-background-checks-2015-11 | geometry-bullets | unscored | — | — | 6/12 | 0.006 | — | ok |
| corpus-pdfium-type3 | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| corpus-f1040 | geometry-bullets | unscored | — | — | — | 0.002 | — | ok |
| omml-equations | geometry-bullets | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-rotate-90 | geometry-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-rotate-180 | geometry-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-rotate-270 | geometry-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-scanned | geometry-bullets | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-wrapped-records | geometry-bullets | False | 0/12 | 0/17 | — | 0.000 | — | ok |
| text-structure-and-literals | geometry-wrapped | True | — | — | — | 0.000 | — | ok |
| positioned-math | geometry-wrapped | True | — | — | — | 0.000 | — | ok |
| math-actualtext | geometry-wrapped | True | — | — | — | 0.000 | — | ok |
| accessible-actualtext | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| two-column-order | geometry-wrapped | False | — | — | — | 0.000 | — | ok |
| unicode-cmap-and-emoji | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| table-bordered | geometry-wrapped | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless | geometry-wrapped | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-merged | geometry-wrapped | False | 8/9 | 9/12 | — | 0.000 | — | ok |
| links-and-outline | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| images-and-vectors | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| image-only | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-aligned | geometry-wrapped | True | 8/8 | 10/10 | — | 0.000 | — | ok |
| rotated-columns | geometry-wrapped | False | — | — | — | 0.000 | — | ok |
| footnotes-and-page-furniture | geometry-wrapped | True | — | — | — | 0.000 | — | ok |
| rtl-visual-glyph-order | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| tagged-reading-order | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| corpus-usrguide | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| corpus-senate-expenditures | geometry-wrapped | unscored | — | — | 23/23 | 0.001 | — | ok |
| corpus-nics-background-checks-2015-11 | geometry-wrapped | unscored | — | — | 6/12 | 0.006 | — | ok |
| corpus-pdfium-type3 | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| corpus-f1040 | geometry-wrapped | unscored | — | — | — | 0.002 | — | ok |
| omml-equations | geometry-wrapped | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-rotate-90 | geometry-wrapped | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-rotate-180 | geometry-wrapped | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-rotate-270 | geometry-wrapped | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-scanned | geometry-wrapped | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-wrapped-records | geometry-wrapped | True | 12/12 | 17/17 | — | 0.000 | — | ok |
| text-structure-and-literals | geometry-wrapped-bullets | True | — | — | — | 0.000 | — | ok |
| positioned-math | geometry-wrapped-bullets | True | — | — | — | 0.000 | — | ok |
| math-actualtext | geometry-wrapped-bullets | True | — | — | — | 0.000 | — | ok |
| accessible-actualtext | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| two-column-order | geometry-wrapped-bullets | False | — | — | — | 0.001 | — | ok |
| unicode-cmap-and-emoji | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| table-bordered | geometry-wrapped-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless | geometry-wrapped-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-merged | geometry-wrapped-bullets | False | 8/9 | 9/12 | — | 0.000 | — | ok |
| links-and-outline | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| images-and-vectors | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| image-only | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-aligned | geometry-wrapped-bullets | True | 8/8 | 10/10 | — | 0.000 | — | ok |
| rotated-columns | geometry-wrapped-bullets | False | — | — | — | 0.000 | — | ok |
| footnotes-and-page-furniture | geometry-wrapped-bullets | True | — | — | — | 0.000 | — | ok |
| rtl-visual-glyph-order | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| tagged-reading-order | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| corpus-usrguide | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| corpus-senate-expenditures | geometry-wrapped-bullets | unscored | — | — | 23/23 | 0.001 | — | ok |
| corpus-nics-background-checks-2015-11 | geometry-wrapped-bullets | unscored | — | — | 6/12 | 0.006 | — | ok |
| corpus-pdfium-type3 | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| corpus-f1040 | geometry-wrapped-bullets | unscored | — | — | — | 0.002 | — | ok |
| omml-equations | geometry-wrapped-bullets | unscored | — | — | — | 0.000 | — | ok |
| table-borderless-rotate-90 | geometry-wrapped-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-rotate-180 | geometry-wrapped-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-rotate-270 | geometry-wrapped-bullets | True | 9/9 | 12/12 | — | 0.000 | — | ok |
| table-borderless-scanned | geometry-wrapped-bullets | False | 0/9 | 0/12 | — | 0.000 | — | ok |
| table-wrapped-records | geometry-wrapped-bullets | True | 12/12 | 17/17 | — | 0.000 | — | ok |
| text-structure-and-literals | yolo-normalized-geometry-wrapped | True | — | — | — | 2.125 | — | ok |
| positioned-math | yolo-normalized-geometry-wrapped | True | — | — | — | 0.041 | — | ok |
| math-actualtext | yolo-normalized-geometry-wrapped | True | — | — | — | 0.041 | — | ok |
| accessible-actualtext | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.039 | — | ok |
| two-column-order | yolo-normalized-geometry-wrapped | True | — | — | — | 0.043 | — | ok |
| unicode-cmap-and-emoji | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.091 | — | ok |
| table-bordered | yolo-normalized-geometry-wrapped | True | 9/9 | 12/12 | — | 0.041 | — | ok |
| table-borderless | yolo-normalized-geometry-wrapped | True | 9/9 | 12/12 | — | 0.041 | — | ok |
| table-merged | yolo-normalized-geometry-wrapped | False | 8/9 | 9/12 | — | 0.041 | — | ok |
| links-and-outline | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.042 | — | ok |
| images-and-vectors | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.040 | — | ok |
| image-only | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.039 | — | ok |
| table-borderless-aligned | yolo-normalized-geometry-wrapped | True | 8/8 | 10/10 | — | 0.041 | — | ok |
| rotated-columns | yolo-normalized-geometry-wrapped | True | — | — | — | 0.044 | — | ok |
| footnotes-and-page-furniture | yolo-normalized-geometry-wrapped | True | — | — | — | 0.040 | — | ok |
| rtl-visual-glyph-order | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.035 | — | ok |
| tagged-reading-order | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.039 | — | ok |
| corpus-usrguide | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.045 | — | ok |
| corpus-senate-expenditures | yolo-normalized-geometry-wrapped | unscored | — | — | 23/23 | 0.107 | — | ok |
| corpus-nics-background-checks-2015-11 | yolo-normalized-geometry-wrapped | unscored | — | — | 6/12 | 0.105 | — | ok |
| corpus-pdfium-type3 | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.114 | — | ok |
| corpus-f1040 | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.056 | — | ok |
| omml-equations | yolo-normalized-geometry-wrapped | unscored | — | — | — | 0.040 | — | ok |
| table-borderless-rotate-90 | yolo-normalized-geometry-wrapped | True | 9/9 | 12/12 | — | 0.042 | — | ok |
| table-borderless-rotate-180 | yolo-normalized-geometry-wrapped | True | 9/9 | 12/12 | — | 0.040 | — | ok |
| table-borderless-rotate-270 | yolo-normalized-geometry-wrapped | True | 9/9 | 12/12 | — | 0.040 | — | ok |
| table-borderless-scanned | yolo-normalized-geometry-wrapped | False | 0/9 | 0/12 | — | 0.039 | — | ok |
| table-wrapped-records | yolo-normalized-geometry-wrapped | True | 12/12 | 17/17 | — | 0.040 | — | ok |
| text-structure-and-literals | qwen-image | True | — | — | — | 3.490 | 7.33 | ok |
| positioned-math | qwen-image | True | — | — | — | 1.401 | 7.33 | ok |
| math-actualtext | qwen-image | True | — | — | — | 1.400 | 7.33 | ok |
| accessible-actualtext | qwen-image | unscored | — | — | — | 1.306 | 7.33 | ok |
| two-column-order | qwen-image | True | — | — | — | 9.615 | 7.33 | ok |
| unicode-cmap-and-emoji | qwen-image | unscored | — | — | — | 18.956 | 7.29 | ok |
| table-bordered | qwen-image | False | 0/9 | 0/12 | — | 2.049 | 7.33 | ok |
| table-borderless | qwen-image | False | 0/9 | 0/12 | — | 3.886 | 7.33 | ok |
| table-merged | qwen-image | False | 0/9 | 0/12 | — | 1.831 | 7.33 | ok |
| links-and-outline | qwen-image | unscored | — | — | — | 1.296 | 7.33 | ok |
| images-and-vectors | qwen-image | unscored | — | — | — | 34.456 | 7.33 | ok |
| image-only | qwen-image | unscored | — | — | — | 1.746 | 7.33 | ok |
| table-borderless-aligned | qwen-image | False | 0/8 | 0/10 | — | 4.104 | 7.33 | ok |
| rotated-columns | qwen-image | True | — | — | — | 9.292 | 7.33 | ok |
| footnotes-and-page-furniture | qwen-image | True | — | — | — | 3.707 | 7.33 | ok |
| rtl-visual-glyph-order | qwen-image | unscored | — | — | — | 16.333 | 7.29 | ok |
| tagged-reading-order | qwen-image | unscored | — | — | — | 1.923 | 7.33 | ok |
| corpus-usrguide | qwen-image | unscored | — | — | — | 13.389 | 7.29 | ok |
| corpus-senate-expenditures | qwen-image | unscored | — | — | 0/23 | 101.120 | 7.33 | ok |
| corpus-nics-background-checks-2015-11 | qwen-image | unscored | — | — | 0/12 | 119.102 | 7.26 | truncated |
| corpus-pdfium-type3 | qwen-image | unscored | — | — | — | 1.330 | 7.31 | ok |
| corpus-f1040 | qwen-image | unscored | — | — | — | 86.313 | 7.33 | ok |
| omml-equations | qwen-image | unscored | — | — | — | 3.992 | 7.33 | ok |
| table-borderless-rotate-90 | qwen-image | False | 0/9 | 0/12 | — | 4.391 | 7.33 | ok |
| table-borderless-rotate-180 | qwen-image | False | 0/9 | 0/12 | — | 3.791 | 7.33 | ok |
| table-borderless-rotate-270 | qwen-image | False | 0/9 | 0/12 | — | 4.081 | 7.33 | ok |
| table-borderless-scanned | qwen-image | False | 0/9 | 0/12 | — | 3.981 | 7.33 | ok |
| table-wrapped-records | qwen-image | False | 0/12 | 0/17 | — | 5.573 | 7.33 | ok |
| text-structure-and-literals | qwen-text | True | — | — | — | 3.149 | 7.53 | ok |
| positioned-math | qwen-text | True | — | — | — | 1.606 | 7.33 | ok |
| math-actualtext | qwen-text | True | — | — | — | 0.897 | 7.33 | ok |
| accessible-actualtext | qwen-text | unscored | — | — | — | 0.927 | 7.33 | ok |
| two-column-order | qwen-text | True | — | — | — | 11.034 | 8.14 | ok |
| unicode-cmap-and-emoji | qwen-text | unscored | — | — | — | 2.351 | 7.30 | ok |
| table-bordered | qwen-text | False | 0/9 | 0/12 | — | 1.922 | 7.33 | ok |
| table-borderless | qwen-text | False | 0/9 | 0/12 | — | 1.922 | 7.33 | ok |
| table-merged | qwen-text | False | 0/9 | 0/12 | — | 1.890 | 7.33 | ok |
| links-and-outline | qwen-text | unscored | — | — | — | 1.442 | 7.33 | ok |
| images-and-vectors | qwen-text | unscored | — | — | — | 2.554 | 7.33 | ok |
| image-only | qwen-text | unscored | — | — | — | 1.409 | 7.33 | ok |
| table-borderless-aligned | qwen-text | False | 0/8 | 0/10 | — | 1.809 | 7.33 | ok |
| rotated-columns | qwen-text | True | — | — | — | 11.139 | 8.14 | ok |
| footnotes-and-page-furniture | qwen-text | True | — | — | — | 1.681 | 7.35 | ok |
| rtl-visual-glyph-order | qwen-text | unscored | — | — | — | 1.207 | 7.30 | ok |
| tagged-reading-order | qwen-text | unscored | — | — | — | 1.027 | 7.33 | ok |
| corpus-usrguide | qwen-text | unscored | — | — | — | 14.689 | 10.79 | ok |
| corpus-senate-expenditures | qwen-text | unscored | — | — | 0/23 | 146.628 | 14.23 | truncated |
| corpus-nics-background-checks-2015-11 | qwen-text | unscored | — | — | — | 27.740 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 2.37 GiB. GPU 0 has a total capacity of 23.56 GiB of which 1.45 GiB is free. Process |
| corpus-pdfium-type3 | qwen-text | unscored | — | — | — | 55.771 | 7.31 | ok |
| corpus-f1040 | qwen-text | unscored | — | — | — | 49.757 | 16.73 | ok |
| omml-equations | qwen-text | unscored | — | — | — | 3.009 | 7.53 | ok |
| table-borderless-rotate-90 | qwen-text | False | 0/9 | 0/12 | — | 120.836 | 7.33 | truncated |
| table-borderless-rotate-180 | qwen-text | False | 0/9 | 0/12 | — | 2.284 | 7.33 | ok |
| table-borderless-rotate-270 | qwen-text | False | 0/9 | 0/12 | — | 120.879 | 7.33 | truncated |
| table-borderless-scanned | qwen-text | False | 0/9 | 0/12 | — | 4.069 | 7.33 | ok |
| table-wrapped-records | qwen-text | False | 0/12 | 0/17 | — | 5.307 | 7.36 | ok |
| text-structure-and-literals | qwen-patch | False | — | — | — | 11.073 | 7.54 | ok |
| positioned-math | qwen-patch | unscored | — | — | — | 1.093 | — | TypeError: patch root must be a JSON object with a tables list |
| math-actualtext | qwen-patch | unscored | — | — | — | 2.224 | — | TypeError: patch root must be a JSON object with a tables list |
| accessible-actualtext | qwen-patch | unscored | — | — | — | 2.116 | — | TypeError: patch root must be a JSON object with a tables list |
| two-column-order | qwen-patch | unscored | — | — | — | 27.512 | — | TypeError: each cell must contain a list of source word IDs |
| unicode-cmap-and-emoji | qwen-patch | unscored | — | — | — | 2.404 | — | TypeError: each cell must contain a list of source word IDs |
| table-bordered | qwen-patch | unscored | — | — | — | 2.928 | — | TypeError: patch root must be a JSON object with a tables list |
| table-borderless | qwen-patch | unscored | — | — | — | 2.127 | — | TypeError: patch root must be a JSON object with a tables list |
| table-merged | qwen-patch | unscored | — | — | — | 2.624 | — | TypeError: patch root must be a JSON object with a tables list |
| links-and-outline | qwen-patch | unscored | — | — | — | 3.055 | — | TypeError: patch root must be a JSON object with a tables list |
| images-and-vectors | qwen-patch | unscored | — | — | — | 1.096 | — | TypeError: patch root must be a JSON object with a tables list |
| image-only | qwen-patch | unscored | — | — | — | 4.138 | — | JSONDecodeError: Expecting value: line 5 column 1 (char 182) |
| table-borderless-aligned | qwen-patch | unscored | — | — | — | 1.115 | — | TypeError: patch root must be a JSON object with a tables list |
| rotated-columns | qwen-patch | unscored | — | — | — | 7.731 | — | TypeError: each cell must contain a list of source word IDs |
| footnotes-and-page-furniture | qwen-patch | False | — | — | — | 2.632 | 7.36 | ok |
| rtl-visual-glyph-order | qwen-patch | unscored | — | — | — | 2.274 | — | TypeError: each cell must contain a list of source word IDs |
| tagged-reading-order | qwen-patch | unscored | — | — | — | 2.633 | — | TypeError: patch root must be a JSON object with a tables list |
| corpus-usrguide | qwen-patch | unscored | — | — | — | 128.701 | — | JSONDecodeError: Unterminated string starting at: line 251 column 10 (char 7811) |
| corpus-senate-expenditures | qwen-patch | unscored | — | — | — | 149.901 | — | JSONDecodeError: Unterminated string starting at: line 973 column 15 (char 15909) |
| corpus-nics-background-checks-2015-11 | qwen-patch | unscored | — | — | — | 20.364 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 2.38 GiB. GPU 0 has a total capacity of 23.56 GiB of which 1.82 GiB is free. Process |
| corpus-pdfium-type3 | qwen-patch | unscored | — | — | — | 56.947 | — | TypeError: each cell must contain a list of source word IDs |
| corpus-f1040 | qwen-patch | unscored | — | — | — | 48.958 | — | JSONDecodeError: Expecting value: line 1 column 1 (char 0) |
| omml-equations | qwen-patch | unscored | — | — | — | 8.790 | 7.54 | ok |
| table-borderless-rotate-90 | qwen-patch | unscored | — | — | — | 3.118 | — | TypeError: patch root must be a JSON object with a tables list |
| table-borderless-rotate-180 | qwen-patch | unscored | — | — | — | 3.018 | — | TypeError: patch root must be a JSON object with a tables list |
| table-borderless-rotate-270 | qwen-patch | unscored | — | — | — | 2.482 | — | TypeError: patch root must be a JSON object with a tables list |
| table-borderless-scanned | qwen-patch | unscored | — | — | — | 2.673 | — | TypeError: patch root must be a JSON object with a tables list |
| table-wrapped-records | qwen-patch | unscored | — | — | — | 3.238 | — | TypeError: patch root must be a JSON object with a tables list |
| text-structure-and-literals | repair-qwen-image | False | — | — | — | 0.010 | — | ok |
| positioned-math | repair-qwen-image | True | — | — | — | 0.010 | — | ok |
| math-actualtext | repair-qwen-image | False | — | — | — | 0.010 | — | ok |
| accessible-actualtext | repair-qwen-image | unscored | — | — | — | 0.009 | — | ok |
| two-column-order | repair-qwen-image | False | — | — | — | 0.010 | — | ok |
| unicode-cmap-and-emoji | repair-qwen-image | unscored | — | — | — | 0.010 | — | ok |
| table-bordered | repair-qwen-image | False | 2/9 | 4/12 | — | 0.011 | — | ok |
| table-borderless | repair-qwen-image | False | 5/9 | 7/12 | — | 0.010 | — | ok |
| table-merged | repair-qwen-image | False | 4/9 | 4/12 | — | 0.010 | — | ok |
| links-and-outline | repair-qwen-image | unscored | — | — | — | 0.011 | — | ok |
| images-and-vectors | repair-qwen-image | unscored | — | — | — | 0.014 | — | ok |
| image-only | repair-qwen-image | unscored | — | — | — | 0.010 | — | ok |
| table-borderless-aligned | repair-qwen-image | False | 0/8 | 10/10 | — | 0.010 | — | ok |
| rotated-columns | repair-qwen-image | False | — | — | — | 0.010 | — | ok |
| footnotes-and-page-furniture | repair-qwen-image | False | — | — | — | 0.010 | — | ok |
| rtl-visual-glyph-order | repair-qwen-image | unscored | — | — | — | 0.011 | — | ok |
| tagged-reading-order | repair-qwen-image | unscored | — | — | — | 0.011 | — | ok |
| corpus-usrguide | repair-qwen-image | unscored | — | — | — | 0.010 | — | ok |
| corpus-senate-expenditures | repair-qwen-image | unscored | — | — | 0/23 | 0.012 | — | ok |
| corpus-nics-background-checks-2015-11 | repair-qwen-image | unscored | — | — | 0/12 | 0.011 | — | ok |
| corpus-pdfium-type3 | repair-qwen-image | unscored | — | — | — | 0.010 | — | ok |
| corpus-f1040 | repair-qwen-image | unscored | — | — | — | 0.013 | — | ok |
| omml-equations | repair-qwen-image | unscored | — | — | — | 0.010 | — | ok |
| table-borderless-rotate-90 | repair-qwen-image | False | 0/9 | 4/12 | — | 0.014 | — | ok |
| table-borderless-rotate-180 | repair-qwen-image | False | 5/9 | 3/12 | — | 0.011 | — | ok |
| table-borderless-rotate-270 | repair-qwen-image | False | 0/9 | 0/12 | — | 0.011 | — | ok |
| table-borderless-scanned | repair-qwen-image | False | 5/9 | 7/12 | — | 0.010 | — | ok |
| table-wrapped-records | repair-qwen-image | False | 0/12 | 10/17 | — | 0.010 | — | ok |
| text-structure-and-literals | repair-qwen-text | False | — | — | — | 0.010 | — | ok |
| positioned-math | repair-qwen-text | True | — | — | — | 0.011 | — | ok |
| math-actualtext | repair-qwen-text | True | — | — | — | 0.010 | — | ok |
| accessible-actualtext | repair-qwen-text | unscored | — | — | — | 0.010 | — | ok |
| two-column-order | repair-qwen-text | False | — | — | — | 0.010 | — | ok |
| unicode-cmap-and-emoji | repair-qwen-text | unscored | — | — | — | 0.010 | — | ok |
| table-bordered | repair-qwen-text | False | 7/9 | 6/12 | — | 0.010 | — | ok |
| table-borderless | repair-qwen-text | False | 7/9 | 6/12 | — | 0.010 | — | ok |
| table-merged | repair-qwen-text | False | 4/9 | 4/12 | — | 0.010 | — | ok |
| links-and-outline | repair-qwen-text | unscored | — | — | — | 0.010 | — | ok |
| images-and-vectors | repair-qwen-text | unscored | — | — | — | 0.011 | — | ok |
| image-only | repair-qwen-text | unscored | — | — | — | 0.010 | — | ok |
| table-borderless-aligned | repair-qwen-text | True | 8/8 | 10/10 | — | 0.011 | — | ok |
| rotated-columns | repair-qwen-text | False | — | — | — | 0.011 | — | ok |
| footnotes-and-page-furniture | repair-qwen-text | True | — | — | — | 0.011 | — | ok |
| rtl-visual-glyph-order | repair-qwen-text | unscored | — | — | — | 0.011 | — | ok |
| tagged-reading-order | repair-qwen-text | unscored | — | — | — | 0.011 | — | ok |
| corpus-usrguide | repair-qwen-text | unscored | — | — | — | 0.013 | — | ok |
| corpus-senate-expenditures | repair-qwen-text | unscored | — | — | 0/23 | 0.012 | — | ok |
| corpus-nics-background-checks-2015-11 | repair-qwen-text | unscored | — | — | — | 0.011 | — | FileNotFoundError: [Errno 2] No such file or directory: '/home/dan/code/oss/pylopdf/bench/results/structure-artifacts/corpus-nics-background |
| corpus-pdfium-type3 | repair-qwen-text | unscored | — | — | — | 0.011 | — | ok |
| corpus-f1040 | repair-qwen-text | unscored | — | — | — | 0.010 | — | ok |
| omml-equations | repair-qwen-text | unscored | — | — | — | 0.011 | — | ok |
| table-borderless-rotate-90 | repair-qwen-text | False | 0/9 | 0/12 | — | 0.013 | — | ok |
| table-borderless-rotate-180 | repair-qwen-text | False | 6/9 | 4/12 | — | 0.011 | — | ok |
| table-borderless-rotate-270 | repair-qwen-text | False | 0/9 | 0/12 | — | 0.012 | — | ok |
| table-borderless-scanned | repair-qwen-text | False | 5/9 | 7/12 | — | 0.011 | — | ok |
| table-wrapped-records | repair-qwen-text | True | 12/12 | 17/17 | — | 0.011 | — | ok |
| text-structure-and-literals | retained-docling | True | — | — | — | 0.747 | — | ok |
| positioned-math | retained-docling | True | — | — | — | 0.814 | — | ok |
| math-actualtext | retained-docling | True | — | — | — | 0.854 | — | ok |
| accessible-actualtext | retained-docling | unscored | — | — | — | 0.734 | — | ok |
| two-column-order | retained-docling | False | — | — | — | 1.512 | — | ok |
| unicode-cmap-and-emoji | retained-docling | unscored | — | — | — | 0.749 | — | ok |
| table-bordered | retained-docling | True | 9/9 | 12/12 | — | 1.318 | — | ok |
| table-borderless | retained-docling | False | 0/9 | 0/12 | — | 0.801 | — | ok |
| table-merged | retained-docling | False | 1/9 | 3/12 | — | 1.292 | — | ok |
| links-and-outline | retained-docling | unscored | — | — | — | 0.005 | — | ValueError: retained model output requires identical single-page input |
| images-and-vectors | retained-docling | unscored | — | — | — | 0.748 | — | ok |
| image-only | retained-docling | unscored | — | — | — | 1.128 | — | ok |
| table-borderless-aligned | retained-docling | False | 0/8 | 0/10 | — | 0.809 | — | ok |
| rotated-columns | retained-docling | True | — | — | — | 0.760 | — | ok |
| footnotes-and-page-furniture | retained-docling | True | — | — | — | 0.870 | — | ok |
| rtl-visual-glyph-order | retained-docling | unscored | — | — | — | 0.768 | — | ok |
| tagged-reading-order | retained-docling | unscored | — | — | — | 0.952 | — | ok |
| corpus-usrguide | retained-docling | unscored | — | — | — | 0.996 | — | ok |
| corpus-senate-expenditures | retained-docling | unscored | — | — | 23/23 | 9.920 | — | ok |
| corpus-nics-background-checks-2015-11 | retained-docling | unscored | — | — | 0/12 | 36.632 | — | ok |
| corpus-pdfium-type3 | retained-docling | unscored | — | — | — | 0.786 | — | ok |
| corpus-f1040 | retained-docling | unscored | — | — | — | 1.620 | — | ok |
| omml-equations | retained-docling | unscored | — | — | — | 0.809 | — | ok |
| table-borderless-rotate-90 | retained-docling | unscored | — | — | — | 0.005 | — | StopIteration:  |
| table-borderless-rotate-180 | retained-docling | unscored | — | — | — | 0.008 | — | StopIteration:  |
| table-borderless-rotate-270 | retained-docling | unscored | — | — | — | 0.005 | — | StopIteration:  |
| table-borderless-scanned | retained-docling | unscored | — | — | — | 0.008 | — | StopIteration:  |
| table-wrapped-records | retained-docling | unscored | — | — | — | 0.008 | — | StopIteration:  |
| text-structure-and-literals | retained-docling-formulas | True | — | — | — | 0.780 | — | ok |
| positioned-math | retained-docling-formulas | True | — | — | — | 0.781 | — | ok |
| math-actualtext | retained-docling-formulas | True | — | — | — | 0.798 | — | ok |
| accessible-actualtext | retained-docling-formulas | unscored | — | — | — | 0.791 | — | ok |
| two-column-order | retained-docling-formulas | False | — | — | — | 1.462 | — | ok |
| unicode-cmap-and-emoji | retained-docling-formulas | unscored | — | — | — | 0.769 | — | ok |
| table-bordered | retained-docling-formulas | True | 9/9 | 12/12 | — | 1.389 | — | ok |
| table-borderless | retained-docling-formulas | False | 0/9 | 0/12 | — | 0.815 | — | ok |
| table-merged | retained-docling-formulas | False | 1/9 | 3/12 | — | 1.261 | — | ok |
| links-and-outline | retained-docling-formulas | unscored | — | — | — | 0.006 | — | ValueError: retained model output requires identical single-page input |
| images-and-vectors | retained-docling-formulas | unscored | — | — | — | 0.771 | — | ok |
| image-only | retained-docling-formulas | unscored | — | — | — | 1.171 | — | ok |
| table-borderless-aligned | retained-docling-formulas | False | 0/8 | 0/10 | — | 0.851 | — | ok |
| rotated-columns | retained-docling-formulas | True | — | — | — | 0.761 | — | ok |
| footnotes-and-page-furniture | retained-docling-formulas | True | — | — | — | 0.841 | — | ok |
| rtl-visual-glyph-order | retained-docling-formulas | unscored | — | — | — | 0.850 | — | ok |
| tagged-reading-order | retained-docling-formulas | unscored | — | — | — | 0.818 | — | ok |
| corpus-usrguide | retained-docling-formulas | unscored | — | — | — | 0.825 | — | ok |
| corpus-senate-expenditures | retained-docling-formulas | unscored | — | — | 23/23 | 9.847 | — | ok |
| corpus-nics-background-checks-2015-11 | retained-docling-formulas | unscored | — | — | 0/12 | 41.483 | — | ok |
| corpus-pdfium-type3 | retained-docling-formulas | unscored | — | — | — | 0.772 | — | ok |
| corpus-f1040 | retained-docling-formulas | unscored | — | — | — | 1.940 | — | ok |
| omml-equations | retained-docling-formulas | unscored | — | — | — | 0.759 | — | ok |
| table-borderless-rotate-90 | retained-docling-formulas | unscored | — | — | — | 0.005 | — | StopIteration:  |
| table-borderless-rotate-180 | retained-docling-formulas | unscored | — | — | — | 0.008 | — | StopIteration:  |
| table-borderless-rotate-270 | retained-docling-formulas | unscored | — | — | — | 0.011 | — | StopIteration:  |
| table-borderless-scanned | retained-docling-formulas | unscored | — | — | — | 0.005 | — | StopIteration:  |
| table-wrapped-records | retained-docling-formulas | unscored | — | — | — | 0.008 | — | StopIteration:  |
| text-structure-and-literals | retained-marker-fast | True | — | — | — | 0.262 | — | ok |
| positioned-math | retained-marker-fast | True | — | — | — | 0.241 | — | ok |
| math-actualtext | retained-marker-fast | True | — | — | — | 0.218 | — | ok |
| accessible-actualtext | retained-marker-fast | unscored | — | — | — | 0.248 | — | ok |
| two-column-order | retained-marker-fast | True | — | — | — | 0.223 | — | ok |
| unicode-cmap-and-emoji | retained-marker-fast | unscored | — | — | — | 1.131 | — | ok |
| table-bordered | retained-marker-fast | False | 7/9 | 6/12 | — | 1.189 | — | ok |
| table-borderless | retained-marker-fast | False | 7/9 | 6/12 | — | 0.355 | — | ok |
| table-merged | retained-marker-fast | False | 7/9 | 6/12 | — | 0.360 | — | ok |
| links-and-outline | retained-marker-fast | unscored | — | — | — | 0.008 | — | ValueError: retained model output requires identical single-page input |
| images-and-vectors | retained-marker-fast | unscored | — | — | — | 0.347 | — | ok |
| image-only | retained-marker-fast | unscored | — | — | — | 0.340 | — | ok |
| table-borderless-aligned | retained-marker-fast | True | 8/8 | 10/10 | — | 0.343 | — | ok |
| rotated-columns | retained-marker-fast | True | — | — | — | 0.319 | — | ok |
| footnotes-and-page-furniture | retained-marker-fast | True | — | — | — | 0.323 | — | ok |
| rtl-visual-glyph-order | retained-marker-fast | unscored | — | — | — | 0.345 | — | ok |
| tagged-reading-order | retained-marker-fast | unscored | — | — | — | 0.291 | — | ok |
| corpus-usrguide | retained-marker-fast | unscored | — | — | — | 0.492 | — | ok |
| corpus-senate-expenditures | retained-marker-fast | unscored | — | — | 0/23 | 0.868 | — | ok |
| corpus-nics-background-checks-2015-11 | retained-marker-fast | unscored | — | — | 12/12 | 0.894 | — | ok |
| corpus-pdfium-type3 | retained-marker-fast | unscored | — | — | — | 0.239 | — | ok |
| corpus-f1040 | retained-marker-fast | unscored | — | — | — | 0.689 | — | ok |
| omml-equations | retained-marker-fast | unscored | — | — | — | 0.320 | — | ok |
| table-borderless-rotate-90 | retained-marker-fast | unscored | — | — | — | 0.007 | — | StopIteration:  |
| table-borderless-rotate-180 | retained-marker-fast | unscored | — | — | — | 0.006 | — | StopIteration:  |
| table-borderless-rotate-270 | retained-marker-fast | unscored | — | — | — | 0.007 | — | StopIteration:  |
| table-borderless-scanned | retained-marker-fast | unscored | — | — | — | 0.007 | — | StopIteration:  |
| table-wrapped-records | retained-marker-fast | unscored | — | — | — | 0.006 | — | StopIteration:  |
| text-structure-and-literals | ocr-geometry-wrapped | True | — | — | — | 0.034 | — | ok |
| positioned-math | ocr-geometry-wrapped | True | — | — | — | 0.025 | — | ok |
| math-actualtext | ocr-geometry-wrapped | True | — | — | — | 0.027 | — | ok |
| accessible-actualtext | ocr-geometry-wrapped | unscored | — | — | — | 0.025 | — | ok |
| two-column-order | ocr-geometry-wrapped | False | — | — | — | 0.029 | — | ok |
| unicode-cmap-and-emoji | ocr-geometry-wrapped | unscored | — | — | — | 0.011 | — | ok |
| table-bordered | ocr-geometry-wrapped | True | 9/9 | 12/12 | — | 0.010 | — | ok |
| table-borderless | ocr-geometry-wrapped | True | 9/9 | 12/12 | — | 0.010 | — | ok |
| table-merged | ocr-geometry-wrapped | False | 8/9 | 9/12 | — | 0.009 | — | ok |
| links-and-outline | ocr-geometry-wrapped | unscored | — | — | — | 0.009 | — | ok |
| images-and-vectors | ocr-geometry-wrapped | unscored | — | — | — | 0.010 | — | ok |
| image-only | ocr-geometry-wrapped | unscored | — | — | — | 2.254 | — | ok |
| table-borderless-aligned | ocr-geometry-wrapped | True | 8/8 | 10/10 | — | 0.009 | — | ok |
| rotated-columns | ocr-geometry-wrapped | True | — | — | — | 0.012 | — | ok |
| footnotes-and-page-furniture | ocr-geometry-wrapped | True | — | — | — | 0.010 | — | ok |
| rtl-visual-glyph-order | ocr-geometry-wrapped | unscored | — | — | — | 0.010 | — | ok |
| tagged-reading-order | ocr-geometry-wrapped | unscored | — | — | — | 0.009 | — | ok |
| corpus-usrguide | ocr-geometry-wrapped | unscored | — | — | — | 0.017 | — | ok |
| corpus-senate-expenditures | ocr-geometry-wrapped | unscored | — | — | 23/23 | 0.018 | — | ok |
| corpus-nics-background-checks-2015-11 | ocr-geometry-wrapped | unscored | — | — | 6/12 | 0.028 | — | ok |
| corpus-pdfium-type3 | ocr-geometry-wrapped | unscored | — | — | — | 0.111 | — | ok |
| corpus-f1040 | ocr-geometry-wrapped | unscored | — | — | — | 0.026 | — | ok |
| omml-equations | ocr-geometry-wrapped | unscored | — | — | — | 0.010 | — | ok |
| table-borderless-scanned | ocr-geometry-wrapped | True | 9/9 | 12/12 | — | 2.200 | — | ok |
| table-wrapped-records | ocr-geometry-wrapped | True | 12/12 | 17/17 | — | 0.011 | — | ok |
| table-borderless-rotate-90 | ocr-geometry-wrapped | True | 9/9 | 12/12 | — | 0.034 | — | ok |
| table-borderless-rotate-180 | ocr-geometry-wrapped | True | 9/9 | 12/12 | — | 0.028 | — | ok |
| table-borderless-rotate-270 | ocr-geometry-wrapped | True | 9/9 | 12/12 | — | 0.026 | — | ok |
| table-borderless-rotate-90 | olmocr-normalized | True | 9/9 | 12/12 | — | 4.462 | 15.84 | ok |
| table-borderless-rotate-180 | olmocr-normalized | True | 9/9 | 12/12 | — | 4.221 | 15.84 | ok |
| table-borderless-rotate-270 | olmocr-normalized | True | 9/9 | 12/12 | — | 4.435 | 15.84 | ok |
| two-column-order | olmocr-compact-text | True | — | — | — | 6.605 | 16.53 | ok |
| table-bordered | olmocr-compact-text | False | 8/9 | 9/12 | — | 4.595 | 15.90 | ok |
| table-borderless | olmocr-compact-text | False | 8/9 | 9/12 | — | 4.660 | 15.90 | ok |
| table-merged | olmocr-compact-text | False | 8/9 | 9/12 | — | 4.688 | 15.90 | ok |
| corpus-senate-expenditures | olmocr-compact-text | unscored | — | — | 0/23 | 31.060 | 20.05 | ok |
| corpus-nics-background-checks-2015-11 | olmocr-compact-text | unscored | — | — | — | 0.553 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 1.86 GiB. GPU 0 has a total capacity of 23.56 GiB of which 500.06 MiB is free. Proce |
| table-wrapped-records | olmocr-compact-text | True | 12/12 | 17/17 | — | 7.304 | 15.95 | ok |
| corpus-senate-expenditures | olmocr-4bit-text | unscored | — | — | 0/23 | 44.975 | 17.57 | ok |
| corpus-nics-background-checks-2015-11 | olmocr-4bit-text | unscored | — | — | — | 0.841 | — | OutOfMemoryError: CUDA out of memory. Tried to allocate 4.09 GiB. GPU 0 has a total capacity of 23.56 GiB of which 2.34 GiB is free. Process |
| two-column-order | olmocr-yolo-crop | True | — | — | — | 5.706 | 15.84 | ok |
| table-bordered | olmocr-yolo-crop | True | 9/9 | 12/12 | — | 3.898 | 15.60 | ok |
| table-borderless | olmocr-yolo-crop | True | 9/9 | 12/12 | — | 3.942 | 15.58 | ok |
| table-merged | olmocr-yolo-crop | True | 9/9 | 12/12 | — | 3.965 | 15.60 | ok |
| corpus-senate-expenditures | olmocr-yolo-crop | unscored | — | — | 11/23 | 106.405 | 15.78 | ok |
| corpus-nics-background-checks-2015-11 | olmocr-yolo-crop | unscored | — | — | 0/12 | 128.006 | 15.76 | truncated |
| table-wrapped-records | olmocr-yolo-crop | True | 12/12 | 17/17 | — | 6.113 | 15.64 | ok |
| two-column-order | olmocr-geometry-crop | True | — | — | — | 5.122 | 15.64 | ok |
| table-bordered | olmocr-geometry-crop | True | 9/9 | 12/12 | — | 4.292 | 15.58 | ok |
| table-borderless | olmocr-geometry-crop | True | 9/9 | 12/12 | — | 4.103 | 15.58 | ok |
| table-merged | olmocr-geometry-crop | False | 8/9 | 9/12 | — | 4.074 | 15.58 | ok |
| table-wrapped-records | olmocr-geometry-crop | True | 12/12 | 17/17 | — | 9.012 | 15.64 | ok |
| corpus-senate-expenditures | olmocr-row-crop | unscored | — | — | 0/23 | 122.965 | 15.54 | ok |
| corpus-nics-background-checks-2015-11 | olmocr-row-crop | unscored | — | — | 7/12 | 1046.099 | 15.69 | truncated |
| two-column-order | qwen-compact-text | True | — | — | — | 6.219 | 7.65 | ok |
| table-bordered | qwen-compact-text | False | 0/9 | 0/12 | — | 1.888 | 7.33 | ok |
| table-borderless | qwen-compact-text | False | 0/9 | 0/12 | — | 1.885 | 7.33 | ok |
| table-merged | qwen-compact-text | False | 0/9 | 0/12 | — | 1.910 | 7.33 | ok |
| corpus-senate-expenditures | qwen-compact-text | unscored | — | — | 0/23 | 94.421 | 9.76 | ok |
| corpus-nics-background-checks-2015-11 | qwen-compact-text | unscored | — | — | 0/12 | 21.152 | 12.96 | ok |
| table-wrapped-records | qwen-compact-text | False | 0/12 | 0/17 | — | 2.382 | 7.33 | ok |
| two-column-order | qwen-compact-patch | unscored | — | — | — | 3.841 | — | TypeError: each cell must contain a list of source word IDs |
| table-bordered | qwen-compact-patch | unscored | — | — | — | 2.429 | — | TypeError: patch root must be a JSON object with a tables list |
| table-borderless | qwen-compact-patch | unscored | — | — | — | 3.668 | — | TypeError: patch root must be a JSON object with a tables list |
| table-merged | qwen-compact-patch | unscored | — | — | — | 2.540 | — | TypeError: patch root must be a JSON object with a tables list |
| corpus-senate-expenditures | qwen-compact-patch | unscored | — | — | — | 83.711 | — | JSONDecodeError: Expecting property name enclosed in double quotes: line 165 column 17 (char 4684) |
| text-structure-and-literals | native-bullets | True | — | — | — | 0.015 | — | ok |
| positioned-math | native-bullets | True | — | — | — | 0.014 | — | ok |
| math-actualtext | native-bullets | True | — | — | — | 0.013 | — | ok |
| accessible-actualtext | native-bullets | unscored | — | — | — | 0.013 | — | ok |
| two-column-order | native-bullets | True | — | — | — | 0.010 | — | ok |
| unicode-cmap-and-emoji | native-bullets | unscored | — | — | — | 0.008 | — | ok |
| table-bordered | native-bullets | True | 9/9 | 12/12 | — | 0.009 | — | ok |
| table-borderless | native-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-merged | native-bullets | False | 8/9 | 9/12 | — | 0.009 | — | ok |
| links-and-outline | native-bullets | unscored | — | — | — | 0.008 | — | ok |
| images-and-vectors | native-bullets | unscored | — | — | — | 0.008 | — | ok |
| image-only | native-bullets | unscored | — | — | — | 0.008 | — | ok |
| table-borderless-aligned | native-bullets | False | 0/8 | 0/10 | — | 0.009 | — | ok |
| rotated-columns | native-bullets | True | — | — | — | 0.010 | — | ok |
| footnotes-and-page-furniture | native-bullets | True | — | — | — | 0.008 | — | ok |
| rtl-visual-glyph-order | native-bullets | unscored | — | — | — | 0.009 | — | ok |
| tagged-reading-order | native-bullets | unscored | — | — | — | 0.008 | — | ok |
| corpus-usrguide | native-bullets | unscored | — | — | — | 0.014 | — | ok |
| corpus-senate-expenditures | native-bullets | unscored | — | — | 0/23 | 0.013 | — | ok |
| corpus-nics-background-checks-2015-11 | native-bullets | unscored | — | — | 12/12 | 0.038 | — | ok |
| corpus-pdfium-type3 | native-bullets | unscored | — | — | — | 0.008 | — | ok |
| corpus-f1040 | native-bullets | unscored | — | — | — | 0.019 | — | ok |
| omml-equations | native-bullets | unscored | — | — | — | 0.009 | — | ok |
| table-borderless-rotate-90 | native-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-borderless-rotate-180 | native-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-borderless-rotate-270 | native-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-borderless-scanned | native-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-wrapped-records | native-bullets | False | 0/12 | 0/17 | — | 0.008 | — | ok |
| text-structure-and-literals | native-header-bullets | True | — | — | — | 0.008 | — | ok |
| positioned-math | native-header-bullets | True | — | — | — | 0.008 | — | ok |
| math-actualtext | native-header-bullets | True | — | — | — | 0.008 | — | ok |
| accessible-actualtext | native-header-bullets | unscored | — | — | — | 0.008 | — | ok |
| two-column-order | native-header-bullets | True | — | — | — | 0.010 | — | ok |
| unicode-cmap-and-emoji | native-header-bullets | unscored | — | — | — | 0.008 | — | ok |
| table-bordered | native-header-bullets | True | 9/9 | 12/12 | — | 0.009 | — | ok |
| table-borderless | native-header-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-merged | native-header-bullets | False | 8/9 | 9/12 | — | 0.010 | — | ok |
| links-and-outline | native-header-bullets | unscored | — | — | — | 0.008 | — | ok |
| images-and-vectors | native-header-bullets | unscored | — | — | — | 0.008 | — | ok |
| image-only | native-header-bullets | unscored | — | — | — | 0.008 | — | ok |
| table-borderless-aligned | native-header-bullets | False | 0/8 | 0/10 | — | 0.008 | — | ok |
| rotated-columns | native-header-bullets | True | — | — | — | 0.009 | — | ok |
| footnotes-and-page-furniture | native-header-bullets | True | — | — | — | 0.008 | — | ok |
| rtl-visual-glyph-order | native-header-bullets | unscored | — | — | — | 0.008 | — | ok |
| tagged-reading-order | native-header-bullets | unscored | — | — | — | 0.008 | — | ok |
| corpus-usrguide | native-header-bullets | unscored | — | — | — | 0.013 | — | ok |
| corpus-senate-expenditures | native-header-bullets | unscored | — | — | 23/23 | 0.016 | — | ok |
| corpus-nics-background-checks-2015-11 | native-header-bullets | unscored | — | — | 12/12 | 0.037 | — | ok |
| corpus-pdfium-type3 | native-header-bullets | unscored | — | — | — | 0.008 | — | ok |
| corpus-f1040 | native-header-bullets | unscored | — | — | — | 0.021 | — | ok |
| omml-equations | native-header-bullets | unscored | — | — | — | 0.009 | — | ok |
| table-borderless-rotate-90 | native-header-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-borderless-rotate-180 | native-header-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-borderless-rotate-270 | native-header-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-borderless-scanned | native-header-bullets | False | 0/9 | 0/12 | — | 0.008 | — | ok |
| table-wrapped-records | native-header-bullets | False | 0/12 | 0/17 | — | 0.008 | — | ok |
| text-structure-and-literals | hybrid-html | True | — | — | — | 0.035 | — | ok |
| positioned-math | hybrid-html | True | — | — | — | 0.033 | — | ok |
| math-actualtext | hybrid-html | True | — | — | — | 0.033 | — | ok |
| accessible-actualtext | hybrid-html | unscored | — | — | — | 0.033 | — | ok |
| two-column-order | hybrid-html | True | — | — | — | 0.037 | — | ok |
| unicode-cmap-and-emoji | hybrid-html | unscored | — | — | — | 0.035 | — | ok |
| table-bordered | hybrid-html | True | 9/9 | 12/12 | — | 0.034 | — | ok |
| table-borderless | hybrid-html | True | 9/9 | 12/12 | — | 0.033 | — | ok |
| table-merged | hybrid-html | True | 9/9 | 12/12 | — | 0.034 | — | ok |
| links-and-outline | hybrid-html | unscored | — | — | — | 0.033 | — | ok |
| images-and-vectors | hybrid-html | unscored | — | — | — | 0.033 | — | ok |
| image-only | hybrid-html | unscored | — | — | — | 2.140 | — | ok |
| table-borderless-aligned | hybrid-html | True | 8/8 | 10/10 | — | 0.030 | — | ok |
| rotated-columns | hybrid-html | True | — | — | — | 0.031 | — | ok |
| footnotes-and-page-furniture | hybrid-html | True | — | — | — | 0.033 | — | ok |
| rtl-visual-glyph-order | hybrid-html | unscored | — | — | — | 0.030 | — | ok |
| tagged-reading-order | hybrid-html | unscored | — | — | — | 0.029 | — | ok |
| corpus-usrguide | hybrid-html | unscored | — | — | — | 0.034 | — | ok |
| corpus-senate-expenditures | hybrid-html | unscored | — | — | 23/23 | 0.035 | — | ok |
| corpus-nics-background-checks-2015-11 | hybrid-html | unscored | — | — | 12/12 | 0.076 | — | ok |
| corpus-pdfium-type3 | hybrid-html | unscored | — | — | — | 0.142 | — | ok |
| corpus-f1040 | hybrid-html | unscored | — | — | — | 0.042 | — | ok |
| omml-equations | hybrid-html | unscored | — | — | — | 0.031 | — | ok |
| table-borderless-rotate-90 | hybrid-html | True | 9/9 | 12/12 | — | 0.032 | — | ok |
| table-borderless-rotate-180 | hybrid-html | True | 9/9 | 12/12 | — | 0.030 | — | ok |
| table-borderless-rotate-270 | hybrid-html | True | 9/9 | 12/12 | — | 0.030 | — | ok |
| table-borderless-scanned | hybrid-html | True | 9/9 | 12/12 | — | 2.235 | — | ok |
| table-wrapped-records | hybrid-html | True | 12/12 | 17/17 | — | 0.031 | — | ok |
| text-structure-and-literals | hybrid-bullets | True | — | — | — | 0.031 | — | ok |
| positioned-math | hybrid-bullets | True | — | — | — | 0.031 | — | ok |
| math-actualtext | hybrid-bullets | True | — | — | — | 0.034 | — | ok |
| accessible-actualtext | hybrid-bullets | unscored | — | — | — | 0.030 | — | ok |
| two-column-order | hybrid-bullets | True | — | — | — | 0.031 | — | ok |
| unicode-cmap-and-emoji | hybrid-bullets | unscored | — | — | — | 0.030 | — | ok |
| table-bordered | hybrid-bullets | True | 9/9 | 12/12 | — | 0.031 | — | ok |
| table-borderless | hybrid-bullets | True | 9/9 | 12/12 | — | 0.030 | — | ok |
| table-merged | hybrid-bullets | True | 9/9 | 12/12 | — | 0.031 | — | ok |
| links-and-outline | hybrid-bullets | unscored | — | — | — | 0.030 | — | ok |
| images-and-vectors | hybrid-bullets | unscored | — | — | — | 0.031 | — | ok |
| image-only | hybrid-bullets | unscored | — | — | — | 2.111 | — | ok |
| table-borderless-aligned | hybrid-bullets | True | 8/8 | 10/10 | — | 0.030 | — | ok |
| rotated-columns | hybrid-bullets | True | — | — | — | 0.032 | — | ok |
| footnotes-and-page-furniture | hybrid-bullets | True | — | — | — | 0.030 | — | ok |
| rtl-visual-glyph-order | hybrid-bullets | unscored | — | — | — | 0.033 | — | ok |
| tagged-reading-order | hybrid-bullets | unscored | — | — | — | 0.030 | — | ok |
| corpus-usrguide | hybrid-bullets | unscored | — | — | — | 0.038 | — | ok |
| corpus-senate-expenditures | hybrid-bullets | unscored | — | — | 23/23 | 0.035 | — | ok |
| corpus-nics-background-checks-2015-11 | hybrid-bullets | unscored | — | — | 12/12 | 0.076 | — | ok |
| corpus-pdfium-type3 | hybrid-bullets | unscored | — | — | — | 0.129 | — | ok |
| corpus-f1040 | hybrid-bullets | unscored | — | — | — | 0.042 | — | ok |
| omml-equations | hybrid-bullets | unscored | — | — | — | 0.031 | — | ok |
| table-borderless-rotate-90 | hybrid-bullets | True | 9/9 | 12/12 | — | 0.030 | — | ok |
| table-borderless-rotate-180 | hybrid-bullets | True | 9/9 | 12/12 | — | 0.030 | — | ok |
| table-borderless-rotate-270 | hybrid-bullets | True | 9/9 | 12/12 | — | 0.031 | — | ok |
| table-borderless-scanned | hybrid-bullets | True | 9/9 | 12/12 | — | 2.203 | — | ok |
| table-wrapped-records | hybrid-bullets | True | 12/12 | 17/17 | — | 0.030 | — | ok |

## Run provenance

```json
{
  "started_at": "2026-10-08T03:18:26.318705+00:00",
  "environment": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44",
  "python": "3.14.7",
  "source_commit": "fa21fb462d9b10431e705fc2dc727f733b15e48e",
  "remote_spend_authorized_usd": 15,
  "remote_spend_usd": 1.024262108,
  "observation_code_sha256": "5a1f588ac88fc76515aaa9253d93e1b6a249a4311eedfcd4ffc2979b30d665e3",
  "spend_scope": "Shared whole-study total, including API and rental; do not add totals across reports",
  "remote_cleanup_verified": true,
  "spend_breakdown": {
    "reported_at": "2026-10-08T06:16:29.886431+00:00",
    "rental_provider_reported_usd": 0.684,
    "rental_provider_query_at": 1791440003.470863,
    "api_provider_reported_usd": 0.340262108,
    "api_requests": 138,
    "unsettled_api_requests": 0,
    "combined_provider_reported_usd": 1.024262108,
    "authorized_cap_usd": 15,
    "billing_note": "Provider-reported snapshot after destruction; rental rows are rounded to three decimals",
    "instance_id": 54777034,
    "instance_removed": true,
    "archive_sha256": "31a21270168baa6d283aaea4c40ea2aa2b1ea227d798a9a0657a4f66c047c825"
  }
}
```

| Run | Adapter | Initialization seconds | Repetitions | Device | Model |
| --- | --- | ---: | ---: | --- | --- |
| 0 | pdfust | 0.000 | 3 | cuda:0 | none |
| 1 | pdfust-text | 0.000 | 3 | cuda:0 | none |
| 2 | geometry | 0.000 | 3 | cuda:0 | none |
| 3 | geometry-bullets | 0.000 | 3 | cuda:0 | none |
| 4 | geometry-wrapped | 0.000 | 3 | cuda:0 | none |
| 5 | geometry-wrapped-bullets | 0.000 | 3 | cuda:0 | none |
| 6 | yolo-geometry | 4.195 | 1 | cuda:0 | /home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/49b97586dbd3bdae169e8f5e165710d0facf5f1e/yolo26m-doclaynet.pt |
| 7 | yolo-geometry-wrapped | 0.209 | 1 | cuda:0 | /home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/49b97586dbd3bdae169e8f5e165710d0facf5f1e/yolo26m-doclaynet.pt |
| 8 | yolo-geometry | 2.014 | 1 | cuda:0 | /home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/49b97586dbd3bdae169e8f5e165710d0facf5f1e/yolo26m-doclaynet.pt |
| 9 | yolo-geometry-wrapped | 0.128 | 1 | cuda:0 | /home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/49b97586dbd3bdae169e8f5e165710d0facf5f1e/yolo26m-doclaynet.pt |
| 10 | olmocr-image | 11.510 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 11 | olmocr-text | 12.841 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 12 | olmocr-patch | 8.354 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 13 | geometry | 0.000 | 3 | cuda:0 | none |
| 14 | geometry-bullets | 0.000 | 3 | cuda:0 | none |
| 15 | geometry-wrapped | 0.000 | 3 | cuda:0 | none |
| 16 | geometry-wrapped-bullets | 0.000 | 3 | cuda:0 | none |
| 17 | native-bullets | 0.000 | 3 | cuda:0 | none |
| 18 | native-header-bullets | 0.000 | 3 | cuda:0 | none |
| 19 | yolo-normalized-geometry-wrapped | 2.058 | 1 | cuda:0 | /home/dan/.cache/huggingface/hub/models--hantian--yolo-doclaynet/snapshots/49b97586dbd3bdae169e8f5e165710d0facf5f1e/yolo26m-doclaynet.pt |
| 20 | qwen-image | 12.194 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 21 | qwen-text | 3.484 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 22 | qwen-patch | 3.370 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 23 | native-header-bullets | 0.000 | 3 | cuda:0 | none |
| 24 | repair-qwen-image | 0.000 | 3 | cuda:0 | none |
| 25 | repair-qwen-text | 0.000 | 3 | cuda:0 | none |
| 26 | retained-docling | 0.000 | 1 | cuda:0 | none |
| 27 | retained-docling-formulas | 0.000 | 1 | cuda:0 | none |
| 28 | retained-marker-fast | 0.000 | 1 | cuda:0 | none |
| 29 | ocr-geometry-wrapped | 0.033 | 1 | cuda:0 | none |
| 30 | ocr-geometry-wrapped | 0.017 | 1 | cuda:0 | none |
| 31 | hybrid-html | 0.031 | 3 | cuda:0 | none |
| 32 | hybrid-bullets | 0.009 | 3 | cuda:0 | none |
| 33 | olmocr-normalized | 15.382 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 34 | olmocr-compact-text | 7.341 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 35 | olmocr-4bit-text | 12.052 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 36 | olmocr-yolo-crop | 6.810 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 37 | olmocr-geometry-crop | 8.888 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 38 | olmocr-row-crop | 7.557 | 1 | cuda:0 | allenai/olmOCR-2-7B-1025 |
| 39 | qwen-compact-text | 5.579 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 40 | qwen-compact-patch | 5.573 | 1 | cuda:0 | Qwen/Qwen2.5-VL-3B-Instruct |
| 41 | native-bullets | 0.000 | 3 | cpu | none |
| 42 | native-header-bullets | 0.000 | 3 | cpu | none |
| 43 | hybrid-html | 0.026 | 3 | cpu | none |
| 44 | hybrid-bullets | 0.009 | 3 | cpu | none |

Full dependency versions, per-result run indexes, code hashes, and retained-run provenance are in JSON.
