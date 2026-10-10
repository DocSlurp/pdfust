# P003 independent literal source availability

Detector-owned source text loses almost all of its optimistic cell opportunity
on the two dense pages. Across all 16 pages, 53 reference tables and 2,333 cells,
full-page character inventories can support 2,259 cells independently, while
detector-owned inventories can support only 1,267. Of that 992-cell reduction,
991 occurs on the two dense pages. This strengthens the acquisition priority;
it does not imply that expanding acquisition will produce correct tables.

| Frozen source subset | Source words | Independently character-possible cells /2333 | Character-impossible cells | Missing reference character occurrences /15772 | Tables with every cell independently character-possible /53 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full page | 10,778 | 2,259 | 74 | 518 | 39 |
| Detector-owned union | 2,205 | 1,267 | 1,066 | 5,905 | 18 |
| Segment geometry control assigned | 952 | 1,162 | 1,171 | 11,759 | 4 |

| Pages | Reference cells | Full-page possible | Detector-union possible | Geometry-assigned possible |
| --- | ---: | ---: | ---: | ---: |
| Dense two, fixed original IDs | 1,972 | 1,933 | 942 | 855 |
| Other fourteen | 361 | 326 | 325 | 307 |

These are necessary text-availability diagnostics with deliberately optimistic
assumptions. Each reference cell is tested independently against the page's
nonspace character multiset. The same source characters may satisfy multiple
cells, and arbitrary character order, source-word splitting, geometry, topology
and semantic table admission are ignored. All 41 blank reference cells pass
this test automatically. The table-level column merely checks that each cell
passes independently; it is **not an attainable complete-table ceiling**.
Character-impossible cells cannot be obtained by literal character-conserving
assembly from that subset under the stated normalization, but character-possible
cells may still be impossible under complete source-word ownership.

The aggregate character deficit separately preserves multiplicity across all
reference cells on a page: it sums positive differences between required and
available character counts. It is not converted into a cell score or optimized
assignment. No source character is borrowed from another page. Normalization is
NFC plus Unicode whitespace collapse only; case, punctuation and OCR mistakes
are preserved. Whitespace can be introduced by assembly and is excluded from
the necessity counts.

The assigned geometry control had already scored only 94 strict cells and one
complete table over these same pages. Its optimistic independent-character
support of 1,162 therefore leaves a large gap attributable to constraints this
bag analysis ignores, including ownership, ordering, topology and geometry.
The previous source-segment menu also failed to improve that achieved score.
Neither result justifies tuning character thresholds or claiming 1,162
attainable cells. Detector acquisition particularly limits dense-page source
availability; the remaining literal sources still require stronger assembly.

Before target loading, the independent analyzer checked all seven archive
authorities against Git `a2c37de`, authenticated the original ordinal source
with its external `b773d57` authority, validated actual PDF hashes, authenticated
the separate segment control against its external `7af212a` authority, rebuilt
all 1,190 source-only alternatives and the assigned controls, and rebuilt every
frozen bag and geometry receipt byte for byte. All 16 intended pages were kept.
Only then were the fixed subsets compared with separate natural16 DEV targets.
No source inventory was changed after this analysis.

The frozen artifact is `source-availability-v2`, SHA-256
`cfcef7584999cb81996426620f303e0633db45c945abd4762e553cc34a37c7e4`.
Detailed results remain in its ignored `independent-availability.json`. Three
focused tests and Ruff passed. The analysis made zero API calls and accessed no
fresh confirmation or protected heldout data. CPU/RSS and throughput of the
independent scorer were unmeasured; source acquisition costs remain separate.
