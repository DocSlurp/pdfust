# Exact-output assembly performance screen

The official-postprocessing adapter currently constructs `set(assigned)` once per
source word while identifying unresolved words. The hypothesis is that moving this
unchanging set outside the comprehension reduces CPU without changing an output or
admission. The smaller faithful implementation is this single data-structure reuse;
removing source validation or limiting the retained words would change the contract.

All 144 independently verified official output states are admitted by their externally
recorded frozen/report hashes and six-file Git authority. The screen uses the original
proposal lists, including overlaps and page failures, and requires exact equality of
state, conflict indexes and source-conservation fields. It never reads quality targets,
calls a model, or changes the original official helper.

The fixed warm-process order is baseline, candidate, candidate, baseline, baseline,
candidate. Three paired pass observations share one process and are not three
independent machines or sessions. The provisional acceptance threshold is at least
20% lower median composition CPU time, complete output equality, unchanged refusals
and no removed gates. A candidate passing the screen receives one separate process
confirmation with the same frozen sequence. Failures and slower measurements stay
in the record; no extra runs are added to seek a passing result.

Per-call wall/CPU measurements exclude the equality comparison. psutil process RSS
sampling at 100 ms and overall resource scope include that comparison. Two additional
cProfile passes are diagnostic only and excluded from the uninstrumented timing
comparison. Loaded source objects are warm; imports, source authentication, original
model forwards, structure decoding and output loading are excluded. Concurrent hosted
research is left running. This experiment cannot establish full-pipeline throughput.

Reproduction: run `python -m bench.p003_compose_perf --input <official-tatr-postprocess-v1>
--trusted-code <official-tatr-postprocess-v1.json> --output <new-directory>` in the
isolated compose-perf worktree, using the main workspace's existing virtualenv.
Raw observations and profiles belong under ignored P003 `compose-perf-v1`; the separate
confirmation, if earned, uses `compose-perf-confirmation-v1`. No paid compute is used.

## Screen and separate-process confirmation

All 144 outputs match exactly in every uninstrumented pass and both diagnostic
profiles, including the two frozen page-error states. Five tests retain duplicate
ownership refusal, overlap refusal, page-atomic errors, distinct repeated literals
and a deliberate skipped-work sentinel that fails the output oracle.

| Process | Implementation | Median composition wall s | Median CPU s | CPU min–max s | Process peak RSS MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| Screen | Original | 1.4375 | 1.4264 | 1.4081–1.5069 | 189.36 |
| Screen | Cached membership set | 0.2563 | 0.2552 | 0.2273–0.2748 | 189.41 |
| Confirmation | Original | 1.5006 | 1.4916 | 1.4530–1.6095 | 193.84 |
| Confirmation | Cached membership set | 0.3239 | 0.3160 | 0.2797–0.3332 | 193.88 |

The fresh process confirms a 4.72-fold reduction in this composition CPU interval,
about 1.18 CPU seconds saved across all 144 states. Its apparent effect on the prior
216.58-second entire postprocessing pass would be only about 0.54% if additive;
that is an estimate across different measurements, not a measured full-pass gain.
The unchanged row/column postprocessor remains the main optimization opportunity.
RSS high-water levels accumulate within each process and do not establish a
candidate-specific allocation increase of the displayed difference.

cProfile separately shows the composition function's self time falling while
source validation remains. Its threading/sampler inclusive times overlap, so they
are not interpreted as a partition of wall time. Only uninstrumented calls enter
the table. Six passes per process are paired repeated measures; this is two
process sessions, not hundreds of independent PDF benchmarks.

Verdict: accept the exact-output data-structure reuse as an isolated experimental
helper. Keep the pinned original helper unchanged because current independent
replays require its historical code identity. This modest absolute saving does not
justify interrupting active inference or redesigning the pipeline. All raw results
and diagnostic profiles remain under the two ignored directories declared above.
