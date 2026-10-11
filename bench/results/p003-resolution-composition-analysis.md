# Fixed vector and resolution-decision compositions

All 75 frozen policy treatments independently replayed and scored. All 25 model/edge arms × three policies were fixed before model outcomes or labels. Every treatment uses the complete same 24 cases. No edge or policy is selected for execution by these scores.

Vector-first PPLX has 17/18 visibly cued matches at 256, 500, 768 and 1024, and 16/18 at 400; its indeterminate answers remain decisive. Vector-first Luna has 17/18 at 400, 500 and 1024 and abstains on all six indeterminate cases. These results include deterministic vector contributions and are not improvements in pure model accuracy. Agreement-only preserves indeterminate abstention for every arm, while classifying fewer cued cases. The table retains all tradeoffs and all lower-scoring policies.


The direct-vector baseline has 14/24 author-label matches, all 14 within the 18 visibly cued cases, 15 classified cases and nine abstentions; it abstains on all six indeterminate cases. It is a distinct deterministic control. Each composition combines that vector evidence with one configured model only, not another model’s fallback. Model-only agreement appears separately below.

Vector-first uses a decisive vector result, otherwise the model; agreement-only classifies only equal decisive evidence; either-evidence uses the sole decisive component or equal decisions and abstains on decisive conflict. Component error/abstention statuses remain in the detailed receipts. Geometry contributions are not credited as pure model decisions. Full24 includes unresolved/errors/unattempted cases; six identical-evidence opposing-label cases are evaluated for abstention, not recoverable hidden-label accuracy.

## All fixed treatments

| Model | Edge | Policy | Model-only agreement /24 | Composite agreement /24 | Cued /18 | Cell/row/wrap /8 | Indeterminate abstained /6 | Classified | Abstained | Decisive conflicts | Component errors |
|---|---:|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| cloudflare/clef | 256 | agreement_only | 14 | 10 | 10 | 5/2/3 | 6 | 10 | 14 | 5 | 0 |
| cloudflare/clef | 256 | either_evidence_conflicts_abstain | 14 | 13 | 10 | 6/3/4 | 0 | 19 | 5 | 5 | 0 |
| cloudflare/clef | 256 | vector_first | 14 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 5 | 0 |
| cloudflare/clef | 400 | agreement_only | 15 | 10 | 10 | 5/2/3 | 6 | 10 | 14 | 5 | 0 |
| cloudflare/clef | 400 | either_evidence_conflicts_abstain | 15 | 14 | 11 | 6/3/5 | 0 | 19 | 5 | 5 | 0 |
| cloudflare/clef | 400 | vector_first | 15 | 18 | 15 | 7/6/5 | 0 | 24 | 0 | 5 | 0 |
| cloudflare/clef | 500 | agreement_only | 15 | 10 | 10 | 4/3/3 | 6 | 10 | 14 | 5 | 0 |
| cloudflare/clef | 500 | either_evidence_conflicts_abstain | 15 | 14 | 11 | 5/4/5 | 0 | 19 | 5 | 5 | 0 |
| cloudflare/clef | 500 | vector_first | 15 | 18 | 15 | 7/6/5 | 0 | 24 | 0 | 5 | 0 |
| cloudflare/clef | 768 | agreement_only | 14 | 10 | 10 | 4/3/3 | 6 | 10 | 14 | 5 | 0 |
| cloudflare/clef | 768 | either_evidence_conflicts_abstain | 14 | 13 | 10 | 5/4/4 | 0 | 19 | 5 | 5 | 0 |
| cloudflare/clef | 768 | vector_first | 14 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 5 | 0 |
| cloudflare/clef | 1024 | agreement_only | 16 | 11 | 11 | 5/3/3 | 6 | 11 | 13 | 4 | 0 |
| cloudflare/clef | 1024 | either_evidence_conflicts_abstain | 16 | 15 | 12 | 6/4/5 | 0 | 20 | 4 | 4 | 0 |
| cloudflare/clef | 1024 | vector_first | 16 | 18 | 15 | 7/6/5 | 0 | 24 | 0 | 4 | 0 |
| cloudflare/clef-flash | 256 | agreement_only | 12 | 8 | 8 | 3/2/3 | 6 | 8 | 16 | 7 | 0 |
| cloudflare/clef-flash | 256 | either_evidence_conflicts_abstain | 12 | 11 | 8 | 4/3/4 | 0 | 17 | 7 | 7 | 0 |
| cloudflare/clef-flash | 256 | vector_first | 12 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 7 | 0 |
| cloudflare/clef-flash | 400 | agreement_only | 14 | 10 | 10 | 3/4/3 | 6 | 10 | 14 | 5 | 0 |
| cloudflare/clef-flash | 400 | either_evidence_conflicts_abstain | 14 | 13 | 10 | 4/5/4 | 0 | 19 | 5 | 5 | 0 |
| cloudflare/clef-flash | 400 | vector_first | 14 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 5 | 0 |
| cloudflare/clef-flash | 500 | agreement_only | 13 | 9 | 9 | 3/3/3 | 6 | 9 | 15 | 6 | 0 |
| cloudflare/clef-flash | 500 | either_evidence_conflicts_abstain | 13 | 12 | 9 | 4/4/4 | 0 | 18 | 6 | 6 | 0 |
| cloudflare/clef-flash | 500 | vector_first | 13 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 6 | 0 |
| cloudflare/clef-flash | 768 | agreement_only | 14 | 10 | 10 | 3/4/3 | 6 | 10 | 14 | 5 | 0 |
| cloudflare/clef-flash | 768 | either_evidence_conflicts_abstain | 14 | 13 | 10 | 4/5/4 | 0 | 19 | 5 | 5 | 0 |
| cloudflare/clef-flash | 768 | vector_first | 14 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 5 | 0 |
| cloudflare/clef-flash | 1024 | agreement_only | 12 | 8 | 8 | 3/2/3 | 6 | 8 | 16 | 7 | 0 |
| cloudflare/clef-flash | 1024 | either_evidence_conflicts_abstain | 12 | 11 | 8 | 4/3/4 | 0 | 17 | 7 | 7 | 0 |
| cloudflare/clef-flash | 1024 | vector_first | 12 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 7 | 0 |
| cloudflare/clef-omni | 256 | agreement_only | 12 | 8 | 8 | 3/2/3 | 6 | 8 | 16 | 7 | 0 |
| cloudflare/clef-omni | 256 | either_evidence_conflicts_abstain | 12 | 11 | 8 | 4/3/4 | 0 | 17 | 7 | 7 | 0 |
| cloudflare/clef-omni | 256 | vector_first | 12 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 7 | 0 |
| cloudflare/clef-omni | 400 | agreement_only | 12 | 8 | 8 | 3/2/3 | 6 | 8 | 16 | 7 | 0 |
| cloudflare/clef-omni | 400 | either_evidence_conflicts_abstain | 12 | 11 | 8 | 4/3/4 | 0 | 17 | 7 | 7 | 0 |
| cloudflare/clef-omni | 400 | vector_first | 12 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 7 | 0 |
| cloudflare/clef-omni | 500 | agreement_only | 12 | 8 | 8 | 3/2/3 | 6 | 8 | 16 | 7 | 0 |
| cloudflare/clef-omni | 500 | either_evidence_conflicts_abstain | 12 | 11 | 8 | 4/3/4 | 0 | 17 | 7 | 7 | 0 |
| cloudflare/clef-omni | 500 | vector_first | 12 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 7 | 0 |
| cloudflare/clef-omni | 768 | agreement_only | 12 | 8 | 8 | 3/2/3 | 6 | 8 | 16 | 7 | 0 |
| cloudflare/clef-omni | 768 | either_evidence_conflicts_abstain | 12 | 11 | 8 | 4/3/4 | 0 | 17 | 7 | 7 | 0 |
| cloudflare/clef-omni | 768 | vector_first | 12 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 7 | 0 |
| cloudflare/clef-omni | 1024 | agreement_only | 12 | 8 | 8 | 3/2/3 | 6 | 8 | 16 | 7 | 0 |
| cloudflare/clef-omni | 1024 | either_evidence_conflicts_abstain | 12 | 11 | 8 | 4/3/4 | 0 | 17 | 7 | 7 | 0 |
| cloudflare/clef-omni | 1024 | vector_first | 12 | 17 | 14 | 7/6/4 | 0 | 24 | 0 | 7 | 0 |
| openai/gpt-6-luna-decisions | 256 | agreement_only | 6 | 5 | 5 | 3/2/0 | 6 | 6 | 18 | 6 | 0 |
| openai/gpt-6-luna-decisions | 256 | either_evidence_conflicts_abstain | 6 | 9 | 9 | 4/3/2 | 6 | 10 | 14 | 6 | 0 |
| openai/gpt-6-luna-decisions | 256 | vector_first | 6 | 15 | 15 | 6/5/4 | 6 | 16 | 8 | 6 | 0 |
| openai/gpt-6-luna-decisions | 400 | agreement_only | 7 | 4 | 4 | 1/3/0 | 6 | 5 | 19 | 9 | 0 |
| openai/gpt-6-luna-decisions | 400 | either_evidence_conflicts_abstain | 7 | 8 | 8 | 2/3/3 | 6 | 9 | 15 | 9 | 0 |
| openai/gpt-6-luna-decisions | 400 | vector_first | 7 | 17 | 17 | 6/5/6 | 6 | 18 | 6 | 9 | 0 |
| openai/gpt-6-luna-decisions | 500 | agreement_only | 7 | 4 | 4 | 2/2/0 | 6 | 5 | 19 | 4 | 0 |
| openai/gpt-6-luna-decisions | 500 | either_evidence_conflicts_abstain | 7 | 13 | 13 | 4/4/5 | 6 | 14 | 10 | 4 | 0 |
| openai/gpt-6-luna-decisions | 500 | vector_first | 7 | 17 | 17 | 6/5/6 | 6 | 18 | 6 | 4 | 0 |
| openai/gpt-6-luna-decisions | 768 | agreement_only | 6 | 4 | 4 | 1/3/0 | 6 | 5 | 19 | 7 | 0 |
| openai/gpt-6-luna-decisions | 768 | either_evidence_conflicts_abstain | 6 | 9 | 9 | 2/5/2 | 6 | 10 | 14 | 7 | 0 |
| openai/gpt-6-luna-decisions | 768 | vector_first | 6 | 16 | 16 | 6/5/5 | 6 | 17 | 7 | 7 | 0 |
| openai/gpt-6-luna-decisions | 1024 | agreement_only | 8 | 5 | 5 | 2/3/0 | 6 | 6 | 18 | 6 | 0 |
| openai/gpt-6-luna-decisions | 1024 | either_evidence_conflicts_abstain | 8 | 11 | 11 | 4/3/4 | 6 | 12 | 12 | 6 | 0 |
| openai/gpt-6-luna-decisions | 1024 | vector_first | 8 | 17 | 17 | 6/5/6 | 6 | 18 | 6 | 6 | 0 |
| perplexity/pplx-decider-v1.1-27b | 256 | agreement_only | 16 | 10 | 10 | 5/4/1 | 6 | 10 | 14 | 4 | 0 |
| perplexity/pplx-decider-v1.1-27b | 256 | either_evidence_conflicts_abstain | 16 | 16 | 13 | 6/5/5 | 0 | 20 | 4 | 4 | 0 |
| perplexity/pplx-decider-v1.1-27b | 256 | vector_first | 16 | 20 | 17 | 7/6/7 | 0 | 24 | 0 | 4 | 0 |
| perplexity/pplx-decider-v1.1-27b | 400 | agreement_only | 19 | 14 | 14 | 6/5/3 | 6 | 15 | 9 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 400 | either_evidence_conflicts_abstain | 19 | 19 | 16 | 7/6/6 | 0 | 24 | 0 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 400 | vector_first | 19 | 19 | 16 | 7/6/6 | 0 | 24 | 0 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 500 | agreement_only | 20 | 14 | 14 | 6/5/3 | 6 | 15 | 9 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 500 | either_evidence_conflicts_abstain | 20 | 20 | 17 | 7/6/7 | 0 | 24 | 0 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 500 | vector_first | 20 | 20 | 17 | 7/6/7 | 0 | 24 | 0 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 768 | agreement_only | 20 | 14 | 14 | 6/5/3 | 6 | 15 | 9 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 768 | either_evidence_conflicts_abstain | 20 | 20 | 17 | 7/6/7 | 0 | 24 | 0 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 768 | vector_first | 20 | 20 | 17 | 7/6/7 | 0 | 24 | 0 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 1024 | agreement_only | 20 | 14 | 14 | 6/5/3 | 6 | 15 | 9 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 1024 | either_evidence_conflicts_abstain | 20 | 20 | 17 | 7/6/7 | 0 | 24 | 0 | 0 | 0 |
| perplexity/pplx-decider-v1.1-27b | 1024 | vector_first | 20 | 20 | 17 | 7/6/7 | 0 | 24 | 0 | 0 | 0 |

## Actual cost and unchanged original protocol

There are 25 original model arms, not 75 paid arms. Charges below are retained original API attempts once per model/edge; they must not be summed over three counterfactual policies. Offline composition makes zero new requests, has no fresh question/page throughput, and measures no actual cost saving. Vector computation is the separately measured existing control. Original strict returned-identifier failures remain unchanged; exact catalog-alias replay is separately labeled and changes no raw probability or usage.

| Original model arm | API attempts | Effective USD once | Original report SHA | Materialization SHA |
|---|---:|---:|---|---|
| synth-clef-resolution-crop1024-r0-c3 | 24 | 0.0098328 | `e5d2fb21ccdd9146c4dcb2d457e17448f0486f5e9034422f886d13a6d708d629` | `c6bbf84a5dd35413fdd895bde8dea393b9d6f4791cf3910d1549e4dfb94a29b4` |
| synth-clef-resolution-crop256-r0-c3 | 24 | 0.0052805 | `fbac706045de7ae0b4f9b6941e0733fd2932d545dd3964dfac6b5b6c231180c5` | `8525763dc1eaf500c16c49337e59721b593f0d53d17663110691002e824b0661` |
| synth-clef-resolution-crop400-r0-c3 | 24 | 0.0055742 | `459e7d534e4ef352972c878ccc55fcbba0b82001c2d9339704a5632803b4ef0e` | `f96da6611cfeb15ac9fb66096fdb556f82f1b49c47801aa5490cb01846dd8a72` |
| synth-clef-resolution-crop500-r0-c3 | 24 | 0.0060638 | `384d9c5759f3ba76d392e409bb1c5ae2ac542ab4dc16d13bd48a7c6449dc1248` | `c62e7cefde7311245e62137e53f32b31de74b8ea5979059ee7388fb4a1125959` |
| synth-clef-resolution-crop768-r0-c3 | 24 | 0.0076306 | `abe270ad81baf4a781c2d31420ab0d719e4b3be5a646b10d05b30b569df3dd7e` | `52ef219d778ae0a097decde19939a40807f52aa93a851f8774cce7da9866e78c` |
| synth-clefflash-resolution-crop1024-r0-c3 | 24 | 0.0015569 | `33305472fd23827ec3ddb6eeb91520b3d29f6875453595aa7beac767cd0e0175` | `ef3a7b0c185457f1aeb7c4038ebe70a1853b3b89f31556b815731b0edd94ef84` |
| synth-clefflash-resolution-crop256-r0-c3 | 24 | 0.0008361 | `3a5e511585838be816bfd5f3f50617cbbed9b52e5eabb11eeab6e9299a7dbc53` | `1c99233e4dba517a4ad4de8d84f18529cea7d99b6d9bf57952163397d63ae391` |
| synth-clefflash-resolution-crop400-r0-c3 | 24 | 0.0008826 | `d9beccb65a9d2a2d3068a1ac544040c760972429e49e555629783d42d67bee7f` | `921709a34a0fb3c55daec336c0fa48de3e6d3bf6789728a88a936c00225fb988` |
| synth-clefflash-resolution-crop500-r0-c3 | 24 | 0.0009601 | `2bc710b77b8ddd840453183ed7751f4006890e039bb4d56121f2a9f342051e57` | `beb29ce1e60d2e654d24c21d5c98f606f5243cc1184c2e9b7d6d907ebce086b2` |
| synth-clefflash-resolution-crop768-r0-c3 | 24 | 0.0012082 | `a89889119ddaa0b6f2e5f79831d98b0f9b7dc9f9029711a8bd07a35930ea79d7` | `e2f4375f3fd70deecddc51794ae7582ce409a2e72b5a9e1296d286344c591ec2` |
| synth-clefomni-resolution-crop1024-r0-c3 | 24 | 0.0061371 | `c30f0d043e16b2e793cbdc08c69ae612be7f4f8d876e68421507a26c3a457bc3` | `e0f4f6b294041e28c8a5a2f5963c43df445d04e489cd14d28b5084726cefe0e6` |
| synth-clefomni-resolution-crop256-r0-c3 | 24 | 0.0032919 | `220892ec6ac37fd9c781438f1219e5ea78e6885a2fba14c4e9f95a7aba51d87d` | `7e4e45a650d001d0108b62935fe4febd18f04a33bd74a4fdfc5c08e51e1d29c7` |
| synth-clefomni-resolution-crop400-r0-c3 | 24 | 0.0034755 | `ac9b7d7e3788ea009036136a97c034105a6e391e0b80b8a07c6832065e733267` | `d4f94867e7232c4c7556e25ecba3933b09addf60db9231fdddf2a806a0fa9064` |
| synth-clefomni-resolution-crop500-r0-c3 | 24 | 0.0037815 | `8eac0a88d229b8022bddd400a84e7ad1c1fc0f6612dbefe6fddc4325d42f4c2e` | `ef880edd69e79724af24df1e527b7d6b9972930196e4ad81fe8bed09df334892` |
| synth-clefomni-resolution-crop768-r0-c3 | 24 | 0.0047607 | `9b2b9943b544ae096e1f9ae0ff8675ab16158a3c501ee58e05455984e0cb1843` | `688574759b775675a47d090d69f30420e2f439454c4d344949fddc11c19021a2` |
| synth-lunadec-resolution-crop1024-r0-c3 | 24 | 0.0035966 | `546f781a9afb8f12d658d10bcf79280e1f28fbe9cfdeca88575bed4382726921` | `93bbc51e823dc34d73f2b39b6ec779d54e5061988b7bbdbf710e224e19b358e5` |
| synth-lunadec-resolution-crop256-r0-c3 | 24 | 0.0016358 | `b199d593f0240f878420f08b4495653b22a381338e203517094561774521a90b` | `a7414a6698badfbaad1a24e2560ee9dd32f7623bbb07dfdbd48c3d16f9f325cd` |
| synth-lunadec-resolution-crop400-r0-c3 | 24 | 0.0018446 | `0b1228dc9b772e6fc6cb0315ff83de1cadebcc467e75ea3664c59412af66297a` | `e9c84058d097f9d4dcb91d41b599045edd504b6e70f001b3c5713474244f0e01` |
| synth-lunadec-resolution-crop500-r0-c3 | 24 | 0.0020326 | `818805094ef4076fe448bbd12a39c7d4f046b27d437085d7ff08954aacc373a1` | `19043e610e54cad54ce2e83f1c83ae652730a5f4c6745b8b86bc99e8d51d7315` |
| synth-lunadec-resolution-crop768-r0-c3 | 24 | 0.0027014 | `3bc7c5fb0f7335ec63f3cd6a21fbc5b8134482cee6b7e38270638dfad58fc2bc` | `3b7f216f776d3469d8bc4463c043e55a12d57d8c6f8a449a932eadcf27ce8c47` |
| synth-pplx-resolution-crop1024-r0-c3 | 24 | 0.0007944 | `93793cf35e50d6094d727b20f8c7823d1825f78cfe3d3a379485f5247c062d6c` | `c1ca95446a15abfc506a711bc89dd0595795c666e98b38db4af615557a54cde3` |
| synth-pplx-resolution-crop256-r0-c3 | 24 | 0.0004151 | `d8ab61cf8d51a6b5aeddcd3f8f5ed730c87d740ec910761137031b6dc3a962c2` | `ced23435266c4345a52601166e5a38ef5d3f580310b0b18799de0d2c3fb42471` |
| synth-pplx-resolution-crop400-r0-c3 | 24 | 0.0004396 | `f8d7071b721a093cd8350dfe274475b3f0b29d38af4cbc014fefc87c740c57ed` | `ed57f3e16b95783c7309b5761e134ac3d1cd0962f78092a34884ff817014dded` |
| synth-pplx-resolution-crop500-r0-c3 | 24 | 0.0004804 | `df30336df4da62cd9d442a6069d0d6144963d7fa602d7849321178a7c9c96adf` | `a046356c4896c83a3da73d61d34e5cdc72c955191304f1c68117f1a4bbaa42a7` |
| synth-pplx-resolution-crop768-r0-c3 | 24 | 0.0006109 | `85d3f4cbae42b20ea60e2cfd88d79d9c6c481b708c7e8c0af916c95d83fc0a19` | `229f0fa181f2b89d6ec0fa0b4b31e25d9020b140a0c05ef60fae8c5a17416bd2` |

## Verification and interpretation

Independent replay pins the approved composition plan and both executed pure composition helpers, then authenticates original source and replays all vector receipts. It checks all 75 model/edge/policy declarations against the frozen queue, re-renders actual source crop pixels, reconstructs native transmitted bodies, authenticates raw response identities/alias authorities/accounting, and rebuilds all three 24-case policy outputs byte-for-byte before labels are opened. Original protocol status is preserved per case.

Preparation SHA `703f4f208b28b14e5b70086134ac9f7ab713a726a870ae3c9b4b476cd55c7efc`; independent authority SHA `3045ef61365bfa6673596128ccc4cd6225d77f99185cb54b2d240dc42ad0f5d8`. Evaluation-only gold SHA `db0f5953579379fbf74ffba9faebf8c6acad1e622b70c4fae389d137d357e2ca` is unchanged. Each materialized arm retains a separate `independent-evaluation.json` beside immutable `original-verification.json` and fixed results.

These are single-run reused-case counterfactuals, not 75 independent quality samples or a stable edge ranking. All outcomes remain separate from pure model quality, no combined probability is synthesized, and no claim of source assignment/table extraction follows. Fresh48 references do not inform these rules or controls.
