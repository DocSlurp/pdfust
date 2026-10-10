# P003 decision-model progress

These tables read completed independently verified DEV evaluations. All intended pages remain in quality/error denominators. Single runs do not establish hosted repeat confidence. Historical candidate generation and newly measured incremental work are separate.

Primary candidate quality includes only model-selected complete crop states. Abstained, failed and identical no-question regions receive no model credit; full intended denominators remain. Historical retained pipeline quality follows separately.

| Run | Model-confirmed strict cells | Complete tables | Missing tables | Extra tables | Negative FP | Decision quality errors | Exact positive pages |
| --- | --- | --- | --- | --- | --- | --- | --- |
| choice-pplx-128-rgb-r2-c6 | 984/2333 | 5/53 | 27 | 0 | 0/4 | 0 | 3 |
| choice-pplx-128-rgb-blank-r0-c6 | 11/2333 | 0/53 | 51 | 0 | 0/4 | 0 | 0 |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | 2/2333 | 0/53 | 52 | 0 | 0/4 | 0 | 0 |
| choice-pplx-512-rgb_palette16-r2-c6 | 981/2333 | 5/53 | 26 | 0 | 0/4 | 0 | 3 |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | 979/2333 | 3/53 | 28 | 0 | 0/4 | 0 | 1 |
| choice-pplx-1024-rgb-r2-c6 | 294/2333 | 4/53 | 38 | 0 | 0/4 | 0 | 3 |
| choice-pplx-400-rgb-seed19-r0-c6 | 1081/2333 | 5/53 | 26 | 3 | 0/4 | 0 | 3 |
| choice-pplx-1024-rgb_palette16-r2-c6 | 294/2333 | 4/53 | 38 | 0 | 0/4 | 0 | 3 |
| choice-pplx-500-rgb_palette16-r0-c6 | 980/2333 | 5/53 | 27 | 0 | 0/4 | 0 | 3 |
Retained pipeline output quality (including historical fallback outputs):

Successful incremental ownership composition, including deterministic geometry and protected source. Failed, skipped and no-question baseline pages receive no composition credit. This is not model-only attribution.

| Run | Composed strict cells | Complete tables | Missing / extra | Negative FP | Incremental failures |
| --- | --- | --- | --- | --- | --- |
| ownership-hybrid-pplx-neighbors-r0-c6 | 268/2333 | 3/53 | 39 / 1 | 0/4 | 1 |
| ownership-allwords-pplx-compact-r0-c6 | 200/2333 | 1/53 | 39 / 0 | 0/4 | 1 |
| ownership-allwords-jev-neighbors-r0-c6 | 49/2333 | 1/53 | 33 / 5 | 0/4 | 2 |
| ownership-direct-jev-neighbors-r0-c6 | 245/2333 | 3/53 | 41 / 1 | 0/4 | 2 |
| ownership-allwords-pplx-neighbors-r0-c6 | 208/2333 | 2/53 | 39 / 0 | 0/4 | 1 |
| ownership-allwords-jev-compact-r0-c6 | 38/2333 | 1/53 | 43 / 1 | 0/4 | 4 |
| ownership-direct-tev-neighbors-r0-c6 | 249/2333 | 3/53 | 39 / 1 | 0/4 | 1 |
| ownership-direct-pplx-neighbors-r0-c6 | 252/2333 | 3/53 | 39 / 1 | 0/4 | 1 |
| ownership-direct-d1-bands-r0-c6 | 249/2333 | 3/53 | 39 / 1 | 0/4 | 1 |
| ownership-direct-jev-bands-r0-c6 | 250/2333 | 3/53 | 39 / 1 | 0/4 | 1 |
| ownership-direct-luna-bands-r0-c6 | 242/2333 | 3/53 | 39 / 1 | 0/4 | 1 |
| ownership-direct-d1-neighbors-r0-c6 | 249/2333 | 3/53 | 39 / 1 | 0/4 | 1 |
Legacy retained pipeline output quality follows separately.

| Run | Model | Treatment | Outputs/intended | Errors | Complete tables | Strict cells | Text cells | Structure cells | Missing tables | Extra tables | Negative FP | Exact positive pages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| choice-pplx-128-rgb-r2-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=128 | 16/16 | 0 | 5/53 | 1087/2333 | 1098 | 1267 | 26 | 3 | 0/4 | 3 |
| ownership-hybrid-pplx-neighbors-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_topology_source, geometry_first=True, chunked_inventory=True, topology_evidence=neighbors, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 3/53 | 370/2333 | 383 | 465 | 38 | 1 | 0/4 | 2 |
| ownership-allwords-pplx-compact-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_topology_source, chunked_inventory=True, topology_evidence=compact, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 1/53 | 302/2333 | 315 | 465 | 38 | 0 | 0/4 | 1 |
| ownership-allwords-jev-neighbors-r0-c6 | typesafe/jev-1.13 | processor=p003_topology_source, chunked_inventory=True, topology_evidence=neighbors, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 1/53 | 126/2333 | 126 | 1045 | 30 | 5 | 0/4 | 1 |
| choice-pplx-128-rgb-blank-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=128, image_visibility=blank | 16/16 | 0 | 3/53 | 784/2333 | 795 | 1045 | 30 | 5 | 0/4 | 2 |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=512, image_mode=rgb_palette16, image_visibility=blank | 16/16 | 0 | 3/53 | 784/2333 | 795 | 1045 | 30 | 5 | 0/4 | 2 |
| ownership-direct-jev-neighbors-r0-c6 | typesafe/jev-1.13 | processor=p003_topology_source, geometry_first=True, ownership_protocol=direct_cell, chunked_inventory=True, topology_evidence=neighbors, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 3/53 | 358/2333 | 371 | 465 | 38 | 1 | 0/4 | 2 |
| natural64-crops-sonnet-1024-legacy-r0-c6 | anthropic/claude-sonnet-5.5 | processor=vision_regions, preset=vision_regions, transcription_representation=legacy, image_edge=1024, gate_image=True | 64/64 | 0 | 14/93 | 1839/3847 | 1851 | 2505 | 34 | 4 | 1/24 | 9 |
| gate-clefomni-128-rgb_palette16-compact-region-r0-c6 | cloudflare/clef-omni | processor=p003_gate, gate_image=True, gate_image_edge=128, gate_packet=compact, gate_image_mode=rgb_palette16, gate_instructions=region | 16/16 | 0 | 1/53 | 280/2333 | 293 | 333 | 44 | 1 | 0/4 | 0 |
| ownership-allwords-pplx-neighbors-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_topology_source, chunked_inventory=True, topology_evidence=neighbors, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 2/53 | 310/2333 | 323 | 465 | 38 | 0 | 0/4 | 1 |
| ownership-allwords-jev-compact-r0-c6 | typesafe/jev-1.13 | processor=p003_topology_source, chunked_inventory=True, topology_evidence=compact, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 2/53 | 242/2333 | 255 | 448 | 39 | 2 | 0/4 | 2 |
| gate-clef-128-rgb_palette16-compact-region-r0-c6 | cloudflare/clef | processor=p003_gate, gate_image=True, gate_image_edge=128, gate_packet=compact, gate_image_mode=rgb_palette16, gate_instructions=region | 16/16 | 0 | 3/53 | 384/2333 | 397 | 465 | 38 | 1 | 0/4 | 2 |
| ownership-direct-tev-neighbors-r0-c6 | togethercomputer/tev1-4b-experimental | processor=p003_topology_source, geometry_first=True, ownership_protocol=direct_cell, chunked_inventory=True, topology_evidence=neighbors, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 3/53 | 351/2333 | 364 | 465 | 38 | 1 | 0/4 | 2 |
| ownership-direct-pplx-neighbors-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_topology_source, geometry_first=True, ownership_protocol=direct_cell, chunked_inventory=True, topology_evidence=neighbors, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 3/53 | 354/2333 | 367 | 465 | 38 | 1 | 0/4 | 2 |
| choice-pplx-512-rgb_palette16-r2-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=512, image_mode=rgb_palette16 | 16/16 | 0 | 5/53 | 981/2333 | 981 | 1287 | 26 | 0 | 0/4 | 3 |
| ownership-direct-d1-bands-r0-c6 | liquid/d1 | processor=p003_topology_source, geometry_first=True, ownership_protocol=direct_cell, chunked_inventory=True, topology_evidence=bands, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 3/53 | 351/2333 | 364 | 465 | 38 | 1 | 0/4 | 2 |
| screen-crops-luna-1024-pinned-r3-c6 | openai/gpt-6-luna | processor=vision_regions, preset=vision_regions, transcription_representation=legacy, image_edge=1024, gate_image=True | 15/16 | 1 | 3/53 | 278/2333 | 278 | 361 | 39 | 0 | 0/4 | 2 |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=128, image_mode=rgb_palette16 | 16/16 | 0 | 4/53 | 1086/2333 | 1097 | 1267 | 26 | 3 | 0/4 | 2 |
| choice-pplx-1024-rgb-r2-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=1024 | 16/16 | 0 | 4/53 | 685/2333 | 685 | 1065 | 30 | 2 | 0/4 | 3 |
| ownership-direct-jev-bands-r0-c6 | typesafe/jev-1.13 | processor=p003_topology_source, geometry_first=True, ownership_protocol=direct_cell, chunked_inventory=True, topology_evidence=bands, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 3/53 | 352/2333 | 365 | 465 | 38 | 1 | 0/4 | 2 |
| screen-crops-luna-1024-matrix-strict-r0-c6 | openai/gpt-6-luna | processor=vision_regions, preset=vision_regions, transcription_representation=matrix_strict, image_edge=1024, gate_image=True | 15/16 | 1 | 3/53 | 290/2333 | 290 | 361 | 39 | 0 | 0/4 | 2 |
| choice-pplx-400-rgb-seed19-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=400 | 16/16 | 0 | 5/53 | 1081/2333 | 1092 | 1267 | 26 | 3 | 0/4 | 3 |
| gate-pplx-400-rgb_palette16-compact-region-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_gate, gate_image=True, gate_image_edge=400, gate_packet=compact, gate_image_mode=rgb_palette16, gate_instructions=region | 16/16 | 0 | 3/53 | 384/2333 | 397 | 465 | 38 | 1 | 0/4 | 2 |
| ownership-direct-luna-bands-r0-c6 | openai/gpt-6-luna-decisions | processor=p003_topology_source, geometry_first=True, ownership_protocol=direct_cell, chunked_inventory=True, topology_evidence=bands, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 3/53 | 344/2333 | 357 | 465 | 38 | 1 | 0/4 | 2 |
| choice-pplx-1024-rgb_palette16-r2-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=1024, image_mode=rgb_palette16 | 16/16 | 0 | 4/53 | 685/2333 | 685 | 1065 | 30 | 2 | 0/4 | 3 |
| gate-pplx-1024-grayscale8-compact-region-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_gate, gate_image=True, gate_image_edge=1024, gate_packet=compact, gate_image_mode=grayscale8, gate_instructions=region | 16/16 | 0 | 3/53 | 384/2333 | 397 | 465 | 38 | 1 | 0/4 | 2 |
| ownership-direct-d1-neighbors-r0-c6 | liquid/d1 | processor=p003_topology_source, geometry_first=True, ownership_protocol=direct_cell, chunked_inventory=True, topology_evidence=neighbors, boundary_words=residual, crossed_tables=residual_prose | 16/16 | 0 | 3/53 | 351/2333 | 364 | 465 | 38 | 1 | 0/4 | 2 |
| screen-crops-haiku-1024-atomic-cells-r0-c6 | anthropic/claude-haiku-5.5 | processor=vision_regions, preset=vision_regions, transcription_representation=atomic_cells, image_edge=1024, gate_image=True | 14/16 | 2 | 2/53 | 358/2333 | 370 | 422 | 40 | 0 | 0/4 | 2 |
| choice-pplx-500-rgb_palette16-r0-c6 | perplexity/pplx-decider-v1.1-27b | processor=p003_candidate_choice, image_edge=500, image_mode=rgb_palette16 | 16/16 | 0 | 5/53 | 1083/2333 | 1094 | 1267 | 26 | 3 | 0/4 | 3 |

Fresh model decisions are separate from retained pipeline outputs. A valid unresolved response is an abstention, not a model-selected output. Served model version aliases are retained as provenance; they alone do not establish model substitution.

| Run | Fresh attempts | Returned calls | Parsed selected choices | Parsed abstentions | Committed model crops | Fully chosen candidate pages | Pages retaining output on abstention | Requested-model mismatches | Explicit retry attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| choice-pplx-128-rgb-r2-c6 | 16 | 16 | 15 | 1 | 15 | 10 | 1 | 0 | 0 |
| ownership-hybrid-pplx-neighbors-r0-c6 | 172 | 172 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| ownership-allwords-pplx-compact-r0-c6 | 250 | 250 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| ownership-allwords-jev-neighbors-r0-c6 | 163 | 163 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| choice-pplx-128-rgb-blank-r0-c6 | 16 | 16 | 2 | 14 | 2 | 0 | 11 | 0 | 0 |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | 16 | 16 | 1 | 15 | 1 | 0 | 11 | 0 | 0 |
| ownership-direct-jev-neighbors-r0-c6 | 99 | 99 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| gate-clefomni-128-rgb_palette16-compact-region-r0-c6 | 18 | 18 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| ownership-allwords-pplx-neighbors-r0-c6 | 253 | 253 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| ownership-allwords-jev-compact-r0-c6 | 154 | 154 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| gate-clef-128-rgb_palette16-compact-region-r0-c6 | 18 | 18 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| ownership-direct-tev-neighbors-r0-c6 | 99 | 99 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| ownership-direct-pplx-neighbors-r0-c6 | 99 | 99 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| choice-pplx-512-rgb_palette16-r2-c6 | 16 | 16 | 16 | 0 | 16 | 11 | 0 | 0 | 0 |
| ownership-direct-d1-bands-r0-c6 | 99 | 99 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | 16 | 16 | 14 | 2 | 14 | 9 | 2 | 0 | 0 |
| choice-pplx-1024-rgb-r2-c6 | 16 | 16 | 15 | 1 | 15 | 10 | 1 | 0 | 0 |
| ownership-direct-jev-bands-r0-c6 | 99 | 99 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| choice-pplx-400-rgb-seed19-r0-c6 | 16 | 16 | 16 | 0 | 16 | 11 | 0 | 0 | 0 |
| gate-pplx-400-rgb_palette16-compact-region-r0-c6 | 18 | 18 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| ownership-direct-luna-bands-r0-c6 | 99 | 99 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| choice-pplx-1024-rgb_palette16-r2-c6 | 16 | 16 | 15 | 1 | 15 | 10 | 1 | 0 | 0 |
| gate-pplx-1024-grayscale8-compact-region-r0-c6 | 18 | 18 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| ownership-direct-d1-neighbors-r0-c6 | 99 | 99 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 0 | 0 |
| choice-pplx-500-rgb_palette16-r0-c6 | 16 | 16 | 15 | 1 | 15 | 10 | 1 | 0 | 0 |

Full-pipeline rates count verified operational outputs. Cost overlays leave original report costs visible. Transport concurrency is part of the treatment; contended runs are separate evidence.

| Run | Measured scope | Transport | Pages/min | Original pages/APIUSD | Original effective USD | Original accounted incl reserves USD | Reconciled effective USD | Reconciled pages/APIUSD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| choice-pplx-128-rgb-r2-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00059822 | 0.00059822 | Unmeasured | Unmeasured |
| ownership-hybrid-pplx-neighbors-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.299019 | 0.299019 | Unmeasured | Unmeasured |
| ownership-allwords-pplx-compact-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.239364 | 0.239364 | Unmeasured | Unmeasured |
| ownership-allwords-jev-neighbors-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.119725 | 0.119725 | Unmeasured | Unmeasured |
| choice-pplx-128-rgb-blank-r0-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00059822 | 0.00059822 | Unmeasured | Unmeasured |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00061408 | 0.00061408 | Unmeasured | Unmeasured |
| ownership-direct-jev-neighbors-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.115492 | 0.115492 | Unmeasured | Unmeasured |
| natural64-crops-sonnet-1024-legacy-r0-c6 | complete pipeline | contended (3) | 3.19658 | 140.427 | 0.455752 | 0.455752 | Unmeasured | Unmeasured |
| gate-clefomni-128-rgb_palette16-compact-region-r0-c6 | incremental admission conditional on frozen generation | contended (3) | Unmeasured | Unmeasured | 0.00602025 | 0.00602025 | Unmeasured | Unmeasured |
| ownership-allwords-pplx-neighbors-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.319352 | 0.319352 | Unmeasured | Unmeasured |
| ownership-allwords-jev-compact-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.110234 | 0.110234 | Unmeasured | Unmeasured |
| gate-clef-128-rgb_palette16-compact-region-r0-c6 | incremental admission conditional on frozen generation | contended (3) | Unmeasured | Unmeasured | 0.0096144 | 0.0096144 | Unmeasured | Unmeasured |
| ownership-direct-tev-neighbors-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 1.34599 | 1.34599 | Unmeasured | Unmeasured |
| ownership-direct-pplx-neighbors-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.655465 | 0.655465 | Unmeasured | Unmeasured |
| choice-pplx-512-rgb_palette16-r2-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00061408 | 0.00061408 | Unmeasured | Unmeasured |
| ownership-direct-d1-bands-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.996754 | 0.996754 | Unmeasured | Unmeasured |
| screen-crops-luna-1024-pinned-r3-c6 | complete pipeline | contended (3) | 1.80164 | 1379.14 | 0.0108763 | 0.0108763 | Unmeasured | Unmeasured |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00059822 | 0.00059822 | Unmeasured | Unmeasured |
| choice-pplx-1024-rgb-r2-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.0007292 | 0.0007292 | Unmeasured | Unmeasured |
| ownership-direct-jev-bands-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.14478 | 0.14478 | Unmeasured | Unmeasured |
| screen-crops-luna-1024-matrix-strict-r0-c6 | complete pipeline | contended (3) | 1.88283 | 1238.75 | 0.012109 | 0.012109 | Unmeasured | Unmeasured |
| choice-pplx-400-rgb-seed19-r0-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00060236 | 0.00060236 | Unmeasured | Unmeasured |
| gate-pplx-400-rgb_palette16-compact-region-r0-c6 | incremental admission conditional on frozen generation | contended (3) | Unmeasured | Unmeasured | 0.00078874 | 0.00078874 | Unmeasured | Unmeasured |
| ownership-direct-luna-bands-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.229366 | 0.229366 | Unmeasured | Unmeasured |
| choice-pplx-1024-rgb_palette16-r2-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.0007292 | 0.0007292 | Unmeasured | Unmeasured |
| gate-pplx-1024-grayscale8-compact-region-r0-c6 | incremental admission conditional on frozen generation | contended (3) | Unmeasured | Unmeasured | 0.00089958 | 0.00089958 | Unmeasured | Unmeasured |
| ownership-direct-d1-neighbors-r0-c6 | incremental ownership conditional on frozen topology and source | contended (3) | Unmeasured | Unmeasured | 0.755455 | 0.755455 | Unmeasured | Unmeasured |
| screen-crops-haiku-1024-atomic-cells-r0-c6 | complete pipeline | contended (3) | 1.93653 | 750.119 | 0.0186637 | 0.0186637 | Unmeasured | Unmeasured |
| choice-pplx-500-rgb_palette16-r0-c6 | incremental ranking on retained candidates | contended (3) | Unmeasured | Unmeasured | 0.00061344 | 0.00061344 | Unmeasured | Unmeasured |

Incremental processing rates exclude historical baseline generation.

| Run | Repair attempted pages/min | Repair attempted pages/APIUSD | Ranking processed pages/min | Ranking processed pages/APIUSD |
| --- | --- | --- | --- | --- |
| choice-pplx-128-rgb-r2-c6 | Unmeasured | Unmeasured | 4.82867 | 26746 |
| ownership-hybrid-pplx-neighbors-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| ownership-allwords-pplx-compact-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| ownership-allwords-jev-neighbors-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| choice-pplx-128-rgb-blank-r0-c6 | Unmeasured | Unmeasured | 3.93995 | 26746 |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | Unmeasured | Unmeasured | 4.15112 | 26055.2 |
| ownership-direct-jev-neighbors-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| gate-clefomni-128-rgb_palette16-compact-region-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| ownership-allwords-pplx-neighbors-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| ownership-allwords-jev-compact-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| gate-clef-128-rgb_palette16-compact-region-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| ownership-direct-tev-neighbors-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| ownership-direct-pplx-neighbors-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| choice-pplx-512-rgb_palette16-r2-c6 | Unmeasured | Unmeasured | 4.99498 | 26055.2 |
| ownership-direct-d1-bands-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | Unmeasured | Unmeasured | 5.45697 | 26746 |
| choice-pplx-1024-rgb-r2-c6 | Unmeasured | Unmeasured | 4.57997 | 21941.9 |
| ownership-direct-jev-bands-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| choice-pplx-400-rgb-seed19-r0-c6 | Unmeasured | Unmeasured | 3.25924 | 26562.2 |
| gate-pplx-400-rgb_palette16-compact-region-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| ownership-direct-luna-bands-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| choice-pplx-1024-rgb_palette16-r2-c6 | Unmeasured | Unmeasured | 5.71603 | 21941.9 |
| gate-pplx-1024-grayscale8-compact-region-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| ownership-direct-d1-neighbors-r0-c6 | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| choice-pplx-500-rgb_palette16-r0-c6 | Unmeasured | Unmeasured | 4.19307 | 26082.4 |

CPU/RSS observations retain their process scopes; worker RSS peaks are never added to parent peaks.

| Run | Process | Wall seconds | CPU seconds | Peak RSS bytes | Measurement scope/evidence |
| --- | --- | --- | --- | --- | --- |
| choice-pplx-128-rgb-r2-c6 | parent | 198.813 | 32.6289 | 294703104 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-hybrid-pplx-neighbors-r0-c6 | parent | 1123.55 | 235.843 | 356765696 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-allwords-pplx-compact-r0-c6 | parent | 1255.73 | 330.87 | 208302080 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-allwords-jev-neighbors-r0-c6 | parent | 673.72 | 213.771 | 204759040 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| choice-pplx-128-rgb-blank-r0-c6 | parent | 243.658 | 32.6765 | 313888768 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | parent | 231.263 | 33.0428 | 292552704 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-direct-jev-neighbors-r0-c6 | parent | 411.85 | 129.165 | 367968256 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| natural64-crops-sonnet-1024-legacy-r0-c6 | parent | 1201.28 | 101.401 | 648187904 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| natural64-crops-sonnet-1024-legacy-r0-c6 | detector worker initialization | 2.9207 | 5.68702 | 1083977728 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| natural64-crops-sonnet-1024-legacy-r0-c6 | detector worker request intervals | 25.0084 | 83.6586 | 1208545280 | 64 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| gate-clefomni-128-rgb_palette16-compact-region-r0-c6 | parent | 176.874 | 27.5258 | 308449280 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-allwords-pplx-neighbors-r0-c6 | parent | 1757.82 | 343.361 | 213069824 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-allwords-jev-compact-r0-c6 | parent | 580.785 | 194.334 | 207323136 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| gate-clef-128-rgb_palette16-compact-region-r0-c6 | parent | 186.822 | 26.7531 | 319049728 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-direct-tev-neighbors-r0-c6 | parent | 605.384 | 138.529 | 369840128 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-direct-pplx-neighbors-r0-c6 | parent | 922.98 | 139.4 | 370778112 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| choice-pplx-512-rgb_palette16-r2-c6 | parent | 192.193 | 33.3596 | 299630592 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-direct-d1-bands-r0-c6 | parent | 422.674 | 144.841 | 369356800 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-luna-1024-pinned-r3-c6 | parent | 499.545 | 32.7216 | 418418688 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-luna-1024-pinned-r3-c6 | detector worker initialization | 5.43263 | 12.0874 | 1065205760 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| screen-crops-luna-1024-pinned-r3-c6 | detector worker request intervals | 6.45866 | 21.3384 | 1153728512 | 16 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | parent | 175.922 | 29.6344 | 299847680 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| choice-pplx-1024-rgb-r2-c6 | parent | 209.608 | 31.4422 | 297259008 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-direct-jev-bands-r0-c6 | parent | 431.429 | 145.98 | 369078272 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-luna-1024-matrix-strict-r0-c6 | parent | 478.004 | 35.4668 | 419934208 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-luna-1024-matrix-strict-r0-c6 | detector worker initialization | 3.58573 | 9.07338 | 1088380928 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| screen-crops-luna-1024-matrix-strict-r0-c6 | detector worker request intervals | 7.40917 | 22.7323 | 1204756480 | 16 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| choice-pplx-400-rgb-seed19-r0-c6 | parent | 294.547 | 33.2362 | 298274816 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| gate-pplx-400-rgb_palette16-compact-region-r0-c6 | parent | 227.272 | 28.3619 | 323043328 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-direct-luna-bands-r0-c6 | parent | 562.23 | 151.718 | 369606656 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| choice-pplx-1024-rgb_palette16-r2-c6 | parent | 167.949 | 36.2092 | 297242624 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| gate-pplx-1024-grayscale8-compact-region-r0-c6 | parent | 192.388 | 30.7809 | 319315968 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| ownership-direct-d1-neighbors-r0-c6 | parent | 479.969 | 143.838 | 368246784 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-haiku-1024-atomic-cells-r0-c6 | parent | 433.766 | 34.2124 | 418062336 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |
| screen-crops-haiku-1024-atomic-cells-r0-c6 | detector worker initialization | 2.92761 | 5.77502 | 1094819840 | Child worker process_time CPU; own /proc/self/statm RSS every 100 ms plus endpoints; getrusage lifetime peak RSS; no parent or subprocess usage included |
| screen-crops-haiku-1024-atomic-cells-r0-c6 | detector worker request intervals | 5.67464 | 19.4085 | 1202495488 | 16 retained single-worker request intervals; sum recorded interval wall/CPU; max sampled RSS. Separate CPU worker subprocess; parent process CPU/RSS excludes worker. Do not sum RSS peaks or overlapping parent per-page CPU intervals. |
| choice-pplx-500-rgb_palette16-r0-c6 | parent | 228.949 | 33.4105 | 292929536 | psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses |

Provider cache counters are unmeasured in these evaluation-only inputs unless explicitly retained as provider-reported usage. No local replay or cache-hit claim is inferred from latency or cost.

| Run | Cache scope | Observed returned/all attempts | Reported read tokens subtotal | Reported write tokens subtotal | Read counter missing calls | Write counter missing calls | All-attempt usage coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| choice-pplx-128-rgb-r2-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-128-rgb-r2-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-128-rgb-r2-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |
| ownership-hybrid-pplx-neighbors-r0-c6 | current measured stage | 172/172 | Unmeasured | Unmeasured | 172 | 172 | True |
| ownership-hybrid-pplx-neighbors-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-hybrid-pplx-neighbors-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| ownership-allwords-pplx-compact-r0-c6 | current measured stage | 250/250 | Unmeasured | Unmeasured | 250 | 250 | True |
| ownership-allwords-pplx-compact-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-allwords-pplx-compact-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| ownership-allwords-jev-neighbors-r0-c6 | current measured stage | 163/163 | Unmeasured | Unmeasured | 163 | 163 | True |
| ownership-allwords-jev-neighbors-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-allwords-jev-neighbors-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-128-rgb-blank-r0-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-128-rgb-blank-r0-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-128-rgb-blank-r0-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-512-rgb_palette16-blank-r0-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |
| ownership-direct-jev-neighbors-r0-c6 | current measured stage | 99/99 | Unmeasured | Unmeasured | 99 | 99 | True |
| ownership-direct-jev-neighbors-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-jev-neighbors-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| natural64-crops-sonnet-1024-legacy-r0-c6 | current measured stage | 56/56 | 0 | 0 | 0 | 0 | True |
| gate-clefomni-128-rgb_palette16-compact-region-r0-c6 | current measured stage | 18/18 | Unmeasured | Unmeasured | 18 | 18 | True |
| gate-clefomni-128-rgb_palette16-compact-region-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-allwords-pplx-neighbors-r0-c6 | current measured stage | 253/253 | Unmeasured | Unmeasured | 253 | 253 | True |
| ownership-allwords-pplx-neighbors-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-allwords-pplx-neighbors-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| ownership-allwords-jev-compact-r0-c6 | current measured stage | 154/154 | Unmeasured | Unmeasured | 154 | 154 | True |
| ownership-allwords-jev-compact-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-allwords-jev-compact-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| gate-clef-128-rgb_palette16-compact-region-r0-c6 | current measured stage | 18/18 | Unmeasured | Unmeasured | 18 | 18 | True |
| gate-clef-128-rgb_palette16-compact-region-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-tev-neighbors-r0-c6 | current measured stage | 99/99 | Unmeasured | Unmeasured | 99 | 99 | True |
| ownership-direct-tev-neighbors-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-tev-neighbors-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| ownership-direct-pplx-neighbors-r0-c6 | current measured stage | 99/99 | Unmeasured | Unmeasured | 99 | 99 | True |
| ownership-direct-pplx-neighbors-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-pplx-neighbors-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-512-rgb_palette16-r2-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-512-rgb_palette16-r2-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-512-rgb_palette16-r2-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |
| ownership-direct-d1-bands-r0-c6 | current measured stage | 99/99 | Unmeasured | Unmeasured | 99 | 99 | True |
| ownership-direct-d1-bands-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-d1-bands-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| screen-crops-luna-1024-pinned-r3-c6 | current measured stage | 19/19 | 2200 | 4297 | 0 | 0 | True |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-128-rgb_palette16-seed7-r0-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |
| choice-pplx-1024-rgb-r2-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-1024-rgb-r2-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-1024-rgb-r2-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |
| ownership-direct-jev-bands-r0-c6 | current measured stage | 99/99 | Unmeasured | Unmeasured | 99 | 99 | True |
| ownership-direct-jev-bands-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-jev-bands-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| screen-crops-luna-1024-matrix-strict-r0-c6 | current measured stage | 19/19 | 0 | 7646 | 0 | 0 | True |
| choice-pplx-400-rgb-seed19-r0-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-400-rgb-seed19-r0-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-400-rgb-seed19-r0-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |
| gate-pplx-400-rgb_palette16-compact-region-r0-c6 | current measured stage | 18/18 | Unmeasured | Unmeasured | 18 | 18 | True |
| gate-pplx-400-rgb_palette16-compact-region-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-luna-bands-r0-c6 | current measured stage | 99/99 | Unmeasured | Unmeasured | 99 | 99 | True |
| ownership-direct-luna-bands-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-luna-bands-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-1024-rgb_palette16-r2-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-1024-rgb_palette16-r2-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-1024-rgb_palette16-r2-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |
| gate-pplx-1024-grayscale8-compact-region-r0-c6 | current measured stage | 18/18 | Unmeasured | Unmeasured | 18 | 18 | True |
| gate-pplx-1024-grayscale8-compact-region-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-d1-neighbors-r0-c6 | current measured stage | 99/99 | Unmeasured | Unmeasured | 99 | 99 | True |
| ownership-direct-d1-neighbors-r0-c6 | historical baseline 0 | 18/18 | 0 | 0 | 0 | 0 | True |
| ownership-direct-d1-neighbors-r0-c6 | historical baseline 1 | 19/19 | 0 | 6497 | 0 | 0 | True |
| screen-crops-haiku-1024-atomic-cells-r0-c6 | current measured stage | 19/19 | 0 | 0 | 0 | 0 | True |
| choice-pplx-500-rgb_palette16-r0-c6 | current measured stage | 16/16 | Unmeasured | Unmeasured | 16 | 16 | True |
| choice-pplx-500-rgb_palette16-r0-c6 | historical baseline 0 | 19/19 | 0 | 6497 | 0 | 0 | True |
| choice-pplx-500-rgb_palette16-r0-c6 | historical baseline 1 | 19/19 | 0 | 0 | 0 | 0 | True |

- `choice-pplx-128-rgb-r2-c6`: evaluation `235adc2a6e9e6cd50172c44a999193a2611dcc0be9ef00a566d7cf19cf559985`; report `b99ec9bdedeb5a5c0951c05a83f23ba7107ea94c50d0e25baa950b97482450f6`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
- `ownership-hybrid-pplx-neighbors-r0-c6`: evaluation `eb92da225f21e8bd35d9376da2d52bc59c3c506967303858cfe61ceba21bdbcb`; report `b3296501762a3d78b10b47b9e110e111e25013120cb5a2702dafabc3c6238245`; failures `{}`; transport `{}`.
- `ownership-allwords-pplx-compact-r0-c6`: evaluation `2293b22d9eb4f62b6250bf6ff624adc5f9ba866f4e59f44482a63d76f0e7e872`; report `48a3ba6db379d4335a6337d4864d24aa2d36b081f6b03a9369ec7664c600c5f1`; failures `{}`; transport `{}`.
- `ownership-allwords-jev-neighbors-r0-c6`: evaluation `74d408f560f4c3e011dfb33ef6fa288466941eee1be094b196a009929dcfd5c8`; report `6e237f13ab3c721e8ff4946598bef958d698d42d5b814af722397b6c94ae6523`; failures `{}`; transport `{}`.
- `choice-pplx-128-rgb-blank-r0-c6`: evaluation `6f106966be6843202569af5fd98e283c73eda0219613af50cb6ff490dbb7f4d3`; report `4b4ba3f447c7e344c63664bfc97b4fea98d9a8da0e888c164b2e0bd829f01f24`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
- `choice-pplx-512-rgb_palette16-blank-r0-c6`: evaluation `6811eebae6d91b1a9cef05d61dfceaf9a88473ac7b6b170cbb163e1316a18cf7`; report `2b96d507593f66bf21d5a345496bbc90888cc75fb3dbed6018ad7e0b72da1843`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
- `ownership-direct-jev-neighbors-r0-c6`: evaluation `fa307d535abb32db1f944d52153eb73edbc201421720d7b0f41dd0ccc9c05f01`; report `6770d32407c5c4e13df35876bc9aa9ee58fb21e5d963ea6b342877f9cb47e7a9`; failures `{}`; transport `{}`.
- `natural64-crops-sonnet-1024-legacy-r0-c6`: evaluation `e08c800b82db525361739f90ce1f2414500a352bafc92a91d2c8dfe9eb2cf0c3`; report `b76763d469ec5d7a88582c5721ae2d672a737f8d5e532fdd5dbf7ca68c49252a`; failures `{}`; transport `{}`.
- `gate-clefomni-128-rgb_palette16-compact-region-r0-c6`: evaluation `64b4f1464ecd281ef9247be94988c369ad5875f85e679bfc77aad0bd8ceaef29`; report `f6668d71a98044d1b8943212edc3b254cc7d175325671457c16610e44103d621`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `46fd5c89a88f7d0baa708dc3ee6320746101aa9de0186a10650a584067e5acba`.
- `ownership-allwords-pplx-neighbors-r0-c6`: evaluation `839f1f28615b63dd2ef2a5afebd2c3b1e6cecf61dad7ea9ab67d59912f079ebf`; report `d343255f9be89e17454638e918457e69486f25703542b1927706bbfe7be22f68`; failures `{}`; transport `{}`.
- `ownership-allwords-jev-compact-r0-c6`: evaluation `ab4cb694743c9e6b4b0225b58f4849e1bcda996b13f80be823d9ba1de55cc55f`; report `0bfd2180be572f43fb39ec5da2186372342f885955f4f49ed2fd5069a5b7f2c6`; failures `{}`; transport `{}`.
- `gate-clef-128-rgb_palette16-compact-region-r0-c6`: evaluation `ebc372d835b052b73e09de9fe348776ab2869b650e17bdc906216183661de8de`; report `a6427d30791fb88ffe49f293d5a54ca139020be4b1ed2c7bd207b927c2ce8cd2`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `46fd5c89a88f7d0baa708dc3ee6320746101aa9de0186a10650a584067e5acba`.
- `ownership-direct-tev-neighbors-r0-c6`: evaluation `1fe2df768e313a49148b1768c7928306676bf0e00563adf3b140d4d162ab84d8`; report `dc55b73e8a49380f2dfd93f585bce287b3225fa1123e29bfbbf716c7de6a7cab`; failures `{}`; transport `{}`.
- `ownership-direct-pplx-neighbors-r0-c6`: evaluation `6b19edbf16c5d347151da1346aebf764f22095c1457601d569db2563f12d798b`; report `9838e93ff78faa9725ac94450653bd57bdc561194235abdf059435432cf110cc`; failures `{}`; transport `{}`.
- `choice-pplx-512-rgb_palette16-r2-c6`: evaluation `b990498d971a57753d7e43308348a204043b842fac506e4f2a8875bef426dc76`; report `cfc7d37d6e71ef39699c9cae893683b1f6ff31551e45d1fa2c7953e8912c1a76`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
- `ownership-direct-d1-bands-r0-c6`: evaluation `a8cdd0e2f958fe4315ed01fa19df2cf7f15fa971ff9d385897bca63adf0faba5`; report `b1466d8ab7b06f9de2f563767ad5b5a294602c11220516111c79464b1b9c3db2`; failures `{}`; transport `{}`.
- `screen-crops-luna-1024-pinned-r3-c6`: evaluation `3ec883cffab6ee125ebbe6ba311045005ab72586c07a561ef59cbcebd507ff64`; report `474cb3e0f6bc8efa5ef1019541da19525db70ac07bc6af9ca6bd78570bff0e20`; failures `{"Table matrix must contain rectangular literal string cells": 1}`; transport `{}`.
- `choice-pplx-128-rgb_palette16-seed7-r0-c6`: evaluation `9b5eeb921440b023f7095bc1cc54675f902ec604a5f9306e084b6ec1b4684906`; report `c5d1559a68e735fb1c8a93a7f663cc0c7b385ba8324f1b56a6a1c24af52505e8`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
- `choice-pplx-1024-rgb-r2-c6`: evaluation `f996c71b067e98aa7e0e71a1ad6b5be7a257e5eef9002eec886d70edea16632a`; report `a99646bcaf2a3431796087da203da327544849c8c5fa37aed3b09cc79460a18e`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
- `ownership-direct-jev-bands-r0-c6`: evaluation `94b64e3adea9a3fca7b44cf55bb3081762c94813cd9d64706bbf8e3373acfb20`; report `2754252db5fc3c0ced9cdccbdc61f55cf7e59af91f513064b788c04538908f9a`; failures `{}`; transport `{}`.
- `screen-crops-luna-1024-matrix-strict-r0-c6`: evaluation `cca5d284886d961d908e4f7dec30ba2cae6bc7c26f330b1bddb5a8e4086df594`; report `aaa15de24ef05392d80d4295d37a537b4368e2891ed423c7707b85302441fbec`; failures `{"Table matrix must contain rectangular literal string cells": 1}`; transport `{}`.
- `choice-pplx-400-rgb-seed19-r0-c6`: evaluation `aafe8a48481d25ea79e2f501167a06a118e6d7796753dc050057dee83ca7d839`; report `039b857a31e5acbbfeb159533392443c06404a30b50eb2cfe103393c08ae8ff2`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
- `gate-pplx-400-rgb_palette16-compact-region-r0-c6`: evaluation `2b40c125e6d71d62778ba0561bdb48134dea021eabf716d4ea95677204b0fab6`; report `ea1088012ec1895fa28ed57157937a3006a5c95997c1d77fc4a5e37bf409dfb0`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `46fd5c89a88f7d0baa708dc3ee6320746101aa9de0186a10650a584067e5acba`.
- `ownership-direct-luna-bands-r0-c6`: evaluation `572a9f12ea49c33f8dd513d9b72300f966e7a5a4372e4f71d44d2a7da51b2e80`; report `33a2a5acef7a30b4b3d02c8974ae43843c6286acd7b00792532fc0facc3286b5`; failures `{}`; transport `{}`.
- `choice-pplx-1024-rgb_palette16-r2-c6`: evaluation `28f40ed4f47531935d3214f93d28b659c59ff5e0c638c623bbec155a42b70094`; report `ce364e0bd07bdd20103e6277583b97a4369015a7c6906a4f520c1d629612f1a9`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.
- `gate-pplx-1024-grayscale8-compact-region-r0-c6`: evaluation `783f87f2be3cd136a666c8932d901e2005c4d3d761bbed678ffe2e37993218c7`; report `62745cc49161da2b5b28cb7db6d89e7c738fbbf7ad13fd154be4015ec1f25236`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `46fd5c89a88f7d0baa708dc3ee6320746101aa9de0186a10650a584067e5acba`.
- `ownership-direct-d1-neighbors-r0-c6`: evaluation `435791b8df0029db87ce84c1fdb84e9ed47c8b4204d02233aea6f78781df9fe1`; report `1de7eea1b6202461c04b71016999f038dec1a7e606badb21d7229f6dae2d1e74`; failures `{}`; transport `{}`.
- `screen-crops-haiku-1024-atomic-cells-r0-c6`: evaluation `3eb7712790ca6faa08ccf9f423ba6c48754933b963e792a9b323a21b112bd1b4`; report `851e553047664b3a22f336774f1da7d82a541416b98e84fe46bd493836d900d9`; failures `{"Atomic cell inventory admission exceeded": 1, "Table bounds are outside normalized image coordinates": 1}`; transport `{}`.
- `choice-pplx-500-rgb_palette16-r0-c6`: evaluation `c830ddac07b617050bd68d7b48a81e53b8858332d4d880e9a95884881184e77f`; report `e30449fd93e9c5f18998962ff572b5c72c8f45c10dade7b38101d42bb98ec255`; failures `{}`; transport `{}`.
  Historical baseline report hashes: `bbf43f93e726aa9f64b65db03d871694af23ce5a3db3566d6b27726cf8923a69`, `58bf4a7f437f257d73671302aa285ed68a182bd43f8ab3485704491262455a57`.

Pending completed evaluation: `full276-ordinal-ocr300-512-r0-c6`, `full276-crops-luna-1024-r0-c6`, `natural64-ordinal-ocredge2048-512-r0-c6`, `ownership-direct-luna-neighbors-r0-c6`, `natural64-crops-haiku-1024-matrix_strict-r0-c6`, `ownership-direct-clefomni-bands-r0-c6`, `ownership-direct-pplx-bands-r0-c6`, `choice-pplx-512-rgb-r2-c6`.
