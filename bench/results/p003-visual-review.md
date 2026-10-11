
A bounded authored DEV source audit now separates literal recovery from physical
structure. Haiku640 r912 adds an unsupported wholly empty fifth column;
r51d adds an unsupported blank Amount subcolumn under a two-column header;
r838 loses a visibly present two-row Description merge. All three retain content
precision/recall 1, which does not certify span membership. Actual source pixels,
frozen gold matrices, actual output matrices and zero-based span witnesses are
retained under ignored `visual-review-v1/random40-span-aa74d7f579e3efb6c76a/`.
Original strict scores, references and existing images remain unchanged. Future
lexical partition captions reject wholly empty added columns and require source
review for physical boundary ambiguity. This corrects the older r912 diagnostic's
overbroad accepted-granularity caption without changing that frozen image.

Continuous content views are available under ignored
`visual-review-v1/content-gradient-a342404ee9f1e341dda0/`. Table-level character
precision and recall from pinned independent audits produce a displayed harmonic
mean: red at 0, yellow at 0.5 and green at 1. The entire output table shares that
content tint; individual cells receive no invented content verdict. Structural
acceptance is separately labelled, with amber warnings for missing rows or lost
merged-cell membership even when character content reaches 1. The newspaper T8
view distinguishes Motor City and Grand Rapids business-value losses from dot
leaders and fraction encoding that also affect the character score. All full
original source pages are retained; original strict images and scores remain
unchanged. Missing matched output uses an explicit zero-display convention,
rather than claiming a newly computed semantic score.

Run the bounded refresh with `python -m bench.p003_content_visual_review --root
<authorized-P003-root> --output <ignored-visual-review-directory>`. It admits only
five declared cases and verifies frozen plan, trusted runtime, report, evaluation,
reference and source hashes before rendering. Font digests, renderer settings and
local wall/CPU time and lifetime peak RSS remain in provenance. This is CPU-only
local diagnostics with no new inference or reference edits.

The follow-up batch `visual-review-v1/content-gradient-6fba505b4c10afba3e11/`
adds `*-groups.png` views. Each color uses a retained alignment group's exact
matched, reference-unit and prediction-unit counts, with F1 `2M/(R+P)`.
The scored unit is normalized Unicode characters including declared join spaces;
representation differences such as reference math markup versus Unicode fractions
can therefore be red without implying a wrong business value. Empty groups with
zero character units are gray. A reference-only missing row is an explicit red
callout, not fabricated output or an inferred source mask. Changed merged-anchor
membership receives an amber border separately from character color.

The T8 witnesses additionally reveal Maine W `4` versus actual `3`, alongside
changed Grand Rapids values and the missing Motor City row. T0 groups preserve
all 21 rows, including the header, under the accepted fixed rank/team partition.
Full original rasters, native reference-bbox crops and scaled diagnostic crops
are retained separately with coordinates, resampling settings and image digests.
The scaled T0 source crop visibly includes all 20 data rows through Canton.

The metadata checkpoint also accepts repeated `--offline-progress "Scope=path"`
arguments. Its separate replay table keeps 32 full-pipeline score replays distinct
from 64 partial decision-run replays and from hosted queue completion. Progress
metadata captures hashes and timestamps; completion itself does not grant quality
credit or imply new inference. Active replay ETA remains unknown when no measured
rate is present. This reporting extension reads only explicitly supplied progress
JSON and preserves worker outputs.
