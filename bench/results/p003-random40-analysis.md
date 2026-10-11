# P003 randomized office-value pipeline confirmation

3/6 predeclared arms independently verified. This is a separate authored corpus: all 40 pages, 36 reference tables, 2,769 cells and eight negative pages remain in every denominator. It is not a natural-document generalization claim. Models and detector resolutions run separately; no automatic fallback or paid retry is added by evaluation.

Plan SHA256: `501386a3636fbc37fafc9dbc6db9762c4cbf36c93900fceaecafe128b5e9420e`. Target SHA256: `129d07decd9b289d35a4e691782e7f204d8fb5b133c01ba46372710acb7f0cce`. Every completed arm uses its independently supplied runtime map, exact source PDFs, request bodies/images and strict response/output replay. Primary errors contribute zero predicted tables; all original outcomes remain retained.

| Run | Strict/text/structure cells /2769 | Predicted cells | Complete tables /36 | Missing/extra tables | Negative FP /8 | Errors /40 | Exact pages /40 |
|---|---|---:|---:|---|---:|---:|---:|
| random40-luna-yolo640-crop1024-r0-c3 | 2769/2769/2769 | 2775 | 35 | 0/0 | 0 | 0 | 39 |
| random40-luna-yolo1280-crop1024-r0-c3 | 2602/2602/2604 | 2604 | 28 | 2/0 | 0 | 1 | 32 |
| random40-haiku-matrix-yolo640-crop1024-r0-c3 | running | — | — | — | — | — | — |
| random40-haiku-matrix-yolo1280-crop1024-r0-c3 | running | — | — | — | — | — | — |
| random40-sonnet-yolo640-crop1024-r0-c3 | 2769/2769/2769 | 2785 | 36 | 0/1 | 1 | 0 | 39 |
| random40-sonnet-yolo1280-crop1024-r0-c3 | running | — | — | — | — | — | — |

| Run | Effective/reported APIUSD | Attempts | Pages/min | Pages/APIUSD | Wall/CPU s | Parent peak RSS MiB |
|---|---|---:|---:|---:|---|---:|
| random40-luna-yolo640-crop1024-r0-c3 | 0.0227106/0 | 41 | 5.52036 | 1761.29 | 434.754/99.1545 | 384.129 |
| random40-luna-yolo1280-crop1024-r0-c3 | 0.0228247/0 | 38 | 5.08901 | 1708.68 | 459.814/91.9851 | 388.84 |
| random40-sonnet-yolo640-crop1024-r0-c3 | 0.353618/0.353618 | 41 | 7.39928 | 113.116 | 324.356/98.3132 | 374.32 |

| Run | Detector requests | Worker init/inference CPU s | Worker init/inference active wall s | Worker sampled peak MiB |
|---|---:|---|---|---:|
| random40-luna-yolo640-crop1024-r0-c3 | 40 | 17.3911/60.5542 | 11.0341/23.148 | 1064.54 |
| random40-luna-yolo1280-crop1024-r0-c3 | 40 | 22.3383/189.444 | 13.9775/60.0389 | 1308.63 |
| random40-sonnet-yolo640-crop1024-r0-c3 | 40 | 18.4664/62.6824 | 11.3113/22.7779 | 1098.11 |

Rates describe complete hosted pipeline runs under contention, not serial execution or offline evaluation speed. CPU uses process_time; parent RSS uses psutil sampling every 100 ms. Detector worker uses four CPU threads; its initialization and request CPU/active wall are shown separately. Worker RSS is sampled from its own /proc/self/statm every 100 ms plus endpoints. Worker and parent peaks must not be summed; worker active intervals overlap parent hosted pipeline wall. Costs include all attributed attempts and retain their provider-reported or estimated basis; unknown values are not zero. Do not allocate whole-run cost or wall time to selected pages or claim perfect page quality from complete reference-table counts.

Single runs at each resolution do not isolate detector causality from stochastic transcription. No setting is selected from these confirmation results.

| Run | Report SHA256 | Runtime map SHA256 |
|---|---|---|
| random40-luna-yolo640-crop1024-r0-c3 | `59a6f9769f71c4079b07f200f0b738991b13a4564e5d2a74509780f140a1906e` | `f1abc8ec1dd13d3a509cdfe93b899bdf0ec71e54140bf416044a66dd63b6ed0f` |
| random40-luna-yolo1280-crop1024-r0-c3 | `5b988effb33b1bc820a1cf50a32945eebd5dbd69f4cae587a1f62c1218eb9966` | `f1abc8ec1dd13d3a509cdfe93b899bdf0ec71e54140bf416044a66dd63b6ed0f` |
| random40-sonnet-yolo640-crop1024-r0-c3 | `c617724276b536ddf447c58cd38ded026b020d1f592f6860d8029a2dea3c6c41` | `f1abc8ec1dd13d3a509cdfe93b899bdf0ec71e54140bf416044a66dd63b6ed0f` |
