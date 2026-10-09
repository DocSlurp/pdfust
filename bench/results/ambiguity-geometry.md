# Blind source geometry and ambiguity

The frozen geometry gate makes eight correct known decisions, no wrong known decisions, and abstains on all eight ambiguous authored cases. It also abstains on eight known cases. This is a conservative structural gate, not a complete relationship classifier or a claim that geometry uniquely determines every relation.

All thresholds and both cohorts' features were frozen and independently re-extracted before references were read. Configuration `blind-geometry-config-v2` has SHA256 `2b47f1bd9e0871dba0e4fb391c2929adc7c168e1d49c4e42b33432e0716fdbf2`; extractor commit `5118cdb` has source SHA256 `1dbe5f13538d81ab9708b76691a5a815ebc209076d6f448313aa29c60187154b`. No threshold or qualifier was changed after scoring.

| Authored scope | Inputs | Known correct | Wrong known | Known abstentions | Ambiguous abstentions |
|---|---:|---:|---:|---:|---:|
| All L015 pairs | 24 | 8/16 | 0 | 8 | 8/8 |
| Between physical lines | 12 | 8/8 | 0 | 0 | 4/4 |
| Along one baseline | 12 | 0/8 | 0 | 8 | 4/4 |

The inline selectors retain measured glyph geometry: their observed inter-chunk gaps are 0, 0.12, 0.36 and 0.72 em. These values are evidence, not a spacing oracle. A source can draw adjacent characters without encoding the intended word boundary; a large geometric gap can also leave more than one interpretation plausible. The gate preserves both alternatives unless an intervening structural boundary supplies distinct support. It does not infer a literal space from proximity, font size or dictionary plausibility.

The numeric descriptor records measured font size, baseline/ink separation, horizontal overlap, indent, within-chunk gaps, local repeated leading, neighboring-column anchor coincidence, neighboring-row alignment, text direction, separator coverage, and local enclosure/detected-cell flags. It uses fresh `Page.get_layout`, `Page.get_text("dict")`, `Page.get_drawings` and bounded native glyph-position snapshots. The private glyph hook preserves native positions and size; approximate glyph ink boxes use baseline minus 0.8 em to baseline plus 0.2 em. No case identity, producer flavor, expected relation or text semantics determines a qualifier.

`compact(result)` exports the fixed numeric/boolean feature whitelist. It excludes the deterministic choice, alternatives, insufficiency messages, literal text, local IDs and scoring metadata. These features can therefore be supplied to a decision model without supplying the gate's answer. Geometric support and semantic choice remain distinct.

A full-span interpreted separator supports splitting. A small local closed enclosure without an intervening boundary supports joining. Conflicting or fragmentary boundaries preserve both alternatives. Alignment, similar font size, repeated leading and coincident neighboring columns alone do not establish ownership. Zero reported measurements remain zero; unavailable measurements remain null.

The flags named `same_explicit_cell` and `different_explicit_cells` refer to cells detected by the native `lines` layout strategy. That strategy can include hybrid inferred subdivisions; the names do not prove explicit original PDF cell operators. Interpreted paths also do not establish clip-resolved pixel visibility or semantic uniqueness. Partially out-of-scope paths and cells are conservatively excluded. The separate pixel qualifier measures visible boundaries and background transitions; this geometry module does not substitute a fill or whitespace pattern for semantic identity.

| Natural reviewed comparison | Inputs | Known correct / known | Wrong known | Known abstentions | Ambiguous abstentions | Total agreement |
|---|---:|---:|---:|---:|---:|---:|
| Full source | 24 | 0/24 | 0 | 24 | 0/0 | 0/24 |
| Record crop, 512 | 24 | 0/24 | 0 | 24 | 0/0 | 0/24 |
| Record crop, 1200 | 24 | 0/24 | 0 | 24 | 0/0 | 0/24 |
| Description crop, 512 | 24 | 0/2 | 0 | 2 | 22/22 | 22/24 |
| Description crop, 1200 | 24 | 0/2 | 0 | 2 | 22/22 | 22/24 |

Natural full-source and admitted-scope agreement use the existing separately reviewed references and remain separate. All 96 admitted conditions abstain: the gate catches the 44 scope-ambiguous conditions while rejecting 52 scope-known conditions. It does not reconstruct the natural records. The geometry descriptor cannot distinguish 512 from 1200 pixels when their PDF crop geometry is the same. These are repeated, overlapping regions from one Senate page and one reviewer context, not independent documents or independently adjudicated structural gold.

| Source-only extraction | Descriptors | Wall seconds | Process CPU seconds | Lifetime RSS peak MiB |
|---|---:|---:|---:|---:|
| Authored | 24 | 0.758 | 0.766 | 112.8 |
| Natural full source plus four admitted scopes | 120 | 3.849 | 3.919 | 129.0 |

Measurements use one serial CPU process, `perf_counter`, `process_time` and Linux `getrusage` lifetime RSS, without sampling. They include fresh source parsing, native layout/drawings/glyph extraction and numerical features. RSS is not an incremental per-case allocation. No GPU, credentials or inference were used; inference cost and throughput are unmeasured.

The result supports a bounded abstention gate for interpreted structural evidence. It does not support automatically resolving unruled natural records or inline boundaries. The next predeclared comparison supplies the same compact descriptors to the native models under unchanged source packets; any improvement must retain known abstention losses and ambiguous decisive answers in the report. The frozen configuration should remain fixed for that comparison rather than adapting to individual misses.

Reproduce source extraction with `python -m bench.ambiguity_geometry --source <L015-or-natural-source-freeze> --destination <new-ignored-directory>`. The command refuses an existing destination and reads no references. Exact source freezes, configuration, descriptors, verification/scoring script and local evaluation are retained under `.scratch/council/lowlevel-eval/`: `ambiguity-geometry-{authored,natural}-scored-v2/`, `score_geometry.py`, and `ambiguity-geometry-evaluation.json`. The retained scorer verifies both complete feature cohorts and fresh extraction before opening the separate references. Eleven CPU tests cover distinct geometry, scale/translation invariance, inline partial-word selectors, conflicting boundaries, scope exclusion, and independence from text or proxy choices. No protected held-out inputs were accessed.
