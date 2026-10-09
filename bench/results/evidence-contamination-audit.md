# Evidence contamination audit — 2026-10-08

Read-only audit of the root checkout's context cases, request projections,
compact prompts, image adapter, retrieval fixtures and both runners. No `.env`,
credentials, embedding responses, embedding rankings, or hosted inference output
was inspected. No production, fixture, prompt or runner file was changed. The
only new artifact is this report.

**The inspected request builders do not directly expose gold, fixture IDs,
private intent or expected answers. This establishes request-field isolation,
not uncontaminated held-out confirmation.** Context prompts have already been
adapted on authored DEV examples; shortlisting also used earlier exposed DEV
results. All corresponding ability numbers must remain DEV findings.

## Checked data flow

- `decision_context_cases.py` stores gold outside `evidence`. Actual PDF text,
  positioned words and extracted drawing operations supply evidence. The
  words defining a schedule convention and a separate-entry note are visible
  source text, not hidden gold fields. These unusually explicit synthetic notes
  make the test easier; success does not demonstrate general author-intent
  recovery on real documents.
- `decision_context_prompts.py` applies evidence allowlists and aliases target
  source IDs to `wN`. Candidate cells and complete record paths are projected
  without fixture metadata. Historical summaries use preceding source physical
  lines and geometry, with an explicit weak-proxy label. No gold wrap label,
  previous prediction or current/future target row enters the summary. A row
  count can include a preceding visible note because grouping detects physical
  baselines, not semantic business rows.
- `decision_context_compact.py` supplies literal source spans, source paint and
  context. Derived separators/fill membership are calculated from admitted
  boxes; fact prose describes those same observed relationships. Instructions
  explain a general boundary rule, rather than selecting an answer per fixture.
- `decision_context_run.py` obtains mode targets from gold for scoring and
  retained local records. Those targets are not added to the provider body.
  Fixture IDs occur in local tags/filenames; `DecisionClient` sends the body,
  not those tags, to the model. Image crops use a fixed target region and
  declared transformation parameters; source images carry no gold overlays.
- `decision_retrieval.py` embedding bodies contain image content only for page
  inputs and literal query text for query inputs. Positive/hard-negative IDs
  remain scorer-side. Domain titles visible in generated images are ordinary
  source content; document filenames and relevance labels are not submitted.
  Native extraction is a separately reported literal baseline, not embedding
  input.
- `decision_retrieval_run.py` fixes page128, page512 and `oracle-roi512` before
  inference, saves a manifest before calls, and does not branch on response
  scores to change documents, queries, crop sizes or prompts. The Gemini query
  prefix is a fixed model-specific configuration recorded in that manifest.

CPU request checks mutated every context case's gold, family and fixture ID and
confirmed identical resulting bodies across 30 cases ×4 evidence modes ×6
representations/builders: 720 comparisons. Another twelve comparisons confirmed
that opposing-label paired current observations produce identical assembly and
compact requests. Total: **732 passing invariance checks**. Retrieval envelope
inspection confirmed only model/input/encoding-format fields. These checks made
no model requests.

## Limits that must accompany results

1. **Already exposed DEV is not held-out.** Thirty context PDFs comprise ten
   correlated templates across three vocabularies. Retrieval documents also
   originate from six authored phrases, each with four related variants. Neither
   counts as an independent producer sample or fresh confirmation. Future
   validation requires sources and decisions that tuning agents cannot inspect.
2. **Candidate oracle is constructed, not discovered.** Context A/B alternatives
   are handcrafted join/split assemblies; gold selects one of those same
   alternatives. A 30/30 oracle validates representability and scoring mechanics
   for this menu. It does not measure automatic candidate generation, broad
   reconstruction, multi-level header discovery, full-page extraction, or
   recovery when the correct candidate is absent. The complete native-evidence
   baseline already solves these authored cases, so no model-over-native gain
   follows from merely matching the oracle.
3. **Oracle ROI is an upper-bound condition.** `oracle-roi512` uses the authored
   document's region box directly. The condition is explicitly named in the
   runner and manifest, which is appropriate. Its result must not be presented
   as end-to-end automatic page retrieval; page128/page512 include page
   context and oracle ROI omits region-discovery cost. Region selection remains
   untested.
4. **Raw compact source IDs retain a nuisance signal.** Compact `_span` retains
   numeric full-page extraction IDs. Earlier source lines or notes can change
   that numbering even when those words are omitted in an evidence arm. No
   direct label-bearing ID was found, and paired opposing-label controls have
   identical IDs and current bodies. Still, these inventory-dependent IDs are
   unnecessary potential shortcuts; a later frozen ID-renumbering ablation would
   assess them. This is a risk to audit, not evidence of an observed leak.
5. **Context code provenance needs careful wording.** Its aggregate
   `code_sha256` is computed after calls and does not include
   `decision_context_compact.py`, although compact arms use that file. Retained
   complete provider request hashes identify the actual submitted bodies. The
   aggregate hash alone must not be described as a pre-run freeze of all prompt
   code. Retrieval writes its source manifest before calls; no response-driven
   change was found in that runner.
6. **Exact authored targets do not prove pixel visibility.** Mode-specific
   observable gold is authored, and image expectation selection assumes visible
   cue variants. Tiny/blurred images may destroy distinguishing cues; correctness
   against a full-source target is different from verified image answerability.
   Preserve both evidence-supported and full-source targets, plus unresolved
   behavior and admitted image provenance.
7. **Forced nearest-neighbor output cannot establish no-match rejection.** The
   retrieval scorer reports two forced no-match false hits and no abstention
   threshold. It does not silently invent a threshold, and a ranking success
   must not be interpreted as calibrated rejection capability. Native literal
   matches can join independently ruled cells; this counterexample is a probe
   of chosen relevance semantics, not proof of universal search relevance.

No direct answer leak requiring invalidation of the inspected DEV requests was
found. The bounded claims above are essential: clean request projection and
frozen retrieval settings do not make development evidence independent.

## Source snapshot

Audited root file SHA-256 values (source only, no hosted outputs):

| File | SHA-256 |
| --- | --- |
| `bench/decision_context_cases.py` | `30b7056190e8f1b04449c59514ec416c649fa06d0d5308b1e69552079754f2c8` |
| `bench/decision_context_prompts.py` | `a223c768394ce6bb4560658106b1191bde6fb1adfb177e989497276e04a14f3f` |
| `bench/decision_context_compact.py` | `a993bbeb3d98344c75ae8ca7f8c22dfcbc744832b0464c49f4eda83333a54d00` |
| `bench/decision_images.py` | `c9fc74501ac25820f9c853d1551b1b6909048ec184e0dfb976e7abbd0ecc843a` |
| `bench/decision_context_run.py` | `52311520f82bd9bf10857a9948980528c372c0460c73788eececf8f0e04e00ec` |
| `bench/decision_retrieval.py` | `45f003a495bd7bf78889c00236928fbd350bbb9d1ff94b20a68bde798af37788` |
| `bench/decision_retrieval_run.py` | `718ffb58b0c1abb7946ee622e70ab11b0dd0f3bbb93823369e926b2afa64e056` |

Root follow-up: future context runs now capture code identity before calls and include the compact prompt module. This repairs future provenance only; earlier request-body hashes remain the authoritative evidence for those completed DEV runs.
