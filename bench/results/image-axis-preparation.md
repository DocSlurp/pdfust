# Aspect-preserving context30 image grid

All 30 authored DEV context assembly cases and all four vision decision models
are frozen across 54 declared size/axis/representation arms. RGB8, grayscale8
and palette4 remain distinct; there are no quality-based arm exclusions.

- 936 unique provider-admitted batch bodies.
- 468 batch aliases from identical source geometry/pixels/request bytes.
- Zero input, pixel, representation or provider-payload refusals.
- 1,620 per-case image records preserve all declared arms.

The aliases represent the same inputs, not additional paid requests or
provider cache measurements. Hosted performance and cost are unmeasured.

Preparation took 68.262s wall / 67.683s CPU, with 356,569,088 bytes (340.1 MiB)
peak RSS. Measurement used SELF `perf_counter/process_time` and current
executable `/proc/self/status VmHWM`; one CPU process, no children or periodic
sampling. The RSS tuple was unpacked into numeric bytes and its measurement
source. Source PDFs and all raw images/bodies remain ignored.

Artifacts:
`/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/image-axis-context30-v1`.
See `bench/IMAGE_AXIS_EXPERIMENT.md` for reproduction, optional anisotropic
arms, provider transport details, refusals and alias limitations. The context30
cases have correlated templates; no real-world or heldout quality claim follows.

The separate optional anisotropic freeze is also complete at
`/home/dan/code/oss/pylopdf/bench/results/pdf-master-artifacts/image-axis-context30-anisotropic-v1`. It retains all main arms and adds 24 explicitly distorted representation/axis/size arms: 624 additional unique batches covering 2,880 case/model observations. The full manifest has 1,560 unique batches, 468 geometric aliases and zero refusals, with 2,340 image records. Preparation took 90.261s wall / 89.877s CPU and 373,354,496 bytes (356.1 MiB) peak RSS, with the same measurement scope as the main grid. No calls were sent.

Main manifest SHA256:
`7deeea36101bba1837659fb53310b1966edc8da1938370f860f0294ba188f1c7`.
Anisotropic manifest SHA256:
`081d9716390605d1ed7d08de7861c99fe905f137cc56664a9d747321d71964c4`.

The optional manifest includes identical main request bodies from the first
freeze. Those are retained for breadth and reproducibility, not additional
independent trials. Root may schedule only configurations where
`fixed_partner` is non-null for the distinct anisotropic phase. Cross-directory
request replay must be labeled from the client's replay flag; it provides no
fresh latency or throughput evidence.
