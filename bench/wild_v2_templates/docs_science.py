"""Authored wild-v2 documents: scientific papers, slide decks and technical manuals."""

# ruff: noqa: E501
from __future__ import annotations

import math
from typing import Any

from bench.wild_templates.model import money, number
from bench.wild_v2_templates.core import (
    H,
    L,
    P,
    box,
    chart,
    chart_table,
    code,
    columns,
    continued,
    equation,
    group,
    item,
    photo,
    screenshot,
    table,
)

SHY = "­"


def _meta(title: str, author: str, subject: str, keywords: list[str], lang: str, created: str) -> dict[str, Any]:  # noqa: PLR0913, PLR0917
    return {"title": title, "author": author, "subject": subject, "keywords": keywords, "lang": lang, "created": created}



# ====================================================================== scientific papers


def paper_en() -> dict[str, Any]:
    """Biocatalysis paper (Chromium, MathML equations, two-column body)."""
    gas = 8.314
    temps = [30, 40, 50, 60, 70]

    def kcat(ea: float, ref: float, t: float) -> float:
        return ref * math.exp(-ea * 1000 / gas * (1 / (t + 273.15) - 1 / 313.15))

    km_free = [0.42, 0.45, 0.49, 0.56, 0.68]
    km_imm = [0.61, 0.63, 0.66, 0.70, 0.75]
    kin_rows = []
    free_k, imm_k = [], []
    for t, kf, ki in zip(temps, km_free, km_imm, strict=True):
        a, b = kcat(52.4, 312.0, t), kcat(44.1, 268.0, t)
        free_k.append(round(a))
        imm_k.append(round(b))
        kin_rows.append([f"{t}", f"{a:.0f}", f"{kf:.2f}", f"{a / kf / 1000:.2f}", f"{b:.0f}", f"{ki:.2f}", f"{b / ki / 1000:.2f}"])
    t1 = table("t1", [["T (°C)", "kcat free (s⁻¹)", "Km free (mM)", "kcat/Km free (mM⁻¹ s⁻¹ ×10³)",
                       "kcat TLL@SBA (s⁻¹)", "Km TLL@SBA (mM)", "kcat/Km TLL@SBA (mM⁻¹ s⁻¹ ×10³)"], *kin_rows],
               caption="Table 1. Apparent kinetic constants of free and immobilized TLL toward p-nitrophenyl butyrate (mean of n = 3; RSD < 4 %).",
               align=["c", "r", "r", "r", "r", "r", "r"], widths=[10, 13, 13, 16, 15, 15, 18])
    deact = [(55, 0.0094, 0.0018), (60, 0.0152, 0.0027), (65, 0.0231, 0.0042)]
    d_rows = []
    for t, kf, ki in deact:
        d_rows.append([f"{t}", f"{kf:.4f}", f"{math.log(2) / kf:.1f}", f"{ki:.4f}", f"{math.log(2) / ki:.1f}", f"{(kf / ki):.1f}"])
    t2 = table("t2", [["T (°C)", "kd free (min⁻¹)", "t½ free (min)", "kd TLL@SBA (min⁻¹)", "t½ TLL@SBA (min)", "Stabilization factor"], *d_rows],
               rendering="borderless", caption="Table 2. First-order deactivation constants and half-lives in 50 mM phosphate buffer, pH 7.5.",
               align=["c", "r", "r", "r", "r", "r"])
    minutes = [0, 15, 30, 45, 60, 90, 120, 180]
    decay_spec = {"title": "Residual activity at 65 °C (%)", "categories": [f"{m} min" for m in minutes],
                  "series": [("Free TLL", [round(100 * math.exp(-0.0231 * m), 1) for m in minutes]),
                             ("TLL@SBA-NH₂", [round(100 * math.exp(-0.0042 * m), 1) for m in minutes])],
                  "max": 100, "ticks": 4, "tick_format": lambda v: f"{v:.0f}"}
    line_spec = {"title": "Turnover number vs. temperature", "categories": [f"{t} °C" for t in temps],
                 "series": [("Free TLL", free_k), ("TLL@SBA-NH₂", imm_k)], "max": 1200, "ticks": 4,
                 "tick_format": lambda v: f"{v:.0f}"}
    reuse = [100.0, 98.6, 97.1, 95.9, 94.2, 92.8, 91.5, 89.7, 88.4, 86.9]
    bar_spec = {"title": "Residual activity after repeated batches (%)", "categories": [str(i) for i in range(1, 11)],
                "series": [("TLL@SBA-NH₂", reuse)], "max": 100, "ticks": 5, "tick_format": lambda v: f"{v:.0f}",
                "colors": ["#3d6b8f"]}
    mm = ("<mi>v</mi><mo>=</mo><mfrac><mrow><msub><mi>V</mi><mi>max</mi></msub><mo>[</mo><mi>S</mi><mo>]</mo></mrow>"
          "<mrow><msub><mi>K</mi><mi>m</mi></msub><mo>+</mo><mo>[</mo><mi>S</mi><mo>]</mo></mrow></mfrac>")
    arr = ("<msub><mi>k</mi><mi>cat</mi></msub><mo>=</mo><mi>A</mi><mo>⁢</mo><mi>exp</mi><mrow><mo>(</mo><mo>−</mo>"
           "<mfrac><msub><mi>E</mi><mi>a</mi></msub><mrow><mi>R</mi><mi>T</mi></mrow></mfrac><mo>)</mo></mrow>")
    decay = ("<mfrac><mrow><mi>A</mi><mo>(</mo><mi>t</mi><mo>)</mo></mrow><msub><mi>A</mi><mn>0</mn></msub></mfrac><mo>=</mo>"
             "<mi>exp</mi><mrow><mo>(</mo><mo>−</mo><msub><mi>k</mi><mi>d</mi></msub><mi>t</mi><mo>)</mo></mrow>")
    half = ("<msub><mi>t</mi><mrow><mn>1</mn><mo>/</mo><mn>2</mn></mrow></msub><mo>=</mo>"
            "<mfrac><mrow><mi>ln</mi><mo>⁡</mo><mn>2</mn></mrow><msub><mi>k</mi><mi>d</mi></msub></mfrac>")
    q10 = ("<msub><mi>Q</mi><mn>10</mn></msub><mo>=</mo><msup><mrow><mo>(</mo><mfrac><msub><mi>k</mi><mn>2</mn></msub>"
           "<msub><mi>k</mi><mn>1</mn></msub></mfrac><mo>)</mo></mrow><mrow><mn>10</mn><mo>/</mo><mo>(</mo><msub><mi>T</mi><mn>2</mn></msub>"
           "<mo>−</mo><msub><mi>T</mi><mn>1</mn></msub><mo>)</mo></mrow></msup>")
    ra = ("<msub><mi>RA</mi><mi>n</mi></msub><mo>=</mo><mfrac><msub><mi>A</mi><mi>n</mi></msub><msub><mi>A</mi><mn>1</mn></msub></mfrac>"
          "<mo>×</mo><mn>100</mn><mo>%</mo>")
    refs = [
        "Bornscheuer, U. T.; Huisman, G. W.; Kazlauskas, R. J.; Lutz, S.; Moore, J. C.; Robins, K. Engineering the third wave of biocatalysis. *Nature* **2012**, 485, 185–194.",
        "Sheldon, R. A.; van Pelt, S. Enzyme immobilisation in biocatalysis: why, what and how. *Chem. Soc. Rev.* **2013**, 42, 6223–6235.",
        "Fernandez-Lafuente, R. Lipase from *Thermomyces lanuginosus*: uses and prospects as an industrial biocatalyst. *J. Mol. Catal. B* **2010**, 62, 197–212.",
        "Hartmann, M.; Kostrov, X. Immobilization of enzymes on porous silicas — benefits and challenges. *Chem. Soc. Rev.* **2013**, 42, 6277–6289.",
        "Zhao, D.; Feng, J.; Huo, Q.; Melosh, N.; Fredrickson, G. H.; Chmelka, B. F.; Stucky, G. D. Triblock copolymer syntheses of mesoporous silica with periodic 50 to 300 angstrom pores. *Science* **1998**, 279, 548–552.",
        "Okafor, R. M.; Sorensen, M. K. Pore-size effects on lipase loading in amine-grafted SBA-15. *Biocatal. Eng. Lett.* **2024**, 9, 211–223.",
        "Park, H.-w.; Lee, S.-j.; Kim, D. Thermal unfolding pathways of fungal lipases probed by DSF. *Protein Stab. Rep.* **2023**, 17, 88–101.",
        "Ferrer-Ibáñez, L.; Giménez, A. Lid opening and interfacial activation of immobilized lipases. *Catal. Sci. Bio.* **2025**, 6, 1402–1417.",
        "Mateo, C.; Palomo, J. M.; Fernandez-Lorente, G.; Guisan, J. M.; Fernandez-Lafuente, R. Improvement of enzyme activity, stability and selectivity via immobilization techniques. *Enzyme Microb. Technol.* **2007**, 40, 1451–1463.",
        "Whitcombe, D. J.; Okafor, R. M. A plate-reader protocol for continuous pNPB hydrolysis assays with drift correction. *Anal. Biochem. Methods* **2025**, 31, 55–63.",
        "Bradford, M. M. A rapid and sensitive method for the quantitation of microgram quantities of protein. *Anal. Biochem.* **1976**, 72, 248–254.",
        "Peterson, M. E.; Daniel, R. M.; Danson, M. J.; Eisenthal, R. The dependence of enzyme activity on temperature. *Biochem. J.* **2007**, 402, 331–337.",
        "Sadana, A. *Biocatalysis: Fundamentals of Enzyme Deactivation Kinetics*; Prentice Hall: Englewood Cliffs, NJ, 1991.",
        "Rodrigues, R. C.; Ortiz, C.; Berenguer-Murcia, Á.; Torres, R.; Fernández-Lafuente, R. Modifying enzyme activity and selectivity by immobilization. *Chem. Soc. Rev.* **2013**, 42, 6290–6307.",
        "Nguyen, T. H.; Brandt, K. Diffusional limitation in mesoporous enzyme carriers: a Thiele-modulus analysis. *Ind. Biocatal.* **2022**, 4, 301–315.",
        "Sorensen, M. K.; Patel, A.; Whitcombe, D. J. Packed-bed transesterification with silica-bound lipases at pilot scale. *Org. Process Res. Dev.* **2026**, 30, 702–714.",
        "Yamamoto, K.; Ito, S. Leaching of physically adsorbed enzymes from amine-grafted silica. *J. Porous Bio-Mater.* **2021**, 12, 47–58.",
        "Cao, L. *Carrier-bound Immobilized Enzymes: Principles, Application and Design*; Wiley-VCH: Weinheim, 2005.",
        "Brunauer, S.; Emmett, P. H.; Teller, E. Adsorption of gases in multimolecular layers. *J. Am. Chem. Soc.* **1938**, 60, 309–319.",
        "Barrett, E. P.; Joyner, L. G.; Halenda, P. P. The determination of pore volume and area distributions in porous substances. *J. Am. Chem. Soc.* **1951**, 73, 373–380.",
        "Niesen, F. H.; Berglund, H.; Vedadi, M. The use of differential scanning fluorimetry to detect ligand interactions that promote protein stability. *Nat. Protoc.* **2007**, 2, 2212–2221.",
        "Garcia-Galan, C.; Berenguer-Murcia, Á.; Fernandez-Lafuente, R.; Rodrigues, R. C. Potential of different enzyme immobilization strategies to improve enzyme performance. *Adv. Synth. Catal.* **2011**, 353, 2885–2904.",
        "Raman, P.; Okafor, R. M. Thermal mapping of 96-well plates in kinetic readers. *Lab. Instrum. Notes* **2025**, 8, 19–24.",
        "Gómez-Rivas, M.; Ferrer-Ibáñez, L. Salt-induced desorption of lipases from aminated supports. *Rev. Catál. Apl.* **2024**, 41, 233–245.",
    ]
    return {
        "template": "scientific_paper", "page_size": "Letter", "languages": ["en-US", "ko", "es"],
        "metadata": _meta("Thermal activation and operational stability of Thermomyces lanuginosus lipase immobilized on amine-functionalized SBA-15",
                          "Rachel M. Okafor; Daniel J. Whitcombe; Hyun-woo Park; Lucía Ferrer-Ibáñez; Martin K. Sorensen",
                          "Journal of Applied Biocatalysis 14 (2026) 412–419",
                          ["lipase", "immobilization", "SBA-15", "thermal stability", "Arrhenius", "biocatalysis"], "en-US",
                          "2026-06-18T14:02:00Z"),
        "theme": {"accent": "#203a5c", "font_size": "11pt", "body_font": "'Noto Serif'", "heading_font": "'Noto Sans'",
                  "margins": "17mm 16mm 17mm 16mm",
                  "extra_css": "html{line-height:1.5}figure{break-inside:avoid}h1{text-align:center;font-size:1.65em}.cols{column-gap:6mm;column-rule:none}.cols h2{font-size:1.08em;border:none;margin-top:.7em}"
                               ".cols h3{font-size:.98em;font-style:italic}.cols p{text-align:justify;hyphens:auto}"
                               "div.eq math{font-size:1.05em} ol li{font-size:.86em;margin-bottom:.15em}"},
        "running_header": "Journal of Applied Biocatalysis 14 (2026) 412–419 · Okafor et al.",
        "running_footer": "{page}",
        "pages": [
            [
                P("Research Article · Received 2 March 2026 · Accepted 29 May 2026 · Published online 18 June 2026", "small center"),
                H(1, "Thermal activation and operational stability of *Thermomyces lanuginosus* lipase immobilized on amine-functionalized SBA-15 silica"),
                P("Rachel M. Okafor¹, Daniel J. Whitcombe¹, Hyun-woo Park (박현우)², Lucía Ferrer-Ibáñez³, Martin K. Sorensen¹*", "center"),
                P("¹ Department of Chemical and Biological Engineering, Lakeshore State University, 1415 Engineering Dr., Madison, WI 53706, USA\n"
                  "² Department of Biotechnology, Hanbit National University (한빛국립대학교), Daejeon 34141, Republic of Korea\n"
                  "³ Instituto de Catálisis Aplicada, Camí de Vera s/n, 46022 València, Spain", "small center"),
                H(2, "Abstract"),
                P("Lipase B–type hydrolases are workhorses of fine-chemical synthesis, yet their use above 50 °C is limited by "
                  "rapid unfolding. We immobilized *Thermomyces lanuginosus* lipase (TLL) on SBA-15 silica grafted with "
                  "3-aminopropyl groups (pore diameter 8.6 nm) and compared the kinetics and thermal stability of the "
                  "carrier-bound enzyme with the free enzyme between 30 and 70 °C. Immobilization raised the apparent Km "
                  "toward p-nitrophenyl butyrate by 45 % at 30 °C, consistent with mild internal diffusion limitation, but "
                  "lowered the apparent activation energy from 52.4 to 44.1 kJ mol⁻¹. First-order deactivation at 65 °C slowed "
                  "5.5-fold, extending the half-life from 30.0 to 165.0 min. After ten 4-h batches of tributyrin hydrolysis "
                  "the immobilized preparation retained 86.9 % of its initial activity with less than 2 % protein leaching. "
                  "These results support SBA-15-NH₂ as a carrier for continuous lipase processes operated at 55–65 °C.", "lead"),
                P("**Keywords:** lipase; enzyme immobilization; mesoporous silica; thermal deactivation; Arrhenius kinetics", "small"),
                columns([
                    H(2, "1. Introduction"),
                    P("Enzymes offer selectivity that is hard to match with chemical catalysts, and the steady improvement of "
                      "protein engineering has widened their industrial reach [1]. Lipases (triacylglycerol hydrolases, EC 3.1.1.3) "
                      "are among the most widely used enzymes because they accept a broad range of esters and remain active in "
                      "organic solvents. The lipase from *Thermomyces lanuginosus* (TLL) is produced cheaply at scale and is used "
                      "in detergents, oil modification and biodiesel production [3]."),
                    P("Free lipases are, however, difficult to recover and lose activity above roughly 50 °C. Immobilization on a "
                      "solid carrier addresses both problems: the biocatalyst can be filtered off and reused, and multipoint "
                      "attachment or confinement can rigidify the protein against unfolding [2, 9]. Ordered mesoporous silicas "
                      "such as SBA-15 are attractive carriers because their pore diameter (5–10 nm) can be matched to the size "
                      "of the enzyme and their surface is easily functionalized [4, 5]."),
                    P("Previous work from our group showed that amine grafting increases TLL loading on SBA-15 by electrostatic "
                      "attraction at pH 7.5, where the carrier is positively charged and the enzyme (pI ≈ 4.4) carries a net "
                      "negative charge [6]. Whether the same preparation also improves operational stability at elevated "
                      "temperature was not examined. Thermal behaviour is decisive for process design: a 10 °C increase in "
                      "operating temperature roughly doubles the reaction rate and lowers the viscosity of oil substrates, but "
                      "only pays off when the catalyst survives long enough to amortize its cost [12, 16]."),
                    P("Here we report a systematic comparison of free and immobilized TLL between 30 and 70 °C. We determine "
                      "Michaelis–Menten constants at five temperatures, fit Arrhenius parameters, measure first-order "
                      "deactivation at three temperatures and test reusability in repeated batches. Structural information "
                      "from differential scanning fluorimetry, carried out at Hanbit National University, is used to interpret "
                      "the stabilization mechanism [7]."),
                ]),
                box("footnote", "* Corresponding author. E-mail: [m.sorensen@lakeshore-state.example](mailto:m.sorensen@lakeshore-state.example); phone +1 608-555-0187."),
            ],
            [
                columns([
                    P("Silica carriers also have drawbacks. Physically adsorbed enzymes can leach under shear or at high "
                      "ionic strength, and narrow pores slow the transport of bulky substrates such as triglycerides [17]. "
                      "The balance between stabilization and mass-transfer resistance therefore depends on pore size, "
                      "surface chemistry and enzyme loading, and must be established for each enzyme–carrier pair."),
                    H(2, "2. Materials and methods"),
                    H(3, "2.1 Chemicals and enzyme"),
                    P("TLL (Lipozyme® TL 100 L, 100 kLU g⁻¹) was a gift from a commercial supplier and was desalted on PD-10 "
                      "columns before use. Pluronic P123, tetraethyl orthosilicate (TEOS, ≥ 99.0 %), "
                      "(3-aminopropyl)triethoxysilane (APTES), p-nitrophenyl butyrate (pNPB) and tributyrin were obtained from "
                      "standard suppliers and used as received. All buffers were prepared in ultrapure water (18.2 MΩ cm)."),
                    photo("f1", ["lab-glassware", "lab-pipettes"], ["lab"],
                          {"lab-glassware": "Figure 1. Glassware set-up for the hydrothermal synthesis and APTES grafting of SBA-15.",
                           "lab-pipettes": "Figure 1. Pipetting station used to prepare the immobilization batches."},
                          "Figure 1. Laboratory set-up used for carrier synthesis.", "none", width="100%"),
                    H(3, "2.2 Carrier synthesis and functionalization"),
                    P("SBA-15 was synthesized following Zhao et al. [5]: 4.0 g P123 was dissolved in 150 mL of 1.6 M HCl at "
                      "35 °C, 8.5 g TEOS was added dropwise and the mixture was stirred for 24 h, aged at 100 °C for 48 h, "
                      "filtered and calcined at 550 °C for 6 h (ramp 1 °C min⁻¹). For grafting, 2.0 g of dried silica was "
                      "refluxed with 2.0 mL APTES in 60 mL dry toluene for 12 h under nitrogen, washed with toluene and ethanol "
                      "and dried at 80 °C. Nitrogen physisorption gave a BET surface area of 612 m² g⁻¹ and a BJH pore diameter "
                      "of 8.6 nm after grafting (742 m² g⁻¹ and 9.1 nm before)."),
                    P("Small-angle X-ray scattering showed the (100), (110) and (200) reflections of a well-ordered hexagonal "
                      "mesostructure with a unit-cell parameter of 11.4 nm. Thermogravimetric analysis under air indicated a "
                      "mass loss of 7.9 % between 200 and 650 °C after grafting, corresponding to 1.32 mmol of aminopropyl "
                      "groups per gram of silica. Elemental analysis (N 1.81 wt %) agreed within 3 % with this value."),
                    H(3, "2.3 Immobilization"),
                    P("Carrier (100 mg) was suspended in 10 mL of 50 mM sodium phosphate buffer, pH 7.5, containing 2.5 mg mL⁻¹ "
                      "protein and shaken at 25 °C and 150 rpm for 4 h. Protein in the supernatant was quantified by the "
                      "Bradford assay [11]; the loading was 198 ± 6 mg g⁻¹ carrier, corresponding to an immobilization yield of "
                      "79 %. The particles were washed three times with buffer and stored at 4 °C."),
                    P("Adsorption isotherms measured between 0.25 and 4.0 mg mL⁻¹ initial protein followed the Langmuir model "
                      "with a maximum capacity of 236 mg g⁻¹ and an affinity constant of 3.1 mL mg⁻¹. The loading used in this "
                      "study therefore corresponds to about 84 % of monolayer saturation, a compromise between volumetric "
                      "activity and crowding of enzyme molecules at the pore entrances. Specific activity of the bound enzyme "
                      "fell by 18 % when the loading was increased to 230 mg g⁻¹ in preliminary experiments, so higher "
                      "loadings were not pursued."),
                ]),
            ],
            [
                columns([
                    H(3, "2.4 Activity assay and kinetic analysis"),
                    P("Hydrolysis of pNPB was followed continuously at 405 nm in a thermostatted plate reader using the "
                      "drift-corrected protocol of Whitcombe and Okafor [10]. Substrate concentrations ranged from 0.1 to "
                      "4.0 mM with 1 % (v/v) acetonitrile as co-solvent. Initial rates were fitted to the Michaelis–Menten "
                      "equation by non-linear least squares:"),
                    equation("eq1", mm, "v = Vmax·[S] / (Km + [S])", "v = {V_{max} left[ S right]} over {K_m + left[ S right]}", number="(1)"),
                    P("where v is the initial rate, Vmax the maximum rate and Km the apparent Michaelis constant. The turnover "
                      "number kcat = Vmax/[E]₀ was calculated from the active-site concentration determined by titration with "
                      "methyl p-nitrophenyl n-hexylphosphonate. For the immobilized enzyme, [E]₀ refers to the protein actually "
                      "bound, so kcat expresses the apparent activity per bound molecule."),
                    P("The temperature dependence of kcat was described by the Arrhenius equation"),
                    equation("eq2", arr, "kcat = A·exp(−Ea / RT)", "k_{cat} = A exp left( - {E_a} over {R T} right)", number="(2)"),
                    P("in which A is the pre-exponential factor, Ea the apparent activation energy, R = 8.314 J mol⁻¹ K⁻¹ and T "
                      "the absolute temperature. Ea was obtained from the slope of ln kcat versus 1/T. As an additional, "
                      "model-free descriptor we report the temperature coefficient"),
                    equation("eq3", q10, "Q10 = (k2 / k1)^(10 / (T2 − T1))", "Q_{10} = left( {k_2} over {k_1} right)^{10 / (T_2 - T_1)}", number="(3)"),
                    P("Temperatures above 50 °C were verified in every well column with a calibrated Pt100 probe, because the "
                      "plate reader overshoots by up to 0.6 °C during the first minutes of a run [23]."),
                    H(3, "2.5 Thermal deactivation"),
                    P("Free or immobilized enzyme was incubated at 55, 60 and 65 °C in buffer without substrate. Aliquots were "
                      "withdrawn at intervals of 10–30 min, cooled on ice for 5 min and assayed at 30 °C. Residual activity "
                      "followed a single-exponential decay,"),
                    equation("eq4", decay, "A(t)/A₀ = exp(−kd·t)", "{A(t)} over {A_0} = exp(- k_d t)", number="(4)"),
                    P("from which the deactivation constant kd and the half-life were calculated:"),
                    equation("eq5", half, "t½ = ln 2 / kd", "t_{1/2} = {ln 2} over {k_d}", number="(5)"),
                    P("The stabilization factor is defined as the ratio of kd values for free and immobilized enzyme at the "
                      "same temperature. All experiments were carried out in triplicate; uncertainties are standard deviations."),
                    H(3, "2.6 Reusability"),
                    P("Tributyrin (0.1 M, emulsified with 2 % gum arabic) was hydrolysed with 50 mg biocatalyst in 20 mL buffer "
                      "at 55 °C for 4 h in a pH-stat at pH 7.5. After each batch the particles were recovered by centrifugation "
                      "(3000 g, 5 min), washed twice and transferred to fresh substrate. Relative activity in batch n was "
                      "expressed as"),
                    equation("eq6", ra, "RAₙ = Aₙ / A₁ × 100 %", 'RA_n = {A_n} over {A_1} times 100 "%"', number="(6)"),
                    P("Leached protein was measured in the combined washings after every second batch."),
                    H(3, "2.7 Differential scanning fluorimetry"),
                    P("Melting curves were recorded in a real-time PCR instrument with SYPRO Orange (5×) from 25 to 95 °C at "
                      "1 °C min⁻¹ [21]. For the immobilized enzyme, 2 mg of particles were suspended in 20 µL of buffer and the "
                      "suspension was kept homogeneous by a 10-s shaking step every minute. The apparent melting temperature "
                      "Tm was taken as the maximum of the first derivative of the fluorescence signal."),
                    H(3, "2.8 Statistics"),
                    P("Non-linear fits were performed with weighted least squares (weights 1/σ²); parameter uncertainties are "
                      "asymptotic standard errors. Differences between preparations were tested with Welch’s t-test at "
                      "α = 0.05."),
                ]),
            ],
            [
                H(2, "3. Results"),
                t1,
                columns([
                    H(3, "3.1 Kinetic constants"),
                    P("Table 1 summarizes the kinetic constants. At 30 °C immobilization increased the apparent Km from 0.42 to "
                      "0.61 mM, while kcat decreased by 13 %. An increase in Km is commonly observed for porous carriers and "
                      "reflects the concentration gradient that develops inside the pores when the reaction is fast compared "
                      "with diffusion [15]. The catalytic efficiency kcat/Km of the immobilized enzyme was therefore about 40 % "
                      "lower than that of the free enzyme at all temperatures."),
                    P("The difference in Km narrowed at higher temperature (0.68 vs. 0.75 mM at 70 °C) because substrate "
                      "diffusivity increases and, for the free enzyme, partial unfolding during the 3-min assay begins to "
                      "lower the apparent affinity. Above 60 °C the initial-rate traces of the free enzyme were visibly "
                      "curved, so the 70 °C values for free TLL should be read as lower bounds."),
                    chart("f2", "line", line_spec, "Figure 2. Temperature dependence of kcat for free and immobilized TLL (pNPB, pH 7.5).",
                          raster=False, width="100%", size=(420, 250)),
                    chart_table("c2", "Temperature", line_spec, lambda v: f"{v:.0f}"),
                    P("Substrate inhibition was not observed up to 4 mM pNPB for either preparation, and Hanes–Woolf plots "
                      "were linear over the full concentration range. Control experiments with stirred and unstirred wells "
                      "gave identical rates for the free enzyme, but a 6 % higher rate for the particles when the plate was "
                      "shaken for 2 s before each reading, which was therefore included in the protocol."),
                    H(3, "3.2 Activation energy"),
                    P("Linear regression of ln kcat against 1/T (R² ≥ 0.995) gave Ea = 52.4 ± 1.3 kJ mol⁻¹ for the free enzyme "
                      "and 44.1 ± 1.1 kJ mol⁻¹ for TLL@SBA-NH₂. The corresponding Q10 values between 40 and 50 °C were 1.83 "
                      "and 1.66. A lower apparent activation energy after immobilization is a known signature of partial "
                      "diffusion control, since the observed rate then scales with the square root of the intrinsic rate "
                      "constant [15]. We nevertheless consider a contribution from a more open lid conformation likely, "
                      "because the Thiele modulus estimated for 8.6-nm pores and 200 mg g⁻¹ loading is only 0.7 [8]."),
                    P("Plotting the efficiency ratio of bound to free enzyme against temperature yields a slope close to zero "
                      "(−0.002 K⁻¹), so the relative penalty of immobilization does not depend on temperature in the studied "
                      "range. This is useful for process design, because the kinetic data obtained at 30 °C can be scaled to "
                      "the operating temperature with the Arrhenius parameters alone."),
                ]),
            ],
            [
                columns([
                    H(3, "3.3 Thermal stability"),
                    P("Deactivation of both preparations followed Eq. (4) closely (R² > 0.98) over at least two half-lives; "
                      "no initial activation phase was detected. The constants are listed in Table 2. At every temperature the "
                      "immobilized enzyme deactivated five to six times more slowly than the free enzyme, and the "
                      "stabilization factor increased slightly with temperature, from 5.2 at 55 °C to 5.5 at 65 °C."),
                    P("Differential scanning fluorimetry showed a shift of the apparent melting temperature from 71.8 ± 0.3 °C "
                      "(free) to 77.4 ± 0.4 °C (bound). Together with the absence of leaching, this points to confinement and "
                      "multipoint electrostatic contact rather than covalent attachment as the origin of the stabilization. "
                      "A similar Tm shift was reported for TLL adsorbed on octyl-agarose, where the open lid conformation is "
                      "fixed by hydrophobic interfacial adsorption [8, 14]."),
                ]),
                t2,
                columns([
                    P("The deactivation energies obtained from the temperature dependence of kd were 98 kJ mol⁻¹ for the free "
                      "enzyme and 91 kJ mol⁻¹ for TLL@SBA-NH₂. Both values are typical of unfolding-controlled loss of "
                      "activity, and the similar magnitude suggests that the carrier slows rather than changes the "
                      "deactivation mechanism. Extrapolated to 55 °C, the immobilized enzyme would retain 50 % of its "
                      "activity after about 6.4 h of continuous exposure, which compares favourably with commercial "
                      "immobilized lipase preparations tested under the same conditions (2.9–4.1 h) [16]."),
                    box("callout", "At 65 °C the half-life increased from 30.0 min (free) to 165.0 min (TLL@SBA-NH₂); "
                        "the gain is achieved without cross-linking or covalent coupling agents.", title="Key finding"),
                    P("The stabilization cannot be explained by a change in the assay conditions alone. Control incubations of "
                      "the free enzyme in the presence of non-functionalized SBA-15, to which TLL binds only weakly at pH 7.5 "
                      "(loading 41 mg g⁻¹), gave kd values within 8 % of those of the free enzyme in buffer. Close contact with "
                      "the aminated pore wall is therefore required."),
                    H(3, "3.4 Protein retention"),
                    P("Leaching was assessed by incubating the biocatalyst for 24 h in buffers of increasing ionic strength. "
                      "Below 0.2 M NaCl less than 1 % of the bound protein was released; at 0.5 M NaCl the release rose to "
                      "6.8 %, as expected for an electrostatically held enzyme. Under the low-salt conditions of the reuse "
                      "experiments, retention is therefore not limiting, but feeds with high salt content would require a "
                      "covalent post-treatment, for example with glutaraldehyde."),
                ]),
                chart("f5", "line", decay_spec, "Figure 5. Residual activity during incubation at 65 °C without substrate; lines are fits to Eq. (4).",
                      raster=True, width="78%", size=(560, 220)),
                chart_table("c5", "Time", decay_spec, lambda v: f"{v:.1f}"),
                columns([
                    P("The fitted curves in Figure 5 reproduce the measured residual activities within ±2.5 percentage "
                      "points over the full incubation. A two-state model with a partially active intermediate did not "
                      "improve the fit significantly (F-test, p = 0.41) and was therefore not pursued."),
                ]),
            ],
            [
                columns([
                    H(3, "3.4 Operational stability"),
                    P("Figure 3 shows the residual activity of the immobilized biocatalyst over ten consecutive 4-h batches of "
                      "tributyrin hydrolysis at 55 °C. Activity decreased almost linearly by about 1.4 percentage points per "
                      "batch and reached 86.9 % in the tenth batch. Cumulative protein leaching was 1.7 % of the initial load, "
                      "which accounts for only a small part of the decline; the remainder is attributed to slow thermal "
                      "deactivation and to mechanical loss of fines during centrifugation (about 0.5 mg per cycle)."),
                    chart("f3", "bar", bar_spec, "Figure 3. Residual activity of TLL@SBA-NH₂ in ten consecutive batches (55 °C, pH 7.5).",
                          raster=True, width="100%", size=(440, 240)),
                    chart_table("c3", "Batch", bar_spec, lambda v: f"{v:.1f}"),
                    P("The particles kept their morphology throughout. Optical microscopy of samples taken after the first "
                      "and tenth batch (Figure 4) showed the characteristic rope-like aggregates of SBA-15, 1–2 µm in length, "
                      "with no sign of attrition beyond the fines mentioned above."),
                    photo("f4", ["microscope", "lab-pipettes"], ["lab"],
                          {"microscope": "Figure 4. Light microscope used to inspect carrier particles after reuse.",
                           "lab-pipettes": "Figure 4. Sampling of particles between batches."},
                          "Figure 4. Particle inspection after the reuse experiments.", "none", width="88%"),
                    H(2, "4. Discussion"),
                    P("The trade-off revealed by Tables 1 and 2 is typical of porous carriers: immobilization costs about 40 % "
                      "of catalytic efficiency at a given temperature but buys a five-fold gain in lifetime. For a continuous "
                      "process the relevant figure of merit is the total turnover number before the activity falls below an "
                      "economic threshold, which scales with kcat/kd. On this basis TLL@SBA-NH₂ outperforms the free enzyme by a "
                      "factor of 4.6 at 65 °C and 4.4 at 55 °C."),
                    P("The stabilization obtained here is moderate compared with covalent multipoint attachment on "
                      "glyoxyl-agarose, which can raise half-lives by two orders of magnitude [14, 22]. Covalent methods, "
                      "however, often cost 50 % or more of the initial activity and require long incubations at pH 10. The "
                      "electrostatic route used here is fast, operates at neutral pH and keeps most of the activity."),
                    P("A rough cost estimate illustrates the practical relevance. With a carrier cost of about $40 per kilogram "
                      "and a loading of 0.2 g protein per gram, the material cost of TLL@SBA-NH₂ is dominated by the enzyme "
                      "itself. Each additional batch at 55 °C therefore lowers the catalyst cost per kilogram of product "
                      "almost proportionally, as long as the activity loss per cycle stays near 1.4 percentage points. At "
                      "this rate, 25 cycles would be possible before the activity falls below 65 %, a common replacement "
                      "threshold in batch oleochemical processes."),
                ]),
            ],
            [
                columns([
                    P("A second practical consequence concerns the choice of operating temperature. Because the apparent "
                      "activation energy of the bound enzyme (44 kJ mol⁻¹) is much smaller than its deactivation energy "
                      "(91 kJ mol⁻¹), raising the temperature shortens the lifetime faster than it increases the rate. For "
                      "the immobilized preparation the optimum of the productivity per catalyst charge lies near 55 °C, "
                      "about 10 °C higher than for the free enzyme."),
                    P("Our results differ from those of Yamamoto and Ito [17], who reported substantial leaching of TLL from "
                      "amine-grafted silica. Their material had a pore diameter of 5.4 nm, smaller than the enzyme's "
                      "longest dimension (≈ 6 nm), so most protein was adsorbed on the external surface. With 8.6-nm pores, "
                      "the majority of the enzyme resides inside the channels, where it is both protected and retained."),
                    P("Limitations of the present study include the use of a single, activated model substrate and the "
                      "batch format of the reuse tests. Packed-bed experiments with vegetable oil, where pore blocking by "
                      "glycerol and long-chain products is expected, are under way in a 250-mL column reactor [16]."),
                    P("Finally, the comparison with literature values is complicated by the variety of activity units in use. "
                      "We report turnover numbers per titrated active site rather than units per gram, so that the effect of "
                      "the carrier on the intrinsic activity can be separated from the effect of loading. Expressed per gram of "
                      "biocatalyst, TLL@SBA-NH₂ reached 1.9 kU g⁻¹ at 55 °C with tributyrin, within the range reported for "
                      "commercial immobilized lipases [9, 18]."),
                    P("Taken together, the data show that a simple, one-step adsorption onto a well-chosen carrier captures a "
                      "large part of the stability gain usually associated with more elaborate immobilization chemistry."),
                    H(2, "5. Conclusions"),
                    P("Electrostatic immobilization of TLL in amine-functionalized SBA-15 with 8.6-nm pores yields a "
                      "biocatalyst with a 5.5-fold longer half-life at 65 °C, a 5.6 °C higher apparent melting temperature "
                      "and 86.9 % residual activity after ten batches. The modest loss of catalytic efficiency is largely "
                      "explained by internal diffusion and is outweighed by the gain in stability. SBA-15-NH₂ is therefore "
                      "a promising carrier for lipase processes operated between 55 and 65 °C."),
                    H(2, "Acknowledgements"),
                    P("We thank Priya Raman for nitrogen physisorption measurements and the Lakeshore Materials "
                      "Characterization Facility for access to the plate reader. H.-w. Park acknowledges a visiting-scholar "
                      "grant from the Hanbit–Lakeshore exchange programme. This work was supported by the National Science "
                      "Foundation (fictitious award CBET-2614402)."),
                    H(2, "Author contributions"),
                    P("R.M.O. and M.K.S. designed the study; R.M.O. and D.J.W. performed the experiments; H.-w.P. carried out "
                      "the DSF measurements; L.F.-I. contributed the lid-conformation analysis; all authors wrote and approved "
                      "the manuscript. The authors declare no competing financial interest."),
                    H(2, "Data availability"),
                    P("Raw plate-reader data and fitting scripts are available at "
                      "[data.lakeshore-state.example/tll-sba15](https://data.lakeshore-state.example/tll-sba15)."),
                ]),
                box("footnote", "¹ Lipozyme® is a registered trademark of its owner; its use does not imply endorsement."),
                box("footnote", "² All temperatures refer to the reaction medium, measured with a calibrated Pt100 probe (± 0.1 °C)."),
            ],
            [
                H(2, "References"),
                columns([L(refs, ordered=True)]),
                H(2, "Supporting Information"),
                P("The Supporting Information is available free of charge: nitrogen physisorption isotherms and pore-size "
                  "distributions (Figure S1), Lineweaver–Burk and Arrhenius plots (Figures S2–S3), DSF melting curves "
                  "(Figure S4), full deactivation time courses (Table S1) and the leaching data (Table S2).", "small"),
                P("© 2026 The Authors. Published under a CC BY 4.0 licence. https://doi.org/10.5555/jab.2026.0412", "small center"),
            ],
        ],
    }



def paper_engb() -> dict[str, Any]:
    """Catchment hydrology paper (LibreOffice, Math objects, two-column sections)."""
    sites = [("WB1", "6 m grass", 2.1, "sandy loam", "Lolium/Festuca sward"),
             ("WB2", "12 m grass", 1.8, "sandy loam", "Lolium/Festuca sward"),
             ("WB3", "12 m willow", 2.4, "loam over chalk", "Salix viminalis coppice"),
             ("WB4", "20 m woodland", 1.5, "clay loam", "Alnus/Fraxinus woodland")]
    t1 = table("t1", [["Site", "Buffer", "Slope (%)", "Soil texture", "Vegetation", "Piezometers"],
                      *[[a, b, f"{c:.1f}", d, e, str(n)] for (a, b, c, d, e), n in zip(sites, [6, 8, 8, 10], strict=True)]],
               caption="Table 1. Characteristics of the four monitored buffer strips (Wensum catchment, Norfolk).",
               align=["l", "l", "r", "l", "l", "r"], widths=[9, 17, 11, 19, 30, 14])
    seasonal = {"WB1": [(11.8, 8.9), (13.4, 10.7), (9.6, 7.9), (12.1, 9.8)],
                "WB2": [(12.2, 6.4), (13.9, 8.1), (9.9, 5.6), (12.6, 7.0)],
                "WB3": [(11.5, 4.1), (14.2, 6.3), (10.3, 3.2), (12.8, 4.9)],
                "WB4": [(12.0, 2.9), (13.6, 4.4), (10.1, 2.2), (12.4, 3.1)]}
    seasons = ["Autumn 2024", "Winter 2024/25", "Spring 2025", "Summer 2025"]
    short = ["Autumn 2024", "Winter 2024/25", "Spring 2025", "Summer 2025"]
    rows, eff = [], {}
    for site, values in seasonal.items():
        eff[site] = [round((cin - cout) / cin * 100, 1) for cin, cout in values]
        rows.append([site, *[f"{v:.1f}" for pair in values for v in pair]])
    head1 = ["Site"] + [x for season in short for x in (season, "")]
    head2 = [""] + ["Cin", "Cout"] * 4
    t2 = table("t2", [head1, head2, *rows], header_rows=2,
               merges=((0, 0, 2, 1), (0, 1, 1, 2), (0, 3, 1, 2), (0, 5, 1, 2), (0, 7, 1, 2)),
               caption="Table 2. Seasonal flow-weighted mean nitrate-N concentrations (mg N L⁻¹) at the field edge (Cin) and the stream edge (Cout).",
               align=["l"] + ["r"] * 8, widths=[12] + [11] * 8)
    seasons = short
    bar_spec = {"title": "Nitrate removal efficiency by site and season (%)", "categories": ["WB1", "WB2", "WB3", "WB4"],
                "series": [(season, [eff[s][k] for s in ["WB1", "WB2", "WB3", "WB4"]]) for k, season in enumerate(seasons)],
                "max": 100, "ticks": 5, "tick_format": lambda v: f"{v:.0f}"}
    months = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    line_spec = {"title": "Monthly mean nitrate-N, WB3 (mg L⁻¹)", "categories": months,
                 "series": [("Field edge", [11.2, 12.0, 13.8, 14.6, 14.1, 12.9, 10.8, 9.9, 10.2, 11.7, 12.6, 13.0]),
                            ("Stream edge", [4.3, 4.6, 6.0, 6.9, 6.4, 4.8, 3.5, 2.9, 3.0, 3.9, 5.0, 5.6])],
                 "max": 16, "ticks": 4, "tick_format": lambda v: f"{v:.0f}"}
    perf = [["WB1", "0.81", "0.94", "+4.2"], ["WB2", "0.78", "1.12", "−6.1"], ["WB3", "0.86", "0.88", "+2.7"], ["WB4", "0.72", "0.97", "−9.4"]]
    t3 = table("t3", [["Site", "NSE (–)", "RMSE (mg N L⁻¹)", "PBIAS (%)"], *perf],
               caption="Table 3. Performance of the first-order transport model in the validation year.", align=["l", "r", "r", "r"],
               widths=[25, 25, 25, 25], width_cm=8.0)
    darcy = "<mi>q</mi><mo>=</mo><mo>−</mo><mi>K</mi><mfrac><mrow><mi>d</mi><mi>h</mi></mrow><mrow><mi>d</mi><mi>l</mi></mrow></mfrac>"
    eff_ml = ("<mi>E</mi><mo>=</mo><mfrac><mrow><msub><mi>C</mi><mi>in</mi></msub><mo>−</mo><msub><mi>C</mi><mi>out</mi></msub></mrow>"
              "<msub><mi>C</mi><mi>in</mi></msub></mfrac><mo>×</mo><mn>100</mn><mo>%</mo>")
    first = ("<mi>C</mi><mo>(</mo><mi>x</mi><mo>)</mo><mo>=</mo><msub><mi>C</mi><mn>0</mn></msub><mi>exp</mi>"
             "<mrow><mo>(</mo><mo>−</mo><mfrac><mrow><mi>k</mi><mi>x</mi></mrow><mi>v</mi></mfrac><mo>)</mo></mrow>")
    load = ("<mi>L</mi><mo>=</mo><munderover><mo>∑</mo><mrow><mi>i</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover>"
            "<msub><mi>Q</mi><mi>i</mi></msub><msub><mi>C</mi><mi>i</mi></msub><mi>Δ</mi><mi>t</mi>")
    nse = ("<mi>NSE</mi><mo>=</mo><mn>1</mn><mo>−</mo><mfrac><mrow><mo>∑</mo><msup><mrow><mo>(</mo><msub><mi>O</mi><mi>i</mi></msub><mo>−</mo>"
           "<msub><mi>P</mi><mi>i</mi></msub><mo>)</mo></mrow><mn>2</mn></msup></mrow><mrow><mo>∑</mo><msup><mrow><mo>(</mo><msub><mi>O</mi><mi>i</mi></msub>"
           "<mo>−</mo><mover><mi>O</mi><mo>¯</mo></mover><mo>)</mo></mrow><mn>2</mn></msup></mrow></mfrac>")
    refs = [
        "Burt, T. P., Matchett, L. S., Goulding, K. W. T., Webster, C. P. and Haycock, N. E. (1999) Denitrification in riparian buffer zones: the role of floodplain hydrology. *Hydrological Processes*, 13, 1451–1463.",
        "Dosskey, M. G., Vidon, P., Gurwick, N. P., Allan, C. J., Duval, T. P. and Lowrance, R. (2010) The role of riparian vegetation in protecting and improving chemical water quality in streams. *Journal of the American Water Resources Association*, 46, 261–277.",
        "Environment Agency (2024) *Nitrate Vulnerable Zones: 2025–2028 Designation Review for the Anglian River Basin District*. Bristol: Environment Agency (fictitious report EA/NVZ/2024/17).",
        "Hill, A. R. (1996) Nitrate removal in stream riparian zones. *Journal of Environmental Quality*, 25, 743–755.",
        "Mayer, P. M., Reynolds, S. K., McCutchen, M. D. and Canfield, T. J. (2007) Meta-analysis of nitrogen removal in riparian buffers. *Journal of Environmental Quality*, 36, 1172–1180.",
        "Moriasi, D. N., Arnold, J. G., Van Liew, M. W., Bingner, R. L., Harmel, R. D. and Veith, T. L. (2007) Model evaluation guidelines for systematic quantification of accuracy in watershed simulations. *Transactions of the ASABE*, 50, 885–900.",
        "Nash, J. E. and Sutcliffe, J. V. (1970) River flow forecasting through conceptual models part I — a discussion of principles. *Journal of Hydrology*, 10, 282–290.",
        "Papadopoulou, E. and Whitfield, E. J. (2023) Seasonal controls on groundwater nitrate in chalk-fed lowland catchments. *Hydrology Research Letters*, 18, 77–91.",
        "Sabater, S., Butturini, A., Clement, J.-C., Burt, T. et al. (2003) Nitrogen removal by riparian buffers along a European climatic gradient. *Ecosystems*, 6, 20–30.",
        "Vidon, P. G. F. and Hill, A. R. (2004) Landscape controls on nitrate removal in stream riparian zones. *Water Resources Research*, 40, W03201.",
        "Whitfield, E. J., ap Gwilym, R. and Wiśniewski, T. (2022) A low-cost piezometer network for buffer-strip monitoring. *Field Hydrology Notes*, 7, 12–25.",
        "Wiśniewski, T. and Kowalczyk, A. (2021) Willow short-rotation coppice as a nitrate sink on arable margins. *Polish Journal of Agro-Ecology*, 33, 145–158.",
    ]
    return {
        "template": "scientific_paper", "page_size": "A4", "languages": ["en-GB", "el", "pl", "cy"], "tagged": True,
        "metadata": _meta("Seasonal nitrate attenuation in riparian buffer strips of a lowland chalk catchment",
                          "Eleanor J. Whitfield; Tomasz Wiśniewski; Eleni Papadopoulou; Rhodri ap Gwilym",
                          "Hydrology and Land Management 9 (2026) 233–239",
                          ["riparian buffer", "nitrate", "denitrification", "groundwater", "Norfolk", "water quality"], "en-GB",
                          "2026-04-22T10:30:00Z"),
        "theme": {"accent": "#2f5130", "lo_size": "10pt", "lo_font": "Noto Serif", "lo_heading_font": "Noto Sans", "lo_margin": "1.8cm"},
        "running_header": "Whitfield et al. · Hydrology and Land Management 9 (2026) 233–239",
        "running_footer": "Page {page} of {pages}",
        "pages": [
            [
                P("ORIGINAL ARTICLE · Open Access", "small"),
                H(1, "Seasonal nitrate attenuation in riparian buffer strips of a lowland chalk catchment"),
                P("Eleanor J. Whitfield¹*, Tomasz Wiśniewski², Eleni Papadopoulou (Ελένη Παπαδοπούλου)³ and Rhodri ap Gwilym¹"),
                P("¹ School of Geography and Environment, Fenland University, Earlham Road, Norwich NR4 7TJ, United Kingdom · "
                  "² Instytut Gleboznawstwa i Ochrony Wód, ul. Łąkowa 14, 60-512 Poznań, Poland · "
                  "³ Institute of Soil and Water Research, Thermi 570 01, Thessaloniki, Greece", "small"),
                H(2, "Abstract"),
                P("Riparian buffer strips are a mainstay of agri-environment schemes in England, but their effectiveness in "
                  "permeable chalk catchments, where much of the nitrate travels as deep groundwater, remains uncertain. "
                  "We monitored four buffer strips of contrasting width and vegetation in the Wensum catchment, Norfolk, "
                  "between October 2024 and September 2025 using 32 nested piezometers. Flow-weighted mean nitrate-N "
                  "concentrations at the field edge ranged from 9.6 to 14.2 mg L⁻¹. Removal efficiency increased with "
                  "buffer width and woody vegetation, from 18–26 % in a 6 m grass strip to 64–78 % in a 20 m woodland strip, "
                  "and was lowest in winter, when shallow flow paths were short-circuited by high water tables. A first-order "
                  "transport model reproduced the observed concentrations with Nash–Sutcliffe efficiencies of 0.72–0.86. "
                  "Our results suggest that, on permeable soils, strips narrower than 12 m deliver limited benefit unless "
                  "they are planted with deep-rooting woody species.", "lead"),
                P("**Keywords:** riparian buffer; nitrate; denitrification; groundwater; chalk aquifer; agri-environment schemes", "small"),
                columns([
                    H(2, "1. Introduction"),
                    P("Diffuse nitrate pollution from arable land remains the main reason why many English rivers fail to reach "
                      "good ecological status under the Water Framework Directive. In the Anglian river basin district, more "
                      "than 70 % of the land area is designated as a Nitrate Vulnerable Zone (NVZ), and groundwater nitrate "
                      "concentrations in parts of the chalk aquifer continue to rise decades after fertiliser inputs were "
                      "reduced (Environment Agency, 2024)."),
                    P("Vegetated buffer strips along watercourses are promoted as a low-cost mitigation measure. Their "
                      "nitrate-removal capacity rests on two processes: plant uptake in the root zone and microbial "
                      "denitrification in waterlogged, carbon-rich soils near the stream (Hill, 1996; Burt et al., 1999). "
                      "Both depend on groundwater actually passing through the biologically active layer. Where flow paths "
                      "are deep, as is typical of permeable chalk and sandy soils, much of the nitrate may bypass the buffer "
                      "altogether (Vidon and Hill, 2004)."),
                    P("Meta-analyses report a wide spread of removal efficiencies, from almost zero to over 90 %, with buffer "
                      "width explaining only part of the variation (Mayer et al., 2007). Subsurface hydrology, soil texture "
                      "and vegetation type appear at least as important. Field data from lowland chalk catchments are scarce, "
                      "and most British studies have been carried out on clay soils with predominantly shallow flow "
                      "(Sabater et al., 2003; Dosskey et al., 2010)."),
                    P("This study addresses that gap. We asked (i) how nitrate removal in buffer strips on a permeable chalk "
                      "catchment varies with buffer width and vegetation, (ii) how removal changes through the hydrological "
                      "year, and (iii) whether a simple first-order transport model can reproduce the observations well "
                      "enough to support the design of new strips."),
                ]),
                box("footnote", "* Corresponding author: e.whitfield@fenland-uni.example · Received 14 January 2026; accepted 3 April 2026."),
            ],
            [
                columns([
                    H(2, "2. Study area and methods"),
                    H(3, "2.1 Study sites"),
                    P("The River Wensum rises near Fakenham and flows south-east for 78 km to join the Yare at Norwich. Its "
                      "catchment (650 km²) is underlain by Upper Cretaceous chalk covered by glacial till and outwash sands, "
                      "and is dominated by cereal, sugar beet and outdoor pig production. Mean annual rainfall at the "
                      "Swanton Morley gauge is 678 mm, and baseflow contributes about 80 % of river discharge."),
                ]),
                photo("f1", ["aerial-farmland", "farm-field"], ["agriculture"],
                          {"aerial-farmland": "Figure 1. Arable landscape of the middle Wensum valley; field margins and buffer strips run along the drainage network.",
                           "farm-field": "Figure 1. Arable field adjoining buffer strip WB2 in early spring."},
                          "Figure 1. Arable land in the study area.", "none", width="70%", width_cm=11.0),
                columns([
                    P("Four buffer strips were selected on three farms between Lyng and Ringland so that they shared similar "
                      "upslope land use (winter wheat in 2024/25) but differed in width and vegetation (Table 1). WB1 and WB2 "
                      "are grass strips established under a Countryside Stewardship agreement in 2016; WB3 was planted with "
                      "willow coppice in 2014; WB4 is a remnant strip of alder and ash woodland."),
                    P("At each site, transects of nested piezometers were installed perpendicular to the stream, with "
                      "screens at 0.5–1.0 m and 2.0–2.5 m below ground. Piezometers were made of 32 mm HDPE pipe with "
                      "0.3 mm slotted screens and sealed with bentonite. Ground and pipe elevations were surveyed by RTK GNSS "
                      "(± 1 cm). The network has been described in detail by Whitfield et al. (2022)."),
                    P("Soil cores (0–100 cm) were taken next to each piezometer in September 2024 and analysed for texture, "
                      "organic carbon and bulk density. Saturated hydraulic conductivity was estimated from slug tests in "
                      "every deep piezometer, using the Bouwer–Rice method."),
                ]),
                t1,
                columns([
                    P("Field operations on the upslope fields followed normal commercial practice. Nitrogen was applied to "
                      "winter wheat at 190–220 kg N ha⁻¹ in three splits between late February and early May 2025, recorded "
                      "by the farmers in their nutrient management plans. No fertiliser or manure was applied within the "
                      "buffer strips, and the grass strips were cut once in late July."),
                    P("Weather during the study year was close to the long-term average, although January 2025 was wet "
                      "(118 % of normal rainfall) and the summer of 2025 was dry and warm, with a soil moisture deficit "
                      "exceeding 110 mm from mid-July."),
                ]),
            ],
            [
                columns([
                    H(3, "2.2 Hydrological monitoring"),
                    P("Water levels in all piezometers were logged every 30 min with pressure transducers (accuracy ± 0.5 cm) "
                      "and corrected for barometric pressure. Lateral specific discharge through each buffer was calculated "
                      "with Darcy’s law,"),
                    equation("eq1", darcy, "q = −K · dh/dl", "q = -K {dh} over {dl}", number="(1)"),
                    P("where q is the specific discharge (m d⁻¹), K the saturated hydraulic conductivity (m d⁻¹) and dh/dl "
                      "the hydraulic gradient between the field-edge and stream-edge piezometers. K varied from 0.4 m d⁻¹ in "
                      "the clay loam at WB4 to 3.9 m d⁻¹ in the sandy loam at WB1 and WB2."),
                    H(3, "2.3 Sampling and chemical analysis"),
                    P("Groundwater was sampled fortnightly from October 2024 to September 2025 (26 rounds) after purging "
                      "three pipe volumes. Samples were filtered in the field (0.45 µm), kept below 4 °C and analysed within "
                      "48 h for nitrate-N, ammonium-N and dissolved organic carbon. Nitrate was determined by ion "
                      "chromatography (limit of detection 0.02 mg N L⁻¹); duplicates agreed within 3 %. Dissolved oxygen and "
                      "redox potential were measured in situ with a flow-through cell."),
                    P("The removal efficiency E of each buffer was computed from flow-weighted mean concentrations at the "
                      "field edge (Cin) and the stream edge (Cout):"),
                    equation("eq2", eff_ml, "E = (Cin − Cout) / Cin × 100 %", 'E = {C_{in} - C_{out}} over {C_{in}} times 100 "%"', number="(2)"),
                    P("To separate attenuation from dilution, chloride was used as a conservative tracer. Nitrate-to-chloride "
                      "ratios at the stream edge were on average 6 % lower than raw concentration ratios, showing that "
                      "dilution by rainfall recharge within the strips was minor."),
                ]),
                photo("f2", ["farm-field", "aerial-farmland"], ["agriculture"],
                          {"farm-field": "Figure 2. Piezometer transect at WB2 (grass, 12 m) in March 2025; the stream lies beyond the hedge line.",
                           "aerial-farmland": "Figure 2. Aerial view of the buffer strips sampled in March 2025."},
                          "Figure 2. Monitoring transect in March 2025.", "none", width="60%", width_cm=9.5),
                columns([
                    H(3, "2.4 Transport model"),
                    P("Assuming steady lateral flow and first-order removal, the concentration at distance x from the field "
                      "edge is"),
                    equation("eq3", first, "C(x) = C₀ · exp(−k·x / v)", "C(x) = C_0 exp left( - {k x} over {v} right)", number="(3)"),
                    P("where C₀ is the field-edge concentration, k the first-order removal rate (d⁻¹) and v the pore-water "
                      "velocity (m d⁻¹), obtained by dividing q by an effective porosity of 0.30. The rate k was calibrated "
                      "separately for each site and season on data from the first six months."),
                ]),
            ],
            [
                columns([
                    P("Annual nitrate loads entering and leaving each strip per metre of stream bank were obtained by "
                      "summing fortnightly fluxes,"),
                    equation("eq4", load, "L = Σᵢ Qᵢ · Cᵢ · Δt", "L = sum from {i=1} to {n} Q_i C_i %DELTA t", number="(4)"),
                    P("where Qᵢ is the lateral discharge per metre of bank, Cᵢ the concentration and Δt the length of the "
                      "sampling interval (14 d). Model performance in the validation period (April–September 2025) was "
                      "assessed with the Nash–Sutcliffe efficiency (Nash and Sutcliffe, 1970),"),
                    equation("eq5", nse, "NSE = 1 − Σ(Oᵢ − Pᵢ)² / Σ(Oᵢ − Ō)²",
                             "NSE = 1 - {sum (O_i - P_i)^2} over {sum (O_i - overline O)^2}", number="(5)"),
                    P("together with the root-mean-square error (RMSE) and the percent bias (PBIAS), following the guidelines "
                      "of Moriasi et al. (2007)."),
                    H(2, "3. Results"),
                    H(3, "3.1 Hydrology"),
                    P("Water tables responded quickly to winter rainfall. At WB1 and WB2 the water table rose to within "
                      "0.3 m of the surface in January and February 2025, while at WB4 it remained between 0.6 and 1.1 m "
                      "below ground throughout the year. Hydraulic gradients towards the stream were steepest in winter "
                      "(0.021–0.034) and reversed briefly at WB3 in August, when the river was fed by upstream releases."),
                    P("Mean lateral specific discharge was highest at the sandy grass sites (0.08 m d⁻¹) and lowest at the "
                      "woodland site (0.01 m d⁻¹). Residence times within the strips, estimated from v and buffer width, "
                      "thus ranged from about 23 days at WB1 to more than four years at WB4. This difference of two orders "
                      "of magnitude is the key to the contrasting removal described below."),
                    P("Dissolved oxygen in the shallow piezometers fell below 2 mg L⁻¹ at the stream edge of WB3 and WB4 "
                      "for most of the year, whereas the grass strips remained oxic (> 5 mg L⁻¹) except during short "
                      "waterlogging episodes in January. Redox potential followed the same pattern."),
                ]),
                chart("f3", "line", line_spec, "Figure 3. Monthly mean nitrate-N concentration at the field edge and stream edge of WB3, October 2024 – September 2025.",
                      raster=True, width="80%", width_cm=13.0, size=(560, 230)),
                chart_table("c3", "Month", line_spec, lambda v: f"{v:.1f}"),
            ],
            [
                H(3, "3.2 Nitrate removal"),
                t2,
                columns([
                    P("Field-edge concentrations were similar at all sites (Table 2), confirming that upslope inputs were "
                      "comparable. Stream-edge concentrations, by contrast, differed markedly. Removal efficiency at the "
                      "6 m grass strip WB1 was only 18–25 %, whereas the 20 m woodland strip WB4 removed 68–78 % of the "
                      "incoming nitrate in every season (Figure 4). Doubling the grass strip width from 6 to 12 m raised efficiency "
                      "to 40–48 %; replacing grass by willow at the same width raised it further to 56–69 %."),
                    P("At all sites, removal was lowest in winter. During this period the high water table shortened "
                      "residence times and part of the flow passed through the topsoil as near-surface runoff, which is "
                      "poorly connected to the denitrifying zone. Removal was highest in spring at the woody sites, "
                      "coinciding with root growth and maximum dissolved organic carbon (up to 18 mg C L⁻¹ at WB4)."),
                    P("Expressed as annual loads per metre of stream bank, WB1 and WB2 received the largest inputs "
                      "(3.1 and 2.9 kg N m⁻¹ yr⁻¹) because of their high discharge, and WB4 the smallest "
                      "(0.4 kg N m⁻¹ yr⁻¹). The absolute mass removed was therefore highest at WB2 and WB3 "
                      "(1.3 and 1.6 kg N m⁻¹ yr⁻¹), even though their removal efficiency was below that of WB4."),
                    P("Ammonium concentrations were low throughout (< 0.1 mg N L⁻¹), so nitrate was not converted into "
                      "other mobile forms of inorganic nitrogen. Nitrous oxide was not measured; however, the strong decline "
                      "of nitrate together with oxygen depletion points to denitrification as the dominant sink at the woody "
                      "sites, with plant uptake contributing mainly in spring."),
                ]),
                chart("f4", "bar", bar_spec, "Figure 4. Seasonal removal efficiency for the four buffer strips computed with Eq. (2) from Table 2.",
                          raster=True, width="70%", width_cm=12.0, size=(560, 230)),
                chart_table("c4", "Site", bar_spec, lambda v: f"{v:.1f}"),
            ],
            [
                columns([
                    H(3, "3.3 Model performance"),
                    P("With site- and season-specific removal rates, the first-order model reproduced stream-edge "
                      "concentrations satisfactorily (Table 3). NSE values between 0.72 and 0.86 meet the ‘good’ category "
                      "of Moriasi et al. (2007), and the bias was within ±10 % at all sites. Calibrated removal rates "
                      "ranged from 0.004 d⁻¹ (WB1, winter) to 0.031 d⁻¹ (WB3, spring)."),
                    t3,
                    P("The model tended to underestimate concentrations at WB4 after heavy rain, when preferential flow "
                      "along old root channels delivered nitrate rapidly to the stream edge. Such events are not captured "
                      "by a steady-state formulation, which explains the larger negative bias at this site."),
                    H(2, "4. Discussion"),
                    P("Our results confirm that buffer width matters, but they also show that width alone is a poor predictor "
                      "of removal on permeable soils. The 12 m willow strip removed considerably more nitrate than the 12 m "
                      "grass strip on similar soils, and the gain was largest in summer and autumn, when willow roots were "
                      "active below 1 m. This agrees with Polish and Danish experience with short-rotation coppice on "
                      "arable margins (Wiśniewski and Kowalczyk, 2021)."),
                    P("The strong seasonality has practical consequences. Most nitrate leaves arable fields in late autumn and "
                      "winter, exactly when removal in the strips is at its lowest. In annual-load terms, winter accounted "
                      "for 46 % of the nitrate entering WB2 but only 31 % of the nitrate removed. Policies that credit buffer "
                      "strips with a fixed removal percentage are therefore likely to overestimate their benefit in chalk "
                      "catchments."),
                    P("Residence time emerged as the unifying control. When the four sites are pooled, removal efficiency "
                      "increases with the logarithm of residence time (r² = 0.81, n = 16). Long residence times result "
                      "either from low conductivity, as at WB4, or from greater width. This suggests a simple design rule: "
                      "on sandy loams with K above 2 m d⁻¹, strips should be at least 15–20 m wide or planted with woody "
                      "vegetation to achieve 50 % removal in winter."),
                    P("Several limitations should be noted. Our monitoring covered a single, climatically average year, and "
                      "the deep flow paths below 2.5 m were not sampled. Some nitrate may have passed beneath all four "
                      "strips unseen; groundwater dating at a nearby borehole indicates that water at 10–15 m depth is "
                      "15–25 years old (Papadopoulou and Whitfield, 2023), so legacy nitrate will continue to reach the "
                      "river irrespective of buffer management. Finally, N₂O emissions, which could offset part of the "
                      "water-quality benefit, were not measured."),
                    P("Despite these caveats, the contrast between sites was consistent across seasons and was "
                      "reproduced by a parsimonious model, which gives us confidence in the main conclusions."),
                ]),
            ],
            [
                columns([
                    H(2, "5. Conclusions"),
                    L(["Removal efficiency increased from about 20 % in a 6 m grass strip to over 70 % in a 20 m woodland strip.",
                       "Woody vegetation roughly doubled removal compared with grass at the same width.",
                       "Removal was lowest in winter, when most nitrate leaves arable land.",
                       "A first-order transport model calibrated per site and season reproduced the data with NSE ≥ 0.72.",
                       "On permeable chalk soils, strips narrower than 12 m deliver limited benefit unless they are planted with deep-rooting species."]),
                    H(2, "Acknowledgements"),
                    P("We thank the landowners at Lyng, Weston Longville and Ringland for access to their land, and Gwen "
                      "Pritchard and Oliver Harcourt for help with fieldwork in all weathers. Diolch hefyd i Dr Siân Llewelyn "
                      "for comments on an earlier draft. The study was funded by the (fictitious) Broadland Rivers Catchment "
                      "Partnership, grant BRCP-2024-06."),
                    H(2, "Data availability statement"),
                    P("Piezometer levels and water chemistry are deposited in the Fenland University data repository "
                      "(doi:10.5555/fu.hydro.2026.014)."),
                    H(2, "References"),
                    L(refs, ordered=True),
                ]),
                box("footnote", "Conflict of interest: the authors declare no conflict of interest. © 2026 The Authors. Hydrology and Land Management is published under a CC BY 4.0 licence."),
            ],
        ],
    }



def paper_zhcn() -> dict[str, Any]:
    """Chinese transport-informatics paper (Chromium, MathML, dashboard screenshot)."""
    models = [("HA（历史均值）", 58.4, 81.2, 14.9), ("ARIMA", 52.7, 74.6, 13.6), ("LSTM", 41.3, 60.8, 10.7),
              ("GCN", 39.8, 58.1, 10.2), ("STGCN", 35.6, 52.9, 9.1), ("DCRNN", 34.9, 51.7, 8.9), ("ST-AGNN（本文）", 30.2, 45.3, 7.6)]
    t1 = table("t1", [["模型", "MAE/s", "RMSE/s", "MAPE/%"], *[[m, f"{a:.1f}", f"{b:.1f}", f"{c:.1f}"] for m, a, b, c in models]],
               caption="表1 不同模型在测试集上的预测误差（预测步长 3 站）", align=["l", "r", "r", "r"], widths=[40, 20, 20, 20],
               rendering="borderless")
    ablation = [("完整模型 ST-AGNN", 30.2, 45.3), ("去除注意力机制（w/o Attn）", 33.1, 49.0), ("去除时间卷积（w/o TCN）", 34.4, 50.6),
                ("去除天气与客流特征（w/o Ext）", 31.9, 47.8), ("使用固定邻接矩阵（Static A）", 32.7, 48.5)]
    t2 = table("t2", [["变体", "MAE/s", "RMSE/s", "MAE 增幅/%"],
                      *[[m, f"{a:.1f}", f"{b:.1f}", "—" if m.startswith("完整") else f"+{(a - ablation[0][1]) / ablation[0][1] * 100:.1f}"] for m, a, b in ablation]],
               caption="表2 消融实验结果", align=["l", "r", "r", "r"], widths=[46, 18, 18, 18])
    steps = ["1站", "2站", "3站", "4站", "5站", "6站"]
    line_spec = {"title": "MAE 随预测步长的变化（秒）", "categories": steps,
                 "series": [("LSTM", [24.8, 33.5, 41.3, 48.9, 55.2, 61.7]), ("DCRNN", [21.2, 28.6, 34.9, 40.8, 46.0, 51.3]),
                            ("ST-AGNN", [18.9, 24.7, 30.2, 35.1, 39.6, 43.8])],
                 "max": 70, "ticks": 7, "tick_format": lambda v: f"{v:.0f}"}
    bar_spec = {"title": "不同时段的 MAE（秒）", "categories": ["早高峰", "平峰", "晚高峰", "夜间"],
                "series": [("DCRNN", [41.6, 30.8, 44.2, 22.5]), ("ST-AGNN", [35.1, 27.0, 37.4, 20.3])],
                "max": 50, "ticks": 5, "tick_format": lambda v: f"{v:.0f}"}
    gcn = ("<msup><mi>H</mi><mrow><mo>(</mo><mi>l</mi><mo>+</mo><mn>1</mn><mo>)</mo></mrow></msup><mo>=</mo><mi>σ</mi><mrow><mo>(</mo>"
           "<msup><mover><mi>D</mi><mo>~</mo></mover><mrow><mo>−</mo><mn>1</mn><mo>/</mo><mn>2</mn></mrow></msup><mover><mi>A</mi><mo>~</mo></mover>"
           "<msup><mover><mi>D</mi><mo>~</mo></mover><mrow><mo>−</mo><mn>1</mn><mo>/</mo><mn>2</mn></mrow></msup>"
           "<msup><mi>H</mi><mrow><mo>(</mo><mi>l</mi><mo>)</mo></mrow></msup><msup><mi>W</mi><mrow><mo>(</mo><mi>l</mi><mo>)</mo></mrow></msup><mo>)</mo></mrow>")
    score = ("<msub><mi>e</mi><mrow><mi>i</mi><mi>j</mi></mrow></msub><mo>=</mo><mi>LeakyReLU</mi><mrow><mo>(</mo><msup><mi mathvariant='bold'>a</mi><mi>T</mi></msup>"
             "<mo>[</mo><mi>W</mi><msub><mi>h</mi><mi>i</mi></msub><mo>‖</mo><mi>W</mi><msub><mi>h</mi><mi>j</mi></msub><mo>]</mo><mo>)</mo></mrow>")
    attn = ("<msub><mi>α</mi><mrow><mi>i</mi><mi>j</mi></mrow></msub><mo>=</mo><mfrac><mrow><mi>exp</mi><mo>(</mo><msub><mi>e</mi><mrow><mi>i</mi><mi>j</mi></mrow></msub><mo>)</mo></mrow>"
            "<mrow><munder><mo>∑</mo><mrow><mi>k</mi><mo>∈</mo><msub><mi>𝒩</mi><mi>i</mi></msub></mrow></munder><mi>exp</mi><mo>(</mo><msub><mi>e</mi><mrow><mi>i</mi><mi>k</mi></mrow></msub><mo>)</mo></mrow></mfrac>")
    loss = ("<mi>ℒ</mi><mo>=</mo><mfrac><mn>1</mn><mi>N</mi></mfrac><munderover><mo>∑</mo><mrow><mi>n</mi><mo>=</mo><mn>1</mn></mrow><mi>N</mi></munderover>"
            "<mo>|</mo><msub><mi>y</mi><mi>n</mi></msub><mo>−</mo><msub><mover><mi>y</mi><mo>^</mo></mover><mi>n</mi></msub><mo>|</mo><mo>+</mo>"
            "<mi>λ</mi><msubsup><mrow><mo>‖</mo><mi>θ</mi><mo>‖</mo></mrow><mn>2</mn><mn>2</mn></msubsup>")
    rmse = ("<mi>RMSE</mi><mo>=</mo><msqrt><mrow><mfrac><mn>1</mn><mi>N</mi></mfrac><munderover><mo>∑</mo><mrow><mi>n</mi><mo>=</mo><mn>1</mn></mrow><mi>N</mi></munderover>"
            "<msup><mrow><mo>(</mo><msub><mi>y</mi><mi>n</mi></msub><mo>−</mo><msub><mover><mi>y</mi><mo>^</mo></mover><mi>n</mi></msub><mo>)</mo></mrow><mn>2</mn></msup></mrow></msqrt>")
    dash = {"brand": "鹭岛公交 · 智能调度", "nav": ["运行监控", "到站预测", "线路分析", "客流统计", "系统设置"],
            "title": "到站时间预测 — 18路（火车站 ⇄ 软件园三期）", "range": "2025-11-18 07:00–09:00",
            "kpis": [("在线车辆", "46", "+2"), ("平均预测误差", "29.6 秒", "−4.1 秒"), ("准点率", "87.4%", "+3.2%"), ("告警", "3", "+1")],
            "series": [31, 29, 34, 38, 41, 37, 33, 30, 28, 27, 29, 31, 30, 28, 26],
            "series_title": "近两小时 MAE（秒）",
            "rows": [["车辆", "下一站", "预测到站", "实际到站", "误差"], ["闽D·3K217", "湖滨东路", "07:42:10", "07:42:31", "+21 秒"],
                     ["闽D·5L908", "莲坂", "07:44:55", "07:44:40", "−15 秒"], ["闽D·2H663", "软件园二期", "07:47:20", "07:47:52", "+32 秒"]],
            "table_title": "最近到站记录", "height": 470}
    refs = [
        "Kipf T N, Welling M. Semi-supervised classification with graph convolutional networks[C]//Proceedings of ICLR. Toulon, 2017.",
        "Veličković P, Cucurull G, Casanova A, et al. Graph attention networks[C]//Proceedings of ICLR. Vancouver, 2018.",
        "Yu B, Yin H, Zhu Z. Spatio-temporal graph convolutional networks: a deep learning framework for traffic forecasting[C]//Proceedings of IJCAI. Stockholm, 2018: 3634-3640.",
        "Li Y, Yu R, Shahabi C, et al. Diffusion convolutional recurrent neural network: data-driven traffic forecasting[C]//Proceedings of ICLR. Vancouver, 2018.",
        "陈晓明, 林雅婷. 基于 GPS 数据的公交行程时间可靠性分析[J]. 交通运输系统工程与信息, 2022, 22(4): 118-126.",
        "王志强, 刘倩, 郑凯. 融合多源数据的公交到站时间预测方法[J]. 中国公路学报, 2023, 36(7): 201-212.",
        "Hochreiter S, Schmidhuber J. Long short-term memory[J]. Neural Computation, 1997, 9(8): 1735-1780.",
        "许文博, 黄思远. 城市公交运行图的自适应邻接矩阵学习[J]. 计算机应用研究, 2024, 41(3): 755-761.",
        "Bai L, Yao L, Li C, et al. Adaptive graph convolutional recurrent network for traffic forecasting[C]//Advances in NeurIPS. 2020: 17804-17815.",
        "厦门市交通运输局. 2024 年厦门市城市公共交通发展年度报告[R]. 厦门, 2025.",
    ]
    return {
        "template": "scientific_paper", "page_size": "A4", "languages": ["zh-CN", "en"],
        "metadata": _meta("基于时空自适应图神经网络的城市公交到站时间预测", "林嘉怡; 周文涛; 郑海峰; 陈思源",
                          "交通信息与智能系统, 2026, 12(3): 45-50",
                          ["公交到站时间", "图神经网络", "注意力机制", "智能交通", "ST-AGNN"], "zh-CN", "2026-03-15T02:00:00Z"),
        "theme": {"accent": "#7a1f1f", "font_size": "11.2pt", "body_font": "'Noto Serif CJK SC', 'Noto Serif'",
                  "heading_font": "'Noto Sans CJK SC'", "margins": "18mm 16mm 18mm 16mm",
                  "extra_css": "html{line-height:1.6}figure{break-inside:avoid}h1{text-align:center;font-size:1.7em}"
                               ".cols{column-gap:6mm;column-rule:none}.cols h2{font-size:1.1em;border:none;margin-top:.6em}"
                               ".cols p{text-align:justify;text-indent:2em}p.center{text-align:center}.cols h3{font-size:1em}"
                               "ol li{font-size:.85em}"},
        "running_header": "交通信息与智能系统　Journal of Traffic Information and Intelligent Systems　2026年3月",
        "running_footer": "· {page} ·",
        "pages": [
            [
                P("文章编号：2096-5555（2026）03-0045-06　　DOI：10.5555/jtiis.2026.03.008", "small"),
                H(1, "基于时空自适应图神经网络的城市公交到站时间预测"),
                P("林嘉怡¹，周文涛¹，郑海峰²，陈思源¹*", "center"),
                P("（1. 鹭江大学 交通与物流学院，福建 厦门 361005；2. 鹭岛公交集团有限公司 智能调度中心，福建 厦门 361012）", "small center"),
                P("**摘　要：**准确的公交到站时间预测是提升公交服务可靠性和乘客出行体验的关键。现有方法多将线路视为独立序列，难以刻画站点之间随时间变化的空间依赖。"
                  "本文提出一种时空自适应图神经网络（Spatio-Temporal Adaptive Graph Neural Network，ST-AGNN）：在空间维度上，以图卷积与图注意力相结合的方式，"
                  "根据实时运行状态动态调整站点间的连接权重；在时间维度上，采用门控时间卷积捕捉多尺度周期特征，并融合天气、客流等外部因素。"
                  "基于厦门市 26 条公交线路、为期 6 个月的 GPS 与 IC 卡数据的实验表明，在预测 3 站的情形下，ST-AGNN 的平均绝对误差（MAE）为 30.2 秒，"
                  "较 DCRNN 降低 13.5%，在早晚高峰时段优势更为明显。"),
                P("**关键词：**公交到站时间；图神经网络；注意力机制；时空数据；智能交通"),
                P("**中图分类号：**U491.1+7　　**文献标志码：**A", "small"),
                P("**Abstract:** Accurate bus arrival time prediction is essential for reliable public transport. We propose ST-AGNN, "
                  "a spatio-temporal adaptive graph neural network that combines graph convolution with graph attention to learn "
                  "time-varying dependencies between stops, and gated temporal convolution to capture multi-scale periodicity. "
                  "Experiments on six months of GPS and smart-card data from 26 routes in Xiamen show a mean absolute error of 30.2 s "
                  "for three-stop-ahead prediction, 13.5% lower than DCRNN.", "small"),
                columns([
                    H(2, "0　引言"),
                    P("公共交通是缓解城市拥堵、降低碳排放的重要手段。随着“公交优先”战略的推进，乘客对出行时间可预期性的要求不断提高。"
                      "研究表明，候车时间的不确定性比候车时间本身更影响乘客满意度［5］。因此，向乘客实时发布准确的到站时间，"
                      "已成为各地智慧公交系统的基本功能。"),
                    P("公交到站时间受道路拥堵、信号控制、上下客时间及天气等多种因素影响，具有明显的非线性和时空相关性。"
                      "早期研究主要采用历史均值、卡尔曼滤波和 ARIMA 等统计模型，其优点是计算简单，但难以适应突发事件。"
                      "近年来，LSTM 等循环神经网络被广泛用于行程时间预测［7］，但它们通常把每条线路视为独立的时间序列，忽略了不同线路共用路段时的相互影响。"),
                    P("以厦门市为例，岛内主干道上平均每个路段有 4.3 条线路共线运行，同一路段上不同线路的车辆行程时间高度相关［10］。"
                      "如果能够利用这种跨线路的信息，就有望在单条线路数据稀疏（如平峰、夜间）时仍保持较高的预测精度。"),
                    P("另一方面，公交运行还具有不同于一般道路交通的特点：车辆按时刻表发车，在站点停靠，受乘客上下车影响显著；"
                      "同一线路的前后车辆之间存在“串车”现象，前车延误会导致后车载客减少、停站时间缩短。"
                      "因此，直接套用路网速度预测模型往往难以取得理想效果，需要针对公交网络的结构和运行规律进行专门设计。"),
                    P("在数据层面，车载 GPS 的定位误差、信号遮挡以及 IC 卡数据的时间偏差都会给建模带来噪声。"
                      "现有研究多基于单一线路或少量线路开展实验，模型在大规模线网上的表现和可部署性仍缺乏验证［6］。"
                      "此外，实际系统对预测的时效性有严格要求，模型的推理时间必须控制在秒级以内。"),
                    P("基于上述分析，本文从公交网络的图结构出发，研究能够同时刻画动态空间依赖和多尺度时间规律的到站时间预测模型，"
                      "并在厦门市的真实数据上进行验证和部署。本文其余部分安排如下：第 1 节给出问题定义；第 2 节介绍模型结构；"
                      "第 3 节报告实验结果；第 4 节总结全文。"),
                ]),
                box("footnote", "收稿日期：2025-12-02；修回日期：2026-01-20。基金项目：福建省自然科学基金（2025J0555）。"
                    "作者简介：林嘉怡（1997—），女，博士研究生，研究方向为交通大数据。*通信作者：陈思源，E-mail：sychen@lujiang-univ.example"),
            ],
            [
                columns([
                    P("图神经网络（GNN）为建模交通网络的空间结构提供了新的思路。Kipf 等［1］提出的图卷积网络（GCN）可以在图结构数据上进行高效的特征传播；"
                      "Yu 等［3］和 Li 等［4］分别提出 STGCN 和 DCRNN，在路网速度预测中取得了显著效果。然而，这些方法大多依赖预先给定的静态邻接矩阵，"
                      "而公交站点之间的关联强度会随时段、天气和客流显著变化。例如，早高峰时某一拥堵路段的延误会迅速向下游多个站点传播，平峰时则影响有限。"),
                    P("针对上述问题，本文的主要贡献如下：（1）构建以站点为节点、以路段为边的公交运行图，并提出融合图卷积与图注意力的自适应空间模块；"
                      "（2）设计多尺度门控时间卷积，联合建模日周期与周周期；（3）在真实数据集上进行了系统的对比与消融实验，验证了模型的有效性。"),
                    H(2, "1　问题定义"),
                    P("将公交网络表示为有向图 G =（V，E，A），其中 V 为站点集合，|V| = N；E 为相邻站点之间的路段；A ∈ ℝ^(N×N) 为邻接矩阵。"
                      "在时刻 t，每个站点的特征 x_t ∈ ℝ^F 包括最近 5 辆车的路段行程时间、停站时间、刷卡人数以及降雨强度等。"
                      "给定过去 T 个时间片的观测，模型的目标是预测未来 τ 个站点的到站时间。本文中时间片长度为 5 分钟，T = 12。"),
                    H(2, "2　模型结构"),
                    H(3, "2.1　自适应空间模块"),
                    P("首先，在邻接矩阵上加入自环 Ã = A + I，并以对称归一化的方式进行图卷积："),
                    equation("eq1", gcn, "H^(l+1) = σ(D̃^(−1/2) Ã D̃^(−1/2) H^(l) W^(l))", "H^{(l+1)} = %sigma ( tilde D^{-1/2} tilde A tilde D^{-1/2} H^{(l)} W^{(l)} )", number="（1）"),
                    P("式中，D̃ 为 Ã 的度矩阵，W^(l) 为第 l 层的可学习权重，σ 为 ReLU 激活函数。静态图卷积只能反映线路的拓扑结构，"
                      "为此我们进一步引入图注意力机制［2］，根据节点当前状态计算动态权重："),
                    equation("eq2", score, "e_ij = LeakyReLU(aᵀ [W h_i ‖ W h_j])", 'e_{ij} = LeakyReLU ( bold a^T [ W h_i "‖" W h_j ] )', number="（2）"),
                    equation("eq3", attn, "α_ij = exp(e_ij) / Σ_(k∈N_i) exp(e_ik)", "%alpha_{ij} = {exp(e_{ij})} over {sum from {k in N_i} exp(e_{ik})}", number="（3）"),
                    P("最终的空间表示为静态卷积输出与注意力加权输出之和，两者的比例由一个可学习的门控系数控制。"
                      "这样，当某一路段发生拥堵时，模型可以自动提高其对下游站点的影响权重。"),
                    P("为降低计算量，注意力只在每个站点的 K 阶邻域内计算，本文取 K = 3。对于共线路段，不同线路的同一站点被合并为一个节点，"
                      "其特征取各线路最近车辆的加权平均，权重为车辆距站点的距离的倒数。经过合并后，运行图共有 612 个节点和 1 487 条边。"
                      "空间模块共堆叠 2 层，每层的隐藏维度为 64，注意力头数为 4。"),
                    P("值得注意的是，自适应权重并非完全由数据驱动。为避免模型学习到不符合实际的长距离依赖，"
                      "我们将注意力得分与路网最短路径距离的高斯核相乘，使物理上相距较远的站点之间的权重自然衰减。"),
                ]),
            ],
            [
                columns([
                    H(3, "2.2　多尺度时间模块"),
                    P("时间维度上采用扩张因果卷积，扩张率依次为 1、2、4，使感受野覆盖最近 1 小时的观测；同时，将前一天和前一周同一时段的数据作为额外输入，"
                      "以捕捉日周期与周周期。门控机制采用 tanh 与 sigmoid 的逐元素乘积，可抑制无关的历史信息。"
                      "外部特征（天气、节假日标志、客流）经全连接层编码后与时空特征拼接。"),
                    P("与循环神经网络相比，卷积结构可以并行计算所有时间片，训练速度约为 DCRNN 的 3.2 倍。"
                      "为了兼顾短期波动与长期趋势，我们在时间模块的输出端设置了一个残差连接，并对不同扩张率的输出进行加权融合。"),
                    H(3, "2.3　损失函数"),
                    P("考虑到到站时间误差的分布存在长尾，本文采用 L1 损失并加入 L2 正则项："),
                    equation("eq4", loss, "L = (1/N) Σ |y_n − ŷ_n| + λ‖θ‖²", "func L = 1 over N sum from {n=1} to N abs{ y_n - hat y_n } + %lambda lline %theta rline ^2", number="（4）"),
                    P("其中 λ = 1×10⁻⁴。模型使用 Adam 优化器训练，初始学习率为 0.001，每 20 轮衰减为原来的一半，批大小为 64，最多训练 120 轮，"
                      "并在验证集误差连续 10 轮不下降时提前停止。"),
                    H(2, "3　实验"),
                    H(3, "3.1　数据集"),
                    P("实验数据来自鹭岛公交集团 2025 年 5 月至 10 月的车载 GPS 记录（采样间隔 10 秒）和 IC 卡刷卡记录，涉及 26 条线路、"
                      "612 个站点，共约 1.84 亿条 GPS 点。经地图匹配和异常值剔除后，得到 1 263 520 条站间行程记录。"
                      "按时间顺序将前 4 个月作为训练集，第 5 个月作为验证集，最后 1 个月作为测试集。"),
                    P("数据预处理包括三个步骤：（1）利用隐马尔可夫地图匹配将 GPS 点投影到线路上；（2）根据车辆进出站点 30 米缓冲区的时间确定到站与离站时刻；"
                      "（3）剔除行程时间超过同路段历史均值 3 倍标准差的记录，约占 0.8%。缺失的时间片采用同一时段前一周的数据线性插补。"),
                    photo("f1", ["city-bus", "city-street"], ["transport"],
                          {"city-bus": "图1　实验线路所用的纯电动公交车（18 路）", "city-street": "图1　18 路沿线的主干道"},
                          "图1　实验线路实景", "none", width="100%"),
                    H(3, "3.2　评价指标与对比方法"),
                    P("采用平均绝对误差（MAE）、均方根误差（RMSE）和平均绝对百分比误差（MAPE）作为评价指标，其中 RMSE 定义为"),
                    equation("eq5", rmse, "RMSE = √((1/N) Σ (y_n − ŷ_n)²)", "RMSE = sqrt{ 1 over N sum from {n=1} to N ( y_n - hat y_n )^2 }", number="（5）"),
                    P("对比方法包括：历史均值（HA）、ARIMA、LSTM［7］、GCN［1］、STGCN［3］和 DCRNN［4］。所有深度模型均在同一硬件环境"
                      "（NVIDIA RTX A5000，24 GB）下使用 PyTorch 2.3 实现，并采用相同的输入特征。"),
                    P("所有实验重复 5 次，取平均值作为最终结果，标准差均小于 0.6 秒。显著性检验采用配对 t 检验，"
                      "ST-AGNN 与次优方法之间的差异在 0.01 水平上显著。"),
                ]),
            ],
            [
                H(3, "3.3　预测精度"),
                t1,
                columns([
                    P("表1 给出了各模型在预测 3 站时的误差。可以看到，统计模型 HA 与 ARIMA 的误差最大，MAE 均超过 50 秒；"
                      "LSTM 能够利用时间依赖，误差明显降低；引入空间信息的 GCN 类方法进一步提升了精度。"
                      "本文提出的 ST-AGNN 在三项指标上均取得最优结果，MAE 为 30.2 秒，相比 DCRNN 降低 4.7 秒（13.5%），"
                      "RMSE 降低 12.4%，MAPE 降低 1.3 个百分点。"),
                    P("图2 展示了误差随预测步长的变化。各模型的误差均随步长增加而增大，但 ST-AGNN 的增长速度最慢：预测 6 站时，"
                      "其 MAE 仅为 43.8 秒，比 LSTM 低 29.0%。这说明自适应空间模块能够有效地将上游的拥堵信息传递到较远的下游站点。"),
                    chart("f2", "line", line_spec, "图2　不同预测步长下的 MAE", raster=False, width="100%", size=(440, 300)),
                    chart_table("c2", "预测步长", line_spec, lambda v: f"{v:.1f}"),
                    P("从时段来看（图3），早晚高峰的误差显著高于平峰和夜间。ST-AGNN 在早高峰将 MAE 由 41.6 秒降至 35.1 秒，"
                      "在晚高峰由 44.2 秒降至 37.4 秒，降幅均在 15% 左右，而夜间的改进仅为 2.2 秒。"
                      "高峰时段路况变化剧烈，站点之间的动态依赖更强，这正是注意力机制发挥作用的场景。"),
                    P("对注意力权重的可视化表明，早高峰时段模型对厦禾路、湖滨南路等拥堵路段赋予了明显更高的权重，"
                      "而夜间权重分布则接近静态邻接矩阵。这与调度人员的经验判断一致，也说明模型学到的空间依赖具有可解释性。"),
                    chart("f3", "bar", bar_spec, "图3　不同时段的预测误差对比", raster=True, width="100%", size=(440, 250)),
                    chart_table("c3", "时段", bar_spec, lambda v: f"{v:.1f}"),
                ]),
            ],
            [
                columns([
                    H(3, "3.4　消融实验"),
                    P("为验证各模块的作用，分别去除注意力机制、时间卷积和外部特征，或将自适应邻接矩阵替换为固定邻接矩阵，结果见表2。"
                      "去除时间卷积后误差增幅最大（+13.9%），说明多尺度时间特征是预测的基础；去除注意力机制使 MAE 增加 9.6%，"
                      "高于使用固定邻接矩阵的 8.3%，表明动态权重比静态拓扑提供了更多信息。外部特征的贡献相对较小（+5.6%），"
                      "但在降雨天气下其作用明显：雨天样本中去除外部特征导致 MAE 增加 11.2%。"),
                    t2,
                    H(3, "3.5　系统部署"),
                    P("ST-AGNN 已于 2025 年 11 月部署在鹭岛公交智能调度平台中，用于 18 路等 6 条骨干线路的实时到站发布。"
                      "模型每 30 秒更新一次预测，单次推理耗时约 42 毫秒（CPU，8 核），满足实时性要求。图4 为调度平台的运行界面，"
                      "试运行期间平均预测误差为 29.6 秒，与离线测试结果基本一致。"),
                ]),
                screenshot("f4", "dashboard", dash, "图4　智能调度平台中的到站时间预测界面（2025 年 11 月 18 日早高峰）", width="92%"),
                columns([
                    H(2, "4　结论"),
                    P("本文提出了一种用于公交到站时间预测的时空自适应图神经网络 ST-AGNN。该模型通过图卷积与图注意力相结合的空间模块，"
                      "动态刻画站点之间随时间变化的依赖关系，并通过多尺度门控时间卷积建模周期特征。实验表明，该模型在不同预测步长和时段下均优于现有方法，"
                      "且已在实际系统中稳定运行。未来工作将考虑引入信号配时数据，并研究跨城市的迁移学习方法。"),
                    P("**致谢：**感谢鹭岛公交集团智能调度中心提供数据支持，感谢匿名审稿人提出的宝贵意见。"),
                ]),
            ],
            [
                H(2, "参考文献（References）"),
                columns([L(refs, ordered=True)]),
                box("footnote", "注：本文数据经脱敏处理，车辆编号与时间均为示例。引用格式：林嘉怡，周文涛，郑海峰，等．基于时空自适应图神经网络的城市公交到站时间预测［J］．交通信息与智能系统，2026，12（3）：45-50．"),
                photo("f5", ["train-station", "city-bus"], ["transport"],
                      {"train-station": "图5　18 路起点站——厦门火车站公交枢纽", "city-bus": "图5　18 路首末站"},
                      "图5　线路起点站", "none", width="55%"),
                P("（责任编辑：张　蕾）", "small right"),
            ],
        ],
    }



def paper_ru() -> dict[str, Any]:
    """Russian building-physics paper (ReportLab, linear Unicode equations)."""
    gsop = (20 - (-4.8)) * 208
    elements = [("Наружные стены", 1840, 1.05, 3.35), ("Окна и витражи", 620, 0.39, 0.72),
                ("Покрытие (кровля)", 1450, 1.42, 4.90), ("Пол по грунту", 1450, 1.80, 1.80)]
    rows, before_total, after_total = [], 0, 0
    for name, area, r0, r1 in elements:
        q0 = round(0.024 * gsop * area / r0 / 100)  # tenths of MWh
        q1 = round(0.024 * gsop * area / r1 / 100)
        before_total += q0
        after_total += q1
        rows.append([name, number(area, "ru", 0), number(r0, "ru", 2), number(r1, "ru", 2), number(q0 / 10, "ru", 1), number(q1 / 10, "ru", 1)])
    saving = before_total - after_total
    rows.append(["Итого", "", "", "", number(before_total / 10, "ru", 1), number(after_total / 10, "ru", 1)])
    t2 = table("t2", [["Ограждающая конструкция", "Площадь A, м²", "R₀ до, м²·°C/Вт", "R₀ после, м²·°C/Вт", "Qгод до, МВт·ч", "Qгод после, МВт·ч"], *rows],
               caption="Таблица 2. Годовые трансмиссионные теплопотери здания школы № 47 до и после утепления (ГСОП = 5158 °C·сут)",
               align=["l", "r", "r", "r", "r", "r"], widths=[26, 14, 15, 15, 15, 15], total_rows=[len(rows)])
    mats = [("Кирпичная кладка (силикатный кирпич)", "640", "0,76", "0,84"), ("Минераловатная плита фасадная", "150", "0,039", "3,85"),
            ("Тонкослойная штукатурка", "8", "0,76", "0,01"), ("Экструдированный пенополистирол (кровля)", "140", "0,032", "4,38"),
            ("Железобетонная плита покрытия", "220", "2,04", "0,11")]
    t1 = table("t1", [["Материал слоя", "δ, мм", "λ, Вт/(м·°C)", "R = δ/λ, м²·°C/Вт"], *[list(m) for m in mats]],
               caption="Таблица 1. Теплотехнические характеристики материалов (по паспортам изготовителей и СП 50.13330)",
               align=["l", "r", "r", "r"], widths=[52, 14, 16, 18], rendering="borderless")
    bar_spec = {"title": "Теплопотери по конструкциям, МВт·ч/год",
                "categories": ["Стены", "Окна", "Кровля", "Пол"],
                "series": [("До утепления", [float(r[4].replace(" ", "").replace(",", ".")) for r in rows[:4]]),
                           ("После утепления", [float(r[5].replace(" ", "").replace(",", ".")) for r in rows[:4]])],
                "max": 250, "ticks": 5, "tick_format": lambda v: number(v, "ru", 0)}
    months = ["окт", "ноя", "дек", "янв", "фев", "мар", "апр"]
    line_spec = {"title": "Потребление тепловой энергии, Гкал", "categories": months,
                 "series": [("2023/24 (до)", [62, 118, 171, 198, 176, 131, 72]), ("2024/25 (после)", [41, 79, 113, 131, 117, 86, 47])],
                 "max": 200, "ticks": 4, "tick_format": lambda v: number(v, "ru", 0)}
    refs = [
        "СП 50.13330.2024. Тепловая защита зданий. Актуализированная редакция СНиП 23-02-2003. — М.: Минстрой России, 2024.",
        "СП 131.13330.2020. Строительная климатология. — М.: Минстрой России, 2020.",
        "Гагарин В. Г., Козлов В. В. Теоретические предпосылки расчёта приведённого сопротивления теплопередаче ограждающих конструкций // Строительные материалы. — 2010. — № 12. — С. 4–12.",
        "Табунщиков Ю. А., Бродач М. М. Математическое моделирование и оптимизация тепловой эффективности зданий. — М.: АВОК-ПРЕСС, 2002. — 194 с.",
        "Сафин Р. Г., Мухаметзянова Л. Р. Опыт термомодернизации школьных зданий в Республике Татарстан // Вестник строительной теплофизики. — 2024. — Т. 9, № 2. — С. 33–41.",
        "Кузнецова Е. А. Натурные тепловизионные обследования ограждающих конструкций // Энергосбережение и ресурсы. — 2023. — № 5. — С. 58–64.",
        "ГОСТ Р 54852-2021. Здания и сооружения. Метод тепловизионного контроля качества теплоизоляции ограждающих конструкций. — М.: Стандартинформ, 2021.",
        "Hens H. Building Physics — Heat, Air and Moisture. 3rd ed. — Berlin: Ernst & Sohn, 2017. — 336 p.",
    ]
    eqs = [
        equation("eq1", "<mi>R</mi><mo>=</mo><mfrac><mi>δ</mi><mi>λ</mi></mfrac>", "R = δ / λ", "R = %delta over %lambda", number="(1)"),
        equation("eq2", "<msub><mi>R</mi><mn>0</mn></msub><mo>=</mo><mfrac><mn>1</mn><msub><mi>α</mi><mi>в</mi></msub></mfrac><mo>+</mo><mo>∑</mo><mfrac><msub><mi>δ</mi><mi>i</mi></msub><msub><mi>λ</mi><mi>i</mi></msub></mfrac><mo>+</mo><mfrac><mn>1</mn><msub><mi>α</mi><mi>н</mi></msub></mfrac>", "R₀ = 1/αв + Σ δᵢ/λᵢ + 1/αн", "R_0 = 1 over alpha_v + sum delta_i over lambda_i + 1 over alpha_n", number="(2)"),
        equation("eq3", "<mi>ГСОП</mi><mo>=</mo><mo>(</mo><msub><mi>t</mi><mi>в</mi></msub><mo>−</mo><msub><mi>t</mi><mi>от</mi></msub><mo>)</mo><mo>·</mo><msub><mi>z</mi><mi>от</mi></msub>", "ГСОП = (tв − tот) · zот", "GSOP = (t_v - t_ot) cdot z_ot", number="(3)"),
        equation("eq4", "<msub><mi>Q</mi><mi>год</mi></msub><mo>=</mo><mn>0,024</mn><mo>·</mo><mi>ГСОП</mi><mo>·</mo><mo>∑</mo><mfrac><msub><mi>A</mi><mi>i</mi></msub><msub><mi>R</mi><mrow><mn>0</mn><mi>i</mi></mrow></msub></mfrac>", "Qгод = 0,024 · ГСОП · Σ (Aᵢ / R₀ᵢ)", "Q_god = 0.024 cdot GSOP cdot sum (A_i / R_0i)", number="(4)"),
        equation("eq5", "<mi>Т</mi><mo>=</mo><mfrac><mi>K</mi><mrow><mi>Δ</mi><mi>Q</mi><mo>·</mo><mi>c</mi></mrow></mfrac>", "Т = K / (ΔQ · c)", "T = K / (%DELTA Q cdot c)", number="(5)"),
    ]
    return {
        "template": "scientific_paper", "page_size": "A4", "languages": ["ru-RU", "en"],
        "metadata": _meta("Оценка эффективности термомодернизации здания общеобразовательной школы по результатам натурных измерений",
                          "Р. Г. Сафин; Л. Р. Мухаметзянова; А. В. Ершов", "Вестник строительной теплофизики, 2026, т. 11, № 1, с. 18–23",
                          ["тепловая защита", "термомодернизация", "сопротивление теплопередаче", "энергосбережение", "школьные здания"],
                          "ru-RU", "2026-02-10T07:45:00Z"),
        "theme": {"accent": "#3a2a6b", "rl_size": 10.4, "rl_serif": True, "rl_margin": 48},
        "running_header": "ВЕСТНИК СТРОИТЕЛЬНОЙ ТЕПЛОФИЗИКИ · 2026 · Т. 11, № 1",
        "running_footer": "— {page} —",
        "pages": [
            [
                P("УДК 697.1:727.1　　DOI 10.5555/vst.2026.11.1.018", "small"),
                H(1, "Оценка эффективности термомодернизации здания общеобразовательной школы по результатам натурных измерений"),
                P("**Р. Г. Сафин¹, Л. Р. Мухаметзянова¹, А. В. Ершов²**"),
                P("¹ Казанский архитектурно-строительный институт (условное наименование), 420043, г. Казань, ул. Зелёная, д. 1\n"
                  "² ООО «Теплоаудит-Поволжье», 420107, г. Казань, ул. Петербургская, д. 50, оф. 312", "small"),
                P("**Аннотация.** Рассмотрены результаты комплексной термомодернизации типового здания школы постройки 1974 года в г. Казани. "
                  "Выполнено утепление наружных стен минераловатными плитами толщиной 150 мм по системе фасадной теплоизоляции с тонким "
                  "штукатурным слоем, утепление покрытия экструдированным пенополистиролом и замена окон. Приведённое сопротивление "
                  "теплопередаче стен увеличилось с 1,05 до 3,35 м²·°C/Вт. Расчётные годовые трансмиссионные теплопотери снизились "
                  f"с {number(before_total / 10, 'ru', 1)} до {number(after_total / 10, 'ru', 1)} МВт·ч, или на {saving / before_total * 100:.0f} %. "
                  "Фактическое потребление тепловой энергии за отопительный период 2024/25 г., приведённое к одинаковым климатическим "
                  "условиям, сократилось на 33,6 %. Срок окупаемости мероприятий составил около 9 лет.", "lead"),
                P("**Ключевые слова:** тепловая защита зданий; термомодернизация; приведённое сопротивление теплопередаче; "
                  "тепловизионное обследование; энергосбережение.", "small"),
                P("**Abstract.** The paper evaluates the thermal retrofit of a 1974 school building in Kazan. External insulation raised the "
                  "thermal resistance of the walls from 1.05 to 3.35 m²·K/W; measured, weather-normalised heat consumption fell by 33.6 %.", "small"),
                columns([
                    H(2, "Введение"),
                    P("Здания общеобразовательных организаций, построенные в 1960–1980-х годах, составляют значительную часть "
                      "бюджетного жилого и общественного фонда. Их ограждающие конструкции проектировались по нормам, требования "
                      "которых к тепловой защите в 2,5–3 раза ниже современных [1]. В результате удельное потребление тепловой "
                      "энергии таких школ достигает 250–300 кВт·ч/м² в год, а расходы на отопление ложатся заметной нагрузкой "
                      "на муниципальные бюджеты."),
                    P("В рамках региональной программы капитального ремонта в 2023–2024 гг. в Республике Татарстан была проведена "
                      "термомодернизация 37 школьных зданий [5]. Оценка эффективности подобных мероприятий обычно ограничивается "
                      "расчётами на стадии проекта, тогда как сопоставление с фактическим потреблением выполняется редко."),
                    P("Цель настоящей работы — сравнить расчётные и фактические показатели тепловой защиты для одного из "
                      "типовых объектов программы и оценить экономическую эффективность выполненных мероприятий."),
                    P("Вопросам натурной проверки тепловой защиты посвящено сравнительно небольшое число публикаций. "
                      "В работе [6] по результатам тепловизионных обследований 42 зданий показано, что фактическое "
                      "сопротивление теплопередаче фасадных систем в среднем на 12–18 % ниже проектного из-за дефектов "
                      "монтажа и увлажнения утеплителя. Аналогичные выводы получены в зарубежных исследованиях [8]."),
                    P("Важно также учитывать, что после утепления меняется структура теплового баланса здания: доля "
                      "вентиляционных теплопотерь и потерь через окна возрастает, а режим работы системы отопления "
                      "требует перенастройки. Без автоматического регулирования значительная часть ожидаемой экономии "
                      "может быть утрачена из-за перетопов в переходные периоды [4]."),
                ]),
            ],
            [
                columns([
                    H(2, "Объект и методы исследования"),
                    P("Объектом исследования является трёхэтажное здание средней общеобразовательной школы № 47 "
                      "(Кировский район г. Казани) по типовому проекту 222-1-148, общей отапливаемой площадью 6 120 м² "
                      "и отапливаемым объёмом 24 300 м³. Наружные стены выполнены из силикатного кирпича толщиной 640 мм, "
                      "покрытие — из железобетонных плит с утеплителем из керамзитового гравия."),
                    P("В ходе капитального ремонта (июнь — сентябрь 2024 г.) выполнены: устройство фасадной теплоизоляции "
                      "из минераловатных плит толщиной 150 мм с тонкослойной штукатуркой; утепление покрытия плитами "
                      "экструдированного пенополистирола толщиной 140 мм; замена деревянных окон на ПВХ-блоки с двухкамерными "
                      "стеклопакетами; установка автоматизированного индивидуального теплового пункта."),
                    P("Термическое сопротивление однородного слоя определяли по формуле (1), где δ — толщина слоя, м; "
                      "λ — расчётный коэффициент теплопроводности, Вт/(м·°C). Сопротивление теплопередаче многослойной "
                      "конструкции рассчитывали по формуле (2) с коэффициентами теплоотдачи внутренней αв = 8,7 Вт/(м²·°C) "
                      "и наружной αн = 23 Вт/(м²·°C) поверхностей [1]."),
                    P("Неоднородность конструкции (оконные откосы, кронштейны, стыки плит) учитывали коэффициентом "
                      "теплотехнической однородности r = 0,86, определённым по методике [3] на основании расчёта "
                      "температурных полей узлов. Тепловизионное обследование фасадов проводили в феврале 2025 г. "
                      "при перепаде температур не менее 25 °C в соответствии с ГОСТ Р 54852 [7]."),
                ]),
                *eqs[:2],
                t1,
                columns([
                    P("Характеристики материалов приведены в таблице 1. Для старой кладки коэффициент теплопроводности "
                      "уточнён по результатам измерений влажности кернов (4,1 % по массе), что привело к значению 0,76 "
                      "вместо паспортного 0,70 Вт/(м·°C)."),
                    P("Градусо-сутки отопительного периода вычисляли по формуле (3) при tв = 20 °C, средней температуре "
                      "отопительного периода tот = −4,8 °C и его продолжительности zот = 208 сут [2]."),
                ]),
            ],
            [
                *eqs[2:4],
                columns([
                    P("Годовые трансмиссионные теплопотери через каждую конструкцию определяли по формуле (4), где Aᵢ — площадь "
                      "конструкции, м², R₀ᵢ — её приведённое сопротивление теплопередаче. Множитель 0,024 переводит "
                      "Вт·сут в кВт·ч. Теплопотери на нагрев инфильтрующегося воздуха в данной работе не рассматривались, "
                      "поскольку система вентиляции не модернизировалась."),
                    P("Фактическое потребление тепловой энергии получено по данным узла коммерческого учёта за отопительные "
                      "периоды 2023/24 и 2024/25 гг. Для сопоставимости значения приведены к нормативным градусо-суткам."),
                    H(2, "Результаты и обсуждение"),
                    P("Расчётные значения сопротивления теплопередаче и годовых теплопотерь до и после утепления приведены "
                      "в таблице 2. Наибольший вклад в снижение теплопотерь дало утепление наружных стен: потери через стены "
                      "уменьшились более чем в три раза. Утепление кровли снизило потери через покрытие на 71 %, замена окон — "
                      "на 46 %. Потери через пол по грунту остались неизменными."),
                ]),
                t2,
                columns([
                    P(f"Суммарные расчётные трансмиссионные теплопотери уменьшились на {number(saving / 10, 'ru', 1)} МВт·ч в год. "
                      "После модернизации доля окон в общих теплопотерях выросла с 30 до 44 %, что указывает на целесообразность "
                      "дальнейшего повышения их теплозащиты при следующем ремонте."),
                    P("Тепловизионное обследование подтвердило отсутствие систематических дефектов теплоизоляции. "
                      "Локальные температурные аномалии (до 2,8 °C) выявлены в зоне цокольного узла и на примыканиях "
                      "оконных блоков второго этажа, где не была выполнена изоляция откосов."),
                    P("Следует отметить, что расчёт выполнен для стационарных условий и не учитывает теплоаккумулирующую "
                      "способность массивной кирпичной кладки, которая после наружного утепления оказывается в тёплой зоне. "
                      "Это снижает амплитуду колебаний температуры в помещениях и позволяет дополнительно экономить энергию "
                      "за счёт ночного понижения температуры теплоносителя."),
                    P("Сравнение с данными по другим объектам программы [5] показывает, что достигнутое снижение "
                      "теплопотерь находится в верхней части диапазона (от 38 до 55 %), что объясняется комплексным "
                      "характером выполненных работ."),
                ]),
            ],
            [
                chart("f1", "bar", bar_spec, "Рис. 1. Годовые трансмиссионные теплопотери по видам ограждающих конструкций", raster=False,
                      width="75%", width_cm=13.0, size=(520, 250)),
                chart_table("c1", "Конструкция", bar_spec, lambda v: number(v, "ru", 1)),
                columns([
                    P("На рис. 1 наглядно показано перераспределение теплопотерь между конструкциями. Если до ремонта "
                      "основная доля приходилась на стены, то после модернизации основными «слабыми местами» стали окна и пол."),
                    P("Помесячное потребление тепловой энергии (рис. 2) в отопительном периоде 2024/25 г. оказалось на "
                      "31–35 % ниже, чем в предыдущем сезоне. С учётом того, что зима 2024/25 г. была несколько теплее "
                      "(ГСОП 4 890 против 5 205 °C·сут), приведённая экономия составила 33,6 %, что близко к расчётной "
                      "величине и подтверждает корректность принятых теплотехнических характеристик."),
                ]),
                chart("f2", "line", line_spec, "Рис. 2. Помесячное потребление тепловой энергии по данным узла учёта", raster=True,
                      width="75%", width_cm=13.0, size=(520, 230)),
                chart_table("c2", "Месяц", line_spec, lambda v: number(v, "ru", 0)),
            ],
            [
                columns([
                    P("Экономическую эффективность оценивали по простому сроку окупаемости (5), где K — капитальные затраты "
                      "на утепление, руб.; ΔQ — годовая экономия тепловой энергии, Гкал; c — тариф на тепловую энергию, "
                      "руб./Гкал. При K = 21,4 млн руб., ΔQ = 296 Гкал и тарифе 2 643 руб./Гкал (2025 г.) с учётом "
                      "ежегодного роста тарифов на 8 % срок окупаемости составляет около 9 лет."),
                    P("Полученный результат существенно меньше нормативного срока эксплуатации фасадной теплоизоляции "
                      "(не менее 25 лет), поэтому мероприятия можно считать экономически оправданными. Кроме того, "
                      "после ремонта улучшился микроклимат: средняя температура в классах в январе 2025 г. составила 21,3 °C "
                      "против 18,6 °C годом ранее, а количество жалоб на холод сократилось."),
                ]),
                eqs[4],
                photo("f3", ["school-building", "classroom"], ["school"],
                      {"school-building": "Рис. 3. Здание школы № 47 после термомодернизации (фото авторов, май 2025 г.)",
                       "classroom": "Рис. 3. Учебный класс после ремонта (фото авторов)"},
                      "Рис. 3. Объект исследования после ремонта", "none", width="70%", width_cm=12.0),
                columns([
                    H(2, "Заключение"),
                    P("1. Комплексная термомодернизация типового здания школы позволила повысить приведённое сопротивление "
                      "теплопередаче наружных стен в 3,2 раза и снизить расчётные трансмиссионные теплопотери на "
                      f"{saving / before_total * 100:.0f} %."),
                    P("2. Фактическое приведённое снижение потребления тепловой энергии (33,6 %) хорошо согласуется "
                      "с расчётом, что подтверждает применимость методики [1, 3] для оценки подобных проектов."),
                    P("3. После утепления стен и кровли основным резервом энергосбережения являются окна и система вентиляции."),
                ]),
            ],
            [
                H(2, "Список литературы"),
                L(refs, ordered=True),
                P("**Сведения об авторах:** Сафин Рустем Гаязович — канд. техн. наук, доцент, e-mail: safin@kasi.example; "
                  "Мухаметзянова Лилия Рашитовна — аспирант; Ершов Алексей Викторович — главный инженер ООО «Теплоаудит-Поволжье».", "small"),
                P("Статья поступила в редакцию 14.11.2025; одобрена после рецензирования 19.12.2025; принята к публикации 15.01.2026.", "small"),
                box("footnote", "¹ Расчёт выполнен для условий г. Казани по СП 131.13330.2020; значения округлены до 0,1 МВт·ч."),
            ],
        ],
        "arithmetic": [{"kind": "column_sum", "table": "t2", "columns": [4, 5], "label_column": 0, "total_label": "Итого"}],
    }



# ====================================================================== slide decks


def slides_en() -> dict[str, Any]:
    """Transit-agency steering committee deck (Chromium, 16:9)."""
    lines = [("Validators and on-board hardware", 4_850, 4_412, 4_790), ("Back-office account system", 3_200, 2_118, 3_340),
             ("Retail network and vending machines", 1_450, 906, 1_420), ("Mobile app and open payments", 1_100, 774, 1_180),
             ("Customer outreach and training", 620, 395, 655), ("Program management and contingency", 1_280, 811, 1_115)]
    k = lambda v: f"${number(v, 'en', 0)}K"  # noqa: E731
    budget = [[n, k(b), k(sp), k(f), ("+" if f > b else "−" if f < b else "") + k(abs(f - b)) if f != b else "$0K"] for n, b, sp, f in lines]
    tb, ts, tf = (sum(x[i] for x in lines) for i in (1, 2, 3))
    budget.append(["Total", k(tb), k(ts), k(tf), ("+" if tf > tb else "−") + k(abs(tf - tb))])
    t1 = table("t1", [["Work package", "Budget", "Spent to date", "Forecast at completion", "Variance"], *budget],
               caption="Capital budget status, as of September 30, 2026 (thousands of USD)", align=["l", "r", "r", "r", "r"],
               widths=[40, 14, 15, 17, 14], total_rows=[len(budget)])
    weeks = ["Jul 6", "Jul 20", "Aug 3", "Aug 17", "Aug 31", "Sep 14", "Sep 28"]
    ride_spec = {"title": "Weekly boardings paid by card tap (thousands)", "categories": weeks,
                 "series": [("Contactless bank card", [38, 51, 66, 84, 97, 118, 131]), ("Harbor Card (stored value)", [212, 208, 214, 205, 201, 197, 192]),
                            ("Mobile wallet", [22, 29, 37, 45, 52, 60, 68])],
                 "max": 250, "ticks": 5, "tick_format": lambda v: f"{v:.0f}"}
    uptime_spec = {"title": "Validator availability by garage, September (%)", "categories": ["Northgate", "Pier 9", "Eastlake", "South Yard", "Rail stations"],
                   "series": [("Target", [99.0] * 5), ("Actual", [99.4, 98.1, 99.2, 97.6, 99.7])],
                   "max": 100, "ticks": 5, "tick_format": lambda v: f"{v:.0f}", "colors": ["#c5ccd6", "#1f5f8b"]}
    dash = {"brand": "HTA Fare Ops", "nav": ["Overview", "Devices", "Transactions", "Incidents", "Reports"],
            "title": "Network overview — all modes", "range": "Sep 1 – Sep 30, 2026",
            "kpis": [("Taps processed", "4.92M", "+11.8%"), ("Open-payment share", "26.4%", "+4.1 pts"), ("Device uptime", "98.9%", "+0.3 pts"),
                     ("Declined taps", "0.71%", "−0.12 pts")],
            "series": [148, 152, 160, 158, 171, 166, 175, 181, 178, 186, 190, 188, 197, 201, 199],
            "series_title": "Daily taps (thousands)",
            "rows": [["Route", "Taps", "Open payments", "Declines", "Uptime"], ["7 Harbor Loop", "412,880", "31.2%", "0.64%", "99.1%"],
                     ["15 Eastlake Express", "298,145", "28.7%", "0.58%", "99.5%"], ["Blue Line (rail)", "1,104,302", "24.9%", "0.77%", "99.8%"]],
            "table_title": "Top routes by volume", "height": 480}
    risks = table("t2", [["Risk", "Likelihood", "Impact", "Mitigation", "Owner"],
                         ["Pier 9 cellular dead zones delay real-time transactions", "High", "Medium", "Private LTE pilot; offline whitelist refresh every 15 min", "J. Okonkwo"],
                         ["Retail partner exits the network (QuickStop, 41 outlets)", "Medium", "High", "Two replacement chains in negotiation; extend TVM coverage", "M. Ferreira"],
                         ["Card-scheme certification slips past December", "Medium", "High", "Weekly calls with acquirer; test plan frozen Oct 20", "D. Whitlock"],
                         ["Low adoption among riders aged 65+", "Medium", "Medium", "Senior centre sessions; reduced-fare card auto-migration", "A. Nguyễn"]],
                  rendering="borderless", align=["l", "c", "c", "l", "l"], widths=[31, 11, 9, 35, 14])
    return {
        "template": "slide_deck", "page_size": "slide", "languages": ["en-US", "es", "zh-CN", "vi"],
        "metadata": _meta("Fare Modernization Program — Steering Committee Update Q3 2026", "Dana Whitlock, Harborview Transit Authority",
                          "Quarterly program status, budget and risks", ["fare collection", "open payments", "steering committee", "transit"],
                          "en-US", "2026-10-12T21:05:00Z"),
        "theme": {"accent": "#1f5f8b", "font_size": "11pt", "body_font": "'Noto Sans'",
                  "extra_css": "section.pg{font-size:1.2em}h1{margin-top:0}li{margin-bottom:.2em!important}.kicker{font-size:.7em}.big{font-size:1.25em;color:#333}"
                               ".huge{font-size:2.1em;color:var(--accent);line-height:1.15}figure{break-inside:avoid}figcaption{font-size:.6em}"
                               "table.t{font-size:.72em}.callout{font-size:.85em}ul,ol{font-size:.95em}li li{font-size:.9em}"
                               ".small{font-size:.65em}.split{align-items:flex-start}"},
        "running_footer": "Harborview Transit Authority  ·  Fare Modernization Program  ·  Steering Committee, October 14, 2026  ·  {page}",
        "pages": [
            [
                group([
                    group([P("Harborview Transit Authority", "kicker"),
                           P("Fare Modernization Program", "huge"),
                           P("Steering Committee update — Q3 2026", "big"),
                           P("Dana Whitlock, Program Director\nOctober 14, 2026 · Board Room, 600 Pier Street", "muted"),
                           P("For internal discussion. Figures are preliminary until the Q3 close on October 24.", "small")]),
                    photo("f1", ["city-bus", "train-station"], ["transport"],
                          {"city-bus": "Route 7 Harbor Loop bus with the new front-door validator", "train-station": "Blue Line platform, Central Station"},
                          "Harborview transit vehicle", "none", width="100%"),
                ], "split"),
            ],
            [
                H(1, "Agenda"),
                L(["Where we are: program status at a glance", "Adoption: ridership by payment type",
                   "Budget and forecast at completion", "Field rollout: validators, garages and stations",
                   "Operations dashboard and device availability", "Rider feedback and accessibility",
                   "Risks and mitigations", "Decisions requested and next steps"], ordered=True),
                P("Pre-read packet sent October 9; questions received by email are answered in the appendix.", "small"),
            ],
            [
                H(1, "Program status at a glance"),
                group([
                    L([item("**Schedule — amber**", ["Bus fleet 100 % equipped (612 vehicles)", "Rail stations 34 of 38 complete; Pier 9 slips to November"], ordered=False),
                       item("**Budget — green**", ["Forecast $12.50M vs. $12.50M budget", "Contingency drawn: $165K of $480K"], ordered=False),
                       item("**Adoption — green**", ["Open payments at 26.4 % of taps, ahead of 20 % target"], ordered=False),
                       "**Certification — amber:** 212 of 240 card-scheme tests passed"]),
                    box("callout", "Overall status is **amber** because of the Pier 9 station works and the remaining card-scheme tests. "
                        "No change to the March 2027 Harbor Card retirement date is proposed.", title="Summary", cls="note"),
                ], "split"),
            ],
            [
                H(1, "Open payments are growing faster than planned"),
                group([
                    chart("f2", "line", ride_spec, "Source: HTA fare back office, weekly extract (Sunday to Saturday)", raster=False,
                          width="100%", size=(560, 300)),
                    L(["Contactless taps up **3.4×** since July launch", "Harbor Card use declining slowly (−9 %), as expected",
                       "Weekend share of open payments is 31 % — visitors and event traffic",
                       item("Fare capping working as designed", ["11,240 riders hit the daily cap of $5.00", "2,015 riders hit the weekly cap of $25.00"], ordered=False)]),
                ], "split"),
                chart_table("c2", "Week", ride_spec, lambda v: f"{v:.0f}"),
            ],
            [
                H(1, "Budget and forecast at completion"),
                t1,
                L(["Validator hardware under budget after volume rebate from Ostrava Devices s.r.o.",
                   "Back-office overrun of $140K: additional reporting module requested by Finance",
                   "Program management reduced by $165K; contingency remains available for Pier 9"]),
            ],
            [
                H(1, "Field rollout: what riders see"),
                group([
                    photo("f3", ["train-station", "city-street"], ["transport"],
                          {"train-station": "Central Station: gate-line validators went live on August 18", "city-street": "Downtown stop with new vending machine"},
                          "Station validators in service", "none", width="100%"),
                    group([L(["612 buses equipped; installation took 14 nights per garage",
                              "34 rail stations live, 4 remaining (Pier 9, Eastlake, Marina, Cannery Row)",
                              "96 new ticket vending machines accept cards, cash and phones",
                              item("Signage in four languages at every validator", ["“Tap here” · “Toque aquí” · “请在此刷卡” · “Chạm vào đây”"], ordered=False)]),
                           P("Photo: HTA Communications, September 2026", "small")]),
                ], "split"),
            ],
            [
                H(1, "Operations dashboard (live view)"),
                screenshot("f4", "dashboard", dash, "Screenshot of the fare operations console, captured October 1, 2026 at 08:15", width="78%"),
            ],
            [
                H(1, "Device availability by garage"),
                group([
                    chart("f5", "bar", uptime_spec, "Availability = minutes in service ÷ scheduled minutes", raster=True, width="100%", size=(560, 300)),
                    L(["Four of five locations meet the 99 % target",
                       item("South Yard below target (97.6 %)", ["Power supply faults on 2015-series buses", "Replacement harnesses arrive October 21"], ordered=False),
                       "Pier 9 dips caused by cellular coverage, not hardware",
                       "Mean time to repair: 3.2 h (target 4 h)"]),
                ], "split"),
                chart_table("c5", "Location", uptime_spec, lambda v: f"{v:.1f}"),
            ],
            [
                H(1, "Rider feedback and accessibility"),
                group([
                    L([item("Survey of 2,480 riders (September)", ["84 % find tapping “easy” or “very easy”", "Top complaint: unclear receipts for capped fares"], ordered=False),
                       item("Accessibility", ["Validators mounted at 1,050 mm per ADA guidance", "Audio tones tested with Harborview Council of the Blind"], ordered=False),
                       "Equity: reduced-fare riders moved automatically to virtual cards; cash top-up at 212 outlets"]),
                    box("sidebar", "“I just tap my phone now, even on the ferry. My mom still uses her Harbor Card and that’s fine too.”\n— Rider comment, Route 15", cls="wide"),
                ], "split"),
            ],
            [
                H(1, "Top risks and mitigations"),
                risks,
                P("Likelihood and impact on the program risk matrix (Low / Medium / High). Full register: SharePoint › FMP › Risk Log v23.", "small"),
            ],
            [
                H(1, "Decisions requested and next steps"),
                L([item("Decisions today", ["Approve use of $120K contingency for Pier 9 private LTE pilot", "Endorse March 1, 2027 retirement of paper transfers"], ordered=True),
                   item("Next 90 days", ["Complete the remaining four rail stations by November 30", "Finish card-scheme certification by December 12",
                                         "Launch account-based reduced fares in January"], ordered=True),
                   "Next steering committee: January 13, 2027"], ordered=True),
            ],
            [
                P("Thank you", "huge"),
                P("Questions and discussion", "big"),
                P("Dana Whitlock · Program Director, Fare Modernization\n[fmp@harborviewtransit.example](mailto:fmp@harborviewtransit.example) · +1 (206) 555-0148"),
                P("Appendix slides A1–A6 (device inventory, test results, outreach calendar) are in the pre-read packet.", "small"),
            ],
        ],
        "arithmetic": [{"kind": "column_sum", "table": "t1", "columns": [1, 2, 3], "label_column": 0, "total_label": "Total"}],
    }



def slides_ja() -> dict[str, Any]:
    """Japanese factory-DX interim report deck (LibreOffice, 16:9, stacked layout)."""
    costs = [("IoTセンサー・ゲートウェイ（42台分）", 18_600_000), ("生産管理システム（クラウド利用料・初年度）", 7_200_000),
             ("ネットワーク工事（工場内Wi-Fi・LAN）", 4_350_000), ("従業員研修・マニュアル作成", 1_980_000), ("外部コンサルティング", 3_300_000)]
    total = sum(c for _, c in costs)
    t1 = table("t1", [["項目", "費用（税抜）"], *[[n, money(c, "ja")] for n, c in costs], ["合計", money(total, "ja")]],
               align=["l", "r"], widths=[70, 30], total_rows=[len(costs) + 1], width_cm=20.0,
               caption="表1　初年度投資額（2026年度予算）")
    months = ["4月", "5月", "6月", "7月", "8月", "9月"]
    oee = {"title": "設備総合効率（OEE）の推移（%）", "categories": months,
           "series": [("第1ライン", [61.2, 63.5, 66.8, 70.1, 72.4, 74.0]), ("第2ライン", [58.4, 59.0, 60.7, 64.9, 68.2, 71.5])],
           "max": 80, "ticks": 4, "tick_format": lambda v: f"{v:.0f}"}
    sheet = {"title": "生産実績_2026年9月.xlsx", "menu": ["ファイル", "ホーム", "挿入", "数式", "データ", "表示"], "cell": "E8",
             "formula": "=SUM(E2:E7)", "tabs": ["9月実績", "8月実績", "設備マスタ"], "lang": "ja", "width": 760,
             "numeric": [False, True, True, True, True], "selected_row": 8,
             "rows": [["設備名", "計画数", "実績数", "不良数", "停止時間(分)"],
                      ["NC旋盤 TL-01", "12,400", "12,118", "37", "214"], ["NC旋盤 TL-02", "12,400", "11,962", "52", "305"],
                      ["マシニングセンタ MC-03", "8,600", "8,447", "21", "168"], ["マシニングセンタ MC-04", "8,600", "8,512", "18", "122"],
                      ["研削盤 GR-05", "6,200", "6,087", "44", "241"], ["検査装置 IN-06", "48,200", "47,126", "0", "96"],
                      ["合計", "96,400", "94,252", "172", "1,146"]]}
    return {
        "template": "slide_deck", "page_size": "slide", "languages": ["ja", "en"], "tagged": True,
        "metadata": _meta("工場DX推進プロジェクト 中間報告（2026年度上期）", "株式会社東和精機 生産技術部 DX推進室",
                          "IoTによる設備稼働の見える化と生産管理システム導入の中間報告",
                          ["工場DX", "IoT", "設備総合効率", "生産管理", "中間報告"], "ja", "2026-10-06T00:30:00Z"),
        "theme": {"accent": "#0b5a52", "lo_size": "16pt", "lo_font": "Noto Sans", "lo_heading_font": "Noto Sans", "lo_margin": "1.6cm",
                  "content_cm": 29.0},
        "running_footer": "株式会社東和精機　DX推進室　　社外秘　　{page} / {pages}",
        "pages": [
            [
                P("株式会社東和精機　生産技術部 DX推進室", "small"),
                H(1, "工場DX推進プロジェクト　中間報告"),
                P("IoTによる設備稼働の見える化と生産管理システムの導入（2026年度上期）"),
                P("2026年10月6日（火）　経営会議資料\n報告者：DX推進室 室長　高橋 美咲"),
                photo("f1", ["factory-machinery", "hand-tools"], ["industry"],
                      {"factory-machinery": "浜松第二工場　第1ライン（NC旋盤エリア）", "hand-tools": "保全チームの工具ステーション"},
                      "浜松第二工場の生産ライン", "none", width="40%", width_cm=9.0),
            ],
            [
                H(1, "本日のアジェンダ"),
                L(["プロジェクトの背景と目的", "上期の取り組み状況", "設備稼働率（OEE）の改善効果", "投資額と費用対効果",
                   "生産管理システムの運用状況", "下期の計画と経営会議へのお願い"], ordered=True),
                P("※ 数値は2026年9月30日時点の速報値です。", "small"),
            ],
            [
                H(1, "1．プロジェクトの背景と目的"),
                L([item("背景", ["熟練作業者の退職により、段取り替えや保全のノウハウが属人化", "設備の停止理由を紙の日報で管理しており、集計に月20時間以上",
                                 "主要顧客（自動車部品メーカー）からトレーサビリティ強化の要請"], ordered=False),
                   item("目的（2027年3月までのKPI）", ["設備総合効率（OEE）：60％ → 75％", "不良率：0.35％ → 0.20％以下",
                                                  "日報集計工数：ゼロ（自動化）"], ordered=False)]),
            ],
            [
                H(1, "2．設備総合効率（OEE）の改善"),
                chart("f2", "line", oee, "図1　ライン別OEEの月次推移（2026年4月〜9月）", raster=True, width="60%", width_cm=16.0, size=(620, 280)),
                chart_table("c2", "月", oee, lambda v: f"{v:.1f}"),
                L(["第1ラインは9月に74.0％を達成し、目標の75％まであと1.0ポイント",
                   "第2ラインは7月のセンサー追加設置以降、改善ペースが加速"]),
            ],
            [
                H(1, "3．投資額と費用対効果"),
                t1,
                L([f"初年度投資額は合計{money(total, 'ja')}（予算比 98.4％）",
                   "停止時間の削減による効果は年間約2,600万円と試算 → 投資回収期間は約1.4年"]),
            ],
            [
                H(1, "4．現場での取り組み"),
                photo("f3", ["factory-machinery", "hand-tools"], ["industry"],
                      {"factory-machinery": "写真：振動・電流センサーを取り付けたNC旋盤（TL-01）",
                       "hand-tools": "写真：センサー取付作業に使用した工具一式"},
                      "写真：センサーを取り付けた設備", "none", width="25%", width_cm=5.6),
                L(["42台の設備に振動・電流・温度センサーを設置（7月完了）",
                   "停止理由はタブレットで2タップ入力　→　入力率 96％"]),
            ],
            [
                H(1, "5．生産管理システムの運用状況"),
                screenshot("f4", "spreadsheet", sheet, "図2　9月の生産実績（システムからのエクスポート画面）", width="70%", width_cm=17.0),
                table("t2", sheet["rows"], rendering="screenshot", caption="図2　9月の生産実績（システムからのエクスポート画面）"),
            ],
            [
                H(1, "6．下期の計画とまとめ"),
                L([item("下期の計画", ["第3・第4ラインへの展開（センサー36台追加）", "AIによる工具摩耗の予兆検知を試験導入（12月〜）",
                                   "ERP（SAP S/4HANA）との実績データ連携"], ordered=False),
                   item("経営会議へのお願い", ["下期追加投資 2,450万円のご承認", "各工場長による月次レビューへの参加"], ordered=False)]),
                P("ご清聴ありがとうございました。ご質問・ご意見をお願いいたします。　問い合わせ：dx-suishin@towa-seiki.example（内線 4127）"),
            ],
        ],
        "arithmetic": [{"kind": "column_sum", "table": "t1", "columns": [1], "label_column": 0, "total_label": "合計"}],
    }



def slides_fr() -> dict[str, Any]:
    """French municipal school-retrofit review deck (pdfust, 16:9)."""
    schools = [("École Jules-Verne (Rezé)", "Isolation des combles, menuiseries", 41_850_000, "Terminé"),
               ("Groupe scolaire Ange-Guépin", "Pompe à chaleur, ventilation double flux", 68_320_000, "Terminé"),
               ("École maternelle Les Tilleuls", "Isolation par l’extérieur", 37_490_000, "Réception en novembre"),
               ("École Aimé-Césaire (Saint-Herblain)", "Toiture photovoltaïque 96 kWc", 21_760_000, "Terminé"),
               ("Groupe scolaire Louise-Michel", "Chaufferie bois, régulation", 54_100_000, "En cours (70 %)")]
    total = sum(x[2] for x in schools)
    t1 = table("t1", [["Établissement", "Travaux", "Montant HT", "État au 30/09"],
                      *[[a, b, money(c, "fr"), d] for a, b, c, d in schools], ["Total", "", money(total, "fr"), ""]],
               align=["l", "l", "r", "l"], widths=[31, 33, 17, 19], total_rows=[len(schools) + 1])
    conso = {"title": "Consommation d’énergie finale (kWh/m²·an)", "categories": ["Jules-Verne", "Ange-Guépin", "Les Tilleuls", "Aimé-Césaire"],
             "series": [("2023 (avant)", [182, 207, 165, 149]), ("2026 (après)", [104, 96, 121, 138])],
             "max": 250, "ticks": 5, "tick_format": lambda v: f"{v:.0f}"}
    sheet = {"title": "Suivi_budget_renovation_ecoles_2026.ods", "menu": ["Fichier", "Édition", "Affichage", "Insertion", "Format", "Données"],
             "cell": "D7", "formula": "=SOMME(D2:D6)", "tabs": ["Budget 2026", "Subventions", "Calendrier"], "lang": "fr", "width": 760,
             "numeric": [False, True, True, True], "selected_row": 7,
             "rows": [["Poste", "Budget voté", "Engagé", "Mandaté"],
                      ["Études et maîtrise d’œuvre", "1 450 000", "1 382 400", "1 120 900"], ["Travaux d’isolation", "9 800 000", "9 214 600", "7 655 300"],
                      ["Équipements de chauffage", "8 600 000", "8 102 200", "6 340 000"], ["Photovoltaïque", "2 300 000", "2 176 000", "2 176 000"],
                      ["Aléas et révisions de prix", "900 000", "412 700", "198 300"], ["Total", "23 050 000", "21 287 900", "17 490 500"]]}
    return {
        "template": "slide_deck", "page_size": "slide", "languages": ["fr-FR"],
        "metadata": _meta("Plan Écoles Basse Consommation — bilan d’étape 2026", "Direction du patrimoine bâti, Métropole Rives-de-Loire",
                          "Présentation à la commission Transition écologique du 15 octobre 2026",
                          ["rénovation énergétique", "écoles", "bilan", "commission"], "fr-FR", "2026-10-13T15:40:00Z"),
        "theme": {"accent": "#1d4f91", "py_size": 22, "py_margin": 40},
        "running_footer": "Métropole Rives-de-Loire · Commission Transition écologique · 15 octobre 2026 · {page}/{pages}",
        "pages": [
            [
                group([
                    group([P("MÉTROPOLE RIVES-DE-LOIRE", "small"),
                           H(1, "Plan Écoles Basse Consommation"),
                           P("Bilan d’étape au 30 septembre 2026", "lead"),
                           P("Commission Transition écologique\nMercredi 15 octobre 2026 — salle du Conseil"),
                           P("Présenté par Claire Morvan, directrice du patrimoine bâti, et Yannick Le Gall, chef de projet énergie", "small")]),
                    photo("f1", ["school-building", "classroom"], ["school"],
                          {"school-building": "Groupe scolaire Ange-Guépin après travaux", "classroom": "Classe rénovée, école Jules-Verne"},
                          "École rénovée", "none", width="100%"),
                ], "split"),
            ],
            [
                H(1, "Sommaire"),
                L(["Rappel du contexte et des objectifs", "Avancement des chantiers 2025–2026", "Premiers résultats énergétiques",
                   "Focus : la toiture solaire d’Aimé-Césaire", "Suivi budgétaire et subventions", "Programme 2027 et points de décision"], ordered=True),
            ],
            [
                H(1, "Contexte et objectifs"),
                L([item("Un patrimoine scolaire énergivore", ["112 écoles, 214 000 m² chauffés", "62 % construites avant 1980",
                                                           "Facture énergétique 2023 : 6,8 M€ TTC"], ordered=False),
                   item("Les objectifs du plan (2024–2030)", ["−40 % de consommation d’ici 2030 (décret tertiaire)", "Sortie du fioul dans toutes les écoles",
                                                            "Confort d’été : moins de 28 °C en classe"], ordered=False)]),
            ],
            [
                H(1, "Avancement des chantiers 2025–2026"),
                t1,
                P("Montants hors taxes, avenants inclus — extraction du 30/09/2026.", "small"),
            ],
            [
                H(1, "Premiers résultats énergétiques"),
                group([
                    chart("f2", "bar", conso, "Consommations corrigées du climat (DJU base 18 °C)", raster=True, width="100%", size=(520, 400)),
                    L(["Jules-Verne : −43 % depuis la rénovation", "Ange-Guépin : −54 %, meilleur résultat du plan",
                       "Les Tilleuls : chantier non terminé, gain partiel", "Aimé-Césaire : la production solaire n’est pas déduite ici"]),
                ], "split"),
                chart_table("c2", "École", conso, lambda v: f"{v:.0f}"),
            ],
            [
                H(1, "Focus : toiture solaire Aimé-Césaire"),
                group([
                    photo("f3", ["solar-panels"], ["energy"], {"solar-panels": "240 modules de 400 Wc posés en juillet 2026"},
                          "Centrale solaire en toiture", "none", width="100%"),
                    L(["Puissance installée : 96 kWc", "Production attendue : 104 MWh/an",
                       item("Autoconsommation collective", ["École, gymnase et médiathèque voisins", "Taux d’autoconsommation estimé : 71 %"], ordered=False),
                       "Mise en service par Enedis le 2 septembre"]),
                ], "split"),
            ],
            [
                H(1, "Suivi budgétaire"),
                group([
                    screenshot("f4", "spreadsheet", sheet, "Tableau de suivi de la direction des finances (capture du 1er octobre)", width="100%"),
                    L(["92 % du budget 2026 engagé", "Subventions notifiées : 6,4 M€ (DSIL, Fonds vert, Région)",
                       "Aléas peu mobilisés : 412 700 € sur 900 000 €"]),
                ], "split"),
                table("t2", sheet["rows"], rendering="screenshot", caption="Tableau de suivi de la direction des finances (capture du 1er octobre)"),
            ],
            [
                H(1, "Programme 2027 et décisions"),
                L([item("Programme 2027 (sous réserve du vote du budget)", ["Huit écoles supplémentaires, dont trois chauffées au fioul",
                                                                          "Végétalisation de quatre cours d’école", "Généralisation des capteurs de CO₂ et de température"], ordered=True),
                   item("Décisions attendues de la commission", ["Avis sur l’enveloppe 2027 de 18,5 M€", "Validation du recours à un contrat de performance énergétique"], ordered=True)],
                  ordered=True),
            ],
            [
                H(1, "Merci de votre attention"),
                P("Questions et échanges", "lead"),
                P("Contact : Claire Morvan, direction du patrimoine bâti\npatrimoine.ecoles@rives-de-loire.example — 02 40 55 01 27"),
                P("Documents complémentaires : fiches chantier, rapport de l’AMO énergie et bilan des subventions, disponibles sur l’espace élus.", "small"),
            ],
        ],
        "arithmetic": [{"kind": "column_sum", "table": "t1", "columns": [2], "label_column": 0, "total_label": "Total"}],
    }



def slides_es() -> dict[str, Any]:
    """Spanish farm-cooperative harvest results deck (ReportLab, 16:9, Standard 14 fonts)."""
    crops = [("Trigo blando", 4_120, 17_304), ("Cebada de dos carreras", 3_480, 14_964), ("Maíz de regadío", 1_250, 15_000),
             ("Colza", 610, 1_952), ("Girasol", 940, 2_068), ("Guisante proteaginoso", 380, 950)]
    ha_total = sum(c[1] for c in crops)
    t_total = sum(c[2] for c in crops)
    rows = [[n, number(h, "es", 0), number(t, "es", 0), number(t / h, "es", 2)] for n, h, t in crops]
    rows.append(["Total", number(ha_total, "es", 0), number(t_total, "es", 0), number(t_total / ha_total, "es", 2)])
    t1 = table("t1", [["Cultivo", "Superficie (ha)", "Producción (t)", "Rendimiento (t/ha)"], *rows],
               align=["l", "r", "r", "r"], widths=[40, 20, 20, 20], total_rows=[len(rows)])
    price = {"title": "Precio medio liquidado (EUR/t)", "categories": ["Trigo", "Cebada", "Maíz", "Colza", "Girasol"],
             "series": [("Campaña 2025", [228, 205, 219, 452, 418]), ("Campaña 2026", [241, 212, 226, 471, 436])],
             "max": 500, "ticks": 5, "tick_format": lambda v: f"{v:.0f}"}
    rain = {"title": "Precipitación mensual en Toro (mm)", "categories": ["Oct", "Nov", "Dic", "Ene", "Feb", "Mar", "Abr", "May", "Jun"],
            "series": [("2025/26", [48, 62, 39, 44, 31, 57, 49, 38, 12]), ("Media 1991-2020", [44, 49, 47, 38, 30, 29, 41, 43, 23])],
            "max": 80, "ticks": 4, "tick_format": lambda v: f"{v:.0f}"}
    return {
        "template": "slide_deck", "page_size": "slide", "languages": ["es-ES"],
        "metadata": _meta("Resultados de la campaña de cereal y oleaginosas 2026", "Consejo Rector, Cooperativa Agraria Vega del Duero",
                          "Presentación a la Asamblea General de socios", ["cooperativa", "cosecha", "cereal", "asamblea", "liquidación"],
                          "es-ES", "2026-09-28T17:00:00Z"),
        "theme": {"accent": "#7a5b12", "rl_size": 20, "rl_margin": 40},
        "running_footer": "Cooperativa Agraria Vega del Duero  ·  Asamblea General Ordinaria  ·  4 de octubre de 2026  ·  {page}",
        "pages": [
            [
                group([
                    group([P("COOPERATIVA AGRARIA VEGA DEL DUERO", "small"),
                           H(1, "Campaña 2026: resultados de cosecha y liquidación"),
                           P("Asamblea General Ordinaria de socios", "lead"),
                           P("Toro (Zamora), 4 de octubre de 2026\nPresenta: Inmaculada Pérez Garrido, gerente")]),
                    photo("f1", ["farm-field", "aerial-farmland"], ["agriculture"],
                          {"farm-field": "Parcelas de cebada en la vega, junio de 2026", "aerial-farmland": "Vista aérea de las parcelas de los socios"},
                          "Campos de los socios", "none", width="100%", width_cm=15.0),
                ], "split"),
            ],
            [
                H(1, "Orden del día"),
                L(["Resumen de la campaña agrícola 2025/26", "Producción por cultivo y rendimientos", "Precios y liquidación a los socios",
                   "Inversiones en maquinaria y secadero", "Propuestas para la campaña 2027 y ruegos y preguntas"], ordered=True),
                P("Documentación disponible en la oficina de la cooperativa desde el 20 de septiembre.", "small"),
            ],
            [
                H(1, "Resumen de la campaña"),
                group([
                    L([item("Clima favorable", ["Otoño lluvioso y buena nascencia", "Marzo muy húmedo: 57 mm", "Junio seco, cosecha sin interrupciones"], ordered=False),
                       item("Producción récord", [f"{number(t_total, 'es', 0)} t entregadas", "+14 % respecto a 2025"], ordered=False),
                       "212 socios activos, 7 altas nuevas"]),
                    chart("f2", "line", rain, "Fuente: estación agroclimática de Toro", raster=True, width="100%", width_cm=15.0, size=(520, 340)),
                ], "split"),
                chart_table("c2", "Mes", rain, lambda v: f"{v:.0f}"),
            ],
            [
                H(1, "Producción por cultivo"),
                t1,
                P("Datos de báscula de los almacenes de Toro y Morales de Toro, cerrados a 15 de septiembre de 2026. "
                  "El maíz incluye la estimación de las parcelas pendientes de cosechar.", "small"),
            ],
            [
                H(1, "Precios y liquidación"),
                group([
                    chart("f3", "bar", price, "Precios medios ponderados, sin IVA", raster=False, width="100%", width_cm=15.0, size=(520, 380)),
                    L(["Subida media del 5 % sobre 2025", "Contrato con harinera de Valladolid: prima de 9 EUR/t por proteína",
                       "Anticipo pagado en julio: 60 % del valor", "Liquidación final: 15 de noviembre"]),
                ], "split"),
                chart_table("c3", "Cultivo", price, lambda v: f"{v:.0f}"),
            ],
            [
                H(1, "Inversiones en maquinaria y secadero"),
                group([
                    photo("f4", ["tractor", "factory-machinery"], ["agriculture", "machinery"],
                          {"tractor": "Nuevo tractor de 180 CV del parque de maquinaria común", "factory-machinery": "Línea de limpieza del secadero"},
                          "Maquinaria de la cooperativa", "none", width="100%", width_cm=15.0),
                    L(["Tractor de 180 CV y sembradora de siembra directa: 248.000 EUR",
                       "Ampliación del secadero de maíz: +40 t/h",
                       item("Subvenciones", ["Plan de modernización de la Junta: 35 %", "Resolución prevista en diciembre"], ordered=False)]),
                ], "split"),
            ],
            [
                H(1, "Campaña 2027 y ruegos y preguntas"),
                L([item("Propuestas a votación", ["Ampliar la superficie de guisante y veza para cumplir la rotación de la PAC",
                                                   "Seguro colectivo de pedrisco con Agroseguro"], ordered=True),
                   "Jornada técnica sobre agricultura de precisión: 12 de noviembre",
                   "Turno de ruegos y preguntas"], ordered=True),
                P("Gracias por vuestra asistencia. Contacto: socios@vegadelduero.example - 980 555 214", "lead"),
            ],
        ],
        "arithmetic": [{"kind": "column_sum", "table": "t1", "columns": [1, 2], "label_column": 0, "total_label": "Total"}],
    }



# ====================================================================== technical manuals


def manual_en() -> dict[str, Any]:
    """Industrial edge-gateway installation and operation manual (Chromium, Letter, 15 pages)."""
    spec_rows = [
        ["Processor", "NXP i.MX 8M Plus, 4 × Cortex-A53 @ 1.6 GHz, NPU 2.3 TOPS"], ["Memory", "4 GB LPDDR4, 32 GB eMMC (pSLC mode 10 GB)"],
        ["Storage expansion", "1 × microSD (SDXC, up to 512 GB), industrial grade recommended"],
        ["Ethernet", "2 × 10/100/1000BASE-T (RJ45), independent MACs; ETH1 supports PoE PD (802.3at)"],
        ["Serial", "2 × RS-485 (isolated, 1.5 kV), 1 × RS-232 / RS-485 selectable"], ["Fieldbus", "Modbus RTU/TCP, OPC UA client and server, MQTT 3.1.1/5.0"],
        ["Digital inputs", "8 × 24 V DC, sink/source, 2 kHz counter on DI1–DI2"], ["Digital outputs", "4 × solid-state relay, 0.5 A @ 30 V DC"],
        ["Analog inputs", "4 × 0–10 V / 4–20 mA, 16-bit, ±0.1 % FS"], ["Wireless (KX-400-LW)", "LTE Cat-4 (bands 2/4/5/12/13/66/71), Wi-Fi 5, BLE 5.0"],
        ["USB", "1 × USB 3.0 host, 1 × USB-C service port"], ["Real-time clock", "Supercapacitor backup, 7 days; NTP / PTP (IEEE 1588) sync"],
        ["Supply voltage", "12–48 V DC (redundant inputs PWR1/PWR2), reverse-polarity protected"],
        ["Power consumption", "6.8 W typical, 11.5 W maximum (without PoE output)"],
        ["Operating temperature", "−40 °C to +70 °C (−40 °F to +158 °F)"], ["Storage temperature", "−40 °C to +85 °C"],
        ["Relative humidity", "5–95 %, non-condensing"], ["Shock / vibration", "IEC 60068-2-27 (50 g) / IEC 60068-2-6 (5 g, 10–500 Hz)"],
        ["Ingress protection", "IP40 (housing), IP20 (terminals)"], ["Dimensions (W × H × D)", "54 × 142 × 118 mm (2.13 × 5.59 × 4.65 in)"],
        ["Weight", "620 g (1.37 lb)"], ["Mounting", "35 mm DIN rail (EN 60715) or wall bracket KX-WB1"],
        ["MTBF", "412,000 h (Telcordia SR-332, 40 °C)"], ["Certifications", "UL 61010-2-201, CE, FCC Part 15 B, IECEx/ATEX Zone 2 (option -EX)"],
    ]
    spec = continued("t3", [["Parameter", "Specification"]], spec_rows, [14, 10], caption="Table 3. Technical specifications (KX-400 and KX-400-LW)",
                     continued_caption="Table 3. Technical specifications (continued)", widths=[28, 72])
    parts = [["1", "KX-400 gateway", "KX-400-00", "1"], ["2", "Pluggable terminal block, 3-pin power (端子台 TB-2)", "KX-TB2-P", "2"],
             ["3", "Pluggable terminal block, 10-pin I/O", "KX-TB10-IO", "2"], ["4", "LTE antenna, SMA, 3 dBi (KX-400-LW only)", "KX-ANT-L3", "2"],
             ["5", "Wi-Fi/BLE antenna, RP-SMA, 2 dBi", "KX-ANT-W2", "1"], ["6", "Quick start guide (EN/ES/FR/日本語)", "KX400-QSG", "1"],
             ["7", "Grounding screw M4 × 8 with lock washer", "HW-M4-8", "1"]]
    t1 = table("t1", [["Item", "Description", "Part number", "Qty"], *parts], caption="Table 1. Package contents",
               align=["c", "l", "l", "r"], widths=[8, 60, 20, 12])
    revs = table("t0", [["Rev.", "Date", "Changes"], ["A", "2025-11-03", "First release"], ["B", "2026-02-17", "Added KX-400-LW cellular variant; corrected DI wiring diagram"],
                        ["C", "2026-07-08", "Firmware 3.2: OPC UA server, container runtime, new web UI screens"]],
                 rendering="borderless", caption="Revision history", widths=[8, 18, 74])
    term = table("t2", [["Terminal", "Signal", "Description", "Wire size"],
                        ["PWR1 +/−", "12–48 V DC", "Primary supply", "0.5–2.5 mm² (AWG 20–14)"],
                        ["PWR2 +/−", "12–48 V DC", "Redundant supply (optional)", "0.5–2.5 mm² (AWG 20–14)"],
                        ["FG", "Functional ground", "Connect to cabinet ground bar", "≥ 1.5 mm² (AWG 16)"],
                        ["DI1–DI8, COM", "24 V DC inputs", "Common selectable sink/source", "0.2–1.5 mm² (AWG 24–16)"],
                        ["DO1–DO4", "SSR outputs", "0.5 A max. per channel", "0.2–1.5 mm² (AWG 24–16)"],
                        ["AI1–AI4, AGND", "0–10 V / 4–20 mA", "Mode set in web UI or CLI", "Shielded twisted pair"],
                        ["A1/B1, A2/B2", "RS-485", "120 Ω termination switchable", "Shielded twisted pair"]],
                 caption="Table 2. Terminal assignment", widths=[16, 18, 38, 28])
    trouble = table("t4", [["Symptom / LED", "Possible cause", "Remedy"],
                           ["PWR LED off", "No supply voltage or reversed polarity", "Measure 12–48 V DC at PWR1; check fuse F1 in cabinet"],
                           ["SYS LED blinking red (2 Hz)", "Boot failure, corrupted firmware image", "Hold RESET 15 s to boot recovery partition; reflash (section 8.2)"],
                           ["SYS LED amber", "Storage above 90 % or temperature above 75 °C", "Clear logs (kx-cli logs purge); improve cabinet ventilation"],
                           ["ETH link LED off", "Cable or switch port fault", "Replace cable; verify port speed is not forced to 10 Mb/s half duplex"],
                           ["Modbus timeouts (code 0x0B)", "Wrong baud rate, missing termination", "Match 19,200 8E1 on all devices; enable 120 Ω at both bus ends"],
                           ["MQTT broker refuses connection", "Expired client certificate", "Upload new certificate under Settings › Security › Certificates"],
                           ["Web UI not reachable", "IP conflict or browser cache", "Use service port 192.168.250.1; clear cache; check ip addr"],
                           ["LTE LED off (-LW)", "SIM not detected or APN wrong", "Reseat SIM; set APN in Network › Cellular; check signal ≥ −100 dBm"]],
                    caption="Table 4. Troubleshooting", rendering="borderless", widths=[26, 32, 42])
    regs = table("t5", [["Address", "Name", "Type", "Unit", "Access"],
                        ["30001", "Supply voltage PWR1", "UINT16", "0.01 V", "R"], ["30002", "Supply voltage PWR2", "UINT16", "0.01 V", "R"],
                        ["30003", "Internal temperature", "INT16", "0.1 °C", "R"], ["30010–30017", "Digital inputs DI1–DI8", "BOOL ×8", "—", "R"],
                        ["30020–30027", "Analog inputs AI1–AI4", "FLOAT32 ×4", "V or mA", "R"], ["30040", "DI1 pulse counter", "UINT32", "pulses", "R"],
                        ["40001–40004", "Digital outputs DO1–DO4", "BOOL ×4", "—", "R/W"], ["40010", "Watchdog timeout", "UINT16", "s", "R/W"],
                        ["40020", "Reset DI1 counter", "UINT16 (write 0xA5A5)", "—", "W"]],
                 caption="Table 5. Modbus TCP register map (unit ID 1)", widths=[18, 34, 22, 14, 12])
    dash = {"brand": "Kestrel EdgeView", "nav": ["Dashboard", "I/O", "Fieldbus", "Pipelines", "Containers", "System"],
            "title": "KX-400 · line3-gw01", "range": "Last 24 hours",
            "kpis": [("CPU load", "23 %", "+4 %"), ("Messages/min", "1,842", "+6.2 %"), ("Uptime", "41 d 07 h", "+1 d"), ("Errors", "2", "−5")],
            "series": [21, 22, 25, 24, 23, 27, 31, 29, 26, 24, 22, 23, 25, 24, 23],
            "series_title": "CPU load (%)",
            "rows": [["Pipeline", "Source", "Destination", "Rate", "Status"], ["press-line-3", "Modbus TCP 10.20.3.41", "MQTT plant/line3", "1 s", "Running"],
                     ["energy-meters", "Modbus RTU (bus 1)", "OPC UA server", "5 s", "Running"], ["vibration-ai", "AI1–AI2", "Container: vib-model", "100 ms", "Warning"]],
            "table_title": "Active data pipelines", "height": 470}
    return {
        "template": "technical_manual", "page_size": "Letter", "languages": ["en-US", "ja", "es", "fr"],
        "metadata": _meta("Kestrel KX-400 Industrial Edge Gateway — Installation and Operation Manual", "Kestrel Automation Inc., Technical Publications",
                          "Installation, configuration, maintenance and troubleshooting of the KX-400 and KX-400-LW",
                          ["edge gateway", "Modbus", "OPC UA", "MQTT", "installation manual", "KX-400"], "en-US", "2026-07-08T13:00:00Z"),
        "theme": {"accent": "#a14b0a", "font_size": "10.5pt", "body_font": "'Noto Sans'", "margins": "18mm 18mm 18mm 18mm",
                  "extra_css": "pre.code{font-size:.8em}figure{break-inside:avoid}.cover{font-size:3em;color:var(--accent);font-weight:700;line-height:1.1;margin:.3em 0}"},
        "running_header": "Kestrel KX-400 Industrial Edge Gateway · Installation and Operation Manual · Rev. C",
        "running_footer": "Doc. KX400-IOM-EN-C · Page {page} of {pages}",
        "pages": [
            [
                P("KESTREL AUTOMATION", "kicker"),
                P("KX-400 Industrial Edge Gateway", "cover"),
                P("Installation and Operation Manual · Models KX-400, KX-400-LW, KX-400-EX · Firmware 3.2", "lead"),
                photo("f1", ["factory-machinery", "hand-tools"], ["industry"],
                      {"factory-machinery": "KX-400 gateways collect data from presses, CNC machines and energy meters on the shop floor.",
                       "hand-tools": "Installation requires only standard cabinet tools."},
                      "Typical installation environment.", "none", width="100%"),
                revs,
                P("© 2026 Kestrel Automation Inc., 4180 Commerce Parkway, Dayton, OH 45414, USA. All rights reserved. "
                  "Kestrel and EdgeView are trademarks of Kestrel Automation Inc. Specifications are subject to change without notice.", "small"),
            ],
            [
                H(2, "Contents"),
                L(["Safety information", "Product overview", "Technical specifications", item("Installation", ["Mounting", "Wiring", "First power-up"]), "Network configuration",
                   "Web interface", "Data pipelines and integrations", item("Maintenance", ["Routine checks", "Firmware update"]),
                   "Troubleshooting", "Support, warranty and regulatory information", "Appendix A: Modbus register map"], ordered=True),
                H(2, "About this manual"),
                P("This manual is intended for control-system integrators, electricians and IT/OT administrators who install, configure "
                  "and maintain the KX-400 gateway. It assumes familiarity with industrial networks, basic Linux administration and "
                  "the safety rules for work in electrical cabinets. Read the complete manual before installing the device and keep it "
                  "available for later reference. The latest version, including localized editions in Spanish, French and Japanese "
                  "(KX-400 取扱説明書), is available at [support.kestrel-automation.example/kx400](https://support.kestrel-automation.example/kx400)."),
                P("Menu paths in the web interface are shown as **Settings › Network › Ethernet**. Values in angle brackets, for "
                  "example <serial-number>, must be replaced by your own values."),
                H(3, "Symbols used in this manual"),
                box("callout", "Indicates a hazardous situation which, if not avoided, could result in death or serious injury.", title="WARNING", cls="warn"),
                box("callout", "Indicates a situation which, if not avoided, could result in damage to the device or loss of data.", title="CAUTION"),
                box("callout", "Provides additional information or a recommended practice.", title="Note", cls="note"),
            ],
            [
                H(1, "1  Safety information"),
                P("The KX-400 is an open-type device intended for installation in an enclosure that provides protection against "
                  "electric shock and fire spread. Installation and electrical connection must only be carried out by qualified "
                  "personnel in accordance with local regulations, such as NFPA 70 (National Electrical Code) in the United States or "
                  "IEC 60364 elsewhere."),
                box("callout", "Disconnect all power sources before wiring the terminals. The supply terminals may carry hazardous voltage "
                    "from adjacent equipment even when the gateway itself is switched off.", title="WARNING — Electric shock", cls="warn"),
                box("callout", "KX-400-EX units installed in Class I, Division 2 or ATEX Zone 2 hazardous locations must not be "
                    "connected or disconnected while the circuit is live unless the area is known to be non-hazardous. Do not use the "
                    "USB service port in hazardous locations.", title="WARNING — Explosion hazard", cls="warn"),
                H(2, "1.1  Intended use"),
                P("The gateway collects data from machines, sensors and controllers, processes it locally and forwards it to "
                  "supervisory systems or cloud services. It is not a safety-rated controller. Never use the digital outputs for "
                  "functions that protect people, such as emergency stop or light-curtain circuits."),
                L(["Operate the device only within the ambient conditions listed in Table 3.", "Use a Class 2 or SELV/PELV power supply rated for at least 15 W.",
                   "Keep at least 25 mm (1 in) of free space above and below the housing for convection cooling.",
                   "Change the default password during commissioning; the device refuses remote access until you do.",
                   "Dispose of the device according to local electronic-waste rules (see section 10.3)."]),
                box("callout", "Electrostatic discharge can damage the device. Touch the grounded DIN rail before handling the "
                    "terminal blocks or the microSD card.", title="CAUTION"),
                H(2, "1.2  Cybersecurity"),
                P("Place the gateway in a dedicated OT network zone behind a firewall as described in IEC 62443-3-3. Disable unused "
                  "services, keep the firmware up to date and restrict access to the web interface to engineering workstations. "
                  "Report suspected vulnerabilities to [psirt@kestrel-automation.example](mailto:psirt@kestrel-automation.example)."),
            ],
            [
                H(1, "2  Product overview"),
                P("The KX-400 combines protocol conversion, local data processing and secure connectivity in a compact DIN-rail housing. "
                  "Data from Modbus devices, OPC UA servers and the on-board I/O is collected by **pipelines**, optionally transformed by "
                  "scripts or containerized applications and published to MQTT brokers, OPC UA clients or databases."),
                H(2, "2.1  Package contents"),
                t1,
                P("Check the contents immediately after receipt. If items are missing or damaged, contact your distributor within "
                  "seven days. Keep the packaging for returns; the device must be shipped in its original foam insert."),
                H(2, "2.2  Front panel and LEDs"),
                L(["**PWR** — green when PWR1 or PWR2 is present; amber when only one of two configured supplies is present",
                   "**SYS** — green: running; blinking green: booting; amber: warning; red: fault",
                   "**ETH1/ETH2** — link (green) and activity (flashing)", "**BUS** — flashes with Modbus RTU traffic; red on communication errors",
                   "**LTE** (-LW only) — signal strength in three steps", "**RESET** button — 3 s: reboot; 15 s: recovery mode; 30 s: factory reset"]),
                P("The serial number, MAC addresses and the default device password are printed on the label on the right side of "
                  "the housing. Note them before mounting, because the label is hidden once neighbouring devices are installed."),
            ],
            [
                H(1, "3  Technical specifications"),
                spec[0],
                box("footnote", "¹ Values at 25 °C ambient unless otherwise stated. ² LTE bands differ for the EU variant KX-400-LW-E (1/3/7/8/20/28)."),
            ],
            [
                spec[1],
                H(2, "3.1  Dimensions"),
                P("The housing is 54 mm wide, so up to three gateways fit in the space of a standard 6-module circuit-breaker "
                  "section. The terminal blocks protrude 14 mm from the front; allow an additional 40 mm for cable bending radius."),
                H(2, "3.2  Derating"),
                P("Above 55 °C ambient the maximum load on the digital outputs is reduced linearly to 0.25 A per channel at 70 °C. "
                  "When the PoE input is used together with the cellular modem, the maximum ambient temperature is limited to 60 °C."),
                H(2, "3.3  Accessories"),
                table("t7", [["Part number", "Description"], ["KX-WB1", "Wall-mounting bracket, stainless steel"],
                             ["KX-PS24-2", "DIN-rail power supply 24 V DC / 2.5 A, Class 2"], ["KX-ANT-L3-5M", "LTE antenna with 5 m cable, IP67, magnetic base"],
                             ["KX-SD64-I", "Industrial microSD card 64 GB, pSLC, −40 to +85 °C"], ["KX-TB-KIT", "Spare terminal block kit (power and I/O)"],
                             ["KX-LIC-OPCUA", "License: OPC UA server, 5,000 tags"], ["KX-LIC-CONT", "License: container runtime (2 containers)"]],
                      caption="Table 7. Accessories and licenses", widths=[25, 75], rendering="borderless"),
                P("Licenses are bound to the serial number of the gateway and are installed under **System › Licenses**. They remain valid "
                  "after firmware updates and factory resets."),
            ],
            [
                H(1, "4  Installation"),
                H(2, "4.1  Mounting on a DIN rail"),
                photo("f2", ["hand-tools", "factory-machinery"], ["tools"],
                      {"hand-tools": "Figure 1. Recommended tools: 3 mm slotted screwdriver, wire stripper, ferrule crimper and torque screwdriver.",
                       "factory-machinery": "Figure 1. Gateway position in the machine cabinet."},
                      "Figure 1. Installation tools.", "right", width="42%"),
                P("Mount the gateway vertically with the terminals facing down so that heat can escape through the ventilation slots "
                  "on the top. Horizontal mounting is permitted but reduces the maximum ambient temperature by 10 °C."),
                P("You need a 35 mm top-hat rail, a slotted screwdriver and, for the wall bracket option, two M4 screws."),
                L([item("Prepare the rail", ["Make sure the rail is connected to protective earth.", "Leave 25 mm free above and below."]),
                   item("Mount the gateway", ["Hook the upper edge of the rear clip onto the rail.", "Press the lower edge until the clip snaps in.",
                                              "Check that the device sits firmly and cannot slide sideways."]),
                   item("Ground the housing", ["Fit the M4 grounding screw with lock washer.", "Connect it to the ground bar with ≥ 1.5 mm² wire."])], ordered=True),
                P("To remove the gateway, insert a screwdriver into the slot of the rail clip, lever it downwards and tilt the device away "
                  "from the rail."),
                box("callout", "Do not mount the gateway directly above variable-frequency drives or other heat sources. Ambient "
                    "temperature is measured 25 mm below the housing.", title="Note", cls="note"),
            ],
            [
                H(2, "4.2  Wiring"),
                P("All terminals are pluggable spring-cage connectors. Use ferrules for stranded wire and strip 10 mm of insulation. "
                  "Tighten the grounding screw to 1.2 N·m (10.6 lbf·in)."),
                term,
                box("callout", "Connecting more than 30 V DC to a digital input destroys the input circuit. Inputs are not protected "
                    "against 120/230 V AC.", title="CAUTION", cls="warn"),
                H(2, "4.3  First power-up"),
                L([item("Before switching on", ["Check polarity at PWR1 with a multimeter.", "Insert the microSD card now if you use one."]),
                   item("Switch on the supply", ["PWR turns green; SYS blinks green for about 40 s.", "SYS turns steady green when the system is ready."]),
                   item("Connect a laptop", ["Use the USB-C service port or ETH2 (default 192.168.250.1/24).",
                                            "Open https://192.168.250.1 and accept the self-signed certificate."]),
                   "Log in as **admin** with the password from the label and set a new password (at least 12 characters)."], ordered=True),
                P("The setup assistant then guides you through the time zone, network and NTP settings. You can skip the assistant "
                  "and configure the device from the command line as described in the next section."),
            ],
            [
                H(1, "5  Network configuration"),
                P("ETH1 is configured for DHCP and ETH2 has the static address 192.168.250.1 by default. The ports are separate "
                  "interfaces; routing between them is disabled, so the gateway can connect a machine network to a plant network "
                  "without bridging the two."),
                code("ssh admin@192.168.250.1\nkx-cli net show\nkx-cli net set eth1 --mode static --address 10.20.3.10/24 \\\n"
                     "    --gateway 10.20.3.1 --dns 10.20.0.53,10.20.0.54\nkx-cli net apply --confirm-timeout 120", "shell",
                     caption="Listing 1. Setting a static address on ETH1 from the console"),
                P("net apply activates the new settings and rolls them back automatically after 120 s unless you confirm them with "
                  "kx-cli net confirm from the new address. This prevents a lock-out caused by a typing error."),
                P("For repeatable commissioning, the complete network configuration can also be supplied as a YAML file through the "
                  "web interface (**System › Configuration › Import**) or on a USB stick inserted at boot:"),
                code("# /etc/kestrel/network.yaml\ninterfaces:\n  eth1:\n    mode: static\n    address: 10.20.3.10/24\n    gateway: 10.20.3.1\n"
                     "    dns: [10.20.0.53, 10.20.0.54]\n  eth2:\n    mode: static\n    address: 192.168.250.1/24\n"
                     "cellular:            # KX-400-LW only\n  apn: iot.carrier.example\n  failover: true\nntp:\n"
                     "  servers: [10.20.0.10, time.nist.example]\nfirewall:\n  default: deny\n  allow:\n"
                     "    - {port: 443, from: 10.20.5.0/24}   # engineering VLAN\n    - {port: 502, from: 10.20.3.0/24}   # Modbus TCP",
                     "yaml", caption="Listing 2. Network configuration file"),
                box("callout", "The built-in firewall denies all incoming connections that are not listed. If you enable the OPC UA "
                    "server, add port 4840 to the allow list.", title="Note", cls="note"),
            ],
            [
                H(1, "6  Web interface"),
                P("The EdgeView web interface runs on the gateway and requires no installation. Supported browsers are current "
                  "versions of Chrome, Edge and Firefox. The dashboard shows the system status, the most important I/O values and "
                  "the state of all data pipelines at a glance (Figure 2)."),
                screenshot("f3", "dashboard", dash, "Figure 2. EdgeView dashboard of a gateway in operation (firmware 3.2)", width="96%"),
                L(["**Dashboard** — system health, message rates and active alarms", "**I/O** — live values, input filters and output test",
                   "**Fieldbus** — Modbus and OPC UA device configuration", "**Pipelines** — data flows from sources to destinations",
                   "**Containers** — install and monitor Docker-compatible applications", "**System** — users, certificates, firmware, backup"]),
            ],
            [
                H(1, "7  Data pipelines and integrations"),
                P("A pipeline connects one source to one or more destinations. Each pipeline has a sampling interval, optional "
                  "deadband filters and a payload template. Pipelines are stored as JSON and can be exported, version-controlled and "
                  "imported on other gateways."),
                code('{\n  "name": "press-line-3",\n  "source": {"type": "modbus-tcp", "host": "10.20.3.41", "unit": 1,\n'
                     '             "registers": [{"addr": 30001, "count": 4, "type": "float32"}]},\n'
                     '  "interval_ms": 1000,\n  "deadband": {"absolute": 0.05},\n'
                     '  "destinations": [\n    {"type": "mqtt", "broker": "mqtts://10.20.0.80:8883",\n'
                     '     "topic": "plant/line3/press/{register}", "qos": 1, "retain": false}\n  ]\n}', "json",
                     caption="Listing 3. Pipeline definition (Pipelines › Import)"),
                P("Values can also be read programmatically through the REST API. Every request needs an API token, which you create "
                  "under **System › Users › API tokens**. The following Python example reads the analog inputs once per second:"),
                code('import time\nimport requests\n\nGATEWAY = "https://10.20.3.10/api/v1"\n'
                     'HEADERS = {"Authorization": "Bearer <api-token>"}\n\n'
                     'while True:\n    r = requests.get(f"{GATEWAY}/io/analog", headers=HEADERS,\n'
                     '                     verify="/etc/ssl/kx400-ca.pem", timeout=5)\n    r.raise_for_status()\n'
                     '    for ch in r.json()["channels"]:\n        print(f\'{ch["name"]}: {ch["value"]:.3f} {ch["unit"]}\')\n    time.sleep(1)',
                     "python", caption="Listing 4. Reading analog inputs through the REST API"),
                P("The API is described in OpenAPI 3.1 format at https://<gateway>/api/v1/openapi.json. Rate limits apply: 20 requests "
                  "per second per token."),
            ],
            [
                H(1, "8  Maintenance"),
                P("The gateway contains no user-serviceable parts and needs no routine maintenance apart from the checks below. "
                  "The supercapacitor that buffers the real-time clock does not need replacement."),
                table("t6", [["Interval", "Task"], ["Monthly", "Check SYS and BUS LEDs; review the alarm log"],
                             ["Every 6 months", "Check terminal screws and cable strain relief; clean ventilation slots with dry compressed air"],
                             ["Yearly", "Install current firmware; renew TLS certificates that expire within 90 days; test backup restore"]],
                      caption="Table 6. Recommended maintenance schedule", widths=[22, 78]),
                H(2, "8.1  Backup and restore"),
                P("A backup contains the complete configuration, user accounts, certificates and pipeline definitions, but not logged "
                  "data or container images. Create a backup before every firmware update."),
                code("kx-cli backup create --encrypt --output /media/usb/kx400-$(date +%F).kxb\nkx-cli backup restore /media/usb/kx400-2026-07-01.kxb",
                     "shell", caption="Listing 5. Creating and restoring a backup"),
                H(2, "8.2  Firmware update"),
                L([item("Download and verify", ["Download the .kxfw file and its .sig signature from the support portal.",
                                               "The gateway refuses images that are not signed by Kestrel."]),
                   item("Install", ["Upload the file under **System › Firmware**, or run kx-cli fw install kx400-3.2.4.kxfw.",
                                    "The image is written to the inactive partition while the gateway keeps running."]),
                   item("Reboot and confirm", ["The gateway restarts from the new partition (about 90 s).",
                                               "If it does not boot within 5 minutes it returns to the previous version automatically."])], ordered=True),
                box("callout", "Do not interrupt the power supply while SYS is blinking amber during the partition switch.", title="CAUTION"),
            ],
            [
                H(1, "9  Troubleshooting"),
                P("Most problems can be identified from the LEDs and the system log (**System › Logs**, or kx-cli logs tail). "
                  "Table 4 lists the most common symptoms. If the problem persists, create a diagnostic package with "
                  "kx-cli support bundle and send it to technical support."),
                trouble,
                box("callout", "A factory reset (RESET held for 30 s) deletes all configuration, certificates and user accounts. "
                    "Create a backup first if the device is still reachable.", title="WARNING", cls="warn"),
            ],
            [
                H(1, "10  Support, warranty and regulatory information"),
                P(" support@kestrel-automation.example     +1 937-555-0110 (Mon–Fri, 8:00–18:00 ET)     support.kestrel-automation.example", "small icons"),
                P("Kestrel Automation warrants the KX-400 against defects in material and workmanship for 36 months from the date of "
                  "shipment. The warranty does not cover damage caused by improper installation, over-voltage, or operation outside "
                  "the specified conditions. Local partners: Kestrel Automation GmbH (Stuttgart), Kestrel Automation Japan K.K. "
                  "（ケストレル・オートメーション株式会社, 横浜市港北区新横浜 3-7-18）and Automatización Kestrel S.A. de C.V. (Monterrey)."),
                H(2, "10.1  FCC statement"),
                P("This device complies with Part 15 of the FCC Rules. Operation is subject to the following two conditions: (1) this "
                  "device may not cause harmful interference, and (2) this device must accept any interference received, including "
                  "interference that may cause undesired operation. FCC ID: 2BKXA-KX400LW."),
                H(2, "10.2  EU declaration of conformity"),
                P("Kestrel Automation Inc. declares that the KX-400 series complies with Directives 2014/30/EU (EMC), 2014/53/EU (RED, "
                  "-LW variant) and 2011/65/EU (RoHS). The full declaration is available on the support portal."),
                H(2, "10.3  Disposal"),
                P("Do not dispose of the device with household waste. In the EU, return it to a WEEE collection point; in the United "
                  "States, use the Kestrel take-back program. The device contains a lithium-free supercapacitor and no batteries."),
            ],
            [
                H(1, "Appendix A  Modbus register map"),
                P("The gateway acts as a Modbus TCP server on port 502 (unit ID 1) and exposes its own I/O and diagnostics. Register "
                  "addresses use the 5-digit convention: 3xxxx are input registers (function code 04), 4xxxx holding registers "
                  "(function codes 03, 06, 16). FLOAT32 values use big-endian word order (ABCD)."),
                regs,
                box("callout", "Writing the watchdog register (40010) enables a fail-safe mode: if no write occurs within the timeout, "
                    "all digital outputs switch off. A value of 0 disables the watchdog.", title="Note", cls="note"),
                P("Kestrel Automation Inc. · 4180 Commerce Parkway · Dayton, OH 45414 · USA · Printed in USA · Doc. KX400-IOM-EN-C", "small center"),
            ],
        ],
    }



def manual_de() -> dict[str, Any]:
    """German heat-pump operating manual (LibreOffice, tagged, 10 pages, soft hyphens)."""
    h = SHY
    spec_rows = [
        ["Heizleistung A7/W35 (Teillast)", "3,9 kW"], ["Leistungszahl COP A7/W35", "5,12"], ["Heizleistung A−7/W35 (max.)", "8,6 kW"],
        ["Leistungszahl COP A−7/W35", "2,94"], ["Heizleistung A2/W35", "6,1 kW"], ["Kühlleistung A35/W18", "7,4 kW"],
        ["Max. Vorlauftemperatur", "75 °C (bis A−10), 65 °C (bis A−20)"], ["Einsatzgrenzen Außenluft", "−25 °C bis +43 °C"],
        ["Kältemittel / Füllmenge", "R290 (Propan) / 1,15 kg, GWP 3"], ["Schallleistungspegel (ErP)", "51 dB(A); Nachtmodus 46 dB(A)"],
        ["Energieeffizienzklasse 35 °C / 55 °C", "A+++ / A++"], ["Spannungsversorgung Verdichter", "3/N/PE 400 V, 50 Hz"],
        ["Absicherung Verdichter", "C 16 A, allpolig trennend"], ["Max. Leistungsaufnahme", "3,8 kW"],
        ["Heizwasser-Mindestvolumenstrom", "1.050 l/h"], ["Restförderhöhe bei Nennvolumenstrom", "520 hPa"],
        ["Anschlüsse Heizkreis", "G 1¼ Außengewinde"], ["Abmessungen Außeneinheit (B × H × T)", "1.180 × 1.025 × 520 mm"],
        ["Gewicht Außeneinheit", "128 kg"], ["Schutzart", "IP X4"], ["Kommunikation", "Modbus TCP, EEBUS, Wi-Fi 2,4 GHz, LAN"],
        ["Smart-Grid-Schnittstelle", "SG Ready (2 Kontakte), §14a EnWG steuerbar"],
    ]
    spec = continued("t2", [["Merkmal", "Wert"]], spec_rows, [14, 8], caption="Tabelle 2: Technische Daten AquaTherm WP 9 S",
                     continued_caption="Tabelle 2: Technische Daten (Fortsetzung)", widths=[55, 45])
    clearance = table("t3", [["Seite", "Mindestabstand", "Hinweis"], ["Lufteintritt (Rückseite)", "300 mm", "zu Wänden und Hecken"],
                             ["Luftaustritt (Vorderseite)", "1.500 mm", "nicht auf Fenster oder Terrassen richten"],
                             ["Links (Wartungsseite)", "500 mm", "Zugang zum Elektro" + h + "anschluss" + h + "kasten"],
                             ["Rechts", "300 mm", "—"], ["Oben", "800 mm", "keine Überdachung tiefer als 0,8 m"]],
                      caption="Tabelle 3: Mindestabstände der Außeneinheit", widths=[32, 20, 48])
    klemmen = table("t4", [["Klemme", "Bezeichnung", "Anschluss"], ["X1: L1, L2, L3, N, PE", "Netz Verdichter", "400 V, separat abgesichert"],
                           ["X2: L, N, PE", "Netz Steuerung", "230 V, nicht über EVU-Sperre schalten"],
                           ["X3: 1/2", "EVU-Sperr" + h + "kontakt", "potenzialfrei, geöffnet = Sperre"],
                           ["X3: 3/4 und 5/6", "SG Ready (Kontakt A/B)", "potenzialfrei"], ["X4: 1/2", "Außen" + h + "temperatur" + h + "fühler", "NTC 10 kΩ"],
                           ["X4: 3/4", "Speicher" + h + "fühler Warmwasser", "NTC 10 kΩ"], ["X5", "Modbus RTU (A/B/GND)", "abgeschirmte Leitung"]],
                    caption="Tabelle 4: Klemmenbelegung im Elektroanschlusskasten", widths=[28, 34, 38])
    wartung = table("t5", [["Intervall", "Tätigkeit", "durch"], ["monatlich", "Verdampfer auf Laub und Schnee prüfen, Kondensatablauf frei halten", "Betreiber"],
                           ["jährlich", "Sichtprüfung, Heizwasserdruck, Filter im Rücklauf reinigen", "Betreiber"],
                           ["jährlich", "Dichtheitsprüfung Kältekreis (empfohlen), elektrische Anschlüsse nachziehen", "Fachbetrieb"],
                           ["alle 2 Jahre", "Heizwasser analysieren (pH 8,2–10,0, Leitfähigkeit < 100 µS/cm)", "Fachbetrieb"]],
                    caption="Tabelle 5: Wartungsplan", widths=[18, 62, 20])
    stoer = table("t6", [["Code", "Störung", "Mögliche Ursache", "Abhilfe"],
                         ["E01", "Hochdruck" + h + "störung", "Volumenstrom zu gering, Luft im Heizkreis", "Heizkreis entlüften, Schmutzfänger reinigen"],
                         ["E04", "Niederdruck" + h + "störung", "Verdampfer vereist oder verschmutzt", "Abtauung manuell starten, Lamellen reinigen"],
                         ["E11", "Fühler" + h + "fehler Außen", "Kabelbruch, Kurzschluss", "Widerstand messen (10 kΩ bei 25 °C)"],
                         ["E17", "Durchfluss" + h + "überwachung", "Umwälzpumpe blockiert", "Pumpe prüfen, ggf. Kundendienst"],
                         ["W22", "EVU-Sperre aktiv", "Sperrzeit des Netzbetreibers", "keine — Betrieb startet automatisch"],
                         ["W30", "Keine Verbindung zum Portal", "WLAN gestört, Passwort geändert", "Netzwerk neu einrichten (Abschnitt 7)"]],
                  caption="Tabelle 6: Störungsmeldungen", rendering="borderless", widths=[9, 21, 34, 36])
    return {
        "template": "technical_manual", "page_size": "A4", "languages": ["de-DE", "en"], "tagged": True,
        "metadata": _meta("Betriebs- und Installationsanleitung AquaTherm WP 9 S", "Nordhaus Wärmetechnik GmbH",
                          "Luft/Wasser-Wärmepumpe in Monoblock-Bauweise mit Kältemittel R290",
                          ["Wärmepumpe", "Betriebsanleitung", "Installationsanleitung", "R290", "Modbus"], "de-DE", "2026-03-02T08:00:00Z"),
        "theme": {"accent": "#005a8c", "lo_size": "10.5pt", "lo_font": "Noto Sans", "lo_heading_font": "Noto Sans", "lo_margin": "2.0cm"},
        "running_header": "AquaTherm WP 9 S · Betriebs- und Installationsanleitung · 83 0412 07 DE · Ausgabe 03/2026",
        "running_footer": "Seite {page} von {pages}",
        "pages": [
            [
                P("Nordhaus Wärmetechnik", "brand"),
                H(1, "Betriebs- und Installationsanleitung"),
                P("Luft/Wasser-Wärmepumpe AquaTherm WP 9 S · Monoblock-Außeneinheit mit Inneneinheit HM 9 · Kältemittel R290", "lead"),
                photo("f1", ["solar-panels", "office-building"], ["energy", "building"],
                      {"solar-panels": "Abbildung 1: Typische Anlage — Wärmepumpe mit Photovoltaik und Batteriespeicher",
                       "office-building": "Abbildung 1: Einsatz in Mehrfamilienhäusern und Bürogebäuden"},
                      "Abbildung 1: Anwendungsbeispiel", "none", width="85%", width_cm=14.5),
                H(2, "Zu dieser Anleitung"),
                P("Diese Anleitung richtet sich an Betreiber sowie an Fachhandwerkerinnen und Fachhandwerker für Heizungs" + h + "technik, "
                  "Kälte" + h + "technik und Elektro" + h + "technik. Die Kapitel 1, 6, 8 und 9 sind für den Betreiber bestimmt; alle übrigen "
                  "Arbeiten dürfen nur von einem autorisierten Fachbetrieb ausgeführt werden. Lesen Sie die Anleitung vor Beginn aller "
                  "Arbeiten vollständig durch und bewahren Sie sie in der Nähe der Inneneinheit auf."),
                P("Mitgeltende Unterlagen: Installations" + h + "anleitung Inneneinheit HM 9 (83 0413), Bedien" + h + "anleitung Regler "
                  "NWT-Control (83 0420), Planungs" + h + "handbuch Wärmepumpen (83 0001)."),
            ],
            [
                H(1, "1  Sicherheit"),
                box("callout", "Arbeiten an elektrischen Bauteilen nur durch Elektrofachkräfte. Vor Öffnen der Verkleidung die Anlage "
                    "allpolig vom Netz trennen und gegen Wiedereinschalten sichern. Die Kondensatoren des Inverters können bis zu "
                    "5 Minuten nach dem Abschalten gefährliche Spannung führen.", title="GEFAHR — Lebensgefahr durch Stromschlag", cls="warn"),
                box("callout", "Die Außeneinheit enthält 1,15 kg des brennbaren Kältemittels R290 (Propan, Sicherheitsgruppe A3). Im "
                    "Schutzbereich von 1 m um die Außeneinheit dürfen sich keine Zündquellen, Kellerschächte, Lichtschächte oder "
                    "Bodenabläufe befinden. Arbeiten am Kältekreis nur durch zertifiziertes Personal (Kategorie I nach "
                    "Verordnung (EU) 2024/573).", title="WARNUNG — Brennbares Kältemittel", cls="warn"),
                H(2, "1.1  Bestimmungsgemäße Verwendung"),
                P("Die Wärmepumpe ist ausschließlich zur Erwärmung und Kühlung von Heizwasser in geschlossenen Warmwasser" + h + "heizungs" + h + "anlagen "
                  "nach EN 12828 sowie zur Trinkwasser" + h + "erwärmung über einen geeigneten Speicher bestimmt. Jede andere Verwendung gilt "
                  "als nicht bestimmungsgemäß. Für hieraus resultierende Schäden haftet der Hersteller nicht."),
                L(["Betrieb nur mit aufbereitetem Heizwasser nach VDI 2035", "keine Verwendung in Schwimmbädern ohne Systemtrennung",
                   "keine Änderungen an der Sicherheits" + h + "einrichtung und an der Regelungs" + h + "software",
                   "Aufstellung nur im Freien, auf tragfähigem und ebenem Untergrund"]),
                H(2, "1.2  Qualifikation des Personals"),
                P("Montage, Inbetriebnahme, Wartung und Reparatur dürfen nur von Fachbetrieben vorgenommen werden, die für Heizungs" + h + "anlagen "
                  "und Elektro" + h + "installationen zugelassen sind. Der Anschluss an das öffentliche Stromnetz ist beim zuständigen "
                  "Netzbetreiber anzumelden."),
                box("callout", "Kinder ab 8 Jahren sowie Personen mit verringerten Fähigkeiten dürfen das Gerät nur unter Aufsicht "
                    "bedienen. Reinigung und Benutzer" + h + "wartung dürfen nicht von Kindern ohne Beaufsichtigung durchgeführt werden.", title="Hinweis", cls="note"),
                H(2, "1.3  Verhalten bei Kältemittelgeruch"),
                L(["Offene Flammen löschen, nicht rauchen, keine elektrischen Schalter betätigen.", "Anlage über die Heizungs" + h + "notschalter allpolig trennen.",
                   "Bereich um die Außeneinheit räumen und Kundendienst verständigen: 0800 555 4180 (kostenfrei, 24 h)."], ordered=True),
            ],
            [
                H(1, "2  Produktbeschreibung"),
                P("Die AquaTherm WP 9 S ist eine modulierende Luft/Wasser-Wärmepumpe in Monoblock-Bauweise. Der gesamte Kältekreis "
                  "befindet sich in der Außeneinheit; zur Inneneinheit werden nur Heizwasser" + h + "leitungen verlegt. Ein drehzahl" + h + "geregelter "
                  "Rollkolben" + h + "verdichter passt die Leistung zwischen 2,4 und 8,6 kW stufenlos an den Wärmebedarf an."),
                P("Die Inneneinheit HM 9 enthält die Hocheffizienz" + h + "umwälzpumpe, das Umschaltventil für Warmwasser, einen 9-kW-"
                  "Elektro" + h + "heizstab für Spitzenlast und Notbetrieb sowie den Regler NWT-Control mit Touch-Display."),
                H(1, "3  Technische Daten"),
                spec[0],
            ],
            [
                spec[1],
                box("footnote", "¹ Messwerte nach EN 14511 bzw. EN 12102; Toleranz ±5 %. ² Bei Betrieb mit Nachtabsenkung des Verdichters."),
                H(2, "3.1  Lieferumfang"),
                L(["Außeneinheit WP 9 S mit Kondensatwanne und Schwingungs" + h + "dämpfern", "Inneneinheit HM 9 mit Regler NWT-Control",
                   "Außen" + h + "temperatur" + h + "fühler und Speicher" + h + "fühler", "2 flexible Anschluss" + h + "schläuche G 1¼, 1 m",
                   "Diese Anleitung, Inbetriebnahme" + h + "protokoll und Energie" + h + "label"]),
                H(2, "3.2  Typenschild"),
                P("Das Typenschild befindet sich auf der rechten Seitenwand der Außeneinheit. Es enthält Gerätetyp, Seriennummer, "
                  "Kältemittel" + h + "füllmenge, zulässige Betriebsdrücke (PS 31 bar) und elektrische Anschlusswerte. Geben Sie bei "
                  "Rückfragen stets die zwölfstellige Seriennummer an."),
                H(2, "3.3  Leistungs" + h + "daten bei verschiedenen Betriebs" + h + "punkten"),
                table("t8", [["Außenluft", "Vorlauf 35 °C: Leistung", "COP", "Vorlauf 55 °C: Leistung", "COP"],
                             ["−15 °C", "7,3 kW", "2,41", "6,6 kW", "1,88"], ["−7 °C", "8,6 kW", "2,94", "7,9 kW", "2,21"],
                             ["+2 °C", "6,1 kW", "4,02", "5,8 kW", "2,96"], ["+7 °C", "3,9 kW", "5,12", "3,7 kW", "3,61"],
                             ["+12 °C", "4,4 kW", "5,94", "4,1 kW", "4,27"]],
                      caption="Tabelle 2a: Heizleistung und Leistungszahl nach EN 14511", align=["l", "r", "r", "r", "r"], rendering="borderless"),
                P("Die angegebenen Werte gelten für Neugeräte mit sauberen Wärmetauschern und schließen die anteilige Leistungsaufnahme "
                  "der Umwälzpumpe ein. Die jahreszeitbedingte Raumheizungs" + h + "energieeffizienz ηs beträgt 192 % bei 35 °C und 147 % bei 55 °C."),
            ],
            [
                H(1, "4  Aufstellung und Montage"),
                P("Die Außeneinheit wird auf einem frostfrei gegründeten Betonfundament oder auf der Wandkonsole WK 2 aufgestellt. "
                  "Wählen Sie den Aufstellort so, dass der Luftaustritt nicht auf Nachbar" + h + "grundstücke gerichtet ist; "
                  "die Immissions" + h + "richtwerte der TA Lärm (nachts 35 dB(A) in reinen Wohngebieten) sind einzuhalten."),
                clearance,
                photo("f2", ["hand-tools", "factory-machinery"], ["tools"],
                      {"hand-tools": "Abbildung 2: Benötigtes Werkzeug — Wasserwaage, Drehmomentschlüssel, Abisolierzange",
                       "factory-machinery": "Abbildung 2: Vormontage im Werk"},
                      "Abbildung 2: Werkzeug für die Montage", "right", width="40%", width_cm=6.0),
                L([item("Fundament vorbereiten", ["Streifenfundamente 300 mm breit, 800 mm tief (frostfrei).", "Kondensat in ein Kiesbett oder frostfrei in die Kanalisation ableiten."]),
                   item("Außeneinheit aufstellen", ["Mit Hubwagen oder 4 Personen transportieren (128 kg).", "Gerät waagerecht ausrichten, Gefälle max. 1 %.",
                                                    "Schwingungs" + h + "dämpfer mit 25 N·m befestigen."]),
                   item("Hydraulik anschließen", ["Anschluss" + h + "schläuche spannungsfrei montieren.", "Absperr" + h + "hähne und Schmutzfänger im Rücklauf vorsehen."])], ordered=True),
                box("callout", "Die Außeneinheit nicht in Senken, Mulden oder unter Balkonen aufstellen, in denen sich austretendes "
                    "Kältemittel sammeln kann.", title="WARNUNG", cls="warn"),
            ],
            [
                H(1, "5  Elektrischer Anschluss"),
                P("Verdichter und Steuerung werden über getrennte Zuleitungen versorgt. Die Steuerung muss auch während einer "
                  "EVU-Sperre mit Spannung versorgt bleiben, damit Frostschutz und Kommunikation aktiv sind. Verwenden Sie für die "
                  "Verdichter" + h + "zuleitung mindestens NYM-J 5 × 2,5 mm² und einen allstrom" + h + "sensitiven Fehlerstrom" + h + "schutz" + h + "schalter Typ B."),
                klemmen,
                box("callout", "Die Fühlerleitungen nicht parallel zu Netzleitungen verlegen; Mindestabstand 100 mm. Bei Leitungslängen über "
                    "25 m geschirmte Leitungen verwenden und den Schirm einseitig auflegen.", title="Hinweis", cls="note"),
                H(2, "5.1  Steuerbare Verbrauchs" + h + "einrichtung nach §14a EnWG"),
                P("Die Wärmepumpe kann vom Netzbetreiber über die Steuerbox oder den EVU-Kontakt auf eine Mindest" + h + "leistung von "
                  "4,2 kW gedimmt werden. Die Einstellung erfolgt im Fachhandwerker-Menü unter **Netz › §14a › Mindestleistung**."),
                H(2, "5.2  Kopplung mit Photovoltaik" + h + "anlagen"),
                P("Überschüssiger Solarstrom kann über die SG-Ready-Kontakte oder über Modbus TCP genutzt werden. Im Zustand 3 "
                  "(verstärkter Betrieb) erhöht die Regelung die Warmwasser" + h + "solltemperatur um 5 K und die Raumtemperatur um 1 K; "
                  "im Zustand 4 wird zusätzlich der Pufferspeicher auf 60 °C geladen. Die Kontakte werden üblicherweise vom "
                  "Energie" + h + "manager des Wechselrichters angesteuert."),
                L(["Mindestlaufzeit nach Freigabe: 20 Minuten", "Mindeststillstandszeit zwischen zwei Starts: 10 Minuten",
                   "Elektro" + h + "heizstab bleibt bei PV-Überschuss gesperrt, sofern nicht ausdrücklich freigegeben"]),
            ],
            [
                H(1, "6  Inbetriebnahme"),
                L([item("Heizungsanlage füllen", ["Mit aufbereitetem Wasser auf 1,5 bar füllen.", "Anlage an allen Hochpunkten entlüften."]),
                   item("Spannung zuschalten", ["Zuerst Steuerung, dann Verdichter einschalten.", "Der Assistent startet automatisch."]),
                   item("Assistent durchlaufen", ["Sprache, Datum und Uhrzeit einstellen.", "Anlagentyp und Heizkurve wählen (Fußboden: Steilheit 0,4).",
                                                  "Volumenstrom prüfen: mind. 1.050 l/h."]),
                   "Inbetriebnahme" + h + "protokoll ausfüllen und dem Betreiber übergeben."], ordered=True),
                H(1, "7  Netzwerk und Smart Home"),
                P("Der Regler lässt sich per LAN oder WLAN in das Heimnetz einbinden. Für Energie" + h + "management" + h + "systeme steht die "
                  "lokale REST-Schnittstelle zur Verfügung; die Konfiguration kann auch per Datei auf einem USB-Stick eingespielt werden:"),
                code("; nwt-control.ini  (USB-Stick, Verzeichnis /NWT)\n[netzwerk]\nmodus = lan\ndhcp = ja\nhostname = waermepumpe-keller\n\n"
                     "[modbus]\naktiv = ja\nport = 502\nunit_id = 1\nschreibzugriff = nur_lokal\n\n[portal]\naktiv = ja\nserver = portal.nordhaus-waerme.example",
                     "ini", caption="Listing 1: Konfigurationsdatei"),
                P("Aktuelle Werte können ohne Anmeldung im lokalen Netz abgefragt werden; schreibende Zugriffe erfordern ein Token aus "
                  "dem Menü **Netzwerk › API-Zugang**:"),
                code('curl -s http://waermepumpe-keller.local/api/v2/status | jq .\ncurl -s -X PUT http://waermepumpe-keller.local/api/v2/warmwasser \\\n'
                     '     -H "Authorization: Bearer <token>" \\\n     -d \'{"solltemperatur": 52, "einmal_laden": true}\'', "shell",
                     caption="Listing 2: Status abfragen und Warmwasser" + h + "ladung auslösen"),
            ],
            [
                H(2, "7.1  Modbus TCP"),
                P("Über Modbus TCP (Port 502) können übergeordnete Systeme wie Photovoltaik-Wechselrichter oder Gebäude" + h + "leittechnik "
                  "Betriebsdaten lesen und Sollwerte vorgeben. Alle Temperaturen werden als vorzeichen" + h + "behaftete Ganzzahl in 0,1 °C übertragen."),
                code("# Python 3 – Beispiel mit pymodbus 3.x\nfrom pymodbus.client import ModbusTcpClient\n\n"
                     'client = ModbusTcpClient("192.168.178.45", port=502)\nclient.connect()\n'
                     "rr = client.read_input_registers(100, count=4, slave=1)\n"
                     "aussen, vorlauf, ruecklauf, ww = [v / 10 for v in rr.registers]\n"
                     'print(f"Außen {aussen:.1f} °C, Vorlauf {vorlauf:.1f} °C, Warmwasser {ww:.1f} °C")\n'
                     "client.write_register(200, 2, slave=1)   # SG-Ready-Zustand 3 (verstärkter Betrieb)\nclient.close()",
                     "python", caption="Listing 3: Temperaturen lesen und SG-Ready-Zustand setzen"),
                table("t7", [["Register", "Inhalt", "Einheit", "Zugriff"], ["30100", "Außentemperatur", "0,1 °C", "lesen"], ["30101", "Vorlauftemperatur", "0,1 °C", "lesen"],
                             ["30102", "Rücklauftemperatur", "0,1 °C", "lesen"], ["30103", "Warmwassertemperatur", "0,1 °C", "lesen"],
                             ["30120", "Elektrische Leistungsaufnahme", "W", "lesen"], ["40200", "SG-Ready-Zustand (1–4)", "—", "lesen/schreiben"],
                             ["40210", "Sollwert Raumtemperatur", "0,1 °C", "lesen/schreiben"]],
                      caption="Tabelle 7: Auszug Modbus-Registertabelle", widths=[16, 44, 16, 24]),
                box("callout", "Schreibende Modbus-Zugriffe häufiger als einmal pro Minute verkürzen die Lebensdauer des internen "
                    "Speichers. Verwenden Sie für schnelle Regelungen ausschließlich die SG-Ready-Kontakte.", title="ACHTUNG"),
            ],
            [
                H(1, "8  Wartung und Pflege"),
                P("Eine regelmäßige Wartung sichert den effizienten Betrieb und ist Voraussetzung für die Herstellergarantie. Wir "
                  "empfehlen den Abschluss eines Wartungs" + h + "vertrags mit Ihrem Fachbetrieb."),
                wartung,
                H(1, "9  Störungsbeseitigung"),
                P("Störungen werden im Display mit Code und Klartext angezeigt und im Fehlerspeicher abgelegt. Warnungen (W) "
                  "beeinträchtigen den Betrieb nicht; bei Störungen (E) schaltet der Verdichter ab und der Heizstab übernimmt bei "
                  "Bedarf den Notbetrieb."),
                stoer,
                P("Tritt eine Störung innerhalb von 24 Stunden mehr als dreimal auf, wird die Wärmepumpe verriegelt. Eine Entriegelung "
                  "ist dann nur noch durch den Fachbetrieb möglich.", "small"),
            ],
            [
                H(1, "10  Außerbetriebnahme und Entsorgung"),
                P("Bei vorübergehender Außerbetriebnahme im Winter muss die Anlage entweder mit Spannung versorgt bleiben "
                  "(Frostschutz aktiv) oder vollständig entleert werden. Bei endgültiger Außerbetriebnahme ist das Kältemittel "
                  "durch einen zertifizierten Fachbetrieb abzusaugen und fachgerecht zu entsorgen."),
                P("Das Gerät darf nicht über den Hausmüll entsorgt werden. Nutzen Sie die Rücknahme" + h + "systeme nach dem "
                  "Elektro- und Elektronik" + h + "gerätegesetz (ElektroG). Metallteile und Kunststoffe sind gekennzeichnet und recycelbar."),
                H(1, "11  Gewährleistung und Kundendienst"),
                P("Es gelten die gesetzlichen Gewährleistungs" + h + "rechte. Darüber hinaus gewährt Nordhaus eine Herstellergarantie von "
                  "5 Jahren auf den Verdichter, sofern die Anlage von einem Fachbetrieb in Betrieb genommen und jährlich gewartet wurde."),
                L(["Kundendienst: 0800 555 4180 (kostenfrei, Mo–Fr 7–19 Uhr, Sa 8–14 Uhr)", "E-Mail: service@nordhaus-waerme.example",
                   "Ersatzteile: [shop.nordhaus-waerme.example](https://shop.nordhaus-waerme.example)", "Österreich: +43 1 555 2280 · Schweiz: +41 44 555 19 70"]),
                H(2, "EU-Konformitätserklärung"),
                P("Hiermit erklärt die Nordhaus Wärmetechnik GmbH, dass die Wärmepumpe AquaTherm WP 9 S den Richtlinien 2014/35/EU, "
                  "2014/30/EU, 2014/68/EU, 2009/125/EG und 2011/65/EU entspricht. Der vollständige Text der Konformitäts" + h + "erklärung "
                  "ist auf der Website verfügbar."),
                P("Nordhaus Wärmetechnik GmbH · Industriestraße 18 · 49377 Vechta · Deutschland · Amtsgericht Oldenburg HRB 205555", "small"),
            ],
        ],
    }



def manual_zhcn() -> dict[str, Any]:
    """Chinese data-logger user manual (pdfust, 7 pages)."""
    spec_rows = [["温度测量范围", "−40 ℃ ～ +85 ℃"], ["温度测量精度", "±0.2 ℃（0 ℃～50 ℃），其余 ±0.4 ℃"], ["温度分辨率", "0.01 ℃"],
                 ["湿度测量范围", "0 ～ 100 %RH（无凝露）"], ["湿度测量精度", "±1.5 %RH（10 %～90 %RH，25 ℃）"], ["湿度分辨率", "0.01 %RH"],
                 ["记录间隔", "10 秒 ～ 24 小时，可设置"], ["存储容量", "500,000 组数据（循环或满停）"], ["显示", "2.9 英寸电子墨水屏"],
                 ["通信接口", "USB Type-C、RS-485（Modbus RTU）、Wi-Fi 2.4 GHz、可选 4G Cat.1"],
                 ["报警方式", "屏幕提示、蜂鸣器、短信/微信推送（联网时）"], ["供电", "2 节 ER14505 锂电池（3.6 V）或 5 V USB 外接电源"],
                 ["电池寿命", "约 18 个月（记录间隔 5 分钟，每日上传 1 次）"], ["工作环境", "−40 ℃ ～ +85 ℃，0 ～ 100 %RH"],
                 ["防护等级", "IP65（探头 IP67）"], ["外形尺寸", "112 mm × 76 mm × 28 mm"], ["重量", "约 165 g（含电池）"],
                 ["认证", "CE、FCC、RoHS，符合 GSP 冷链验证要求"]]
    spec = continued("t1", [["项目", "参数"]], spec_rows, [11, 7], caption="表 1　TH-30 技术参数", continued_caption="表 1　TH-30 技术参数（续）", widths=[30, 70])
    cal = table("t3", [["项目", "周期", "方法", "执行人"], ["外观与探头检查", "每月", "目视检查外壳、线缆与探头滤帽", "使用人员"],
                       ["更换电池", "电量 < 20 % 时", "按第 8.2 节操作，注意极性", "使用人员"],
                       ["温度校准", "12 个月", "与标准铂电阻温度计比对（3 个温度点）", "计量机构"],
                       ["湿度校准", "12 个月", "饱和盐溶液法或湿度发生器", "计量机构"]],
                caption="表 3　维护与校准计划", widths=[22, 18, 42, 18])
    trouble = table("t4", [["现象", "可能原因", "处理方法"], ["屏幕无显示", "电池耗尽或接触不良", "更换电池；检查电池仓弹片"],
                           ["显示 “Err 01”", "温度探头断线", "检查探头插头；更换探头 TP-30"],
                           ["显示 “Err 05”", "存储器已满（满停模式）", "导出数据后清空记录，或改为循环记录"],
                           ["无法连接 Wi-Fi", "密码错误或使用 5 GHz 网络", "仅支持 2.4 GHz；重新运行配网"],
                           ["数据上传失败", "服务器地址或证书错误", "检查 MQTT 配置；同步设备时间"],
                           ["湿度读数偏高", "探头凝露或滤帽污染", "在干燥环境放置 2 小时；更换滤帽"]],
                    caption="表 4　常见故障及处理", rendering="borderless", widths=[24, 34, 42])
    rohs = table("t5", [["部件名称", "铅 (Pb)", "汞 (Hg)", "镉 (Cd)", "六价铬 (Cr(VI))", "多溴联苯 (PBB)", "多溴二苯醚 (PBDE)"],
                        ["外壳", "○", "○", "○", "○", "○", "○"], ["电路板组件", "×", "○", "○", "○", "○", "○"],
                        ["温湿度探头", "○", "○", "○", "○", "○", "○"], ["线缆及接插件", "×", "○", "○", "○", "○", "○"],
                        ["显示屏", "○", "○", "○", "○", "○", "○"]],
                 caption="表 5　产品中有害物质的名称及含量", align=["l", "c", "c", "c", "c", "c", "c"], widths=[22, 11, 11, 11, 15, 14, 16])
    return {
        "template": "technical_manual", "page_size": "A4", "languages": ["zh-CN", "en"],
        "metadata": _meta("TH-30 智能温湿度记录仪 用户手册", "苏州浩川仪器科技有限公司", "TH-30 系列温湿度记录仪的安装、配置、维护与故障排除",
                          ["温湿度记录仪", "用户手册", "冷链", "Modbus", "MQTT"], "zh-CN", "2026-05-20T01:30:00Z"),
        "theme": {"accent": "#0f6b5c", "py_size": 12.0, "py_margin": 54},
        "running_header": "TH-30 智能温湿度记录仪 用户手册 · 文件编号 HC-UM-TH30-CN · 版本 V2.1",
        "running_footer": "第 {page} 页 / 共 {pages} 页",
        "pages": [
            [
                P("浩川仪器 HAOCHUAN INSTRUMENTS", "brand"),
                H(1, "TH-30 智能温湿度记录仪 用户手册"),
                P("适用型号：TH-30、TH-30W（Wi-Fi）、TH-30G（4G）　　固件版本：V3.4 及以上", "lead"),
                photo("f1", ["lab-glassware", "laptop-desk"], ["lab", "office"],
                      {"lab-glassware": "图 1　TH-30 用于实验室试剂储存环境监测", "laptop-desk": "图 1　使用电脑配置记录仪"},
                      "图 1　典型应用场景", "none", width="80%"),
                H(2, "前言"),
                P("感谢您选用浩川仪器 TH-30 系列温湿度记录仪。本手册介绍产品的安装、配置、使用、维护与故障排除方法。使用前请仔细阅读本手册，"
                  "并妥善保管以备查阅。由于产品持续改进，本手册内容如有变更，恕不另行通知；最新版本请访问 www.haochuan-inst.example 下载。"),
            ],
            [
                H(2, "安全注意事项"),
                box("callout", "请勿将记录仪靠近火源或加热至 85 ℃ 以上，锂电池过热可能导致起火或爆炸。请勿对电池进行充电、拆解或短路。", title="警告", cls="warn"),
                box("callout", "在易燃易爆环境中使用前，请确认所选型号具有相应的防爆认证。标准型 TH-30 不适用于危险场所。", title="警告", cls="warn"),
                box("callout", "用于药品冷链（GSP）验证时，请确保记录仪在校准有效期内，并在使用前完成时间同步。", title="注意", cls="note"),
                H(1, "1　产品概述"),
                P("TH-30 是一款高精度、低功耗的温湿度记录仪，适用于医药冷链、仓储物流、实验室、档案馆和数据中心等场景。设备采用瑞士进口数字温湿度传感器，"
                  "可通过 USB、RS-485、Wi-Fi 或 4G 将数据上传至浩川云平台或用户自建的服务器，支持超限报警和数据防篡改（SHA-256 签名）。"),
                L(["高精度：温度 ±0.2 ℃，湿度 ±1.5 %RH，每台设备出厂均附校准证书", "长续航：标准配置下电池可使用约 18 个月",
                   "大容量：本地存储 50 万组数据，断网期间数据不丢失，恢复联网后自动补传", "合规：满足 GSP 附录《温湿度自动监测》和 21 CFR Part 11 的数据完整性要求"]),
                H(1, "2　技术参数"),
                spec[0],
            ],
            [
                spec[1],
                H(1, "3　包装清单"),
                L(["TH-30 主机 × 1（已安装电池，出厂时电池处于断开状态）", "外置探头 TP-30（线长 1.5 m）× 1（仅 TH-30-E 型）",
                   "壁挂支架及螺丝 × 1 套", "USB Type-C 数据线 × 1", "出厂校准证书 × 1、快速入门指南 × 1"]),
                H(1, "4　安装"),
                L([item("拆除电池绝缘片", ["打开背面电池仓盖（十字螺丝刀）。", "取出透明绝缘片，屏幕显示开机画面后合上仓盖。"]),
                   item("选择安装位置", ["避免阳光直射、出风口和热源附近。", "冷库内距离门口至少 1.5 m，高度建议 1.2 ～ 1.8 m。"]),
                   item("固定设备", ["用 2 颗 M4 螺丝将支架固定在墙面。", "将主机向下滑入支架卡槽，听到“咔哒”声即安装到位。"])], ordered=True),
                photo("f2", ["hand-tools", "laptop-desk"], ["tools"],
                      {"hand-tools": "图 2　安装所需工具：十字螺丝刀、电钻、膨胀螺丝", "laptop-desk": "图 2　通过电脑完成首次配置"},
                      "图 2　安装工具", "right", width="30%"),
                P("安装完成后，请等待约 15 分钟，使设备与环境达到热平衡后再开始正式记录。冷库等低温环境中，从常温移入时应等待 30 分钟以上，以免传感器凝露。"),
                P("使用外置探头时，请将探头线缆固定在支架上，探头头部应悬空放置，不得贴靠墙面或货物。"),
                H(2, "4.1　冷链运输中的使用"),
                P("用于冷藏车运输时，请将记录仪固定在货物中部，避免靠近蒸发器出风口。启运前可设置“延时启动”，到达后通过 USB 直接生成 PDF 报告。"),
            ],
            [
                H(1, "5　按键与显示"),
                L(["功能键（短按）：切换显示温度、湿度、最大值/最小值", "功能键（长按 3 秒）：开始或停止记录",
                   "设置键（长按 5 秒）：进入配网模式，Wi-Fi 指示灯快闪", "屏幕右上角图标：电池电量、信号强度、报警状态"]),
                H(1, "6　参数配置"),
                P("通过 USB 连接电脑后，设备在电脑上显示为虚拟串口（波特率 115200，8N1）。可使用 HC-Config 软件或任意串口终端发送 AT 指令进行配置："),
                code("AT+INTERVAL=300          // 记录间隔 300 秒\nAT+ALARM=T,2.0,8.0        // 温度报警上下限 2.0 ℃ ～ 8.0 ℃\n"
                     "AT+ALARM=H,35,75         // 湿度报警上下限 35 %RH ～ 75 %RH\nAT+MODE=LOOP             // 循环记录\n"
                     'AT+WIFI="Cold-Store-2F","********"\nAT+SAVE\nOK', "text", caption="代码 1　串口 AT 指令示例"),
                P("也可以将配置写入 JSON 文件，通过 HC-Config 批量下发到多台设备："),
                code('{\n  "device": "TH-30W",\n  "interval_s": 300,\n  "alarm": {"temp": [2.0, 8.0], "humi": [35, 75], "delay_s": 600},\n'
                     '  "mqtt": {\n    "host": "mqtt.haochuan-inst.example",\n    "port": 8883,\n    "topic": "coldchain/warehouse-2/{sn}",\n'
                     '    "tls": true\n  },\n  "timezone": "Asia/Shanghai"\n}', "json", caption="代码 2　设备配置文件 config.json"),
                box("callout", "报警延时（delay_s）用于避免开门取货时的短时超限误报。用于 GSP 验证时，请按照企业质量管理文件设置，不宜超过 15 分钟。", title="提示", cls="note"),
                H(2, "6.2　报警通知"),
                P("当测量值超出上下限并持续超过报警延时后，设备蜂鸣器鸣响，屏幕显示报警图标；联网型号同时向云平台发送报警消息，"
                  "云平台按照预设的通知规则发送短信、微信和电子邮件（见图 3）。报警解除后会再次发送恢复通知。"),
            ],
            [
                H(1, "7　数据读取与集成"),
                P("记录的数据可以通过 HC-Config 导出为 PDF 报告或 CSV 文件。PDF 报告包含设备序列号、校准信息、统计值和曲线图，并带有数字签名，"
                  "可直接用于药品质量追溯。"),
                H(2, "7.1　Modbus RTU"),
                P("RS-485 接口默认地址为 1，波特率 9600，8N1。保持寄存器 0x0000 为温度（有符号整数，单位 0.01 ℃），0x0001 为湿度（单位 0.01 %RH）。"
                  "以下 Python 示例每 10 秒读取一次数据："),
                code('import time\nimport minimalmodbus\n\nlogger = minimalmodbus.Instrument("/dev/ttyUSB0", 1)\nlogger.serial.baudrate = 9600\n\n'
                     "while True:\n    t = logger.read_register(0x0000, 2, signed=True)\n    h = logger.read_register(0x0001, 2)\n"
                     '    print(f"温度 {t:.2f} ℃  湿度 {h:.2f} %RH")\n    time.sleep(10)', "python", caption="代码 3　读取实时数据"),
                H(2, "7.2　MQTT 数据格式"),
                P("联网型号按设定间隔向服务器发布 JSON 消息，示例如下。时间戳为 UTC 毫秒，sig 字段为数据签名。"),
                code('{"sn": "TH30W2604A1187", "ts": 1747722600000, "t": 4.37, "h": 61.20,\n "bat": 86, "rssi": -63, "alarm": 0, "sig": "9f3c…e1a2"}', "json",
                     caption="代码 4　MQTT 消息示例"),
                P("如需对接企业已有的 WMS 或 MES 系统，可向我司技术支持索取 HTTP API 文档及 SDK（支持 Java、Python 和 C#）。"),
                screenshot("f3", "email", {"folders": ["收件箱", "报警通知", "已发送", "归档"], "subject": "【温度超限报警】2 号冷库 TH30W2604A1187",
                                           "from": "浩川云平台 <alarm@cloud.haochuan-inst.example>", "to": "冷链质量组 <qa-coldchain@yaokang.example>",
                                           "date": "2026-05-18 03:42", "lang": "zh-CN", "height": 300,
                                           "body": ["设备 TH30W2604A1187（2 号冷库 2F-B03）温度超出上限。", "当前值：8.6 ℃，上限：8.0 ℃，持续时间：12 分钟。",
                                                    "请及时检查冷库门是否关闭、制冷机组是否正常运行。", "此邮件由系统自动发送，请勿直接回复。"]},
                           "图 3　云平台发送的报警邮件示例", width="100%"),
            ],
            [
                H(1, "8　维护与校准"),
                P("为保证测量准确，请按照表 3 定期维护和校准设备。校准应由具有资质的计量机构进行，并出具校准证书。"),
                cal,
                H(2, "8.2　更换电池"),
                L(["停止记录并导出数据。", "打开电池仓，取出旧电池，按极性标识装入 2 节新电池（ER14505，3.6 V）。",
                   "合上仓盖，设备自动开机并同步时间（联网时）。", "废旧锂电池请按当地规定回收处理，不得随意丢弃。"], ordered=True),
                H(2, "8.3　校准证书与溯源"),
                P("每台记录仪出厂时均附有由本公司计量实验室出具的校准证书，测量结果可溯源至国家计量基准。用户也可委托当地计量院所进行校准，"
                  "校准后请在 HC-Config 中录入证书编号和有效期，以便在报告中自动显示。"),
                H(1, "9　故障排除"),
                trouble,
                P("如以上方法无法解决问题，请记录设备序列号和故障现象，联系售后服务。", "small"),
            ],
            [
                H(1, "10　保修与售后服务"),
                P("自购买之日起，主机保修 2 年，探头保修 1 年，电池等易耗品不在保修范围内。因不当使用、私自拆修、进水或超出规定环境使用造成的损坏不予保修。"),
                L(["售后服务热线：400-555-0371（工作日 8:30–17:30）", "技术支持邮箱：support@haochuan-inst.example",
                   "地址：江苏省苏州市工业园区星湖街 328 号创意产业园 12 栋 5 楼（邮编 215123）"]),
                H(2, "有害物质声明"),
                P("根据《电器电子产品有害物质限制使用管理办法》，本产品中有害物质的名称及含量如下表所示。"),
                rohs,
                P("○：表示该有害物质在该部件所有均质材料中的含量均在 GB/T 26572 规定的限量要求以下。\n"
                  "×：表示该有害物质至少在该部件的某一均质材料中的含量超出 GB/T 26572 规定的限量要求（符合欧盟 RoHS 豁免条款）。", "small"),
                P("环保使用期限：10 年。苏州浩川仪器科技有限公司 保留对本手册的最终解释权。", "small"),
            ],
        ],
    }



def manual_engb() -> dict[str, Any]:
    """British smart irrigation controller installation guide (ReportLab, Standard 14 fonts, 9 pages)."""
    spec_rows = [["Model", "CH-6 (6 zones), expandable to 18 zones with CH-EX6 modules"], ["Supply", "230 V AC 50 Hz via plug-in transformer, 24 V AC 1.25 A output"],
                 ["Zone outputs", "24 V AC, 0.56 A per zone, 0.84 A total including master valve"], ["Master valve / pump relay", "1 output, 24 V AC, 0.28 A"],
                 ["Sensor inputs", "2 inputs for rain, soil-moisture or flow sensors (dry contact or pulse)"], ["Flow sensor", "Pulse input up to 100 Hz, K-factor configurable"],
                 ["Wi-Fi", "802.11 b/g/n, 2.4 GHz, WPA2/WPA3"], ["Ethernet", "10/100 Mbit/s RJ45 (CH-6 Pro only)"],
                 ["Data backup", "Programmes stored in flash memory; clock backed up for 72 h"], ["Display", "2.4 in colour LCD with 5-key keypad"],
                 ["Operating temperature", "-10 to +50 °C"], ["Enclosure", "Indoor model IP20; outdoor model CH-6-O IP55, lockable"],
                 ["Dimensions", "190 × 150 × 48 mm (indoor); 240 × 210 × 95 mm (outdoor)"], ["Weight", "0.62 kg (indoor); 1.4 kg (outdoor)"],
                 ["Wire size to valves", "0.5 to 1.5 mm², max. 300 m at 1.0 mm²"], ["Standards", "BS EN 60335-2-24, UKCA, CE, RED 2014/53/EU"]]
    spec = continued("t1", [["Item", "Specification"]], spec_rows, [10, 6], caption="Table 1. Technical specification",
                     continued_caption="Table 1. Technical specification (continued)", widths=[30, 70])
    zones = table("t2", [["Zone", "Area", "Emitter", "Flow (l/min)", "Run time"], ["1", "Front lawn", "Pop-up rotors (4)", "22.0", "18 min"],
                         ["2", "Rear lawn", "Pop-up rotors (6)", "31.5", "20 min"], ["3", "Herbaceous border", "Drip line 16 mm", "6.4", "35 min"],
                         ["4", "Vegetable beds", "Micro-sprays", "11.8", "15 min"], ["5", "Greenhouse", "Drip emitters 2 l/h", "3.2", "25 min"],
                         ["6", "Patio containers", "Drip emitters 4 l/h", "2.6", "10 min"]],
                  caption="Table 2. Example zone schedule for a domestic garden", align=["c", "l", "l", "r", "r"], widths=[10, 26, 30, 17, 17])
    trouble = table("t3", [["Symptom", "Likely cause", "What to do"],
                           ["Display blank", "No mains power or faulty transformer", "Check the socket; measure 24 V AC at terminals AC1/AC2"],
                           ["Zone does not open", "Broken wire or faulty solenoid", "Measure solenoid resistance: 20 to 60 ohms is normal"],
                           ["'Short' shown on a zone", "Damaged cable or water in a joint", "Inspect valve box; remake joints with gel-filled connectors"],
                           ["Watering skipped", "Rain sensor active or weather skip", "Check sensor status on the home screen; review the app log"],
                           ["App shows 'Offline'", "Wi-Fi password changed or router too far away", "Re-run Wi-Fi set-up; fit a Wi-Fi extender"],
                           ["Unexpected high flow alarm", "Burst pipe or missing nozzle", "Close the master valve; inspect the zone shown in the alarm"]],
                    caption="Table 3. Troubleshooting", rendering="borderless", widths=[24, 34, 42])
    return {
        "template": "technical_manual", "page_size": "A4", "languages": ["en-GB"],
        "metadata": _meta("Calder CH-6 Smart Irrigation Controller - Installation and User Guide", "Calder Hydro Ltd",
                          "Installation, programming, app connection and maintenance of the CH-6 controller",
                          ["irrigation controller", "installation guide", "Wi-Fi", "garden watering", "CH-6"], "en-GB", "2026-01-26T11:00:00Z"),
        "theme": {"accent": "#2e6b30", "rl_size": 11.8, "rl_serif": False, "rl_margin": 54},
        "running_header": "Calder CH-6 Smart Irrigation Controller | Installation and User Guide | Issue 4",
        "running_footer": "CH6-IUG-EN-04  -  Page {page} of {pages}",
        "pages": [
            [
                P("CALDER HYDRO", "brand"),
                H(1, "CH-6 Smart Irrigation Controller"),
                P("Installation and User Guide for models CH-6, CH-6 Pro and CH-6-O (outdoor). Firmware 2.8 and later.", "lead"),
                photo("f1", ["garden-flowers", "park-path"], ["garden"],
                      {"garden-flowers": "Automatic watering keeps borders healthy while using up to 40% less water than a hose.",
                       "park-path": "The CH-6 is also suitable for small parks and communal grounds."},
                      "Gardens watered by the CH-6.", "none", width="100%", width_cm=15.5),
                H(2, "Before you start"),
                P("Thank you for choosing Calder. Please read this guide fully before installing the controller and keep it somewhere safe. "
                  "The installation of the controller itself is straightforward, but the wiring of valves in the garden may require "
                  "some experience with outdoor electrical work. If in doubt, ask a competent installer; a list of Calder-approved "
                  "installers is available at calderhydro.example/installers."),
            ],
            [
                H(1, "1  Safety"),
                box("callout", "The plug-in transformer must be connected to a socket protected by a 30 mA residual current device (RCD). "
                    "Do not install the indoor model outdoors or in a damp location such as an unheated garage with condensation.",
                    title="Warning", cls="warn"),
                box("callout", "Never connect mains voltage (230 V) to any terminal of the controller. The valve outputs operate at 24 V AC "
                    "only. Connecting mains voltage will destroy the controller and may cause fire.", title="Warning", cls="warn"),
                L(["This appliance can be used by children aged from 8 years and above if they have been given supervision or instruction.",
                   "Children shall not play with the appliance.", "Use only the transformer supplied (part no. CH-TX24).",
                   "Isolate the water supply before working on valves or pipework.",
                   "Fit a double check valve or an air gap to protect the drinking-water supply, as required by the Water Supply (Water Fittings) Regulations 1999."]),
                box("callout", "Some water companies restrict the use of automatic watering systems during a hosepipe ban. Drip irrigation "
                    "is often exempt. Check with your water supplier before use.", title="Note", cls="note"),
                H(1, "2  What is in the box"),
                L(["CH-6 controller with wall-mounting plate", "Plug-in transformer 230 V / 24 V AC with 2 m lead", "Fixing kit: 3 screws and wall plugs",
                   "Terminal labels and wiring diagram card", "This guide and a quick start card"]),
                P("You will also need: a 3 mm flat screwdriver, a drill with a 6 mm masonry bit, multi-core irrigation cable, "
                  "waterproof gel-filled connectors and a smartphone with the Calder Garden app (iOS 16 or Android 10 and later)."),
            ],
            [
                H(1, "3  Technical specification"),
                spec[0],
                P("The total current of all zones running at the same time must not exceed 0.84 A. Most solenoid valves draw 0.2 to 0.3 A, "
                  "so up to two zones plus the master valve can run together. The controller prevents overload by queueing zones "
                  "automatically."),
                H(2, "3.1  Compatible valves and sensors"),
                P("The CH-6 works with any normally closed 24 V AC solenoid valve. Latching (DC) valves designed for battery controllers "
                  "are not compatible. Calder valves CV-25 and CV-32 are recommended because their solenoids draw only 0.19 A."),
                L(["Rain sensors: any normally closed switch-type sensor, for example the Calder RS-1 wireless rain sensor",
                   "Soil-moisture sensors: Calder SM-2 (pulse) or third-party sensors with a dry-contact output",
                   "Flow sensors: Calder FS-20 (K-factor 3.42) or any pulse sensor up to 100 Hz",
                   "Pumps: via a 24 V AC coil relay or the Calder PSR-16 pump start relay"]),
                box("callout", "When using a flow sensor, run the Learn flow function once after installation. The controller then "
                    "records the normal flow of each zone and raises an alarm if the flow rises by more than 25%, which usually indicates "
                    "a burst pipe or a missing nozzle.", title="Tip", cls="note"),
            ],
            [
                spec[1],
                H(1, "4  Installation"),
                H(2, "4.1  Mounting the controller"),
                P("Choose a dry, frost-free location near a mains socket, for example inside a garage or utility room. The display should "
                  "be at eye level and out of direct sunlight. The outdoor model CH-6-O can be mounted on an external wall; fit it under "
                  "an overhang where possible."),
                L([item("Fix the wall plate", ["Hold the plate level and mark the three holes.", "Drill 6 mm holes, insert the wall plugs and fix the plate."]),
                   item("Hang the controller", ["Hook the controller onto the top lugs.", "Secure it with the screw underneath."]),
                   "Route the valve cable through the cable entry at the bottom and fit the cable gland."], ordered=True),
                photo("f2", ["hand-tools", "potted-plants"], ["tools"],
                      {"hand-tools": "Figure 1. Tools needed for installation.", "potted-plants": "Figure 1. Greenhouse drip zone."},
                      "Figure 1. Tools needed for installation.", "right", width="38%", width_cm=5.5),
                P("Leave a drip loop in the cable below the controller so that water running down the cable cannot enter the enclosure."),
                P("Keep the controller at least 1 m away from the router if you use Wi-Fi, but within range for a reliable connection: "
                  "the app shows signal strength during set-up and should read at least two bars."),
            ],
            [
                H(2, "4.2  Wiring the valves"),
                P("Each valve solenoid has two wires. Connect one wire of every solenoid to the common wire (C) and the other to the "
                  "zone terminal (1 to 6). Join cables in the valve box with gel-filled connectors only; ordinary terminal blocks corrode "
                  "within a season."),
                L([item("Prepare the cable", ["Strip 7 mm of insulation from each core.", "Use the colour code on the wiring card for your records."]),
                   item("Connect at the controller", ["Push each core into its spring terminal until it clicks.", "Connect the common core to terminal C."]),
                   item("Connect sensors (optional)", ["Rain sensor to S1 and COM; remove the factory jumper.", "Flow sensor to S2 and COM, observing polarity."]),
                   "Plug in the transformer and switch on. The controller starts and shows the language menu."], ordered=True),
                box("callout", "If you use a pump instead of mains pressure, connect the pump start relay to terminal MV. Never connect "
                    "the pump motor directly to the controller.", title="Note", cls="note"),
                H(2, "4.3  Example zone plan"),
                zones,
                P("Total water use for the schedule above is roughly 1,280 litres per watering day, or about 1.3 m³. At a typical "
                  "metered tariff this costs less than three pounds per day of watering.", "small"),
            ],
            [
                H(1, "5  Connecting to the app"),
                L(["Download the Calder Garden app and create an account.", "Tap Add controller and scan the QR code on the side of the CH-6.",
                   "Select your home Wi-Fi network (2.4 GHz) and enter the password.", "Name your zones and choose the soil type and plant type for each one.",
                   "Enable Weather skip so that watering is reduced after rain."], ordered=True),
                P("The CH-6 Pro also offers a local API for home-automation systems. The following commands show the controller "
                  "status and start zone 3 for 10 minutes from a computer on the same network:"),
                code("curl http://ch6-garden.local/api/status\ncurl -X POST http://ch6-garden.local/api/zones/3/run \\\n"
                     "     -H 'X-Api-Key: <your-key>' -d 'minutes=10'", "shell", caption="Listing 1. Local API commands"),
                P("Advanced users can import a complete programme as a YAML file in the app under Settings > Import:"),
                code("controller: CH-6\nseason_adjust: 100      # per cent\nrain_delay_hours: 48\nprogrammes:\n  A:\n"
                     "    start_times: ['05:30', '21:00']\n    days: [mon, wed, fri, sun]\n    zones:\n      1: 18\n      2: 20\n"
                     "  B:\n    start_times: ['06:15']\n    days: every_day\n    zones:\n      3: 35\n      5: 25\n      6: 10",
                     "yaml", caption="Listing 2. Programme file"),
            ],
            [
                H(1, "6  Programming at the controller"),
                P("You can programme the CH-6 entirely from the keypad if you prefer not to use the app. The controller has three "
                  "independent programmes (A, B and C), each with up to four start times per day. Zones within a programme run one "
                  "after another; programmes that overlap are queued."),
                L([item("Set the clock", ["Press MENU, choose Date & time, set the values with the arrow keys."]),
                   item("Create a programme", ["Choose Programmes > A > Start times.", "Set the watering days: weekdays, odd/even days or an interval.",
                                              "Set the run time for each zone; 0 min means the zone is not used."]),
                   item("Check and save", ["Press OK to save; the home screen shows the next scheduled start."])], ordered=True),
                H(2, "6.1  Seasonal adjustment"),
                P("Seasonal adjustment changes all run times by a percentage, from 10% to 200%. In spring and autumn 60 to 80% is "
                  "usually sufficient; in a heatwave you may increase it to 150%. With Weather skip enabled in the app, the controller "
                  "calculates the adjustment automatically from local evapotranspiration data supplied by the Met Office."),
                H(2, "6.2  Manual watering"),
                P("Press the zone number key and OK to start a single zone for its programmed time, or hold OK for three seconds to run "
                  "all zones in sequence. Press STOP at any time to cancel watering."),
                photo("f3", ["park-path", "garden-flowers"], ["garden"],
                      {"park-path": "Figure 2. Communal grounds watered by a CH-6 Pro with flow monitoring.",
                       "garden-flowers": "Figure 2. Border planting on a drip line zone."},
                      "Figure 2. Typical installation site.", "none", width="50%", width_cm=7.0),
            ],
            [
                H(1, "7  Maintenance"),
                L(["Spring: open the main valve, run each zone for two minutes and check every sprinkler and drip line for leaks.",
                   "Summer: clean the filter on the drip line every month; check that sprinklers are not blocked by growing plants.",
                   "Autumn: reduce seasonal adjustment; at the first frost forecast, drain the pipework or blow it out with compressed air.",
                   "Winter: switch the controller to Off but leave it powered so that the clock and firmware stay current."]),
                box("callout", "Water left in pipes, valves or the backflow preventer can freeze and split them. Damage caused by frost is "
                    "not covered by the warranty.", title="Caution"),
                H(2, "7.1  Firmware updates"),
                P("Controllers connected to Wi-Fi update themselves overnight between 2am and 4am when no watering is scheduled. You can "
                  "check the installed version under Menu > About. Updates never change your programmes. If an update fails, the controller "
                  "restarts with the previous version and tries again the following night."),
                H(1, "8  Troubleshooting"),
                trouble,
            ],
            [
                H(1, "9  Warranty and support"),
                P("Calder Hydro Ltd guarantees the CH-6 against faulty materials and workmanship for three years from the date of purchase, "
                  "extended to five years if you register the product within 60 days. This does not affect your statutory rights."),
                L(["Online help: calderhydro.example/support", "Email: help@calderhydro.example", "Telephone: 01422 555 830 (Monday to Friday, 8.30am to 5pm)",
                   "Post: Calder Hydro Ltd, Unit 7, Mytholm Works, Hebden Bridge HX7 6DL, United Kingdom"]),
                H(2, "Declaration of conformity"),
                P("Calder Hydro Ltd declares that the radio equipment type CH-6 is in compliance with the Radio Equipment Regulations 2017 "
                  "and Directive 2014/53/EU. The full text of the declarations is available at calderhydro.example/doc."),
                H(2, "Disposal"),
                P("This product must not be disposed of with household waste. Take it to your local household waste recycling centre or "
                  "return it to the retailer under the WEEE take-back scheme."),
                P("Calder, Calder Hydro and Calder Garden are trademarks of Calder Hydro Ltd. Registered in England and Wales, company number "
                  "08555123. Issue 4, January 2026.", "small"),
            ],
        ],
    }


DOCS = [
    ("w2-paper-en-25", "chromium", paper_en),
    ("w2-paper-engb-26", "libreoffice", paper_engb),
    ("w2-paper-zhcn-27", "chromium", paper_zhcn),
    ("w2-paper-ru-28", "reportlab", paper_ru),
    ("w2-slides-en-29", "chromium", slides_en),
    ("w2-slides-ja-30", "libreoffice", slides_ja),
    ("w2-slides-fr-31", "pylopdf", slides_fr),
    ("w2-slides-es-32", "reportlab", slides_es),
    ("w2-manual-en-33", "chromium", manual_en),
    ("w2-manual-de-34", "libreoffice", manual_de),
    ("w2-manual-zhcn-35", "pylopdf", manual_zhcn),
    ("w2-manual-engb-36", "reportlab", manual_engb),
]
