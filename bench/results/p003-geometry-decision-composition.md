# Frozen geometry and decision compositions

All 30 offline composition arms are prepared without opening private labels: five independently configured image models, each at crop edges 128 and 512, crossed with three fixed policies. Every arm retains all 24 synthetic cases. The models are PPLX, Clef, Clef Flash, Clef Omni, and Luna Decisions; all retained model requests used text geometry plus their actual source crop. There is no cross-model fallback, new hosted call, GPU work, or source modification.

The policies are fixed before scoring:

- `vector_first`: retain a decisive vector-rule choice; only when vector rules abstain use that same model's decisive choice. A vector source failure is not replaced.
- `agreement_only`: retain a choice only when both components are decisive and equal; otherwise abstain.
- `either_evidence_conflicts_abstain`: retain one available decisive choice or equal decisive choices; abstain on conflicts. Component failures remain explicit even when the other component supplies a choice.

No probabilities are combined or calibrated. Each result retains the vector and model statuses/choices, original strict model status, unchanged raw model probabilities, response hash, selected component, conflict flag, and reason. Decisions never inspect author memberships, expected labels, scored reports, or image-model identities as routing evidence.

Preparation independently authenticates the complete source pool, all PDFs/renders/packets, external runtime maps, exact retained request/response/accounting receipts, and all vector outcomes. It then uses only the finite approved catalog alias replay: original strict failures remain immutable; only exact attested response model IDs are normalized before the unchanged strict parser. No rank, choice, or probability is altered.

The prepared artifact is `pipeline-p003/geometry-decision-composition-v2`. It freezes 720 result receipts, ten original model run inventories, complete vector/model components, source evidence, and 29 current code files. This artifact supersedes the initial preparation receipt for approval; the initial directory remains unchanged. The final inventory explicitly includes canonical requests, wire requests/encoded bodies, raw responses, and outcomes.

Unscored decisive counts:

| Model | Crop edge | Vector first | Agreement only | Either evidence, conflicts abstain |
| --- | ---: | ---: | ---: | ---: |
| PPLX | 128 | 24 | 10 | 20 |
| PPLX | 512 | 24 | 15 | 24 |
| Clef | 128 | 24 | 9 | 18 |
| Clef | 512 | 24 | 9 | 18 |
| Clef Flash | 128 | 24 | 11 | 20 |
| Clef Flash | 512 | 24 | 9 | 18 |
| Clef Omni | 128 | 24 | 8 | 17 |
| Clef Omni | 512 | 24 | 8 | 17 |
| Luna Decisions | 128 | 19 | 5 | 12 |
| Luna Decisions | 512 | 17 | 5 | 11 |

These counts describe retained choices, not accuracy. Root must independently approve the code/source receipts before evaluation opens separately hashed labels. The planned evaluation reports every arm on all 24 cases, 18 visually cued cases, six indeterminate cases, and each relationship kind. No winner is selected or used to change these policies.

All original calls actually occurred. Actual retained charges and durations remain attached once to each of ten unique original model runs; reused policy charges must not be summed 30 times. The vector-first policy would hypothetically suppress 15 model calls per arm because the vector control was decisive on 15 cases. This is a counterfactual request count, not actual savings; no savings amount or fresh throughput is reported.

Final receipts:

- Freeze: `0f5b3e905645ec1c18e9c9eb3406c114d57390baf0efc43c50a6765637965bc4`.
- Plan/results: `4814c38ed11f7ef652a12ab87812916d81c05a925fe9b57dc6a82fab588a5f5d`.
- Components: `6b110437b5553e5b8c8f143a46b5796ecf2a0e174353e1826ecc183d86a000f5`.
- Source evidence: `875187117a87f12100ad3282714bef8235db18b907cad8b2e43e67687efeab0a`.
- Composition helper: `56d64b803f3d30504d9b2bfaf723cab26ab09e114284ad24fe4dfb56b7305a56`.
- Approved original 48-arm plan: `79d165e01c20459fdc597ef62d5728f2cfa1ff5b9ed1089ebb812041e6d9549c`.
- Approved aliases: `2611b9db728544889bbcce3779d74452c0fe6e46f1a5c66aa3b3487ed827e068`.

Preparation took 8.21 seconds wall and 5.50 seconds process CPU, including full source rendering and output replay. Unsampled lifetime peak RSS was 619,564 KiB, including imports. It used one Python process, two Rayon threads, and one OpenMP/BLAS/MKL thread. Eight tests verify all policies, conflicts/abstentions/failures, source identity, strict decisive payloads, retained alias provenance, and unchanged input receipts. Ruff and targeted mypy pass.
