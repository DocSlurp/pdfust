# Source-only evidence designs D001

This CPU-only adapter freezes four native `/decisions` requests per verified
physical silver DEV page. It imports no client and reads no credentials. Root
can supply the existing shared-ledger `DecisionClient` with each retained JSON
request, replacing only `model`; retain response, provider usage/charges, and
request hash together. All pages use the same fixed gate definition and A/B/
unresolved choices. Labels, family, template, case names and expected values
never enter requests. `scorer-only.json` is a separate local scoring input.

```bash
/home/dan/code/oss/pylopdf/.venv/bin/python -m bench.decision_evidence_designs \
  /home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/silver-v1/2e3b8c00f83375cc \
  --output bench/results/pdf-master-artifacts/evidence-designs/freeze-v1 \
  --gate-only
```

Omit `--gate-only` to freeze bounded header/continuation proposals. Preparation
and evaluation are reusable functions: `snapshot(case)` accepts the same
`pdf_bytes`/`page_index` selector as `silver_image_cases`; `build_request` accepts
that frozen snapshot; `score_gate(expected, results)` accepts scorer labels and
raw native result bodies indexed by anonymous page ID. Scoring never constructs
or modifies a request. Full requests/responses stay under ignored artifacts.
Do not pay for `source_admission_refusal` records: locally record unresolved and
retain their original denominators.

| Arm | Evidence | Hypothesis |
| --- | --- | --- |
| geometry | Word boxes/IDs, geometric bands and fragments, observed axis lines | Connected rule geometry can reject form boxes and prose cheaply without text semantics. |
| neighbors | Same geometry plus literal source words | Local semantics can distinguish headers and wrapped cells from separate rows. |
| blob | Geometry plus a 512-pixel gray word-box and black line schematic | A spatial thumbnail can expose rule connectivity with little image payload; there is no rendered text to transcribe. |
| hybrid | Literal words/geometry plus source extractor grid boxes, dimensions and cells | Explicit vector candidates can focus reasoning, while missing/conflicting candidates require abstention rather than absence assumptions. |

The schematic is generated from actual extractor words and axis-aligned line
commands, never authored target geometry. It is neither a native page rendering
nor a general image-only adapter. Filled rules, curved geometry, clipping,
soft masks and pixel visibility are outside its evidence. Rules represented
only as thin fills may therefore be absent in geometry/blob arms even when a
native source grid is detected. The hybrid prior is a hypothesis, not a gold
answer. This experiment tests whether that existing prior helps model decisions;
it does not independently prove model table understanding.

Physical bands group top coordinates within 0.35 word heights. Word gaps above
one word height split fragments. Proposed continuation pairs occupy adjacent
bands with left edges within 0.75 word heights and vertical gaps within one
word height. The first eight pairs in deterministic geometry order are offered;
this bounds questions, not source evidence. The first band is proposed for a
header decision, with an explicit instruction against assuming it is a header.
Each question allows unresolved. Fragments partition all source word IDs once;
requests invent no words or cells. Choices are diagnostic proposals: there is
no automatic application, inferred missing value, header mutation, or PDF edit.

Assembly questions are useful hypotheses only where a retained page actually
has plausible table structure. Many DEV prose pages generate adjacent-band
pairs too. Run the cheap gate first and reserve a separate declared assembly
experiment for source-selected candidates. Do not call header/continuation
choices extraction-quality gains: these requests currently have no independent
source-ID structural scoring target, and a positive gate does not establish
cell ownership, merged spans or complete table reconstruction.

The gate scorer reports positive precision/recall, negative specificity, macro
recall and unresolved counts. Abstentions and missing responses stay in the
positive/negative class denominators. Ten of 125 pages are authored positives;
accuracy alone is misleading. Labels are repository-authored synthetic silver,
not independently reviewed gold. Gate results cannot support real-world quality
claims. Model-reported probabilities are not calibrated correctness.

Admission refuses more than 4,096 source words, 65,536 UTF-8 source-text bytes,
4,096 observed axis lines or 750,000 request bytes. Source refusal yields a
frozen unresolved-only instruction and remains in all-page scoring. Preparation
is sequential CPU-only. Resource observations use process_time/perf_counter and
Linux current-executable VmHWM; RSS is lifetime peak, not per-page allocation.
Native extension and Python wrapper hashes are retained in the manifest. No
local GPU, remote inference, heldout access, or ledger mutation occurs here.
