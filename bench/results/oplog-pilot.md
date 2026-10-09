# R002 coordinate edit-session pilot

Ten prespecified DEV regions per model, whole-region 512 px images, bounded edit menus. Initial header band and column hypotheses are supplied by the harness. This is conditional cell assembly, not independent page extraction. Candidate oracle is unmeasured.

| Model | Group exact | Slot exact / scorable | Source placement | Mean pair P/R | Conserved |
| --- | ---: | ---: | ---: | ---: | ---: |
| openai/gpt-6-luna-decisions | 5/10 | 5/9 | 66/76 | 1.000/0.752 | 10/10 |
| perplexity/pplx-decider-v1.1-27b | 6/10 | 6/9 | 69/76 | 1.000/0.812 | 10/10 |

| Model | Provider requests | USD | Region-pages/$ | Region-pages/min | Session endings |
| --- | ---: | ---: | ---: | ---: | --- |
| openai/gpt-6-luna-decisions | 41 | 0.012120 | 825 | 45.8 | {'finished': 9, 'loop': 1} |
| perplexity/pplx-decider-v1.1-27b | 42 | 0.003173 | 3,152 | 32.2 | {'abstained': 8, 'finished': 1, 'loop': 1} |

Region-pages count complete attempted sessions, including failures to finish, per summed provider charges and serial HTTP time for all edits. Each is a region task, not a full-page conversion. Positive reported charges take precedence; zero/missing charges use retained catalog prices and observed tokens. Local replay does not establish provider caching. Preparation CPU/RAM was not measured in this pilot.

The missing slot annotation stays outside the nine-region slot denominator, with all ten in group exactness. Abstention and loop stops retain words but do not count as successful extraction.
