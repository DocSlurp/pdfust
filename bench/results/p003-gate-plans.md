# P003 frozen-generation gate plans

Prepared 2026-10-10 UTC, CPU only; no client constructed and no hosted calls executed.
The independently trusted DEV baseline is
`pipeline-p003/screen-ordinal-ocr300-512-r0`, authenticated against the explicitly
supplied `pipeline-p003/trusted-code/b773d57.json`. All 16 intended pages passed
complete source/state/Markdown authentication. Its 18 generated regions receive
fresh gates; 34 source-policy bypasses retain their deterministic native states.
No gold, prior answers, or data-family labels select requests or treatments.

Ignored plans are retained in both worktree and main workspace under
`bench/results/pdf-master-artifacts/pipeline-p003/plans/frozen-gate-v1/`.
The manifest SHA256 is
`69e0f72b42cfc8fddaab41aed339593c85be9317d6953959ca02bcec755358c7`;
it records baseline/report/trust/runner/queue digests and individual plan hashes.
The actual standalone CLI parser and actual pre-output treatment guards validate
every arm without invoking authentication, output creation, or a client. Root's
current `p003_parallel.validate_plan` also accepted every queue. Execute literal
plans with queue seed **20261010**; the matching ordered plans are retained.

| Plan | Arms | Maximum fresh region calls | SHA256 |
| --- | ---: | ---: | --- |
| image-a.json | 36 | 648 | ac0fc19cf006de4ff5a30816fdad847c90ff4c1770d36f1f1a995ef900df5842 |
| image-b.json | 36 | 648 | c3e6727d184caa21fa35e048b211802fae72072de5fa215bc1281f74679798d2 |
| prompt-core.json | 20 | 360 | b9eafc12ce10d0c920c29146c4df1a92b4646d7e1ac6f024013a7cebce220f85 |
| prompt-followup.json | 8 | 144 | dd556310bda8967a1b74d8541c6a3a3a7e4f69dc9b35c423ac3c59bd7ffbab1c |

The 72 image arms cross PPLX Decider, Luna Decisions, Clef, and Clef Omni with
edges 128/256/400/512/768/1024 and independent RGB, grayscale8, RGB palette16.
Image-a contains PPLX/Luna; image-b contains Clef/Clef Omni. All use compact
literal OCR evidence, the region rubric, and no rolling row context. Only gate
images change; source, region order, historical generation, and fallback are
frozen. Palette16 is a 4-bit **palette index**, whose entries retain RGB8 colors;
grayscale8 is a separate 8-bit luminance treatment. Neither establishes the
provider's internal image representation. Clef Flash is deferred until a root
controlled cooldown screen after its repeated HTTP429; no automatic retry arm
is included. RGB512 controls are reused by the prompt screen.

The prompt core uses 12 matched text-only compact/region controls: all four
image models plus Jev, OpenRouter d1, Tev, Solar, Solar Flash, Mercury, Microsoft
Decision, and Drex, using exact catalog IDs. The eight additional image arms
compare `visual_schema` and `recall_first` rubrics against the factorial controls.
The eight prespecified follow-ups compare lineflow/fullwords against compact in
text controls for PPLX and Clef, then `skeptical`/`local_relations` image rubrics
for those two models. This changes one factor within each matched contrast and
covers both a large advertised context and a documented state truncation risk.
OpenRouter d1 is text-only; Gateway d1 image and Laya text remain separate serial
provider experiments. Model selection follows the retained public catalog
[provenance](p003-model-catalog.md), rather than invented aliases.

Allocate 30–90 minutes for the prompt screen, verification, and review in stages;
this is a bounded research allocation, not a predicted API completion time.
Launch core before follow-up, retaining all intended pages and failed attempts.
The image factorial is separate. Root coordinates exclusive paid work, actual
budget/deadline admission and transport3; all rates are labeled contended and
conditional on frozen historical generation. Repeating OCR or transcription
would invalidate these gate-only comparisons. Compare complete-output quality,
missing/extra tables, negative false positives, gate admissions/errors, evidence
omissions, actual bytes, reported usage, and incremental cost/latency. Keep
historical generation costs visible separately. These are single replicate DEV
screens; no heldout material was accessed.

## Reported input-token audit

Read only root-authorized `parallel-incremental-v1/status.json`, its 29 named
reports and fresh selector/boundary request files. The audit preserves exact
reported usage, text state UTF8 bytes, image presence, question counts, provider
latency and artifact hashes; historical transcription calls are excluded.
There are **367 ledger attempt entries and 363 retained fresh calls with usage**;
failed/unrecorded calls are not assigned zero tokens. The complete audit SHA256
is `a303798bd37fa63c953564b6bc0c46c5fb048cb30cb40a8506e253364143bc29`.

| Model | Calls with usage | Literal state bytes min–max | Reported input tokens min / median / max | Median provider ms |
| --- | ---: | ---: | ---: | ---: |
| Clef | 58 | 787–20,865 | 701 / 1,598.5 / 17,586 | 926.9 |
| Clef Flash | 2 | 2,028–13,066 | 1,294 / 6,713 / 12,132 | 5,067.2 |
| Clef Omni | 58 | 787–20,865 | 698 / 1,601 / 17,568 | 607.1 |
| d1 | 29 | 787–20,865 | 487 / 1,087 / 119,824 | 608.6 |
| Microsoft | 13 | 1,172–17,788 | 869 / 7,932 / 16,462 | 715.3 |
| Luna Decisions | 58 | 787–20,865 | 558 / 1,209 / 11,820 | 593.2 |
| PPLX Decider | 58 | 787–20,865 | 652 / 1,550 / 222,934 | 627.7 |
| Tev | 29 | 787–20,865 | 687 / 1,453 / 218,870 | 580.6 |
| Jev | 29 | 787–20,865 | 895 / 1,789 / 16,819 | 548.3 |
| Solar Flash | 29 | 787–20,865 | 926 / 1,700 / 221,798 | 1,334.1 |

These distributions mix one-question candidate selection and boundary batches
of 4–16 questions, and some calls include images. State bytes exclude questions
and images. All five reported counts above 100,000 occur in 16-question batches
with 17,788–17,975 state bytes. Therefore counters are not directly comparable
per literal word or proof of state retention; request expansion, provider token
accounting and image tokens remain unresolved. Clef's reported counts above
2,000 do not refute its documented silent state truncation behavior. Compact
and sample64 explicitly record omissions/precision; the bounded prompt screen
uses compact versus lossless fullwords/lineflow to investigate this risk without
claiming that byte reduction guarantees retained context. The audit includes no
inferred tokenizer counts or inferred truncation events.

Checks: three CPU-only tests passed, including unchanged filesystem during all
CLI validations and historical-call exclusion; Ruff and strict mypy passed.
Readonly complete-baseline authentication took 0.698 wall / 0.690 CPU seconds,
with lifetime process RSS 92,956 KiB (Linux getrusage; contended with root workers).
This is validation overhead, not remote performance.
