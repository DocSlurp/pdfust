# R001: provider charges and verified cleanup

The provider posted **USD 9.727** for this complete GPU wave, including compute, disk and transfer. All five created instances, including the failed bootstrap replacement, are deleted; absence was independently verified at 2026-10-09 21:43:17 UTC. No R001 instance or attached instance disk remains in the provider inventory. The temporary task SSH private key was removed locally after final artifact collection.

| Owned instance | Role | Compute USD | Disk USD | Download USD | Upload USD | Total posted USD |
|---|---|---:|---:|---:|---:|---:|
| 55084071 | Intern runtime isolation | 2.010 | 0.067 | 0.040 | 0.001 | 2.118 |
| 55084862 | Clef / Flash; final PPLX / Intern recovery | 2.296 | 0.078 | 0.326 | 0.006 | 2.706 |
| 55084868 | Failed initial vLLM bootstrap | 0.000 | 0.001 | 0.000 | 0.000 | 0.001 |
| 55084918 | PPLX / Intern / JPT / Nimble | 1.982 | 0.062 | 0.767 | 0.006 | 2.817 |
| 55085144 | Stock vLLM models and shared-server concurrency | 1.743 | 0.058 | 0.282 | 0.002 | 2.085 |

The all-charge-type provider query returned five matching records with `count=total=5` and no continuation token. The amounts above are provider-posted charges observed after deletion, not an assertion that a later invoice cannot settle further. The refused offer created no instance; the failed bootstrap instance remains charged at its reported USD 0.001. Initial failed runs, model downloads, warm idle time, runtime investigation, recovery downloads and teardown are included. None is removed to improve a serving-cost estimate.

The shared ledger replaced the R001 USD 18 reservation with its USD 9.727 reported charge and released USD 8.273 of that reservation. The original reservation remains as historical metadata, not an additional charge. Every older ledger row was preserved. Conservative cumulative campaign accounting is **USD 28.5428416248 of the USD 100 cap**, including **USD 6.05 of older unresolved reservations**. This conservative total combines reported costs, separately labeled catalog estimates and those reservations; it is not all confirmed spending.

Benchmark tables use reported native token usage where supplied, and leave missing PPLX usage unknown. Rental serving rates use measured time and quoted hourly GPU-plus-disk rates. Their warm inputs/USD estimates exclude the lifecycle and transfer costs above. Parallel throughput uses elapsed wall or concurrent span, never summed overlapping latency. Individual model billing is not invented from shared-host time. Conditional page-region inputs are not complete PDF extraction pages or independent documents.

Final artifacts were collected before retirement. Fifty-three retained compressed archives total 98,901,405 bytes at this checkpoint; their paths, byte counts and SHA256 hashes are indexed locally in `.scratch/remote-gpu-20261009/r001/retained-archive-index.json`. Full requests, responses, images, logs, source provenance and receipts remain ignored by Git. Tracked code, tests and Markdown reports are pushed only to private `justsml/pdfust`.

Local accounting receipts: `fleet.json`, `charges-postcleanup-confirmation.json`, `final-accounting.json`, and `reconcile_r001.py` under `.scratch/remote-gpu-20261009/r001/`. The persistent campaign ledger is `bench/results/pdf-master-artifacts/decisions/ledger.json`. Charge-receipt SHA256: `96eb3430853f4cfb0159b952d7f793fb34807d3d92b46c07f19a55704075338d`. No credentials appear in tracked reports.

A later post-deletion check increased the initial USD 9.713 receipt by USD 0.014. Both receipts and the ledger amendment history are retained; the totals above use the newer positive reported charge.
