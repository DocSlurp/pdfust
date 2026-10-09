# Minimalist prompt track

Five generic q0-only variants are frozen before the next scored run: terse task, equal false-positive/false-negative costs, direct candidate comparison, semantic table definition, and a declared three-to-one false-table penalty. The numeric penalty is an experimental decision preference, not a provider charge or calibrated correctness model.

`variants()` returns fresh records with `name`, `rationale` and `instructions`. `transform(body, variant)` deep-copies a retained request and changes only `questions.q0.instructions`; model, literal source, images, IDs, candidate menu and other questions remain unchanged. Instructions contain no examples, labels, per-page facts or scorer references. Names use the `minimal-` prefix to distinguish this track from the structural prompt registry.

The root runner compares Luna and PPLX on the same frozen 48-page DEV cohort. Keep original generic instructions as a control, all fixed page denominators, native-grid routing and complete candidate matrices. Report borderless exact cells and intended ownership, prose false admissions, unresolved/missing observations, complete request costs and matched image/text conditions separately. Aggregate feedback may motivate a separately named second wave; it must not rewrite the first registry or select different pages. No default behavior changes follow from this authored DEV screen alone.

This registry performs no inference, reads no source files or private references, and accesses no credentials. Local tests verify deep-copy isolation and invariance of every request field except the generic q0 instruction.
