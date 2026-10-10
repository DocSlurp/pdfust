# P003 decision-model progress

These tables read completed independently verified DEV evaluations. All intended pages remain in quality/error denominators. Single runs do not establish hosted repeat confidence. Historical candidate generation and newly measured incremental work are separate.

| Run | Model | Treatment | Outputs/intended | Errors | Complete tables | Strict cells | Text cells | Structure cells | Missing tables | Extra tables | Negative FP | Exact positive pages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| screen-crops-haiku-1024-matrix-strict-r0-c3 | anthropic/claude-haiku-5.5 | processor=vision_regions, preset=vision_regions, transcription_representation=matrix_strict, image_edge=1024 | 15/16 | 1 | 3/53 | 452/2333 | 465 | 527 | 39 | 0 | 0/4 | 2 |
| screen-crops-sonnet-1024-pinned-r0-c3 | anthropic/claude-sonnet-5.5 | processor=vision_regions, preset=vision_regions, transcription_representation=legacy, image_edge=1024 | 15/16 | 1 | 4/53 | 289/2333 | 289 | 361 | 39 | 0 | 0/4 | 3 |
| screen-proposals-union-prob-pplx-haiku-r0-c3 | anthropic/claude-haiku-5.5 | processor=p003_regions, preset=p003_regions, transcription_representation=legacy, image_edge=1024 | 13/16 | 3 | 2/53 | 270/2333 | 270 | 422 | 38 | 1 | 0/4 | 1 |
| screen-proposals-union-small-pplx-haiku-r0-c3 | anthropic/claude-haiku-5.5 | processor=p003_regions, preset=p003_regions, transcription_representation=legacy, image_edge=1024 | 15/16 | 1 | 1/53 | 138/2333 | 138 | 400 | 34 | 6 | 0/4 | 1 |
| screen-crops-gemini35lite-1024-simple-schema-r0-c3 | google/gemini-3.5-flash-lite | processor=vision_regions, preset=vision_regions, transcription_representation=legacy, image_edge=1024 | 15/16 | 1 | 3/53 | 287/2333 | 289 | 352 | 39 | 0 | 0/4 | 2 |

Full-pipeline rates count verified operational outputs. Cost overlays leave original report costs visible. Transport concurrency is part of the treatment; contended runs are separate evidence.

| Run | Measured scope | Transport | Pages/min | Original pages/APIUSD | Original effective USD | Original accounted incl reserves USD | Reconciled effective USD | Reconciled pages/APIUSD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| screen-crops-haiku-1024-matrix-strict-r0-c3 | complete pipeline | contended (3) | 6.74174 | 1604.79 | 0.009347 | 0.009347 | Unmeasured | Unmeasured |
| screen-crops-sonnet-1024-pinned-r0-c3 | complete pipeline | contended (3) | 4.8799 | 64.6307 | 0.232088 | 0.232088 | Unmeasured | Unmeasured |
| screen-proposals-union-prob-pplx-haiku-r0-c3 | complete pipeline | contended (3) | 0.782388 | 295.66 | 0.0439695 | 0.0439695 | Unmeasured | Unmeasured |
| screen-proposals-union-small-pplx-haiku-r0-c3 | complete pipeline | contended (3) | 0.941397 | 333.88 | 0.0449264 | 0.0449264 | Unmeasured | Unmeasured |
| screen-crops-gemini35lite-1024-simple-schema-r0-c3 | complete pipeline | contended (3) | 9.08768 | 345.237 | 0.0434484 | 0.0434484 | Unmeasured | Unmeasured |

CPU/RSS observations retain their process scopes; worker RSS peaks are never added to parent peaks.

| Run | Process | Wall seconds | CPU seconds | Peak RSS bytes | Measurement scope/evidence |
| --- | --- | --- | --- | --- | --- |
| screen-crops-haiku-1024-matrix-strict-r0-c3 | parent | 133.497 | 31.6122 | 354684928 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-haiku-1024-matrix-strict-r0-c3 | detector worker initialization | 3.66461 | 8.08175 | 1063837696 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| screen-crops-haiku-1024-matrix-strict-r0-c3 | detector worker request intervals | 6.2864 | 20.5969 | 1189068800 | 16 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| screen-crops-sonnet-1024-pinned-r0-c3 | parent | 184.43 | 30.0416 | 356290560 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-sonnet-1024-pinned-r0-c3 | detector worker initialization | 5.6632 | 13.6192 | 1057796096 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| screen-crops-sonnet-1024-pinned-r0-c3 | detector worker request intervals | 6.86311 | 21.8461 | 1167769600 | 16 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| screen-proposals-union-prob-pplx-haiku-r0-c3 | parent | 996.948 | 1190.95 | 802566144 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-proposals-union-prob-pplx-haiku-r0-c3 | detector worker initialization | 6.18388 | 14.1857 | 1058136064 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| screen-proposals-union-prob-pplx-haiku-r0-c3 | detector worker request intervals | 5.99483 | 19.9629 | 1155637248 | 16 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| screen-proposals-union-small-pplx-haiku-r0-c3 | parent | 956.026 | 1163.12 | 821719040 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-proposals-union-small-pplx-haiku-r0-c3 | detector worker initialization | 2.79743 | 5.85683 | 1057394688 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| screen-proposals-union-small-pplx-haiku-r0-c3 | detector worker request intervals | 5.43957 | 18.7544 | 1154584576 | 16 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| screen-crops-gemini35lite-1024-simple-schema-r0-c3 | parent | 99.0352 | 28.9904 | 355524608 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-gemini35lite-1024-simple-schema-r0-c3 | detector worker initialization | 3.87104 | 7.28715 | 1063337984 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| screen-crops-gemini35lite-1024-simple-schema-r0-c3 | detector worker request intervals | 6.73968 | 21.7069 | 1160884224 | 16 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |

Provider cache counters are unmeasured in these evaluation-only inputs unless explicitly retained as provider-reported usage. No local replay or cache-hit claim is inferred from latency or cost.

| Run | Cache scope | Observed fresh/all attempts | Reported read tokens subtotal | Reported write tokens subtotal | Read counter missing calls | Write counter missing calls | All-attempt usage coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| screen-crops-haiku-1024-matrix-strict-r0-c3 | current measured stage | 19/19 | 0 | 0 | 0 | 0 | True |
| screen-crops-sonnet-1024-pinned-r0-c3 | current measured stage | 19/19 | 0 | 0 | 0 | 0 | True |
| screen-proposals-union-prob-pplx-haiku-r0-c3 | current measured stage | 220/220 | 0 | 0 | 188 | 188 | True |
| screen-proposals-union-small-pplx-haiku-r0-c3 | current measured stage | 222/222 | 0 | 0 | 188 | 188 | True |
| screen-crops-gemini35lite-1024-simple-schema-r0-c3 | current measured stage | 19/19 | 0 | 0 | 0 | 0 | True |

- `screen-crops-haiku-1024-matrix-strict-r0-c3`: evaluation `6c37fd4fa641b8828c0fc9468a3ee5c69dd35357369525f8fc6d3dd654ff16f5`; report `7a664b30e8b95088eb3ea25490791f47564d49ae0838f21d918a5cba4fed2ed2`; failures `{"Table bounds are outside normalized image coordinates": 1}`; transport `{}`.
- `screen-crops-sonnet-1024-pinned-r0-c3`: evaluation `a5e9ae9afadbcde203fd99b658b9b7dfa7fd345bdc6fa527f36ffd377a228dfb`; report `59c0082b0b2eb478f4432c9b2077ff4a8f4686f8aa149c9c6bf5f6ff45595cf2`; failures `{"Returned crop tables overlap; ownership is unverified": 1}`; transport `{}`.
- `screen-proposals-union-prob-pplx-haiku-r0-c3`: evaluation `26bf18bd2cf11f0927beb7932924590d2a9e1384cda5c9821dea8f1fdbe8e8fc`; report `629df657a767f2a8e2af879509e668c87130fa96f9007f0b0cd3cfc32cb156d7`; failures `{"Covered merge slots must be empty strings": 1, "Returned crop tables overlap; ownership is unverified": 1, "Table bounds are outside normalized image coordinates": 1}`; transport `{}`.
- `screen-proposals-union-small-pplx-haiku-r0-c3`: evaluation `a83f774a45f4d2a70812661071fe8cd4b6b8cfae5c2fc71c84c30b806f4f5577`; report `719e53bc5ac1069e6070cb9214e91c7f620771856dc6133af74d989199d4e940`; failures `{"Table bounds are outside normalized image coordinates": 1}`; transport `{}`.
- `screen-crops-gemini35lite-1024-simple-schema-r0-c3`: evaluation `8d56ccc409d4f71ea16b0331995510e896bacec5f1c5204f54ba583410edf09b`; report `f678e82098da750c5ddba11683c309646e917cffb544154388bc557c08f37431`; failures `{"Returned crop tables overlap; ownership is unverified": 1}`; transport `{}`.
