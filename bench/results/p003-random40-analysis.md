# P003 randomized office-value pipeline confirmation

6/6 predeclared arms independently verified. This is a separate authored corpus: all 40 pages, 36 reference tables, 2,769 cells and eight negative pages remain in every denominator. It is not a natural-document generalization claim. Models and detector resolutions run separately; no automatic fallback or paid retry is added by evaluation.

Plan SHA256: `501386a3636fbc37fafc9dbc6db9762c4cbf36c93900fceaecafe128b5e9420e`. Target SHA256: `129d07decd9b289d35a4e691782e7f204d8fb5b133c01ba46372710acb7f0cce`. Every completed arm uses its independently supplied runtime map, exact source PDFs, request bodies/images and strict response/output replay. Primary errors contribute zero predicted tables; all original outcomes remain retained.

| Run | Strict/text/structure cells /2769 | Predicted cells | Complete tables /36 | Missing/extra tables | Negative FP /8 | Errors /40 | Exact pages /40 |
|---|---|---:|---:|---|---:|---:|---:|
| random40-luna-yolo640-crop1024-r0-c3 | 2769/2769/2769 | 2775 | 35 | 0/0 | 0 | 0 | 39 |
| random40-luna-yolo1280-crop1024-r0-c3 | 2602/2602/2604 | 2604 | 28 | 2/0 | 0 | 1 | 32 |
| random40-haiku-matrix-yolo640-crop1024-r0-c3 | 2733/2735/2766 | 2818 | 33 | 0/1 | 1 | 0 | 36 |
| random40-haiku-matrix-yolo1280-crop1024-r0-c3 | 2561/2562/2562 | 2564 | 26 | 3/0 | 0 | 2 | 30 |
| random40-sonnet-yolo640-crop1024-r0-c3 | 2769/2769/2769 | 2785 | 36 | 0/1 | 1 | 0 | 39 |
| random40-sonnet-yolo1280-crop1024-r0-c3 | 2499/2499/2499 | 2499 | 29 | 3/0 | 0 | 2 | 33 |

| Run | Effective/reported APIUSD | Cost basis | Attempts | Operational usable pages/min | Operational usable pages/APIUSD | Wall/CPU s | Parent peak RSS MiB |
|---|---|---|---:|---:|---:|---|---:|
| random40-luna-yolo640-crop1024-r0-c3 | 0.0227106/0 | provider-reported BYOK upstream plus gateway USD | 41 | 5.52036 | 1761.29 | 434.754/99.1545 | 384.129 |
| random40-luna-yolo1280-crop1024-r0-c3 | 0.0228247/0 | provider-reported BYOK upstream plus gateway USD | 38 | 5.08901 | 1708.68 | 459.814/91.9851 | 388.84 |
| random40-haiku-matrix-yolo640-crop1024-r0-c3 | 0.0242338/0.0242338 | provider-reported USD | 41 | 6.31584 | 1650.59 | 379.997/114.682 | 375.656 |
| random40-haiku-matrix-yolo1280-crop1024-r0-c3 | 0.0233927/0.0233927 | provider-reported USD | 38 | 6.00374 | 1624.44 | 379.763/100.859 | 374.855 |
| random40-sonnet-yolo640-crop1024-r0-c3 | 0.353618/0.353618 | provider-reported USD | 41 | 7.39928 | 113.116 | 324.356/98.3132 | 374.32 |
| random40-sonnet-yolo1280-crop1024-r0-c3 | 0.33916/0.33916 | provider-reported USD | 38 | 6.01351 | 112.042 | 379.146/99.8304 | 394.047 |

| Run | Detector requests | Worker init/inference CPU s | Worker init/inference active wall s | Worker sampled peak MiB |
|---|---:|---|---|---:|
| random40-luna-yolo640-crop1024-r0-c3 | 40 | 17.3911/60.5542 | 11.0341/23.148 | 1064.54 |
| random40-luna-yolo1280-crop1024-r0-c3 | 40 | 22.3383/189.444 | 13.9775/60.0389 | 1308.63 |
| random40-haiku-matrix-yolo640-crop1024-r0-c3 | 40 | 13.4205/70.9278 | 5.89184/25.6829 | 1061.77 |
| random40-haiku-matrix-yolo1280-crop1024-r0-c3 | 40 | 16.1134/210.129 | 5.29259/69.9428 | 1312.41 |
| random40-sonnet-yolo640-crop1024-r0-c3 | 40 | 18.4664/62.6824 | 11.3113/22.7779 | 1098.11 |
| random40-sonnet-yolo1280-crop1024-r0-c3 | 40 | 18.8552/212.672 | 6.46471/70.142 | 1320.2 |

Rates count operationally usable pages of the full hosted pipeline under contention; they do not count only exact or complete-table pages and do not describe serial execution or offline evaluation speed. CPU uses process_time; parent RSS uses psutil sampling every 100 ms. Detector worker uses four CPU threads; its initialization and request CPU/active wall are shown separately. Worker RSS is sampled from its own /proc/self/statm every 100 ms plus endpoints. Worker and parent peaks must not be summed; worker active intervals overlap parent hosted pipeline wall. Costs include all attributed attempts and retain their provider-reported or estimated basis; unknown values are not zero. Do not allocate whole-run cost or wall time to selected pages or claim perfect page quality from complete reference-table counts.

Single runs at each resolution do not isolate detector causality from stochastic transcription. No setting is selected from these confirmation results.

| Run | Report SHA256 | Runtime map SHA256 |
|---|---|---|
| random40-luna-yolo640-crop1024-r0-c3 | `59a6f9769f71c4079b07f200f0b738991b13a4564e5d2a74509780f140a1906e` | `f1abc8ec1dd13d3a509cdfe93b899bdf0ec71e54140bf416044a66dd63b6ed0f` |
| random40-luna-yolo1280-crop1024-r0-c3 | `5b988effb33b1bc820a1cf50a32945eebd5dbd69f4cae587a1f62c1218eb9966` | `f1abc8ec1dd13d3a509cdfe93b899bdf0ec71e54140bf416044a66dd63b6ed0f` |
| random40-haiku-matrix-yolo640-crop1024-r0-c3 | `5fac849f43cf8d5a826b80f81bac5216cc4206c203d1642af45001dc57840579` | `f359d2fbcd1916fa5bbb8f3fd30f0bb5ef92ebeeac01f98ac674797ad8eb6cd6` |
| random40-haiku-matrix-yolo1280-crop1024-r0-c3 | `1ff3f4b847cdf7b883685c839e53a8cf514a51106720d11899fea52470e66ba3` | `f359d2fbcd1916fa5bbb8f3fd30f0bb5ef92ebeeac01f98ac674797ad8eb6cd6` |
| random40-sonnet-yolo640-crop1024-r0-c3 | `c617724276b536ddf447c58cd38ded026b020d1f592f6860d8029a2dea3c6c41` | `f1abc8ec1dd13d3a509cdfe93b899bdf0ec71e54140bf416044a66dd63b6ed0f` |
| random40-sonnet-yolo1280-crop1024-r0-c3 | `cb7e4440eb432ff7ae2dbc6c3d92760c6adb59cf21ee5ae63256060a3c352ab2` | `f1abc8ec1dd13d3a509cdfe93b899bdf0ec71e54140bf416044a66dd63b6ed0f` |

| Run | Retained failure categories |
|---|---|
| random40-luna-yolo640-crop1024-r0-c3 | none |
| random40-luna-yolo1280-crop1024-r0-c3 | {'Returned crop tables overlap; ownership is unverified': 1} |
| random40-haiku-matrix-yolo640-crop1024-r0-c3 | none |
| random40-haiku-matrix-yolo1280-crop1024-r0-c3 | {'Returned crop tables overlap; ownership is unverified': 1, 'Invalid merged span bounds': 1} |
| random40-sonnet-yolo640-crop1024-r0-c3 | none |
| random40-sonnet-yolo1280-crop1024-r0-c3 | {'Returned crop tables overlap; ownership is unverified': 1, 'Table bounds are outside normalized image coordinates': 1} |
