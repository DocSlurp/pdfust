"""Acquire, profile, and validate the real-world-v2 DEV corpus of licensed PDFs.

See ``bench/REAL_WORLD_V2.md``. Every document comes from a source whose
license allows redistribution and research use. Downloads are untrusted: each
one lands in its own fresh directory, nothing from it is executed, and it is
only parsed by pypdf inside an isolated ``python -I`` subprocess before
qpdf optionally keeps a recorded page range. Everything is written to the
ignored ``bench/results/pdf-master-artifacts/real-world-v2/`` directory.

Commands::

    python -m bench.real_world_v2 fetch [--id ID ...]     # sequential, polite
    python -m bench.real_world_v2 profile                 # producer/version/features
    python -m bench.real_world_v2 health                  # pylopdf vs pdftotext vs PyMuPDF
    python -m bench.real_world_v2 candidates --id ID --page N   # truth drafting aid
    python -m bench.real_world_v2 validate                # manifest + truth schemas

This is DEV data. It never reads held-out silver locations.
"""

# Fixed local tools (qpdf, pdftotext, pdftoppm, this interpreter) run with argument lists.
# ruff: noqa: PLR2004, S603, S310, S607, C901, PLR0912, PLR0913, TRY003, TRY301, EM101, EM102, D103, PERF401
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "bench/results/pdf-master-artifacts/real-world-v2"
# Wikimedia's robot policy rejects anonymous clients, so name the project URL (no email).
USER_AGENT = (
    "pylopdf-real-world-v2-benchmark/0.1 (+https://github.com/justsml/jev-pdf; "
    "PDF research corpus, sequential low-volume downloads)"
)
MAX_DOWNLOAD_BYTES = 60 * 1024 * 1024
MAX_KEPT_BYTES = 5 * 1024 * 1024
MAX_KEPT_PAGES = 30
REQUEST_BUDGET = 150
REQUEST_DELAY_SECONDS = 2.0

LICENSES: dict[str, str] = {
    "US-PD": "https://www.usa.gov/government-copyright",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC-BY-SA-3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC-BY-SA-2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "PD-JP-Art13": "https://commons.wikimedia.org/wiki/Template:PD-JapanGov",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "PD-Gutenberg": "https://www.gutenberg.org/policy/license.html",
    "OGL-UK-3.0": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    "JP-PDL-1.0": "https://www.digital.go.jp/resources/open_data/public_data_license_v1.0",
    "JP-GSTOU-2.0": "https://www.digital.go.jp/resources/open_data/",
    "PD-old": "https://creativecommons.org/publicdomain/mark/1.0/",
}
SOURCE_KINDS = {
    "us-gov",
    "arxiv",
    "wikimedia",
    "eu",
    "uk-gov",
    "gutenberg",
    "jp-gov",
    "public-domain-scan",
    "standards-example",
}
TRUTH_STATUSES = {"verified", "partial"}
TEXT_KINDS = {"heading", "paragraph", "sidebar", "callout", "footnote", "header", "footer"}
BLOCK_KINDS = TEXT_KINDS | {"list", "table", "figure", "caption", "formula"}
TABLE_RENDERINGS = {"ruled", "borderless", "partially_ruled", "screenshot", "chart_data"}


def _source(
    source_id: str,
    url: str,
    license_id: str,
    attribution: str,
    *,
    kind: str,
    title: str,
    languages: list[str],
    pages: str | None = None,
    license_url: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "id": source_id,
        "url": url,
        "license": license_id,
        "license_url": license_url or LICENSES[license_id],
        "attribution": attribution,
        "kind": kind,
        "title": title,
        "languages": languages,
        "pages": pages,
        "notes": notes,
    }


USGOV = "Work of the United States Government; not subject to US copyright (17 U.S.C. 105)."

# Curated sources. ``pages`` is a qpdf page range kept from the original (1-based).
SOURCES: list[dict[str, Any]] = [
    _source(
        "irs-fw4-2026",
        "https://www.irs.gov/pub/irs-pdf/fw4.pdf",
        "US-PD",
        f"Internal Revenue Service, Form W-4. {USGOV}",
        kind="us-gov",
        title="Form W-4 Employee's Withholding Certificate",
        languages=["en-US"],
        notes="Fillable AcroForm with worksheets and withholding tables.",
    ),
    _source(
        "irs-i1040tt",
        "https://www.irs.gov/pub/irs-pdf/i1040tt.pdf",
        "US-PD",
        f"Internal Revenue Service, 1040 Tax Table. {USGOV}",
        kind="us-gov",
        title="Instructions for Form 1040: Tax Table",
        languages=["en-US"],
        pages="1-6",
        notes="Dense multi-page tax table continuing across pages.",
    ),
    _source(
        "irs-fw9",
        "https://www.irs.gov/pub/irs-pdf/fw9.pdf",
        "US-PD",
        f"Internal Revenue Service, Form W-9. {USGOV}",
        kind="us-gov",
        title="Form W-9 Request for Taxpayer Identification Number and Certification",
        languages=["en-US"],
        notes="Fillable AcroForm with dense instructions.",
    ),
    _source(
        "nist-cswp29-csf2",
        "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf",
        "US-PD",
        f"National Institute of Standards and Technology, NIST CSWP 29 (Cybersecurity Framework 2.0). {USGOV}",
        kind="us-gov",
        title="The NIST Cybersecurity Framework (CSF) 2.0",
        languages=["en-US"],
        pages="1-30",
    ),
    _source(
        "gao-25-108401-highlights",
        "https://www.gao.gov/assets/gao-25-108401-highlights.pdf",
        "US-PD",
        f"U.S. Government Accountability Office, GAO-25-108401 Highlights. {USGOV}",
        kind="us-gov",
        title="GAO FY2026 budget request testimony highlights",
        languages=["en-US"],
    ),
    _source(
        "crs-if10183",
        "https://www.everycrsreport.com/files/2024-11-01_IF10183_a94ece50e7d0f5015b2087aabd23ec7335dfec37.pdf",
        "US-PD",
        "Congressional Research Service, In Focus IF10183 U.S. Foreign Assistance "
        f"(2024-11-01 version, EveryCRSReport.com mirror). {USGOV}",
        kind="us-gov",
        title="U.S. Foreign Assistance (CRS In Focus)",
        languages=["en-US"],
    ),
    _source(
        "fda-50605s31-label-2002",
        "https://www.accessdata.fda.gov/drugsatfda_docs/label/2002/50605s31lbl.pdf",
        "US-PD",
        f"U.S. Food and Drug Administration, Drugs@FDA label 50605 s031 (2002). {USGOV}",
        kind="us-gov",
        title="Drugs@FDA approved labeling, application 50605 supplement 31",
        languages=["en-US"],
        notes="Archived 2002 label; may be superseded.",
    ),
    _source(
        "naca-tr824-airfoil-summary",
        "https://ntrs.nasa.gov/api/citations/19930090976/downloads/19930090976.pdf",
        "US-PD",
        f"NACA Report 824, Abbott, Von Doenhoff and Stivers, 1945, via NASA NTRS. {USGOV}",
        kind="us-gov",
        title="Summary of Airfoil Data (NACA TR-824)",
        languages=["en-US"],
        pages="1-12",
        notes="Digitized 1945 scan with an OCR text layer.",
    ),
    _source(
        "gutenberg-41568-whitehead",
        "https://www.gutenberg.org/files/41568/41568-pdf.pdf",
        "PD-Gutenberg",
        "A. N. Whitehead, An Introduction to Mathematics; Project Gutenberg ebook #41568, public domain in the USA.",
        kind="gutenberg",
        title="An Introduction to Mathematics",
        languages=["en"],
        pages="1-20",
        notes="LaTeX-typeset Distributed Proofreaders edition.",
    ),
    _source(
        "jp-digital-pdl-outline",
        "https://digital.go.jp/assets/contents/node/basic_page/field_ref_resources/"
        "f7fde41d-ffca-4b2a-9b25-94b8a701a037/b44a7e0c/20240705_resources_data_outline_07.pdf",
        "JP-PDL-1.0",
        "Digital Agency of Japan (デジタル庁), 公共データ利用規約（第1.0版）概要, 2024-07-05; "
        "used under the Public Data License 1.0 (CC BY 4.0 compatible).",
        kind="jp-gov",
        title="公共データ利用規約（第1.0版）の概要",
        languages=["ja"],
    ),
]

ARXIV_IDS: dict[str, tuple[str, str, str, list[str], str | None]] = {
    # id: (arXiv id, license, title, languages, pages)
    "arxiv-2403.11436-trs-codes": (
        "2403.11436",
        "CC-BY-4.0",
        "Deep Holes of Twisted Reed-Solomon Codes",
        ["en"],
        "1-20",
    ),
    "arxiv-2412.08972-rulearena": (
        "2412.08972",
        "CC-BY-4.0",
        "RuleArena: A Benchmark for Rule-Guided Reasoning with LLMs in Real-World Scenarios",
        ["en"],
        "1-12",
    ),
    "arxiv-2505.24490-outer-k-planar": (
        "2505.24490",
        "CC-BY-4.0",
        "On the maximum number of edges of outer k-planar graphs",
        ["en"],
        None,
    ),
    "arxiv-2409.11638-banstereoset": (
        "2409.11638",
        "CC0-1.0",
        "BanStereoSet: A Dataset to Measure Stereotypical Social Biases in LLMs for Bangla",
        ["en", "bn"],
        None,
    ),
    "arxiv-2505.13772-krikri": (
        "2505.13772",
        "CC-BY-4.0",
        "Krikri: Advancing Open Large Language Models for Greek",
        ["en", "el"],
        "1-14",
    ),
    "arxiv-2503.14372-resnet-control": (
        "2503.14372",
        "CC-BY-4.0",
        "Online ResNet-Based Adaptive Control for Nonlinear Target Tracking",
        ["en"],
        None,
    ),
}
for _sid, (_aid, _lic, _title, _langs, _pages) in ARXIV_IDS.items():
    SOURCES.append(
        _source(
            _sid,
            f"https://arxiv.org/pdf/{_aid}",
            _lic,
            f"arXiv:{_aid}, '{_title}', by its authors; license verified on https://arxiv.org/abs/{_aid}.",
            kind="arxiv",
            title=_title,
            languages=_langs,
            pages=_pages,
        )
    )


COMMONS = "https://commons.wikimedia.org/wiki/File:"
SOURCES += [
    _source(
        "commons-ko-wikiconf-2022-keynote",
        "https://upload.wikimedia.org/wikipedia/commons/0/05/2022-Wikiconf-Community.pdf",
        "CC-BY-SA-4.0",
        "책읽는달팽 (Wikimedia Commons user), '2022-Wikiconf-Community.pdf', CC BY-SA 4.0, "
        f"{COMMONS}2022-Wikiconf-Community.pdf",
        kind="wikimedia",
        title="2022 Korean WikiConference community talk (Keynote slides)",
        languages=["ko"],
        notes="16:9 slides exported by Apple Keynote through Quartz PDFContext (Korean macOS).",
    ),
    _source(
        "commons-word-critical-librarianship",
        "https://upload.wikimedia.org/wikipedia/commons/6/68/"
        "Keynote_address_Wikimedia_through_the_prisms_of_critical_librarianship.pdf",
        "CC-BY-SA-4.0",
        "AfricanLibrarian (Wikimedia Commons user), 'Keynote address Wikimedia through the prisms of "
        f"critical librarianship', CC BY-SA 4.0, {COMMONS}"
        "Keynote_address_Wikimedia_through_the_prisms_of_critical_librarianship.pdf",
        kind="wikimedia",
        title="Keynote address: Wikimedia through the prisms of critical librarianship",
        languages=["en"],
        notes="Microsoft Word 2016 export.",
    ),
    _source(
        "commons-pptx-whole-glam-2023",
        "https://upload.wikimedia.org/wikipedia/commons/8/8a/"
        "The_Whole_GLAM_package_%E2%80%93_Wikimania_2023_presentation_slides.pdf",
        "CC-BY-4.0",
        "Avocadobabygirl (Wikimedia Commons user), 'The Whole GLAM package - Wikimania 2023 "
        f"presentation slides', CC BY 4.0, {COMMONS}"
        "The_Whole_GLAM_package_%E2%80%93_Wikimania_2023_presentation_slides.pdf",
        kind="wikimedia",
        title="The Whole GLAM package (Wikimania 2023 slides)",
        languages=["en"],
        notes="PowerPoint for Microsoft 365 export.",
    ),
    _source(
        "commons-gslides-helpdesk-2022",
        "https://upload.wikimedia.org/wikipedia/commons/c/ca/Wikimania_2022_Helpdesk_presentation.pdf",
        "CC-BY-SA-4.0",
        "Eric Luth (WMSE), 'Wikimania 2022 Helpdesk presentation', CC BY-SA 4.0, "
        f"{COMMONS}Wikimania_2022_Helpdesk_presentation.pdf",
        kind="wikimedia",
        title="Wikimania 2022 Helpdesk presentation (Google Slides)",
        languages=["en"],
    ),
    _source(
        "usace-keynote-pdfmaker",
        "https://upload.wikimedia.org/wikipedia/commons/e/e9/"
        "Introduction_and_keynote_address_-_USACE-p16021coll11-1031.pdf",
        "US-PD",
        "United States Army Corps of Engineers, Portland District, 'Introduction and keynote address' "
        f"(USACE digital library p16021coll11/1031), via Wikimedia Commons. {USGOV}",
        kind="us-gov",
        title="USACE Portland District: Introduction and keynote address",
        languages=["en-US"],
        notes="Acrobat PDFMaker 11 for PowerPoint.",
    ),
    _source(
        "eisenhower-1960-talking-paper-scan",
        "https://upload.wikimedia.org/wikipedia/commons/8/8c/"
        "Foreign_Ministers_Meeting_Summit_Keynote_-_Talking_Paper_for_the_Secretary_-_DPLA_-_"
        "4ae5ad3bc42d3808a3d5d33ac5b092ee.pdf",
        "US-PD",
        "Office of the President (Eisenhower), 1960 talking paper, National Archives via DPLA and "
        f"Wikimedia Commons. {USGOV}",
        kind="public-domain-scan",
        title="Foreign Ministers Meeting / Summit Keynote: Talking Paper for the Secretary (1960)",
        languages=["en-US"],
        pages="1-6",
        notes="Typewritten archival scan; Adobe Acrobat 11 Image Conversion Plug-in.",
    ),
    _source(
        "ia-rational-education-1900s-scan",
        "https://upload.wikimedia.org/wikipedia/commons/8/8a/"
        "Rational_education%2C_the_keynote_of_the_Rational_school_.._%28IA_rationaleducatio00calv%29.pdf",
        "PD-old",
        "Bruce T. Calvert, 'Rational education, the keynote of the Rational school', public domain; "
        "digitized by the Internet Archive (rationaleducatio00calv), via Wikimedia Commons.",
        kind="public-domain-scan",
        title="Rational education, the keynote of the Rational school",
        languages=["en"],
        pages="1-20",
        notes="Internet Archive scan recoded by LuraDocument with a hidden OCR text layer.",
    ),
    _source(
        "wikipedia-ar-algorithm",
        "https://ar.wikipedia.org/api/rest_v1/page/pdf/%D8%AE%D9%88%D8%A7%D8%B1%D8%B2%D9%85%D9%8A%D8%A9",
        "CC-BY-SA-4.0",
        "Wikipedia contributors, 'خوارزمية', Arabic Wikipedia, CC BY-SA 4.0; "
        "https://ar.wikipedia.org/wiki/%D8%AE%D9%88%D8%A7%D8%B1%D8%B2%D9%85%D9%8A%D8%A9 (page history lists authors).",
        kind="wikimedia",
        title="خوارزمية (Arabic Wikipedia PDF export)",
        languages=["ar"],
    ),
    _source(
        "wikipedia-zh-pi",
        "https://zh.wikipedia.org/api/rest_v1/page/pdf/%E5%9C%93%E5%91%A8%E7%8E%87",
        "CC-BY-SA-4.0",
        "Wikipedia contributors, '圓周率', Chinese Wikipedia, CC BY-SA 4.0; "
        "https://zh.wikipedia.org/wiki/%E5%9C%93%E5%91%A8%E7%8E%87 (page history lists authors).",
        kind="wikimedia",
        title="圓周率 (Chinese Wikipedia PDF export)",
        languages=["zh-Hant", "zh-Hans"],
        pages="1-10",
    ),
    _source(
        "census-p60-259-2016",
        "https://www.census.gov/content/dam/Census/library/publications/2017/demo/P60-259.pdf",
        "US-PD",
        f"U.S. Census Bureau, Income and Poverty in the United States: 2016 (P60-259). {USGOV}",
        kind="us-gov",
        title="Income and Poverty in the United States: 2016",
        languages=["en-US"],
        pages="1-30",
    ),
]

SOURCES += [
    _source(
        "commons-miyagi-gazette-662-aes256",
        "https://upload.wikimedia.org/wikipedia/commons/1/11/"
        "%E4%BB%A4%E5%92%8C8%E5%B9%B4%E5%AE%AE%E5%9F%8E%E7%9C%8C%E5%85%AC%E5%A0%B1%E7%AC%AC662%E5%8F%B7.pdf",
        "PD-JP-Art13",
        "Miyagi Prefecture (宮城県), 令和8年宮城県公報第662号; official gazette not subject to copyright "
        "under Article 13 of the Japanese Copyright Act; via Wikimedia Commons.",
        kind="jp-gov",
        title="宮城県公報 第662号 (Miyagi Prefecture gazette)",
        languages=["ja"],
        pages="1-12",
        notes="AES-256 encrypted with an empty user password (copy/change restricted); Word + Acrobat.",
    ),
    _source(
        "commons-ala-lc-japanese-romanization",
        "https://upload.wikimedia.org/wikipedia/commons/3/34/ALA-LC_Romanization_Table_Japanese_%282022%29.pdf",
        "US-PD",
        "Library of Congress, ALA-LC Romanization Tables: Japanese (2022), "
        f"https://www.loc.gov/catdir/cpso/romanization/japanese.pdf, via Wikimedia Commons. {USGOV}",
        kind="us-gov",
        title="ALA-LC Romanization Table: Japanese (2022)",
        languages=["en", "ja"],
        pages="1-10,35-36",
        notes="Word 2019; front matter plus the two romanized/kana equivalent chart pages (source pp. 35-36).",
    ),
    _source(
        "commons-special-relativity-powerdot",
        "https://upload.wikimedia.org/wikipedia/commons/8/8a/Special_relativity_lecture.pdf",
        "CC-BY-SA-3.0",
        "User:Boud (Wikimedia Commons), 'Special relativity lecture', CC BY-SA 3.0, "
        f"{COMMONS}Special_relativity_lecture.pdf",
        kind="wikimedia",
        title="Special relativity lecture (LaTeX powerdot slides)",
        languages=["en"],
        pages="1-24",
        notes="LaTeX powerdot slides distilled by GPL Ghostscript 10.00.0.",
    ),
    _source(
        "commons-bluebook-1962-iran-papercapture",
        "https://upload.wikimedia.org/wikipedia/commons/0/06/Project_Blue_Book_report_-_1962-09-8725001-Iran.pdf",
        "US-PD",
        "United States Air Force, Project Blue Book case file 1962-09 Iran, National Archives scan via "
        f"Internet Archive and Wikimedia Commons. {USGOV}",
        kind="public-domain-scan",
        title="Project Blue Book report, September 1962, Iran",
        languages=["en-US"],
        notes="Typewritten scan with an Adobe Acrobat 10 Paper Capture OCR layer.",
    ),
    _source(
        "commons-nbs-jres-interferometers-papercapture",
        "https://upload.wikimedia.org/wikipedia/commons/d/d3/"
        "Large_aperture_interferometers_with_small_beam_dividers_%28IA_jresv67Cn3p201%29.pdf",
        "US-PD",
        "James B. Saunders, 'Large aperture interferometers with small beam dividers', Journal of Research "
        f"of the National Bureau of Standards 67C(3):201 (1963), via Internet Archive and Wikimedia Commons. {USGOV}",
        kind="public-domain-scan",
        title="Large aperture interferometers with small beam dividers (J. Res. NBS 67C, 1963)",
        languages=["en-US"],
        notes="Journal scan with an Adobe Acrobat 9 Paper Capture OCR layer; formulas.",
    ),
    _source(
        "commons-physrevx-11-041050-distiller",
        "https://upload.wikimedia.org/wikipedia/commons/4/4c/PhysRevX.11.041050.pdf",
        "CC-BY-4.0",
        "M. Kramer et al., 'Strong-Field Gravity Tests with the Double Pulsar', Phys. Rev. X 11, 041050 "
        "(2021), https://doi.org/10.1103/PhysRevX.11.041050, CC BY 4.0, via Wikimedia Commons.",
        kind="wikimedia",
        title="Strong-Field Gravity Tests with the Double Pulsar (Phys. Rev. X 11, 041050)",
        languages=["en"],
        pages="1-10",
        notes="APS journal typesetting distilled by Acrobat Distiller 10; math and tables.",
    ),
    _source(
        "commons-josm-fossgis-2012-beamer",
        "https://upload.wikimedia.org/wikipedia/commons/2/25/JOSM_FOSSGIS_2012.pdf",
        "CC-BY-SA-2.0",
        f"Simon Legner (User:simon04), 'JOSM FOSSGIS 2012', CC BY-SA 2.0, {COMMONS}JOSM_FOSSGIS_2012.pdf",
        kind="wikimedia",
        title="JOSM talk at FOSSGIS 2012 (LaTeX Beamer slides)",
        languages=["de"],
    ),
    _source(
        "wikipedia-he-algorithm",
        "https://he.wikipedia.org/api/rest_v1/page/pdf/%D7%90%D7%9C%D7%92%D7%95%D7%A8%D7%99%D7%AA%D7%9D",
        "CC-BY-SA-4.0",
        "Wikipedia contributors, 'אלגוריתם', Hebrew Wikipedia, CC BY-SA 4.0; "
        "https://he.wikipedia.org/wiki/%D7%90%D7%9C%D7%92%D7%95%D7%A8%D7%99%D7%AA%D7%9D (page history lists authors).",
        kind="wikimedia",
        title="אלגוריתם (Hebrew Wikipedia PDF export)",
        languages=["he"],
        pages="1-10",
    ),
    _source(
        "eurostat-key-figures-2021",
        "https://ec.europa.eu/eurostat/documents/15216629/15223208/KS-EI-21-001-EN-N.pdf",
        "CC-BY-4.0",
        "Eurostat, Key figures on Europe - 2021 edition (KS-EI-21-001), (c) European Union, 2021; "
        "reuse authorised under CC BY 4.0 as stated in the publication.",
        kind="eu",
        title="Key figures on Europe - 2021 edition",
        languages=["en"],
        pages="1-24",
    ),
    _source(
        "uk-dcms-cultural-exports-2012",
        "https://assets.publishing.service.gov.uk/media/5a78dd44e5274a277e69010c/"
        "Export_of_objects_of_cultural_interest_2012_Statistical_Release-final_v5.pdf",
        "OGL-UK-3.0",
        "Department for Culture, Media and Sport, Export of objects of cultural interest annual statistical "
        "release 2011-12. Contains public sector information licensed under the Open Government Licence v3.0.",
        kind="uk-gov",
        title="Export of objects of cultural interest: statistical release 2011-12",
        languages=["en-GB"],
    ),
    _source(
        "uk-dcms-rcewa-values-2012",
        "https://assets.publishing.service.gov.uk/media/5a799721ed915d07d35b6ab6/RCEWA_Values_2012.pdf",
        "OGL-UK-3.0",
        "Department for Culture, Media and Sport, RCEWA case values 2002-03 to 2011-12. Contains public "
        "sector information licensed under the Open Government Licence v3.0.",
        kind="uk-gov",
        title="Values associated with cases presented to the RCEWA, 2002-03 to 2011-12",
        languages=["en-GB"],
    ),
]

SOURCES += [
    _source(
        "commons-iorga-sibiu-cvision",
        "https://upload.wikimedia.org/wikipedia/commons/4/4b/Nicolae_Iorga_-_Noi_acte_rom%C3%A2ne%C8%99ti_la_Sibiu.pdf",
        "PD-old",
        "Nicolae Iorga (1871-1940), 'Noi acte românești la Sibiu', public domain (author died 1940); "
        f"via Wikimedia Commons, {COMMONS}Nicolae_Iorga_-_Noi_acte_rom%C3%A2ne%C8%99ti_la_Sibiu.pdf",
        kind="public-domain-scan",
        title="Noi acte românești la Sibiu",
        languages=["ro"],
        pages="1-12",
        notes="Book scan compressed by CVISION PdfCompressor 5 with an OCR text layer.",
    ),
    _source(
        "pdfa-pdf20-utf8-test",
        "https://raw.githubusercontent.com/pdf-association/pdf20examples/master/pdf20-utf8-test.pdf",
        "CC-BY-4.0",
        "PDF Association, pdf20examples 'pdf20-utf8-test.pdf', CC BY 4.0, "
        "https://github.com/pdf-association/pdf20examples",
        kind="standards-example",
        title="PDF 2.0 UTF-8 text string test",
        languages=["en", "ja", "el"],
        notes="Hand-authored PDF 2.0 example; a standards probe rather than a natural document.",
    ),
    _source(
        "pdfa-pdf20-incremental",
        "https://raw.githubusercontent.com/pdf-association/pdf20examples/master/"
        "PDF%202.0%20via%20incremental%20save.pdf",
        "CC-BY-4.0",
        "PDF Association, pdf20examples 'PDF 2.0 via incremental save.pdf', CC BY 4.0, "
        "https://github.com/pdf-association/pdf20examples",
        kind="standards-example",
        title="PDF 2.0 version upgrade through an incremental update",
        languages=["en"],
        notes="Hand-authored PDF 2.0 example with an appended incremental revision.",
    ),
]


# --------------------------------------------------------------------------- paths


def guard_path(path: Path) -> Path:
    for candidate in (path, path.resolve()):
        name = str(candidate).lower()
        if "heldout-silver" in name or "silver-heldout-v1" in name:
            raise ValueError("Held-out silver paths are forbidden in this DEV runner")
    return path.resolve()


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(directory: Path) -> dict[str, Any]:
    path = guard_path(directory) / "manifest.json"
    if path.exists():
        data: dict[str, Any] = json.loads(path.read_text())
        return data
    return {"version": 1, "corpus": "real-world-v2", "split": "DEV", "documents": []}


def save_manifest(directory: Path, manifest: dict[str, Any]) -> None:
    manifest["documents"].sort(key=lambda item: item["id"])
    manifest["updated_at"] = _now()
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- fetch

_PYPDF_PROBE = r"""
import json, sys
from pypdf import PdfReader
reader = PdfReader(sys.argv[1], strict=False)
encrypted = reader.is_encrypted
if encrypted:
    reader.decrypt("")
info = reader.metadata or {}
print(json.dumps({"pages": len(reader.pages), "encrypted": encrypted,
                  "producer": str(info.get("/Producer") or ""),
                  "creator": str(info.get("/Creator") or "")}))
"""


def pypdf_probe(path: Path, timeout: float = 120) -> dict[str, Any]:
    """Open an untrusted PDF with pypdf in an isolated interpreter."""
    result = subprocess.run(
        [sys.executable, "-I", "-c", _PYPDF_PROBE, str(path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=tempfile.gettempdir(),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pypdf could not open {path.name}: {result.stderr.strip()[-400:]}")
    probe: dict[str, Any] = json.loads(result.stdout.strip().splitlines()[-1])
    return probe


def _count_request(directory: Path, url: str, status: str) -> int:
    log = directory / "requests.log"
    with log.open("a") as handle:
        handle.write(f"{_now()}\t{status}\t{url}\n")
    return sum(1 for _ in log.open())


def download(url: str, target: Path, directory: Path) -> dict[str, Any]:
    if (directory / "requests.log").exists():
        used = sum(1 for _ in (directory / "requests.log").open())
        if used >= REQUEST_BUDGET:
            raise RuntimeError(f"HTTP request budget of {REQUEST_BUDGET} exhausted")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as out:
            total = 0
            while chunk := response.read(1 << 16):
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise RuntimeError(f"download exceeds {MAX_DOWNLOAD_BYTES} bytes")
                out.write(chunk)
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
    except Exception as error:
        _count_request(directory, url, f"error:{type(error).__name__}")
        raise
    _count_request(directory, url, "ok")
    return {
        "final_url": final_url,
        "content_type": content_type,
        "bytes": total,
        "seconds": round(time.perf_counter() - started, 3),
    }


def fetch_source(source: dict[str, Any], directory: Path, *, force: bool = False, reuse: bool = True) -> dict[str, Any]:
    pdf_dir = directory / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    kept = pdf_dir / f"{source['id']}.pdf"
    manifest = load_manifest(directory)
    existing = {doc["id"]: doc for doc in manifest["documents"]}
    if kept.exists() and source["id"] in existing and not force:
        return dict(existing[source["id"]])
    downloads = directory / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    previous = sorted(downloads.glob(f"{source['id']}-*/download.json"), key=lambda p: p.stat().st_mtime)
    if reuse and previous and json.loads(previous[-1].read_text())["url"] == source["url"]:
        sidecar = json.loads(previous[-1].read_text())
        original = previous[-1].parent / "original.pdf"
        retrieved_at, transfer = sidecar["retrieved_at"], sidecar["transfer"]
    else:
        # A fresh, empty directory per download; nothing in it is ever executed.
        fresh = Path(tempfile.mkdtemp(prefix=f"{source['id']}-", dir=downloads))
        original = fresh / "original.pdf"
        retrieved_at = _now()
        transfer = download(source["url"], original, directory)
        (fresh / "download.json").write_text(
            json.dumps({"url": source["url"], "retrieved_at": retrieved_at, "transfer": transfer}, indent=2)
        )
    if not original.read_bytes()[:1024].lstrip().startswith(b"%PDF-"):
        raise RuntimeError(f"{source['id']}: response is not a PDF ({transfer['content_type']})")
    original_probe = pypdf_probe(original)
    page_range = clamp_range(source["pages"], original_probe["pages"])
    if page_range == f"1-{original_probe['pages']}":
        page_range = None  # the whole document fits; keep the original bytes
    if page_range:
        subprocess.run(
            ["qpdf", "--warning-exit-0", str(original), "--pages", ".", page_range, "--", str(kept)],
            check=True,
            capture_output=True,
            timeout=300,
        )
    else:
        shutil.copyfile(original, kept)
    kept_probe = pypdf_probe(kept)
    size = kept.stat().st_size
    if size > MAX_KEPT_BYTES or kept_probe["pages"] > MAX_KEPT_PAGES:
        kept.unlink()
        raise RuntimeError(f"{source['id']}: kept file has {size} bytes / {kept_probe['pages']} pages")
    record = {
        **source,
        "retrieved_at": retrieved_at,
        "final_url": transfer["final_url"],
        "download_bytes": transfer["bytes"],
        "original_sha256": sha256_file(original),
        "original_pages": original_probe["pages"],
        "page_range_kept": page_range or f"1-{original_probe['pages']}",
        "derived_by": "qpdf --pages (original Info/trailer retained)" if page_range else "unmodified",
        "path": f"pdfs/{source['id']}.pdf",
        "sha256": sha256_file(kept),
        "bytes": size,
        "page_count": kept_probe["pages"],
        "producer": kept_probe["producer"],
        "creator": kept_probe["creator"],
        "encrypted": kept_probe["encrypted"],
    }
    record.pop("pages")
    existing[source["id"]] = record
    manifest["documents"] = list(existing.values())
    save_manifest(directory, manifest)
    return record


# --------------------------------------------------------------------------- profile

_PROFILE = r"""
import json, re, sys
from pypdf import PdfReader
from pypdf.generic import IndirectObject
path = sys.argv[1]
raw = open(path, "rb").read()
reader = PdfReader(path, strict=False)
if reader.is_encrypted:
    reader.decrypt("")
def res(obj):
    return obj.get_object() if isinstance(obj, IndirectObject) else obj
fonts, filters, sizes = {}, {}, set()
invisible = False
rotations = set()
for index, page in enumerate(reader.pages):
    box = page.mediabox
    w, h = float(box.width), float(box.height)
    rotations.add(int(page.get("/Rotate", 0) or 0) % 360)
    sizes.add((round(w), round(h)))
    resources = res(page.get("/Resources")) or {}
    for font in (res(resources.get("/Font")) or {}).values():
        font = res(font)
        sub = str(font.get("/Subtype")).lstrip("/")
        enc = res(font.get("/Encoding"))
        if isinstance(enc, str):
            key = sub + ":" + enc.lstrip("/")
        elif enc is not None:
            key = sub + ":Differences"
        else:
            key = sub
        if "/ToUnicode" not in font:
            key += " (no ToUnicode)"
        fonts[key] = fonts.get(key, 0) + 1
    for xobj in (res(resources.get("/XObject")) or {}).values():
        xobj = res(xobj)
        if xobj.get("/Subtype") == "/Image":
            flt = xobj.get("/Filter")
            name = "+".join(str(f) for f in flt) if isinstance(flt, list) else str(flt)
            filters[name] = filters.get(name, 0) + 1
    if index < 3:
        try:
            if re.search(rb"(^|\s)3\s+Tr\b", page.get_contents().get_data() or b""):
                invisible = True
        except Exception:
            pass
root = reader.trailer["/Root"]
acro = res(root.get("/AcroForm"))
fields = len(reader.get_fields() or {}) if acro else 0
engine = None
for needle, name in ((b"LuaTeX", "LuaTeX"), (b"XeTeX", "XeTeX"), (b"xdvipdfmx", "XeTeX/xdvipdfmx"),
                     (b"PTEX.Fullbanner", "pdfTeX"), (b"dvips", "dvips")):
    if needle in raw:
        engine = name
        break
print(json.dumps({
    "tex_engine": engine,
    "header": raw[:8].decode("latin-1").strip(),
    "pdf_version": reader.pdf_header.replace("%PDF-", ""),
    "xref_stream": b"/XRef" in raw,
    "object_streams": b"/ObjStm" in raw,
    "linearized": b"/Linearized" in raw[:2048],
    "eof_count": raw.count(b"%%EOF"),
    "encrypted": reader.is_encrypted,
    "tagged": "/StructTreeRoot" in root,
    "acroform_fields": fields,
    "xfa": bool(acro and "/XFA" in acro),
    "optional_content": "/OCProperties" in root,
    "fonts": fonts,
    "image_filters": filters,
    "invisible_text_3Tr": invisible,
    "page_sizes": sorted(sizes),
    "rotations": sorted(rotations),
}))
"""


def profile_pdf(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-I", "-c", _PROFILE, str(path)],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=tempfile.gettempdir(),
        check=False,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip()[-400:]}
    data: dict[str, Any] = json.loads(result.stdout.strip().splitlines()[-1])
    return data


def producer_family(producer: str, creator: str) -> str:
    text = f"{producer} {creator}".lower().replace("\u00ae", "")
    rules = [
        ("pdfmaker", "Microsoft Office via Acrobat PDFMaker"),
        ("microsoft word", "Microsoft Word"),
        ("microsoft excel", "Microsoft Excel"),
        ("cvision", "CVISION PdfCompressor"),
        ("powerpoint", "Microsoft PowerPoint"),
        ("arxiv genpdf", "TeX (arXiv GenPDF, pikepdf restamp)"),
        ("pdftex", "pdfTeX"),
        ("luatex", "LuaTeX"),
        ("xetex", "XeTeX"),
        ("xdvipdfmx", "XeTeX"),
        ("dvipdfm", "dvipdfmx"),
        ("microsoft", "Microsoft Office"),
        ("antenna house", "Antenna House"),
        ("luradocument", "LuraDocument (Internet Archive)"),
        ("adlib", "Adlib Express"),
        ("just pdf", "JustSystems JUST PDF"),
        ("google", "Google Docs/Slides"),
        ("indesign", "Adobe InDesign"),
        ("designer", "Adobe LiveCycle Designer"),
        ("distiller", "Adobe Distiller"),
        ("paper capture", "Adobe Acrobat Paper Capture"),
        ("acrobat", "Adobe Acrobat"),
        ("quartz", "Apple Quartz"),
        ("ghostscript", "Ghostscript"),
        ("skia", "Skia/Chromium"),
        ("libreoffice", "LibreOffice"),
        ("openoffice", "OpenOffice"),
        ("itext", "iText"),
        ("abbyy", "ABBYY"),
        ("pdflib", "PDFlib"),
        ("qpdf", "qpdf"),
        ("adobe pdf library", "Adobe PDF Library"),
    ]
    for needle, family in rules:
        if needle in text:
            return family
    return producer.strip() or creator.strip() or "unknown"


# --------------------------------------------------------------------------- health

_HEALTH = r"""
import json, resource, subprocess, sys, time, warnings
warnings.simplefilter("ignore")
path, tool = sys.argv[1], sys.argv[2]
start = time.perf_counter()
out = {"tool": tool}
try:
    if tool == "pylopdf":
        import pylopdf
        with pylopdf.open(path) as doc:
            text = doc.get_text()
            pages = doc.page_count
    elif tool == "pymupdf":
        import pymupdf
        with pymupdf.open(path) as doc:
            text = "".join(page.get_text() for page in doc)
            pages = doc.page_count
    else:
        text = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"], capture_output=True,
                              check=True, timeout=240).stdout.decode("utf-8", "replace")
        pages = text.count("\f")
    out.update(chars=len(text), nonspace=sum(1 for c in text if not c.isspace()),
               replacement=text.count("\ufffd"), pages=pages, text=text)
except Exception as error:
    out["error"] = f"{type(error).__name__}: {str(error)[:200]}"
out["seconds"] = round(time.perf_counter() - start, 3)
own, kids = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
out["cpu_seconds"] = round(own.ru_utime + own.ru_stime + kids.ru_utime + kids.ru_stime, 3)
out["peak_rss_kib"] = max(own.ru_maxrss, kids.ru_maxrss)
print(json.dumps(out))
"""


def bigram_f1(left: str, right: str) -> float | None:
    """Whitespace-free character-bigram multiset F1, a language-agnostic agreement proxy."""
    a = "".join(left.split())
    b = "".join(right.split())
    if not a and not b:
        return None
    grams_a = Counter(a[i : i + 2] for i in range(len(a) - 1))
    grams_b = Counter(b[i : i + 2] for i in range(len(b) - 1))
    overlap = sum((grams_a & grams_b).values())
    total = sum(grams_a.values()) + sum(grams_b.values())
    return round(2 * overlap / total, 4) if total else 0.0


def health_pdf(path: Path, tool: str) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-c", _HEALTH, str(path), tool],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=tempfile.gettempdir(),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"tool": tool, "error": "timeout after 300 s"}
    if result.returncode != 0 or not result.stdout.strip():
        return {"tool": tool, "error": f"exit {result.returncode}: {result.stderr.strip()[-200:]}"}
    data: dict[str, Any] = json.loads(result.stdout.strip().splitlines()[-1])
    return data


# --------------------------------------------------------------------------- validation

MANIFEST_REQUIRED = {
    "id": str,
    "url": str,
    "license": str,
    "license_url": str,
    "attribution": str,
    "kind": str,
    "title": str,
    "languages": list,
    "retrieved_at": str,
    "sha256": str,
    "original_sha256": str,
    "page_range_kept": str,
    "page_count": int,
    "bytes": int,
    "path": str,
}


def validate_manifest_record(record: dict[str, Any]) -> list[str]:
    """Return schema problems for one manifest document record (empty when valid)."""
    errors: list[str] = []
    for key, kind in MANIFEST_REQUIRED.items():
        if not isinstance(record.get(key), kind) or isinstance(record.get(key), bool):
            errors.append(f"{key}: expected {kind.__name__}")
    if errors:
        return errors
    if record["license"] not in LICENSES:
        errors.append(f"license: unknown {record['license']!r}")
    if not record["license_url"].startswith("https://"):
        errors.append("license_url: must be https")
    if not record["url"].startswith("https://"):
        errors.append("url: must be https")
    if record["kind"] not in SOURCE_KINDS:
        errors.append(f"kind: unknown {record['kind']!r}")
    for key in ("sha256", "original_sha256"):
        value = record[key]
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            errors.append(f"{key}: not a sha256 hex digest")
    try:
        datetime.strptime(record["retrieved_at"] + "+0000", "%Y-%m-%dT%H:%M:%SZ%z")
    except ValueError:
        errors.append("retrieved_at: expected UTC YYYY-MM-DDTHH:MM:SSZ")
    if not 1 <= record["page_count"] <= MAX_KEPT_PAGES:
        errors.append("page_count: outside 1..30")
    if not 0 < record["bytes"] <= MAX_KEPT_BYTES:
        errors.append("bytes: outside 1..5 MiB")
    if not valid_range(record["page_range_kept"]):
        errors.append("page_range_kept: expected qpdf range such as 1-6 or 1,3,5-7")
    path = Path(record["path"])
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("pdfs",):
        errors.append("path: must be relative under pdfs/")
    if not record["attribution"].strip():
        errors.append("attribution: empty")
    if not record["languages"] or not all(isinstance(x, str) and x for x in record["languages"]):
        errors.append("languages: expected non-empty BCP 47 tags")
    return errors


def clamp_range(spec: str | None, pages: int) -> str | None:
    """Clamp a simple ``a-b`` range to the document length; other specs pass through."""
    if not spec:
        return None
    start, _, end = spec.partition("-")
    if end.isdigit() and start.isdigit():
        return f"{start}-{min(int(end), pages)}"
    return spec


def valid_range(text: str) -> bool:
    for part in text.split(","):
        bounds = part.split("-")
        if not 1 <= len(bounds) <= 2 or not all(b.isdigit() and int(b) >= 1 for b in bounds):
            return False
        if len(bounds) == 2 and int(bounds[0]) > int(bounds[1]):
            return False
    return bool(text)


def validate_truth(truth: dict[str, Any]) -> list[str]:
    """Return schema problems for one truth.json (wild-v1 schema plus real-world fields)."""
    errors: list[str] = []
    if truth.get("version") != 1:
        errors.append("version: expected 1")
    for key in ("doc_id", "truth_method", "truth_status"):
        if not isinstance(truth.get(key), str) or not truth.get(key):
            errors.append(f"{key}: expected non-empty string")
    status = truth.get("truth_status")
    if status not in TRUTH_STATUSES:
        errors.append(f"truth_status: expected one of {sorted(TRUTH_STATUSES)}")
    if not isinstance(truth.get("uncertainty"), list):
        errors.append("uncertainty: expected list of strings (may be empty)")
    pages = truth.get("pages")
    if not isinstance(pages, list) or not pages or not all(isinstance(p, int) and p >= 1 for p in pages):
        errors.append("pages: expected non-empty list of 1-based page numbers")
        pages = []
    languages = truth.get("languages")
    if not isinstance(languages, list) or not languages:
        errors.append("languages: expected non-empty list")
    blocks = truth.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        return [*errors, "blocks: expected non-empty list"]
    table_ids: set[str] = set()
    for index, block in enumerate(blocks):
        where = f"blocks[{index}]"
        if not isinstance(block, dict):
            errors.append(f"{where}: expected object")
            continue
        kind = block.get("kind")
        if kind not in BLOCK_KINDS:
            errors.append(f"{where}.kind: unknown {kind!r}")
            continue
        if block.get("page") not in pages:
            errors.append(f"{where}.page: must be one of the truth pages")
        partial = block.get("partial", False)
        if not isinstance(partial, bool):
            errors.append(f"{where}.partial: expected bool")
        if partial and status == "verified":
            errors.append(f"{where}: partial blocks require truth_status 'partial'")
        if kind in TEXT_KINDS | {"caption", "formula"}:
            if not isinstance(block.get("text"), str) or not block["text"].strip():
                errors.append(f"{where}.text: expected non-empty string")
            if kind == "heading" and block.get("level") not in {1, 2, 3, 4, 5, 6}:
                errors.append(f"{where}.level: expected 1..6")
        elif kind == "list":
            items = block.get("items")
            if not isinstance(items, list) or not items or not all(isinstance(i, str) for i in items):
                errors.append(f"{where}.items: expected non-empty list of strings")
        elif kind == "table":
            errors.extend(_validate_table(block, where, table_ids))
    return errors


def _validate_table(block: dict[str, Any], where: str, table_ids: set[str]) -> list[str]:
    errors: list[str] = []
    table_id = block.get("id")
    if not isinstance(table_id, str) or not table_id or table_id in table_ids:
        errors.append(f"{where}.id: expected unique non-empty string")
    else:
        table_ids.add(table_id)
    if block.get("partial"):
        errors.append(f"{where}: table cell matrices must be complete")
    if block.get("rendering") not in TABLE_RENDERINGS:
        errors.append(f"{where}.rendering: expected one of {sorted(TABLE_RENDERINGS)}")
    values = block.get("values")
    if not isinstance(values, list) or not values or not all(isinstance(row, list) and row for row in values):
        return [*errors, f"{where}.values: expected non-empty matrix"]
    width = len(values[0])
    if any(len(row) != width for row in values):
        errors.append(f"{where}.values: rows must all have {width} cells")
    if not all(isinstance(cell, str) for row in values for cell in row):
        errors.append(f"{where}.values: cells must be strings")
    header_rows = block.get("header_rows")
    if not isinstance(header_rows, int) or not 0 <= header_rows <= len(values):
        errors.append(f"{where}.header_rows: expected 0..row count")
    for span in block.get("spans", []):
        try:
            row, column = span["row"], span["column"]
            rows, columns = span["row_span"], span["column_span"]
        except (KeyError, TypeError):
            errors.append(f"{where}.spans: expected row/column/row_span/column_span")
            continue
        if not (
            0 <= row < len(values)
            and 0 <= column < width
            and rows >= 1
            and columns >= 1
            and row + rows <= len(values)
            and column + columns <= width
            and rows * columns > 1
        ):
            errors.append(f"{where}.spans: span {span} outside the matrix")
    return errors


def validate_directory(directory: Path) -> dict[str, list[str]]:
    directory = guard_path(directory)
    problems: dict[str, list[str]] = {}
    manifest = load_manifest(directory)
    ids = set()
    for record in manifest["documents"]:
        errors = validate_manifest_record(record)
        pdf = directory / record.get("path", "")
        if not errors:
            if not pdf.is_file():
                errors.append("path: file missing")
            elif sha256_file(pdf) != record["sha256"]:
                errors.append("sha256: mismatch")
        ids.add(record.get("id"))
        if errors:
            problems[str(record.get("id"))] = errors
    for path in sorted((directory / "truth").glob("*.json")):
        truth = json.loads(path.read_text())
        errors = validate_truth(truth)
        if truth.get("doc_id") not in ids:
            errors.append("doc_id: not in manifest")
        if errors:
            problems[f"truth/{path.name}"] = errors
    return problems


# --------------------------------------------------------------------------- CLI


def _cmd_fetch(args: argparse.Namespace) -> None:
    directory = guard_path(args.directory)
    wanted = set(args.id or [])
    log = directory / "requests.log"
    for source in SOURCES:
        if wanted and source["id"] not in wanted:
            continue
        before = log.stat().st_size if log.exists() else 0
        try:
            record = fetch_source(source, directory, force=args.force, reuse=not args.no_reuse)
            print(
                f"ok   {source['id']}: {record['page_count']} pages, {record['bytes']} bytes, "
                f"{record['producer'] or record['creator']}"
            )
        except Exception as error:  # failures are reported, not fatal
            print(f"FAIL {source['id']}: {type(error).__name__}: {error}")
        if (log.stat().st_size if log.exists() else 0) != before:
            time.sleep(REQUEST_DELAY_SECONDS)  # be polite after a real HTTP request


def _cmd_profile(args: argparse.Namespace) -> None:
    directory = guard_path(args.directory)
    manifest = load_manifest(directory)
    for record in manifest["documents"]:
        profile = profile_pdf(directory / record["path"])
        record["profile"] = profile
        record["producer_family"] = producer_family(record.get("producer", ""), record.get("creator", ""))
        print(
            record["id"],
            record["producer_family"],
            profile.get("pdf_version"),
            "xref-stream" if profile.get("xref_stream") else "",
            profile.get("fonts"),
        )
    save_manifest(directory, manifest)


def _cmd_health(args: argparse.Namespace) -> None:
    directory = guard_path(args.directory)
    manifest = load_manifest(directory)
    rows = []
    for record in manifest["documents"]:
        path = directory / record["path"]
        row = {"id": record["id"], "producer_family": record.get("producer_family", "")}
        for tool in ("pylopdf", "pdftotext", "pymupdf"):
            row[tool] = health_pdf(path, tool)
        texts = {tool: row[tool].pop("text", None) for tool in ("pylopdf", "pdftotext", "pymupdf")}
        for other in ("pdftotext", "pymupdf"):
            if texts["pylopdf"] is not None and texts[other] is not None:
                row[f"pylopdf_vs_{other}_bigram_f1"] = bigram_f1(texts["pylopdf"], texts[other])
        rows.append(row)
        tools = ("pylopdf", "pdftotext", "pymupdf")
        print(record["id"], {tool: row[tool].get("nonspace", row[tool].get("error")) for tool in tools})
    measurement = (
        "Each tool runs in its own isolated subprocess, sequentially; seconds are wall time inside "
        "that process, CPU and peak RSS come from getrusage (self + children) at exit."
    )
    (directory / "health.json").write_text(
        json.dumps({"generated_at": _now(), "measurement": measurement, "rows": rows}, indent=2) + "\n"
    )
    lines = [
        (
            "| Document | Producer | pylopdf | pdftotext | PyMuPDF | F1 vs pdftotext | F1 vs PyMuPDF "
            "| pylopdf s | pylopdf CPU s | pylopdf RSS MiB |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:

        def cell(result: dict[str, Any]) -> str:
            return f"ERROR {result['error'][:60]}" if "error" in result else str(result["nonspace"])

        lines.append(
            f"| {row['id']} | {row['producer_family']} | {cell(row['pylopdf'])} | "
            f"{cell(row['pdftotext'])} | {cell(row['pymupdf'])} | "
            f"{row.get('pylopdf_vs_pdftotext_bigram_f1', '')} | {row.get('pylopdf_vs_pymupdf_bigram_f1', '')} | "
            f"{row['pylopdf'].get('seconds', '')} | {row['pylopdf'].get('cpu_seconds', '')} | "
            f"{round(row['pylopdf'].get('peak_rss_kib', 0) / 1024, 1)} |"
        )
    (directory / "health.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def _cmd_candidates(args: argparse.Namespace) -> None:
    """Write extractor candidates and a 100 dpi render for one page to reconcile by eye."""
    directory = guard_path(args.directory)
    pdf = directory / "pdfs" / f"{args.id}.pdf"
    out = directory / "candidates" / args.id
    out.mkdir(parents=True, exist_ok=True)
    page = args.page
    layout = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", "-f", str(page), "-l", str(page), str(pdf), "-"],
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8", "replace")
    (out / f"p{page}.pdftotext.txt").write_text(layout)
    script = (
        "import sys, warnings, pymupdf, pylopdf\nwarnings.simplefilter('ignore')\n"
        "p, n, o = sys.argv[1], int(sys.argv[2]) - 1, sys.argv[3]\n"
        "with pymupdf.open(p) as d: open(o + '.pymupdf.txt', 'w').write(d[n].get_text())\n"
        "with pylopdf.open(p) as d:\n"
        "    pg = d[n]\n    open(o + '.pylopdf.txt', 'w').write(pg.get_text())\n"
        "    open(o + '.pylopdf.md', 'w').write(d.to_markdown(pages=[n]))\n"
    )
    subprocess.run([sys.executable, "-c", script, str(pdf), str(page), str(out / f"p{page}")], check=True)
    subprocess.run(
        ["pdftoppm", "-r", str(args.dpi), "-png", "-f", str(page), "-l", str(page), str(pdf), str(out / f"p{page}")],
        check=True,
    )
    print(out)


def _cmd_validate(args: argparse.Namespace) -> None:
    problems = validate_directory(args.directory)
    for key, errors in problems.items():
        for error in errors:
            print(f"{key}: {error}")
    print("valid" if not problems else f"{len(problems)} invalid entries")
    if problems:
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch")
    fetch.add_argument("--id", action="append")
    fetch.add_argument("--force", action="store_true")
    fetch.add_argument("--no-reuse", action="store_true", help="download again even if cached")
    fetch.set_defaults(func=_cmd_fetch)
    commands.add_parser("profile").set_defaults(func=_cmd_profile)
    commands.add_parser("health").set_defaults(func=_cmd_health)
    candidates = commands.add_parser("candidates")
    candidates.add_argument("--id", required=True)
    candidates.add_argument("--page", type=int, required=True)
    candidates.add_argument("--dpi", type=int, default=100)
    candidates.set_defaults(func=_cmd_candidates)
    commands.add_parser("validate").set_defaults(func=_cmd_validate)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
