# P001 complete-page pipeline comparison

Offline private scoring after complete pipeline runs. Chronological completed-report order; each row retains its run name. DEV authored silver supports table/non-table structure only. Operational output means retained Markdown and complete source-owned state; it does not imply semantic correctness.

Dataset SHA-256: `3a1268f1d731a7c60a3fa91f1e90e887c3f41a84aec05beed81b797253afa9b2`. Manifest bytes SHA-256: `7570272d524d68ff3aad59ac1b5ea080e48b77acf605ba8bb30bef27205b94c8`. The fixed pilot is selected by frozen manifest membership; absent results remain failures. Full and pilot cohorts have distinct denominators.

| Run | Cohort | Policy | Model | Gate review model | Image edge | Context rows | Legend | Normalize rotation | OCR empty pages | Gate premise | column_consensus | compact_packet | readable_packet | Output / pages | Exact positive pages | Negative FP pages | All / scored errors |
|---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---:|---:|---:|---:|
| native-r1 | full | native | CPU only | — | — | — | — | False | False | — | False | False | False | 177/181 | 16/35 | 0/133 | 4/1 |
| pilot-pplx-512 | pilot | assembly | perplexity/pplx-decider-v1.1-27b | — | 512 | 1 | True | False | False | — | False | False | False | 32/32 | 15/16 | 4/16 | 0/0 |
| native-r2 | full | native | CPU only | — | — | — | — | False | False | — | False | False | False | 177/181 | 16/35 | 0/133 | 4/1 |
| native-text-r1 | full | native_text | CPU only | — | — | — | — | False | False | — | False | False | False | 178/181 | 3/35 | 26/133 | 3/1 |
| native-r3 | full | native | CPU only | — | — | — | — | False | False | — | False | False | False | 177/181 | 16/35 | 0/133 | 4/1 |
| pilot-flash-512 | pilot | assembly | cloudflare/clef-flash | — | 512 | 1 | True | False | False | — | False | False | False | 32/32 | 5/16 | 0/16 | 0/0 |
| pilot-luna-512 | pilot | assembly | openai/gpt-6-luna-decisions | — | 512 | 1 | True | False | False | — | False | False | False | 32/32 | 15/16 | 4/16 | 0/0 |
| pilot-flash-256 | pilot | assembly | cloudflare/clef-flash | — | 256 | 1 | True | False | False | — | False | False | False | 32/32 | 3/16 | 0/16 | 0/0 |
| pilot-luna-256 | pilot | assembly | openai/gpt-6-luna-decisions | — | 256 | 1 | True | False | False | — | False | False | False | 32/32 | 15/16 | 4/16 | 0/0 |
| pilot-pplx-256 | pilot | assembly | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | False | False | — | False | False | False | 32/32 | 15/16 | 4/16 | 0/0 |
| pilot-flash-1024 | pilot | assembly | cloudflare/clef-flash | — | 1024 | 1 | True | False | False | — | False | False | False | 32/32 | 6/16 | 1/16 | 0/0 |
| pilot-luna-1024 | pilot | assembly | openai/gpt-6-luna-decisions | — | 1024 | 1 | True | False | False | — | False | False | False | 32/32 | 15/16 | 2/16 | 0/0 |
| pilot-pplx-1024 | pilot | assembly | perplexity/pplx-decider-v1.1-27b | — | 1024 | 1 | True | False | False | — | False | False | False | 32/32 | 15/16 | 4/16 | 0/0 |
| pilot-repair-flash-c1 | pilot | repair | cloudflare/clef-flash | — | 512 | 1 | True | False | False | — | False | False | False | 32/32 | 10/16 | 5/16 | 0/0 |
| pilot-repair-luna-c1 | pilot | repair | openai/gpt-6-luna-decisions | — | 512 | 1 | True | False | False | — | False | False | False | 32/32 | 10/16 | 5/16 | 0/0 |
| pilot-repair-pplx-c1 | pilot | repair | perplexity/pplx-decider-v1.1-27b | — | 512 | 1 | True | False | False | — | False | False | False | 32/32 | 11/16 | 6/16 | 0/0 |
| pilot-repair-flash-c3 | pilot | repair | cloudflare/clef-flash | — | 512 | 3 | True | False | False | — | False | False | False | 32/32 | 10/16 | 6/16 | 0/0 |
| pilot-repair-luna-c3 | pilot | repair | openai/gpt-6-luna-decisions | — | 512 | 3 | True | False | False | — | False | False | False | 32/32 | 10/16 | 6/16 | 0/0 |
| pilot-repair-pplx-c3 | pilot | repair | perplexity/pplx-decider-v1.1-27b | — | 512 | 3 | True | False | False | — | False | False | False | 32/32 | 11/16 | 5/16 | 0/0 |
| pilot-oriented-pplx-256 | pilot | assembly | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | False | — | False | False | False | 32/32 | 16/16 | 4/16 | 0/0 |
| pilot-gated-pplx-minimal | pilot | gated | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | False | minimal | False | False | False | 32/32 | 16/16 | 1/16 | 0/0 |
| pilot-gated-pplx-relational | pilot | gated | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | False | relational | False | False | False | 32/32 | 16/16 | 1/16 | 0/0 |
| pilot-gated-luna-1024 | pilot | gated | openai/gpt-6-luna-decisions | — | 1024 | 1 | True | True | False | relational | False | False | False | 32/32 | 16/16 | 1/16 | 0/0 |
| pilot-gated-flash-512 | pilot | gated | cloudflare/clef-flash | — | 512 | 1 | True | True | False | relational | False | False | False | 32/32 | 10/16 | 0/16 | 0/0 |
| pilot-adaptive-pplx | pilot | adaptive | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | False | — | False | False | False | 32/32 | 12/16 | 6/16 | 0/0 |
| pilot-adaptive-luna | pilot | adaptive | openai/gpt-6-luna-decisions | — | 256 | 1 | True | True | False | — | False | False | False | 32/32 | 10/16 | 4/16 | 0/0 |
| pilot-text-pplx | pilot | assembly | perplexity/pplx-decider-v1.1-27b | — | 0 | 1 | True | True | False | — | False | False | False | 32/32 | 16/16 | 4/16 | 0/0 |
| pilot-text-luna | pilot | assembly | openai/gpt-6-luna-decisions | — | 0 | 1 | True | True | False | — | False | False | False | 32/32 | 15/16 | 3/16 | 0/0 |
| pilot-text-flash | pilot | assembly | cloudflare/clef-flash | — | 0 | 1 | True | True | False | — | False | False | False | 32/32 | 0/16 | 0/16 | 0/0 |
| pilot-frontier-haiku | pilot | assembly | anthropic/claude-haiku-5.5 | — | 512 | 1 | True | True | False | — | False | False | False | 32/32 | 16/16 | 3/16 | 0/0 |
| pilot-frontier-sonnet | pilot | assembly | anthropic/claude-sonnet-5.5 | — | 512 | 1 | True | True | False | — | False | False | False | 32/32 | 16/16 | 0/16 | 0/0 |
| pilot-frontier-opus | pilot | assembly | anthropic/claude-opus-5.5 | — | 512 | 1 | True | True | False | — | False | False | False | 32/32 | 16/16 | 0/16 | 0/0 |
| pilot-gated-reading-pplx | pilot | gated | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | False | reading_order | False | False | False | 32/32 | 16/16 | 1/16 | 0/0 |
| pilot-gated-reading-luna | pilot | gated | openai/gpt-6-luna-decisions | — | 1024 | 1 | True | True | False | reading_order | False | False | False | 32/32 | 16/16 | 1/16 | 0/0 |
| pilot-gated-reviewed-pplx | pilot | gated | perplexity/pplx-decider-v1.1-27b | anthropic/claude-sonnet-5.5 | 256 | 1 | True | True | False | relational | False | False | False | 32/32 | 16/16 | 0/16 | 0/0 |
| full-native-ocr | full | native | CPU only | — | — | — | — | True | True | — | False | False | False | 178/181 | 16/35 | 0/133 | 3/0 |
| full-assembly-pplx | full | assembly | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | True | — | False | False | False | 175/181 | 34/35 | 27/133 | 6/0 |
| full-gated-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | True | relational | False | False | False | 178/181 | 34/35 | 4/133 | 3/0 |
| full-gated-reading-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | True | reading_order | False | False | False | 178/181 | 34/35 | 9/133 | 3/0 |
| full-gated-luna | full | gated | openai/gpt-6-luna-decisions | — | 1024 | 1 | True | True | True | relational | False | False | False | 178/181 | 34/35 | 6/133 | 3/0 |
| full-gated-flash | full | gated | cloudflare/clef-flash | — | 512 | 1 | True | True | True | relational | False | False | False | 178/181 | 22/35 | 5/133 | 3/0 |
| full-adaptive-pplx | full | adaptive | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | True | — | False | False | False | 178/181 | 28/35 | 30/133 | 3/0 |
| full-gated-reviewed-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | anthropic/claude-sonnet-5.5 | 256 | 1 | True | True | True | relational | False | False | False | 178/181 | 34/35 | 0/133 | 3/0 |
| full-frontier-haiku | full | assembly | anthropic/claude-haiku-5.5 | — | 512 | 1 | True | True | True | — | False | False | False | 175/181 | 34/35 | 18/133 | 6/0 |
| full-frontier-sonnet | full | assembly | anthropic/claude-sonnet-5.5 | — | 512 | 1 | True | True | True | — | False | False | False | 174/181 | 34/35 | 0/133 | 7/1 |
| full-frontier-opus | full | assembly | anthropic/claude-opus-5.5 | — | 512 | 1 | True | True | True | — | False | False | False | 175/181 | 34/35 | 0/133 | 6/0 |
| full-cascade-pplx | full | cascade | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | True | — | False | False | False | 177/181 | 34/35 | 27/133 | 4/0 |
| full-column-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | True | relational | True | False | False | 178/181 | 35/35 | 4/133 | 3/0 |
| full-column-reviewed-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | anthropic/claude-sonnet-5.5 | 256 | 1 | True | True | True | relational | True | False | False | 178/181 | 35/35 | 0/133 | 3/0 |
| full-compact-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | True | relational | False | True | False | 178/181 | 31/35 | 4/133 | 3/0 |
| full-compact-text-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | — | 0 | 1 | True | True | True | relational | False | True | False | 178/181 | 28/35 | 5/133 | 3/0 |
| full-column-compact-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | — | 256 | 1 | True | True | True | relational | True | True | False | 178/181 | 32/35 | 4/133 | 3/0 |
| full-column-compact-reviewed-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | anthropic/claude-sonnet-5.5 | 256 | 1 | True | True | True | relational | True | True | False | 178/181 | 32/35 | 0/133 | 3/0 |
| full-column-compact-haiku-review | full | gated | perplexity/pplx-decider-v1.1-27b | anthropic/claude-haiku-5.5 | 256 | 1 | True | True | True | relational | True | True | False | 177/181 | 31/35 | 10/133 | 4/1 |
| full-column-compact-sonnet | full | assembly | anthropic/claude-sonnet-5.5 | — | 512 | 1 | True | True | True | — | True | True | False | 166/181 | 33/35 | 2/133 | 15/7 |
| full-column-readable-reviewed-pplx | full | gated | perplexity/pplx-decider-v1.1-27b | anthropic/claude-sonnet-5.5 | 256 | 1 | True | True | True | relational | True | False | True | 178/181 | 35/35 | 0/133 | 3/0 |

Every successful page's retained Markdown is checked byte-for-byte against a trusted deterministic rendering of its complete source-owned final state. Artifact Python is never executed.

Legacy frozen renderer source unavailable: `native-r1`. Their Markdown matches the trusted output format, but historical renderer source integrity is unverified; matched repeats with retained source are preferred.

| Run | Exact scored pages | Complete tables / charged tables | Exact cells / expected tables | Exact spans / expected tables | Correct slots / expected / charged slots | Missing / extra tables | Conserved / checked output pages | Oracle exact positive pages |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| native-r1 | 149/168 | 16/35 | 16/35 | 16/35 | 228/437/437 | 19/0 | 177/177 | 16/35 |
| pilot-pplx-512 | 27/32 | 15/20 | 15/16 | 15/16 | 198/207/280 | 1/4 | 32/32 | 15/16 |
| native-r2 | 149/168 | 16/35 | 16/35 | 16/35 | 228/437/437 | 19/0 | 177/177 | 16/35 |
| native-text-r1 | 110/168 | 3/75 | 3/35 | 3/35 | 32/437/1149 | 32/40 | 178/178 | 3/35 |
| native-r3 | 149/168 | 16/35 | 16/35 | 16/35 | 228/437/437 | 19/0 | 177/177 | 16/35 |
| pilot-flash-512 | 21/32 | 5/16 | 5/16 | 5/16 | 63/207/207 | 11/0 | 32/32 | 15/16 |
| pilot-luna-512 | 27/32 | 15/21 | 15/16 | 15/16 | 198/207/300 | 1/5 | 32/32 | 15/16 |
| pilot-flash-256 | 19/32 | 3/16 | 3/16 | 3/16 | 36/207/207 | 13/0 | 32/32 | 15/16 |
| pilot-luna-256 | 27/32 | 15/20 | 15/16 | 15/16 | 198/207/294 | 1/4 | 32/32 | 15/16 |
| pilot-pplx-256 | 27/32 | 15/21 | 15/16 | 15/16 | 198/207/288 | 1/5 | 32/32 | 15/16 |
| pilot-flash-1024 | 21/32 | 6/17 | 6/16 | 6/16 | 75/207/237 | 10/1 | 32/32 | 15/16 |
| pilot-luna-1024 | 29/32 | 15/18 | 15/16 | 15/16 | 198/207/246 | 1/2 | 32/32 | 15/16 |
| pilot-pplx-1024 | 27/32 | 15/20 | 15/16 | 15/16 | 198/207/280 | 1/4 | 32/32 | 15/16 |
| pilot-repair-flash-c1 | 21/32 | 10/27 | 10/16 | 10/16 | 138/207/434 | 6/11 | 32/32 | 15/16 |
| pilot-repair-luna-c1 | 21/32 | 10/26 | 10/16 | 10/16 | 138/207/415 | 6/10 | 32/32 | 15/16 |
| pilot-repair-pplx-c1 | 21/32 | 11/27 | 11/16 | 11/16 | 150/207/404 | 5/11 | 32/32 | 15/16 |
| pilot-repair-flash-c3 | 20/32 | 10/28 | 10/16 | 10/16 | 138/207/449 | 6/12 | 32/32 | 15/16 |
| pilot-repair-luna-c3 | 20/32 | 10/28 | 10/16 | 10/16 | 138/207/457 | 6/12 | 32/32 | 15/16 |
| pilot-repair-pplx-c3 | 22/32 | 11/26 | 11/16 | 11/16 | 150/207/394 | 5/10 | 32/32 | 15/16 |
| pilot-oriented-pplx-256 | 28/32 | 16/20 | 16/16 | 16/16 | 207/207/280 | 0/4 | 32/32 | 16/16 |
| pilot-gated-pplx-minimal | 31/32 | 16/17 | 16/16 | 16/16 | 207/207/222 | 0/1 | 32/32 | 16/16 |
| pilot-gated-pplx-relational | 31/32 | 16/17 | 16/16 | 16/16 | 207/207/222 | 0/1 | 32/32 | 16/16 |
| pilot-gated-luna-1024 | 31/32 | 16/17 | 16/16 | 16/16 | 207/207/222 | 0/1 | 32/32 | 16/16 |
| pilot-gated-flash-512 | 26/32 | 10/16 | 10/16 | 10/16 | 138/207/207 | 6/0 | 32/32 | 16/16 |
| pilot-adaptive-pplx | 22/32 | 12/26 | 12/16 | 12/16 | 159/207/400 | 4/10 | 32/32 | 16/16 |
| pilot-adaptive-luna | 22/32 | 10/25 | 10/16 | 10/16 | 135/207/405 | 6/9 | 32/32 | 16/16 |
| pilot-text-pplx | 28/32 | 16/20 | 16/16 | 16/16 | 207/207/280 | 0/4 | 32/32 | 16/16 |
| pilot-text-luna | 28/32 | 15/19 | 15/16 | 15/16 | 192/207/264 | 1/3 | 32/32 | 16/16 |
| pilot-text-flash | 16/32 | 0/16 | 0/16 | 0/16 | 0/207/207 | 16/0 | 32/32 | 16/16 |
| pilot-frontier-haiku | 29/32 | 16/19 | 16/16 | 16/16 | 207/207/276 | 0/3 | 32/32 | 16/16 |
| pilot-frontier-sonnet | 32/32 | 16/16 | 16/16 | 16/16 | 207/207/207 | 0/0 | 32/32 | 16/16 |
| pilot-frontier-opus | 32/32 | 16/16 | 16/16 | 16/16 | 207/207/207 | 0/0 | 32/32 | 16/16 |
| pilot-gated-reading-pplx | 31/32 | 16/17 | 16/16 | 16/16 | 207/207/222 | 0/1 | 32/32 | 16/16 |
| pilot-gated-reading-luna | 31/32 | 16/17 | 16/16 | 16/16 | 207/207/222 | 0/1 | 32/32 | 16/16 |
| pilot-gated-reviewed-pplx | 32/32 | 16/16 | 16/16 | 16/16 | 207/207/207 | 0/0 | 32/32 | 16/16 |
| full-native-ocr | 149/168 | 16/35 | 16/35 | 16/35 | 228/437/437 | 19/0 | 178/178 | 16/35 |
| full-assembly-pplx | 140/168 | 34/62 | 34/35 | 35/35 | 433/437/969 | 0/27 | 175/175 | 34/35 |
| full-gated-pplx | 163/168 | 34/39 | 34/35 | 35/35 | 433/437/527 | 0/4 | 178/178 | 34/35 |
| full-gated-reading-pplx | 158/168 | 34/44 | 34/35 | 35/35 | 433/437/617 | 0/9 | 178/178 | 34/35 |
| full-gated-luna | 161/168 | 34/41 | 34/35 | 35/35 | 433/437/527 | 0/6 | 178/178 | 34/35 |
| full-gated-flash | 150/168 | 22/40 | 22/35 | 22/35 | 300/437/569 | 13/5 | 178/178 | 34/35 |
| full-adaptive-pplx | 131/168 | 28/71 | 28/35 | 29/35 | 361/437/1265 | 6/36 | 178/178 | 34/35 |
| full-gated-reviewed-pplx | 167/168 | 34/35 | 34/35 | 35/35 | 433/437/437 | 0/0 | 178/178 | 34/35 |
| full-frontier-haiku | 149/168 | 34/53 | 34/35 | 35/35 | 433/437/815 | 0/18 | 175/175 | 34/35 |
| full-frontier-sonnet | 166/168 | 34/35 | 34/35 | 35/35 | 433/437/437 | 0/0 | 174/174 | 34/35 |
| full-frontier-opus | 167/168 | 34/35 | 34/35 | 34/35 | 428/437/437 | 1/0 | 175/175 | 34/35 |
| full-cascade-pplx | 140/168 | 34/62 | 34/35 | 35/35 | 433/437/969 | 0/27 | 177/177 | 34/35 |
| full-column-pplx | 164/168 | 35/39 | 35/35 | 35/35 | 437/437/527 | 0/4 | 178/178 | 35/35 |
| full-column-reviewed-pplx | 168/168 | 35/35 | 35/35 | 35/35 | 437/437/437 | 0/0 | 178/178 | 35/35 |
| full-compact-pplx | 160/168 | 31/42 | 31/35 | 32/35 | 397/437/590 | 3/7 | 178/178 | 34/35 |
| full-compact-text-pplx | 156/168 | 28/46 | 28/35 | 29/35 | 361/437/638 | 6/11 | 178/178 | 34/35 |
| full-column-compact-pplx | 161/168 | 32/42 | 32/35 | 32/35 | 401/437/590 | 3/7 | 178/178 | 35/35 |
| full-column-compact-reviewed-pplx | 165/168 | 32/38 | 32/35 | 32/35 | 401/437/500 | 3/3 | 178/178 | 35/35 |
| full-column-compact-haiku-review | 154/168 | 31/48 | 31/35 | 31/35 | 389/437/710 | 4/13 | 177/177 | 35/35 |
| full-column-compact-sonnet | 159/168 | 33/37 | 33/35 | 33/35 | 413/437/476 | 2/2 | 166/166 | 35/35 |
| full-column-readable-reviewed-pplx | 168/168 | 35/35 | 35/35 | 35/35 | 437/437/437 | 0/0 | 178/178 | 35/35 |

| Run | Output p/min | Output p/USD | Exact positive p/min | Exact positive p/USD | Wall s | CPU s | Peak sampled RSS bytes | Provider USD | Missing provider charges | Effective USD | Accounted USD | Cost bases |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| native-r1 | 3690.3 | unknown | 333.586 | unknown | 2.87782 | 2.97454 | 125878272 | 0 | 0 | 0 | 0 | {} |
| pilot-pplx-512 | 54.5532 | 10205.9 | 25.5718 | 4784.02 | 35.195 | 14.9024 | 201883648 | 0.00313544 | 0 | 0.00313544 | 0.00313544 | {"provider-reported USD": 32} |
| native-r2 | 4291.37 | unknown | 387.92 | unknown | 2.47474 | 2.56821 | 130228224 | 0 | 0 | 0 | 0 | {} |
| native-text-r1 | 4023.99 | unknown | 67.8201 | unknown | 2.65408 | 2.72698 | 132030464 | 0 | 0 | 0 | 0 | {} |
| native-r3 | 4259.93 | unknown | 385.078 | unknown | 2.493 | 2.58923 | 125640704 | 0 | 0 | 0 | 0 | {} |
| pilot-flash-512 | 31.7319 | 5318.91 | 4.9581 | 831.079 | 60.507 | 15.8482 | 192167936 | 0.00601627 | 0 | 0.00601627 | 0.00601627 | {"provider-reported USD": 32} |
| pilot-luna-512 | 67.6551 | 3136.06 | 31.7133 | 1470.03 | 28.3792 | 16.2325 | 191758336 | 0 | 0 | 0.0102039 | 0.0102039 | {"catalog estimate": 32} |
| pilot-flash-256 | 31.8398 | 5442.45 | 2.98498 | 510.23 | 60.3019 | 15.4808 | 204025856 | 0.0058797 | 0 | 0.0058797 | 0.0058797 | {"provider-reported USD": 32} |
| pilot-luna-256 | 58.3245 | 3293.03 | 27.3396 | 1543.61 | 32.9193 | 20.4373 | 192884736 | 0 | 0 | 0.0097175 | 0.0097175 | {"catalog estimate": 32} |
| pilot-pplx-256 | 46.5715 | 10445.4 | 21.8304 | 4896.26 | 41.2269 | 20.2362 | 204152832 | 0.00306356 | 0 | 0.00306356 | 0.00306356 | {"provider-reported USD": 32} |
| pilot-flash-1024 | 24.9997 | 4737.66 | 4.68745 | 888.312 | 76.8009 | 19.8347 | 197775360 | 0.00675439 | 0 | 0.00675439 | 0.00675439 | {"provider-reported USD": 32} |
| pilot-luna-1024 | 61.0887 | 2645 | 28.6354 | 1239.84 | 31.4297 | 16.8555 | 197107712 | 0 | 0 | 0.0120983 | 0.0120983 | {"catalog estimate": 32} |
| pilot-pplx-1024 | 38.8031 | 9080.8 | 18.189 | 4256.62 | 49.4806 | 19.6573 | 200085504 | 0.00352392 | 0 | 0.00352392 | 0.00352392 | {"provider-reported USD": 32} |
| pilot-repair-flash-c1 | 72.5316 | 24224.2 | 22.6661 | 7570.06 | 26.4712 | 10.3348 | 194093056 | 0.00132099 | 0 | 0.00132099 | 0.00132099 | {"provider-reported USD": 17} |
| pilot-repair-luna-c1 | 108.632 | 9985.96 | 33.9475 | 3120.61 | 17.6743 | 10.4208 | 205475840 | 0 | 0 | 0.0032045 | 0.0032045 | {"catalog estimate": 21} |
| pilot-repair-pplx-c1 | 84.2327 | 31661.2 | 28.955 | 10883.5 | 22.794 | 11.9655 | 193032192 | 0.0010107 | 0 | 0.0010107 | 0.0010107 | {"provider-reported USD": 23} |
| pilot-repair-flash-c3 | 49.3068 | 16880.9 | 15.4084 | 5275.29 | 38.9399 | 13.8762 | 193368064 | 0.00189563 | 0 | 0.00189563 | 0.00189563 | {"provider-reported USD": 18} |
| pilot-repair-luna-c3 | 69.801 | 8570.13 | 21.8128 | 2678.16 | 27.5068 | 17.3023 | 195485696 | 0 | 0 | 0.0037339 | 0.0037339 | {"catalog estimate": 19} |
| pilot-repair-pplx-c3 | 47.392 | 27889.6 | 16.291 | 9587.06 | 40.5131 | 18.8634 | 191852544 | 0.00114738 | 0 | 0.00114738 | 0.00114738 | {"provider-reported USD": 22} |
| pilot-oriented-pplx-256 | 47.1868 | 10798.8 | 23.5934 | 5399.42 | 40.6893 | 19.444 | 193822720 | 0.00296328 | 0 | 0.00296328 | 0.00296328 | {"provider-reported USD": 32} |
| pilot-gated-pplx-minimal | 60.2864 | 19642.3 | 30.1432 | 9821.13 | 31.848 | 16.8666 | 192708608 | 0.00162914 | 0 | 0.00162914 | 0.00162914 | {"provider-reported USD": 28} |
| pilot-gated-pplx-relational | 54.5458 | 20241.1 | 27.2729 | 10120.6 | 35.1998 | 20.5435 | 205422592 | 0.00158094 | 0 | 0.00158094 | 0.00158094 | {"provider-reported USD": 27} |
| pilot-gated-luna-1024 | 54.9414 | 4337.04 | 27.4707 | 2168.52 | 34.9463 | 22.6739 | 204877824 | 0 | 0 | 0.0073783 | 0.0073783 | {"catalog estimate": 27} |
| pilot-gated-flash-512 | 34.1627 | 8043.34 | 10.6758 | 2513.54 | 56.2017 | 21.6577 | 200462336 | 0.00397845 | 0 | 0.00397845 | 0.00397845 | {"provider-reported USD": 30} |
| pilot-adaptive-pplx | 82.1111 | 40437.7 | 30.7917 | 15164.2 | 23.3829 | 11.7197 | 192634880 | 0.00079134 | 0 | 0.00079134 | 0.00079134 | {"provider-reported USD": 21} |
| pilot-adaptive-luna | 100.023 | 12560.8 | 31.2573 | 3925.26 | 19.1955 | 10.3758 | 192548864 | 0 | 0 | 0.0025476 | 0.0025476 | {"catalog estimate": 18} |
| pilot-text-pplx | 48.909 | 11643 | 24.4545 | 5821.48 | 39.2565 | 17.1114 | 193626112 | 0.00274844 | 0 | 0.00274844 | 0.00274844 | {"provider-reported USD": 32} |
| pilot-text-luna | 63.9053 | 3507.62 | 29.9556 | 1644.2 | 30.0445 | 17.7252 | 203886592 | 0 | 0 | 0.009123 | 0.009123 | {"catalog estimate": 32} |
| pilot-text-flash | 35.5441 | 6059.27 | 0 | 0 | 54.0174 | 16.4484 | 205336576 | 0.00528116 | 0 | 0.00528116 | 0.00528116 | {"provider-reported USD": 32} |
| pilot-frontier-haiku | 16.0081 | 1989.01 | 8.00403 | 994.505 | 119.94 | 23.9085 | 195391488 | 0.0160884 | 0 | 0.0160884 | 0.0160884 | {"provider-reported USD": 32} |
| pilot-frontier-sonnet | 18.2279 | 109.77 | 9.11396 | 54.8851 | 105.333 | 19.181 | 195506176 | 0.291518 | 0 | 0.291518 | 0.291518 | {"provider-reported USD": 32} |
| pilot-frontier-opus | 13.0072 | 56.1703 | 6.50362 | 28.0852 | 147.61 | 19.8952 | 197185536 | 0.569696 | 0 | 0.569696 | 0.569696 | {"provider-reported USD": 32} |
| pilot-gated-reading-pplx | 68.0934 | 15080.8 | 34.0467 | 7540.41 | 28.1966 | 13.1731 | 199663616 | 0.0021219 | 0 | 0.0021219 | 0.0021219 | {"provider-reported USD": 27} |
| pilot-gated-reading-luna | 69.4643 | 3301.35 | 34.7321 | 1650.68 | 27.6401 | 14.2842 | 200142848 | 0 | 0 | 0.009693 | 0.009693 | {"catalog estimate": 28} |
| pilot-gated-reviewed-pplx | 61.2827 | 3128.21 | 30.6414 | 1564.11 | 31.3302 | 13.2686 | 197636096 | 0.0102295 | 0 | 0.0102295 | 0.0102295 | {"provider-reported USD": 27} |
| full-native-ocr | 1524.94 | unknown | 137.073 | unknown | 7.00355 | 17.8262 | 465768448 | 0 | 0 | 0 | 0 | {} |
| full-assembly-pplx | 53.0304 | 10169.8 | 10.303 | 1975.85 | 198 | 98.1431 | 558686208 | 0.0172078 | 0 | 0.0172078 | 0.0172078 | {"provider-reported USD": 175} |
| full-gated-pplx | 117.883 | 28641.2 | 22.5171 | 5470.79 | 90.5979 | 57.2135 | 542253056 | 0.00621482 | 0 | 0.00621482 | 0.00621482 | {"provider-reported USD": 84} |
| full-gated-reading-pplx | 91.6304 | 19961.2 | 17.5024 | 3812.81 | 116.555 | 71.1836 | 524369920 | 0.0089173 | 0 | 0.0089173 | 0.0089173 | {"provider-reported USD": 88} |
| full-gated-luna | 105.765 | 6321.02 | 20.2022 | 1207.39 | 100.979 | 76.6113 | 540606464 | 0 | 0 | 0.02816 | 0.02816 | {"catalog estimate": 89} |
| full-gated-flash | 58.455 | 10957.5 | 7.22477 | 1354.3 | 182.705 | 70.6604 | 545579008 | 0.0162445 | 0 | 0.0162445 | 0.0162445 | {"provider-reported USD": 98} |
| full-adaptive-pplx | 151.612 | 69429.3 | 23.8491 | 10921.5 | 70.4428 | 51.9641 | 540483584 | 0.00256376 | 0 | 0.00256376 | 0.00256376 | {"provider-reported USD": 67} |
| full-gated-reviewed-pplx | 72.3848 | 1658.72 | 13.8263 | 316.833 | 147.545 | 63.8772 | 541716480 | 0.107312 | 0 | 0.107312 | 0.107312 | {"provider-reported USD": 90} |
| full-frontier-haiku | 22.0223 | 2092.66 | 4.27862 | 406.573 | 476.79 | 104.75 | 547942400 | 0.0836258 | 0 | 0.0836258 | 0.0836258 | {"provider-reported USD": 175} |
| full-frontier-sonnet | 15.9365 | 107.684 | 3.11403 | 21.0416 | 655.101 | 108.119 | 546701312 | 1.61585 | 0 | 1.61585 | 1.61585 | {"provider-reported USD": 175} |
| full-frontier-opus | 13.0243 | 56.3242 | 2.53044 | 10.943 | 806.183 | 106.756 | 551821312 | 3.10701 | 0 | 3.10701 | 3.10701 | {"provider-reported USD": 175} |
| full-cascade-pplx | 58.74 | 10893 | 11.2834 | 2092.45 | 180.797 | 98.8326 | 561770496 | 0.0162489 | 0 | 0.0162489 | 0.0162489 | {"provider-reported USD": 159} |
| full-column-pplx | 114.119 | 25915.7 | 22.4391 | 5095.79 | 93.5868 | 61.0101 | 527753216 | 0.00686842 | 0 | 0.00686842 | 0.00686842 | {"provider-reported USD": 85} |
| full-column-reviewed-pplx | 72.3586 | 1725.88 | 14.2278 | 339.359 | 147.598 | 66.3178 | 547733504 | 0.103136 | 0 | 0.103136 | 0.103136 | {"provider-reported USD": 91} |
| full-compact-pplx | 113.934 | 29823.1 | 19.8425 | 5193.92 | 93.7383 | 62.1688 | 544456704 | 0.00596852 | 0 | 0.00596852 | 0.00596852 | {"provider-reported USD": 84} |
| full-compact-text-pplx | 102.103 | 31226.9 | 16.0612 | 4912.09 | 104.6 | 64.4532 | 528424960 | 0.00570022 | 0 | 0.00570022 | 0.00570022 | {"provider-reported USD": 85} |
| full-column-compact-pplx | 107.54 | 27062.5 | 19.333 | 4865.17 | 99.3121 | 64.708 | 531001344 | 0.00657736 | 0 | 0.00657736 | 0.00657736 | {"provider-reported USD": 85} |
| full-column-compact-reviewed-pplx | 69.0265 | 1751.22 | 12.4093 | 314.826 | 154.723 | 65.7487 | 543662080 | 0.101643 | 0 | 0.101643 | 0.101643 | {"provider-reported USD": 91} |
| full-column-compact-haiku-review | 81.5534 | unknown | 14.2834 | unknown | 130.222 | 68.1271 | 532701184 | 0.0103152 | 1 | unknown | 0.310315 | {"provider-reported USD": 99, "reserved": 1} |
| full-column-compact-sonnet | 13.5659 | 113.444 | 2.69683 | 22.5522 | 734.196 | 107.983 | 555094016 | 1.46327 | 0 | 1.46327 | 1.46327 | {"provider-reported USD": 175} |
| full-column-readable-reviewed-pplx | 71.7085 | 1754.59 | 14.1 | 345.004 | 148.936 | 65.0606 | 539107328 | 0.101448 | 0 | 0.101448 | 0.101448 | {"provider-reported USD": 91} |

Successful retained calls by requested model:

Primary and optional review models form one experimental policy; both charges enter the run total. This breakdown covers only calls retained in completed page results. Failed or parse-rejected attempts may be absent, so the complete-run ledger-attempt cost totals above remain authoritative. Reported USD is a known-value subtotal with missing counts, not a complete total when values are missing.

| Run | Requested model | Successful calls | Reported USD subtotal | Missing reported charges | Effective USD for listed calls | Accounted USD for listed calls | Cost bases |
|---|---|---:|---:|---:|---:|---:|---|
| pilot-pplx-512 | perplexity/pplx-decider-v1.1-27b | 32 | 0.00313544 | 0 | 0.00313544 | 0.00313544 | {"provider-reported USD": 32} |
| pilot-flash-512 | cloudflare/clef-flash | 32 | 0.00601627 | 0 | 0.00601627 | 0.00601627 | {"provider-reported USD": 32} |
| pilot-luna-512 | openai/gpt-6-luna-decisions | 32 | 0 | 0 | 0.0102039 | 0.0102039 | {"catalog estimate": 32} |
| pilot-flash-256 | cloudflare/clef-flash | 32 | 0.0058797 | 0 | 0.0058797 | 0.0058797 | {"provider-reported USD": 32} |
| pilot-luna-256 | openai/gpt-6-luna-decisions | 32 | 0 | 0 | 0.0097175 | 0.0097175 | {"catalog estimate": 32} |
| pilot-pplx-256 | perplexity/pplx-decider-v1.1-27b | 32 | 0.00306356 | 0 | 0.00306356 | 0.00306356 | {"provider-reported USD": 32} |
| pilot-flash-1024 | cloudflare/clef-flash | 32 | 0.00675439 | 0 | 0.00675439 | 0.00675439 | {"provider-reported USD": 32} |
| pilot-luna-1024 | openai/gpt-6-luna-decisions | 32 | 0 | 0 | 0.0120983 | 0.0120983 | {"catalog estimate": 32} |
| pilot-pplx-1024 | perplexity/pplx-decider-v1.1-27b | 32 | 0.00352392 | 0 | 0.00352392 | 0.00352392 | {"provider-reported USD": 32} |
| pilot-repair-flash-c1 | cloudflare/clef-flash | 17 | 0.00132099 | 0 | 0.00132099 | 0.00132099 | {"provider-reported USD": 17} |
| pilot-repair-luna-c1 | openai/gpt-6-luna-decisions | 21 | 0 | 0 | 0.0032045 | 0.0032045 | {"catalog estimate": 21} |
| pilot-repair-pplx-c1 | perplexity/pplx-decider-v1.1-27b | 23 | 0.0010107 | 0 | 0.0010107 | 0.0010107 | {"provider-reported USD": 23} |
| pilot-repair-flash-c3 | cloudflare/clef-flash | 18 | 0.00189563 | 0 | 0.00189563 | 0.00189563 | {"provider-reported USD": 18} |
| pilot-repair-luna-c3 | openai/gpt-6-luna-decisions | 19 | 0 | 0 | 0.0037339 | 0.0037339 | {"catalog estimate": 19} |
| pilot-repair-pplx-c3 | perplexity/pplx-decider-v1.1-27b | 22 | 0.00114738 | 0 | 0.00114738 | 0.00114738 | {"provider-reported USD": 22} |
| pilot-oriented-pplx-256 | perplexity/pplx-decider-v1.1-27b | 32 | 0.00296328 | 0 | 0.00296328 | 0.00296328 | {"provider-reported USD": 32} |
| pilot-gated-pplx-minimal | perplexity/pplx-decider-v1.1-27b | 28 | 0.00162914 | 0 | 0.00162914 | 0.00162914 | {"provider-reported USD": 28} |
| pilot-gated-pplx-relational | perplexity/pplx-decider-v1.1-27b | 27 | 0.00158094 | 0 | 0.00158094 | 0.00158094 | {"provider-reported USD": 27} |
| pilot-gated-luna-1024 | openai/gpt-6-luna-decisions | 27 | 0 | 0 | 0.0073783 | 0.0073783 | {"catalog estimate": 27} |
| pilot-gated-flash-512 | cloudflare/clef-flash | 30 | 0.00397845 | 0 | 0.00397845 | 0.00397845 | {"provider-reported USD": 30} |
| pilot-adaptive-pplx | perplexity/pplx-decider-v1.1-27b | 21 | 0.00079134 | 0 | 0.00079134 | 0.00079134 | {"provider-reported USD": 21} |
| pilot-adaptive-luna | openai/gpt-6-luna-decisions | 18 | 0 | 0 | 0.0025476 | 0.0025476 | {"catalog estimate": 18} |
| pilot-text-pplx | perplexity/pplx-decider-v1.1-27b | 32 | 0.00274844 | 0 | 0.00274844 | 0.00274844 | {"provider-reported USD": 32} |
| pilot-text-luna | openai/gpt-6-luna-decisions | 32 | 0 | 0 | 0.009123 | 0.009123 | {"catalog estimate": 32} |
| pilot-text-flash | cloudflare/clef-flash | 32 | 0.00528116 | 0 | 0.00528116 | 0.00528116 | {"provider-reported USD": 32} |
| pilot-frontier-haiku | anthropic/claude-haiku-5.5 | 32 | 0.0160884 | 0 | 0.0160884 | 0.0160884 | {"provider-reported USD": 32} |
| pilot-frontier-sonnet | anthropic/claude-sonnet-5.5 | 32 | 0.291518 | 0 | 0.291518 | 0.291518 | {"provider-reported USD": 32} |
| pilot-frontier-opus | anthropic/claude-opus-5.5 | 32 | 0.569696 | 0 | 0.569696 | 0.569696 | {"provider-reported USD": 32} |
| pilot-gated-reading-pplx | perplexity/pplx-decider-v1.1-27b | 27 | 0.0021219 | 0 | 0.0021219 | 0.0021219 | {"provider-reported USD": 27} |
| pilot-gated-reading-luna | openai/gpt-6-luna-decisions | 28 | 0 | 0 | 0.009693 | 0.009693 | {"catalog estimate": 28} |
| pilot-gated-reviewed-pplx | anthropic/claude-sonnet-5.5 | 1 | 0.008714 | 0 | 0.008714 | 0.008714 | {"provider-reported USD": 1} |
| pilot-gated-reviewed-pplx | perplexity/pplx-decider-v1.1-27b | 26 | 0.00151548 | 0 | 0.00151548 | 0.00151548 | {"provider-reported USD": 26} |
| full-assembly-pplx | perplexity/pplx-decider-v1.1-27b | 175 | 0.0172078 | 0 | 0.0172078 | 0.0172078 | {"provider-reported USD": 175} |
| full-gated-pplx | perplexity/pplx-decider-v1.1-27b | 84 | 0.00621482 | 0 | 0.00621482 | 0.00621482 | {"provider-reported USD": 84} |
| full-gated-reading-pplx | perplexity/pplx-decider-v1.1-27b | 88 | 0.0089173 | 0 | 0.0089173 | 0.0089173 | {"provider-reported USD": 88} |
| full-gated-luna | openai/gpt-6-luna-decisions | 89 | 0 | 0 | 0.02816 | 0.02816 | {"catalog estimate": 89} |
| full-gated-flash | cloudflare/clef-flash | 98 | 0.0162445 | 0 | 0.0162445 | 0.0162445 | {"provider-reported USD": 98} |
| full-adaptive-pplx | perplexity/pplx-decider-v1.1-27b | 67 | 0.00256376 | 0 | 0.00256376 | 0.00256376 | {"provider-reported USD": 67} |
| full-gated-reviewed-pplx | anthropic/claude-sonnet-5.5 | 12 | 0.101444 | 0 | 0.101444 | 0.101444 | {"provider-reported USD": 12} |
| full-gated-reviewed-pplx | perplexity/pplx-decider-v1.1-27b | 78 | 0.00586794 | 0 | 0.00586794 | 0.00586794 | {"provider-reported USD": 78} |
| full-frontier-haiku | anthropic/claude-haiku-5.5 | 175 | 0.0836258 | 0 | 0.0836258 | 0.0836258 | {"provider-reported USD": 175} |
| full-frontier-sonnet | anthropic/claude-sonnet-5.5 | 174 | 1.5978 | 0 | 1.5978 | 1.5978 | {"provider-reported USD": 174} |
| full-frontier-opus | anthropic/claude-opus-5.5 | 175 | 3.10701 | 0 | 3.10701 | 3.10701 | {"provider-reported USD": 175} |
| full-cascade-pplx | perplexity/pplx-decider-v1.1-27b | 159 | 0.0162489 | 0 | 0.0162489 | 0.0162489 | {"provider-reported USD": 159} |
| full-column-pplx | perplexity/pplx-decider-v1.1-27b | 85 | 0.00686842 | 0 | 0.00686842 | 0.00686842 | {"provider-reported USD": 85} |
| full-column-reviewed-pplx | anthropic/claude-sonnet-5.5 | 12 | 0.096634 | 0 | 0.096634 | 0.096634 | {"provider-reported USD": 12} |
| full-column-reviewed-pplx | perplexity/pplx-decider-v1.1-27b | 79 | 0.00650174 | 0 | 0.00650174 | 0.00650174 | {"provider-reported USD": 79} |
| full-compact-pplx | perplexity/pplx-decider-v1.1-27b | 84 | 0.00596852 | 0 | 0.00596852 | 0.00596852 | {"provider-reported USD": 84} |
| full-compact-text-pplx | perplexity/pplx-decider-v1.1-27b | 85 | 0.00570022 | 0 | 0.00570022 | 0.00570022 | {"provider-reported USD": 85} |
| full-column-compact-pplx | perplexity/pplx-decider-v1.1-27b | 85 | 0.00657736 | 0 | 0.00657736 | 0.00657736 | {"provider-reported USD": 85} |
| full-column-compact-reviewed-pplx | anthropic/claude-sonnet-5.5 | 12 | 0.095344 | 0 | 0.095344 | 0.095344 | {"provider-reported USD": 12} |
| full-column-compact-reviewed-pplx | perplexity/pplx-decider-v1.1-27b | 79 | 0.00629942 | 0 | 0.00629942 | 0.00629942 | {"provider-reported USD": 79} |
| full-column-compact-haiku-review | anthropic/claude-haiku-5.5 | 12 | 0.0035237 | 0 | 0.0035237 | 0.0035237 | {"provider-reported USD": 12} |
| full-column-compact-haiku-review | perplexity/pplx-decider-v1.1-27b | 87 | 0.0067915 | 0 | 0.0067915 | 0.0067915 | {"provider-reported USD": 87} |
| full-column-compact-sonnet | anthropic/claude-sonnet-5.5 | 166 | 1.32593 | 0 | 1.32593 | 1.32593 | {"provider-reported USD": 166} |
| full-column-readable-reviewed-pplx | anthropic/claude-sonnet-5.5 | 12 | 0.095004 | 0 | 0.095004 | 0.095004 | {"provider-reported USD": 12} |
| full-column-readable-reviewed-pplx | perplexity/pplx-decider-v1.1-27b | 79 | 0.0064442 | 0 | 0.0064442 | 0.0064442 | {"provider-reported USD": 79} |

Candidate oracle coverage uses private references to choose an already-retained complete candidate. It is reference-informed and unrunnable as an extraction policy; it does not synthesize missing candidates. Coverage is policy-specific: it scores only alternatives retained by that run. No output or model was supplied references during inference. Exactness compares complete matrices and spans after whitespace normalization; extra tables charge both table and cell denominators. Errors on negative pages remain failures, not correct zero-table pages.

Source conservation covers extracted snapshot word IDs, not all painted PDF content, Unicode mapping, visibility, OCR or semantic relations. Natural documents with incomplete references are diagnostic-only. Headings, lists, forms, equations, images and general document quality are not gold-scored. See [corpus contract](pipeline-corpus-design.md).

API cost excludes local electricity and amortization. Positive provider charges and catalog estimates retain distinct bases; missing provider counts remain visible. Accounted USD can contain reservations, which are separate from effective charges. Unknown effective totals yield unknown p/USD. Zero-cost native throughput has no finite p/USD.

<details>
<summary>Complete per-family structure scores</summary>

| Run | Family | Scored / diagnostic pages | Exact positive / positives | Negative FP / negatives | Exact scored pages | Errors |
|---|---|---:|---:|---:|---:|---:|
| native-r1 | companion/borderless-plain | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r1 | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r1 | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| native-r1 | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| native-r1 | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| native-r1 | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| native-r1 | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r1 | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r1 | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r1 | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r1 | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-aligned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| native-r1 | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r1 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r1 | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r1 | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r1 | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| pilot-pplx-512 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-512 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-512 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-pplx-512 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-512 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-pplx-512 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-512 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-512 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-512 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-512 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-512 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-512 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-pplx-512 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r2 | companion/borderless-plain | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r2 | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r2 | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| native-r2 | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| native-r2 | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| native-r2 | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| native-r2 | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r2 | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r2 | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r2 | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r2 | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-aligned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| native-r2 | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r2 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r2 | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r2 | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r2 | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | companion/borderless-plain | 6/0 | 2/6 | 0/0 | 2/6 | 0 |
| native-text-r1 | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-text-r1 | companion/prose | 12/0 | 0/0 | 8/12 | 4/12 | 0 |
| native-text-r1 | companion/ruled-control | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| native-text-r1 | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| native-text-r1 | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| native-text-r1 | silver/merged-table | 5/0 | 0/5 | 0/0 | 0/5 | 0 |
| native-text-r1 | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/multilevel-table | 5/0 | 0/5 | 0/0 | 0/5 | 0 |
| native-text-r1 | silver/reading-order | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| native-text-r1 | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | silver/sidebar | 5/0 | 0/0 | 2/5 | 3/5 | 0 |
| native-text-r1 | silver/three-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| native-text-r1 | silver/two-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| native-text-r1 | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-text-r1 | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/table-bordered | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-text-r1 | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| native-text-r1 | structure/table-merged | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-text-r1 | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-text-r1 | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-text-r1 | structure/two-column-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| native-text-r1 | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | companion/borderless-plain | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r3 | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| native-r3 | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| native-r3 | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| native-r3 | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| native-r3 | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| native-r3 | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r3 | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| native-r3 | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| native-r3 | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r3 | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-aligned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| native-r3 | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| native-r3 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| native-r3 | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| native-r3 | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| native-r3 | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| pilot-flash-512 | companion/borderless-plain | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-flash-512 | companion/borderless-wrap | 4/0 | 3/4 | 0/0 | 3/4 | 0 |
| pilot-flash-512 | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-512 | companion/ruled-control | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-512 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-512 | silver/merged-table | 2/0 | 1/2 | 0/0 | 1/2 | 0 |
| pilot-flash-512 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/multilevel-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-512 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-512 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-flash-512 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-luna-512 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-512 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-512 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-luna-512 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-512 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-luna-512 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-512 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-512 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-512 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-512 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-512 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-luna-512 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-flash-256 | companion/borderless-plain | 4/0 | 1/4 | 0/0 | 1/4 | 0 |
| pilot-flash-256 | companion/borderless-wrap | 4/0 | 1/4 | 0/0 | 1/4 | 0 |
| pilot-flash-256 | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-256 | companion/ruled-control | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-256 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-256 | silver/merged-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-256 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/multilevel-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-256 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-256 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-flash-256 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-luna-256 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-256 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-256 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-luna-256 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-256 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-luna-256 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-256 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-256 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-256 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-256 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-256 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-luna-256 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-pplx-256 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-256 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-256 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-pplx-256 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-256 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-pplx-256 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-256 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-256 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-256 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-256 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-256 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-256 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-pplx-256 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-flash-1024 | companion/borderless-plain | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-flash-1024 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-flash-1024 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-flash-1024 | companion/ruled-control | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-1024 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-flash-1024 | silver/merged-table | 2/0 | 1/2 | 0/0 | 1/2 | 0 |
| pilot-flash-1024 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/multilevel-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-flash-1024 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-flash-1024 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-flash-1024 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-luna-1024 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-1024 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-luna-1024 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-luna-1024 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-1024 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-luna-1024 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-1024 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-luna-1024 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-luna-1024 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-luna-1024 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-luna-1024 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-pplx-1024 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-1024 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-pplx-1024 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-pplx-1024 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-1024 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-pplx-1024 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-1024 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-pplx-1024 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-1024 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-1024 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-pplx-1024 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-pplx-1024 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-pplx-1024 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-repair-flash-c1 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-repair-flash-c1 | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-repair-flash-c1 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-repair-flash-c1 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-flash-c1 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-repair-flash-c1 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-flash-c1 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-flash-c1 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | silver/sidebar | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-flash-c1 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-flash-c1 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-flash-c1 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c1 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-flash-c1 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-luna-c1 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-repair-luna-c1 | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-repair-luna-c1 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-repair-luna-c1 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-luna-c1 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c1 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c1 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c1 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c1 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c1 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-repair-luna-c1 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-luna-c1 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c1 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-luna-c1 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c1 | silver/rotated-page | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-luna-c1 | silver/sidebar | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-luna-c1 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-luna-c1 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-luna-c1 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c1 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-luna-c1 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-pplx-c1 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-repair-pplx-c1 | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-repair-pplx-c1 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-repair-pplx-c1 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-pplx-c1 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c1 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c1 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c1 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c1 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c1 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-repair-pplx-c1 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-pplx-c1 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c1 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-pplx-c1 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-pplx-c1 | silver/rotated-page | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-pplx-c1 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c1 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-pplx-c1 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-pplx-c1 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c1 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-pplx-c1 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-repair-flash-c3 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-repair-flash-c3 | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-repair-flash-c3 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-repair-flash-c3 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-flash-c3 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c3 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c3 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c3 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c3 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c3 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-repair-flash-c3 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-flash-c3 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c3 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-flash-c3 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-flash-c3 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c3 | silver/sidebar | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-flash-c3 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-flash-c3 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-flash-c3 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-flash-c3 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-flash-c3 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-luna-c3 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-repair-luna-c3 | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-repair-luna-c3 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-repair-luna-c3 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-luna-c3 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c3 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c3 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c3 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c3 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c3 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-repair-luna-c3 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-luna-c3 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c3 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-luna-c3 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-luna-c3 | silver/rotated-page | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-luna-c3 | silver/sidebar | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-luna-c3 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-luna-c3 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c3 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-luna-c3 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-luna-c3 | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-pplx-c3 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-repair-pplx-c3 | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-repair-pplx-c3 | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-repair-pplx-c3 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-pplx-c3 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-repair-pplx-c3 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-pplx-c3 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-repair-pplx-c3 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-pplx-c3 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | silver/sidebar | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-pplx-c3 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-repair-pplx-c3 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-repair-pplx-c3 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-repair-pplx-c3 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-oriented-pplx-256 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-oriented-pplx-256 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-oriented-pplx-256 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-oriented-pplx-256 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-oriented-pplx-256 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-oriented-pplx-256 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-oriented-pplx-256 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-oriented-pplx-256 | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-oriented-pplx-256 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-oriented-pplx-256 | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-oriented-pplx-256 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-oriented-pplx-256 | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-oriented-pplx-256 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-pplx-minimal | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-pplx-minimal | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-pplx-minimal | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-gated-pplx-minimal | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-pplx-minimal | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-pplx-minimal | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-pplx-minimal | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-pplx-minimal | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-minimal | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-pplx-minimal | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-pplx-relational | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-pplx-relational | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-pplx-relational | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-gated-pplx-relational | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-pplx-relational | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-pplx-relational | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-pplx-relational | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-pplx-relational | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-pplx-relational | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-pplx-relational | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-luna-1024 | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-luna-1024 | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-luna-1024 | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-gated-luna-1024 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-luna-1024 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-luna-1024 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-luna-1024 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-luna-1024 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-luna-1024 | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-luna-1024 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-flash-512 | companion/borderless-plain | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-gated-flash-512 | companion/borderless-wrap | 4/0 | 3/4 | 0/0 | 3/4 | 0 |
| pilot-gated-flash-512 | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-flash-512 | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-flash-512 | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-flash-512 | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-flash-512 | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-flash-512 | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-flash-512 | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-gated-flash-512 | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-adaptive-pplx | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-adaptive-pplx | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-adaptive-pplx | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-adaptive-pplx | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-adaptive-pplx | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-pplx | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-pplx | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-pplx | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-pplx | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-pplx | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-adaptive-pplx | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-adaptive-pplx | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-pplx | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-adaptive-pplx | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-adaptive-pplx | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-pplx | silver/sidebar | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-adaptive-pplx | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-adaptive-pplx | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-adaptive-pplx | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-adaptive-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-adaptive-luna | companion/borderless-plain | 4/0 | 3/4 | 0/0 | 3/4 | 0 |
| pilot-adaptive-luna | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-adaptive-luna | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-adaptive-luna | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-adaptive-luna | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-adaptive-luna | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-adaptive-luna | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-adaptive-luna | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/sidebar | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-adaptive-luna | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-adaptive-luna | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-adaptive-luna | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-adaptive-luna | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-text-pplx | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-text-pplx | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-text-pplx | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-text-pplx | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-text-pplx | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-text-pplx | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-text-pplx | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-text-pplx | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-text-pplx | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-text-pplx | silver/two-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-text-pplx | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-text-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-text-luna | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-text-luna | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-text-luna | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-text-luna | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-text-luna | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-text-luna | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-text-luna | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/multilevel-table | 2/0 | 1/2 | 0/0 | 1/2 | 0 |
| pilot-text-luna | silver/reading-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-text-luna | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-text-luna | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-luna | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-text-luna | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-text-flash | companion/borderless-plain | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-text-flash | companion/borderless-wrap | 4/0 | 0/4 | 0/0 | 0/4 | 0 |
| pilot-text-flash | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-text-flash | companion/ruled-control | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-text-flash | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-text-flash | silver/merged-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-text-flash | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/multilevel-table | 2/0 | 0/2 | 0/0 | 0/2 | 0 |
| pilot-text-flash | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-text-flash | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-text-flash | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| pilot-frontier-haiku | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-frontier-haiku | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-frontier-haiku | companion/prose | 2/0 | 0/0 | 2/2 | 0/2 | 0 |
| pilot-frontier-haiku | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-haiku | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-frontier-haiku | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-haiku | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-haiku | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/three-column | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| pilot-frontier-haiku | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-haiku | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-frontier-haiku | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-frontier-sonnet | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-frontier-sonnet | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-frontier-sonnet | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-frontier-sonnet | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-sonnet | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-frontier-sonnet | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-sonnet | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-sonnet | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-sonnet | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-frontier-sonnet | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-frontier-opus | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-frontier-opus | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-frontier-opus | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-frontier-opus | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-opus | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-frontier-opus | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-opus | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-frontier-opus | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-frontier-opus | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-frontier-opus | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-reading-pplx | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-reading-pplx | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-reading-pplx | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-gated-reading-pplx | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reading-pplx | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-reading-pplx | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reading-pplx | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reading-pplx | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-reading-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-reading-luna | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-reading-luna | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-reading-luna | companion/prose | 2/0 | 0/0 | 1/2 | 1/2 | 0 |
| pilot-gated-reading-luna | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reading-luna | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-reading-luna | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reading-luna | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reading-luna | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reading-luna | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-reading-luna | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | companion/borderless-plain | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-reviewed-pplx | companion/borderless-wrap | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| pilot-gated-reviewed-pplx | companion/prose | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-reviewed-pplx | companion/ruled-control | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reviewed-pplx | silver/cropped-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/duplicate-overprint | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/footnotes | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/form-fields | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/headers-footers | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/math | 2/0 | 0/0 | 0/2 | 2/2 | 0 |
| pilot-gated-reviewed-pplx | silver/merged-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reviewed-pplx | silver/mixed-panels | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/multilevel-table | 2/0 | 2/2 | 0/0 | 2/2 | 0 |
| pilot-gated-reviewed-pplx | silver/reading-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/rotated-page | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/sidebar | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/three-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/two-column | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | silver/vector-noise | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| pilot-gated-reviewed-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-native-ocr | companion/borderless-plain | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| full-native-ocr | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| full-native-ocr | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| full-native-ocr | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-native-ocr | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-native-ocr | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-native-ocr | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-native-ocr | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-native-ocr | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-native-ocr | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-native-ocr | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-native-ocr | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-native-ocr | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-native-ocr | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-native-ocr | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-native-ocr | structure/table-borderless-aligned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-native-ocr | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-native-ocr | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-native-ocr | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-native-ocr | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-native-ocr | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-native-ocr | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-native-ocr | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-native-ocr | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-native-ocr | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-native-ocr | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-assembly-pplx | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-assembly-pplx | companion/prose | 12/0 | 0/0 | 10/12 | 2/12 | 0 |
| full-assembly-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-assembly-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-assembly-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-assembly-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-assembly-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-assembly-pplx | silver/reading-order | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-assembly-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | silver/three-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-assembly-pplx | silver/two-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-assembly-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-assembly-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-assembly-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-assembly-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-assembly-pplx | structure/rotated-columns | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| full-assembly-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-assembly-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-assembly-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-assembly-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-assembly-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-assembly-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-assembly-pplx | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-assembly-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-assembly-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-assembly-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-assembly-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-assembly-pplx | structure/two-column-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| full-assembly-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-gated-pplx | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-gated-pplx | companion/prose | 12/0 | 0/0 | 4/12 | 8/12 | 0 |
| full-gated-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-gated-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-gated-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-gated-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-pplx | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-gated-reading-pplx | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-gated-reading-pplx | companion/prose | 12/0 | 0/0 | 9/12 | 3/12 | 0 |
| full-gated-reading-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-gated-reading-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-gated-reading-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-gated-reading-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-reading-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-reading-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reading-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reading-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reading-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reading-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reading-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reading-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reading-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reading-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reading-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reading-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reading-pplx | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-reading-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reading-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reading-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reading-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reading-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reading-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-gated-luna | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-gated-luna | companion/prose | 12/0 | 0/0 | 6/12 | 6/12 | 0 |
| full-gated-luna | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-gated-luna | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-gated-luna | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-gated-luna | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-luna | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-luna | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-luna | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-luna | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-luna | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-luna | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-luna | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-luna | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-luna | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-luna | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-luna | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-luna | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-luna | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-luna | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-luna | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-luna | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-luna | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-luna | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-luna | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | companion/borderless-plain | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| full-gated-flash | companion/borderless-wrap | 6/0 | 5/6 | 0/0 | 5/6 | 0 |
| full-gated-flash | companion/prose | 12/0 | 0/0 | 2/12 | 10/12 | 0 |
| full-gated-flash | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-gated-flash | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-gated-flash | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-gated-flash | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-flash | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-flash | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/three-column | 5/0 | 0/0 | 3/5 | 2/5 | 0 |
| full-gated-flash | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-flash | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-flash | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-flash | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-flash | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-flash | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-flash | structure/table-borderless | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-flash | structure/table-borderless-aligned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-flash | structure/table-borderless-rotate-180 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-flash | structure/table-borderless-rotate-270 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-flash | structure/table-borderless-rotate-90 | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-flash | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-flash | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-flash | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-flash | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-flash | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-flash | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-flash | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-adaptive-pplx | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| full-adaptive-pplx | companion/prose | 12/0 | 0/0 | 12/12 | 0/12 | 0 |
| full-adaptive-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-adaptive-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-adaptive-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-adaptive-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-adaptive-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-adaptive-pplx | silver/reading-order | 5/0 | 0/0 | 4/5 | 1/5 | 0 |
| full-adaptive-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | silver/sidebar | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-adaptive-pplx | silver/three-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-adaptive-pplx | silver/two-column | 5/0 | 0/0 | 4/5 | 1/5 | 0 |
| full-adaptive-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-adaptive-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-adaptive-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-adaptive-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-adaptive-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-adaptive-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-adaptive-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-adaptive-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-adaptive-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-adaptive-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-adaptive-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-adaptive-pplx | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-adaptive-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-adaptive-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-adaptive-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-adaptive-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-adaptive-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-adaptive-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-gated-reviewed-pplx | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-gated-reviewed-pplx | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| full-gated-reviewed-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-gated-reviewed-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-gated-reviewed-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-gated-reviewed-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-gated-reviewed-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-gated-reviewed-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-gated-reviewed-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-gated-reviewed-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-frontier-haiku | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-frontier-haiku | companion/prose | 12/0 | 0/0 | 10/12 | 2/12 | 0 |
| full-frontier-haiku | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-frontier-haiku | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-frontier-haiku | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-frontier-haiku | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-frontier-haiku | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-frontier-haiku | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | silver/three-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-frontier-haiku | silver/two-column | 5/0 | 0/0 | 2/5 | 3/5 | 0 |
| full-frontier-haiku | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-haiku | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-haiku | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-haiku | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-haiku | structure/rotated-columns | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| full-frontier-haiku | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-haiku | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-haiku | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-haiku | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-haiku | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-haiku | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-haiku | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-frontier-haiku | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-haiku | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-haiku | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-haiku | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-haiku | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-haiku | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-frontier-sonnet | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-frontier-sonnet | companion/prose | 12/0 | 0/0 | 0/12 | 11/12 | 1 |
| full-frontier-sonnet | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-frontier-sonnet | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-frontier-sonnet | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-frontier-sonnet | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-frontier-sonnet | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-frontier-sonnet | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-sonnet | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-sonnet | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-sonnet | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-sonnet | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-sonnet | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-sonnet | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-sonnet | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-sonnet | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-sonnet | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-sonnet | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-sonnet | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-frontier-sonnet | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-sonnet | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-sonnet | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-sonnet | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-sonnet | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-sonnet | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-frontier-opus | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-frontier-opus | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| full-frontier-opus | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-frontier-opus | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-frontier-opus | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-frontier-opus | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-frontier-opus | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-frontier-opus | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-frontier-opus | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-opus | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-opus | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-opus | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-opus | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-opus | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-opus | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-opus | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-opus | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-opus | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-opus | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-frontier-opus | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-opus | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-frontier-opus | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-frontier-opus | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-opus | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-frontier-opus | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-cascade-pplx | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-cascade-pplx | companion/prose | 12/0 | 0/0 | 10/12 | 2/12 | 0 |
| full-cascade-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-cascade-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-cascade-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-cascade-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-cascade-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-cascade-pplx | silver/reading-order | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-cascade-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | silver/three-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-cascade-pplx | silver/two-column | 5/0 | 0/0 | 5/5 | 0/5 | 0 |
| full-cascade-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-cascade-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-cascade-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-cascade-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-cascade-pplx | structure/rotated-columns | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| full-cascade-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-cascade-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-cascade-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-cascade-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-cascade-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-cascade-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-cascade-pplx | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-cascade-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-cascade-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-cascade-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-cascade-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-cascade-pplx | structure/two-column-order | 1/0 | 0/0 | 1/1 | 0/1 | 0 |
| full-cascade-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-pplx | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-pplx | companion/prose | 12/0 | 0/0 | 4/12 | 8/12 | 0 |
| full-column-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-column-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-column-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-column-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/table-borderless-scanned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-reviewed-pplx | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-reviewed-pplx | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| full-column-reviewed-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-column-reviewed-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-column-reviewed-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-column-reviewed-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-reviewed-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/table-borderless-scanned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-reviewed-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-reviewed-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-compact-pplx | companion/borderless-wrap | 6/0 | 3/6 | 0/0 | 3/6 | 0 |
| full-compact-pplx | companion/prose | 12/0 | 0/0 | 4/12 | 8/12 | 0 |
| full-compact-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-compact-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-compact-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-compact-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-compact-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-compact-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-pplx | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-compact-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-compact-text-pplx | companion/borderless-wrap | 6/0 | 0/6 | 0/0 | 0/6 | 0 |
| full-compact-text-pplx | companion/prose | 12/0 | 0/0 | 5/12 | 7/12 | 0 |
| full-compact-text-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-compact-text-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-compact-text-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-compact-text-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-compact-text-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-compact-text-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-compact-text-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-text-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-text-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-text-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-text-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-text-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-text-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-text-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-text-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-text-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-text-pplx | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 0 |
| full-compact-text-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-text-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-compact-text-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-compact-text-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-text-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-compact-text-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-compact-pplx | companion/borderless-wrap | 6/0 | 3/6 | 0/0 | 3/6 | 0 |
| full-column-compact-pplx | companion/prose | 12/0 | 0/0 | 4/12 | 8/12 | 0 |
| full-column-compact-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-column-compact-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-column-compact-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-column-compact-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-compact-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-compact-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/table-borderless-scanned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-compact-reviewed-pplx | companion/borderless-wrap | 6/0 | 3/6 | 0/0 | 3/6 | 0 |
| full-column-compact-reviewed-pplx | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| full-column-compact-reviewed-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-column-compact-reviewed-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-column-compact-reviewed-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-column-compact-reviewed-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-reviewed-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/table-borderless-scanned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-reviewed-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-reviewed-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-compact-haiku-review | companion/borderless-wrap | 6/0 | 3/6 | 0/0 | 3/6 | 0 |
| full-column-compact-haiku-review | companion/prose | 12/0 | 0/0 | 10/12 | 2/12 | 0 |
| full-column-compact-haiku-review | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-column-compact-haiku-review | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-column-compact-haiku-review | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-column-compact-haiku-review | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-haiku-review | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/table-borderless-scanned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/table-wrapped-records | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| full-column-compact-haiku-review | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-haiku-review | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-haiku-review | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-compact-sonnet | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-compact-sonnet | companion/prose | 12/0 | 0/0 | 1/12 | 6/12 | 5 |
| full-column-compact-sonnet | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-column-compact-sonnet | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-column-compact-sonnet | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-column-compact-sonnet | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-compact-sonnet | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/multilevel-table | 5/0 | 4/5 | 0/0 | 4/5 | 1 |
| full-column-compact-sonnet | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/three-column | 5/0 | 0/0 | 1/5 | 4/5 | 0 |
| full-column-compact-sonnet | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-compact-sonnet | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-sonnet | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-sonnet | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-sonnet | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-sonnet | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-sonnet | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-sonnet | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-sonnet | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-sonnet | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-sonnet | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-sonnet | structure/table-borderless-scanned | 1/0 | 0/1 | 0/0 | 0/1 | 1 |
| full-column-compact-sonnet | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-sonnet | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-compact-sonnet | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-compact-sonnet | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-sonnet | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-compact-sonnet | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | companion/borderless-plain | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-readable-reviewed-pplx | companion/borderless-wrap | 6/0 | 6/6 | 0/0 | 6/6 | 0 |
| full-column-readable-reviewed-pplx | companion/prose | 12/0 | 0/0 | 0/12 | 12/12 | 0 |
| full-column-readable-reviewed-pplx | companion/ruled-control | 4/0 | 4/4 | 0/0 | 4/4 | 0 |
| full-column-readable-reviewed-pplx | silver/cropped-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/duplicate-overprint | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/footnotes | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/form-fields | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/headers-footers | 10/0 | 0/0 | 0/10 | 10/10 | 0 |
| full-column-readable-reviewed-pplx | silver/image-flow | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/image-inset | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/math | 40/0 | 0/0 | 0/40 | 40/40 | 0 |
| full-column-readable-reviewed-pplx | silver/merged-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/mixed-panels | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/multilevel-table | 5/0 | 5/5 | 0/0 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/reading-order | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/rotated-page | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/sidebar | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/three-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/two-column | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | silver/vector-noise | 5/0 | 0/0 | 0/5 | 5/5 | 0 |
| full-column-readable-reviewed-pplx | structure/accessible-actualtext | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/corpus-f1040 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/corpus-nics-background-checks-2015-11 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/corpus-pdfium-type3 | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/corpus-senate-expenditures | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/corpus-usrguide | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/footnotes-and-page-furniture | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/image-only | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/images-and-vectors | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/links-and-outline | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/math-actualtext | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/omml-equations | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/positioned-math | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/rotated-columns | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/rtl-visual-glyph-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/table-bordered | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/table-borderless | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/table-borderless-aligned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/table-borderless-rotate-180 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/table-borderless-rotate-270 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/table-borderless-rotate-90 | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/table-borderless-scanned | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/table-merged | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/table-wrapped-records | 1/0 | 1/1 | 0/0 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/tagged-reading-order | 0/1 | 0/0 | 0/0 | 0/0 | 0 |
| full-column-readable-reviewed-pplx | structure/text-structure-and-literals | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/two-column-order | 1/0 | 0/0 | 0/1 | 1/1 | 0 |
| full-column-readable-reviewed-pplx | structure/unicode-cmap-and-emoji | 0/1 | 0/0 | 0/0 | 0/0 | 0 |

</details>

Incomplete frozen runs (not scored):

No completed report exists for these frozen runs; they may be running or aborted. Result-file counts are progress evidence only. Accuracy, charges, wall/CPU and RSS remain unknown. Jobs not yet frozen by the runner are outside this observed inventory.

| Run | Policy | Model | Gate review model | column_consensus | compact_packet | readable_packet | Planned pages | Result files | Source contract matches |
|---|---|---|---|---|---|---|---:|---:|---|
| None observed | — | — | — | False | False | False | — | — | — |

Measurement and frozen provenance:

- `native-r1`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "8f7920a0a1c27b64696238fbea55f3a45d7178b16087179b9d1b560ed0ca4da0", "pipeline_run.py": "08eabdb0717f044856b0e35456a7b04267378ff049f01e5b7a096a87965a889d"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-pplx-512`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "8f7920a0a1c27b64696238fbea55f3a45d7178b16087179b9d1b560ed0ca4da0", "pipeline_run.py": "3fcd576461a437ced1c8e6b65c915c52e8b5ca0ebbc0430c67424307d21fb562"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `native-r2`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `native-text-r1`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `native-r3`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-flash-512`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-luna-512`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-flash-256`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-luna-256`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-pplx-256`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_run.py": "0e8ecb2c50ddecb2cc2f290b089b2bfe79ba0111f8e1f5db2f08deb08c37977c"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-flash-1024`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "1e45acff39062373e618ac3dfef4d6fedb978800198c67a9b675a0d76daac5f5"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-luna-1024`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-pplx-1024`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-repair-flash-c1`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-repair-luna-c1`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-repair-pplx-c1`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-repair-flash-c3`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-repair-luna-c3`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-repair-pplx-c3`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "02c4edfb3338218a46f8b336072778a1a868a8a6d11bf5cde26361f438afec37"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-oriented-pplx-256`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-gated-pplx-minimal`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-gated-pplx-relational`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-gated-luna-1024`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-gated-flash-512`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-adaptive-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-adaptive-luna`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-text-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-text-luna`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-text-flash`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-frontier-haiku`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "09e26463afc4c90678ba834ce46b8b478d85046e82f2b06bd5b18738bddc91f3", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "ad24156e5a2d9832e52b765ed13356b236e48c1d7483e787f0795de6304cc6d2"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-frontier-sonnet`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "1f9bbaee008f3063a4c8bd927b36a094336f637c06aeec32a0b7425cfe1964f5"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-frontier-opus`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "5e679ff5fad00a534c9a30356c42c960a16c320936a127fab2d60a78af829ff7"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-gated-reading-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "5e679ff5fad00a534c9a30356c42c960a16c320936a127fab2d60a78af829ff7"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-gated-reading-luna`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "5e679ff5fad00a534c9a30356c42c960a16c320936a127fab2d60a78af829ff7"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `pilot-gated-reviewed-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "5e679ff5fad00a534c9a30356c42c960a16c320936a127fab2d60a78af829ff7"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-native-ocr`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "1f5f92233fffb1309eca9d4f7f9b9e87f1c6647b6fab31f10797af4fa2d61189", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-assembly-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "1f5f92233fffb1309eca9d4f7f9b9e87f1c6647b6fab31f10797af4fa2d61189", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-gated-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "1f5f92233fffb1309eca9d4f7f9b9e87f1c6647b6fab31f10797af4fa2d61189", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-gated-reading-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "1f5f92233fffb1309eca9d4f7f9b9e87f1c6647b6fab31f10797af4fa2d61189", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-gated-luna`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "1f5f92233fffb1309eca9d4f7f9b9e87f1c6647b6fab31f10797af4fa2d61189", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-gated-flash`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-adaptive-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-gated-reviewed-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-frontier-haiku`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-frontier-sonnet`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-frontier-opus`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-cascade-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-column-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_column_consensus.py": "6082527e48dc22c6ea86a9d8b51079d8ea2cfcc81fb72d495b28bfd3a59fb3cc", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-column-reviewed-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_column_consensus.py": "6082527e48dc22c6ea86a9d8b51079d8ea2cfcc81fb72d495b28bfd3a59fb3cc", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-compact-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_compact_packet.py": "e96a93d0f91778b32ac3962541d8261f4226fdffe784a159a66d04db2b612e27", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-compact-text-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_compact_packet.py": "e96a93d0f91778b32ac3962541d8261f4226fdffe784a159a66d04db2b612e27", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-column-compact-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_column_consensus.py": "6082527e48dc22c6ea86a9d8b51079d8ea2cfcc81fb72d495b28bfd3a59fb3cc", "pipeline_compact_packet.py": "e96a93d0f91778b32ac3962541d8261f4226fdffe784a159a66d04db2b612e27", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8e4b26ea64e41977914f392fb04ecab8b04f631b73693d67be6ebffeef2b0684", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-column-compact-reviewed-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_column_consensus.py": "6082527e48dc22c6ea86a9d8b51079d8ea2cfcc81fb72d495b28bfd3a59fb3cc", "pipeline_compact_packet.py": "e96a93d0f91778b32ac3962541d8261f4226fdffe784a159a66d04db2b612e27", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "28adb733e62e27236cd0d7060d3b5d6ba205c2cc4fa89d45d6ac270d51680e88", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-column-compact-haiku-review`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_column_consensus.py": "6082527e48dc22c6ea86a9d8b51079d8ea2cfcc81fb72d495b28bfd3a59fb3cc", "pipeline_compact_packet.py": "e96a93d0f91778b32ac3962541d8261f4226fdffe784a159a66d04db2b612e27", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "28adb733e62e27236cd0d7060d3b5d6ba205c2cc4fa89d45d6ac270d51680e88", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-column-compact-sonnet`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_column_consensus.py": "6082527e48dc22c6ea86a9d8b51079d8ea2cfcc81fb72d495b28bfd3a59fb3cc", "pipeline_compact_packet.py": "e96a93d0f91778b32ac3962541d8261f4226fdffe784a159a66d04db2b612e27", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "28adb733e62e27236cd0d7060d3b5d6ba205c2cc4fa89d45d6ac270d51680e88", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
- `full-column-readable-reviewed-pplx`: psutil.Process RSS sampled every 100 ms; process_time CPU; one process, no subprocesses; frozen environment/code: `{"code_sha256": {"corpus_routes.py": "9ab3a774a835e21481e6e87d1bad03234eba16013737f483908d46e062ca6c40", "decision_evidence_designs.py": "b25041384f9c2ca313a499cf31f10dbcd314fccc05a01271d6351ae08f417f30", "decision_hosted.py": "dda278ddc7dec74aeea7c4a0265a98d7389023466ed7fb24340c6507d46dd1be", "pipeline_admission.py": "08e96bec64d965cc0edd5480e6d00c8be92cd59b25fb85d98052e4c734311069", "pipeline_assembly.py": "1a2eb3927e9d634f51a01715e05fc82c01be011770af08851e8306b7c5523471", "pipeline_column_consensus.py": "6082527e48dc22c6ea86a9d8b51079d8ea2cfcc81fb72d495b28bfd3a59fb3cc", "pipeline_frontier.py": "eb209bf91ffadbeb8079f0349d7fc346a1c39ed407f9eb03075a7815ecf87175", "pipeline_readable_packet.py": "9329b3b40f02785483a59bede4d9ad910c13dddfe84ce181f5374da5474c0701", "pipeline_repair.py": "f02fa6a537000552d73e403db67aacd9a671a763a6361c13978cc9a67d15f025", "pipeline_routing.py": "6e9ae131dfb25c0004aed3949f1ce2ef1c598a20bf730b9fd1c9cbaec1de7f87", "pipeline_run.py": "8b2c1fe769382204a686985cfa566059223b034cf6dac8c47a6ff9e264923077", "rolling_rows.py": "2a8546465a6279c67b73c6a63aaf078eebf39fd7fae92c02f1073a755d1cf884", "rolling_topology.py": "c08047e2a86d9af9f174d999ba2d51e7d755d896db370e0e1ed8e413724aedb1", "silver.py": "0a054a0c70f00418742f1279696baa154f386e9a1f8ea47d474dfa83555b17f1", "silver_structure.py": "2972d875718eeac6399962b4682469d85fbdf76caba5e8401ab3b2dddf2addb4"}, "concurrency": 1, "logical_cpus": 8, "platform": "Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44", "python": "3.14.7"}`. Overall wall includes API waiting; CPU and RSS cover the current process only. Remote GPU and separate stage resource totals are unmeasured.
