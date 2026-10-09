# OmniDocBench DEV sample

16 deterministic DEV rows from 1651 official pages at revision `aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec`. Public benchmark contamination is unknown; this is not a heldout result.

Selection greedily covers source type, language, layout, and isolated-formula/table presence, with seeded SHA256 tie order. It never uses recognition answer text, model outputs, or quality scores. Raw annotations/images and complete baseline outputs remain ignored local artifacts.

Dataset restriction: [Dataset card: research purposes only; not for commercial use](https://huggingface.co/datasets/opendatalab/OmniDocBench/blob/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/README.md). Raw dataset assets are not committed or redistributed.

The pinned current release contains page images but no original PDFs. Each CPU check inserts the official image into a newly generated PDF without an OCR layer. Zero native text and zero vector tables are expected properties of these carriers, not native-PDF extraction failures. No OCR or hosted inference was run.

All 16 carrier PDFs have one image placement and zero native text characters.
Full image IDs, hashes and metadata are retained in the [sample registry](../omnidoc-dev/registry.json).

| Source page | Document type | Language | Layout | Formula / table blocks | Render bytes |
| --- | --- | --- | --- | ---: | ---: |
| [Page 01](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/exam_paper_2016%E5%B9%B4%E5%AE%89%E5%BE%BD%E7%9C%81%E4%B8%AD%E8%80%83%E8%8B%B1%E8%AF%AD%E8%AF%95%E9%A2%98%EF%BC%88%E8%A7%A3%E6%9E%90%EF%BC%89_page_003.png) | exam_paper | english | single_column | 0 / 0 | 163,029 B |
| [Page 02](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/page-9f6bc620-1983-4503-bb0f-f9c7949ccb77.png) | academic_literature | simplified_chinese | other_layout | 5 / 1 | 417,005 B |
| [Page 03](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/color_textbook_zhonggaokao_%E5%B0%8F%E5%AD%A6_KET%E5%90%AC%E8%AF%B4%E8%AF%BB%E5%86%99%E9%80%90%E9%A1%B9%E7%AA%81%E7%A0%B4_KET%E5%90%AC%E8%AF%B4%E8%AF%BB%E5%86%99%E9%80%90%E9%A1%B9%E7%AA%81%E7%A0%B4%E4%B9%8B%E8%BD%BB%E6%9D%BE%E6%90%9E%E5%AE%9AKET%E5%86%99%E4%BD%9C25%E5%88%86%20%E3%80%9010%E8%AE%B2%20%E8%A4%9A%E8%BF%9E%E4%B8%80%E3%80%91_%E7%AC%AC08%E8%AE%B2%E7%AC%AC%E5%85%AB%E8%AF%BE%E5%86%99%E4%BD%9CPart8%E8%AE%AD%E7%BB%83_%E7%AC%AC%E5%85%AB%E8%AF%BE%E5%86%99%E4%BD%9CPart8%E8%AE%AD%E7%BB%83_page_003.png) | colorful_textbook | en_ch_mixed | double_column | 0 / 0 | 303,824 B |
| [Page 04](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/newspaper_fe5ed29024932fad071afc53807b16ba_5.jpg) | newspaper | english | three_column | 0 / 0 | 739,528 B |
| [Page 05](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/eastmoney_1746461e6e00efee224a9209974b4bb6de3b11e339e4d86c41569eeddcc3c20e.pdf_8.jpg) | research_report | simplified_chinese | 1andmore_column | 0 / 1 | 429,386 B |
| [Page 06](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/page-942ac90d-4704-43f3-9286-719c7be9e655.png) | historical_document | traditional_chinese | other_layout | 0 / 0 | 214,385 B |
| [Page 07](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/page-0b772bee-71ec-4d4a-a406-d7691b1a6e86.png) | magazine | other | other_layout | 0 / 0 | 363,735 B |
| [Page 08](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/yanbaor2_f197117877bfd892faf3c89f14c35ae92c3150ec7affb49dd51d8f8ce202604a.pdf_22.jpg) | book | simplified_chinese | double_column | 0 / 0 | 263,476 B |
| [Page 09](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/notes_f7f010b78016aeebd76e56d9283eb67f_5.jpg) | note | english | single_column | 0 / 0 | 125,717 B |
| [Page 10](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/PPT_PresentationSpecification_page_025.png) | PPT2PDF | english | single_column | 0 / 0 | 133,842 B |
| [Page 11](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/eastmoney_ea59610b9b1a8f0df46f7a89da1116cbf256c772e1148f26017991e28c8bca21.pdf_18.jpg) | research_report | simplified_chinese | single_column | 0 / 2 | 370,839 B |
| [Page 12](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/newspaper_The%20Guardian%20UK_0801%40magazinesclubnew_page_061.png) | newspaper | english | other_layout | 0 / 0 | 9,641,232 B |
| [Page 13](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/docstructbench_llm-raw-scihub-o.O-dneu.20401.pdf_2.jpg) | academic_literature | english | double_column | 0 / 0 | 551,930 B |
| [Page 14](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/jiaocaineedrop_jiaocai_needrop_en_3713.jpg) | exam_paper | simplified_chinese | double_column | 0 / 1 | 422,042 B |
| [Page 15](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/jiaocai_jiaocai_en_37.jpg) | exam_paper | english | single_column | 0 / 0 | 118,025 B |
| [Page 16](https://huggingface.co/datasets/opendatalab/OmniDocBench/resolve/aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec/images/jiaocaineedrop_eng_gls.pdf_6.jpg) | colorful_textbook | english | double_column | 0 / 0 | 683,977 B |

CPU baseline: 3.014s elapsed, 2.742s user + 0.260s system CPU, 810.5 MiB process-lifetime peak RSS. Tool/scope: Linux resource.getrusage(RUSAGE_SELF), process lifetime peak RSS; no sampling; single sequential process; CPU only; no children. Machine: `Linux-7.2.5-3-omarchy-x86_64-with-glibc2.44`, 8 logical CPUs, pylopdf `0.13.0`. Network download time is excluded; local image insertion/extraction/rendering is included. Remote resource usage is unmeasured because no remote inference ran.

This sample provides external page-image layout/language coverage. Native text, reading order, math transcription, and table recognition quality require OCR or matching original PDFs and a separately specified evaluation protocol.
