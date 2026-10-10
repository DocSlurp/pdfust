# P003 independent gate image and semantic instruction treatments

Prepared CPU-only on 2026-10-10. No inference, credentials, GPU, OCR,
detection, or reference labels were used for this implementation/profile.

`p003_run --gate-image-mode rgb|grayscale8|rgb_palette16` applies after the
existing gate crop/resize at 128, 256, 400, 512, 768, or 1024 pixels on the
long edge. RGB is the default and preserves the exact existing URL/PNG bytes;
its configuration field is omitted. The generation image retains its existing
independent size and bytes. NonRGB encodings require the ordinary P003
`gated_ordinal` processor, pixels, and OpenRouter. Candidate proposals retain
their existing gate behavior.

`grayscale8` produces PNG color type 0 with 8-bit luminance samples. It removes
color through Pillow RGB-to-L conversion. `rgb_palette16` produces PNG color
type 3 with 4-bit palette indexes and at most 16 entries, each storing ordinary
8-bit RGB components. This is **4-bit indexed color**, not 4 bits per RGB
channel. Median-cut quantization is deterministic for the pinned Pillow version
and uses no dithering. Grayscale and indexed color are independent treatments;
both can lose source color information. PNG byte savings do not establish lower
provider image-token charges or improved recognition.

The helper admits bounded RGB PNGs and checks original bytes/hash, dimensions,
and declared edge before conversion. It preserves the viewport and records
encoded SHA/bytes, dimensions, PNG bit depth/color type, decoded image mode,
palette size, conversion description, and original RGB SHA/bytes. Source replay
verifies these fields and the actual retained request image against a fresh
render of the frozen PDF with its original rotation policy. Failed attempts
retain evidence before transmission. The helper is a required frozen dependency
for nonRGB treatments, authenticated against the verifier's current code.

Root's independent `p003_prompt_variants.py` provides four additional CLI
`--gate-instructions` choices: `visual_schema`, `recall_first`, `skeptical`, and
`local_relations`. Existing `legacy` and `region` rubrics retain their request
bytes. The new rubrics share the exact existing table/prose/unresolved choices.
Their helper is frozen and authenticated. Verification rebuilds the actual
native or chat template from frozen model/rubric/token settings around the
retained literal evidence; it rejects changed instructions, criteria, schema,
transport fields, or model. This template check does not independently prove the
literal OCR prompt's completeness; existing source and packet audits remain
necessary. Image-source replay independently authenticates nonRGB pixels.

The historical compatibility exception names only reviewed prechange regional
runner SHA `fa51763aa571aedd12f3b625174e80b2fc57f4485b0898bb2d1bef225f8a8449`
(root 3745e7e). It is accepted for original source order only with RGB and
legacy/region instructions. Exact source-order helpers and ordinal parsers
remain required. Source acquisition, source ownership, generation, composition,
and Markdown behavior in that runner are unchanged by this implementation.

## Conversion-only profile

Retained inputs are the 18 actual gate PNGs from authorized DEV
`pipeline-p003/screen-gated-pplx-ocr300-512-r0/*-request-*.json`; only image
blocks of table/prose/unresolved requests were used. Their fixed edge is 512.
Each mode ran three serial in-process repeats, including decode, conversion,
encoding and hash where applicable. Values below sum each image's mean over
three repeats. These measurements ran while root's paid workers were active;
they are contended observations, not isolated throughput claims.

| Mode | Input bytes | Encoded bytes | CPU seconds | Wall seconds |
| --- | ---: | ---: | ---: | ---: |
| RGB identity | 1,164,317 | 1,164,317 | 0.00010 | 0.00014 |
| Grayscale 8-bit | 1,164,317 | 497,651 | 0.13448 | 0.13790 |
| RGB palette 16 | 1,164,317 | 287,528 | 0.35069 | 0.36072 |

Grayscale retained 42.7% and palette retained 24.7% of original encoded bytes.
Process-lifetime peak RSS was 31,232 KiB (`resource.getrusage`, Linux KiB,
no sampling); this is not an isolated conversion allocation delta. Rendering,
OCR, model latency, provider preprocessing and quality are unmeasured here.
The ignored artifact `pipeline-p003/gate-image-encodings/profile.json` records
all input request-file/PNG hashes, output hashes/metadata, repeat times,
Python/Pillow versions and process scope; SHA-256:
`f28ba52a8a6cbafe3f8ca10067645d2dcc2b4bf24c27e1d99c3552e44d913350`.

Tests cover all six edges and all three encodings, deterministic PNG headers,
source-metadata refusal, frozen-PDF replay with payload tampering, and actual
native/chat request construction across all four new semantic rubrics. They
verify that the generation URL is unchanged and altered archived rubrics fail
verification. Existing gate, report, and strict-transcription checks remain in
the focused test suite. No subprocess or process-group cleanup is involved.
