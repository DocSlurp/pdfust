"""Authored wild-v2 office documents: government forms, contracts, CVs and meeting minutes.

Sixteen documents across four producers. Forms carry real AcroForm widgets
(ReportLab) filled by pylopdf; contracts use nested ordered clause lists and
payment schedules; CVs vary single- and two-column layouts; minutes carry
action-item tables that continue across pages and vote tallies that add up.
All people, companies, addresses and identifiers are fictional.
"""

# Authored data tables: long lines, positional boolean field values and implicit concatenation in lists are intentional.
# ruff: noqa: E501, FBT003, ISC004, PLR2004, PLR0913, PLR0917, ANN401
from __future__ import annotations

from datetime import date
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
    field,
    form,
    group,
    item,
    pair,
    photo,
    screenshot,
    table,
)

LRM, RLM = "\u200e", "\u200f"


# ---------------------------------------------------------------- shared helpers


def fee_table(table_id: str, rows: list[tuple[str, str, int, int]], locale: str, header: list[str], total_label: str,
              *, caption: str = "", qty_fmt: Any = str, widths: list[float] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    """Build a fee/price table: (code, description, quantity, unit minor units) rows plus a total row.

    Returns the table block, its arithmetic declarations and the total in minor units.
    """
    body = []
    total = 0
    for code, text, quantity, unit in rows:
        amount = quantity * unit
        total += amount
        body.append([code, text, qty_fmt(quantity), money(unit, locale), money(amount, locale)])
    values = [header, *body, ["", total_label, "", "", money(total, locale)]]
    block = table(table_id, values, caption=caption, align=["l", "l", "r", "r", "r"], widths=widths or [9, 49, 10, 15, 17],
                  total_rows=[len(values) - 1])
    checks = [{"kind": "line_items", "table": table_id, "quantity": 2, "unit_price": 3, "amount": 4},
              {"kind": "column_sum", "table": table_id, "columns": [4], "label_column": 1, "total_label": total_label}]
    return block, checks, total


def ordered(items: list[Any]) -> dict[str, Any]:
    """Ordered (possibly nested) list."""
    return L(items, ordered=True)


def classed(block: dict[str, Any], cls: str) -> dict[str, Any]:
    """Attach a CSS class to a block (Chromium uses it; other producers ignore it)."""
    block["cls"] = cls
    return block


def legal_css(starts: dict[int, int]) -> str:
    """Chromium CSS for legal clause numbering (4. / 4.1 / (a)) continuing across page sections."""
    css = ("ol.cl{padding-inline-start:2.1em}ol.cl>li{margin-top:.45em}ol.cl>li::marker{content:counter(list-item) '.  ';font-weight:700}"
           "ol.cl ol{padding-inline-start:2.4em}ol.cl>li>ol>li::marker{content:counters(list-item,'.') '  '}"
           "ol.cl ol ol{list-style-type:lower-alpha}ol.cl ol ol>li::marker{content:'(' counter(list-item,lower-alpha) ')  '}")
    css += "".join(f"section.pg[data-page='{page}'] ol.cl{{counter-reset:list-item {start}}}" for page, start in starts.items())
    return css


# ================================================================ government forms


def form_en() -> dict[str, Any]:
    """City business license renewal with change of location (US Letter, 5 pages)."""
    fees, fee_checks, fee_total = fee_table("fees", [
        ("R-02", "Annual renewal fee, Class B food service establishment", 1, 18500),
        ("E-01", "Per-employee fee (full-time equivalents as of January 1)", 14, 1250),
        ("H-07", "Retail food health endorsement (Tri-County Health)", 1, 9600),
        ("L-03", "Liquor license administrative surcharge, hotel & restaurant", 1, 6000),
        ("C-11", "Change of business location processing", 1, 2500),
        ("S-04", "Sidewalk café permit, per table (Aspen Ave frontage)", 4, 1800),
    ], "en-US", ["Code", "Fee item", "Qty", "Unit fee", "Amount"], "Total fee due", caption="Section 5 — Fee calculation (2026–2027 schedule)")
    total = money(fee_total, "en-US")
    return {
        "template": "government_form", "page_size": "Letter", "languages": ["en-US", "ja"],
        "metadata": {"title": "Form BL-210 Business License Renewal and Change of Information — Hoshino Ramen & Grill LLC",
                     "author": "City of Larkspur Falls Finance Department", "subject": "Business license renewal, license BL0418263",
                     "keywords": ["business license", "renewal", "change of address", "Form BL-210", "Larkspur Falls"], "lang": "en-US",
                     "created": "2026-02-17T15:42:00Z"},
        "theme": {"accent": "#1d4a6e", "rl_size": 10.4},
        "running_header": "City of Larkspur Falls · Form BL-210 (Rev. 03/2026) · License BL0418263",
        "running_footer": "Page {page} of {pages} — Incomplete applications will be returned. Keep a copy for your records.",
        "arithmetic": [*fee_checks, {"kind": "sum", "terms": [["+", total], ["-", "$0.00"]], "equals": total}],
        "pages": [
            [
                group([P("City of Larkspur Falls", "brand"),
                       P("Finance Department · Business License Division\n410 Aspen Civic Plaza, Suite 120\nLarkspur Falls, CO 80496\n(970) 555-0188 · licensing@larkspurfalls.example", "small right")], "letterhead"),
                H(1, "Business License Renewal and Change of Information"),
                P("**Form BL-210** · Use this form to renew an existing business license for the period July 1, 2026 through June 30, 2027 "
                  "and to report changes to ownership, location, mailing address or business activity. A separate form (BL-100) is "
                  "required for a new business or for a change of legal entity."),
                H(2, "Instructions"),
                L(["Type or print clearly in blue or black ink. Fields marked with an asterisk (*) are required.",
                   "Renewal applications must be received by **April 30, 2026**. Applications received after that date are subject to a "
                   "late fee of 25% of the renewal fee per month, up to 100%.",
                   "If your business moved, complete Section 3 and attach a zoning clearance (Form Z-4) for the new location.",
                   "Sales tax accounts are administered separately; changes reported here do **not** update your sales tax license.",
                   "Fees are non-refundable once the application has been processed."], ordered=True),
                box("callout", "Most renewals can be filed online at [larkspurfalls.example/licensing](https://larkspurfalls.example/licensing) "
                    "without paper forms. Use this paper form only if you are also reporting a change of location or ownership.",
                    title="File online and save time", cls="note"),
                form("Section 1 — Business identification", [
                    [field("legal_name", "Legal name of business *", "Hoshino Ramen & Grill LLC", width=2),
                     field("dba", "Trade name (DBA)", "Hoshino Ramen", width=1.2)],
                    [field("license_no", "City license number *", "BL0418263", field_type="comb", max_len=9, width=1.4),
                     field("fein", "Federal EIN (no dashes) *", "844172093", field_type="comb", max_len=9, width=1.4),
                     field("entity", "Entity type *", "Limited liability company", field_type="choice",
                           options=["Sole proprietorship", "General partnership", "Limited liability company", "Corporation", "Nonprofit"], width=1.4)],
                    [field("naics", "NAICS code", "722511", field_type="comb", max_len=6, width=1),
                     field("started", "Date business started in city", "09/14/2021", width=1),
                     field("state_id", "Colorado SOS ID", "20211694530", width=1.2)],
                ]),
            ],
            [
                form("Section 2 — Owners, members and responsible officers", [
                    [field("owner1_name", "Name (as shown on ID) *", "Aiko Hoshino (星野 愛子)", width=2),
                     field("owner1_title", "Title", "Managing member", width=1.2),
                     field("owner1_pct", "Ownership %", "60", width=0.7)],
                    [field("owner1_phone", "Phone", "(970) 555-0147", width=1),
                     field("owner1_email", "Email", "aiko@hoshinoramen.example", width=1.6),
                     field("owner1_res", "Colorado resident", True, field_type="checkbox", width=1)],
                    [field("owner2_name", "Name (as shown on ID)", "Rafael Medeiros-Kühn", width=2),
                     field("owner2_title", "Title", "Member", width=1.2),
                     field("owner2_pct", "Ownership %", "40", width=0.7)],
                    [field("owner2_phone", "Phone", "(970) 555-0162", width=1),
                     field("owner2_email", "Email", "rafael.mk@hoshinoramen.example", width=1.6),
                     field("owner2_res", "Colorado resident", True, field_type="checkbox", width=1)],
                ]),
                P("List every person who owns 10% or more of the business or who is responsible for day-to-day operations. Attach a "
                  "separate sheet if there are more than two. Changes in ownership of 50% or more require a new license (Form BL-100)."),
                form("Section 3 — Change of location or mailing address", [
                    [field("chg_location", "Business location has changed", True, field_type="checkbox", width=1),
                     field("chg_mailing", "Mailing address has changed", False, field_type="checkbox", width=1),
                     field("chg_effective", "Effective date of change *", "03/01/2026", width=1)],
                    [field("prev_address", "Previous business address", "1187 Tamarack Street, Unit B", width=2),
                     field("prev_zip", "Previous ZIP", "80494", field_type="comb", max_len=5, width=1)],
                    [field("new_address", "New business address (no P.O. boxes) *", "62 Aspen Avenue, Ground Floor", width=2),
                     field("new_zip", "New ZIP *", "80496", field_type="comb", max_len=5, width=1)],
                    [field("parcel", "Assessor parcel number (if known)", "R0071-442-19", width=1.4),
                     field("zoning", "Zoning clearance (Form Z-4) no.", "Z4-26-0093", width=1.2),
                     field("sqft", "Floor area (sq ft)", "2,350", width=0.8)],
                ]),
                box("sidebar", "If you moved into a building that previously held a restaurant, the Fire Prevention Bureau will contact you "
                    "within ten business days to schedule an occupancy inspection. Keep the inspection report on site and available "
                    "to city staff. A change of location does not transfer your liquor license; file the state modification "
                    "(DR 8442) separately with the Liquor Enforcement Division.", title="Inspections after a move"),
                P("¹ A parcel number is printed on your property tax statement or lease exhibit. Leave blank if unknown.", "small"),
            ],
            [
                form("Section 4 — Business activity and employees", [
                    [field("activity", "Describe your principal business activity *",
                           "Full-service restaurant: ramen, rice bowls and Japanese grill; beer, sake and wine served with meals; takeout and delivery through third-party apps.",
                           multiline=True, width=1)],
                    [field("ft_emp", "Full-time employees", "11", width=1), field("pt_emp", "Part-time employees", "6", width=1),
                     field("fte", "Full-time equivalents *", "14", width=1),
                     field("hours", "Hours of operation", "Tue–Sun 11:00–22:00", width=1.6)],
                    [field("serves_alcohol", "Sells or serves alcohol", True, field_type="checkbox", width=1),
                     field("food_service", "Prepares or serves food", True, field_type="checkbox", width=1),
                     field("home_based", "Home-based business", False, field_type="checkbox", width=1)],
                    [field("liquor_no", "State liquor license no.", "03-11845-0000", width=1.2),
                     field("health_permit", "Health permit no.", "TCH-RF-2021-5530", width=1.2),
                     field("tables", "Sidewalk café tables requested", "4", width=1)],
                ]),
                P("Full-time equivalents are calculated by adding all hours worked by part-time staff during the first full week of "
                  "January, dividing by 40 and adding the result to the number of full-time employees. Round to the nearest whole "
                  "number. Seasonal staff who worked fewer than 60 days in the previous year are excluded."),
                fees,
                P(f"Make checks payable to **City of Larkspur Falls**. The total due for this application is **{total}**. "
                  "Card payments made at the counter or online carry a 2.4% convenience fee charged by the card processor; "
                  "that fee is not included above. Returned checks are subject to a $35.00 charge."),
                box("footnote", "² The per-employee fee is capped at 120 full-time equivalents for any one license (Larkspur Falls Municipal Code § 5-2-140)."),
            ],
            [
                form("Section 6 — Payment", [
                    [field("pay_method", "Payment method *", "Check", field_type="choice", options=["Check", "Money order", "Credit card", "ACH debit"], width=1),
                     field("check_no", "Check number", "4471", width=1), field("amount_paid", "Amount enclosed *", total, width=1)],
                ]),
                H(2, "Section 7 — Declarations"),
                P("By signing this application, the applicant and every signatory declare that:"),
                L(["the information on this form and on all attachments is true, correct and complete to the best of their knowledge;",
                   "the business holds every state and county permit required for the activities described in Section 4;",
                   "the business will comply with Title 5 (Business Regulations) and Title 17 (Zoning) of the Larkspur Falls Municipal Code;",
                   "they understand that a false statement may result in denial, suspension or revocation of the license and may be "
                   "punishable under C.R.S. § 18-8-503;",
                   "the city may share license information with the Colorado Department of Revenue and Tri-County Health."]),
                form("", [
                    [field("decl_true", "I certify that the statements above are true and complete.", True, field_type="checkbox", width=1)],
                    [field("decl_contact", "I agree to receive renewal notices by email instead of mail.", True, field_type="checkbox", width=1)],
                    [field("decl_tax", "The business has no unpaid city taxes, fees or penalties.", True, field_type="checkbox", width=1)],
                ]),
                H(2, "Privacy notice"),
                P("Information collected on this form is a public record under the Colorado Open Records Act, except for Social "
                  "Security numbers, federal tax identification numbers, home addresses and personal telephone numbers, which the "
                  "city withholds from public inspection. Business names, locations and license status are published in the online "
                  "business directory."),
                P("Questions about the renewal process can be directed to the Business License Division Monday through Friday, "
                  "8:00 a.m. to 4:30 p.m., at (970) 555-0188. Interpreters are available on request; please mention your preferred "
                  "language when you call (日本語、Español, Tiếng Việt and others)."),
            ],
            [
                form("Section 8 — Signature", [
                    [field("sign_name", "Printed name of authorized signer *", "Aiko Hoshino", width=1.5),
                     field("sign_title", "Title *", "Managing member", width=1), field("sign_date", "Date *", "02/17/2026", width=0.8)],
                    [field("preparer", "Prepared by (if other than signer)", "Mountain Ledger Bookkeeping — Dana Whitfield", width=1.6),
                     field("preparer_phone", "Preparer phone", "(970) 555-0121", width=1)],
                ]),
                photo("p1", ["city-hall"], ["civic", "building"], {"city-hall": "Larkspur Falls City Hall, 410 Aspen Civic Plaza. Walk-in renewals are accepted at the Finance counter on the first floor."},
                      "Larkspur Falls City Hall", wrap="right", width="40%", width_cm=6.4),
                P("**Where to file.** Mail the signed form, your payment and any attachments to City of Larkspur Falls, Business "
                  "License Division, P.O. Box 2240, Larkspur Falls, CO 80496-2240, or drop them in the secure payment box next to the "
                  "main entrance of City Hall. Do not send cash by mail."),
                P("**Processing time.** Complete renewals are processed within 15 business days. A change of location adds up to "
                  "10 business days for the zoning and fire reviews. Your new license certificate will be mailed to the business "
                  "address and must be posted where customers can see it."),
                P("**Checklist.** Signed Form BL-210 · payment · Form Z-4 zoning clearance (if moving) · copy of current health permit · "
                  "copy of state liquor license (if serving alcohol) · sidewalk café site plan (if requesting tables)."),
                H(2, "For office use only"),
                table("office", [["Received", "Reviewed by", "Zoning", "Fire", "Health", "Receipt no."],
                                 ["02/19/2026", "M. Okafor", "Approved", "Pending", "On file", "R-26-018842"]],
                      caption="Processing record", widths=[16, 18, 16, 16, 16, 18]),
            ],
        ],
    }


def form_de() -> dict[str, Any]:
    """Gewerbeanmeldung (GewA 1 style) with fees, 3 pages A4."""
    fees, fee_checks, fee_total = fee_table("gebuehren", [
        ("1.1", "Gewerbeanmeldung (Bearbeitungsgebühr)", 1, 2600),
        ("1.4", "Beglaubigte Zweitschrift der Anmeldebestätigung", 2, 650),
        ("3.2", "Auskunft aus dem Gewerbezentralregister (eigene Person)", 1, 1300),
        ("5.1", "Schriftliche Bescheinigung für Kreditinstitut", 1, 800),
    ], "de", ["Nr.", "Gebührentatbestand", "Anzahl", "Einzelbetrag", "Betrag"], "Summe der Gebühren",
        caption="Tabelle 1: Gebühren nach der Verwaltungsgebührensatzung der Stadt Bad Kellbach")
    total = money(fee_total, "de")
    return {
        "template": "government_form", "page_size": "A4", "languages": ["de-DE", "tr"],
        "metadata": {"title": "Gewerbeanmeldung – Yıldırım Fahrradwerkstatt", "author": "Stadt Bad Kellbach, Ordnungsamt – Gewerbeangelegenheiten",
                     "subject": "Anzeige nach § 14 GewO, Neuerrichtung eines Handwerksbetriebs",
                     "keywords": ["Gewerbeanmeldung", "GewA 1", "Gewerbeordnung", "Bad Kellbach"], "lang": "de-DE",
                     "created": "2026-03-09T10:05:00Z"},
        "theme": {"accent": "#7a1f2b", "rl_size": 10.2, "rl_serif": False},
        "running_header": "Stadt Bad Kellbach · Ordnungsamt · Gewerbeanmeldung (GewA 1)",
        "running_footer": "Seite {page} von {pages} · Aktenzeichen 32.1-GA-2026-0417",
        "arithmetic": fee_checks,
        "pages": [
            [
                group([P("Stadt Bad Kellbach", "brand"),
                       P("Ordnungsamt – Gewerbeangelegenheiten\nRathausplatz 3 · 79341 Bad Kellbach\nTel. 07644 555-210 · gewerbe@bad-kellbach.example", "small right")], "letterhead"),
                H(1, "Gewerbe­anmeldung nach § 14 GewO"),
                P("Bitte füllen Sie dieses Formular vollständig in Druckbuchstaben aus. Für jede Betriebsstätte ist eine eigene "
                  "Anzeige erforderlich. Die Anmeldung ist innerhalb von vier Wochen nach Beginn der Tätigkeit abzugeben; "
                  "eine verspätete Anzeige kann als Ordnungs­widrigkeit mit einem Bußgeld geahndet werden."),
                box("callout", "Personengesellschaften (z. B. GbR) melden für jede geschäftsführende Gesellschafterin und jeden "
                    "geschäftsführenden Gesellschafter gesondert an. Juristische Personen geben unter Abschnitt 1 die Angaben der "
                    "gesetzlichen Vertretung an.", title="Hinweis", cls="note"),
                form("Abschnitt 1 – Angaben zur Person", [
                    [field("nachname", "Familienname *", "Yıldırım", width=1.2), field("vorname", "Vorname(n) *", "Derya Elif", width=1.2),
                     field("geschlecht", "Geschlecht", "weiblich", field_type="choice", options=["weiblich", "männlich", "divers", "keine Angabe"], width=0.8)],
                    [field("geburtsdatum", "Geburtsdatum *", "14.06.1991", width=1), field("geburtsort", "Geburtsort *", "Kayseri (Türkei)", width=1.4),
                     field("staat", "Staatsangehörigkeit *", "deutsch", field_type="choice",
                           options=["deutsch", "türkisch", "andere EU-Staatsangehörigkeit", "sonstige"], width=1)],
                    [field("strasse", "Anschrift der Wohnung (Straße, Hausnummer) *", "Mühlbachweg 17", width=2),
                     field("plz", "Postleitzahl *", "79341", field_type="comb", max_len=5, width=1)],
                    [field("ort", "Ort *", "Bad Kellbach", width=1.2), field("telefon", "Telefon", "0176 5550 3381", width=1),
                     field("email", "E-Mail", "derya@radwerk-kellbach.example", width=1.6)],
                    [field("steuer_id", "Steuerliche Identifikationsnummer", "47036892815", field_type="comb", max_len=11, width=2),
                     field("handwerk", "Eintragung in die Handwerksrolle vorhanden", True, field_type="checkbox", width=1.2)],
                ]),
                P("Die Angaben zur Person werden mit dem Melderegister abgeglichen. Bei ausländischer Staatsangehörigkeit außerhalb der "
                  "EU fügen Sie bitte eine Kopie des Aufenthaltstitels bei, aus dem die Erlaubnis zur selbständigen Tätigkeit hervorgeht.", "small"),
                H(3, "Welche Unterlagen benötige ich?"),
                L(["gültiger Personalausweis oder Reisepass mit Meldebescheinigung",
                   "bei Handwerksbetrieben: Handwerkskarte oder Eintragungsbestätigung der Handwerkskammer",
                   "bei erlaubnispflichtigen Gewerben: die Erlaubnis (z. B. nach § 34c GewO)",
                   "bei Vertretung: schriftliche Vollmacht und Ausweiskopie der vertretenen Person"]),
            ],
            [
                form("Abschnitt 2 – Angaben zum Betrieb", [
                    [field("betrieb_name", "Geschäftsbezeichnung", "Radwerk Kellbach – Fahrradwerkstatt Yıldırım", width=2),
                     field("beginn", "Beginn der Tätigkeit *", "01.04.2026", width=1)],
                    [field("betrieb_strasse", "Betriebsstätte (Straße, Hausnummer) *", "Bahnhofstraße 42a", width=2),
                     field("betrieb_plz", "Postleitzahl *", "79341", field_type="comb", max_len=5, width=1)],
                    [field("art", "Art des Betriebs *", "Handwerk", field_type="choice", options=["Industrie", "Handwerk", "Handel", "Sonstiges"], width=1),
                     field("beschaeftigte_vz", "Beschäftigte Vollzeit", "1", width=0.8), field("beschaeftigte_tz", "Beschäftigte Teilzeit", "2", width=0.8)],
                    [field("taetigkeit", "Angemeldete Tätigkeit (genaue Bezeichnung) *",
                           "Reparatur und Wartung von Fahrrädern und Pedelecs, Einzelhandel mit Fahrrädern, Fahrradteilen und Zubehör, Vermietung von Lastenrädern",
                           multiline=True, width=1)],
                    [field("neuerrichtung", "Neuerrichtung", True, field_type="checkbox", width=1),
                     field("uebernahme", "Übernahme", False, field_type="checkbox", width=1),
                     field("nebenerwerb", "Nebenerwerb", False, field_type="checkbox", width=1),
                     field("erlaubnis", "Erlaubnispflichtig", False, field_type="checkbox", width=1)],
                ]),
                P("Bitte beschreiben Sie die Tätigkeit so genau wie möglich. Allgemeine Angaben wie „Handel aller Art“ oder "
                  "„Dienstleistungen“ können nicht angenommen werden, weil die Anmeldung an Finanzamt, Handwerkskammer, "
                  "Berufsgenossenschaft und Statistisches Landesamt weitergeleitet wird."),
                fees,
                P(f"Die Gebühren in Höhe von **{total}** sind bei Abgabe der Anmeldung fällig. Sie können bar, mit Girocard oder "
                  "per Überweisung auf das Konto der Stadtkasse (IBAN DE41 6805 0101 0000 1234 56, Verwendungszweck: "
                  "32.1-GA-2026-0417) bezahlt werden. Die Anmeldebestätigung wird erst nach Zahlungseingang ausgehändigt."),
                box("footnote", "¹ Gebühren gemäß Anlage 1 der Verwaltungsgebührensatzung vom 12.11.2024; eine Ermäßigung ist für "
                    "Existenzgründungen aus der Arbeitslosigkeit nach Vorlage des Bewilligungsbescheids möglich."),
            ],
            [
                H(2, "Abschnitt 3 – Erklärungen"),
                L(["Mir ist bekannt, dass die Anmeldung keine Genehmigung darstellt und dass für bestimmte Tätigkeiten zusätzliche "
                   "Erlaubnisse erforderlich sind.",
                   "Ich versichere, dass gegen mich kein Gewerbeuntersagungsverfahren anhängig ist.",
                   "Änderungen der Tätigkeit, eine Verlegung der Betriebsstätte oder die Aufgabe des Betriebs zeige ich unverzüglich an."]),
                form("", [
                    [field("erkl_richtig", "Ich versichere die Richtigkeit und Vollständigkeit meiner Angaben.", True, field_type="checkbox", width=1)],
                    [field("erkl_daten", "Ich habe die Datenschutzhinweise zur Kenntnis genommen.", True, field_type="checkbox", width=1)],
                    [field("unterschrift_ort", "Ort, Datum *", "Bad Kellbach, 09.03.2026", width=1),
                     field("unterschrift_name", "Name der unterzeichnenden Person *", "Derya Elif Yıldırım", width=1.4)],
                ]),
                H(2, "Datenschutzhinweise"),
                P("Die Erhebung der Daten beruht auf § 14 der Gewerbeordnung in Verbindung mit Art. 6 Abs. 1 Buchst. c und e DSGVO. "
                  "Die Daten werden an die in § 14 Abs. 8 GewO genannten Stellen übermittelt, insbesondere an das Finanzamt, die "
                  "Industrie- und Handelskammer oder Handwerkskammer, die Agentur für Arbeit und das Statistische Landesamt. "
                  "Name, betriebliche Anschrift und angezeigte Tätigkeit dürfen allgemein zugänglich gemacht werden."),
                P("Sie haben das Recht auf Auskunft, Berichtigung und Einschränkung der Verarbeitung. Verantwortliche Stelle ist die "
                  "Stadt Bad Kellbach, Ordnungsamt; die behördliche Datenschutz­beauftragte erreichen Sie unter "
                  "datenschutz@bad-kellbach.example."),
                box("sidebar", "Eingang: 09.03.2026 · bearbeitet: K. Hollerbach · Gebühr bezahlt (Girocard) · Weiterleitung an "
                    "Finanzamt Emmendingen, HWK Freiburg, BG ETEM am 10.03.2026", title="Bearbeitungsvermerke (nur für die Behörde)"),
                photo("p1", ["city-hall"], ["civic", "building"], {"city-hall": "Rathaus Bad Kellbach – das Bürgerbüro befindet sich im Erdgeschoss, Eingang Marktseite."},
                      "Rathaus Bad Kellbach", wrap="right", width="36%", width_cm=5.6),
                P("**Öffnungszeiten des Gewerbeamts:** Mo, Di, Do 8:00–12:00 Uhr, Do zusätzlich 14:00–18:00 Uhr. Termine können "
                  "online unter [bad-kellbach.example/termine](https://bad-kellbach.example/termine) gebucht werden."),
                P("Bitte bringen Sie zur Abgabe Ihren Personalausweis oder Reisepass mit; bei Handwerksbetrieben zusätzlich die "
                  "Eintragungsbestätigung der Handwerkskammer. Die Anmeldebestätigung erhalten Sie in der Regel sofort."),
            ],
        ],
    }


def form_ja() -> dict[str, Any]:
    """住所異動届（転居）と証明書交付申請、3 pages A4."""
    fees, fee_checks, fee_total = fee_table("tesuryo", [
        ("1", "住民票の写し（世帯全員・続柄記載）", 2, 300),
        ("2", "住民票記載事項証明書", 1, 300),
        ("3", "印鑑登録証明書", 1, 300),
        ("4", "戸籍の附票の写し", 1, 400),
    ], "ja", ["番号", "証明書の種類", "通数", "手数料", "金額"], "合計", caption="表１　証明書交付手数料（青葉台市手数料条例別表第２）")
    total = money(fee_total, "ja")
    return {
        "template": "government_form", "page_size": "A4", "languages": ["ja"],
        "metadata": {"title": "住民異動届（転居届）・証明書交付申請書 — 山口 陽菜", "author": "青葉台市 市民課",
                     "subject": "転居届及び証明書交付申請", "keywords": ["住民異動届", "転居届", "証明書交付申請", "青葉台市"], "lang": "ja",
                     "created": "2026-04-06T01:30:00Z"},
        "theme": {"accent": "#2c5f2d", "rl_size": 10.2},
        "running_header": "青葉台市　住民異動届（転居届）　様式第３号",
        "running_footer": "{page}／{pages}ページ　受付番号　市民－２６－０４１８７",
        "arithmetic": fee_checks,
        "pages": [
            [
                group([P("青葉台市", "brand"), P("市民部　市民課　住民記録係\n〒２２７－８５０１　青葉台市本町一丁目１番１号\n電話　０４５－５５５－２１１０（直通）", "small right")], "letterhead"),
                H(1, "住民異動届（転居届）"),
                P("市内で住所を変更した方は、新しい住所に住み始めた日から１４日以内に届け出てください。届出には、本人確認書類"
                  "（マイナンバーカード、運転免許証など）と、異動する方全員のマイナンバーカードが必要です。代理人が届け出る場合は、"
                  "委任状と代理人の本人確認書類をお持ちください。"),
                box("callout", "正当な理由なく届出期間を過ぎた場合は、住民基本台帳法第５２条により過料を科されることがあります。"
                    "届出後、国民健康保険・児童手当・小中学校の手続きも同じ窓口で案内します。", title="ご注意", cls="warn"),
                form("１　届出人", [
                    [field("shimei", "氏名 *", "山口 陽菜", width=1.2), field("furigana", "フリガナ *", "ヤマグチ ヒナ", width=1.2),
                     field("seinengappi", "生年月日 *", "1988年11月3日", width=1)],
                    [field("zokugara", "世帯主との続柄 *", "本人", width=0.8),
                     field("denwa", "日中の連絡先 *", "090-5550-2741", width=1.2),
                     field("kojin_bango", "個人番号（マイナンバー）", "482917305614", field_type="comb", max_len=12, width=2)],
                ]),
                form("２　住所", [
                    [field("shin_jusho", "新住所 *", "青葉台市緑町三丁目８番２号　グリーンテラス緑町２０５", width=2.4),
                     field("shin_yubin", "郵便番号 *", "2270042", field_type="comb", max_len=7, width=1)],
                    [field("kyu_jusho", "旧住所 *", "青葉台市桜ヶ丘一丁目２２番１５号", width=2.4),
                     field("kyu_yubin", "郵便番号", "2270031", field_type="comb", max_len=7, width=1)],
                    [field("idou_bi", "異動日（住み始めた日） *", "2026年3月28日", width=1),
                     field("todoke_bi", "届出日 *", "2026年4月6日", width=1),
                     field("setai_nushi", "世帯主氏名 *", "山口 陽菜", width=1),
                     field("ninzu", "異動人数 *", "3", field_type="choice", options=["1", "2", "3", "4", "5", "6"], width=0.6)],
                ]),
                H(2, "届出に必要なもの"),
                L(["届出人の本人確認書類（マイナンバーカード、運転免許証、在留カードなど）",
                   "異動する方全員のマイナンバーカード（お持ちの方のみ）",
                   "国民健康保険の資格確認書、介護保険被保険者証（加入している方）",
                   "代理人が届け出る場合は委任状（世帯員以外の方）"]),
            ],
            [
                H(2, "３　異動する方"),
                P("届出人と一緒に転居する方を記入してください。世帯全員が異動する場合は、全員分を記入します。"),
                form("", [
                    [field("m1_shimei", "氏名", "山口 悠真", width=1.2), field("m1_furigana", "フリガナ", "ヤマグチ ユウマ", width=1.2),
                     field("m1_seinen", "生年月日", "2016年5月21日", width=1),
                     field("m1_zoku", "続柄", "子", width=0.7)],
                    [field("m2_shimei", "氏名", "山口 澄子", width=1.2), field("m2_furigana", "フリガナ", "ヤマグチ スミコ", width=1.2),
                     field("m2_seinen", "生年月日", "1957年8月9日", width=1),
                     field("m2_zoku", "続柄", "母", width=0.7)],
                ]),
                H(2, "４　関連する手続き"),
                P("該当するものに印を付けてください。担当課へ情報を引き継ぎ、必要な書類をご案内します。"),
                form("", [
                    [field("kokuho", "国民健康保険に加入している", True, field_type="checkbox", width=1),
                     field("jidou_teate", "児童手当を受給している", True, field_type="checkbox", width=1)],
                    [field("tenkou", "小・中学校の転校がある", True, field_type="checkbox", width=1),
                     field("inkan", "印鑑登録をしている", False, field_type="checkbox", width=1)],
                    [field("kaigo", "介護保険の認定を受けている", True, field_type="checkbox", width=1),
                     field("mynumber_card", "マイナンバーカードの住所変更をする", True, field_type="checkbox", width=1)],
                ]),
                P("転校する場合は、在籍校から「在学証明書」と「教科用図書給与証明書」を受け取り、教育委員会学務課（本庁舎４階）"
                  "で手続きしてください。新しい学区は緑町小学校です。介護保険の認定を受けている方は、高齢福祉課で被保険者証の"
                  "住所変更を行います。"),
                box("sidebar", "マイナンバーカードの券面の住所は、窓口で追記します。暗証番号（数字４桁）が必要です。"
                    "暗証番号を忘れた場合は、本人確認のうえ再設定できます。", title="マイナンバーカードの住所変更"),
            ],
            [
                H(2, "５　証明書交付申請"),
                P("転居後の住民票の写しなどが必要な場合は、あわせて申請できます。手数料は現金またはキャッシュレス決済でお支払いください。"),
                fees,
                P(f"手数料の合計は{total}です。勤務先・学校への提出用、運転免許証の住所変更用など、使いみちに応じて必要な通数を"
                  "請求してください。"),
                form("６　署名", [
                    [field("shomei", "届出人署名 *", "山口 陽菜", width=1.2), field("shomei_bi", "記入日 *", "2026年4月6日", width=1),
                     field("dairinin", "代理人の場合は代理人氏名", "（本人届出）", width=1.2)],
                ]),
                H(2, "個人情報の取扱いについて"),
                P("この届出書に記入された個人情報は、住民基本台帳の記録及び関連する行政手続きのために利用し、法令に基づく場合を除き、"
                  "目的外に利用又は提供することはありません。"),
                table("shokuin", [["受付", "入力", "照合", "証明発行", "関連課連絡"],
                                  ["4/6 佐藤", "4/6 中村", "4/6 小林", "4/6 済", "国保・児童・学務・介護"]],
                      caption="職員記入欄", widths=[18, 18, 18, 18, 28]),
                photo("p1", ["city-hall"], ["civic", "building"], {"city-hall": "青葉台市役所本庁舎。市民課は１階３番窓口です。"},
                      "青葉台市役所本庁舎", wrap="left", width="34%", width_cm=5.2),
                P("**受付時間**　平日８時３０分から１７時１５分まで。毎月第２・第４土曜日の午前（９時から１２時）も、転入・転居・転出の届出を"
                  "受け付けています。混雑する３月下旬から４月上旬は、待ち時間が２時間を超えることがあります。"),
                P("**お問い合わせ**　市民課住民記録係　電話０４５－５５５－２１１０。外国語での案内（英語・中国語・韓国語・ベトナム語）は、"
                  "多言語コールセンターをご利用ください。"),
            ],
        ],
    }


def form_pl() -> dict[str, Any]:
    """Wniosek o rejestrację pojazdu, 3 pages A4."""
    fees, fee_checks, fee_total = fee_table("oplaty", [
        ("1", "Dowód rejestracyjny", 1, 5400),
        ("2", "Tablice rejestracyjne samochodowe (komplet)", 1, 8000),
        ("3", "Nalepka kontrolna", 1, 1850),
        ("4", "Pozwolenie czasowe", 1, 1350),
        ("5", "Opłata ewidencyjna (CEPiK)", 4, 50),
        ("6", "Opłata skarbowa od pełnomocnictwa", 1, 1700),
    ], "pl", ["Lp.", "Rodzaj opłaty", "Liczba", "Stawka", "Kwota"], "Razem do zapłaty",
        caption="Tabela 1. Opłaty związane z rejestracją pojazdu")
    total = money(fee_total, "pl")
    return {
        "template": "government_form", "page_size": "A4", "languages": ["pl-PL"],
        "metadata": {"title": "Wniosek o rejestrację pojazdu – Zofia Wiśniewska-Kowalczyk", "author": "Starostwo Powiatowe w Różanach, Wydział Komunikacji",
                     "subject": "Rejestracja pojazdu sprowadzonego z Niemiec", "keywords": ["rejestracja pojazdu", "wniosek", "wydział komunikacji", "Różany"],
                     "lang": "pl-PL", "created": "2026-05-12T07:48:00Z"},
        "theme": {"accent": "#a3222b", "rl_size": 10.2},
        "running_header": "Starostwo Powiatowe w Różanach · Wydział Komunikacji i Transportu",
        "running_footer": "Strona {page} z {pages} · Wniosek nr KT.5410.1.2318.2026",
        "arithmetic": fee_checks,
        "pages": [
            [
                group([P("Starostwo Powiatowe w Różanach", "brand"),
                       P("Wydział Komunikacji i Transportu\nul. Kościuszki 14, 62-418 Różany\ntel. 63 555 41 20 · komunikacja@rozany-powiat.example", "small right")], "letterhead"),
                H(1, "Wniosek o rejestrację pojazdu"),
                P("Wniosek składa właściciel pojazdu lub jego pełnomocnik w terminie 30 dni od dnia nabycia pojazdu albo jego "
                  "sprowadzenia na terytorium Rzeczypospolitej Polskiej. Prosimy wypełnić formularz drukowanymi literami, a pola "
                  "wyboru zaznaczyć znakiem „X”."),
                box("callout", "Przekroczenie 30-dniowego terminu na rejestrację grozi karą administracyjną w wysokości od 200 zł "
                    "do 1000 zł. Wizytę w wydziale można zarezerwować przez internet.", title="Ważne", cls="warn"),
                form("Część A – Dane właściciela", [
                    [field("nazwisko", "Nazwisko *", "Wiśniewska-Kowalczyk", width=1.4), field("imie", "Imię *", "Zofia", width=1),
                     field("pesel", "PESEL *", "85071203458", field_type="comb", max_len=11, width=1.8)],
                    [field("ulica", "Ulica, nr domu, nr lokalu *", "ul. Łąkowa 7 m. 12", width=1.6),
                     field("kod", "Kod pocztowy *", "62-418", field_type="comb", max_len=6, width=1),
                     field("miejscowosc", "Miejscowość *", "Różany", width=1)],
                    [field("telefon", "Telefon", "+48 605 555 284", width=1), field("email", "E-mail", "z.wisniewska@poczta.example", width=1.5),
                     field("wspolwlasciciel", "Pojazd ma współwłaściciela", False, field_type="checkbox", width=1)],
                ]),
                form("Część B – Rodzaj sprawy", [
                    [field("rej_sprowadzony", "Rejestracja pojazdu sprowadzonego z UE", True, field_type="checkbox", width=1),
                     field("rej_nowy", "Rejestracja pojazdu nowego", False, field_type="checkbox", width=1)],
                    [field("tablice_indyw", "Tablice indywidualne", False, field_type="checkbox", width=1),
                     field("zatrzymanie_tablic", "Zachowanie dotychczasowych tablic", False, field_type="checkbox", width=1)],
                ]),
                P("Pojazd sprowadzony z innego państwa członkowskiego Unii Europejskiej wymaga przed rejestracją badania technicznego "
                  "w okręgowej stacji kontroli pojazdów oraz zapłaty akcyzy w urzędzie skarbowym. Wydział nie przyjmie wniosku bez "
                  "oryginałów dokumentów zagranicznych – zostaną one zatrzymane i odesłane do organu, który je wydał."),
            ],
            [
                form("Część C – Dane pojazdu", [
                    [field("marka", "Marka *", "Škoda", width=1),
                     field("model", "Model / wersja *", "Octavia Combi 2.0 TDI", width=1.4), field("rok", "Rok produkcji *", "2021", width=0.7)],
                    [field("vin", "Numer identyfikacyjny VIN *", "TMBJR7NX3MY041829", field_type="comb", max_len=17, width=3)],
                    [field("rodzaj", "Rodzaj pojazdu *", "samochód osobowy", field_type="choice", options=["samochód osobowy", "autobus", "motocykl", "motorower", "przyczepa"], width=1.2),
                     field("paliwo", "Rodzaj paliwa", "olej napędowy", width=1), field("pojemnosc", "Pojemność silnika (cm³)", "1968", width=1)],
                    [field("tablice_dotych", "Dotychczasowy numer rejestracyjny", "FR-DK 4471 (Niemcy)", width=1.4),
                     field("data_nabycia", "Data nabycia *", "28.04.2026", width=1), field("przebieg", "Przebieg (km)", "68 412", width=0.8)],
                ]),
                P("Do wniosku należy dołączyć: dowód własności pojazdu (umowę kupna lub fakturę) wraz z tłumaczeniem przysięgłym, "
                  "zagraniczny dowód rejestracyjny (Zulassungsbescheinigung Teil I i Teil II), zaświadczenie o pozytywnym wyniku "
                  "badania technicznego, dowód zapłaty akcyzy oraz dowody uiszczenia opłat wymienionych w tabeli poniżej."),
                fees,
                P(f"Łączna kwota opłat wynosi **{total}**. Opłaty można uiścić kartą płatniczą w kasie wydziału albo przelewem na "
                  "rachunek Starostwa: 41 1020 4795 0000 9102 0055 6677, tytułem „rejestracja – PESEL 85071203458”."),
                box("footnote", "¹ Opłatę skarbową od pełnomocnictwa (17 zł) uiszcza się tylko wtedy, gdy wniosek składa pełnomocnik."),
            ],
            [
                form("Część D – Pełnomocnik i odbiór dokumentów", [
                    [field("pelnomocnik", "Imię i nazwisko pełnomocnika", "Tomasz Kowalczyk", width=1.4),
                     field("odbior", "Sposób odbioru dowodu *", "osobiście w wydziale", width=1.2)],
                    [field("powiadomienie_sms", "Proszę o powiadomienie SMS o gotowym dowodzie", True, field_type="checkbox", width=1)],
                ]),
                H(2, "Część E – Oświadczenia"),
                L(["Oświadczam, że dane zawarte we wniosku są zgodne ze stanem faktycznym.",
                   "Oświadczam, że jestem świadoma odpowiedzialności karnej za złożenie fałszywego oświadczenia (art. 233 § 6 Kodeksu karnego).",
                   "Przyjmuję do wiadomości, że pozwolenie czasowe jest ważne 30 dni."], ordered=True),
                form("", [
                    [field("osw_prawda", "Potwierdzam powyższe oświadczenia.", True, field_type="checkbox", width=1)],
                    [field("miejsce_data", "Miejscowość i data *", "Różany, 12.05.2026", width=1),
                     field("podpis", "Imię i nazwisko wnioskodawcy *", "Zofia Wiśniewska-Kowalczyk", width=1.4)],
                ]),
                H(2, "Klauzula informacyjna (RODO)"),
                P("Administratorem danych osobowych jest Starosta Różański z siedzibą przy ul. Kościuszki 14 w Różanach. Dane są "
                  "przetwarzane w celu rejestracji pojazdu na podstawie art. 6 ust. 1 lit. c RODO w związku z ustawą – Prawo o ruchu "
                  "drogowym i przechowywane przez okres wynikający z przepisów o archiwizacji. Przysługuje Pani/Panu prawo dostępu do "
                  "danych, ich sprostowania oraz wniesienia skargi do Prezesa Urzędu Ochrony Danych Osobowych."),
                P("Kontakt z inspektorem ochrony danych: iod@rozany-powiat.example."),
                table("adnotacje", [["Przyjęto", "Sprawdzono", "Nr rejestracyjny", "Pozwolenie czasowe"],
                                    ["12.05.2026 – A. Mazur", "12.05.2026 – K. Nowak", "PRZ 48K7T", "ważne do 11.06.2026"]],
                      caption="Adnotacje urzędowe", widths=[25, 25, 22, 28]),
                box("sidebar", "Wydział Komunikacji przyjmuje interesantów od poniedziałku do piątku w godz. 7:30–15:30, we wtorki do 17:00. "
                    "Stan sprawy można sprawdzić w serwisie [pojazd.rozany-powiat.example](https://pojazd.rozany-powiat.example) po podaniu "
                    "numeru VIN.", title="Godziny obsługi"),
            ],
        ],
    }



# ================================================================ legal contracts


def contract_en() -> dict[str, Any]:
    """Master services agreement (LibreOffice, untagged, 10 pages)."""
    usd = "en-US"
    rows, total = [], 0
    impl = [("Implementation milestone 1 — signing of this Agreement", date(2026, 6, 15), 4650000),
            ("Implementation milestone 2 — approval of the Solution Design", date(2026, 7, 31), 4650000),
            ("Implementation milestone 3 — completion of user acceptance testing", date(2026, 9, 30), 5580000),
            ("Implementation milestone 4 — Go-Live of the Yokohama and Osaka sites", date(2026, 11, 2), 3720000)]
    number_ = 0
    for text, due, cents in impl:
        number_ += 1
        rows.append([str(number_), text, day(due, "en_short"), money(cents, usd)])
        total += cents
    for index in range(14):
        month = 11 + index
        year, month = 2026 + (month - 1) // 12, (month - 1) % 12 + 1
        cents = 1475000 if year == 2026 or month < 4 else 1534000
        number_ += 1
        label = date(year, month, 1).strftime("%B %Y")
        rows.append([str(number_), f"Subscription fee, {label} (Platform, 40 named users)", day(date(year, month, 1), "en_short"), money(cents, usd)])
        total += cents
    schedule = continued("payment", [["No.", "Payment event", "Due date", "Amount (USD)"]], rows, [15, 3],
                         caption="Table 1 — Payment schedule", continued_caption="Table 1 — Payment schedule (continued)",
                         align=["r", "l", "l", "r"], widths=[7, 59, 16, 18], total=[["", "Total contract value (initial term)", "", money(total, usd)]])
    sla = table("sla", [["Service level", "Target", "Measurement", "Service credit"],
                        ["Platform availability", "99.7% per month", "Synthetic checks every 60 s", "5% of monthly fee per 0.1% below target"],
                        ["Severity 1 response", "30 minutes, 24 × 7", "Ticket timestamp", "2% per hour of delay"],
                        ["Severity 2 response", "4 business hours", "Ticket timestamp", "1% per business day of delay"],
                        ["Route-plan generation", "≤ 90 s for 5,000 stops", "Monthly 95th percentile", "3% of monthly fee"],
                        ["Data export on request", "5 business days", "Written confirmation", "None (remedy under § 13.6)"]],
                caption="Table 2 — Service levels and credits", widths=[24, 20, 24, 32])
    notices = table("notices", [["Party", "Address for notices", "Attention", "Email"],
                                ["Provider", "1800 Wynkoop Street, Suite 600, Denver, CO 80202, USA", "General Counsel", "legal@brightwater.example"],
                                ["Customer", "〒220-0012 横浜市西区みなとみらい4-6-2, Japan", "法務部 (Legal Department)", "legal@kosei-logi.example"]],
                    caption="Table 3 — Notice details", widths=[12, 46, 20, 22])
    return {
        "template": "legal_contract", "page_size": "Letter", "languages": ["en-US", "ja"], "tagged": False,
        "metadata": {"title": "Master Services Agreement BWA-MSA-2026-014 — Brightwater Analytics and Kōsei Logistics",
                     "author": "Brightwater Analytics, Inc. Legal Department", "subject": "Route optimization platform subscription and implementation services",
                     "keywords": ["master services agreement", "SaaS", "service levels", "Kōsei Logistics"], "lang": "en-US",
                     "created": "2026-06-11T18:20:00Z"},
        "theme": {"accent": "#1f3a5f", "lo_size": "10pt", "lo_font": "Noto Serif"},
        "running_header": "Master Services Agreement No. BWA-MSA-2026-014 — Page {page} of {pages}",
        "running_footer": "Confidential — Brightwater Analytics, Inc. / Kōsei Logistics Co., Ltd.",
        "arithmetic": [{"kind": "column_sum", "table": "payment", "columns": [3], "label_column": 1, "total_label": "Total contract value (initial term)"}],
        "pages": [
            [
                H(1, "Master Services Agreement"),
                P("Agreement No. BWA-MSA-2026-014 · Effective Date: June 15, 2026", "meta"),
                P("This Master Services Agreement (the “**Agreement**”) is entered into as of the Effective Date by and between the following parties:"),
                pair(P("**Brightwater Analytics, Inc.**, a Delaware corporation with its principal office at 1800 Wynkoop Street, Suite 600, "
                       "Denver, Colorado 80202, USA (the “**Provider**”), represented by Megan O’Rourke, Chief Revenue Officer;"),
                     P("**Kōsei Logistics Co., Ltd.** (株式会社光誠ロジスティクス), a company organized under the laws of Japan with its registered "
                       "office at 4-6-2 Minatomirai, Nishi-ku, Yokohama 220-0012, Japan (the “**Customer**”), represented by Takeshi Morimoto (森本 武), "
                       "Representative Director.")),
                P("The Provider and the Customer are each referred to as a “**Party**” and together as the “**Parties**”."),
                H(2, "Recitals"),
                P("A. The Provider develops and operates RouteWise, a cloud platform for vehicle route planning, dock scheduling and delivery "
                  "tracking, and provides related implementation, integration and support services."),
                P("B. The Customer operates regional distribution centers in Yokohama, Osaka and Fukuoka and a fleet of approximately "
                  "640 contracted delivery vehicles, and wishes to replace its existing route planning software."),
                P("C. Following a competitive tender (reference KL-RFP-2026-03) and a four-week pilot at the Yokohama site, the Customer "
                  "selected the Provider to implement and operate the platform for its domestic network."),
                P("D. The Parties wish to set out the terms on which the Provider will deliver the platform and the services, including "
                  "service levels, fees, data protection obligations and the allocation of risk between them."),
                P("NOW, THEREFORE, in consideration of the mutual covenants contained in this Agreement, and for other good and valuable "
                  "consideration, the receipt and sufficiency of which are acknowledged, the Parties agree as follows."),
                H(3, "Contents"),
                P("1. Definitions · 2. Term · 3. Services · 4. Fees and Payment · 5. Payment Schedule · 6. Service Levels · 7. Confidentiality · "
                  "8. Data Protection · 9. Intellectual Property · 10. Warranties · 11. Limitation of Liability · 12. Indemnification · "
                  "13. Termination · 14. Governing Law and Disputes · 15. General Provisions · Signatures · Exhibits A–C", "small"),
            ],
            [
                ordered([
                    item("**Definitions.** Capitalized terms have the meanings given below.", [
                        "“**Affiliate**” means any entity that controls, is controlled by or is under common control with a Party, where control means ownership of more than 50% of the voting interests.",
                        "“**Customer Data**” means all data, including shipment, address and driver information, submitted to the Platform by or for the Customer.",
                        "“**Go-Live**” means the first business day on which the Platform is used to plan live delivery routes at a Site.",
                        "“**Platform**” means the RouteWise software-as-a-service offering, including its application programming interfaces and mobile driver application.",
                        "“**Services**” means the subscription to the Platform, the Implementation Services and the Support Services described in Exhibit A.",
                        "“**Site**” means each distribution center listed in Exhibit B.",
                    ]),
                    item("**Term.** This Agreement starts on the Effective Date and continues for an initial term ending on December 31, 2027 (the “**Initial Term**”).", [
                        "Thereafter it renews automatically for successive periods of twelve months unless either Party gives at least ninety (90) days’ written notice of non-renewal.",
                    ]),
                    item("**Services.** The Provider shall provide the Services in accordance with this Agreement and the statements of work agreed under it.", [
                        "The Provider shall perform the Implementation Services according to the project plan in Exhibit A, including:",
                        item("Implementation deliverables:", [
                            "configuration of the Platform for each Site, including vehicle types, depot hours and delivery time windows;",
                            "integration with the Customer’s warehouse management system (WMS) and the Japan Post address master;",
                            "migration of twelve months of historical route data; and",
                            "training of up to 60 dispatchers and 12 administrators in Japanese.",
                        ]),
                    ]),
                    item("**Fees and Payment.** The Customer shall pay the fees set out in Section 5 and Exhibit C.", [
                        item("Invoicing:", [
                            "implementation fees are invoiced on achievement of each milestone;",
                            "subscription fees are invoiced monthly in advance.",
                        ]),
                        "Invoices are payable within thirty (30) days of receipt by wire transfer in United States dollars.",
                        "Fees are exclusive of taxes. Where Japanese consumption tax or withholding tax applies, the Parties shall cooperate to apply the United States–Japan tax treaty.¹",
                    ]),
                ]),
                box("footnote", "¹ U.S.–Japan income tax convention of November 6, 2003, as amended in 2013."),
            ],
            [
                H(2, "5. Payment Schedule"),
                P("**5.1** The fees payable during the Initial Term are set out in Table 1. Subscription fees for 2027 include the annual "
                  "adjustment of 4.0% agreed in Exhibit C, applied from April 1, 2027."),
                P("**5.2** If a milestone is delayed for reasons attributable solely to the Customer for more than thirty (30) days, the "
                  "Provider may invoice the milestone payment as if the milestone had been achieved."),
                *schedule[:1],
            ],
            [
                *schedule[1:],
                P("**5.3** Subscription fees cover 40 named dispatcher users and unlimited driver devices. Additional named users are "
                  "charged at USD 310.00 per user per month, prorated daily."),
                H(2, "6. Service Levels"),
                P("**6.1** From Go-Live at the first Site, the Provider shall meet the service levels in Table 2. Service levels are "
                  "measured monthly and reported to the Customer within ten (10) business days after the end of each month."),
                sla,
                P("**6.2** Service credits are the Customer’s sole monetary remedy for a failure to meet a service level, but do not "
                  "limit the Customer’s right to terminate under Section 13.3. Total service credits in any month shall not exceed 20% of "
                  "the subscription fee for that month."),
                P("**6.3** Scheduled maintenance announced at least five (5) days in advance and performed between 01:00 and 05:00 "
                  "Japan Standard Time on Sundays is excluded from availability calculations."),
            ],
            [
                H(2, "7. Confidentiality"),
                P("**7.1** “Confidential Information” means all non-public information disclosed by one Party to the other that is "
                  "marked as confidential or that a reasonable person would understand to be confidential, including the terms of "
                  "this Agreement, pricing, product roadmaps, customer lists and Customer Data."),
                P("**7.2** The receiving Party shall (a) use Confidential Information only to perform or receive the Services, (b) not "
                  "disclose it to any third party except its employees, Affiliates and professional advisers who need to know it and are "
                  "bound by obligations at least as protective as this Section, and (c) protect it with at least the same degree of "
                  "care it uses for its own confidential information, and in no event less than reasonable care."),
                P("**7.3** These obligations do not apply to information that is or becomes public through no fault of the receiving "
                  "Party, was lawfully known to it before disclosure, is independently developed without use of the disclosing "
                  "Party’s information, or is required to be disclosed by law, provided that the receiving Party gives prompt notice "
                  "where legally permitted."),
                P("**7.4** The obligations in this Section survive for five (5) years after termination of this Agreement, and "
                  "indefinitely for trade secrets and Customer Data."),
                H(2, "8. Data Protection"),
                P("**8.1** The Customer is the controller and the Provider is the processor of personal data contained in Customer "
                  "Data, including driver names, mobile numbers and consignee addresses. The Parties shall comply with the Act on the "
                  "Protection of Personal Information of Japan (APPI) and with the data processing addendum attached as Exhibit D."),
                P("**8.2** The Provider shall host Customer Data in data centers located in Tokyo and Osaka. Remote access from the "
                  "United States is limited to named support engineers, logged and reviewed monthly."),
                P("**8.3** The Provider shall notify the Customer without undue delay, and in any case within forty-eight (48) hours, "
                  "after becoming aware of a personal data breach affecting Customer Data, and shall provide the information the "
                  "Customer reasonably requires to report the breach to the Personal Information Protection Commission."),
                P("**8.4** On termination, the Provider shall return Customer Data in CSV and JSON formats and then delete it within "
                  "sixty (60) days, except copies retained in backups that are overwritten in the ordinary course within ninety (90) days."),
            ],
            [
                H(2, "9. Intellectual Property"),
                P("**9.1** The Provider retains all rights in the Platform, its documentation and any improvements, including those "
                  "suggested by the Customer. No rights are granted except as expressly stated in this Agreement."),
                P("**9.2** The Customer retains all rights in Customer Data. The Customer grants the Provider a non-exclusive license to "
                  "use Customer Data solely to provide the Services and, in aggregated and de-identified form, to improve the "
                  "Platform’s routing models."),
                P("**9.3** Integration code written specifically for the Customer’s WMS (the “**Custom Connectors**”) is licensed to the "
                  "Customer on a perpetual, royalty-free basis for its internal business purposes."),
                H(2, "10. Warranties"),
                P("**10.1** Each Party warrants that it has full power and authority to enter into and perform this Agreement."),
                P("**10.2** The Provider warrants that (a) the Services will be performed in a professional and workmanlike manner by "
                  "suitably qualified personnel, (b) the Platform will perform materially in accordance with its documentation, and "
                  "(c) it will not knowingly introduce malicious code into the Platform."),
                P("**10.3** If the Platform does not conform to the warranty in Section 10.2(b), the Provider shall, at its option and "
                  "expense, correct the non-conformity within thirty (30) days or refund the subscription fees paid for the period of "
                  "non-conformity."),
                P("**10.4** EXCEPT AS EXPRESSLY STATED IN THIS AGREEMENT, NEITHER PARTY MAKES ANY OTHER WARRANTY, EXPRESS OR IMPLIED, "
                  "INCLUDING ANY WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE OR NON-INFRINGEMENT."),
                box("callout", "Route plans produced by the Platform are recommendations. The Customer remains responsible for "
                    "compliance with road traffic laws, driver working-hour limits under the Labor Standards Act and the safe loading "
                    "of vehicles.", title="Operational responsibility", cls="note"),
            ],
            [
                H(2, "11. Limitation of Liability"),
                P("**11.1** NEITHER PARTY SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL OR PUNITIVE DAMAGES, OR "
                  "FOR LOSS OF PROFITS, REVENUE OR GOODWILL, ARISING OUT OF OR RELATING TO THIS AGREEMENT, EVEN IF ADVISED OF THEIR POSSIBILITY."),
                P("**11.2** EACH PARTY’S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATING TO THIS AGREEMENT SHALL NOT EXCEED THE FEES "
                  "PAID AND PAYABLE BY THE CUSTOMER IN THE TWELVE (12) MONTHS PRECEDING THE EVENT GIVING RISE TO THE CLAIM."),
                P("**11.3** The limitations in Sections 11.1 and 11.2 do not apply to (a) a Party’s indemnification obligations, (b) "
                  "breach of Section 7 (Confidentiality) or Section 8 (Data Protection), for which the cap is three times the amount in "
                  "Section 11.2, (c) the Customer’s obligation to pay fees, or (d) liability for gross negligence, willful misconduct "
                  "or fraud."),
                H(2, "12. Indemnification"),
                P("**12.1** The Provider shall defend the Customer against any third-party claim alleging that the Platform infringes a "
                  "patent, copyright or trademark, or misappropriates a trade secret, and shall pay the damages and costs finally "
                  "awarded or agreed in settlement."),
                P("**12.2** If the Platform becomes, or in the Provider’s opinion is likely to become, the subject of such a claim, the "
                  "Provider may (a) procure the right for the Customer to continue using it, (b) modify it to be non-infringing without "
                  "material loss of functionality, or (c) if neither is commercially reasonable, terminate the affected Services and "
                  "refund prepaid fees for the remaining period."),
                P("**12.3** The Customer shall defend the Provider against third-party claims arising from Customer Data or from the "
                  "Customer’s use of the Platform in breach of this Agreement."),
                P("**12.4** The indemnified Party shall give prompt written notice of the claim, allow the indemnifying Party sole control "
                  "of the defense and settlement, and provide reasonable assistance at the indemnifying Party’s expense. No settlement "
                  "that admits fault on behalf of the indemnified Party may be made without its prior written consent."),
            ],
            [
                H(2, "13. Termination"),
                P("**13.1** Either Party may terminate this Agreement by written notice if the other Party materially breaches it and "
                  "fails to cure the breach within thirty (30) days after receiving notice describing the breach in reasonable detail."),
                P("**13.2** Either Party may terminate immediately by written notice if the other Party becomes insolvent, makes a "
                  "general assignment for the benefit of creditors, or becomes the subject of bankruptcy, civil rehabilitation or "
                  "corporate reorganization proceedings."),
                P("**13.3** The Customer may terminate the subscription by written notice if platform availability falls below 99.0% "
                  "in any two consecutive months or in any three months during a rolling twelve-month period."),
                P("**13.4** The Customer may terminate for convenience after December 31, 2026 on one hundred and twenty (120) days’ "
                  "notice, subject to payment of an early termination fee equal to three (3) months of subscription fees."),
                P("**13.5** On termination, all unpaid fees for Services performed up to the termination date become due, and each Party "
                  "shall return or destroy the other Party’s Confidential Information."),
                P("**13.6** For up to ninety (90) days after termination, the Provider shall provide reasonable transition assistance at "
                  "the time-and-materials rates in Exhibit C, including the export of Customer Data in the formats described in Section 8.4."),
                H(2, "14. Governing Law and Disputes"),
                P("**14.1** This Agreement is governed by the laws of the State of New York, without regard to its conflict-of-laws rules. "
                  "The United Nations Convention on Contracts for the International Sale of Goods does not apply."),
                P("**14.2** The Parties shall first attempt to resolve any dispute through good-faith negotiations between their senior "
                  "executives for at least thirty (30) days."),
                P("**14.3** Any dispute not so resolved shall be finally settled by arbitration administered by the Japan Commercial "
                  "Arbitration Association under its Commercial Arbitration Rules by three arbitrators. The seat of arbitration is Tokyo "
                  "and the language is English. Judgment on the award may be entered in any court having jurisdiction.²"),
            ],
            [
                H(2, "15. General Provisions"),
                P("**15.1 Notices.** Notices must be in writing and delivered by hand, by international courier or by email with "
                  "confirmation of receipt to the addresses in Table 3, or to another address notified in accordance with this Section."),
                notices,
                P("**15.2 Assignment.** Neither Party may assign this Agreement without the other Party’s prior written consent, except to "
                  "an Affiliate or to a successor in a merger or sale of substantially all of its assets, on written notice."),
                P("**15.3 Subcontracting.** The Provider may use subcontractors, including its Japanese implementation partner Nishikaze "
                  "Systems K.K., and remains responsible for their performance."),
                P("**15.4 Force majeure.** Neither Party is liable for delay caused by events beyond its reasonable control, including "
                  "earthquakes, typhoons, pandemics, war or failures of public networks, provided it notifies the other Party promptly "
                  "and uses reasonable efforts to mitigate. Payment obligations are not excused."),
                P("**15.5 Entire agreement.** This Agreement, including its Exhibits, is the entire agreement between the Parties on its "
                  "subject matter and supersedes all prior proposals, including the tender response dated March 27, 2026. In case of "
                  "conflict, the body of this Agreement prevails over the Exhibits."),
                P("**15.6 Language.** This Agreement is made in English. A Japanese translation may be prepared for convenience; the "
                  "English version prevails."),
                P("**15.7 Counterparts.** This Agreement may be signed in counterparts and by electronic signature, each of which is "
                  "an original and which together form one instrument."),
            ],
            [
                H(2, "Signatures"),
                P("IN WITNESS WHEREOF, the Parties have caused this Agreement to be executed by their duly authorized representatives "
                  "as of the Effective Date."),
                pair(P("**BRIGHTWATER ANALYTICS, INC.**\n\nBy: ______________________________\nName: Megan O’Rourke\nTitle: Chief Revenue Officer\nDate: June 12, 2026"),
                     P("**KŌSEI LOGISTICS CO., LTD.**\n株式会社光誠ロジスティクス\n\nBy: ______________________________\nName: Takeshi Morimoto (森本 武)\nTitle: Representative Director\nDate: June 15, 2026")),
                H(2, "Exhibits"),
                L(["Exhibit A — Statement of Work: Implementation and Support Services",
                   "Exhibit B — Sites: Yokohama DC (Kanagawa), Osaka Nanko DC (Osaka), Fukuoka Hakozaki DC (Fukuoka)",
                   "Exhibit C — Fees, Rate Card and Annual Adjustment",
                   "Exhibit D — Data Processing Addendum"]),
                P("Approved as to form: Brightwater Analytics, Inc. Legal Department (ref. LGL-2026-0388); Kōsei Logistics Co., Ltd. "
                  "Legal Department (法務部、管理番号 KL-HJ-26-112).", "small"),
                box("footnote", "² The Parties confirm that the arbitration agreement in Section 14.3 is a separate agreement and remains "
                    "valid if any other part of this Agreement is held invalid."),
            ],
        ],
    }



def contract_es() -> dict[str, Any]:
    """Contrato de suministro e instalación fotovoltaica (Chromium, 6 pages)."""
    base = 18642000
    hitos = [("Firma del contrato (anticipo)", "15/06/2026", 30), ("Entrega de módulos e inversores en obra", "31/07/2026", 40),
             ("Puesta en marcha y certificado de instalación (CIE)", "30/09/2026", 20), ("Acta de recepción definitiva", "15/12/2026", 10)]
    rows, totals = [], [0, 0, 0]
    for name, when, pct in hitos:
        amount = base * pct // 100
        tax = round(amount * 0.21)
        rows.append([name, when, f"{pct} %", money(amount, "es"), money(tax, "es"), money(amount + tax, "es")])
        totals = [totals[0] + amount, totals[1] + tax, totals[2] + amount + tax]
    rows.append(["Total", "", "100 %", *(money(v, "es") for v in totals)])
    pagos = table("pagos", [["Hito", "Fecha prevista", "%", "Base imponible", "IVA (21 %)", "Total"], *rows],
                  caption="Tabla 1. Calendario de pagos", align=["l", "l", "r", "r", "r", "r"], widths=[34, 14, 7, 15, 14, 16], total_rows=[len(rows)])
    spec = {"title": "Producción mensual estimada (MWh)", "categories": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
            "series": [("Estimación P50", [21.4, 25.8, 34.9, 39.6, 45.2, 47.8, 49.1, 45.0, 37.3, 30.2, 22.9, 19.6]),
                       ("Garantía (P90)", [19.0, 22.9, 31.0, 35.2, 40.2, 42.5, 43.7, 40.0, 33.2, 26.9, 20.4, 17.4])],
            "max": 60, "ticks": 4, "tick_format": lambda v: number(v, "es", 0)}
    return {
        "template": "legal_contract", "page_size": "A4", "languages": ["es-ES"],
        "metadata": {"title": "Contrato de suministro e instalación de planta fotovoltaica de autoconsumo – SCA San Isidro de Lorca",
                     "author": "Solaria Mediterránea Instalaciones, S.L.", "subject": "Planta fotovoltaica de 312 kWp sobre cubierta, Lorca (Murcia)",
                     "keywords": ["contrato", "fotovoltaica", "autoconsumo", "calendario de pagos", "Lorca"], "lang": "es-ES",
                     "created": "2026-06-10T09:30:00Z"},
        "theme": {"accent": "#8c4a12", "font_size": "9.6pt", "body_font": "'Noto Serif'", "heading_font": "'Noto Sans'",
                  "margins": "18mm 18mm 18mm 18mm", "extra_css": legal_css({1: 0, 2: 2, 3: 4, 4: 7, 5: 11, 6: 14})},
        "running_header": "Contrato SM-2026/087 · Suministro e instalación FV · página {page} de {pages}",
        "running_footer": "Solaria Mediterránea Instalaciones, S.L. — SCA San Isidro de Lorca · Rubrica de las partes: ______ / ______",
        "arithmetic": [{"kind": "column_sum", "table": "pagos", "columns": [3, 4, 5], "label_column": 0, "total_label": "Total"},
                       {"kind": "sum", "terms": [["+", money(totals[0], "es")], ["+", money(totals[1], "es")]], "equals": money(totals[2], "es")}],
        "pages": [
            [
                H(1, "Contrato de suministro e instalación de una planta fotovoltaica de autoconsumo"),
                P("Contrato n.º SM-2026/087 · En Lorca (Murcia), a 12 de junio de 2026", "meta"),
                H(2, "Reunidos"),
                pair(P("**De una parte**, D.ª Inmaculada Ferrández Ruiz, con DNI 48\u00a0392\u00a0117-K, en nombre y representación de "
                       "**Solaria Mediterránea Instalaciones, S.L.**, con CIF B-73\u00a0415\u00a0902 y domicilio en Polígono Industrial Oeste, "
                       "calle Uruguay, parcela 12/7, 30820 Alcantarilla (Murcia), en su condición de administradora solidaria "
                       "(en adelante, «el Instalador»)."),
                     P("**De otra parte**, D. Ginés Martínez Navarro, con DNI 23\u00a0261\u00a0540-M, en nombre y representación de la "
                       "**Sociedad Cooperativa Agraria San Isidro de Lorca**, con CIF F-30\u00a0018\u00a0744 y domicilio en Carretera de "
                       "Granada, km 3, 30817 Lorca (Murcia), en su condición de presidente del Consejo Rector (en adelante, «la Cooperativa»).")),
                P("Ambas partes se reconocen mutuamente la capacidad legal necesaria para obligarse en este acto y, a tal efecto,"),
                H(2, "Exponen"),
                P("**I.** Que la Cooperativa es titular de la nave de manipulación y envasado de hortalizas situada en la parcela 41 del "
                  "polígono 9 de Lorca, con una cubierta de chapa tipo sándwich de 4\u00a0150\u00a0m² y un consumo eléctrico anual de "
                  "aproximadamente 610\u00a0MWh, concentrado en las cámaras frigoríficas."),
                P("**II.** Que el Instalador es una empresa habilitada para instalaciones eléctricas de baja tensión (categoría "
                  "especialista, n.º de registro 30/IBTE/2019/0412) con experiencia en plantas fotovoltaicas sobre cubierta."),
                P("**III.** Que, tras el estudio técnico y la oferta n.º OF-26-0331 de 21 de abril de 2026, la Cooperativa desea "
                  "encargar el suministro, la instalación y la puesta en marcha de una planta fotovoltaica de autoconsumo con "
                  "excedentes acogida a compensación, cofinanciada con fondos Next Generation EU."),
                P("Y, en virtud de lo anterior, las partes acuerdan celebrar el presente contrato, que se regirá por las siguientes"),
                H(2, "Cláusulas"),
                classed(ordered([
                    item("**Definiciones.** A efectos de este contrato, los términos siguientes tendrán el significado que se indica:", [
                        "«Planta»: el conjunto de 568 módulos de 550\u00a0Wp, tres inversores de 100\u00a0kW, estructura coplanar, cableado y protecciones descritos en el Anexo I.",
                        "«Puesta en marcha»: la primera conexión de la Planta a la red interior de la Cooperativa tras la verificación del Instalador.",
                        "«Recepción definitiva»: la firma del acta prevista en la cláusula 7, una vez transcurrido el periodo de prueba.",
                    ]),
                    item("**Objeto.** El Instalador se obliga a suministrar, instalar, legalizar y poner en marcha la Planta, con una "
                         "potencia pico de 312,4\u00a0kWp, y la Cooperativa a pagar el precio pactado.", [
                        "El objeto incluye:",
                        item("Prestaciones incluidas:", [
                            "la redacción del proyecto técnico y la dirección de obra por ingeniero colegiado;",
                            "la tramitación de la licencia urbanística, el certificado de instalación y la inscripción en el registro de autoconsumo;",
                            "el sistema de monitorización con acceso web para la Cooperativa durante toda la vida útil de la Planta.",
                        ]),
                    ]),
                ]), "cl"),
            ],
            [
                classed(ordered([
                    item("**Plazo de ejecución.** Las obras comenzarán dentro de los quince días siguientes a la obtención de la licencia.", [
                        "La Puesta en marcha deberá producirse, como máximo, el 30 de septiembre de 2026.",
                        "Por cada semana completa de retraso imputable al Instalador se aplicará una penalización del 0,5\u00a0% del precio, con el límite del 10\u00a0%.",
                    ]),
                    item("**Precio y forma de pago.** El precio total es de 186\u00a0420,00\u00a0€ más IVA, cerrado y a tanto alzado.", [
                        item("El precio incluye:", [
                            "todos los materiales, transporte, medios de elevación y gestión de residuos;",
                            "las tasas e impuestos municipales (ICIO) vinculados a la licencia;",
                            "la formación de dos operarios de mantenimiento de la Cooperativa.",
                        ]),
                        "El pago se realizará conforme al calendario de la Tabla 1, mediante transferencia a 30 días desde la fecha de la factura.",
                        "La Cooperativa podrá retener el último pago hasta la subsanación de los defectos señalados en el acta de recepción.¹",
                    ]),
                ]), "cl"),
                pagos,
                P(f"El importe total del contrato, IVA incluido, asciende a **{money(totals[2], 'es')}** "
                  f"({money(totals[0], 'es')} de base imponible y {money(totals[1], 'es')} de IVA). Las facturas se emitirán a nombre de "
                  "la Cooperativa e indicarán la referencia del expediente de ayuda NG-MUR-AUT-2026-0193."),
                box("footnote", "¹ La retención no podrá superar el importe del hito 4 ni prolongarse más de sesenta días."),
            ],
            [
                classed(ordered([
                    item("**Garantías.** El Instalador garantiza la Planta frente a defectos de material y de montaje.", [
                        item("Plazos de garantía:", [
                            "módulos: 12 años de producto y 30 años de rendimiento lineal (mínimo 87,4\u00a0% en el año 30);",
                            "inversores: 10 años, con sustitución en un plazo máximo de 72 horas;",
                            "instalación y estanqueidad de la cubierta: 5 años desde la Recepción definitiva.",
                        ]),
                    ]),
                    item("**Producción garantizada.** El Instalador garantiza durante los tres primeros años una producción anual "
                         "mínima de 382\u00a0MWh (escenario P90), medida en el contador de generación.", [
                        "Si la producción real, corregida por irradiación, fuera inferior, el Instalador abonará la diferencia a 0,11\u00a0€/kWh.",
                    ]),
                    item("**Recepción.** Tras un periodo de prueba de sesenta días desde la Puesta en marcha, las partes firmarán el acta de Recepción definitiva.", [
                        "Los defectos menores se harán constar en el acta y se subsanarán en un plazo de treinta días.",
                    ]),
                ]), "cl"),
                chart("f1", "bar", spec, "Figura 1. Producción mensual estimada y garantizada de la Planta (Anexo II)", raster=False, width="88%", size=(560, 240)),
                chart_table("c1", "Mes", spec, lambda v: number(v, "es", 1)),
                photo("p1", ["solar-panels"], ["energy"], {"solar-panels": "Instalación de referencia del Instalador: 280 kWp sobre la nave de una almazara en Totana (2025)."},
                      "Instalación de referencia del Instalador", wrap="right", width="38%"),
                P("La estimación de producción se basa en datos de irradiación de PVGIS-SARAH3 para Lorca, con una inclinación de 6° "
                  "(coplanar a la cubierta) y una orientación de −12° respecto al sur. Las pérdidas del sistema se han estimado en un 13,8\u00a0%."),
            ],
            [
                classed(ordered([
                    item("**Obligaciones de la Cooperativa.** La Cooperativa deberá:", [
                        "facilitar el acceso a la cubierta y a los cuadros eléctricos en horario de 7:00 a 19:00, de lunes a sábado;",
                        "aportar el certificado de solidez estructural de la cubierta emitido por técnico competente;",
                        "designar un interlocutor único para la obra, que será D. Pedro Cánovas Sánchez, jefe de mantenimiento.",
                    ]),
                    item("**Seguridad y salud.** El Instalador cumplirá el Real Decreto 1627/1997 y aportará el plan de seguridad antes del inicio.", [
                        "Los trabajos en cubierta se realizarán con línea de vida y redes de protección certificadas.",
                        "La Cooperativa informará de los riesgos propios de su actividad, en particular del tránsito de carretillas.",
                    ]),
                    item("**Responsabilidad y seguros.** El Instalador responderá de los daños que cause a la Cooperativa o a terceros durante la ejecución.", [
                        item("El Instalador mantendrá en vigor:", [
                            "un seguro de responsabilidad civil general con un límite mínimo de 1\u00a0500\u00a0000\u00a0€ por siniestro;",
                            "un seguro a todo riesgo de construcción por el valor de la Planta hasta la Recepción definitiva.",
                        ]),
                        "La responsabilidad total del Instalador por este contrato no excederá del precio, salvo dolo o culpa grave.",
                    ]),
                    item("**Resolución.** Serán causas de resolución del contrato:", [
                        "el incumplimiento grave de cualquiera de las partes no subsanado en un plazo de treinta días desde el requerimiento;",
                        "el retraso de la Puesta en marcha superior a doce semanas por causa imputable al Instalador;",
                        "la denegación definitiva de la licencia, en cuyo caso se abonarán únicamente los trabajos realizados.",
                    ]),
                ]), "cl"),
                box("callout", "Si la ayuda Next Generation EU fuera revocada por causa imputable al Instalador (en particular, por no "
                    "justificar el origen de los equipos o el cumplimiento del principio DNSH), este reembolsará a la Cooperativa el "
                    "importe de la ayuda perdida.", title="Ayudas públicas", cls="warn"),
            ],
            [
                classed(ordered([
                    item("**Mantenimiento.** Durante los dos primeros años desde la Recepción definitiva, el Instalador prestará sin coste "
                         "adicional el mantenimiento preventivo descrito en la Tabla 2.", [
                        "El mantenimiento correctivo de defectos cubiertos por la garantía no se facturará en ningún caso.",
                        item("Tiempos de respuesta ante avisos:", [
                            "parada total de la Planta o de un inversor: presencia en planta en 24 horas;",
                            "pérdida de comunicación del sistema de monitorización: resolución remota en 48 horas;",
                            "otras incidencias: visita programada en el plazo de siete días.",
                        ]),
                        "A partir del tercer año, la Cooperativa podrá contratar el mantenimiento con el Instalador por 3.950,00\u00a0€ anuales más IVA, revisables según el IPC.",
                    ]),
                    item("**Subcontratación.** El Instalador podrá subcontratar el montaje de la estructura y la limpieza de módulos, previa comunicación por escrito.", [
                        "El Instalador responderá frente a la Cooperativa de la actuación de sus subcontratistas como si fuera propia.",
                        "Los subcontratistas deberán estar inscritos en el Registro de Empresas Acreditadas (REA).",
                    ]),
                    item("**Fuerza mayor.** Ninguna parte responderá del retraso causado por hechos imprevisibles o inevitables.", [
                        "Se consideran tales, entre otros, las DANA o episodios de lluvias torrenciales declarados por la AEMET, las huelgas generales y el retraso en la conexión imputable a la distribuidora.",
                        "La parte afectada lo notificará en un plazo de cinco días y los plazos se prorrogarán por el tiempo de duración del impedimento.",
                    ]),
                ]), "cl"),
                table("mantenimiento", [["Operación", "Frecuencia", "Responsable", "Registro"],
                                        ["Inspección visual de módulos, estructura y cableado", "Semestral", "Instalador", "Informe con fotografías"],
                                        ["Limpieza de módulos con agua desmineralizada", "Semestral (marzo y septiembre)", "Instalador", "Parte de trabajo"],
                                        ["Termografía de módulos y cuadros eléctricos", "Anual", "Instalador", "Informe termográfico"],
                                        ["Revisión de inversores y actualización de firmware", "Anual", "Instalador / fabricante", "Hoja de servicio"],
                                        ["Comprobación de protecciones y puesta a tierra", "Anual", "Instalador", "Certificado de medidas"],
                                        ["Lectura de producción y comparación con la garantía P90", "Mensual", "Cooperativa", "Monitorización web"]],
                      caption="Tabla 2. Plan de mantenimiento preventivo (años 1 y 2)", widths=[44, 20, 18, 18]),
                P("El Instalador remitirá a la Cooperativa, dentro del mes siguiente a cada semestre, un informe de explotación con la "
                  "producción, la disponibilidad de los inversores, las incidencias atendidas y las recomendaciones de mejora."),
            ],
            [
                classed(ordered([
                    item("**Protección de datos.** Cada parte tratará los datos de contacto de los representantes de la otra con la "
                         "única finalidad de gestionar este contrato, conforme al Reglamento (UE) 2016/679 y a la Ley Orgánica 3/2018.", [
                        "Los datos de monitorización de la Planta pertenecen a la Cooperativa y el Instalador solo podrá usarlos para el mantenimiento.",
                    ]),
                    item("**Confidencialidad.** Las partes mantendrán reservados los términos económicos de este contrato y la información técnica intercambiada.", [
                        "La obligación subsistirá durante los tres años siguientes a la terminación del contrato.",
                    ]),
                    item("**Notificaciones.** Las comunicaciones se realizarán por escrito a las direcciones indicadas en el encabezamiento o por correo electrónico.", [
                        "Instalador: contratos@solariamediterranea.example; Cooperativa: gerencia@sanisidrolorca.example.",
                    ]),
                    item("**Ley aplicable y jurisdicción.** Este contrato se rige por la legislación española.", [
                        "Para cualquier controversia, las partes se someten a los Juzgados y Tribunales de Lorca, con renuncia a cualquier otro fuero.",
                    ]),
                ]), "cl"),
                H(2, "Anexos"),
                L(["Anexo I – Memoria técnica y presupuesto desglosado (oferta OF-26-0331)",
                   "Anexo II – Estudio de producción y garantía P90",
                   "Anexo III – Plan de seguridad y salud",
                   "Anexo IV – Pólizas de seguro del Instalador"]),
                P("Y, en prueba de conformidad, las partes firman el presente contrato por duplicado y a un solo efecto en el lugar y la fecha indicados en el encabezamiento."),
                pair(P("**Por el Instalador**\nSolaria Mediterránea Instalaciones, S.L.\n\n\n______________________________\nD.ª Inmaculada Ferrández Ruiz\nAdministradora solidaria"),
                     P("**Por la Cooperativa**\nSCA San Isidro de Lorca\n\n\n______________________________\nD. Ginés Martínez Navarro\nPresidente del Consejo Rector")),
                box("footnote", "² Este contrato fue aprobado por el Consejo Rector de la Cooperativa en su sesión de 5 de junio de 2026 (acta n.º 14/2026)."),
            ],
        ],
    }



def contract_he() -> dict[str, Any]:
    """הסכם שכירות בלתי מוגנת (Chromium, RTL, 5 pages)."""
    rent = 745000
    rows, total = [], 0
    for index in range(12):
        month = (8 + index - 1) % 12 + 1
        year = 2026 + (8 + index - 1) // 12
        rows.append([str(index + 1), f"{RLM}10.{month:02d}.{year}", f"{LRM}3301-{4471 + index}{LRM}", money(rent, "he")])
        total += rent
    schedule = continued("cheques", [["מס׳", "תאריך פירעון", "מס׳ המחאה", "סכום"]], rows, [7, 5],
                         caption="טבלה 1 – לוח המחאות דמי השכירות לשנת השכירות הראשונה",
                         continued_caption="טבלה 1 – לוח המחאות דמי השכירות (המשך)", align=["r", "r", "r", "r"], widths=[10, 30, 30, 30],
                         total=[["", "סה״כ לשנת השכירות", "", money(total, "he")]])
    css = legal_css({1: 0, 2: 2, 3: 5, 4: 7, 5: 12}) + "ol.cl ol ol>li::marker{content:'(' counter(list-item,hebrew) ')  '}"
    return {
        "template": "legal_contract", "page_size": "A4", "languages": ["he-IL", "en"], "dir": "rtl",
        "metadata": {"title": "הסכם שכירות בלתי מוגנת – רחוב הנביאים 28, חיפה", "author": "משרד עו״ד אלמוג־שטרן",
                     "subject": "שכירות דירת מגורים, דירה 7, קומה 3", "keywords": ["הסכם שכירות", "שכירות בלתי מוגנת", "חיפה", "ערבות"],
                     "lang": "he-IL", "created": "2026-07-21T07:15:00Z"},
        "theme": {"accent": "#24496b", "font_size": "11.5pt", "margins": "18mm 18mm 18mm 18mm", "extra_css": css},
        "running_header": "הסכם שכירות – רחוב הנביאים 28, חיפה – עמוד {page} מתוך {pages}",
        "running_footer": "חתימת המשכיר: __________   חתימת השוכרים: __________",
        "arithmetic": [{"kind": "column_sum", "table": "cheques", "columns": [3], "label_column": 1, "total_label": "סה״כ לשנת השכירות"},
                       {"kind": "sum", "terms": [["+", money(rent, "he")], ["+", money(rent, "he")], ["+", money(rent, "he")]], "equals": money(3 * rent, "he")}],
        "pages": [
            [
                H(1, "הסכם שכירות בלתי מוגנת"),
                P("שנערך ונחתם בחיפה ביום 21 בחודש יולי 2026", "meta"),
                pair(P(f"**בין:** מר אהרון בן־דוד, ת״ז 031447289, מרחוב מוריה 112, חיפה, טלפון 054‑5550417, דוא״ל {LRM}aharon.bd@mail.example{LRM}\n(להלן: **״המשכיר״**)\n**מצד אחד;**"),
                     P(f"**לבין:** גב׳ נועה לוינסון, ת״ז 204518836, ומר דניאל {LRM}Daniel Okafor{LRM} (אוקאפור), דרכון בריטי {LRM}GB 538194027{LRM}, "
                       "יחד ולחוד\n(להלן: **״השוכרים״**)\n**מצד שני;**")),
                H(2, "מבוא"),
                P("**הואיל** והמשכיר הוא הבעלים הרשום של דירה בת 3.5 חדרים בקומה השלישית ברחוב הנביאים 28, חיפה, הידועה כגוש 10812 חלקה 44 "
                  "תת־חלקה 7, לרבות מחסן ומקום חניה מס׳ 7 (להלן: **״המושכר״**);"),
                P("**והואיל** והשוכרים מעוניינים לשכור את המושכר למטרת מגורים בלבד, והמשכיר מסכים להשכיר להם את המושכר בתנאי השכירות "
                  "הבלתי מוגנת ובהתאם לחוק השכירות והשאילה, התשל״א–1971, ולפרק ו׳1 לחוק (שכירות דירה למגורים);"),
                P("**והואיל** והשוכרים הצהירו כי ראו ובדקו את המושכר ומצאו אותו מתאים למטרתם;"),
                table("terms", [["פרט", "תנאי"], ["המושכר", "דירת 3.5 חדרים, קומה 3, רחוב הנביאים 28, חיפה, כולל מחסן וחניה מס׳ 7"],
                                ["תקופת השכירות", "10.08.2026 עד 09.08.2027, עם אופציה לשנה נוספת"],
                                ["דמי שכירות חודשיים", money(rent, "he")], ["ביטחונות", "ערבות בנקאית ₪14,900.00 ושטר חוב ₪30,000.00"]],
                      caption="תמצית עיקרי העסקה", widths=[28, 72]),
                P("**לפיכך הוצהר, הותנה והוסכם בין הצדדים כדלקמן:**"),
                classed(ordered([
                    item("**מבוא ופרשנות.** המבוא להסכם והנספחים לו מהווים חלק בלתי נפרד ממנו.", [
                        "כותרות הסעיפים נועדו לנוחות בלבד ואין להשתמש בהן לפרשנות ההסכם.",
                        "האמור בלשון רבים משמעו גם בלשון יחיד, וההפך.",
                    ]),
                    item("**המושכר.** המשכיר משכיר לשוכרים והשוכרים שוכרים מהמשכיר את המושכר, לרבות המטלטלין המפורטים בנספח א׳.", [
                        item("המטלטלין כוללים, בין היתר:", [
                            f"מקרר, תנור אפייה וכיריים גז, מדיח כלים מתוצרת {LRM}Bosch{LRM};",
                            "מזגנים בסלון ובשני חדרי השינה, ודוד שמש עם גיבוי חשמלי;",
                            "ארונות מטבח וארון קיר בחדר השינה הראשי.",
                        ]),
                        "המשכיר מצהיר כי אין כל מניעה חוקית, חוזית או אחרת להשכרת המושכר, וכי המושכר אינו משועבד לצד שלישי.",
                    ]),
                ]), "cl"),
            ],
            [
                classed(ordered([
                    item("**תקופת השכירות.** השכירות תחל ביום 10.08.2026 ותסתיים ביום 09.08.2027 (להלן: **״תקופת השכירות״**).", [
                        "לשוכרים נתונה אופציה להאריך את השכירות לשנה נוספת, בהודעה בכתב שתימסר למשכיר לפחות 60 יום לפני תום התקופה.",
                        "בתקופת האופציה יעודכנו דמי השכירות בשיעור של 3% לכל היותר.",
                    ]),
                    item(f"**דמי השכירות.** השוכרים ישלמו למשכיר דמי שכירות חודשיים בסך {money(rent, 'he')} (שבעת אלפים ארבע מאות וחמישים שקלים חדשים).", [
                        item("דמי השכירות ישולמו:", [
                            "מראש, בעשירי לכל חודש, באמצעות 12 המחאות דחויות המפורטות בטבלה 1;",
                            "לחלופין, בהעברה בנקאית לחשבון המשכיר בבנק לאומי, סניף 902, חשבון 44718/30;",
                            "בתוספת הפרשי הצמדה למדד המחירים לצרכן, אם עלה המדד ביותר מ־2% ממדד הבסיס.",
                        ]),
                        "איחור בתשלום של יותר מ־14 יום יחייב בריבית פיגורים בשיעור הקבוע בחוק פסיקת ריבית והצמדה.¹",
                    ]),
                ]), "cl"),
                schedule[0],
                box("footnote", "¹ חוק פסיקת ריבית והצמדה, התשכ״א–1961."),
            ],
            [
                schedule[1],
                P(f"עם חתימת ההסכם מסרו השוכרים למשכיר את שלוש ההמחאות הראשונות, בסך כולל של {money(3 * rent, 'he')}. "
                  "יתר ההמחאות יימסרו לא יאוחר מיום תחילת השכירות."),
                classed(ordered([
                    item("**ביטחונות.** להבטחת קיום התחייבויותיהם ימסרו השוכרים למשכיר, במעמד חתימת ההסכם:", [
                        item("את הביטחונות הבאים:", [
                            "ערבות בנקאית אוטונומית בסך ₪14,900.00, צמודה למדד, בתוקף עד 60 יום לאחר תום תקופת השכירות;",
                            f"שטר חוב בסך ₪30,000.00 חתום בידי שני ערבים (גב׳ מרים לוינסון ומר {LRM}Chidi Okafor{LRM});",
                        ]),
                        "המשכיר רשאי לממש את הביטחונות רק לאחר שמסר לשוכרים התראה בכתב של 10 ימים לפחות.",
                        "הביטחונות יוחזרו לשוכרים תוך 60 יום מתום השכירות, לאחר הצגת אישורי תשלום של חשבונות הארנונה, המים, החשמל והגז.",
                    ]),
                    item("**שימוש במושכר.** השוכרים ישתמשו במושכר למגורים בלבד ולא יעשו בו כל שינוי ללא הסכמת המשכיר מראש ובכתב.", [
                        "השוכרים לא יעבירו את זכויותיהם ולא ישכירו את המושכר בשכירות משנה, לרבות באמצעות אתרי השכרה לטווח קצר.",
                        "החזקת חיית מחמד אחת (חתול) מותרת, בכפוף לתקנון הבית המשותף.",
                    ]),
                ]), "cl"),
            ],
            [
                classed(ordered([
                    item("**תיקונים ותחזוקה.** המשכיר יתקן, תוך זמן סביר ממועד הדרישה, כל פגם במושכר שאינו נובע משימוש בלתי סביר.", [
                        "פגם שאינו סובל דיחוי, כגון נזילת מים או תקלה בחשמל, יתוקן תוך שלושה ימים.",
                        "תיקון פגם אחר יבוצע תוך 30 יום, כקבוע בסעיף 25ט לחוק.",
                        "השוכרים יישאו בתיקונים הנובעים מבלאי שוטף של מנעולים, נורות וברזים.",
                    ]),
                    item("**תשלומים שוטפים.** במשך תקופת השכירות יישאו השוכרים בתשלומי הארנונה, המים, החשמל, הגז ודמי ועד הבית (₪180.00 לחודש).", [
                        "השוכרים יעבירו את חשבונות הארנונה והמים על שמם תוך 14 יום מתחילת השכירות.",
                        "תשלומים בעלי אופי הוני, לרבות היטלי השבחה ושיפוץ חזיתות, יחולו על המשכיר.",
                    ]),
                    item("**ביטוח.** המשכיר יבטח את מבנה הדירה, והשוכרים רשאים לבטח את תכולתם.", [
                        "בפוליסות הביטוח ייכלל סעיף ויתור על זכות התחלוף כלפי הצד השני, למעט כלפי מי שגרם לנזק בזדון.",
                    ]),
                    item("**הפרה וסיום.** הפרת סעיפים 3, 4, 6 או 7 תיחשב הפרה יסודית של ההסכם.", [
                        "בהפרה יסודית שלא תוקנה תוך 14 יום ממתן התראה בכתב, רשאי הצד הנפגע לבטל את ההסכם.",
                        "השוכרים רשאים לסיים את השכירות לפני תומה בהודעה מוקדמת של 90 יום, ובלבד שיציעו שוכר חלופי מתאים.",
                    ]),
                    item("**פינוי המושכר.** בתום השכירות יפנו השוכרים את המושכר וימסרו אותו כשהוא נקי ובמצב שבו קיבלו אותו, למעט בלאי סביר.", [
                        "על כל יום איחור בפינוי ישלמו השוכרים פיצוי מוסכם בסך ₪350.00, מבלי לגרוע מכל סעד אחר.",
                    ]),
                ]), "cl"),
                box("callout", "השוכרים מאשרים כי קיבלו לידיהם את ״רשימת הליקויים הידועים במושכר״ (נספח ב׳) לפני חתימת ההסכם, "
                    "כנדרש בסעיף 25ה לחוק השכירות והשאילה.", title="הצהרה על ליקויים ידועים", cls="note"),
            ],
            [
                classed(ordered([
                    item("**שונות.** כל שינוי בהסכם זה ייעשה בכתב ובחתימת שני הצדדים.", [
                        "הודעות יישלחו לכתובות הצדדים המפורטות בכותרת ההסכם, או בדואר אלקטרוני, ויראו אותן כמתקבלות תוך 3 ימי עסקים.",
                        "סמכות השיפוט הבלעדית בכל עניין הנוגע להסכם זה נתונה לבתי המשפט המוסמכים בחיפה.",
                        f"הנוסח העברי של ההסכם הוא המחייב. תרגום לאנגלית ({LRM}English convenience translation{LRM}) נמסר לשוכר דניאל אוקאפור לנוחותו בלבד.²",
                    ]),
                ]), "cl"),
                H(2, "נספחים"),
                L(["נספח א׳ – רשימת מטלטלין ופרוטוקול מסירה עם תמונות", "נספח ב׳ – רשימת הליקויים הידועים במושכר",
                   "נספח ג׳ – נוסח הערבות הבנקאית", "נספח ד׳ – תקנון הבית המשותף"]),
                P("**ולראיה באו הצדדים על החתום:**"),
                pair(P("______________________\n**המשכיר**\nאהרון בן־דוד"),
                     P(f"______________________\n**השוכרים**\nנועה לוינסון\n{LRM}Daniel Okafor{LRM}")),
                H(3, "אישור עורך הדין"),
                P("אני הח״מ, עו״ד יעל אלמוג־שטרן (מ.ר. 58213), מאשרת כי הצדדים חתמו על הסכם זה בפניי ביום 21.07.2026, לאחר שזיהו עצמם "
                  "בתעודות מזהות, וכי הוסבר לשוכר דניאל אוקאפור תוכן ההסכם בשפה האנגלית והוא הצהיר כי הבינו."),
                P("______________________\nיעל אלמוג־שטרן, עו״ד"),
                box("footnote", "² בכל מקרה של סתירה בין הנוסח העברי לבין התרגום, יגבר הנוסח העברי."),
            ],
        ],
    }



def contract_zhtw() -> dict[str, Any]:
    """ERP 系統建置委託契約書（ReportLab, CID font, 5 pages）."""
    price = 4860000
    stages = [("第一期", "契約簽訂後十五日內", 20), ("第二期", "需求規格書經甲方驗收後", 25), ("第三期", "系統上線並完成平行測試後", 30),
              ("第四期", "最終驗收合格後", 20), ("保固款", "保固期滿無待解決問題後", 5)]
    rows, total = [], 0
    for name, cond, pct in stages:
        amount = price * pct // 100
        total += amount
        rows.append([name, cond, f"{pct}％", money(amount, "zhTW")])
    rows.append(["合計", "", "100％", money(total, "zhTW")])
    pay = table("fukuan", [["期別", "付款條件", "比例", "金額（含稅）"], *rows], caption="表一　付款期程",
                align=["l", "l", "r", "r"], widths=[14, 50, 12, 24], total_rows=[len(rows)])
    team = table("renyuan", [["職務", "姓名", "投入比例", "主要工作"],
                             ["專案經理", "林冠宇", "100％", "專案管理、進度與風險控管"],
                             ["系統分析師", "陳怡君", "100％", "需求訪談、流程設計、規格書撰寫"],
                             ["資深工程師", "黃柏翰", "100％", "生產排程與 MRP 模組客製"],
                             ["資料轉換工程師", "吳承恩", "50％", "舊系統料號、BOM 與庫存資料轉換"],
                             ["教育訓練講師", "蔡佩珊", "30％", "關鍵使用者與一般使用者訓練"]],
                 caption="表二　乙方專案人員", widths=[18, 14, 14, 54])
    rd_spec = {"title": "預估人日", "categories": ["需求訪談", "規格設計", "客製開發", "資料轉換", "整合測試", "教育訓練", "上線輔導"],
               "series": [("乙方", [42, 36, 118, 40, 54, 22, 48]), ("甲方配合", [30, 12, 6, 28, 46, 18, 20])],
               "max": 140, "ticks": 4, "tick_format": lambda v: number(v, "en", 0)}
    return {
        "template": "legal_contract", "page_size": "A4", "languages": ["zh-TW", "en"],
        "metadata": {"title": "ERP 系統建置委託契約書－宏遠精密機械股份有限公司", "author": "雲杉資訊股份有限公司 法務室",
                     "subject": "企業資源規劃系統導入、客製開發及維護", "keywords": ["委託契約", "ERP", "付款期程", "保固"], "lang": "zh-TW",
                     "created": "2026-03-18T02:10:00Z"},
        "theme": {"accent": "#5b2c6f", "rl_size": 11.6},
        "running_header": "ERP 系統建置委託契約書（契約編號：HY-IT-2026-007）　第 {page} 頁，共 {pages} 頁",
        "running_footer": "甲方：宏遠精密機械股份有限公司　　乙方：雲杉資訊股份有限公司",
        "arithmetic": [{"kind": "column_sum", "table": "fukuan", "columns": [3], "label_column": 0, "total_label": "合計"}],
        "pages": [
            [
                H(1, "ERP 系統建置委託契約書"),
                P("契約編號：HY-IT-2026-007　　簽約日期：中華民國一一五年三月十八日", "meta"),
                pair(P("**委託人（以下簡稱甲方）**\n宏遠精密機械股份有限公司\n統一編號：28417730\n地址：臺中市西屯區工業區三十八路 152 號\n代表人：董事長　張明哲"),
                     P("**受託人（以下簡稱乙方）**\n雲杉資訊股份有限公司\n統一編號：53906218\n地址：臺北市內湖區瑞光路 488 號 9 樓\n代表人：總經理　許文彥")),
                P("甲方為整合生產、採購、庫存及財務作業，委託乙方建置企業資源規劃系統（以下簡稱「本系統」）。雙方本於誠信原則，"
                  "同意訂立本契約，條款如下："),
                H(2, "第一條　契約文件及效力"),
                ordered([item("本契約包括下列文件：", ["本契約書本文；", "甲方需求說明書（RFP 編號 HY-RFP-2025-12）；", "乙方建議書及報價單（2026 年 2 月 20 日版）；", "雙方簽認之會議紀錄及變更單。"]),
                         "前項文件內容有衝突時，以本契約書本文優先，其次依前項所列順序定之。"]),
                H(2, "第二條　委託範圍"),
                ordered([item("乙方應依本契約完成下列工作：", [
                            "生產、採購、庫存、銷售、成本及總帳模組之導入與參數設定；",
                            "與甲方現有 MES 系統及電子發票平台之介接；",
                            "舊系統資料轉換，包括料號約 3.2 萬筆、BOM 約 4,800 份及近三年交易資料；",
                            "教育訓練、上線輔導及上線後三個月之駐點支援。"]),
                         "本系統採雲端訂閱與地端部署併行架構，詳細規格以需求規格書為準。",
                         "超出前二項範圍之工作，應依第十條變更程序辦理。"]),
                H(2, "第三條　履約期限"),
                ordered(["乙方應於簽約後十五日內提出專案計畫書，經甲方書面同意後執行。",
                         "本系統應於中華民國一一五年十月一日前正式上線，並於上線後六十日內完成最終驗收。",
                         "因甲方未依約提供資料或決策延遲致無法如期完成者，履約期限得順延，順延日數由雙方協商定之。"]),
            ],
            [
                H(2, "第四條　契約價金及付款方式"),
                ordered([f"本契約總價為新臺幣{number(price, 'en', 0)}元整（含營業稅），為總價承攬。",
                         item("甲方應依表一之期程付款，乙方應於各期付款條件成就後開立統一發票：", [
                             "甲方於收到發票後三十日內，以電匯方式支付至乙方指定帳戶；",
                             "甲方對發票內容有疑義者，應於收受後七日內以書面通知乙方，並先行支付無爭議部分。"]),
                         "雲端訂閱費用另依每年度訂單計價，不包含於前項總價內。"]),
                pay,
                P(f"表一各期金額合計{money(total, 'zhTW')}，與本條第一項所定總價相符。保固款得由乙方提出等額之銀行履約保證函代替。"),
                H(2, "第五條　專案組織"),
                P("乙方應指派具備同類型製造業 ERP 導入經驗之專案人員，非經甲方書面同意，不得更換表二所列之專案經理及系統分析師。"
                  "甲方應指派專案負責人一名及各部門關鍵使用者，配合需求訪談與測試。"),
                team,
            ],
            [
                H(2, "第六條　驗收"),
                ordered([item("驗收分為下列階段：", ["需求規格書驗收；", "整合測試驗收：依雙方確認之測試案例執行，關鍵測試案例通過率須達百分之百；", "最終驗收：上線後連續六十日，系統可用率達 99.5％以上，且無一級問題未解決。"]),
                         "甲方應於乙方通知驗收後十個工作日內完成驗收；逾期未表示意見者，視為驗收合格。",
                         "驗收不合格者，乙方應於甲方通知後十五日內改善並重新申請驗收。"]),
                H(2, "第七條　保固及維護"),
                ordered(["保固期間自最終驗收合格之日起算十二個月，乙方應免費修正本系統之瑕疵。",
                         item("問題等級及回應時間如下：", ["一級（系統停擺或無法出貨）：一小時內回應，八小時內提出暫行解決方案；",
                                                      "二級（主要功能異常）：四小時內回應，三個工作日內修正；",
                                                      "三級（一般問題或操作諮詢）：一個工作日內回應。"]),
                         "保固期滿後，甲方得以每年契約總價百分之十二之費用委託乙方提供維護服務。"]),
                box("callout", "一級問題之通報應以電話（02-5550-8800）及電子郵件（support@yunshan.example）同時為之，"
                    "並於工單系統登錄；未登錄者，回應時間自登錄時起算。", title="緊急通報窗口", cls="note"),
                H(2, "第八條　智慧財產權"),
                ordered(["本系統之標準套裝軟體著作權屬乙方或其授權人所有，甲方取得非專屬、不可轉讓之永久使用權。",
                         "專為甲方客製之程式及文件，其著作財產權於甲方付清相關價金時移轉予甲方，乙方保留其中通用元件之使用權。",
                         "乙方保證所交付之軟體未侵害第三人之智慧財產權；如有侵害，乙方應負責處理並賠償甲方因此所受之損害。"]),
            ],
            [
                H(2, "第九條　保密及個人資料保護"),
                ordered(["雙方對於因履行本契約所知悉之他方營業秘密、技術資料及客戶資料，應負保密義務，非經他方書面同意不得洩漏。",
                         "乙方處理甲方員工及客戶個人資料時，應遵守個人資料保護法之規定，並僅得於委託目的範圍內利用。",
                         "保密義務於本契約終止或解除後五年內仍繼續有效。"]),
                H(2, "第十條　契約變更"),
                ordered(["任一方請求變更工作範圍者，應填具變更單，載明變更內容、對時程及價金之影響，經雙方簽認後生效。",
                         "變更所需之工作量以人日計價，每人日新臺幣 12,000 元；單次變更逾 30 人日者，應另行簽訂增補協議。"]),
                chart("f1", "bar", rd_spec, "圖一　各階段預估投入人日（變更估算之基準）", raster=False, width_cm=13.5, size=(520, 200)),
                chart_table("c1", "階段", rd_spec, lambda v: number(v, "en", 0)),
                H(2, "第十一條　遲延及違約責任"),
                ordered([item("乙方未能於第三條所定期限內完成上線者：", ["每逾一日，按契約總價千分之一計算違約金；", "違約金總額以契約總價百分之十為上限。"]),
                         "任一方違反本契約之損害賠償責任，除故意或重大過失外，以契約總價為上限，且不包括間接損失及所失利益。¹"]),
                H(2, "第十二條　契約終止及解除"),
                ordered(["任一方重大違約，經他方以書面限期十五日催告改善而未改善者，他方得終止或解除本契約。",
                         "契約終止時，乙方應將已完成之工作成果、文件及甲方資料返還甲方，甲方應支付已完成且驗收合格部分之價金。"]),
                box("footnote", "¹ 依民法第二百五十條規定，違約金如有過高情事，法院得減至相當之數額。"),
            ],
            [
                H(2, "第十三條　準據法及管轄法院"),
                ordered(["本契約以中華民國法律為準據法。",
                         "因本契約發生之爭議，雙方應先本於誠信協商；協商不成時，同意以臺灣臺中地方法院為第一審管轄法院。"]),
                H(2, "第十四條　其他約定"),
                ordered(["本契約之通知應以書面送達本契約所載地址；地址變更時應即通知他方。",
                         "本契約未盡事宜，依相關法令及誠信原則辦理。",
                         "本契約正本一式二份，由雙方各執一份為憑；副本二份，由雙方專案負責人各執一份。"]),
                H(2, "立契約書人"),
                pair(P("**甲方：宏遠精密機械股份有限公司**\n代表人：張明哲　（簽章）\n\n專案負責人：資訊處經理　劉育廷\n電話：04-2355-0172"),
                     P("**乙方：雲杉資訊股份有限公司**\n代表人：許文彥　（簽章）\n\n專案經理：林冠宇\n電話：02-5550-8812")),
                P("中華民國一一五年三月十八日", "center"),
                H(3, "附件"),
                L(["附件一：甲方需求說明書", "附件二：乙方建議書及報價單", "附件三：服務水準協議（SLA）", "附件四：個人資料保護約定書"]),
                box("footnote", "² 本契約之印花稅由雙方各自負擔；依印花稅法規定，承攬契據按金額千分之一貼用印花稅票。"),
            ],
        ],
    }



# ================================================================ resumes


def cv_en() -> dict[str, Any]:
    """Two-column data engineering résumé (Chromium, 3 pages)."""
    css = (".split{gap:6mm}.split>:first-child{flex:0 0 30%;background:#f2f5f7;padding:3mm 4mm;border-top:3px solid #0f5e63}"
           ".split>:first-child h2{font-size:1.05em}.split>:first-child p{font-size:.92em}.split>:first-child ul{font-size:.9em}"
           ".split>:last-child{flex:1}.cvname{font-size:2.3em;font-weight:700;color:#0f5e63;margin:0}")
    side1 = group([
        H(2, "Contact"),
        P(" priya.rc@mailbox.example\n +1 (206) 555-0193\n Seattle, WA 98103\n github.example/priyarc\n linkedin.example/in/priya-rc", "icons"),
        H(2, "Core skills"),
        L(["Python, SQL, Scala", "Apache Spark & Flink", "dbt, Airflow, Dagster", "Kafka, Debezium (CDC)", "Snowflake, BigQuery, Postgres",
           "Terraform, Kubernetes", "Data modeling (Kimball, Data Vault 2.0)", "Data quality & observability"]),
        H(2, "Languages"),
        P("**English** — native\n**Tamil** (தமிழ்) — native\n**Spanish** — professional (DELE B2)\n**Mandarin** (普通话) — conversational (HSK 3)"),
        H(2, "Education"),
        P("**M.S. Computer Science**\nUniversity of Washington, Seattle — 2016\nThesis: *Incremental view maintenance for streaming joins*"),
        P("**B.Tech. Information Technology**\nAnna University, Chennai — 2013\nFirst class with distinction (8.9/10)"),
    ])
    main1 = group([
        H(2, "Experience"),
        H(3, "Staff Data Engineer — Cascadia Freight Systems, Seattle"),
        P("*March 2022 – present* · logistics marketplace, 1,400 employees", "small"),
        L(["Lead a team of six engineers that owns the shipment event platform (≈ 2.1 billion events/day) and the analytics warehouse.",
           "Replaced nightly batch exports with Debezium change-data-capture into Kafka, cutting median data freshness from 26 hours to 4 minutes.",
           "Designed a Data Vault 2.0 model for carrier, lane and invoice data; migrated 340 dbt models without downtime for finance reporting.",
           "Introduced data contracts and automated quality checks (Great Expectations, Monte Carlo); incidents reaching dashboards fell by 71% year over year.",
           "Reduced Snowflake spend by $412,000 a year through clustering, warehouse right-sizing and retiring 1,100 unused tables.",
           "Mentor four engineers; two were promoted to senior in 2025. Chair of the internal data architecture review board."]),
        H(3, "Senior Data Engineer — Lumen & Lark Health, Portland"),
        P("*June 2018 – February 2022* · digital health, Series C", "small"),
        L(["Built HIPAA-compliant ingestion for HL7 FHIR feeds from 38 partner clinics, with field-level encryption and audit logging.",
           "Migrated 60 Airflow DAGs from a single VM to Kubernetes executors; pipeline failures dropped from ~12 to 2 per month.",
           "Developed the patient-cohort feature store used by three machine learning models for appointment no-show prediction."]),
    ])
    return {
        "template": "resume", "page_size": "Letter", "languages": ["en-US", "ta", "zh", "es"],
        "metadata": {"title": "Priya Raghunathan-Cole — Résumé", "author": "Priya Raghunathan-Cole", "subject": "Staff data engineer résumé",
                     "keywords": ["résumé", "data engineering", "Spark", "dbt", "Seattle"], "lang": "en-US", "created": "2026-09-02T22:05:00Z"},
        "theme": {"accent": "#0f5e63", "font_size": "10.2pt", "body_font": "'Noto Sans'", "margins": "14mm 14mm 16mm 14mm", "extra_css": css},
        "running_footer": "Priya Raghunathan-Cole · Résumé · page {page} of {pages}",
        "pages": [
            [
                P("Priya Raghunathan-Cole", "cvname"),
                P("Staff Data Engineer · streaming data platforms · analytics engineering", "lead"),
                P("Data engineer with ten years of experience building reliable batch and streaming pipelines for logistics and health "
                  "care. I like turning fragile nightly jobs into observable, well-modeled data products, and I enjoy growing engineers "
                  "who want to do the same. Looking for a principal-level role with ownership of platform architecture."),
                group([side1, main1], "split"),
            ],
            [
                group([
                    group([H(2, "Certifications"),
                           P("SnowPro Advanced: Data Engineer (2024)\nCertified Kubernetes Application Developer (2023)\nAWS Certified Data Engineer – Associate (2024)"),
                           H(2, "Community"),
                           P("Co-organizer, Seattle Data Engineering Meetup (2,300 members) since 2021.\nVolunteer instructor, Code the Sound — SQL for nonprofits."),
                           H(2, "Awards"),
                           P("Cascadia Freight Engineering Excellence Award (2024)\nLumen & Lark “Patient First” Award (2020)"),
                           H(2, "Interests"),
                           P("Long-distance cycling (STP 2024, 206 mi), South Indian cooking, carnatic violin.")]),
                    group([
                        H(3, "Senior Data Engineer — Lumen & Lark Health (continued)"),
                        L(["Partnered with the privacy office on de-identification (k-anonymity ≥ 11) for research data shares.",
                           "On-call lead for the data platform; wrote the runbooks still in use for backfills and schema migrations."]),
                        H(3, "Data Engineer — Orcasound Media, Seattle"),
                        P("*August 2016 – May 2018* · streaming audio, ad-supported", "small"),
                        L(["Built the listening-event pipeline on Kinesis and Spark Streaming (≈ 40,000 events/s at peak).",
                           "Delivered the first self-service BI layer in Looker; 120 weekly active users within six months.",
                           "Cut royalty-report preparation from five days to one by automating reconciliation with label statements."]),
                        H(3, "Software Engineer Intern — Kaveri Analytics, Chennai"),
                        P("*January 2013 – June 2013*", "small"),
                        L(["Wrote ETL jobs in Java and Hive for a retail loyalty program covering 3.4 million customers."]),
                        H(2, "Selected projects"),
                        P("**tidewater** — open-source library for testing dbt models against production-like fixtures. 1,800 GitHub stars, "
                          "used by about 90 companies. Maintainer since 2021. [github.example/priyarc/tidewater](https://github.example/priyarc/tidewater)"),
                        P("**Late-arriving events at scale** — internal design that handles carrier scans arriving up to 30 days late using "
                          "watermarks plus a correction stream; adopted by three other teams."),
                        P("**Warehouse cost dashboard** — per-team cost attribution for Snowflake credits with weekly anomaly alerts; "
                          "made spend visible to 14 product teams."),
                    ]),
                ], "split"),
                box("callout", "Comfortable leading cross-functional design reviews, writing RFCs and presenting trade-offs to executives. "
                    "Open to hybrid roles in Seattle or remote within US Pacific time.", title="What I am looking for", cls="note"),
            ],
            [
                H(2, "Publications and talks"),
                L(["Raghunathan-Cole, P. “Contracts, not heroics: data quality at a freight marketplace.” *Data Council*, Austin, 2025.",
                   "Raghunathan-Cole, P., and M. Ishikawa. “Exactly-once is a team sport: lessons from CDC pipelines.” *Current ’24*, San Jose, 2024.",
                   "Raghunathan, P., and D. Suciu. “Incremental view maintenance for windowed stream joins.” *Proceedings of the VLDB PhD Workshop*, 2016.",
                   "“From cron to contracts” — guest lecture, CSE 414 Introduction to Data Management, University of Washington, 2023."]),
                H(2, "Technical skills in detail"),
                table("skills", [["Area", "Tools and depth", "Years"],
                                 ["Languages", "Python (expert), SQL (expert), Scala (advanced), Go (working)", "10"],
                                 ["Processing", "Spark, Flink, Beam, Kafka Streams; batch and streaming joins, backfills", "8"],
                                 ["Orchestration", "Airflow, Dagster, dbt Core and dbt Cloud, GitHub Actions", "7"],
                                 ["Storage", "Snowflake, BigQuery, Postgres, Iceberg on S3, Delta Lake", "8"],
                                 ["Infrastructure", "Terraform, Kubernetes, Helm, AWS (MSK, EMR, Glue), GCP", "6"],
                                 ["Quality", "Great Expectations, Soda, Monte Carlo, OpenLineage", "4"]],
                      caption="Skills matrix", widths=[18, 70, 12], align=["l", "l", "r"]),
                H(2, "Leadership highlights"),
                L(["Hired and onboarded 9 engineers across two companies; designed the data engineering interview loop at Cascadia Freight.",
                   "Ran the 2024 warehouse migration program across finance, operations and marketing (14 stakeholders, delivered two weeks early).",
                   "Introduced blameless postmortems for data incidents; median time to resolve fell from 9 to 3 hours."]),
                H(2, "References"),
                group([P("**Marcus Ishikawa**\nVP Engineering, Cascadia Freight Systems\nmarcus.ishikawa@cascadiafreight.example\n+1 (206) 555-0144"),
                       P("**Dr. Aleksandra Nowicka**\nDirector of Data, Lumen & Lark Health\na.nowicka@lumenlark.example\n+1 (503) 555-0178")], "split"),
            ],
        ],
    }


def cv_de() -> dict[str, Any]:
    """Tabellarischer Lebenslauf (LibreOffice, untagged, 3 pages)."""
    stationen = [
        ["seit 04/2022", "Projektleiterin Freiraumplanung, Grünwerk Landschaftsarchitekten PartGmbB, Freiburg im Breisgau\n"
                         "Leitung von Projekten bis 6,8 Mio. € Baukosten (LPH 1–8 HOAI); Führung eines Teams von vier Mitarbeitenden; "
                         "Wettbewerbsbetreuung und Bürgerbeteiligung"],
        ["", "Schwerpunkt: klimaangepasste Stadträume, Schwammstadt-Prinzip, Regenwasser­bewirtschaftung"],
        ["07/2018 – 03/2022", "Landschaftsarchitektin, Stadt Bad Kellbach, Amt für Stadtgrün und Umwelt\n"
                              "Planung und Bauleitung öffentlicher Grünanlagen, Spielplätze und Straßenbegleitgrün; Ausschreibung nach VOB/A"],
        ["", "Referenzprojekt: Neugestaltung des Uferparks an der Kellbach (2,1 ha, Fertigstellung 2021)"],
        ["10/2016 – 06/2018", "Wissenschaftliche Mitarbeiterin, Hochschule für Wirtschaft und Umwelt Nürtingen-Geislingen, "
                              "Institut für Landschaftsplanung\nForschungsprojekt „Klimabäume für die Stadt“ (gefördert vom BMUV)"],
        ["04/2015 – 09/2016", "Werkstudentin, Studio Feldmann Landschaftsarchitektur, Stuttgart\nVisualisierungen, Pflanzpläne, Kostenschätzungen nach DIN 276"],
        ["08/2013 – 01/2014", "Praktikum, Parks Department, City of Copenhagen (Københavns Kommune)\nMitarbeit am Klimatilpasningsplan, Kartierung von Überflutungs­bereichen"],
    ]
    beruf = continued("beruf", [["Zeitraum", "Tätigkeit"]], stationen, [4, 3], rendering="borderless", caption="Berufserfahrung",
                      continued_caption="Berufserfahrung (Fortsetzung)", widths=[22, 78])
    return {
        "template": "resume", "page_size": "A4", "languages": ["de-DE", "da", "en"], "tagged": False,
        "metadata": {"title": "Lebenslauf – Dipl.-Ing. Katharina Oberländer", "author": "Katharina Oberländer", "subject": "Tabellarischer Lebenslauf, Landschaftsarchitektur",
                     "keywords": ["Lebenslauf", "Landschaftsarchitektin", "Freiraumplanung", "Bewerbung"], "lang": "de-DE", "created": "2026-08-17T16:40:00Z"},
        "theme": {"accent": "#2f5d3a", "lo_size": "11pt", "lo_font": "Noto Sans"},
        "running_footer": "Katharina Oberländer · Lebenslauf · Seite {page} von {pages}",
        "pages": [
            [
                H(1, "Lebenslauf"),
                photo("p1", ["park-path"], ["park", "landscape"], {"park-path": "Referenzprojekt Uferpark Bad Kellbach (Planung und Bauleitung, 2019–2021)"},
                      "Referenzprojekt Uferpark Bad Kellbach", wrap="right", width="38%", width_cm=6.0),
                P("Dipl.-Ing. (FH) Katharina Oberländer, M.Sc.\nLandschaftsarchitektin (AKBW, Mitgliedsnr. 04-51873)"),
                P("Wiehrestraße 61\n79102 Freiburg im Breisgau\nTelefon: 0761 555 48 27\nE-Mail: k.oberlaender@posteo.example"),
                P("Geboren am 3. Mai 1989 in Konstanz · Staatsangehörigkeit: deutsch · verheiratet, ein Kind"),
                H(2, "Profil"),
                P("Landschaftsarchitektin mit zehn Jahren Erfahrung in Planung, Ausschreibung und Bauleitung öffentlicher Freiräume. "
                  "Mein Schwerpunkt liegt auf klimaangepassten Stadträumen: Entsiegelung, Baumstandorte mit Wasser­speicher­substraten "
                  "und multifunktionale Retentionsflächen. Ich arbeite gern an der Schnittstelle von Verwaltung, Bürgerschaft und Fachplanung."),
                *beruf[:1],
            ],
            [
                *beruf[1:],
                table("ausbildung", [["Zeitraum", "Ausbildung"],
                                     ["10/2014 – 09/2016", "Master of Science Umweltschutz, Hochschule Nürtingen-Geislingen\nAbschlussnote 1,3 – Masterarbeit: „Stadtbäume im Klimawandel: Standortwahl mit Hilfe von Hitzekarten“"],
                                     ["10/2009 – 09/2013", "Diplom-Ingenieurin (FH) Landschaftsarchitektur, Hochschule Weihenstephan-Triesdorf\nAbschlussnote 1,7; Auslandssemester an der Københavns Universitet (2012)"],
                                     ["09/2000 – 06/2009", "Allgemeine Hochschulreife, Heinrich-Suso-Gymnasium Konstanz, Note 1,9"]],
                      rendering="borderless", caption="Ausbildung", widths=[22, 78]),
                H(2, "Weiterbildung"),
                L(["Zertifizierte Baumkontrolleurin nach FLL (2020)", "Fachplanerin Regenwasser­bewirtschaftung, DWA-Lehrgang (2022)",
                   "Moderation von Beteiligungsprozessen, Akademie für Natur- und Umweltschutz Baden-Württemberg (2023)",
                   "BIM-Basiskurs für Freiraumplanung (Vectorworks Landmark), 40 Unterrichtseinheiten (2024)"]),
                H(2, "Ausgewählte Projekte"),
                L(["**Schulhof Rieselfeld, Freiburg** – Entsiegelung von 3.200 m², Klassenzimmer im Freien, Baukosten 1,4 Mio. € (2024)",
                   "**Quartiersplatz Am Weinweg, Lahr** – 1. Preis im nichtoffenen Wettbewerb, Ausführung 2025–2026",
                   "**Uferpark Bad Kellbach** – Renaturierung von 480 m Uferlinie, Hochwasserschutz HQ100, Spiel- und Aufenthaltsbereiche (2021)"]),
            ],
            [
                H(2, "Kenntnisse"),
                table("kenntnisse", [["Bereich", "Kenntnisse", "Niveau"],
                                     ["CAD / BIM", "Vectorworks Landmark, AutoCAD, Revit (Grundlagen)", "sehr gut"],
                                     ["GIS", "QGIS, ArcGIS Pro, Auswertung von Klimaanalysekarten", "sehr gut"],
                                     ["AVA", "California.pro, GAEB-Schnittstellen", "gut"],
                                     ["Visualisierung", "Adobe Photoshop, InDesign, Twinmotion", "gut"],
                                     ["Recht", "HOAI, VOB/A und VOB/B, Baumschutzsatzungen", "sehr gut"]],
                      caption="EDV- und Fachkenntnisse", widths=[20, 60, 20]),
                H(2, "Sprachen"),
                L(["Deutsch – Muttersprache", "Englisch – verhandlungssicher (C1, Cambridge Advanced)",
                   "Dänisch – gute Kenntnisse (B2; „Jeg taler dansk på arbejdet“)", "Französisch – Grundkenntnisse (A2)"]),
                H(2, "Ehrenamt und Mitgliedschaften"),
                L(["Mitglied im Bund Deutscher Landschaftsarchitekt:innen (bdla) seit 2017",
                   "Jurymitglied „Gärten in der Stadt“, Landesgartenschau GmbH Baden-Württemberg (2023, 2025)",
                   "Ehrenamtliche Baumpatenschaften im Stadtteil Wiehre, Koordination von 35 Pat:innen"]),
                H(2, "Veröffentlichungen"),
                L(["Oberländer, K. (2024): Schwammstadt im Bestand – was kleine Kommunen leisten können. In: *Stadt + Grün* 73 (5), S. 22–27.",
                   "Oberländer, K.; Reiß, T. (2017): Klimabäume für die Stadt – Ergebnisse der Standortversuche 2015–2017. Nürtingen: HfWU."]),
                P("Freiburg im Breisgau, 17. August 2026"),
                P("*Katharina Oberländer*"),
            ],
        ],
    }


def cv_ko() -> dict[str, Any]:
    """이력서 및 경력기술서 (pylopdf, 3 pages)."""
    return {
        "template": "resume", "page_size": "A4", "languages": ["ko-KR", "en"],
        "metadata": {"title": "이력서 – 박서연", "author": "박서연", "subject": "배터리 셀 공정 엔지니어 경력직 지원",
                     "keywords": ["이력서", "경력기술서", "배터리", "공정 엔지니어"], "lang": "ko-KR", "created": "2026-09-14T03:20:00Z"},
        "theme": {"accent": "#1b4f8a", "py_size": 11.2},
        "running_header": "박서연 이력서 · 지원 분야: 배터리 셀 공정개발 (경력)",
        "running_footer": "{page} / {pages}",
        "pages": [
            [
                H(1, "이력서"),
                table("insa", [["성명", "박서연", "영문", "PARK SEOYEON"],
                               ["생년월일", "1992. 2. 27.", "연락처", "010-5550-7392"],
                               ["이메일", "seoyeon.park@mail.example", "병역", "해당 없음"],
                               ["주소", "충청북도 청주시 흥덕구 오송생명로 211, 302동 1104호", "", ""]],
                      caption="인적 사항", widths=[14, 40, 12, 34], merges=((3, 1, 1, 3),)),
                table("hakryeok", [["기간", "학교 및 전공", "구분", "학점"],
                                   ["2016. 3. – 2018. 2.", "KAIST 생명화학공학과 석사 (전기화학 소재 연구실)", "졸업", "4.02 / 4.3"],
                                   ["2011. 3. – 2016. 2.", "부산대학교 화학공학과 학사", "졸업", "3.91 / 4.5"],
                                   ["2008. 3. – 2011. 2.", "부산 해운대고등학교", "졸업", "–"]],
                      caption="학력 사항", widths=[24, 50, 10, 16], align=["l", "l", "c", "r"]),
                table("gyeongryeok", [["기간", "회사명 및 부서", "직위", "담당 업무"],
                                      ["2022. 7. – 현재", "한빛에너지솔루션(주) 셀개발센터 공정기술팀", "책임", "46파이 원통형 셀 전극 공정 개발, 양산 이관"],
                                      ["2018. 3. – 2022. 6.", "대성배터리(주) 오창공장 생산기술팀", "선임", "파우치형 셀 조립·화성 공정 개선"]],
                      caption="경력 사항 (총 8년 6개월)", widths=[22, 38, 10, 30]),
                table("jagyeok", [["취득일", "자격증 및 어학", "발급 기관"],
                                  ["2019. 11. 22.", "화공기사", "한국산업인력공단"],
                                  ["2021. 5. 14.", "6시그마 블랙벨트 (BB)", "한국표준협회"],
                                  ["2025. 3. 9.", "TOEIC 945점", "ETS"],
                                  ["2024. 12. 1.", "JLPT N2", "일본국제교류기금"]],
                      caption="자격 및 어학", widths=[22, 48, 30]),
                H(2, "핵심 역량"),
                L(["건식 전극(Dry electrode) 및 고로딩 전극 공정 개발 – 실험 설계(DOE)부터 양산 조건 확정까지 주도",
                   "공정 데이터 분석: Python(pandas, scikit-learn), Minitab, JMP를 활용한 불량 원인 분석",
                   "해외 설비 업체(일본, 독일) 및 고객사와의 기술 협의 경험 – 영어·일본어 회의 진행 가능"]),
                table("susang", [["연도", "수상 및 교육 이수 내역", "기관"],
                                 ["2025", "사내 기술대상 우수상 (건식 전극 파일럿 라인 구축)", "한빛에너지솔루션"],
                                 ["2021", "6시그마 우수 과제 발표 대회 금상", "대성배터리"],
                                 ["2023", "이차전지 공정 전문가 과정 수료 (120시간)", "한국전지산업협회"],
                                 ["2017", "한국전기화학회 추계학술대회 우수 포스터상", "한국전기화학회"]],
                      caption="수상 및 교육", widths=[12, 60, 28]),
                P("병역 사항 해당 없음. 장애·보훈 대상 아님. 자격 증빙 서류는 서류 전형 합격 후 원본 대조가 가능합니다.", "small"),
            ],
            [
                H(1, "경력기술서"),
                H(2, "한빛에너지솔루션(주) 셀개발센터 공정기술팀 · 책임연구원 (2022. 7. – 현재)"),
                P("차세대 46파이 원통형 셀(4680 규격)의 양극 전극 공정 개발과 양산 라인 이관을 담당하고 있습니다. 파일럿 라인 4개 공정의 "
                  "조건 표준을 수립하고, 국내외 설비 업체와 함께 코터·프레스 설비 사양을 정의했습니다."),
                L(["고로딩 양극(면적 용량 5.2 mAh/cm²) 코팅 공정 개발: 건조 균열 불량률을 8.4%에서 1.1%로 감소",
                   "롤프레스 공정 조건 최적화로 전극 밀도 편차(±0.05 g/cc) 확보, 셀 용량 산포 32% 개선",
                   "건식 전극 파일럿 설비 도입 프로젝트 PM – 예산 18억 원, 일정 내 셋업 완료(2024. 9.)",
                   "양산 이관 시 공정 FMEA 및 관리계획서 작성, 초기 수율 92.6% 달성(목표 90%)",
                   "특허 출원 2건: 전극 건조 장치 및 방법(10-2024-0118734), 고로딩 전극 제조 방법(10-2025-0031590)"]),
                H(2, "대성배터리(주) 오창공장 생산기술팀 · 선임 (2018. 3. – 2022. 6.)"),
                P("전기차용 파우치형 셀 조립 및 화성 공정의 생산기술 엔지니어로서 라인 수율과 설비 가동률 향상 업무를 수행했습니다."),
                L(["노칭 공정 버(burr) 불량 개선: 금형 관리 기준 재정립으로 월 불량 비용 약 1억 2천만 원 절감",
                   "화성·에이징 공정 시간 단축(72시간 → 56시간) 검증, 생산 능력 22% 증대",
                   "6시그마 BB 과제 「스태킹 정렬 불량 감소」 수행 – 공정 능력 지수(Cpk) 0.87에서 1.41로 향상",
                   "신입 엔지니어 교육 프로그램 운영(연 2회, 누적 24명)"]),
                H(2, "주요 프로젝트 요약"),
                table("project", [["기간", "프로젝트", "역할", "성과"],
                                  ["2024. 1. – 2024. 9.", "건식 전극 파일럿 라인 구축", "PM", "일정 준수, 예산 3% 절감"],
                                  ["2023. 3. – 2023. 12.", "46파이 셀 양극 공정 표준화", "공정 리더", "수율 92.6% 달성"],
                                  ["2020. 6. – 2021. 4.", "스태킹 정렬 불량 감소 (6시그마)", "BB 리더", "Cpk 1.41 달성"]],
                      caption="", widths=[22, 36, 14, 28]),
                H(2, "보유 기술 상세"),
                L(["전극 공정: 믹싱(고형분 72% 슬러리), 코팅(슬롯다이), 건조, 롤프레스, 슬리팅",
                   "분석: SEM/EDS, 입도 분석, 접착력(Peel test), 전극 저항 측정, 반쪽 셀 평가",
                   "품질 도구: FMEA, 관리계획서, SPC, 8D 보고서, 4M 변경 관리",
                   "소프트웨어: Python, Minitab, JMP, SAP PP/QM 조회, Spotfire"]),
                P("석사 과정에서는 리튬이온전지 실리콘 음극의 바인더 설계를 연구하였으며, 관련 논문 1편을 SCI 학술지에 공동 저자로 게재하였습니다 "
                  "(Journal of Power Sources, 2018)."),
            ],
            [
                H(1, "자기소개서"),
                H(2, "지원 동기"),
                P("배터리 산업에서 8년 넘게 일하며 실험실의 결과가 양산 라인에서 그대로 재현되지 않는 순간을 수없이 경험했습니다. "
                  "그때마다 공정 변수와 설비, 사람을 함께 보는 시각이 문제 해결의 열쇠였습니다. 귀사가 추진 중인 건식 전극 양산 "
                  "프로젝트는 제가 파일럿 단계에서 쌓은 경험을 가장 크게 살릴 수 있는 무대라고 생각해 지원하게 되었습니다."),
                H(2, "성장 과정과 일하는 방식"),
                P("부산에서 자라 화학공학을 전공하며, 데이터로 설득하는 습관을 길렀습니다. 대성배터리에서 처음 맡은 노칭 불량 과제에서 "
                  "현장 작업자분들의 기록을 매일 함께 정리하며 원인을 찾았고, 그 경험 덕분에 지금도 문제를 정의할 때 현장 데이터부터 "
                  "확인합니다. 회의에서는 결론과 근거, 남은 위험을 한 장으로 정리해 공유하는 것을 원칙으로 삼고 있습니다."),
                H(2, "입사 후 포부"),
                P("입사 후 1년 안에 건식 전극 양산 라인의 공정 조건 표준을 확정하고, 3년 안에 셀 제조 원가를 10% 이상 낮추는 공정 "
                  "혁신 과제를 주도하고 싶습니다. 또한 일본·독일 설비 업체와의 협업 경험을 바탕으로 해외 공장 이관에도 기여하겠습니다."),
                H(2, "협업과 리더십 경험"),
                P("건식 전극 파일럿 라인 구축 당시 설비 업체, 품질팀, 생산팀이 서로 다른 일정을 고집해 셋업이 지연될 위기가 있었습니다. "
                  "저는 주간 통합 회의를 만들고 모든 쟁점을 하나의 이슈 목록으로 관리해, 결정이 필요한 항목을 매주 금요일까지 정리했습니다. "
                  "그 결과 세 부서가 같은 우선순위를 보게 되었고, 최종 셋업을 계획보다 열흘 앞당길 수 있었습니다."),
                box("sidebar", "희망 연봉: 회사 내규에 따름 · 입사 가능일: 2026년 11월 1일 · 근무지: 청주 및 오창 가능", title="기타 사항"),
                P("위의 기재 사항은 사실과 다름이 없음을 확인합니다."),
                P("2026년 9월 14일\n지원자 박서연 (인)", "right"),
            ],
        ],
    }


def cv_el() -> dict[str, Any]:
    """Βιογραφικό σημείωμα πολιτικού μηχανικού (ReportLab, 3 pages)."""
    return {
        "template": "resume", "page_size": "A4", "languages": ["el-GR", "en"],
        "metadata": {"title": "Βιογραφικό σημείωμα – Ελένη Καραγιάννη", "author": "Ελένη Καραγιάννη", "subject": "Πολιτική μηχανικός, BIM coordinator",
                     "keywords": ["βιογραφικό", "πολιτικός μηχανικός", "BIM", "Revit"], "lang": "el-GR", "created": "2026-07-30T08:00:00Z"},
        "theme": {"accent": "#1d5f8c", "rl_size": 10.9},
        "running_header": "Ελένη Καραγιάννη – Βιογραφικό σημείωμα",
        "running_footer": "Σελίδα {page} από {pages}",
        "pages": [
            [
                group([P("Ελένη Καραγιάννη", "brand"),
                       P("Λεωφ. Βασιλίσσης Όλγας 142, 546 45 Θεσσαλονίκη\nΤηλ.: +30 694 555 2187\neleni.karagianni@mail.example", "small right")], "letterhead"),
                P("Πολιτική Μηχανικός Δ.Π.Θ., M.Sc. · BIM Coordinator · Μέλος ΤΕΕ (Α.Μ. 148237)", "lead"),
                H(2, "Προφίλ"),
                P("Πολιτική μηχανικός με εννέα χρόνια εμπειρίας στον στατικό σχεδιασμό κτιρίων από οπλισμένο σκυρόδεμα και στον συντονισμό "
                  "έργων με τη μεθοδολογία BIM. Έχω εργαστεί σε δημόσια και ιδιωτικά έργα στην Ελλάδα και την Κύπρο, από σχολικά "
                  "κτίρια έως ξενοδοχειακές μονάδες, και έχω οργανώσει ροές εργασίας κατά ISO 19650 για ομάδες έως 25 ατόμων."),
                group([group([H(2, "Δεξιότητες"),
                              L(["Autodesk Revit, Navisworks, AutoCAD", "SAP2000, ETABS, SOFiSTiK", "Dynamo και Python scripting",
                                 "Ευρωκώδικες EC2, EC8, ΚΑΝ.ΕΠΕ.", "ISO 19650, IFC, BCF", "Primavera P6, MS Project"])]),
                       group([H(2, "Γλώσσες"),
                              L(["Ελληνικά – μητρική", "Αγγλικά – άριστα (C2, Proficiency)", "Γερμανικά – πολύ καλά (B2, Goethe-Zertifikat)",
                                 "Ιταλικά – βασικά (A2)"])])], "split"),
                H(2, "Επαγγελματική εμπειρία"),
                H(3, "BIM Coordinator – Δομοτεχνική Βορείου Ελλάδος Α.Ε., Θεσσαλονίκη"),
                P("*Μάρτιος 2021 – σήμερα*", "small"),
                L(["Συντονισμός μοντέλων αρχιτεκτονικής, στατικής και Η/Μ μελέτης για 11 έργα συνολικού προϋπολογισμού 96 εκατ. €.",
                   "Σύνταξη BIM Execution Plan (BEP) και προτύπων ονοματολογίας για όλη την εταιρεία· εκπαίδευση 18 μηχανικών.",
                   "Clash detection στο Navisworks: μείωση των αλλαγών κατά την κατασκευή κατά 35 % στο νέο 2ο ΕΠΑΛ Καλαμαριάς.",
                   "Ανάπτυξη εργαλείων Dynamo για αυτόματη εξαγωγή ποσοτήτων οπλισμού (BBS) σε Excel.",
                   "Επικοινωνία με τον Κτηματικό και Πολεοδομικό φορέα για την έκδοση αδειών μέσω e-Άδειες."]),
            ],
            [
                H(3, "Στατικός μηχανικός – Λαμπρόπουλος & Συνεργάτες, Λευκωσία (Κύπρος)"),
                P("*Σεπτέμβριος 2018 – Φεβρουάριος 2021*", "small"),
                L(["Στατική μελέτη ξενοδοχείου 7 ορόφων (184 δωμάτια) στη Λεμεσό με σεισμική μόνωση βάσης (lead-rubber bearings).",
                   "Αποτίμηση και ενίσχυση υφιστάμενων κτιρίων κατά ΚΑΝ.ΕΠΕ. και EN 1998-3 με μανδύες και ινοπλισμένα πολυμερή (FRP).",
                   "Επίβλεψη κατασκευής και έλεγχοι ποιότητας σκυροδέματος (C30/37, δοκίμια 28 ημερών)."]),
                H(3, "Μηχανικός μελετών – Τεχνική Εταιρεία «Αξών» Ε.Π.Ε., Ξάνθη"),
                P("*Ιούλιος 2016 – Αύγουστος 2018*", "small"),
                L(["Σχέδια ξυλοτύπων και οπλισμών σε AutoCAD για κατοικίες και αγροτικές αποθήκες.",
                   "Προμετρήσεις και τεύχη δημοπράτησης για δήμους της Περιφέρειας Ανατολικής Μακεδονίας και Θράκης."]),
                H(2, "Εκπαίδευση"),
                table("spoudes", [["Περίοδος", "Τίτλος", "Ίδρυμα", "Βαθμός"],
                                  ["2016 – 2018", "M.Sc. Αντισεισμικός Σχεδιασμός Κατασκευών", "Αριστοτέλειο Πανεπιστήμιο Θεσσαλονίκης", "9,1/10"],
                                  ["2010 – 2016", "Δίπλωμα Πολιτικού Μηχανικού (5ετές, integrated master)", "Δημοκρίτειο Πανεπιστήμιο Θράκης", "8,2/10"],
                                  ["2014", "Erasmus+, Structural Engineering", "Technische Universität München", "–"]],
                      caption="", widths=[14, 36, 38, 12], align=["l", "l", "l", "r"]),
                H(2, "Πιστοποιήσεις"),
                L(["Autodesk Certified Professional: Revit for Structural Design (2022)",
                   "buildingSMART Professional Certification – Foundation (2023)",
                   "PRINCE2® Foundation, AXELOS (2024)"]),
                box("sidebar", "Διπλωματική M.Sc.: «Σεισμική απόκριση πλαισίων Ο/Σ με τοιχοπληρώσεις: σύγκριση μη γραμμικών "
                    "στατικών και δυναμικών αναλύσεων» – επιβλέπων καθ. Α. Παπαδόπουλος. Βραβείο αριστείας ΤΕΕ/ΤΚΜ 2018.", title="Ερευνητική εργασία"),
            ],
            [
                H(2, "Επιλεγμένα έργα"),
                table("erga", [["Έτος", "Έργο", "Ρόλος", "Προϋπολογισμός"],
                               ["2025", "Νέο 2ο ΕΠΑΛ Καλαμαριάς (ΣΔΙΤ), 7.800 m²", "BIM Coordinator", "14,2 εκατ. €"],
                               ["2024", "Επέκταση εργοστασίου τροφίμων, Σίνδος", "BIM Coordinator", "9,6 εκατ. €"],
                               ["2023", "Ενεργειακή αναβάθμιση 6 σχολείων, Δήμος Νεάπολης-Συκεών", "Στατική μελέτη / BIM", "3,4 εκατ. €"],
                               ["2020", "Ξενοδοχείο «Amathus Bay», Λεμεσός", "Στατικός μηχανικός", "21,5 εκατ. €"],
                               ["2019", "Ενίσχυση διατηρητέου κτιρίου, Λευκωσία", "Στατικός μηχανικός", "1,1 εκατ. €"]],
                      caption="Πίνακας 1. Ενδεικτικά έργα", widths=[9, 47, 24, 20], align=["l", "l", "l", "r"]),
                H(2, "Δημοσιεύσεις"),
                L(["Καραγιάννη, Ε., Παπαδόπουλος, Α. (2019). «Επιρροή των τοιχοπληρώσεων στη σεισμική απόκριση πλαισίων». "
                   "*Πρακτικά 18ου Συνεδρίου Σκυροδέματος ΤΕΕ*, Αθήνα.",
                   "Karagianni, E. (2024). “Automating rebar schedules with Dynamo: a case study from Greek public schools.” "
                   "*BIM World Munich*, poster session."]),
                H(2, "Εθελοντική δράση"),
                P("Μέλος της ομάδας ταχείας αυτοψίας του ΤΕΕ/ΤΚΜ μετά τον σεισμό της Σάμου (2020) – έλεγχος 64 κτιρίων σε τρεις ημέρες. "
                  "Μέντορας στο πρόγραμμα «Women in Engineering» του Α.Π.Θ. από το 2022."),
                H(2, "Συστάσεις"),
                group([P("**Δρ Αντώνης Παπαδόπουλος**\nΚαθηγητής, Τμήμα Πολιτικών Μηχανικών Α.Π.Θ.\napapad@civil.auth.example"),
                       P("**Νίκος Λαμπρόπουλος**\nΔιευθυντής, Λαμπρόπουλος & Συνεργάτες\nn.lampropoulos@lamp-eng.example")], "split"),
                P("Θεσσαλονίκη, 30 Ιουλίου 2026", "right"),
            ],
        ],
    }



# ================================================================ meeting minutes


def vote(label: str, ayes: int, nays: int, abstain: int, absent: int, total: int) -> tuple[str, dict[str, Any]]:
    """Vote tally sentence plus its arithmetic check (ayes + nays + abstentions + absent = members)."""
    text = f"{label} Ayes {ayes}, Nays {nays}, Abstain {abstain}, Absent {absent} (of {total} members)."
    return text, {"kind": "sum", "terms": [["+", str(ayes)], ["+", str(nays)], ["+", str(abstain)], ["+", str(absent)]], "equals": str(total)}


def minutes_en() -> dict[str, Any]:
    """City council regular meeting minutes (LibreOffice, untagged, 5 pages)."""
    checks: list[dict[str, Any]] = []

    def motion(text: str, ayes: int, nays: int, abstain: int, absent: int) -> dict[str, Any]:
        sentence, check = vote("**Vote:**", ayes, nays, abstain, absent, 7)
        checks.append(check)
        return P(f"{text} {sentence}")

    budget_rows = [["Fund / line", "Adopted FY2027", "Amendment", "Revised FY2027"],
                   ["General Fund — Public Works", "4,812,500", "+186,000", "4,998,500"],
                   ["General Fund — Parks & Recreation", "2,240,000", "+64,500", "2,304,500"],
                   ["Transit Fund — Route 4 pilot", "0", "+318,000", "318,000"],
                   ["Capital — Aspen Ave streetscape", "1,150,000", "+92,000", "1,242,000"],
                   ["Reserves (unassigned)", "3,075,000", "−660,500", "2,414,500"],
                   ["Net change", "", "0", ""]]
    sheet = screenshot("s1", "spreadsheet", {"title": "FY2027 Budget Amendment No. 1 — Finance Dept.xlsx", "menu": ["File", "Edit", "View", "Insert", "Format", "Data", "Help"],
                                              "cell": "C7", "formula": "=SUM(C2:C6)", "tabs": ["Amendment 1", "Revenue", "Notes"], "rows": budget_rows,
                                              "numeric": [False, True, True, True], "selected_row": 7, "width": 760},
                       "Exhibit B (as presented): FY2027 Budget Amendment No. 1, screenshot from the Finance Department slide deck", width_cm=15.5)
    actions = [["A-26-41", "Publish adopted sidewalk café ordinance and fee schedule", "City Clerk (D. Ferreira)", "Oct 9, 2026", "Done"],
               ["A-26-42", "Issue RFP for Route 4 shuttle operator", "Transit Mgr (K. Oyelaran-Hart)", "Oct 23, 2026", "In progress"],
               ["A-26-43", "Post Budget Amendment No. 1 to transparency portal", "Finance Dir. (R. Castellanos)", "Oct 10, 2026", "Done"],
               ["A-26-44", "Schedule community meeting on Tamarack St. crosswalk", "Public Works (J. Lindqvist)", "Oct 30, 2026", "Open"],
               ["A-26-45", "Return with options for snow-removal contract", "Public Works (J. Lindqvist)", "Nov 5, 2026", "Open"],
               ["A-26-46", "Translate parking notices into Spanish and Vietnamese", "Communications (T. Nguyễn)", "Oct 31, 2026", "In progress"],
               ["A-26-47", "Report on library Sunday hours pilot usage", "Library Dir. (M. Haddad)", "Nov 5, 2026", "Open"],
               ["A-26-48", "Draft letter of support for CDOT Safe Routes grant", "City Manager (A. Brennan)", "Oct 16, 2026", "Done"],
               ["A-26-49", "Update council rules of procedure for hybrid meetings", "City Attorney (L. Moreau)", "Nov 19, 2026", "Open"],
               ["A-26-50", "Inventory city-owned EV chargers and uptime", "Fleet (B. Okonkwo)", "Dec 3, 2026", "Open"],
               ["A-26-51", "Send thank-you letters to Harvest Fest volunteers", "Mayor’s Office", "Oct 15, 2026", "Done"]]
    action_segments = continued("actions", [["No.", "Action", "Owner", "Due", "Status"]], actions, [5, 6],
                                caption="Action items arising from this meeting", continued_caption="Action items (continued)",
                                widths=[11, 41, 24, 13, 11])
    return {
        "template": "meeting_minutes", "page_size": "Letter", "languages": ["en-US", "es", "vi"], "tagged": False,
        "metadata": {"title": "Minutes of the Regular Meeting of the Larkspur Falls City Council, October 6, 2026", "author": "Office of the City Clerk, City of Larkspur Falls",
                     "subject": "City council regular meeting minutes", "keywords": ["city council", "minutes", "budget amendment", "sidewalk café"], "lang": "en-US",
                     "created": "2026-10-08T21:10:00Z"},
        "theme": {"accent": "#1d4a6e", "lo_size": "10.5pt", "lo_font": "Noto Sans"},
        "running_header": "Larkspur Falls City Council — Regular Meeting — October 6, 2026",
        "running_footer": "Approved minutes are the official record. Page {page} of {pages}",
        "arithmetic": checks,
        "pages": [
            [
                H(1, "Minutes of the Regular Meeting of the City Council"),
                P("City of Larkspur Falls, Colorado · Tuesday, October 6, 2026, 6:00 p.m. · Council Chambers, 410 Aspen Civic Plaza, and via livestream", "meta"),
                H(2, "1. Call to order and roll call"),
                P("Mayor Eleanor Whitcombe called the meeting to order at 6:02 p.m. and led the Pledge of Allegiance. City Clerk Daniela "
                  "Ferreira called the roll."),
                P("**Present:** Mayor Eleanor Whitcombe; Mayor Pro Tem Sofía Ibarra-Núñez; Councilmembers Nguyễn Thị Lan, Tomasz "
                  "Kowalczyk, Adebayo Oyelaran, and Hannah Strand-Eriksen (remote, Ward 3)."),
                P("**Absent:** Councilmember Robert “Bobby” Delacroix (excused, family medical leave)."),
                P("**Staff present:** City Manager Aidan Brennan; City Attorney Louise Moreau; Finance Director Rafael Castellanos; Public "
                  "Works Director Johan Lindqvist; Transit Manager Kemi Oyelaran-Hart¹; City Clerk Daniela Ferreira."),
                H(2, "2. Approval of the agenda"),
                motion("Councilmember Kowalczyk moved to approve the agenda with item 7 (executive session) moved to the end; seconded by "
                       "Councilmember Nguyễn. Motion carried.", 6, 0, 0, 1),
                H(2, "3. Public comment on items not on the agenda"),
                P("Five residents spoke. Marisol Pérez (Tamarack Street) asked for a marked crosswalk near Sage Elementary and presented a "
                  "petition with 212 signatures. Dwight Abernathy objected to the new parking time limits on Aspen Avenue. Trần Văn Minh, "
                  "owner of Pho Larkspur, asked that parking notices be translated into Vietnamese. Two speakers thanked staff for the "
                  "Harvest Fest cleanup. The Mayor referred the crosswalk request to Public Works (see action A-26-44)."),
                H(2, "4. Consent calendar"),
                L(["Minutes of the regular meeting of September 15, 2026", "Warrant register for September 2026 ($2,861,402.17)",
                   "Resolution 26-58 accepting a $45,000 Colorado Main Street mini-grant", "Renewal of the janitorial services contract with BrightPath Facility Services"], ordered=True),
                motion("Mayor Pro Tem Ibarra-Núñez moved to approve the consent calendar; seconded by Councilmember Strand-Eriksen. Motion carried.", 6, 0, 0, 1),
                box("footnote", "¹ Transit Manager Kemi Oyelaran-Hart is not related to Councilmember Adebayo Oyelaran; disclosed for the record at the Councilmember’s request."),
            ],
            [
                H(2, "5. Public hearing: Ordinance 26-14, sidewalk cafés on Aspen Avenue (second reading)"),
                P("The Mayor opened the public hearing at 6:31 p.m. Community Development staff summarized the ordinance: permits for up to "
                  "six tables per frontage, a minimum clear pedestrian path of six feet, seasonal operation from April 1 to October 31, and "
                  "a fee of $18.00 per table per season. The Downtown Business Association supports the ordinance."),
                P("Public testimony: Aiko Hoshino (Hoshino Ramen) supported the ordinance and asked for winter operation with heaters; "
                  "Grace Whitfield (Accessible Larkspur) asked that the six-foot path be measured from the curb, not from the tree grates; "
                  "Marco Bellandi supported the ordinance. The hearing was closed at 6:52 p.m."),
                P("Council discussion focused on accessibility. Councilmember Oyelaran proposed an amendment requiring the clear path to "
                  "be measured from the outer edge of tree grates and street furniture; the City Attorney confirmed the amendment is not "
                  "substantive and does not require a new first reading."),
                motion("Councilmember Oyelaran moved to amend Section 3(b) as described; seconded by Councilmember Nguyễn. Amendment carried.", 6, 0, 0, 1),
                motion("Councilmember Kowalczyk moved to adopt Ordinance 26-14 as amended; seconded by Mayor Pro Tem Ibarra-Núñez. Motion carried.", 5, 1, 0, 1),
                P("Councilmember Strand-Eriksen voted no, stating that winter operation should be considered before adoption."),
                photo("p1", ["city-street"], ["street", "civic"], {"city-street": "Aspen Avenue frontage proposed for sidewalk café permits (staff photo, September 2026)"},
                      "Aspen Avenue frontage", wrap="none", width_cm=11.0),
            ],
            [
                H(2, "6. FY2027 Budget Amendment No. 1"),
                P("Finance Director Castellanos presented Budget Amendment No. 1 (Exhibit B). The amendment appropriates $660,500 from "
                  "unassigned reserves for storm-drain repairs, extended park maintenance, the Route 4 shuttle pilot and the Aspen Avenue "
                  "streetscape. Reserves remain at 21.4% of General Fund expenditures, above the 17% policy minimum."),
                sheet,
                table("budget", budget_rows, rendering="screenshot", caption="FY2027 Budget Amendment No. 1 (Exhibit B)"),
                P("Councilmember Kowalczyk asked whether the Route 4 pilot would continue after June 2027. The City Manager answered that "
                  "the pilot is limited to nine months and will be evaluated against ridership targets of 120 boardings per weekday. "
                  "Councilmember Nguyễn requested that the evaluation include surveys in Spanish and Vietnamese."),
                motion("Mayor Pro Tem Ibarra-Núñez moved to adopt Resolution 26-59 approving Budget Amendment No. 1; seconded by "
                       "Councilmember Oyelaran. Motion carried.", 5, 0, 1, 1),
                P("Councilmember Kowalczyk abstained, citing his employment with a firm that may bid on the streetscape contract."),
            ],
            [
                H(2, "7. Route 4 shuttle pilot — staff report"),
                P("Transit Manager Oyelaran-Hart reported that the pilot will connect the Larkspur Falls Park-and-Ride, Aspen Avenue, the "
                  "regional hospital and the community college every 30 minutes on weekdays from 6:30 a.m. to 7:30 p.m. Fares will be free "
                  "for the first three months. The operator will be selected through an RFP issued this month."),
                P("Council directed staff to report ridership monthly and to coordinate with the school district on bell times."),
                H(2, "8. Council and staff reports"),
                L(["Mayor Whitcombe reported on the Front Range mayors’ meeting on wildfire mitigation funding.",
                   "Councilmember Nguyễn announced a Vietnamese-language small-business workshop on October 24 at the library.",
                   "The City Manager reported that the library Sunday hours pilot averaged 186 visitors per Sunday in September.",
                   "Public Works reported that leaf collection begins October 19; schedules are online and in the utility bill insert."]),
                H(2, "9. Action items"),
                *action_segments[:1],
            ],
            [
                *action_segments[1:],
                H(2, "10. Executive session"),
                motion("At 8:14 p.m., Councilmember Strand-Eriksen moved to convene in executive session under C.R.S. § 24-6-402(4)(e) to "
                       "discuss negotiations regarding the snow-removal contract; seconded by Councilmember Oyelaran. Motion carried.", 6, 0, 0, 1),
                P("Council reconvened in open session at 8:47 p.m. No action was taken."),
                H(2, "11. Adjournment"),
                P("There being no further business, Mayor Whitcombe adjourned the meeting at 8:49 p.m. The next regular meeting is "
                  "scheduled for Tuesday, October 20, 2026, at 6:00 p.m. in Council Chambers."),
                P("Respectfully submitted,\n\nDaniela Ferreira, CMC\nCity Clerk"),
                P("Approved by the City Council on October 20, 2026.\n\nEleanor Whitcombe, Mayor"),
                box("callout", "Video of this meeting is available at [larkspurfalls.example/council](https://larkspurfalls.example/council). "
                    "Written public comments received before 3:00 p.m. on the meeting day are attached as Exhibit D.", title="Public record", cls="note"),
            ],
        ],
    }


def minutes_zhcn() -> dict[str, Any]:
    """董事会会议纪要（LibreOffice, tagged, 5 pages）."""
    checks: list[dict[str, Any]] = []

    def biaojue(text: str, yes: int, no: int, abstain: int) -> dict[str, Any]:
        checks.append({"kind": "sum", "terms": [["+", str(yes)], ["+", str(no)], ["+", str(abstain)]], "equals": "7"})
        return P(f"{text}表决结果：同意{yes}票，反对{no}票，弃权{abstain}票（应参加表决董事7名）。")

    spec = {"title": "季度营业收入（万元）", "categories": ["2025Q3", "2025Q4", "2026Q1", "2026Q2", "2026Q3"],
            "series": [("营业收入", [18640, 21310, 17980, 22450, 24870]), ("其中：新能源客户", [6120, 7830, 7210, 9960, 11840])],
            "max": 30000, "ticks": 3, "tick_format": lambda v: number(v, "zh", 0)}
    tasks = [["1", "完成二期产线设备招标文件并挂网", "设备部 刘建国", "10月25日", "进行中"],
             ["2", "向银行提交项目贷款申请材料", "财务部 王丽娟", "10月31日", "进行中"],
             ["3", "制定应收账款专项清收方案", "财务部 王丽娟", "10月20日", "已完成"],
             ["4", "完成IATF 16949监督审核整改", "质量部 赵敏", "11月15日", "未开始"],
             ["5", "修订安全生产责任制并组织考核", "安环部 孙志强", "11月30日", "进行中"],
             ["6", "提交2027年度预算编制指引", "财务部 王丽娟", "11月10日", "未开始"],
             ["7", "完成股权激励计划第二期行权名单核对", "董事会办公室 陈思远", "10月28日", "进行中"],
             ["8", "与江苏客户签订年度框架协议", "销售部 周海涛", "11月20日", "进行中"],
             ["9", "研发中心搬迁方案报董事长审批", "研发中心 何晓峰", "11月5日", "未开始"],
             ["10", "披露第三季度报告", "董事会办公室 陈思远", "10月30日", "已完成"]]
    seg = continued("renwu", [["序号", "工作事项", "责任部门及负责人", "完成时限", "状态"]], tasks, [5, 5],
                    caption="表2　会议决定事项督办清单", continued_caption="表2　会议决定事项督办清单（续）", widths=[7, 43, 24, 13, 13])
    return {
        "template": "meeting_minutes", "page_size": "A4", "languages": ["zh-CN", "en"], "tagged": True,
        "metadata": {"title": "上海浦江新材料股份有限公司第三届董事会第九次会议纪要", "author": "上海浦江新材料股份有限公司董事会办公室",
                     "subject": "董事会会议纪要", "keywords": ["董事会", "会议纪要", "表决", "督办"], "lang": "zh-CN", "created": "2026-10-16T08:00:00Z"},
        "theme": {"accent": "#a12a2a", "lo_size": "11.5pt"},
        "running_header": "上海浦江新材料股份有限公司　第三届董事会第九次会议纪要",
        "running_footer": "第 {page} 页／共 {pages} 页　内部资料，注意保密",
        "arithmetic": [*checks, {"kind": "sum", "terms": [["+", "17,980"], ["+", "22,450"], ["+", "24,870"]], "equals": "65,300"}],
        "pages": [
            [
                H(1, "第三届董事会第九次会议纪要"),
                P("会议时间：2026年10月15日（星期四）14:00—17:20\n会议地点：公司总部三楼第一会议室（上海市闵行区紫星路588号），同时采用视频方式\n"
                  "会议召集人及主持人：董事长　张国华　　记录人：董事会秘书　陈思远", "meta"),
                H(2, "一、出席及列席情况"),
                P("本次会议应出席董事7名，实际出席董事7名，其中以视频方式出席2名（独立董事李明哲、独立董事 Margaret Lin 林美华）。"
                  "公司监事会主席黄建平、财务总监王丽娟、副总经理周海涛列席会议。会议的召集、召开程序符合《公司法》和《公司章程》的规定。"),
                table("chuxi", [["姓名", "职务", "出席方式"],
                                ["张国华", "董事长", "现场"], ["吴卫东", "董事、总经理", "现场"], ["郑佳", "董事", "现场"],
                                ["马骏", "董事（股东代表）", "现场"], ["许文清", "董事", "现场"],
                                ["李明哲", "独立董事", "视频"], ["Margaret Lin 林美华", "独立董事", "视频"]],
                      caption="表1　董事出席情况", widths=[30, 40, 30]),
                H(2, "二、会议议程"),
                L(["审议《2026年第三季度报告》", "审议《关于投资建设二期年产3万吨电池级导电浆料项目的议案》",
                   "审议《关于向银行申请综合授信额度的议案》", "听取总经理关于安全生产和质量体系情况的汇报", "其他事项"], ordered=True),
            ],
            [
                H(2, "三、议题讨论及决议"),
                H(3, "（一）2026年第三季度报告"),
                P("财务总监王丽娟汇报了第三季度经营情况：第三季度实现营业收入24,870万元，环比增长10.8%；前三季度累计营业收入65,300万元，"
                  "同比增长14.2%。来自新能源客户的收入占比提升至47.6%。应收账款余额较年初增加较多，主要集中在两家整车企业。"),
                chart("f1", "bar", spec, "图1　近五个季度营业收入", raster=True, width_cm=14.0),
                chart_table("c1", "季度", spec, lambda v: number(v, "zh", 0)),
                P("独立董事李明哲提出，应收账款周转天数已由62天增加至78天，建议管理层制定专项清收方案并在下次会议上报告。"
                  "董事马骏建议在季度报告中补充说明主要客户集中度风险。"),
                biaojue("经审议，会议通过该议案。", 7, 0, 0),
            ],
            [
                H(3, "（二）投资建设二期年产3万吨电池级导电浆料项目"),
                P("总经理吴卫东介绍了项目可行性研究报告：项目选址于公司嘉兴生产基地，总投资约4.86亿元，其中设备投资3.12亿元，"
                  "建设期18个月，预计达产后年均新增营业收入9.6亿元，税后内部收益率15.3%，静态投资回收期6.2年（含建设期）。"),
                P("董事郑佳关注碳纳米管原材料价格波动对项目收益的影响，要求补充敏感性分析。独立董事 Margaret Lin 林美华认为项目与公司"
                  "战略一致，但建议分两阶段投入设备，以降低下游需求不及预期的风险。董事许文清对项目的资金来源提出疑问，财务总监答复"
                  "拟以自有资金约1.5亿元和银行项目贷款约3.36亿元解决。"),
                biaojue("经审议，会议同意该项目分两阶段实施，并授权管理层办理立项、环评及土地等相关手续。", 6, 0, 1),
                P("董事许文清投弃权票，理由是希望在银行授信落实后再作决定。"),
                H(3, "（三）向银行申请综合授信额度"),
                P("为满足生产经营和项目建设的资金需求，公司拟向中国工商银行、招商银行等金融机构申请合计不超过人民币8亿元的综合授信额度，"
                  "期限一年，授信品种包括流动资金贷款、项目贷款、银行承兑汇票等。"),
                biaojue("经审议，会议通过该议案，该议案尚需提交股东大会审议。", 7, 0, 0),
                box("callout", "根据《公司章程》第一百一十条，对外投资金额超过最近一期经审计净资产10%的事项，应当在董事会审议通过后提交股东大会审议。",
                    title="董事会秘书提示", cls="note"),
            ],
            [
                H(3, "（四）安全生产和质量体系情况汇报"),
                P("吴卫东总经理汇报：前三季度未发生一般及以上生产安全事故；嘉兴基地完成了危险化学品仓库的智能监控改造。"
                  "IATF 16949 监督审核中发现一般不符合项3项，已制定整改计划。董事会要求安全生产责任制修订后组织全员考核。"),
                H(3, "（五）其他事项"),
                P("董事会秘书陈思远通报了股权激励计划第二期行权安排及第三季度报告的披露时间（10月30日）。会议同意下一次定期会议于"
                  "2027年1月中旬召开，审议年度经营计划和预算。"),
                H(2, "四、会议决定事项督办"),
                P("会议要求董事会办公室对以下事项进行督办，各责任部门于每月5日前报送进展情况："),
                *seg[:1],
            ],
            [
                *seg[1:],
                H(2, "五、其他说明"),
                P("本纪要经与会董事审阅确认后存档。董事对纪要内容有异议的，应在收到纪要之日起三个工作日内书面提出。"),
                P("出席会议董事签字：\n张国华　　吴卫东　　郑佳　　马骏　　许文清　　李明哲　　Margaret Lin 林美华"),
                P("记录人：陈思远\n2026年10月16日", "right"),
                P("抄送：公司监事会、经营管理层、各部门负责人", "small"),
            ],
        ],
    }



def minutes_tr() -> dict[str, Any]:
    """Site kat malikleri kurulu toplantı tutanağı (Chromium, 4 pages)."""
    checks: list[dict[str, Any]] = []

    def oylama(text: str, kabul: int, ret: int, cekimser: int) -> dict[str, Any]:
        checks.append({"kind": "sum", "terms": [["+", str(kabul)], ["+", str(ret)], ["+", str(cekimser)]], "equals": "48"})
        return P(f"{text} **Oylama:** {kabul} kabul, {ret} ret, {cekimser} çekimser (toplantıda temsil edilen 48 bağımsız bölüm).")

    kalemler = [("Özel güvenlik hizmeti (3 personel, 7/24)", 115200000), ("Temizlik hizmeti (2 personel)", 48600000),
                ("Bahçe ve peyzaj bakımı", 21480000), ("Ortak alan elektrik ve su", 26840000), ("Asansör bakım sözleşmesi (8 asansör)", 9600000),
                ("Havuz bakımı ve kimyasallar", 13250000), ("Profesyonel yönetim hizmeti", 18000000), ("Bina sigortası (ortak alanlar)", 7430000),
                ("Yedek akçe", 12000000)]
    toplam = sum(v for _, v in kalemler)
    butce = table("butce", [["Gider kalemi", "2027 tahmini (₺)"], *[[k, money(v, "tr")] for k, v in kalemler], ["Toplam", money(toplam, "tr")]],
                  caption="Tablo 1. 2027 yılı işletme bütçesi", align=["l", "r"], widths=[70, 30], total_rows=[len(kalemler) + 1])
    aidat = toplam // 64 // 12
    spec = {"title": "Aylık aidat tahsilat oranı (%)", "categories": ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl"],
            "series": [("2026", [91, 88, 93, 95, 90, 84, 79, 82, 94]), ("2025", [86, 85, 89, 90, 88, 81, 76, 80, 89])],
            "min": 60, "max": 100, "ticks": 4, "tick_format": lambda v: f"%{number(v, 'tr', 0)}"}
    gorevler = [["1", "Asansör firmasıyla yeni bakım sözleşmesinin imzalanması", "Yönetim Kurulu Başkanı (S. Aydın)", "31.10.2026", "Devam ediyor"],
                ["2", "B blok çatı izolasyonu için üç teklif alınması", "Denetçi (M. Çelik)", "15.11.2026", "Açık"],
                ["3", "Aidat borcu 3 ayı geçen malikler için ihtarname gönderilmesi", "Site Müdürü (E. Kılıç)", "20.10.2026", "Tamamlandı"],
                ["4", "Havuz kullanım kurallarının panolara asılması", "Site Müdürü (E. Kılıç)", "01.11.2026", "Açık"],
                ["5", "Otopark plakalı giriş sisteminin keşfi", "Üye (H. Öztürk)", "30.11.2026", "Açık"],
                ["6", "Elektrikli araç şarj ünitesi için elektrik projesinin hazırlatılması", "Üye (D. Arslan)", "15.12.2026", "Açık"],
                ["7", "Bahçe sulama sisteminin kış bakımı", "Peyzaj firması / Site Müdürü", "10.11.2026", "Devam ediyor"],
                ["8", "Yeni işletme projesinin tüm maliklere tebliği", "Yönetim Kurulu", "25.10.2026", "Tamamlandı"],
                ["9", "Kamera sistemi KVKK aydınlatma metninin güncellenmesi", "Avukat (Av. Z. Yalçın)", "30.11.2026", "Açık"]]
    seg = continued("gorevler", [["No", "Görev", "Sorumlu", "Termin", "Durum"]], gorevler, [4, 5], caption="Tablo 2. Görev ve takip listesi",
                    continued_caption="Tablo 2. Görev ve takip listesi (devam)", widths=[6, 44, 25, 12, 13])
    chat_spec = {"channel": "Lale Bahçe Sitesi – Sakinler", "topic": "Duyurular ve arıza bildirimleri · 214 üye", "height": 330,
                 "messages": [("Ayşe Demirtaş (C-12)", "08:14", "Günaydın, C blok asansörü yine 4. katta kaldı. Bu ay üçüncü kez!"),
                              ("Emre Kılıç – Site Müdürü", "08:21", "Bildirim için teşekkürler. Firmayı aradım, teknisyen 10:00 gibi gelecek."),
                              ("Hakan Öztürk (A-3)", "08:35", "Bakım firması değişsin artık. Genel kurulda gündeme alalım lütfen."),
                              ("Selin Aydın – Yönetim", "09:02", "Teklifler toplandı, 12 Ekim toplantısında oylayacağız. Herkesi bekliyoruz."),
                              ("Nikos Papadakis (B-7)", "09:10", "I will attend too. Can someone share the offers in English?")]}
    return {
        "template": "meeting_minutes", "page_size": "A4", "languages": ["tr-TR", "en"],
        "metadata": {"title": "Lale Bahçe Sitesi Olağan Kat Malikleri Kurulu Toplantı Tutanağı – 12 Ekim 2026", "author": "Lale Bahçe Sitesi Yönetim Kurulu",
                     "subject": "Kat malikleri kurulu toplantı tutanağı", "keywords": ["toplantı tutanağı", "kat malikleri kurulu", "işletme projesi", "aidat"],
                     "lang": "tr-TR", "created": "2026-10-13T11:30:00Z"},
        "theme": {"accent": "#0b6e4f", "font_size": "10.2pt", "body_font": "'Noto Sans'", "margins": "16mm 17mm 18mm 17mm"},
        "running_header": "Lale Bahçe Sitesi – Olağan Kat Malikleri Kurulu – 12.10.2026",
        "running_footer": "Sayfa {page} / {pages} · Divan üyelerince imzalanmıştır",
        "arithmetic": [*checks, {"kind": "column_sum", "table": "butce", "columns": [1], "label_column": 0, "total_label": "Toplam"}],
        "pages": [
            [
                H(1, "Olağan Kat Malikleri Kurulu Toplantı Tutanağı"),
                P("Lale Bahçe Sitesi · Çamlık Mah. Menekşe Sok. No: 4, 34771 Ümraniye / İstanbul · Toplantı tarihi: 12 Ekim 2026, saat 19:30 · Yer: Site sosyal tesisi", "meta"),
                H(2, "1. Açılış ve yoklama"),
                P("634 Sayılı Kat Mülkiyeti Kanunu’nun 29. maddesi uyarınca yapılan çağrı üzerine toplanan kurulda, 64 bağımsız bölümden 41’i "
                  "asaleten, 7’si vekâleten olmak üzere 48 bağımsız bölüm temsil edilmiştir. Toplantı nisabının sağlandığı görülerek toplantı "
                  "Yönetim Kurulu Başkanı Selin Aydın tarafından açılmıştır."),
                H(2, "2. Divan heyetinin seçimi"),
                oylama("Divan başkanlığına Av. Zeynep Yalçın (A-9), yazmanlığa Mert Çelik (B-14) önerilmiştir.", 46, 0, 2),
                H(2, "3. Gündem"),
                L(["Yönetim kurulu faaliyet raporunun okunması ve ibrası", "Denetim raporunun okunması",
                   "Asansör bakım firmasının değiştirilmesi", "2027 yılı işletme projesi ve aidat tutarının belirlenmesi",
                   "Elektrikli araç şarj ünitesi kurulması", "Dilek ve temenniler"], ordered=True),
                H(2, "4. Faaliyet raporu ve denetim raporu"),
                P("Yönetim Kurulu Başkanı Selin Aydın, 2026 yılında yapılan işleri özetledi: çocuk oyun alanının zemini kauçukla yenilendi, "
                  "otopark aydınlatması LED’e dönüştürüldü (yıllık yaklaşık %38 tasarruf), A blok çatı yağmur olukları onarıldı. Denetçi Mert "
                  "Çelik, hesapların düzenli tutulduğunu, ancak aidat tahsilatının yaz aylarında düştüğünü belirtti."),
                chart("f1", "line", spec, "Şekil 1. 2025 ve 2026 yıllarında aylık aidat tahsilat oranları", raster=False, width="82%", size=(560, 230)),
                chart_table("c1", "Ay", spec, lambda v: f"%{number(v, 'tr', 0)}"),
                oylama("Yönetim kurulunun ibrası oya sunulmuştur.", 41, 3, 4),
            ],
            [
                H(2, "5. Asansör bakım firmasının değiştirilmesi"),
                P("Son üç ayda C blok asansöründe yedi arıza kaydı oluştuğu, sakinlerin şikâyetlerinin site WhatsApp grubunda yoğunlaştığı "
                  "belirtilmiştir. Yönetim, grupta paylaşılan mesajların bir ekran görüntüsünü bilgi amacıyla tutanağa eklemiştir:"),
                screenshot("s1", "chat", chat_spec, "Ek 1. Site sakinleri WhatsApp grubundan ekran görüntüsü (9 Ekim 2026)", width="74%", width_cm=12.0),
                P("Üç firmadan alınan teklifler incelenmiş; en düşük teklifi veren Yükselen Asansör Ltd. Şti.’nin aylık 9.600,00 ₺ + KDV "
                  "bedelle, 2 saat içinde arızaya müdahale ve yılda iki ücretsiz parça değişimi taahhüdüyle çalışmasına karar verilmiştir. "
                  "Malik Nikos Papadakis (B-7) için tekliflerin İngilizce özeti hazırlanmasına karar verilmiştir."),
                oylama("Mevcut sözleşmenin feshedilerek Yükselen Asansör ile sözleşme yapılması oya sunulmuştur.", 44, 1, 3),
            ],
            [
                H(2, "6. 2027 yılı işletme projesi"),
                P("Yönetim kurulu tarafından hazırlanan 2027 yılı işletme projesi okunmuştur. Güvenlik ve temizlik hizmetlerinde asgari ücret "
                  "artışı nedeniyle giderlerin önceki yıla göre %31,4 artması öngörülmektedir."),
                butce,
                P(f"Bütçenin 64 bağımsız bölüme eşit dağıtılmasıyla aylık aidat **{money(aidat, 'tr')}** olarak hesaplanmıştır. Havuz giderlerinin "
                  "yalnızca havuz kullanan bloklara yansıtılması önerisi, yönetim planına aykırı olduğu gerekçesiyle reddedilmiştir."),
                oylama("İşletme projesi ve aidat tutarı oya sunulmuştur.", 39, 6, 3),
                H(2, "7. Elektrikli araç şarj ünitesi"),
                P("Otoparka iki adet 22 kW şarj ünitesi kurulması önerilmiştir. Kurulum maliyetinin kullanıcılar tarafından karşılanması ve "
                  "tüketimin kartlı sistemle ölçülmesi şartıyla öneri kabul edilmiştir; elektrik projesi hazırlanacaktır."),
                oylama("Şarj ünitesi kurulumu için ön çalışma yapılması oya sunulmuştur.", 37, 5, 6),
                H(2, "8. Görevler"),
                *seg[:1],
            ],
            [
                *seg[1:],
                H(2, "9. Dilek ve temenniler"),
                L(["Site içinde araç hızının 10 km/s ile sınırlandırılması ve tabelaların yenilenmesi istendi.",
                   "Evcil hayvan sahiplerinin bahçede tasma kullanması konusunda hatırlatma yapılması talep edildi.",
                   "Yaz aylarında havuz saatlerinin 22:00’ye kadar uzatılması önerisi bir sonraki toplantıya bırakıldı.",
                   "Yabancı uyruklu malikler için duyuruların İngilizce de paylaşılması önerildi."]),
                box("callout", "Toplantıya katılmayan malikler, bu tutanağın tebliğinden itibaren bir ay içinde kararlara karşı sulh hukuk "
                    "mahkemesinde iptal davası açabilir (KMK m. 33).", title="Hatırlatma", cls="note"),
                P("Gündemde görüşülecek başka konu kalmadığından toplantı saat 22:10’da kapatılmıştır. İşbu tutanak divan heyeti tarafından "
                  "okunarak imza altına alınmıştır."),
                pair(P("**Divan Başkanı**\nAv. Zeynep Yalçın\n\n_____________________"), P("**Yazman**\nMert Çelik\n\n_____________________")),
            ],
        ],
    }


def minutes_he() -> dict[str, Any]:
    """פרוטוקול ישיבת ועד הורים (pylopdf, RTL, 3 pages)."""
    checks: list[dict[str, Any]] = []
    votes = [("אישור תקציב ועד ההורים לשנת הלימודים", 9, 1, 1), ("בחירת ספק ההסעות לטיול השנתי", 8, 2, 1),
             ("הצטרפות לתוכנית ״בית ספר ירוק״", 11, 0, 0)]
    vote_rows = []
    for subject, yes, no, abstain in votes:
        vote_rows.append([subject, str(yes), str(no), str(abstain), "11"])
        checks.append({"kind": "sum", "terms": [["+", str(yes)], ["+", str(no)], ["+", str(abstain)]], "equals": "11"})
    budget = [("סל תרבות – הצגות ומופעים", 1840000), ("טקסים ואירועי סוף שנה", 965000), ("מתנות לצוות ולסיום כיתות ו׳", 720000),
              ("קרן סיוע לתלמידים", 600000), ("ציוד לחצר ולגינה הלימודית", 1150000), ("רזרבה", 325000)]
    total = sum(v for _, v in budget)
    tasks = [["1", "פרסום התקציב המאושר לכלל ההורים", "יו״ר הוועד – מיכל אברהמי", "01.11.2026", "בוצע"],
             ["2", "קבלת שלוש הצעות מחיר להסעות", "גזבר – רועי שפירא", "10.11.2026", "בטיפול"],
             ["3", "תיאום יום שתילה בגינה הלימודית", "רכזת ירוקה – הדס נחום", "20.11.2026", "פתוח"],
             ["4", "הכנת נוהל לקרן הסיוע", "דנה גולן ויועצת בית הספר", "15.11.2026", "בטיפול"],
             ["5", "בדיקת הצללה במגרש הספורט מול הרשות", "אבי מזרחי", "30.11.2026", "פתוח"],
             ["6", "הפצת סקר הורים על שעות הצהרון", "נציגת כיתות ג׳ – סיגל בן חיים", "25.11.2026", "פתוח"],
             ["7", "עדכון רשימת נציגי הכיתות באתר", "מזכירת הוועד – ליאת כהן", "05.11.2026", "בוצע"]]
    seg = continued("mesimot", [["מס׳", "משימה", "אחראי", "מועד", "סטטוס"]], tasks, [3, 4], caption="טבלה 3 – משימות להמשך",
                    continued_caption="טבלה 3 – משימות להמשך (המשך)", widths=[7, 40, 28, 13, 12])
    return {
        "template": "meeting_minutes", "page_size": "A4", "languages": ["he-IL"], "dir": "rtl",
        "metadata": {"title": "פרוטוקול ישיבת ועד ההורים – בית הספר אלונים, 27.10.2026", "author": "ועד ההורים המוסדי, בית הספר אלונים",
                     "subject": "פרוטוקול ישיבה", "keywords": ["פרוטוקול", "ועד הורים", "תקציב", "הצבעה"], "lang": "he-IL", "created": "2026-10-28T18:45:00Z"},
        "theme": {"accent": "#7a3b69", "py_size": 11.6},
        "running_header": "ועד ההורים המוסדי – בית הספר אלונים, קריית טבעון – ישיבה מס׳ 2",
        "running_footer": "עמוד {page} מתוך {pages}",
        "arithmetic": [*checks, {"kind": "column_sum", "table": "taktziv", "columns": [1], "label_column": 0, "total_label": "סה״כ"}],
        "pages": [
            [
                H(1, "פרוטוקול ישיבת ועד ההורים המוסדי"),
                table("pratim", [["פרט", "ערך"], ["תאריך", "27.10.2026"], ["שעה", "20:00"], ["מקום", "חדר המורים, בית הספר אלונים, קריית טבעון"],
                                 ["ישיבה", "ישיבה שנייה לשנת הלימודים התשפ״ז"]], caption="פרטי הישיבה", align=["r", "r"], widths=[25, 75]),
                H(2, "נוכחים"),
                P("מיכל אברהמי (יו״ר), רועי שפירא (גזבר), ליאת כהן (מזכירה), הדס נחום, דנה גולן, אבי מזרחי, סיגל בן חיים, יוסי עזרא, "
                  "נועה פרידמן, עומר חדד, רחל ביטון."),
                P("נעדרו: אלון קרמר (מילואים), שירן טל."),
                P("מוזמנים: מנהלת בית הספר, גב׳ אורית לוי; היועצת, גב׳ תמר שלום."),
                H(2, "סדר היום"),
                L(["אישור פרוטוקול הישיבה הקודמת", "דיווח המנהלת על פתיחת שנת הלימודים", "אישור תקציב ועד ההורים",
                   "הסעות לטיול השנתי", "תוכנית בית ספר ירוק וגינה לימודית", "שונות"], ordered=True),
                H(2, "1. אישור פרוטוקול"),
                P("פרוטוקול הישיבה הקודמת, מחודש ספטמבר, אושר פה אחד ללא הערות."),
                H(2, "2. דיווח המנהלת"),
                P("המנהלת עדכנה כי בבית הספר לומדים השנה ארבע מאות שמונים ושישה תלמידים בשמונה־עשרה כיתות. נקלטו שלוש מורות חדשות, והוקמה כיתת תקשורת שנייה. "
                  "עבודות השיפוץ בשירותי הבנות הסתיימו לפני תחילת השנה. המנהלת הודתה להורים על ההתגייסות לצביעת החצר בחופשת הקיץ."),
                P("היועצת הציגה את תוכנית ״כישורי חיים״ לכיתות ד׳–ו׳ וביקשה מההורים לעודד שיח בבית על שימוש מושכל ברשתות."),
            ],
            [
                H(2, "3. תקציב ועד ההורים"),
                P("הגזבר הציג את הצעת התקציב לשנת הלימודים. ההכנסות מבוססות על תשלום רשות של מאה ועשרים שקלים לתלמיד ועל שיעור הגבייה בשנה שעברה, תשעים ושלושה אחוזים."),
                table("taktziv", [["סעיף", "סכום"], *[[k, money(v, "he")] for k, v in budget], ["סה״כ", money(total, "he")]],
                      caption="טבלה 1 – הצעת תקציב ועד ההורים", align=["r", "r"], widths=[70, 30], total_rows=[len(budget) + 1]),
                P("בדיון הועלתה הצעה להגדיל את קרן הסיוע על חשבון המתנות לצוות. הוחלט להשאיר את החלוקה המוצעת ולבחון שוב באמצע השנה."),
                H(2, "4. הסעות לטיול השנתי"),
                P("התקבלו שתי הצעות מחיר. ההצעה של חברת ״הגליל הירוק״ זולה בשמונה אחוזים אך כוללת אוטובוסים ללא חגורות בטיחות בכל המושבים. "
                  "הוחלט לבקש הצעה שלישית ולהעדיף אוטובוסים עם חגורות."),
                H(2, "5. בית ספר ירוק"),
                P("הדס נחום הציגה את תוכנית ההצטרפות לרשת בתי הספר הירוקים, הכוללת גינה לימודית, מחזור פסולת אורגנית וסיור בפארק הקישון. "
                  "ההורים הביעו תמיכה רחבה."),
                table("hatzbaot", [["נושא ההצבעה", "בעד", "נגד", "נמנעים", "נוכחים"], *vote_rows],
                      caption="טבלה 2 – תוצאות ההצבעות", align=["r", "c", "c", "c", "c"], widths=[52, 12, 12, 12, 12]),
                *seg[:1],
            ],
            [
                *seg[1:],
                H(2, "6. שונות"),
                L(["הוצע לקיים ערב הורים בנושא בטיחות בדרכים לקראת החורף, בשיתוף משטרת התנועה.",
                   "נציגי כיתות א׳ ביקשו לבדוק תוספת שומר בשער הצפוני בשעות הפיזור.",
                   "נקבע כי סיכומי הישיבות יופצו להורים בקבוצות הכיתתיות תוך שבוע."]),
                H(2, "החלטות"),
                L(["תקציב ועד ההורים אושר כמפורט בטבלה 1.", "תתקבל הצעת מחיר שלישית להסעות עד העשירי בנובמבר.",
                   "בית הספר יצטרף לתוכנית בית ספר ירוק, ויום שתילה ראשון ייקבע בנובמבר."], ordered=True),
                box("callout", "הישיבה הבאה תתקיים ביום שלישי, הראשון בדצמבר, בשעה שמונה בערב בחדר המורים. הורים המעוניינים להעלות נושא "
                    "לסדר היום מתבקשים לפנות למזכירת הוועד עד שבוע לפני הישיבה.", title="הישיבה הבאה", cls="note"),
                P("הישיבה ננעלה בשעה עשר וחמש דקות בלילה."),
                P("רשמה: ליאת כהן, מזכירת הוועד\nאישרה: מיכל אברהמי, יו״ר ועד ההורים"),
            ],
        ],
    }


DOCS = [
    ("w2-form-en-37", "reportlab", form_en),
    ("w2-form-de-38", "reportlab", form_de),
    ("w2-form-ja-39", "reportlab", form_ja),
    ("w2-form-pl-40", "reportlab", form_pl),
    ("w2-contract-en-41", "libreoffice", contract_en),
    ("w2-contract-es-42", "chromium", contract_es),
    ("w2-contract-he-43", "chromium", contract_he),
    ("w2-contract-zhtw-44", "reportlab", contract_zhtw),
    ("w2-cv-en-45", "chromium", cv_en),
    ("w2-cv-de-46", "libreoffice", cv_de),
    ("w2-cv-ko-47", "pylopdf", cv_ko),
    ("w2-cv-el-48", "reportlab", cv_el),
    ("w2-minutes-en-49", "libreoffice", minutes_en),
    ("w2-minutes-zhcn-50", "libreoffice", minutes_zhcn),
    ("w2-minutes-tr-51", "chromium", minutes_tr),
    ("w2-minutes-he-52", "pylopdf", minutes_he),
]
