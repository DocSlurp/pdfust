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
