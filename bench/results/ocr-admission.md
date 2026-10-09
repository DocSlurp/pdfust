# Frozen OCR1200 overlap0.5 admission combination

All 28 original DEV pages retained: 4 native-vector zero-call controls and 48 prepared image512 requests (24 pages × two models). No request has been sent.

Source inventories are the immutable 1200-pixel OCR regions, with exact text, region IDs and display bboxes. Physical candidates remain frozen baseline; rolling candidates are the frozen A004 0.5-height overlap arm. Original whole-page rasters are downsampled to 512 pixels by the unchanged A002 body factory. The baseline generic q0 prompt and declared complete-candidate menu are unchanged. Native PDF vectors/text appear only in the four separate native routes, not hosted OCR evidence.

| Cohort | Original target-token recall |
|---|---|
| borderless | 180/180 |
| prose | 432/432 |
| ruled-control | 132/132 |

Original-token recall is a case-sensitive whitespace-token bag metric scored only after freezing. It is not CER, reading order, or independently annotated source-ID gold. Both retained alternatives conserve each OCR region exactly once across candidate cells and unresolved IDs. That inventory claim is separate from recall of original intended words or correct row ownership. The four native routes map OCR region centers to detected cells; ambiguous centers stay unresolved.

Hosted quality and cost remain unmeasured. The rolling candidate ceiling previously reached 12/12 borderless tables, but proposed false tables on 12/12 prose pages; this combination measures whether admission can select or abstain from that frozen menu. Models are `perplexity/pplx-decider-v1.1-27b` and `openai/gpt-6-luna-decisions`.

Frozen manifest SHA256: `68047a8c1dcf89c23eaf885b340dcbd76f79e253bbfa857148ad462ffbed82cb`. Request preparation: 1.820s wall / 1.810s CPU; 888.7 MiB process-lifetime RSS. Measurement: source-only request assembly; perf_counter/process_time; getrusage SELF process-lifetime RSS; single CPU process, no children, no periodic sampling. Prior OCR costs are not included in these assembly timings.

Artifacts: `/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/ocr1200-overlap05-admission-v1`. Original targets remain at `/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/borderless-dev-v1/66c3cde77b110038/private-targets.json`. The manifest/source/candidate/request schema is compatible with the existing rolling_row_run verifier/evaluator. Raw observations, frozen bodies, menus and private recall outputs stay ignored. No hosted-client import, credentials, network call, training, GPU, or heldout access occurs.
