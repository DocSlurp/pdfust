# P003 page-scoped render reuse

The isolated prototype preserved every JPEG90 crop byte, decoded RGB pixel hash, and metadata field while reducing fully amortized local CPU time by 83.6–83.8% (6.09–6.18×) in two fixed DEV passes. It is ready for a separately authorized integration, but no candidate runner or active paid treatment was changed.

The current `p003_candidate_run._rerender` hashes/opens the source PDF, renders a full page at a longest edge of 4095 pixels, decodes that raster, and produces one crop for every crop/edge request. The prototype performs the same authenticated full-page rendering once, retains one RGB page, and repeats the identical BICUBIC EXTENT transform and JPEG quality90 encode for each crop and requested edge. Every output is generated directly from the full-page raster; there is no chained resize or global cache. PDF hash, page number, original rotation and display viewport must match. Resident RGB admission is bounded to 4095²×3 bytes (50.31 MB), separately from measured transient native rendering, PNG, JPEG and verification allocations. Closing the page releases the retained image and refuses subsequent crops.

The independently trusted input was `pipeline-p003/screen-crops-luna-1024-pinned-r0`, with its matching external trusted-code map. All 16 records are retained. Fourteen operational pages contain 19 original crop viewports, producing 133 outputs per pass at edges 128/256/400/512/768/1024/1200. Pages `p42049db34e230ce77d75` and `p1bfa52a41a5e15015698` have status `ok` and zero detected crops, so they bypass rendering in both arms. There are no baseline errors. No references, gold, provider requests or credentials were used.

| Local phase | Pass 1 wall / CPU, seconds | Pass 2 wall / CPU, seconds |
|---|---:|---:|
| Original fresh page render for every crop/edge | 62.196 / 60.343 | 63.875 / 62.177 |
| Reuse page-render setup | 6.732 / 6.473 | 7.071 / 6.844 |
| Reuse warmed crop operations | 3.408 / 3.217 | 3.391 / 3.272 |
| Reuse fully amortized total | 10.226 / 9.772 | 10.557 / 10.210 |

Original peak sampled RSS was 249.45/251.60 MB; reuse was 228.96/202.04 MB. Including fresh child process startup, summed wall cost was 65.36/67.06 seconds original versus 13.14/13.79 seconds reuse. Total and warmed operation intervals include the matched decoded-RGB hash verification overhead. Setup contains PDF authentication/open/render/decode; fully amortized total additionally includes warmed cropping, verification and page cleanup. Thus warmed cropping is explicitly not presented as the total cost.

Each page/arm used a fresh single subprocess with a fixed seeded balanced ordering opportunity and two predeclared passes. CPU uses `process_time`, including native threads; RSS uses psutil sampling every 100 ms. The machine exposes 8 logical CPUs. The machine was shared with the active research campaign; three synthetic renderer tests also ran during the first pass. These are contended local preprocessing observations, with OS file caches left intact. Both passes independently show the same large reduction, but two passes do not establish a production latency distribution. Renderer versions and source/code hashes are frozen with the raw evidence. No full-pipeline throughput or provider caching benefit is claimed; those rates remain undefined.

The acceptance gate was exact encoded outputs, decoded pixels and metadata, with at least 10% amortized CPU reduction. All 28 page pairs / 266 crop-edge comparisons passed and both passes exceeded the CPU gate. Three focused tests additionally compare actual returned byte strings on full/fractional crops at every edge and rotations 0/90, and check PDF/rotation/memory admission and closed-image behavior. Ruff passes.

Raw frozen records, job bodies, complete subprocess stdout/stderr, per-arm resource measurements and output hash inventories are retained locally in `bench/results/pdf-master-artifacts/p003-render-reuse-v1/`. Prototype code SHA256 is `566813a917780de997ae6724e472d2e33fffaadeb396d6dcea8d92431f5d905a`. Reproduce using the same environment:

```sh
.venv/bin/python -m bench.p003_render_reuse \
  --baseline bench/results/pdf-master-artifacts/pipeline-p003/screen-crops-luna-1024-pinned-r0 \
  --trusted-code bench/results/pdf-master-artifacts/pipeline-p003/trusted-code/screen-crops-luna-1024-pinned-r0.json \
  --output bench/results/pdf-master-artifacts/p003-render-reuse-fresh --repeats 2
```

A future candidate-runner integration can instantiate `PageRender(record,page_result)` once per page, call `.crop(crop,edge)` for all admitted crop/edge choices, and close it in `finally` before proceeding to another page. The experiment leaves that integration separate from currently frozen paid treatments.
