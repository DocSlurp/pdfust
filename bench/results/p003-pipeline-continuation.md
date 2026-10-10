# Stopped-arm continuation

`p003_pipeline_continuation` is an offline helper. Root must stop the original
arm and its descendants before using it. It never launches a process, accesses
credentials or a ledger, performs inference, retries a page, or switches models.
Use only private ignored artifact directories for plans and combined outputs.

Preparation authenticates every original frozen PDF and archived code file
against an independently supplied root trusted-code map. It checks that the
artifact inventory remains stable during authentication. Completed successful
pages pass the existing local strict output verifier; the archive is never
executed. Serialized errors are retained as `completed_error`. Invalid completed
outputs are quarantined as `invalid_completed_output`, independently of errors.
Missing results with any retained page artifact are `interrupted_artifacts` and
are blocked. Only `clean_missing` pages enter the subset manifest. No completed
error is selected again. A separate explicit same-model retry investigation is
outside this helper.

```
python -m bench.p003_pipeline_continuation prepare \
  --segment STOPPED_ORIGINAL_ARM --trusted-code ROOT_CODE_MAP \
  --manifest ORIGINAL_SOURCE_MANIFEST --output FRESH_IGNORED_PLAN
```

`manifest.json` contains original source records for clean missing pages only,
with the original source manifest digest. `plan.json` retains full source
records, original configuration, successful/error outcomes, blocked IDs and the
complete original artifact hash inventory. Original manifest bytes must match
the original frozen digest. Root can launch a fresh same-model pipeline arm
using this subset and the original treatment. Preserve every original config
field except `run_id`; preserve the original frozen code. An independently
audited historical Git checkout is preferable if active source code changed.

Combination accepts an explicit JSON list of segment specifications:
`{"directory": "...", "trusted_code": "..."}`. Invoke `combine --segments
SPEC.json --output FRESH_IGNORED_COMBINED`. It rejects different models,
treatments, source records, code hashes, repeated completed pages and silent
retries of interrupted pages. Every original segment is copied under
`segments/INDEX`; selected original per-page bytes are copied unchanged to the
combined root. Missing pages remain explicitly listed. Invalid success outputs
cannot become successful combined outputs.

Complete original reports supply whole-segment resources and costs. A stopped
original without a report contributes unknown CPU, wall and costs. Never replace
those totals with completed-page receipts or overlapping page CPU intervals.
Root may supply an explicit `measurement` object per segment with its separately
measured `metrics` (`wall_seconds`, `cpu_seconds`, `peak_sampled_rss_bytes`),
`effective_usd`, `accounted_usd` and measurement provenance. This object is
retained verbatim and is a root attestation, not independent financial
verification. Totals are complete only when every segment supplies a known
quantity; RSS uses the maximum, not a sum. Segment elapsed intervals exclude idle
gaps and are labeled contended segmented pipeline measurements. Incomplete runs
and unknown elapsed totals have no pages/minute rate. All original failed and
unresolved attempts must remain in root-supplied accounting.

Five tests cover frozen source/code/manifest authentication, successful versus
error/invalid/interrupted admission, no automatic retries, unchanged retained
bytes, model isolation and unknown versus exact-once resource/cost accounting.
Ruff passes. Real source-only validation independently authenticates all 16
completed Luna natural16 vision-region outputs with the root supplied code map;
there were no invalid outputs. No paid calls were made.
