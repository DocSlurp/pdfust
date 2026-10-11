# Independent synthetic geometry control evaluation

All 96 frozen outcomes replayed exactly from authenticated source evidence before authored labels were opened. The controls use the same 24 synthetic relationship cases as the separate hosted experiment, with 18 visually cued cases and six cases whose opposing labels have identical words, rules, and pixels. Original source and control artifacts remain unchanged.

| Control | Classified / 24 | Author-label matches / 24 | Matches among classified | Matches / 18 visually cued | Abstentions / 24 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Physical word-box row proxy | 8 | 4 | 4 / 8 | 3 | 16 |
| Actual vector rules | 15 | 14 | 14 / 15 | 14 | 9 |
| Actual crop raster, 128 pixels | 7 | 7 | 7 / 7 | 7 | 17 |
| Actual crop raster, 512 pixels | 8 | 8 | 8 / 8 | 8 | 16 |

The physical proxy decides only row questions and matches four of eight logical-row labels. A physical baseline does not establish logical membership. The vector control matches six cell, five row, and three wrap labels; its one classified mismatch is a row question. The raster controls retain fewer decisions: the 128-pixel treatment matches three cell, two row, and two wrap labels; 512 pixels adds one wrap decision. Their conditional agreement describes this small retained subset, not complete coverage or general table extraction.

Vector and raster controls abstain on all six visually indeterminate cases. The physical proxy returns the same answer across one indistinguishable opposing-label pair, so only one hidden label matches there. The six indeterminate cases are scored separately; their labels cannot all be recovered from identical observed evidence. No model probabilities, hosted cost, source assignments, or complete-pipeline rate are attributed to these controls.

Authentication checks independently supplied source/code authorities, all original PDFs and rendered image bytes, complete literal source/drawing projections, exact current geometry helper hashes, the externally supplied control freeze hash, and all 96 reconstructed outcome receipts. Rehashing a corrupted outcome and its local manifest cannot bypass source replay. Only after these checks does evaluation open separately hashed generator-owned gold. Three tests cover complete replay, this tampering refusal, and abstention/error/indeterminate denominators. Ruff and targeted mypy pass.

The original control reports 0.77 seconds wall and 0.76 seconds CPU, one worker, sampled parent peak RSS 44,097,536 bytes at 100 ms, and lifetime peak RSS 539,156 KiB including imports. These are retained reported resource measurements, not a newly measured throughput comparison. Independent replay is CPU-only and makes no hosted calls.

Receipts:

- Original control freeze: `fc956db68477638b347603268e6d91422236de293cfbea0d20acc38463b16691`.
- Original outcomes: `ab35856b4913cfe28571175776c32b4099bbdc071e7d460102ab81c5d0cae6cd`.
- Source freeze: `fe51369b77b2f6d45c80713c9ebc8cb71b79659b37db6ae5e94c2e5418cba84e`.
- Separate gold: `db0f5953579379fbf74ffba9faebf8c6acad1e622b70c4fae389d137d357e2ca`.
- Independent report: `c09d94360a3fdf5e40665ec3213e646f17b897ee2f18efe158f623ecaee8960d`, at `pipeline-p003/synthetic-geometry-independent-v2.json`.

The new evaluator is `bench.p003_synthetic_geometry_eval`. Its CLI requires explicit source/control directories, independent source/control code maps, an approved control freeze hash, and a separate gold file/hash. It refuses an existing output file. No rules were changed after scoring.
