"""Authored wild-v1 documents for the unnamed, merged_headers and mixed families."""

# ruff: noqa: E501
from __future__ import annotations

from datetime import date
from typing import Any

from bench.wild_templates import model
from bench.wild_templates.common import H, L, P, box, chart, chart_table, photo, plan_table, screenshot
from bench.wild_templates.model import day, money

# ---------------------------------------------------------------- unnamed (blank first row)


def lab_appendix_en(plan: dict[str, Any]) -> dict[str, Any]:
    """English lab data appendix with a blank first table row and a spreadsheet-only table (kinds: word2, usd, date)."""
    items = [
        ("Trypsin-EDTA 0.25%, 100 mL", 3850, date(2026, 1, 12)), ("Fetal bovine serum, 500 mL", 61200, date(2026, 1, 12)),
        ("DMEM high glucose, 6 × 500 mL", 14730, date(2026, 1, 19)), ("Penicillin–streptomycin 100×", 4275, date(2026, 1, 19)),
        ("Serological pipettes 10 mL, case of 200", 9640, date(2026, 1, 26)), ("96-well plates, flat bottom, 50/pk", 11820, date(2026, 2, 2)),
        ("ELISA kit, human IL-6", 68900, date(2026, 2, 2)), ("Cryovials 2 mL, 500/pk", 7490, date(2026, 2, 9)),
        ("Nitrile gloves M, 10 × 100", 8160, date(2026, 2, 9)), ("PBS 10×, 1 L", 2980, date(2026, 2, 16)),
        ("Liquid nitrogen refill, 160 L dewar", 21000, date(2026, 2, 23)),
    ]
    rows = [{"word2": [name], "usd": [money(c, "en-US")], "date": [day(d, "iso")]} for name, c, d in items]
    table = plan_table(plan, 0, "t1", "ruled", ["word2", "usd", "date"], rows, header=None,
                       caption="Table C1. Reagent and consumables log, January–February 2026", widths=[56, 20, 24])
    plate = [["Well", "Sample", "A450", "IL-6 (pg/mL)"], ["A1", "Blank", "0.048", "—"], ["A2", "Std 1 (300 pg/mL)", "2.314", "300.0"],
             ["A3", "Std 2 (150 pg/mL)", "1.276", "150.0"], ["A4", "Std 3 (75 pg/mL)", "0.702", "75.0"],
             ["B1", "Donor 07, day 0", "0.391", "38.6"], ["B2", "Donor 07, day 3", "1.058", "121.9"],
             ["B3", "Donor 12, day 0", "0.287", "26.4"], ["B4", "Donor 12, day 3", "0.944", "107.3"]]
    sheet = {"title": "IL6_plate2_2026-02-18.xlsx — Sheets", "menu": ["File", "Edit", "View", "Insert", "Format", "Data", "Tools"],
             "cell": "D6", "formula": "=FORECAST(C6, standards!B2:B9, standards!A2:A9)", "tabs": ["plate2", "standards", "notes"],
             "rows": plate, "numeric": [False, False, True, True], "selected_row": 6, "width": 640}
    return {
        "template": "lab_data_appendix", "page_size": "Letter", "languages": ["en-US"],
        "metadata": {"title": "Appendix C — Materials and raw data, IL-6 response study", "author": "Okafor Lab, Department of Immunology",
                     "subject": "Supplementary materials log and ELISA plate export", "keywords": ["appendix", "ELISA", "IL-6", "reagents"],
                     "lang": "en-US", "created": "2026-02-27T19:10:00Z"},
        "theme": {"accent": "#2d4a6b", "body_font": "'Noto Serif'", "heading_font": "'Noto Sans'", "font_size": "9.6pt"},
        "running_header": "IL-6 response study — supplementary material",
        "running_footer": "Appendix C · {page}",
        "blocks": [
            H(1, "Appendix C — Materials and raw data"),
            photo("f1", ["microscope", "lab-pipettes", "lab-glassware"], ["lab", "science"],
                  {"microscope": "Inverted microscope used for confluence checks.", "lab-pipettes": "Pipettes calibrated before each plate run.",
                   "lab-glassware": "Media preparation glassware."},
                  "Laboratory equipment used in the study.", "right", "34%"),
            H(2, "C.1 Reagents and consumables"),
            P("All reagents were stored according to the manufacturer’s instructions: serum and trypsin at −20 °C, media "
              "at 2–8 °C protected from light. Cells were seeded at 2.5 × 10⁵ cells/mL in 75 cm² flasks and passaged at "
              "≥ 80 % confluence. Pipettes were verified gravimetrically before use (accuracy ± 0.8 % at 100 µL)."),
            P("The log below was exported from the purchasing system; the export dropped the column headings, which are, "
              "from left to right: item, cost (USD, excluding shipping) and date received.", "small"),
            table,
            H(2, "C.2 ELISA plate export"),
            P("Absorbance was read at 450 nm with 570 nm correction. The standard curve (four-parameter logistic) gave "
              "R² = 0.998; samples below the lowest standard are reported as “—”. The screenshot shows the working sheet as "
              "shared with the statistics team on 18 February.¹"),
            screenshot("f2", "spreadsheet", sheet, "Figure C1. Plate 2 working sheet (screenshot)", width="80%"),
            model.table("t2", "screenshot", plate, caption="Plate 2 values as shown in Figure C1"),
            box("footnote", "¹ Raw instrument files (.xpt) are archived on the lab server under /il6/2026-02/plate2."),
        ],
    }


def lab_appendix_zh(plan: dict[str, Any]) -> dict[str, Any]:
    """Simplified Chinese reagent log with blank first row and vector line chart (kinds: word2, date, usd, word2)."""
    items = [
        ("无水乙醇（分析纯）500 mL×10", date(2026, 2, 3), 18600, "常温避火储存"), ("胰蛋白酶-EDTA 0.25%", date(2026, 2, 3), 26500, "−20 °C冻存"),
        ("DMEM高糖培养基", date(2026, 2, 10), 132000, "4 °C避光保存"), ("胎牛血清 500 mL", date(2026, 2, 10), 386000, "分装后冻存"),
        ("96孔细胞培养板", date(2026, 2, 17), 74000, "50块／箱"), ("CCK-8检测试剂盒", date(2026, 2, 24), 115000, "批号K2602"),
        ("移液器吸头 200 µL", date(2026, 3, 3), 42000, "灭菌独立包装"), ("液氮补充", date(2026, 3, 10), 36000, "每周补充一次"),
    ]
    rows = [{"word2": [name, note], "date": [day(d, "cjk")], "usd": [money(c, "zh")]} for name, d, c, note in items]
    table = plan_table(plan, 0, "t1", "ruled", ["word2", "date", "usd", "word2"], rows, header=None,
                       caption="表B-1　试剂与耗材采购记录（2026年2—3月）", widths=[36, 22, 18, 24])
    spec = {"title": "CO₂培养箱温度记录（°C）", "categories": ["3月2日", "3月3日", "3月4日", "3月5日", "3月6日", "3月9日", "3月10日"],
            "series": [("1号箱", [37.0, 37.1, 36.9, 37.0, 37.2, 37.0, 36.9]), ("2号箱", [37.1, 37.0, 37.0, 36.8, 37.0, 37.1, 37.0])],
            "min": 36.0, "max": 38.0, "ticks": 4, "tick_format": lambda v: f"{v:.1f}"}
    return {
        "template": "lab_data_appendix", "page_size": "A4", "languages": ["zh-CN"],
        "metadata": {"title": "附录B：试剂采购与设备运行记录", "author": "华东生物医药研究院 细胞生物学实验室",
                     "subject": "细胞增殖实验的试剂采购与培养箱温度记录", "keywords": ["附录", "试剂", "培养箱", "实验记录"],
                     "lang": "zh-CN", "created": "2026-03-12T02:30:00Z"},
        "theme": {"accent": "#7a1f2b", "font_size": "9.8pt"},
        "running_header": "细胞增殖实验报告　附录B",
        "running_footer": "第 {page} 页，共 {pages} 页",
        "blocks": [
            H(1, "附录B　试剂采购与设备运行记录"),
            P("本附录汇总了2026年2月至3月细胞增殖实验所用试剂与耗材的采购情况，以及两台CO₂培养箱的温度记录。"
              "采购数据由财务系统导出，导出文件缺少表头；各列依次为：试剂名称、到货日期、金额（含税）、备注。"),
            H(2, "B.1　采购记录"),
            table,
            P("说明：胎牛血清到货后按每管50 mL分装，避免反复冻融；CCK-8试剂盒批号已登记在实验记录本第14页。"
              "全部试剂均在有效期内使用。"),
            H(2, "B.2　培养箱温度"),
            P("两台培养箱的设定温度均为37.0 °C，允许偏差为±0.5 °C。记录期间未出现超限报警，最大偏差出现在3月5日（2号箱，36.8 °C），"
              "原因是当天上午频繁开门取样。"),
            chart("f1", "line", spec, "图B-1　培养箱每日上午9时温度读数", raster=False, width="82%"),
            chart_table("c1", "日期", spec, lambda v: f"{v:.1f}"),
            box("callout", "如需原始记录，请联系实验室管理员：王晓明（分机 8231）。", title="备注"),
        ],
    }


def lab_journal_ru(plan: dict[str, Any]) -> dict[str, Any]:
    """Russian equipment-verification log for LibreOffice with blank first row (kinds: word2, date, usd)."""
    items = [
        ("Весы аналитические Mettler Toledo XPR205", date(2026, 1, 14), 680000), ("pH-метр Hanna HI 2211", date(2026, 1, 14), 235000),
        ("Дозатор пипеточный 100–1000 мкл", date(2026, 1, 21), 145000), ("Термостат суховоздушный ТС-1/80 СПУ", date(2026, 1, 28), 390000),
        ("Спектрофотометр ПЭ-5400ВИ", date(2026, 2, 4), 970000), ("Центрифуга Eppendorf 5424 R", date(2026, 2, 11), 725000),
        ("Термометр электронный ЛТ-300", date(2026, 2, 18), 110000), ("Холодильник фармацевтический ХФ-250", date(2026, 2, 25), 280000),
        ("Шкаф сушильный ШС-80-01 СПУ", date(2026, 3, 4), 340000), ("Гигрометр психрометрический ВИТ-2", date(2026, 3, 11), 95000),
        ("Иономер И-160МИ", date(2026, 3, 18), 460000),
    ]
    rows = [{"word2": [n], "date": [day(d, "dotted")], "usd": [money(c, "ru")]} for n, d, c in items]
    table = plan_table(plan, 0, "t1", "ruled", ["word2", "date", "usd"], rows, header=None,
                       caption="Таблица П2.1. Поверка и калибровка оборудования в I квартале 2026 г.", widths=[58, 20, 22])
    total = sum(c for *_, c in items)
    return {
        "template": "lab_data_appendix", "page_size": "A4", "languages": ["ru-RU"],
        "metadata": {"title": "Приложение 2. Журнал поверки оборудования", "author": "Лаборатория аналитической химии, ФБУ «Северный ЦСМ»",
                     "subject": "Сведения о поверке средств измерений за I квартал 2026 года", "keywords": ["поверка", "оборудование", "журнал", "лаборатория"],
                     "lang": "ru-RU", "created": "2026-03-25T06:00:00Z"},
        "theme": {"accent": "#24476b", "lo_font": "Noto Serif", "lo_heading_font": "Noto Sans", "lo_size": "10pt", "content_cm": 17.2},
        "running_header": "Отчёт о деятельности лаборатории за I квартал 2026 г.",
        "running_footer": "Стр. {page} из {pages}",
        "blocks": [
            H(1, "Приложение 2. Журнал поверки оборудования"),
            photo("f1", ["lab-glassware", "lab-pipettes", "microscope"], ["lab", "science"],
                  {"lab-glassware": "Мерная посуда проходит калибровку отдельно.", "lab-pipettes": "Дозаторы поверяются гравиметрическим методом.",
                   "microscope": "Оптическое оборудование лаборатории."},
                  "Оборудование лаборатории.", "right", width_cm=5.5),
            P("В I квартале 2026 года все средства измерений лаборатории прошли плановую поверку в установленные сроки. "
              "Замечаний к состоянию оборудования не выявлено; дозатор пипеточный после поверки отнесён к классу точности "
              "±0,6 % при объёме 1000 мкл."),
            P("Ниже приведена выгрузка из учётной системы. При экспорте строка заголовков оказалась пустой; столбцы "
              "означают: наименование прибора, дату поверки и стоимость услуги (без НДС)."),
            table,
            P(f"Общая стоимость поверки составила {money(total, 'ru')}. Расходы покрыты за счёт средств, предусмотренных "
              "планом финансово-хозяйственной деятельности на 2026 год."),
            H(2, "Замечания"),
            L(["Весы XPR205 перенесены на антивибрационный стол после поверки.",
               "Для термостата ТС-1/80 СПУ заказан запасной датчик температуры.",
               "Следующая поверка спектрофотометра — не позднее 04.02.2027."]),
        ],
    }


# ---------------------------------------------------------------- merged headers


def grant_en(plan: dict[str, Any]) -> dict[str, Any]:
    """US grant budget with a grouped half-year header (kinds: date, word2, usd, mixed; merge over usd+mixed)."""
    items = [
        (date(2026, 7, 1), "Field technician salaries (2.0 FTE)", 5840000), (date(2026, 7, 1), "Fringe benefits at 31%", 1810400),
        (date(2026, 7, 15), "Water-level loggers and telemetry (12 units)", 1428000), (date(2026, 8, 3), "Boat fuel, maintenance and dock fees", 675000),
        (date(2026, 9, 1), "Laboratory analysis: nutrients and salinity", 986000), (date(2026, 10, 5), "Partner subaward — Haifa coastal data team", 1250000),
        (date(2026, 11, 2), "Community science training workshops", 420000),
    ]
    total = sum(c for *_, c in items)
    rows = [{"date": [day(d, "us")], "word2": [text], "usd": [money(c, "en-US")], "mixed": [f"{c / total * 100:.1f}%"]} for d, text, c in items]
    table = plan_table(plan, 0, "t1", "ruled", ["date", "word2", "usd", "mixed"], rows,
                       header={"date": ["Start"], "word2": ["Budget line"], "usd": ["Q3–Q4 FY2026"], "mixed": [""]},
                       subheader={"date": [""], "word2": [""], "usd": ["Requested"], "mixed": ["Share"]},
                       total={"date": [""], "word2": ["Total request"], "usd": [money(total, "en-US")], "mixed": ["100.0%"]},
                       numeric=("usd", "mixed"), caption="Table 1. Year 2 budget request by line (second half of FY2026)", widths=[14, 50, 20, 16])
    spec = {"title": "Quarterly spending, FY2026 (USD thousands)", "categories": ["Q1", "Q2", "Q3", "Q4"],
            "series": [("Planned", [52.0, 55.0, 64.0, 60.1]), ("Actual / forecast", [49.6, 57.2, 66.0, 58.1])], "max": 80, "ticks": 4,
            "tick_format": lambda v: f"{v:.0f}"}
    return {
        "template": "grant_budget", "page_size": "Letter", "languages": ["en-US", "he", "ar"],
        "metadata": {"title": "Coastal Wetland Monitoring Network — Year 2 budget justification", "author": "Gulf Estuary Research Consortium",
                     "subject": "Budget request and justification for the second half of FY2026", "keywords": ["grant", "budget", "wetlands", "monitoring"],
                     "lang": "en-US", "created": "2026-05-18T14:00:00Z"},
        "theme": {"accent": "#235d3a", "body_font": "'Noto Serif'", "heading_font": "'Noto Sans'", "font_size": "9.7pt"},
        "running_header": "Award NA-26-CW-0042 · Budget justification",
        "running_footer": "Gulf Estuary Research Consortium — {page} of {pages}",
        "blocks": [
            H(1, "Year 2 budget justification"),
            P("Coastal Wetland Monitoring Network · Award NA-26-CW-0042 · Principal investigator: Dr. Renée Castellanos", "small muted"),
            H(2, "1. Summary of request"),
            P("We request $124,094.00 for the second half of FY2026 to keep twelve tidal monitoring stations online through "
              "the hurricane season and to extend the network’s data-sharing agreement with our Mediterranean partners. Personnel "
              "remain the largest share of the budget because station visits cannot be automated: loggers must be cleaned, "
              "downloaded and re-leveled every three weeks."),
            table,
            H(2, "2. Spending to date"),
            P("Spending in the first half of the year tracked the plan closely. The Q2 overrun reflects an emergency replacement "
              "of two loggers after a February storm; it is offset by lower boat costs in Q4 because two stations will be "
              "serviced from shore."),
            chart("f1", "bar", spec, "Figure 1. Planned and actual quarterly spending", raster=False, width="80%"),
            chart_table("c1", "Quarter", spec, lambda v: f"{v:.1f}"),
            H(2, "3. Partners"),
            P("The subaward funds the coastal data team led by Dr. \u2068נועה לוי\u2069 (Noa Levi) at the University of Haifa, who "
              "maintains the shared quality-control code. Dr. \u2068سامي حداد\u2069 (Sami Haddad) of the American University of Beirut "
              "contributes salinity calibration data at no cost to the award.¹"),
            box("footnote", "¹ Letters of collaboration are included in Attachment D. Indirect costs are excluded from this request per the program notice."),
        ],
    }


def grant_ko(plan: dict[str, Any]) -> dict[str, Any]:
    """Korean arts-program budget with grouped schedule header (kinds: mixed, date, word1, usd, word2; merge over date+word1)."""
    items = [
        ("가-1", date(2026, 3, 2), "1분기", 12000000, "강사비 (공연예술 워크숍 8회)"), ("가-2", date(2026, 3, 16), "1분기", 4500000, "참여자 재료비 및 소품"),
        ("가-3", date(2026, 4, 6), "2분기", 8800000, "구민회관 소극장 대관료"), ("나-1", date(2026, 4, 20), "2분기", 6200000, "홍보물 제작 및 온라인 광고"),
        ("나-2", date(2026, 5, 11), "2분기", 3000000, "사진·영상 기록"), ("나-3", date(2026, 6, 1), "2분기", 2400000, "자원봉사자 활동비"),
        ("다-1", date(2026, 7, 6), "3분기", 15000000, "지역 축제 무대 설치 및 음향"), ("다-2", date(2026, 8, 17), "3분기", 5600000, "초청 공연단 출연료"),
        ("다-3", date(2026, 9, 7), "3분기", 1800000, "안전 관리 및 행사 보험"), ("라-1", date(2026, 10, 12), "4분기", 3500000, "결과 보고서 및 자료집 인쇄"),
        ("라-2", date(2026, 11, 2), "4분기", 2200000, "성과 공유회 운영"),
    ]
    rows = [{"mixed": [code], "date": [day(d, "ko")], "word1": [q], "usd": [money(c, "ko")], "word2": [text]} for code, d, q, c, text in items]
    total = sum(i[3] for i in items)
    table = plan_table(plan, 0, "t1", "ruled", ["mixed", "date", "word1", "usd", "word2"], rows,
                       header={"mixed": ["항목"], "date": ["집행 일정"], "word1": [""], "usd": ["예산액"], "word2": ["세부 내용"]},
                       subheader={"mixed": [""], "date": ["착수일"], "word1": ["분기"], "usd": [""], "word2": [""]},
                       total={"mixed": ["합계"], "date": [""], "word1": [""], "usd": [money(total, "ko")], "word2": [""]},
                       caption="표 1. 세부 항목별 예산 집행 계획", widths=[9, 17, 10, 18, 46])
    quarters: dict[str, int] = {}
    for item in items:
        quarters[item[2]] = quarters.get(item[2], 0) + item[3]
    spec = {"title": "분기별 예산 배분 (백만 원)", "categories": list(quarters), "series": [("예산", [v / 1e6 for v in quarters.values()])],
            "max": 25, "ticks": 5, "tick_format": lambda v: f"{v:.0f}"}
    return {
        "template": "grant_budget", "page_size": "A4", "languages": ["ko-KR"],
        "metadata": {"title": "2026년도 지역 문화예술 지원사업 예산 계획서", "author": "사단법인 마을공연예술협동조합",
                     "subject": "‘우리 동네 무대’ 사업 예산 및 집행 계획", "keywords": ["예산 계획서", "문화예술", "지원사업"],
                     "lang": "ko-KR", "created": "2026-02-10T00:30:00Z"},
        "theme": {"accent": "#1d4f91", "font_size": "9.6pt"},
        "running_header": "2026년도 지역 문화예술 지원사업 | 우리 동네 무대",
        "running_footer": "- {page} -",
        "blocks": [
            H(1, "2026년도 ‘우리 동네 무대’ 예산 계획서"),
            P("신청 단체: 사단법인 마을공연예술협동조합 · 사업 기간: 2026. 3. 2. ~ 2026. 11. 30. · 담당자: 박서연", "small muted"),
            H(2, "1. 사업 개요"),
            P("‘우리 동네 무대’는 주민이 직접 기획하고 출연하는 생활 공연예술 프로그램입니다. 상반기에는 연극·음악 워크숍을 "
              "통해 참여자를 모집하고, 하반기에는 지역 축제 무대에서 그 결과를 선보입니다. 작년 시범 사업에는 주민 126명이 "
              "참여했으며, 만족도 조사에서 응답자의 91%가 ‘다시 참여하겠다’고 답했습니다."),
            H(2, "2. 예산 집행 계획"),
            table,
            chart("f1", "bar", spec, "그림 1. 분기별 예산 배분", raster=False, width="70%"),
            chart_table("c1", "분기", spec, lambda v: f"{v:.1f}"),
            H(2, "3. 자부담 및 정산"),
            L(["자부담 10%는 조합 적립금으로 충당합니다.", "모든 지출은 전용 계좌와 카드로 집행하고 증빙을 보관합니다.",
               "중간 정산은 2026. 7. 31.까지, 최종 정산은 2026. 12. 15.까지 제출합니다."]),
        ],
    }


def butce_tr(plan: dict[str, Any]) -> dict[str, Any]:
    """Turkish association project budget for LibreOffice (kinds: date, word2, usd; merge over date+word2)."""
    items = [
        (date(2026, 4, 6), "Gönüllü eğitimi ve iş güvenliği semineri", 750000), (date(2026, 4, 20), "Toplama ekipmanı: eldiven, maşa, file çuval", 1824000),
        (date(2026, 5, 4), "İnciraltı sahili temizlik günü – ulaşım", 960000), (date(2026, 5, 18), "Atıkların ayrıştırılması ve geri dönüşüm bedeli", 435000),
        (date(2026, 6, 1), "Çocuklar için deniz ekolojisi atölyesi", 680000), (date(2026, 6, 15), "Mikroplastik numune analizi (Ege Üniversitesi)", 1250000),
        (date(2026, 6, 29), "Sosyal medya içerikleri ve basın bülteni", 320000), (date(2026, 7, 13), "Sonuç raporunun basımı ve dağıtımı", 275000),
    ]
    rows = [{"date": [day(d, "dotted")], "word2": [t], "usd": [money(c, "tr")]} for d, t, c in items]
    total = sum(c for *_, c in items)
    table = plan_table(plan, 0, "t1", "ruled", ["date", "word2", "usd"], rows,
                       header={"date": ["Faaliyet"], "word2": [""], "usd": ["Tutar"]},
                       subheader={"date": ["Tarih"], "word2": ["Açıklama"], "usd": [""]},
                       total={"date": [""], "word2": ["Toplam"], "usd": [money(total, "tr")]},
                       caption="Tablo 1. Faaliyet bazında bütçe", widths=[18, 58, 24])
    return {
        "template": "grant_budget", "page_size": "A4", "languages": ["tr-TR"],
        "metadata": {"title": "Temiz Kıyılar Projesi – Bütçe Planı 2026", "author": "İzmir Kıyı Gönüllüleri Derneği",
                     "subject": "Hibe başvurusu için ayrıntılı bütçe ve gerekçe", "keywords": ["bütçe", "hibe", "kıyı temizliği", "İzmir"],
                     "lang": "tr-TR", "created": "2026-03-03T08:00:00Z"},
        "theme": {"accent": "#0d5c75", "lo_font": "Noto Sans", "lo_heading_font": "Noto Sans", "lo_size": "10pt", "content_cm": 17.2},
        "running_header": "İzmir Kıyı Gönüllüleri Derneği",
        "running_footer": "Sayfa {page} / {pages}",
        "blocks": [
            H(1, "Temiz Kıyılar Projesi – Bütçe Planı"),
            P("Başvuru sahibi: İzmir Kıyı Gönüllüleri Derneği · Proje süresi: Nisan–Temmuz 2026 · Sorumlu: Elif Yıldırım", "small"),
            H(2, "Projenin amacı"),
            P("Proje, İnciraltı ve Güzelbahçe sahillerinde dört ay boyunca düzenli temizlik günleri yapmayı, toplanan atıkları "
              "ayrıştırarak geri dönüşüme kazandırmayı ve mikroplastik kirliliğini ölçmeyi amaçlıyor. Geçen yıl 412 gönüllüyle "
              "3,8 ton atık toplanmıştı; bu yıl hedefimiz 5 ton."),
            H(2, "Bütçe"),
            table,
            P("Tüm tutarlara KDV dahildir. Ekipmanlar proje bitiminde derneğin envanterine kaydedilecek ve sonraki "
              "etkinliklerde kullanılacaktır. Ulaşım giderleri, İzmir Büyükşehir Belediyesi’nin sağladığı ücretsiz otobüs "
              "desteği dikkate alınarak hesaplanmıştır.¹"),
            box("footnote", "¹ Belediye desteği yazılı olarak teyit edilirse ulaşım kalemi 4.800,00 ₺ azalacaktır."),
        ],
    }


# ---------------------------------------------------------------- mixed (ruled plus borderless)


def research_en(plan: dict[str, Any]) -> dict[str, Any]:
    """English research report page: ruled plan table, borderless key figures, photo, dashboard screenshot, raster chart."""
    items = [
        ("Site A — tool and die, 184 kW", date(2023, 5, 11), 26840000), ("Site B — commercial bakery, 96 kW", date(2023, 8, 2), 15120000),
        ("Site C — plastics molding, 240 kW", date(2023, 10, 19), 33600000), ("Site D — sign fabrication, 48 kW", date(2024, 2, 7), 8450000),
        ("Site E — metal finishing, 150 kW", date(2024, 4, 23), 22950000), ("Site F — printing, 72 kW", date(2024, 6, 12), 11880000),
        ("Site G — brewery, 110 kW", date(2024, 9, 3), 17160000), ("Site H — cabinet shop, 205 kW", date(2024, 11, 14), 29110000),
        ("Site J — auto parts, 320 kW", date(2025, 3, 5), 43200000), ("Site K — food packaging, 132 kW", date(2025, 6, 18), 18216000),
        ("Site L — textile finishing, 88 kW", date(2025, 9, 9), 12584000),
    ]
    rows = [{"word2": [s], "date": [day(d, "iso")], "usd": [money(c, "en-US")]} for s, d, c in items]
    table = plan_table(plan, 0, "t1", "ruled", ["word2", "date", "usd"], rows,
                       header={"word2": ["Site"], "date": ["Commissioned"], "usd": ["Installed cost"]},
                       caption="Table 2. Installed systems in the interview sample", widths=[56, 20, 24])
    key = model.table("t2", "borderless", [["Indicator", "Value"], ["Median simple payback", "7.8 years"], ["Median system size", "132 kW"],
                                           ["Sites with battery storage", "18%"], ["Survey response rate", "64% (n = 47)"]],
                      caption="Key figures", align=["l", "r"], cls="keyfig")
    top = [["Site", "kWh (Feb)", "vs. forecast"], ["Site C — plastics molding", "18,420", "+6.2%"], ["Site H — cabinet shop", "15,980", "+3.9%"],
           ["Site A — tool and die", "14,760", "−1.4%"], ["Site K — food packaging", "12,305", "+0.8%"], ["Site E — metal finishing", "11,870", "−4.7%"]]
    dash = {"brand": "SunLedger", "nav": ["Overview", "Sites", "Alerts", "Reports", "Settings"], "title": "Fleet overview",
            "range": "Feb 1 – Feb 28, 2026", "kpis": [("Fleet generation", "142.6 MWh", "+4.1% vs. forecast"), ("Capacity factor", "11.8%", "+0.6 pt"),
                                                     ("Sites reporting", "45 / 47", "−2 offline")],
            "series_title": "Daily generation (MWh)", "series": [3.9, 4.6, 5.2, 4.1, 3.2, 5.8, 6.1, 5.5, 4.8, 5.9, 6.4, 6.0, 5.1, 4.4],
            "table_title": "Top sites by generation", "rows": top, "height": 500}
    spec = {"title": "Sample generation by month, 2025 (MWh)", "categories": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
            "series": [("Measured", [98, 121, 176, 214, 251, 262, 270, 248, 203, 158, 104, 86]), ("Modeled", [92, 118, 170, 220, 255, 268, 266, 241, 196, 150, 101, 84])],
            "max": 300, "ticks": 3, "tick_format": lambda v: f"{v:.0f}"}
    return {
        "template": "research_report_page", "page_size": "Letter", "languages": ["en-US"],
        "metadata": {"title": "Rooftop Solar Adoption Among Small Manufacturers in the Ohio Valley — Section 3", "author": "Dana Whitcombe; Luis Ferreira-Okoye",
                     "subject": "Results: installed systems, costs and measured generation", "keywords": ["rooftop solar", "manufacturing", "payback", "Ohio Valley"],
                     "lang": "en-US", "created": "2026-03-20T15:30:00Z"},
        "theme": {"accent": "#7a4b00", "body_font": "'Noto Serif'", "heading_font": "'Noto Sans'", "font_size": "9.6pt",
                  "extra_css": "table.keyfig{width:46%;float:right;margin:0 0 .6em 1em} table.keyfig td.num{font-weight:700}"},
        "running_header": "Ohio Valley Manufacturing Energy Study · Working paper 26-03",
        "running_footer": "{page}",
        "blocks": [
            P("Section 3", "kicker"),
            H(1, "Results: what small manufacturers actually installed"),
            photo("f1", ["solar-panels", "office-building", "factory-machinery"], ["energy", "industry"],
                  {"solar-panels": "A ballasted rooftop array at one of the sampled plants.",
                   "office-building": "Many sampled firms lease space in multi-tenant buildings.",
                   "factory-machinery": "Process loads dominate daytime demand at most sites."},
                  "One of the sampled sites.", "left", "40%"),
            P("Of the 47 firms that completed the survey, 11 had commissioned a rooftop system by the end of 2025. Costs "
              "fell steadily over the period: the median installed cost per kilowatt dropped from $1,460 for systems commissioned "
              "in 2023 to $1,380 in 2025, although the largest saving came from simpler permitting rather than cheaper hardware."),
            P("Interviewees repeatedly described the decision as a financing question, not a technical one. As one plant "
              "manager put it, “the roof was never the problem; the bank was.” This echoes the 2019 state study, whose title — "
              "“Eﬃciency Investments and Small-Firm Credit: Why the ﬁnancing gap persists” — is quoted here as printed.¹"),
            key,
            table,
            H(2, "3.2 Measured generation"),
            P("Monthly generation tracked the model within ±5 % for nine of twelve months. The remaining gaps coincide with "
              "snow cover in January and inverter faults at Site E in October. Real-time monitoring is now standard: every "
              "site in the sample reports to a shared dashboard, reproduced below as participants see it."),
            chart("f2", "line", spec, "Figure 4. Measured versus modeled generation, all sites", raster=True, width="88%", size=(600, 240)),
            chart_table("c1", "Month", spec, str),
            screenshot("f3", "dashboard", dash, "Figure 5. Monitoring dashboard, February 2026 (screenshot)", width="92%"),
            model.table("t3", "screenshot", top, caption="Top sites by generation as shown in Figure 5"),
            box("footnote", "¹ Ligature characters are retained exactly as they appear in the 2019 report’s PDF metadata. "
                "Data and interview guide: [ohiovalley-energy.example.org/wp26-03](https://ohiovalley-energy.example.org/wp26-03)."),
        ],
    }


def research_hi(plan: dict[str, Any]) -> dict[str, Any]:
    """Hindi drip-irrigation research page with Indian digit grouping (kinds: word2, usd, date, date)."""
    items = [
        ("पीरपिंपळगाव, जालना — 2.5 एकड़", 148500, date(2024, 11, 4), date(2025, 11, 10)), ("वडगाँव, बीड — 3 एकड़", 172000, date(2024, 11, 18), date(2025, 11, 20)),
        ("मोहोळ, सोलापुर — 4 एकड़", 226400, date(2024, 12, 2), date(2025, 12, 5)), ("औसा, लातूर — 2 एकड़", 121800, date(2024, 12, 16), date(2025, 12, 18)),
        ("तुळजापुर, धाराशिव — 5 एकड़", 279000, date(2025, 1, 8), date(2026, 1, 12)), ("सेलू, परभणी — 1.5 एकड़", 96300, date(2025, 1, 20), date(2026, 1, 22)),
        ("हदगाँव, नांदेड़ — 3.5 एकड़", 198700, date(2025, 2, 3), date(2026, 2, 6)), ("पैठण, छत्रपति संभाजीनगर — 2 एकड़", 118900, date(2025, 2, 17), date(2026, 2, 19)),
        ("चोपड़ा, जलगाँव — 6 एकड़", 334500, date(2025, 3, 3), date(2026, 3, 5)), ("मेहकर, बुलढाणा — 2.5 एकड़", 141200, date(2025, 3, 17), date(2026, 3, 18)),
        ("राहुरी, अहमदनगर — 4.5 एकड़", 251600, date(2025, 3, 31), date(2026, 4, 2)),
    ]
    rows = [{"word2": [s], "usd": [money(c * 100, "hi")], "date": [day(a, "slash_dmy"), day(b, "slash_dmy")]} for s, c, a, b in items]
    table = plan_table(plan, 0, "t1", "ruled", ["word2", "usd", "date", "date"], rows,
                       header={"word2": ["स्थल (गाँव, ज़िला — क्षेत्रफल)"], "usd": ["कुल लागत"], "date": ["स्थापना", "समीक्षा"]},
                       caption="तालिका 2. अध्ययन में शामिल ड्रिप सिंचाई प्रणालियाँ", widths=[44, 20, 18, 18])
    key = model.table("t2", "borderless", [["संकेतक", "मान"], ["पानी की औसत बचत", "38%"], ["उपज में औसत वृद्धि", "21%"],
                                           ["लागत वसूली की औसत अवधि", "2.4 वर्ष"], ["सरकारी अनुदान का हिस्सा", "55%"]],
                      caption="मुख्य निष्कर्ष", align=["l", "r"], cls="keyfig")
    spec = {"title": "प्रति एकड़ पानी का उपयोग (हज़ार लीटर)", "categories": ["कपास", "मक्का", "अनार", "प्याज़"],
            "series": [("ड्रिप से पहले", [520, 410, 610, 380]), ("ड्रिप के बाद", [330, 270, 360, 240])], "max": 700, "ticks": 7,
            "tick_format": lambda v: f"{v:.0f}"}
    return {
        "template": "research_report_page", "page_size": "A4", "languages": ["hi-IN"],
        "metadata": {"title": "मराठवाड़ा में छोटे किसानों द्वारा ड्रिप सिंचाई अपनाने का अध्ययन", "author": "डॉ. अनीता देशपांडे, कृषि अर्थशास्त्र विभाग",
                     "subject": "क्षेत्र अध्ययन के परिणाम: लागत, पानी की बचत और उपज", "keywords": ["ड्रिप सिंचाई", "मराठवाड़ा", "किसान", "अध्ययन"],
                     "lang": "hi-IN", "created": "2026-04-06T05:30:00Z"},
        "theme": {"accent": "#6a3b0f", "font_size": "10pt", "extra_css": "table.keyfig{width:44%;float:left;margin:0 1em .6em 0}"},
        "running_header": "कृषि अर्थशास्त्र विभाग — शोध पत्र 2026/04",
        "running_footer": "पृष्ठ {page} / {pages}",
        "blocks": [
            H(1, "ड्रिप सिंचाई अपनाने के परिणाम"),
            photo("f1", ["farm-field", "aerial-farmland", "tractor"], ["agriculture", "landscape"],
                  {"farm-field": "अध्ययन क्षेत्र का एक खेत।", "aerial-farmland": "मराठवाड़ा के खेतों का हवाई दृश्य।", "tractor": "खेत की तैयारी।"},
                  "अध्ययन क्षेत्र।", "right", "38%"),
            P("इस अध्ययन में मराठवाड़ा क्षेत्र के 11 छोटे किसानों के खेतों पर ड्रिप सिंचाई प्रणाली की लागत, पानी की बचत और उपज पर "
              "उसके प्रभाव का आकलन किया गया। सभी किसानों ने प्रधानमंत्री कृषि सिंचाई योजना के तहत अनुदान लिया था और "
              "प्रणाली लगने के लगभग एक साल बाद उनके खेतों का दोबारा सर्वेक्षण किया गया।"),
            P("औसतन प्रति एकड़ लागत ₹57,000 के आसपास रही, लेकिन बड़े खेतों में यह कम थी। किसानों ने बताया कि सबसे बड़ा फ़ायदा "
              "बिजली के बिल और मज़दूरी में बचत के रूप में मिला, क्योंकि अब रात में खेत में पानी देने की ज़रूरत नहीं पड़ती।"),
            key,
            table,
            H(2, "फ़सलवार पानी का उपयोग"),
            chart("f2", "bar", spec, "चित्र 3. ड्रिप लगाने से पहले और बाद में पानी का उपयोग", raster=False, width="78%"),
            chart_table("c1", "फ़सल", spec, lambda v: f"{v:.0f}"),
            P("पानी की सबसे ज़्यादा बचत अनार के बाग़ों में हुई। प्याज़ में बचत कम रही, क्योंकि कई किसान अब भी रोपाई के समय "
              "पारंपरिक तरीक़े से सिंचाई करते हैं। अगले चरण में हम ₹1,00,000 से कम लागत वाली प्रणालियों के रखरखाव ख़र्च का अध्ययन करेंगे।"),
        ],
    }


def research_en_gb_lo(plan: dict[str, Any]) -> dict[str, Any]:
    """British station-accessibility interim report for LibreOffice (kinds: date, usd, word2) with Greek code-switching."""
    items = [
        (date(2025, 3, 28), 124000000, "Hebden Bridge: lifts to both platforms"), (date(2025, 5, 16), 38650000, "Shipley: raised platform humps"),
        (date(2025, 6, 27), 210500000, "Huddersfield: step-free footbridge"), (date(2025, 8, 8), 9420000, "Mytholmroyd: tactile paving renewal"),
        (date(2025, 9, 19), 56300000, "Brighouse: ramped access to platform 2"), (date(2025, 10, 31), 17880000, "Saltaire: accessible ticket office counter"),
        (date(2025, 12, 12), 143200000, "Dewsbury: lifts and new waiting shelter"), (date(2026, 1, 23), 6150000, "Todmorden: induction loops and signage"),
        (date(2026, 2, 27), 88700000, "Batley: platform extension and ramps"), (date(2026, 3, 20), 12430000, "Mirfield: accessible toilets"),
    ]
    rows = [{"date": [day(d, "iso")], "usd": [money(c, "en-GB")], "word2": [s]} for d, c, s in items]
    table = plan_table(plan, 0, "t1", "ruled", ["date", "usd", "word2"], rows,
                       header={"date": ["Completed"], "usd": ["Outturn cost"], "word2": ["Station and works"]},
                       caption="Table 3. Schemes completed in the evaluation period", widths=[18, 24, 58])
    key = model.table("t2", "borderless", [["Measure", "Before", "After"], ["Step-free stations in sample", "4 of 14", "11 of 14"],
                                           ["Assisted-travel bookings per month", "212", "297"], ["Median boarding time with ramp", "74 s", "41 s"]],
                      caption="Table 4. Headline indicators", align=["l", "r", "r"])
    return {
        "template": "research_report_page", "page_size": "A4", "languages": ["en-GB", "el"],
        "metadata": {"title": "Step-free Access at Regional Stations: Interim Evaluation", "author": "Transport Accessibility Research Unit, University of West Yorkshire",
                     "subject": "Interim findings on costs and outcomes of station accessibility schemes", "keywords": ["accessibility", "rail stations", "evaluation"],
                     "lang": "en-GB", "created": "2026-04-14T09:00:00Z"},
        "theme": {"accent": "#4b2e83", "lo_font": "Noto Serif", "lo_heading_font": "Noto Sans", "lo_size": "10pt", "content_cm": 17.2},
        "running_header": "Interim evaluation — not for citation",
        "running_footer": "Page {page} of {pages}",
        "blocks": [
            H(1, "Step-free access at regional stations: interim evaluation"),
            P("Sarah Pemberton, Γιώργος Αντωνίου (Giorgos Antoniou) and Imran Siddiqui · April 2026", "small"),
            H(2, "4. Costs and early outcomes"),
            photo("f1", ["train-station", "city-bus", "city-street"], ["transport", "civic"],
                  {"train-station": "A regional platform before raised humps were installed.", "city-bus": "Bus–rail interchange outside one of the stations.",
                   "city-street": "Station forecourt approach."},
                  "A station in the evaluation sample.", "right", width_cm=6.2),
            P("Ten schemes were completed between March 2025 and March 2026. Outturn costs varied widely, from £61,500 for "
              "induction loops and signage at Todmorden to more than £2.1 million for the new footbridge at Huddersfield. "
              "The two most expensive schemes account for half of the total spend."),
            P("Early outcomes are encouraging. Assisted-travel bookings at the sample stations rose by 40 % compared with "
              "the same months a year earlier, and ramp boarding times fell sharply where platform humps were installed."),
            table,
            key,
            H(2, "5. Comparison with Greek regional stations"),
            P("For context, Γιώργος Αντωνίου reviewed the programme of the Greek infrastructure manager at Θεσσαλονίκη "
              "(Thessaloniki) and Λάρισα (Larisa), where level boarding was delivered by raising whole platforms rather than "
              "using humps. Unit costs were higher, but passengers no longer need to book assistance in advance.²"),
            box("footnote", "² Interview with ΟΣΕ engineering staff, 12 February 2026; figures converted at €1 = £0.84."),
        ],
    }
