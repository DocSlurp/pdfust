# Self-hosted decision-model shortlist

Research snapshot: 2026-10-09. These eight releases expose trained candidate
scoring, rather than requiring unrestricted answer generation. Ranking below
is our proposed experiment order, based on PDF relevance, adoption, deployment
cost and architectural variety. It is not a measured PDF quality ranking.
No weights were downloaded or remote GPU allocated for this research.

Model cards, reference inference code and public Hugging Face API metadata were
checked. Downloads are the Hub's rolling monthly count, not unique users or a
quality score. GPU sizes below are **planning classes for bounded, low-batch
BF16 inference**, not measured minimum VRAM or full-context guarantees.

| Priority / model | Evidence and effective context | Why test it | Starting GPU class | HF monthly downloads / likes |
|---|---|---|---:|---:|
| 1. [Intern-Decision-4B](https://huggingface.co/internlm/Intern-Decision-4B) | Text + images; reference runtime defaults to 8,192 combined tokens, rejects overflow; up to 16 questions | Small genuine vision decision model; simultaneous cell/header questions | 24 GB | 2,891 / 83 |
| 2. [Cloudflare Clef-Flash, 9B](https://huggingface.co/Cloudflare/clef-flash) | Text/JSON + images; encoder defaults to 16,384 tokens | Joint question head; compare directly with our hosted Flash results | 32–48 GB | 18,971 / 709 |
| 3. [Perplexity Decider v1.1, 27B](https://huggingface.co/perplexity-ai/pplx-decider-v1.1-27b) | Text + images; reference preparation hard-caps the combined input at 8,192 tokens | Strong hosted candidate on our grouping controls; explicit local image preprocessing | 80 GB | 1,072 / 88 |
| 4. [AutoTrust JEV-27B-VL](https://huggingface.co/autotrust/JEV-27B-VL) | Text + images; server defaults to 32K, supports up to 256K with sufficient memory | Popular vision decision release; broader page/rolling-state evidence | 80 GB; larger for longest context | 1,536,533 / 3,555 |
| 5. [NeoHorse-Jev-4B](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B) | Text + one image; image request cap 12,288 tokens, image budget 1,024; text-state cap 2,048 in native runtime | Alternative decision head/runtime; text/geometry versus image-assisted decisions | 24 GB | 2,597 / 27 |
| 6. [GEV-26B-Decide](https://huggingface.co/autotrust/GEV-26B-Decide) | Text + images; 256K native context, publisher tested through 128K | Gemma mixture of experts: 26B total, about 4B active; different backbone | 80 GB | 909,755 / 2,155 |
| 7. [Cloudflare Clef, 27B](https://huggingface.co/Cloudflare/clef) | Text/JSON + images; encoder defaults to 16,384 tokens | Matched larger sibling for testing whether the joint schema head scales | 80 GB | 12,066 / 1,930 |
| 8. [Bespoke-Nimble-9B](https://huggingface.co/bespokelabs/Bespoke-Nimble-9B) | Text-only reference scorer; 8,192-token prompt cap, up to 255 choices per field | Context-grounded control for glyph strings, geometry and rolling row state | 32–48 GB | 6,405 / 235 |

All eight selected releases declare Apache-2.0. GEV's Gemma 4 base also uses
[Apache-2.0](https://ai.google.dev/gemma/apache_2). The similarly named Nimble
**v3** is a different, noncommercial release and is not this selection. The
Perplexity card still mentions private access, but the live Hub API reported
`private=false` and `gated=false`; verify file access again before provisioning.

## Deployment details that change the experiment

- **Perplexity:** preserve its noncausal full-attention behavior, separate
  decision readout and exactly-once temperature application. A stock causal
  chat loader does not reproduce the evaluated model. Its published image
  evaluation used a 262,144-pixel cap; the current loader permits a higher cap.
  Test that cap independently from our input crop dimensions.
- **Clef / Flash:** use the supplied `joint_schema_model.py` and decision head.
  Its question sharing is particularly relevant to classifying several cells
  against the same region. Generic Hub chat examples are not the reference
  decision workflow.
- **Intern-Decision:** use its shipped Hugging Face engine and calibration.
  It scores placeholder positions without inserting reference answers. That
  engine is its only implemented backend, with up to eight images and 62
  options per question.
- **AutoTrust JEV:** use its decision server and pinned supported vLLM build.
  The card requires a maximum of eight concurrent sequences because larger
  batches can return incorrect decision probabilities. Long context is an
  additional latency/memory experiment, not the initial default.
- **GEV:** its supplied vLLM patch enables the decision-head LoRA. Start with
  `thinking="off"`; the advertised adaptive-thinking score mixes decisions
  with generated reasoning and cannot be ranked as one-pass inference.
- **NeoHorse:** freeze the native image request's actual bounds and ask one
  question per image call initially. Its text and image paths have different
  admission limits.
- **Nimble:** download the adapter plus its pinned base. The helper scores
  fields separately; it does not promise Clef-style shared multi-question work.
  Current release temperature is 1.0, not the older checkpoint's value.

These are runtime contracts and publisher claims, not local validation results.
Community benchmark scores across editions and task mixtures are not pooled
into a synthetic leaderboard here.

## Initial experiment layers

1. **Transport and identity:** pin model/base/code revisions, load without
   training, and verify text-only plus circle/square/blank image controls.
   Record actual image dimensions and processor-produced visual-token counts.
2. **Matched evidence:** reuse frozen DEV source evidence, with geometry/text
   alone and then the same evidence plus a crop. Test fresh 512/768/1024 edges,
   RGB/grayscale/two-bit images separately. Keep question wording fixed first.
3. **Question sharing:** compare one boundary question per call with a shared
   region and several independent questions where supported. Audit that adding
   a distractor question does not corrupt other answers.
4. **Assembly:** compare join/split decisions, row membership, header ownership
   and bounded coordinate edits. Combine the frozen geometry gate with model
   decisions; route from source evidence, never reference labels.
5. **Efficiency:** after a BF16 quality baseline, test batching, prefix reuse
   and supported quantization independently. Runtime prefix reuse is labeled
   separately from provider-reported cache hits in hosted experiments.

The protected silver set remains untouched. Host metrics should include GPU
peak allocation and reserved memory, sampled utilization, CPU time and peak RSS,
plus initialization/download time. Report supplied-region decisions separately
from complete assembled pages. Full-page pages/minute requires timing the whole
pipeline; pages/USD includes paid startup, idle time, storage and teardown.
Until measured, self-hosted quality, pages/minute and pages/USD are **unmeasured**.

## Alternatives and exclusions

[Jev-Omni](https://huggingface.co/akhilaaa3/Jev-Omni) is a useful Apache-2.0
Gemma 4-12B vision alternative (4,287 downloads, 390 likes). Its pinned loader uses
BF16 despite an older FP32 memory statement in the card; a 48 GB GPU is a
reasonable planning class, but the wrapper does not establish a tested long
context limit. [Imajev-4B](https://huggingface.co/mohit67890/imajev-4b) offers a
smaller additional vision candidate with a 4,096-token runtime limit.

[JPT](https://huggingface.co/kirp/jpt-4b) and
[Nimble v3](https://huggingface.co/bespokelabs/Bespoke-Nimble-9B-v3) have
noncommercial release licenses.
[Tev1-4B's card](https://huggingface.co/togethercomputer/Tev1-4B-experimental)
says its fine-tuned release license is pending.
[MiniCPM5-2B-Jev](https://huggingface.co/ytbai/MiniCPM5-2B-Jev) has limited
adoption and a base/head compatibility discrepancy that needs a cold-load check.
[Eval Engine decision-4b](https://huggingface.co/evalengine/decision-4b)
is a compact text option, but its documented 2,048-token
limit makes it less suitable for the larger evidence packets. General-purpose
Qwen or LFM vision models remain separate constrained-output baselines.

## Frozen release identities

| Model | Hub revision |
|---|---|
| Intern-Decision-4B | `0e5e6aa7d6d750e2b1504ba11a8136cb58aeb3cd` |
| Clef-Flash | `fde727a287004204b7518dcc983fe64379776712` |
| Perplexity v1.1 | `6195aa55a72ae21e503c8a60198f7b390d42adb5` |
| JEV-27B-VL | `ba3f0d584994b37998f235c0a3f6f1beff32ba1e` |
| NeoHorse-Jev-4B | `434cb21d3a994a953d3ae5788405fcb2c4970554` |
| GEV-26B-Decide | `7c89590ead085bf77630b4bf68264ea30b6ddc78` |
| Clef | `ed3eed331870db2eff4b0db01237128ede8a00ce` |
| Bespoke-Nimble-9B | `bd792f44ec8e265be861bfcdf4e05967ffe0e858` |

Nimble's specified Qwen3.5-9B base revision is
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Raw public metadata and source snapshots
are retained under ignored council research artifacts, separate from PDF inputs.
