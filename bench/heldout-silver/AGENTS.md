# Held-out data protection protocol

This directory contains inventory and access rules only. It does not authorize
reading the protected dataset.

Tuning, development, optimization, research, and experiment agents MUST NOT read,
search, import, execute, inspect images from, or derive feedback from:

`bench/results/pdf-master-artifacts/silver-heldout-v1/`

This includes generators, PDFs, references, gold, semantic metadata, validation
rows, previews, and descriptive per-document measurements. Do not include that
prefix in repository-wide searches or debugging inputs. A filesystem locator or
hash in the inventory is not permission to follow it.

Only the independent data custodian may author and validate this dataset before
freeze. After a candidate is frozen, an explicitly authorized independent
evaluator or explicit user release may access it. Evaluation must retain the
candidate identity, dataset inventory digest, complete run provenance, and
separation from tuning. Never repair or tune an extractor from held-out examples
and continue claiming the same release is held out.

Before release, report only counts, aggregate diversity counts, validation
status, and identity hashes to developers. Do not return case-level titles,
labels, examples, generators, references, scores, or semantic diagnostics.

Isolation is procedural under one OS user, not enforced by filesystem access
control. The protected prefix is Git-ignored. Do not stage, upload, or publish its
contents. Ordinary tests must not open these documents automatically.

## Langfuse copy (user release, 2026-10-11)

On 2026-10-11 the user explicitly released this dataset for storage in the
local Langfuse. `uv run python -m bench.langfuse_backfill heldout
--custodian-release` uploads it as dataset
`HELD-OUT-NOT-FOR-TRAINING/silver-heldout-v1/<root prefix>` and prints only
counts and identity hashes. The dataset and every item carry `split=HELD_OUT`
and `training_use`, `tuning_use`, and `development_feedback` set to
`PROHIBITED`. The first upload stored 20 items, matched 20/20 targets and 20/20
registry PDF hashes, under inventory digest `c1f887661e3d…`.

The Langfuse copy has the same protection as the files. Tuning, development,
optimization, research, and experiment agents must not list, open, query,
export, or score any `HELD-OUT-NOT-FOR-TRAINING/` dataset or its items, and
must exclude that prefix from dataset sweeps. Langfuse has no per-dataset
access control inside a project, so this separation is also procedural. The
release covers storage only. It does not authorize evaluation, and evaluation
still requires a frozen candidate and an authorized evaluator.
