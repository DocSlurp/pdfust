"""Authored wild-v2 documents: restaurant menus, event programs and newsletters (docs 53-64).

Every document is fictional but internally consistent: prices, ticket and
package tables are computed here from integer minor units and declared in
``doc["arithmetic"]`` so the build verifies them.
"""

# ruff: noqa: E501
from __future__ import annotations

from typing import Any

from bench.wild_templates.common import nfd
from bench.wild_templates.model import money, number
from bench.wild_v2_templates.core import (
    H,
    L,
    P,
    box,
    chart,
    chart_table,
    columns,
    continued,
    group,
    pair,
    photo,
    screenshot,
    table,
)

NBSP = "\u00a0"
NNBSP = "\u202f"
LRM = "\u200e"
RLM = "\u200f"
ZWJ = "\u200d"
ZWNJ = "\u200c"


# ---------------------------------------------------------------- formatters


def eur_fr(cents: int) -> str:
    """French menu price with a narrow no-break space before the euro sign: ``14,50 €``."""
    return f"{cents // 100},{cents % 100:02d}{NNBSP}€"


def baht(value: int) -> str:
    """Whole-baht menu price: ``฿1,250``."""
    return f"฿{value:,}"


def dong(value: int) -> str:
    """Vietnamese dong (zero-decimal): ``65.000 ₫``."""
    return money(value, "vi")


def gbp(pence: int) -> str:
    """British pounds: ``£14.50``."""
    return money(pence, "en-GB")


def usd(cents: int) -> str:
    """US dollars: ``$1,250.00``."""
    return money(cents, "en-US")


def inr(paise: int) -> str:
    """Indian rupees with lakh grouping: ``₹1,23,456``."""
    return "₹" + number(paise / 100, "hi", 0)


_AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def ar_num(value: int) -> str:
    """Arabic-Indic digits with the Arabic thousands separator."""
    return f"{value:,}".replace(",", "٬").translate(_AR_DIGITS)


def qar(dirhams: int) -> str:
    """Qatari riyal in Arabic-Indic digits: ``١٬٢٥٠٫٠٠ ر.ق``."""
    whole = ar_num(dirhams // 100)
    return f"{whole}٫{f'{dirhams % 100:02d}'.translate(_AR_DIGITS)} ر.ق"


def pln(grosze: int) -> str:
    """Polish zloty: ``1 250,00 zł`` (no-break space grouping)."""
    return money(grosze, "pl")


def eur_es(cents: int) -> str:
    """Spanish euro amount: ``1.250,00 €``."""
    return money(cents, "es")


def rub(kopecks: int) -> str:
    """Russian rubles: ``1 250 ₽`` (whole rubles)."""
    return number(kopecks / 100, "ru", 0) + NBSP + "₽"


def eur_el(cents: int) -> str:
    """Greek euro amount: ``1.250,00 €``."""
    whole = f"{cents // 100:,}".replace(",", ".")
    return f"{whole},{cents % 100:02d}{NBSP}€"


def dish(name: str, description: str, price: str) -> dict[str, Any]:
    """Build a menu line: name and description on the left, price on the right (flex row in Chromium)."""
    return group([P(f"**{name}**\n{description}"), P(price, "right")], "menu-item")


# ================================================================ restaurant menus


def menu_fr() -> dict[str, Any]:
    """Lyon bistro, autumn menu (Chromium)."""
    n = NBSP
    starters = [
        ("Œuf parfait, crème de cèpes¹ ²", "mouillettes au beurre noisette, copeaux de comté 18 mois", 1250),
        ("Salade lyonnaise", "frisée, lardons fumés, croûtons à l’ail, œuf poché¹ ²", 1150),
        ("Pâté en croûte maison¹ ³", "volaille, foie gras et pistache, pickles de cèleri", 1450),
        ("Velouté de potimarron", "huile de noisette, graines torréfiées⁴ (végétarien)", 950),
        ("Harengs pommes à l’huile⁵", "pommes ratte tièdes, oignons rouges, aneth", 1050),
        ("Cervelle de canut", "fromage blanc aux herbes, échalote, pain de campagne¹ ²", 850),
    ]
    mains = [
        ["Quenelle de brochet, sauce Nantua", "brochet du lac du Bourget, écrevisses, riz pilaf", "1, 2, 3, 5, 6", eur_fr(2350)],
        ["Andouillette 5A de chez Bobosse", "sauce moutarde à l’ancienne, gratin dauphinois", "2, 8", eur_fr(2150)],
        ["Tablier de sapeur", "gras-double pané, sauce gribiche, pommes grenaille", "1, 2, 3, 8", eur_fr(1990)],
        ["Bœuf bourguignon", "joue de bœuf braisée 7 h, carottes, lardons, purée", "2, 7, 9", eur_fr(2450)],
        ["Filet de bar rôti", "ﬁlet sur peau, fenouil confit, beurre blanc au citron", "2, 5", eur_fr(2690)],
        ["Volaille de Bresse aux morilles", "suprême, crème au vin jaune, riz sauvage", "2, 9", eur_fr(3200)],
        ["Risotto d’épeautre aux champignons", "cèpes, girolles, parmesan, roquette (végétarien)", "1, 2", eur_fr(1890)],
    ]
    desserts = [
        ("Tarte aux pralines roses¹ ² ⁴", "pâte sablée, crème fraîche d’Isigny", 850),
        ("Île flottante", "crème anglaise vanille Bourbon, caramel¹ ²", 800),
        ("Mousse au chocolat noir 70 %", "copeaux de fève de cacao, fleur de sel²", 850),
        ("Saint-Marcellin affiné", "salade de mesclun, noix⁴", 750),
        ("Plateau de fromages de la Mère Richard", "trois fromages, confiture de cerises noires²", 1250),
        ("Café gourmand", "expresso et trois mignardises du moment¹ ² ⁴", 990),
    ]
    drinks = [
        ["Expresso / Noisette", eur_fr(220), "Eau minérale Évian 50 cl", eur_fr(450)],
        ["Café allongé", eur_fr(260), "Badoit 75 cl", eur_fr(650)],
        ["Cappuccino", eur_fr(420), "Limonade artisanale Elixia", eur_fr(450)],
        ["Thé ou infusion bio", eur_fr(450), "Jus de pomme de l’Ardèche", eur_fr(480)],
        ["Chocolat chaud à l’ancienne", eur_fr(520), "Bière Ninkasi pression 25 cl", eur_fr(550)],
        ["Irish coffee", eur_fr(990), "Cidre brut fermier 33 cl", eur_fr(600)],
    ]
    wines = [
        ["Blancs", "", "", "", ""],
        ["Mâcon-Villages, Dom. Guillot", "Bourgogne", "2024", eur_fr(700), eur_fr(3400)],
        ["Saint-Véran « Les Pommards »", "Bourgogne", "2023", eur_fr(900), eur_fr(4400)],
        ["Condrieu, Dom. Vernay", "Rhône nord", "2023", "—", eur_fr(9500)],
        ["Viognier IGP Collines rhodaniennes", "Rhône nord", "2024", eur_fr(650), eur_fr(3100)],
        ["Rosé", "", "", "", ""],
        ["Tavel, Château de Trinquevedel", "Rhône sud", "2025", eur_fr(750), eur_fr(3600)],
        ["Rouges", "", "", "", ""],
        ["Beaujolais-Villages, Dom. Chignard", "Beaujolais", "2024", eur_fr(600), eur_fr(2900)],
        ["Morgon « Côte du Py »", "Beaujolais", "2023", eur_fr(850), eur_fr(4100)],
        ["Fleurie, Dom. de la Madone", "Beaujolais", "2024", eur_fr(800), eur_fr(3800)],
        ["Crozes-Hermitage, Dom. Combier", "Rhône nord", "2022", eur_fr(950), eur_fr(4600)],
        ["Saint-Joseph, Dom. Gonon", "Rhône nord", "2022", "—", eur_fr(6200)],
        ["Côte-Rôtie, Dom. Jamet", "Rhône nord", "2020", "—", eur_fr(12800)],
        ["Gigondas, Dom. Santa Duc", "Rhône sud", "2021", eur_fr(1100), eur_fr(5200)],
        ["Pot lyonnais (46 cl)", "Côtes-du-Rhône", "2024", "—", eur_fr(1800)],
    ]
    starter, main, dessert, menu_price = 1250, 2450, 850, 3800
    saving = starter + main + dessert - menu_price
    return {
        "template": "restaurant_menu", "page_size": "A4", "languages": ["fr-FR"],
        "metadata": {"title": "Le Comptoir des Halles — Carte d’automne 2026", "author": "Le Comptoir des Halles SARL",
                     "subject": "Carte du bistrot : entrées, plats, desserts, boissons et vins",
                     "keywords": ["menu", "bistrot", "Lyon", "carte des vins", "automne 2026"], "lang": "fr-FR",
                     "created": "2026-09-22T10:30:00Z"},
        "theme": {"accent": "#7a1f2b", "font_size": "10pt", "body_font": "'Noto Serif'", "margins": "16mm 17mm 18mm 17mm"},
        "running_header": "Le Comptoir des Halles · Carte d’automne 2026",
        "running_footer": "Prix nets, service compris · Page {page} / {pages}",
        "pages": [
            [
                P("Le Comptoir des Halles", "brand"),
                P(f"Bistrot lyonnais depuis 1987 · 12 rue de la Charité, 69002 Lyon · 04{n}72{n}55{n}01{n}38 · "
                  "[comptoirdeshalles.example](https://comptoirdeshalles.example/reserver)", "small"),
                H(1, "Carte d’automne 2026"),
                photo("ph1", ["bread-bakery"], ["food"], {"bread-bakery": "Le pain au levain de la boulangerie Saint-Vincent, livré chaque matin à 7 h."},
                      "Notre pain au levain, livré chaque matin.", "none", width="100%"),
                P("Bienvenue au Comptoir ! Depuis bientôt quarante ans, notre cuisine suit le rythme des Halles Paul-Bocuse, à "
                  "deux pas d’ici : les volailles viennent de Bresse, les fromages de chez la Mère Richard et les légumes des "
                  f"maraîchers des monts du Lyonnais. La carte change avec les saisons{n}; l’ardoise du jour, elle, change avec le marché.", "lead"),
                pair(
                    table("t-hours", [["Jour", "Déjeuner", "Dîner"],
                                      ["Lundi", "fermé", "fermé"],
                                      ["Mardi – jeudi", "12 h – 14 h", "19 h – 22 h"],
                                      ["Vendredi", "12 h – 14 h", "19 h – 22 h 30"],
                                      ["Samedi", "12 h – 14 h 30", "19 h – 22 h 30"],
                                      ["Dimanche", "12 h – 15 h", "fermé"]],
                          rendering="borderless", caption="Horaires d’ouverture", widths=[40, 30, 30]),
                    box("callout", f"Entrée + plat ou plat + dessert{n}: **{eur_fr(2350)}**\nEntrée + plat + dessert{n}: **{eur_fr(2850)}**\n"
                        "Du mardi au vendredi midi, hors jours fériés. Plats de l’ardoise uniquement.", title="Formule du marché"),
                ),
                box("sidebar", f"Œuf parfait ({eur_fr(starter)}), bœuf bourguignon ({eur_fr(main)}) et tarte aux pralines "
                    f"({eur_fr(dessert)}) valent {eur_fr(starter + main + dessert)} à la carte. Le Menu Découverte vous les propose pour "
                    f"**{eur_fr(menu_price)}**, soit {eur_fr(saving)} d’économie. Accord mets-vins (3 verres){n}: + {eur_fr(1800)}.",
                    title="Menu Découverte", cls="wide"),
                P(f"Réservation conseillée le week-end. Groupes à partir de 10 personnes{n}: menus sur demande au 04{n}72{n}55{n}01{n}38.", "small muted"),
            ],
            [
                H(2, "Entrées"),
                photo("ph2", ["salad-bowl"], ["food"], {"salad-bowl": "La salade lyonnaise, version d’automne."},
                      "La salade lyonnaise.", "right", width="38%"),
                P("Nos entrées sont préparées à la minute. Le pâté en croûte est monté la veille et repose une nuit avant "
                  "d’être tranché, comme le faisait Madame Brazier, dont nous gardons précieusement le carnet de recettes."),
                P(f"Les végétariens ne sont pas oubliés{n}: le velouté et la cervelle de canut sont sans viande, et nous adaptons "
                  "volontiers la salade lyonnaise sans lardons."),
                columns([dish(a, b, eur_fr(c)) for a, b, c in starters], count=2),
                H(2, "L’ardoise du jour"),
                P("Chaque midi, le chef Antoine Ferrand écrit à la craie deux entrées, deux plats et un dessert selon les arrivages. "
                  "Demandez-la à votre serveur ou consultez-la sur le tableau près du comptoir — elle est aussi publiée chaque "
                  "matin à 10 h sur notre page de réservation."),
                box("callout", "Le jeudi soir, le tablier de sapeur est accompagné d’un « pot » de Côtes-du-Rhône pour deux "
                    f"({eur_fr(3200)} au total). Pas de réservation, premier arrivé, premier servi{n}!", title="Jeudi des bouchons", cls="note"),
                H(3, "Nos producteurs"),
                L(["Volailles fermières de Bresse — élevage Mercier, Saint-Étienne-du-Bois",
                   "Fromages affinés — la Mère Richard, Halles Paul-Bocuse",
                   "Légumes et herbes — Gaec des Coteaux, Saint-Martin-en-Haut",
                   "Charcuterie — Maison Sibilia (andouillette, saucisson brioché)",
                   "Poissons du lac du Bourget — pêcherie Lacustre, Aix-les-Bains"]),
            ],
            [
                H(2, "Plats"),
                P("Tous nos plats sont accompagnés d’une garniture de saison. Les viandes sont d’origine française (Charolais, "
                  "Bresse, Ardèche)" + f"{n}; le poisson provient de pêche durable et peut varier selon la criée."),
                table("t-mains", [["Plat", "Accompagnement", "Allergènes", "Prix"], *mains], rendering="borderless",
                      caption="Plats — numéros d’allergènes : voir la clé en dernière page", align=["l", "l", "c", "r"],
                      widths=[30, 44, 12, 14]),
                photo("ph3", ["catering-buffet"], ["food"], {"catering-buffet": "Le service du midi : les plats sortent de la cuisine ouverte."},
                      "Le service du midi.", "left", width="40%"),
                P("La quenelle de brochet est notre plat signature depuis 1987. Elle est pochée puis gratinée au four dans sa "
                  "sauce Nantua aux écrevisses — comptez vingt minutes de cuisson, elle en vaut la peine."),
                P("Le bœuf bourguignon mijote sept heures à basse température dans un Côtes-du-Rhône de la maison Combier. "
                  "Il est servi en cocotte individuelle avec une purée au beurre demi-sel."),
                box("callout", f"Pour les moins de 12 ans{n}: steak haché de Charolais ou filet de poisson, frites maison, "
                    f"boule de glace et sirop à l’eau — {eur_fr(1250)}.", title="Menu Bouchon (enfants)"),
                P(f"Supplément frites maison{n}: {eur_fr(400)} · Supplément gratin dauphinois{n}: {eur_fr(550)} · "
                  f"Salade verte{n}: {eur_fr(450)}", "small"),
                P(f"Pain et beurre de baratte offerts. Une carafe d’eau est servie sur simple demande{n}: n’hésitez pas.", "small muted"),
            ],
            [
                H(2, "Fromages & desserts"),
                columns([dish(a, b, eur_fr(c)) for a, b, c in desserts], count=2),
                P("Nos desserts sont faits maison, à l’exception des glaces et sorbets de la maison Nardone (deux boules "
                  f"{eur_fr(650)}, trois boules {eur_fr(850)}).", "small"),
                H(2, "Boissons"),
                photo("ph4", ["coffee-cup"], ["food"], {"coffee-cup": "Café de la brûlerie Mokxa, torréfié à Lyon."},
                      "Café de la brûlerie Mokxa.", "right", width="34%"),
                P("Notre café vient de la brûlerie Mokxa, rue de l’Annonciade : un assemblage Brésil-Éthiopie torréfié "
                  "chaque semaine. Le lait est entier et bio, les boissons végétales (avoine, amande) sont sans supplément."),
                P("Les sirops et limonades sont produits dans la Drôme, et les jus de fruits pressés à froid en Ardèche."),
                table("t-drinks", [["Boissons chaudes", "Prix", "Boissons fraîches", "Prix"], *drinks], rendering="ruled",
                      caption="Boissons", align=["l", "r", "l", "r"], widths=[30, 14, 40, 16]),
                box("footnote", f"Licence IV. L’abus d’alcool est dangereux pour la santé, à consommer avec modération. Vente "
                    f"d’alcool interdite aux mineurs de moins de 18{n}ans."),
            ],
            [
                H(2, "Carte des vins"),
                P("Notre sommelière, Claire Dumoulin, a sélectionné des vins de vignerons indépendants du Beaujolais et de la "
                  f"vallée du Rhône. Le verre est servi à 12{n}cl, la bouteille à 75{n}cl."),
                table("t-wine", [["Vin", "Appellation", "Millésime", "Verre 12 cl", "Bouteille 75 cl"], *wines],
                      rendering="ruled", caption="Vins au verre et à la bouteille", align=["l", "l", "c", "r", "r"],
                      widths=[38, 18, 12, 15, 17], merges=((1, 0, 1, 5), (6, 0, 1, 5), (8, 0, 1, 5))),
                P(f"Droit de bouchon{n}: {eur_fr(1500)} par bouteille apportée (une bouteille par table de quatre).", "small"),
                table("t-digestifs", [["Digestifs (4 cl)", "Prix"], ["Chartreuse verte", eur_fr(900)], ["Marc du Bugey", eur_fr(750)],
                                      ["Calvados Pays d’Auge 6 ans", eur_fr(850)], ["Poire Williams, distillerie Paul Devoille", eur_fr(800)]],
                      rendering="borderless", align=["l", "r"], widths=[75, 25]),
                H(3, "Allergènes"),
                P("Conformément au règlement (UE) n° 1169/2011, les quatorze allergènes majeurs sont signalés par un chiffre en "
                  "exposant dans la carte. Notre équipe peut vous renseigner sur la composition de chaque plat."),
                box("footnote", "¹ gluten · ² lait · ³ œufs · ⁴ fruits à coque · ⁵ poisson · ⁶ crustacés · ⁷ céleri · ⁸ moutarde · ⁹ sulfites"),
                box("footnote", "Des traces d’autres allergènes peuvent être présentes : notre cuisine ouverte travaille tous les produits."),
                P(f"Le Comptoir des Halles SARL · SIRET 342{n}118{n}905{n}00027 · Maître restaurateur depuis 2014 · "
                  "Titres-restaurant acceptés le midi · Paiement sans contact, CB, espèces.", "small muted"),
            ],
        ],
        "arithmetic": [{"kind": "sum", "terms": [["+", eur_fr(starter)], ["+", eur_fr(main)], ["+", eur_fr(dessert)],
                                                  ["-", eur_fr(menu_price)]], "equals": eur_fr(saving)}],
    }


def menu_th() -> dict[str, Any]:
    """Northern Thai restaurant in Chiang Mai, Thai with English dish names (LibreOffice, tagged)."""
    starters = [
        ["แหนมซี่โครงทอด¹", "Fried fermented pork ribs", baht(145)],
        ["ไส้อั่วสมุนไพร", "Northern Thai herb sausage", baht(165)],
        ["น้ำพริกหนุ่ม ผักนึ่ง แคบหมู", "Green chilli dip, steamed vegetables, pork crackling", baht(120)],
        ["ยำหัวปลี²", "Banana blossom salad with roasted peanuts", baht(130)],
        ["ทอดมันปลากราย³", "Fish cakes with cucumber relish", baht(155)],
        ["เมี่ยงคำ²", "Betel leaf wraps with ginger, lime and peanuts", baht(110)],
    ]
    mains = [
        ["ข้าวซอยไก่", "Khao soi with chicken drumstick", baht(150)],
        ["ข้าวซอยเนื้อตุ๋น", "Khao soi with braised beef", baht(180)],
        ["แกงฮังเลหมู", "Hang lay pork belly curry with ginger", baht(220)],
        ["แกงแคไก่", "Jungle curry with chicken and wild greens", baht(190)],
        ["ลาบคั่วเชียงราย", "Chiang Rai spicy minced pork laab", baht(160)],
        ["ปลานิลนึ่งมะนาว³", "Steamed tilapia with lime and chilli", baht(320)],
        ["ผัดผักกาดกวางตุ้งไฟแดง¹", "Stir-fried choy sum with garlic", baht(95)],
        ["ไข่เจียวชะอม", "Cha-om herb omelette", baht(90)],
        ["ข้าวเหนียว / ข้าวหอมมะลิ", "Sticky rice / jasmine rice", f"{baht(25)} / {baht(20)}"],
    ]
    drinks = [["เครื่องดื่ม", "Drink", "ราคา"],
              ["ชาไทยเย็น", "Thai iced tea", baht(65)],
              ["กาแฟดอยช้าง (ร้อน/เย็น)", "Doi Chang coffee (hot/iced)", baht(70)],
              ["น้ำลำไยสด", "Fresh longan juice", baht(60)],
              ["น้ำมะพร้าวอ่อน", "Young coconut", baht(80)],
              ["เบียร์สิงห์ / ช้าง (ขวดใหญ่)", "Singha / Chang beer (large)", baht(120)]]
    wines = [["ไวน์", "Wine", "แก้ว", "ขวด"],
             ["GranMonte Spring Chenin Blanc", "เขาใหญ่, ไทย", baht(240), baht(1150)],
             ["Silverlake Sauvignon Blanc", "พัทยา, ไทย", baht(220), baht(1050)],
             ["Monsoon Valley Shiraz", "หัวหิน, ไทย", baht(220), baht(990)],
             ["Villa Maria Riesling", "Marlborough, NZ", baht(290), baht(1450)],
             ["Casillero del Diablo Merlot", "Central Valley, Chile", baht(260), baht(1250)]]
    set_items = [("ข้าวซอยไก่", 2, 150), ("แกงฮังเลหมู", 1, 220), ("ลาบคั่วเชียงราย", 1, 160),
                 ("น้ำพริกหนุ่ม ผักนึ่ง แคบหมู", 1, 120), ("ข้าวเหนียว", 4, 25), ("ข้าวเหนียวมะม่วง", 2, 120)]
    set_rows = [[name, str(qty), baht(unit), baht(qty * unit)] for name, qty, unit in set_items]
    set_total = sum(qty * unit for _, qty, unit in set_items)
    set_price = 990
    return {
        "template": "restaurant_menu", "page_size": "A4", "languages": ["th-TH", "en"], "tagged": True,
        "metadata": {"title": "ครัวบ้านสวน — เมนูอาหารฤดูฝน 2569", "author": "ครัวบ้านสวน เชียงใหม่",
                     "subject": "เมนูอาหารเหนือ เครื่องดื่ม และไวน์ / Northern Thai menu", "keywords": ["เมนู", "อาหารเหนือ", "เชียงใหม่", "menu"],
                     "lang": "th-TH", "created": "2026-07-01T04:00:00Z"},
        "theme": {"accent": "#2f6b3a", "lo_size": "10pt", "lo_font": "Noto Sans"},
        "running_header": "ครัวบ้านสวน · Baan Suan Kitchen · เมนูฤดูฝน 2569",
        "running_footer": "ราคารวมภาษีมูลค่าเพิ่มแล้ว · หน้า {page} / {pages}",
        "pages": [
            [
                P("ครัวบ้านสวน · Baan Suan Kitchen", "brand"),
                P("88/3 ถนนนิมมานเหมินท์ ซอย 9 ตำบลสุเทพ อำเภอเมือง เชียงใหม่ 50200 · โทร 053 555 0172 · baansuan.example", "small"),
                H(1, "เมนูอาหาร ฤดูฝน 2569"),
                photo("ph1", ["garden-flowers", "farm-field"], ["garden"], {"garden-flowers": "สวนผักและดอกไม้หลังร้าน เก็บสดทุกเช้า",
                                                                           "farm-field": "แปลงผักของร้านที่อำเภอแม่ริม"},
                      "สวนผักหลังร้าน", "none", width_cm=13.0),
                P("ยินดีต้อนรับสู่ครัวบ้านสวน ร้านอาหารพื้นเมืองล้านนาที่ปรุงด้วยผักจากสวนของเราเองที่อำเภอแม่ริม และวัตถุดิบจาก"
                  "กาดเมืองใหม่ทุกเช้า เมนูของเราเปลี่ยนตามฤดูกาล หากท่านแพ้อาหารหรือต้องการลดความเผ็ด กรุณาแจ้งพนักงานก่อนสั่งอาหาร", "lead"),
                table("t-hours", [["วัน", "เวลาเปิด"], ["จันทร์ – ศุกร์", "11:00 – 15:00 และ 17:30 – 22:00"],
                                  ["เสาร์ – อาทิตย์", "10:30 – 22:30"], ["วันพุธที่ 2 ของทุกเดือน", "ปิดทำความสะอาดครัว"]],
                      rendering="borderless", caption="เวลาเปิดบริการ", widths=[40, 60]),
                H(2, "อาหารว่าง · Starters"),
                table("t-starters", [["เมนู", "English", "ราคา"], *starters], rendering="ruled", align=["l", "l", "r"], widths=[40, 45, 15]),
            ],
            [
                H(2, "อาหารจานหลัก · Mains"),
                table("t-mains", [["เมนู", "English", "ราคา"], *mains], rendering="ruled", align=["l", "l", "r"], widths=[38, 45, 17]),
                P("ระดับความเผ็ด: เราปรุงแบบเผ็ดกลางเป็นมาตรฐาน สามารถสั่งแบบไม่เผ็ด เผ็ดน้อย หรือเผ็ดแบบคนเมืองได้"),
                photo("ph2", ["salad-bowl", "catering-buffet"], ["food"], {"salad-bowl": "ยำหัวปลีและผักเครื่องเคียงจากสวน",
                                                                          "catering-buffet": "สำรับอาหารเหนือสำหรับงานเลี้ยง"},
                      "ยำหัวปลี", "none", width_cm=10.0),
                box("callout", "ข้าวซอยของเราใช้เส้นสดจากร้านป้าจันทร์ ย่านช้างคลาน เคี่ยวน้ำแกงกับเครื่องแกงที่ตำเองทุกวัน "
                    "Our khao soi paste is pounded fresh every morning.", title="เมนูแนะนำ · Chef’s pick"),
                box("footnote", "¹ มีถั่วเหลือง / contains soy  ² มีถั่วลิสง / contains peanuts  ³ มีปลา / contains fish"),
            ],
            [
                H(2, "ของหวานและเครื่องดื่ม · Desserts & drinks"),
                table("t-desserts", [["ของหวาน", "Dessert", "ราคา"], ["ข้าวเหนียวมะม่วง", "Mango sticky rice", baht(120)],
                                     ["บัวลอยน้ำขิง", "Rice dumplings in ginger syrup", baht(75)],
                                     ["ไอศกรีมกะทิ ถั่วลิสงคั่ว²", "Coconut ice cream, roasted peanuts", baht(85)]],
                      rendering="borderless", align=["l", "l", "r"], widths=[40, 45, 15]),
                table("t-drinks", drinks, rendering="borderless", caption="เครื่องดื่ม", align=["l", "l", "r"], widths=[40, 45, 15]),
                table("t-wine", wines, rendering="ruled", caption="ไวน์ (แก้ว 150 มล. / ขวด 750 มล.)", align=["l", "l", "r", "r"],
                      widths=[40, 30, 15, 15]),
                H(2, "ชุดอาหารสำหรับ 4 ท่าน · Family set"),
                table("t-set", [["รายการ", "จำนวน", "ราคาต่อหน่วย", "รวม"], *set_rows, ["รวมราคาปกติ", "", "", baht(set_total)]],
                      rendering="ruled", caption="ชุดบ้านสวน (สั่งล่วงหน้า 1 วัน)", align=["l", "r", "r", "r"], widths=[46, 14, 20, 20],
                      total_rows=[len(set_rows) + 1]),
                P(f"ราคาชุด {baht(set_price)} ประหยัด {baht(set_total - set_price)} จากราคาปกติ "
                  "ราคานี้ยังไม่รวมค่าบริการ 10%"),
                P("ร้านไม่ใช้ผงชูรส · รับชำระด้วยบัตรเครดิต พร้อมเพย์ และเงินสด · We accept cards, PromptPay and cash.", "small"),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-set", "quantity": 1, "unit_price": 2, "amount": 3},
                       {"kind": "column_sum", "table": "t-set", "columns": [3], "label_column": 0, "total_label": "รวมราคาปกติ"},
                       {"kind": "sum", "terms": [["+", baht(set_total)], ["-", baht(set_price)]], "equals": baht(set_total - set_price)}],
    }


def menu_vi() -> dict[str, Any]:
    """Hanoi pho house (pylopdf): zero-decimal dong, one NFD paragraph."""
    pho = [["Món", "Mô tả", "Nhỏ", "Lớn"],
           ["Phở bò tái", "Thịt bò tái chần, hành hoa, rau mùi", dong(55000), dong(70000)],
           ["Phở bò chín", "Thịt nạm, gầu luộc mềm, thái mỏng", dong(55000), dong(70000)],
           ["Phở tái nạm gầu", "Kết hợp ba loại thịt, nước dùng đậm", dong(65000), dong(80000)],
           ["Phở sốt vang", "Bò hầm rượu vang, quế hồi, cà rốt", dong(70000), dong(85000)],
           ["Phở gà ta", "Gà ta thả vườn, lá chanh, hành phi", dong(55000), dong(70000)],
           ["Phở cuốn", "Bánh phở cuốn bò xào, rau thơm (5 cuốn)", dong(60000), dong(95000)],
           ["Phở xào giòn", "Bánh phở chiên giòn, bò xào cải ngồng", "—", dong(90000)]]
    sides = [["Món thêm", "Giá"], ["Quẩy (2 chiếc)", dong(10000)], ["Trứng chần", dong(8000)],
             ["Thêm thịt bò tái (50 g)", dong(25000)], ["Nước dùng thêm", dong(15000)], ["Bánh phở thêm", dong(10000)]]
    others = [["Món", "Mô tả", "Giá"],
              ["Bún chả Hà Nội", "Chả viên, chả miếng nướng than hoa, bún, rau sống", dong(65000)],
              ["Bún thang", "Gà xé, giò lụa, trứng tráng, nấm hương", dong(70000)],
              ["Nem rán (4 chiếc)", "Thịt lợn, mộc nhĩ, miến, chấm nước mắm chua ngọt", dong(60000)],
              ["Gỏi cuốn tôm thịt (3 chiếc)", "Tôm, thịt ba chỉ, bún, chấm tương đậu", dong(55000)],
              ["Cơm rang dưa bò", "Cơm rang, dưa cải muối, thịt bò xào", dong(75000)]]
    drinks = [["Đồ uống", "Ly / chai", "Bình / chai lớn"],
              ["Trà đá", dong(5000), dong(20000)],
              ["Nước chanh tươi", dong(25000), dong(80000)],
              ["Cà phê nâu đá", dong(30000), "—"],
              ["Bia Hà Nội (chai 450 ml)", dong(25000), "—"],
              ["Bia hơi (cốc 500 ml / can 2 lít)", dong(20000), dong(70000)],
              ["Vang Đà Lạt Classic đỏ", dong(65000), dong(320000)],
              ["Vang Chile Santa Rita trắng", dong(95000), dong(480000)]]
    combo = [("Phở tái nạm gầu (lớn)", 2, 80000), ("Nem rán (4 chiếc)", 1, 60000), ("Phở cuốn (5 cuốn)", 1, 60000),
             ("Quẩy (2 chiếc)", 2, 10000), ("Trà đá", 4, 5000)]
    combo_rows = [[name, str(qty), dong(unit), dong(qty * unit)] for name, qty, unit in combo]
    combo_total = sum(q * u for _, q, u in combo)
    combo_price = 290000
    history = ("Quán được bà Nguyễn Thị Lựu mở năm 1958 trong một gian nhà ống trên phố Hàng Than. Ba thế hệ sau, chúng tôi "
               "vẫn ninh xương ống bò suốt mười hai tiếng, nướng gừng và hành tím trên bếp than trước khi thả vào nồi, và chỉ "
               "dùng quế, hồi, thảo quả mua ở chợ Đồng Xuân.")
    return {
        "template": "restaurant_menu", "page_size": "A4", "languages": ["vi-VN"],
        "metadata": {"title": "Thực đơn Phở Hàng Than 1958", "author": "Phở Hàng Than 1958",
                     "subject": "Thực đơn phở, món ăn kèm và đồ uống", "keywords": ["thực đơn", "phở", "Hà Nội", "bún chả"],
                     "lang": "vi-VN", "created": "2026-08-15T02:00:00Z"},
        "theme": {"accent": "#a33a12", "py_size": 10.0},
        "running_header": "Phở Hàng Than 1958 · 47 Hàng Than, Ba Đình, Hà Nội · 024 3555 0147",
        "running_footer": "Giá đã bao gồm VAT · Trang {page}/{pages}",
        "pages": [
            [
                P("Phở Hàng Than 1958", "brand"),
                P("Phở gia truyền ba thế hệ · Mở cửa 6:00 – 13:30 và 17:00 – 22:00 hằng ngày", "small"),
                H(1, "Thực đơn"),
                photo("ph1", ["harbor", "city-street"], ["street"], {"city-street": "Phố Hàng Than lúc sáng sớm, khi quán bắt đầu mở cửa.",
                                                                      "harbor": "Bến thuyền Hồ Tây, cách quán mười phút đi bộ."},
                      "Phố Hàng Than lúc sáng sớm.", "right", width="42%"),
                P(history),
                P("Nước dùng trong, ngọt tự nhiên từ xương, không dùng mì chính. Bánh phở được tráng mỏng mỗi sáng tại xưởng "
                  "của gia đình ở làng Vân Cù, Thừa Thiên Huế cũ."),
                H(2, "Phở"),
                table("t-pho", pho, rendering="ruled", caption="Phở bò, phở gà và các món từ bánh phở", align=["l", "l", "r", "r"],
                      widths=[26, 44, 15, 15]),
                table("t-sides", sides, rendering="borderless", caption="Gọi thêm", align=["l", "r"], widths=[70, 30]),
                box("sidebar", "Nếm nước dùng trước khi thêm gia vị. Vắt chanh, thêm ớt tươi hoặc tương ớt tùy khẩu vị. Quẩy ngon nhất "
                    "khi chấm ngập vào nước phở khoảng mười giây.", title="Ăn phở kiểu Hà Nội"),
            ],
            [
                H(2, "Bún, nem và món khác"),
                table("t-others", others, rendering="ruled", align=["l", "l", "r"], widths=[30, 52, 18]),
                photo("ph2", ["bread-bakery", "salad-bowl"], ["food"], {"salad-bowl": "Rau sống ăn kèm: húng quế, mùi tàu, giá đỗ.",
                                                                        "bread-bakery": "Quẩy giòn được chiên mỗi sáng."},
                      "Rau sống ăn kèm.", "left", width="36%"),
                P("Món bún chả chỉ phục vụ buổi trưa từ 10:30, vì chả được nướng trên than hoa ngay trước khi dọn ra bàn."),
                P(nfd("Rau sống được rửa qua nước lọc ba lần. Quý khách ăn chay có thể chọn phở nấm hương với nước dùng rau củ, "
                      "xin báo trước với nhân viên.")),
                H(2, "Suất gia đình (4 người)"),
                table("t-combo", [["Món", "SL", "Đơn giá", "Thành tiền"], *combo_rows, ["Tổng giá lẻ", "", "", dong(combo_total)]],
                      rendering="ruled", caption="Suất gia đình Hàng Than", align=["l", "r", "r", "r"], widths=[46, 10, 20, 24],
                      total_rows=[len(combo_rows) + 1]),
                box("callout", f"Giá suất gia đình: {dong(combo_price)}, tiết kiệm {dong(combo_total - combo_price)} so với gọi lẻ. "
                    "Áp dụng từ thứ Hai đến thứ Sáu, không áp dụng ngày lễ, Tết.", title="Ưu đãi"),
                P("Suất gia đình cần đặt trước ít nhất hai tiếng qua điện thoại 024 3555 0147 hoặc Zalo cùng số. Bàn tròn tầng hai "
                  "có sức chứa tối đa mười người, phù hợp cho gia đình và nhóm bạn."),
            ],
            [
                H(2, "Đồ uống"),
                table("t-drinks", drinks, rendering="ruled", caption="Đồ uống, bia và rượu vang", align=["l", "r", "r"], widths=[52, 24, 24]),
                photo("ph3", ["coffee-cup"], ["food"], {"coffee-cup": "Cà phê nâu đá pha phin, hạt Robusta Buôn Ma Thuột."},
                      "Cà phê nâu đá.", "right", width="34%"),
                P("Cà phê được pha phin từ hạt Robusta Buôn Ma Thuột rang mộc. Bia hơi được giao tươi mỗi chiều từ nhà máy "
                  "trên đường Hoàng Hoa Thám."),
                P("Rượu vang được bán theo ly 150 ml hoặc theo chai 750 ml."),
                H(2, "Thông tin dị ứng"),
                L(["(G) có gluten: quẩy, nem rán, bánh mì", "(Đ) có đậu nành: tương đậu, nước tương",
                   "(H) có hải sản: gỏi cuốn tôm thịt, nước mắm", "(T) có trứng: bún thang, trứng chần"]),
                box("footnote", "Mọi món ăn có thể chứa vết đậu phộng và vừng do dùng chung bếp. Xin báo cho nhân viên nếu quý khách bị dị ứng."),
                P("Nhận đặt bàn từ 8 người · Thanh toán tiền mặt, thẻ, chuyển khoản VietQR · Không phụ thu ngày thường.", "small"),
                P("Phở Hàng Than 1958 · MST 0101555147 · phohangthan.example", "small muted"),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-combo", "quantity": 1, "unit_price": 2, "amount": 3, "decimal": ","},
                       {"kind": "column_sum", "table": "t-combo", "columns": [3], "label_column": 0, "total_label": "Tổng giá lẻ"},
                       {"kind": "sum", "terms": [["+", dong(combo_total)], ["-", dong(combo_price)]], "equals": dong(combo_total - combo_price)}],
    }


def menu_engb() -> dict[str, Any]:
    """Cotswolds gastropub (ReportLab, cp1252 text so Standard 14 fonts)."""
    starters = [
        ["Soup of the day, Hobbs House sourdough (v)", "G, D", gbp(750)],
        ["Smoked mackerel pâté, pickled cucumber, toast", "F, G, D, Mu", gbp(950)],
        ["Twice-baked Oxford Blue soufflé (v)", "E, D, G", gbp(1050)],
        ["Ham hock terrine, piccalilli, crackling", "Mu, Su", gbp(995)],
        ["Crispy Cornish squid, lime & chilli mayonnaise", "Mo, E, G", gbp(1100)],
    ]
    mains = [
        ["Beer-battered haddock, triple-cooked chips, mushy peas", "F, G, Su", gbp(1850)],
        ["Wheatsheaf beef & Hook Norton ale pie, mash, greens", "G, D, Ce", gbp(1995)],
        ["Pan-roasted hake, brown shrimp butter, samphire", "F, Cr, D", gbp(2350)],
        ["Lamb rump, pressed potato, salsa verde", "D, Su", gbp(2600)],
        ["Wild mushroom & leek pudding, truffle cream (v)", "G, D, E", gbp(1750)],
        ["Wheatsheaf burger, smoked Cheddar, chips", "G, D, Mu, Se", gbp(1795)],
        ["28-day aged sirloin 10 oz, peppercorn sauce", "D, Su", gbp(3200)],
    ]
    puddings = [
        ["Sticky toffee pudding, clotted cream", "G, D, E", gbp(850)],
        ["Bramley apple & blackberry crumble, custard (v)", "G, D, E", gbp(850)],
        ["Dark chocolate tart, salted caramel ice cream", "G, D, E, So", gbp(900)],
        ["Selection of three Cotswold cheeses, oatcakes", "G, D, Ce", gbp(1250)],
    ]
    ales = [["Cask & draught", "Brewery", "ABV", "Half", "Pint"],
            ["Hooky Bitter", "Hook Norton, Oxon", "3.5%", gbp(250), gbp(480)],
            ["Old Hooky", "Hook Norton, Oxon", "4.6%", gbp(275), gbp(530)],
            ["Butcombe Original", "Butcombe, Somerset", "4.0%", gbp(265), gbp(510)],
            ["Guest ale (ask at the bar)", "rotating", "–", gbp(270), gbp(520)],
            ["Cotswold Lager", "Cotswold Brew Co.", "4.2%", gbp(300), gbp(580)],
            ["Westons Stowford Press cider", "Westons, Herefordshire", "4.5%", gbp(280), gbp(540)]]
    wines = [["Wine", "Origin", "175 ml", "250 ml", "Bottle"],
             ["Picpoul de Pinet, Ormarine", "Languedoc, France", gbp(750), gbp(1050), gbp(2900)],
             ["Sauvignon Blanc, Te Pā", "Marlborough, NZ", gbp(850), gbp(1190), gbp(3300)],
             ["Bacchus, Three Choirs", "Gloucestershire, England", gbp(900), gbp(1250), gbp(3500)],
             ["Côtes de Provence rosé, Mirabeau", "Provence, France", gbp(800), gbp(1120), gbp(3100)],
             ["Merlot, Viña Echeverría", "Curicó, Chile", gbp(700), gbp(980), gbp(2700)],
             ["Rioja Crianza, Muriel", "Rioja, Spain", gbp(850), gbp(1190), gbp(3300)],
             ["Malbec, Doña Paula", "Mendoza, Argentina", gbp(900), gbp(1260), gbp(3500)],
             ["Chapel Down Brut NV", "Kent, England", gbp(1100), "–", gbp(5200)]]
    party = [("Three-course set menu", 24, 3850), ("Arrival glass of Chapel Down", 24, 1100), ("Children's menu", 4, 1200),
             ("Bottle of Picpoul de Pinet", 6, 2900), ("Private dining room hire", 1, 15000)]
    party_rows = [[name, str(qty), gbp(unit), gbp(qty * unit)] for name, qty, unit in party]
    party_total = sum(q * u for _, q, u in party)
    deposit = 25000
    return {
        "template": "restaurant_menu", "page_size": "A4", "languages": ["en-GB"],
        "metadata": {"title": "The Wheatsheaf, Long Compton — Autumn Menu 2026", "author": "The Wheatsheaf Inn Ltd",
                     "subject": "Food, drink and wine menu with allergen key and private dining", "keywords": ["menu", "gastropub",
                                                                                                             "Cotswolds", "Sunday roast"],
                     "lang": "en-GB", "created": "2026-10-02T09:00:00Z"},
        "theme": {"accent": "#3d4a2a", "rl_size": 10.0, "rl_serif": True},
        "running_header": "The Wheatsheaf · Long Compton · Autumn 2026",
        "running_footer": "A discretionary 12.5% service charge is added to tables of eight or more · Page {page} of {pages}",
        "pages": [
            [
                group([P("The Wheatsheaf", "brand"), P("Main Street, Long Compton, Warwickshire CV36 5JS\n01608 555 214 · thewheatsheaf.example", "small right")], "split"),
                H(1, "Autumn Menu"),
                photo("ph1", ["farm-field", "aerial-farmland"], ["agriculture"], {"farm-field": "Barley fields on the Compton estate, where our malt is grown.",
                                                                                 "aerial-farmland": "The Compton estate from the air."},
                      "Barley fields on the Compton estate.", "none", width="80%", width_cm=12.5),
                P("Welcome to the Wheatsheaf. We are a seventeenth-century coaching inn on the edge of the Cotswolds, and we cook "
                  "with what our neighbours grow: beef and lamb from Fosseway Farm, vegetables from the walled garden at Weston Park "
                  "and ales brewed four miles down the road in Hook Norton.", "lead"),
                table("t-hours", [["Kitchen", "Lunch", "Dinner"], ["Monday – Thursday", "12:00–14:30", "18:00–21:00"],
                                  ["Friday – Saturday", "12:00–15:00", "18:00–21:30"], ["Sunday", "12:00–17:00 (roasts)", "closed"]],
                      rendering="borderless", caption="Kitchen opening hours (bar open 11:00–23:00 daily)", widths=[40, 30, 30]),
                box("callout", "Two courses £24.50 · three courses £29.50. Roast sirloin of Fosseway beef or rolled pork "
                    "belly, Yorkshire pudding, duck-fat potatoes and seasonal greens. Served every Sunday from 12:00 until "
                    "sold out.", title="Sunday Roast"),
                P("Our menu changes with the seasons, and sometimes with the weather. Please ask about today’s specials board.", "small"),
            ],
            [
                H(2, "Starters"),
                table("t-starters", [["Dish", "Allergens", "Price"], *starters], rendering="borderless", align=["l", "c", "r"], widths=[66, 18, 16]),
                H(2, "Mains"),
                table("t-mains", [["Dish", "Allergens", "Price"], *mains], rendering="borderless", align=["l", "c", "r"], widths=[66, 18, 16]),
                P("Sides £4.50 each: triple-cooked chips · buttered greens · heritage carrots with honey · house salad", "small"),
                photo("ph2", ["catering-buffet", "salad-bowl"], ["food"], {"catering-buffet": "Sunday lunch at the long table in the snug.",
                                                                          "salad-bowl": "Walled-garden salad with Cotswold rapeseed oil."},
                      "Sunday lunch in the snug.", "right", width="36%", width_cm=6.0),
                P("Head chef Rosie Achterberg trained at the Manoir before coming home to Warwickshire. Her pie crust uses "
                  "beef dripping and is rolled by hand every morning."),
                P("Vegetarian (v) dishes can usually be made vegan; just ask."),
                H(2, "Puddings"),
                table("t-puddings", [["Pudding", "Allergens", "Price"], *puddings], rendering="borderless", align=["l", "c", "r"], widths=[66, 18, 16]),
            ],
            [
                H(2, "Drinks"),
                table("t-ales", ales, rendering="ruled", caption="On tap", align=["l", "l", "c", "r", "r"], widths=[34, 30, 10, 13, 13]),
                table("t-wine", wines, rendering="ruled", caption="Wine by the glass and bottle", align=["l", "l", "r", "r", "r"],
                      widths=[34, 27, 13, 13, 13]),
                H(2, "Private dining"),
                P("The Hayloft seats up to 30 guests for birthdays, wakes and village celebrations. Here is an example for a "
                  "christening lunch we hosted in September:"),
                table("t-party", [["Item", "Qty", "Each", "Total"], *party_rows, ["Total", "", "", gbp(party_total)]],
                      rendering="ruled", align=["l", "r", "r", "r"], widths=[52, 12, 16, 20], total_rows=[len(party_rows) + 1]),
                P(f"A deposit of {gbp(deposit)} secures the date; the balance of {gbp(party_total - deposit)} is due on the day.", "small"),
                table("t-soft", [["Coffee & soft drinks", "Price", "", "Price"],
                                 ["Americano / flat white", gbp(320), "Cotswold Spring water 750 ml", gbp(450)],
                                 ["Pot of Yorkshire Tea", gbp(300), "Fentimans ginger beer", gbp(390)],
                                 ["Hot chocolate & marshmallows", gbp(380), "Luscombe apple juice", gbp(370)]],
                      rendering="borderless", align=["l", "r", "l", "r"], widths=[34, 14, 38, 14]),
                P("Dogs are welcome in the bar and the snug; water bowls and biscuits are by the fire. Three en-suite rooms "
                  "are available upstairs from £125 a night including breakfast.", "small"),
                box("footnote", "Allergen key: Ce celery · Cr crustaceans · D dairy · E egg · F fish · G gluten · Mo molluscs · "
                    "Mu mustard · Se sesame · So soya · Su sulphites. Our kitchen handles nuts; we cannot guarantee any dish is nut free."),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-party", "quantity": 1, "unit_price": 2, "amount": 3},
                       {"kind": "column_sum", "table": "t-party", "columns": [3], "label_column": 0, "total_label": "Total"},
                       {"kind": "sum", "terms": [["+", gbp(party_total)], ["-", gbp(deposit)]], "equals": gbp(party_total - deposit)}],
    }


# ================================================================ event programs


def program_en() -> dict[str, Any]:
    """Two-day civic data conference program (pylopdf); CJK/Hangul names sit in their own table cells."""
    schedule = [
        ["Thu 8:00–9:00", "Registration, coffee and pastries", "—", "Lobby B"],
        ["Thu 9:00–9:30", "Welcome and opening remarks", "Dana Whitfield, Program Chair", "Puget Hall"],
        ["Thu 9:30–10:30", "Keynote: Open budgets that residents actually read", "Nguyễn Thị Lan, Saigon Open Data Lab", "Puget Hall"],
        ["Thu 10:30–10:50", "Break and sponsor exhibition", "—", "Lobby B"],
        ["Thu 10:50–11:40", "Publishing transit ridership without re-identification", "Marcus Oyelaran, King County Metro", "Room 201"],
        ["Thu 10:50–11:40", "Workshop: Cleaning permit data with DuckDB", "Ingrid Solberg, Bergen Kommune", "Room 204"],
        ["Thu 11:40–12:30", "Lessons from Athens’ 311 open feed", "Eleni Papadaki, City of Athens", "Room 201"],
        ["Thu 11:40–12:30", "Accessible charts for council reports", "Priya Raman, Code for Spokane", "Room 204"],
        ["Thu 12:30–13:40", "Lunch (vegetarian and halal options)", "—", "Sound View Terrace"],
        ["Thu 13:40–14:30", "Panel: Data stewardship in tribal nations", "Joseph Little Elk (moderator)", "Puget Hall"],
        ["Thu 14:30–15:20", "Street-tree inventories from LiDAR", "Misaki Tanaka, Yokohama City", "Room 201"],
        ["Thu 14:30–15:20", "Writing data-sharing agreements people sign", "Olga Smirnova, Tallinn Digital Office", "Room 204"],
        ["Thu 15:20–15:40", "Break", "—", "Lobby B"],
        ["Thu 15:40–16:30", "Lightning talks (8 × 5 minutes)", "Various", "Puget Hall"],
        ["Thu 16:30–17:15", "Open data awards", "Dana Whitfield, Program Chair", "Puget Hall"],
        ["Thu 17:30–19:30", "Reception at the Foss Waterway Seaport", "—", "705 Dock St"],
        ["Fri 8:00–9:00", "Coffee and birds-of-a-feather tables", "—", "Lobby B"],
        ["Fri 9:00–10:00", "Keynote: Public records in the age of language models", "Rafael Montoya Ruiz, Universidad de los Andes", "Puget Hall"],
        ["Fri 10:00–10:50", "Housing data across county lines", "Grace Whitaker, Pierce County", "Room 201"],
        ["Fri 10:00–10:50", "Workshop: Publishing GTFS-Realtime feeds", "Kim Jihoon, Seoul Metropolitan Government", "Room 204"],
        ["Fri 10:50–11:10", "Break and sponsor exhibition", "—", "Lobby B"],
        ["Fri 11:10–12:00", "Measuring heat islands with volunteer sensors", "Aisha Bello, Tacoma Climate Coalition", "Room 201"],
        ["Fri 11:10–12:00", "From PDF to tables: rescuing legacy reports", "Tomasz Wierzbicki, Kraków City Hall", "Room 204"],
        ["Fri 12:00–13:10", "Lunch and poster session", "—", "Sound View Terrace"],
        ["Fri 13:10–14:00", "Panel: Funding open data after the grant ends", "Hannah Becker (moderator)", "Puget Hall"],
        ["Fri 14:00–14:50", "Election results APIs that survive election night", "Daniel Ochoa, Washington SOS", "Room 201"],
        ["Fri 14:00–14:50", "Workshop: Privacy budgets for small-area statistics", "Nguyễn Thị Lan, Saigon Open Data Lab", "Room 204"],
        ["Fri 15:00–15:45", "Closing keynote: The boring infrastructure we need", "Ingrid Solberg, Bergen Kommune", "Puget Hall"],
        ["Fri 15:45–16:00", "Closing remarks and survey", "Dana Whitfield, Program Chair", "Puget Hall"],
    ]
    seg = continued("t-schedule", [["Time", "Session", "Speaker", "Room"]], schedule, [15, 9, 5],
                    caption="Program at a glance (all times Pacific)", continued_caption="Program at a glance (continued)",
                    widths=[16, 42, 28, 14])
    names = [["Speaker", "Name in original script", "Based in"],
             ["Misaki Tanaka", "田中 美咲", "Yokohama, Japan"],
             ["Kim Jihoon", "김지훈", "Seoul, South Korea"],
             ["Olga Smirnova", "Ольга Смирнова", "Tallinn, Estonia"],
             ["Eleni Papadaki", "Ελένη Παπαδάκη", "Athens, Greece"],
             ["Nguyễn Thị Lan", "Nguyễn Thị Lan", "Ho Chi Minh City, Vietnam"]]
    prices = [["Ticket", "Early bird (to Sep 30)", "Regular", "On-site"],
              ["Full conference (2 days)", usd(39500), usd(49500), usd(57500)],
              ["One day", usd(22500), usd(27500), usd(32500)],
              ["Government / nonprofit (2 days)", usd(24500), usd(29500), usd(34500)],
              ["Student (with valid ID)", usd(7500), usd(9500), usd(9500)],
              ["Workshop add-on (per workshop)", usd(12000), usd(15000), usd(15000)]]
    order = [("Government / nonprofit (2 days)", 6, 29500), ("Workshop add-on", 4, 15000), ("Student (with valid ID)", 2, 9500),
             ("Reception guest ticket", 3, 4500)]
    order_rows = [[name, str(qty), usd(unit), usd(qty * unit)] for name, qty, unit in order]
    gross = sum(q * u for _, q, u in order)
    discount = -(6 * 29500 // 10)
    order_rows.append(["Group discount, 10% on 6+ conference passes", "", "", usd(discount)])
    total = gross + discount
    dash_rows = [["Ticket type", "Sold", "Capacity", "Revenue"],
                 ["Full conference", "312", "400", "$148,410"],
                 ["One day", "141", "200", "$37,925"],
                 ["Gov / nonprofit", "227", "260", "$65,465"],
                 ["Student", "64", "80", "$5,760"],
                 ["Workshops", "188", "240", "$27,600"]]
    dashboard = {"brand": "TixHarbor", "nav": ["Overview", "Orders", "Attendees", "Check-in", "Reports", "Settings"],
                 "title": "Cascadia Civic Data Summit 2026", "range": "Jun 1 – Oct 9, 2026",
                 "kpis": [("Tickets sold", "932", "+18% vs 2025"), ("Gross revenue", "$285,160", "+12% vs 2025"),
                          ("Refunds", "11", "-4 vs 2025"), ("Waitlist", "57", "+57")],
                 "series_title": "Daily ticket sales", "series": [4, 6, 5, 9, 14, 12, 18, 26, 21, 17, 22, 31, 44, 38, 29, 33, 41, 52, 47, 39],
                 "table_title": "Sales by ticket type", "rows": dash_rows, "height": 470}
    attendance = {"title": "Attendance by year", "categories": ["2021", "2022", "2023", "2024", "2025", "2026"],
                  "series": [("In person", [0, 310, 520, 640, 790, 932]), ("Online", [1150, 820, 430, 380, 360, 300])],
                  "max": 1200, "ticks": 4, "tick_format": lambda v: f"{v:,.0f}"}
    return {
        "template": "event_program", "page_size": "Letter", "languages": ["en-US", "vi", "ru", "el", "ja", "ko"],
        "metadata": {"title": "Cascadia Civic Data Summit 2026 — Program", "author": "Cascadia Civic Data Collaborative",
                     "subject": "Conference program, speakers, tickets and practical information, November 12–13, 2026",
                     "keywords": ["conference", "open data", "civic tech", "Tacoma", "program"], "lang": "en-US",
                     "created": "2026-10-09T17:45:00Z"},
        "theme": {"accent": "#0f5c6e", "py_size": 9.5},
        "running_header": "Cascadia Civic Data Summit 2026 · Tacoma, WA · November 12–13",
        "running_footer": "cascadiadata.example · Page {page} of {pages}",
        "pages": [
            [
                P("Cascadia Civic Data Summit", "brand"),
                P("November 12–13, 2026 · Harborview Conference Center · 1500 Commerce Street, Tacoma, WA 98402", "small"),
                H(1, "Program and attendee guide"),
                photo("ph1", ["container-port", "harbor"], ["harbor"], {"container-port": "The Port of Tacoma seen from the conference center terrace.",
                                                                        "harbor": "Thea Foss Waterway, a short walk from the venue."},
                      "The Port of Tacoma from the terrace.", "none", width="100%"),
                H(2, "Welcome to Tacoma"),
                P("Five years ago this summit started as a video call between three city data teams who wanted to stop "
                  "reinventing the same budget dashboards. This November we expect more than 900 people in the room and "
                  "another 300 online, from 41 cities, 9 tribal nations and 14 countries."),
                P("This year’s theme, “Data that survives contact with the public,” is about the unglamorous work that keeps "
                  "open data useful: documentation, privacy reviews, stable APIs and plain-language reports. We hope you leave "
                  "with at least one idea you can ship before the end of the fiscal year."),
                P("— Dana Whitfield, Program Chair, and the Cascadia Civic Data Collaborative board", "small"),
                box("sidebar", "Wi-Fi: HarborviewEvents · password summit2026\nSocial: #CascadiaData26\nHelp desk: Lobby B, "
                    "open 7:30–18:00 both days · +1 253-555-0190\nCode of conduct: cascadiadata.example/conduct", title="At a glance"),
            ],
            [
                H(2, "Program"),
                P("Sessions in Puget Hall are livestreamed and captioned. Rooms 201 and 204 hold 120 seats each; workshops "
                  "require the add-on ticket and a laptop. Session slides will be posted within a week of the summit."),
                seg[0],
            ],
            [
                seg[1],
                P("Thursday evening: the reception at the Foss Waterway Seaport is included in every conference ticket. Shuttles "
                  "leave from the Commerce Street entrance every 15 minutes from 17:15."),
                photo("ph2", ["train-station", "city-bus"], ["transport"], {"train-station": "Tacoma Dome Station: Link light rail and Sounder trains stop here.",
                                                                            "city-bus": "Pierce Transit route 1 stops outside the venue."},
                      "Getting to the venue by transit.", "left", width="40%"),
                P("By transit: take Sound Transit Link to Tacoma Dome Station and transfer to the T Line streetcar (free) to the "
                  "Commerce Street stop. From Sea-Tac Airport, allow about 70 minutes."),
                P("By car: the Park Plaza North garage on Commerce Street offers a summit rate of $14 per day; show your badge "
                  "at the exit. Bicycle racks are inside the loading dock on South 15th Street."),
            ],
            [
                seg[2],
                box("callout", "Platinum: Northwest Geodata Cooperative · Gold: Rainier Cloud Services, OpenPermit · Silver: TixHarbor, "
                    "Salish Sea Foundation, Mapleline Analytics · Community partners: Code for Tacoma, Tacoma Public Library",
                    title="Thank you to our sponsors"),
                H(2, "Accessibility"),
                L(["All rooms are step-free; an elevator is next to the Lobby B help desk.",
                   "Live captions (CART) are shown in Puget Hall and on the livestream.",
                   "A quiet room is available in Room 210 throughout both days.",
                   "ASL interpretation is provided for keynotes; request it for other sessions by November 2.",
                   "All-gender restrooms are on the second floor next to Room 204."]),
                H(2, "Posters"),
                P("Twenty-two posters will hang on the Sound View Terrace from Thursday 12:00 to Friday 14:00. Poster authors "
                  "stand by their boards during Friday lunch; voting for the people’s choice award closes at 13:00."),
                chart("c1", "bar", attendance, "Attendance has shifted back to in-person since the hybrid years.", raster=True,
                      width="70%", size=(520, 220)),
                chart_table("c1-data", "Year", attendance, lambda v: f"{v:,}"),
            ],
            [
                H(2, "Speakers"),
                columns([
                    H(3, "Nguyễn Thị Lan"),
                    photo("ph3", ["aerial-city"], ["aerial"], {"aerial-city": "Ho Chi Minh City, where the Saigon Open Data Lab maps budgets by ward."},
                          "Ho Chi Minh City.", "none", width="100%"),
                    P("Lan founded the Saigon Open Data Lab in 2019 after eight years as a statistician at the city’s finance "
                      "department. Her team publishes ward-level budgets in Vietnamese and English."),
                    H(3, "Ingrid Solberg"),
                    P("Ingrid leads the data platform team at Bergen Kommune, which has run a public API for building permits "
                      "since 2017. She maintains several open-source tools for cleaning Norwegian address data."),
                    H(3, "Rafael Montoya Ruiz"),
                    photo("ph4", ["laptop-desk"], ["technology"], {"laptop-desk": "Rafael drafts most of his opinions on public-records law at home in Bogotá."},
                          "Working from Bogotá.", "none", width="100%"),
                    P("Rafael is a professor of information law at Universidad de los Andes in Bogotá and a former adviser "
                      "to Colombia’s transparency secretariat."),
                    H(3, "Eleni Papadaki"),
                    P("Eleni coordinates the 311 service-request feed of the City of Athens and wrote its public data dictionary."),
                ], count=2),
                P("Several speakers prefer their names in their original script. Badges show both forms:"),
                table("t-names", names, rendering="borderless", widths=[30, 30, 40]),
            ],
            [
                H(2, "Tickets"),
                table("t-prices", prices, rendering="ruled", caption="Ticket prices (USD, sales tax not applicable)",
                      align=["l", "r", "r", "r"], widths=[40, 22, 19, 19]),
                P("Group example: a county data office registering six staff, four workshop seats, two student interns and "
                  "three reception guests pays:"),
                table("t-order", [["Item", "Qty", "Unit price", "Amount"], *order_rows, ["Total due", "", "", usd(total)]],
                      rendering="ruled", align=["l", "r", "r", "r"], widths=[52, 10, 18, 20], total_rows=[len(order_rows) + 1]),
                screenshot("s1", "dashboard", dashboard, "Registration dashboard on October 9, 2026 (screenshot from TixHarbor).",
                           width="88%"),
                table("t-dash", dash_rows, rendering="screenshot", caption="Sales by ticket type"),
                box("footnote", "Refunds are available until October 29, 2026, minus a $25 processing fee. Name changes are free."),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-order", "quantity": 1, "unit_price": 2, "amount": 3},
                       {"kind": "column_sum", "table": "t-order", "columns": [3], "label_column": 0, "total_label": "Total due"}],
    }


def program_hi() -> dict[str, Any]:
    """Jaipur cultural festival program in Hindi with English names (LibreOffice, tagged)."""
    sched = [
        ["शुक्र 17:00", "उद्घाटन समारोह और दीप प्रज्वलन", "मुख्य अतिथि: श्रीमती सुधा मेहता", "मुख्य मंच"],
        ["शुक्र 18:00", "राजस्थानी लोक संगीत", "Mame Khan Manganiyar Ensemble", "मुख्य मंच"],
        ["शुक्र 19:30", "कथक प्रस्तुति: ‘ऋतु संहार’", "पं. राजेंद्र गंगानी और शिष्य", "मुख्य मंच"],
        ["शुक्र 21:00", "कठपुतली प्रदर्शन", "Jaipur Kathputli Collective", "आंगन मंच"],
        ["शनि 10:00", "बच्चों के लिए ब्लॉक प्रिंटिंग कार्यशाला", "Anokhi Museum टीम", "कार्यशाला कक्ष"],
        ["शनि 11:30", "पुस्तक चर्चा: ‘मरुस्थल की कहानियाँ’", "डॉ. नंदिता शर्मा, लेखिका", "पुस्तक मंडप"],
        ["शनि 13:00", "राजस्थानी व्यंजन प्रदर्शन", "शेफ़ अर्जुन राठौड़", "भोजन प्रांगण"],
        ["शनि 15:00", "कविता पाठ: नई आवाज़ें", "युवा कवि मंच, जयपुर", "पुस्तक मंडप"],
        ["शनि 17:00", "ग़ज़ल संध्या", "उस्ताद अहमद हुसैन – मोहम्मद हुसैन", "मुख्य मंच"],
        ["शनि 19:30", "घूमर और कालबेलिया नृत्य", "Gulabo Sapera Dance Troupe", "मुख्य मंच"],
        ["रवि 07:00", "आमेर किले तक हेरिटेज वॉक", "INTACH जयपुर चैप्टर", "आमेर गेट"],
        ["रवि 10:00", "मिट्टी के बर्तन बनाने की कार्यशाला", "कुम्हार समुदाय, बगरू", "कार्यशाला कक्ष"],
        ["रवि 12:00", "पैनल: हस्तशिल्प का डिजिटल भविष्य", "Ritu Kumar, Rahul Jain, सीमा वर्मा", "पुस्तक मंडप"],
        ["रवि 15:00", "सितार और तबला जुगलबंदी", "पं. शुभेंद्र राव, उस्ताद ज़ाकिर अली", "मुख्य मंच"],
        ["रवि 17:30", "समापन: सूफ़ी कव्वाली", "Nizami Brothers", "मुख्य मंच"],
        ["रवि 19:30", "आतिशबाज़ी और धन्यवाद", "आयोजन समिति", "जल महल घाट"],
    ]
    seg = continued("t-sched", [["दिन / समय", "कार्यक्रम", "कलाकार / वक्ता", "स्थल"]], sched, [11, 5],
                    caption="कार्यक्रम सूची (6–8 नवंबर 2026)", continued_caption="कार्यक्रम सूची (जारी)", widths=[14, 36, 32, 18])
    tickets = [("दिवस पास (वयस्क)", 2, 50000), ("दिवस पास (बच्चे, 5–12 वर्ष)", 2, 20000), ("तीन दिवसीय पास (वयस्क)", 1, 120000),
               ("कार्यशाला शुल्क", 3, 35000), ("पार्किंग (प्रति दिन)", 3, 10000)]
    t_rows = [[name, str(q), inr(u), inr(q * u)] for name, q, u in tickets]
    t_total = sum(q * u for _, q, u in tickets)
    sponsor = [["प्रायोजन श्रेणी", "राशि", "लाभ"],
               ["स्वर्ण प्रायोजक", inr(1000000_00), "मुख्य मंच पर नाम, 40 पास, स्टॉल"],
               ["रजत प्रायोजक", inr(500000_00), "बैनर, 20 पास, स्टॉल"],
               ["कांस्य प्रायोजक", inr(250000_00), "बैनर, 10 पास"],
               ["सामुदायिक सहयोगी", inr(50000_00), "कार्यक्रम पुस्तिका में नाम"]]
    visitors = {"title": "दर्शक संख्या (हज़ार में)", "categories": ["2022", "2023", "2024", "2025"],
                "series": [("दर्शक", [38, 52, 61, 74])], "max": 80, "ticks": 4, "tick_format": lambda v: f"{v:.0f}"}
    return {
        "template": "event_program", "page_size": "A4", "languages": ["hi-IN", "en"], "tagged": True,
        "metadata": {"title": "रंगसंगम सांस्कृतिक महोत्सव 2026 — कार्यक्रम पुस्तिका", "author": "रंगसंगम कला न्यास, जयपुर",
                     "subject": "तीन दिवसीय सांस्कृतिक महोत्सव का कार्यक्रम, टिकट और जानकारी",
                     "keywords": ["महोत्सव", "जयपुर", "लोक संगीत", "कार्यक्रम"], "lang": "hi-IN", "created": "2026-10-05T06:30:00Z"},
        "theme": {"accent": "#9c2f5a", "lo_size": "10pt", "lo_font": "Noto Sans"},
        "running_header": "रंगसंगम सांस्कृतिक महोत्सव 2026 · जवाहर कला केंद्र, जयपुर",
        "running_footer": "rangsangam.example · पृष्ठ {page} / {pages}",
        "pages": [
            [
                P("रंगसंगम सांस्कृतिक महोत्सव 2026", "brand"),
                P("6–8 नवंबर 2026 · जवाहर कला केंद्र, जवाहरलाल नेहरू मार्ग, जयपुर 302004 · हेल्पलाइन 0141 555 0168", "small"),
                H(1, "कार्यक्रम पुस्तिका"),
                photo("ph1", ["garden-flowers", "park-path"], ["garden"], {"garden-flowers": "जवाहर कला केंद्र के उद्यान में गेंदे की सजावट",
                                                                         "park-path": "आंगन मंच तक जाने वाला छायादार रास्ता"},
                      "केंद्र का उद्यान", "none", width_cm=12.5),
                H(2, "स्वागत संदेश"),
                P(f"प्रिय कला-प्रेमियों, रंगसंगम के पाँचवें संस्करण में आपका हार्दिक स्वागत है। इस वर्ष तीन दिनों में चालीस से अधिक "
                  f"प्रस्तुतियाँ होंगी — राजस्थान के लोक संगीत से लेकर सूफ़ी क़व्वाली तक। हमारा प्रयास है कि हर पीढ़ी को अपनी "
                  f"सांस्कृतिक विरासत से जुड़ने का अवसर मिले, और शिल्पकारों को सीधे दर्शकों तक पहुँचने का मंच मिले। "
                  f"इस बार ‘द्{ZWJ}वार’ नाम का नया प्रांगण बनाया गया है जहाँ बगरू और सांगानेर के कारीगर अपना काम दिखाएँगे।"),
                P("— मीनाक्षी राठौड़, अध्यक्ष, रंगसंगम कला न्यास (Rangsangam Arts Trust)", "small"),
                box("callout", "प्रवेश द्वार: गेट नंबर 2 (जवाहरलाल नेहरू मार्ग) · टिकट काउंटर सुबह 9 बजे से · सुरक्षा जाँच अनिवार्य · "
                    "क्‌षमा करें, पालतू जानवरों को अंदर लाने की अनुमति नहीं है।", title="महत्वपूर्ण सूचना"),
            ],
            [
                H(2, "कार्यक्रम सूची"),
                P("सभी कार्यक्रम निर्धारित समय पर शुरू होंगे। मुख्य मंच पर बैठने की व्यवस्था ‘पहले आओ, पहले पाओ’ के आधार पर है। "
                  "Workshops require advance booking at the help desk."),
                seg[0],
                box("footnote", "* कार्यक्रम में बदलाव की सूचना महोत्सव ऐप और मुख्य द्वार के सूचना पट्ट पर दी जाएगी।"),
                H(3, "इस वर्ष के मुख्य आकर्षण"),
                L(["पहली बार कालबेलिया और घूमर की संयुक्त प्रस्तुति",
                   "‘मरुस्थल की कहानियाँ’ पुस्तक का लोकार्पण",
                   "बगरू के कारीगरों के साथ ब्लॉक प्रिंटिंग — बच्चों के लिए निःशुल्क",
                   "रविवार सुबह आमेर किले तक हेरिटेज वॉक (सीमित स्थान)"]),
            ],
            [
                seg[1],
                H(2, "कलाकार परिचय"),
                photo("ph2", ["mountain-lake", "park-path"], ["landscape"], {"mountain-lake": "थार की झील के किनारे रिहर्सल",
                                                                            "park-path": "आंगन मंच के पास का उद्यान"},
                      "रिहर्सल स्थल", "right", width_cm=6.0),
                P("**Mame Khan Manganiyar** जैसलमेर के सत्तू गाँव से आते हैं और मांगणियार परंपरा की चौदहवीं पीढ़ी के गायक हैं। "
                  "उन्होंने कान फ़िल्म महोत्सव सहित दुनिया भर के मंचों पर प्रस्तुति दी है।"),
                P("**डॉ. नंदिता शर्मा** राजस्थान विश्वविद्यालय में हिंदी साहित्य की प्राध्यापक हैं। उनका नया कहानी-संग्रह "
                  "‘मरुस्थल की कहानियाँ’ इसी महोत्सव में लोकार्पित होगा।"),
                P("**Gulabo Sapera** कालबेलिया नृत्य को विश्व मंच तक ले जाने वाली कलाकार हैं; 2016 में उन्हें पद्मश्री से "
                  "सम्मानित किया गया।"),
                P("**पं. शुभेंद्र राव** पं. रवि शंकर के शिष्य हैं और सितार पर शास्त्रीय तथा समकालीन संगीत के प्रयोगों के लिए "
                  "जाने जाते हैं। रविवार की जुगलबंदी में उनके साथ जयपुर घराने के तबला वादक उस्ताद ज़ाकिर अली होंगे।"),
                P("**Nizami Brothers** दिल्ली की हज़रत निज़ामुद्दीन दरगाह की क़व्वाली परंपरा से जुड़े हैं। समापन संध्या में वे "
                  "अमीर ख़ुसरो की रचनाएँ प्रस्तुत करेंगे।"),
                box("callout", "भोजन प्रांगण में राजस्थान के बारह ज़िलों के पारंपरिक व्यंजन — दाल-बाटी-चूरमा, गट्टे की सब्ज़ी, "
                    "केर-सांगरी और घेवर — शाम 6 बजे से रात 10 बजे तक उपलब्ध रहेंगे।", title="स्वाद राजस्थान का"),
            ],
            [
                H(2, "टिकट और शुल्क"),
                table("t-ticket-prices", [["टिकट", "मूल्य"], ["दिवस पास (वयस्क)", inr(50000)], ["दिवस पास (बच्चे, 5–12 वर्ष)", inr(20000)],
                                          ["तीन दिवसीय पास (वयस्क)", inr(120000)], ["कार्यशाला शुल्क (प्रति व्यक्ति)", inr(35000)],
                                          ["वरिष्ठ नागरिक (65+) और दिव्यांगजन", "निःशुल्क"]],
                      rendering="borderless", align=["l", "r"], widths=[70, 30]),
                P("उदाहरण: चार सदस्यों वाले एक परिवार का शनिवार का ख़र्च —"),
                table("t-family", [["मद", "संख्या", "दर", "राशि"], *t_rows, ["कुल", "", "", inr(t_total)]], rendering="ruled",
                      align=["l", "r", "r", "r"], widths=[46, 14, 18, 22], total_rows=[len(t_rows) + 1]),
                table("t-sponsor", sponsor, rendering="ruled", caption="प्रायोजन पैकेज (राशि रुपये में, GST अतिरिक्त)",
                      align=["l", "r", "l"], widths=[28, 22, 50]),
                chart("c1", "bar", visitors, "पिछले चार वर्षों में दर्शकों की संख्या", raster=True, width_cm=10.5, size=(440, 200)),
                chart_table("c1-data", "वर्ष", visitors, lambda v: f"{v}"),
                L(["निकटतम मेट्रो स्टेशन: राम नगर (1.2 किमी)", "निःशुल्क पेयजल और प्राथमिक चिकित्सा केंद्र गेट 2 के पास",
                   "खोई हुई वस्तुएँ: सूचना केंद्र, फ़ोन 0141 555 0169"]),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-family", "quantity": 1, "unit_price": 2, "amount": 3},
                       {"kind": "column_sum", "table": "t-family", "columns": [3], "label_column": 0, "total_label": "कुल"}],
    }


def program_ar() -> dict[str, Any]:
    """Doha book fair program in Arabic (Chromium, RTL) with Latin affiliations wrapped in LRM marks."""
    def aff(text: str) -> str:
        return f"{LRM}{text}{LRM}"

    def t(h: int, m: int, h2: int, m2: int) -> str:
        return f"{h:02d}:{m:02d} – {h2:02d}:{m2:02d}".translate(_AR_DIGITS)

    sched = [
        [t(10, 0, 10, 45), "حفل الافتتاح الرسمي", "سعادة وزير الثقافة", "القاعة الكبرى"],
        [t(11, 0, 12, 0), "مستقبل النشر العربي في العصر الرقمي", f"د. ليلى الحربي — {aff('Qatar University')}", "القاعة الكبرى"],
        [t(12, 0, 13, 0), "ورشة: كتابة القصة القصيرة للناشئة", "أ. يوسف المرزوقي", "قاعة الورش ١"],
        [t(13, 0, 14, 0), "حوار مع الروائي حسن بلال", f"تقديم: سارة الكعبي — {aff('Al Jazeera')}", "منصة الحوار"],
        [t(14, 30, 15, 30), "الترجمة الأدبية بين العربية والإسبانية", f"Carmen Ruiz — {aff('Universidad de Granada')}", "القاعة الكبرى"],
        [t(16, 0, 17, 0), "توقيع كتب: إصدارات دار الريان", "مجموعة من المؤلفين", "جناح ب١٢"],
        [t(17, 0, 18, 0), "أمسية شعرية", "الشاعرة نجاة الزهراني", "منصة الحوار"],
        [t(18, 30, 19, 30), "مكتبات المستقبل والذكاء الاصطناعي", f"م. عمر الشهري — {aff('Qatar National Library')}", "القاعة الكبرى"],
        [t(10, 0, 11, 0), "حكايات للأطفال من التراث القطري", "أ. مريم السليطي", "ركن الطفل"],
        [t(11, 0, 12, 0), "صناعة الكتاب الصوتي", f"James Whitmore — {aff('Audible Studios')}", "قاعة الورش ٢"],
        [t(12, 0, 13, 30), "ندوة: حقوق المؤلف في البيئة الرقمية", f"د. خالد العتيبي — {aff('WIPO Arab Bureau')}", "القاعة الكبرى"],
        [t(14, 0, 15, 0), "الخط العربي: ورشة تطبيقية", "الخطاط إبراهيم النعيمي", "قاعة الورش ١"],
        [t(15, 30, 16, 30), "أدب الرحلة: من ابن بطوطة إلى المدونات", "د. فاطمة المنصوري", "منصة الحوار"],
        [t(17, 0, 18, 30), "حفل توزيع جوائز المعرض", "لجنة التحكيم", "القاعة الكبرى"],
    ]
    seg = continued("t-sched", [["الوقت", "الفعالية", "المتحدث", "المكان"]], sched, [8, 6],
                    caption="جدول الفعاليات — اليوم الأول (الخميس ١٢ نوفمبر)",
                    continued_caption="تابع: فعاليات اليوم الثاني (الجمعة ١٣ نوفمبر)", widths=[17, 37, 30, 16])
    tickets = [("تذكرة دخول يومية (بالغ)", 4, 2000), ("تذكرة دخول يومية (طالب)", 3, 1000), ("ورشة الخط العربي", 2, 7500),
               ("ورشة الكتاب الصوتي", 1, 9000)]
    rows = [[name, ar_num(q), qar(u), qar(q * u)] for name, q, u in tickets]
    total = sum(q * u for _, q, u in tickets)
    visitors = {"title": "عدد الزوار (بالألف)", "categories": ["2022", "2023", "2024", "2025"],
                "series": [("الزوار", [182, 215, 241, 268])], "max": 300, "ticks": 3, "tick_format": lambda v: ar_num(int(v))}
    return {
        "template": "event_program", "page_size": "A4", "languages": ["ar", "en", "es"], "dir": "rtl",
        "metadata": {"title": "معرض الخليج الدولي للكتاب ٢٠٢٦ — دليل البرنامج", "author": "اللجنة المنظمة لمعرض الخليج الدولي للكتاب",
                     "subject": "برنامج الفعاليات الثقافية والندوات وأسعار التذاكر", "keywords": ["معرض الكتاب", "الدوحة", "ندوات", "برنامج"],
                     "lang": "ar", "created": "2026-10-20T08:00:00Z"},
        "theme": {"accent": "#6b3d1e", "font_size": "10.5pt", "margins": "16mm 16mm 18mm 16mm"},
        "running_header": "معرض الخليج الدولي للكتاب ٢٠٢٦ · مركز الدوحة للمعارض والمؤتمرات",
        "running_footer": "الصفحة {page} من {pages}",
        "pages": [
            [
                P("معرض الخليج الدولي للكتاب", "brand"),
                P(f"الدورة الحادية عشرة · ١٢–٢١ نوفمبر ٢٠٢٦ · مركز الدوحة للمعارض والمؤتمرات · {LRM}gulfbookfair.example{RLM}", "small"),
                H(1, "دليل البرنامج الثقافي"),
                photo("ph1", ["library-shelves"], ["civic"], {"library-shelves": "رفوف دور النشر المشاركة في الجناح الرئيسي"},
                      "رفوف دور النشر", "none", width="46%"),
                H(2, "كلمة الترحيب"),
                P("يسعدنا أن نرحب بكم في الدورة الحادية عشرة من معرض الخليج الدولي للكتاب، التي تجمع هذا العام أكثر من "
                  "٥٠٠ دار نشر من ٣٨ دولة تحت شعار «القراءة جسرٌ بين الأجيال». يتضمن البرنامج الثقافي ما يزيد على ١٢٠ "
                  "فعالية بين ندوات وأمسيات شعرية وورش عمل للكبار والصغار."),
                P(f"ونخص بالشكر ضيف شرف هذه الدورة، المملكة الإسبانية، التي يقدّم جناحها مختارات من الأدب الأندلسي "
                  f"المترجم، إضافة إلى ندوة عن الترجمة الأدبية تشارك فيها الأستاذة كارمن رويث من {aff('Universidad de Granada')}."),
                P("— د. عبد الله الكواري، رئيس اللجنة المنظمة", "small"),
                box("sidebar", f"ساعات العمل: يوميًا من ٩:٠٠ ص (الجمعة من ٤:٠٠ م)، والتفاصيل في الصفحة ٤\n"
                    f"الهاتف: {LRM}+974 4555 0123{LRM}\nالوسم: {LRM}#GulfBookFair26{LRM}", title="معلومات سريعة", cls="wide"),
            ],
            [
                H(2, "جدول الفعاليات"),
                P("جميع الندوات مجانية لحاملي تذكرة الدخول، أما الورش فتتطلب حجزًا مسبقًا عبر تطبيق المعرض. تُقدَّم "
                  "ترجمة فورية إلى الإنجليزية في القاعة الكبرى."),
                seg[0],
                box("callout", "يستضيف ركن الطفل يوميًا من الساعة ٤:٠٠ إلى ٨:٠٠ مساءً جلسات قراءة تفاعلية وعروض دمى. "
                    "الدخول مجاني للأطفال دون ١٢ عامًا برفقة ذويهم.", title="ركن الطفل", cls="note"),
                H(2, "دليل القاعات"),
                table("t-halls", [["القاعة", "الموقع", "السعة", "ملاحظات"],
                                  ["القاعة الكبرى", "الدور الأرضي، المدخل الشمالي", f"{ar_num(800)} مقعد", "ترجمة فورية إلى الإنجليزية"],
                                  ["منصة الحوار", "وسط الجناح الرئيسي", f"{ar_num(150)} مقعدًا", "جلسات مفتوحة دون حجز"],
                                  ["قاعة الورش ١", "الطابق الأول — الجناح الشرقي", f"{ar_num(40)} مقعدًا", "حجز مسبق"],
                                  ["قاعة الورش ٢", "الطابق الأول — الجناح الغربي", f"{ar_num(40)} مقعدًا", "حجز مسبق"],
                                  ["ركن الطفل", "الجناح ج — بجوار المطاعم", f"{ar_num(120)} طفلًا", "برفقة ولي الأمر"]],
                      rendering="borderless", widths=[20, 34, 18, 28]),
                P("تقع أجنحة دور النشر العربية في القاعتين ١ و٢، بينما تضم القاعة ٣ دور النشر الأجنبية وجناح ضيف الشرف. "
                  "تتوفر خرائط مطبوعة عند مكاتب الاستعلامات عند كل مدخل، كما يمكن البحث عن أي دار نشر برقم جناحها في تطبيق المعرض."),
            ],
            [
                seg[1],
                H(2, "ضيوف البرنامج"),
                photo("ph2", ["paper-documents", "whiteboard"], ["document"], {"paper-documents": "مخطوطات معروضة في جناح ضيف الشرف",
                                                                              "whiteboard": "ورشة الكتابة الإبداعية"},
                      "مخطوطات جناح ضيف الشرف", "left", width="38%"),
                P(f"**د. ليلى الحربي** أستاذة الإعلام الرقمي في {aff('Qatar University')}، صدر لها كتاب «الناشر الذكي» عام ٢٠٢٤."),
                P(f"**كارمن رويث** ({aff('Carmen Ruiz')}) مترجمة إسبانية نقلت أكثر من عشرين عملًا عربيًا إلى الإسبانية، "
                  "وحازت جائزة الشيخ حمد للترجمة."),
                P(f"**م. عمر الشهري** مدير الخدمات الرقمية في {aff('Qatar National Library')}، ويقود مشروع رقمنة المخطوطات الخليجية."),
                P(f"**جيمس ويتمور** ({aff('James Whitmore')}) منتج في {aff('Audible Studios')} بلندن، أشرف على تسجيل أكثر من "
                  "مئتي كتاب صوتي بالعربية والإنجليزية."),
                P("**الخطاط إبراهيم النعيمي** حاصل على إجازة في خطَّي الثلث والنسخ من إسطنبول، ويدرّس الخط العربي في الدوحة منذ "
                  "خمسة عشر عامًا."),
                box("callout", "تُعلن جوائز المعرض في ختام اليوم الثاني في خمس فئات: الرواية، والشعر، وكتاب الطفل، والترجمة، "
                    f"وأفضل دار نشر ناشئة. تبلغ قيمة الجائزة الكبرى {qar(10000000)}.", title="جوائز المعرض"),
            ],
            [
                H(2, "التذاكر والأسعار"),
                P("مثال على تكلفة زيارة عائلية مع حجز ورشتين (الأسعار بالريال القطري):"),
                table("t-tickets", [["البند", "العدد", "سعر الوحدة", "المبلغ"], *rows, ["الإجمالي", "", "", qar(total)]],
                      rendering="ruled", align=["l", "r", "r", "r"], widths=[46, 12, 20, 22], total_rows=[len(rows) + 1]),
                chart("c1", "bar", visitors, "تطور عدد زوار المعرض خلال السنوات الأربع الماضية", raster=True, width="62%", size=(460, 210)),
                chart_table("c1-data", "السنة", visitors, ar_num),
                box("callout", f"{aff('Qatar Airways')} · {aff('Ooredoo')} · بنك الدوحة · دار الريان للنشر · مؤسسة قطر",
                    title="الرعاة"),
                H(2, "مواعيد الزيارة"),
                table("t-hours", [["اليوم", "الفترة الصباحية", "الفترة المسائية"],
                                  ["السبت – الأربعاء", "٩:٠٠ ص – ١:٠٠ م", "٤:٠٠ م – ١٠:٠٠ م"],
                                  ["الخميس", "٩:٠٠ ص – ١:٠٠ م", "٤:٠٠ م – ١١:٠٠ م"],
                                  ["الجمعة", "مغلق", "٤:٠٠ م – ١٠:٠٠ م"],
                                  ["الثلاثاء ١٧ نوفمبر", "مخصص للمدارس", "٤:٠٠ م – ١٠:٠٠ م"]],
                      rendering="borderless", widths=[34, 33, 33]),
                H(2, "معلومات عملية"),
                L(["مواقف مجانية في المواقف الشمالية مع حافلات ترددية كل ١٠ دقائق",
                   "محطة المترو الأقرب: مركز الدوحة للمعارض (الخط الأحمر)",
                   "يتوفر مصلى ومطاعم في الطابق الأرضي",
                   f"شبكة الإنترنت اللاسلكية: {LRM}GBF-Guest{LRM} دون كلمة مرور"]),
                box("footnote", "* الأسعار شاملة للرسوم، والدخول مجاني لكبار السن وذوي الإعاقة ومرافقيهم. لا تُستردّ قيمة التذاكر بعد الاستخدام."),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-tickets", "quantity": 1, "unit_price": 2, "amount": 3, "decimal": "٫"},
                       {"kind": "column_sum", "table": "t-tickets", "columns": [3], "label_column": 0, "total_label": "الإجمالي"}],
    }


def program_pl() -> dict[str, Any]:
    """Gdańsk urban-futures conference program in Polish (Chromium) with a ticket-sales spreadsheet screenshot."""
    sched = [
        ["Śr 8:30–9:30", "Rejestracja i poranna kawa", "—", "Foyer"],
        ["Śr 9:30–10:00", "Otwarcie konferencji", "Agnieszka Kowalczyk, prezydent Fundacji", "Sala A"],
        ["Śr 10:00–11:00", "Wykład otwierający: Miasto 15-minutowe w praktyce", "prof. Carlos Moreno (online)", "Sala A"],
        ["Śr 11:15–12:15", "Zieleń błękitna: retencja wody w dzielnicach", "dr inż. Paweł Zieliński, Politechnika Gdańska", "Sala A"],
        ["Śr 11:15–12:15", "Warsztat: budżet obywatelski krok po kroku", "Marta Wójcik, Urząd Miasta Gdyni", "Sala B"],
        ["Śr 12:15–13:15", "Obiad", "—", "Restauracja „Żuraw”"],
        ["Śr 13:15–14:30", "Panel: transport publiczny po 2030 roku", "Łukasz Grabowski (moderacja)", "Sala A"],
        ["Śr 14:45–15:45", "Dane o jakości powietrza w czasie rzeczywistym", "Ewa Lewandowska, Airly", "Sala B"],
        ["Śr 16:00–17:00", "Rewitalizacja terenów postoczniowych", "Jakub Dąbrowski, Biuro Rozwoju Gdańska", "Sala A"],
        ["Śr 19:00–22:00", "Kolacja konferencyjna", "—", "Hala 90B"],
        ["Czw 9:00–10:00", "Mieszkalnictwo społeczne w Wiedniu i w Polsce", "Katharina Gruber, Wiener Wohnen", "Sala A"],
        ["Czw 10:15–11:15", "Miasta dostępne dla wszystkich", "Zofia Mazur, Fundacja Integracja", "Sala A"],
        ["Czw 10:15–11:15", "Warsztat: mapowanie upałów z mieszkańcami", "Tomasz Kamiński, Miejskie Laboratorium", "Sala B"],
        ["Czw 11:30–12:30", "Energetyka obywatelska i spółdzielnie", "Ingrid Solberg, Bergen Kommune", "Sala A"],
        ["Czw 12:30–13:30", "Obiad", "—", "Restauracja „Żuraw”"],
        ["Czw 13:30–14:30", "Debata oksfordzka: samochód w centrum miasta", "drużyny studenckie UG i PG", "Sala A"],
        ["Czw 14:45–15:30", "Podsumowanie i zamknięcie", "Agnieszka Kowalczyk", "Sala A"],
    ]
    seg = continued("t-sched", [["Dzień i godzina", "Temat", "Prelegent", "Sala"]], sched, [10, 7],
                    caption="Program konferencji, 21–22 października 2026", continued_caption="Program konferencji (cd.)",
                    widths=[16, 40, 30, 14])
    prices = [("Bilet standardowy (2 dni)", 3, 89000), ("Bilet dla samorządów (2 dni)", 5, 59000), ("Bilet studencki", 4, 19000),
              ("Kolacja konferencyjna", 6, 18000)]
    rows = [[name, str(q), pln(u), pln(q * u)] for name, q, u in prices]
    net = sum(q * u for _, q, u in prices)
    vat = round(net * 0.23)
    rows += [["Razem netto", "", "", pln(net)]]
    sheet_rows = [["Kategoria", "Sprzedane", "Pula", "Przychód netto"],
                  ["Standard", "214", "300", "190 460,00 zł"],
                  ["Samorządy", "168", "200", "99 120,00 zł"],
                  ["Studenci", "97", "120", "18 430,00 zł"],
                  ["Kolacja", "251", "280", "45 180,00 zł"],
                  ["Razem", "730", "900", "353 190,00 zł"]]
    editions = {"title": "Uczestnicy konferencji", "categories": ["2023", "2024", "2025", "2026"],
                "series": [("Na miejscu", [280, 410, 560, 730]), ("Online", [450, 390, 340, 300])], "max": 800, "ticks": 4,
                "tick_format": lambda v: number(v, "pl", 0)}
    sheet = {"title": "sprzedaz_biletow_MP2026.xlsx", "menu": ["Plik", "Edycja", "Widok", "Wstaw", "Format", "Dane", "Pomoc"],
             "cell": "D7", "formula": "=SUMA(D3:D6)", "tabs": ["Podsumowanie", "Zamówienia", "Faktury"],
             "rows": sheet_rows, "numeric": [False, True, True, True], "selected_row": 6, "width": 640, "lang": "pl"}
    return {
        "template": "event_program", "page_size": "A4", "languages": ["pl-PL", "en"],
        "metadata": {"title": "Miasto Przyszłości 2026 — program konferencji", "author": "Fundacja Miasto Przyszłości",
                     "subject": "Program, prelegenci, bilety i informacje praktyczne, Gdańsk 21–22 października 2026",
                     "keywords": ["konferencja", "Gdańsk", "urbanistyka", "program"], "lang": "pl-PL", "created": "2026-10-01T07:15:00Z"},
        "theme": {"accent": "#1d4f91", "font_size": "9.8pt", "body_font": "'Noto Sans'", "margins": "15mm 16mm 17mm 16mm"},
        "running_header": "Konferencja „Miasto Przyszłości 2026” · Gdańsk",
        "running_footer": "miastoprzyszlosci.example · strona {page} z {pages}",
        "pages": [
            [
                P("Miasto Przyszłości 2026", "brand"),
                P("21–22 października 2026 · Centrum Konferencyjne „Stocznia”, ul. Doki 1, 80-863 Gdańsk", "small"),
                H(1, "Program konferencji"),
                photo("ph1", ["aerial-city", "city-street"], ["civic"], {"aerial-city": "Gdańsk z lotu ptaka: Wyspa Spichrzów i Młode Miasto.",
                                                                         "city-street": "Ulica Długa w Gdańsku."},
                      "Gdańsk z lotu ptaka.", "none", width="100%"),
                H(2, "Słowo wstępne"),
                columns([
                    P("Drodzy Uczestnicy, po raz czwarty spotykamy się w Gdańsku, aby rozmawiać o mieście, które chcemy zostawić "
                      "następnym pokoleniom. Tegoroczna edycja skupia się na trzech wyzwaniach: adaptacji do zmian klimatu, "
                      "dostępnym mieszkalnictwie i transporcie, który nie wyklucza nikogo."),
                    P("Na terenach dawnej stoczni — tam, gdzie w 1980 roku rodziła się „Solidarność” — gościmy ponad 700 osób z "
                      "samorządów, uczelni i organizacji pozarządowych z 11 krajów. Dziękujemy partnerom, wolontariuszom i "
                      "wszystkim prelegentom, którzy dzielą się swoim doświadczeniem."),
                    P("— Agnieszka Kowalczyk, prezes Fundacji Miasto Przyszłości", "small"),
                ], count=2),
                H(2, "Trzy ścieżki tematyczne"),
                L(["**Klimat i woda** — retencja, zieleń, upały w mieście (Sala A i warsztaty w Sali B)",
                   "**Mieszkać godnie** — mieszkalnictwo społeczne, rewitalizacja, dostępność",
                   "**Ruch bez wykluczeń** — transport publiczny, rower, piesi, dane w czasie rzeczywistym"]),
                box("sidebar", "Rejestracja: foyer, od 8:30 w obu dniach\nTłumaczenie PL ⇄ EN: kanał 2\nInfolinia: +48 58 555 01 26\n"
                    "Organizator: Fundacja Miasto Przyszłości, ul. Długie Ogrody 12, 80-765 Gdańsk", title="W skrócie", cls="wide"),
            ],
            [
                H(2, "Program"),
                P("Wszystkie wystąpienia w Sali A są tłumaczone symultanicznie na język angielski (kanał 2 na słuchawkach). "
                  "Na warsztaty w Sali B obowiązują zapisy w punkcie rejestracji."),
                seg[0],
                box("callout", "Kolacja konferencyjna w Hali 90B rozpocznie się o 19:00. Autobus wahadłowy odjeżdża sprzed wejścia "
                    "głównego o 18:40 i 18:50. Wstęp za okazaniem identyfikatora z oznaczeniem ★.", title="Wieczór 21 października"),
                table("t-tracks", [["Ścieżka", "Koordynator", "Liczba sesji"], ["Klimat i woda", "dr inż. Paweł Zieliński", "6"],
                                   ["Mieszkać godnie", "Katharina Gruber", "5"], ["Ruch bez wykluczeń", "Łukasz Grabowski", "6"],
                                   ["Razem", "", "17"]], rendering="borderless", caption="Sesje według ścieżek",
                      align=["l", "l", "r"], widths=[40, 40, 20], total_rows=[4]),
            ],
            [
                seg[1],
                H(2, "Prelegenci"),
                photo("ph2", ["solar-panels"], ["energy"], {"solar-panels": "Instalacja fotowoltaiczna spółdzielni energetycznej w Bergen."},
                      "Spółdzielnia energetyczna w Bergen.", "right", width="36%"),
                P("**Ingrid Solberg** kieruje zespołem danych miejskich w Bergen. Opowie, jak norweskie spółdzielnie mieszkańców "
                  "finansują dachowe farmy słoneczne i dzielą się nadwyżkami energii."),
                P("**dr inż. Paweł Zieliński** z Politechniki Gdańskiej projektuje zbiorniki retencyjne i ogrody deszczowe. "
                  "Po powodzi w 2016 roku współtworzył gdański program „Kranówka i deszczówka”."),
                P("**Katharina Gruber** od dwudziestu lat pracuje w Wiener Wohnen, największym zarządcy mieszkań komunalnych w Europie."),
                P("**Zofia Mazur** z Fundacji Integracja audytuje dostępność przestrzeni publicznych; jej zespół sprawdził w tym roku "
                  "ponad 300 przystanków tramwajowych w Trójmieście."),
                box("sidebar", "Ewa Lewandowska · Jakub Dąbrowski · Tomasz Kamiński · Marta Wójcik · Łukasz Grabowski",
                    title="Pozostali prelegenci", cls="wide"),
                chart("c1", "line", editions, "Liczba uczestników kolejnych edycji konferencji", raster=False, width="80%", size=(520, 200)),
                chart_table("c1-data", "Edycja", editions, str),
            ],
            [
                H(2, "Bilety i rejestracja"),
                P("Przykładowe zamówienie grupowe urzędu miasta (ceny netto, faktura VAT 23%):"),
                table("t-order", [["Pozycja", "Liczba", "Cena jedn.", "Wartość"], *rows], rendering="ruled",
                      align=["l", "r", "r", "r"], widths=[48, 12, 18, 22], total_rows=[len(rows)]),
                P(f"Razem netto {pln(net)} + VAT 23% {pln(vat)} = **{pln(net + vat)} brutto**."),
                screenshot("s1", "spreadsheet", sheet, "Stan sprzedaży biletów na dzień 1 października 2026 (zrzut ekranu arkusza).",
                           width="78%"),
                table("t-sheet", sheet_rows, rendering="screenshot", caption="Sprzedaż biletów według kategorii"),
                H(2, "Informacje praktyczne"),
                L(["Dojazd: SKM do przystanku Gdańsk Stocznia, następnie 8 minut pieszo.",
                   "Parking: ograniczona liczba miejsc przy ul. Popiełuszki (40 zł za dzień).",
                   "Szatnia i pokój dla rodziców z dziećmi na parterze.",
                   "Wi-Fi: MP2026 · hasło: gdansk2026"]),
                box("footnote", "Faktury wystawiamy w ciągu 7 dni od zaksięgowania wpłaty. Rezygnacja do 7 października — zwrot 100%, "
                    "później możliwa jest wyłącznie zmiana uczestnika."),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-order", "quantity": 1, "unit_price": 2, "amount": 3, "decimal": ","},
                       {"kind": "column_sum", "table": "t-order", "columns": [3], "label_column": 0, "total_label": "Razem netto"},
                       {"kind": "sum", "terms": [["+", pln(net)], ["+", pln(vat)]], "equals": pln(net + vat)}],
    }


# ================================================================ newsletters


def newsletter_en() -> dict[str, Any]:
    """Neighborhood association newsletter (Chromium) with emoji, code-switched names and a continued events table."""
    harvest = {"title": "Community garden harvest (lb)", "categories": ["Tomatoes", "Squash", "Greens", "Beans", "Berries"],
               "series": [("2025", [412, 268, 190, 122, 75]), ("2026", [538, 301, 244, 160, 96])], "max": 600, "ticks": 4,
               "tick_format": lambda v: f"{v:.0f}"}
    budget = [("Membership dues (212 households × $25)", 530000), ("Fall festival sponsors", 245000),
              ("City of Portland neighborhood grant", 400000), ("Plant sale", 118750), ("Garden plot fees (38 × $40)", 152000)]
    spend = [("Garden water and tools", 162500), ("Newsletter printing and postage", 98400), ("Fall festival", 286000),
             ("Trail cleanup supplies", 41250), ("Insurance", 72000)]
    operating = sum(c for _, c in spend)
    reserve = sum(c for _, c in budget) - operating
    spend.append(("Reserve fund", reserve))
    b_rows = [[name, usd(c), ""] for name, c in budget] + [[name, "", usd(c)] for name, c in spend]
    total_in = sum(c for _, c in budget)
    total_out = sum(c for _, c in spend)
    events = [
        ["Sat Oct 17", "Fall Festival & chili cook-off 🌶️", "Riverbend Park pavilion", "Free"],
        ["Tue Oct 20", "Board meeting (open to all members)", "Library community room", "Free"],
        ["Sat Oct 24", "Willamette Greenway trail cleanup", "Meet at the Sellwood boat ramp", "Free"],
        ["Thu Oct 29", "Pumpkin carving for kids", "Garden shed", "$5 per pumpkin"],
        ["Sat Oct 31", "Halloween porch trail map pickup", "Riverbend Market", "Free"],
        ["Wed Nov 4", "Fix-it fair: bikes, lamps, small appliances", "St. Agatha parish hall", "Donation"],
        ["Sat Nov 7", "Seed library swap", "Sellwood Library", "Free"],
        ["Thu Nov 12", "Neighborhood emergency team training", "Fire Station 20", "Free, register"],
        ["Sun Nov 15", "Community potluck (bring a dish to share)", "Riverbend Park pavilion", "Free"],
        ["Tue Nov 17", "Board meeting and 2027 budget hearing", "Library community room", "Free"],
        ["Sat Nov 21", "Holiday wreath workshop", "Garden shed", "$18 materials"],
        ["Sat Dec 5", "Tree lighting and cocoa", "SE 13th & Tacoma plaza", "Free"],
        ["Sun Dec 13", "Winter coat drive drop-off", "Riverbend Market", "Donation"],
    ]
    seg = continued("t-events", [["Date", "Event", "Where", "Cost"]], events, [6, 7], caption="Upcoming events",
                    continued_caption="Upcoming events (continued)", widths=[14, 44, 28, 14])
    dash = {"brand": "VolunteerHub", "nav": ["Dashboard", "Shifts", "People", "Hours", "Exports"],
            "title": "Riverbend volunteers — 2026 season", "range": "Mar 1 – Oct 4, 2026",
            "kpis": [("Volunteer hours", "2,184", "+22% vs 2025"), ("Active volunteers", "167", "+31"),
                     ("Shifts filled", "94%", "+6 pts"), ("No-shows", "3%", "-2 pts")],
            "series_title": "Hours per week", "series": [22, 31, 40, 38, 55, 61, 72, 80, 77, 69, 74, 92, 88, 70, 64, 58],
            "table_title": "Top teams", "rows": [["Team", "Hours"], ["Garden crew", "812"], ["Trail stewards", "466"],
                                                  ["Festival committee", "391"], ["Newsletter delivery", "215"]], "height": 440}
    return {
        "template": "newsletter", "page_size": "Letter", "languages": ["en-US", "vi", "ar", "ja", "es"],
        "metadata": {"title": "The Riverbend Courier — Fall 2026", "author": "Riverbend Neighborhood Association",
                     "subject": "Quarterly neighborhood newsletter: trail reopening, garden harvest, budget and events",
                     "keywords": ["newsletter", "neighborhood association", "community garden", "Portland"], "lang": "en-US",
                     "created": "2026-10-05T15:00:00Z"},
        "theme": {"accent": "#1e5b3a", "font_size": "9.6pt", "body_font": "'Noto Serif'", "margins": "14mm 15mm 16mm 15mm"},
        "running_header": "The Riverbend Courier · Fall 2026 · Vol. 14, No. 3",
        "running_footer": "riverbendpdx.example · Page {page} of {pages}",
        "pages": [
            [
                P("The Riverbend Courier", "brand"),
                P("News from the Riverbend Neighborhood Association · Portland, Oregon · Fall 2026 · Free to every household", "small"),
                H(1, "Greenway trail reopens after two-year rebuild"),
                photo("ph1", ["park-path"], ["park"], {"park-path": "The new Willamette Greenway boardwalk south of the boat ramp."},
                      "The new Greenway boardwalk.", "none", width="52%"),
                columns([
                    P("After 26 months of fencing, detours and more than a few muddy shoes, the Willamette Greenway trail between "
                      "the Sellwood boat ramp and Oaks Bottom reopened on September 19. About 300 neighbors walked the new "
                      "boardwalk on opening day, and the ribbon was cut by nine-year-old Amara Okafor, who wrote the most "
                      "letters to the city asking when it would be finished."),
                    P("The $4.2 million project replaced 1,400 feet of eroding gravel path with a raised boardwalk, two "
                      "wildlife viewing platforms and lighting that switches off from 10 p.m. to protect nesting herons. Portland "
                      "Parks says the boardwalk is designed to stay dry in a 25-year flood."),
                    box("sidebar", "Trail reopens · 1\nGarden harvest record · 2\nNeighbors you should know · 3\nBudget report · 4\n"
                        "Events calendar · 4–5\nContacts · 5", title="In this issue"),
                    P("Volunteers from our Trail Stewards team will keep up the native plantings along the edge. If you can spare "
                      "two hours on a Saturday morning, sign up at [riverbendpdx.example/trail](https://riverbendpdx.example/trail) "
                      "— gloves, tools and coffee provided."),
                    P("One request from the parks crew: please keep dogs leashed on the boardwalk. The lower marsh is a "
                      "protected habitat, and the beavers were there first."),
                ], count=2),
            ],
            [
                H(2, "A record year at the community garden"),
                columns([
                    photo("ph2", ["garden-flowers"], ["garden"], {"garden-flowers": "Sunflowers along the garden fence in August."},
                          "Sunflowers along the garden fence.", "none", width="100%"),
                    P("Our 38 plots produced 1,339 pounds of food this season, up 26 percent from last year. Tomatoes did best "
                      "again, helped by a warm September and the new drip lines installed in the spring."),
                    P("About a third of the harvest went to the Sellwood Community House food pantry. Pantry coordinator "
                      "Nguyễn Văn Minh says fresh produce is always the first thing to go: “People ask for greens by name now.”"),
                    P("Shout-out to our garden captains 👩‍🌾👨‍🌾 and the Tuesday watering crew 🌻 — you kept everything "
                      "alive through the August heat dome. The waitlist for 2027 plots opens on January 10."),
                    box("callout", "“We planted the garden for vegetables. What we actually grew was a neighborhood.”\n— Rosa Delgado, "
                        "garden founder, 2012", title="Overheard at the harvest supper"),
                    P("New this year: a shared tool library in the garden shed. Members can borrow a broadfork, a wheelbarrow or the "
                      "much-loved apple press with a key code from the garden captains."),
                ], count=2),
                chart("c1", "bar", harvest, "Harvest by crop, 2025 vs 2026 (pounds, from the garden logbook).", raster=False,
                      width="80%", size=(520, 220)),
                chart_table("c1-data", "Crop", harvest, str),
            ],
            [
                H(2, "Neighbors you should know"),
                columns([
                    H(3, "Nguyễn Văn Minh"),
                    P("Minh moved to Riverbend from Đà Nẵng in 2009 and has run the food pantry since 2019. On Saturdays you’ll "
                      "find him behind the counter at Phở Riverbend, the restaurant his family opened on SE 13th Avenue."),
                    H(3, "Fatima Al-Sayed (فاطمة السيد)"),
                    P("Fatima teaches Arabic and math at Sellwood Middle School and started the homework club that meets at the "
                      "library every Tuesday and Thursday. Volunteer tutors are always welcome."),
                    H(3, "Kenji Watanabe (渡辺 健二)"),
                    photo("ph3", ["hand-tools"], ["tools"], {"hand-tools": "Kenji’s workbench at the monthly fix-it fair."},
                          "Kenji’s workbench.", "none", width="62%"),
                    P("A retired machinist, Kenji runs the fix-it fair. Last year his team repaired 214 items, from toasters to "
                      "a 1962 Singer sewing machine, and kept nearly a ton of stuff out of the landfill."),
                    H(3, "María José Fernández"),
                    P("María José chairs the festival committee and has negotiated this year’s chili cook-off down to a "
                      "strict three-alarm limit. ¡Bienvenidos todos!"),
                ], count=2),
                screenshot("s1", "dashboard", dash, "Volunteer hours this season, from our VolunteerHub dashboard.", width="86%"),
            ],
            [
                H(2, "Budget report 2026–27"),
                P("The board approved the following budget on September 15. Members can comment before the budget hearing on "
                  "November 17; the full ledger is available at the library desk."),
                table("t-budget", [["Line", "Income", "Expense"], *b_rows, ["Total", usd(total_in), usd(total_out)]],
                      rendering="ruled", align=["l", "r", "r"], widths=[60, 20, 20], total_rows=[len(b_rows) + 1]),
                P(f"Income of {usd(total_in)} minus operating expenses of {usd(operating)} leaves {usd(reserve)}, which goes into the "
                  "reserve fund line above for the playground resurfacing planned in 2028.", "small"),
                seg[0],
            ],
            [
                seg[1],
                H(2, "Letters and notices"),
                columns([
                    P("**Lost cat:** grey tabby named Biscuit, last seen near SE Spokane Street on September 30. Call Hana at "
                      "503-555-0117."),
                    P("**Thank you** to whoever returned my wallet to Riverbend Market with every card still inside. — Doug P."),
                    P("**Free:** two raised-bed frames (4 × 8 ft), cedar, you haul. Email beds@riverbendpdx.example."),
                    P("**Wanted:** volunteers to deliver this newsletter on four routes north of Tacoma Street. About one hour "
                      "per quarter."),
                ], count=2),
                box("sidebar", "Riverbend Neighborhood Association · PO Box 82014, Portland, OR 97282\nEmail: board@riverbendpdx.example · "
                    "Phone: 503-555-0142\nChair: Lauren Kim · Treasurer: Samuel Adeyemi · Newsletter: Priya Natarajan\n"
                    "Board meetings: third Tuesday of every month, 7 p.m., Sellwood Library", title="Contact us", cls="wide"),
                H(2, "From the chair"),
                columns([
                    P("This is my last Courier column as chair. After six years I am handing over to whoever the members elect in "
                      "January, and I could not be leaving at a better moment: the trail is open, the garden is full and our "
                      "reserve fund is healthy for the first time since 2019."),
                    P("Thank you to the 167 people who volunteered at least one shift this year, and to the local businesses that "
                      "sponsor the festival: Riverbend Market, Phở Riverbend, Sellwood Press and Oaks Bottom Bicycles. See you at "
                      "the potluck! — Lauren Kim"),
                ], count=2),
                P("The Riverbend Courier is printed on recycled paper by Sellwood Press and delivered by volunteers to 2,300 "
                  "households. Opinions in letters are the writers’ own.", "small muted"),
            ],
        ],
        "arithmetic": [{"kind": "column_sum", "table": "t-budget", "columns": [1, 2], "label_column": 0, "total_label": "Total"},
                       {"kind": "sum", "terms": [["+", usd(total_in)], ["-", usd(operating)]], "equals": usd(reserve)}],
    }


def newsletter_es() -> dict[str, Any]:
    """Agricultural cooperative newsletter in Spanish (LibreOffice, tagged)."""
    price = [("Cereza", 18450, 238), ("Melocotón", 26300, 92), ("Pera conferencia", 14800, 71), ("Almendra (en grano)", 3120, 512),
             ("Aceite de oliva virgen extra (l)", 4200, 865)]
    liq = [[name, number(kg, "es", 0), eur_es(cents), eur_es(kg * cents)] for name, kg, cents in price]
    liq_total = sum(kg * cents for _, kg, cents in price)
    campaign = {"title": "Kilos entregados por campaña (miles)", "categories": ["2022", "2023", "2024", "2025", "2026"],
                "series": [("Fruta dulce", [512, 468, 590, 610, 644]), ("Almendra", [38, 21, 44, 47, 52])], "max": 700, "ticks": 4,
                "tick_format": lambda v: number(v, "es", 0)}
    chat = {"channel": "Socios Coop. Valle del Jalón", "topic": "Avisos de campaña · 214 participantes",
            "messages": [("Pilar Gimeno", "07:12", "Buenos días. Hoy la báscula abre a las 7:30 por la revisión del camión."),
                         ("Javier Lasheras", "07:15", "¿Se puede entregar la pera por la tarde?"),
                         ("Pilar Gimeno", "07:16", "Sí, hasta las 19:00. Por la mañana solo melocotón."),
                         ("Rosa Embid", "08:02", "Las cajas nuevas ya están en la nave 2 👍"),
                         ("Ana Sancho (Oficina)", "09:40", "Recordad: la asamblea es el 14 de noviembre a las 18:30.")],
            "height": 330}
    events = [["Fecha", "Actividad", "Lugar", "Inscripción"],
              ["24/10/2026", "Curso de poda en verde de frutales", "Finca experimental, Morata", "Gratuita para socios"],
              ["31/10/2026", "Jornada sobre riego por goteo con sondas", "Salón de la cooperativa", "Gratuita"],
              ["07/11/2026", "Visita a la almazara durante la molturación", "Almazara, Ricla", "Plazas limitadas"],
              ["14/11/2026", "Asamblea general ordinaria", "Salón de la cooperativa", "Socios"],
              ["28/11/2026", "Feria del aceite nuevo", "Plaza de España, Ricla", "Libre"],
              ["12/12/2026", "Comida de Navidad de socios", "Restaurante El Molino", "35,00 € por persona"]]
    return {
        "template": "newsletter", "page_size": "A4", "languages": ["es-ES"], "tagged": True,
        "metadata": {"title": "El Surco nº 47 — Otoño 2026", "author": "Cooperativa Agrícola Valle del Jalón",
                     "subject": "Boletín trimestral para socios: campaña de fruta, liquidaciones, almazara y agenda",
                     "keywords": ["boletín", "cooperativa", "fruta", "aceite", "Aragón"], "lang": "es-ES", "created": "2026-10-08T08:00:00Z"},
        "theme": {"accent": "#7b5b14", "lo_size": "10pt", "lo_font": "Noto Serif"},
        "running_header": "El Surco · Boletín de la Cooperativa Agrícola Valle del Jalón · nº 47",
        "running_footer": "Página {page} de {pages}",
        "pages": [
            [
                P("El Surco", "brand"),
                P("Boletín de la Cooperativa Agrícola Valle del Jalón · Ricla (Zaragoza) · nº 47 · otoño de 2026", "small"),
                H(1, "Una campaña de fruta para recordar"),
                photo("ph1", ["aerial-farmland", "farm-field"], ["agriculture"], {"aerial-farmland": "Las parcelas de frutales de la vega del Jalón, vistas desde el dron de la cooperativa.",
                                                                                 "farm-field": "Campos de la vega del Jalón en junio."},
                      "La vega del Jalón.", "none", width_cm=15.0),
                columns([
                    P("La campaña 2026 cierra con 644.000 kilos de fruta dulce entregados, la cifra más alta desde que la cooperativa "
                      "lleva registros informatizados. La cereza temprana llegó una semana antes de lo habitual y, pese a la "
                      "granizada del 3 de junio en la partida de Valdemoros, la calidad media fue excelente."),
                    P("«Ha sido un año de mucho trabajo, pero el esfuerzo de todos se nota», resume el presidente, Joaquín "
                      "Aznar. La nueva línea de calibrado óptico, financiada en parte con fondos FEADER, ha permitido clasificar "
                      "hasta 14 toneladas por hora y reducir las devoluciones de los clientes en un 40 %."),
                    P("En las próximas semanas recibiréis la liquidación definitiva. Como avance, publicamos en la página 3 los "
                      "precios medios por producto y un ejemplo de liquidación de un socio tipo."),
                ], count=2),
                box("callout", "Un año más, los socios del Valle del Jalón demostráis que trabajar juntos compensa. Gracias a "
                    "todos los que habéis ayudado en la central en los días de más entrada, y a las familias que lo han hecho posible.\n"
                    "— Joaquín Aznar, presidente", title="Carta del presidente"),
            ],
            [
                H(2, "La almazara, a pleno rendimiento"),
                photo("ph2", ["factory-machinery"], ["industry"], {"factory-machinery": "La nueva batidora de la almazara, instalada en septiembre."},
                      "La nueva batidora de la almazara.", "right", width_cm=6.5),
                P("La almazara empezará a moler la variedad empeltre el 2 de noviembre. Este año estrenamos una batidora de "
                  "acero inoxidable con control de temperatura que permite trabajar por debajo de 27 °C en todo el proceso, "
                  "lo que garantiza la calificación de «extracción en frío»."),
                P("Os pedimos que entreguéis la aceituna en cajas o palots, nunca en sacos, y en un plazo máximo de 48 horas "
                  "desde la recolección. Cada entrega se analiza en el laboratorio para medir rendimiento graso y acidez."),
                box("sidebar", "Ricla, Morata, Calatorao y Lumpiaque: 312 socios activos, 1.840 hectáreas de frutal y olivar, "
                    "una almazara, una central hortofrutícola y una tienda en Ricla.", title="La cooperativa en cifras"),
                H(2, "Lo que se dice en el grupo"),
                P("El grupo de mensajería de socios se ha convertido en la forma más rápida de avisar de cambios de horario. "
                  "Esta es una conversación típica de una mañana de septiembre:"),
                screenshot("s1", "chat", chat, "Captura del grupo de avisos de socios (publicada con permiso de los participantes).",
                           width_cm=12.0),
            ],
            [
                H(2, "Avance de liquidación"),
                P("Precios medios provisionales de la campaña 2026, ya descontados los gastos de manipulación y comercialización. "
                  "El ejemplo corresponde a un socio de Morata con cuatro hectáreas de frutal y olivar."),
                table("t-liq", [["Producto", "Kilos", "Precio medio (€/kg)", "Importe"], *liq, ["Total", "", "", eur_es(liq_total)]],
                      rendering="ruled", caption="Ejemplo de liquidación", align=["l", "r", "r", "r"], widths=[40, 18, 20, 22],
                      total_rows=[len(liq) + 1]),
                P("Las cantidades se abonarán en dos pagos: el 60 % el 30 de noviembre y el resto tras la asamblea, una vez "
                  "aprobadas las cuentas.", "small"),
                chart("c1", "bar", campaign, "Evolución de las entregas de los socios en las últimas cinco campañas.", raster=True,
                      width_cm=14.0, size=(520, 220)),
                chart_table("c1-data", "Campaña", campaign, lambda v: number(v, "es", 0)),
                box("callout", "Si tenéis dudas sobre la liquidación, pasad por la oficina de lunes a viernes de 8:00 a 14:00 o "
                    "llamad al 976 555 041.", title="¿Dudas?"),
            ],
            [
                H(2, "Agenda de otoño"),
                table("t-agenda", events, rendering="borderless", caption="Próximas actividades", widths=[14, 40, 26, 20]),
                H(2, "Breves"),
                columns([
                    P("**Seguro agrario.** El plazo para contratar el seguro de olivar con Agroseguro termina el 15 de diciembre. "
                      "La cooperativa tramita la póliza sin coste adicional."),
                    P("**Tienda.** Desde noviembre, la tienda abre también los sábados de 10:00 a 13:30. Encontraréis el aceite "
                      "nuevo, almendra tostada y conservas de melocotón con hueso."),
                    P("**Relevo generacional.** Cinco jóvenes se han incorporado este año como socios. ¡Bienvenidos, y gracias por "
                      "apostar por el campo!"),
                    P("**Formación.** La Diputación ofrece cursos gratuitos de manipulador de fitosanitarios en Ricla en enero."),
                ], count=2),
                H(2, "Nuevos socios en 2026"),
                table("t-new", [["Socio", "Localidad", "Cultivo principal", "Hectáreas"],
                                ["Lucía Pérez Gil", "Ricla", "Cereza", "2,4"], ["Hugo Lasheras Embid", "Morata de Jalón", "Melocotón", "3,1"],
                                ["Nerea Sancho Royo", "Calatorao", "Olivar", "5,8"], ["Adrián Gimeno Lahoz", "Lumpiaque", "Almendro", "6,2"],
                                ["Marta Aznar Bona", "Ricla", "Pera", "1,9"]],
                      rendering="ruled", align=["l", "l", "l", "r"], widths=[34, 26, 24, 16]),
                P("Recordamos que el plazo de solicitud de nuevas altas para la campaña 2027 está abierto hasta el 31 de enero. "
                  "Los jóvenes agricultores menores de 40 años no pagan cuota de entrada el primer año."),
                box("footnote", "Cooperativa Agrícola Valle del Jalón, S. Coop. · Ctra. de Calatorao, km 2 · 50270 Ricla (Zaragoza) · "
                    "Tel. 976 555 040 · oficina@coopjalon.example · CIF F50555040"),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-liq", "quantity": 1, "unit_price": 2, "amount": 3, "decimal": ","},
                       {"kind": "column_sum", "table": "t-liq", "columns": [3], "label_column": 0, "total_label": "Total"}],
    }


def newsletter_ru() -> dict[str, Any]:
    """Corporate newsletter of a wind-energy company in Russian (Chromium)."""
    output = {"title": "Выработка, ГВт·ч", "categories": ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен"],
              "series": [("2025", [41, 38, 36, 29, 24, 19, 17, 21, 30]), ("2026", [44, 42, 39, 33, 27, 22, 20, 24, 35])],
              "max": 50, "ticks": 5, "tick_format": lambda v: f"{v:.0f}"}
    mail = {"folders": ["Входящие", "Отправленные", "Черновики", "Архив"], "subject": "Итоги третьего квартала и планы на зиму",
            "from": "Андрей Волков <a.volkov@balticwind.example>", "to": "Всем сотрудникам", "date": "5 октября 2026 г., 9:14",
            "body": ["Коллеги, добрый день!",
                     ("Третий квартал мы закрыли с выработкой 79 ГВт·ч — на 16 % больше, чем год назад. Спасибо службе эксплуатации "
                      "за то, что коэффициент готовности турбин не опускался ниже 97 %."),
                     ("Зимой главная задача — безопасность работ на высоте при обледенении. Прошу всех пройти обновлённый "
                      "инструктаж до 1 ноября."),
                     "С уважением, Андрей Волков"], "attachment": "Итоги_Q3_2026.pdf", "lang": "ru", "height": 380}
    events = [["Дата", "Событие", "Место", "Участие"],
              ["16.10.2026", "День открытых дверей для студентов БФУ", "Ветропарк «Куршская коса»", "по записи"],
              ["23.10.2026", "Турнир по мини-футболу", "СК «Балтика»", "команды отделов"],
              ["01.11.2026", "Крайний срок инструктажа по работе на высоте", "Учебный центр", "обязательно"],
              ["14.11.2026", "Субботник: посадка деревьев", "Приморский парк", "свободное"],
              ["27.12.2026", "Новогодний корпоратив", "Ресторан «Янтарь»", "сотрудники и семьи"]]
    bonus = [("Победителю конкурса рационализаторов", 1, 15000000), ("Призёрам (2-е и 3-е место)", 2, 7500000),
             ("Поощрительные премии авторам идей", 6, 1500000)]
    b_rows = [[name, str(q), rub(u), rub(q * u)] for name, q, u in bonus]
    b_total = sum(q * u for _, q, u in bonus)
    return {
        "template": "newsletter", "page_size": "A4", "languages": ["ru-RU"],
        "metadata": {"title": "Северный ветер — корпоративный вестник, октябрь 2026", "author": "АО «Балтийские ветровые системы»",
                     "subject": "Новости компании: итоги квартала, люди, конкурс рационализаторов и календарь событий",
                     "keywords": ["корпоративный вестник", "ветроэнергетика", "Калининград"], "lang": "ru-RU",
                     "created": "2026-10-06T07:30:00Z"},
        "theme": {"accent": "#14507a", "font_size": "9.8pt", "body_font": "'Noto Sans'", "margins": "15mm 15mm 17mm 15mm"},
        "running_header": "«Северный ветер» · № 10 (118) · октябрь 2026",
        "running_footer": "Корпоративный вестник АО «Балтийские ветровые системы» · стр. {page} из {pages}",
        "pages": [
            [
                P("Северный ветер", "brand"),
                P("Корпоративный вестник АО «Балтийские ветровые системы» · Калининград · № 10 (118), октябрь 2026", "small"),
                H(1, "Квартал рекордной выработки"),
                photo("ph1", ["solar-panels"], ["energy"], {"solar-panels": "Гибридная площадка в Зеленоградске: солнечные панели у подножия ветроустановок."},
                      "Гибридная площадка в Зеленоградске.", "none", width="100%"),
                columns([
                    P("За июль — сентябрь ветропарки компании выработали 79 ГВт·ч электроэнергии — на 16 % больше, чем за тот же "
                      "период 2025 года. Основной вклад внесли четыре новые турбины мощностью 4,2 МВт на площадке «Куршская "
                      "коса», введённые в эксплуатацию в мае."),
                    P("Коэффициент использования установленной мощности составил 31,4 % против 28,9 % годом ранее. По словам "
                      "главного инженера Ирины Соколовой, это результат перехода на предиктивное обслуживание редукторов: "
                      "датчики вибрации теперь предупреждают о неисправности за две-три недели."),
                    P("В сентябре компания также подписала соглашение с портом Балтийск о поставке «зелёной» энергии для "
                      "электрификации причальных кранов — первый подобный контракт в регионе."),
                ], count=2),
                box("sidebar", "Итоги квартала — 1\nПисьмо генерального директора — 2\nЛюди компании — 3\nКонкурс "
                    "рационализаторов — 3\nКалендарь — 4", title="В номере", cls="wide"),
            ],
            [
                H(2, "Письмо генерального директора"),
                screenshot("s1", "email", mail, "Письмо Андрея Волкова сотрудникам от 5 октября (снимок экрана почтового клиента).",
                           width="82%"),
                H(2, "Выработка по месяцам"),
                chart("c1", "line", output, "Месячная выработка электроэнергии в 2025 и 2026 годах, ГВт·ч.", raster=False, width="86%",
                      size=(540, 230)),
                chart_table("c1-data", "Месяц", output, str),
                P("Весенний и летний спад выработки — сезонная закономерность для Балтики: средняя скорость ветра в июле "
                  "почти вдвое ниже январской. Зимние месяцы традиционно дают до 45 % годового объёма."),
                table("t-parks", [["Площадка", "Турбин", "Мощность, МВт", "Выработка Q3, ГВт·ч"],
                                  ["Куршская коса", "12", "46,2", "36,8"], ["Зеленоградск", "8", "24,0", "19,1"],
                                  ["Ушаково", "6", "15,0", "11,9"], ["Приморск", "5", "14,5", "11,2"],
                                  ["Итого", "31", "99,7", "79,0"]], rendering="ruled", caption="Выработка по площадкам за III квартал",
                      align=["l", "r", "r", "r"], widths=[34, 16, 22, 28], total_rows=[5]),
            ],
            [
                H(2, "Люди компании"),
                photo("ph2", ["factory-machinery", "hand-tools"], ["industry"], {"factory-machinery": "Ремонтный цех в Гурьевске, где восстанавливают редукторы.",
                                                                               "hand-tools": "Инструмент бригады верхолазов."},
                      "Ремонтный цех в Гурьевске.", "left", width="40%"),
                P("**Дмитрий Кузнецов**, бригадир службы эксплуатации, отработал в компании десять лет. За это время он поднимался "
                  "на гондолы турбин больше 1 200 раз — в сумме это примерно 120 километров по вертикали."),
                P("«Самое сложное — не высота, а погода. Ветер у нас меняется за полчаса, поэтому мы всегда держим запас по "
                  "времени и никогда не торопимся», — говорит Дмитрий."),
                box("callout", "«Хорошая идея не обязана быть большой. Иногда одна новая заглушка экономит неделю простоя».\n"
                    "— Елена Морозова, руководитель отдела качества", title="Цитата месяца"),
                H(2, "Конкурс рационализаторов"),
                P("Жюри рассмотрело 37 предложений. Первое место заняла идея техника Павла Орлова — термочехол для датчиков "
                  "ветра, который предотвращает их обледенение. Призовой фонд конкурса распределён так:"),
                table("t-bonus", [["Премия", "Кол-во", "Сумма", "Итого"], *b_rows, ["Призовой фонд", "", "", rub(b_total)]],
                      rendering="ruled", align=["l", "r", "r", "r"], widths=[52, 12, 18, 18], total_rows=[len(b_rows) + 1]),
                H(2, "Добро пожаловать в команду"),
                L(["Алина Захарова — инженер-аналитик, служба эксплуатации",
                   "Тимур Хасанов — техник-верхолаз, площадка «Ушаково»",
                   "Виктория Нестерова — специалист по охране труда",
                   "Георгий Абрамян — ведущий юрист"]),
            ],
            [
                H(2, "Календарь событий"),
                table("t-events", events, rendering="borderless", caption="Октябрь — декабрь 2026", widths=[14, 42, 26, 18]),
                photo("ph3", ["harbor", "container-port"], ["harbor"], {"harbor": "Порт Балтийск, где начнётся электрификация причальных кранов.",
                                                                        "container-port": "Контейнерный терминал порта Балтийск."},
                      "Порт Балтийск.", "right", width="38%"),
                P("Приглашаем сотрудников и членов их семей на субботник в Приморском парке. Инструмент и саженцы "
                  "предоставит компания; после работы — горячий чай и пироги от столовой."),
                P("Заявки на новогодний корпоратив принимает отдел персонала до 1 декабря. В этом году — с детской программой."),
                H(2, "Охрана труда"),
                P("С начала года в компании не зафиксировано ни одного несчастного случая с потерей рабочего времени — 412 дней "
                  "подряд. Напоминаем главные правила работы на высоте в холодный сезон:"),
                L(["не подниматься на турбину при скорости ветра выше 15 м/с на уровне гондолы;",
                   "проверять страховочную систему перед каждым подъёмом, даже если она проверялась утром;",
                   "работать только парами и держать связь с диспетчером каждые 30 минут."], ordered=True),
                box("footnote", "Над номером работали: Мария Белова (редактор), Сергей Лебедев (фото), Ольга Ткаченко (вёрстка). "
                    "Пишите нам: vestnik@balticwind.example, внутренний телефон 2-14. Тираж 600 экз."),
            ],
        ],
        "arithmetic": [{"kind": "line_items", "table": "t-bonus", "quantity": 1, "unit_price": 2, "amount": 3},
                       {"kind": "column_sum", "table": "t-bonus", "columns": [3], "label_column": 0, "total_label": "Призовой фонд"},
                       {"kind": "column_sum", "table": "t-parks", "columns": [1, 2, 3], "label_column": 0, "total_label": "Итого"}],
    }


def newsletter_el() -> dict[str, Any]:
    """Cultural association newsletter in Greek (pylopdf): no emoji, raster chart."""
    members = {"title": "Μέλη του συλλόγου", "categories": ["2022", "2023", "2024", "2025", "2026"],
               "series": [("Μέλη", [184, 203, 221, 247, 268])], "max": 300, "ticks": 3, "tick_format": lambda v: f"{v:.0f}"}
    income = [("Συνδρομές μελών (268 × 30 €)", 804000), ("Δίδακτρα χορευτικών τμημάτων", 1146000), ("Επιχορήγηση Δήμου", 500000),
              ("Έσοδα εκδηλώσεων", 392050)]
    spend = [("Αμοιβές δασκάλων", 1080000), ("Ενοίκιο και λογαριασμοί", 624000), ("Παραδοσιακές στολές", 318000),
             ("Εκδηλώσεις και εκδρομές", 455000), ("Αποθεματικό", 365050)]
    rows = [[name, eur_el(c), ""] for name, c in income] + [[name, "", eur_el(c)] for name, c in spend]
    t_in, t_out = sum(c for _, c in income), sum(c for _, c in spend)
    events = [["Ημερομηνία", "Εκδήλωση", "Χώρος", "Είσοδος"],
              ["Σάβ. 17/10/2026", "Έναρξη χορευτικών τμημάτων", "Αίθουσα του συλλόγου", "Μέλη"],
              ["Κυρ. 25/10/2026", "Εκδρομή στο Ναύπλιο", "Αναχώρηση από την πλατεία", "25,00 €"],
              ["Τετ. 28/10/2026", "Παρέλαση και κατάθεση στεφάνου", "Ηρώο Χαλανδρίου", "Ελεύθερη"],
              ["Σάβ. 14/11/2026", "Βραδιά ρεμπέτικου", "Δημοτικό Θέατρο", "10,00 €"],
              ["Κυρ. 29/11/2026", "Εργαστήρι κεντήματος", "Αίθουσα του συλλόγου", "Ελεύθερη"],
              ["Σάβ. 19/12/2026", "Χριστουγεννιάτικη γιορτή παιδιών", "Πλατεία Δούκα", "Ελεύθερη"]]
    return {
        "template": "newsletter", "page_size": "A4", "languages": ["el-GR"],
        "metadata": {"title": "Ενημερωτικό Δελτίο — Φθινόπωρο 2026", "author": "Πολιτιστικός Σύλλογος Χαλανδρίου «Η Ευρυδίκη»",
                     "subject": "Νέα του συλλόγου, οικονομικός απολογισμός και πρόγραμμα εκδηλώσεων",
                     "keywords": ["ενημερωτικό δελτίο", "πολιτιστικός σύλλογος", "Χαλάνδρι", "παραδοσιακοί χοροί"], "lang": "el-GR",
                     "created": "2026-10-03T09:00:00Z"},
        "theme": {"accent": "#1f4f8a", "py_size": 9.6, "py_serif": True},
        "running_header": "Πολιτιστικός Σύλλογος Χαλανδρίου «Η Ευρυδίκη» · Ενημερωτικό Δελτίο αρ. 31",
        "running_footer": "Σελίδα {page} από {pages}",
        "pages": [
            [
                P("Η Ευρυδίκη", "brand"),
                P("Ενημερωτικό Δελτίο του Πολιτιστικού Συλλόγου Χαλανδρίου · Φθινόπωρο 2026 · Αρ. φύλλου 31", "small"),
                H(1, "Νέα χρονιά, νέα τμήματα"),
                photo("ph1", ["garden-flowers"], ["garden"], {"garden-flowers": "Ο κήπος πίσω από την αίθουσα του συλλόγου, όπου γίνονται οι καλοκαιρινές πρόβες."},
                      "Ο κήπος του συλλόγου.", "none", width="88%"),
                columns([
                    P("Με μεγάλη χαρά ανακοινώνουμε ότι από τις 17 Οκτωβρίου ξεκινούν τα χορευτικά τμήματα της νέας περιόδου. "
                      "Φέτος προσθέτουμε τμήμα χορών της Θράκης για ενήλικες και δεύτερο τμήμα για παιδιά 6–9 ετών, καθώς οι "
                      "αιτήσεις ξεπέρασαν τις θέσεις."),
                    P("Τα μαθήματα θα γίνονται στην ανακαινισμένη αίθουσα της οδού Αγίου Γεωργίου 14. Το καλοκαίρι αλλάξαμε το "
                      "δάπεδο και τοποθετήσαμε κλιματισμό, χάρη στην επιχορήγηση του Δήμου και στις δωρεές των μελών μας."),
                    P("Οι εγγραφές γίνονται κάθε απόγευμα 18:00–20:30 στη γραμματεία. Για οικογένειες με δύο ή περισσότερα "
                      "παιδιά ισχύει έκπτωση 20% στα δίδακτρα."),
                    box("sidebar", "Δευτέρα: Παιδικό Α΄ 17:30 · Ενήλικες 20:00\nΤετάρτη: Παιδικό Β΄ 17:30 · Θρακιώτικοι 20:00\n"
                        "Παρασκευή: Εφηβικό 18:30 · Προχωρημένοι 20:30", title="Πρόγραμμα μαθημάτων"),
                ], count=2),
            ],
            [
                H(2, "Το καλοκαίρι που πέρασε"),
                photo("ph2", ["mountain-lake"], ["landscape"], {"mountain-lake": "Η λίμνη Πλαστήρα, σταθμός της καλοκαιρινής εκδρομής."},
                      "Λίμνη Πλαστήρα.", "right", width="42%"),
                P("Τον Ιούλιο το χορευτικό μας συμμετείχε στο φεστιβάλ παραδοσιακών χορών της Καρδίτσας, όπου παρουσίασε "
                  "χορούς από το Σουφλί και τη Νέα Βύσσα. Την επόμενη μέρα επισκεφθήκαμε τη λίμνη Πλαστήρα και το Μουσείο "
                  "Λαογραφίας στο Μορφοβούνι."),
                P("Στις αρχές Σεπτεμβρίου η έκθεση φωτογραφίας «Χαλάνδρι, 1950–1980» έκλεισε με περισσότερους από 1.400 "
                  "επισκέπτες. Ευχαριστούμε θερμά τις οικογένειες που μας εμπιστεύτηκαν τα αρχεία τους."),
                box("callout", "«Ο χορός δεν είναι μόνο βήματα· είναι ο τρόπος που μια κοινότητα θυμάται τον εαυτό της.»\n"
                    "— Κατερίνα Παπαδοπούλου, δασκάλα χορού", title="Από τις πρόβες"),
                H(2, "Η ομάδα κεντήματος"),
                P("Η ομάδα κεντήματος συναντιέται κάθε Πέμπτη πρωί και φέτος ανέλαβε την επισκευή δεκαοκτώ παραδοσιακών "
                  "φορεσιών. Αν έχετε στο σπίτι παλιά υφαντά ή κεντήματα που θα θέλατε να δωρίσετε, επικοινωνήστε με την "
                  "κυρία Ελένη Βασιλείου."),
                chart("c1", "bar", members, "Η πορεία των μελών του συλλόγου τα τελευταία πέντε χρόνια.", raster=True,
                      width="62%", size=(460, 200)),
                chart_table("c1-data", "Έτος", members, str),
            ],
            [
                H(2, "Οικονομικός απολογισμός 2025–26"),
                P("Η γενική συνέλευση της 21ης Σεπτεμβρίου ενέκρινε ομόφωνα τον απολογισμό της χρήσης. Παραθέτουμε τα βασικά "
                  "στοιχεία εσόδων και εξόδων."),
                table("t-budget", [["Κατηγορία", "Έσοδα", "Έξοδα"], *rows, ["Σύνολο", eur_el(t_in), eur_el(t_out)]],
                      rendering="ruled", align=["l", "r", "r"], widths=[60, 20, 20], total_rows=[len(rows) + 1]),
                P("Το αποθεματικό θα χρηματοδοτήσει την αγορά ηχητικού εξοπλισμού για τις υπαίθριες εκδηλώσεις.", "small"),
                photo("ph3", ["paper-documents"], ["document"], {"paper-documents": "Τα βιβλία ταμείου ελέγχθηκαν από την εξελεγκτική επιτροπή."},
                      "Τα βιβλία ταμείου.", "left", width="34%"),
                P("Η εξελεγκτική επιτροπή (Νίκος Γεωργίου, Μαρία Αντωνίου, Σπύρος Δημητρίου) έλεγξε όλα τα παραστατικά και "
                  "δεν διαπίστωσε καμία απόκλιση."),
                P("Τα μέλη μπορούν να δουν αναλυτικά τα βιβλία στη γραμματεία, κατόπιν συνεννόησης."),
                H(2, "Νέο διοικητικό συμβούλιο"),
                table("t-board", [["Θέση", "Όνομα", "Τηλέφωνο"], ["Πρόεδρος", "Γιώργος Αλεξίου", "697 555 0101"],
                                  ["Αντιπρόεδρος", "Σοφία Μιχαηλίδου", "697 555 0102"], ["Γραμματέας", "Δήμητρα Κωνσταντίνου", "697 555 0103"],
                                  ["Ταμίας", "Παναγιώτης Ρήγας", "697 555 0104"], ["Υπεύθυνη χορευτικών", "Κατερίνα Παπαδοπούλου", "697 555 0105"]],
                      rendering="borderless", widths=[34, 40, 26]),
                box("footnote", "Οι αρχαιρεσίες έγιναν στις 21 Σεπτεμβρίου 2026 με συμμετοχή 143 μελών (53% των ταμειακά εντάξει μελών)."),
            ],
            [
                H(2, "Πρόγραμμα εκδηλώσεων"),
                table("t-events", events, rendering="borderless", caption="Οκτώβριος – Δεκέμβριος 2026", widths=[18, 40, 28, 14]),
                H(2, "Ανακοινώσεις"),
                L(["Η ετήσια συνδρομή (30,00 €) πληρώνεται έως τις 31 Δεκεμβρίου στη γραμματεία ή με κατάθεση στον λογαριασμό του συλλόγου.",
                   "Ζητούνται εθελοντές για τη Χριστουγεννιάτικη γιορτή των παιδιών.",
                   "Η βιβλιοθήκη του συλλόγου δανείζει βιβλία λαογραφίας κάθε Σάββατο 10:00–13:00."]),
                H(2, "Η εκδρομή στο Ναύπλιο"),
                photo("ph4", ["harbor"], ["harbor"], {"harbor": "Το λιμάνι του Ναυπλίου με το Μπούρτζι στο βάθος."},
                      "Το λιμάνι του Ναυπλίου.", "right", width="40%"),
                P("Την Κυριακή 25 Οκτωβρίου θα επισκεφθούμε το Ναύπλιο με ενδιάμεση στάση στον Ισθμό της Κορίνθου. Θα "
                  "ανεβούμε στο Παλαμήδι, θα δούμε το Πελοποννησιακό Λαογραφικό Ίδρυμα και θα φάμε στην παλιά πόλη."),
                P("Η τιμή των 25,00 € περιλαμβάνει τη μετακίνηση και την ξενάγηση. Δηλώσεις συμμετοχής έως τις 20 Οκτωβρίου."),
                P("Αναχώρηση στις 8:00 από την πλατεία Δούκα, επιστροφή περίπου στις 20:30."),
                box("sidebar", "Πολιτιστικός Σύλλογος Χαλανδρίου «Η Ευρυδίκη» · Αγίου Γεωργίου 14, 152 34 Χαλάνδρι\n"
                    "Τηλ. 210 555 0198 · info@evrydiki.example\nΠρόεδρος: Γιώργος Αλεξίου · Γραμματέας: Δήμητρα Κωνσταντίνου",
                    title="Επικοινωνία"),
            ],
        ],
        "arithmetic": [{"kind": "column_sum", "table": "t-budget", "columns": [1, 2], "label_column": 0, "total_label": "Σύνολο"}],
    }



DOCS = [
    ("w2-menu-fr-53", "chromium", menu_fr),
    ("w2-menu-th-54", "libreoffice", menu_th),
    ("w2-menu-vi-55", "pylopdf", menu_vi),
    ("w2-menu-engb-56", "reportlab", menu_engb),
    ("w2-program-en-57", "pylopdf", program_en),
    ("w2-program-hi-58", "libreoffice", program_hi),
    ("w2-program-ar-59", "chromium", program_ar),
    ("w2-program-pl-60", "chromium", program_pl),
    ("w2-newsletter-en-61", "chromium", newsletter_en),
    ("w2-newsletter-es-62", "libreoffice", newsletter_es),
    ("w2-newsletter-ru-63", "chromium", newsletter_ru),
    ("w2-newsletter-el-64", "pylopdf", newsletter_el),
]
