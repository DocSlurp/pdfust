# P003 source-owned row/crop candidate opportunity audit

Neither whole-crop selection nor independent physical-row cohort selection
improves strict cells in this six-policy pool: the exact restricted oracle
remains **384/2,333 strict cells and 3/53 complete tables** on all 16 DEV pages.
The authenticated source-ID fallback dominates this pool's geometry alternatives.
No hosted ranking experiment was launched or runnable hosted harness added,
because the prerequisite opportunity audit found no strict-cell gain.

The pool uses the provisional topology shapes from the independently trusted
`pipeline-p003/screen-ordinal-ocr300-512-r0` baseline. Its table bounds derive only
from source-owned word boxes. It does **not** measure the separate fresh
no-text topology/chunked pipeline's candidate language, nor establish a global
extraction ceiling. Root's provisional uniform/source-band quality observations
on that separate pipeline are not directly comparable to this matched pool.
Source snapshots and original source-ID partitions are authenticated against
`pipeline-p003/trusted-code/b773d57.json`. Generated cell strings are discarded;
fallback values are rebuilt from literal source IDs. Only after all candidate
pools and physical cohorts were persisted were references loaded from the
explicitly authorized `pipeline-p002/screens/natural16` DEV corpus.

| Matched fixed policy | Strict cells / 2,333 | Complete tables / 53 |
| --- | ---: | ---: |
| Authenticated source-ID fallback | 384 | 3 |
| Uniform nearest-center | 231 | 2 |
| Uniform conservative overlap/margin | 229 | 2 |
| Source-band nearest-center | 360 | 3 |
| Source-band conservative overlap/margin | 351 | 3 |
| Source-band relaxed overlap/margin | 360 | 3 |
| Exact whole-crop choice oracle | 384 | 3 |
| Exact independent physical-cohort choice oracle | 384 | 3 |

The six prespecified policies produce 79 distinct region states across 52 source
regions; only 10 regions have distinct choices after deduplication. There are
319 differing literal words among 10,778 total words. The 42 regions with one
unique state require no ranking. State labels are blinded letters ordered by
state digest; policy names and quality scores remain local provenance and are
absent from model evidence. Physical duplicates retain their separate source
IDs, and every source ID has exactly one cell or unresolved owner.

Uniform grids divide declared bounds evenly. Source bands reuse the existing
fixed physical-line clearance and persistent whitespace-gutter hypotheses.
Nearest-center assigns only words whose centers lie inside a declared table.
Conservative assignment additionally requires complete word containment,
intersection fraction at least 0.8 and score margin at least 0.15. Relaxed source
assignment uses 0.5 and 0.05. These are frozen untuned geometry hypotheses;
the overlap-minus-0.05-distance score is not a probability. Native or merged
source-owned tables remain protected. No topology, word text, or omitted source
is synthesized. Incompatible or ambiguous words remain unresolved.

Whole-crop selection maximizes the established normalized span-aware strict
anchor score against fixed baseline table pairing. Finer choices operate on
mechanical physical-line cohorts of differing source IDs, not semantic records.
Each ID belongs to one cohort, so mixing cohort alternatives cannot duplicate
source ownership. The decoder preserves untouched cell order and rebuilds
changed cells in deterministic source order. It validates the complete output
atomically. This makes row/crop selection a source-conserving alternative to
per-word decision calls without giving a model authority to generate text.

The row oracle first used two greedy coordinate-ascent passes, yielding no gain;
that observation alone was not treated as a ceiling. The final exact oracle
builds cell-equality factors over already frozen cohort alternatives and solves
them by bounded max-sum variable elimination. One region has 737,280 raw joint
combinations, but the largest elimination intermediate needs only **108**
entries, below the explicit 100,000-entry admission. Every factor optimum is
checked against the actual source-conserving decoder. The authenticated fallback
is preferred on ties. This proves the strict-cell ceiling within this candidate
and cohort language under fixed table pairing; it does not prove an optimum
for edit distance or other objectives. Missing tables and fixed topology errors
remain outside this candidate language.

The pure helper also prepares a native bounded Choice request for one entire
crop, optional inline pixels and an `unresolved` fallback. Difference evidence
shows literal text, coordinates and alternative owner triples only for changed
words, with explicit unchanged-word omission counts, complete local pool/source
hashes and packet hashes. Actual difference packets range from 370 to 9,378 UTF8
bytes (58,097 total across 52 regions); there is no implicit truncation. Model
identity appears only in the transport routing field. A future hosted harness
would need independently authenticated source/topology, fresh metered calls,
complete error receipts and gate-only latency/cost. This audit supports deferring
such calls for this particular pool.

Ignored artifacts are copied to main and worktree under
`pipeline-p003/source-choices-v1/`: complete source-only pools, exact/greedy
oracle receipts, reproduction script and manifest. The current diagnostic
SHA256 is `08e5e61f2148b06f7f14d4e6dfaececc493cc3ffc15f5899cefcf5af912b948b`;
source-only pool SHA256 is
`2a5f9e37b1414732c88e96b13ec1c849151c3124af23318ccc2b5e369d65d952`;
manifest SHA256 is
`dfb03b79b0ff1930c7b7bd3611cccd97c5dfe087d53313ae29e0692347fa643e`.
No heldout material or credentials were read. No inference occurred.

Six CPU-only tests passed: generated-text exclusion, physical-duplicate
conservation, explicit partial evidence, exact fallback preservation, stale-menu
rejection, synthetic attainable gain, exhaustive small max-sum agreement and
blinded native request construction. Ruff and strict mypy passed. The complete
diagnostic took 13.597 wall / 13.402 CPU seconds; Linux getrusage lifetime peak
RSS was 539,156 KiB, including corpus validation and retained-state materialization,
while root paid workers were active. The exact oracle itself previously took
0.470 wall seconds. These are local diagnostic measurements, not hosted rates.
