"""Authored wild-v2 finance documents: annual/quarterly reports and bank statements."""

# ruff: noqa: E501, PLR0913, PLR0917, TRY003, EM102, PLR2004, ANN401, RUF005
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from bench.wild_templates.model import day, money, number
from bench.wild_v2_templates.core import (
    H,
    L,
    P,
    box,
    chart,
    chart_table,
    continued,
    group,
    photo,
    rng,
    screenshot,
    table,
)

NB = " "
NNB = " "

# ---------------------------------------------------------------- bank statement engine


def split_sizes(total: int, capacities: list[int]) -> list[int]:
    """Fill pages in order up to their row capacity; every page must receive rows."""
    sizes, left = [], total
    for capacity in capacities:
        take = min(capacity, left)
        sizes.append(take)
        left -= take
    if left or not sizes[-1]:
        raise ValueError(f"{total} rows do not match page capacities {capacities}")
    return sizes


def _months(start: date, end: date) -> list[tuple[int, int]]:
    out, year, month = [], start.year, start.month
    while (year, month) <= (end.year, end.month):
        out.append((year, month))
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return out


def ledger(key: str, start: date, end: date, recurring: list[tuple[int, str, int]], pool: list[tuple[str, int, int]],
           count: int) -> list[tuple[date, str, int]]:
    """Seeded transactions ``(date, description, signed minor units)`` sorted by date.

    ``recurring`` entries are ``(day of month, description, signed amount)``; ``pool`` entries are
    ``(description, low, high)`` debits drawn ``count`` times.
    """
    r = rng(key)
    events: list[tuple[date, str, int]] = []
    for year, month in _months(start, end):
        for dom, text, cents in recurring:
            when = date(year, month, dom)
            if start <= when <= end:
                events.append((when, text, cents))
    span = (end - start).days
    for _ in range(count):
        text, low, high = r.choice(pool)
        cents = r.randrange(low, high + 1)
        if high >= 1000:
            cents = cents // 5 * 5 if high < 20000 else cents // 100 * 100
        events.append((start + timedelta(days=r.randrange(span + 1)), text, -cents))
    events.sort(key=lambda e: (e[0], -e[2], e[1]))
    return events


def statement_rows(events: list[tuple[date, str, int]], opening: int, fmt: Any, when: Any, opening_label: str,
                   sizes: list[int], carried: tuple[str, str] | None, *, order: str = "date,desc,out,in,bal") -> tuple[list[list[str]], list[int], int]:
    """Running-balance rows plus segment sizes (adding brought/carried forward rows between segments)."""
    columns = order.split(",")

    def row(values: dict[str, str]) -> list[str]:
        return [values.get(c, "") for c in columns]

    rows = [row({"date": when(events[0][0]), "desc": opening_label, "bal": fmt(opening)})]
    balance = opening
    body = []
    for moment, text, cents in events:
        balance += cents
        body.append(row({"date": when(moment), "desc": text, "out": fmt(-cents) if cents < 0 else "",
                         "in": fmt(cents) if cents > 0 else "", "bal": fmt(balance)}))
    rows += body
    sizes = split_sizes(len(rows), sizes)
    if not carried:
        return rows, sizes, balance
    out, new_sizes, cursor = [], [], 0
    for index, size in enumerate(sizes):
        segment = rows[cursor:cursor + size]
        cursor += size
        if index:
            previous_balance = out[-1][columns.index("bal")]
            segment = [row({"desc": carried[0], "bal": previous_balance})] + segment
        if index < len(sizes) - 1:
            segment = [*segment, row({"desc": carried[1], "bal": segment[-1][columns.index("bal")]})]
        out += segment
        new_sizes.append(len(segment))
    return out, new_sizes, balance


# ---------------------------------------------------------------- w2-bank-engb-05 (reportlab, en-GB)


def bank_en_gb() -> dict[str, Any]:
    """Quarterly current-account statement from a UK building society."""
    fmt = lambda c: money(c, "en-GB").replace("£", "")  # noqa: E731 - column formatter
    events = ledger("bank-engb", date(2026, 1, 1), date(2026, 3, 31), [
        (1, "STANDING ORDER  RENT  KESTREL LETTINGS LTD", -112500),
        (5, "DIRECT DEBIT  COUNCIL TAX  BRISTOL CITY", -16700),
        (8, "DIRECT DEBIT  BRISTOL WATER", -3412),
        (12, "DIRECT DEBIT  OCTOPUS ENERGY", -9850),
        (15, "DIRECT DEBIT  VODAFONE LTD", -2499),
        (26, "BANK GIRO CREDIT  SALARY  AVONMOUTH MARINE LTD", 284316),
    ], [
        ("CARD PAYMENT  TESCO STORES 2817  BRISTOL", 1240, 8960), ("CARD PAYMENT  SAINSBURY'S S/MKT  CLIFTON", 980, 6420),
        ("CARD PAYMENT  GREAT WESTERN RAIL  BRISTOL TM", 1150, 4890), ("CONTACTLESS  PRET A MANGER  BROAD QUAY", 395, 1185),
        ("CONTACTLESS  FIRST BUS  BRISTOL", 220, 750), ("CARD PAYMENT  BOOTS 1142  CABOT CIRCUS", 450, 3299),
        ("CARD PAYMENT  AMAZON.CO.UK  MKTPLACE", 799, 6499), ("CASH MACHINE  LLOYDS BANK  QUEENS RD", 2000, 10000),
        ("CARD PAYMENT  THE APPLE TREE  BRISTOL", 1480, 4620), ("CARD PAYMENT  SHELL HOTWELLS", 3500, 7200),
        ("FASTER PAYMENT  R OKONKWO  FLAT BILLS", 2500, 6000), ("CONTACTLESS  WAITROSE 0631  HENLEAZE", 640, 4380),
    ], 78)
    opening = 184233
    rows, sizes, closing = statement_rows(events, opening, fmt, lambda d: f"{d.day:02d} {d.strftime('%b')} {str(d.year)[2:]}",
                                          "BALANCE BROUGHT FORWARD", [12, 24, 24, 24, 16], ("BALANCE BROUGHT FORWARD", "BALANCE CARRIED FORWARD"))
    paid_out = -sum(c for _, _, c in events if c < 0)
    paid_in = sum(c for _, _, c in events if c > 0)
    header = [["Date", "Payment type and details", "Paid out", "Paid in", "Balance"]]
    segments = continued("t1", header, rows, sizes, caption="Your transactions", continued_caption="Your transactions (continued)",
                         align=["l", "l", "r", "r", "r"], widths=[12, 46, 14, 14, 14])
    summary = table("t0", [["Account summary", ""], ["Balance on 01 January 2026", money(opening, "en-GB")],
                           ["Money out", money(paid_out, "en-GB")], ["Money in", money(paid_in, "en-GB")],
                           ["Balance on 31 March 2026", money(closing, "en-GB")]], header_rows=1, align=["l", "r"], widths=[60, 40],
                    width_share=0.55)
    footer = "Severn & Avon Building Society · Sort code 40-17-62 · Account 31847206 · Page {page} of {pages}"
    pages = [
        [group([P("Severn & Avon Building Society", "brand"), P("Head Office: 14 Narrow Quay, Bristol BS1 4QA\nHelpline 0117 496 0381 · severnavon.example", "small right")], "split"),
         group([P("Ms Imogen Okafor-Lyle\nFlat 3, 27 Royal York Crescent\nClifton\nBristol BS8 4JX", "meta"),
                P("**Everyday Current Account**\nStatement 1 of 2026\n01 January to 31 March 2026\nSort code 40-17-62 · Account 31847206\nIBAN GB71 SAVB 4017 6231 8472 06", "meta")], "split"),
         summary,
         P("Your Arranged Overdraft limit is £500.00 and it was not used during this period. Interest on credit balances is paid "
           "monthly at 1.10% AER (variable)."),
         segments[0]],
        [segments[1]],
        [segments[2]],
        [segments[3]],
        [segments[4],
         H(2, "Important information"),
         P("Please check this statement carefully. If you see a payment you do not recognise, call us on 0117 496 0381 straight away. "
           "Lines are open 8am to 8pm Monday to Friday and 9am to 1pm on Saturday."),
         box("callout", "Your eligible deposits with Severn & Avon Building Society are protected up to a total of £85,000 by the "
             "Financial Services Compensation Scheme, the UK's deposit guarantee scheme. Any deposits you hold above the limit are "
             "unlikely to be covered.", title="Financial Services Compensation Scheme"),
         P("From 1 May 2026 the fee for an unarranged payment returned unpaid will be removed. No action is needed. Our full tariff "
           "is available in branch and at [severnavon.example/tariff](https://severnavon.example/tariff).", "small"),
         P("Severn & Avon Building Society is authorised by the Prudential Regulation Authority and regulated by the Financial "
           "Conduct Authority and the Prudential Regulation Authority (Firm Reference Number 106402).", "small")],
    ]
    return {
        "template": "bank_statement", "page_size": "A4", "languages": ["en-GB"],
        "metadata": {"title": "Statement 1 of 2026 — Everyday Current Account 31847206", "author": "Severn & Avon Building Society",
                     "subject": "Current account statement, 1 January to 31 March 2026",
                     "keywords": ["bank statement", "current account", "Q1 2026"], "lang": "en-GB", "created": "2026-04-02T05:40:00Z"},
        "theme": {"accent": "#0b5d5b", "rl_size": 8.8, "rl_margin": 44},
        "running_footer": footer, "pages": pages,
        "arithmetic": [{"kind": "running_balance", "table": "t1", "debit": 2, "credit": 3, "balance": 4},
                       {"kind": "sum", "terms": [["+", money(opening, "en-GB")], ["-", money(paid_out, "en-GB")], ["+", money(paid_in, "en-GB")]],
                        "equals": money(closing, "en-GB")}],
    }


# ---------------------------------------------------------------- w2-bank-fr-06 (chromium, fr-FR)


def bank_fr() -> dict[str, Any]:
    """French bank statement without per-line balance: debit/credit columns, totals and new balance."""
    fmt = lambda c: money(c, "fr").replace(f"{NB}€", "")  # noqa: E731
    events = ledger("bank-fr", date(2026, 4, 1), date(2026, 5, 31), [
        (2, "PRLV SEPA FONCIA LYON CONFLUENCE LOYER AVRIL-MAI", -98400),
        (4, "PRLV SEPA EDF CLIENTS PARTICULIERS", -7350),
        (6, "PRLV SEPA FREE MOBILE", -1999),
        (10, "PRLV SEPA MUTUELLE HARMONIE SANTÉ", -4280),
        (28, "VIR SEPA RECU /DE CAISSE PRIMAIRE ASSURANCE MALADIE", 2384),
        (29, "VIR SEPA RECU /DE ATELIERS RHÔNE-ALPES INGÉNIERIE SALAIRE", 312745),
    ], [
        ("CB CARREFOUR MARKET LYON 7E", 1280, 9640), ("CB BOULANGERIE DU PRÉ GAUCHER", 240, 1190), ("CB SNCF INTERNET", 2900, 11800),
        ("CB TCL LYON TITRES TRANSPORT", 210, 6540), ("CB FNAC BELLECOUR", 1499, 8990), ("CB PHARMACIE DES ÉTATS-UNIS", 520, 3860),
        ("RETRAIT DAB LYON JEAN MACÉ", 2000, 8000), ("CB LA CAVE D'ŒNOPHILE", 1450, 5600), ("CB MONOPRIX GUILLOTIÈRE", 870, 6210),
        ("CB TOTALENERGIES A7 VIENNE", 4200, 8100), ("CB CINÉMA COMŒDIA", 1100, 2400), ("PAYPAL *VINTED", 900, 4500),
    ], 64)
    for index, (moment, text, cents) in enumerate(events):
        if text == "CB CARREFOUR MARKET LYON 7E" and moment.day % 3 == 0:
            events[index] = (moment, f"CB CARREFOUR MARKET LYON 7E FACT. {moment.day:02d}{moment.month:02d}26", cents)
    opening = 241018
    when = lambda d: f"{d.day:02d}/{d.month:02d}"  # noqa: E731
    rows = [[when(m), when(m + timedelta(days=1 if c < 0 else 0)), t, fmt(-c) if c < 0 else "", fmt(c) if c > 0 else ""] for m, t, c in events]
    debit = -sum(c for _, _, c in events if c < 0)
    credit = sum(c for _, _, c in events if c > 0)
    closing = opening - debit + credit
    total = [["", "", "Total des opérations", fmt(debit), fmt(credit)]]
    header = [["Date", "Valeur", "Nature des opérations", "Débit", "Crédit"]]
    segments = continued("t1", header, rows, split_sizes(len(rows), [16, 23, 23, 18]), caption="Détail des opérations — compte de chèques nº 00041 72093 18",
                         continued_caption="Détail des opérations (suite)", align=["l", "l", "l", "r", "r"], widths=[9, 9, 54, 14, 14], total=total)
    spec = {"title": "Dépenses par catégorie (€)", "categories": ["Logement", "Courses", "Transports", "Santé", "Loisirs"],
            "series": [("Avril", [1088.50, 412.30, 198.40, 61.20, 143.00]), ("Mai", [1041.30, 389.75, 236.10, 74.90, 118.60])],
            "max": 1200, "ticks": 4, "tick_format": lambda v: number(v, "fr", 0)}
    pages = [
        [group([P("Banque Rhodanienne", "brand"), P("Agence Lyon Jean-Macé · 52 avenue Jean-Jaurès · 69007 Lyon\nTél. 04 72 55 01 38 · lundi–vendredi 9 h – 18 h", "small right")], "split"),
         group([P("**M. et Mme Bastien et Léa Ferrand-Nguyễn**\n14 rue de l’Université\n69007 LYON", "meta"),
                P("**Relevé de compte nº 5**\ndu 1er avril au 31 mai 2026\nIBAN FR76 1820 6000 4172 0931 8000 112\nBIC BRHOFRPPXXX", "meta right")], "split"),
         P(f"Ancien solde créditeur au 31/03/2026 : **{money(opening, 'fr')}**", "lead"),
         segments[0]],
        [segments[1]],
        [segments[2]],
        [segments[3],
         P(f"Nouveau solde créditeur au 31/05/2026 : **{money(closing, 'fr')}**", "lead"),
         box("footnote", "¹ Les opérations par carte sont débitées à la date de valeur J+1. Taux débiteur annuel effectif (TAEG) du découvert autorisé : 14,90 %.")],
        [H(2, "Votre budget en un coup d’œil"),
         chart("f1", "bar", spec, "Répartition des dépenses courantes, avril–mai 2026 (hors épargne)", raster=False, width="82%"),
         chart_table("c1", "Catégorie", spec, lambda v: number(v, "fr", 2)),
         H(2, "Informations importantes"),
         P("À compter du 1er juillet 2026, la cotisation annuelle de votre carte Visa Premier passera de 134,00 € à 139,00 €. "
           "Conformément à la réglementation, vous disposez d’un délai de deux mois pour refuser cette modification et résilier "
           "votre contrat sans frais."),
         box("callout", "Nous ne vous demanderons jamais vos codes confidentiels ni de valider une opération par téléphone. En cas de "
             "doute, raccrochez et appelez votre conseiller, Mme Aurélie Chassagne, au 04 72 55 01 38.", title="Vigilance « faux conseiller »", cls="warn"),
         P("Médiateur : en cas de litige non résolu par votre agence, vous pouvez saisir gratuitement le médiateur de la Banque "
           "Rhodanienne, 7 place Bellecour, 69002 Lyon, ou en ligne sur [mediateur.banque-rhodanienne.example](https://mediateur.banque-rhodanienne.example).", "small"),
         P("Banque Rhodanienne — société anonyme coopérative à capital variable — RCS Lyon 642 017 359 — intermédiaire en assurance ORIAS nº 07 023 418.", "small muted")],
    ]
    return {
        "template": "bank_statement", "page_size": "A4", "languages": ["fr-FR", "vi"],
        "metadata": {"title": "Relevé de compte nº 5 — avril–mai 2026", "author": "Banque Rhodanienne",
                     "subject": "Relevé de compte de chèques, 1er avril au 31 mai 2026", "keywords": ["relevé de compte", "banque", "2026"],
                     "lang": "fr-FR", "created": "2026-06-01T03:15:00Z"},
        "theme": {"accent": "#7a1f3d", "font_size": "8.8pt", "margins": "14mm 14mm 16mm 14mm"},
        "running_footer": "Banque Rhodanienne · Relevé nº 5 · page {page}/{pages}", "pages": pages,
        "arithmetic": [{"kind": "column_sum", "table": "t1", "columns": [3, 4], "label_column": 2, "total_label": "Total des opérations"},
                       {"kind": "sum", "terms": [["+", money(opening, "fr")], ["-", money(debit, "fr")], ["+", money(credit, "fr")]], "equals": money(closing, "fr")}],
    }


# ---------------------------------------------------------------- w2-bank-pl-07 (libreoffice untagged, pl-PL)


def bank_pl() -> dict[str, Any]:
    """Polish monthly account statement with balance after each operation."""
    fmt = lambda c: money(c, "pl").replace(f"{NB}zł", "")  # noqa: E731
    events = ledger("bank-pl", date(2026, 2, 1), date(2026, 2, 28), [
        (3, "Przelew wychodzący: Spółdzielnia Mieszkaniowa „Śródmieście” – czynsz luty", -68714),
        (10, "Polecenie zapłaty: TAURON Sprzedaż sp. z o.o.", -21388),
        (10, "Przelew przychodzący: Wydawnictwo Wiśniewski i Synowie – wynagrodzenie 01/2026", 742150),
        (14, "Przelew na rachunek oszczędnościowy „Wakacje 2026”", -50000),
        (20, "Przelew wychodzący: Urząd Skarbowy Kraków-Krowodrza – PIT", -31200),
    ], [
        ("Płatność kartą: Biedronka 4127 Kraków", 1849, 18760), ("Płatność kartą: Żabka Z3381 Kraków", 799, 4590),
        ("Płatność BLIK: Allegro.pl", 2999, 34900), ("Płatność kartą: Orlen Stacja nr 1104", 15000, 32050),
        ("Płatność kartą: Rossmann 288", 1299, 8840), ("Płatność kartą: MPK Kraków – bilet okresowy", 8000, 8000),
        ("Wypłata z bankomatu: Euronet ul. Długa 17", 10000, 40000), ("Płatność kartą: Kawiarnia „Pod Ratuszem”", 1450, 3890),
        ("Płatność kartą: Apteka Gemini", 1520, 9875), ("Przelew BLIK na telefon: Zofia Kędzierska", 2000, 15000),
    ], 52)
    opening = 1294308
    rows, sizes, closing = statement_rows(events, opening, fmt, lambda d: day(d, "dotted"), "Saldo początkowe",
                                          [15, 24, 24], None, order="date,desc,out,in,bal")
    header = [["Data operacji", "Opis operacji", "Obciążenia", "Uznania", "Saldo po operacji"]]
    segments = continued("t1", header, rows, sizes, caption="Zestawienie operacji (kwoty w PLN)", continued_caption="Zestawienie operacji – ciąg dalszy",
                         align=["l", "l", "r", "r", "r"], widths=[13, 47, 13, 13, 14])
    paid_out = -sum(c for _, _, c in events if c < 0)
    paid_in = sum(c for _, _, c in events if c > 0)
    pages = [
        [P("Bank Wiślany S.A.", "brand"),
         P("ul. Karmelicka 41, 31-128 Kraków · infolinia 12 555 04 40 · bankwislany.example", "small"),
         H(1, "Wyciąg z rachunku nr 2/2026"),
         P("**Posiadacz rachunku:** Bartłomiej Żółtowski-Nowak, ul. Józefa Dietla 72 m. 9, 31-039 Kraków\n"
           "**Rachunek:** Konto Osobiste Plus, PL 61 1090 1014 0000 0712 1981 2874\n"
           f"**Okres:** {day(date(2026, 2, 1), 'dotted')} – {day(date(2026, 2, 28), 'dotted')}   **Waluta:** PLN", "meta"),
         segments[0]],
        [segments[1]],
        [segments[2]],
        [H(2, "Podsumowanie okresu"),
         table("t2", [["Pozycja", "Kwota (PLN)"], ["Saldo początkowe", fmt(opening)], ["Suma obciążeń", fmt(paid_out)],
                      ["Suma uznań", fmt(paid_in)], ["Saldo końcowe", fmt(closing)]], rendering="borderless", align=["l", "r"], widths=[70, 30]),
         P("Oprocentowanie środków na rachunku wynosiło w okresie wyciągu 0,50% w skali roku. Odsetki kapitalizowane są na koniec "
           "każdego miesiąca kalendarzowego i podlegają zryczałtowanemu podatkowi dochodowemu w wysokości 19%."),
         box("callout", "Od 1 kwietnia 2026 r. opłata za wypłatę gotówki z bankomatów innych banków w kraju wyniesie 0,00 zł przy "
             "wpływach na rachunek co najmniej 2 000,00 zł miesięcznie. Pełna Tabela Opłat i Prowizji jest dostępna w oddziałach "
             "oraz na stronie banku.", title="Zmiany w Tabeli Opłat i Prowizji"),
         P("Prosimy o sprawdzenie zgodności salda. Ewentualne zastrzeżenia należy zgłosić w ciągu 14 dni od daty otrzymania "
           "wyciągu – w oddziale, przez infolinię lub w bankowości internetowej. Brak zastrzeżeń w tym terminie oznacza "
           "uznanie salda za zgodne."),
         P("Środki zgromadzone na rachunkach w Banku Wiślanym S.A. objęte są systemem gwarantowania depozytów Bankowego Funduszu "
           "Gwarancyjnego do równowartości 100 000 euro.", "small"),
         P("Bank Wiślany Spółka Akcyjna z siedzibą w Krakowie, Sąd Rejonowy dla Krakowa-Śródmieścia, XI Wydział Gospodarczy KRS, "
           "KRS 0000127459, NIP 676-00-12-874, kapitał zakładowy 412 000 000 zł (wpłacony w całości). Dokument wygenerowany "
           "elektronicznie, nie wymaga podpisu ani stempla.", "small")],
    ]
    return {
        "template": "bank_statement", "page_size": "A4", "languages": ["pl-PL"], "tagged": False,
        "metadata": {"title": "Wyciąg z rachunku nr 2/2026", "author": "Bank Wiślany S.A.", "subject": "Wyciąg z rachunku osobistego za luty 2026",
                     "keywords": ["wyciąg", "rachunek osobisty", "luty 2026"], "lang": "pl-PL", "created": "2026-03-01T04:02:00Z"},
        "theme": {"accent": "#1d3f73", "lo_size": "9pt", "lo_font": "Noto Sans", "lo_margin": "1.6cm"},
        "running_footer": "Bank Wiślany S.A. · Wyciąg nr 2/2026 · strona {page} z {pages}", "pages": pages,
        "arithmetic": [{"kind": "running_balance", "table": "t1", "debit": 2, "credit": 3, "balance": 4},
                       {"kind": "sum", "terms": [["+", fmt(opening)], ["-", fmt(paid_out)], ["+", fmt(paid_in)]], "equals": fmt(closing)}],
    }


# ---------------------------------------------------------------- w2-bank-ar-08 (pylopdf, ar)

_AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def _aed(cents: int) -> str:
    whole, fraction = divmod(abs(cents), 100)
    text = f"{whole:,}.{fraction:02d}"
    return ("-" if cents < 0 else "") + text


def bank_ar() -> dict[str, Any]:
    """Arabic (UAE) account statement; Arabic-only and Latin-only text boxes for pylopdf."""
    events = ledger("bank-ar", date(2026, 3, 1), date(2026, 3, 31), [
        (1, "تحويل راتب من شركة الخليج للهندسة", 1845000),
        (2, "إيجار سكني (دفعة شيك)", -650000),
        (5, "فاتورة هيئة كهرباء ومياه دبي", -48730),
        (9, "اشتراك الإنترنت المنزلي", -38900),
        (15, "قسط تمويل السيارة", -214500),
        (22, "تحويل إلى حساب التوفير", -200000),
    ], [
        ("شراء من كارفور مول الإمارات", 4500, 61200), ("شراء من صيدلية الحياة", 2200, 18600), ("سحب نقدي من صراف آلي", 20000, 100000),
        ("شراء من مطعم الفنر", 9500, 32000), ("شراء من محطة وقود إينوك", 9000, 21000), ("شراء من مكتبة جرير", 3500, 27500),
        ("تعبئة رصيد نول للمواصلات", 5000, 10000), ("شراء من مخبز الريف", 1200, 6500),
    ], 41)
    opening = 2713855
    rows, sizes, closing = statement_rows(events, opening, _aed, lambda d: d.strftime("%d/%m/%Y"), "الرصيد الافتتاحي", [16, 34], None)
    header = [["التاريخ", "البيان", "مدين", "دائن", "الرصيد"]]
    segments = continued("t1", header, rows, sizes, caption="تفاصيل الحركات (بالدرهم الإماراتي)", continued_caption="تفاصيل الحركات (تابع)",
                         align=["l", "l", "r", "r", "r"], widths=[15, 41, 14, 14, 16])
    paid_out = -sum(c for _, _, c in events if c < 0)
    paid_in = sum(c for _, _, c in events if c > 0)
    pages = [
        [P("بنك الواحة الوطني", "brand"),
         P("Al Waha National Bank PJSC", "small"),
         H(1, "كشف حساب جاري"),
         P("كشف شهري لحساب جاري شخصي"),
         table("t0", [["البيان", "التفاصيل"], ["اسم العميل", "سلمى عبد الرحمن الكتبي"], ["الفترة", "01/03/2026 - 31/03/2026"], ["رقم الحساب", "0193-472815-001"],
                      ["رقم الآيبان", "AE07 0331 2345 6789 0123 456"], ["الفرع", "فرع البرشاء، دبي"], ["العملة", "درهم إماراتي"]],
               rendering="borderless", widths=[35, 65]),
         segments[0]],
        [segments[1]],
        [H(2, "ملخص الحساب"),
         table("t2", [["البند", "المبلغ"], ["الرصيد الافتتاحي", _aed(opening)], ["إجمالي المدين", _aed(paid_out)], ["إجمالي الدائن", _aed(paid_in)],
                      ["الرصيد الختامي", _aed(closing)]], align=["l", "r"], widths=[60, 40]),
         P("يرجى مراجعة هذا الكشف بعناية وإبلاغ البنك بأي ملاحظات خلال ثلاثين يومًا من تاريخ إصداره، وإلا اعتُبرت البيانات الواردة فيه صحيحة ومقبولة."),
         box("callout", "لن يطلب منك البنك أبدًا الإفصاح عن الرقم السري أو رمز التحقق عبر الهاتف أو الرسائل النصية. في حال الاشتباه بأي عملية، يرجى الاتصال بمركز خدمة العملاء فورًا.", title="تنبيه أمني", cls="warn"),
         P("مركز خدمة العملاء على مدار الساعة"),
         P("+971 4 555 0192 · alwaha-bank.example"),
         P("بنك الواحة الوطني ش.م.ع خاضع لرقابة مصرف الإمارات العربية المتحدة المركزي.", "small")],
    ]
    return {
        "template": "bank_statement", "page_size": "A4", "languages": ["ar", "en"], "dir": "rtl",
        "metadata": {"title": "كشف حساب جاري، مارس ٢٠٢٦", "author": "بنك الواحة الوطني", "subject": "كشف حساب شهري",
                     "keywords": ["كشف حساب", "بنك", "مارس 2026"], "lang": "ar", "created": "2026-04-01T02:30:00Z"},
        "theme": {"accent": "#1b5e3b", "py_size": 9.5},
        "running_footer": "الصفحة {page} من {pages}", "pages": pages,
        "arithmetic": [{"kind": "running_balance", "table": "t1", "debit": 2, "credit": 3, "balance": 4},
                       {"kind": "sum", "terms": [["+", _aed(opening)], ["-", _aed(paid_out)], ["+", _aed(paid_in)]], "equals": _aed(closing)}],
    }


# ---------------------------------------------------------------- shared report helpers


def _signed(value: int, positive: Any, negative: Any) -> str:
    return positive(value) if value >= 0 else negative(-value)


def store_table(key: str, stores: list[tuple[str, str, str]], scale_low: int, scale_high: int) -> list[tuple[str, str, str, int, int]]:
    """Seeded two-year revenue per site ``(name, city, opened, prior, current)``."""
    r = rng(key)
    out = []
    for name, city, opened in stores:
        prior = r.randrange(scale_low, scale_high)
        growth = r.uniform(-0.08, 0.17)
        current = prior if opened.endswith("2025") and False else int(prior * (1 + growth))
        out.append((name, city, opened, prior, current))
    return out


# ---------------------------------------------------------------- w2-annual-en-01 (chromium, en-US)

_EN_STORES = [
    ("Bend Old Mill", "Bend, OR", "2011"), ("Boise Eighth Street", "Boise, ID", "2014"), ("Bozeman Main", "Bozeman, MT", "2013"),
    ("Boulder Pearl Street", "Boulder, CO", "2009"), ("Coeur d’Alene Sherman", "Coeur d’Alene, ID", "2018"),
    ("Denver LoDo", "Denver, CO", "2012"), ("Durango Main Avenue", "Durango, CO", "2016"), ("Eugene Fifth Street", "Eugene, OR", "2010"),
    ("Flagstaff Route 66", "Flagstaff, AZ", "2017"), ("Fort Collins Old Town", "Fort Collins, CO", "2015"),
    ("Hood River Oak Street", "Hood River, OR", "2008"), ("Jackson Town Square", "Jackson, WY", "2014"),
    ("Kalispell Center", "Kalispell, MT", "2019"), ("Ketchum Sun Valley", "Ketchum, ID", "2012"), ("Lake Tahoe Truckee", "Truckee, CA", "2016"),
    ("Logan Center Street", "Logan, UT", "2020"), ("Missoula Higgins", "Missoula, MT", "2011"), ("Moab Center", "Moab, UT", "2018"),
    ("Ogden 25th Street", "Ogden, UT", "2021"), ("Olympia Capitol Way", "Olympia, WA", "2019"), ("Park City Main", "Park City, UT", "2013"),
    ("Portland Pearl District", "Portland, OR", "2007"), ("Portland Sellwood", "Portland, OR", "2016"), ("Reno Midtown", "Reno, NV", "2020"),
    ("Salt Lake Sugar House", "Salt Lake City, UT", "2010"), ("Santa Fe Railyard", "Santa Fe, NM", "2017"),
    ("Seattle Ballard", "Seattle, WA", "2009"), ("Seattle Capitol Hill", "Seattle, WA", "2015"), ("Spokane Riverfront", "Spokane, WA", "2014"),
    ("Steamboat Lincoln Avenue", "Steamboat Springs, CO", "2018"), ("Tacoma Proctor", "Tacoma, WA", "2021"),
    ("Walla Walla Main", "Walla Walla, WA", "2022"), ("Wenatchee Riverside", "Wenatchee, WA", "2022"), ("Whitefish Central", "Whitefish, MT", "2019"),
    ("Kyoto Arashiyama (京都嵐山)", "Kyoto, Japan", "2023"), ("Sapporo Ōdōri (札幌大通)", "Sapporo, Japan", "2024"),
    ("Vancouver Kitsilano", "Vancouver, BC", "2021"), ("Calgary Kensington", "Calgary, AB", "2023"),
]


def annual_en() -> dict[str, Any]:
    """US outdoor retailer annual report with a store revenue note continuing over two pages."""
    k = lambda v: f"{v:,}"  # noqa: E731 - $ thousands
    paren = lambda v: f"({v:,})"  # noqa: E731
    stores = store_table("annual-en", _EN_STORES, 2400, 9800)
    store_rows = []
    for name, city, opened, prior, current in stores:
        change = (current - prior) / prior * 100
        store_rows.append([name, city, opened, k(prior), k(current), f"{'+' if change >= 0 else '−'}{abs(change):.1f}%"])
    prior_total, current_total = sum(s[3] for s in stores), sum(s[4] for s in stores)
    total_change = (current_total - prior_total) / prior_total * 100
    note_segments = continued("t3", [["Store", "Location", "Opened", "FY2024", "FY2025", "Change"]], store_rows, [24, 14],
                              caption="Note 14 — Net retail sales by store ($ thousands)", continued_caption="Note 14 — Net retail sales by store, continued ($ thousands)",
                              align=["l", "l", "c", "r", "r", "r"], widths=[30, 24, 9, 13, 13, 11],
                              total=[["Total retail", "", "", k(prior_total), k(current_total), f"+{total_change:.1f}%"]])
    retail_prior, retail_current = prior_total, current_total
    online_prior, online_current = 61284, 74930
    wholesale_prior, wholesale_current = 22715, 24108
    revenue_prior = retail_prior + online_prior + wholesale_prior
    revenue_current = retail_current + online_current + wholesale_current
    cogs_prior, cogs_current = int(revenue_prior * 0.552), int(revenue_current * 0.541)
    gross_prior, gross_current = revenue_prior - cogs_prior, revenue_current - cogs_current
    sga_prior, sga_current = int(revenue_prior * 0.318), int(revenue_current * 0.309)
    dep_prior, dep_current = 9412, 10287
    op_prior, op_current = gross_prior - sga_prior - dep_prior, gross_current - sga_current - dep_current
    int_prior, int_current = 2108, 1876
    pre_prior, pre_current = op_prior - int_prior, op_current - int_current
    tax_prior, tax_current = int(pre_prior * 0.247), int(pre_current * 0.244)
    net_prior, net_current = pre_prior - tax_prior, pre_current - tax_current
    income = table("t2", [
        ["", "FY2025", "FY2024"],
        ["Retail stores", k(retail_current), k(retail_prior)], ["Online", k(online_current), k(online_prior)],
        ["Wholesale and rentals", k(wholesale_current), k(wholesale_prior)],
        ["Net revenue", k(revenue_current), k(revenue_prior)],
        ["Cost of goods sold", paren(cogs_current), paren(cogs_prior)], ["Gross profit", k(gross_current), k(gross_prior)],
        ["Selling, general and administrative", paren(sga_current), paren(sga_prior)],
        ["Depreciation and amortization", paren(dep_current), paren(dep_prior)],
        ["Operating income", k(op_current), k(op_prior)], ["Interest expense, net", paren(int_current), paren(int_prior)],
        ["Income before income taxes", k(pre_current), k(pre_prior)], ["Provision for income taxes", paren(tax_current), paren(tax_prior)],
        ["Net income", k(net_current), k(net_prior)],
    ], caption="Consolidated statements of income ($ thousands)", align=["l", "r", "r"], widths=[58, 21, 21], total_rows=[4, 6, 9, 13])
    sums = []
    for col, (rev, cogs, gross, sga, dep, op, intr, pre, tax, net, parts) in (
            (1, (revenue_current, cogs_current, gross_current, sga_current, dep_current, op_current, int_current, pre_current, tax_current, net_current, (retail_current, online_current, wholesale_current))),
            (2, (revenue_prior, cogs_prior, gross_prior, sga_prior, dep_prior, op_prior, int_prior, pre_prior, tax_prior, net_prior, (retail_prior, online_prior, wholesale_prior)))):
        del col
        sums += [{"kind": "sum", "terms": [["+", k(p)] for p in parts], "equals": k(rev)},
                 {"kind": "sum", "terms": [["+", k(rev)], ["-", k(cogs)]], "equals": k(gross)},
                 {"kind": "sum", "terms": [["+", k(gross)], ["-", k(sga)], ["-", k(dep)]], "equals": k(op)},
                 {"kind": "sum", "terms": [["+", k(op)], ["-", k(intr)]], "equals": k(pre)},
                 {"kind": "sum", "terms": [["+", k(pre)], ["-", k(tax)]], "equals": k(net)}]
    cash, receivables, inventory, prepaid = 48211, 9874, 118430, 6512
    ppe, leases, goodwill = 96204, 141880, 12650
    assets = cash + receivables + inventory + prepaid + ppe + leases + goodwill
    payables, accrued, current_lease, debt, lease_liab = 41207, 22918, 18406, 38000, 129774
    equity = assets - (payables + accrued + current_lease + debt + lease_liab)
    balance = table("t4", [
        ["", "Dec 31, 2025"],
        ["Cash and cash equivalents", k(cash)], ["Accounts receivable, net", k(receivables)], ["Merchandise inventories", k(inventory)],
        ["Prepaid expenses and other", k(prepaid)], ["Property and equipment, net", k(ppe)], ["Operating lease right-of-use assets", k(leases)],
        ["Goodwill", k(goodwill)], ["Total assets", k(assets)],
        ["Accounts payable", k(payables)], ["Accrued liabilities", k(accrued)], ["Current operating lease liabilities", k(current_lease)],
        ["Long-term debt", k(debt)], ["Long-term operating lease liabilities", k(lease_liab)], ["Shareholders’ equity", k(equity)],
        ["Total liabilities and equity", k(assets)],
    ], rendering="borderless", caption="Condensed consolidated balance sheet ($ thousands)", align=["l", "r"], widths=[70, 30], total_rows=[8, 15])
    sums += [{"kind": "column_sum", "table": "t4", "columns": [1], "label_column": 0, "total_label": "Total assets"},
             {"kind": "sum", "terms": [["+", k(v)] for v in (payables, accrued, current_lease, debt, lease_liab, equity)], "equals": k(assets)},
             {"kind": "column_sum", "table": "t3", "columns": [3, 4], "label_column": 0, "total_label": "Total retail"}]
    spec = {"title": "Net revenue by channel ($ millions)", "categories": ["FY2021", "FY2022", "FY2023", "FY2024", "FY2025"],
            "series": [("Retail", [151.2, 171.8, 189.4, retail_prior / 1000, retail_current / 1000]),
                       ("Online", [38.6, 47.1, 55.0, online_prior / 1000, online_current / 1000]),
                       ("Wholesale", [17.9, 19.4, 21.3, wholesale_prior / 1000, wholesale_current / 1000])],
            "max": 300, "ticks": 6, "tick_format": lambda v: f"{v:.0f}"}
    emissions = {"title": "Scope 1 and 2 emissions (t CO₂e)", "categories": ["2021", "2022", "2023", "2024", "2025"],
                 "series": [("Stores", [4120, 3980, 3615, 3240, 2890]), ("Distribution", [1460, 1415, 1302, 1188, 1043])],
                 "max": 5000, "ticks": 5, "tick_format": lambda v: f"{v:,.0f}"}
    dash = {"brand": "Northwind Ridge", "nav": ["Overview", "Stores", "Online", "Loyalty", "Reports"], "title": "Loyalty program — FY2025",
            "range": "Jan 1 – Dec 31, 2025", "kpis": [("Active members", "412,906", "+18.4%"), ("Repeat rate", "57.2%", "+3.1 pts"),
                                                       ("Avg. basket", "$84.17", "+$2.40"), ("Unsubscribe", "0.8%", "−0.2 pts")],
            "series": [31, 33, 32, 36, 38, 41, 44, 43, 47, 51, 55, 60], "series_title": "Monthly active members (thousands)",
            "table_title": "Top regions", "rows": [["Region", "Members", "Share"], ["Pacific Northwest", "158,320", "38.3%"],
                                                   ["Mountain West", "131,774", "31.9%"], ["Southwest", "61,045", "14.8%"],
                                                   ["Canada and Japan", "61,767", "15.0%"]]}
    pages = [
        [P("2025 ANNUAL REPORT", "kicker"),
         H(1, "Northwind Ridge Outfitters, Inc."),
         P("Gear for the long way round — thirty-eight stores, one trail community", "lead"),
         photo("f1", ["mountain-lake", "park-path"], ["landscape"], {"mountain-lake": "Lake Josephine at first light, the view on the cover of our 2025 catalog."},
               "The trail ahead.", "none", width="100%"),
         H(2, "2025 at a glance"),
         table("t1", [["", "FY2025", "FY2024", "Change"], ["Net revenue ($ thousands)", k(revenue_current), k(revenue_prior), f"+{(revenue_current - revenue_prior) / revenue_prior * 100:.1f}%"],
                      ["Operating income ($ thousands)", k(op_current), k(op_prior), f"+{(op_current - op_prior) / op_prior * 100:.1f}%"],
                      ["Diluted earnings per share", "$1.87", "$1.52", "+23.0%"], ["Stores at year end", "38", "35", "+3"],
                      ["Loyalty members", "412,906", "348,771", "+18.4%"]], rendering="borderless", align=["l", "r", "r", "r"], widths=[46, 18, 18, 18])],
        [H(2, "Letter to our shareholders"),
         P("Dear fellow shareholders,", ""),
         P("When we opened our first store in a converted feed warehouse in Hood River in 2008, we promised to sell only what we would "
           "carry ourselves. Seventeen years later that promise still decides what goes on our shelves, and in 2025 it carried us "
           f"to record net revenue of ${revenue_current / 1000:,.1f} million, up {(revenue_current - revenue_prior) / revenue_prior * 100:.1f}% from the prior year."),
         P("Three things stood out. First, our stores kept their edge: comparable-store sales rose 6.2% even as we absorbed a wet spring "
           "that delayed the camping season by almost a month in the Pacific Northwest. Second, online revenue grew 22.3%, helped by "
           "buy-online-pick-up-in-store, which now accounts for 31% of web orders. Third, we took our first steps abroad, and the "
           "results surprised even the optimists in the room."),
         P("Our Kyoto Arashiyama store (京都嵐山店), opened in April 2023, finished its second full year profitable, and in September "
           "we opened in Sapporo’s Ōdōri district (札幌大通) with a rental program for winter gear designed with our partner "
           "Hokkaidō Yama Kōbō (北海道山工房). Calgary and Vancouver continue to build steadily."),
         P("We also made choices that cost us in the short term. We exited two leases in suburban malls where foot traffic no longer "
           "justified the rent, and we raised starting pay in every store to at least $19.50 an hour. Gross margin still expanded by "
           "110 basis points because full-price sell-through improved and we cut freight costs by consolidating inbound containers "
           "through the Port of Tacoma."),
         P("Looking ahead, we plan to open four stores in 2026, all in towns where our loyalty members already drive more than an hour "
           "to shop with us. We will keep our balance sheet conservative: we ended the year with $48.2 million in cash and repaid "
           "$12.0 million of our term loan."),
         P("Thank you for your trust, and see you on the trail."),
         P("*Margaret “Peg” Ostrowski*\nChair and Chief Executive Officer\nPortland, Oregon, February 24, 2026", "meta")],
        [H(2, "Business review"),
         chart("f2", "bar", spec, "Figure 1: Net revenue by channel, FY2021–FY2025", raster=False, width="88%"),
         chart_table("c1", "Fiscal year", spec, lambda v: f"{v:.1f}"),
         photo("f3", ["hand-tools", "factory-machinery"], ["workshop", "tools"], {"hand-tools": "The repair bench at our Bend Old Mill store fixed 9,400 items in 2025."},
               "Our repair benches kept 9,400 items in use in 2025.", "right", width="38%"),
         P("**Stores.** Retail sales were driven by apparel and footwear, which together made up 54% of store revenue. Hard goods "
           "were flat, with strength in packrafts and trekking poles offset by weaker tent sales after two very strong years."),
         P("**Online.** Our rebuilt website went live in March. Conversion rose from 2.4% to 2.9%, and average delivery time fell to "
           "2.6 days. Returns stayed below 9% of online revenue thanks to more detailed size guides."),
         P("**Repair and resale.** The Second Ascent program, which buys back used gear for store credit, processed 27,300 items. "
           "Resale revenue is included in retail stores and carried a gross margin of 61%.")],
        [H(2, "Loyalty and community"),
         P("Membership in Trail Club, our free loyalty program, grew 18.4% to 412,906 active members. Members accounted for 68% of "
           "revenue, and their repeat-purchase rate improved to 57.2%. The screenshot below is from the dashboard our store managers "
           "review every Monday morning."),
         screenshot("f4", "dashboard", dash, "Figure 2: Trail Club dashboard as of December 31, 2025 (internal reporting tool)", width="96%"),
         P("Through the Northwind Ridge Foundation we granted $1.14 million to 63 trail, river and youth-outdoors organizations, "
           "including the Blue Mountains Trail Crew and Juntos al Aire Libre in Salt Lake City. Employees logged 11,820 volunteer hours."),
         box("sidebar", "Every store hosts a monthly “fix-it night” where staff and members repair zippers, seams and stove valves "
             "for free. In 2025 the busiest night was in Missoula, with 141 repairs in three hours.", title="Fix-it nights", cls="wide")],
        [income,
         P("Fiscal 2025 and fiscal 2024 each comprised 52 weeks ended on the Saturday nearest December 31. Amounts may not add "
           "across due to rounding to thousands; all subtotals shown are computed from the rounded figures.", "small"),
         H(2, "Management’s discussion of results"),
         P(f"Gross profit increased to ${gross_current / 1000:,.1f} million, or {gross_current / revenue_current * 100:.1f}% of net revenue, compared with "
           f"{gross_prior / revenue_prior * 100:.1f}% in fiscal 2024. The improvement reflects lower inbound freight, fewer clearance markdowns "
           "and a higher share of private-label apparel."),
         P(f"Selling, general and administrative expenses were {sga_current / revenue_current * 100:.1f}% of net revenue. Store wage increases added about "
           "$3.1 million, more than offset by lower marketing spend as we shifted from paid search to member email.")],
        [note_segments[0]],
        [note_segments[1],
         P("Stores opened in 2024 or 2025 are excluded from comparable-store sales until they complete 13 full fiscal months. "
           "Kyoto, Sapporo, Vancouver and Calgary revenue is translated at average exchange rates for each period.", "small"),
         balance],
        [H(2, "Sustainability"),
         chart("f5", "line", emissions, "Figure 3: Scope 1 and 2 emissions, 2021–2025", raster=True, width="80%"),
         chart_table("c2", "Year", emissions, lambda v: f"{v:,.0f}"),
         P("Emissions from our stores and distribution center fell 11.1% in 2025, mainly because 21 stores now buy renewable "
           "electricity through utility green-tariff programs. Our target is a 50% reduction from the 2021 baseline by 2030; we are "
           "currently 30.6% below it."),
         L(["Packaging: 94% of online orders shipped in recycled or reusable mailers (2024: 81%).",
            "Product: 38% of apparel units used recycled or responsibly sourced fibers.",
            "Waste: the Tacoma distribution center diverted 87% of waste from landfill.",
            "People: 44% of store managers are women; voluntary turnover fell to 29% from 36%."])],
        [H(2, "Board of directors"),
         table("t5", [["Director", "Role", "Since"], ["Margaret Ostrowski", "Chair and Chief Executive Officer", "2008"],
                      ["Daniel Whitehorse", "Lead Independent Director", "2015"], ["Keiko Nakamura-Reyes (中村・レジェス 恵子)", "Audit Committee Chair", "2019"],
                      ["Tomás Echeverría", "Compensation Committee Chair", "2017"], ["Priya Raghunathan", "Director", "2022"],
                      ["Ingrid Solberg", "Director", "2024"]], rendering="borderless", widths=[42, 42, 16]),
         H(2, "Shareholder information"),
         P("**Annual meeting.** The annual meeting of shareholders will be held virtually on May 14, 2026, at 9:00 a.m. Pacific Time "
           "at [meetnow.example/NWRO2026](https://meetnow.example/NWRO2026)."),
         P("**Stock listing.** Our common stock trades on the Nasdaq Global Select Market under the symbol NWRO."),
         P("**Investor relations.** Hannah Brisbois, ir@northwindridge.example, +1 503-555-0187."),
         box("footnote", "¹ Comparable-store sales and adjusted measures are non-GAAP financial measures; reconciliations are included in our Form 10-K."),
         box("footnote", "² Loyalty member counts include members with at least one purchase in the trailing 12 months.")],
    ]
    return {
        "template": "annual_report", "page_size": "Letter", "languages": ["en-US", "ja"],
        "metadata": {"title": "Northwind Ridge Outfitters, Inc. — 2025 Annual Report", "author": "Northwind Ridge Outfitters, Inc.",
                     "subject": "Annual report to shareholders for fiscal year 2025", "keywords": ["annual report", "FY2025", "retail", "outdoor"],
                     "lang": "en-US", "created": "2026-03-06T17:00:00Z"},
        "theme": {"accent": "#25523b", "body_font": "'Noto Serif'", "heading_font": "'Noto Sans'", "font_size": "9.6pt",
                  "margins": "16mm 17mm 18mm 17mm"},
        "running_header": "Northwind Ridge Outfitters · 2025 Annual Report", "running_footer": "{page}", "pages": pages,
        "arithmetic": sums,
    }


# ---------------------------------------------------------------- w2-quarterly-de-02 (libreoffice tagged, de-DE)


def quarterly_de() -> dict[str, Any]:
    """German interim report with an order-backlog table continuing over two pages."""
    eur = lambda v: number(v / 10, "de", 1)  # noqa: E731 - values in tenths of Mio. €
    projects = [
        ("Prüfstand Getriebe E-Achse", "Zwickau", "Automotive"), ("Spindelgehäuse Baureihe SG-40", "Heilbronn", "Werkzeugmaschinen"),
        ("Messzelle Batteriemodul", "Salzgitter", "Automotive"), ("Linearführung Halbleiter-Handling", "Dresden", "Elektronik"),
        ("Hydraulikblock Erntemaschine", "Harsewinkel", "Landtechnik"), ("Präzisionswelle Windgetriebe", "Rheine", "Energie"),
        ("Greifersystem Pharma-Abfüllung", "Biberach", "Medizintechnik"), ("Lagergehäuse Straßenbahn", "Bautzen", "Bahntechnik"),
        ("Kühlplatte Leistungselektronik", "Regensburg", "Elektronik"), ("Dosiereinheit Klebstoff", "Ulm", "Automotive"),
        ("Rotornabe Kleinwindanlage", "Husum", "Energie"), ("Implantat-Fräsvorrichtung", "Tuttlingen", "Medizintechnik"),
        ("Achsträger Prototyp", "Ingolstadt", "Automotive"), ("Montagelinie Wärmepumpe", "Kassel", "Energie"),
        ("Drehtisch Laserzelle", "Ditzingen", "Werkzeugmaschinen"), ("Bremsprüfstand Güterwagen", "Kassel", "Bahntechnik"),
        ("Sensorhalter Mähdrescher", "Harsewinkel", "Landtechnik"), ("Vakuumkammer Beschichtung", "Alzenau", "Elektronik"),
        ("Gelenkwelle Schienenfahrzeug", "Salzgitter", "Bahntechnik"), ("Endoskop-Antriebseinheit", "Tuttlingen", "Medizintechnik"),
        ("Getriebedeckel Kleinserie", "Wolfsburg", "Automotive"), ("Spannvorrichtung Turbinenschaufel", "Mülheim", "Energie"),
        ("Wafer-Träger Keramik", "Jena", "Elektronik"), ("Pumpengehäuse Bewässerung", "Osnabrück", "Landtechnik"),
        ("Schwenkkopf 5-Achs-Fräse", "Pfronten", "Werkzeugmaschinen"), ("Gehäuse Infusionspumpe", "Melsungen", "Medizintechnik"),
        ("Kupplungsflansch Schiffsantrieb", "Kiel", "Energie"), ("Batterierahmen Nutzfahrzeug", "Wörth", "Automotive"),
        ("Antriebsritzel Rolltreppe", "Hameln", "Bahntechnik"), ("Messarm Koordinatenmessgerät", "Oberkochen", "Elektronik"),
    ]
    r = rng("quarterly-de")
    rows, total_order, total_backlog = [], 0, 0
    for name, site, sector in projects:
        order = r.randrange(8, 96)  # tenths of Mio. €
        delivered = r.randrange(0, order)
        backlog = order - delivered
        total_order += order
        total_backlog += backlog
        rows.append([name, site, sector, eur(order), eur(delivered), eur(backlog)])
    total_delivered = total_order - total_backlog
    segments = continued("t3", [["Projekt", "Standort Kunde", "Branche", "Auftragswert", "Abgerechnet", "Auftragsbestand"]], rows, [23, 7],
                         caption="Tabelle 3: Auftragsbestand nach Projekten zum 30.06.2026 (in Mio. €)",
                         continued_caption="Tabelle 3 (Fortsetzung): Auftragsbestand nach Projekten (in Mio. €)",
                         align=["l", "l", "l", "r", "r", "r"], widths=[34, 16, 18, 11, 10, 11],
                         total=[["Summe", "", "", eur(total_order), eur(total_delivered), eur(total_backlog)]])
    revenue = [(412, 389), (118, 103), (67, 71), (59, 48)]  # Q2 2026 vs Q2 2025, in Mio € tenths? (use tenths)
    seg_rows = [["Maschinenbau", eur(revenue[0][0]), eur(revenue[0][1])], ["Automotive", eur(revenue[1][0]), eur(revenue[1][1])],
                ["Medizintechnik", eur(revenue[2][0]), eur(revenue[2][1])], ["Energie und Bahntechnik", eur(revenue[3][0]), eur(revenue[3][1])]]
    rev_now, rev_prev = sum(a for a, _ in revenue), sum(b for _, b in revenue)
    seg_rows.append(["Konzernumsatz", eur(rev_now), eur(rev_prev)])
    material, staff, other, depreciation = 287, 196, 71, 38
    ebit = rev_now - material - staff - other - depreciation
    financial = 6
    ebt = ebit - financial
    taxes = 31
    net = ebt - taxes
    guv = table("t2", [["", "Q2/2026", "Q2/2025"], *seg_rows],
                caption="Tabelle 2: Umsatz nach Segmenten (in Mio. €)", align=["l", "r", "r"], widths=[50, 25, 25], total_rows=[5])
    guv2 = table("t4", [["Gewinn- und Verlustrechnung Q2/2026", "Mio. €"], ["Umsatzerlöse", eur(rev_now)], ["Materialaufwand", "−" + eur(material)],
                        ["Personalaufwand", "−" + eur(staff)], ["Sonstige betriebliche Aufwendungen", "−" + eur(other)],
                        ["Abschreibungen", "−" + eur(depreciation)], ["EBIT", eur(ebit)], ["Finanzergebnis", "−" + eur(financial)],
                        ["Ergebnis vor Steuern", eur(ebt)], ["Ertragsteuern", "−" + eur(taxes)], ["Konzernergebnis", eur(net)]],
                 rendering="borderless", align=["l", "r"], widths=[70, 30], total_rows=[6, 10])
    spec = {"title": "Auftragseingang je Quartal (Mio. €)", "categories": ["Q3/25", "Q4/25", "Q1/26", "Q2/26"],
            "series": [("Auftragseingang", [61.4, 58.9, 70.2, 74.8]), ("Umsatz", [64.0, 66.3, 63.1, 65.6])], "max": 90, "ticks": 3,
            "tick_format": lambda v: number(v, "de", 0)}
    pages = [
        [P("Albrecht Feinmechanik AG", "brand"),
         H(1, "Halbjahresfinanzbericht zum 30. Juni 2026"),
         P("Konzern-Zwischenmitteilung für das zweite Quartal und das erste Halbjahr 2026 · Schwäbisch Gmünd, 6. August 2026", "small"),
         H(2, "Das Wichtigste in Kürze"),
         L([f"Konzernumsatz im zweiten Quartal {eur(rev_now)} Mio. € (Vorjahr {eur(rev_prev)} Mio. €), ein Plus von {number((rev_now - rev_prev) / rev_prev * 100, 'de', 1)} %",
            f"EBIT {eur(ebit)} Mio. €; EBIT-Marge {number(ebit / rev_now * 100, 'de', 1)} % (Vorjahr 4,6 %)",
            "Auftragseingang mit 74,8 Mio. € auf Rekordniveau – getragen von Elektronik und Medizintechnik",
            "Prognose für das Gesamtjahr 2026 bestätigt: Umsatz zwischen 255 und 270 Mio. €"]),
         H(2, "Vorwort des Vorstands"),
         P("Sehr geehrte Aktionärinnen und Aktionäre,"),
         P("das zweite Quartal hat gezeigt, dass sich unsere Ausrichtung auf anspruchsvolle Kleinserien auszahlt. Während die "
           "Nachfrage der Automobilzulieferer weiterhin schwankt, gewinnen wir in der Medizintechnik und bei Ausrüstern der "
           "Halbleiterfertigung Aufträge, die höhere Präzision und kürzere Lieferzeiten verlangen. Unser neues Werk in Görlitz hat "
           "im Mai die Serienfertigung aufgenommen und liefert bereits Wafer-Träger aus technischer Keramik."),
         P("Zugleich bleiben wir vorsichtig: Die Energie­kosten liegen weiterhin deutlich über dem Niveau von 2021, und die "
           "Instand­haltungs­aufwendungen für unseren Maschinen­park steigen. Wir investieren deshalb gezielt in "
           "Automatisierung und Wärmerückgewinnung."),
         P("*Dr. Friederike Albrecht-Yılmaz, Vorstandsvorsitzende · Jörg Brandstätter, Finanzvorstand*", "small")],
        [H(2, "Geschäftsverlauf"),
         chart("f1", "bar", spec, "Abbildung 1: Auftragseingang und Umsatz der letzten vier Quartale", raster=True, width_cm=13.5),
         chart_table("c1", "Quartal", spec, lambda v: number(v, "de", 1)),
         P("Der Auftragseingang erreichte mit 74,8 Mio. € einen neuen Höchststand. Wesentlich dazu beigetragen haben zwei "
           "Rahmenverträge mit Herstellern von Anlagen für die Halbleiterfertigung in Dresden und Jena sowie ein Großauftrag für "
           "Gehäuse von Infusionspumpen. Die Book-to-Bill-Ratio lag bei 1,14."),
         guv,
         P("Im Segment Maschinenbau stieg der Umsatz um 5,9 %; Preisanpassungen aus dem Vorjahr wirkten erstmals ganzjährig. "
           "Automotive profitierte von Prototypenaufträgen für Batterierahmen, während Serienabrufe für Getriebedeckel um "
           "rund ein Fünftel zurückgingen.")],
        [H(2, "Ertragslage"),
         guv2,
         P("Die Materialaufwandsquote sank auf 43,8 % (Vorjahr 45,2 %), da wir Stahl- und Aluminiumpreise für das zweite "
           "Halbjahr frühzeitig abgesichert haben. Der Personalaufwand erhöhte sich tarifbedingt und durch 46 zusätzliche "
           "Beschäftigte am Standort Görlitz. Zum Stichtag beschäftigte der Konzern 1.284 Mitarbeiterinnen und Mitarbeiter."),
         box("callout", "Das EBIT enthält Anlaufkosten für das Werk Görlitz in Höhe von 1,9 Mio. €. Bereinigt um diesen Effekt "
             "hätte die EBIT-Marge 6,2 % betragen.", title="Sondereffekt Werksanlauf"),
         photo("f2", ["factory-machinery", "hand-tools"], ["industry", "machinery"], {"factory-machinery": "Fünfachs-Bearbeitungszentrum im neuen Werk Görlitz"},
               "Fertigung im Werk Görlitz", "none", width_cm=10.5)],
        [segments[0]],
        [segments[1],
         P("Der Auftragsbestand umfasst alle verbindlich erteilten, noch nicht abgerechneten Aufträge. Rahmenverträge sind nur "
           "mit den bereits abgerufenen Mengen enthalten.¹", "small"),
         H(2, "Finanz- und Vermögenslage"),
         P("Der operative Cashflow betrug im ersten Halbjahr 14,2 Mio. € (Vorjahr 11,7 Mio. €). Die Investitionen von 18,9 Mio. € "
           "entfielen überwiegend auf das Werk Görlitz. Die Nettofinanzverschuldung stieg auf 42,3 Mio. €; die Eigenkapitalquote "
           "liegt mit 47,1 % weiterhin auf solidem Niveau.")],
        [H(2, "Chancen, Risiken und Ausblick"),
         P("Gegenüber der Darstellung im Geschäftsbericht 2025 haben sich die Chancen und Risiken nicht wesentlich verändert. "
           "Ein Risiko sehen wir weiterhin in der Abhängigkeit von wenigen Großkunden der Automobilindustrie, auf die 21 % des "
           "Umsatzes entfallen."),
         L(["Umsatz 2026: 255 bis 270 Mio. € (bisher unverändert)", "EBIT-Marge 2026: 5,0 bis 6,0 %",
            "Investitionen 2026: rund 32 Mio. €, davon 24 Mio. € für Görlitz", "Dividendenpolitik: Ausschüttung von 30 bis 40 % des Konzernergebnisses"]),
         H(2, "Finanzkalender"),
         table("t5", [["Termin", "Ereignis"], ["5. November 2026", "Quartalsmitteilung Q3/2026"], ["24. November 2026", "Deutsches Eigenkapitalforum, Frankfurt am Main"],
                      ["25. März 2027", "Geschäftsbericht 2026"], ["12. Mai 2027", "Hauptversammlung, Schwäbisch Gmünd"]],
               rendering="borderless", widths=[30, 70]),
         P("Investor Relations: Sabine Kowalczyk, Telefon +49 7171 555-0240, [ir@albrecht-feinmechanik.example](mailto:ir@albrecht-feinmechanik.example)", "small"),
         box("footnote", "¹ Auftragswerte ohne Umsatzsteuer; Fremdwährungsaufträge zum Stichtagskurs umgerechnet."),
         box("footnote", "² Alle Zahlen ungeprüft. Rundungsdifferenzen sind möglich.")],
    ]
    sums = [{"kind": "column_sum", "table": "t3", "columns": [3, 4, 5], "label_column": 0, "total_label": "Summe"},
            {"kind": "column_sum", "table": "t2", "columns": [1, 2], "label_column": 0, "total_label": "Konzernumsatz"},
            {"kind": "sum", "terms": [["+", eur(rev_now)], ["-", eur(material)], ["-", eur(staff)], ["-", eur(other)], ["-", eur(depreciation)]], "equals": eur(ebit)},
            {"kind": "sum", "terms": [["+", eur(ebit)], ["-", eur(financial)], ["-", eur(taxes)]], "equals": eur(net)}]
    return {
        "template": "quarterly_report", "page_size": "A4", "languages": ["de-DE", "tr"], "tagged": True,
        "metadata": {"title": "Halbjahresfinanzbericht zum 30. Juni 2026 – Albrecht Feinmechanik AG", "author": "Albrecht Feinmechanik AG, Investor Relations",
                     "subject": "Zwischenbericht Q2 und H1 2026", "keywords": ["Halbjahresfinanzbericht", "Q2 2026", "Auftragsbestand"],
                     "lang": "de-DE", "created": "2026-08-06T05:30:00Z"},
        "theme": {"accent": "#8a2b2b", "lo_size": "9.5pt", "lo_font": "Noto Serif", "lo_heading_font": "Noto Sans", "content_cm": 17.0},
        "running_header": "Albrecht Feinmechanik AG · Halbjahresfinanzbericht 2026", "running_footer": "Seite {page} von {pages}",
        "pages": pages, "arithmetic": sums,
    }


# ---------------------------------------------------------------- w2-quarterly-ja-03 (pylopdf, ja)


def quarterly_ja() -> dict[str, Any]:
    """Japanese quarterly earnings summary (決算短信) with a store sales table over two pages."""
    m = lambda v: f"{v:,}"  # noqa: E731 - 百万円
    tri = lambda v: f"{v:,}" if v >= 0 else f"△{-v:,}"  # noqa: E731
    stores = [
        ("札幌大通店", "北海道", "2009年"), ("仙台一番町店", "宮城県", "2011年"), ("盛岡大通店", "岩手県", "2016年"), ("新潟古町店", "新潟県", "2014年"),
        ("金沢香林坊店", "石川県", "2012年"), ("大宮西口店", "埼玉県", "2008年"), ("柏の葉店", "千葉県", "2019年"), ("吉祥寺店", "東京都", "2005年"),
        ("二子玉川店", "東京都", "2013年"), ("町田店", "東京都", "2010年"), ("横浜みなとみらい店", "神奈川県", "2015年"), ("藤沢店", "神奈川県", "2018年"),
        ("静岡呉服町店", "静岡県", "2017年"), ("名古屋栄店", "愛知県", "2007年"), ("岐阜柳ケ瀬店", "岐阜県", "2021年"), ("京都河原町店", "京都府", "2006年"),
        ("梅田茶屋町店", "大阪府", "2004年"), ("心斎橋店", "大阪府", "2012年"), ("神戸元町店", "兵庫県", "2010年"), ("岡山表町店", "岡山県", "2020年"),
        ("広島本通店", "広島県", "2011年"), ("松山大街道店", "愛媛県", "2022年"), ("高松丸亀町店", "香川県", "2023年"), ("福岡天神店", "福岡県", "2008年"),
        ("熊本下通店", "熊本県", "2016年"), ("鹿児島天文館店", "鹿児島県", "2019年"), ("那覇国際通り店", "沖縄県", "2024年"),
        ("オンラインストア", "—", "2003年"),
    ]
    r = rng("quarterly-ja")
    rows, prev_total, cur_total = [], 0, 0
    for name, prefecture, opened in stores:
        prev = r.randrange(180, 920) if name != "オンラインストア" else 4120
        cur = int(prev * r.uniform(0.94, 1.15)) if name != "那覇国際通り店" else prev + 212
        prev_total += prev
        cur_total += cur
        change = (cur - prev) / prev * 100
        rows.append([name, prefecture, opened, m(prev), m(cur), f"{'' if change >= 0 else '△'}{abs(change):.1f}%"])
    segments = continued("t2", [["店舗", "所在地", "開店", "前年同期", "当第3四半期", "増減率"]], rows, [24, 4],
                         caption="【店舗別売上高】（単位：百万円）", continued_caption="【店舗別売上高】（続き）（単位：百万円）",
                         align=["l", "l", "c", "r", "r", "r"], widths=[28, 15, 11, 16, 17, 13],
                         total=[["合計", "", "", m(prev_total), m(cur_total), f"{(cur_total - prev_total) / prev_total * 100:.1f}%"]])
    sales, sales_prev = cur_total, prev_total
    op, op_prev = int(sales * 0.071), int(sales_prev * 0.064)
    ordinary, ordinary_prev = op + 38, op_prev + 22
    net, net_prev = int(ordinary * 0.67), int(ordinary_prev * 0.66)
    pct = lambda a, b: f"{(a - b) / b * 100:.1f}"  # noqa: E731
    results = table("t1", [["", "売上高", "営業利益", "経常利益", "親会社株主に帰属する四半期純利益"],
                           ["2026年3月期第3四半期", m(sales), m(op), m(ordinary), m(net)], ["増減率（％）", pct(sales, sales_prev), pct(op, op_prev), pct(ordinary, ordinary_prev), pct(net, net_prev)],
                           ["2025年3月期第3四半期", m(sales_prev), m(op_prev), m(ordinary_prev), m(net_prev)]],
                    caption="（1）連結経営成績（累計）（百万円未満切捨て）", align=["l", "r", "r", "r", "r"], widths=[28, 16, 16, 16, 24])
    current_assets, fixed_assets = 21843, 15207
    total_assets = current_assets + fixed_assets
    liabilities = 14692
    equity = total_assets - liabilities
    bs = table("t3", [["科目", "前連結会計年度", "当第3四半期"], ["流動資産", "20,118", m(current_assets)], ["固定資産", "14,736", m(fixed_assets)],
                      ["資産合計", "34,854", m(total_assets)], ["負債合計", "14,203", m(liabilities)], ["純資産合計", "20,651", m(equity)],
                      ["負債純資産合計", "34,854", m(total_assets)]],
               caption="（2）連結貸借対照表（要約）（単位：百万円）", align=["l", "r", "r"], widths=[40, 30, 30])
    monthly = {"title": "既存店前年同月比（％）", "categories": ["4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
               "series": [("売上高", [103.2, 104.8, 101.9, 106.4, 105.1, 107.3, 108.9, 109.6, 111.2]),
                          ("客数", [100.4, 101.7, 99.2, 102.8, 101.5, 103.0, 104.1, 104.8, 106.0])],
               "min": 95, "max": 115, "ticks": 4, "tick_format": lambda v: f"{v:.0f}"}
    pages = [
        [P("2026年3月期　第3四半期決算短信〔日本基準〕（連結）", "brand"),
         P("2026年2月6日", "right"),
         table("t0", [["項目", "内容"], ["上場会社名", "株式会社あおば生活雑貨"], ["コード番号", "3187（東証プライム）"],
                      ["代表者", "代表取締役社長　森川 理恵"], ["問合せ先責任者", "取締役管理本部長　石田 浩平（TEL 03-5555-0471）"],
                      ["URL", "https://aoba-zakka.example/ir"]], rendering="borderless", widths=[30, 70]),
         H(2, "1．2026年3月期第3四半期の連結業績（2025年4月1日～2025年12月31日）"),
         results,
         P(f"（注）当第3四半期連結累計期間の1株当たり四半期純利益は{net * 1000000 // 18420000:,}円、前年同期は{net_prev * 1000000 // 18420000:,}円であります。", "small"),
         H(2, "2．配当の状況"),
         P("年間配当金は1株当たり48円（中間24円、期末24円）を予定しており、前期から6円の増配となります。直近に公表されている配当予想からの修正はありません。")],
        [H(2, "3．当四半期決算に関する定性的情報"),
         H(3, "（1）経営成績に関する説明"),
         P("当第3四半期連結累計期間におけるわが国経済は、雇用・所得環境の改善やインバウンド需要の拡大により緩やかな回復基調で推移しました。"
           "一方で、食料品やエネルギー価格の上昇が続き、生活必需品以外の消費には慎重な姿勢がみられました。"),
         P("このような環境のもと、当社グループは「長く使える、ちょうどいい道具」をテーマに、木製キッチン用品やリネン製品などのプライベートブランド商品の"
           "開発を強化しました。秋冬シーズンには土鍋や湯たんぽなどの季節商品が好調に推移し、既存店売上高は前年同期比6.8％増となりました。"),
         P("店舗展開につきましては、2024年11月に開店した那覇国際通り店が通期で寄与したほか、高松丸亀町店の改装を実施しました。"
           "当第3四半期末の店舗数は27店舗（前期末比増減なし）であります。"),
         H(3, "（2）財政状態に関する説明"),
         P("当第3四半期末の総資産は、前連結会計年度末に比べ22億円増加しました。主な要因は、年末商戦に向けた商品の積み増しによる棚卸資産の増加であります。"),
         H(3, "（3）連結業績予想などの将来予測情報に関する説明"),
         P("2025年5月13日に公表いたしました通期の連結業績予想に変更はありません。売上高は255億円、営業利益は18億円を見込んでおります。"),
         box("callout", "本資料に記載されている業績見通し等の将来に関する記述は、当社が現在入手している情報及び合理的であると判断する一定の前提に基づいており、"
             "実際の業績等は様々な要因により大きく異なる可能性があります。", title="将来予測に関する注意事項")],
        [segments[0]],
        [segments[1],
         P("（注）既存店とは開店後13か月を経過した店舗をいいます。オンラインストアの売上高には店舗受取分を含みません。", "small"),
         H(2, "4．四半期連結財務諸表及び主な注記"),
         bs,
         chart("f2", "line", monthly, "既存店売上高・客数の前年同月比（％）", raster=True, width="80%"),
         chart_table("c1", "月", monthly, lambda v: f"{v:.1f}")],
        [
         H(3, "（継続企業の前提に関する注記）"),
         P("該当事項はありません。"),
         H(3, "（株主資本の金額に著しい変動があった場合の注記）"),
         P("該当事項はありません。"),
         H(3, "（セグメント情報）"),
         P("当社グループは生活雑貨の企画・販売事業の単一セグメントであるため、記載を省略しております。"),
         H(3, "（追加情報）"),
         P("当社は2025年10月より、物流拠点を埼玉県加須市の新センターへ集約いたしました。移転に伴う一時費用1億2,400万円は販売費及び一般管理費に計上しております。"
           "新センターでは自動倉庫を導入しており、出荷能力は旧拠点比で約1.6倍となる見込みです。"),
         H(3, "（重要な後発事象）"),
         P("2026年1月20日開催の取締役会において、株式会社ふたば木工（岐阜県高山市）の全株式を取得し子会社化することを決議いたしました。"
           "取得価額は8億6,000万円であり、2026年3月31日に株式譲渡を実行する予定であります。"),
         table("t4", [["地域", "前期末", "当第3四半期末"], ["北海道・東北", "3", "3"], ["関東", "8", "8"], ["中部・北陸", "4", "4"],
                      ["近畿", "4", "4"], ["中国・四国", "4", "4"], ["九州・沖縄", "4", "4"], ["合計", "27", "27"]],
               rendering="borderless", caption="【地域別店舗数】（単位：店）", align=["l", "r", "r"], widths=[40, 30, 30]),
         photo("f1", ["bread-bakery", "coffee-cup", "potted-plants"], ["product"], {"coffee-cup": "プライベートブランド「AOBA DAYS」のマグカップ"},
               "プライベートブランド商品", "none", width="42%")],
    ]
    sums = [{"kind": "column_sum", "table": "t2", "columns": [3, 4], "label_column": 0, "total_label": "合計"},
            {"kind": "column_sum", "table": "t4", "columns": [1, 2], "label_column": 0, "total_label": "合計"},
            {"kind": "sum", "terms": [["+", m(current_assets)], ["+", m(fixed_assets)]], "equals": m(total_assets)},
            {"kind": "sum", "terms": [["+", m(liabilities)], ["+", tri(equity)]], "equals": m(total_assets)}]
    return {
        "template": "quarterly_report", "page_size": "A4", "languages": ["ja"],
        "metadata": {"title": "2026年3月期 第3四半期決算短信〔日本基準〕（連結）", "author": "株式会社あおば生活雑貨",
                     "subject": "第3四半期決算短信", "keywords": ["決算短信", "第3四半期", "2026年3月期"], "lang": "ja", "created": "2026-02-06T06:00:00Z"},
        "theme": {"accent": "#2c4a7a", "py_size": 9.2},
        "running_footer": "株式会社あおば生活雑貨（3187）2026年3月期 第3四半期決算短信　— {page} —", "pages": pages, "arithmetic": sums,
    }


# ---------------------------------------------------------------- w2-annual-es-04 (reportlab, es-ES, Standard 14 Times)


def annual_es() -> dict[str, Any]:
    """Spanish agricultural cooperative annual report; member settlements kg x price = amount over two pages."""
    eur = lambda c: money(c, "es").replace(f"{NB}€", "")  # noqa: E731
    members = ["Aguilar Sánchez, Rosa María", "Alcaraz Pérez, Juan Antonio", "Andúgar Molina, José", "Bastida Ruiz, Encarnación",
               "Belmonte López, Francisco", "Cánovas Ortiz, Pedro", "Carrasco Lorca, Antonia", "Cascales Navarro, Diego",
               "Fernández Sáez, Mercedes", "Gallego Martínez, Ginés", "García Valero, Isabel", "Gómez Abellán, Salvador",
               "Hernández Pina, Ana Belén", "Ibáñez Tomás, Raimundo", "Jiménez Soler, Catalina", "Lajarín Ruiz, Andrés",
               "López Meseguer, Dolores", "Lorente Bernal, Pascual", "Marín Egea, Fuensanta", "Martínez Campillo, Bartolomé",
               "Meroño Cayuela, Ascensión", "Molina Sandoval, Tomás", "Navarro Ferrer, Josefa", "Ortuño Gil, Mariano",
               "Pardo Salinas, Juana", "Peñalver Ros, Alfonso", "Pujante García, Remedios", "Ros Martínez, Clemente",
               "Ruiz Abellán, Carmen", "Sánchez Lucas, Joaquín", "Soto Riquelme, Rosario", "Tornel Valverde, Benito",
               "Valverde Hernández, Maravillas", "Vicente Paredes, Lorenzo", "Zapata Gómez, Agustina"]
    crops = [("Limón Fino", 41), ("Limón Verna", 38), ("Naranja Navelina", 29), ("Mandarina Clemenules", 47), ("Pomelo Star Ruby", 52)]
    r = rng("annual-es")
    rows, total_kg, total_amount = [], 0, 0
    for name in members:
        crop, base = r.choice(crops)
        kg = r.randrange(18, 260) * 100
        price = base + r.randrange(-4, 6)  # céntimos/kg
        amount = kg * price
        total_kg += kg
        total_amount += amount
        rows.append([name, crop, number(kg, "es", 0), number(price / 100, "es", 3), eur(amount)])
    segments = continued("t3", [["Socio", "Variedad", "Kilos", "€/kg", "Importe liquidado"]], rows, [17, 18],
                         caption="Cuadro 3. Liquidaciones a socios de la campaña 2024/25", continued_caption="Cuadro 3. Liquidaciones a socios (continuación)",
                         align=["l", "l", "r", "r", "r"], widths=[38, 22, 12, 10, 18],
                         total=[["Total campaña", "", number(total_kg, "es", 0), "", eur(total_amount)]])
    ventas, subvenciones = 1268430000, 41250000
    ingresos = ventas + subvenciones
    liquidaciones, personal, suministros, amortizacion, otros = 982170000, 148920000, 63410000, 38200000, 52870000
    gastos = liquidaciones + personal + suministros + amortizacion + otros
    resultado = ingresos - gastos
    pyg = table("t2", [["Concepto", "2025"], ["Ventas de fruta y hortaliza", eur(ventas)], ["Subvenciones de explotación", eur(subvenciones)],
                       ["Total ingresos", eur(ingresos)], ["Liquidaciones a socios", eur(liquidaciones)], ["Gastos de personal", eur(personal)],
                       ["Suministros y transporte", eur(suministros)], ["Amortización del inmovilizado", eur(amortizacion)],
                       ["Otros gastos de explotación", eur(otros)], ["Total gastos", eur(gastos)], ["Resultado del ejercicio", eur(resultado)]],
                caption="Cuadro 2. Cuenta de pérdidas y ganancias abreviada (euros)", align=["l", "r"], widths=[65, 35], total_rows=[3, 9, 10])
    spec = {"title": "Kilos comercializados por variedad (toneladas)", "categories": ["Limón", "Naranja", "Mandarina", "Pomelo"],
            "series": [("2023/24", [14820, 6210, 4180, 920]), ("2024/25", [16040, 5730, 4890, 1105])], "max": 20000, "ticks": 4,
            "tick_format": lambda v: number(v, "es", 0)}
    sheet = {"title": "Entregas_campaña_2024-25.xlsx", "menu": ["Archivo", "Inicio", "Insertar", "Fórmulas", "Datos", "Revisar"],
             "cell": "E8", "formula": "=SUMA(E2:E7)", "tabs": ["Resumen", "Por socio", "Calidades"],
             "rows": [["Semana", "Limón", "Naranja", "Mandarina", "Total kg"], ["S41", "312.400", "88.150", "64.900", "465.450"],
                      ["S42", "355.800", "91.300", "102.420", "549.520"], ["S43", "401.250", "97.880", "118.300", "617.430"],
                      ["S44", "388.600", "104.700", "121.050", "614.350"], ["S45", "362.900", "99.240", "117.800", "579.940"],
                      ["S46", "340.150", "93.600", "96.230", "529.980"], ["Total", "2.161.100", "574.870", "620.700", "3.356.670"]],
             "numeric": [False, True, True, True, True], "selected_row": 8}
    pages = [
        [P("Cooperativa Agrícola Vega del Segura, S. Coop.", "brand"),
         H(1, "Informe anual 2025"),
         P("Campaña 2024/25 · Molina de Segura (Murcia)", "lead"),
         H(2, "Carta del presidente"),
         P("Estimados socios y socias:"),
         P("Cerramos una campaña que empezó con preocupación y terminó con alivio. Las lluvias de octubre llegaron tarde, pero "
           "llegaron, y la cosecha de limón Fino superó nuestras previsiones en un ocho por ciento. Gracias al esfuerzo de todos "
           "hemos podido liquidar a nuestros socios un precio medio superior al de la campaña anterior."),
         P("Este año hemos dado pasos importantes. Inauguramos la nueva línea de calibrado óptico en el almacén de Ceutí, que nos "
           "permite clasificar hasta 22 toneladas por hora y reducir los destríos. También firmamos un acuerdo de suministro de "
           "tres años con una cadena de supermercados alemana que valora especialmente nuestra certificación de producción integrada."),
         P("No todo ha sido fácil. El precio del agua del trasvase sigue siendo motivo de inquietud y los costes de transporte "
           "por carretera han aumentado de nuevo. La Asamblea General deberá decidir en junio si ampliamos la balsa de riego de "
           "Los Valientes, un proyecto que el Consejo Rector considera prioritario."),
         P("Un abrazo a todos,\n*Ginés Gallego Martínez*, presidente del Consejo Rector", "meta")],
        [H(2, "La campaña en cifras"),
         chart("f1", "bar", spec, "Gráfico 1. Kilos comercializados por variedad, campañas 2023/24 y 2024/25", raster=False, width_cm=14),
         chart_table("c1", "Variedad", spec, lambda v: number(v, "es", 0)),
         P("La cooperativa comercializó 27.765 toneladas, un 8,4 % más que la campaña anterior. El 71 % de la fruta se exportó, "
           "principalmente a Alemania, Francia y los Países Bajos. La mandarina Clemenules tuvo un comportamiento excelente gracias "
           "a la buena coloración y a un calibre medio superior al habitual."),
         photo("f2", ["aerial-farmland", "farm-field"], ["agriculture"], {"aerial-farmland": "Parcelas de socios en la huerta de Molina de Segura."},
               "Parcelas de socios en la Vega Media.", "none", width_cm=11)],
        [pyg,
         P("El resultado positivo del ejercicio se destinará, según propuesta del Consejo Rector, en un 20 % al Fondo de Reserva "
           "Obligatorio, en un 5 % al Fondo de Educación y Promoción y el resto a retornos cooperativos a los socios en proporción "
           "a la actividad realizada."),
         H(2, "Entregas semanales en el pico de campaña"),
         P("La siguiente captura procede de la hoja de control que el almacén de Ceutí comparte cada lunes con el Consejo Rector."),
         screenshot("f3", "spreadsheet", sheet, "Imagen 1. Hoja de entregas por semana (semanas 41 a 46)", width_cm=15),
         table("t5", sheet["rows"], rendering="screenshot", caption="Entregas por semana (kg)")],
        [segments[0]],
        [segments[1],
         P("Precio por kilo neto de destríos y aportación al fondo de comercialización. Los importes se abonaron por transferencia "
           "el 15 de enero de 2026.", "small")],
        [H(2, "Balance de situación resumido"),
         table("t4", [["Activo", "Euros", "Patrimonio neto y pasivo", "Euros"],
                      ["Inmovilizado material", "4.812.600,00", "Capital social", "1.240.000,00"],
                      ["Existencias", "318.450,00", "Fondos de reserva", "2.986.330,00"],
                      ["Deudores comerciales", "1.946.210,00", "Deudas con entidades de crédito", "1.618.400,00"],
                      ["Tesorería", "702.940,00", "Acreedores y socios", "1.935.470,00"],
                      ["Total activo", "7.780.200,00", "Total patrimonio neto y pasivo", "7.780.200,00"]],
               caption="Cuadro 4. Balance a 31 de diciembre de 2025", align=["l", "r", "l", "r"], widths=[30, 20, 30, 20], total_rows=[5]),
         H(2, "Producción sostenible"),
         L(["El 100 % de la superficie de los socios está certificada en producción integrada.",
            "La instalación fotovoltaica del almacén generó 412 MWh, el 38 % del consumo eléctrico.",
            "Se recuperaron 96 toneladas de envases de fitosanitarios a través del sistema SIGFITO.",
            "Se impartieron 14 cursos de formación con 286 asistentes."])],
        [H(2, "Órganos de gobierno"),
         table("t6", [["Cargo", "Nombre"], ["Presidente", "Ginés Gallego Martínez"], ["Vicepresidenta", "Isabel García Valero"],
                      ["Secretario", "Pascual Lorente Bernal"], ["Tesorera", "Dolores López Meseguer"], ["Vocales", "Clemente Ros Martínez, Catalina Jiménez Soler, Agustina Zapata Gómez"],
                      ["Interventor", "Andrés Lajarín Ruiz"], ["Gerente", "María José Belchí Ortega"]], rendering="borderless", widths=[30, 70]),
         H(2, "Calendario"),
         P("La Asamblea General Ordinaria se celebrará el sábado 13 de junio de 2026 a las 10.00 horas en primera convocatoria y a "
           "las 10.30 horas en segunda, en el salón de actos de la cooperativa (Ctra. de Alguazas, km 2,5, Molina de Segura)."),
         box("callout", "Las cuentas anuales completas y el informe de auditoría están a disposición de los socios en las oficinas "
             "de la cooperativa durante los quince días anteriores a la Asamblea.", title="Documentación"),
         box("footnote", "(1) Datos de la campaña 2024/25 (1 de septiembre de 2024 a 31 de agosto de 2025)."),
         box("footnote", "(2) Cifras de la cuenta de resultados auditadas por Cánovas y Asociados Auditores, S.L.P.")],
    ]
    sums = [{"kind": "line_items", "table": "t3", "quantity": 2, "unit_price": 3, "amount": 4, "decimal": ","},
            {"kind": "column_sum", "table": "t3", "columns": [2, 4], "label_column": 0, "total_label": "Total campaña"},
            {"kind": "sum", "terms": [["+", eur(ventas)], ["+", eur(subvenciones)]], "equals": eur(ingresos)},
            {"kind": "sum", "terms": [["+", eur(v)] for v in (liquidaciones, personal, suministros, amortizacion, otros)], "equals": eur(gastos)},
            {"kind": "sum", "terms": [["+", eur(ingresos)], ["-", eur(gastos)]], "equals": eur(resultado)},
            {"kind": "column_sum", "table": "t4", "columns": [1, 3], "label_column": 0, "total_label": "Total activo"},
            {"kind": "column_sum", "table": "t5", "columns": [1, 2, 3, 4], "label_column": 0, "total_label": "Total"}]
    del total_kg
    return {
        "template": "annual_report", "page_size": "A4", "languages": ["es-ES"],
        "metadata": {"title": "Informe anual 2025 — Cooperativa Agrícola Vega del Segura", "author": "Cooperativa Agrícola Vega del Segura, S. Coop.",
                     "subject": "Memoria e informe anual de la campaña 2024/25", "keywords": ["informe anual", "cooperativa", "cítricos", "2025"],
                     "lang": "es-ES", "created": "2026-05-20T09:00:00Z"},
        "theme": {"accent": "#2f6b2f", "rl_serif": True, "rl_size": 10},
        "running_footer": "Vega del Segura · Informe anual 2025 · Página {page} de {pages}", "pages": pages, "arithmetic": sums,
    }


DOCS = [
    ("w2-annual-en-01", "chromium", annual_en),
    ("w2-quarterly-de-02", "libreoffice", quarterly_de),
    ("w2-quarterly-ja-03", "pylopdf", quarterly_ja),
    ("w2-annual-es-04", "reportlab", annual_es),
    ("w2-bank-engb-05", "reportlab", bank_en_gb),
    ("w2-bank-fr-06", "chromium", bank_fr),
    ("w2-bank-pl-07", "libreoffice", bank_pl),
    ("w2-bank-ar-08", "pylopdf", bank_ar),
]
