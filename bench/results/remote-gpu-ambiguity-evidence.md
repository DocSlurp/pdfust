# Remote GPU measured ambiguity evidence

V1 delivered288/288 valid answers for Intern and Qwen9. Flash, Clef and PPLX each stopped after three adapter refusals before model inference; the remaining285 inputs were unattempted. Those are transport failures, with no model-quality result. The one-text-segment v2 correction is a distinct frozen presentation and will be reported separately.

Intern original-wording evidence arms all remained12/16 known and0/8 ambiguous, matching their original image controls. Its RGB500 geometry/identity arm reached11/16 known versus9/16 for same-prompt control (two gains/no losses), still0/8 ambiguous. Qwen RGB256 geometry/identity and both/identity lost all six ambiguity abstentions from their6/8 matched control; pixels/identity retained6/8 while losing one known answer. At RGB500, Qwen geometry/identity gained two known answers and lost three ambiguity abstentions; both/identity gained three known answers and lost four ambiguity abstentions. Numeric evidence can change choices without establishing the missing cell identity. No v1 Qwen fresh-original pairing is available.

24 authored DEV regions × two image sizes × three evidence packs × two fixed prompts

Pixel measurements use a supplemental source render640 regardless of the model image resolution. All source features, exact images and projections were verified before root-local DEV scoring. No extractor semantic choice, labels, IDs or treatment names enter supplemental model evidence.

| Model / treatment | Valid/planned | Known correct | Ambiguous abstention | Known abstentions | Exact partition | Conserved |
|---|---:|---:|---:|---:|---:|---:|
| flash / rgb-256/geometry/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-256/geometry/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-256/pixels/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-256/pixels/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-256/both/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-256/both/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-500/geometry/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-500/geometry/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-500/pixels/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-500/pixels/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-500/both/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| flash / rgb-500/both/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-256/geometry/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-256/geometry/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-256/pixels/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-256/pixels/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-256/both/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-256/both/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-500/geometry/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-500/geometry/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-500/pixels/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-500/pixels/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-500/both/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| clef / rgb-500/both/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-256/geometry/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-256/geometry/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-256/pixels/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-256/pixels/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-256/both/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-256/both/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-500/geometry/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-500/geometry/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-500/pixels/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-500/pixels/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-500/both/original | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
| pplx / rgb-500/both/identity | 0/24 | 0/16 | 0/8 | 0 | 0/24 | 0/0 |
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

Missing/failed/schema-invalid inputs remain in planned denominators. This experiment combines additional measured source evidence and approved generic wording; original-image baselines isolate the evidence effect only for original wording. Stock generated labels have no native probabilities or calibration. CPU/RSS/CUDA and paired gains/losses, when matched baseline runs are supplied, remain in the JSON artifact.

Presentation: source-ambiguity-evidence-v1. V1 uses original text, image, supplemental text; V2 uses one exact-prefix text segment before the image. Different presentation versions remain separate experiments.
Paired controls below preserve each treatment's exact question wording and image. Original wording uses native fresh-original runs; identity uses the matched prompt-size screen. Qwen9 has identity controls only; its missing48 original controls are preplanned for a future wave. No512 image is substituted.

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

Native timing includes shared-GPU companion contention; baseline quality is paired but timing is not a controlled speed comparison. Qwen9 uses eight concurrent HTTP inputs to a shared server: summed request latency is not batch elapsed, and client resources do not measure model-server resources. Group CPU/RSS cover measured model process or HTTP client as labeled. Device-wide GPU monitoring and allocator peaks are separately retained; partial/missing measurements stay unknown.
