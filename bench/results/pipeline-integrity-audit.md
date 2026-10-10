# P001 pipeline integrity audit

Independent CPU-only review of current runner, proposal, admission, transport and
report code plus the 38 completed P001 runs available during the audit. No
credentials, network requests, paid inference or heldout data were accessed.

## Verified evidence and outputs

The completed runs contain 2,259 page results: 2,232 successful outputs and 27
retained failures. Every successful retained structure matches its report;
source IDs occur exactly once across cells and unresolved inventory; literal
values and span tiling validate; and Markdown matches deterministic rendering
of the full source-owned final state byte-for-byte. The audit parsed 1,124
retained source request packets: 795 assembly, 157 repair and 172 admission.
No structured filename, family, reference, target, pilot or private-scoring
metadata was found in those packets. Source text remains literal data; reviewer
requests repeat source evidence without supplying the primary answer.

The report integrity fix now enforces these Markdown checks. Frozen runner bytes
must match their recorded hash and their Markdown function must match the
reviewed historical AST. Artifact Python is parsed, never executed. All retained
runner sources share the same renderer. `native-r1` lacks its frozen source:
its Markdown still matches the trusted format, but the reporter explicitly
marks historical renderer source integrity unverified. Later native repeats
retain source and are preferred. The comparison-table separator was corrected;
a test checks header, separator and row widths for every emitted table,
including unfinished runs. Seventeen report tests, Ruff and mypy pass.

## Denominators and routing

Failures remain present: 18 no-text refusals, six incomplete native-grid tilings
and three complete-packet size refusals. Full cohorts retain 181 pages, including
168 structure-scored and 13 diagnostic-only pages; the fixed pilot retains
32 scored pages. Missing/error negative outputs are not credited as correct
zero-table pages. Unfinished runs remain visibly separate from completed scores.

The optional review uses explicitly uncalibrated primary score/margin thresholds.
An admitted review replaces the primary answer; a review failure intentionally
makes the entire page an error. Frontier primary models without probabilities
cannot trigger this score-based review. Native-grid bypass preserves observed
grids and does not search residual words for additional borderless tables.
Repair cannot introduce new tables or change column topology; its overlapping
context windows can collectively expose most of a small page.

## Limits and follow-up

Conservation covers the retained extracted snapshot, not all painted PDF
content, Unicode mapping, pixel visibility or semantic correctness. It does not
independently re-extract every PDF to authenticate snapshot text. Headings,
images, equations, forms and overall prose quality lack complete references.
A gated `unresolved` yields an operational zero-table output; negative structural
credit measures that output, not a confident semantic classification.

Historical freezes omit several imported proposal dependencies and runtime
package versions; subsequent freezes should capture them. Text-only assembly
instructions still refer to a full-page image even when no image is attached;
make that availability explicit in a separately versioned prompt. Generic outer
choice instructions also mention `keep` during admission, although admission
only declares table/prose/unresolved; use stage-specific wording in future arms.

The read-only artifact census took 2.96 seconds wall and 2.87 seconds process CPU
with 538,996,736 bytes lifetime peak self RSS. Measurement used `perf_counter`,
`process_time` and Linux self `getrusage`, one sequential CPU process, no sampling
or subprocess workload. These are integrity observations, not quality gains.
