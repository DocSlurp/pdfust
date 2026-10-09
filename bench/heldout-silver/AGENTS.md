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
