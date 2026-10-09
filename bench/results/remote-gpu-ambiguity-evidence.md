# Remote GPU measured ambiguity evidence

All four native models returned 288/288 valid answers with the corrected v2 presentation. Adding measured geometry or pixels produced mixed gains and losses against the same-image, same-question controls. Ambiguous abstention remained between 0/8 and 2/8: the extra measurements did not establish the missing word or cell identity. No production policy is selected from these DEV results.

For RGB 500 with identity wording, Flash pixels gained one known answer and one ambiguous abstention (8/16 and 2/8); Clef combined evidence gained three known answers but lost one ambiguous abstention (11/16 and 0/8). PPLX RGB 256 pixels gained two known answers but lost two ambiguous abstentions (12/16 and 0/8). Intern RGB 500 geometry gained two known answers with no ambiguity change (11/16 and 0/8). These examples illustrate the tradeoff; all predeclared arms remain below.

The v2 PPLX and Intern comparisons use 48 original and 48 identity controls rerun on the same recovery host with the same frozen source bytes. Flash and Clef use their retained matching fresh-image and prompt-size controls. All four v2 models used the USD 1.275/hour Max-Q host treatment. Flash and Clef shared a GPU with a companion model; wall-time comparisons with earlier serial runs are not controlled speed comparisons. Source render and verification are local CPU work, excluded from remote inference timing.

All source packets, all fresh images, numeric feature recomputations, evidence projections and returned request hashes passed verification before local DEV references were opened. The 24 authored regions are reused across treatments; they are not independent pages or a natural-document generalization claim. Supplemental pixels come from a separately declared fresh 640-edge CPU render, independent of the model image edge.

Actual lifecycle charges and verified host deletion are in the [remote GPU cost report](remote-gpu-costs.md). The tables below estimate dedicated GPU equivalents from observed batch duration; they are not provider invoices or additive costs for models sharing a host.

## V2: one text segment before the image

24 authored DEV regions × two image sizes × three evidence packs × two fixed prompts

Supplemental pixels use a requested 640-edge fresh source render, independent of model image resolution. Original text, images, questions and whitelisted measurements passed verification before DEV scoring.

Presentation: source-ambiguity-evidence-transport-v2. V1 uses original text, image, supplemental text; V2 uses one exact-prefix text segment before the image. Presentation versions remain separate experiments.

| Model / treatment | Valid/planned | Known correct | Ambiguous abstention | Known abstentions | Exact partition | Conserved |
|---|---:|---:|---:|---:|---:|---:|
| flash / rgb-256/geometry/original | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 |
| flash / rgb-256/geometry/identity | 24/24 | 10/16 | 0/8 | 1 | 10/24 | 24/24 |
| flash / rgb-256/pixels/original | 24/24 | 10/16 | 0/8 | 0 | 10/24 | 24/24 |
| flash / rgb-256/pixels/identity | 24/24 | 9/16 | 1/8 | 0 | 10/24 | 24/24 |
| flash / rgb-256/both/original | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 |
| flash / rgb-256/both/identity | 24/24 | 10/16 | 0/8 | 1 | 10/24 | 24/24 |
| flash / rgb-500/geometry/original | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 |
| flash / rgb-500/geometry/identity | 24/24 | 7/16 | 0/8 | 2 | 7/24 | 24/24 |
| flash / rgb-500/pixels/original | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 |
| flash / rgb-500/pixels/identity | 24/24 | 8/16 | 2/8 | 0 | 10/24 | 24/24 |
| flash / rgb-500/both/original | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 |
| flash / rgb-500/both/identity | 24/24 | 8/16 | 0/8 | 1 | 8/24 | 24/24 |
| clef / rgb-256/geometry/original | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 |
| clef / rgb-256/geometry/identity | 24/24 | 9/16 | 0/8 | 5 | 9/24 | 24/24 |
| clef / rgb-256/pixels/original | 24/24 | 8/16 | 0/8 | 1 | 8/24 | 24/24 |
| clef / rgb-256/pixels/identity | 24/24 | 8/16 | 0/8 | 5 | 8/24 | 24/24 |
| clef / rgb-256/both/original | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 |
| clef / rgb-256/both/identity | 24/24 | 11/16 | 0/8 | 1 | 11/24 | 24/24 |
| clef / rgb-500/geometry/original | 24/24 | 10/16 | 0/8 | 0 | 10/24 | 24/24 |
| clef / rgb-500/geometry/identity | 24/24 | 9/16 | 0/8 | 4 | 9/24 | 24/24 |
| clef / rgb-500/pixels/original | 24/24 | 9/16 | 0/8 | 1 | 9/24 | 24/24 |
| clef / rgb-500/pixels/identity | 24/24 | 7/16 | 0/8 | 7 | 7/24 | 24/24 |
| clef / rgb-500/both/original | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 |
| clef / rgb-500/both/identity | 24/24 | 11/16 | 0/8 | 1 | 11/24 | 24/24 |
| pplx / rgb-256/geometry/original | 24/24 | 10/16 | 0/8 | 0 | 10/24 | 24/24 |
| pplx / rgb-256/geometry/identity | 24/24 | 9/16 | 0/8 | 2 | 9/24 | 24/24 |
| pplx / rgb-256/pixels/original | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 |
| pplx / rgb-256/pixels/identity | 24/24 | 12/16 | 0/8 | 2 | 12/24 | 24/24 |
| pplx / rgb-256/both/original | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 |
| pplx / rgb-256/both/identity | 24/24 | 8/16 | 2/8 | 2 | 10/24 | 24/24 |
| pplx / rgb-500/geometry/original | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 |
| pplx / rgb-500/geometry/identity | 24/24 | 9/16 | 0/8 | 3 | 9/24 | 24/24 |
| pplx / rgb-500/pixels/original | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 |
| pplx / rgb-500/pixels/identity | 24/24 | 12/16 | 0/8 | 3 | 12/24 | 24/24 |
| pplx / rgb-500/both/original | 24/24 | 9/16 | 0/8 | 0 | 9/24 | 24/24 |
| pplx / rgb-500/both/identity | 24/24 | 10/16 | 1/8 | 2 | 11/24 | 24/24 |
| intern / rgb-256/geometry/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-256/geometry/identity | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 |
| intern / rgb-256/pixels/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-256/pixels/identity | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-256/both/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-256/both/identity | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 |
| intern / rgb-500/geometry/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-500/geometry/identity | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 |
| intern / rgb-500/pixels/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-500/pixels/identity | 24/24 | 9/16 | 0/8 | 3 | 9/24 | 24/24 |
| intern / rgb-500/both/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-500/both/identity | 24/24 | 10/16 | 0/8 | 1 | 10/24 | 24/24 |

All failed/missing inputs retain planned denominators in JSON. N/A means no valid model inference; transport failures are not zero model accuracy. Matched controls keep exact image and question wording. Both original and identity controls are available for all four native v2 models.

| Model / treatment | Control known / ambiguous | Known gains / losses | Ambiguous gains / losses | Changes | Unpaired |
|---|---:|---:|---:|---:|---:|
| flash / rgb-256/geometry/original | 10/16 / 0/8 | 0 / 1 | 0 / 0 | 2 | 0 |
| flash / rgb-256/geometry/identity | 9/16 / 2/8 | 3 / 2 | 0 / 2 | 8 | 0 |
| flash / rgb-256/pixels/original | 10/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| flash / rgb-256/pixels/identity | 9/16 / 2/8 | 1 / 1 | 0 / 1 | 3 | 0 |
| flash / rgb-256/both/original | 10/16 / 0/8 | 0 / 1 | 0 / 0 | 1 | 0 |
| flash / rgb-256/both/identity | 9/16 / 2/8 | 3 / 2 | 0 / 2 | 8 | 0 |
| flash / rgb-500/geometry/original | 9/16 / 0/8 | 0 / 1 | 0 / 0 | 1 | 0 |
| flash / rgb-500/geometry/identity | 7/16 / 1/8 | 2 / 2 | 0 / 1 | 7 | 0 |
| flash / rgb-500/pixels/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| flash / rgb-500/pixels/identity | 7/16 / 1/8 | 1 / 0 | 1 / 0 | 3 | 0 |
| flash / rgb-500/both/original | 9/16 / 0/8 | 0 / 1 | 0 / 0 | 1 | 0 |
| flash / rgb-500/both/identity | 7/16 / 1/8 | 3 / 2 | 0 / 1 | 7 | 0 |
| clef / rgb-256/geometry/original | 9/16 / 0/8 | 0 / 1 | 0 / 0 | 1 | 0 |
| clef / rgb-256/geometry/identity | 9/16 / 2/8 | 1 / 1 | 0 / 2 | 5 | 0 |
| clef / rgb-256/pixels/original | 9/16 / 0/8 | 0 / 1 | 0 / 0 | 1 | 0 |
| clef / rgb-256/pixels/identity | 9/16 / 2/8 | 0 / 1 | 0 / 2 | 5 | 0 |
| clef / rgb-256/both/original | 9/16 / 0/8 | 0 / 1 | 0 / 0 | 2 | 0 |
| clef / rgb-256/both/identity | 9/16 / 2/8 | 3 / 1 | 0 / 2 | 9 | 0 |
| clef / rgb-500/geometry/original | 9/16 / 0/8 | 2 / 1 | 0 / 0 | 3 | 0 |
| clef / rgb-500/geometry/identity | 8/16 / 1/8 | 2 / 1 | 0 / 1 | 8 | 0 |
| clef / rgb-500/pixels/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 1 | 0 |
| clef / rgb-500/pixels/identity | 8/16 / 1/8 | 0 / 1 | 0 / 1 | 3 | 0 |
| clef / rgb-500/both/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| clef / rgb-500/both/identity | 8/16 / 1/8 | 3 / 0 | 0 / 1 | 7 | 0 |
| pplx / rgb-256/geometry/original | 12/16 / 0/8 | 0 / 2 | 0 / 0 | 2 | 0 |
| pplx / rgb-256/geometry/identity | 10/16 / 2/8 | 1 / 2 | 0 / 2 | 7 | 0 |
| pplx / rgb-256/pixels/original | 12/16 / 0/8 | 0 / 1 | 0 / 0 | 1 | 0 |
| pplx / rgb-256/pixels/identity | 10/16 / 2/8 | 2 / 0 | 0 / 2 | 6 | 0 |
| pplx / rgb-256/both/original | 12/16 / 0/8 | 0 / 1 | 0 / 0 | 2 | 0 |
| pplx / rgb-256/both/identity | 10/16 / 2/8 | 0 / 2 | 0 / 0 | 5 | 0 |
| pplx / rgb-500/geometry/original | 10/16 / 0/8 | 0 / 1 | 0 / 0 | 2 | 0 |
| pplx / rgb-500/geometry/identity | 12/16 / 2/8 | 1 / 4 | 0 / 2 | 9 | 0 |
| pplx / rgb-500/pixels/original | 10/16 / 0/8 | 0 / 1 | 0 / 0 | 2 | 0 |
| pplx / rgb-500/pixels/identity | 12/16 / 2/8 | 0 / 0 | 0 / 2 | 3 | 0 |
| pplx / rgb-500/both/original | 10/16 / 0/8 | 0 / 1 | 0 / 0 | 2 | 0 |
| pplx / rgb-500/both/identity | 12/16 / 2/8 | 0 / 2 | 0 / 1 | 5 | 0 |
| intern / rgb-256/geometry/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-256/geometry/identity | 11/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-256/pixels/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-256/pixels/identity | 11/16 / 0/8 | 1 / 0 | 0 / 0 | 1 | 0 |
| intern / rgb-256/both/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-256/both/identity | 11/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-500/geometry/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-500/geometry/identity | 9/16 / 0/8 | 2 / 0 | 0 / 0 | 2 | 0 |
| intern / rgb-500/pixels/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-500/pixels/identity | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 1 | 0 |
| intern / rgb-500/both/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-500/both/identity | 9/16 / 0/8 | 1 / 0 | 0 / 0 | 1 | 0 |

| Model / treatment | Inference/HTTP sum s | CPU s | Peak process/client RSS MiB |
|---|---:|---:|---:|
| flash / rgb-256/geometry/original | 4.808 | 5.810 | 18792.8 |
| flash / rgb-256/geometry/identity | 5.212 | 6.303 | 18792.8 |
| flash / rgb-256/pixels/original | 5.301 | 6.378 | 18792.8 |
| flash / rgb-256/pixels/identity | 6.033 | 7.076 | 18792.8 |
| flash / rgb-256/both/original | 6.159 | 7.264 | 18792.8 |
| flash / rgb-256/both/identity | 6.592 | 7.741 | 18792.8 |
| flash / rgb-500/geometry/original | 4.306 | 5.457 | 18792.8 |
| flash / rgb-500/geometry/identity | 5.244 | 6.357 | 18792.8 |
| flash / rgb-500/pixels/original | 4.644 | 5.790 | 18792.8 |
| flash / rgb-500/pixels/identity | 5.633 | 6.837 | 18792.8 |
| flash / rgb-500/both/original | 5.443 | 6.651 | 18792.8 |
| flash / rgb-500/both/identity | 6.416 | 7.606 | 18792.8 |
| clef / rgb-256/geometry/original | 8.977 | 9.996 | 53025.3 |
| clef / rgb-256/geometry/identity | 8.063 | 9.082 | 53025.3 |
| clef / rgb-256/pixels/original | 8.935 | 9.959 | 53025.3 |
| clef / rgb-256/pixels/identity | 9.003 | 10.009 | 53025.3 |
| clef / rgb-256/both/original | 10.012 | 11.079 | 53025.3 |
| clef / rgb-256/both/identity | 9.788 | 10.832 | 53025.3 |
| clef / rgb-500/geometry/original | 8.401 | 9.466 | 53025.3 |
| clef / rgb-500/geometry/identity | 8.147 | 9.243 | 53025.3 |
| clef / rgb-500/pixels/original | 8.901 | 9.984 | 53025.3 |
| clef / rgb-500/pixels/identity | 8.892 | 9.944 | 53025.3 |
| clef / rgb-500/both/original | 10.258 | 11.367 | 53025.3 |
| clef / rgb-500/both/identity | 9.979 | 11.104 | 53025.3 |
| pplx / rgb-256/geometry/original | 6.369 | 7.099 | 6085.3 |
| pplx / rgb-256/geometry/identity | 5.754 | 6.483 | 6085.3 |
| pplx / rgb-256/pixels/original | 6.104 | 6.832 | 6085.3 |
| pplx / rgb-256/pixels/identity | 6.045 | 6.761 | 6085.3 |
| pplx / rgb-256/both/original | 7.581 | 8.316 | 6085.3 |
| pplx / rgb-256/both/identity | 7.539 | 8.267 | 6085.3 |
| pplx / rgb-500/geometry/original | 5.915 | 6.653 | 6085.3 |
| pplx / rgb-500/geometry/identity | 5.898 | 6.628 | 6085.3 |
| pplx / rgb-500/pixels/original | 6.195 | 6.915 | 6085.3 |
| pplx / rgb-500/pixels/identity | 6.155 | 6.884 | 6085.3 |
| pplx / rgb-500/both/original | 7.738 | 8.471 | 6085.3 |
| pplx / rgb-500/both/identity | 7.706 | 8.439 | 6085.3 |
| intern / rgb-256/geometry/original | 1.950 | 2.655 | 9087.8 |
| intern / rgb-256/geometry/identity | 1.348 | 2.065 | 9087.8 |
| intern / rgb-256/pixels/original | 1.401 | 2.111 | 9087.8 |
| intern / rgb-256/pixels/identity | 1.401 | 2.111 | 9087.8 |
| intern / rgb-256/both/original | 1.637 | 2.339 | 9087.8 |
| intern / rgb-256/both/identity | 1.639 | 2.342 | 9087.8 |
| intern / rgb-500/geometry/original | 1.403 | 2.119 | 9087.8 |
| intern / rgb-500/geometry/identity | 1.372 | 2.080 | 9087.8 |
| intern / rgb-500/pixels/original | 1.442 | 2.153 | 9087.8 |
| intern / rgb-500/pixels/identity | 1.438 | 2.151 | 9087.8 |
| intern / rgb-500/both/original | 1.669 | 2.384 | 9087.8 |
| intern / rgb-500/both/identity | 1.663 | 2.386 | 9087.8 |

| Model | Status / valid | Batch wall s | CPU s | Peak RSS MiB | Region inputs/min | GPU USD/h | Estimated batch USD | Region inputs/estimated USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| flash | complete; 288/288 | 76.9859 | 86.6422 | 18792.8 | 224.4566 | 1.2750 | 0.0273 | 10562.6657 |
| clef | complete; 288/288 | 123.0381 | 131.3963 | 53025.3 | 140.4443 | 1.2750 | 0.0436 | 6609.1423 |
| pplx | complete; 288/288 | 92.5098 | 95.8161 | 6085.3 | 186.7910 | 1.2750 | 0.0328 | 8790.1628 |
| intern | complete; 288/288 | 25.2731 | 32.6075 | 9087.8 | 683.7318 | 1.2750 | 0.0090 | 32175.6131 |

Rates count repeated region inputs, not independent pages. Batch wall includes native worker initialization; Qwen HTTP clients exclude external server initialization. Dollar values use the supplied hourly host quote times observed batch wall: dedicated-GPU-equivalent estimates excluding downloads, provisioning, idle time and teardown. These are not invoices and cannot be added across companion models sharing a GPU. Failed pre-inference rows retain measured overhead but inference rates/cost estimates are N/A. Native CPU/RSS include the model process; Qwen CPU totals cover child clients. Server CPU/RSS and allocator peaks are unmeasured here. Device monitoring and server-tree samples stay separate.

Native timing includes shared-GPU companion contention; baseline quality is paired but timing is not a controlled speed comparison. Qwen 9B uses eight concurrent HTTP inputs to a shared server: summed request latency is not batch elapsed, and client resources do not measure model-server resources. Group CPU/RSS cover measured model process or HTTP client as labeled. Device-wide GPU monitoring and allocator peaks are separately retained; partial/missing measurements stay unknown.

## V1: separate retained presentation

Intern and Qwen 9B each returned 288/288 valid answers. Flash, Clef and PPLX each stopped after three adapter refusals before model inference, leaving 285 inputs unattempted. Their quality columns are N/A; raw planned denominators and measured startup overhead remain in JSON. V1 uses text, image, supplemental text, whereas v2 combines the exact original text prefix and supplemental JSON before the image. These presentations are separate experiments.

Intern original-wording arms all remained 12/16 known and 0/8 ambiguous. At RGB 500, its geometry/identity arm gained two known answers with no losses (11/16), still 0/8 ambiguous. Qwen RGB 256 geometry/identity and combined/identity lost all six ambiguity abstentions from their matched 6/8 control; pixels/identity retained 6/8 while losing one known answer. At RGB 500, Qwen combined/identity gained three known answers and lost four ambiguity abstentions. Qwen has no matching original RGB 256/500 controls; 48 controls remain a preplanned future comparison, and no 512-edge substitute is used.

24 authored DEV regions × two image sizes × three evidence packs × two fixed prompts

Supplemental pixels use a requested 640-edge fresh source render, independent of model image resolution. Original text, images, questions and whitelisted measurements passed verification before DEV scoring.

Presentation: source-ambiguity-evidence-v1. V1 uses original text, image, supplemental text; V2 uses one exact-prefix text segment before the image. Presentation versions remain separate experiments.

| Model / treatment | Valid/planned | Known correct | Ambiguous abstention | Known abstentions | Exact partition | Conserved |
|---|---:|---:|---:|---:|---:|---:|
| flash / rgb-256/geometry/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-256/geometry/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-256/pixels/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-256/pixels/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-256/both/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-256/both/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-500/geometry/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-500/geometry/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-500/pixels/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-500/pixels/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-500/both/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| flash / rgb-500/both/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-256/geometry/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-256/geometry/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-256/pixels/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-256/pixels/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-256/both/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-256/both/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-500/geometry/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-500/geometry/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-500/pixels/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-500/pixels/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-500/both/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| clef / rgb-500/both/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-256/geometry/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-256/geometry/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-256/pixels/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-256/pixels/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-256/both/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-256/both/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-500/geometry/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-500/geometry/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-500/pixels/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-500/pixels/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-500/both/original | 0/24 | N/A | N/A | N/A | N/A | N/A |
| pplx / rgb-500/both/identity | 0/24 | N/A | N/A | N/A | N/A | N/A |
| intern / rgb-256/geometry/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-256/geometry/identity | 24/24 | 10/16 | 0/8 | 0 | 10/24 | 24/24 |
| intern / rgb-256/pixels/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-256/pixels/identity | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-256/both/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-256/both/identity | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 |
| intern / rgb-500/geometry/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-500/geometry/identity | 24/24 | 11/16 | 0/8 | 1 | 11/24 | 24/24 |
| intern / rgb-500/pixels/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-500/pixels/identity | 24/24 | 10/16 | 0/8 | 2 | 10/24 | 24/24 |
| intern / rgb-500/both/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| intern / rgb-500/both/identity | 24/24 | 10/16 | 0/8 | 2 | 10/24 | 24/24 |
| qwen9 / rgb-256/geometry/original | 24/24 | 12/16 | 0/8 | 0 | 12/24 | 24/24 |
| qwen9 / rgb-256/geometry/identity | 24/24 | 7/16 | 0/8 | 1 | 7/24 | 24/24 |
| qwen9 / rgb-256/pixels/original | 24/24 | 12/16 | 1/8 | 0 | 13/24 | 24/24 |
| qwen9 / rgb-256/pixels/identity | 24/24 | 7/16 | 6/8 | 3 | 13/24 | 24/24 |
| qwen9 / rgb-256/both/original | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 |
| qwen9 / rgb-256/both/identity | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 |
| qwen9 / rgb-500/geometry/original | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 |
| qwen9 / rgb-500/geometry/identity | 24/24 | 7/16 | 1/8 | 1 | 8/24 | 24/24 |
| qwen9 / rgb-500/pixels/original | 24/24 | 11/16 | 0/8 | 0 | 11/24 | 24/24 |
| qwen9 / rgb-500/pixels/identity | 24/24 | 6/16 | 4/8 | 5 | 10/24 | 24/24 |
| qwen9 / rgb-500/both/original | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 |
| qwen9 / rgb-500/both/identity | 24/24 | 8/16 | 0/8 | 0 | 8/24 | 24/24 |

All failed/missing inputs retain planned denominators in JSON. N/A means no valid model inference; transport failures are not zero model accuracy. Matched controls keep exact image and question wording. Qwen 9B has identity controls only; 48 original controls remain preplanned for a future wave. No 512-edge image is substituted.

| Model / treatment | Control known / ambiguous | Known gains / losses | Ambiguous gains / losses | Changes | Unpaired |
|---|---:|---:|---:|---:|---:|
| flash / rgb-256/geometry/original | 10/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-256/geometry/identity | 9/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-256/pixels/original | 10/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-256/pixels/identity | 9/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-256/both/original | 10/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-256/both/identity | 9/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-500/geometry/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-500/geometry/identity | 7/16 / 1/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-500/pixels/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-500/pixels/identity | 7/16 / 1/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-500/both/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| flash / rgb-500/both/identity | 7/16 / 1/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-256/geometry/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-256/geometry/identity | 9/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-256/pixels/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-256/pixels/identity | 9/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-256/both/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-256/both/identity | 9/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-500/geometry/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-500/geometry/identity | 8/16 / 1/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-500/pixels/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-500/pixels/identity | 8/16 / 1/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-500/both/original | 9/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| clef / rgb-500/both/identity | 8/16 / 1/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-256/geometry/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-256/geometry/identity | 10/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-256/pixels/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-256/pixels/identity | 10/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-256/both/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-256/both/identity | 10/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-500/geometry/original | 10/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-500/geometry/identity | 12/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-500/pixels/original | 10/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-500/pixels/identity | 12/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-500/both/original | 10/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| pplx / rgb-500/both/identity | 12/16 / 2/8 | 0 / 0 | 0 / 0 | 0 | 24 |
| intern / rgb-256/geometry/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-256/geometry/identity | 11/16 / 0/8 | 0 / 1 | 0 / 0 | 1 | 0 |
| intern / rgb-256/pixels/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-256/pixels/identity | 11/16 / 0/8 | 1 / 0 | 0 / 0 | 1 | 0 |
| intern / rgb-256/both/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-256/both/identity | 11/16 / 0/8 | 1 / 1 | 0 / 0 | 2 | 0 |
| intern / rgb-500/geometry/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-500/geometry/identity | 9/16 / 0/8 | 2 / 0 | 0 / 0 | 3 | 0 |
| intern / rgb-500/pixels/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-500/pixels/identity | 9/16 / 0/8 | 1 / 0 | 0 / 0 | 2 | 0 |
| intern / rgb-500/both/original | 12/16 / 0/8 | 0 / 0 | 0 / 0 | 0 | 0 |
| intern / rgb-500/both/identity | 9/16 / 0/8 | 1 / 0 | 0 / 0 | 2 | 0 |
| qwen9 / rgb-256/geometry/identity | 8/16 / 6/8 | 0 / 1 | 0 / 6 | 10 | 0 |
| qwen9 / rgb-256/pixels/identity | 8/16 / 6/8 | 0 / 1 | 1 / 1 | 6 | 0 |
| qwen9 / rgb-256/both/identity | 8/16 / 6/8 | 0 / 0 | 0 / 6 | 9 | 0 |
| qwen9 / rgb-500/geometry/identity | 5/16 / 4/8 | 2 / 0 | 0 / 3 | 7 | 0 |
| qwen9 / rgb-500/pixels/identity | 5/16 / 4/8 | 1 / 0 | 0 / 0 | 2 | 0 |
| qwen9 / rgb-500/both/identity | 5/16 / 4/8 | 3 / 0 | 0 / 4 | 9 | 0 |

| Model / treatment | Inference/HTTP sum s | CPU s | Peak process/client RSS MiB |
|---|---:|---:|---:|
| flash / rgb-256/geometry/original | unknown | unknown | unknown |
| flash / rgb-256/geometry/identity | unknown | unknown | unknown |
| flash / rgb-256/pixels/original | unknown | unknown | unknown |
| flash / rgb-256/pixels/identity | unknown | unknown | unknown |
| flash / rgb-256/both/original | unknown | unknown | unknown |
| flash / rgb-256/both/identity | unknown | unknown | unknown |
| flash / rgb-500/geometry/original | unknown | unknown | unknown |
| flash / rgb-500/geometry/identity | unknown | unknown | unknown |
| flash / rgb-500/pixels/original | unknown | unknown | unknown |
| flash / rgb-500/pixels/identity | unknown | unknown | unknown |
| flash / rgb-500/both/original | unknown | unknown | unknown |
| flash / rgb-500/both/identity | unknown | unknown | unknown |
| clef / rgb-256/geometry/original | unknown | unknown | unknown |
| clef / rgb-256/geometry/identity | unknown | unknown | unknown |
| clef / rgb-256/pixels/original | unknown | unknown | unknown |
| clef / rgb-256/pixels/identity | unknown | unknown | unknown |
| clef / rgb-256/both/original | unknown | unknown | unknown |
| clef / rgb-256/both/identity | unknown | unknown | unknown |
| clef / rgb-500/geometry/original | unknown | unknown | unknown |
| clef / rgb-500/geometry/identity | unknown | unknown | unknown |
| clef / rgb-500/pixels/original | unknown | unknown | unknown |
| clef / rgb-500/pixels/identity | unknown | unknown | unknown |
| clef / rgb-500/both/original | unknown | unknown | unknown |
| clef / rgb-500/both/identity | unknown | unknown | unknown |
| pplx / rgb-256/geometry/original | unknown | unknown | unknown |
| pplx / rgb-256/geometry/identity | unknown | unknown | unknown |
| pplx / rgb-256/pixels/original | unknown | unknown | unknown |
| pplx / rgb-256/pixels/identity | unknown | unknown | unknown |
| pplx / rgb-256/both/original | unknown | unknown | unknown |
| pplx / rgb-256/both/identity | unknown | unknown | unknown |
| pplx / rgb-500/geometry/original | unknown | unknown | unknown |
| pplx / rgb-500/geometry/identity | unknown | unknown | unknown |
| pplx / rgb-500/pixels/original | unknown | unknown | unknown |
| pplx / rgb-500/pixels/identity | unknown | unknown | unknown |
| pplx / rgb-500/both/original | unknown | unknown | unknown |
| pplx / rgb-500/both/identity | unknown | unknown | unknown |
| intern / rgb-256/geometry/original | 3.496 | 5.721 | 9085.6 |
| intern / rgb-256/geometry/identity | 1.990 | 4.219 | 9085.6 |
| intern / rgb-256/pixels/original | 1.992 | 4.216 | 9085.6 |
| intern / rgb-256/pixels/identity | 1.979 | 4.228 | 9085.6 |
| intern / rgb-256/both/original | 2.031 | 4.280 | 9085.6 |
| intern / rgb-256/both/identity | 2.002 | 4.254 | 9085.6 |
| intern / rgb-500/geometry/original | 2.013 | 4.281 | 9085.6 |
| intern / rgb-500/geometry/identity | 2.017 | 4.278 | 9085.6 |
| intern / rgb-500/pixels/original | 2.026 | 4.293 | 9085.6 |
| intern / rgb-500/pixels/identity | 2.031 | 4.281 | 9085.6 |
| intern / rgb-500/both/original | 2.034 | 4.284 | 9085.6 |
| intern / rgb-500/both/identity | 2.021 | 4.266 | 9085.6 |
| qwen9 / rgb-256/geometry/original | 12.993 | unknown | 31.3 |
| qwen9 / rgb-256/geometry/identity | 8.938 | unknown | 30.7 |
| qwen9 / rgb-256/pixels/original | 12.483 | unknown | 31.4 |
| qwen9 / rgb-256/pixels/identity | 10.682 | unknown | 30.8 |
| qwen9 / rgb-256/both/original | 13.556 | unknown | 30.7 |
| qwen9 / rgb-256/both/identity | 14.228 | unknown | 30.7 |
| qwen9 / rgb-500/geometry/original | 13.169 | unknown | 30.6 |
| qwen9 / rgb-500/geometry/identity | 9.524 | unknown | 30.8 |
| qwen9 / rgb-500/pixels/original | 12.187 | unknown | 31.3 |
| qwen9 / rgb-500/pixels/identity | 10.291 | unknown | 30.7 |
| qwen9 / rgb-500/both/original | 12.981 | unknown | 31.4 |
| qwen9 / rgb-500/both/identity | 13.424 | unknown | 30.8 |

| Model | Status / valid | Batch wall s | CPU s | Peak RSS MiB | Region inputs/min | GPU USD/h | Estimated batch USD | Region inputs/estimated USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| flash | failure_limit; 0/288 | 6.0625 | 6.7018 | 18794.8 | N/A | 1.2750 | N/A | N/A |
| clef | failure_limit; 0/288 | 8.3522 | 9.0862 | 53026.8 | N/A | 1.2750 | N/A | N/A |
| pplx | failure_limit; 0/288 | 18.8838 | 19.8866 | 6079.3 | N/A | 1.2750 | N/A | N/A |
| intern | complete; 288/288 | 37.6908 | 65.2119 | 9085.6 | 458.4672 | 1.3750 | 0.0144 | 20005.8405 |
| qwen9 | complete; 288/288 | 20.0625 | 3.5642 | N/A | 861.3069 | 1.3083 | 0.0073 | 39499.4367 |

Rates count repeated region inputs, not independent pages. Batch wall includes native worker initialization; Qwen HTTP clients exclude external server initialization. Dollar values use the supplied hourly host quote times observed batch wall: dedicated-GPU-equivalent estimates excluding downloads, provisioning, idle time and teardown. These are not invoices and cannot be added across companion models sharing a GPU. Failed pre-inference rows retain measured overhead but inference rates/cost estimates are N/A. Native CPU/RSS include the model process; Qwen CPU totals cover child clients. Server CPU/RSS and allocator peaks are unmeasured here. Device monitoring and server-tree samples stay separate.

Native timing includes shared-GPU companion contention; baseline quality is paired but timing is not a controlled speed comparison. Qwen 9B uses eight concurrent HTTP inputs to a shared server: summed request latency is not batch elapsed, and client resources do not measure model-server resources. Group CPU/RSS cover measured model process or HTTP client as labeled. Device-wide GPU monitoring and allocator peaks are separately retained; partial/missing measurements stay unknown.
