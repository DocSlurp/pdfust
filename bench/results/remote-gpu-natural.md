# Native natural DEV comparison

The source-only stage preserves all96 existing L011 request bodies and PNGs, covering24 overlapping regions and four image/context arms on one Senate page. No model responses or review references were used to prepare or select these packets. Native results are pending.

Run the verified reporter after retrieving the explicit native result directories:

```sh
python -m bench.remote_natural \
  --source bench/results/pdf-master-artifacts/decisions/lowlevel-v1/natural-source \
  --references-dir bench/results/pdf-master-artifacts/decisions/lowlevel-v1/natural-matrix \
  --packets .scratch/remote-gpu-20261009/r001/stage/natural/manifest.json \
  --run Flash=PATH_TO_FLASH_OUTPUT \
  --run Clef=PATH_TO_CLEF_OUTPUT \
  --run PPLX=PATH_TO_PPLX_OUTPUT \
  --run Intern=PATH_TO_INTERN_OUTPUT \
  --markdown bench/results/remote-gpu-natural.md \
  --json .scratch/remote-gpu-20261009/r001/results/natural-report.json
```

The reporter verifies exact source requests, images, stage inventory and every returned request hash before opening the separate root-local review file. It reports provisional full-source and admitted-scope agreement separately, with complete planned denominators and explicit failed/missing/malformed counts. These source-aware references are not independently adjudicated structural gold. The cohort does not measure generalization across documents or producers; scope and fixed-edge resolution jointly affect legibility.
