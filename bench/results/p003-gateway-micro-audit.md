# P003 independent Gateway micro replay

2026-10-10. CPU-only, offline, authorized ordinal DEV16 sources. No references,
credentials, ledger access, requests, retries, or original output changes.

`bench/p003_gateway_micro_audit.py` independently authenticates the four retained
`pipeline-p003/gateway-micro-v1` runs using separately supplied external code maps
in `gateway-micro-offline-v1` and the source authority `trusted-code/b773d57.json`.
It checks archived code/artifact bytes, exact current pure replay dependencies,
all complete source plans, deterministic 12-pair selection, canonical requests,
native Gateway translations, exact encoded wire bytes, and fresh response
receipts. It executes current authenticated helpers, never archived code, and
does not construct a client. Derived diagnostics are retained separately in
`pipeline-p003/gateway-micro-independent-v2`.

The independently reviewed native normalizer digest is
`beb4bdb6cb8a0f81d244ceddbe6258eb45fcf28a5c892aba6bc9564f26861d86`.
It requires both the requested and returned model to equal `liquid/d1`, exact
answer/question identity, and an answer `name` exactly equal to its enclosing
question ID. It deep-copies the response and removes only that echoed field.
Unknown fields remain available for strict rejection; this is not a general
repair. Choices, raw probabilities, confidence, metadata and probability insertion
order remain unchanged. Original responses are unchanged. The audit checks the
complete expected response delta and strict parser preservation of raw choice
and probability values. There is no probability normalization or ranking change.

| Run | Original outcome | Derived offline interpretation |
| --- | --- | --- |
| d1 micro | 12 malformed answers | 12 valid nonabstaining answers after exact echo removal |
| d1 verbose | 12 malformed answers | 12 valid nonabstaining answers after exact echo removal |
| Laya micro | 11 nonabstaining, 1 abstention | Identical; no normalization |
| Laya verbose | 1 transport error, 11 not attempted | Identical; no normalization |

All 12 d1 source-pair identities match across evidence treatments. Four choices
disagree: 2/4 cell, 1/4 row and 1/4 wrap relations. Median chosen-minus-runner-up
raw margin is 0.436768 micro versus 0.656002 verbose. Micro margins range
0–0.715374 with two exact top ties; verbose margins range 0.055028–0.889603
with no top ties. These margins are uncalibrated descriptions, not accuracy or
evidence that verbosity improves decisions. Two literal words and their original
boxes are preserved in both treatments; packet structure, explanatory text and
rounding differ, so this is not a clean length-only causal comparison.

Laya has **0/12 valid paired comparisons**, not zero observed disagreement.
Its first verbose request matches the retained HTTP422 receipt exactly. The
wire uses a scalar text `state`, 1,923 UTF-8 bytes, and a 2,447-byte complete
request with the boundless route. It contains no image or body-list state.
The retained JSON diagnostic has empty error types, locations and reason
categories; the original server error body was not retained. Consequently the
available evidence cannot identify the validation rule, establish a length limit,
or justify changing question types. The historical USD0.30 reservation remains
recorded as reserved; this audit neither reconciles nor reclassifies it.

Eight focused tests cover exact removal, identity refusals, retained unsupported
fields, probability alteration rejection, deep-copy isolation, failed comparison
denominators, pair-order identity and probability ties. Ruff and the analyzer's
Mypy check pass. CPU/RSS receipts are in the derived summary: one offline parent,
`perf_counter`/`process_time`, unsampled `getrusage` lifetime peak including
imports; all authoritative input hashes and analyzer/normalizer hashes are
retained. Replay took 37.782 wall seconds and 37.214 CPU seconds; lifetime
peak RSS was 539,156 KiB. The derived summary SHA256 is
`9852e4e89109b2d8947dfd7117b0f94983e15f0a2c8c64b0a467cbf0a87d82eb`.
No accuracy or recovered complete-page quality is measured.

Reproduce from a checkout containing the authenticated current replay helpers:

```sh
python -m bench.p003_gateway_micro_audit \
  --root bench/results/pdf-master-artifacts/pipeline-p003/gateway-micro-v1 \
  --trust-directory bench/results/pdf-master-artifacts/pipeline-p003/gateway-micro-offline-v1 \
  --source-trust bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/b773d57.json \
  --normalizer-sha256 beb4bdb6cb8a0f81d244ceddbe6258eb45fcf28a5c892aba6bc9564f26861d86 \
  --output bench/results/pdf-master-artifacts/pipeline-p003/gateway-micro-independent-new
```

The output directory must be new. The normalizer digest is an explicit reviewed
authority, not a digest trusted merely because an artifact supplies it. The
external four archived-code maps and original source map remain independently
required. Original run outcomes and reported historical accounting remain intact.
