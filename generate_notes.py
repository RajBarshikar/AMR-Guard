from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def set_page_margins(doc, top=1.5, bottom=1.5, left=2, right=2):
    for section in doc.sections:
        section.top_margin    = Cm(top)
        section.bottom_margin = Cm(bottom)
        section.left_margin   = Cm(left)
        section.right_margin  = Cm(right)

def add_title(doc, text, size=22, bold=True, color=(0x1A, 0x73, 0xE8), center=True):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(*color)
    return p

def add_heading(doc, text, level=1, color=(0x1A, 0x73, 0xE8)):
    colors = {
        1: (0x1A, 0x73, 0xE8),   # Blue
        2: (0xD6, 0x28, 0x28),   # Red
        3: (0x18, 0x80, 0x38),   # Green
        4: (0x7B, 0x1F, 0xA2),   # Purple
    }
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    size_map = {1: 16, 2: 14, 3: 13, 4: 12}
    run.font.size = Pt(size_map.get(level, 12))
    run.font.color.rgb = RGBColor(*colors.get(level, (0,0,0)))
    return p

def add_bullet(doc, text, bold_prefix=None, indent=0):
    p = doc.add_paragraph(style='List Bullet')
    if indent > 0:
        p.paragraph_format.left_indent = Inches(0.25 * indent)
    if bold_prefix:
        run = p.add_run(bold_prefix + ": ")
        run.bold = True
        run.font.size = Pt(10.5)
        run2 = p.add_run(text)
        run2.font.size = Pt(10.5)
    else:
        run = p.add_run(text)
        run.font.size = Pt(10.5)
    return p

def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.runs[0].font.size = Pt(10.5)
    return p

def add_formula(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0xBF, 0x36, 0x00)
    # box shading
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'FFF3E0')
    p._p.get_or_add_pPr().append(shd)
    return p

def add_page_break(doc):
    doc.add_page_break()

def add_highlight_box(doc, text, fill='E8F5E9', text_color=(0x1B, 0x5E, 0x20)):
    p = doc.add_paragraph()
    run = p.add_run("⚑  " + text)
    run.bold = True
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor(*text_color)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    p._p.get_or_add_pPr().append(shd)
    return p

def add_table(doc, headers, rows, header_fill='1A73E8', col_widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for para in hdr_cells[i].paragraphs:
            for run in para.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.size = Pt(10.5)
        # Header background
        tc = hdr_cells[i]._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), header_fill)
        tcPr.append(shd)
    for row_data in rows:
        row_cells = table.add_row().cells
        for i, cell_text in enumerate(row_data):
            row_cells[i].text = cell_text
            for para in row_cells[i].paragraphs:
                for run in para.runs:
                    run.font.size = Pt(10)
    if col_widths:
        for i, row in enumerate(table.rows):
            for j, cell in enumerate(row.cells):
                if j < len(col_widths):
                    cell.width = Inches(col_widths[j])
    return table

def add_mnemonic(doc, text):
    p = doc.add_paragraph()
    run = p.add_run("🧠 MNEMONIC: " + text)
    run.bold = True
    run.italic = True
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor(0x6A, 0x1B, 0x9A)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F3E5F5')
    p._p.get_or_add_pPr().append(shd)

def add_exam_q(doc, q, a):
    p = doc.add_paragraph()
    r1 = p.add_run("Q: " + q + "\n")
    r1.bold = True
    r1.font.size = Pt(10.5)
    r1.font.color.rgb = RGBColor(0xD6, 0x28, 0x28)
    r2 = p.add_run("A: " + a)
    r2.font.size = Pt(10.5)

# ─────────────────────────────────────────────
set_page_margins(doc)

# ═══════════════════════════════════════════════════════════
# COVER PAGE
# ═══════════════════════════════════════════════════════════
doc.add_paragraph()
doc.add_paragraph()
add_title(doc, "BIOPHARMACEUTICS & PHARMACOKINETICS", 24, color=(0x1A, 0x73, 0xE8))
add_title(doc, "UNIT 3 — EXAM-READY NOTES", 20, color=(0xD6, 0x28, 0x28))
add_title(doc, "B. Pharmacy | Semester 6", 14, color=(0x18, 0x80, 0x38), bold=False)
doc.add_paragraph()
add_title(doc, "📚 Topics Covered:", 13, color=(0x37, 0x47, 0x51), bold=True)
add_title(doc, "Introduction • Pharmacokinetics • PK Models • Rate Processes\nOne-Compartment Open Model • PK Parameters", 11, color=(0x37, 0x47, 0x51), bold=False)
doc.add_paragraph()
add_title(doc, "Optimized for: 10-mark | 5-mark | 2-mark answers", 11, color=(0x7B, 0x1F, 0xA2), bold=True)
add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 1: INTRODUCTION TO PHARMACOKINETICS
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 1: INTRODUCTION TO PHARMACOKINETICS", 1)
doc.add_paragraph()

add_heading(doc, "1.1 Quick Definition", 2)
add_bullet(doc, "Pharmacokinetics (PK): Study of kinetics of drug ADME (Absorption, Distribution, Metabolism, Excretion) and their relationship with pharmacological/therapeutic/toxicological response.", bold_prefix="📌 Pharmacokinetics")
add_bullet(doc, "Clinical PK: Application of PK principles in safe & effective management of individual patient.", bold_prefix="Clinical PK")
add_bullet(doc, "Population PK: Study of PK differences of drugs in various population groups.", bold_prefix="Population PK")
add_bullet(doc, "Toxicokinetics: Application of PK principles to drug safety evaluation studies.", bold_prefix="Toxicokinetics")
add_bullet(doc, "Dosage Regimen: The frequency of administration of a drug in a particular dose.", bold_prefix="Dosage Regimen")

doc.add_paragraph()
add_heading(doc, "1.2 Two Aspects of PK Studies", 2)
add_bullet(doc, "Theoretical Aspect: Development of pharmacokinetic models to predict drug disposition. Uses statistical methods.")
add_bullet(doc, "Experimental Aspect: Development of biological sampling techniques, analytical methods for drug concentration measurement in biological samples.")

doc.add_paragraph()
add_heading(doc, "1.3 Key Pharmacokinetic Parameters (Plasma Level-Time Curve)", 2)

add_table(doc,
    ["Parameter", "Symbol", "Definition", "Unit"],
    [
        ["Peak Plasma Concentration", "Cmax", "Maximum drug concentration in plasma; at peak, absorption rate = elimination rate", "mcg/mL"],
        ["Time of Peak Concentration", "tmax", "Time required for drug to reach Cmax; estimates rate of absorption", "hours"],
        ["Area Under Curve", "AUC", "Total integrated area under plasma-time profile; reflects total drug absorbed (extent of absorption)", "mcg/mL × hr"],
    ],
    col_widths=[1.5, 0.7, 3.0, 0.9]
)

doc.add_paragraph()
add_heading(doc, "1.4 Pharmacodynamic Parameters", 2)

add_table(doc,
    ["Parameter", "Symbol", "Definition"],
    [
        ["Minimum Effective Concentration", "MEC", "Minimum plasma drug concentration to produce therapeutic effect"],
        ["Maximum Safe Concentration", "MSC (MTC)", "Plasma drug conc. above which adverse/toxic effects appear"],
        ["Onset of Action", "—", "Beginning of pharmacological response (when plasma conc. just exceeds MEC)"],
        ["Onset Time", "—", "Time required for drug to start producing pharmacological response"],
        ["Duration of Action", "—", "Time period plasma conc. remains above MEC"],
        ["Intensity of Action", "—", "Maximum pharmacological response at peak plasma concentration"],
        ["Therapeutic Range", "—", "Drug concentration between MEC and MSC (Therapeutic Window)"],
        ["Therapeutic Index", "TI", "Ratio of MSC to MEC; also = toxic dose / therapeutic dose"],
    ],
    col_widths=[2.0, 1.0, 3.2]
)

doc.add_paragraph()
add_highlight_box(doc, "EXAM TIP: Cmax reflects INTENSITY, tmax reflects RATE, AUC reflects EXTENT of drug absorption.", fill='E3F2FD', text_color=(0x0D, 0x47, 0xA1))
add_mnemonic(doc, "'CTA' = Cmax (intensity), Tmax (rate), AUC (extent)")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 2: RATE PROCESSES & ORDER OF REACTIONS
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 2: RATE PROCESSES & ORDERS OF REACTIONS", 1)
doc.add_paragraph()

add_heading(doc, "2.1 Quick Definition", 2)
add_bullet(doc, "Rate: Velocity with which a reaction/process occurs.")
add_bullet(doc, "Order of Reaction: Manner in which drug concentration influences the rate of reaction.")
add_bullet(doc, "General Rate Equation: dC/dt = −KCⁿ  (K = rate constant, n = order of reaction)", bold_prefix="Formula")

doc.add_paragraph()
add_heading(doc, "2.2 Types of Rate Processes (Comparison Table)", 2)

add_table(doc,
    ["Feature", "Zero-Order", "First-Order", "Mixed-Order"],
    [
        ["Rate equation", "dC/dt = −K₀", "dC/dt = −KC", "Michaelis-Menten"],
        ["Rate depends on", "Constant (independent of conc.)", "Directly proportional to conc.", "Changes with dose"],
        ["Integrated equation", "C = C₀ − K₀t", "C = C₀ · e^(−Kt)  or  logC = logC₀ − Kt/2.303", "Variable"],
        ["Half-life", "t½ = C₀/2K₀ (concentration-dependent)", "t½ = 0.693/K (constant)", "Dose-dependent"],
        ["Graph (C vs t)", "Straight line", "Curve (monoexponential)", "Variable"],
        ["Graph (log C vs t)", "Curve", "Straight line (slope = −K/2.303)", "Variable"],
        ["Examples", "IV infusion, implants, osmotic pumps, saturated enzyme systems", "Most ADME processes", "Phenytoin, ethanol (at high dose)"],
        ["Also called", "Constant rate / Saturation kinetics", "Linear kinetics", "Dose-dependent / Nonlinear kinetics"],
    ],
    col_widths=[1.5, 1.7, 2.2, 1.6]
)

doc.add_paragraph()
add_heading(doc, "2.3 Zero-Order Process — Key Points", 2)
add_bullet(doc, "Rate is INDEPENDENT of drug concentration.")
add_bullet(doc, "Occurs when enzyme/carrier is saturated (Vmax reached).")
add_bullet(doc, "C = C₀ − K₀t  → Plot of C vs t = straight line with slope = −K₀, y-intercept = C₀", bold_prefix="Formula")
add_bullet(doc, "t½ = C₀ / 2K₀  (depends on initial concentration)", bold_prefix="Half-life")
add_bullet(doc, "IV infusion (constant rate), controlled drug delivery (implants, osmotic pumps), saturated metabolism/protein binding")

doc.add_paragraph()
add_heading(doc, "2.4 First-Order Process — Key Points", 2)
add_bullet(doc, "Rate is DIRECTLY PROPORTIONAL to drug concentration.")
add_bullet(doc, "Most pharmacokinetic processes follow first-order kinetics.")
add_bullet(doc, "C = C₀ · e^(−Kt)  |  log C = log C₀ − Kt/2.303", bold_prefix="Formula")
add_bullet(doc, "t½ = 0.693/K  → CONSTANT, independent of initial concentration", bold_prefix="Half-life")
add_bullet(doc, "Plot of log C vs t = straight line with slope = −K/2.303")

doc.add_paragraph()
add_heading(doc, "2.5 Mixed-Order (Nonlinear) Kinetics", 2)
add_bullet(doc, "Kinetics changes from first-order → zero-order with increasing dose or chronic medication.")
add_bullet(doc, "Also called: Dose-dependent kinetics, Michaelis-Menten kinetics, Saturable kinetics.")
add_bullet(doc, "Examples: Vitamin C (absorption), Naproxen (distribution), Riboflavin (elimination)")

add_formula(doc, "Michaelis-Menten: −dC/dt = Vmax·C / (Km + C)")
add_bullet(doc, "When C >> Km → zero-order; When C << Km → first-order")

add_highlight_box(doc, "EXAM TIP: First-order t½ is CONSTANT; Zero-order t½ is CONCENTRATION-DEPENDENT. This is a common MCQ trap!", fill='FFF9C4', text_color=(0x7B, 0x60, 0x00))
add_mnemonic(doc, "'FIZZ' = First-order Is Zero order's opposite in t½ behavior")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 3: PHARMACOKINETIC MODELS
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 3: PHARMACOKINETIC MODELS", 1)
doc.add_paragraph()

add_heading(doc, "3.1 Quick Definition", 2)
add_bullet(doc, "PK Model: A hypothesis using mathematical terms to concisely describe quantitative relationships of drug disposition in the body over time.")
add_bullet(doc, "Purpose: To predict drug concentration in body, compute PK parameters, and describe time course of drug.")

doc.add_paragraph()
add_heading(doc, "3.2 Classification of PK Models", 2)

add_table(doc,
    ["Model Type", "Also Known As", "Key Feature"],
    [
        ["Compartment Models", "Empirical models", "Imaginary compartments; most commonly used"],
        ["Physiological Models", "PBPK models (Realistic)", "Based on actual anatomy/physiology"],
        ["Distributed Parameter Models", "Realistic models", "Considers regional blood flow & diffusion variations"],
        ["Non-compartmental (NCA)", "Model-independent", "No specific compartment assumed; uses statistical moments"],
    ],
    col_widths=[2.0, 1.8, 2.8]
)

doc.add_paragraph()
add_heading(doc, "3.3 Compartment Models — Deep Dive", 2)
add_bullet(doc, "A compartment is NOT a real anatomical region — it's a hypothetical/imaginary unit consisting of tissues with SIMILAR blood flow and drug affinity.")
add_bullet(doc, "Body is considered as several compartments connected reversibly.")
add_bullet(doc, "Drug movement between compartments described by first-order rate constants (K).")
add_bullet(doc, "Subscript notation: K₁₂ = drug movement from compartment 1 → 2; K₂₁ = compartment 2 → 1.")

doc.add_paragraph()
add_heading(doc, "3.4 Types of Compartment Models", 3)

add_table(doc,
    ["Model", "Compartments", "Structure", "Administration"],
    [
        ["Mammillary", "1, 2, 3...", "Peripheral compartments connected TO central compartment (parallel)", "Most common in PK"],
        ["Catenary", "1, 2, 3...", "Compartments joined in SERIES (like train compartments)", "Rarely used (not physiologically realistic)"],
    ],
    col_widths=[1.5, 1.3, 2.5, 1.8]
)

doc.add_paragraph()
add_heading(doc, "🔑 Mammillary Model — Key Details", 3)
add_bullet(doc, "Central compartment (Compartment 1): Plasma + highly perfused tissues (lungs, liver, kidneys) — rapidly equilibrate with drug.")
add_bullet(doc, "Drug directly absorbed into central compartment (blood).")
add_bullet(doc, "Elimination occurs from central compartment (liver & kidneys are chief eliminating organs).")
add_bullet(doc, "Peripheral compartments (2, 3...): Low vascularity, poor perfusion tissues (muscle, fat).")
add_bullet(doc, "K₀₁ = Ka (absorption rate constant); K₁₀ = KE (elimination rate constant)")

doc.add_paragraph()
add_heading(doc, "3.5 Mammillary Model Types (Summary)", 3)

add_table(doc,
    ["Model No.", "Description", "Route"],
    [
        ["Model 1", "One-compartment open model, IV bolus", "IV"],
        ["Model 2", "One-compartment open model, extravascular (oral, rectal)", "EV"],
        ["Model 3", "Two-compartment open model, IV administration", "IV"],
        ["Model 4", "Two-compartment open model, extravascular", "EV"],
        ["Model 5", "Three-compartment open model, IV", "IV"],
        ["Model 6", "Three-compartment open model, extravascular", "EV"],
    ],
    col_widths=[1.0, 4.0, 1.2]
)

doc.add_paragraph()
add_heading(doc, "3.6 Physiological (PBPK) Models", 2)
add_bullet(doc, "Based on KNOWN anatomical and physiological data → more realistic picture.")
add_bullet(doc, "Tissues with similar perfusion properties grouped together:")
add_bullet(doc, "Rapidly Equilibrating Tissues (RET): Lungs, liver, brain, kidney", indent=1)
add_bullet(doc, "Slowly Equilibrating Tissues (SET): Muscles, adipose tissue", indent=1)
add_bullet(doc, "Two types based on rate-limiting factor:")
add_bullet(doc, "Blood flow rate-limited (perfusion rate-limited): Drug movement within tissue >> rate of delivery by blood. For lipophilic drugs.", indent=1)
add_bullet(doc, "Membrane permeation rate-limited (diffusion-limited): Cell membrane is barrier. For highly polar, ionized, charged drugs.", indent=1)

doc.add_paragraph()
add_heading(doc, "3.7 Distributed Parameter Models", 2)
add_bullet(doc, "Similar to physiological models but accounts for variations in:")
add_bullet(doc, "Variations in blood flow to an organ", indent=1)
add_bullet(doc, "Variations in drug diffusion within an organ", indent=1)
add_bullet(doc, "Useful for assessing regional drug concentrations in tumors or necrotic tissues.")
add_bullet(doc, "Mathematical equations are more complex; data collection is more difficult.")

doc.add_paragraph()
add_heading(doc, "3.8 Non-Compartmental Analysis (NCA) / Model-Independent Method", 2)
add_bullet(doc, "Does NOT require assumption of a specific compartment model.")
add_bullet(doc, "Based on: (1) Linear kinetics assumption, (2) Statistical moments theory.")
add_bullet(doc, "Single dose of drug administered → experimental data collected.")
add_bullet(doc, "Key parameter: MRT (Mean Residence Time)")
add_formula(doc, "MRT = AUMC / AUC")
add_bullet(doc, "AUMC = Area Under first-Moment Curve (plot of C×t vs t)")
add_bullet(doc, "AUC = Area Under zero-Moment Curve (plot of C vs t)")
add_bullet(doc, "MRT = Average time spent by drug in body before elimination.")
add_bullet(doc, "MRT represents time for 63.2% of IV bolus dose to be eliminated.")
add_bullet(doc, "MRT is the statistical moment analogy of half-life (t½).")
add_bullet(doc, "Areas calculated by Trapezoidal Rule.")

add_highlight_doc = doc
add_highlight_box(doc, "EXAM TIP: Mammillary model = PARALLEL arrangement; Catenary model = SERIES arrangement (like train compartments).", fill='E8F5E9', text_color=(0x1B, 0x5E, 0x20))
add_mnemonic(doc, "'MAMA is Central' = Mammillary model has peripheral compartments connected to CENTRAL compartment")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 4: ONE-COMPARTMENT OPEN MODEL
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 4: ONE-COMPARTMENT OPEN MODEL", 1)
doc.add_paragraph()

add_heading(doc, "4.1 Quick Definition", 2)
add_bullet(doc, "The simplest PK model; body treated as a SINGLE kinetically homogeneous unit.")
add_bullet(doc, "'Open' = Input (availability) and output (elimination) are UNIDIRECTIONAL; drug can be eliminated from body.")
add_bullet(doc, "Also called: Instantaneous Distribution Model.")

doc.add_paragraph()
add_heading(doc, "4.2 Assumptions of One-Compartment Open Model", 2)

add_table(doc,
    ["#", "Assumption"],
    [
        ["1", "Body = single kinetically homogeneous unit with NO barriers to drug movement"],
        ["2", "Distribution equilibrium attained INSTANTANEOUSLY and maintained at all times"],
        ["3", "Drugs move dynamically IN (absorption) and OUT (elimination) of the compartment"],
        ["4", "Elimination follows first-order (monoexponential) kinetics"],
        ["5", "Rate of input (absorption) > Rate of output (elimination)"],
        ["6", "Plasma is the anatomical reference compartment; plasma conc. represents all body tissues"],
        ["Note", "Model does NOT assume plasma drug conc. equals concentration in other tissues"],
    ],
    col_widths=[0.4, 5.8]
)

doc.add_paragraph()
add_heading(doc, "4.3 Types of One-Compartment Open Models", 2)
add_bullet(doc, "Model 1: IV Bolus administration")
add_bullet(doc, "Model 2: Continuous IV Infusion (constant rate / zero-order)")
add_bullet(doc, "Model 3: Extravascular administration — Zero-order absorption")
add_bullet(doc, "Model 4: Extravascular administration — First-order absorption")

doc.add_paragraph()
add_heading(doc, "4.4 IV Bolus Administration", 2)
add_bullet(doc, "Drug given as rapid IV injection (1–3 min for complete circulation).")
add_bullet(doc, "Absorption rate is neglected (no absorption phase).")
add_bullet(doc, "Only ELIMINATION PHASE is observed.")
add_bullet(doc, "Rate equation: dX/dt = −KE·X", bold_prefix="Formula")
add_formula(doc, "C = C₀ · e^(−KE·t)  ⟹  log C = log C₀ − (KE/2.303)·t")
add_bullet(doc, "Semilog plot of C vs t = straight line with slope = −KE/2.303 and y-intercept = C₀")

doc.add_paragraph()
add_heading(doc, "🔑 Elimination Phase Parameters (IV Bolus)", 3)

add_table(doc,
    ["Parameter", "Symbol", "Formula", "Notes"],
    [
        ["Elimination Rate Constant", "KE (or k)", "From slope of log C vs t: KE = −2.303 × slope", "Units: hr⁻¹ or min⁻¹"],
        ["Elimination Half-Life", "t½", "t½ = 0.693 / KE", "Time for plasma conc to drop by 50%"],
        ["Apparent Volume of Distribution", "Vd", "Vd = X₀ / C₀ = Dose / C₀", "Units: L or mL; relates total body drug to plasma conc."],
        ["Clearance", "Cl", "Cl = KE × Vd  =  Dose / AUC", "Units: mL/min or L/hr"],
        ["AUC (IV Bolus)", "AUC", "AUC = C₀ / KE  =  Dose / (KE × Vd)", "Total drug absorbed"],
    ],
    col_widths=[1.8, 0.7, 2.4, 1.3]
)

doc.add_paragraph()
add_heading(doc, "4.5 Clearance — In Depth", 2)
add_bullet(doc, "Defined as: Volume of plasma cleared of drug per unit time by metabolism + excretion.")
add_bullet(doc, "Most important parameter in clinical drug applications.")
add_bullet(doc, "Clearances are ADDITIVE across organs:")
add_formula(doc, "ClTotal = ClRenal + ClHepatic + ClOther organs")
add_formula(doc, "ClRenal = Rate of elimination by kidney / C")
add_formula(doc, "ClHepatic = Rate of elimination by liver / C")
add_bullet(doc, "Cl = KE × Vd  (product of elimination rate constant and volume of distribution)", bold_prefix="Key Formula")
add_formula(doc, "Cl = 0.693 × Vd / t½")
add_bullet(doc, "Clearance is constant when drug follows first-order kinetics.")

doc.add_paragraph()
add_heading(doc, "4.6 Apparent Volume of Distribution (Vd) — In Depth", 2)
add_bullet(doc, "Vd has NO direct physiological meaning — it's a 'virtual' volume.")
add_bullet(doc, "Defined as: Volume of plasma in which the TOTAL AMOUNT of drug in the body would be dissolved to reflect observed plasma concentration.")
add_formula(doc, "Vd = X₀ / C₀  =  Dose (mg) / C₀ (mg/L)   →  Units: Liters")
add_bullet(doc, "Cp(plasma) ∝ Amount of drug in tissues → Vd is the constant of proportionality.")
add_bullet(doc, "High Vd (>40L): Extensive tissue distribution (e.g., chloroquine)")
add_bullet(doc, "Low Vd (~5L): Drug stays in plasma (e.g., heparin)")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 5: IV INFUSION & EXTRAVASCULAR ADMINISTRATION
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 5: IV INFUSION & EXTRAVASCULAR ADMINISTRATION", 1)
doc.add_paragraph()

add_heading(doc, "5.1 Intravenous Infusion (Constant Rate — Zero-Order)", 2)
add_bullet(doc, "Used when: (1) Drug has potential for toxicity via rapid injection, (2) Stable plasma concentration is desired.")
add_bullet(doc, "Drug administered at CONSTANT RATE (zero-order input) by IV infusion.")
add_bullet(doc, "Duration of infusion >> half-life of the drug.")

doc.add_paragraph()
add_heading(doc, "Advantages of IV Infusion", 3)
add_bullet(doc, "Easy to control infusion rate as per individual patient needs.")
add_bullet(doc, "Prevents fluctuating peak-valley (maxima-minima) plasma levels → ideal for drugs with narrow therapeutic index.")
add_bullet(doc, "Other drugs, electrolytes, nutrients can be simultaneously administered.")

add_formula(doc, "During infusion: C = R₀/(KE·Vd) × [1 − e^(−KE·t)]")
add_formula(doc, "Steady-state (Css): Css = R₀ / (KE × Vd)  =  R₀ / Cl")
add_bullet(doc, "Css reached when infusion rate (R₀) = elimination rate (KE·Vd·Css)")
add_bullet(doc, "After infusion stopped: C = Css · e^(−KE·t)")

doc.add_paragraph()
add_heading(doc, "5.2 Infusion + Loading Dose", 2)
add_bullet(doc, "Problem: Drugs with long half-life take very long to reach steady-state (e.g., phenobarbital = 5 days).")
add_bullet(doc, "Solution: Give a LOADING DOSE (IV bolus) first to achieve desired Css immediately, then follow with infusion to maintain it.")
add_formula(doc, "Loading Dose (DL) = Css × Vd")
add_formula(doc, "Infusion Rate (R₀) = Css × KE × Vd  =  Css × Cl")

doc.add_paragraph()
add_heading(doc, "5.3 Extravascular (EV) Administration", 2)
add_bullet(doc, "Routes: Oral, IM, rectal, subcutaneous, etc.")
add_bullet(doc, "Absorption is PREREQUISITE for therapeutic activity.")
add_bullet(doc, "Rate of absorption: Zero-order or First-order process.")

doc.add_paragraph()
add_heading(doc, "Comparison: Zero-Order vs First-Order Absorption", 3)

add_table(doc,
    ["Feature", "Zero-Order Absorption", "First-Order Absorption"],
    [
        ["Rate", "Constant (independent of ARA)", "Decreases as ARA decreases (dependent on ARA)"],
        ["ARA vs t plot (regular)", "Linear (straight line), slope = absorption rate", "Curvilinear"],
        ["ARA vs t plot (semilog)", "Ever-increasing gradient (curve)", "Straight line, slope = Ka"],
        ["Examples", "Controlled drug delivery, GITS, transdermal patches", "Most oral tablets/capsules"],
        ["Model equation", "Same as IV infusion equations", "Biexponential equation"],
    ],
    col_widths=[1.6, 2.2, 2.2]
)

add_bullet(doc, "ARA = Amount Remaining to be Absorbed", bold_prefix="Note")

doc.add_paragraph()
add_heading(doc, "First-Order Absorption Model", 3)
add_formula(doc, "C = (Ka·F·X₀) / (Vd(Ka−KE)) × [e^(−KE·t) − e^(−Ka·t)]")
add_bullet(doc, "Ka = first-order absorption rate constant")
add_bullet(doc, "KE = first-order elimination rate constant")
add_bullet(doc, "F = bioavailability fraction")
add_bullet(doc, "At tmax: Absorption rate = Elimination rate (Cmax occurs here)")
add_formula(doc, "tmax = 2.303/(Ka−KE) × log(Ka/KE)")
add_formula(doc, "Cmax = (F·X₀/Vd) × e^(−KE·tmax)")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 6: PHARMACOKINETIC PARAMETERS (COMPLETE)
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 6: PHARMACOKINETIC PARAMETERS — COMPLETE SUMMARY", 1)
doc.add_paragraph()

add_heading(doc, "6.1 Elimination Rate Constant (KE or k)", 2)
add_bullet(doc, "Describes FRACTION of drug eliminated per unit time.")
add_bullet(doc, "Describes rate at which plasma concentrations decline during elimination phase.")
add_formula(doc, "dX/dt = −KE·X  →  X = X₀·e^(−KE·t)  →  KE = 0.693/t½")
add_bullet(doc, "Clinical Use: Estimate how long to stop a drug if patient has toxic levels.")

doc.add_paragraph()
add_heading(doc, "6.2 Half-Life (t½)", 2)
add_bullet(doc, "Also called: Biological half-life.")
add_bullet(doc, "Time for plasma drug concentration (and amount in body) to decline by 50%.")
add_formula(doc, "t½ = 0.693 / KE")
add_bullet(doc, "First-order: t½ is CONSTANT (independent of initial concentration).")
add_bullet(doc, "Clinical Importance:")
add_bullet(doc, "Determine dosing frequency", indent=1)
add_bullet(doc, "Estimate time to reach steady state (~5 × t½)", indent=1)
add_bullet(doc, "Predict drug accumulation", indent=1)

doc.add_paragraph()
add_heading(doc, "6.3 Apparent Volume of Distribution (Vd)", 2)
add_formula(doc, "Vd = Dose / C₀  =  X / Cp")
add_bullet(doc, "Not a real volume — relates total body drug amount to plasma concentration.")
add_bullet(doc, "Primary pharmacokinetic parameter (along with clearance).")

add_table(doc,
    ["Vd Value", "Interpretation", "Drug Example"],
    [
        ["~3-5 L", "Drug confined to plasma", "Heparin, warfarin"],
        ["~12-15 L", "Drug distributes to ECF", "Gentamicin"],
        ["~40 L", "Total body water distribution", "Theophylline"],
        [">100 L", "Extensive tissue binding", "Chloroquine, digoxin"],
    ],
    col_widths=[1.2, 2.8, 2.2]
)

doc.add_paragraph()
add_heading(doc, "6.4 Clearance (Cl)", 2)
add_bullet(doc, "Volume of plasma cleared of drug per unit time.")
add_bullet(doc, "Most important parameter in clinical drug applications.")
add_formula(doc, "Cl = KE × Vd  =  Dose / AUC")
add_formula(doc, "Cl = 0.693 × Vd / t½")
add_formula(doc, "ClTotal = ClRenal + ClHepatic + ClOther")

doc.add_paragraph()
add_heading(doc, "6.5 Absorption Rate Constant (Ka)", 2)
add_bullet(doc, "Fractional rate of drug absorption from administration site into systemic circulation.")
add_bullet(doc, "Units: time⁻¹ (hr⁻¹)")
add_formula(doc, "Ka = ln(2) / t½,absorption  =  0.693 / t½a")
add_bullet(doc, "Influences both Cmax and tmax.")
add_bullet(doc, "Clinical Importance:")
add_bullet(doc, "Determines time required for drug to reach effective plasma concentration", indent=1)
add_bullet(doc, "Used to design multiple dosage regimens", indent=1)
add_bullet(doc, "In bioequivalence studies: Ka comparison indicates relative rate of absorption", indent=1)

doc.add_paragraph()
add_heading(doc, "6.6 Area Under Curve (AUC)", 2)
add_bullet(doc, "Reflects TOTAL amount of active drug reaching systemic circulation.")
add_bullet(doc, "Independent of route of administration and elimination process (when linear).")
add_bullet(doc, "AUC ∝ Dose (proportional to dose in linear kinetics)")
add_formula(doc, "AUC (IV bolus) = C₀ / KE  =  Dose / (KE × Vd)")

add_heading(doc, "Importance of AUC:", 3)
add_bullet(doc, "Toxicology: Measure of DRUG EXPOSURE")
add_bullet(doc, "Biopharmaceutics: COMPARISON of drug products (bioequivalence)")
add_bullet(doc, "Pharmacokinetics: Measure of PK parameters — Clearance, Bioavailability")

doc.add_paragraph()
add_heading(doc, "6.7 Methods to Calculate AUC", 2)

add_table(doc,
    ["Method", "Description"],
    [
        ["1. Trapezoidal Rule", "Most common. Divide curve into trapezoids, calculate area of each, sum all. AUC = Σ (Cn + Cn+1)/2 × (tn+1 − tn)"],
        ["2. Planimeter (Platometer)", "Mechanical measuring instrument to determine area of arbitrary 2D shape"],
        ["3. Cut & Weigh Method", "Plot concentration-time curve on graph paper. Cut out area under curve. Weigh it. Compare with weight of known area: AUC1/AUC2 = W1/W2"],
        ["4. Counting Squares", "Plot on graph paper. Count squares under curve. Calculate area per square × number of squares"],
    ],
    col_widths=[2.0, 4.2]
)

add_highlight_box(doc, "MOST IMPORTANT: Trapezoidal Rule is the standard method for AUC calculation — most frequently asked!", fill='FFF3E0', text_color=(0xE6, 0x51, 0x00))

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# ALL EXAM NOTES
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📝 EXAM ANSWER NOTES", 1)
doc.add_paragraph()

# ── 10-MARK ANSWERS ──
add_heading(doc, "A. 10-MARK ANSWER NOTES", 2)
add_heading(doc, "Q1. Write a note on One-Compartment Open Model with IV Bolus Administration.", 3)
doc.add_paragraph("Answer structure:")
add_bullet(doc, "Definition: One-compartment open model is the simplest PK model where body is treated as a single, kinetically homogeneous unit. 'Open' = unidirectional input-output.")
add_bullet(doc, "Assumptions (list all 6 — see Chapter 4.2 table)")
add_bullet(doc, "Model Diagram: Input (absorption) → [Body/Compartment] → Output (Elimination), with KE arrow")
add_bullet(doc, "Mathematical derivation for IV Bolus: dX/dt = −KE·X → C = C₀·e^(−KE·t) → log C = log C₀ − (KE/2.303)·t")
add_bullet(doc, "Parameters: KE (from slope), t½ = 0.693/KE, Vd = Dose/C₀, Cl = KE × Vd")
add_bullet(doc, "Graphical representation: Cartesian (C vs t = curve) and Semilog (log C vs t = straight line)")

doc.add_paragraph()
add_heading(doc, "Q2. Classify and explain Pharmacokinetic Models.", 3)
add_bullet(doc, "Introduction: PK model definition and purpose")
add_bullet(doc, "Classification Table: Compartment, Physiological, Distributed Parameter, Non-compartmental")
add_bullet(doc, "Compartment models: Mammillary (central + peripheral, parallel) vs Catenary (series)")
add_bullet(doc, "Mammillary model details: Central compartment, peripheral compartments, rate constants K₁₂, K₂₁, K₁₀")
add_bullet(doc, "Physiological models: PBPK, RET vs SET, blood flow-limited vs diffusion-limited")
add_bullet(doc, "Non-compartmental analysis: MRT = AUMC/AUC, statistical moments theory")

doc.add_paragraph()
add_heading(doc, "Q3. Explain Rate Processes in Pharmacokinetics.", 3)
add_bullet(doc, "Introduction: Rate, rate constant, order of reaction")
add_bullet(doc, "Zero-order: Definition, equation C = C₀ − K₀t, graph, t½, examples")
add_bullet(doc, "First-order: Definition, equation C = C₀e^(−Kt), logC graph, t½ = 0.693/K, examples")
add_bullet(doc, "Mixed-order: Definition, Michaelis-Menten, nonlinear kinetics, dose-dependent examples")
add_bullet(doc, "Comparison table of all three types")

doc.add_paragraph()
add_heading(doc, "Q4. Explain Pharmacokinetic Parameters with formulas.", 3)
add_bullet(doc, "Cmax, tmax, AUC (bioavailability parameters)")
add_bullet(doc, "KE, t½, Vd, Cl (disposition parameters)")
add_bullet(doc, "Ka (absorption parameter)")
add_bullet(doc, "MEC, MSC, TI, Therapeutic window (PD parameters)")
add_bullet(doc, "All formulas + clinical significance of each")

doc.add_paragraph()
add_heading(doc, "Q5. Explain IV Infusion with loading dose concept.", 3)
add_bullet(doc, "IV infusion: Why used, zero-order input")
add_bullet(doc, "Advantages: 3 points")
add_bullet(doc, "Steady-state: Css = R₀/Cl, reached at ~5 half-lives")
add_bullet(doc, "Loading dose concept: Why needed (long t½ drugs), formula DL = Css × Vd")
add_bullet(doc, "Diagram: Loading dose + infusion → resultant constant plasma level")

doc.add_paragraph()
add_heading(doc, "B. 5-MARK ANSWER NOTES", 2)

add_table(doc,
    ["Topic", "5-Mark Answer Outline"],
    [
        ["Cmax, tmax, AUC", "Define each, their units, what they measure (intensity/rate/extent), how to use from plasma curve"],
        ["Mammillary vs Catenary Model", "Define each, diagram description, key differences (parallel vs series), why mammillary is preferred"],
        ["Zero-order kinetics", "Definition, equation C = C₀−K₀t, graph, t½ formula, 3 examples"],
        ["First-order kinetics", "Definition, C = C₀e^(−Kt), logC graph, t½ = 0.693/K, constant t½, most PK processes"],
        ["Clearance", "Definition, formula Cl = KE·Vd = Dose/AUC, additive nature, ClTotal components, clinical use"],
        ["Volume of Distribution", "Definition, formula Vd = Dose/C₀, not a real volume, high vs low Vd interpretation"],
        ["Non-compartmental Analysis", "Model-independent method, MRT = AUMC/AUC, trapezoidal rule, advantage"],
        ["Extravascular absorption", "Zero-order vs first-order absorption, ARA plots, equations, Ka significance"],
        ["AUC calculation methods", "4 methods: Trapezoidal (most important), Planimeter, Cut & Weigh, Counting squares"],
        ["MEC, MSC, Therapeutic Index", "Define all, therapeutic window concept, formula TI = MSC/MEC or toxic dose/therapeutic dose"],
    ],
    col_widths=[2.2, 4.0]
)

doc.add_paragraph()
add_heading(doc, "C. 2-MARK ANSWER NOTES", 2)

add_table(doc,
    ["Question", "Answer (2-mark)"],
    [
        ["Define Pharmacokinetics", "Study of kinetics of ADME and their relationship with pharmacological/toxicological response in man and animals."],
        ["What is Cmax?", "Peak plasma concentration; maximum drug concentration reached in plasma; Cmax ∝ intensity of action; expressed in mcg/mL."],
        ["What is tmax?", "Time to reach peak plasma concentration; indicates rate of absorption; expressed in hours."],
        ["Define AUC", "Area under plasma concentration-time curve; reflects total drug reaching systemic circulation (extent of absorption); unit: mcg/mL·hr."],
        ["Define MEC", "Minimum Effective Concentration — minimum plasma drug concentration required to produce therapeutic effect."],
        ["Define Therapeutic Index", "TI = MSC/MEC; ratio of toxic dose to therapeutic dose; higher TI = safer drug."],
        ["What is zero-order kinetics?", "Rate of drug elimination/absorption is CONSTANT, independent of drug concentration; C = C₀ − K₀t; examples: IV infusion, osmotic pumps."],
        ["What is first-order kinetics?", "Rate is directly proportional to drug concentration; t½ = 0.693/KE (constant); log C vs t = straight line; most PK processes."],
        ["Define Volume of Distribution", "Vd = Dose/C₀; apparent (not real) volume of plasma in which total drug in body would need to be dissolved to reflect observed plasma concentration."],
        ["Define Clearance", "Cl = KE × Vd = Dose/AUC; volume of plasma cleared of drug per unit time; expressed in mL/min or L/hr."],
        ["What is half-life (t½)?", "Time for plasma drug concentration to decline by 50%; t½ = 0.693/KE; constant for first-order processes."],
        ["What is MRT?", "Mean Residence Time = AUMC/AUC; average time spent by drug in body before elimination; time for 63.2% of IV dose to be eliminated."],
        ["What is Ka?", "Absorption rate constant; fractional rate of drug absorption from site of administration; Ka = 0.693/t½a; affects Cmax and tmax."],
        ["What is loading dose?", "Initial large dose given to achieve desired Css immediately, before starting maintenance infusion. DL = Css × Vd."],
        ["What is Catenary model?", "Compartment model where compartments are joined in SERIES (like train compartments); rarely used as not physiologically realistic."],
        ["What is Mammillary model?", "Most common compartment model; peripheral compartments connected in PARALLEL to central compartment; elimination occurs from central compartment."],
        ["What is steady state (Css)?", "Css = R₀/Cl; plasma concentration at which infusion rate = elimination rate; achieved after ~5 half-lives."],
        ["Trapezoidal rule for AUC", "AUC calculated by dividing plasma-time curve into trapezoids; area of each = (Cn + Cn+1)/2 × (tn+1 − tn); sum all areas."],
    ],
    col_widths=[2.5, 3.7]
)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# LAST MINUTE REVISION SHEET
# ═══════════════════════════════════════════════════════════
add_heading(doc, "⚡ LAST-MINUTE REVISION SHEET — UNIT 3", 1)
doc.add_paragraph()
add_highlight_box(doc, "Revise this 1 hour before the exam!", fill='FFEBEE', text_color=(0xC6, 0x28, 0x28))
doc.add_paragraph()

add_heading(doc, "🔑 MUST-KNOW DEFINITIONS", 2)
add_bullet(doc, "Pharmacokinetics = Study of ADME kinetics")
add_bullet(doc, "Dosage Regimen = Frequency of drug administration")
add_bullet(doc, "Cmax = Peak plasma concentration (intensity)")
add_bullet(doc, "tmax = Time to peak (rate of absorption)")
add_bullet(doc, "AUC = Area under curve (extent of absorption)")
add_bullet(doc, "MEC = Minimum plasma conc. for therapeutic effect")
add_bullet(doc, "MSC/MTC = Plasma conc. above which toxicity occurs")
add_bullet(doc, "TI = MSC/MEC")
add_bullet(doc, "Vd = Apparent volume of distribution = Dose/C₀")
add_bullet(doc, "Cl = Clearance = KE × Vd")
add_bullet(doc, "t½ = 0.693/KE")
add_bullet(doc, "MRT = AUMC/AUC")
add_bullet(doc, "Loading Dose = Css × Vd")

doc.add_paragraph()
add_heading(doc, "📊 KEY FORMULAS QUICK REFERENCE", 2)

add_table(doc,
    ["Formula", "Meaning"],
    [
        ["C = C₀ − K₀t", "Zero-order; C vs t = straight line"],
        ["C = C₀·e^(−KE·t) OR log C = log C₀ − KE·t/2.303", "First-order; log C vs t = straight line"],
        ["t½ = 0.693/KE", "First-order half-life (constant)"],
        ["t½ = C₀/(2K₀)", "Zero-order half-life (depends on C₀)"],
        ["Vd = Dose/C₀", "Volume of distribution"],
        ["Cl = KE × Vd = Dose/AUC", "Clearance"],
        ["Css = R₀/Cl = R₀/(KE·Vd)", "Steady-state concentration during infusion"],
        ["DL = Css × Vd", "Loading dose"],
        ["R₀ = Css × Cl", "Required infusion rate"],
        ["MRT = AUMC/AUC", "Mean residence time"],
        ["Ka = 0.693/t½a", "Absorption rate constant"],
        ["tmax = ln(Ka/KE)/(Ka−KE)", "Time of peak (EV route)"],
        ["TI = MSC/MEC", "Therapeutic index"],
        ["ClTotal = ClR + ClH + ClO", "Total body clearance (additive)"],
    ],
    col_widths=[3.3, 2.9]
)

doc.add_paragraph()
add_heading(doc, "⚡ QUICK FACT FLASH CARDS", 2)

add_table(doc,
    ["Point to Remember", "Answer"],
    [
        ["First-order t½ is...?", "CONSTANT (independent of initial dose)"],
        ["Zero-order t½ depends on...?", "Initial concentration C₀"],
        ["At tmax, absorption rate = ?", "Elimination rate"],
        ["AUC reflects...?", "EXTENT of drug absorption"],
        ["tmax reflects...?", "RATE of drug absorption"],
        ["Mammillary model: arrangement?", "Peripheral compartments PARALLEL to central compartment"],
        ["Catenary model: arrangement?", "Compartments in SERIES (like train)"],
        ["'Open' in one-compartment open model means?", "Input & output are UNIDIRECTIONAL; drug can be eliminated"],
        ["Steady state reached after...?", "~4–5 half-lives"],
        ["MRT represents 63.2% elimination of...?", "IV Bolus dose"],
        ["RET includes...?", "Lungs, liver, brain, kidney (rapidly equilibrating)"],
        ["SET includes...?", "Muscles, adipose tissue (slowly equilibrating)"],
        ["Vd > 100L means...?", "Extensive tissue distribution/binding"],
        ["Clearance is constant when...?", "Drug follows first-order kinetics"],
        ["Which AUC method is standard?", "Trapezoidal Rule"],
        ["PBPK = ?", "Physiologically-Based Pharmacokinetic models"],
        ["Mixed-order also called?", "Dose-dependent / Nonlinear / Michaelis-Menten kinetics"],
        ["Example of zero-order absorption?", "Controlled release (GITS, transdermal patches)"],
    ],
    col_widths=[3.3, 2.9]
)

doc.add_paragraph()
add_heading(doc, "🧠 MNEMONICS COLLECTION", 2)
add_mnemonic(doc, "'ADME' = Absorption, Distribution, Metabolism, Excretion (pharmacokinetics studies all 4)")
add_mnemonic(doc, "'CTA' = Cmax (intensity), Tmax (rate), AUC (extent) — 3 main bioavailability parameters")
add_mnemonic(doc, "'MAMA is Central' = Mammillary model → peripheral compartments connected to CENTRAL compartment")
add_mnemonic(doc, "'FIZZ' = First-order Is Zero's opposite in t½ — First-order t½ is constant; Zero-order is not")
add_mnemonic(doc, "'PBPK = Physiology Based' = Physiological models based on real anatomy/physiology")
add_mnemonic(doc, "'3 K's of IV Bolus' = KE (rate), t½ (halflife), Cl (clearance) — 3 elimination parameters")
add_mnemonic(doc, "'Loading = Level immediately' = Loading dose achieves Css immediately")
add_mnemonic(doc, "'MRT = Minutes to Residency Termination' = Mean Residence Time = average time drug stays in body")

doc.add_paragraph()
add_heading(doc, "📋 FREQUENTLY ASKED EXAM QUESTIONS", 2)

add_table(doc,
    ["Topic", "Marks", "Frequency"],
    [
        ["One-compartment open model — IV bolus (definition, assumptions, equations, graph)", "10", "★★★★★"],
        ["Classification of pharmacokinetic models", "10/5", "★★★★★"],
        ["Zero-order vs first-order kinetics (comparison + formulas)", "10/5", "★★★★★"],
        ["Cmax, tmax, AUC — define and explain", "5/2", "★★★★★"],
        ["Pharmacokinetic parameters — Vd, Cl, t½, KE, Ka", "10/5", "★★★★☆"],
        ["Mammillary vs Catenary model", "5", "★★★★☆"],
        ["IV infusion with loading dose", "5/10", "★★★★☆"],
        ["Non-compartmental analysis / MRT", "5", "★★★☆☆"],
        ["AUC calculation methods", "5/2", "★★★☆☆"],
        ["Physiological (PBPK) models", "5", "★★★☆☆"],
        ["Mixed-order / nonlinear kinetics", "5/2", "★★★☆☆"],
        ["MEC, MSC, Therapeutic Index, Therapeutic Window", "2/5", "★★★★☆"],
    ],
    col_widths=[3.5, 0.8, 1.9]
)

# ─────────────────────────────────────────────
# FINAL SAVE
# ─────────────────────────────────────────────
output_path = r'R:\Phaiml\Biopharmaceutics_Unit3_ExamNotes.docx'
doc.save(output_path)
print(f"SUCCESS! Notes saved to: {output_path}")
