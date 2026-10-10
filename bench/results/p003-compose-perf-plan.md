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
