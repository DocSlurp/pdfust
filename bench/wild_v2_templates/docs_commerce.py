"""wild-v2 commerce documents: card statements, receipt bundles, utility bills and purchase orders.

Every amount is computed in integer minor units (whole units for KRW, VND and
TWD) and every table whose numbers must add up is declared in
``doc["arithmetic"]`` so the build verifies it.
"""

# ruff: noqa: ANN401, ARG005, E501, FBT001, FBT003, PLR0913, PLR0917, PLR2004
from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from bench.wild_templates.common import nfd
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
    item,
    photo,
    rng,
    screenshot,
    table,
)

LRM, RLM = "\u200e", "\u200f"


def mul(quantity: float, unit: int) -> int:
    """Quantity x unit price rounded half up to the minor unit (same rule as the arithmetic checker)."""
    return int(quantity * unit + 0.5 + 1e-9)


def part(base: int, numerator: int, denominator: int) -> int:
    """Return ``base * numerator / denominator`` rounded half up (nonnegative)."""
    return (base * numerator * 2 + denominator) // (2 * denominator)


def balance_rows(opening: list[str], opening_balance: int, moves: list[tuple[list[str], int, int]], chunks: list[int],
                 fmt: Any, carry: list[str], bring: list[str]) -> tuple[list[list[str]], list[int], int]:
    """Running-balance rows: ``moves`` are ``(prefix cells, charge, credit)``; balance = previous + charge - credit.

    ``chunks`` lists moves per page segment; carried/brought-forward rows are inserted at segment boundaries.
    Returns the rows, the per-segment row counts and the closing balance.
    """
    if sum(chunks) != len(moves):
        msg = f"chunks {chunks} != {len(moves)} moves"
        raise ValueError(msg)
    balance = opening_balance
    rows: list[list[str]] = [[*opening, "", "", fmt(balance)]]
    sizes: list[int] = []
    start = 0
    for index, count in enumerate(chunks):
        segment = 0
        if index == 0:
            segment += 1
        else:
            rows.append([*bring, "", "", fmt(balance)])
            segment += 1
        for prefix, charge, credit in moves[start:start + count]:
            balance += charge - credit
            rows.append([*prefix, fmt(charge) if charge else "", fmt(credit) if credit else "", fmt(balance)])
            segment += 1
        start += count
        if index < len(chunks) - 1:
            rows.append([*carry, "", "", fmt(balance)])
            segment += 1
        sizes.append(segment)
    return rows, sizes, balance


# ====================================================================== credit-card statements


def card_en() -> dict[str, Any]:
    """US rewards Visa statement (pylopdf) with a running balance over 79 postings."""
    r = rng("w2-card-en-09")
    usd = lambda c: money(c, "en-US")  # noqa: E731
    start = date(2026, 4, 9)
    merchants = [
        ("ALBERTSONS #0187 BOISE ID", "Groceries", 2400, 13800, 7), ("WINCO FOODS #34 BOISE ID", "Groceries", 3100, 16500, 6),
        ("FRED MEYER FUEL #655 BOISE ID", "Gas", 3200, 6400, 5), ("BIG CITY COFFEE BOISE ID", "Dining", 650, 2150, 6),
        ("AMAZON MKTPL*2K4LR77Q0 AMZN.COM/BILL WA", "Online", 1299, 8999, 6), ("COSTCO WHSE #0751 BOISE ID", "Warehouse", 8800, 26400, 3),
        ("TRADER JOE'S #128 BOISE ID", "Groceries", 1800, 7400, 4), ("SHELL OIL 57444201 MERIDIAN ID", "Gas", 2900, 5800, 3),
        ("BARBACOA BOISE ID", "Dining", 6400, 14800, 2), ("REI #47 BOISE ID", "Sporting goods", 3500, 18900, 2),
        ("WALGREENS #11245 BOISE ID", "Pharmacy", 900, 4600, 3), ("DOLLAR TREE 4471 BOISE ID", "Retail", 525, 2400, 2),
        ("BOISE CO-OP NORTH END ID", "Groceries", 1500, 6200, 4), ("ST LUKE'S MED CTR PAYMT ID", "Medical", 4000, 4000, 1),
        ("CHEVRON 0204417 MOUNTAIN HOME ID", "Gas", 4100, 5600, 1), ("ALASKA AIR 0272418836219 SEATTLE WA", "Travel", 31840, 31840, 1),
        ("HOTEL ANDRA SEATTLE WA", "Travel", 61287, 61287, 1), ("H MART 한아름 LYNNWOOD WA", "Groceries", 4300, 8800, 1),
        ("TOUS LES JOURS 뚜레쥬르 LYNNWOOD WA", "Bakery", 1650, 2900, 1), ("CAFÉ MÉLANGE SEATTLE WA", "Dining", 2300, 4100, 1),
        ("PIKE PLACE CHOWDER SEATTLE WA", "Dining", 3600, 5200, 1), ("UBER *TRIP HELP.UBER.COM CA", "Rideshare", 1480, 4120, 3),
        ("IDAHO POWER CO 208-555-0172 ID", "Utilities", 11264, 11264, 1), ("SPARKLIGHT INTERNET 800-555-0193 AZ", "Utilities", 7999, 7999, 1),
        ("NETFLIX.COM 866-555-0141 CA", "Streaming", 1799, 1799, 1), ("SPOTIFY USA 877-555-0108 NY", "Streaming", 1199, 1199, 1),
        ("GOOGLE *ONE STORAGE G.CO/HELP CA", "Online", 299, 299, 1), ("BOISE PARKS & REC ID", "Recreation", 4500, 4500, 1),
        ("LES SCHWAB TIRES #0112 BOISE ID", "Auto", 18764, 18764, 1), ("PETCO 1428 BOISE ID", "Pets", 2800, 7900, 2),
    ]
    purchases: list[tuple[date, str, int]] = []
    category_of = {name: category for name, category, *_ in merchants}
    for name, _category, low, high, count in merchants:
        for _ in range(count):
            when = start + timedelta(days=r.randint(0, 28))
            if "SEATTLE" in name or "LYNNWOOD" in name or "ALASKA" in name:
                when = date(2026, 4, 23) + timedelta(days=r.randint(0, 3))
            purchases.append((when, name, r.randint(low // 10, high // 10) * 10 + r.choice([0, 3, 5, 9])))
    foreign = (date(2026, 4, 28), "LIBRAIRIE GALLIMARD MONTRÉAL QC  CAD 64.25", 4712)
    purchases.append(foreign)
    purchases.sort(key=lambda t: (t[0], t[1]))
    payments = [(date(2026, 4, 14), "PAYMENT THANK YOU — ONLINE ACH", 120000), (date(2026, 5, 1), "PAYMENT THANK YOU — ONLINE ACH", 85000)]
    refunds = [(date(2026, 4, 30), "REI #47 BOISE ID — RETURN", 6489)]
    fee = round(foreign[2] * 3 / 100)
    events: list[tuple[date, str, int, int]] = [(d, n, a, 0) for d, n, a in purchases]
    events += [(d, n, 0, a) for d, n, a in payments + refunds]
    events.append((foreign[0], "FOREIGN TRANSACTION FEE 3% — GALLIMARD", fee, 0))
    events.sort(key=lambda t: (t[0], t[3] == 0, t[1]))
    previous = 241873
    # average daily balance (purchases) for the interest charge
    daily, balance = [], previous
    for offset in range(30):
        today = start + timedelta(days=offset)
        balance += sum(c - p for d, _n, c, p in events if d == today)
        daily.append(balance)
    adb = sum(daily) // len(daily)
    interest = round(adb * 2449 / 10000 * 30 / 365)
    closing = date(2026, 5, 8)
    events.append((closing, "INTEREST CHARGE ON PURCHASES", interest, 0))
    moves = []
    for index, (when, name, charge, credit) in enumerate(events):
        post = min(when + timedelta(days=1 + index % 2), closing)
        ref = f"{24492 + index * 7:05d}{(index * 389) % 10000:04d}" if charge and not name.startswith(("INTEREST", "FOREIGN")) else ""
        moves.append(([when.strftime("%m/%d"), post.strftime("%m/%d"), name, ref], charge, credit))
    n = len(moves)
    chunks = [31, 33, n - 64]
    rows, sizes, new_balance = balance_rows(["", "", "PREVIOUS BALANCE", ""], previous, moves, chunks, usd,
                                            ["", "", "Balance carried forward", ""], ["", "", "Balance brought forward", ""])
    total_purchases = sum(a for _d, _n, a in purchases)
    total_pay = sum(a for _d, _n, a in payments)
    total_credit = sum(a for _d, _n, a in refunds)
    if new_balance != previous - total_pay - total_credit + total_purchases + fee + interest:
        msg = "card statement does not reconcile"
        raise ValueError(msg)
    one_pct = part(new_balance, 1, 100)
    minimum = one_pct + interest + fee
    header = [["Trans.", "Post", "Description", "Reference", "Charges", "Payments & credits", "Balance"]]
    segments = continued("tx", header, rows, sizes, caption="Transactions — Account ending 4417",
                         continued_caption="Transactions (continued) — Account ending 4417",
                         align=["l", "l", "l", "l", "r", "r", "r"], widths=[7, 7, 37, 13, 11, 13, 12], rendering="borderless")
    summary = table("summary", [
        ["Account summary", ""], ["Previous balance", usd(previous)], ["Payments", f"−{usd(total_pay)}"],
        ["Other credits", f"−{usd(total_credit)}"], ["Purchases", f"+{usd(total_purchases)}"], ["Cash advances", "+$0.00"],
        ["Fees charged", f"+{usd(fee)}"], ["Interest charged", f"+{usd(interest)}"], ["New balance", usd(new_balance)],
    ], rendering="borderless", align=["l", "r"], widths=[62, 38], total_rows=[8])
    warning = table("minpay", [
        ["If you make no additional charges using this card and each month you pay…", "You will pay off the balance shown on this statement in about…", "And you will end up paying an estimated total of…"],
        ["Only the minimum payment", "14 years", usd(round(new_balance * 2.31))],
        [usd(round(new_balance * 1.162 / 36 + 50) // 100 * 100), "3 years", f"{usd(round(new_balance * 1.162 / 36 + 50) // 100 * 100 * 36)} (Savings = {usd(round(new_balance * 2.31) - round(new_balance * 1.162 / 36 + 50) // 100 * 100 * 36)})"],
    ], align=["l", "c", "r"], widths=[38, 30, 32], caption="Minimum Payment Warning")
    ytd = table("ytd", [["2026 totals year-to-date", ""], ["Total fees charged in 2026", usd(fee + 1408)],
                        ["Total interest charged in 2026", usd(interest + 15873)]], rendering="borderless", align=["l", "r"], widths=[70, 30])
    calc = table("apr", [
        ["Type of balance", "Annual percentage rate (APR)", "Balance subject to interest rate", "Interest charge"],
        ["Purchases", "24.49% (v)", usd(adb), usd(interest)], ["Cash advances", "29.49% (v)", "$0.00", "$0.00"],
        ["Balance transfers", "24.49% (v)", "$0.00", "$0.00"],
    ], align=["l", "c", "r", "r"], widths=[28, 26, 26, 20], caption="Interest charge calculation — 30 days in billing period")
    rewards = table("rewards", [
        ["Juniper Rewards summary", "Points"], ["Points balance on 04/08/2026", "18,442"],
        ["Base points earned (1 point per $1)", f"{total_purchases // 100:,}"], ["Bonus points: dining and travel (2×)", "1,186"],
        ["Points redeemed — statement credit", "−10,000"], ["Points balance on 05/08/2026", f"{18442 + total_purchases // 100 + 1186 - 10000:,}"],
    ], rendering="borderless", align=["l", "r"], widths=[72, 28], total_rows=[5])
    by_category: dict[str, int] = {}
    counts: dict[str, int] = {}
    for _d, name, amount_ in purchases:
        key = category_of.get(name, "Other")
        key = key if key in {"Groceries", "Gas", "Dining", "Online", "Travel", "Warehouse", "Utilities"} else "Other"
        by_category[key] = by_category.get(key, 0) + amount_
        counts[key] = counts.get(key, 0) + 1
    ordered = sorted(by_category.items(), key=lambda kv: (kv[0] == "Other", -kv[1]))
    categories = table("cat", [["Spending category", "Transactions", "Amount"],
                               *[[k, str(counts[k]), usd(v)] for k, v in ordered],
                               ["Total purchases", str(len(purchases)), usd(total_purchases)]],
                       rendering="borderless", align=["l", "r", "r"], widths=[56, 18, 26], total_rows=[len(ordered) + 1],
                       caption="Your spending by category this period")
    coupon = table("coupon", [
        ["Account number", "New balance", "Minimum payment due", "Payment due date", "Amount enclosed"],
        ["4127 •••• •••• 4417", usd(new_balance), usd(minimum), "06/02/2026", "$ ______________"],
    ], align=["l", "r", "r", "c", "r"], widths=[24, 18, 22, 17, 19])
    return {
        "template": "credit_card_statement", "page_size": "Letter", "languages": ["en-US", "ko", "fr"],
        "metadata": {"title": "Juniper Peak Visa Signature statement — May 2026", "author": "Juniper Peak Federal Credit Union",
                     "subject": "Credit card statement, billing period 04/09/2026–05/08/2026, account ending 4417",
                     "keywords": ["credit card statement", "Visa", "minimum payment", "rewards"], "lang": "en-US",
                     "created": "2026-05-09T06:40:00Z"},
        "theme": {"accent": "#2d5a3d", "py_size": 8.8},
        "running_header": "Juniper Peak Visa Signature® · Account ending 4417 · Statement closing date 05/08/2026",
        "running_footer": "Page {page} of {pages}",
        "arithmetic": [
            {"kind": "running_balance", "table": "tx", "debit": 5, "credit": 4, "balance": 6},
            {"kind": "sum", "terms": [["+", usd(previous)], ["-", usd(total_pay)], ["-", usd(total_credit)], ["+", usd(total_purchases)],
                                      ["+", usd(fee)], ["+", usd(interest)]], "equals": usd(new_balance)},
            {"kind": "column_sum", "table": "cat", "columns": [1, 2], "label_column": 0, "total_label": "Total purchases"},
            {"kind": "sum", "terms": [["+", usd(one_pct)], ["+", usd(interest)], ["+", usd(fee)]], "equals": usd(minimum)},
        ],
        "pages": [
            [
                group([P("Juniper Peak Federal Credit Union", "brand"),
                       P("Card services: 1-208-555-0130 (24 hours)\nLost or stolen card: 1-208-555-0131\nPO Box 7720, Boise, ID 83707\njuniperpeak.example/cards", "small right")], "letterhead"),
                H(1, "Visa Signature® Rewards statement"),
                group([P("**Daniela Okafor-Reyes**\n1847 Larkspur Lane\nBoise, ID 83706-4512", "meta"),
                       P("**Account number:** 4127 •••• •••• 4417\n**Billing period:** 04/09/2026 – 05/08/2026\n**Credit limit:** $15,000.00\n"
                         f"**Available credit:** {usd(1500000 - new_balance)}\n**Cash advance limit:** $3,000.00", "meta")], "split"),
                group([summary,
                       box("callout", f"**New balance:** {usd(new_balance)}\n**Minimum payment due:** {usd(minimum)}\n**Payment due date:** 06/02/2026\n\n"
                           "**Late Payment Warning:** If we do not receive your minimum payment by the date listed above, you may "
                           "have to pay a late fee of up to $41.00 and your APRs may be increased up to the Penalty APR of 29.99%.",
                           title="Payment information", cls="warn")], "split"),
                warning,
                P("If you would like information about credit counseling services, call 1-888-555-0177.", "small"),
                box("callout", f"How we calculated your minimum payment: 1% of your new balance ({usd(one_pct)}) plus the interest "
                    f"charged this period ({usd(interest)}) plus fees ({usd(fee)}) = {usd(minimum)}. If your new balance is less than "
                    "$35.00, the minimum payment equals the new balance.", title="Minimum payment", cls="note"),
                box("sidebar", "Juniper Peak will never call, text or email you to ask for your full card number, PIN or a one-time "
                    "passcode. If you receive such a request, hang up and call the number on the back of your card. Turn on purchase "
                    "alerts in the app to be notified of every card-not-present transaction within seconds.", title="Fraud protection"),
                P("Pay online at juniperpeak.example/pay, in the Juniper Peak app, or by mail using the coupon on the last page. "
                  "Payments received by 5:00 p.m. Mountain Time on a business day are credited the same day.", "small"),
            ],
            [H(2, "Transactions"), segments[0]],
            [segments[1]],
            [
                segments[2],
                P(f"Total fees charged for this period: {usd(fee)}    Total interest charged for this period: {usd(interest)}", "right"),
                ytd,
                calc,
                P("(v) = variable rate. Your APRs vary with the market based on the Prime Rate. The daily periodic rate for "
                  "purchases is 0.06710%. We calculate interest using the average daily balance method (including new transactions).", "small"),
                box("footnote", "¹ Foreign transactions are converted by Visa at the rate in effect on the processing date; the "
                    "CAD 64.25 purchase on 04/28 converted at 0.7334 USD per CAD before the 3% foreign transaction fee."),
                box("footnote", "² Transactions marked with a Korean or French merchant name are shown exactly as transmitted by the merchant."),
            ],
            [
                categories,
                H(2, "Juniper Rewards"),
                rewards,
                box("sidebar", "You redeemed 10,000 points for a $100.00 statement credit on 04/18. Points earned on travel booked "
                    "through Juniper Travel count double through 07/31/2026. Points never expire while your account is open "
                    "and in good standing.", title="Rewards update"),
                H(2, "Important information"),
                L([("Billing rights: if you think there is an error on your statement, write to us at PO Box 7725, Boise, ID 83707 "
                    "within 60 days. You may also contact us at juniperpeak.example/dispute."),
                   ("Autopay: you are not enrolled. Enroll online to avoid late fees; autopay can pay the minimum, the statement "
                    "balance, or a fixed amount."),
                   "Para servicio al cliente en español, llame al 1-208-555-0135."]),
                P("Detach and return this portion with your check made payable to Juniper Peak FCU. Do not send cash.", "small"),
                coupon,
                P("Juniper Peak FCU · Card Payments · PO Box 7730 · Boise, ID 83707-7730", "small"),
            ],
        ],
    }



def card_ko() -> dict[str, Any]:
    """Korean card statement (chromium): installments, overseas use, points and a vector spending chart."""
    r = rng("w2-card-ko-10")
    won = lambda v: number(v, "ko")  # noqa: E731
    domestic = [
        ("스타벅스코리아 홍대입구역점", 4500, 13500, 6), ("GS25 망원한강점", 1200, 18000, 6), ("쿠팡(주)", 9800, 89000, 6),
        ("이마트 성산점", 32000, 168000, 3), ("배달의민족", 14000, 42000, 6), ("카카오T 택시", 4800, 23000, 5),
        ("올리브영 합정점", 8900, 54000, 3), ("SK에너지 상암주유소", 50000, 80000, 2), ("코레일 KTX 승차권", 59800, 59800, 2),
        ("교보문고 광화문점", 13500, 48000, 2), ("다이소 망원점", 2000, 15000, 3), ("CU 상암DMC점", 1500, 9000, 4),
        ("파리바게뜨 망원역점", 4500, 21000, 3), ("무신사스토어", 39000, 129000, 2), ("CGV 상암", 15000, 30000, 1),
        ("메가MGC커피 성산점", 2000, 6500, 4), ("홈플러스 합정점", 23000, 98000, 2), ("마포구립 체육센터", 55000, 55000, 1),
        ("NETFLIX.COM", 17000, 17000, 1), ("YOUTUBEPREMIUM", 14900, 14900, 1), ("SKT 통신요금 자동납부", 69000, 69000, 1),
        ("티머니 후불교통 (4월분)", 62350, 62350, 1), ("망원시장 청년떡집", 6000, 18000, 2), ("BURGER KING 합정역점", 7900, 15800, 2),
    ]
    lines: list[tuple[date, str, int]] = []
    for name, low, high, count in domestic:
        for _ in range(count):
            when = date(2026, 5, 1) + timedelta(days=r.randint(0, 30))
            amount_ = high if low == high else r.randint(low // 100, high // 100) * 100
            lines.append((when, name, amount_))
    lines.sort(key=lambda t: (t[0], t[1]))
    rate = 138530  # KRW per USD x 100
    overseas = [(date(2026, 5, 9), "AMAZON.COM AMZN.COM/BILL (USD 42.18)", 4218), (date(2026, 5, 21), "AIRBNB * HMXQ4Z9T2K (USD 318.40)", 31840)]
    rows: list[list[str]] = []
    principal_total = fee_total = 0
    for when, name, amount_ in lines:
        rows.append([when.strftime("%m.%d"), "본인 3712", name, won(amount_), "일시불", "", won(amount_), "0", "0"])
        principal_total += amount_
    lump_total = principal_total
    abroad_total = abroad_fee = 0
    for when, name, cents in overseas:
        krw = mul(cents, rate) // 10000
        fee = part(krw, 12, 1000)
        rows.append([when.strftime("%m.%d"), "본인 3712", name, won(krw), "해외", "", won(krw), won(fee), "0"])
        principal_total += krw
        fee_total += fee
        abroad_total += krw
        abroad_fee += fee
    installments = [
        (date(2026, 5, 6), "삼성전자 디지털프라자 홍대점", 1290000, 6, 1), (date(2026, 5, 17), "LG전자 베스트샵 마포점", 690000, 3, 1),
        (date(2026, 3, 12), "롯데하이마트 상암점", 840000, 6, 3), (date(2026, 1, 25), "한샘 리하우스 (가구)", 1560000, 10, 5),
    ]
    inst_rows, inst_checks, inst_principal, inst_fee, upcoming = [], [], 0, 0, []
    for when, name, price, months, nth in installments:
        base = price // months
        first = price - base * (months - 1)
        paid_before = first + base * (nth - 2) if nth > 1 else 0
        principal = first if nth == 1 else base
        remaining_before = price - paid_before
        fee = round(remaining_before * 149 / 1000 / 12)
        after = remaining_before - principal
        inst_rows.append([when.strftime("%m.%d"), "본인 3712", name, won(price), str(months), str(nth), won(principal), won(fee), won(after)])
        inst_checks.append({"kind": "sum", "terms": [["+", won(remaining_before)], ["-", won(principal)]], "equals": won(after)})
        inst_principal += principal
        inst_fee += fee
        if after:
            upcoming.append([name, f"{nth + 1}/{months}", won(min(base, after)), won(round(after * 149 / 1000 / 12)), won(after - min(base, after))])
    rows = sorted(rows + inst_rows, key=lambda row: row[0])
    principal_total += inst_principal
    fee_total += inst_fee
    discount = 5000
    due = principal_total + fee_total - discount
    total_row = [["", "", "합계", "", "", "", won(principal_total), won(fee_total), ""]]
    header = [["이용일자", "이용카드", "이용가맹점", "이용금액", "할부개월", "회차", "결제원금", "수수료(이자)", "결제 후 잔액"]]
    n = len(rows)
    segments = continued("use", header, rows, [31, 34, n - 65], caption="이용내역 (단위: 원)", continued_caption="이용내역 (계속, 단위: 원)",
                         align=["c", "c", "l", "r", "c", "c", "r", "r", "r"], widths=[8, 9, 27, 11, 8, 6, 11, 10, 10], total=total_row)
    summary = table("bill", [["구분", "금액(원)"], ["일시불", won(lump_total)], ["할부 결제원금", won(inst_principal)],
                             ["해외이용", won(abroad_total)], ["현금서비스", "0"], ["할부수수료·해외이용수수료", won(fee_total)],
                             ["청구할인 (통신요금 할인)", f"−{won(discount)}"], ["결제하실 금액", won(due)]],
                    align=["l", "r"], widths=[62, 38], total_rows=[7], caption="이번 달 결제하실 금액")
    spend = {"title": "최근 6개월 이용금액 (만원)", "categories": ["1월", "2월", "3월", "4월", "5월", "6월 청구"],
             "series": [("일시불", [142.6, 118.3, 151.0, 133.8, 129.4, round(lump_total / 10000, 1)]),
                        ("할부·해외", [41.2, 38.5, 63.9, 61.4, 58.7, round((inst_principal + abroad_total) / 10000, 1)])],
             "max": 250, "ticks": 5, "tick_format": lambda v: number(v, "ko", 0), "colors": ["#1b4f8f", "#f0a030"]}
    points = table("pt", [["포인트 구분", "포인트"], ["전월 이월 포인트", "12,840"], ["이번 달 적립 (0.7%)", won(lump_total * 7 // 1000)],
                          ["카페·편의점 추가 적립 (5%)", "3,415"], ["사용 포인트 (5. 12. 청구할인 전환)", "−10,000"],
                          ["소멸 예정 포인트 (2026. 7. 31.)", "1,206"]], align=["l", "r"], widths=[70, 30])
    rates = table("rates", [["구분", "적용 이자율·수수료율", "비고"], ["일시불 구매", "—", "이자 없음"],
                            ["할부 (2~12개월)", "연 9.9% ~ 19.9%", "회원님 적용 14.9%"], ["현금서비스", "연 5.9% ~ 19.9%", "회원님 적용 17.4%"],
                            ["카드론 (장기카드대출)", "연 6.5% ~ 19.5%", "신용점수에 따라 차등"], ["일부결제금액이월약정 (리볼빙)", "연 7.9% ~ 19.9%", "미약정"],
                            ["연체이자율", "약정금리 + 연 3%p", "최고 연 20%"]], align=["l", "c", "l"], widths=[38, 32, 30],
                   caption="이자율 및 수수료율 안내 (2026. 6. 기준)")
    next_month = table("next", [["가맹점", "다음 회차", "결제원금", "예상 수수료", "잔여 원금"], *upcoming],
                       align=["l", "c", "r", "r", "r"], widths=[40, 12, 16, 16, 16], caption="다음 달 할부 결제 예정 (단위: 원)")
    return {
        "template": "credit_card_statement", "page_size": "A4", "languages": ["ko-KR", "en"],
        "metadata": {"title": "누리카드 2026년 6월 이용대금 명세서", "author": "누리카드 주식회사",
                     "subject": "2026년 5월 이용분 카드 이용대금 명세서 (결제일 2026. 6. 14.)",
                     "keywords": ["이용대금명세서", "신용카드", "할부", "포인트"], "lang": "ko-KR", "created": "2026-06-02T00:30:00Z"},
        "theme": {"accent": "#1b4f8f", "font_size": "8.8pt", "margins": "15mm 13mm 17mm 13mm"},
        "running_header": "누리카드 이용대금 명세서 · 김서연 회원님 · 2026년 6월 청구",
        "running_footer": "{page} / {pages}",
        "arithmetic": [
            {"kind": "column_sum", "table": "use", "columns": [6, 7], "label_column": 2, "total_label": "합계"},
            {"kind": "column_sum", "table": "bill", "columns": [1], "label_column": 0, "total_label": "결제하실 금액"},
            {"kind": "sum", "terms": [["+", won(principal_total)], ["+", won(fee_total)], ["-", won(discount)]], "equals": won(due)},
            *inst_checks,
        ],
        "pages": [
            [
                group([P("누리카드", "brand"), P("고객센터 1588-5550 (평일 09:00~18:00)\n분실·도난 신고 1588-5551 (24시간)\nnuricard.example", "small right")], "letterhead"),
                H(1, "2026년 6월 이용대금 명세서"),
                group([P("**김서연** 회원님\n(03994) 서울특별시 마포구 월드컵북로 21길 17, 302호\n누리 더 모먼트 카드 (본인 3712)", "meta"),
                       P(f"**결제일:** 2026. 6. 14. (일) → 6. 15. (월) 출금\n**이용기간:** 2026. 5. 1. ~ 2026. 5. 31.\n**결제계좌:** 하나은행 ***-******-41207\n"
                         f"**결제하실 금액:** {money(due, 'ko')}\n**이용한도:** 8,000,000원 (잔여 {won(8000000 - due - 2140000)}원)", "meta")], "split"),
                summary,
                box("callout", "결제일이 휴일인 경우 다음 영업일에 출금됩니다. 결제계좌 잔액이 부족하면 연체이자가 부과되고, 5영업일 이상 "
                    "연체 시 신용평가회사에 연체정보가 등록될 수 있습니다.", title="결제 안내", cls="warn"),
                chart("spend", "bar", spend, "최근 6개월 이용금액 추이", raster=False, width="82%", size=(560, 230)),
                chart_table("spend-data", "월", spend, lambda v: number(v, "ko", 1)),
                P("※ 해외이용금액은 국제브랜드사(Visa) 매입 시점의 환율(USD 1 = 1,385.30원)을 적용하였으며, 해외이용수수료 1.2%가 별도 부과됩니다.", "small"),
            ],
            [H(2, "이용내역"), segments[0]],
            [segments[1]],
            [segments[2], next_month],
            [
                H(2, "포인트 안내"),
                points,
                box("sidebar", "카페·편의점 5% 추가 적립은 전월 실적 40만 원 이상일 때 월 최대 5,000포인트까지 제공됩니다. "
                    "적립된 포인트는 1포인트 = 1원으로 청구할인, 연회비 결제, 기부에 사용할 수 있습니다.", title="누리 더 모먼트 혜택"),
                rates,
                box("callout", "일부결제금액이월약정(리볼빙)은 결제하실 금액의 일부만 결제하고 나머지는 다음 달로 이월하는 서비스입니다. "
                    "이월된 금액에는 약정 이자율이 적용되므로 장기간 이용 시 이자 부담이 커질 수 있습니다. 현재 회원님은 미약정 상태입니다.",
                    title="리볼빙 이용 시 유의사항", cls="note"),
                H(3, "알려드립니다"),
                L(["2026. 7. 1.부터 해외 온라인 가맹점 이용 시 원화결제(DCC) 차단 서비스가 기본으로 적용됩니다.",
                   "명세서 내용에 이의가 있으시면 결제일 전까지 고객센터 또는 누리카드 앱 > 이용내역 > 이의신청으로 접수해 주세요.",
                   "카드 이용 알림은 앱 푸시로 무료 제공되며, 문자(SMS) 알림은 월 300원이 청구됩니다."]),
                box("footnote", "¹ 할부수수료는 결제 전 잔여 원금 × 연 14.9% ÷ 12로 계산하며 원 단위 미만은 반올림합니다."),
                box("footnote", "² 본 명세서는 2026. 6. 1. 기준으로 작성되었으며, 이후 취소·매입 건은 다음 달 명세서에 반영됩니다."),
            ],
        ],
    }


def card_tr() -> dict[str, Any]:
    """Turkish credit-card statement (ReportLab, embedded Noto because of ₺)."""
    r = rng("w2-card-tr-11")
    tl = lambda c: money(c, "tr")  # noqa: E731
    merchants = [
        ("MİGROS KADIKÖY MODA", 18000, 165000, 4), ("A101 YELDEĞİRMENİ", 4500, 38000, 3), ("ŞOK MARKET RASİMPAŞA", 3500, 26000, 3),
        ("KAHVE DÜNYASI BAHARİYE", 9500, 32000, 3), ("GETİR YEMEK", 22000, 61000, 3), ("TRENDYOL.COM", 29900, 189900, 3),
        ("İSTANBULKART DOLUM KADIKÖY İSKELE", 50000, 100000, 2), ("SHELL ÇIRAĞAN BEŞİKTAŞ", 150000, 240000, 2),
        ("TÜRK HAVA YOLLARI İST", 287450, 287450, 1), ("D&R KIZILAY ANKARA", 34500, 52000, 1), ("IŞIK OPTİK ÜSKÜDAR", 185000, 185000, 1),
        ("ECZANE ŞİFA ACIBADEM", 12750, 48900, 2), ("TURKCELL FATURA OTOMATİK", 64900, 64900, 1), ("İGDAŞ DOĞALGAZ OTOMATİK", 138760, 138760, 1),
        ("SPOTIFY P1A2B3C4", 9999, 9999, 1), ("ÇİÇEKSEPETİ.COM", 64000, 64000, 1), ("BİM KOZYATAĞI", 6000, 21000, 2),
    ]
    lines = []
    for name, low, high, count in merchants:
        for _ in range(count):
            when = date(2026, 4, 12) + timedelta(days=r.randint(0, 29))
            lines.append((when, name, "", high if low == high else r.randint(low // 100, high // 100) * 100 + r.choice([0, 50, 90])))
    lines.append((date(2026, 4, 19), "VATAN BİLGİSAYAR ALTUNİZADE 1/6 TAKSİT", "1/6", 549900 // 6 + 549900 % 6))
    lines.append((date(2026, 1, 8), "KOÇTAŞ ATAŞEHİR 4/9 TAKSİT", "4/9", 1215000 // 9))
    previous = 2468315
    payments = [(date(2026, 4, 15), "ÖDEME — MOBİL ŞUBE, TEŞEKKÜR EDERİZ", "", -2468315)]
    interest = 0
    lines += payments
    lines.sort(key=lambda t: (t[0], t[1]))
    purchases = sum(a for *_x, a in lines if a > 0)
    paid = -sum(a for *_x, a in lines if a < 0)
    cash_interest = 18640
    kkdf = part(cash_interest, 15, 100)
    bsmv = part(cash_interest, 15, 100)
    lines.append((date(2026, 5, 11), "NAKİT AVANS FAİZİ", "", cash_interest))
    lines.append((date(2026, 5, 11), "KKDF (%15)", "", kkdf))
    lines.append((date(2026, 5, 11), "BSMV (%15)", "", bsmv))
    lines.insert(0, (date(2026, 4, 12), "ÖNCEKİ DÖNEM BORCU", "", previous))
    del interest
    rows = []
    bonus_total = 0
    for when, name, inst, amount_ in lines:
        bonus = part(amount_, 5, 1000) if amount_ > 0 and not name.startswith(("ÖNCEKİ", "NAKİT", "KKDF", "BSMV")) else 0
        bonus_total += bonus
        rows.append([day(when, "dotted"), name, inst, tl(amount_), tl(bonus) if bonus else ""])
    total = previous - paid + purchases + cash_interest + kkdf + bsmv
    rows_total = [["", "Dönem Borcu", "", tl(total), tl(bonus_total)]]
    header = [["İşlem Tarihi", "Açıklama", "Taksit", "Tutar", "Bonus"]]
    n = len(rows)
    segments = continued("ekstre", header, rows, [16, n - 16], caption="Hesap Hareketleri", continued_caption="Hesap Hareketleri (devamı)",
                         align=["l", "l", "c", "r", "r"], widths=[14, 50, 9, 16, 11], total=rows_total)
    minimum = part(total, 40, 100)
    summary = table("ozet", [["Hesap Özeti", ""], ["Önceki dönem borcu", tl(previous)], ["Ödemeler", f"−{tl(paid)}"],
                             ["Harcamalar ve taksitler", tl(purchases)], ["Faiz, KKDF ve BSMV", tl(cash_interest + kkdf + bsmv)],
                             ["Dönem borcu", tl(total)], ["Asgari ödeme tutarı (%40)", tl(minimum)]],
                    rendering="borderless", align=["l", "r"], widths=[62, 38], total_rows=[5])
    return {
        "template": "credit_card_statement", "page_size": "A4", "languages": ["tr-TR"],
        "metadata": {"title": "Yıldız Kart Hesap Özeti — Mayıs 2026", "author": "Kardelen Katılım Dışı Bankası A.Ş.",
                     "subject": "Kredi kartı hesap özeti, 12.04.2026–11.05.2026 dönemi", "keywords": ["hesap özeti", "kredi kartı", "asgari ödeme", "bonus"],
                     "lang": "tr-TR", "created": "2026-05-12T05:10:00Z"},
        "theme": {"accent": "#8c1c2c", "rl_size": 9.0},
        "running_header": "Kardelen Bank · Yıldız Kart Hesap Özeti · Kart No: 5258 •••• •••• 0614",
        "running_footer": "Sayfa {page} / {pages}",
        "arithmetic": [
            {"kind": "column_sum", "table": "ekstre", "columns": [3, 4], "label_column": 1, "total_label": "Dönem Borcu"},
            {"kind": "column_sum", "table": "ozet", "columns": [1], "label_column": 0, "total_label": "Dönem borcu"},
            {"kind": "sum", "terms": [["+", tl(cash_interest)], ["+", tl(kkdf)], ["+", tl(bsmv)]], "equals": tl(cash_interest + kkdf + bsmv)},
        ],
        "pages": [
            [
                group([P("Kardelen Bank", "brand"), P("Müşteri İletişim Merkezi: 0850 555 07 07\nkardelenbank.example\nBüyükdere Cad. No: 214, 34394 Şişli/İstanbul", "small right")], "letterhead"),
                H(1, "Yıldız Kart Hesap Özeti"),
                group([P("**Sayın Elif Şahinoğlu**\nCaferağa Mah. Moda Cad. No: 81 D: 6\n34710 Kadıköy/İstanbul", "meta"),
                       P("**Hesap kesim tarihi:** 11.05.2026\n**Son ödeme tarihi:** 21.05.2026\n**Kart limiti:** 80.000,00 ₺\n"
                         f"**Kullanılabilir limit:** {tl(8000000 - total - 366600)}\n**Sonraki hesap kesim:** 11.06.2026", "meta")], "split"),
                group([summary, box("callout", f"Dönem borcunuz **{tl(total)}**, asgari ödeme tutarınız **{tl(minimum)}**. Son ödeme tarihi "
                                    "olan 21.05.2026 saat 23:59'a kadar ödeme yapmanız gerekir. Asgari tutarın altında kalan ödemelerde "
                                    "gecikme faizi uygulanır ve durum Kredi Kayıt Bürosu'na bildirilir.", title="Ödeme Bilgisi", cls="warn")], "split"),
                segments[0],
            ],
            [segments[1],
             P("Taksitli işlemlerinizin kalan tutarları sonraki dönem ekstrelerinize yansıtılacaktır: VATAN BİLGİSAYAR 5 taksit × "
               f"{tl(549900 // 6)}, KOÇTAŞ 5 taksit × {tl(1215000 // 9)}.", "small")],
            [
                H(2, "Faiz ve Ücret Bilgileri"),
                table("faiz", [["Oran türü", "Aylık", "Yıllık"], ["Akdi faiz (alışveriş)", "%3,75", "%45,00"], ["Gecikme faizi", "%4,05", "%48,60"],
                               ["Nakit avans faizi", "%3,75", "%45,00"], ["KKDF / BSMV", "%15 / %15", "Faiz tutarı üzerinden"]],
                      align=["l", "r", "r"], widths=[50, 20, 30], caption="Uygulanan faiz oranları (TCMB azami oranları)"),
                P(f"Bu dönem 28.04.2026 tarihli 5.000,00 ₺ nakit avans için {tl(cash_interest)} faiz hesaplanmış; buna {tl(kkdf)} KKDF ve "
                  f"{tl(bsmv)} BSMV eklenmiştir. Dönem borcunun tamamını ödemeniz hâlinde alışveriş harcamalarınıza faiz işletilmez."),
                H(2, "Bonus Özeti"),
                table("bonus", [["", "Bonus"], ["Önceki dönemden devreden", "184,20 ₺"], ["Bu dönem kazanılan (%0,5)", tl(bonus_total)],
                                ["Kullanılan", "−120,00 ₺"], ["Kullanılabilir bonus", tl(18420 + bonus_total - 12000)]],
                      rendering="borderless", align=["l", "r"], widths=[70, 30], total_rows=[4]),
                box("sidebar", "Haziran ayı boyunca market ve akaryakıt harcamalarınıza ilave %2 bonus! Kampanya Kardelen Mobil'den "
                    "katılım onayı verilen işlemler için geçerlidir; ışıklı tabela görülen anlaşmalı üye işyerlerinde iki katı bonus.", title="Kampanya"),
                H(2, "Önemli Bilgiler"),
                L(["Asgari ödeme oranı, kart limiti 50.000 ₺ üzerinde olduğundan %40 olarak uygulanmaktadır.",
                   "Hesap özetine 30 gün içinde itiraz edebilirsiniz; itirazlar 0850 555 07 07 veya Kardelen Mobil üzerinden alınır.",
                   "Kartınızın yıllık üyelik ücreti 12.06.2026 tarihli hesap özetinize yansıtılacaktır (1.250,00 ₺).",
                   "Iğdır, Şırnak ve Ağrı illerindeki deprem dayanışma kampanyasına bonuslarınızı bağışlayabilirsiniz."]),
                P("Bu hesap özeti 6502 sayılı Tüketicinin Korunması Hakkında Kanun kapsamında düzenlenmiştir. Kardelen Bank A.Ş. · Mersis No: 0482 0555 7700 0017", "small"),
            ],
        ],
    }


def card_he() -> dict[str, Any]:
    """Israeli card statement in Hebrew (LibreOffice, RTL, tagged) with LRM-wrapped Latin merchants."""
    r = rng("w2-card-he-12")
    ils = lambda c: money(c, "he")  # noqa: E731
    latin = lambda s: f"{LRM}{s}{LRM}"  # noqa: E731
    merchants = [
        ("שופרסל דיל רמת גן", "מזון וצריכה", 4500, 52000, 4), ("רמי לוי שיווק השקמה", "מזון וצריכה", 8000, 61000, 3),
        ("סופר-פארם ביאליק", "פארם", 2500, 18900, 3), ("ארומה אבן גבירול", "מסעדות ובתי קפה", 2400, 9800, 4),
        ("פז דלק מחלף גהה", "דלק", 18000, 36000, 3), ("רב-קו טעינה", "תחבורה", 5000, 10000, 2), ("גולף אנד קו קניון איילון", "הלבשה", 9900, 34900, 1),
        ("מאפיית לחם ארז", "מזון וצריכה", 1800, 6400, 3), ("סלקום תקשורת", "תקשורת", 9900, 9900, 1), ("חברת החשמל לישראל", "חשמל", 41260, 41260, 1),
        (latin("SPOTIFY P2A41C"), "מנויים", 2190, 2190, 1), (latin("NETFLIX.COM"), "מנויים", 5490, 5490, 1),
        (latin("WOLT TEL AVIV"), "מסעדות ובתי קפה", 6800, 16900, 3), (latin("IKEA RISHON LEZION"), "ריהוט", 23900, 64900, 1),
        (latin("GOOGLE *YOUTUBE"), "מנויים", 2390, 2390, 1), ("קפה לנדוור הבורסה", "מסעדות ובתי קפה", 3800, 7600, 2),
    ]
    rows = []
    for name, branch, low, high, count in merchants:
        for _ in range(count):
            when = date(2026, 5, 1) + timedelta(days=r.randint(0, 29))
            value = high if low == high else r.randint(low // 10, high // 10) * 10
            rows.append((when, name, branch, ils(value), value, ""))
    foreign = [(date(2026, 5, 12), latin("BOOKING.COM AMSTERDAM"), "תיירות", 31800, 117024), (date(2026, 5, 20), latin("AMAZON MKTPLACE US"), "קניות ברשת", 6249, 22997)]
    for when, name, branch, usd_cents, charge in foreign:
        rows.append((when, name, branch, f"${usd_cents // 100}.{usd_cents % 100:02d}", charge, "עסקה בדולרים, שער 3.68"))
    rows.append((date(2026, 3, 18), "מחסני חשמל רמת גן", "מוצרי חשמל", ils(479400), 79900, "תשלום 3 מתוך 6"))
    rows.append((date(2026, 5, 3), latin("ZARA DIZENGOFF CENTER"), "הלבשה", ils(-18990), -18990, "זיכוי — החזרת פריט"))
    rows.sort(key=lambda t: t[0])
    total = sum(t[4] for t in rows)
    values = [[day(w, "slash_dmy"), n, b, shown, ils(c), note] for w, n, b, shown, c, note in rows]
    header = [["תאריך עסקה", "שם בית העסק", "ענף", "סכום העסקה", "סכום החיוב", "פירוט נוסף"]]
    segments = continued("charges", header, values, [14, len(values) - 14], caption="פירוט עסקאות בכרטיס המסתיים ב־8841",
                         continued_caption="המשך הפירוט — כרטיס 8841", align=["c", "r", "r", "l", "l", "r"], widths=[12, 28, 16, 13, 13, 18],
                         total=[["", "סה״כ לחיוב בכרטיס", "", "", ils(total), ""]])
    fees = 0
    branches: dict[str, int] = {}
    for _w, _n, b, _s, c, _note in rows:
        branches[b] = branches.get(b, 0) + c
    by_branch = sorted(branches.items(), key=lambda kv: -kv[1])
    branch_table = table("branch", [["ענף", "סכום החיוב"], *[[k, ils(v)] for k, v in by_branch], ["סה״כ", ils(total)]],
                         rendering="borderless", align=["r", "l"], widths=[60, 40], total_rows=[len(by_branch) + 1],
                         caption="החיובים שלך לפי ענף")
    summary = table("sum", [["פירוט החיוב", "סכום"], ["עסקאות בארץ", ils(sum(t[4] for t in rows if "שער" not in t[5]))],
                            ["עסקאות בחו״ל", ils(sum(t[4] for t in rows if "שער" in t[5]))], ["עמלות", ils(fees)],
                            ["סה״כ לחיוב ב־10/06/2026", ils(total)]], align=["r", "l"], widths=[60, 40], total_rows=[4])
    return {
        "template": "credit_card_statement", "page_size": "A4", "languages": ["he-IL", "en"], "dir": "rtl", "tagged": True,
        "metadata": {"title": "כרמל קארד — פירוט חיובים לחודש מאי 2026", "author": "כרמל קארד בע״מ",
                     "subject": "דף פירוט חיובים בכרטיס אשראי, מועד חיוב 10/06/2026", "keywords": ["פירוט חיובים", "כרטיס אשראי", "תשלומים", "נקודות"],
                     "lang": "he-IL", "created": "2026-06-01T04:00:00Z"},
        "theme": {"accent": "#0d5c63", "lo_size": "9.5pt", "lo_font": "Noto Sans Hebrew"},
        "running_header": "כרמל קארד · פירוט חיובים · נועה בן־דוד",
        "running_footer": "עמוד {page} מתוך {pages}",
        "arithmetic": [
            {"kind": "column_sum", "table": "charges", "columns": [4], "label_column": 1, "total_label": "סה״כ לחיוב בכרטיס"},
            {"kind": "column_sum", "table": "sum", "columns": [1], "label_column": 0, "total_label": "סה״כ לחיוב ב־10/06/2026"},
            {"kind": "column_sum", "table": "branch", "columns": [1], "label_column": 0, "total_label": "סה״כ"},
        ],
        "pages": [
            [
                P("כרמל קארד", "brand"),
                P("מוקד שירות לקוחות: 03-555-0170 · ת״ד 5512 תל אביב", "small"),
                P(f"אתר: {LRM}carmelcard.example{LRM}{RLM} · אפליקציה: כרמל קארד", "small"),
                H(1, "פירוט חיובים לחודש מאי 2026"),
                P("**לכבוד:** נועה בן־דוד, רחוב הרצל 42 דירה 7, רמת גן 5251204\n**כרטיס:** ויזה כרמל פלטינום המסתיים ב־8841\n"
                  "**מועד חיוב:** 10/06/2026 · **חשבון לחיוב:** בנק לאומי, סניף 812, חשבון 33-41207\n**מסגרת אשראי:** ₪25,000.00", "meta"),
                summary,
                box("callout", f"הסכום של {ils(total)} יחויב בחשבון הבנק שלך ב־10/06/2026. אם ברצונך לפרוס את החיוב לתשלומים, "
                    "אפשר לעשות זאת באפליקציה עד יומיים לפני מועד החיוב.", title="לתשומת לבך", cls="note"),
                segments[0],
            ],
            [segments[1],
             P("עסקאות במטבע חוץ הומרו לשקלים לפי השער היציג ביום קליטת העסקה בתוספת עמלת המרה, שנכללה בסכום החיוב.", "small")],
            [
                H(2, "עסקאות בתשלומים"),
                table("inst", [["בית העסק", "סכום העסקה", "תשלום נוכחי", "סכום התשלום", "יתרה לתשלום"],
                               ["מחסני חשמל רמת גן", ils(479400), "3 מתוך 6", ils(79900), ils(239700)]],
                      align=["r", "l", "c", "l", "l"], widths=[30, 18, 16, 18, 18]),
                H(2, "מועדון הנקודות"),
                P(f"בחודש זה צברת {total // 1000} נקודות (נקודה על כל ₪10 בעסקאות בארץ). יתרת הנקודות שלך: 3,418. "
                  f"אפשר להמיר נקודות להנחה בטיסות {LRM}EL AL{LRM} ובאתר ההטבות של כרמל קארד."),
                H(2, "מידע על ריבית ועמלות"),
                table("rates", [["סוג אשראי", "ריבית שנתית", "הערות"], ["עסקאות בתשלומים ללא ריבית", "0%", "עד 12 תשלומים בבתי עסק מורשים"],
                                ["עסקאות קרדיט", "פריים + 6.9%", "11.4% נכון ליום הפקת הדף"], ["פריסת חיוב חודשי", "פריים + 4.5%", "9.0%"],
                                ["ריבית פיגורים", "ריבית העסקה + 3%", "לפי חוק"]], align=["r", "c", "r"], widths=[38, 24, 38]),
                box("callout", "שים לב: פריסה של חיוב לתשלומים כרוכה בתשלום ריבית. עלות האשראי הכוללת מוצגת לפני האישור באפליקציה.",
                    title="אזהרה", cls="warn"),
                L(["ניתן להגיש הסתייגות מעסקה תוך 30 יום ממועד החיוב באתר או במוקד.",
                   "עמלת כרטיס חודשית: ₪0.00 — פטור בזכות היקף שימוש מעל ₪5,000 בחודש.",
                   f"החל מ־01/07/2026 יתווסף שירות התראות {LRM}SMS{LRM} על כל עסקה מעל ₪500, ללא עלות."]),
                branch_table,
                box("footnote", "¹ ריבית הפריים ליום הפקת הדף: 4.5%. הריבית משתנה בהתאם לריבית בנק ישראל."),
            ],
        ],
    }



# ====================================================================== receipts and expense bundles


def receipt(tid: str, header: list[str], items: list[tuple[str, float, str, int]], fmt: Any, sub_label: str, adds: list[tuple[str, int]],
            total_label: str, *, widths: list[float] | None = None, caption: str = "", rendering: str = "borderless",
            after: list[tuple[str, int]] = (), decimal: str = ".", share: float = 1.0, minus: str = "−") -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    """Receipt item table: ``items`` are ``(description, quantity, quantity text, unit price)``.

    ``adds`` (tax, tip, discount) follow the subtotal and lead to ``total_label``; ``after`` rows are informational
    breakdowns placed below the total (for VAT-inclusive receipts) and must sum to the total.
    """
    sign = lambda v: fmt(v) if v >= 0 else minus + fmt(-v)  # noqa: E731
    rows = [list(header)]
    subtotal = 0
    for text, quantity, shown, unit in items:
        value = mul(quantity, unit)
        subtotal += value
        rows.append([text, shown, fmt(unit), fmt(value)])
    checks: list[dict[str, Any]] = [{"kind": "line_items", "table": tid, "quantity": 1, "unit_price": 2, "amount": 3, "decimal": decimal}]
    total = subtotal
    if sub_label != total_label:
        rows.append([sub_label, "", "", fmt(subtotal)])
        for label, value in adds:
            rows.append([label, "", "", sign(value)])
            total += value
    rows.append([total_label, "", "", fmt(total)])
    totals = list(range(len(items) + 1, len(rows)))
    for label, value in after:
        rows.append([label, "", "", fmt(value)])
    checks.append({"kind": "column_sum", "table": tid, "columns": [3], "label_column": 0, "total_label": sub_label})
    if adds:
        checks.append({"kind": "sum", "terms": [["+", fmt(subtotal)], *[["+" if v >= 0 else "-", fmt(abs(v))] for _l, v in adds]], "equals": fmt(total)})
    if after:
        checks.append({"kind": "sum", "terms": [["+", fmt(v)] for _l, v in after], "equals": fmt(total)})
    block = table(tid, rows, rendering=rendering, align=["l", "r", "r", "r"], widths=widths or [48, 10, 20, 22], total_rows=totals, caption=caption,
                  **({"width_share": share} if share != 1.0 else {}))
    return block, checks, total


def receipts_en() -> dict[str, Any]:
    """US expense report with eight receipts and a mileage log that exists only as a spreadsheet screenshot (chromium)."""
    usd = lambda c: money(c, "en-US")  # noqa: E731
    head = ["Item", "Qty", "Price", "Amount"]
    tax = lambda sub: part(sub, 8625, 100000)  # noqa: E731
    checks: list[dict[str, Any]] = []
    totals: dict[str, int] = {}

    def make(tid: str, items: list[tuple[str, float, str, int]], adds_fn: Any, sub: str = "Subtotal", total: str = "Total", **kw: Any) -> dict[str, Any]:
        subtotal = sum(mul(q, u) for _t, q, _s, u in items)
        block, more, value = receipt(tid, head, items, usd, sub, adds_fn(subtotal), total, **kw)
        checks.extend(more)
        totals[tid] = value
        return block

    air = make("r1", [("Base fare, Main Cabin AUS ⇄ SFO", 1, "1", 31256), ("U.S. transportation tax", 1, "1", 2344),
                      ("Sept. 11 security fee", 2, "2", 560), ("Flight segment tax", 2, "2", 530), ("Passenger facility charge", 2, "2", 450)],
               lambda s: [], sub="Total charged", total="Total charged")
    hotel = make("r2", [("Deluxe King, nightly rate", 3, "3", 28900), ("In-room dining, breakfast", 1, "1", 3450)],
                 lambda s: [("Hotel tax 14%", part(s, 14, 100)), ("Tourism assessment 1.5%", part(s, 15, 1000))], total="Balance paid")
    sushi = make("r3", [("Chef's omakase おまかせ", 3, "3", 6800), ("Vegetable set 精進", 1, "1", 5400), ("Hot sake 熱燗, carafe", 2, "2", 1800),
                        ("Hōjicha tea", 4, "4", 350)], lambda s: [("Sales tax 8.625%", tax(s)), ("Tip (20%)", part(s, 20, 100))])
    coffee = make("r4", [("Oat latte, 12 oz", 2, "2", 575), ("Breakfast burrito", 1, "1", 1150), ("Almond croissant", 1, "1", 425)],
                  lambda s: [("Sales tax 8.625%", tax(s))])
    bakery = make("r5", [("Soboro bread 소보로빵", 6, "6", 325), ("Red bean bun 단팥빵", 6, "6", 325), ("Coffee traveler, 96 oz", 2, "2", 2400),
                         ("Assorted mini cakes", 1, "1", 1895)], lambda s: [("Sales tax 8.625%", tax(s))])
    cab = make("r6", [("Meter fare SFO → Union Square", 1, "1", 5240), ("SFO airport exit fee", 1, "1", 500)],
               lambda s: [("Tip", 1000)], sub="Fare", total="Total")
    supplies = make("r7", [("Flip-chart pad, 25 sheets", 2, "2", 3899), ("Dry-erase markers, 8 ct", 2, "2", 1249), ("Sticky notes 3×3, 12 pk", 1, "1", 1599),
                           ("USB-C to HDMI adapter", 1, "1", 2499)], lambda s: [("Sales tax 8.625%", tax(s))])
    parking = make("r8", [("Economy garage, daily", 4, "4", 1200)], lambda s: [], sub="Amount paid", total="Amount paid")
    rate = 70
    trips = [("05/18/2026", "Home (Cedar Park)", "AUS Economy Garage", "Departure SFO trip", 23.6), ("05/21/2026", "AUS Economy Garage", "Home (Cedar Park)", "Return SFO trip", 23.6),
             ("05/22/2026", "Bramblewood HQ", "Dell Diamond area, Round Rock", "Follow-up with Tejas Grid Co-op", 17.2),
             ("05/22/2026", "Round Rock", "Bramblewood HQ", "Return", 17.2)]
    log = [["Date", "From", "To", "Purpose", "Miles", "Rate", "Amount"]]
    mileage = 0
    for when, a, b, why, miles in trips:
        value = mul(miles, rate)
        mileage += value
        log.append([when, a, b, why, f"{miles:.1f}", usd(rate), usd(value)])
    log.append(["Total", "", "", "", f"{sum(t[4] for t in trips):.1f}", "", usd(mileage)])
    checks.append({"kind": "line_items", "table": "mileage", "quantity": 4, "unit_price": 5, "amount": 6})
    checks.append({"kind": "column_sum", "table": "mileage", "columns": [6], "label_column": 0, "total_label": "Total"})
    sheet = {"title": "Mileage log — P. Natarajan — May 2026.xlsx", "menu": ["File", "Edit", "View", "Insert", "Format", "Data", "Tools"],
             "cell": "G6", "formula": "=SUM(G2:G5)", "tabs": ["Mileage", "Rates 2026", "Notes"], "rows": log,
             "numeric": [False, False, False, False, True, True, True], "selected_row": 6, "width": 820}
    summary_rows = [["No.", "Date", "Merchant", "Category", "Paid with", "Amount"],
                    ["1", "05/02/2026", "Cascade Air (e-ticket 0272418836219)", "Airfare", "Corporate Amex", usd(totals["r1"])],
                    ["2", "05/21/2026", "Hotel Alder & Pine, San Francisco", "Lodging", "Corporate Amex", usd(totals["r2"])],
                    ["3", "05/19/2026", "Sushi Ran 寿司蘭 — client dinner", "Meals, client", "Corporate Amex", usd(totals["r3"])],
                    ["4", "05/20/2026", "Fogline Coffee", "Meals, travel", "Personal Visa", usd(totals["r4"])],
                    ["5", "05/20/2026", "Tous les Jours 뚜레쥬르, Geary Blvd", "Workshop catering", "Personal Visa", usd(totals["r5"])],
                    ["6", "05/18/2026", "Metro Cab SF #4471", "Ground transport", "Cash", usd(totals["r6"])],
                    ["7", "05/19/2026", "Mission Office Supply", "Workshop supplies", "Personal Visa", usd(totals["r7"])],
                    ["8", "05/21/2026", "AUS Economy Garage", "Parking", "Personal Visa", usd(totals["r8"])],
                    ["9", "05/22/2026", "Personal vehicle, 81.6 mi @ $0.70", "Mileage", "—", usd(mileage)]]
    grand = sum(totals.values()) + mileage
    corporate = totals["r1"] + totals["r2"] + totals["r3"]
    summary_rows.append(["", "", "Total expenses", "", "", usd(grand)])
    checks.append({"kind": "column_sum", "table": "er", "columns": [5], "label_column": 2, "total_label": "Total expenses"})
    checks.append({"kind": "sum", "terms": [["+", usd(grand)], ["-", usd(corporate)]], "equals": usd(grand - corporate)})
    checks.append({"kind": "column_sum", "table": "amex", "columns": [3], "label_column": 1, "total_label": "Total corporate card"})

    def slip(lines: str, meta: str, block: dict[str, Any], foot: str) -> dict[str, Any]:
        return group([P(lines, "center"), P(meta, "small"), block, P(foot, "small center")], "receipt")

    return {
        "template": "retail_receipts", "page_size": "Letter", "languages": ["en-US", "ja", "ko"],
        "metadata": {"title": "Expense report ER-2026-0614 — San Francisco customer workshop", "author": "Priya Natarajan",
                     "subject": "Travel and workshop expenses with itemized receipts, May 18–22, 2026",
                     "keywords": ["expense report", "receipts", "reimbursement", "mileage"], "lang": "en-US", "created": "2026-05-26T15:05:00Z"},
        "theme": {"accent": "#5b3a8c", "font_size": "9.2pt", "margins": "15mm 15mm 17mm 15mm"},
        "running_header": "Bramblewood Analytics, Inc. · Expense report ER-2026-0614 · P. Natarajan",
        "running_footer": "Page {page} of {pages}",
        "arithmetic": checks,
        "pages": [
            [
                group([P("Bramblewood Analytics, Inc.", "brand"), P("Finance & Travel · 600 Congress Ave, Suite 1400\nAustin, TX 78701 · expenses@bramblewood.example", "small right")], "letterhead"),
                H(1, "Expense report ER-2026-0614"),
                group([P("**Employee:** Priya Natarajan (E-20417)\n**Department:** Field Engineering, cost center 4410\n**Manager:** Marcus Oyelaran\n**Submitted:** 05/26/2026", "meta"),
                       P("**Trip:** Customer workshop, Northgate Water District, San Francisco\n**Dates:** 05/18/2026 – 05/22/2026\n**Project code:** NWD-PILOT-26\n**Billable to customer:** No", "meta")], "split"),
                P("Receipts are attached in the order listed. Items 1–3 were charged to the corporate card and are shown for "
                  "reconciliation only; the reimbursement due to the employee is the total of items 4–9."),
                table("er", summary_rows, rendering="ruled", align=["c", "l", "l", "l", "l", "r"], widths=[5, 12, 35, 18, 16, 14], total_rows=[10],
                      caption="Summary of expenses"),
                group([table("due", [["Reconciliation", ""], ["Total expenses", usd(grand)], ["Less: paid on corporate card", "−" + usd(corporate)],
                                     ["Reimbursement due to employee", usd(grand - corporate)]], rendering="borderless", align=["l", "r"], widths=[65, 35], total_rows=[3]),
                       box("callout", "Client meals require the names of all attendees. Dinner on 05/19: Priya Natarajan; Marcus Oyelaran; "
                           "Dr. Hana Kobayashi (小林 花) and Luis Ortega, Northgate Water District. Alcohol is within the $25 per person limit.",
                           title="Policy notes", cls="note")], "split"),
                table("sign", [["Role", "Name", "Signature", "Date"], ["Employee", "Priya Natarajan", "/s/ P. Natarajan", "05/26/2026"],
                               ["Approver", "Marcus Oyelaran", "", ""], ["Finance review", "Accounts Payable", "", ""]],
                      align=["l", "l", "l", "l"], widths=[20, 28, 32, 20], caption="Approvals"),
                box("footnote", "¹ Mileage is reimbursed at the 2026 company rate of $0.70 per mile; commuting miles between home and HQ are excluded."),
            ],
            [
                H(2, "Receipts 1, 2 and 6 · Travel"),
                group([slip("**Cascade Air**\nElectronic ticket receipt\nConfirmation QHZ4TR", "Issued 05/02/2026 · Ticket 0272418836219\nPassenger NATARAJAN/PRIYA\nAUS 05/18 CA 1184 · SFO 05/21 CA 1191", air,
                           "AMEX CORPORATE •••• 61005\nFare is non-refundable; changes permitted for a fee."),
                       slip("**Hotel Alder & Pine**\n940 Sutter Street\nSan Francisco, CA 94109\n(415) 555-0123", "Folio 88213 · Room 512 · 3 nights\nArrive 05/18/2026 · Depart 05/21/2026", hotel,
                           "AMEX CORPORATE •••• 61005\nThank you for staying with us.")], "split"),
                P("The hotel was booked through the corporate travel portal at the negotiated government-district rate. The breakfast "
                  "charge on 05/20 was a working breakfast before the second workshop day and is claimed as a travel meal.", "small"),
                group([slip("**METRO CAB SF** · Medallion 4471\nDriver ID 20-8836", "05/18/2026 · Pickup 11:06 AM SFO Terminal 1\nDrop-off 11:41 AM 940 Sutter St · 14.2 mi", cab,
                           "Paid cash · receipt printed by meter"),
                       box("callout", "The cab ride from SFO was taken because the BART Yellow Line was suspended between SFO and "
                           "Glen Park on the morning of 05/18 for track work. A screenshot of the BART service alert is on file.",
                           title="Why not transit?", cls="warn")], "split"),
            ],
            [
                H(2, "Receipts 3–4 · Meals"),
                group([slip("**SUSHI RAN 寿司蘭**\n1418 Polk Street\nSan Francisco, CA 94109\n(415) 555-0186", "05/19/2026 8:42 PM · Server: Akiko\nTable 12 · Guests 4 · Check 3307", sushi,
                           "AMEX CORPORATE •••• 61005 · AUTH 044817\nありがとうございました"),
                       slip("**Fogline Coffee**\n2201 Fillmore St\nSan Francisco, CA 94115", "05/20/2026 7:58 AM · Order #A-214\nCashier: Devon", coffee,
                           "VISA •••• 2291 · contactless\nRefills on drip coffee are free.")], "split"),
                photo("lunch", ["catering-buffet", "coffee-cup"], ["food"], {"catering-buffet": "Workshop lunch for the district operations team, May 20"},
                      "Workshop catering, May 20", "right", width="42%"),
                P("The second workshop day ran from 8:30 a.m. to 4:00 p.m. at the district’s Bayview operations center with eleven "
                  "attendees. Lunch was provided by the district; only the pastries and coffee for the morning session (receipt 5) "
                  "are claimed here."),
                P("Breakfast at Fogline Coffee on 05/20 was for two people (Priya Natarajan and Marcus Oyelaran) while preparing the "
                  "demo environment, and it falls under the travel-meal allowance rather than client entertainment."),
                P("All receipts are originals scanned at 300 dpi. Paper copies will be kept for 90 days in case of audit.", "small"),
            ],
            [
                H(2, "Receipts 5 and 7 · Workshop"),
                group([slip("**TOUS les JOURS 뚜레쥬르**\n5217 Geary Blvd\nSan Francisco, CA 94118", "05/20/2026 7:31 AM · Reg 2 · Trans 6619", bakery,
                           "VISA •••• 2291\n감사합니다 · Thank you!"),
                       slip("**Mission Office Supply**\n2789 Mission St\nSan Francisco, CA 94110", "05/19/2026 4:12 PM · Store 07 · Reg 1\nAssociate: Lupe", supplies,
                           "VISA •••• 2291 · chip\nReturns within 30 days with receipt.")], "split"),
                P("The flip-chart pads and markers were used for the failure-mode mapping exercise with the district’s SCADA "
                  "operators; the leftover pads were given to the district. The HDMI adapter stays with the demo laptop kit "
                  "(asset tag BA-LT-0193) and has been logged in the equipment register."),
                box("sidebar", "Pastries and coffee for the morning session were ordered for 12 people. Per policy 4.3, "
                    "light refreshments for customer workshops are capped at $12.00 per attendee; the claim of "
                    "$115.09 is within the $144.00 cap.", title="Refreshment cap"),
                L(["Day 1 (05/19): current-state walkthrough, alarm flood review, failure-mode mapping",
                   "Day 2 (05/20): pilot dashboard demo, data-access agreement, next steps",
                   "Follow-up (05/22): call with Tejas Grid Co-op about a joint pilot in Round Rock"]),
            ],
            [
                H(2, "Mileage and parking"),
                screenshot("sheet", "spreadsheet", sheet, "Mileage log exported from the team spreadsheet (screenshot)", width="96%"),
                table("mileage", log, rendering="screenshot", caption="Mileage log as shown in the screenshot"),
                group([slip("**AUS Economy Garage**\nAustin-Bergstrom International Airport", "Entry 05/18/2026 5:47 AM\nExit 05/21/2026 9:12 PM · Lane 4", parking,
                           "VISA •••• 2291 · ticket 0061773"),
                       group([H(3, "Employee certification"),
                              P("I certify that these expenses were incurred for business purposes on behalf of Bramblewood Analytics, "
                                "that they have not been and will not be submitted for reimbursement elsewhere, and that the attached "
                                "receipts are complete and accurate."),
                              P("Signature: /s/ Priya Natarajan    Date: 05/26/2026"),
                              P("Reimbursement will be paid by direct deposit with the 06/05/2026 payroll run.", "small")])], "split"),
                table("amex", [["Card posting", "Merchant as shown on corporate card", "Report item", "Amount"],
                               ["05/04/2026", "CASCADE AIR 0272418836219", "1", usd(totals["r1"])],
                               ["05/22/2026", "HOTEL ALDER AND PINE SAN FRANCISCO", "2", usd(totals["r2"])],
                               ["05/20/2026", "SUSHI RAN SAN FRANCISCO CA", "3", usd(totals["r3"])],
                               ["", "Total corporate card", "", usd(corporate)]],
                      rendering="borderless", align=["l", "l", "c", "r"], widths=[16, 50, 14, 20], total_rows=[4],
                      caption="Corporate card reconciliation (Amex statement closing 05/25/2026)"),
            ],
        ],
    }



def daxie(cents: int) -> str:
    """Chinese financial capital numerals for an amount in fen (below 100 million yuan)."""
    digits = "零壹贰叁肆伍陆柒捌玖"

    def four(n: int) -> str:
        out, zero = "", False
        for pos, unit in ((3, "仟"), (2, "佰"), (1, "拾"), (0, "")):
            d = n // 10 ** pos % 10
            if d == 0:
                zero = bool(out)
            else:
                out += ("零" if zero else "") + digits[d] + unit
                zero = False
        return out

    yuan, rest = divmod(cents, 100)
    jiao, fen = divmod(rest, 10)
    text = ""
    if yuan >= 10000:
        high, low = divmod(yuan, 10000)
        text = four(high) + "万" + (("零" if low < 1000 else "") + four(low) if low else "")
    elif yuan:
        text = four(yuan)
    text += "元" if yuan else ""
    if not jiao and not fen:
        return text + "整"
    text += digits[jiao] + "角" if jiao else ("零" if yuan else "")
    return text + (digits[fen] + "分" if fen else "整")


def vn_words(n: int) -> str:
    """Vietnamese reading of a whole number of dong."""
    d = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

    def three(x: int, full: bool) -> list[str]:
        h, t, u = x // 100, x // 10 % 10, x % 10
        out = [d[h], "trăm"] if full or h else []
        if t == 0:
            out += (["linh"] if out and u else []) + ([d[u]] if u else [])
        elif t == 1:
            out += ["mười"] + ([("lăm" if u == 5 else d[u])] if u else [])
        else:
            out += [d[t], "mươi"] + ([{1: "mốt", 4: "tư", 5: "lăm"}.get(u, d[u])] if u else [])
        return out

    groups = []
    while n:
        groups.append(n % 1000)
        n //= 1000
    words: list[str] = []
    for index in range(len(groups) - 1, -1, -1):
        if groups[index]:
            words += three(groups[index], index != len(groups) - 1) + ([["", "nghìn", "triệu", "tỷ"][index]] if index else [])
    text = " ".join(words)
    return text[0].upper() + text[1:] + " đồng"


def receipts_zhcn() -> dict[str, Any]:
    """Simplified Chinese travel reimbursement with rail tickets, a VAT e-invoice and till receipts (ReportLab CID)."""
    cny = lambda c: money(c, "zh")  # noqa: E731
    num = lambda c: number(c / 100, "zh")  # noqa: E731
    checks: list[dict[str, Any]] = []
    rail = 64650
    taxi = [(date(2026, 4, 14), "深圳北站 至 南山区科技园", "21.4", 7260), (date(2026, 4, 16), "南山区科技园 至 深圳北站", "20.9", 7080)]
    fapiao_items = [("*住宿服务*住宿费", "标准大床房", "晚", 3, 45283), ("*餐饮服务*早餐", "自助", "份", 2, 5660), ("*生活服务*洗衣费", "", "件", 3, 1887)]
    fp_rows = [["项目名称", "规格型号", "单位", "数量", "单价", "金额", "税率", "税额"]]
    fp_amount = fp_tax = 0
    for name, spec, unit, qty, price in fapiao_items:
        value = mul(qty, price)
        tax = part(value, 6, 100)
        fp_amount += value
        fp_tax += tax
        fp_rows.append([name, spec, unit, str(qty), num(price), num(value), "6%", num(tax)])
    fp_rows.append(["合计", "", "", "", "", cny(fp_amount), "", cny(fp_tax)])
    fp_total = fp_amount + fp_tax
    checks += [{"kind": "line_items", "table": "fapiao", "quantity": 3, "unit_price": 4, "amount": 5},
               {"kind": "column_sum", "table": "fapiao", "columns": [5, 7], "label_column": 0, "total_label": "合计"},
               {"kind": "sum", "terms": [["+", cny(fp_amount)], ["+", cny(fp_tax)]], "equals": cny(fp_total)}]
    hotpot, more, hotpot_total = receipt("hotpot", ["品名", "数量", "单价", "金额"], [
        ("鸳鸯锅底", 1, "1", 6800), ("精品肥牛卷", 2, "2", 5800), ("鲜毛肚", 1, "1", 4800), ("手打虾滑", 1, "1", 4200), ("鸭血", 1, "1", 2200),
        ("时蔬拼盘", 1, "1", 3600), ("酸梅汤（扎）", 1, "1", 2800), ("米饭", 3, "3", 300)], num, "小计", [("会员优惠", -2000)], "实收",
        widths=[46, 12, 20, 22], share=0.47, minus="-")
    checks += more
    market, more, market_total = receipt("market", ["商品", "数量", "单价", "金额"], [
        ("农夫山泉 550ml", 6, "6", 200), ("得力 订书机", 1, "1", 1590), ("晨光 中性笔 0.5mm（12支）", 1, "1", 2380), ("A4 打印纸（包）", 2, "2", 2650),
        ("心相印 抽纸 3包装", 1, "1", 1290), ("Type-C 数据线 1m", 1, "1", 3990)], num, "合计", [], "合计", widths=[52, 10, 18, 20], share=0.47)
    checks += more
    entries = [("1", "2026-04-14", "铁路电子客票", "杭州东—深圳北 G3007 二等座", rail), ("2", "2026-04-14", "出租车发票", "深圳市鹏城出租汽车有限公司", taxi[0][3]),
               ("3", "2026-04-14", "增值税电子普通发票", "深圳湾畔商务酒店有限公司（3晚）", fp_total), ("4", "2026-04-15", "餐饮小票", "蜀香阁火锅（南山科技园店）", hotpot_total),
               ("5", "2026-04-15", "超市小票", "百佳惠超市（科苑店）", market_total), ("6", "2026-04-16", "出租车发票", "深圳市鹏城出租汽车有限公司", taxi[1][3]),
               ("7", "2026-04-17", "铁路电子客票", "深圳北—杭州东 G3010 二等座", rail)]
    allowance = 3 * 10000
    grand = sum(e[4] for e in entries) + allowance
    summary = [["序号", "日期", "票据类型", "开票方 / 摘要", "金额（元）"], *[[a, b, c, d_, num(v)] for a, b, c, d_, v in entries],
               ["8", "2026-04-14至17", "出差补助", "伙食补助 3天 × 100.00", num(allowance)], ["", "", "合计", "", num(grand)]]
    checks.append({"kind": "column_sum", "table": "baoxiao", "columns": [4], "label_column": 2, "total_label": "合计"})

    folio = [["日期", "项目", "金额（含税）"], ["04-14", "房费 1608房", "480.00"], ["04-15", "房费 1608房", "480.00"], ["04-15", "自助早餐", "60.00"],
             ["04-16", "房费 1608房", "480.00"], ["04-16", "自助早餐", "60.00"], ["04-16", "洗衣（衬衫3件）", "60.00"], ["", "合计", num(fp_total)]]
    checks.append({"kind": "column_sum", "table": "folio", "columns": [2], "label_column": 1, "total_label": "合计"})
    budget, used = 4000000, 2186540
    checks.append({"kind": "sum", "terms": [["+", num(budget)], ["-", num(used)], ["-", num(grand)]], "equals": num(budget - used - grand)})

    def kv(tid: str, pairs: list[list[str]], caption: str) -> dict[str, Any]:
        return table(tid, pairs, rendering="ruled", header_rows=0, align=["l", "l"], widths=[34, 66], caption=caption, width_share=0.47)

    return {
        "template": "retail_receipts", "page_size": "A4", "languages": ["zh-CN"],
        "metadata": {"title": "差旅费报销单 BX-2026-0419（深圳出差）", "author": "陈思远", "subject": "深圳客户拜访差旅费报销及原始票据",
                     "keywords": ["差旅费", "报销单", "发票", "小票"], "lang": "zh-CN", "created": "2026-04-20T02:30:00Z"},
        "theme": {"accent": "#a12a2a", "rl_size": 9.4},
        "running_header": "杭州云栖数智科技有限公司 　 差旅费报销单 BX-2026-0419",
        "running_footer": "第 {page} 页 共 {pages} 页",
        "arithmetic": checks,
        "pages": [
            [
                group([P("杭州云栖数智科技有限公司", "brand"), P("财务部 　 杭州市西湖区云栖小镇创智路8号\n电话：0571-5550-3366", "small right")], "letterhead"),
                H(1, "差旅费报销单"),
                group([P("**报销人：** 陈思远（工号 YQ-0716）\n**部门：** 华南市场部\n**出差地点：** 广东省深圳市南山区\n**出差时间：** 2026年4月14日至4月17日", "meta"),
                       P("**单据编号：** BX-2026-0419\n**填报日期：** 2026年4月20日\n**项目：** 智慧园区能耗平台（鹏城科技园）\n**附单据：** 7 张", "meta")], "split"),
                P("出差事由：赴深圳鹏城科技园管理有限公司进行平台二期需求调研，并参加4月15日的项目启动会。行程、住宿均按公司差旅标准执行，"
                  "住宿标准为每晚不超过500元（一线城市）。"),
                table("baoxiao", summary, align=["c", "l", "l", "l", "r"], widths=[7, 18, 18, 39, 18], total_rows=[9], caption="费用明细"),
                P(f"报销金额合计（大写）：**人民币{daxie(grand)}**　（小写）{cny(grand)}"),
                table("approve", [["环节", "签字", "日期", "意见"], ["报销人", "陈思远", "2026-04-20", "—"], ["部门负责人", "", "", ""],
                                  ["财务审核", "", "", ""], ["总经理审批", "", "", ""]], align=["l", "l", "l", "l"], widths=[20, 25, 20, 35], caption="审批流程"),
                P("填报说明：（1）电子发票须同时上传PDF原件，纸质小票须粘贴在粘贴单上；（2）伙食补助按出差天数计算，每天100元，不需提供票据；"
                  "（3）超过标准的住宿费用由个人承担，并在备注中说明原因。", "small"),
            ],
            [
                H(2, "一、交通票据"),
                group([kv("rail1", [["电子客票号", "E412907735"], ["车次 / 席别", "G3007 / 二等座 07车12F"], ["区间", "杭州东 — 深圳北"],
                                    ["开车时间", "2026-04-14 07:42"], ["票价", cny(rail)], ["乘车人", "陈思远 3301**********2418"]], "铁路电子客票（去程）"),
                       kv("rail2", [["电子客票号", "E413066212"], ["车次 / 席别", "G3010 / 二等座 05车03A"], ["区间", "深圳北 — 杭州东"],
                                    ["开车时间", "2026-04-17 15:18"], ["票价", cny(rail)], ["乘车人", "陈思远 3301**********2418"]], "铁路电子客票（返程）")], "split"),
                group([kv(f"taxi{n}", [["发票代码", f"14403250{n}171"], ["日期", day(w, "iso")], ["行程", route], ["里程（公里）", km],
                                       ["金额", cny(v)], ["车号", "粤BD3K71" if n == 1 else "粤BF0928"]], f"深圳出租车发票（{'一' if n == 1 else '二'}）")
                       for n, (w, route, km, v) in enumerate(taxi, start=1)], "split"),
                P("说明：4月15日至16日在园区内往返均为步行或乘坐园区接驳车，未产生市内交通费用。返程车次因会议延长由G3006改签为G3010，"
                  "改签未产生差价及手续费。", "small"),
                table("trip", [["日期", "时间", "地点", "事项"], ["4月14日", "07:42—14:05", "杭州东—深圳北", "乘G3007赴深圳，下午入住酒店"],
                               ["4月15日", "09:00—17:30", "鹏城科技园A座12楼", "需求调研、项目启动会"], ["4月16日", "09:30—16:00", "园区能源站、3号楼机房", "现场勘查电表与网关点位"],
                               ["4月17日", "09:00—12:00", "鹏城科技园A座12楼", "需求确认会，15:18乘G3010返杭"]],
                      align=["l", "l", "l", "l"], widths=[12, 18, 30, 40], caption="行程安排"),
                box("callout", "铁路电子客票的报销凭证为“电子发票（铁路电子客票）”，请在12306中开具后打印，与行程信息一并提交。"
                    "出租车发票须与行程时间一致，补开的发票不予报销。", title="财务提示"),
            ],
            [
                H(2, "二、住宿发票"),
                P("电子发票（普通发票）", "center"),
                group([P("**发票号码：** 26442000000081734512\n**开票日期：** 2026年04月17日", "meta"),
                       P("**购买方：** 杭州云栖数智科技有限公司\n**统一社会信用代码：** 91330106MA2KX3P71Q", "meta")], "split"),
                P("**销售方：** 深圳湾畔商务酒店有限公司　**统一社会信用代码：** 91440300MA5G8YJ20N", "meta"),
                table("fapiao", fp_rows, align=["l", "l", "c", "r", "r", "r", "c", "r"], widths=[22, 13, 7, 7, 12, 14, 9, 16], total_rows=[len(fp_rows) - 1]),
                table("fp-total", [["价税合计（大写）", f"{daxie(fp_total)}", "（小写）", cny(fp_total)]], header_rows=0,
                      align=["l", "l", "r", "r"], widths=[22, 44, 14, 20]),
                P("备注：入住日期2026-04-14，离店日期2026-04-17，房号1608，入住人陈思远。", "small"),
                P("开票人：刘婷　　收款人：前台　　复核：王建华", "small"),
                P("住宿费单价452.83元为不含税价，含税每晚480.00元，在公司一线城市每晚500元的标准以内。早餐两份为4月15日、16日；"
                  "4月14日入住较晚，未用早餐。洗衣费为3件衬衫，因连续两天参加客户会议而产生，经部门负责人同意后报销。"),
                table("folio", folio, rendering="borderless", align=["l", "l", "r"], widths=[20, 50, 30], total_rows=[7], caption="酒店账单明细（入住单号 F0414-1608）"),
                box("sidebar", "增值税电子普通发票的税率为6%，税额不能抵扣，全额计入差旅费。收到发票后请核对购买方名称和统一社会信用代码，"
                    "信息有误的发票须由酒店红冲后重新开具。", title="发票说明"),
            ],
            [
                H(2, "三、餐饮及办公用品"),
                group([group([P("**蜀香阁火锅（南山科技园店）**\n深圳市南山区科苑路15号\n电话：0755-5550-8821", "center"),
                              P("台号：A12　人数：3　单号：202604151937\n时间：2026-04-15 19:37", "small"), hotpot,
                              P("支付方式：微信支付　交易单号尾号 4410\n谢谢惠顾，欢迎再次光临！", "small")]),
                       group([P("**百佳惠超市（科苑店）**\n深圳市南山区科苑南路3099号", "center"),
                              P("收银机：03　收银员：1027\n时间：2026-04-15 08:16", "small"), market,
                              P("支付方式：支付宝　尾号 6603\n凭小票七日内可退换", "small")])], "split"),
                P("4月15日晚餐为与客户项目组的工作餐（3人：陈思远、鹏城科技园周磊、林晓雯），人均69.47元，在每人每餐150元的标准以内。"
                  "超市所购文具与数据线用于项目启动会，会后已交回华南市场部。"),
                table("budget", [["预算科目", "年度预算", "已使用", "本次报销", "剩余可用"],
                                 ["华南市场部 差旅费", num(budget), num(used), num(grand), num(budget - used - grand)]],
                      align=["l", "r", "r", "r", "r"], widths=[28, 18, 18, 18, 18], caption="部门预算执行情况（元）"),
                box("footnote", "注1：本报销单所附小票均为原件，已粘贴在第2号粘贴单上。"),
                box("footnote", "注2：金额以人民币元计，保留两位小数。"),
                P("报销人声明：以上费用均为本人因公出差实际发生，所附票据真实、完整，未在其他渠道重复报销。　签字：陈思远"),
            ],
        ],
    }


def receipts_th() -> dict[str, Any]:
    """Thai trip expense summary with VAT-inclusive receipts (pylopdf, Thai-script text boxes)."""
    thb = lambda c: number(c / 100, "th")  # noqa: E731
    head = ["รายการ", "จำนวน", "ราคา", "จำนวนเงิน"]
    checks: list[dict[str, Any]] = []
    totals: dict[str, int] = {}

    def make(tid: str, items: list[tuple[str, int, int]], vat: bool) -> dict[str, Any]:
        rows = [(text, q, str(q), unit) for text, q, unit in items]
        subtotal = sum(mul(q, u) for _t, q, u in items)
        before = part(subtotal, 100, 107)
        after = [("มูลค่าสินค้าก่อนภาษี", before), ("ภาษีมูลค่าเพิ่ม 7%", subtotal - before)] if vat else []
        block, more, value = receipt(tid, head, rows, thb, "รวมทั้งสิ้น", [], "รวมทั้งสิ้น", after=after, widths=[46, 14, 18, 22])
        checks.extend(more)
        totals[tid] = value
        return block

    cafe = make("th1", [("อเมริกาโน่เย็น", 2, 6500), ("ลาเต้ร้อน", 1, 7000), ("ครัวซองต์เนยสด", 2, 5500)], True)
    soi = make("th2", [("ข้าวซอยไก่", 3, 6000), ("ไส้อั่วชุดเล็ก", 1, 12000), ("แคบหมู", 1, 4000), ("น้ำมะนาวโซดา", 3, 3500)], False)
    pharm = make("th3", [("ยาแก้แพ้ ลอราทาดีน", 1, 8500), ("ผงเกลือแร่", 4, 1200), ("พลาสเตอร์ปิดแผล", 1, 3500)], True)
    store = make("th4", [("น้ำดื่ม 600 มล.", 3, 1000), ("ขนมปังไส้สังขยา", 2, 2500), ("ถ่านไฟฉาย AA แพ็ก 4", 1, 5900)], True)
    hotel = make("th5", [("ห้องพักดีลักซ์", 2, 145000), ("อาหารเช้าเพิ่ม", 1, 18000)], True)
    ride = make("th6", [("รถสองแถว ในเมือง", 4, 3000), ("รถรับส่งสนามบิน", 1, 15000)], False)
    entries = [("12/05/2569", "ร้านกาแฟบ้านดอย สาขานิมมานเหมินท์", "ค่ารับรอง", "th1"), ("12/05/2569", "ร้านข้าวซอยป้าแดง", "ค่าอาหาร", "th2"),
               ("13/05/2569", "เภสัชกรรมสุขภาพดี", "ค่ายาและเวชภัณฑ์", "th3"), ("14/05/2569", "ร้านสะดวกซื้อใกล้บ้าน สาขาสนามบิน", "ค่าใช้จ่ายเบ็ดเตล็ด", "th4"),
               ("12–14/05/2569", "โรงแรมเวียงพิงค์บูทีค", "ค่าที่พัก", "th5"), ("12–14/05/2569", "ค่าเดินทางในพื้นที่", "ค่าพาหนะ", "th6")]
    grand = sum(totals.values())
    summary = [["ลำดับ", "วันที่", "ผู้รับเงิน", "ประเภท", "จำนวนเงิน"], *[[str(n), w, who, kind, thb(totals[t])] for n, (w, who, kind, t) in enumerate(entries, start=1)],
               ["", "", "รวมทั้งสิ้น", "", thb(grand)]]
    checks.append({"kind": "column_sum", "table": "thsum", "columns": [4], "label_column": 2, "total_label": "รวมทั้งสิ้น"})

    def slip(title: str, meta: str, block: dict[str, Any], foot: str) -> dict[str, Any]:
        return group([P(title, "center"), P(meta, "small"), block, P(foot, "small")])

    return {
        "template": "retail_receipts", "page_size": "A4", "languages": ["th-TH"],
        "metadata": {"title": "สรุปค่าใช้จ่ายเดินทางไปเชียงใหม่ พฤษภาคม 2569", "author": "พิมพ์ชนก วงศ์ทอง",
                     "subject": "ใบสรุปค่าใช้จ่ายพร้อมใบเสร็จรับเงินและใบกำกับภาษีอย่างย่อ", "keywords": ["ใบเสร็จรับเงิน", "ค่าใช้จ่ายเดินทาง", "ภาษีมูลค่าเพิ่ม"],
                     "lang": "th-TH", "created": "2026-05-15T03:00:00Z"},
        "theme": {"accent": "#7a4b12", "py_size": 9.2},
        "running_header": "บริษัท สยามเกษตรอัจฉริยะ จำกัด · ใบสรุปค่าใช้จ่ายเดินทาง",
        "running_footer": "หน้า {page} จาก {pages}",
        "arithmetic": checks,
        "pages": [
            [
                P("บริษัท สยามเกษตรอัจฉริยะ จำกัด", "brand"),
                P("๘๘ ถนนวิภาวดีรังสิต แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร ๑๐๙๐๐ · โทร ๐๒ ๕๕๕ ๐๑๙๘", "small"),
                H(1, "ใบสรุปค่าใช้จ่ายเดินทาง"),
                group([P("ผู้เบิก: นางสาวพิมพ์ชนก วงศ์ทอง\nตำแหน่ง: ผู้จัดการฝ่ายขายภาคเหนือ\nรหัสพนักงาน: 610247", "meta"),
                       P("สถานที่: จังหวัดเชียงใหม่\nระยะเวลา: 12–14 พฤษภาคม 2569 รวม ๓ วัน ๒ คืน\nเลขที่ใบเบิก: EXP-2569-0512", "meta")], "split"),
                P("วัตถุประสงค์การเดินทาง: เข้าพบสหกรณ์ผู้ปลูกลำไยอำเภอสารภี เพื่อนำเสนอระบบตรวจวัดความชื้นในดินรุ่นใหม่ "
                  "และติดตั้งเครื่องต้นแบบจำนวน ๔ จุด ตามที่ได้ตกลงกับคณะกรรมการสหกรณ์ไว้เมื่อเดือนเมษายน"),
                table("thsum", summary, align=["c", "l", "l", "l", "r"], widths=[8, 16, 38, 20, 18], total_rows=[len(summary) - 1], caption="รายการค่าใช้จ่าย (บาท)"),
                box("callout", "ค่าที่พักไม่เกินอัตราที่บริษัทกำหนด คืนละ ๑,๕๐๐ บาท สำหรับต่างจังหวัด ค่ารับรองลูกค้าที่ร้านกาแฟเป็นการประชุมกับประธานสหกรณ์และเหรัญญิก",
                    title="หมายเหตุ", cls="note"),
                table("thsign", [["ผู้เบิก", "ผู้อนุมัติ", "ฝ่ายบัญชี"], ["พิมพ์ชนก วงศ์ทอง", "ธีรวัฒน์ แก้วมณี", "ศิริพร ทองดี"], ["15/05/2569", "", ""]],
                      align=["c", "c", "c"], widths=[34, 33, 33], caption="ลงนาม"),
            ],
            [
                H(2, "ใบเสร็จรับเงิน วันที่ ๑๒ พฤษภาคม"),
                group([slip("ร้านกาแฟบ้านดอย สาขานิมมานเหมินท์\nใบกำกับภาษีอย่างย่อ", "เลขที่ 0045127 · 12/05/2569 10:42\nเลขประจำตัวผู้เสียภาษี 0505561004417", cafe,
                            "ชำระด้วยพร้อมเพย์ · ราคารวมภาษีมูลค่าเพิ่มแล้ว"),
                       slip("ร้านข้าวซอยป้าแดง\nใบเสร็จรับเงิน", "เล่มที่ 12 เลขที่ 588 · 12/05/2569 12:35\nโต๊ะ 4 · 3 ท่าน", soi,
                            "ชำระเงินสด · ร้านไม่ได้จดทะเบียนภาษีมูลค่าเพิ่ม")], "split"),
                photo("cafe", ["coffee-cup", "bread-bakery"], ["food"], {"coffee-cup": "กาแฟระหว่างประชุมกับคณะกรรมการสหกรณ์"},
                      "ร้านกาแฟที่ใช้ประชุมกับลูกค้า", "left", width="38%"),
                P("การประชุมช่วงเช้าที่ร้านกาแฟใช้เวลาประมาณ ๒ ชั่วโมง ผู้เข้าร่วมได้แก่ คุณสมศักดิ์ ใจมั่น ประธานสหกรณ์ และคุณอรุณี ศรีวงศ์ เหรัญญิก "
                  "ที่ประชุมตกลงให้ติดตั้งเครื่องต้นแบบในแปลงสมาชิก ๔ ราย และจะประเมินผลหลังเก็บเกี่ยวในเดือนสิงหาคม"),
                P("มื้อกลางวันเป็นการรับประทานอาหารร่วมกับเจ้าหน้าที่ภาคสนามของบริษัทอีก ๒ คน ซึ่งเดินทางมาจากลำพูนเพื่อช่วยติดตั้งเครื่อง "
                  "ร้านไม่ได้ออกใบกำกับภาษีเนื่องจากไม่ได้จดทะเบียนภาษีมูลค่าเพิ่ม จึงแนบใบเสร็จรับเงินแบบเล่มแทน"),
                P("ใบเสร็จทุกใบเป็นต้นฉบับ สแกนด้วยความละเอียด ๓๐๐ จุดต่อนิ้ว และเก็บต้นฉบับไว้ที่ฝ่ายบัญชี", "small"),
            ],
            [
                H(2, "ใบเสร็จรับเงิน วันที่ ๑๓–๑๔ พฤษภาคม"),
                group([slip("เภสัชกรรมสุขภาพดี\nใบกำกับภาษีอย่างย่อ", "เลขที่ 26-01733 · 13/05/2569 18:05", pharm, "ชำระเงินสด"),
                       slip("ร้านสะดวกซื้อใกล้บ้าน สาขาสนามบิน\nใบกำกับภาษีอย่างย่อ", "เลขที่ 3317-0098821 · 14/05/2569 16:22", store, "ชำระด้วยบัตรเดบิต")], "split"),
                group([slip("โรงแรมเวียงพิงค์บูทีค\nใบเสร็จรับเงิน/ใบกำกับภาษี", "เลขที่ INV-690514-031 · เช็คเอาท์ 14/05/2569\nห้อง 207 · 2 คืน", hotel,
                            "ชำระด้วยบัตรเครดิตบริษัท"),
                       slip("ค่าพาหนะในพื้นที่\nใบรับรองแทนใบเสร็จรับเงิน", "12–14/05/2569 · ไม่มีใบเสร็จจากผู้ให้บริการ", ride,
                            "ผู้เบิกรับรองว่าได้จ่ายจริง")], "split"),
                box("footnote", "๑ ค่ารถสองแถวและรถรับส่งสนามบินไม่มีใบเสร็จ จึงใช้ใบรับรองแทนใบเสร็จรับเงินตามระเบียบของบริษัท"),
                P("ข้าพเจ้าขอรับรองว่าค่าใช้จ่ายข้างต้นได้จ่ายไปจริงเพื่อกิจการของบริษัท และไม่ได้เบิกซ้ำจากแหล่งอื่น"),
            ],
        ],
    }


def receipts_vi() -> dict[str, Any]:
    """Vietnamese business-trip receipt bundle (LibreOffice, untagged) with one NFD paragraph."""
    vnd = lambda v: number(v, "vi")  # noqa: E731
    head = ["Tên hàng", "SL", "Đơn giá", "Thành tiền"]
    checks: list[dict[str, Any]] = []
    totals: dict[str, int] = {}

    def make(tid: str, items: list[tuple[str, float, str, int]], vat: str, caption: str) -> dict[str, Any]:
        subtotal = sum(mul(q, u) for _t, q, _s, u in items)
        if vat == "add":
            block, more, value = receipt(tid, head, items, vnd, "Tạm tính", [("Thuế GTGT 8%", part(subtotal, 8, 100))], "Tổng cộng", caption=caption, widths=[50, 10, 18, 22], decimal=",")
        elif vat == "incl":
            before = part(subtotal, 100, 108)
            block, more, value = receipt(tid, head, items, vnd, "Tổng cộng", [], "Tổng cộng", caption=caption, widths=[50, 10, 18, 22], decimal=",",
                                         after=[("Giá chưa thuế", before), ("Thuế GTGT 8%", subtotal - before)])
        else:
            block, more, value = receipt(tid, head, items, vnd, "Tổng cộng", [], "Tổng cộng", caption=caption, widths=[50, 10, 18, 22], decimal=",")
        checks.extend(more)
        totals[tid] = value
        return block

    taxi = make("v1", [("Cước taxi Sân bay Đà Nẵng – Khách sạn (9,6 km)", 1, "1", 152000), ("Phí vào sân bay", 1, "1", 15000)], "none",
                "Biên nhận taxi Tiên Sa — xe 43A-218.65")
    pho = make("v2", [("Phở bò tái nạm", 2, "2", 65000), ("Mì Quảng gà", 1, "1", 55000), ("Bánh xèo (đĩa)", 1, "1", 70000),
                      ("Trà đá", 3, "3", 5000), ("Nước sâm", 2, "2", 15000)], "add", "Hóa đơn bán lẻ — Quán Mì Quảng Bà Mua 2")
    market = make("v3", [("Nước suối Lavie 500 ml", 6, "6", 6500), ("Giấy A4 Double A (ram)", 1, "1", 89000), ("Bút bi Thiên Long TL-027 (hộp)", 1, "1", 48000),
                         ("Băng keo trong 5 cm", 2, "2", 18500), ("Bánh đậu xanh Hải Dương (hộp)", 3, "3", 42000)], "incl", "Phiếu tính tiền — Siêu thị Hoa Sen Hải Châu")
    hotel = make("v4", [("Phòng Superior hướng biển (đêm)", 2, "2", 980000), ("Giặt ủi", 1, "1", 85000), ("Minibar — nước suối", 2, "2", 20000)], "add",
                 "Hóa đơn GTGT — Khách sạn Biển Ngọc")
    entries = [("1", "06/05/2026", "Taxi Tiên Sa", "Đi lại", "v1"), ("2", "06/05/2026", "Quán Mì Quảng Bà Mua 2", "Tiếp khách", "v2"),
               ("3", "07/05/2026", "Siêu thị Hoa Sen", "Văn phòng phẩm, quà tặng", "v3"), ("4", "08/05/2026", "Khách sạn Biển Ngọc", "Lưu trú", "v4")]
    allowance = 3 * 200000
    grand = sum(totals.values()) + allowance
    rows = [["STT", "Ngày", "Đơn vị bán", "Nội dung", "Số tiền (₫)"], *[[a, b, c, d_, vnd(totals[t])] for a, b, c, d_, t in entries],
            ["5", "06–08/05/2026", "—", "Phụ cấp lưu trú 3 ngày × 200.000", vnd(allowance)], ["", "", "Tổng cộng", "", vnd(grand)]]
    checks.append({"kind": "column_sum", "table": "vsum", "columns": [4], "label_column": 2, "total_label": "Tổng cộng"})
    return {
        "template": "retail_receipts", "page_size": "A4", "languages": ["vi-VN"], "tagged": False,
        "metadata": {"title": "Bảng kê chứng từ công tác phí — Đà Nẵng, tháng 5/2026", "author": "Nguyễn Thị Thu Hà",
                     "subject": "Thanh toán công tác phí kèm hóa đơn bán lẻ và hóa đơn GTGT", "keywords": ["công tác phí", "hóa đơn", "thuế GTGT", "bảng kê"],
                     "lang": "vi-VN", "created": "2026-05-11T02:15:00Z"},
        "theme": {"accent": "#0b5d3b", "lo_size": "9.5pt", "lo_font": "Noto Sans"},
        "running_header": "Công ty TNHH Sao Mai Logistics · Bảng kê chứng từ BK-0526",
        "running_footer": "Trang {page}/{pages}",
        "arithmetic": checks,
        "pages": [
            [
                P("CÔNG TY TNHH SAO MAI LOGISTICS", "brand"),
                P("Số 27 Trần Quang Khải, phường Hoàn Kiếm, Hà Nội · MST 0108 552 417 · ĐT 024 3555 0172", "small"),
                H(1, "Bảng kê chứng từ thanh toán công tác phí"),
                P("**Người đề nghị:** Nguyễn Thị Thu Hà — Phòng Kinh doanh\n**Nơi công tác:** Thành phố Đà Nẵng · **Thời gian:** 06/05/2026 – 08/05/2026\n"
                  "**Mục đích:** Khảo sát kho ngoại quan tại KCN Hòa Khánh và làm việc với khách hàng Thủy sản Sơn Trà", "meta"),
                table("vsum", rows, align=["c", "l", "l", "l", "r"], widths=[6, 16, 28, 32, 18], total_rows=[len(rows) - 1], caption="Bảng tổng hợp chi phí"),
                P(f"Số tiền đề nghị thanh toán: **{money(grand, 'vi')}**\nBằng chữ: *{vn_words(grand)}*."),
                P("Vé máy bay Hà Nội – Đà Nẵng khứ hồi do phòng Hành chính đặt và thanh toán trực tiếp, không nằm trong bảng kê này."),
                H(2, "Chứng từ 1 — Taxi từ sân bay"),
                taxi,
                P("Thanh toán tiền mặt. Biên nhận in từ đồng hồ tính cước, có chữ ký tài xế.", "small"),
            ],
            [
                H(2, "Chứng từ 2 — Ăn trưa tiếp khách"),
                P("Quán Mì Quảng Bà Mua 2 · 19–21 Trần Bình Trọng, Hải Châu, Đà Nẵng · Bàn 7 · 12:18 ngày 06/05/2026", "small"),
                pho,
                P("Khách mời: ông Lê Văn Phúc (Giám đốc kho vận, Thủy sản Sơn Trà) và bà Trần Mỹ Linh (Kế toán trưởng). Thanh toán qua chuyển khoản QR."),
                H(2, "Chứng từ 3 — Văn phòng phẩm và quà tặng"),
                P("Siêu thị Hoa Sen · 255 Hùng Vương, Hải Châu · Quầy 05 · 17:40 ngày 07/05/2026 · Giá đã bao gồm thuế GTGT", "small"),
                market,
                P("Giấy và bút dùng để in biên bản khảo sát tại kho; bánh đậu xanh là quà biếu đối tác theo định mức tiếp khách của công ty. "
                  "Thanh toán bằng thẻ ghi nợ cá nhân, số thẻ kết thúc bằng 4471.", "small"),
                box("callout", "Hóa đơn bán lẻ dưới 200.000 ₫ được chấp nhận theo quy chế chi tiêu nội bộ; các khoản từ 200.000 ₫ trở lên cần "
                    "hóa đơn điện tử có mã của cơ quan thuế và ghi đúng tên, mã số thuế của công ty.", title="Lưu ý", cls="note"),
            ],
            [
                H(2, "Chứng từ 4 — Khách sạn"),
                P("Khách sạn Biển Ngọc · 118 Võ Nguyên Giáp, Sơn Trà, Đà Nẵng · Hóa đơn điện tử số 00004127, ký hiệu 1C26TBN · MST 0401 776 258", "small"),
                hotel,
                P("Nhận phòng 06/05/2026, trả phòng 08/05/2026, phòng 506. Thanh toán bằng thẻ tín dụng công ty."),
                nfd(P("Ghi chú của người đề nghị: chi phí giặt ủi phát sinh do lịch làm việc kéo dài sang ngày thứ ba; minibar chỉ dùng nước suối. "
                      "Toàn bộ chứng từ gốc đã được dán vào giấy dán chứng từ và nộp cho phòng Kế toán ngày 11/05/2026.")),
                box("footnote", "¹ Thuế suất GTGT 8% áp dụng theo chính sách giảm thuế đang có hiệu lực đối với dịch vụ ăn uống và lưu trú."),
                table("vsign", [["Người đề nghị", "Trưởng phòng", "Kế toán", "Giám đốc"], ["Nguyễn Thị Thu Hà", "Phạm Quốc Bảo", "Đỗ Minh Trang", "Vũ Đức Long"],
                                ["(đã ký)", "", "", ""]], align=["c", "c", "c", "c"], widths=[25, 25, 25, 25], caption="Xác nhận"),
            ],
        ],
    }



# ====================================================================== utility bills


def dmul(quantity: str, unit: str) -> int:
    """Exact ``quantity x unit`` (plain decimal strings) in minor units, rounded half up."""
    return int((Decimal(quantity) * Decimal(unit) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def utility_en() -> dict[str, Any]:
    """US electric bill with net metering (LibreOffice, tagged, raster usage chart, payment stub)."""
    usd = lambda c: money(c, "en-US")  # noqa: E731
    delivered = (48213, 49026)
    received = (7904, 8192)
    used = delivered[1] - delivered[0]
    exported = received[1] - received[0]
    net = used - exported
    lines = [("Basic charge", "1", "11.50", "per month"), ("Delivery charge", str(net), "0.04812", "per kWh"),
             ("Energy charge, first 1,000 kWh", str(net), "0.07531", "per kWh"), ("Transmission adjustment", str(net), "0.00384", "per kWh"),
             ("Low-income assistance", "1", "0.55", "per month")]
    rows = [["Description", "Quantity", "Rate", "Amount"]]
    subtotal = 0
    for label, qty, rate, unit in lines:
        value = dmul(qty, rate)
        subtotal += value
        rows.append([label, f"{int(qty):,} kWh" if "kWh" in unit else qty, f"${rate} {unit}", usd(value)])
    public = part(subtotal, 30, 1000)
    franchise = part(subtotal + public, 35, 1000)
    rows += [["Public purpose charge (3.0%)", "", "", usd(public)], ["City of Corvallis franchise fee (3.5%)", "", "", usd(franchise)]]
    current = subtotal + public + franchise
    rows.append(["Total current charges", "", "", usd(current)])
    previous, payment = 14218, 14218
    months = ["May 25", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan 26", "Feb", "Mar", "Apr", "May 26"]
    spec = {"title": "Net kWh billed per month", "categories": months,
            "series": [("Net kWh", [611, 402, 455, 498, 371, 512, 846, 1104, 1187, 1012, 798, 641, net])], "max": 1400, "ticks": 7,
            "tick_format": lambda v: f"{v:,.0f}", "colors": ["#2e6f95"]}
    meter = table("meter", [["Meter", "Register", "Read date", "Previous", "Current", "Multiplier", "kWh"],
                            ["CPL 7740218", "Delivered from grid", "05/06/2026", f"{delivered[0]:,}", f"{delivered[1]:,}", "1", f"{used:,}"],
                            ["CPL 7740218", "Received from your solar", "05/06/2026", f"{received[0]:,}", f"{received[1]:,}", "1", f"−{exported:,}"],
                            ["", "Net energy billed", "", "", "", "", f"{net:,}"]],
                  align=["l", "l", "c", "r", "r", "c", "r"], widths=[14, 24, 13, 13, 13, 10, 13], total_rows=[3], caption="Meter readings — actual reads")
    return {
        "template": "utility_bill", "page_size": "Letter", "languages": ["en-US", "es", "vi", "zh-Hant", "ru"], "tagged": True,
        "metadata": {"title": "Cascadia Power & Light — electric bill, May 2026", "author": "Cascadia Power & Light",
                     "subject": "Residential electric service with net metering, service period 04/06/2026–05/06/2026",
                     "keywords": ["utility bill", "electricity", "net metering", "kWh"], "lang": "en-US", "created": "2026-05-08T11:00:00Z"},
        "theme": {"accent": "#2e6f95", "lo_size": "9.5pt", "lo_font": "Noto Sans", "content_cm": 17.6},
        "running_header": "Cascadia Power & Light · Account 3302-118-4470 · Bill date May 8, 2026",
        "running_footer": "Page {page} of {pages}",
        "arithmetic": [
            {"kind": "line_items", "table": "charges", "quantity": 1, "unit_price": 2, "amount": 3, "decimal": "."},
            {"kind": "column_sum", "table": "charges", "columns": [3], "label_column": 0, "total_label": "Total current charges"},
            {"kind": "column_sum", "table": "meter", "columns": [6], "label_column": 1, "total_label": "Net energy billed"},
            {"kind": "sum", "terms": [["+", usd(previous)], ["-", usd(payment)], ["+", usd(current)]], "equals": usd(previous - payment + current)},
        ],
        "pages": [
            [
                P("Cascadia Power & Light", "brand"),
                P("PO Box 4100, Salem, OR 97302 · Customer service 1-800-555-0144 · Outages 1-800-555-0145 · cascadiapower.example", "small"),
                H(1, "Your electric bill"),
                P("**Mei-Ling Hartwell**\nService address: 715 NW Hawthorne Ave, Corvallis, OR 97330\n**Account number:** 3302-118-4470\n"
                  "**Service period:** 04/06/2026 – 05/06/2026 (30 days)\n**Rate schedule:** Residential Service, Schedule 7 with net metering", "meta"),
                table("acct", [["Account summary", ""], ["Previous balance", usd(previous)], ["Payment received 04/28/2026 — thank you", "−" + usd(payment)],
                               ["Balance forward", "$0.00"], ["Current charges", usd(current)], ["Total amount due by 05/29/2026", usd(previous - payment + current)]],
                      rendering="borderless", align=["l", "r"], widths=[70, 30], total_rows=[5]),
                box("callout", f"Your solar system sent {exported} kWh back to the grid this month, which offset {round(exported / used * 100)}% of the "
                    f"energy you used. You are billed for the net {net} kWh. Excess generation in a month rolls forward as a kWh credit.",
                    title="Net metering at a glance", cls="note"),
                P("Your next meter read is scheduled for June 5, 2026. Readings are transmitted automatically by your smart meter; no "
                  "one needs access to your property."),
                P("Para recibir ayuda en español, llame al 1-800-555-0146. Để được hỗ trợ bằng tiếng Việt, xin gọi 1-800-555-0147. "
                  "如需中文服務，請致電 1-800-555-0148。 Помощь на русском языке: 1-800-555-0149.", "small"),
                box("callout", "Spring storm season is here. Never touch a downed line; stay at least 35 feet away and call 1-800-555-0145. "
                    "Sign up for outage texts at cascadiapower.example/alerts.", title="Safety reminder", cls="warn"),
            ],
            [
                H(2, "Your energy use"),
                meter,
                chart("usage", "bar", spec, "Monthly net energy use, May 2025 – May 2026", raster=True, width="92%", width_cm=15.5, size=(640, 240)),
                chart_table("usage-data", "Month", spec, lambda v: f"{v:,}"),
                P("Your net use was lower than in May last year mainly because of longer daylight hours: your panels produced more "
                  "while the household’s daytime use stayed about the same. Winter months show higher net use because the heat pump "
                  "runs more and solar output is low between November and February."),
                table("compare", [["", "This period", "Same period last year"], ["Days in billing period", "30", "30"], ["Net kWh billed", f"{net:,}", "611"],
                                  ["Average daily kWh", f"{net / 30:.1f}", f"{611 / 30:.1f}"], ["Average temperature", "58 °F", "55 °F"],
                                  ["Solar kWh sent to grid", f"{exported:,}", "241"]],
                      align=["l", "r", "r"], widths=[50, 25, 25], caption="Usage comparison"),
            ],
            [
                H(2, "Detail of current charges"),
                table("charges", rows, align=["l", "r", "r", "r"], widths=[46, 16, 22, 16], total_rows=[len(rows) - 1],
                      caption="Residential Service — Schedule 7, net metering"),
                photo("solar", ["solar-panels"], ["energy"], {"solar-panels": "Rooftop solar arrays like yours offset part of each month’s use."},
                      "Rooftop solar", "right", width="38%", width_cm=6.2),
                P("Under net metering, the energy your panels deliver to the grid is subtracted from the energy you take from it. "
                  "Charges that depend on kWh use the net amount; the basic charge and assistance charge apply every month regardless "
                  "of how much energy you use."),
                P("Unused credits roll forward month to month. Any credits remaining at the end of the March billing cycle are "
                  "donated to the Cascadia low-income assistance fund, as required by Oregon net metering rules."),
                P("The public purpose charge funds energy-efficiency programs and is set by the state at 3% of electricity service "
                  "charges. The franchise fee is collected for the City of Corvallis for the use of public rights-of-way."),
                box("footnote", "¹ Rates effective January 1, 2026, as approved by the Oregon Public Utility Commission in Order 25-418."),
                box("footnote", "² The transmission adjustment is reviewed annually and may change on June 1."),
            ],
            [
                H(2, "Ways to pay"),
                L(["Online or in the Cascadia app — free, with card, bank account or digital wallet",
                   "AutoPay — enroll at cascadiapower.example/autopay; your bill is paid on the due date",
                   "By phone — 1-800-555-0144, available 24 hours (a $1.95 convenience fee applies to card payments)",
                   "In person — any PayNearMe location; bring the barcode from this page",
                   "By mail — return the stub below with a check payable to Cascadia Power & Light"]),
                box("sidebar", "If you are having trouble paying, ask about Equal Pay, payment arrangements and the Oregon Energy "
                    "Assistance Program. Households at or below 60% of state median income may qualify for a monthly bill discount of "
                    "up to 40%.", title="Help paying your bill"),
                H(3, "Understanding your bill"),
                L(["**kWh (kilowatt-hour):** the unit used to measure electricity; a 1,000-watt heater running for one hour uses 1 kWh.",
                   "**Net energy billed:** energy delivered from the grid minus energy your solar system sent to the grid.",
                   "**Basic charge:** a fixed monthly charge that covers metering, billing and customer service.",
                   "**Delivery charge:** the cost of moving electricity over local poles, wires and substations to your home."]),
                P("Please detach and return the portion below with your payment. Do not staple or fold.", "small"),
                table("stub", [["Account number", "Due date", "Total amount due", "Amount enclosed"],
                               ["3302-118-4470", "05/29/2026", usd(previous - payment + current), "$ ____________"]],
                      align=["l", "c", "r", "r"], widths=[30, 20, 25, 25], caption="Payment stub"),
                P("MEI-LING HARTWELL\n715 NW HAWTHORNE AVE\nCORVALLIS OR 97330-4417", "meta"),
                P("CASCADIA POWER & LIGHT\nPO BOX 4100\nSALEM OR 97302-4100", "meta"),
                P("33021184470 0000" + f"{previous - payment + current:07d}" + " 0529 7", "small"),
            ],
        ],
    }


def utility_de() -> dict[str, Any]:
    """German annual electricity bill (ReportLab, Standard 14 Helvetica, native vector chart)."""
    eur = lambda c: money(c, "de")  # noqa: E731
    shy = "\u00ad"
    readings = [(41287, 42701, "31.12.2024", "30.06.2025", "geschätzt"), (42701, 44163, "30.06.2025", "31.12.2025", "Kundenablesung")]
    k1, k2 = (b - a for a, b, *_ in readings)
    lines = [("Arbeitspreis", "01.01.–30.06.2025", f"{number(k1, 'de', 0)} kWh", str(k1), "0.3245", "0,3245 €/kWh"),
             ("Arbeitspreis", "01.07.–31.12.2025", f"{number(k2, 'de', 0)} kWh", str(k2), "0.2989", "0,2989 €/kWh"),
             ("Grundpreis", "01.01.–30.06.2025", "181 Tage", "181", "0.4110", "0,4110 €/Tag"),
             ("Grundpreis", "01.07.–31.12.2025", "184 Tage", "184", "0.4110", "0,4110 €/Tag"),
             ("Messstellenbetrieb (moderne Messeinrichtung)", "01.01.–31.12.2025", "12 Monate", "12", "1.6807", "1,6807 €/Monat")]
    rows = [["Position", "Zeitraum", "Menge", "Preis (netto)", "Betrag (netto)"]]
    net = 0
    for label, period, shown, qty, rate, rate_shown in lines:
        value = dmul(qty, rate)
        net += value
        rows.append([label, period, shown, rate_shown, eur(value)])
    rows.append(["Summe netto", "", "", "", eur(net)])
    vat = part(net, 19, 100)
    gross = net + vat
    paid = 12 * 7200
    balance = gross - paid
    forecast = dmul("2900", "0.2989") + dmul("365", "0.4110") + dmul("12", "1.6807")
    new_rate = -(-part(forecast, 119, 100) // 1200) * 100
    spec = {"title": "Ihr Stromverbrauch im Vergleich (kWh)", "categories": ["2023", "2024", "2025", "Ø 3-Personen-Haushalt"],
            "series": [("Verbrauch", [3184, 3012, k1 + k2, 3500])], "max": 4000, "ticks": 4, "tick_format": lambda v: number(v, "de", 0),
            "colors": ["#3d6b35"]}
    mix = [["Energieträger", "Stadtwerke Lindenau", "Deutschland"], ["Erneuerbare Energien (EEG-gefördert)", "52,4 %", "56,1 %"],
           ["Erneuerbare Energien, nicht gefördert", "21,8 %", "4,2 %"], ["Erdgas", "14,6 %", "14,9 %"], ["Kohle", "9,7 %", "22,6 %"],
           ["Sonstige fossile Energieträger", "1,5 %", "2,2 %"], ["Summe", "100,0 %", "100,0 %"]]
    return {
        "template": "utility_bill", "page_size": "A4", "languages": ["de-DE"],
        "metadata": {"title": "Jahresabrechnung Strom 2025 – Stadtwerke Lindenau", "author": "Stadtwerke Lindenau GmbH",
                     "subject": "Stromabrechnung für den Zeitraum 01.01.2025 bis 31.12.2025, Vertragskonto 2004 7713 58",
                     "keywords": ["Stromrechnung", "Jahresabrechnung", "Abschlag", "Zählerstand"], "lang": "de-DE", "created": "2026-01-19T07:30:00Z"},
        "theme": {"accent": "#3d6b35", "rl_size": 9.2},
        "running_header": "Stadtwerke Lindenau GmbH · Jahresabrechnung Strom 2025 · Vertragskonto 2004 7713 58",
        "running_footer": "Seite {page} von {pages}",
        "arithmetic": [
            {"kind": "line_items", "table": "rechnung", "quantity": 2, "unit_price": 3, "amount": 4, "decimal": ","},
            {"kind": "column_sum", "table": "rechnung", "columns": [4], "label_column": 0, "total_label": "Summe netto"},
            {"kind": "sum", "terms": [["+", eur(net)], ["+", eur(vat)]], "equals": eur(gross)},
            {"kind": "sum", "terms": [["+", eur(gross)], ["-", eur(paid)]], "equals": eur(balance)},
            {"kind": "column_sum", "table": "mix", "columns": [1, 2], "label_column": 0, "total_label": "Summe"},
            {"kind": "column_sum", "table": "bestandteile", "columns": [1], "label_column": 0, "total_label": "Arbeitspreis gesamt"},
        ],
        "pages": [
            [
                group([P("Stadtwerke Lindenau", "brand"), P("Stadtwerke Lindenau GmbH · Industriestraße 40 · 04179 Leipzig\nKundenservice 0341 555 2200 · service@sw-lindenau.example", "small right")], "letterhead"),
                group([P("Familie Brückner\nAm Mühlgraben 14\n04179 Leipzig", "meta"),
                       P("**Vertragskonto:** 2004 7713 58\n**Rechnungsnummer:** 2026-0119-44817\n**Rechnungsdatum:** 19.01.2026\n**Lieferstelle:** Am Mühlgraben 14, 04179 Leipzig\n**Marktlokation:** 50417382915", "meta")], "split"),
                H(1, "Ihre Jahresabrechnung Strom 2025"),
                P("Sehr geehrte Familie Brückner,\nvielen Dank, dass Sie Strom von den Stadtwerken Lindenau beziehen. Mit dieser Rechnung "
                  "rechnen wir Ihren Verbrauch vom 01.01.2025 bis 31.12.2025 ab. Zum 01.07.2025 haben wir den Arbeitspreis gesenkt; "
                  "dafür haben wir Ihren Zählerstand zum Stichtag rechnerisch ermittelt."),
                table("summe", [["Ihre Rechnung auf einen Blick", ""], ["Rechnungsbetrag (brutto)", eur(gross)], ["abzüglich geleisteter Abschläge (12 × 72,00 €)", "−" + eur(paid)],
                                ["Nachzahlung", eur(balance)]], rendering="borderless", align=["l", "r"], widths=[70, 30], total_rows=[3]),
                box("callout", f"Die Nachzahlung von {eur(balance)} buchen wir am 05.02.2026 per SEPA-Lastschrift von Ihrem Konto "
                    f"DE12 8605 5592 •••• 4471 ab. Ihr neuer monatlicher Abschlag beträgt ab dem 15.02.2026 **{eur(new_rate)}**.",
                    title="Das ist zu tun: nichts", cls="note"),
                H(2, "Zählerstände"),
                table("zaehler", [["Zählernummer", "Ablesedatum alt", "Stand alt", "Ablesedatum neu", "Stand neu", "Verbrauch", "Ableseart"],
                                  *[["1ESY1160 4471 23", a_d, number(a, "de", 0), b_d, number(b, "de", 0), f"{number(b - a, 'de', 0)} kWh", how]
                                    for a, b, a_d, b_d, how in readings]],
                      align=["l", "c", "r", "c", "r", "r", "l"], widths=[18, 13, 11, 13, 11, 14, 20]),
                P(f"Gesamtverbrauch 2025: **{number(k1 + k2, 'de', 0)} kWh** — das sind {number((k1 + k2) / 365, 'de', 1)} kWh pro Tag.", "small"),
                table("vertrag", [["Ihr Vertrag", ""], ["Tarif", "LindenStrom Fix 24"], ["Vertragsbeginn", "01.07.2023"],
                                  ["Preisgarantie (ohne Steuern und Umlagen)", "bis 30.06.2026"], ["Kündigungsfrist", "1 Monat zum Monatsende"],
                                  ["Zahlungsweise", "SEPA-Lastschrift, Mandat ML-2004771358"]],
                      rendering="borderless", align=["l", "r"], widths=[55, 45]),
            ],
            [
                H(2, "Rechnungsdetails"),
                table("rechnung", rows, align=["l", "l", "r", "r", "r"], widths=[34, 20, 14, 16, 16], total_rows=[len(rows) - 1]),
                table("brutto", [["Summe netto", eur(net)], ["Umsatzsteuer 19 %", eur(vat)], ["Rechnungsbetrag brutto", eur(gross)]], header_rows=0,
                      rendering="borderless", align=["l", "r"], widths=[70, 30], total_rows=[2]),
                P(f"Im Arbeitspreis enthalten sind Netz{shy}nutzungs{shy}entgelt (8,21 ct/kWh), Strom{shy}steuer (2,05 ct/kWh), "
                  f"Konzessions{shy}abgabe (1,32 ct/kWh) sowie die Umlagen nach KWKG und § 19 StromNEV. Die Preise verstehen sich netto¹."),
                table("bestandteile", [["Bestandteil des Arbeitspreises ab 01.07.2025", "ct/kWh netto"], ["Energiebeschaffung und Vertrieb", "15,65"],
                                       ["Netznutzungsentgelt", "8,21"], ["Stromsteuer", "2,05"], ["Konzessionsabgabe", "1,32"], ["Umlage nach § 19 StromNEV", "1,56"],
                                       ["Offshore-Netzumlage", "0,82"], ["KWKG-Umlage", "0,28"], ["Arbeitspreis gesamt", "29,89"]],
                      rendering="borderless", align=["l", "r"], widths=[70, 30], total_rows=[8]),
                chart("vergleich", "bar", spec, "Abbildung: Jahresverbrauch im Vergleich", raster=False, width="80%", width_cm=13, size=(520, 220)),
                chart_table("vergleich-data", "Jahr", spec, lambda v: number(v, "de", 0)),
                box("footnote", "¹ Alle Preise netto zzgl. 19 % Umsatzsteuer. Der Grundpreis wird taggenau abgerechnet."),
                box("footnote", "² Durchschnittswert laut Stromspiegel für Deutschland 2025, Mehrfamilienhaus ohne Warmwasserbereitung."),
            ],
            [
                H(2, "Ihr neuer Abschlag"),
                P(f"Für 2026 erwarten wir einen Verbrauch von rund 2.900 kWh. Daraus ergibt sich ein Jahresbetrag von {eur(part(forecast, 119, 100))} "
                  f"brutto und ein monatlicher Abschlag von **{eur(new_rate)}** (auf volle Euro aufgerundet)."),
                table("abschlag", [["Fälligkeit", "Betrag"], *[[f"15.{m:02d}.2026", eur(new_rate)] for m in (2, 3, 4, 5, 6, 7)], ["… monatlich bis 15.12.2026", eur(new_rate)]],
                      rendering="borderless", align=["l", "r"], widths=[60, 40], caption="Abschlagsplan (Auszug)"),
                H(2, "Stromkennzeichnung"),
                table("mix", mix, align=["l", "r", "r"], widths=[50, 25, 25], total_rows=[6], caption="Energieträgermix nach § 42 EnWG (Bezugsjahr 2024)"),
                P("CO2-Emissionen: 198 g/kWh (Deutschland: 381 g/kWh). Radioaktiver Abfall: 0,0000 g/kWh.", "small"),
                H(2, "Wichtige Hinweise"),
                L(["Bei Fragen zu Ihrer Rechnung erreichen Sie uns montags bis freitags von 8 bis 18 Uhr unter 0341 555 2200.",
                   ("Verbraucherbeschwerden richten Sie bitte zuerst an uns. Wird ihnen nicht abgeholfen, können Sie die Schlichtungsstelle "
                    "Energie e. V., Friedrichstraße 133, 10117 Berlin, anrufen."),
                   "Sie können Ihren Vertrag mit einer Frist von einem Monat zum Monatsende kündigen; Ihre Preisgarantie gilt bis 30.06.2026.",
                   "Informationen zu Energiedienstleistungen und Effizienzmaßnahmen finden Sie unter sw-lindenau.example/energiesparen."]),
                table("bank", [["Empfänger", "Stadtwerke Lindenau GmbH"], ["IBAN", "DE44 8605 5592 1100 4471 00"], ["BIC", "WELADE8LXXX"],
                               ["Verwendungszweck", "VK 2004771358 RG 2026-0119-44817"], ["Gläubiger-ID", "DE98ZZZ00000447121"]], header_rows=0,
                      align=["l", "l"], widths=[30, 70], caption="Bankverbindung für Überweisungen"),
            ],
        ],
    }



def utility_hi() -> dict[str, Any]:
    """Hindi commercial electricity bill with English code-switching, lakh grouping and a raster chart (chromium)."""
    inr = lambda c: money(c, "hi")  # noqa: E731
    grp = lambda v: number(v, "hi", 0)  # noqa: E731
    kwh = (284615, 298465)
    kvah = (301220, 315840)
    units = kwh[1] - kwh[0]
    lines = [("स्थायी शुल्क (Fixed Charge) — संविदा भार", "60 kW", "60", "450.00"), ("ऊर्जा शुल्क, 0–1000 यूनिट", grp(1000), "1000", "7.50"),
             ("ऊर्जा शुल्क, 1000 से अधिक यूनिट", grp(units - 1000), str(units - 1000), "8.40"),
             ("ईंधन एवं विद्युत क्रय समायोजन (FPPAS)", grp(units), str(units), "0.18"), ("मीटर किराया (3-फेज़ CT मीटर)", "1", "1", "250.00")]
    rows = [["विवरण / Particulars", "मात्रा", "दर (₹)", "राशि"]]
    subtotal = 0
    for label, shown, qty, rate in lines:
        value = dmul(qty, rate)
        subtotal += value
        rows.append([label, shown, rate, inr(value)])
    duty_base = subtotal - dmul("1", "250.00")
    duty = part(duty_base, 75, 1000)
    rows.append(["विद्युत शुल्क (Electricity Duty) @ 7.5%", "", "", inr(duty)])
    current = subtotal + duty
    rows.append(["चालू माह का कुल बिल", "", "", inr(current)])
    rounded = (current + 50) // 100 * 100
    adjust = rounded - current
    rebate = min(part(dmul(str(units), "7.50"), 1, 100) // 100 * 100, 100000)
    months = ["जून", "जुलाई", "अग.", "सित.", "अक्टू.", "नव.", "दिस.", "जन.", "फर.", "मार्च", "अप्रै.", "मई"]
    spec = {"title": "मासिक खपत (यूनिट / kWh)", "categories": months,
            "series": [("खपत", [17420, 16880, 15910, 14230, 11650, 9340, 8920, 9180, 9760, 11240, 12960, units])], "max": 20000, "ticks": 4,
            "tick_format": grp, "colors": ["#c2571a"]}
    history = [["दिनांक", "रसीद संख्या", "माध्यम", "राशि"], ["14.04.2026", "OL2604140918", "UPI", inr(13814600)], ["13.03.2026", "OL2603130442", "NEFT", inr(11927300)],
               ["12.02.2026", "OL2602120117", "UPI", inr(10318500)], ["14.01.2026", "CS2601140022", "चेक (Cheque)", inr(9876200)],
               ["", "कुल भुगतान (4 माह)", "", inr(13814600 + 11927300 + 10318500 + 9876200)]]
    return {
        "template": "utility_bill", "page_size": "A4", "languages": ["hi-IN", "en-IN"],
        "metadata": {"title": "बिजली बिल मई 2026 — होटल गंगा व्यू, वाराणसी", "author": "काशी विद्युत वितरण कंपनी लिमिटेड",
                     "subject": "वाणिज्यिक विद्युत संयोजन (LMV-2) का मासिक बिल, खाता संख्या 4417 2039 5518",
                     "keywords": ["बिजली बिल", "LMV-2", "विद्युत शुल्क", "भुगतान पर्ची"], "lang": "hi-IN", "created": "2026-05-14T04:45:00Z"},
        "theme": {"accent": "#c2571a", "font_size": "9.4pt", "margins": "14mm 14mm 16mm 14mm"},
        "running_header": "काशी विद्युत वितरण कंपनी लिमिटेड (KVVCL) · खाता 4417 2039 5518 · बिल माह मई 2026",
        "running_footer": "पृष्ठ {page} / {pages}",
        "arithmetic": [
            {"kind": "line_items", "table": "charges", "quantity": 1, "unit_price": 2, "amount": 3, "decimal": "."},
            {"kind": "column_sum", "table": "charges", "columns": [3], "label_column": 0, "total_label": "चालू माह का कुल बिल"},
            {"kind": "sum", "terms": [["+", inr(current)], ["+", inr(adjust)]], "equals": inr(rounded)},
            {"kind": "sum", "terms": [["+", inr(rounded)], ["-", inr(rebate)]], "equals": inr(rounded - rebate)},
            {"kind": "column_sum", "table": "paid", "columns": [3], "label_column": 1, "total_label": "कुल भुगतान (4 माह)"},
        ],
        "pages": [
            [
                group([P("काशी विद्युत वितरण कंपनी लिमिटेड", "brand"),
                       P("Kashi Vidyut Vitaran Company Ltd.\nविद्युत भवन, सिगरा, वाराणसी — 221010\nटोल-फ्री: 1912 · kvvcl.example", "small right")], "letterhead"),
                H(1, "बिजली बिल — मई 2026"),
                group([P("**उपभोक्ता:** होटल गंगा व्यू प्रा. लि.\n**पता:** बी 2/148, अस्सी घाट, भदैनी, वाराणसी — 221005\n**खाता संख्या (Account No.):** 4417 2039 5518\n"
                         "**श्रेणी (Tariff):** LMV-2, वाणिज्यिक (Commercial)\n**संविदा भार (Contracted Load):** 60 kW", "meta"),
                       P("**बिल संख्या:** KV/VNS/2605/0091827\n**बिल तिथि:** 14.05.2026\n**बिल अवधि:** 12.04.2026 – 12.05.2026 (30 दिन)\n"
                         "**नियत तिथि (Due Date):** 28.05.2026\n**उपकेंद्र / फीडर:** भेलूपुर 33/11 kV / अस्सी-2", "meta")], "split"),
                table("due", [["भुगतान सारांश", "राशि"], ["पिछला बकाया (Arrears)", "₹0.00"], ["चालू माह का कुल बिल", inr(current)],
                              ["पूर्णांकन समायोजन (Rounding)", inr(adjust)], ["नियत तिथि तक देय राशि", inr(rounded)],
                              ["ऑनलाइन भुगतान छूट (1%), 21.05.2026 तक", "−" + inr(rebate)], ["21.05.2026 तक ऑनलाइन भुगतान पर देय", inr(rounded - rebate)]],
                      rendering="borderless", align=["l", "r"], widths=[68, 32], total_rows=[4]),
                box("callout", f"कृपया {inr(rounded)} का भुगतान 28.05.2026 तक करें। नियत तिथि के बाद भुगतान करने पर 1.25% प्रति माह की दर से "
                    "विलंब भुगतान अधिभार (LPS) लगेगा, और 15 दिन बाद बिना अतिरिक्त सूचना के संयोजन काटा जा सकता है।", title="भुगतान सूचना", cls="warn"),
                P("इस माह आपकी खपत पिछले माह से लगभग 7% अधिक रही, जो गर्मी में AC load बढ़ने के कारण सामान्य है। आपका अधिकतम माँग (MDI) "
                  "52.4 kW रहा, जो संविदा भार 60 kW के भीतर है। Power factor 0.947 है; 0.90 से कम होने पर अधिभार लगता है।"),
                box("sidebar", "KVVCL ऐप या UPI से भुगतान करने पर ऊर्जा शुल्क पर 1% छूट मिलती है (अधिकतम ₹1,000)। बिल की PDF प्रति "
                    "WhatsApp पर पाने के लिए 'BILL' लिखकर 1912 पर भेजें।", title="डिजिटल भुगतान"),
                P("Note: This is a computer-generated bill and does not require a signature. For English bill format, log in to the consumer portal.", "small"),
            ],
            [
                H(2, "मीटर रीडिंग विवरण / Meter Reading"),
                table("meter", [["मीटर संख्या", "पैरामीटर", "पिछली रीडिंग 12.04.2026", "वर्तमान रीडिंग 12.05.2026", "MF", "खपत"],
                                ["KVV-3P-0045127", "kWh", grp(kwh[0]), grp(kwh[1]), "1", grp(units)],
                                ["KVV-3P-0045127", "kVAh", grp(kvah[0]), grp(kvah[1]), "1", grp(kvah[1] - kvah[0])],
                                ["KVV-3P-0045127", "MDI (kW)", "—", "52.4", "1", "52.4"]],
                      align=["l", "l", "r", "r", "c", "r"], widths=[20, 14, 20, 20, 8, 18], caption="रीडिंग प्रकार: AMR (स्वचालित)"),
                H(2, "शुल्क विवरण / Tariff Breakdown"),
                table("charges", rows, align=["l", "r", "r", "r"], widths=[52, 14, 12, 22], total_rows=[len(rows) - 1]),
                P("ऊर्जा शुल्क की दरें उत्तर प्रदेश विद्युत नियामक आयोग (UPERC) के टैरिफ आदेश 2025-26 के अनुसार हैं। विद्युत शुल्क स्थायी शुल्क, "
                  "ऊर्जा शुल्क और FPPAS के योग पर लगाया गया है; मीटर किराए पर विद्युत शुल्क नहीं लगता।", "small"),
                chart("usage", "bar", spec, "पिछले 12 माह की खपत (यूनिट)", raster=True, width="88%", size=(600, 230)),
                chart_table("usage-data", "माह", spec, grp),
            ],
            [
                H(2, "पिछले भुगतान / Payment History"),
                table("paid", history, rendering="borderless", align=["l", "l", "l", "r"], widths=[18, 32, 22, 28], total_rows=[5]),
                H(2, "महत्वपूर्ण सूचनाएँ"),
                L(["बिल संबंधी शिकायत 1912 पर या kvvcl.example/shikayat पर दर्ज करें; 7 कार्य दिवस में निस्तारण किया जाएगा।",
                   "विद्युत सुरक्\u200dषा: मीटर बोर्ड और सर्विस केबल के पास पानी या ज्वलनशील सामग्री न रखें।",
                   "Solar rooftop (net metering) के लिए आवेदन ऑनलाइन किया जा सकता है; 10 kW तक के संयंत्र पर सब्सिडी उपलब्ध है।",
                   "संविदा भार बढ़ाने के लिए अधिकतम माँग लगातार 3 माह तक संविदा भार से अधिक होने पर नोटिस भेजा जाएगा।"]),
                box("footnote", "¹ 1 यूनिट = 1 किलोवाट-घंटा (kWh)। राशियाँ भारतीय अंक-पद्धति (लाख) में दर्शाई गई हैं, जैसे ₹1,23,456.00।"),
                P("— — — — — — — — — — कृपया यहाँ से काटें — — — — — — — — — —", "center"),
                H(3, "भुगतान पर्ची / Payment Slip"),
                table("slip", [["खाता संख्या", "बिल संख्या", "नियत तिथि", "देय राशि", "जमा राशि"],
                               ["4417 2039 5518", "KV/VNS/2605/0091827", "28.05.2026", inr(rounded), ""]],
                      align=["l", "l", "c", "r", "r"], widths=[20, 28, 16, 18, 18]),
                P("उपभोक्ता: होटल गंगा व्यू प्रा. लि. · भुगतान केंद्र: विद्युत भवन सिगरा, जनसेवा केंद्र, या किसी भी अधिकृत बैंक शाखा में।\n"
                  "चेक 'Kashi Vidyut Vitaran Co. Ltd.' के नाम देय हो; पीछे खाता संख्या अवश्य लिखें।", "small"),
                P("कैशियर के हस्ताक्षर: ____________    रसीद संख्या: ____________    दिनांक: ____________", "small"),
            ],
        ],
    }


def utility_ru() -> dict[str, Any]:
    """Russian housing and utilities single payment document (pylopdf, raster chart)."""
    rub = lambda c: money(c, "ru")  # noqa: E731
    val = lambda c: number(abs(c) / 100, "ru") if c >= 0 else "−" + number(-c / 100, "ru")  # noqa: E731
    services = [("Содержание жилого помещения", "м²", "54.6", 1, "32.15", 0), ("Текущий ремонт общего имущества", "м²", "54.6", 1, "6.84", 0),
                ("Обращение с ТКО", "чел.", "3", 0, "148.92", 0), ("Холодное водоснабжение", "м³", "9.412", 3, "51.77", -dmul("2.405", "51.77")),
                ("ГВС (теплоноситель)", "м³", "4.215", 3, "51.77", 0), ("ГВС (тепловая энергия)", "Гкал", "0.274", 3, "2418.63", 0),
                ("Водоотведение", "м³", "13.627", 3, "38.40", 0), ("Отопление", "Гкал", "1.092", 3, "2418.63", 0),
                ("Электроэнергия, день (Т1)", "кВт·ч", "186", 0, "5.94", 0), ("Электроэнергия, ночь (Т2)", "кВт·ч", "74", 0, "3.12", 0),
                ("ХВС на содержание общего имущества", "м³", "0.218", 3, "51.77", 0), ("Электроэнергия на СОИ", "кВт·ч", "6.42", 2, "5.94", 0),
                ("Запирающее устройство (домофон)", "кв.", "1", 0, "65.00", 0), ("Взнос на капитальный ремонт", "м²", "54.6", 1, "13.46", 0)]
    rows = [["Вид услуги", "Ед.", "Объём", "Тариф, ₽", "Начислено, ₽", "Перерасчёт, ₽", "Итого, ₽"]]
    charged = recalc = 0
    for name, unit, qty, places, rate, delta in services:
        value = dmul(qty, rate)
        charged += value
        recalc += delta
        rows.append([name, unit, number(float(qty), "ru", places), number(float(rate), "ru", 2), val(value), val(delta) if delta else "", val(value + delta)])
    total = charged + recalc
    rows.append(["Итого за апрель 2026", "", "", "", val(charged), val(recalc), val(total)])
    debt, paid = 640218, 640218
    spec = {"title": "Начислено за 12 месяцев, тыс. ₽", "categories": ["05.25", "06", "07", "08", "09", "10", "11", "12", "01.26", "02", "03", "04"],
            "series": [("Начислено", [4.82, 3.91, 3.88, 3.95, 4.12, 6.03, 7.21, 7.94, 8.06, 7.58, 6.40, round(total / 100000, 2)])], "max": 10, "ticks": 5,
            "min": 0, "tick_format": lambda v: number(v, "ru", 0), "colors": ["#6b3fa0"]}
    meters = [["Прибор учёта", "Заводской №", "Предыдущие (25.03)", "Текущие (25.04)", "Расход"],
              ["ХВС, кухня", "40217739", "412,118", "417,624", "5,506"], ["ХВС, ванная", "40217740", "298,771", "302,677", "3,906"],
              ["ГВС, кухня", "50388112", "201,334", "203,951", "2,617"], ["ГВС, ванная", "50388113", "176,402", "178,000", "1,598"],
              ["Электроэнергия Т1", "011174128", "18 742", "18 928", "186"], ["Электроэнергия Т2", "011174128", "7 315", "7 389", "74"]]
    return {
        "template": "utility_bill", "page_size": "A4", "languages": ["ru-RU"],
        "metadata": {"title": "Единый платёжный документ за апрель 2026 г. — л/с 6620417735", "author": "ООО «ЖилКомфорт-Сервис»",
                     "subject": "Квитанция ЖКХ: содержание жилья и коммунальные услуги, г. Екатеринбург, ул. Малышева, 118–47",
                     "keywords": ["ЕПД", "квитанция ЖКХ", "коммунальные услуги", "показания счётчиков"], "lang": "ru-RU", "created": "2026-05-02T03:00:00Z"},
        "theme": {"accent": "#6b3fa0", "py_size": 8.6},
        "running_header": "ООО «ЖилКомфорт-Сервис» · ЕПД за апрель 2026 г. · лицевой счёт 6620417735",
        "running_footer": "Страница {page} из {pages}",
        "arithmetic": [
            {"kind": "line_items", "table": "uslugi", "quantity": 2, "unit_price": 3, "amount": 4, "decimal": ","},
            {"kind": "column_sum", "table": "uslugi", "columns": [4, 5, 6], "label_column": 0, "total_label": "Итого за апрель 2026"},
            {"kind": "sum", "terms": [["+", rub(debt)], ["-", rub(paid)], ["+", rub(total)]], "equals": rub(debt - paid + total)},
            {"kind": "sum", "terms": [["+", "5,506"], ["+", "3,906"]], "equals": "9,412"},
            {"kind": "sum", "terms": [["+", "2,617"], ["+", "1,598"]], "equals": "4,215"},
        ],
        "pages": [
            [
                group([P("ЖилКомфорт-Сервис", "brand"),
                       P("ООО «ЖилКомфорт-Сервис», ИНН 6671048826\n620062, г. Екатеринбург, ул. Чебышёва, д. 4, оф. 12\nДиспетчерская: +7 343 555-04-17 (круглосуточно)", "small right")], "letterhead"),
                H(1, "Единый платёжный документ за апрель 2026 г."),
                group([P("**Плательщик:** Морозова Анна Викторовна\n**Адрес:** г. Екатеринбург, ул. Малышева, д. 118, кв. 47\n"
                         "**Общая площадь:** 54,6 м² · **Зарегистрировано:** 3 чел.", "meta"),
                       P("**Лицевой счёт:** 6620417735\n**Расчётный период:** 01.04.2026 – 30.04.2026\n**Оплатить до:** 10.05.2026\n"
                         "**ЕЛС ГИС ЖКХ:** 66ЕА119047", "meta")], "split"),
                table("svod", [["Сводка по лицевому счёту", "Сумма"], ["Задолженность на 01.04.2026", rub(debt)], ["Оплачено в апреле (06.04.2026)", "−" + rub(paid)],
                               ["Начислено за апрель", rub(charged)], ["Перерасчёт", ("−" + rub(-recalc)) if recalc < 0 else rub(recalc)],
                               ["Итого к оплате", rub(debt - paid + total)]], rendering="borderless", align=["l", "r"], widths=[70, 30], total_rows=[5]),
                box("callout", "Показания индивидуальных приборов учёта передаются с 20 по 25 число каждого месяца через личный кабинет, "
                    "по телефону диспетчерской или через терминалы в подъезде. При непередаче показаний начисление производится по среднему.",
                    title="Обратите внимание", cls="note"),
                H(2, "Показания индивидуальных приборов учёта"),
                table("schetchiki", meters, align=["l", "c", "r", "r", "r"], widths=[30, 18, 18, 18, 16]),
                P("Поверка счётчиков ГВС истекает 14.09.2026. Пожалуйста, закажите поверку или замену заранее: без действующей поверки "
                  "начисление через три месяца будет производиться по нормативу с повышающим коэффициентом 1,5."),
            ],
            [
                H(2, "Расчёт размера платы за содержание жилого помещения и коммунальные услуги"),
                table("uslugi", rows, align=["l", "c", "r", "r", "r", "r", "r"], widths=[33, 8, 10, 11, 13, 12, 13], total_rows=[len(rows) - 1]),
                box("footnote", "¹ Тарифы на тепловую энергию, водоснабжение и водоотведение установлены постановлениями РЭК Свердловской "
                    "области № 214-ПК и № 216-ПК от 18.12.2025, действуют с 01.01.2026."),
                box("footnote", "² Перерасчёт по ХВС за март 2026 г.: начисление по среднему заменено фактическими показаниями (−2,405 м³ × 51,77 ₽)."),
                box("footnote", "³ Взнос на капитальный ремонт перечисляется на специальный счёт дома в ПАО «Уралтрансбанк»."),
                H(3, "Справочная информация"),
                table("normy", [["Показатель", "Значение"], ["Норматив потребления ХВС, м³ на чел. в месяц", "4,35"], ["Норматив потребления ГВС, м³ на чел. в месяц", "3,40"],
                                ["Объём ХВС на СОИ по дому, м³", "18,71"], ["Площадь помещений МКД, м²", "4 682,30"], ["Норматив отопления, Гкал на м² в месяц", "0,0200"]],
                      rendering="borderless", align=["l", "r"], widths=[75, 25]),
                P("Плата за отопление начисляется по показаниям общедомового прибора учёта пропорционально площади квартиры. "
                  "Корректировка за 2025 год будет выполнена в мае 2026 г."),
            ],
            [
                chart("dinamika", "line", spec, "Динамика начислений по лицевому счёту", raster=True, width="86%", size=(600, 220)),
                chart_table("dinamika-data", "Месяц", spec, lambda v: number(v, "ru", 2)),
                box("callout", "При оплате после 10-го числа начисляются пени в размере 1/300 ключевой ставки ЦБ РФ за каждый день просрочки, "
                    "начиная с 31-го дня. Оплата через Госуслуги, банковское приложение или кассу без комиссии.", title="Сроки оплаты", cls="warn"),
                H(2, "Платёжный документ (извещение)"),
                table("izveshchenie", [["Получатель", "ООО «ЖилКомфорт-Сервис»"], ["ИНН / КПП", "6671048826 / 667101001"], ["Расчётный счёт", "40702810416540017735"],
                                       ["Банк", "Уральский банк ПАО Сбербанк, г. Екатеринбург"], ["БИК / корр. счёт", "046577674 / 30101810500000000674"],
                                       ["Лицевой счёт", "6620417735"], ["Период", "апрель 2026"], ["Сумма к оплате", rub(debt - paid + total)]],
                      header_rows=0, align=["l", "l"], widths=[32, 68]),
                P("Плательщик: Морозова А. В.          Подпись: ______________          Дата: ______________"),
                P("Аварийно-диспетчерская служба: +7 343 555-04-17. Приём граждан: вторник 10:00–13:00, четверг 15:00–19:00, ул. Чебышёва, 4.", "small"),
            ],
        ],
    }



# ====================================================================== purchase orders and packing slips


def shipments(key: str, ordered: list[int], short: int) -> list[int]:
    """Deterministic shipped quantities: ``short`` lines are partially shipped, the rest in full."""
    r = rng(key)
    partial = set(r.sample(range(len(ordered)), short))
    return [max(1, q * r.choice([2, 3, 5]) // 10 * (1 if q >= 10 else 0)) if i in partial and q > 1 else q for i, q in enumerate(ordered)]


def po_en() -> dict[str, Any]:
    """US purchase order to a Japanese supplier plus the supplier's bilingual packing list (chromium)."""
    usd = lambda c: money(c, "en-US")  # noqa: E731
    r = rng("w2-po-en-21")
    catalog = [
        ("OS-LGR15-{n}", "Linear guide rail LGR-15, {n} mm", ["300", "400", "600", "800"], "EA", (4120, 9860), (8, 40)),
        ("OS-LGB15-SN", "Guide block LGB-15, standard preload", [""], "EA", (2875, 2875), (40, 160)),
        ("OS-BS1605-{n}", "Ball screw Ø16 lead 5, C7, {n} mm", ["350", "500"], "EA", (11850, 15630), (6, 24)),
        ("OS-BK12", "Fixed-side support unit BK12", [""], "EA", (3460, 3460), (12, 48)),
        ("OS-BF12", "Floating-side support unit BF12", [""], "EA", (1985, 1985), (12, 48)),
        ("OS-CPL-{n}", "Jaw coupling, aluminum, bore {n}", ["8×10", "10×12", "12×14"], "EA", (1240, 1580), (20, 60)),
        ("OS-BRG-{n}", "Deep-groove ball bearing {n}-2RS", ["6000", "6001", "6201", "6202"], "EA", (184, 412), (100, 400)),
        ("OS-TB-{n}", "Timing belt HTD-5M, width 15, {n} mm", ["450", "600"], "EA", (965, 1210), (20, 80)),
        ("OS-PUL-5M-{n}", "Timing pulley HTD-5M, {n} teeth", ["20", "30"], "EA", (1530, 2190), (20, 60)),
        ("OS-SHC-M{n}", "Socket head cap screw M{n}, A2 stainless (box of 100)", ["3×8", "4×12", "5×16", "6×20"], "BX", (690, 1860), (5, 30)),
        ("OS-LC-{n}", "Linear bushing LM{n}UU", ["8", "12"], "EA", (395, 610), (40, 120)),
        ("OS-SFT-{n}", "Induction-hardened shaft Ø{n}, h6, 500 mm", ["8", "12"], "EA", (2210, 3040), (10, 40)),
        ("OS-SK-{n}", "Shaft support SK{n}, aluminum", ["8", "12"], "EA", (520, 740), (20, 80)),
        ("OS-CC-{n}", "Cable carrier 15×20, {n} links", ["40", "60"], "EA", (1890, 2650), (6, 24)),
        ("OS-PRX-{n}", "Inductive proximity sensor M12, PNP {n}, 2 m cable", ["NO", "NC"], "EA", (2340, 2340), (12, 40)),
        ("OS-SHF-{n}", "Shaft end collar, bore {n}", ["8", "12"], "EA", (210, 285), (40, 120)),
        ("OS-HS-{n}", "Hard stop, urethane bumper Ø{n}", ["10", "16"], "EA", (360, 470), (16, 48)),
        ("OS-BRK-{n}", "Motor mount bracket NEMA {n}, black anodized", ["23", "34"], "EA", (2780, 3640), (6, 24)),
        ("OS-LUB-70", "Lithium grease cartridge for guide blocks, 70 g", [""], "EA", (1150, 1150), (10, 30)),
        ("OS-WSH-M{n}", "Spring washer M{n}, A2 stainless (box of 200)", ["4", "5", "6"], "BX", (420, 560), (4, 16)),
    ]
    lines = []
    for code, text, variants, uom, (low, high), (qlow, qhigh) in catalog:
        for index, variant in enumerate(variants):
            price = low + (high - low) * index // max(len(variants) - 1, 1)
            qty = r.randint(qlow // 2, qhigh // 2) * 2
            lines.append((code.format(n=variant.replace("×", "x")), text.format(n=variant), qty, uom, price))
    lines.append(("OS-ENG-FAI", "First article inspection report, per drawing RR-ASM-2201 rev. D", 1, "LOT", 48000))
    lines.append(("OS-PKG-VCI", "VCI anti-rust packaging and export crating", 1, "LOT", 31500))
    rows, subtotal = [], 0
    need = [date(2026, 6, 15), date(2026, 6, 29), date(2026, 7, 13)]
    for number_, (code, text, qty, uom, price) in enumerate(lines, start=1):
        value = mul(qty, price)
        subtotal += value
        rows.append([f"{number_ * 10:03d}", code, text, f"{qty:,}", uom, usd(price), usd(value), day(need[number_ % 3], "us")])
    freight = 184000
    total = subtotal + freight
    by_date: dict[date, list[int]] = {}
    for number_, (_c, _t, qty, _u, price) in enumerate(lines, start=1):
        slot = by_date.setdefault(need[number_ % 3], [0, 0])
        slot[0] += 1
        slot[1] += mul(qty, price)
    schedule = table("sched", [["Need-by date", "Lines", "Value"], *[[day(k, "us"), str(v[0]), usd(v[1])] for k, v in sorted(by_date.items())],
                               ["Total", str(len(lines)), usd(subtotal)]], rendering="borderless", align=["l", "r", "r"], widths=[40, 25, 35],
                     total_rows=[len(by_date) + 1], caption="Delivery schedule by need-by date")
    n = len(rows)
    header = [["Line", "Part number", "Description", "Qty", "UoM", "Unit price", "Amount", "Need by"]]
    segs = continued("po", header, rows, [14, 24, n - 38], caption="Order lines", continued_caption="Order lines (continued)",
                     align=["c", "l", "l", "r", "c", "r", "r", "c"], widths=[6, 15, 33, 7, 6, 11, 12, 10],
                     total=[["", "", "Subtotal", "", "", "", usd(subtotal), ""], ["", "", "Freight and insurance, CIP Oakland", "", "", "", usd(freight), ""],
                            ["", "", "Total order value (USD)", "", "", "", usd(total), ""]])
    ordered = [q for _c, _t, q, _u, _p in lines]
    shipped = shipments("w2-po-en-21-ship", ordered, 5)
    pack_rows = []
    for number_, ((code, text, qty, _uom, _p), sent) in enumerate(zip(lines, shipped, strict=True), start=1):
        pack_rows.append([f"{number_ * 10:03d}", code, text, f"{qty:,}", f"{sent:,}", f"{qty - sent:,}", f"C-{(number_ - 1) // 4 + 1:02d}"])
    pack_total = [["", "", "Total units", f"{sum(ordered):,}", f"{sum(shipped):,}", f"{sum(ordered) - sum(shipped):,}", ""]]
    pack = continued("pack", [["PO line", "Part number", "Description 品名", "Ordered 注文数", "Shipped 出荷数", "Backordered 残数", "Carton"]], pack_rows, [26, n - 26],
                     caption="Packing list 梱包明細書 — shipment 1 of 2", continued_caption="Packing list 梱包明細書 (continued)",
                     align=["c", "l", "l", "r", "r", "r", "c"], widths=[7, 16, 35, 11, 11, 12, 8], total=pack_total, rendering="borderless")
    back = [(row[0], row[1], row[3], row[4], row[5]) for row in pack_rows if row[5] != "0"]
    cartons = (n - 1) // 4 + 1
    mail = {"folders": ["Inbox", "Purchasing", "Suppliers", "Sent", "Archive"], "subject": "RE: PO 4500018273 — order acknowledgment / 注文請書",
            "from": "Kenta Mori 森 健太 <k.mori@otsuka-seiki.example>", "to": "To: Sofia Lindqvist <s.lindqvist@redwater-robotics.example>",
            "date": "Thu 4/23/2026 6:12 PM",
            "body": ["Dear Ms. Lindqvist,",
                     (f"Thank you for purchase order 4500018273. We confirm all {n} lines at the quoted prices. Most items "
                      "will ship on 5/29 from our Higashiosaka plant; ball screws and some bearings will follow about three weeks later "
                      "because of a heat-treatment backlog."),
                     ("The signed order acknowledgment (注文請書) is attached. Please let me know if a "
                      "partial shipment is not acceptable."),
                     "Best regards, Kenta Mori, Export Sales, Otsuka Seiki Co., Ltd."],
            "attachment": "注文請書_4500018273.pdf (212 KB)", "height": 420}
    checks = [{"kind": "line_items", "table": "po", "quantity": 3, "unit_price": 5, "amount": 6, "decimal": "."},
              {"kind": "column_sum", "table": "po", "columns": [6], "label_column": 2, "total_label": "Subtotal"},
              {"kind": "sum", "terms": [["+", usd(subtotal)], ["+", usd(freight)]], "equals": usd(total)},
              {"kind": "column_sum", "table": "sched", "columns": [1, 2], "label_column": 0, "total_label": "Total"},
              {"kind": "column_sum", "table": "pack", "columns": [3, 4, 5], "label_column": 2, "total_label": "Total units"}]
    checks += [{"kind": "sum", "terms": [["+", o], ["-", s_]], "equals": b} for _l, _c, o, s_, b in back]
    return {
        "template": "purchase_order", "page_size": "Letter", "languages": ["en-US", "ja"],
        "metadata": {"title": "Purchase order 4500018273 — Otsuka Seiki Co., Ltd.", "author": "Redwater Robotics, Inc. — Purchasing",
                     "subject": "Motion components for the RR-2200 gantry, with supplier packing list for shipment 1 of 2",
                     "keywords": ["purchase order", "packing list", "backorder", "Incoterms"], "lang": "en-US", "created": "2026-04-21T17:20:00Z"},
        "theme": {"accent": "#7a2e1f", "font_size": "8.8pt", "margins": "14mm 13mm 16mm 13mm"},
        "running_header": "Redwater Robotics, Inc. · PO 4500018273 · Otsuka Seiki Co., Ltd.",
        "running_footer": "PO 4500018273 · Page {page} of {pages}",
        "arithmetic": checks,
        "pages": [
            [
                group([P("Redwater Robotics, Inc.", "brand"), P("4120 Commerce Parkway, Fremont, CA 94538, USA\npurchasing@redwater-robotics.example · +1 510-555-0161", "small right")], "letterhead"),
                H(1, "Purchase order 4500018273"),
                group([P("**Supplier:**\nOtsuka Seiki Co., Ltd.\n株式会社大塚精機\n〒577-0013 大阪府東大阪市長堂3丁目8-21\nSupplier no. 200417 · Contact: 森 健太 (Kenta Mori)", "meta"),
                       P("**Ship to:**\nRedwater Robotics, Inc. — Receiving Dock 3\n4120 Commerce Parkway, Fremont, CA 94538\n**Bill to:** Accounts Payable, same address", "meta"),
                       P("**PO date:** 04/21/2026\n**Buyer:** Sofia Lindqvist\n**Payment terms:** Net 45 from receipt\n**Incoterms® 2020:** CIP Oakland\n**Currency:** USD", "meta")], "split"),
                P("Please confirm this order within five business days and quote the PO number and line numbers on all shipping "
                  "documents, invoices and correspondence. Partial shipments are accepted for lines marked as backordered on the "
                  "acknowledgment."),
                segs[0],
            ],
            [segs[1]],
            [
                segs[2],
                box("callout", "Prices are firm for the duration of this order and include export packing. The supplier’s quotation "
                    "Q-26-0331 dated 03/31/2026 is incorporated by reference; in case of conflict this purchase order prevails.",
                    title="Pricing", cls="note"),
                schedule,
                P("Special instructions: ball screws (lines 060–070) must be shipped with end caps and wrapped individually in VCI film. "
                  "Bearings may be packed in the supplier’s standard boxes of 10. Do not mix lines with different need-by dates in one carton."),
                P("Approved by: Daniel Achebe, Director of Supply Chain — 04/21/2026 (electronic approval, SAP release strategy R2)", "small"),
            ],
            [
                H(2, "Terms and conditions"),
                L([item("Delivery", ["Deliver to the ship-to address Monday–Friday, 7:00 a.m. – 3:00 p.m. Pacific time.",
                                     "Each carton must carry a label with PO number, line number, part number and quantity.",
                                     "Notify the buyer at least two weeks in advance of any delay."]),
                   item("Quality", ["Parts must conform to drawing RR-ASM-2201 rev. D and the referenced material specifications.",
                                    "A first article inspection report (AS9102 format) is required before the first shipment.",
                                    item("Nonconforming parts", ["are returned at the supplier’s expense", "must be replaced within 10 business days"], ordered=False)]),
                   item("Invoicing", ["Submit invoices by email to ap@redwater-robotics.example, one invoice per shipment.",
                                      "Invoices without a valid PO and line number will be returned unpaid."]),
                   "Governing law: State of California. The United Nations Convention on Contracts for the International Sale of Goods does not apply."],
                  ordered=True),
                screenshot("ack", "email", mail, "Supplier order acknowledgment received 04/23/2026 (screenshot)", width="88%"),
                box("footnote", "¹ Incoterms® is a trademark of the International Chamber of Commerce."),
            ],
            [
                group([P("**Otsuka Seiki Co., Ltd.** 株式会社大塚精機\n〒577-0013 大阪府東大阪市長堂3丁目8-21 · TEL 06-6555-0128", "meta"),
                       P(f"**Invoice / 送り状:** OS-EX-260529-03\n**Ship date / 出荷日:** 2026-05-29\n**Cartons / 梱包数:** {cartons} · **Pallets:** 2\n**Vessel:** ONE Harmony 0618E, Kobe → Oakland", "meta")], "split"),
                pack[0],
            ],
            [
                pack[1],
                photo("port", ["container-port"], ["logistics"], {"container-port": "Containers staged for export at the port of Kobe"},
                      "Export terminal", "right", width="36%"),
                P(f"Shipment 1 contains {sum(shipped):,} of {sum(ordered):,} units in {cartons} cartons on two pallets "
                  f"(gross weight 612 kg). The {len(back)} backordered lines will ship as shipment 2 on or about 06/19/2026 under the same PO."),
                P("Receiving: count cartons against this list, note any visible damage on the carrier’s delivery receipt, and "
                  "report shortages to the buyer within 48 hours."),
                P("Received by: ____________________    Date: ____________    Receiving report no.: RR-REC-______", "small"),
            ],
        ],
    }



def po_zhtw() -> dict[str, Any]:
    """Traditional Chinese purchase order with a shipping note (LibreOffice, tagged); NT$ amounts are whole dollars."""
    twd = lambda v: money(v, "zhTW")  # noqa: E731
    grp = lambda v: number(v, "zhTW")  # noqa: E731
    catalog = [
        ("RC0402-10K", "晶片電阻 0402 10KΩ ±1%", "5000", "0.12"), ("RC0402-4K7", "晶片電阻 0402 4.7KΩ ±1%", "5000", "0.12"),
        ("RC0603-100R", "晶片電阻 0603 100Ω ±1%", "4000", "0.15"), ("CC0402-104", "積層陶瓷電容 0402 0.1µF 16V X7R", "10000", "0.18"),
        ("CC0603-106", "積層陶瓷電容 0603 10µF 10V X5R", "4000", "0.95"), ("CC1206-226", "積層陶瓷電容 1206 22µF 25V X5R", "2000", "3.40"),
        ("EC-470-35", "鋁質電解電容 470µF 35V（Φ10×16）", "1000", "4.20"), ("L-4R7-3015", "功率電感 4.7µH 3015", "2000", "5.60"),
        ("D-SS34", "蕭特基二極體 SS34 SMA", "3000", "0.85"), ("D-TVS-SMBJ24", "TVS 二極體 SMBJ24A", "1500", "2.10"),
        ("Q-AO3400", "MOSFET N 通道 30V 5.7A SOT-23", "3000", "1.65"), ("U-LDO-3V3", "LDO 穩壓 IC 3.3V 500mA SOT-223", "2000", "6.80"),
        ("U-BUCK-24", "降壓轉換 IC 24V→5V 3A", "1200", "18.50"), ("U-MCU-F103", "微控制器 32 位元 LQFP-48", "800", "62.00"),
        ("U-RS485", "RS-485 收發器 SOIC-8", "1200", "9.80"), ("X-8M", "石英晶體 8MHz 3225", "1500", "3.90"),
        ("CN-USBC-16", "USB Type-C 母座 16P 沉板", "1500", "7.20"), ("CN-TB-508-3", "歐式端子台 5.08mm 3P", "2000", "4.60"),
        ("CN-HDR-2x5", "排針 2×5P 2.54mm 直立", "2000", "1.80"), ("CN-JST-4P", "線對板連接器 1.25mm 4P", "3000", "1.10"),
        ("LED-0603-G", "LED 0603 綠色", "5000", "0.35"), ("LED-0603-R", "LED 0603 紅色", "5000", "0.35"),
        ("SW-TACT-6x6", "輕觸開關 6×6×5mm", "2000", "0.90"), ("F-PTC-050", "自恢復保險絲 0.5A 1206", "2000", "1.60"),
        ("HS-AL-20", "鋁擠型散熱片 20×20×10mm", "1000", "8.50"), ("PCB-MB-V3", "主機板 PCB 4 層 FR-4 1.6t（V3.2）", "800", "48.00"),
        ("PCB-IO-V2", "I/O 擴充板 PCB 2 層 FR-4（V2.0）", "800", "21.00"), ("ENC-ABS-01", "ABS 外殼 上蓋（黑色，UL94-V0）", "800", "36.00"),
        ("ENC-ABS-02", "ABS 外殼 下蓋（黑色，UL94-V0）", "800", "33.00"), ("SCR-M3x6", "自攻螺絲 M3×6 鍍鎳", "4000", "0.45"),
        ("LBL-RATING", "銘牌標籤 PET 銀底（含序號）", "800", "2.30"), ("GSK-SIL-01", "矽膠防水墊圈", "800", "5.50"),
        ("CBL-PWR-1M", "電源線 2P 1m 附端子", "800", "14.00"), ("BAG-ESD-15", "防靜電袋 15×20cm", "1000", "1.20"),
        ("BOX-INNER", "內盒 彩印 單入", "800", "11.00"), ("BOX-OUTER", "外箱 五層瓦楞 20 入", "40", "38.00"),
    ]
    rows, subtotal = [], 0
    for number_, (code, text, qty, price) in enumerate(catalog, start=1):
        value = int((Decimal(qty) * Decimal(price)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        subtotal += value
        rows.append([str(number_), code, text, grp(int(qty)), "PCS" if not code.startswith(("BOX", "BAG")) else "個", price, grp(value),
                     "2026/06/10" if number_ % 3 else "2026/06/24"])
    tax = part(subtotal, 5, 100)
    total = subtotal + tax
    n = len(rows)
    header = [["項次", "料號", "品名規格", "數量", "單位", "單價", "金額", "交期"]]
    segs = continued("cg", header, rows, [16, 14, n - 30], caption="採購明細（金額單位：新臺幣元）", continued_caption="採購明細（續）",
                     align=["c", "l", "l", "r", "c", "r", "r", "c"], widths=[5, 15, 33, 9, 6, 8, 12, 12],
                     total=[["", "", "未稅合計", "", "", "", grp(subtotal), ""], ["", "", "營業稅 5%", "", "", "", grp(tax), ""],
                            ["", "", "含稅總計", "", "", "", grp(total), ""]])
    ordered = [int(q) for _c, _t, q, _p in catalog]
    shipped = [q if i % 7 != 3 else q * 3 // 5 for i, q in enumerate(ordered)][:24]
    ship_rows = [[str(k + 1), catalog[k][0], catalog[k][1], grp(ordered[k]), grp(shipped[k]), grp(ordered[k] - shipped[k]),
                  "6/24 補交" if ordered[k] - shipped[k] else ""] for k in range(len(shipped))]
    ship_rows.append(["", "", "合計", grp(sum(ordered[:24])), grp(sum(shipped)), grp(sum(ordered[:24]) - sum(shipped)), ""])
    by_date: dict[str, list[int]] = {}
    for row in rows:
        slot = by_date.setdefault(row[7], [0, 0])
        slot[0] += 1
        slot[1] += int(row[6].replace(",", ""))
    schedule = table("jq", [["交期", "項數", "未稅金額"], *[[k, str(v[0]), grp(v[1])] for k, v in sorted(by_date.items())], ["合計", str(n), grp(subtotal)]],
                     align=["c", "r", "r"], widths=[40, 20, 40], total_rows=[len(by_date) + 1], caption="交期分配")
    checks = [{"kind": "column_sum", "table": "jq", "columns": [1, 2], "label_column": 0, "total_label": "合計"},
              {"kind": "line_items", "table": "cg", "quantity": 3, "unit_price": 5, "amount": 6, "decimal": "."},
              {"kind": "column_sum", "table": "cg", "columns": [6], "label_column": 2, "total_label": "未稅合計"},
              {"kind": "sum", "terms": [["+", grp(subtotal)], ["+", grp(tax)]], "equals": grp(total)},
              {"kind": "column_sum", "table": "ship", "columns": [3, 4, 5], "label_column": 2, "total_label": "合計"}]
    return {
        "template": "purchase_order", "page_size": "A4", "languages": ["zh-TW"], "tagged": True,
        "metadata": {"title": "採購單 PO-HS-2605-0172（永盛精密工業）", "author": "宏碩電子股份有限公司 採購課",
                     "subject": "工業閘道器 GW-300 量產料件採購及首批出貨單", "keywords": ["採購單", "出貨單", "營業稅", "欠交"],
                     "lang": "zh-TW", "created": "2026-05-06T01:40:00Z"},
        "theme": {"accent": "#1d4e89", "lo_size": "9pt", "lo_font": "Noto Sans CJK TC", "content_cm": 17.4},
        "running_header": "宏碩電子股份有限公司　採購單 PO-HS-2605-0172",
        "running_footer": "第 {page} 頁／共 {pages} 頁",
        "arithmetic": checks,
        "pages": [
            [
                P("宏碩電子股份有限公司", "brand"),
                P("新竹科學園區力行六路 18 號　電話：(03) 555-7720　統一編號：28817402", "small"),
                H(1, "採購單"),
                P("**單號：** PO-HS-2605-0172　**日期：** 2026/05/06　**採購人員：** 林怡君（分機 2314）\n"
                  "**供應商：** 永盛精密工業有限公司（廠商代號 V-0388）\n**地址：** 臺中市大里區仁化路 512 巷 9 號　**聯絡人：** 黃志明 經理\n"
                  "**付款條件：** 月結 60 天（T/T）　**交貨地點：** 本公司新竹廠 B1 收料區　**幣別：** 新臺幣（NT$）", "meta"),
                P("請於收到本採購單後三個工作天內回簽確認交期；如無法如期交貨，請事先以書面（電子郵件亦可）通知本公司採購課。"),
                segs[0],
            ],
            [
                segs[1],
                H(3, "核可替代料"),
                table("alt", [["原料號", "核可替代料號", "製造商", "備註"], ["U-LDO-3V3", "U-LDO-3V3-B", "立錡／RT", "腳位相容，需另附規格書"],
                              ["U-RS485", "U-RS485-T", "德州儀器／TI", "限用工業級（−40～85 °C）"], ["X-8M", "X-8M-K", "希華晶體", "負載電容 12 pF"],
                              ["CN-USBC-16", "CN-USBC-16A", "正崴", "沉板深度 0.8 mm"]], align=["l", "l", "l", "l"], widths=[22, 24, 22, 32]),
                P("使用替代料前，供應商須提出變更申請（ECN），經本公司研發及品保單位書面核准後始得出貨；未經核准擅自替換者，整批退貨。"),
            ],
            [
                segs[2],
                P(f"含稅總計：**{twd(total)}**（新臺幣 {grp(total)} 元整）"),
                box("callout", "單價以千顆計價之料件，已換算為每單位單價；金額四捨五入至元。發票請開立三聯式統一發票，並註明本採購單號。",
                    title="計價說明", cls="note"),
                schedule,
                table("pay", [["項目", "內容"], ["發票抬頭", "宏碩電子股份有限公司（統編 28817402）"], ["付款方式", "月結 60 天，電匯至供應商指定帳戶"],
                              ["請款期限", "每月 25 日前寄達，逾期順延至次月"], ["聯絡窗口", "會計課 王淑芬（分機 2208）"]],
                      align=["l", "l"], widths=[25, 75], caption="付款及請款資訊"),
            ],
            [
                H(2, "交貨及驗收條款"),
                L([item("交貨：", ["分批交貨須事先取得本公司同意；每批應附出貨單一式兩聯。",
                                   "外箱需標示：採購單號、料號、數量、生產批號（Lot No.）。"]),
                   item("品質：", ["所有料件應符合 RoHS 2.0 及 REACH 規範，並隨貨附上合格證明。",
                                   "IC 類料件之生產日期不得早於交貨日前 24 個月。",
                                   "抽樣檢驗依 MIL-STD-105E 一般檢驗水準 II，AQL 0.65。"]),
                   item("不良品處理：", ["經檢驗不合格之批次，供應商應於 7 日內換貨，所生運費由供應商負擔。"]),
                   "其他未盡事宜，依本公司「採購一般條款」（2025 年版）辦理。"], ordered=True),
                photo("line", ["factory-machinery", "hand-tools"], ["industry"], {"factory-machinery": "本公司新竹廠 SMT 產線（示意）"},
                      "生產線示意", "none", width="62%", width_cm=10.5),
                table("qa", [["檢驗項目", "標準", "抽樣"], ["外觀", "無刮傷、無變形、標示清楚", "AQL 0.65"], ["尺寸", "依圖面公差 ±0.1 mm", "每批 5 pcs"],
                             ["電性", "依規格書", "每批 32 pcs"], ["包裝", "防潮、防靜電，濕度卡 < 10%", "全數"]],
                      align=["l", "l", "c"], widths=[18, 56, 26], caption="進料檢驗標準（摘要）"),
                P("核准：採購課長　陳柏翰　　　審核：物管　張雅婷　　　承辦：林怡君", "small"),
            ],
            [
                H(2, "出貨單（第一批）"),
                P("**出貨廠商：** 永盛精密工業有限公司　**出貨單號：** YS-SO-260610-07\n**出貨日期：** 2026/06/10　**對應採購單：** PO-HS-2605-0172　**箱數：** 18 箱", "meta"),
                table("ship", [["項次", "料號", "品名", "訂購量", "本次出貨", "欠交", "備註"], *ship_rows],
                      rendering="borderless", align=["c", "l", "l", "r", "r", "r", "l"], widths=[5, 16, 33, 11, 11, 10, 14], total_rows=[len(ship_rows)]),
                P("第 25 至 36 項依原訂交期 2026/06/24 出貨；第 4、11、18 項因原廠配額不足部分欠交，餘量隨第二批補交。", "small"),
                P("收貨簽收：＿＿＿＿＿＿＿＿　日期：＿＿＿＿＿＿　（請核對箱數無誤後簽回一聯）", "small"),
            ],
        ],
    }


def po_pl() -> dict[str, Any]:
    """Polish purchase order with a goods-issue note (WZ) and a consignment note (ReportLab, embedded Noto)."""
    pln = lambda c: money(c, "pl")  # noqa: E731
    val = lambda c: number(c / 100, "pl")  # noqa: E731
    catalog = [
        ("Cement portlandzki CEM I 42,5R, worek 25 kg", "szt.", "320", "26.90"), ("Cement CEM II/B-S 32,5R, worek 25 kg", "szt.", "480", "22.40"),
        ("Wapno hydratyzowane, worek 25 kg", "szt.", "120", "19.80"), ("Zaprawa murarska M10, worek 25 kg", "szt.", "200", "17.60"),
        ("Klej do płytek C2TE, worek 25 kg", "szt.", "150", "48.50"), ("Klej elastyczny S1, worek 20 kg", "szt.", "60", "89.00"),
        ("Fuga cementowa szara, 5 kg", "szt.", "80", "32.40"), ("Grunt głęboko penetrujący, 10 l", "szt.", "45", "61.90"),
        ("Bloczek betonowy 38×24×12 cm", "szt.", "1600", "4.85"), ("Pustak ceramiczny P+W 25 cm", "szt.", "1200", "9.70"),
        ("Nadproże L19 2,10 m", "szt.", "40", "86.00"), ("Pręt żebrowany Ø12 B500SP, 12 m", "szt.", "150", "62.30"),
        ("Pręt żebrowany Ø8 B500SP, 12 m", "szt.", "200", "27.80"), ("Siatka zgrzewana 15×15 Ø6, 2×3 m", "szt.", "90", "58.40"),
        ("Strzemiona 20×30 cm Ø6", "szt.", "600", "1.45"), ("Drut wiązałkowy wyżarzony 1,2 mm, 25 kg", "szt.", "8", "169.00"),
        ("Folia budowlana 0,2 mm, rolka 4×25 m", "szt.", "30", "92.00"), ("Papa podkładowa P/64/1200, rolka 10 m²", "szt.", "40", "54.90"),
        ("Styropian EPS 100-038, 10 cm", "m³", "36.5", "289.00"), ("Wełna mineralna 15 cm, λ 0,035", "m²", "420.0", "21.60"),
        ("Płyta OSB/3 22 mm, 2500×1250", "szt.", "60", "118.00"), ("Płyta g-k 12,5 mm, 1200×2600", "szt.", "180", "27.90"),
        ("Profil CW 50, 3 m", "szt.", "240", "11.20"), ("Profil UW 50, 4 m", "szt.", "120", "12.60"),
        ("Kruszywo płukane 2–8 mm", "t", "24.0", "78.00"), ("Piasek budowlany 0–2 mm", "t", "36.5", "52.00"),
        ("Kostka brukowa 8 cm, szara", "m²", "310.0", "46.90"), ("Obrzeże betonowe 8×30×100 cm", "szt.", "220", "13.40"),
    ]
    rows, net = [], 0
    for number_, (text, unit, qty, price) in enumerate(catalog, start=1):
        value = dmul(qty, price)
        net += value
        q = number(float(qty), "pl", 1 if "." in qty else 0)
        rows.append([str(number_), text, q, unit, number(float(price), "pl", 2), val(value), "23%"])
    vat = part(net, 23, 100)
    gross = net + vat
    n = len(rows)
    segs = continued("zam", [["Lp.", "Nazwa towaru", "Ilość", "J.m.", "Cena netto", "Wartość netto", "VAT"]], rows, [13, n - 13],
                     caption="Pozycje zamówienia", continued_caption="Pozycje zamówienia (ciąg dalszy)", align=["c", "l", "r", "c", "r", "r", "c"],
                     widths=[5, 45, 10, 6, 11, 15, 8],
                     total=[["", "Razem netto", "", "", "", val(net), ""], ["", "VAT 23%", "", "", "", val(vat), ""], ["", "Razem brutto", "", "", "", val(gross), ""]])
    shipped = [(t, u, q, q if k not in (1, 9, 18) else str(int(float(q) * 0.75))) for k, (t, u, q, _p) in enumerate(catalog[:18])]
    wz_rows = []
    for k, (text, unit, q, sent) in enumerate(shipped, start=1):
        missing = float(q) - float(sent)
        wz_rows.append([str(k), text, unit, number(float(q), "pl", 0), number(float(sent), "pl", 0), number(missing, "pl", 0)])
    pallets = [("Cement i zaprawy", 7, 1050 * 7), ("Kleje, fugi, grunty", 3, 2385), ("Bloczki betonowe", 6, 7920), ("Pustaki ceramiczne", 6, 8040),
               ("Stal zbrojeniowa (wiązki)", 4, 6186), ("Folia, papa, drut", 2, 1162)]
    checks = [{"kind": "line_items", "table": "zam", "quantity": 2, "unit_price": 4, "amount": 5, "decimal": ","},
              {"kind": "column_sum", "table": "zam", "columns": [5], "label_column": 1, "total_label": "Razem netto"},
              {"kind": "sum", "terms": [["+", val(net)], ["+", val(vat)]], "equals": val(gross)},
              {"kind": "column_sum", "table": "palety", "columns": [1, 2], "label_column": 0, "total_label": "Razem"}]
    checks += [{"kind": "sum", "terms": [["+", r_[3]], ["-", r_[4]]], "equals": r_[5]} for r_ in wz_rows if r_[5] != "0"]
    return {
        "template": "purchase_order", "page_size": "A4", "languages": ["pl-PL"],
        "metadata": {"title": "Zamówienie ZAM/2026/05/0147 wraz z WZ i listem przewozowym", "author": "Mazur-Bud sp. z o.o.",
                     "subject": "Zamówienie materiałów budowlanych – budowa osiedla „Zielone Tarasy”, etap II",
                     "keywords": ["zamówienie", "WZ", "list przewozowy", "VAT"], "lang": "pl-PL", "created": "2026-05-12T07:45:00Z"},
        "theme": {"accent": "#a33a1f", "rl_size": 9.0},
        "running_header": "Mazur-Bud sp. z o.o. · Zamówienie ZAM/2026/05/0147",
        "running_footer": "Strona {page} z {pages}",
        "arithmetic": checks,
        "pages": [
            [
                group([P("Mazur-Bud", "brand"), P("Mazur-Bud sp. z o.o. · ul. Gen. Władysława Andersa 42, 15-113 Białystok\nNIP 542-318-77-04 · tel. 85 555 31 20 · zaopatrzenie@mazur-bud.example", "small right")], "letterhead"),
                H(1, "Zamówienie nr ZAM/2026/05/0147"),
                group([P("**Dostawca:**\nHurtownia Materiałów Budowlanych „Łęgprzem” S.A.\nul. Żwirki i Wigury 118, 15-703 Białystok\nNIP 966-204-51-88", "meta"),
                       P("**Data zamówienia:** 12.05.2026\n**Termin dostawy:** 19–20.05.2026\n**Miejsce dostawy:** budowa „Zielone Tarasy”, ul. Ciołkowskiego 210, Białystok\n**Płatność:** przelew 30 dni", "meta")], "split"),
                P("Zamawiamy poniższe materiały zgodnie z ofertą nr OF/4471/26 z dnia 08.05.2026. Prosimy o potwierdzenie przyjęcia "
                  "zamówienia do realizacji oraz o wcześniejsze awizowanie dostawy u kierownika budowy, p. Grzegorza Wójcika (tel. 601 555 218)."),
                segs[0],
            ],
            [
                segs[1],
                P(f"Słownie: {pln(gross)} brutto. Ceny zawierają transport na plac budowy oraz rozładunek HDS.", "small"),
                H(2, "Warunki realizacji"),
                L(["Dostawa w dni robocze w godz. 7:00–15:00; stal zbrojeniowa w pierwszym kursie (19.05.2026), izolacje i kruszywa w drugim.",
                   "Do każdej dostawy należy dołączyć dokument WZ oraz deklaracje właściwości użytkowych dla wyrobów budowlanych.",
                   "Palety zwrotne rozliczane według cennika dostawcy; prosimy o wykazanie ich na fakturze w osobnej pozycji.",
                   "Braki ilościowe i uszkodzenia zgłaszamy w ciągu 2 dni roboczych od dostawy."]),
                P("Zamawiający: Krzysztof Mazur, Prezes Zarządu · Sporządziła: Agnieszka Pawłowska, dział zaopatrzenia", "small"),
            ],
            [
                H(1, "WZ – Wydanie zewnętrzne nr WZ/0519/2026"),
                P("**Wystawca:** „Łęgprzem” S.A., magazyn nr 2, ul. Żwirki i Wigury 118, Białystok · **Data wydania:** 19.05.2026\n"
                  "**Odbiorca:** Mazur-Bud sp. z o.o., budowa „Zielone Tarasy” · **Dotyczy zamówienia:** ZAM/2026/05/0147 (pozycje 1–18)", "meta"),
                table("wz", [["Lp.", "Nazwa towaru", "J.m.", "Zamówiono", "Wydano", "Brak"], *wz_rows],
                      align=["c", "l", "c", "r", "r", "r"], widths=[5, 51, 7, 13, 12, 12]),
                P("Braki w pozycjach 2 i 10 zostaną dostarczone w drugim kursie 20.05.2026 razem z pozycjami 19–28 zamówienia.", "small"),
                table("wz-podpis", [["Wydał", "Sprawdził", "Odebrał"], ["Tomasz Kowalczyk", "Ewa Zielińska", "Grzegorz Wójcik"], ["19.05.2026 6:40", "19.05.2026 6:55", "19.05.2026 9:20"]],
                      align=["c", "c", "c"], widths=[33, 33, 34]),
            ],
            [
                H(1, "List przewozowy nr LP/2026/2291"),
                table("lp", [["Nadawca", "„Łęgprzem” S.A., ul. Żwirki i Wigury 118, 15-703 Białystok"], ["Odbiorca", "Mazur-Bud sp. z o.o., budowa „Zielone Tarasy”, ul. Ciołkowskiego 210"],
                             ["Przewoźnik", "Trans-Podlasie Sławomir Dąbrowski, Wasilków"], ["Pojazd", "MAN TGS 26.400 z HDS, nr rej. BI 4471K"],
                             ["Kierowca", "Sławomir Dąbrowski, tel. 602 555 774"], ["Dokumenty", "WZ/0519/2026, deklaracje właściwości użytkowych (6 szt.)"]],
                      header_rows=0, align=["l", "l"], widths=[22, 78]),
                table("palety", [["Rodzaj ładunku", "Palety", "Masa brutto [kg]"], *[[a, str(b), number(c, "pl", 0)] for a, b, c in pallets],
                                 ["Razem", str(sum(b for _a, b, _c in pallets)), number(sum(c for _a, _b, c in pallets), "pl", 0)]],
                      rendering="borderless", align=["l", "r", "r"], widths=[60, 15, 25], total_rows=[len(pallets) + 1], caption="Specyfikacja ładunku"),
                box("callout", "Dopuszczalna masa całkowita pojazdu: 26 000 kg. Rozładunek HDS wyłącznie w strefie wyznaczonej przez kierownika "
                    "budowy; obowiązują kaski i kamizelki odblaskowe.", title="Uwagi BHP", cls="warn"),
                P("Zastrzeżenia odbiorcy: brak. Stan opakowań: bez uszkodzeń. Liczba palet zwrotnych pozostawionych na budowie: 28.", "small"),
                P("Podpis nadawcy: ____________   Podpis przewoźnika: ____________   Podpis odbiorcy: ____________", "small"),
            ],
        ],
    }


def po_es() -> dict[str, Any]:
    """Mexican purchase order and packing list (pylopdf) for a bakery's packaging supplies."""
    mxn = lambda c: money(c, "en-US")  # noqa: E731
    catalog = [
        ("BOL-KR-01", "Bolsa kraft para bolillo, 18×35 cm", "millar", "12", "385.00"), ("BOL-KR-02", "Bolsa kraft con ventana para pan dulce", "millar", "8", "612.50"),
        ("BOL-PP-03", "Bolsa de polipropileno para pan de caja, 50 µm", "millar", "10", "548.00"), ("BOL-BIO-04", "Bolsa compostable con asa, 30×40 cm", "millar", "4", "1240.00"),
        ("CAJ-PAS-05", "Caja para pastel de 1 kg con ventana", "pieza", "1500", "9.85"), ("CAJ-PAS-06", "Caja para pastel de 2 kg con ventana", "pieza", "800", "14.20"),
        ("CAJ-DON-07", "Caja para 6 donas, cartulina sulfatada", "pieza", "2500", "4.35"), ("CAJ-COR-08", "Caja corrugada de reparto 60×40×30 cm", "pieza", "300", "22.80"),
        ("CHA-09", "Charola de cartón dorada 30 cm", "pieza", "1200", "3.15"), ("CHA-10", "Charola de cartón dorada 25 cm", "pieza", "1200", "2.60"),
        ("CAP-11", "Capacillo para cupcake no. 72, café", "millar", "20", "96.00"), ("CAP-12", "Capacillo para panqué rectangular", "millar", "6", "238.00"),
        ("ETQ-13", "Etiqueta térmica 50×30 mm, rollo de 1,000", "rollo", "60", "74.50"), ("ETQ-14", "Etiqueta impresa «La Espiga de Oro», 4 tintas", "millar", "25", "310.00"),
        ("ETQ-15", "Etiqueta de fecha de caducidad, 2 colores", "millar", "15", "142.00"), ("CIN-16", "Cinta canela 48 mm × 150 m", "pieza", "96", "38.90"),
        ("PEL-17", "Película estirable 18 in, calibre 80", "rollo", "40", "289.00"), ("PAP-18", "Papel encerado para envolver, 50×70 cm", "kg", "75.5", "58.00"),
        ("VAS-19", "Vaso térmico 12 oz con tapa", "pieza", "2000", "2.95"), ("SER-20", "Servilleta de papel 30×30, paquete de 500", "paquete", "120", "41.00"),
        ("GUA-21", "Guante de nitrilo talla M, caja de 100", "caja", "60", "129.00"), ("COF-22", "Cofia desechable plisada, paquete de 100", "paquete", "40", "68.00"),
        ("FLE-23", "Flete a planta Zapopan", "servicio", "1", "1850.00"),
    ]
    rows, subtotal = [], 0
    for number_, (code, text, unit, qty, price) in enumerate(catalog, start=1):
        value = dmul(qty, price)
        subtotal += value
        rows.append([str(number_), code, text, f"{float(qty):,.1f}" if "." in qty else f"{int(qty):,}", unit, mxn(int(Decimal(price) * 100)), mxn(value)])
    iva = part(subtotal, 16, 100)
    total = subtotal + iva
    n = len(rows)
    segs = continued("oc", [["Part.", "Clave", "Descripción", "Cantidad", "Unidad", "Precio unitario", "Importe"]], rows, [11, n - 11],
                     caption="Partidas de la orden", continued_caption="Partidas de la orden (continuación)",
                     align=["c", "l", "l", "r", "c", "r", "r"], widths=[6, 11, 39, 10, 10, 12, 12],
                     total=[["", "", "Subtotal", "", "", "", mxn(subtotal)], ["", "", "IVA 16%", "", "", "", mxn(iva)], ["", "", "Total MXN", "", "", "", mxn(total)]])
    ship = []
    for number_, (code, text, unit, qty, _p) in enumerate(catalog[:-1], start=1):
        sent = qty if number_ not in (4, 14) else ("2" if number_ == 4 else "15")
        ship.append([str(number_), code, text, qty, sent, str(round(float(qty) - float(sent), 1)).removesuffix(".0"), unit])
    checks = [{"kind": "line_items", "table": "oc", "quantity": 3, "unit_price": 5, "amount": 6, "decimal": "."},
              {"kind": "column_sum", "table": "oc", "columns": [6], "label_column": 2, "total_label": "Subtotal"},
              {"kind": "sum", "terms": [["+", mxn(subtotal)], ["+", mxn(iva)]], "equals": mxn(total)},
              {"kind": "sum", "terms": [["+", "4"], ["-", "2"]], "equals": "2"}, {"kind": "sum", "terms": [["+", "25"], ["-", "15"]], "equals": "10"}]
    return {
        "template": "purchase_order", "page_size": "Letter", "languages": ["es-MX"],
        "metadata": {"title": "Orden de compra OC-2026-0388 — Empaques y Etiquetas del Bajío", "author": "Panificadora La Espiga de Oro, S.A. de C.V.",
                     "subject": "Compra de empaques, etiquetas y consumibles para planta Zapopan, con lista de empaque",
                     "keywords": ["orden de compra", "lista de empaque", "IVA", "empaques"], "lang": "es-MX", "created": "2026-05-04T16:10:00Z"},
        "theme": {"accent": "#9a6b12", "py_size": 8.8},
        "running_header": "Panificadora La Espiga de Oro, S.A. de C.V. · Orden de compra OC-2026-0388",
        "running_footer": "Página {page} de {pages}",
        "arithmetic": checks,
        "pages": [
            [
                group([P("La Espiga de Oro", "brand"), P("Panificadora La Espiga de Oro, S.A. de C.V.\nAv. Vallarta 6503, Col. Ciudad Granja, 45010 Zapopan, Jal.\nRFC PEO-980312-KL4 · compras@espigadeoro.example", "small right")], "letterhead"),
                H(1, "Orden de compra OC-2026-0388"),
                group([P("**Proveedor:**\nEmpaques y Etiquetas del Bajío, S.A. de C.V.\nBlvd. Adolfo López Mateos 2810 Pte., León, Gto.\nRFC EEB-110524-9Q2 · Contacto: Lic. Mariana Ochoa", "meta"),
                       P("**Fecha:** 04/05/2026\n**Entrega:** 18/05/2026, planta Zapopan, andén 2\n**Condiciones de pago:** crédito a 30 días\n**Moneda:** pesos mexicanos (MXN)\n**Comprador:** Jorge Iñiguez Camarena", "meta")], "split"),
                P("Favor de surtir conforme a la cotización COT-4417 del 29 de abril. Todo material en contacto con alimentos debe "
                  "contar con certificado de grado alimenticio; anexar copia con la factura (CFDI 4.0, uso G01)."),
                segs[0],
            ],
            [
                segs[1],
                H(2, "Condiciones"),
                L(["Horario de recepción: lunes a sábado de 6:00 a 13:00 h; presentar orden de compra y lista de empaque.",
                   "Las etiquetas impresas deben respetar el arte aprobado (versión 3, abril 2026) y el código de barras EAN-13.",
                   "Se aceptan entregas parciales; los faltantes deben entregarse en un plazo máximo de 10 días.",
                   "Material dañado o fuera de especificación se devolverá con cargo al proveedor."]),
                photo("pan", ["bread-bakery"], ["food"], {"bread-bakery": "Pan dulce de la planta Zapopan, listo para empaque"},
                      "Producto terminado", "right", width="36%"),
                P("Las bolsas con ventana y las cajas para pastel corresponden al relanzamiento de la línea de pan dulce artesanal, "
                  "programado para el 1 de junio en nuestras 14 sucursales de la zona metropolitana de Guadalajara."),
                P("Autorizó: Ing. Rocío Villaseñor, Gerente de Planta · Elaboró: Jorge Iñiguez Camarena, Compras", "small"),
            ],
            [
                H(1, "Lista de empaque LE-EEB-26-1187"),
                P("Embarque del 18/05/2026 · Orden de compra OC-2026-0388 · 9 tarimas · transporte propio del proveedor, unidad JAL-58-41-R", "small"),
                table("le", [["Part.", "Clave", "Descripción", "Pedido", "Surtido", "Pendiente", "Unidad"], *ship],
                      rendering="borderless", align=["c", "l", "l", "r", "r", "r", "c"], widths=[6, 12, 44, 10, 10, 10, 8]),
                box("callout", "Pendientes: partida 4 (bolsa compostable) por desabasto de resina; partida 14 (etiqueta impresa) en espera de "
                    "aprobación de la prueba de color. Ambas se entregarán a más tardar el 28/05/2026.", title="Entregas pendientes", cls="note"),
                P("Recibió: ______________________   Fecha y hora: ______________   Sello de almacén", "small"),
            ],
        ],
    }


DOCS: list[tuple[str, str, Any]] = [
    ("w2-card-en-09", "pylopdf", card_en),
    ("w2-card-ko-10", "chromium", card_ko),
    ("w2-card-tr-11", "reportlab", card_tr),
    ("w2-card-he-12", "libreoffice", card_he),
    ("w2-receipts-en-13", "chromium", receipts_en),
    ("w2-receipts-zhcn-14", "reportlab", receipts_zhcn),
    ("w2-receipts-th-15", "pylopdf", receipts_th),
    ("w2-receipts-vi-16", "libreoffice", receipts_vi),
    ("w2-utility-en-17", "libreoffice", utility_en),
    ("w2-utility-de-18", "reportlab", utility_de),
    ("w2-utility-hi-19", "chromium", utility_hi),
    ("w2-utility-ru-20", "pylopdf", utility_ru),
    ("w2-po-en-21", "chromium", po_en),
    ("w2-po-zhtw-22", "libreoffice", po_zhtw),
    ("w2-po-pl-23", "reportlab", po_pl),
    ("w2-po-es-24", "pylopdf", po_es),
]
