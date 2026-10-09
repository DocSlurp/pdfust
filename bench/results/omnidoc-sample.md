# OmniDocBench DEV sample

16 deterministic DEV rows from 1651 official pages at revision `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec`. Public benchmark contamination is unknown; this is not a heldout result.

Selection greedily covers source type, language, layout, and isolated-formula/table presence, with seeded SHA256 tie order. It never uses recognition answer text, model outputs, or quality scores. Raw annotations/images and complete baseline outputs remain ignored local artifacts.

Dataset restriction: [Dataset card: research purposes only; not for commercial use](https://huggingface.co/datasets/opendatalab/OmniDocBench/blob/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/README.md). Raw dataset assets are not committed or redistributed.

The pinned current release contains page images but no original PDFs. Each CPU check inserts the official image into a newly generated PDF without an OCR layer. Zero native text and zero vector tables are expected properties of these carriers, not native-PDF extraction failures. No OCR or hosted inference was run.

| # | Page image ID | Source type | Language | Layout | Formula / table blocks | Image placements | Native text | Render |
|---|---|---|---|---|---|---|---|---|
| 1 | `exam_paper_2016年安徽省中考英语试题（解析）_page_003.png` | exam_paper | english | single_column | 0 / 0 | 1 | 0 | 163,029 B |
| 2 | `page-9f6bc620-1983-4503-bb0f-f9c7949ccb77.png` | academic_literature | simplified_chinese | other_layout | 5 / 1 | 1 | 0 | 417,005 B |
| 3 | `color_textbook_zhonggaokao_小学_KET听说读写逐项突破_KET听说读写逐项突破之轻松搞定KET写作25分 【10讲 褚连一】_第08讲第八课写作Part8训练_第八课写作Part8训练_page_003.png` | colorful_textbook | en_ch_mixed | double_column | 0 / 0 | 1 | 0 | 303,824 B |
| 4 | `newspaper_fe5ed29024932fad071afc53807b16ba_5.jpg` | newspaper | english | three_column | 0 / 0 | 1 | 0 | 739,528 B |
| 5 | `eastmoney_1746461e6e00efee224a9209974b4bb6de3b11e339e4d86c41569eeddcc3c20e.pdf_8.jpg` | research_report | simplified_chinese | 1andmore_column | 0 / 1 | 1 | 0 | 429,386 B |
| 6 | `page-942ac90d-4704-43f3-9286-719c7be9e655.png` | historical_document | traditional_chinese | other_layout | 0 / 0 | 1 | 0 | 214,385 B |
| 7 | `page-0b772bee-71ec-4d4a-a406-d7691b1a6e86.png` | magazine | other | other_layout | 0 / 0 | 1 | 0 | 363,735 B |
| 8 | `yanbaor2_f197117877bfd892faf3c89f14c35ae92c3150ec7affb49dd51d8f8ce202604a.pdf_22.jpg` | book | simplified_chinese | double_column | 0 / 0 | 1 | 0 | 263,476 B |
| 9 | `notes_f7f010b78016aeebd76e56d9283eb67f_5.jpg` | note | english | single_column | 0 / 0 | 1 | 0 | 125,717 B |
| 10 | `PPT_PresentationSpecification_page_025.png` | PPT2PDF | english | single_column | 0 / 0 | 1 | 0 | 133,842 B |
| 11 | `eastmoney_ea59610b9b1a8f0df46f7a89da1116cbf256c772e1148f26017991e28c8bca21.pdf_18.jpg` | research_report | simplified_chinese | single_column | 0 / 2 | 1 | 0 | 370,839 B |
| 12 | `newspaper_The Guardian UK_0801@magazinesclubnew_page_061.png` | newspaper | english | other_layout | 0 / 0 | 1 | 0 | 9,641,232 B |
| 13 | `docstructbench_llm-raw-scihub-o.O-dneu.20401.pdf_2.jpg` | academic_literature | english | double_column | 0 / 0 | 1 | 0 | 551,930 B |
| 14 | `jiaocaineedrop_jiaocai_needrop_en_3713.jpg` | exam_paper | simplified_chinese | double_column | 0 / 1 | 1 | 0 | 422,042 B |
| 15 | `jiaocai_jiaocai_en_37.jpg` | exam_paper | english | single_column | 0 / 0 | 1 | 0 | 118,025 B |
| 16 | `jiaocaineedrop_eng_gls.pdf_6.jpg` | colorful_textbook | english | double_column | 0 / 0 | 1 | 0 | 683,977 B |

CPU baseline: 3.014s elapsed, 2.742s user + 0.260s system CPU, 810.5 MiB process-lifetime peak RSS. Tool/scope: Linux resource.getrusage(RUSAGE_SELF), process lifetime peak RSS; no sampling; single sequential process; CPU only; no children. Machine: `Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44`, 8 logical CPUs, pylopdf `0.13.0`. Network download time is excluded; local image insertion/extraction/rendering is included. Remote resource usage is unmeasured because no remote inference ran.

This sample provides external page-image layout/language coverage. Native text, reading order, math transcription, and table recognition quality require OCR or matching original PDFs and a separately specified evaluation protocol.
