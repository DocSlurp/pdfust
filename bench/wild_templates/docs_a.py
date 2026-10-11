"""Authored wild-v1 documents for the ruled, borderless and wrapped families."""

# ruff: noqa: E501
from __future__ import annotations

from datetime import date
from typing import Any

from bench.wild_templates.common import H, L, P, box, chart, chart_table, group, nfd, photo, plan_table, screenshot
from bench.wild_templates.model import day, money, number

# ---------------------------------------------------------------- ruled


def invoice_en(plan: dict[str, Any]) -> dict[str, Any]:
    """Engineering services invoice to a Japanese client (kinds: date, usd, word2, word2, mixed)."""
    rates = {"Senior engineer": 18500, "Engineer": 14500, "Technician": 9500}
    items = [
        (date(2026, 3, 2), "Senior engineer", "fixture design review, rev. C", "WP-2 Fixture redesign", 6.5),
        (date(2026, 3, 3), "Engineer", "FEA of clamp arm under 4 kN load", "WP-2 Fixture redesign", 9.0),
        (date(2026, 3, 5), "Engineer", "tolerance stack-up, datum scheme B", "WP-2 Fixture redesign", 5.5),
        (date(2026, 3, 9), "Technician", "prototype assembly and fit check", "WP-3 Prototype build", 12.0),
        (date(2026, 3, 10), "Technician", "CMM inspection of 24 features", "WP-3 Prototype build", 7.5),
        (date(2026, 3, 12), "Senior engineer", "design review call with Kitamura team", "WP-1 Project management", 2.0),
        (date(2026, 3, 16), "Travel", "PDX–HND economy airfare, billed at cost", "WP-4 On-site support", None),
        (date(2026, 3, 17), "Senior engineer", "on-site commissioning, Ōta plant", "WP-4 On-site support", 8.0),
        (date(2026, 3, 18), "Engineer", "operator training and handover notes", "WP-4 On-site support", 6.0),
        (date(2026, 3, 24), "Engineer", "final report and drawing package", "WP-1 Project management", 4.5),
    ]
    rows, amounts, hours = [], [], 0.0
    for when, role, task, package, spent in items:
        cents = 148620 if spent is None else round(rates[role] * spent)
        amounts.append(cents)
        hours += spent or 0
        rows.append({"date": [day(when, "us")], "usd": [money(cents, "en-US")], "word2": [f"{role} — {task}", package],
                     "mixed": ["flat" if spent is None else f"{spent:.1f}"]})
    subtotal = sum(amounts)
    table = plan_table(plan, 0, "t1", "ruled", ["date", "usd", "word2", "word2", "mixed"], rows,
                       header={"date": ["Date"], "usd": ["Amount"], "word2": ["Description", "Work package"], "mixed": ["Hours"]},
                       total={"date": [""], "usd": [money(subtotal, "en-US")], "word2": ["Total", ""], "mixed": [f"{hours:.1f}"]},
                       numeric=("usd", "mixed"), caption="Services rendered, March 2026", widths=[12, 14, 38, 24, 12])
    return {
        "template": "vendor_invoice", "page_size": "Letter", "languages": ["en-US", "ja"],
        "metadata": {"title": "Invoice INV-2026-0418 — Kitamura Precision Components", "author": "Halvorsen & Pike Engineering LLC",
                     "subject": "Engineering services, fixture redesign and commissioning, March 2026",
                     "keywords": ["invoice", "engineering services", "fixture redesign", "Kitamura"], "lang": "en-US",
                     "created": "2026-04-03T16:20:00Z"},
        "theme": {"accent": "#1f4e5f", "body_font": "'Noto Sans'", "font_size": "9pt", "margins": "14mm 15mm 16mm 15mm"},
        "running_footer": "Halvorsen & Pike Engineering LLC · INV-2026-0418 · Page {page} of {pages}",
        "blocks": [
            group([P("Halvorsen & Pike Engineering LLC", "brand"),
                   P("2210 NW Raleigh St, Suite 300\nPortland, OR 97210, USA", "small right")], "letterhead"),
            P(" billing@halvorsenpike.example    +1 503-555-0142    halvorsenpike.example", "small icons"),
            H(1, "Invoice INV-2026-0418"),
            group([P("**Bill to**\nKitamura Precision Components K.K.\n北村精密部品株式会社\n〒144-0052 東京都大田区蒲田5丁目12-8\nAttn: Kenji Kitamura (北村 健二)", "meta"),
                   P("**Invoice date:** 04/03/2026\n**Due date:** 05/03/2026\n**Purchase order:** KPC-PO-26-0091\n**Project:** Clamp fixture redesign, line 3", "meta")], "split"),
            H(2, "Services rendered"),
            P("Work was performed under the engineering services agreement dated January 12, 2026. Hours are billed in "
              "half-hour increments at the rates below; travel is passed through at cost without markup."),
            table,
            P(f"**Subtotal:** {money(subtotal, 'en-US')}\n**Sales tax (export of services):** $0.00\n**Total due:** {money(subtotal, 'en-US')}", "right"),
            box("callout", "Senior engineer $185.00/h · engineer $145.00/h · technician $95.00/h. Travel and freight are billed at cost.",
                title="Rates"),
            H(2, "Payment details"),
            P("Please pay by international wire within 30 days and quote “INV-2026-0418” in the payment reference. "
              "Bank: First Columbia Bank, Portland — SWIFT FCBKUS6P — account 4471 0093 2208. Questions about this invoice "
              "can go to Maren Halvorsen at [billing@halvorsenpike.example](mailto:billing@halvorsenpike.example)."),
            P("Thank you for a smooth commissioning week in Ōta. The signed acceptance protocol (AP-0317) and the as-built "
              "drawings were sent separately through your supplier portal.", "small"),
        ],
    }


def quarterly_de(plan: dict[str, Any]) -> dict[str, Any]:
    """German quarterly financial summary (kinds: date, word2, mixed, date, usd) with a vector chart."""
    items = [
        (date(2026, 1, 8), "Abschlagszahlung Wohnanlage Lindenhof", "KST 410", date(2026, 1, 10), 4850000),
        (date(2026, 1, 15), "Materialeinkauf Wärmepumpen", "KST 220", date(2026, 1, 19), -2384017),
        (date(2026, 1, 30), "Löhne und Gehälter Januar", "KST 100", date(2026, 1, 30), -6121240),
        (date(2026, 2, 6), "Schlussrechnung Kita „Sonnenblume“", "KST 410", date(2026, 2, 12), 3697580),
        (date(2026, 2, 13), "Leasingrate Servicefahrzeuge", "KST 300", date(2026, 2, 15), -431800),
        (date(2026, 2, 27), "Löhne und Gehälter Februar", "KST 100", date(2026, 2, 27), -6088415),
        (date(2026, 3, 4), "Wartungsverträge Gewerbekunden", "KST 430", date(2026, 3, 6), 2941000),
        (date(2026, 3, 11), "Fördermittel BAFA (Zuschuss)²", "KST 900", date(2026, 3, 20), 1200000),
        (date(2026, 3, 18), "Instandhaltung Werkstatt", "KST 300", date(2026, 3, 18), -276533),
        (date(2026, 3, 31), "Löhne und Gehälter März", "KST 100", date(2026, 3, 31), -6102090),
    ]
    rows = [{"date": [day(a, "dotted"), day(b, "dotted")], "word2": [text], "mixed": [center], "usd": [money(cents, "de")]}
            for a, text, center, b, cents in items]
    net = sum(item[4] for item in items)
    table = plan_table(plan, 0, "t1", "ruled", ["date", "word2", "mixed", "date", "usd"], rows,
                       header={"date": ["Buchungsdatum", "Wertstellung"], "word2": ["Vorgang"], "mixed": ["Kostenstelle"], "usd": ["Betrag"]},
                       total={"date": ["", ""], "word2": ["Saldo der Einzelposten"], "mixed": [""], "usd": [money(net, "de")]},
                       caption="Tabelle 2: Wesentliche Geschäftsvorfälle im ersten Quartal¹", widths=[15, 36, 14, 15, 20])
    spec = {"title": "Umsatz je Monat (Tsd. €)", "categories": ["Januar", "Februar", "März"],
            "series": [("Ist", [142.3, 151.8, 168.4]), ("Plan", [145.0, 150.0, 160.0])], "max": 200, "ticks": 4,
            "tick_format": lambda v: number(v, "de", 0)}
    return {
        "template": "quarterly_financial_summary", "page_size": "A4", "languages": ["de-DE"],
        "metadata": {"title": "Quartalsbericht Q1/2026 – Brenner Haustechnik GmbH", "author": "Katrin Weißenborn, Kaufmännische Leitung",
                     "subject": "Finanzielle Zusammenfassung des ersten Quartals 2026",
                     "keywords": ["Quartalsbericht", "Q1 2026", "Liquidität", "Umsatz"], "lang": "de-DE", "created": "2026-04-09T08:15:00Z"},
        "theme": {"accent": "#8a2b2b", "body_font": "'Noto Serif'", "heading_font": "'Noto Sans'", "font_size": "9.8pt"},
        "running_header": "Brenner Haustechnik GmbH · Quartalsbericht Q1/2026 · vertraulich",
        "running_footer": "Seite {page} von {pages}",
        "blocks": [
            H(1, "Quartalsbericht Q1/2026"),
            P("Brenner Haustechnik GmbH · Gewerbepark Süd 7 · 93055 Regensburg · Stand: 09.04.2026", "small muted"),
            H(2, "1. Zusammenfassung"),
            P("Das erste Quartal verlief besser als geplant. Der Umsatz lag mit 462,5 Tsd. € rund 1,6 % über dem Plan, "
              "vor allem dank der vorgezogenen Schlussrechnung für die Kita „Sonnenblume“ und einer starken Nachfrage nach "
              "Wärmepumpen im Bestandsgeschäft. Die Personalkosten blieben stabil; die Materialpreise für Kupferrohr sind "
              "gegenüber dem Vorquartal um 4,1 % gestiegen."),
            chart("f1", "bar", spec, "Abbildung 1: Monatlicher Umsatz im Vergleich zum Plan", raster=False, width="78%"),
            chart_table("c1", "Monat", spec, lambda v: number(v, "de", 1)),
            H(2, "2. Geschäftsvorfälle und Liquidität"),
            P("Die folgende Übersicht enthält alle Einzelposten über 2.500 €. Negative Beträge sind Auszahlungen. Die "
              "Instand\u00adhaltungs\u00adrück\u00adstellungen für die Werkstatt wurden im März teilweise in Anspruch genommen."),
            table,
            P("Der Kassenbestand zum 31.03.2026 beträgt 218.430,12 €. Die Kontokorrentlinie über 150.000 € wurde im gesamten "
              "Quartal nicht beansprucht. Für April erwarten wir Zahlungseingänge von rund 95.000 € aus laufenden Abschlägen."),
            H(2, "3. Ausblick"),
            L(["Start des Großprojekts „Quartier am Weinweg“ (Auftragswert ca. 1,2 Mio. €) im Mai",
               "Einstellung von zwei Anlagenmechanikern zum 01.06.2026",
               "Prüfung eines zweiten Lagerstandorts in Straubing bis Ende Q2"]),
            box("footnote", "¹ Vorläufige, ungeprüfte Zahlen; Rundungsdifferenzen sind möglich."),
            box("footnote", "² Zuschuss aus der „Bundesförderung für effiziente Gebäude“, Bescheid vom 02.12.2025."),
        ],
    }


def facture_fr(plan: dict[str, Any]) -> dict[str, Any]:
    """French furniture-workshop invoice for LibreOffice (kinds: mixed, word2, usd, usd, date, date)."""
    nb = " "
    items = [
        (12, "Chaise bistrot en chêne massif", 14800, date(2026, 2, 5), date(2026, 3, 2)),
        (4, "Table ronde Ø 90 cm, plateau noyer", 41250, date(2026, 2, 5), date(2026, 3, 2)),
        (2, f"Banquette d’angle sur mesure, tissu «{nb}lin naturel{nb}»", 138000, date(2026, 2, 5), date(2026, 3, 4)),
        (6, "Tabouret de bar, hauteur 75 cm", 12990, date(2026, 2, 9), date(2026, 3, 2)),
        (1, "Comptoir d’accueil, façade cannelée", 294000, date(2026, 2, 9), date(2026, 3, 5)),
        (8, "Applique murale en laiton brossé", 8640, date(2026, 2, 9), date(2026, 3, 5)),
        (3, "Étagère murale en chêne, 120 cm", 16400, date(2026, 2, 16), date(2026, 3, 5)),
        (10, "Patins feutre de protection (lot de 4)", 690, date(2026, 2, 16), date(2026, 3, 2)),
        (1, "Vernis mat anti-taches, application en atelier", 27500, date(2026, 2, 16), date(2026, 3, 2)),
        (1, "Livraison et installation sur site", 45000, date(2026, 2, 5), date(2026, 3, 6)),
    ]
    rows, total = [], 0
    for qty, text, unit, ordered, delivered in items:
        total += qty * unit
        rows.append({"mixed": [str(qty)], "word2": [text], "usd": [money(unit, "fr"), money(qty * unit, "fr")],
                     "date": [day(ordered, "slash_dmy"), day(delivered, "slash_dmy")]})
    vat = round(total * 0.2)
    table = plan_table(plan, 0, "t1", "ruled", ["mixed", "word2", "usd", "usd", "date", "date"], rows,
                       header={"mixed": ["Qté"], "word2": ["Désignation"], "usd": ["P.U. HT", "Montant HT"], "date": ["Commandé le", "Livré le"]},
                       total={"mixed": [""], "word2": ["Total HT"], "usd": ["", money(total, "fr")], "date": ["", ""]},
                       numeric=("usd", "mixed"), widths=[6, 36, 13, 15, 15, 15])
    return {
        "template": "vendor_invoice", "page_size": "A4", "languages": ["fr-FR"],
        "metadata": {"title": "Facture FA-2026-0127 – Hôtel Les Tilleuls", "author": "Atelier Lemoine & Fils",
                     "subject": "Mobilier sur mesure pour la salle du petit-déjeuner",
                     "keywords": ["facture", "mobilier", "ébénisterie", "Dijon"], "lang": "fr-FR", "created": "2026-03-09T10:00:00Z"},
        "theme": {"accent": "#5a3d1e", "lo_font": "Noto Serif", "lo_heading_font": "Noto Sans", "lo_size": "9.5pt", "content_cm": 17.2},
        "running_header": "Atelier Lemoine & Fils — Facture FA-2026-0127",
        "running_footer": "Page {page} / {pages}",
        "blocks": [
            P("Atelier Lemoine & Fils", "brand"),
            P(f"Ébénisterie · Agencement · 7 impasse des Tanneurs, 21000 Dijon · SIRET 512{nb}874{nb}339{nb}00021 · TVA FR41{nb}512874339", "small"),
            H(1, "Facture n° FA-2026-0127"),
            P(f"**Client{nb}:** Hôtel Les Tilleuls, M. Bertrand Faivre, 14 rue des Carmes, 21000 Dijon\n"
              f"**Date de facture{nb}:** 09/03/2026 — **Échéance{nb}:** 30/04/2026 — **Commande{nb}:** BC-0412"),
            P("Fourniture et pose du mobilier de la salle du petit-déjeuner, conformément au devis D-2025-311 accepté le "
              f"4 février. Les quantités livrées ont été vérifiées sur place avec M.{nb}Faivre le 6 mars."),
            H(2, "Détail de la commande"),
            table,
            P(f"**Total HT{nb}:** {money(total, 'fr')}\n**TVA 20{nb}%{nb}:** {money(vat, 'fr')}\n**Total TTC{nb}:** {money(total + vat, 'fr')}", "right"),
            H(2, "Conditions de règlement"),
            P(f"Paiement par virement à 30 jours fin de mois{nb}; aucun escompte pour paiement anticipé. En cas de retard, des "
              f"pénalités égales à trois fois le taux d’intérêt légal seront appliquées, ainsi qu’une indemnité forfaitaire de 40{nb}€ "
              f"pour frais de recouvrement. Une question{nb}? Écrivez-nous{nb}: [compta@lemoine-ebeniste.example](mailto:compta@lemoine-ebeniste.example)."),
            P(f"IBAN FR76{nb}3000{nb}4012{nb}3400{nb}0105{nb}5512{nb}345 — BIC BNPAFRPPDIJ", "small"),
        ],
    }


# ---------------------------------------------------------------- borderless


def spec_sheet_ja(plan: dict[str, Any]) -> dict[str, Any]:
    """Japanese coffee product line-up spec sheet (kinds: date, usd, word2) with a wrapped photo."""
    items = [
        (date(2025, 4, 10), 1280, "ドリップバッグ 青葉ブレンド 10g×5袋"),
        (date(2025, 6, 2), 1380, "ドリップバッグ エチオピア・イルガチェフェ 10g×5袋"),
        (date(2025, 9, 18), 1480, "ドリップバッグ コロンビア・ウィラ 10g×5袋"),
        (date(2025, 11, 5), 1580, "ドリップバッグ 冬季限定ブレンド 10g×5袋"),
        (date(2026, 1, 15), 2680, "ギフトセット 3種アソート 15袋入"),
        (date(2026, 2, 2), 1980, "カフェインレス コロンビア 10g×8袋"),
        (date(2026, 3, 14), 1280, "ドリップバッグ 春ブレンド「桜」 10g×5袋"),
        (date(2026, 3, 14), 3240, "コーヒー豆 青葉ブレンド 200g（中煎り）"),
        (date(2026, 4, 1), 3780, "コーヒー豆 エチオピア・ゲイシャ 100g（浅煎り）"),
        (date(2026, 4, 1), 980, "コールドブリュー パック 30g×2袋"),
        (date(2026, 5, 20), 4320, "業務用ドリップバッグ 50袋入（受注生産）"),
    ]
    rows = [{"date": [day(d, "cjk")], "usd": [money(p, "ja")], "word2": [name]} for d, p, name in items]
    table = plan_table(plan, 0, "t1", "borderless", ["date", "usd", "word2"], rows,
                       header={"date": ["発売日"], "usd": ["希望小売価格（税込）"], "word2": ["製品名・内容量"]},
                       caption="表１　製品ラインアップ（２０２６年３月現在）", widths=[22, 22, 56])
    return {
        "template": "product_spec_sheet", "page_size": "A4", "languages": ["ja-JP"],
        "metadata": {"title": "製品仕様書　ドリップバッグ・シリーズ", "author": "株式会社青葉珈琲焙煎所 品質管理部",
                     "subject": "ドリップバッグおよびコーヒー豆の製品仕様と価格", "keywords": ["製品仕様書", "ドリップバッグ", "コーヒー"],
                     "lang": "ja-JP", "created": "2026-03-14T01:00:00Z"},
        "theme": {"accent": "#3d5a2a", "font_size": "9.6pt"},
        "running_header": "株式会社青葉珈琲焙煎所　製品仕様書",
        "running_footer": "{page}／{pages}",
        "blocks": [
            H(1, "ドリップバッグ・シリーズ 製品仕様書"),
            P("発行日：2026年3月14日　改訂：第３版　発行：品質管理部", "small muted"),
            photo("f1", ["coffee-cup", "bread-bakery"], ["food", "product"],
                  {"coffee-cup": "写真１　青葉ブレンドの抽出例（中煎り）", "bread-bakery": "写真１　直営カフェで提供している焼き菓子との組み合わせ例"},
                  "写真１　製品イメージ", "right", "38%"),
            H(2, "１．製品概要"),
            P("青葉珈琲焙煎所のドリップバッグは、自社工場で焙煎した豆を焙煎後２４時間以内に挽き、窒素充填して個包装しています。"
              "カップにセットしてお湯を注ぐだけで、ハンドドリップに近い味わいを手軽にお楽しみいただけます。"
              "今春は桜の季節に合わせた限定ブレンドと、業務用の５０袋入りを新たに加えました。"),
            P("いずれの製品も、生豆の段階で欠点豆を手選別し、ロットごとにカッピングで風味を確認してから出荷しています。"
              "賞味期限は製造日から１２か月です。開封後はお早めにお召し上がりください。"),
            H(2, "２．共通仕様"),
            L(["原材料名：コーヒー豆（生豆生産国名は各製品の表示による）", "内容量：１袋あたり１０ｇ（コールドブリューは３０ｇ）",
               "保存方法：高温多湿・直射日光を避けて常温で保存", "抽出の目安：９０～９５℃のお湯を１４０ｍＬ、３回に分けて注ぐ",
               "製造者：株式会社青葉珈琲焙煎所　宮城県仙台市青葉区一番町２丁目４－１"]),
            H(2, "３．価格一覧"),
            table,
            box("callout", "価格はすべて消費税（８％）込みです。業務用製品は最小ロット１０箱から承ります。お問い合わせ：sales@aoba-coffee.example",
                title="ご注意"),
        ],
    }


def agenda_en_gb(plan: dict[str, Any]) -> dict[str, Any]:
    """British rail conference agenda (kinds: date, word2, usd, date) with photo and sidebar."""
    items = [
        (date(2026, 4, 14), "Digital signalling: lessons from the Cambrian line", 4500, date(2026, 3, 31)),
        (date(2026, 4, 14), "Station accessibility audit workshop", 6000, date(2026, 3, 31)),
        (date(2026, 4, 14), "Site visit: Wakefield Europort freight interchange", 8500, date(2026, 3, 24)),
        (date(2026, 4, 15), "Battery and hydrogen trains: procurement clinic", 4500, date(2026, 4, 1)),
        (date(2026, 4, 15), "Timetable resilience masterclass", 6000, date(2026, 4, 1)),
        (date(2026, 4, 15), "Early-career networking breakfast", 0, date(2026, 4, 8)),
        (date(2026, 4, 15), "Community rail partnerships roundtable", 3000, date(2026, 4, 3)),
        (date(2026, 4, 16), "Depot tour: Neville Hill traction maintenance", 8500, date(2026, 3, 27)),
        (date(2026, 4, 16), "Forum dinner at the Leeds Corn Exchange", 7250, date(2026, 4, 6)),
    ]
    rows = [{"date": [day(a, "en_gb"), day(b, "en_gb")], "word2": [s], "usd": [money(f, "en-GB")]} for a, s, f, b in items]
    table = plan_table(plan, 0, "t1", "borderless", ["date", "word2", "usd", "date"], rows,
                       header={"date": ["Date", "Booking closes"], "word2": ["Session"], "usd": ["Fee"]},
                       caption="Workshops, visits and add-on sessions", widths=[18, 48, 12, 22])
    return {
        "template": "conference_agenda", "page_size": "A4", "languages": ["en-GB", "el"],
        "metadata": {"title": "Northern Rail Futures Forum 2026 — Programme", "author": "Northern Rail Futures Forum secretariat",
                     "subject": "Programme, add-on sessions and practical information", "keywords": ["conference", "rail", "Leeds", "programme"],
                     "lang": "en-GB", "created": "2026-02-20T11:45:00Z"},
        "theme": {"accent": "#6b2f6b", "body_font": "'Noto Sans'", "font_size": "9.6pt"},
        "running_header": "Northern Rail Futures Forum · Leeds · 14–16 April 2026",
        "running_footer": "Programme v3 — page {page} of {pages}",
        "blocks": [
            P("14–16 April 2026 · Leeds", "kicker"),
            H(1, "Northern Rail Futures Forum 2026"),
            P("Three days of practical sessions for people who plan, build and run the railway in the North — from signalling "
              "engineers and timetable planners to community rail officers.", "lead"),
            photo("f1", ["city-hall", "library-shelves", "train-station"], ["civic", "building"],
                  {"city-hall": "The plenary sessions take place in the Victoria Hall.",
                   "library-shelves": "The reading room is open to delegates for quiet work.",
                   "train-station": "Leeds station is a six-minute walk from the venue."},
                  "The venue is a short walk from Leeds station.", "left", "40%"),
            H(2, "Plenary programme"),
            P("Each morning opens with a plenary in the Victoria Hall. This year’s keynote is given by Dr Eleni Papadopoulou "
              "(Ελένη Παπαδοπούλου), director of network planning at Hellenic Train, who will compare the Athens–Thessaloniki "
              "upgrade with the TransPennine Route Upgrade."),
            L(["09:00–09:30 Registration and coffee", "09:30–10:15 Keynote: “Two upgrades, one lesson”",
               "10:15–11:00 Panel: funding the next control period", "11:30–12:30 Parallel sessions (see below)"], ordered=True),
            box("sidebar", "Leeds station is a six-minute walk. Delegates with reduced mobility can book assisted travel "
                "through Passenger Assist; step-free routes are signed from the station’s south entrance.", title="Getting there"),
            H(2, "Add-on sessions", cls="clear"),
            P("Workshops and visits have limited places and must be booked separately. Fees include lunch where the session "
              "runs through midday. Site visits require safety boots and photo ID."),
            table,
            P("Book online at [nrff2026.example.org/register](https://nrff2026.example.org/register) or email the secretariat "
              "at [hello@nrff2026.example.org](mailto:hello@nrff2026.example.org). Cancellations made before the booking "
              "deadline are refunded in full."),
        ],
    }


def jornadas_es(plan: dict[str, Any]) -> dict[str, Any]:
    """Spanish teaching-innovation conference agenda for LibreOffice (kinds: date, word1, usd, word2)."""
    items = [
        (date(2026, 4, 22), "Paraninfo", 0, "Inauguración y conferencia marco"),
        (date(2026, 4, 22), "Aula 2.1", 2500, "Taller de evaluación formativa"),
        (date(2026, 4, 22), "Biblioteca", 0, "Mesa redonda: ¿qué cambia la IA en el aula?"),
        (date(2026, 4, 22), "Aula 2.3", 2500, "Aprendizaje basado en proyectos en FP"),
        (date(2026, 4, 23), "Laboratorio", 3000, "Gamificación en matemáticas de ESO"),
        (date(2026, 4, 23), "Exterior", 1200, "Visita al CEIP Ramiro Solans"),
        (date(2026, 4, 23), "Paraninfo", 0, "Comunicaciones libres (bloque A)"),
        (date(2026, 4, 23), "Aula 2.1", 2000, "Taller de lectura fácil"),
        (date(2026, 4, 23), "Comedor", 3800, "Cena de las Jornadas"),
        (date(2026, 4, 24), "Aula 2.3", 2000, "Taller de radio escolar"),
        (date(2026, 4, 24), "Paraninfo", 0, "Clausura y entrega de certificados"),
    ]
    rows = [{"date": [day(d, "slash_dmy")], "word1": [room], "usd": [money(p, "es")], "word2": [act]} for d, room, p, act in items]
    table = plan_table(plan, 0, "t1", "borderless", ["date", "word1", "usd", "word2"], rows,
                       header={"date": ["Fecha"], "word1": ["Sala"], "usd": ["Precio"], "word2": ["Actividad"]},
                       caption="Programa de actividades", widths=[16, 16, 14, 54])
    return {
        "template": "conference_agenda", "page_size": "A4", "languages": ["es-ES"],
        "metadata": {"title": "XI Jornadas de Innovación Educativa – Programa", "author": "Comité organizador de las Jornadas",
                     "subject": "Programa, precios e inscripción", "keywords": ["jornadas", "innovación educativa", "Zaragoza"],
                     "lang": "es-ES", "created": "2026-03-02T09:30:00Z"},
        "theme": {"accent": "#a33a1f", "lo_font": "Noto Sans", "lo_heading_font": "Noto Sans", "lo_size": "10pt", "content_cm": 17.2},
        "running_header": "XI Jornadas de Innovación Educativa · Zaragoza",
        "running_footer": "Página {page} de {pages}",
        "blocks": [
            H(1, "XI Jornadas de Innovación Educativa"),
            P("Zaragoza, del 22 al 24 de abril de 2026 · Facultad de Educación", "lead"),
            photo("f1", ["classroom", "school-building", "library-shelves"], ["school", "education"],
                  {"classroom": "Una de las aulas donde se celebrarán los talleres.",
                   "school-building": "El CEIP Ramiro Solans abrirá sus puertas el jueves.",
                   "library-shelves": "La biblioteca acogerá la mesa redonda."},
                  "Instalaciones de la Facultad de Educación.", "right", width_cm=6.0),
            P("Las Jornadas reúnen cada año a más de trescientos docentes de infantil, primaria, secundaria y formación "
              "profesional. ¿Su objetivo? Compartir experiencias que funcionan de verdad en el aula, con tiempo para "
              "conversar y aprender unos de otros."),
            P("Este año dedicamos una mesa redonda a la inteligencia artificial y ampliamos los talleres prácticos. "
              "¡Las plazas son limitadas! Las actividades gratuitas no requieren inscripción previa, salvo la visita al centro."),
            H(2, "Programa"),
            table,
            H(2, "Inscripción"),
            L(["Cuota general: 60,00 € (incluye documentación y cafés)", "Estudiantes de máster y personal en paro: 25,00 €",
               "Certificado de 20 horas reconocido por el Departamento de Educación"]),
            P("Inscripciones hasta el 10 de abril en [jornadas-innovacion.example.es](https://jornadas-innovacion.example.es/inscripcion). "
              "Para cualquier duda, escriba a la secretaría técnica: Begoña Muñoz Ibáñez."),
        ],
    }


# ---------------------------------------------------------------- wrapped


def expense_en(plan: dict[str, Any]) -> dict[str, Any]:
    """US expense report with long descriptions, Korean/Hindi code-switching, email screenshot and raster chart."""
    items = [
        (168430, "Round-trip economy airfare SFO–ICN–BOM–SFO on Asiana and Air India, booked through the corporate travel portal; e-ticket 988-2214937710", "Airfare", date(2026, 2, 14)),
        (61248, "Hotel, four nights at Lotte City Hotel Mapo (롯데시티호텔 마포), Seoul; breakfast included and city tax itemized on the folio", "Lodging", date(2026, 3, 6)),
        (18790, "Client dinner with the Hanbit Logistics (한빛물류) team at Hanilkwan, Jongno-gu; four attendees named on the itemized receipt", "Meals", date(2026, 3, 4)),
        (4620, "AREX express train from Incheon Airport to Seoul Station plus T-money card top-ups for subway travel to the client office", "Ground transport", date(2026, 3, 2)),
        (38875, "Hotel, three nights at Hyatt Pune (हयात पुणे), Kalyani Nagar, at the negotiated corporate rate; no incidentals charged", "Lodging", date(2026, 3, 11)),
        (5810, "Airport taxi and app-based rides between the hotel and the Hinjewadi client office; trip receipts attached in the portal", "Ground transport", date(2026, 3, 10)),
        (9435, "Working lunch for nine workshop participants at the client site, catered by a local vendor because the canteen was closed", "Meals", date(2026, 3, 9)),
        (2999, "International data roaming pass covering both countries, required for on-call coverage during the workshop week", "Telecom", date(2026, 3, 1)),
    ]
    rows = [{"usd": [money(a, "en-US")], "word2": [text, cat], "date": [day(d, "us")]} for a, text, cat, d in items]
    total = sum(a for a, *_ in items)
    table = plan_table(plan, 0, "t1", "ruled", ["usd", "word2", "word2", "date"], rows,
                       header={"usd": ["Amount"], "word2": ["Description", "Category"], "date": ["Date"]},
                       total={"usd": [money(total, "en-US")], "word2": ["Total reimbursable", ""], "date": [""]},
                       caption="Itemized expenses", widths=[13, 55, 17, 15])
    categories: dict[str, int] = {}
    for amount, _, cat, _ in items:
        categories[cat] = categories.get(cat, 0) + amount
    spec = {"title": "Spend by category (USD)", "categories": list(categories),
            "series": [("Trip total", [v / 100 for v in categories.values()])], "max": 2000, "ticks": 4,
            "tick_format": lambda v: f"${v:,.0f}"}
    mail = {"folders": ["Inbox", "Receipts", "Travel", "Sent"], "subject": "Your e-ticket receipt — Booking ref. 7KQ2XD",
            "from": "Asiana Airlines <noreply@flyasiana.example>", "to": "To: Priya Raghunathan", "date": "Sat, Feb 14, 2026, 9:42 PM",
            "body": ["Dear Ms. Raghunathan, thank you for booking with Asiana Airlines.",
                     "Itinerary: SFO → ICN Mar 1 · ICN → BOM Mar 6 · BOM → SFO Mar 12 (Air India)",
                     "Total charged to card ending 4417: USD 1,684.30"],
            "attachment": "eticket-988-2214937710.pdf", "height": 330}
    return {
        "template": "expense_report", "page_size": "Letter", "languages": ["en-US", "ko", "hi"],
        "metadata": {"title": "Expense report ER-2026-0311 — Seoul and Pune client workshops", "author": "Priya Raghunathan",
                     "subject": "Travel expenses for client workshops, March 2026", "keywords": ["expense report", "travel", "Seoul", "Pune"],
                     "lang": "en-US", "created": "2026-03-13T22:05:00Z"},
        "theme": {"accent": "#20568f", "body_font": "'Noto Sans'", "font_size": "9.3pt"},
        "running_header": "Brightline Analytics, Inc. — Expense report ER-2026-0311",
        "running_footer": "Submitted 03/13/2026 · page {page} of {pages}",
        "blocks": [
            H(1, "Expense report ER-2026-0311"),
            {"kind": "fields", "items": [("Employee", "Priya Raghunathan"), ("Employee ID", "BA-10482"), ("Department", "Customer Success"),
                                         ("Cost center", "CS-2200"), ("Trip", "Seoul and Pune client workshops"), ("Travel dates", "03/01/2026 – 03/12/2026")]},
            H(2, "Business purpose"),
            P("Two on-site onboarding workshops for new enterprise customers: Hanbit Logistics in Seoul (March 3–5) and "
              "Deccan Agro Exports in Pune (March 9–10). Both workshops were requested in the Q1 success plans and approved "
              "by Daniel Ortega on January 28."),
            table,
            chart("f2", "bar", spec, "Figure 1. Spend by category", raster=True, wrap="right", width="44%", size=(470, 250)),
            chart_table("c1", "Category", spec, lambda v: f"${v:,.2f}"),
            H(2, "Notes for the approver"),
            P("Lodging stayed under the city caps for Seoul ($165/night) and Pune ($140/night). The client dinner in Seoul "
              "exceeded the $40 per-person meal guideline by $6.98 per person; the overage is explained on the receipt "
              "upload. No alcohol is included in any claimed meal."),
            P("The airfare receipt is reproduced below because the airline issued it only by email."),
            screenshot("f1", "email", mail, "Figure 2. Airline e-ticket receipt (email)", width="86%"),
            P("I certify that these expenses were incurred for business purposes and have not been reimbursed elsewhere.", "small"),
        ],
    }


def itinerary_vi(plan: dict[str, Any]) -> dict[str, Any]:
    """Vietnamese company-retreat itinerary in decomposed (NFD) text (kinds: word2, usd, usd, date)."""
    items = [
        ("Đón đoàn tại sân bay Nội Bài, xe 29 chỗ đưa về khách sạn ở phố cổ, nhận phòng và nghỉ ngơi trước bữa tối", 4500000, 1500000, date(2026, 5, 14)),
        ("Ăn tối tại nhà hàng chả cá trên phố Chả Cá, thực đơn cố định cho 18 người, đã báo trước hai suất chay", 7200000, 2000000, date(2026, 5, 14)),
        ("Di chuyển Hà Nội – Hạ Long bằng đường cao tốc, dừng chân nghỉ ngơi ở Hải Dương, lên du thuyền buổi trưa", 6800000, 3000000, date(2026, 5, 15)),
        ("Du thuyền vịnh Hạ Long hai ngày một đêm: hang Sửng Sốt, chèo kayak ở hang Luồn, lớp học nấu ăn buổi chiều", 54000000, 20000000, date(2026, 5, 15)),
        ("Ngắm bình minh và tập thái cực quyền trên boong, trả phòng, ăn trưa trên tàu trước khi cập bến Tuần Châu", 3600000, 0, date(2026, 5, 16)),
        ("Chuyển sang Ninh Bình, nhận phòng homestay ở Tam Cốc, buổi tối họp tổng kết quý tại phòng hội nghị nhỏ", 12600000, 4000000, date(2026, 5, 16)),
        ("Đi thuyền ở Tràng An, tham quan chùa Bái Đính, đạp xe qua cánh đồng lúa, ăn trưa với đặc sản dê núi", 9900000, 2500000, date(2026, 5, 17)),
        ("Trở về Hà Nội, tiễn đoàn ra sân bay; dự phòng chi phí phát sinh và tiền bồi dưỡng cho hướng dẫn viên", 5400000, 0, date(2026, 5, 17)),
    ]
    rows = [{"word2": [text], "usd": [money(cost, "vi"), money(paid, "vi")], "date": [day(d, "slash_dmy")]} for text, cost, paid, d in items]
    cost = sum(i[1] for i in items)
    paid = sum(i[2] for i in items)
    table = plan_table(plan, 0, "t1", "ruled", ["word2", "usd", "usd", "date"], rows,
                       header={"word2": ["Hoạt động"], "usd": ["Chi phí dự kiến", "Đã đặt cọc"], "date": ["Ngày"]},
                       total={"word2": ["Tổng cộng"], "usd": [money(cost, "vi"), money(paid, "vi")], "date": [""]},
                       caption="Bảng 1. Lịch trình và chi phí chi tiết", widths=[52, 17, 16, 15])
    doc = {
        "template": "travel_itinerary", "page_size": "A4", "languages": ["vi-VN"],
        "metadata": {"title": "Lịch trình nghỉ dưỡng công ty – Hạ Long và Ninh Bình", "author": "Phòng Hành chính – Nhân sự, Công ty TNHH Sông Xanh",
                     "subject": "Lịch trình, chi phí và lưu ý cho chuyến đi tháng 5/2026", "keywords": ["lịch trình", "Hạ Long", "Ninh Bình", "nghỉ dưỡng"],
                     "lang": "vi-VN", "created": "2026-04-02T03:00:00Z"},
        "theme": {"accent": "#0f6b6b", "body_font": "'Noto Sans'", "font_size": "9.6pt"},
        "running_header": "Công ty TNHH Sông Xanh – Chuyến đi tháng 5/2026",
        "running_footer": "Trang {page}/{pages}",
        "blocks": [
            H(1, "Lịch trình nghỉ dưỡng: Hạ Long – Ninh Bình"),
            P("Từ ngày 14 đến 17 tháng 5 năm 2026 · 18 người · Trưởng đoàn: chị Nguyễn Thị Thu Hường", "lead"),
            photo("f1", ["harbor", "mountain-lake", "park-path"], ["harbor", "landscape"],
                  {"harbor": "Bến tàu nơi đoàn lên du thuyền.", "mountain-lake": "Phong cảnh núi non trên đường đi Ninh Bình.",
                   "park-path": "Đường mòn dạo bộ gần khu homestay."},
                  "Hình ảnh minh họa điểm đến.", "right", "40%"),
            P("Chuyến đi năm nay kết hợp nghỉ ngơi với buổi tổng kết quý. Mọi người vui lòng mang theo căn cước công dân, "
              "giày thể thao và áo khoác mỏng vì buổi sáng trên vịnh khá lạnh. Lịch trình có thể thay đổi nhẹ tùy thời tiết."),
            P("Công ty đã đặt cọc cho các dịch vụ chính. Phần còn lại sẽ được thanh toán bằng chuyển khoản sau khi kết thúc "
              "chuyến đi, căn cứ trên hóa đơn thực tế."),
            H(2, "Lịch trình chi tiết"),
            table,
            H(2, "Lưu ý"),
            L(["Tập trung tại sảnh văn phòng lúc 6 giờ 30 sáng ngày 14/05.", "Mỗi người được mang tối đa một vali và một ba lô nhỏ.",
               "Người say sóng nên báo trước để được bố trí cabin ở giữa tàu.", "Liên hệ khẩn cấp: anh Trần Quốc Bảo, 0912 345 678."]),
        ],
    }
    return nfd(doc)


def delegacja_pl(plan: dict[str, Any]) -> dict[str, Any]:
    """Polish business-trip settlement for LibreOffice (kinds: usd, word2, date)."""
    items = [
        (28900, "Bilet PKP Intercity Warszawa Centralna – Gdańsk Główny, klasa 2, pociąg EIP 5100, miejsce przy stoliku", date(2026, 3, 9)),
        (28900, "Bilet powrotny Gdańsk Główny – Warszawa Centralna, pociąg EIP 5113, zakup w aplikacji przewoźnika", date(2026, 3, 12)),
        (114600, "Hotel Hanza w Gdańsku – trzy noclegi ze śniadaniem, faktura VAT wystawiona na spółkę", date(2026, 3, 12)),
        (13500, "Dieta za trzy dni podróży służbowej (3 × 45,00 zł) zgodnie z rozporządzeniem w sprawie należności", date(2026, 3, 12)),
        (6450, "Przejazdy taksówką z dworca do hotelu oraz z hotelu na teren targów AmberExpo w dniu montażu stoiska", date(2026, 3, 9)),
        (42000, "Opłata za podłączenie prądu i miejsce parkingowe przy stoisku nr B-14, uiszczona u organizatora", date(2026, 3, 10)),
        (21280, "Kolacja służbowa z przedstawicielami firmy Bałtyk-Pak, potwierdzona listą uczestników i fakturą", date(2026, 3, 11)),
        (3800, "Wydruk ulotek i cenników w punkcie ksero przy ul. Długiej – materiały uzupełniające na stoisko", date(2026, 3, 10)),
    ]
    rows = [{"usd": [money(a, "pl")], "word2": [t], "date": [day(d, "dotted")]} for a, t, d in items]
    total = sum(a for a, *_ in items)
    table = plan_table(plan, 0, "t1", "ruled", ["usd", "word2", "date"], rows,
                       header={"usd": ["Kwota"], "word2": ["Opis wydatku"], "date": ["Data"]},
                       total={"usd": [money(total, "pl")], "word2": ["Razem do rozliczenia"], "date": [""]},
                       caption="Zestawienie wydatków", widths=[17, 66, 17])
    return {
        "template": "expense_report", "page_size": "A4", "languages": ["pl-PL"],
        "metadata": {"title": "Rozliczenie delegacji nr 14/2026 – targi w Gdańsku", "author": "Małgorzata Zielińska",
                     "subject": "Rozliczenie kosztów podróży służbowej, 9–12 marca 2026", "keywords": ["delegacja", "rozliczenie", "Gdańsk", "targi"],
                     "lang": "pl-PL", "created": "2026-03-16T07:40:00Z"},
        "theme": {"accent": "#2c4f7c", "lo_font": "Noto Sans", "lo_heading_font": "Noto Sans", "lo_size": "9.5pt", "content_cm": 17.2},
        "running_header": "Ogrodnictwo Zielony Dom sp. z o.o. — Dział Sprzedaży",
        "running_footer": "Strona {page} z {pages}",
        "blocks": [
            H(1, "Rozliczenie delegacji krajowej nr 14/2026"),
            {"kind": "fields", "items": [("Pracownik", "Małgorzata Zielińska"), ("Stanowisko", "Specjalistka ds. sprzedaży"),
                                         ("Cel wyjazdu", "Targi ogrodnicze AmberExpo, Gdańsk"), ("Termin", "9–12 marca 2026")]},
            P("Celem wyjazdu było przygotowanie i obsługa stoiska firmy podczas targów ogrodniczych w Gdańsku. W ciągu trzech "
              "dni przeprowadziłam 27 rozmów handlowych, w tym z dwoma nowymi dystrybutorami z Pomorza. Szczegółowa notatka "
              "z rozmów została przekazana kierownikowi działu."),
            H(2, "Wydatki"),
            table,
            P("Do rozliczenia dołączam oryginały biletów, fakturę za hotel oraz potwierdzenia płatności kartą służbową. "
              "Zaliczka w wysokości 1 500,00 zł została pobrana 5 marca; do zwrotu na rzecz pracownika pozostaje różnica."),
            H(2, "Akceptacja"),
            L(["Sprawdzono pod względem merytorycznym: Paweł Wójcik, kierownik działu", "Sprawdzono pod względem formalnym i rachunkowym: Dział Księgowości",
               "Zatwierdzono do wypłaty: Zarząd"], ordered=True),
        ],
    }
