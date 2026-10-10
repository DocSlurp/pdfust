# P003 decision-model progress

These tables read completed independently verified DEV evaluations. All intended pages remain in quality/error denominators. Single runs do not establish hosted repeat confidence. Historical candidate generation and newly measured incremental work are separate.

Primary candidate quality includes only model-selected complete crop states. Abstained, failed and identical no-question regions receive no model credit; full intended denominators remain. Historical retained pipeline quality follows separately.

| Run | Model-confirmed strict cells | Complete tables | Missing tables | Extra tables | Negative FP | Decision quality errors | Exact positive pages |
| --- | --- | --- | --- | --- | --- | --- | --- |
| confirmation48-choice-pplx-0-rgb-r0-c3 | 1515/4203 | 23/66 | 29 | 0 | 0/10 | 4 | 16 |
| confirmation48-choice-pplx-128-rgb-r0-c3 | 1605/4203 | 16/66 | 26 | 0 | 0/10 | 4 | 10 |
| confirmation48-choice-pplx-512-rgb-r0-c3 | 1793/4203 | 25/66 | 17 | 0 | 0/10 | 4 | 18 |
Retained pipeline output quality (including historical fallback outputs):

| Run | Model | Treatment | Outputs/intended | Errors | Complete tables | Strict cells | Text cells | Structure cells | Missing tables | Extra tables | Negative FP | Exact positive pages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirmation48-luna-1024-r0-c3 | openai/gpt-6-luna | processor=vision_regions, preset=vision_regions, transcription_representation=legacy, image_edge=1024, gate_image=True | 47/48 | 1 | 25/66 | 2467/4203 | 2480 | 3213 | 9 | 0 | 0/10 | 19 |
| confirmation48-sonnet-1024-r0-c3 | anthropic/claude-sonnet-5.5 | processor=vision_regions, preset=vision_regions, transcription_representation=legacy, image_edge=1024, gate_image=True | 45/48 | 3 | 27/66 | 1891/4203 | 1895 | 2456 | 19 | 0 | 0/10 | 20 |
| confirmation48-haiku-matrix-1024-r0-c3 | anthropic/claude-haiku-5.5 | processor=vision_regions, preset=vision_regions, transcription_representation=matrix_strict, image_edge=1024, gate_image=True | 47/48 | 1 | 27/66 | 2664/4203 | 2674 | 3874 | 8 | 1 | 0/10 | 19 |
| confirmation48-ordinal-ocr300-512-r0-c3 | anthropic/claude-haiku-5.5 | processor=regions, preset=ordinal, transcription_representation=legacy, image_edge=512, gate_image=True | 44/48 | 4 | 23/66 | 2080/4203 | 2086 | 2329 | 19 | 3 | 1/10 | 19 |
| confirmation48-choice-pplx-0-rgb-r0-c3 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=0 | 47/48 | 1 | 26/66 | 2545/4203 | 2555 | 3223 | 9 | 0 | 0/10 | 19 |
| confirmation48-choice-pplx-128-rgb-r0-c3 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=128 | 47/48 | 1 | 26/66 | 2546/4203 | 2556 | 3223 | 9 | 0 | 0/10 | 19 |
| confirmation48-choice-pplx-512-rgb-r0-c3 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=512 | 47/48 | 1 | 26/66 | 2545/4203 | 2555 | 3223 | 9 | 0 | 0/10 | 19 |

Fresh model decisions are separate from retained pipeline outputs. A valid unresolved response is an abstention, not a model-selected output. Served model version aliases are retained as provenance; they alone do not establish model substitution.

| Run | Fresh attempts | Returned calls | Parsed selected choices | Parsed abstentions | Committed model crops | Fully chosen candidate pages | Pages retaining output on abstention | Requested-model mismatches | Explicit retry attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirmation48-choice-pplx-0-rgb-r0-c3 | 39 | 39 | 31 | 8 | 31 | 24 | 7 | 0 | 0 |
| confirmation48-choice-pplx-128-rgb-r0-c3 | 39 | 39 | 30 | 9 | 30 | 23 | 8 | 0 | 0 |
| confirmation48-choice-pplx-512-rgb-r0-c3 | 39 | 39 | 39 | 0 | 39 | 31 | 0 | 0 | 0 |

Full-pipeline rates count verified operational outputs. Cost overlays leave original report costs visible. Transport concurrency is part of the treatment; contended runs are separate evidence.

| Run | Measured scope | Transport | Pages/min | Original pages/APIUSD | Original effective USD | Original accounted incl reserves USD | Reconciled effective USD | Reconciled pages/APIUSD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirmation48-luna-1024-r0-c3 | complete pipeline | contended (3) | 5.0144 | 1605.26 | 0.0292787 | 0.0292787 | Unmeasured | Unmeasured |
| confirmation48-sonnet-1024-r0-c3 | complete pipeline | contended (3) | 6.36403 | 89.8659 | 0.500746 | 0.500746 | Unmeasured | Unmeasured |
| confirmation48-haiku-matrix-1024-r0-c3 | complete pipeline | contended (3) | 6.43767 | 1337.74 | 0.0351338 | 0.0351338 | Unmeasured | Unmeasured |
| confirmation48-ordinal-ocr300-512-r0-c3 | complete pipeline | contended (3) | 2.7028 | 684.287 | 0.0643005 | 0.0643005 | Unmeasured | Unmeasured |
| confirmation48-choice-pplx-0-rgb-r0-c3 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00098172 | 0.00098172 | Unmeasured | Unmeasured |
| confirmation48-choice-pplx-128-rgb-r0-c3 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00107728 | 0.00107728 | Unmeasured | Unmeasured |
| confirmation48-choice-pplx-512-rgb-r0-c3 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00111316 | 0.00111316 | Unmeasured | Unmeasured |

Incremental processing rates exclude historical baseline generation.

| Run | Repair attempted pages/min | Repair attempted pages/APIUSD | Ranking processed pages/min | Ranking processed pages/APIUSD |
| --- | --- | --- | --- | --- |
| confirmation48-choice-pplx-0-rgb-r0-c3 | Unmeasured | Unmeasured | 7.10732 | 48893.8 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| confirmation48-choice-pplx-128-rgb-r0-c3 | Unmeasured | Unmeasured | 6.16077 | 44556.7 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| confirmation48-choice-pplx-512-rgb-r0-c3 | Unmeasured | Unmeasured | 6.03841 | 43120.5 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured |

CPU/RSS observations retain their process scopes; worker RSS peaks are never added to parent peaks.

| Run | Process | Wall seconds | CPU seconds | Peak RSS bytes | Measurement scope/evidence |
| --- | --- | --- | --- | --- | --- |
| confirmation48-luna-1024-r0-c3 | parent | 562.38 | 101.365 | 438079488 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| confirmation48-luna-1024-r0-c3 | detector worker initialization | 3.64253 | 8.32126 | 1064321024 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| confirmation48-luna-1024-r0-c3 | detector worker request intervals | 16.4529 | 57.2241 | 1181679616 | 48 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| confirmation48-sonnet-1024-r0-c3 | parent | 424.26 | 114.27 | 488845312 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| confirmation48-sonnet-1024-r0-c3 | detector worker initialization | 5.39022 | 11.8017 | 1070940160 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| confirmation48-sonnet-1024-r0-c3 | detector worker request intervals | 19.0302 | 62.2699 | 1178050560 | 48 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| confirmation48-haiku-matrix-1024-r0-c3 | parent | 438.047 | 110.49 | 522895360 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| confirmation48-haiku-matrix-1024-r0-c3 | detector worker initialization | 6.75426 | 14.2126 | 1090289664 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| confirmation48-haiku-matrix-1024-r0-c3 | detector worker request intervals | 18.7669 | 63.2273 | 1196912640 | 48 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| confirmation48-ordinal-ocr300-512-r0-c3 | parent | 976.764 | 1635.32 | 937193472 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| confirmation48-ordinal-ocr300-512-r0-c3 | detector worker initialization | 2.72488 | 5.37713 | 1091784704 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| confirmation48-ordinal-ocr300-512-r0-c3 | detector worker request intervals | 14.9302 | 52.5735 | 1189404672 | 47 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| confirmation48-choice-pplx-0-rgb-r0-c3 | parent | 405.216 | 76.9918 | 185901056 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| confirmation48-choice-pplx-128-rgb-r0-c3 | parent | 467.474 | 86.5719 | 319143936 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| confirmation48-choice-pplx-512-rgb-r0-c3 | parent | 476.947 | 86.9117 | 347500544 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |

Provider cache counters are unmeasured in these evaluation-only inputs unless explicitly retained as provider-reported usage. No local replay or cache-hit claim is inferred from latency or cost.

| Run | Cache scope | Observed returned/all attempts | Reported read tokens subtotal | Reported write tokens subtotal | Read counter missing calls | Write counter missing calls | All-attempt usage coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| confirmation48-luna-1024-r0-c3 | current measured stage | 52/52 | 0 | 20897 | 0 | 0 | True |
| confirmation48-sonnet-1024-r0-c3 | current measured stage | 55/55 | 0 | 0 | 0 | 0 | True |
| confirmation48-haiku-matrix-1024-r0-c3 | current measured stage | 53/53 | 0 | 0 | 0 | 0 | True |
| confirmation48-ordinal-ocr300-512-r0-c3 | current measured stage | 39/39 | 0 | 0 | 0 | 0 | True |
| confirmation48-choice-pplx-0-rgb-r0-c3 | current measured stage | 39/39 | Unmeasured | Unmeasured | 39 | 39 | True |
| confirmation48-choice-pplx-0-rgb-r0-c3 | historical baseline 0 | 52/52 | 0 | 20897 | 0 | 0 | True |
| confirmation48-choice-pplx-0-rgb-r0-c3 | historical baseline 1 | 55/55 | 0 | 0 | 0 | 0 | True |
| confirmation48-choice-pplx-128-rgb-r0-c3 | current measured stage | 39/39 | Unmeasured | Unmeasured | 39 | 39 | True |
| confirmation48-choice-pplx-128-rgb-r0-c3 | historical baseline 0 | 52/52 | 0 | 20897 | 0 | 0 | True |
| confirmation48-choice-pplx-128-rgb-r0-c3 | historical baseline 1 | 55/55 | 0 | 0 | 0 | 0 | True |
| confirmation48-choice-pplx-512-rgb-r0-c3 | current measured stage | 39/39 | Unmeasured | Unmeasured | 39 | 39 | True |
| confirmation48-choice-pplx-512-rgb-r0-c3 | historical baseline 0 | 52/52 | 0 | 20897 | 0 | 0 | True |
| confirmation48-choice-pplx-512-rgb-r0-c3 | historical baseline 1 | 55/55 | 0 | 0 | 0 | 0 | True |

- `confirmation48-luna-1024-r0-c3`: evaluation `6bab980676c3eff3b94e5a2614e7d9796ecfb75aa7fd7a64d1fbdb93b50d8786`; report `cc0ffd0dc3e83089de5a7d88f938a947dd492ead3f706f8f9aa789e0490e120f`; failures `{"Table matrix must contain rectangular literal string cells": 1}`; transport `{}`.
- `confirmation48-sonnet-1024-r0-c3`: evaluation `374f9fd0b9f3cf75a8ed7e54d1fd582921df34551226f6cb04a64928da9ad037`; report `2e0fb00b4071ac5fa0e6ca6fde632b91e0ecad77c3a3823dfc78b60bda552850`; failures `{"Covered merge slots must be empty strings": 1, "Table bounds are outside normalized image coordinates": 2}`; transport `{}`.
- `confirmation48-haiku-matrix-1024-r0-c3`: evaluation `a41ed7cb6fc13f5cab4c0a7064c2b2bc9b42d6892413dfdaacfbff2697d89a42`; report `8515859f9d4ba77cfadd0d9054940b730a09fb5e6eff9e87b395129cd425062f`; failures `{"Covered merge slots must be empty strings": 1}`; transport `{}`.
- `confirmation48-ordinal-ocr300-512-r0-c3`: evaluation `12cb7000d96239c9fe3c6805e45d3097f3f8ac4a587db2dbd508c7148d66dfa8`; report `0b553ef0a2dc6320f2f7b2f9d19d49715b524a6fbf7542b805ba5439858d9e4a`; failures `{"Complete empty-page raster exceeds 64M pixel admission": 1, "Duplicate word index": 1, "Response was truncated or has no normal finish": 2}`; transport `{}`.
- `confirmation48-choice-pplx-0-rgb-r0-c3`: evaluation `74cdb9c4414228491081c173f253fb90cb1ebe5454b39d598fe110d506b917e0`; report `2a98ed2d5eab25eb501b8d4657c77d158e96f18a7d082947b44047bbbd721db2`; failures `{"Table matrix must contain rectangular literal string cells": 1}`; transport `{}`.
  Historical baseline report hashes: `cc0ffd0dc3e83089de5a7d88f938a947dd492ead3f706f8f9aa789e0490e120f`, `2e0fb00b4071ac5fa0e6ca6fde632b91e0ecad77c3a3823dfc78b60bda552850`.
- `confirmation48-choice-pplx-128-rgb-r0-c3`: evaluation `4e1e0efd4d3c3cb2cb08c0b072f415755b89d22286917d02b5ffa9c1b9763466`; report `56ed50403d79790de25c14f619874673e06137829bfa53ad874ef67f7abfb067`; failures `{"Table matrix must contain rectangular literal string cells": 1}`; transport `{}`.
  Historical baseline report hashes: `cc0ffd0dc3e83089de5a7d88f938a947dd492ead3f706f8f9aa789e0490e120f`, `2e0fb00b4071ac5fa0e6ca6fde632b91e0ecad77c3a3823dfc78b60bda552850`.
- `confirmation48-choice-pplx-512-rgb-r0-c3`: evaluation `7b997e0dff5b3f4a568e928c2e91dcc753add4d4170eb7c82c08556d25187060`; report `5e176c57469d552619b6fbdc84091b00e98b8235bbee847b20567bb4d7bfd28e`; failures `{"Table matrix must contain rectangular literal string cells": 1}`; transport `{}`.
  Historical baseline report hashes: `cc0ffd0dc3e83089de5a7d88f938a947dd492ead3f706f8f9aa789e0490e120f`, `2e0fb00b4071ac5fa0e6ca6fde632b91e0ecad77c3a3823dfc78b60bda552850`.
