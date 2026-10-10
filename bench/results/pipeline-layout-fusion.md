# P002 predefined source-only detector fusion

Three geometry-only proposal arms were frozen before inspecting outcomes: baseline class-aware NMS, larger-first containment preference and compatible-overlap union. The fixed natural16 cached-source diagnostic conserved all 7,351 source IDs exactly once in every arm. Containment substantially reduced competing/empty proposals while preserving or modestly increasing detector-owned source words. This supplies a candidate for a separately metered model comparison, not evidence of improved semantic quality or lower measured model cost.

## Frozen arms and context contract

- `nms`: class-aware confidence-ranked suppression at IoU > 0.5, identical selected geometry and priority to the existing NMS.
- `larger_containment`: descending bbox area, then confidence and original index; suppress a same-class smaller box when intersection/minimum area is at least 0.8. Preserve the larger work-unit bbox and every suppressed member.
- `overlap_union`: union same-class connected components with IoU at least 0.35 and a compatible axis profile. At least one axis must overlap at least 0.8 of its smaller projection and have smaller/larger size ratio at least 0.5. Union bounds remain inside the full-page viewport.

No thresholds use source family, references or model outputs. Every raw box and original member remains retained, with deterministic proposal/member IDs. A fused confidence is the maximum original member confidence, explicitly labeled as an observation rather than semantic confidence in the fused bbox. Multiple-crop and original tile-edge warnings remain visible. Union can connect multiple semantic objects; the downstream model must keep actual tables separate or abstain.

Complete source context means the full cached page source supplies all words inside the chosen work-unit bbox. It does not assert that a physical table is complete or that the proposal is a table. Detector crop context and original tile-edge risk remain separate fields; physical-table completeness is always unknown. Capacity chunks still have incomplete source context. Native source grids retain priority and remaining words remain residual.

## Fixed-source outcomes

The two fixed evidence sets are whole + 2×2 tiles and whole + both 2×2/3×3 grids. Both reuse the original complete detector calls without new inference. Word budgets 256 and 1,024 share a 16,000-character source budget.

| Evidence | Word budget | Arm | Table proposals | Detector regions | Owned source words | Original boundary-risk regions | Capacity regions | Empty proposals | Contested word centers |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| whole_2x2 | 256 | nms | 47 | 37 | 1777 | 15 | 0 | 10 | 363 |
| whole_2x2 | 256 | larger_containment | 31 | 33 | 1777 | 15 | 4 | 0 | 26 |
| whole_2x2 | 256 | overlap_union | 40 | 34 | 1783 | 15 | 0 | 6 | 406 |
| whole_2x2 | 1024 | nms | 47 | 37 | 1777 | 15 | 0 | 10 | 363 |
| whole_2x2 | 1024 | larger_containment | 31 | 31 | 1777 | 15 | 0 | 0 | 26 |
| whole_2x2 | 1024 | overlap_union | 40 | 34 | 1783 | 15 | 0 | 6 | 406 |
| whole_2x2_3x3 | 256 | nms | 116 | 65 | 1948 | 53 | 0 | 51 | 1024 |
| whole_2x2_3x3 | 256 | larger_containment | 43 | 43 | 1972 | 38 | 4 | 2 | 122 |
| whole_2x2_3x3 | 256 | overlap_union | 78 | 54 | 1981 | 45 | 0 | 24 | 724 |
| whole_2x2_3x3 | 1024 | nms | 116 | 65 | 1948 | 53 | 0 | 51 | 1024 |
| whole_2x2_3x3 | 1024 | larger_containment | 43 | 41 | 1972 | 36 | 0 | 2 | 122 |
| whole_2x2_3x3 | 1024 | overlap_union | 78 | 54 | 1981 | 45 | 0 | 24 | 724 |

At 1,024 words, whole + 2×2 containment preserves 1,777 owned words while reducing detector work units 37→31, empty proposals 10→0 and contested word centers 363→26. With both grids it increases owned words 1,948→1,972, while reducing work units 65→41, empty proposals 51→2 and conflicts 1,024→122. The 256-word budget reintroduces four capacity fragments for containment; the 1,024-word budget avoids these on this screen. Overlap union reduces fragmentation less strongly and can extend the work-unit bbox into additional source words.

Boundary counts include any original member's risk, including suppressed members. They therefore differ from the earlier tiling diagnostic's selected-box-only flags; risk is preserved rather than erased by fusion. More owned words may also include prose or distinct tables. These counts cannot determine table accuracy, text correctness, actual API cost or the winner of the next model experiment. No references were read or localization scores computed.

## Resources, admission and validation

The retained-source fusion/partition/serialization pass took 4.415 wall seconds and 4.389 own-process CPU seconds. Linux getrusage lifetime peak RSS was 69,868 KiB; RSS was not sampled. Scope excludes original OCR, rendering and detector inference. One process ran serially; other research activity may be concurrent.

Inputs are bounded to fourteen calls × 1,024 raw boxes. Complete same-class pair work is capped at one million comparisons; fused results stop at 1,024 boxes. Geometry, finite area, confidence and full-page containment are checked before fusion. Partition admission preserves existing complete-source and region limits. No partial fused result or source partition is exposed on refusal.

Eight fusion tests plus fourteen detector/tiling tests pass; Ruff lint and formatting checks pass. Tests cover raw evidence preservation, deterministic IDs, exact source ownership, baseline compatibility, contained-fragment stealing, class/disjoint separation, compatible union, original boundary uncertainty, capacity abstention and invalid/over-limit input refusal.

Run `python -m bench.pipeline_layout_fusion --manifest <natural16 manifest> --sources-directory <natural16-generate-sonnet> --tiles-directory <detector-natural16-tiles> --output <new directory>`. Source frozen records and detector manifest identity are checked. Thresholds, code/source/tile hashes, complete raw and fused evidence and every partition remain in ignored `bench/results/pdf-master-artifacts/pipeline-p002/detector-natural16-fusion-v2/`. This remains opt-in experimental code, with no package default changes and no hosted requests.
