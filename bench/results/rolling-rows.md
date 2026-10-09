# Source-only rolling row candidate experiment R002

Rules were frozen before the independent scorer opened private targets. The
input is the 28-page source-only `run-or_2i6th/source-evidence.json` export from
DEV corpus `66c3cde77b110038`. The candidate artifact SHA256 is
`30044b381bb5d2cf3842a975f486b3f8c92c7c7a3b736efeecea52d6156dc75e`.
Source builders never read private targets, family labels, expected values or
existing native candidates. No model call or GPU work occurred.

The physical alternative assigns gap-separated source fragments to recurring
left or right edge column anchors and keeps each physical band as a row. The
rolling alternative additionally joins sparse hanging bands to the preceding
row when the gap is at most 1.8 median word heights and the hanging fragment is
outside columns with at least three numeric-only supporting fragments. Anchor
support is at least three physical bands; edge tolerance is 0.75 median word
heights. Complete bands and numeric-column-bearing bands remain separate.
Numeric recognition tests literal token shape; it implies no semantic value.

Both variants propose candidates on all 28 pages, own 720 extracted word IDs,
and retain 112 other IDs as unresolved. Exact ID conservation is checked for
every candidate, including unassigned page headings and footers. The physical
alternative retains six seven-row candidates that become four-row candidates
under rolling assembly. This describes candidate differences, not correctness.

Every cell role remains unknown. The first retained row is included without an
assumed header role. These are unaccepted alternatives, not new default tables;
prose can share exactly the same anchors and band geometry. A decider may later
abstain instead of accepting either proposal. Merged spans are not inferred:
all generated cells have unit spans. Native vector controls therefore measure
this mechanism's scope rather than proving unrestricted table recovery.

CPU-only sequential preparation took 0.043 wall seconds, 0.025 process CPU
seconds and 24.71 MiB lifetime peak RSS, measured with perf_counter/process_time
and `/proc/self/status` VmHWM; no sampling or subprocesses. Twelve Python tests
passed, including source metadata perturbation invariance, numeric-row
separation, final-row hanging continuation, duplicate-ID refusal and complete
word conservation. Ruff checks passed. Independent scorer results are pending.

```bash
python -m bench.rolling_rows path/to/source-evidence.json \
  --output bench/results/pdf-master-artifacts/evidence-designs/rolling-v1.json
```

Generated source and complete candidate artifacts remain ignored. Use
`assemble(page, "physical")` and `assemble(page, "rolling")` with literal
word dictionaries and `page_size`; scorer code must consume the already frozen
`candidates` arrays separately. Candidate coverage is an oracle upper bound,
not achieved model selection, real-world quality or calibrated confidence.
