"""Authored wild-v1 documents for the column_pairs and negative families."""

# ruff: noqa: E501
from __future__ import annotations

from datetime import date
from typing import Any

from bench.wild_templates import model
from bench.wild_templates.common import H, L, P, box, chart, chart_table, photo, plan_table, screenshot
from bench.wild_templates.model import day, money

# ---------------------------------------------------------------- column pairs


def plans_zh_tw(plan: dict[str, Any]) -> dict[str, Any]:
    """Traditional Chinese cloud-storage plan comparison; two side-by-side tables and a raster chart."""
    a = [("CY-S1", date(2026, 1, 1), 1200, "1 TB・5 位使用者・基本版"), ("CY-S2", date(2026, 1, 1), 2400, "3 TB・10 位使用者"),
         ("CY-S3", date(2026, 1, 1), 4500, "10 TB・25 位使用者"), ("CY-B1", date(2026, 3, 1), 6800, "20 TB・50 位使用者・稽核紀錄"),
         ("CY-B2", date(2026, 3, 1), 9900, "50 TB・100 位使用者"), ("CY-E1", date(2026, 4, 1), 18000, "容量不限・200 位使用者・專屬客服"),
         ("CY-A1", date(2026, 1, 1), 300, "加購：每 1 TB 額外容量"), ("CY-A2", date(2026, 1, 1), 150, "加購：每位額外使用者"),
         ("CY-A3", date(2026, 3, 1), 2000, "加購：異地備份"), ("CY-A4", date(2026, 4, 1), 3500, "加購：資料保存七年"),
         ("CY-T1", date(2026, 1, 1), 0, "30 天免費試用（限新客戶）")]
    b = [(date(2026, 2, 1), 990, "入門版：500 GB・3 位使用者"), (date(2026, 2, 1), 2200, "標準版：2 TB・10 位使用者"),
         (date(2026, 2, 1), 4800, "進階版：8 TB・25 位使用者"), (date(2026, 2, 1), 7200, "商務版：25 TB・50 位使用者"),
         (date(2026, 5, 1), 11500, "企業版：60 TB・100 位使用者"), (date(2026, 5, 1), 21000, "旗艦版：容量不限・250 位使用者"),
         (date(2026, 2, 1), 280, "加購：每 1 TB 額外容量"), (date(2026, 2, 1), 180, "加購：每位額外使用者"),
         (date(2026, 2, 1), 1500, "加購：異地備份（每日）"), (date(2026, 5, 1), 4000, "加購：電子郵件封存"),
         (date(2026, 2, 1), 0, "14 天免費試用")]
    t1 = plan_table(plan, 0, "t1", "ruled", ["mixed", "date", "usd", "word2"],
                    [{"mixed": [c], "date": [day(d, "cjk")], "usd": [money(p, "zhTW")], "word2": [t]} for c, d, p, t in a],
                    header={"mixed": ["方案代碼"], "date": ["生效日"], "usd": ["月費"], "word2": ["內容"]},
                    caption="表一　雲曜科技", widths=[16, 26, 18, 40], cls="compact")
    t2 = plan_table(plan, 1, "t2", "ruled", ["date", "usd", "word2"],
                    [{"date": [day(d, "cjk")], "usd": [money(p, "zhTW")], "word2": [t]} for d, p, t in b],
                    header={"date": ["生效日"], "usd": ["月費"], "word2": ["方案內容"]},
                    caption="表二　北辰數位", widths=[28, 20, 52], cls="compact")
    spec = {"title": "同級方案月費比較（新臺幣）", "categories": ["約 1 TB", "約 3 TB", "約 10 TB", "約 25 TB", "約 50 TB"],
            "series": [("雲曜科技", [1200, 2400, 4500, 6800, 9900]), ("北辰數位", [990, 2200, 4800, 7200, 11500])],
            "max": 12000, "ticks": 4, "tick_format": lambda v: f"{v:,.0f}"}
    return {
        "template": "plan_comparison_sheet", "page_size": "A4", "languages": ["zh-TW"],
        "metadata": {"title": "企業雲端儲存方案比較（2026年度）", "author": "資訊室　林家豪", "subject": "雲曜科技與北辰數位方案及價格比較",
                     "keywords": ["雲端儲存", "方案比較", "採購"], "lang": "zh-TW", "created": "2026-03-05T06:00:00Z"},
        "theme": {"accent": "#14507a", "font_size": "9.5pt", "extra_css": "table.compact{font-size:.82em}"},
        "running_header": "內部採購評估資料　請勿外流",
        "running_footer": "第 {page} 頁／共 {pages} 頁",
        "blocks": [
            H(1, "企業雲端儲存方案比較（2026年度）"),
            P("製表日期：2026年3月5日　製表人：資訊室 林家豪　用途：年度採購評估", "small muted"),
            P("本公司現行檔案伺服器將於今年底停止原廠支援，資訊室評估改用雲端儲存服務。以下比較兩家通過資安初審的廠商，"
              "價格均為未稅月費，依各廠商2026年公告價目表整理。兩家方案的容量級距不同，比較時請以實際使用者人數為準。"),
            {"kind": "pair", "blocks": [t1, t2]},
            chart("f1", "bar", spec, "圖一　同級方案月費比較", raster=True, width="80%", size=(560, 240)),
            chart_table("c1", "容量級距", spec, lambda v: f"{v:,.0f}"),
            H(2, "初步建議"),
            L(["目前全公司約 46 位使用者、檔案總量約 7.2 TB，兩家的「10 TB／25 人」級距較接近需求。",
               "雲曜科技的異地備份為月費制，北辰數位則為每日備份，需確認是否符合稽核要求。",
               "建議於4月底前申請兩家的免費試用，並由財務部與法務室共同檢視合約條款。"], ordered=True),
        ],
    }


def plans_en(plan: dict[str, Any]) -> dict[str, Any]:
    """English coworking rate-card comparison with emoji, two side-by-side tables and a spreadsheet screenshot."""
    a = [(date(2025, 1, 1), "Day pass", 3500), (date(2025, 1, 1), "10-day flex bundle", 29000), (date(2025, 1, 1), "Hot desk, part-time", 18900),
         (date(2025, 1, 1), "Hot desk, unlimited", 31900), (date(2025, 1, 1), "Dedicated desk", 44900), (date(2025, 1, 1), "Private office, 2 people", 115000),
         (date(2025, 1, 1), "Private office, 4 people", 208000), (date(2025, 4, 1), "Meeting room, per hour", 4000),
         (date(2025, 4, 1), "Mail and package handling", 4900), (date(2025, 4, 1), "Locker", 2500), (date(2025, 9, 1), "Bike storage", 1500)]
    b = [(date(2026, 7, 1), 3900, "Day pass"), (date(2026, 7, 1), 20900, "Hot desk, part-time"), (date(2026, 7, 1), 33900, "Hot desk, unlimited"),
         (date(2026, 7, 1), 47900, "Dedicated desk"), (date(2026, 7, 1), 119000, "Private office, 2 people"),
         (date(2026, 7, 1), 215000, "Private office, 4 people"), (date(2026, 7, 1), 4500, "Meeting room, per hour"),
         (date(2026, 7, 1), 0, "Bike storage (now included)")]
    t1 = plan_table(plan, 0, "t1", "ruled", ["date", "word2", "usd"],
                    [{"date": [day(d, "en_short")], "word2": [p], "usd": [money(c, "en-US")]} for d, p, c in a],
                    header={"date": ["Effective"], "word2": ["Plan"], "usd": ["Monthly"]}, caption="Current rate card", widths=[30, 46, 24])
    t2 = plan_table(plan, 1, "t2", "ruled", ["date", "usd", "word2"],
                    [{"date": [day(d, "en_short")], "usd": [money(c, "en-US")], "word2": [p]} for d, c, p in b],
                    header={"date": ["Effective"], "usd": ["Monthly"], "word2": ["Plan"]}, caption="Proposed rate card", widths=[30, 24, 46])
    survey = [["Plan", "Respondents", "Satisfied", "Would renew"], ["Day pass", "38", "71%", "—"], ["Hot desk, part-time", "54", "78%", "81%"],
              ["Hot desk, unlimited", "61", "84%", "88%"], ["Dedicated desk", "29", "90%", "93%"], ["Private office", "17", "82%", "76%"]]
    sheet = {"title": "Member survey Q1 2026 — export", "menu": ["File", "Home", "Insert", "Data", "Review", "View"],
             "cell": "C4", "formula": '=COUNTIFS(raw!D:D,"Hot desk, unlimited",raw!G:G,">=4")/B4', "tabs": ["summary", "raw", "comments"],
             "rows": survey, "numeric": [False, True, True, True], "selected_row": 4, "width": 600}
    return {
        "template": "plan_comparison_sheet", "page_size": "Letter", "languages": ["en-US"],
        "metadata": {"title": "Foundry Commons membership rates: current vs. proposed", "author": "Jordan Ellis, Community Manager",
                     "subject": "Board pre-read on the July 2026 rate change", "keywords": ["coworking", "membership", "pricing", "board"],
                     "lang": "en-US", "created": "2026-04-22T17:00:00Z"},
        "theme": {"accent": "#c2410c", "body_font": "'Noto Sans'", "font_size": "9.5pt"},
        "running_header": "Foundry Commons · Board pre-read · April 2026",
        "running_footer": "Draft for discussion — page {page} of {pages}",
        "blocks": [
            H(1, "Membership rates: current vs. proposed"),
            P("Prepared for the April 28 board meeting. The proposal raises most plans by 4–7% from July 1, folds bike storage "
              "into every membership, and retires the 10-day flex bundle, which only nine members used last quarter.", "lead"),
            {"kind": "pair", "blocks": [t1, t2]},
            H(2, "Why now"),
            P("Our lease renewal adds $2,350 a month from June, and utilities rose 11% year over year. Even with the increase, "
              "the unlimited hot desk stays below the downtown median of $365 reported in the regional coworking survey."),
            box("callout", "☕ better coffee · 🚲 more bike racks · 👩🏽\u200d💻 quiet focus booths · 🧑\u200d🤝\u200d🧑 more member events · 📦 later package pickup",
                title="Top five member requests"),
            H(2, "What members told us"),
            P("The Q1 survey had 199 responses. The summary tab is pasted below as it appears in the shared workbook; the "
              "raw responses stay in the members-only drive."),
            screenshot("f1", "spreadsheet", sheet, "Q1 member survey, summary tab (screenshot)", width="78%"),
            model.table("t3", "screenshot", survey, caption="Survey summary as shown in the screenshot"),
            P("Full survey comments: [foundrycommons.example/board/q1-survey](https://foundrycommons.example/board/q1-survey).", "small"),
        ],
    }


def catering_th(plan: dict[str, Any]) -> dict[str, Any]:
    """Thai catering-package comparison for LibreOffice; two side-by-side tables, ZWSP word hints and a photo."""
    zw = "\u200b"
    a = [("ค็อกเทลเบรก", 35000, "ขนมว่าง 4 อย่าง กาแฟและชา", "30 มิ.ย. 2569"), ("บุฟเฟต์อาหารไทย", 65000, "อาหารคาว 6 อย่าง ของหวาน 2 อย่าง", "31 ธ.ค. 2569"),
         ("บุฟเฟต์นานาชาติ", 89000, "สลัดบาร์ อาหารคาว 8 อย่าง ผลไม้", "31 ธ.ค. 2569"), ("โต๊ะจีน 9 อย่าง", 55000, "ราคาต่อท่าน สั่งขั้นต่ำ 10 ท่าน", "31 ธ.ค. 2569"),
         ("ข้าวกล่องประชุม", 12000, "ข้าวพร้อมกับข้าว 2 อย่าง น้ำดื่ม", "30 มิ.ย. 2569"), ("อาหารเช้าคอนติเนนตัล", 28000, "ขนมปัง ไข่ ผลไม้ น้ำผลไม้", "30 มิ.ย. 2569"),
         ("แพ็กเกจงานแต่งงาน", 120000, "บุฟเฟต์พรีเมียม พร้อมซุ้มอาหาร 3 ซุ้ม", "31 ธ.ค. 2569")]
    b = [(150000, "1 ม.ค. 2569", "ซุ้มกาแฟสด (ต่อ 50 ท่าน)"), (250000, "1 ม.ค. 2569", "ซุ้มก๋วยเตี๋ยวเรือ"), (180000, "1 ม.ค. 2569", "ซุ้มไอศกรีมกะทิ"),
         (300000, "1 มี.ค. 2569", "ซุ้มข้าวเหนียวมะม่วง"), (80000, "1 ม.ค. 2569", "ผ้าปูโต๊ะและผ้าคลุมเก้าอี้ (10 ชุด)"),
         (450000, "1 ม.ค. 2569", "ดอกไม้ประดับโต๊ะอาหาร"), (35000, "1 ม.ค. 2569", "พนักงานเสิร์ฟเพิ่ม (ต่อชั่วโมง)"),
         (600000, "1 เม.ย. 2569", "ระบบเสียงและไมโครโฟน"), (200000, "1 เม.ย. 2569", "ค่าขนส่งนอกเขตกรุงเทพฯ"),
         (0, "1 ม.ค. 2569", "ชิมอาหารก่อนงาน (2 ท่าน)"), (120000, "1 มี.ค. 2569", "น้ำผลไม้ปั่น (30 แก้ว)")]
    t1 = plan_table(plan, 0, "t1", "ruled", ["word2", "usd", "word2", "date"],
                    [{"word2": [n, d], "usd": [money(p, "th")], "date": [until]} for n, p, d, until in a],
                    header={"word2": ["แพ็กเกจ", "รายละเอียด"], "usd": ["ราคาต่อท่าน"], "date": ["ราคานี้ถึง"]},
                    caption="ตารางที่ 1 แพ็กเกจหลัก", widths=[27, 20, 33, 20], width_cm=8.2)
    t2 = plan_table(plan, 1, "t2", "ruled", ["usd", "date", "word2"],
                    [{"usd": [money(p, "th")], "date": [d], "word2": [n]} for p, d, n in b],
                    header={"usd": ["ราคา"], "date": ["เริ่มให้บริการ"], "word2": ["รายการเสริม"]},
                    caption="ตารางที่ 2 รายการเสริม", widths=[26, 26, 48], width_cm=8.2)
    intro = zw.join(["ครัวบ้านสวน", "ให้", "บริการ", "จัดเลี้ยง", "นอกสถานที่", "มา", "กว่า", "สิบห้า", "ปี", " ", "เรา", "ใช้", "วัตถุดิบ",
                     "สด", "จาก", "ตลาด", "ท้องถิ่น", "ทุก", "เช้า", " ", "และ", "ปรุง", "ใหม่", "ก่อน", "งาน", "ทุก", "ครั้ง"])
    return {
        "template": "plan_comparison_sheet", "page_size": "A4", "languages": ["th-TH"],
        "metadata": {"title": "เปรียบเทียบแพ็กเกจจัดเลี้ยง ปี 2569", "author": "ครัวบ้านสวน แคเทอริ่ง", "subject": "ราคาแพ็กเกจหลักและรายการเสริมสำหรับลูกค้าองค์กร",
                     "keywords": ["จัดเลี้ยง", "แพ็กเกจ", "ราคา"], "lang": "th-TH", "created": "2026-01-08T04:00:00Z"},
        "theme": {"accent": "#7c2d12", "lo_font": "Noto Sans", "lo_heading_font": "Noto Sans", "lo_size": "10pt", "content_cm": 17.2},
        "running_header": "ครัวบ้านสวน แคเทอริ่ง · โทร 02-123-4567",
        "running_footer": "หน้า {page} จาก {pages}",
        "blocks": [
            H(1, "แพ็กเกจจัดเลี้ยงสำหรับองค์กร ปี 2569"),
            photo("f1", ["catering-buffet", "salad-bowl", "bread-bakery"], ["catering", "food"],
                  {"catering-buffet": "ตัวอย่างการจัดไลน์บุฟเฟต์", "salad-bowl": "สลัดบาร์ในแพ็กเกจบุฟเฟต์นานาชาติ", "bread-bakery": "ขนมปังอบสดสำหรับอาหารเช้า"},
                  "ตัวอย่างอาหารของเรา", "right", width_cm=6.0),
            P(intro),
            P("ราคาทั้งหมดรวมภาษีมูลค่าเพิ่มแล้ว สั่งขั้นต่ำ 30 ท่านต่อแพ็กเกจ ยกเว้นโต๊ะจีนและข้าวกล่อง กรุณาแจ้งจำนวนผู้ร่วมงานที่แน่นอนล่วงหน้าอย่างน้อย 7 วัน"),
            H(2, "ราคาแพ็กเกจและรายการเสริม"),
            {"kind": "pair", "blocks": [t1, t2]},
            H(2, "เงื่อนไขการชำระเงิน"),
            L(["มัดจำ 50% เมื่อยืนยันการจอง", "ชำระส่วนที่เหลือภายใน 3 วันหลังจบงาน", "ยกเลิกก่อนงาน 14 วัน คืนมัดจำเต็มจำนวน"]),
        ],
    }


# ---------------------------------------------------------------- negative (no data tables)


def memo_ar(_plan: dict[str, Any]) -> dict[str, Any]:
    """Arabic RTL policy memo with bidi controls, Arabic-Indic digits, tatweel and an RTL email screenshot."""
    lrm = "\u200e"
    mail = {"folders": ["الوارد", "المرسل", "المسودات", "الأرشيف"], "subject": "استفسار بخصوص بدل الإنترنت",
            "from": "ليلى منصور <l.mansour@nakheel-eng.example>", "to": "إلى: الموارد البشرية", "date": "الأحد ٨ مارس ٢٠٢٦، ١٠:١٥ ص",
            "body": ["مرحبًا، هل يشمل بدل الإنترنت الموظفين المتعاقدين بدوام جزئي؟", "وهل يُصرف البدل عن شهر مارس كاملًا أم من تاريخ السريان؟",
                     "شكرًا لكم، ليلى"], "dir": "rtl", "lang": "ar", "height": 300}
    return {
        "template": "policy_memo", "page_size": "A4", "dir": "rtl", "languages": ["ar", "en"],
        "metadata": {"title": "مذكرة: تحديث سياسة العمل عن بُعد", "author": "إدارة الموارد البشرية – شركة النخيل للاستشارات الهندسية",
                     "subject": "الضوابط الجديدة للعمل عن بُعد اعتبارًا من أبريل ٢٠٢٦", "keywords": ["سياسة", "العمل عن بعد", "الموارد البشرية"],
                     "lang": "ar", "created": "2026-03-14T07:00:00Z"},
        "theme": {"accent": "#0b5d4b", "font_size": "10.5pt"},
        "running_header": "شركة النخيل للاستشارات الهندسية – مذكرة داخلية",
        "running_footer": "صفحة {page} من {pages}",
        "blocks": [
            P("مـذكـرة داخـلـيـة", "kicker"),
            H(1, "تحديث سياسة العمل عن بُعد"),
            {"kind": "fields", "items": [("إلى", "جميع الموظفين"), ("من", "إدارة الموارد البشرية"), ("التاريخ", "١٤ مارس ٢٠٢٦"),
                                         ("المرجع", f"{lrm}HR-POL-2026-03{lrm}")]},
            P("بعد مراجعة نتائج التجربة التي استمرت ستة أشهر، قررت الإدارة اعتماد نظام العمل الهجين بشكل دائم اعتبارًا من "
              "١ أبريل ٢٠٢٦. يهدف هذا التحديث إلى توضيح الأيام المسموح بها، ومتطلبات الأمن المعلوماتي، وآلية صرف بدل الإنترنت."),
            H(2, "أولًا: أيام العمل عن بُعد"),
            L(["يحق لكل موظف العمل عن بُعد يومين في الأسبوع بحد أقصى، بعد موافقة مديره المباشر.",
               "يُشترط الحضور إلى المكتب يوم الثلاثاء لجميع أعضاء الفرق الهندسية.",
               f"تُسجَّل أيام العمل عن بُعد في نظام {lrm}PeopleDesk{lrm} قبل نهاية الأسبوع السابق."], ordered=True),
            H(2, "ثانيًا: الأمن المعلوماتي"),
            P(f"يجب الاتصال بشبكة الشركة عبر {lrm}VPN{lrm} فقط، ويُمنع حفظ ملفات المشاريع على الأجهزة الشخصية. سيتم تفعيل "
              "المصادقة الثنائية لجميع الحسابات قبل ٣١ مارس."),
            H(2, "ثالثًا: بدل الإنترنت"),
            P("يُصرف بدل شهري قدره ١٥٠ درهمًا لكل موظف يعمل عن بُعد يومًا واحدًا على الأقل أسبوعيًا، أي ما يعادل ١٬٨٠٠ درهم سنويًا. "
              "وقد وصلتنا عدة استفسارات حول هذا البند، ومنها الرسالة التالية:"),
            screenshot("f1", "email", mail, "نموذج من الاستفسارات الواردة إلى الموارد البشرية", width="84%"),
            P("للاستفسار، يُرجى التواصل مع إدارة الموارد البشرية على الرقم الداخلي ٢٢٠٤ أو عبر البريد hr@nakheel-eng.example.", "small"),
        ],
    }


def newsletter_en(_plan: dict[str, Any]) -> dict[str, Any]:
    """Two-column nonprofit newsletter with photos, sidebar, chat screenshot, emoji and links; no data tables."""
    conversation = {"channel": "# volunteers", "topic": "Riverside Community Garden Trust · Saturday crew",
                    "messages": [("Marisol Vega", "8:02 AM", "Compost delivery arrives at 9 — can two people help spread it on beds 4–9? 🌱"),
                                 ("Tom Okonkwo", "8:05 AM", "On my way, bringing the big wheelbarrow 👍"),
                                 ("Aiko Tanaka", "8:11 AM", "I'll start the seedlings in the greenhouse. Who has the key?"),
                                 ("Marisol Vega", "8:12 AM", "Key is in the lockbox, code is the same as last month.")], "height": 330}
    return {
        "template": "nonprofit_newsletter", "page_size": "Letter", "languages": ["en-US"],
        "metadata": {"title": "The Allotment — Spring 2026", "author": "Riverside Community Garden Trust",
                     "subject": "Quarterly newsletter for members and volunteers", "keywords": ["newsletter", "community garden", "volunteers", "spring"],
                     "lang": "en-US", "created": "2026-03-21T13:00:00Z"},
        "theme": {"accent": "#2f6b2f", "body_font": "'Noto Serif'", "heading_font": "'Noto Sans'", "font_size": "9.6pt"},
        "running_footer": "The Allotment · Spring 2026 · {page}",
        "blocks": [
            {"kind": "group", "cls": "masthead", "blocks": [H(1, "The Allotment"),
                                                             P("Riverside Community Garden Trust · Spring 2026 · Issue 37", "small")]},
            {"kind": "columns", "count": 2, "blocks": [
                H(2, "Beds are open for the season 🌷"),
                photo("f1", ["garden-flowers", "potted-plants", "park-path"], ["garden", "plants"],
                      {"garden-flowers": "The pollinator border in late April last year.", "potted-plants": "Seedlings waiting in the greenhouse.",
                       "park-path": "The new accessible path along the river side."},
                      "Spring at the garden.", "right", "48%"),
                P("After a wet winter, the soil finally dried out enough for us to open all 64 raised beds on March 14. Thank "
                  "you to everyone who turned up for the clean-up weekend — 41 volunteers moved four tonnes of wood chip and "
                  "rebuilt the two collapsed beds by the shed."),
                P("Returning plot holders keep their beds automatically. Twelve beds were offered to people on the waiting "
                  "list, and three are reserved for the Lincoln Elementary garden club. If you can no longer manage your bed, "
                  "please tell us by April 30 so someone else can use it this year."),
                H(2, "Meet our new grower-in-residence"),
                P("We’re delighted to welcome Aiko Tanaka 👩🏻\u200d🌾, who joins us for the season from the city’s urban agriculture "
                  "fellowship. Aiko will run Saturday workshops on seed saving and no-dig beds, and she’s already reorganized "
                  "the greenhouse shelving (it has never looked better)."),
                box("sidebar", "April 11 — seed swap, 10:00–12:00 · April 25 — compost workshop · May 9 — plant sale 🌿 · "
                    "May 23 — pizza night at the cob oven 🍕", title="Dates for your diary", cls="wide"),
                H(2, "From the volunteer chat"),
                P("Most Saturday coordination now happens in our group chat. Here’s a typical morning:"),
                screenshot("f2", "chat", conversation, "Saturday morning in the volunteer channel.", width="100%"),
                H(2, "Harvest share"),
                photo("f3", ["salad-bowl", "bread-bakery", "farm-field"], ["food", "agriculture"],
                      {"salad-bowl": "Salad greens from the harvest share table.", "bread-bakery": "Loaves baked in the cob oven.",
                       "farm-field": "Our partner farm outside town."},
                      "From the harvest share table.", "left", "46%"),
                P("Last year members donated 1,180 lb of produce to the Eastside Food Pantry. This season we’re adding a "
                  "weekly share shelf by the gate: take what you need, leave what you can. Volunteers 🧑🏾\u200d🍳 will cook a community "
                  "lunch from the surplus on the first Sunday of each month."),
                P("Questions, photos or stories for the next issue? Write to [news@riversidegarden.example.org](mailto:news@riversidegarden.example.org) "
                  "or visit [riversidegarden.example.org](https://riversidegarden.example.org)."),
            ]},
        ],
    }


def intake_he(_plan: dict[str, Any]) -> dict[str, Any]:
    """Hebrew RTL dental-clinic intake form for LibreOffice; labeled fields and checklists, no data tables."""
    rlm = "\u200f"
    return {
        "template": "intake_form", "page_size": "A4", "dir": "rtl", "languages": ["he-IL"],
        "metadata": {"title": "טופס קליטת מטופל חדש", "author": 'מרפאת השיניים "חיוך בכרמל"', "subject": "פרטים אישיים, היסטוריה רפואית והסכמה לטיפול",
                     "keywords": ["טופס קליטה", "מרפאת שיניים", "הסכמה"], "lang": "he-IL", "created": "2026-01-19T08:00:00Z"},
        "theme": {"accent": "#155e75", "lo_font": "Noto Sans", "lo_heading_font": "Noto Sans", "lo_size": "10pt", "content_cm": 17.2},
        "running_header": "מרפאת השיניים \"חיוך בכרמל\" · רח' מוריה 112, חיפה",
        "running_footer": "עמוד {page} מתוך {pages}",
        "blocks": [
            H(1, "טופס קליטת מטופל חדש"),
            P('נא למלא את הטופס לפני הביקור הראשון. הפרטים נשמרים בתיק הרפואי בהתאם לחוק זכויות החולה, התשנ"ו–1996.'),
            H(2, "פרטים אישיים"),
            {"kind": "fields", "items": [("שם מלא", "יעל ברגמן"), ("תעודת זהות", "034567891"), ("תאריך לידה", "07.11.1988"),
                                         ("טלפון נייד", f"{rlm}052-7364190"), ("כתובת", "רח' הנביאים 18, חיפה"), ("קופת חולים", "מכבי"),
                                         ("איש קשר לחירום", "דניאל ברגמן, 054-2210987"), ("תאריך מילוי", "19.01.2026")]},
            H(2, "היסטוריה רפואית"),
            P("סמנו את כל המצבים הרלוונטיים:"),
            L(["☐ סוכרת", "☐ לחץ דם גבוה", "☒ אסתמה", "☐ מחלת לב", "☐ הריון", "☒ רגישות לפניצילין"]),
            P("תרופות קבועות: משאף ונטולין לפי הצורך."),
            H(2, "הסכמה ותשלום"),
            P("ידוע לי שבדיקה ראשונה כוללת צילום פנורמי ועלותה ₪180. טיפולים נוספים יבוצעו רק לאחר הצגת תוכנית טיפול "
              "והצעת מחיר. ביטול תור בהתראה של פחות מ־24 שעות יחויב בדמי ביטול של ₪100."),
            P("אני מאשר/ת כי הפרטים שמסרתי נכונים ומלאים."),
            {"kind": "fields", "items": [("חתימה", "י. ברגמן"), ("תאריך", "19.01.2026")]},
        ],
    }
