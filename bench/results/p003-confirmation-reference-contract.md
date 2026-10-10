# P003 fresh confirmation references

The 48-page confirmation set was frozen from source metadata before natural annotation access. It contains 32 new OmniDocBench pages and 16 new authored designs. Known DEV/training/P002 source IDs and known parent groups were excluded by the source preparer; unknown parents were ineligible. Protected heldout directories were not consulted.

| Cohort | Pages | Positive / negative pages | Tables | Scored anchor cells |
| --- | ---: | ---: | ---: | ---: |
| New natural Omni | 32 | 24 / 8 | 50 | 3,866 |
| New authored designs | 16 | 14 / 2 | 16 | 337 |
| Complete confirmation | 48 | 38 / 10 | 66 | 4,203 |

All 48 pages have usable structural references. Natural references use selected official HTML and polygons, projected with the source-frozen scale 0.36 and zero offset/rotation. Authored references retain the separate construction matrices and spans. These references are scoring evidence, never model evidence.

The runtime `manifest.json` remains unchanged. Schema 2 identifies only source metadata, PDF hashes, and the predeclared selection hash, excluding PDF paths and every target. The source dataset SHA is `6a95069917f121c0ab591467606b017f9d1a94077d445ef58fa6ca70440fe3e1`; manifest SHA is `2548256a5289d64e1a0a5d0de1683c6e068fa8db295fce64814f3bb134664b99`. The separately attached `private-targets.json` SHA is `3a4cfc4bb904f171c9d27306e6ce64c4cb35268cfe0f5f7b83f62fbf2889bcb1`.

`bench.p003_confirmation.load_corpus` verifies independently announced source hashes, actual source PDF bytes, authorized official annotation bytes, and construction targets. It rebuilds the selected references before accepting the attachment receipt. Replacing both targets and their receipt cannot authenticate altered references. The P003 reporter dispatches to this loader for the explicit source-only identity; existing corpus identities retain their existing validator.

Offline verification:

```sh
python -m bench.p003_confirmation --directory <pipeline-p003/confirmation48-v1>
```

The primary frozen treatment is PPLX 128 RGB, with same-model repeats and separate 512 RGB/text controls. Luna and Sonnet generation runs retain separate quality and costs. Decision-confirmed quality excludes failed or abstained candidate regions and uses all 48 pages, 66 tables, and 4,203 anchor cells; deterministic no-question regions and retained baseline pipeline quality remain separate. No results have been selected from these references and no inference is performed by the reference attachment or loader.
