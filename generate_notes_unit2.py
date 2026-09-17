from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

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

def add_heading(doc, text, level=1):
    colors = {
        1: (0x1A, 0x73, 0xE8),
        2: (0xD6, 0x28, 0x28),
        3: (0x18, 0x80, 0x38),
        4: (0x7B, 0x1F, 0xA2),
    }
    size_map = {1: 16, 2: 14, 3: 13, 4: 12}
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(size_map.get(level, 12))
    run.font.color.rgb = RGBColor(*colors.get(level, (0,0,0)))
    return p

def add_bullet(doc, text, bold_prefix=None, indent=0):
    p = doc.add_paragraph(style='List Bullet')
    if indent > 0:
        p.paragraph_format.left_indent = Inches(0.25 * indent)
    if bold_prefix:
        r1 = p.add_run(bold_prefix + ": ")
        r1.bold = True
        r1.font.size = Pt(10.5)
        r2 = p.add_run(text)
        r2.font.size = Pt(10.5)
    else:
        run = p.add_run(text)
        run.font.size = Pt(10.5)
    return p

def add_formula(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0xBF, 0x36, 0x00)
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
        for row in table.rows:
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

# ─────────────────────────────────────────────
set_page_margins(doc)

# ═══════════════════════════════════════════════════════════
# COVER PAGE
# ═══════════════════════════════════════════════════════════
doc.add_paragraph()
doc.add_paragraph()
add_title(doc, "BIOPHARMACEUTICS & PHARMACOKINETICS", 24, color=(0x1A, 0x73, 0xE8))
add_title(doc, "UNIT 2 — EXAM-READY NOTES", 20, color=(0xD6, 0x28, 0x28))
add_title(doc, "B. Pharmacy | Semester 6", 14, color=(0x18, 0x80, 0x38), bold=False)
doc.add_paragraph()
add_title(doc, "📚 Topics Covered:", 13, color=(0x37, 0x47, 0x51), bold=True)
add_title(doc, "Drug Elimination • Drug Metabolism • Renal Excretion\nFactors Affecting Renal Excretion • Renal Clearance • Non-Renal Excretion\nBioavailability & Bioequivalence • BCS • IVIVC • Enhancement of Bioavailability", 11, color=(0x37, 0x47, 0x51), bold=False)
doc.add_paragraph()
add_title(doc, "Optimized for: 10-mark | 5-mark | 2-mark answers", 11, color=(0x7B, 0x1F, 0xA2), bold=True)
add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 1: ELIMINATION & DRUG METABOLISM
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 1: DRUG ELIMINATION & METABOLISM", 1)
doc.add_paragraph()

add_heading(doc, "1.1 Quick Definitions", 2)
add_bullet(doc, "Elimination: Irreversible loss of drug from the body. Occurs via: (1) Biotransformation + (2) Excretion.", bold_prefix="📌 Elimination")
add_bullet(doc, "Biotransformation (= Metabolism): Chemical conversion of one form to another, usually enzymatically. Excludes chemical instability.", bold_prefix="Biotransformation")
add_bullet(doc, "Duration and intensity of action depend on: Rate of tissue redistribution + Rate of elimination.", bold_prefix="Key Point")

doc.add_paragraph()
add_heading(doc, "1.2 Outcomes of Drug Metabolism", 2)
add_table(doc,
    ["Outcome", "Description", "Example"],
    [
        ["Pharmacological INACTIVATION", "Most common. Metabolites have little/no activity.", "Most drugs → inactive metabolites"],
        ["Equal Activity", "Metabolites retain similar pharmacological activity.", "Diazepam → Desmethyldiazepam"],
        ["Toxicological ACTIVATION", "Rare. Metabolites have high tissue reactivity (toxic).", "Paracetamol overdose → NAPQI (toxic)"],
        ["Pharmacological ACTIVATION (Prodrug)", "Inactive drug converted to active form.", "Enalapril → Enalaprilat (active)"],
    ],
    col_widths=[2.0, 2.5, 2.0]
)

doc.add_paragraph()
add_heading(doc, "1.3 Sites of Drug Metabolism", 2)
add_bullet(doc, "PRIMARY SITE: Liver (richest in drug-metabolising enzymes)", bold_prefix="📌")
add_bullet(doc, "Decreasing order of drug-metabolising ability:")
add_formula(doc, "Liver > Lungs > Kidneys > Intestine > Placenta > Adrenals > Skin")
add_bullet(doc, "Extrahepatic metabolism: Minor importance; lower levels of drug-metabolising enzymes in other tissues.")

doc.add_paragraph()
add_heading(doc, "1.4 Drug-Metabolising Enzymes", 2)
add_table(doc,
    ["Feature", "Microsomal Enzymes", "Non-Microsomal Enzymes"],
    [
        ["Location", "Endoplasmic reticulum (ER) of liver cells; microsomes are ER fragments", "Cytoplasm (soluble) + Mitochondria (not ER)"],
        ["Reactions catalysed", "Oxidation, Reduction, Hydrolysis, Glucuronidation", "Few oxidative; Reduction, Hydrolysis, Conjugation (except glucuronidation)"],
        ["Specificity", "Non-specific; broad range of drugs", "Non-specific"],
        ["Importance", "Majority of drug biotransformation reactions", "Minority of reactions"],
    ],
    col_widths=[1.5, 2.5, 2.5]
)

doc.add_paragraph()
add_heading(doc, "1.5 Phases of Drug Metabolism (★★★ Most Important)", 2)
add_table(doc,
    ["Feature", "Phase I Reactions", "Phase II Reactions"],
    [
        ["Also called", "Functionalisation reactions", "Conjugation (synthetic) reactions"],
        ["Type of reactions", "Oxidation, Reduction, Hydrolysis", "Conjugation: Glucuronidation, Sulfation, Glycine conjugation, Glutathione conjugation, Acetylation, Methylation"],
        ["What happens", "Introduces/unmasks polar functional groups (-OH, -COOH, -NH₂, -SH) on lipid-soluble drug", "Covalent attachment of small polar endogenous molecules to -OH, -COOH, -NH₂, -SH groups"],
        ["Product", "More polar metabolite (can undergo Phase II)", "Highly water-soluble conjugates"],
        ["Outcome", "May activate, inactivate or maintain drug activity", "Almost always INACTIVATION; ready for renal/biliary excretion"],
        ["Enzymes", "Mainly microsomal (CYP450 enzymes)", "Both microsomal (glucuronidation) and non-microsomal"],
        ["Sequence", "Generally precedes Phase II", "Follows Phase I"],
    ],
    col_widths=[1.5, 2.7, 2.3]
)

add_highlight_box(doc, "EXAM TIP: Phase I = Functionalisation (adds/unmasks polar groups). Phase II = Conjugation (makes it water-soluble for excretion). Phase I precedes Phase II.", fill='E3F2FD', text_color=(0x0D, 0x47, 0xA1))
add_mnemonic(doc, "'FIRE COMES FIRST' = Phase I (Functionalisation) before Phase II (Conjugation)")
add_mnemonic(doc, "'OxRHy' = Phase I reactions: Oxidation, Reduction, Hydrolysis")
add_mnemonic(doc, "'GAS GAMe' = Phase II conjugations: Glucuronidation, Acetylation, Sulfation, Glycine, Acetylation, Methylation")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 2: RENAL EXCRETION OF DRUGS
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 2: RENAL EXCRETION OF DRUGS", 1)
doc.add_paragraph()

add_heading(doc, "2.1 Quick Definition & Key Points", 2)
add_bullet(doc, "Almost ALL drugs and metabolites are excreted by kidneys to some extent.")
add_bullet(doc, "Basic functional unit of kidney = NEPHRON (1 million per kidney).")
add_bullet(doc, "Nephron components: Glomerulus → Proximal tubule → Loop of Henle → Distal tubule → Collecting tubule.")
add_bullet(doc, "Drugs excreted in urine must be: Water-soluble, Non-volatile, Small molecular size (<500 Da), Slowly metabolised.")
add_bullet(doc, "Example of exclusively renal-excreted drug: Gentamicin.")

doc.add_paragraph()
add_heading(doc, "2.2 Three Processes of Renal Excretion (★★★★★ Most Exam Important)", 2)
add_formula(doc, "Rate of Excretion = Rate of Filtration + Rate of Secretion − Rate of Reabsorption")

add_table(doc,
    ["Feature", "Glomerular Filtration (GF)", "Active Tubular Secretion (ATS)", "Tubular Reabsorption (TR)"],
    [
        ["Location", "Glomerulus", "Proximal tubule (mainly)", "All along renal tubules"],
        ["Process type", "Passive, non-selective, unidirectional", "Active (carrier-mediated, energy-requiring)", "Active OR Passive"],
        ["Driving force", "Hydrostatic pressure of blood", "Carrier system (against concentration gradient)", "Concentration gradient (passive); Active carriers (active)"],
        ["Drugs filtered/secreted", "Ionized + unionized; EXCEPT plasma protein-bound", "Acidic drugs (penicillin, salicylates) & Basic drugs (morphine, mecamylamine)", "Lipophilic, unionized drugs (passive); Endogenous: glucose, electrolytes (active)"],
        ["GFR", "120–130 mL/min (10% of renal blood flow)", "Excretion rate > GFR (indicates secretion)", "Excretion rate < GFR (indicates reabsorption)"],
        ["Effect on excretion", "INCREASES drug in urine (facilitates excretion)", "INCREASES drug in urine (facilitates excretion)", "DECREASES drug in urine (retains drug; ↑ t½)"],
        ["pH effect", "Not affected by pH", "Not affected by pH or protein binding", "HIGHLY affected by urine pH and pKa"],
        ["Marker drugs", "Creatinine, Inulin", "Penicillin (organic anions); PAH", "Glucose (active); Lipophilic drugs (passive)"],
    ],
    col_widths=[1.3, 1.6, 1.8, 1.8]
)

doc.add_paragraph()
add_heading(doc, "2.3 Passive Tubular Reabsorption — pH Dependency", 2)
add_bullet(doc, "Most drugs are weak electrolytes (weak acids/weak bases).")
add_bullet(doc, "Diffusion through lipid tubular membrane depends on DEGREE OF IONISATION.")
add_bullet(doc, "Only UNIONIZED (lipophilic) form is reabsorbed passively.")
add_bullet(doc, "Three factors governing ionisation and reabsorption:")
add_bullet(doc, "1. pH of urine (varies 4.5 – 7.5)", indent=1)
add_bullet(doc, "2. pKa of the drug", indent=1)
add_bullet(doc, "3. Urine flow rate", indent=1)

add_formula(doc, "Henderson-Hasselbalch (Weak Acid):  pH = pKa + log [ionized]/[unionized]")
add_formula(doc, "Henderson-Hasselbalch (Weak Base):  pH = pKa + log [unionized]/[ionized]")
add_formula(doc, "% ionized (weak acid) = 10^(pH−pKa) / (1 + 10^(pH−pKa)) × 100")

add_table(doc,
    ["Drug Type", "Alkaline urine (pH ↑)", "Acidic urine (pH ↓)"],
    [
        ["Weak ACID", "MORE ionized → LESS reabsorbed → MORE excreted", "LESS ionized → MORE reabsorbed → LESS excreted"],
        ["Weak BASE", "LESS ionized → MORE reabsorbed → LESS excreted", "MORE ionized → LESS reabsorbed → MORE excreted"],
        ["Clinical Use", "Alkalinize urine for acidic drug overdose (e.g., aspirin poisoning → give NaHCO₃)", "Acidify urine for basic drug overdose (e.g., amphetamine poisoning → give NH₄Cl)"],
    ],
    col_widths=[1.2, 2.7, 2.6]
)

add_highlight_box(doc, "pH PARTITION TRICK: To INCREASE excretion of acidic drug → alkalinize urine. To INCREASE excretion of basic drug → acidify urine.", fill='FFF9C4', text_color=(0x7B, 0x60, 0x00))
add_mnemonic(doc, "'TRAP THE ION' = Ionized drugs are TRAPPED in tubular lumen (cannot cross membrane) → excreted")
add_mnemonic(doc, "'ACID-ALKALINE-OUT' = Acidic drug excreted in ALKaline urine; Basic drug excreted in ACIDic urine")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 3: FACTORS AFFECTING RENAL EXCRETION
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 3: FACTORS AFFECTING RENAL EXCRETION", 1)
doc.add_paragraph()

add_heading(doc, "3.1 Classification of Factors", 2)
add_table(doc,
    ["Factor", "Details"],
    [
        ["1. Physicochemical properties of drug", "Molecular size (<300 Da → easily filtered); pKa (governs ionization & reabsorption); Lipid solubility (high lipophilicity → more reabsorption → less excretion); Stereochemical nature (enantiomers may show differential filtration)"],
        ["2. Plasma drug concentration", "GF and passive reabsorption: directly related to plasma conc. Active secretion/reabsorption: shows saturation kinetics at high conc."],
        ["3. Distribution & binding characteristics", "Plasma protein-bound drug → NOT filtered (acts as macromolecule). High Vd → poor urinary excretion. Drugs restricted to blood compartment → higher excretion rate."],
        ["4. Urine pH", "Affects ionization of weak acids/bases → alters passive reabsorption (see Chapter 2)"],
        ["5. Blood flow to kidneys", "Important for GF and actively secreted drugs. ↑ renal blood flow → ↑ contact with secretory sites → ↑ elimination (perfusion rate-limited clearance)"],
        ["6. Biological factors", "Age (newborns: 30-40% lower GFR; elderly: reduced GFR, prolonged t½); Sex (renal excretion ~10% lower in females); Genetic factors; Circadian rhythm"],
        ["7. Drug interactions", "Displacement of protein binding → ↑ free drug → ↑ filtration. Competition for active secretion carriers. Changes in urine pH. Forced diuresis."],
        ["8. Disease states", "Renal dysfunction: ↓ GFR → ↓ drug elimination → ↑ t½ → drug accumulation → toxicity. Uremia: impaired GFR + fluid/protein metabolite accumulation."],
    ],
    col_widths=[2.0, 4.5]
)

doc.add_paragraph()
add_heading(doc, "3.2 Forced Diuresis (Clinical Application)", 2)
add_bullet(doc, "Forced Diuresis: Increase in urine flow by large fluid intake or administration of mannitol/other diuretics.")
add_bullet(doc, "Used in DRUG OVERDOSE treatment to enhance elimination.")
add_bullet(doc, "Effective ONLY for drugs whose reabsorption is pH-sensitive (weak acids, weak bases).")
add_bullet(doc, "Polar drugs (not reabsorbed) are unaffected by urine flow rate — only produce more dilute urine.")
add_bullet(doc, "Examples: NaHCO₃ → alkaline urine → ↑ aspirin excretion; NH₄Cl → acidic urine → ↑ amphetamine excretion")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 4: RENAL CLEARANCE
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 4: RENAL CLEARANCE", 1)
doc.add_paragraph()

add_heading(doc, "4.1 Quick Definition", 2)
add_bullet(doc, "Clearance was FIRST introduced to describe renal excretion of endogenous compounds to measure kidney function.")
add_bullet(doc, "Renal Clearance (ClR): Volume of blood/plasma completely cleared of unchanged drug by the kidney per unit time.")
add_bullet(doc, "Unit: mL/min")
add_bullet(doc, "Clearance is CONSTANT for any given plasma drug concentration.")

add_formula(doc, "Clearance (Cl) = Rate of Elimination / Plasma Drug Concentration")
add_formula(doc, "Renal Clearance (ClR) = Rate of urinary excretion / Plasma drug concentration (C)")
add_formula(doc, "ClR = (Rate of filtration + Rate of secretion − Rate of reabsorption) / C")

doc.add_paragraph()
add_heading(doc, "4.2 Renal Clearance Ratio", 2)
add_formula(doc, "Renal Clearance Ratio = ClR of drug / ClR of Creatinine")
add_bullet(doc, "Renal clearance ratio > 1 → Drug is SECRETED (in addition to filtration)")
add_bullet(doc, "Renal clearance ratio = 1 → Drug is only FILTERED (not secreted or reabsorbed)")
add_bullet(doc, "Renal clearance ratio < 1 → Drug is REABSORBED (after filtration)")
add_bullet(doc, "Creatinine is used as a MARKER because it is exclusively filtered (not secreted or reabsorbed). GFR = Creatinine clearance ≈ 120–130 mL/min.")

doc.add_paragraph()
add_heading(doc, "4.3 Types of Clearance", 2)
add_table(doc,
    ["Type", "Definition", "Formula"],
    [
        ["Renal Clearance", "Volume of plasma cleared of drug by kidney per unit time", "ClR = Rate of urinary excretion / C"],
        ["Hepatic Clearance", "Volume of plasma cleared by liver per unit time", "ClH = Rate of hepatic elimination / C"],
        ["Biliary Clearance", "Ability of liver to excrete drug in bile", "ClBile = Biliary excretion rate / C"],
        ["Total Body Clearance", "Sum of all organ clearances", "ClTotal = ClR + ClH + Clother = Dose/AUC"],
        ["Non-renal Clearance", "Clearance by all organs other than kidney", "ClNR = ClTotal − ClR"],
    ],
    col_widths=[1.7, 2.5, 2.3]
)

add_highlight_box(doc, "EXAM TIP: Total Body Clearance is ADDITIVE — sum of all organ clearances. Vd relates plasma conc to AMOUNT in body; Clearance relates plasma conc to RATE of elimination.", fill='E8F5E9', text_color=(0x1B, 0x5E, 0x20))

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 5: NON-RENAL ROUTES OF DRUG EXCRETION
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 5: NON-RENAL (EXTRARENAL) ROUTES OF EXCRETION", 1)
doc.add_paragraph()

add_heading(doc, "5.1 Routes Summary Table (★★★★)", 2)
add_table(doc,
    ["Route", "Key Drug Features", "Examples / Special Points"],
    [
        ["1. Biliary Excretion", "Molecular weight threshold: >300 Da (anions) / >300 Da (cations). Phase II metabolites (glucuronides) preferentially excreted. Polarity ↑ = biliary excretion ↑", "Chloramphenicol, morphine, indomethacin. Marker: Sulfobromophthalein (excreted in 30 min at normal hepatic function)"],
        ["2. Pulmonary Excretion", "Gaseous/volatile substances excreted by simple diffusion. NOT metabolites — only intact gaseous drugs excreted.", "General anesthetics (Halothane). Alcohol (high blood solubility → slow pulmonary excretion). Factors: pulmonary blood flow, respiration rate, solubility."],
        ["3. Salivary Excretion", "pH of saliva: 5.8–8.4. Unionized lipid-soluble drugs excreted passively.", "Caffeine, Phenytoin, Theophylline. Bitter aftertaste = sign of drug excretion. Basic drugs can inhibit saliva → dry mouth."],
        ["4. Mammary (Milk) Excretion", "pH of milk: 6.4–7.6. 0.5–1 L milk/day in lactating mothers. Amount in milk <1% — rarely toxic.", "Barbiturates, morphine (may cause infant toxicity). Tetracycline → tooth discoloration. Nicotine in milk of smoking mothers. High protein-bound drugs (e.g., diazepam) → less in milk."],
        ["5. Skin/Sweat Excretion", "Follows pH partition hypothesis. May cause urticaria/dermatitis.", "Benzoic acid, salicylic acid, alcohol. Heavy metals: lead, mercury, arsenic."],
        ["6. Gastrointestinal Excretion", "Occurs mainly after parenteral administration. Water-soluble/ionized forms of weak acids/bases excreted. Drugs reabsorbed and undergo enterohepatic recycling.", "Nicotine, quinine (excreted in stomach)"],
        ["7. Genital Excretion", "Reproductive tract/genital secretions may contain drugs.", "Some drugs detected in semen"],
    ],
    col_widths=[1.5, 2.7, 2.3]
)

doc.add_paragraph()
add_heading(doc, "5.2 Biliary Excretion — Classification of Compounds", 2)
add_table(doc,
    ["Group", "Bile/Plasma Concentration Ratio", "Examples"],
    [
        ["Group A", "≈ 1", "Sodium, potassium, chloride ions, glucose"],
        ["Group B", "> 1 (10 to 1000)", "Bile salts, bilirubin glucuronide, creatinine, sulphobromophthalein conjugates"],
        ["Group C", "< 1", "Sucrose, inulin, phosphates, phospholipids, mucoproteins"],
    ],
    col_widths=[1.2, 2.5, 2.8]
)

add_highlight_box(doc, "ENTEROHEPATIC RECYCLING: Drug excreted in bile → reaches intestine → reabsorbed → back to liver. Prolongs drug action. Example: oral contraceptives.", fill='FFF9C4', text_color=(0x7B, 0x60, 0x00))
add_mnemonic(doc, "'BSP GPMS' = Biliary, Salivary, Pulmonary, Mammary, GI, Skin — 6 non-renal excretion routes + Genital = 7 total")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 6: BIOAVAILABILITY
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 6: BIOAVAILABILITY", 1)
doc.add_paragraph()

add_heading(doc, "6.1 Quick Definition", 2)
add_bullet(doc, "Bioavailability: Rate and EXTENT (amount) of absorption of UNCHANGED drug from its dosage form into the systemic circulation.", bold_prefix="📌 Definition")
add_bullet(doc, "Also called: Physiological availability / Biological availability.")
add_bullet(doc, "It is an ABSOLUTE term.")
add_bullet(doc, "Route of administration influence on bioavailability:")
add_formula(doc, "Parenteral > Oral > Rectal > Topical")

doc.add_paragraph()
add_heading(doc, "6.2 Factors Affecting Bioavailability (When Dose is Same)", 2)
add_bullet(doc, "Pharmaceutical factors: Physicochemical properties of drug + Characteristics of dosage form.")
add_bullet(doc, "Patient-related factors: Age, sex, disease state, gastric emptying, GI pH, etc.")
add_bullet(doc, "Route of administration.")

doc.add_paragraph()
add_heading(doc, "6.3 Absolute vs Relative Bioavailability (★★★★★)", 2)
add_table(doc,
    ["Feature", "Absolute Bioavailability (F)", "Relative Bioavailability (Fr)"],
    [
        ["Definition", "Systemic availability of drug after oral (or other EV) route compared to IV administration", "Systemic availability compared to an oral standard (solution/suspension) of the same drug"],
        ["Reference standard", "IV dose (100% bioavailability) — gold standard", "Oral solution/suspension of same drug"],
        ["Symbol", "F", "Fr"],
        ["Purpose", "Characterizes drug's inherent absorption from IV site; measures absolute fraction absorbed", "Characterizes absorption of drug from its formulation"],
        ["Formula", "F = (AUCoral × DIV) / (AUCIV × Doral)", "Fr = (AUCtest × Dstd) / (AUCstd × Dtest)"],
        ["Expression", "Percentage (%)", "Percentage (%)"],
        ["IV value", "100% (no absorption step)", "Not used"],
    ],
    col_widths=[1.5, 2.5, 2.5]
)

add_highlight_box(doc, "IV administration = 100% bioavailability (bypasses absorption). IM can also be used as reference if drug is poorly water-soluble.", fill='E3F2FD', text_color=(0x0D, 0x47, 0xA1))

doc.add_paragraph()
add_heading(doc, "6.4 Objectives of Bioavailability Studies", 2)
add_bullet(doc, "Early drug development: Evidence of therapeutic utility of new drug entities.")
add_bullet(doc, "Determine influence of excipients, patient factors, and drug interactions on absorption efficiency.")
add_bullet(doc, "Development of new formulations of existing drugs.")
add_bullet(doc, "Quality control during marketing: Influence of processing, storage, stability on absorption.")
add_bullet(doc, "Comparison of drug availability from different dosage forms or different manufacturers.")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 7: MEASUREMENT OF BIOAVAILABILITY
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 7: MEASUREMENT OF BIOAVAILABILITY", 1)
doc.add_paragraph()

add_heading(doc, "7.1 Classification of Methods", 2)
add_table(doc,
    ["Method Category", "Sub-type", "Basis"],
    [
        ["I. Pharmacokinetic Methods (Indirect)", "a. Plasma level-time studies", "Assumes plasma conc profile reflects therapeutic effectiveness"],
        ["I. Pharmacokinetic Methods (Indirect)", "b. Urinary excretion studies", "Urinary excretion of unchanged drug ∝ plasma concentration"],
        ["II. Pharmacodynamic Methods (Direct)", "a. Acute pharmacological response", "Measure acute pharmacological effect (ECG, EEG, pupil diameter) vs time"],
        ["II. Pharmacodynamic Methods (Direct)", "b. Therapeutic response", "Observe clinical response in patients with disease"],
    ],
    col_widths=[2.3, 2.0, 2.2]
)

doc.add_paragraph()
add_heading(doc, "7.2 Plasma Level-Time Studies (Most Common Method)", 2)
add_bullet(doc, "Based on DIRECT RELATIONSHIP between plasma drug concentration and drug at site of action.")
add_bullet(doc, "Three KEY parameters measured:")
add_table(doc,
    ["Parameter", "What it measures", "Relationship"],
    [
        ["Cmax (peak plasma conc.)", "Whether drug is sufficiently absorbed for therapeutic response", "Function of BOTH rate AND extent of absorption. ↑ dose or ↑ absorption rate → ↑ Cmax"],
        ["tmax (time to peak)", "Rate of absorption", "↑ absorption rate → ↓ tmax (peak occurs earlier)"],
        ["AUC", "Extent of absorption / total drug reaching systemic circulation", "↑ extent of absorption → ↑ AUC"],
    ],
    col_widths=[1.8, 2.3, 2.4]
)

add_formula(doc, "AUC (trapezoidal) = Σ (Cn + Cn+1)/2 × (tn+1 − tn) + AUCextrapolated")
add_formula(doc, "AUCextrapolated = Clast / KE")

doc.add_paragraph()
add_heading(doc, "Study Design:", 3)
add_bullet(doc, "Single dose study: Blood samples for 2–3 biological half-lives. At least 3 points on ascending part of curve for accurate Ka.")
add_bullet(doc, "Multiple dose study: Drug for at least 5 half-lives with dosing interval ≥ t½ to reach steady-state.")

doc.add_paragraph()
add_heading(doc, "7.3 Urinary Excretion Studies", 2)
add_bullet(doc, "Based on: Urinary excretion of unchanged drug is directly proportional to plasma concentration.")
add_bullet(doc, "Applicable when: At least 20% of administered dose is excreted UNCHANGED in urine.")
add_bullet(doc, "Best for: Drugs extensively excreted unchanged (e.g., thiazide diuretics, urinary antiseptics like nitrofurantoin).")
add_bullet(doc, "Collection: Urine samples at regular intervals for 7 half-lives.")
add_bullet(doc, "Criteria: Total emptying of bladder at each collection; frequent early sampling; fraction excreted unchanged must remain constant.")

add_table(doc,
    ["Urinary Parameter", "Analogy to Plasma Parameter", "Clinical Meaning"],
    [
        ["(dXu/dt)max — Maximum urinary excretion rate", "Cmax", "↑ absorption rate → ↑ (dXu/dt)max"],
        ["(tu)max — Time for maximum excretion rate", "tmax", "↓ as absorption rate increases"],
        ["Xu∞ — Cumulative amount excreted in urine", "AUC", "↑ as extent of absorption increases"],
    ],
    col_widths=[2.8, 1.5, 2.2]
)

doc.add_paragraph()
add_heading(doc, "7.4 Pharmacodynamic Methods", 2)
add_bullet(doc, "Acute pharmacological response: ECG/EEG changes, pupil diameter, blood pressure vs time. Pharmacological effect-time curve constructed. Measurement for at least 3 half-lives.")
add_bullet(doc, "Therapeutic response: Clinical response in patients. Least preferred — very difficult to quantify accurately.")
add_bullet(doc, "Disadvantage of PD methods: Response is variable; active metabolite may give response not proportional to parent drug concentration.")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 8: IN VITRO DISSOLUTION TESTING
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 8: IN VITRO DRUG DISSOLUTION TESTING", 1)
doc.add_paragraph()

add_heading(doc, "8.1 Factors in Dissolution Test Design", 2)
add_bullet(doc, "Apparatus factors: Design, size, shape of container, nature and speed of agitation.")
add_bullet(doc, "Dissolution fluid factors: Composition, viscosity, volume, temperature (37°C), sink vs non-sink conditions.")
add_bullet(doc, "Process parameters: Method of dosage form introduction, sampling technique, fluid changes.")

doc.add_paragraph()
add_heading(doc, "8.2 Types of Dissolution Apparatus (All 7 — Exam Important)", 2)
add_table(doc,
    ["Apparatus No.", "Name", "Key Feature", "Used For"],
    [
        ["Apparatus 1", "Rotating Basket Apparatus", "Cylindrical basket (22 mesh) at 2 cm from bottom; 1L hemispherical glass vessel; 37°C water bath. SS316 metal parts.", "General solid dosage forms (tablets, capsules)"],
        ["Apparatus 2", "Rotating Paddle Apparatus", "Same as App.1 but basket replaced by PADDLE (stirrer). Sinkers recommended for floating forms (capsules). Wire helix for floatable preparations.", "Most common; general solid dosage forms"],
        ["Apparatus 3", "Reciprocating Cylinder", "Cylindrical flat-bottomed glass vessels with reciprocating cylinders.", "Controlled-release bead/pellet formulations"],
        ["Apparatus 4", "Flow-Through Cell Apparatus", "Reservoir + pump forces dissolution medium through cell holding test sample. Closed mode (recirculated) or Open mode (continuous fresh medium = perfect sink).", "Low-solubility drugs; poorly soluble drugs under sink conditions"],
        ["Apparatus 5", "Paddle Over Disc Apparatus", "Apparatus 2 + disc at bottom to hold transdermal product.", "Transdermal products"],
        ["Apparatus 6", "Rotating Cylinder (Cylinder Apparatus)", "SS cylinder instead of basket; sample mounted on inert porous cellulosic material.", "Transdermal products"],
        ["Apparatus 7", "Reciprocating Disc", "Disc-shaped holders on inert porous cellulosic support; reciprocates vertically in dissolution medium.", "Transdermal + non-disintegrating controlled-release oral preparations"],
    ],
    col_widths=[1.0, 1.7, 2.5, 1.3]
)

add_highlight_box(doc, "EXAM TIP: App 1 = Basket; App 2 = Paddle (most widely used); App 4 = Flow-Through (perfect sink); App 5,6,7 = Transdermal products.", fill='E8F5E9', text_color=(0x1B, 0x5E, 0x20))
add_mnemonic(doc, "'BP FPR' = Basket, Paddle, Flow-through, Paddle-over-disc, Rotating cylinder, Reciprocating disc — Apps 1 to 7")

doc.add_paragraph()
add_heading(doc, "8.3 Sink vs Non-Sink Conditions", 2)
add_table(doc,
    ["Condition", "Description", "Apparatus Type"],
    [
        ["Sink conditions", "Drug concentration in dissolution medium is always much less than saturation (drug keeps dissolving freely). Perfect sink = continuous fresh medium.", "Open/Flow-through (App 4)"],
        ["Non-sink conditions", "Fixed volume — drug concentration increases over time. Limited by container volume.", "Closed-compartment (App 1, 2 — beaker type)"],
    ],
    col_widths=[1.5, 3.0, 2.0]
)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 9: IVIVC
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 9: IN VITRO–IN VIVO CORRELATION (IVIVC)", 1)
doc.add_paragraph()

add_heading(doc, "9.1 Definition", 2)
add_bullet(doc, "IVIVC: Predictive mathematical model describing the relationship between an IN VITRO property (rate/extent of dissolution) of a dosage form and an IN VIVO response (plasma drug concentration or amount absorbed).", bold_prefix="📌")
add_bullet(doc, "Main objective: Enable dissolution test to serve as a SURROGATE for in vivo bioavailability studies.")

doc.add_paragraph()
add_heading(doc, "9.2 Applications of IVIVC", 2)
add_bullet(doc, "Ensure batch-to-batch consistency in physiological performance.")
add_bullet(doc, "Tool for developing new dosage form with desired in vivo performance.")
add_bullet(doc, "Validate or set dissolution specifications based on in vivo performance.")

doc.add_paragraph()
add_heading(doc, "9.3 Types/Levels of IVIVC (★★★★★)", 2)
add_table(doc,
    ["Level", "Type", "What is correlated", "Usefulness", "Key Feature"],
    [
        ["Level A", "Highest; Point-to-point correlation", "In vitro dissolution ↔ In vivo rate of absorption (point-by-point)", "HIGHEST — Most useful for regulatory submissions. Dissolution curve serves as surrogate for in vivo performance.", "Best for quality control and formulation changes"],
        ["Level B", "Statistical moment analysis", "Mean in vitro dissolution time ↔ Mean Residence Time (MRT) or mean in vivo dissolution time", "NOT point-to-point; multiple in vivo curves can give same MRT → Cannot justify manufacturing changes or quality control.", "Based on MRT = AUMC/AUC"],
        ["Level C", "Single-point correlation", "One dissolution time point (e.g., t50%) ↔ One PK parameter (AUC, tmax, or Cmax)", "LIMITED — Only useful as formulation development guide or quality control. Cannot fully characterize in vivo profile.", "Single point only"],
        ["Multiple Level C", "Multiple single-point correlations", "Several PK parameters ↔ Amount dissolved at various time points", "Better than Level C but less than Level A", "Combines multiple C correlations"],
    ],
    col_widths=[0.8, 1.3, 2.0, 1.7, 1.7]
)

add_highlight_box(doc, "EXAM TIP: Level A IVIVC is the BEST (highest usefulness). It is a point-to-point correlation between in vitro dissolution and in vivo absorption rates.", fill='FFEBEE', text_color=(0xC6, 0x28, 0x28))

doc.add_paragraph()
add_heading(doc, "9.4 BCS and IVIVC Expectations", 2)
add_table(doc,
    ["BCS Class", "Solubility", "Permeability", "IVIVC Expected?"],
    [
        ["Class I", "High", "High", "Level A IVIVC expected (dissolution rate-limited → good IVIVC)"],
        ["Class II", "Low", "High", "Level A IVIVC expected (dissolution is rate-limiting step)"],
        ["Class III", "High", "Low", "Level C IVIVC (permeability limits; dissolution not rate-limiting)"],
        ["Class IV", "Low", "Low", "Little or no IVIVC"],
    ],
    col_widths=[1.0, 1.2, 1.2, 4.1]
)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 10: BIOEQUIVALENCE
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 10: BIOEQUIVALENCE STUDIES", 1)
doc.add_paragraph()

add_heading(doc, "10.1 Types of Equivalence (★★★★)", 2)
add_table(doc,
    ["Type", "Definition"],
    [
        ["Chemical Equivalence", "Two or more drug products contain the SAME labelled chemical substance as active ingredient in the SAME AMOUNT."],
        ["Pharmaceutical Equivalence", "Identical in strength, quality, purity, content uniformity and disintegration/dissolution characteristics."],
        ["Therapeutic Equivalence", "Contain same active ingredient AND produce identical pharmacological effects and control disease to same extent."],
        ["Bioequivalence (BE)", "Two drug products that produce similar bioavailability (similar AUC, Cmax, tmax) so the pharmacokinetic/pharmacodynamic parameters are essentially the same."],
    ],
    col_widths=[2.0, 4.5]
)

doc.add_paragraph()
add_heading(doc, "10.2 When are Bioequivalence Studies Needed (In Vivo)?", 2)
add_bullet(doc, "Indicated for serious conditions requiring assured therapeutic response.")
add_bullet(doc, "Drug has narrow therapeutic margin (NTI drugs — e.g., phenytoin, digoxin, warfarin).")
add_bullet(doc, "Complicated PK: absorption <70%, absorption window present, nonlinear kinetics, presystemic elimination >70%.")
add_bullet(doc, "Unfavourable physicochemical properties: low solubility, metastable polymorphs, instability.")
add_bullet(doc, "Documented evidence of bioavailability problems.")

doc.add_paragraph()
add_heading(doc, "10.3 Biowaivers (When In Vivo BE Not Required)", 2)
add_bullet(doc, "Drug product differs only in STRENGTH (linear PK, same qualitative composition, same manufacturer).")
add_bullet(doc, "Drug product has been slightly reformulated (irrelevant to bioavailability).")
add_bullet(doc, "Product is in solution form (same concentration, no excipients affecting absorption).")
add_bullet(doc, "Acceptable IVIVC established AND similar in vitro dissolution rate.")
add_bullet(doc, "Product for topical use (local effect only).")
add_bullet(doc, "Product for oral use but NOT intended to be absorbed (antacids, radio-opaque media).")
add_bullet(doc, "Product administered by inhalation as gas/vapour.")

doc.add_paragraph()
add_heading(doc, "10.4 BCS Classification System (★★★★★)", 2)
add_table(doc,
    ["BCS Class", "Solubility", "Permeability", "Absorption", "Drug Examples"],
    [
        ["Class I", "High", "High", "Well absorbed (rate-limited by gastric emptying)", "Diltiazem, Propranolol, Metoprolol"],
        ["Class II", "Low", "High", "Variable (dissolution rate-limited)", "Nifedipine, Carbamazepine, Naproxen"],
        ["Class III", "High", "Low", "Variable (permeability-limited)", "Insulin, Metformin, Cimetidine"],
        ["Class IV", "Low", "Low", "Poorly absorbed (both limitations)", "Taxol, Chlorothiazide, Furosemide"],
    ],
    col_widths=[1.0, 1.0, 1.0, 2.2, 2.3]
)

add_formula(doc, "BCS Biowaiver possible for Class I & III drugs under specific conditions (BCS-based biowaivers)")
add_highlight_box(doc, "BCS EXAM TRICK: Class I = Best absorption. Class IV = Worst absorption. Class II = dissolution-limited. Class III = permeability-limited.", fill='FFF9C4', text_color=(0x7B, 0x60, 0x00))
add_mnemonic(doc, "'High-High, Low-High, High-Low, Low-Low' = BCS I, II, III, IV (Solubility-Permeability pairs)")
add_mnemonic(doc, "'DILTIAZEM Is one' = Class I (Diltiazem), 'NIFEDIPINE Is two' = Class II, 'METFORMIN Is three', 'FUROSEMIDE Is four'")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# CHAPTER 11: ENHANCEMENT OF BIOAVAILABILITY
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📖 CHAPTER 11: METHODS FOR ENHANCEMENT OF BIOAVAILABILITY", 1)
doc.add_paragraph()

add_heading(doc, "11.1 Approaches for Enhancement", 2)
add_bullet(doc, "Pharmaceutical Approach (most detailed in syllabus):")
add_bullet(doc, "Enhancement of drug SOLUBILITY/DISSOLUTION RATE", indent=1)
add_bullet(doc, "Enhancement of drug PERMEABILITY", indent=1)
add_bullet(doc, "Enhancement of drug STABILITY", indent=1)
add_bullet(doc, "Enhancement of GI RETENTION time", indent=1)

doc.add_paragraph()
add_heading(doc, "11.2 Methods to Enhance Drug Solubility / Dissolution Rate (★★★★★)", 2)

add_table(doc,
    ["Method", "Mechanism/Description", "Examples"],
    [
        ["1. Micronization", "Reduce particle size to 1–10 microns (micro milling). ↑ surface area → ↑ dissolution. Methods: Spray drying, air attrition/fluid energy/jet mill.", "Griseofulvin, steroidal & sulpha drugs"],
        ["2. Nanonization", "Convert drug to nanocrystals (200–600 nm). Three technologies: Pearl milling, Wet homogenization, Non-aqueous homogenization. Nanosuspension = nanocrystals in water.", "Amphotericin B"],
        ["3. Supercritical Fluid (SCF) Recrystallization", "Drug dissolved in SCF (T & P > critical values → liquid+gas properties). On pressure change, drug recrystallizes at greatly reduced particle size.", "Various poorly soluble drugs"],
        ["4. Spray Freezing into Liquid (SFL)", "Atomize drug+excipient solution into cryogenic liquid (liquid N₂) or compressed gas. Lyophilize frozen particles → amorphous nanostructured aggregates with high surface area + excellent wettability.", "High surface area powders"],
        ["5. EPAS (Evaporative Precipitation into Aqueous Solution)", "Drug dissolved in low-boiling organic solvent → heated under pressure → sprayed into heated aqueous solution containing surfactants → nanoparticles formed rapidly.", "Lipophilic drugs"],
        ["6. Use of Surfactants", "Below CMC: promote wetting and penetration of dissolution fluid into solid drug. Above CMC: drug trapped in micelle → ↓ bioavailability (avoid).", "Polysorbates (nonionic); Spiranolactone"],
        ["7. Salt Forms", "Convert drug to salt → improved solubility. Minimum 3 unit pKa difference between drug and counter ion needed for stable salts.", "Alkali metal salts of penicillins (acidic); Strong acid salts of atropine (basic)"],
        ["8. Precipitation Inhibitors", "Prevent supersaturation from precipitating by inert polymers that form steric barrier to crystallization.", "HPMC, PVP, PVA, PEG"],
        ["9. pH Microenvironment Alteration", "In situ salt formation, addition of buffers to formulation.", "Buffered aspirin tablets"],
        ["10. Amorphs, Anhydrates, Polymorphs", "Amorphs > metastable polymorphs in solubility. Anhydrates more soluble than hydrates. Solvates more soluble than non-solvates.", "Select most soluble crystal form"],
        ["11. Solid Solutions (Melts)", "Drug molecularly dispersed in solid carrier (molecular dispersion/mixed crystals). Prepared by fusion method (melt together → rapid solidification). Best dissolution among solid dispersion types.", "Griseofulvin–succinic acid"],
        ["12. Eutectic Mixtures", "Two-component system prepared by fusion. Water dissolves carrier leaving drug in microcrystalline state → rapid dissolution.", "Paracetamol-urea, Griseofulvin-urea"],
        ["13. Solid Dispersions", "Active ingredient dispersed in inert solid carrier. Methods: (a) Hot melt, (b) Solvent evaporation, (c) Hot melt extrusion.", "Various BCS Class II drugs"],
        ["14. Cyclodextrin Complexation", "β and γ-cyclodextrins: bucket-shaped oligosaccharides. Hydrophobic cavity traps lipophilic drug → forms inclusion complex → greatly improved aqueous solubility.", "Thiazide diuretics, barbiturates, benzodiazepines, NSAIDs"],
        ["15. Adsorption on Carriers", "Inorganic clays (bentonite) adsorb poorly soluble drugs → maintain max concentration gradient. Rapid release due to weak physical bonding + clay hydration/swelling.", "Griseofulvin, Indomethacin, Prednisone"],
    ],
    col_widths=[1.7, 3.0, 1.8]
)

doc.add_paragraph()
add_heading(doc, "11.3 Enhancement of Drug PERMEABILITY", 2)
add_bullet(doc, "Ion Pairing: Co-administer hydrophilic/polar drug with lipophilic counter ion → more lipophilic ion-pair → improved membrane partitioning. E.g., increases oral BA of atenolol ~2-fold.", bold_prefix="1.")
add_bullet(doc, "Lipid Technologies: Lipid-based formulations for hydrophobic drugs. Mechanisms: enhanced dissolution, bile salt stimulation, reduced gastric emptying, ↑ intestinal membrane permeability, lymphatic uptake (bypass first-pass). Forms: lipid solutions/suspensions, emulsions, microemulsions (SMEDDS), SLN (100–1000 nm), NLC, LDC nanoparticles, liposomes.", bold_prefix="2.")
add_bullet(doc, "Penetration Enhancers: Facilitate drug transport across biomembrane. Main for hydrophilic drugs difficult to penetrate lipid membrane. Three categories based on speed/injury:", bold_prefix="3.")
add_bullet(doc, "Fast, strong, reversible injury: Fatty acids (oleic, linoleic, arachidonic acid) & monoglycerides", indent=1)
add_bullet(doc, "Fast, temporary injury, average activity: Salicylates, bile salts", indent=1)
add_bullet(doc, "Average-strong, sustained histological changes: SLS, EDTA, citric acid", indent=1)

doc.add_paragraph()
add_heading(doc, "11.4 Enhancement of Drug STABILITY (GI)", 2)
add_bullet(doc, "Enteric Coating: Delays drug release in stomach (protects acid-labile drugs). E.g., erythromycin, penicillin V, pancreatin, omeprazole.", bold_prefix="1.")
add_bullet(doc, "Complexation: Increases stability in GI tract. β-cyclodextrins; other agents: caffeine, sodium salicylate, sodium benzoate, nicotinamide.", bold_prefix="2.")
add_bullet(doc, "Bioadhesive Delivery Systems: Intimate contact with GI mucosa → reduces drug degradation.", bold_prefix="3.")
add_bullet(doc, "Metabolism Inhibitors: Selectively inhibit metabolizing enzymes → ↑ fraction absorbed → ↑ bioavailability.", bold_prefix="4.")

doc.add_paragraph()
add_heading(doc, "11.5 Enhancement of GI RETENTION", 2)
add_bullet(doc, "Gastro-Retentive Drug Delivery Systems (GRDDS): Designed to retain drug device in stomach/upper small intestine until complete drug release.", bold_prefix="GRDDS")
add_bullet(doc, "Mechanisms: Based on delayed gastric emptying and controlled release principles.")
add_bullet(doc, "Excipients used: Bioadhesive or swelling on hydration: Cellulose ethers, natural gums, synthetic acrylic acid polymers.")
add_bullet(doc, "Benefits: ↑ contact with epithelial surfaces; prolonged stomach residence; delayed intestinal transit.")

add_highlight_box(doc, "EXAM TIP: Solid solutions show BEST dissolution. Order: Solid solutions > Eutectic mixtures > Solid dispersions > Crystalline drug. Amorphous form is more soluble than crystalline.", fill='E8F5E9', text_color=(0x1B, 0x5E, 0x20))
add_mnemonic(doc, "'MNESS CAS PE' = Micronization, Nanonization, SCF, SFL, EPAS, Surfactants, Cyclodextrin, Amorphs, Salt forms, Precipitation inhibitors, Eutectic/Solid dispersion")

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# EXAM ANSWER NOTES
# ═══════════════════════════════════════════════════════════
add_heading(doc, "📝 EXAM ANSWER NOTES", 1)
doc.add_paragraph()

# ── 10-MARK ANSWERS ──
add_heading(doc, "A. 10-MARK ANSWER NOTES", 2)

add_heading(doc, "Q1. Explain Drug Metabolism with Phase I and Phase II reactions.", 3)
add_bullet(doc, "Introduction: Elimination = Biotransformation + Excretion. Biotransformation = chemical conversion enzymatically.")
add_bullet(doc, "Sites: Liver (primary) > Lungs > Kidneys > Intestine. Order of metabolising ability.")
add_bullet(doc, "Enzymes: Microsomal (ER, majority of reactions) vs Non-microsomal (cytoplasm/mitochondria).")
add_bullet(doc, "Phase I reactions: Oxidation, Reduction, Hydrolysis. Functionalisation. Introduces/unmasks -OH, -COOH, -NH₂, -SH.")
add_bullet(doc, "Phase II reactions: Conjugation with glucuronic acid, sulphate, glycine, glutathione, acetyl groups. Forms highly water-soluble conjugates → renal/biliary excretion.")
add_bullet(doc, "Outcomes: Inactivation (most common), equal activity, toxicological activation, pharmacological activation (prodrugs e.g., enalapril→enalaprilat).")
add_bullet(doc, "Comparison table Phase I vs Phase II.")

doc.add_paragraph()
add_heading(doc, "Q2. Explain Renal Excretion of Drugs with all three processes.", 3)
add_bullet(doc, "Introduction: Nephron as functional unit. 1 million nephrons/kidney.")
add_bullet(doc, "Components: Glomerulus, Proximal tubule, Loop of Henle, Distal tubule, Collecting tubule.")
add_bullet(doc, "Process 1 — Glomerular Filtration: Non-selective, passive, unidirectional. GFR = 120–130 mL/min. Bound drugs NOT filtered. Marker: Inulin, creatinine.")
add_bullet(doc, "Process 2 — Active Tubular Secretion: Proximal tubule. Carrier-mediated, energy requiring, against gradient. Two systems: organic acids (penicillin) + organic bases (morphine). Not affected by pH or protein binding. Excretion > GFR.")
add_bullet(doc, "Process 3 — Tubular Reabsorption: Along all tubules. Passive (pH-dependent; unionized drugs) or Active (endogenous: glucose, electrolytes). Excretion < GFR. ↑ t½. Henderson-Hasselbalch equation.")
add_bullet(doc, "Formula: Rate of excretion = Filtration + Secretion − Reabsorption.")

doc.add_paragraph()
add_heading(doc, "Q3. Explain Bioavailability — definition, types, measurement methods.", 3)
add_bullet(doc, "Definition: Rate and extent of absorption of unchanged drug from dosage form.")
add_bullet(doc, "Absolute BA (F): Compared to IV. Formula: F = (AUCoral × DIV)/(AUCIV × Doral). IV = 100% BA.")
add_bullet(doc, "Relative BA (Fr): Compared to oral standard. Formula: Fr = (AUCtest × Dstd)/(AUCstd × Dtest).")
add_bullet(doc, "Pharmacokinetic methods: Plasma level-time (Cmax, tmax, AUC) + Urinary excretion (dXu/dt max, tu-max, Xu∞).")
add_bullet(doc, "Pharmacodynamic methods: Acute pharmacological response + therapeutic response.")
add_bullet(doc, "Objectives of BA studies: 5 points (drug development, excipient effects, new formulations, quality control, comparison across manufacturers).")

doc.add_paragraph()
add_heading(doc, "Q4. Write a detailed note on BCS with IVIVC.", 3)
add_bullet(doc, "BCS definition: Classification of drugs into 4 classes based on solubility and intestinal permeability.")
add_bullet(doc, "Class I–IV: Table with solubility, permeability, absorption pattern, examples.")
add_bullet(doc, "IVIVC definition: Predictive mathematical model between in vitro dissolution and in vivo response.")
add_bullet(doc, "IVIVC Levels: A (point-to-point, best), B (MRT-based, not useful for QC), C (single-point, limited), Multiple C.")
add_bullet(doc, "BCS and IVIVC expectations: Class I & II → Level A expected. Class III → Level C. Class IV → little or no IVIVC.")
add_bullet(doc, "Biowaivers: When in vivo BE not required (BCS Class I with rapid dissolution + high permeability).")

doc.add_paragraph()
add_heading(doc, "Q5. Describe methods to enhance bioavailability.", 3)
add_bullet(doc, "Introduction: Poor BA due to poor solubility OR poor permeability (BCS Class II, III, IV).")
add_bullet(doc, "Enhancement of Solubility/Dissolution: Micronization, Nanonization, SCF, Surfactants, Salt forms, Solid dispersions, Cyclodextrins, Eutectic mixtures, Solid solutions.")
add_bullet(doc, "Enhancement of Permeability: Ion pairing, Lipid technologies (SMEDDS, SLN, liposomes), Penetration enhancers.")
add_bullet(doc, "Enhancement of Stability: Enteric coating, complexation, bioadhesive systems, metabolism inhibitors.")
add_bullet(doc, "Enhancement of GI retention: GRDDS (gastro-retentive systems).")

doc.add_paragraph()
add_heading(doc, "B. 5-MARK ANSWER NOTES", 2)

add_table(doc,
    ["Topic", "5-Mark Answer Outline"],
    [
        ["Phase I vs Phase II metabolism", "Define each, types of reactions, enzymes involved, products formed, comparison table, 2 examples each"],
        ["Renal Clearance", "Definition, formula ClR = excretion rate/C, physiological formula, clearance ratio, types of clearance and additive property"],
        ["Non-renal excretion routes", "List all 7 routes, 2-3 key points each; focus on biliary (Group A,B,C), mammary (pH, clinical relevance), pulmonary"],
        ["Factors affecting renal excretion", "List all 8 factors with 1-2 points each: physico-chemical, plasma conc, Vd, urine pH, blood flow, biological, interactions, disease"],
        ["Absolute vs Relative Bioavailability", "Define each, symbol, reference standard, formula, purpose, expressed in %"],
        ["Dissolution apparatus", "All 7 apparatus: number, name, key feature, use — table format"],
        ["IVIVC levels", "Define IVIVC, all 4 levels (A, B, C, Multiple C) with what is correlated, usefulness, key feature"],
        ["BCS classification", "4 classes with solubility, permeability, absorption, examples, clinical/regulatory relevance"],
        ["Methods to enhance solubility", "Micronization, Nanonization, Solid dispersion, Cyclodextrins, Salt forms, SCF — definition + mechanism + example for each"],
        ["Bioequivalence studies", "Types of equivalence, when BE studies needed, biowaivers, in vivo vs in vitro BE"],
        ["Urinary excretion studies", "Principle, when applicable, 3 key parameters, criteria, advantages"],
        ["Tubular reabsorption", "Definition, pH dependency, Henderson-Hasselbalch, urine pH effect on weak acids/bases, clinical applications (overdose treatment)"],
    ],
    col_widths=[2.2, 4.3]
)

doc.add_paragraph()
add_heading(doc, "C. 2-MARK ANSWER NOTES", 2)

add_table(doc,
    ["Question", "Answer (2-mark)"],
    [
        ["Define Bioavailability", "Rate and extent (amount) of absorption of unchanged drug from dosage form into systemic circulation. Expressed as F (absolute) or Fr (relative) in percentage."],
        ["What is Absolute Bioavailability?", "F = (AUCoral × DIV)/(AUCIV × Doral). Systemic availability of drug after oral administration compared to IV (reference = 100% BA)."],
        ["What is Relative Bioavailability?", "Fr = (AUCtest × Dstd)/(AUCstd × Dtest). Availability compared to an oral standard of the same drug (e.g., oral solution)."],
        ["Define Biotransformation", "Chemical conversion of a drug to another form, usually enzymatically, within the body. Synonymous with drug metabolism."],
        ["What is Phase I reaction?", "Functionalisation reactions (Oxidation, Reduction, Hydrolysis). Introduces/unmasks polar groups (-OH, -COOH, -NH₂, -SH). Precede Phase II reactions."],
        ["What is Phase II reaction?", "Conjugation reactions. Covalent attachment of polar endogenous molecules (glucuronic acid, sulphate, glycine, glutathione) to drugs → water-soluble conjugates → readily excreted."],
        ["What is Renal Clearance?", "Volume of blood/plasma completely cleared of unchanged drug by the kidney per unit time. Unit: mL/min. ClR = Rate of urinary excretion/Plasma concentration."],
        ["What is GFR?", "Glomerular Filtration Rate = 120–130 mL/min (10% of renal blood flow/1.2L blood per min). Measured by creatinine/inulin clearance."],
        ["Define IVIVC", "Predictive mathematical model describing relationship between in vitro property (dissolution) and in vivo response (plasma conc. or amount absorbed). Main objective = dissolution test as surrogate for BA studies."],
        ["What is BCS Class I?", "High solubility + High permeability. Well absorbed orally. Rate of absorption limited by gastric emptying. Examples: Diltiazem, Propranolol, Metoprolol."],
        ["What is BCS Class IV?", "Low solubility + Low permeability. Poorly absorbed — both limitations present. Examples: Taxol, Furosemide, Chlorothiazide."],
        ["What is LEVEL A IVIVC?", "Highest and most useful level of IVIVC. Point-to-point relationship between in vitro dissolution and in vivo absorption rate. Dissolution curve serves as surrogate for in vivo performance."],
        ["What is Micronization?", "Reduction of solid drug particle size to 1–10 microns (micro milling). ↑ surface area → ↑ dissolution rate. Methods: spray drying, fluid energy/jet mill. Example: Griseofulvin."],
        ["What is Solid Dispersion?", "Dispersion of active ingredient in inert solid carrier. Methods: hot melt, solvent evaporation, hot melt extrusion. Used to enhance dissolution of poorly soluble drugs."],
        ["What is Enterohepatic Recycling?", "Drug excreted in bile → reaches intestine → reabsorbed → returns to liver via portal circulation. Prolongs drug action. Example: oral contraceptives."],
        ["What is Forced Diuresis?", "Increase in urine flow by large fluid intake or diuretics (mannitol) to enhance renal drug elimination. Used in drug overdose treatment for weak acids/bases."],
        ["What is Bioequivalence?", "Two drug products that produce similar bioavailability (AUC, Cmax, tmax within ±20% of each other) such that their PK/PD parameters are essentially the same."],
        ["What are Biowaivers?", "Exemptions from in vivo bioequivalence studies. Granted when: drug product differs only in strength (linear PK), is a solution, for topical/local use, for inhalation, or has acceptable IVIVC."],
        ["What is Cyclodextrin complexation?", "β and γ-cyclodextrins form molecular inclusion complexes with hydrophobic drugs. Hydrophobic cavity traps drug → ↑ aqueous solubility and dissolution rate. Example: NSAIDs, benzodiazepines."],
        ["What is Mammillary excretion?", "Excretion of drugs in breast milk (pH 6.4–7.6). 0.5–1 L milk/day. Amount <1% of dose. Clinical concern: barbiturates, morphine may cause infant toxicity. Tetracycline causes tooth discoloration."],
    ],
    col_widths=[2.5, 4.0]
)

add_page_break(doc)

# ═══════════════════════════════════════════════════════════
# LAST MINUTE REVISION SHEET
# ═══════════════════════════════════════════════════════════
add_heading(doc, "⚡ LAST-MINUTE REVISION SHEET — UNIT 2", 1)
doc.add_paragraph()
add_highlight_box(doc, "Revise this 1 hour before the exam!", fill='FFEBEE', text_color=(0xC6, 0x28, 0x28))
doc.add_paragraph()

add_heading(doc, "🔑 MUST-KNOW DEFINITIONS", 2)
add_bullet(doc, "Elimination = Biotransformation + Excretion")
add_bullet(doc, "Biotransformation = Chemical conversion of drug to another form (enzymatic)")
add_bullet(doc, "Phase I = Functionalisation (OxRHy: Oxidation, Reduction, Hydrolysis)")
add_bullet(doc, "Phase II = Conjugation (Glucuronidation, Sulfation, Glycine, Glutathione, Acetylation, Methylation)")
add_bullet(doc, "Bioavailability = Rate and Extent of absorption of unchanged drug")
add_bullet(doc, "Absolute BA (F) = compared to IV. Relative BA (Fr) = compared to oral standard")
add_bullet(doc, "IVIVC = In vitro dissolution ↔ In vivo absorption (mathematical model)")
add_bullet(doc, "Level A IVIVC = Point-to-point correlation (BEST and most useful)")
add_bullet(doc, "BCS = Biopharmaceutics Classification System (4 classes based on S & P)")
add_bullet(doc, "GFR = 120–130 mL/min; Marker = Creatinine/Inulin")
add_bullet(doc, "Renal Clearance = Rate of urinary excretion / Plasma drug concentration")
add_bullet(doc, "Micronization = Particle size 1–10 μm; Nanonization = 200–600 nm")

doc.add_paragraph()
add_heading(doc, "📊 KEY FORMULAS QUICK REFERENCE", 2)
add_table(doc,
    ["Formula", "Meaning"],
    [
        ["F = (AUCoral × DIV) / (AUCIV × Doral)", "Absolute bioavailability"],
        ["Fr = (AUCtest × Dstd) / (AUCstd × Dtest)", "Relative bioavailability"],
        ["ClR = Rate of urinary excretion / C", "Renal clearance"],
        ["ClTotal = ClR + ClH + ClOther = Dose/AUC", "Total body clearance"],
        ["Renal Clearance Ratio = ClR(drug)/ClR(creatinine)", ">1 = secretion; =1 = filtration only; <1 = reabsorption"],
        ["AUC(trap) = Σ(Cn + Cn+1)/2 × (tn+1 − tn) + Clast/KE", "Trapezoidal rule for AUC"],
        ["Henderson-Hasselbalch (Weak Acid): pH = pKa + log [ionized]/[unionized]", "Degree of ionization of weak acid"],
        ["Henderson-Hasselbalch (Weak Base): pH = pKa + log [unionized]/[ionized]", "Degree of ionization of weak base"],
    ],
    col_widths=[3.5, 3.0]
)

doc.add_paragraph()
add_heading(doc, "⚡ QUICK FACT FLASH CARDS", 2)
add_table(doc,
    ["Point to Remember", "Answer"],
    [
        ["Primary site of drug metabolism?", "LIVER"],
        ["Metabolising ability order?", "Liver > Lungs > Kidneys > Intestine > Placenta > Adrenals > Skin"],
        ["Phase I precedes Phase II? TRUE or FALSE?", "TRUE — Phase I first, then Phase II"],
        ["Most drugs undergo what outcome of metabolism?", "Pharmacological INACTIVATION"],
        ["Example of prodrug (pharmacological activation)?", "Enalapril → Enalaprilat"],
        ["GFR normal value?", "120–130 mL/min"],
        ["Glomerular filtration — plasma protein-bound drug filtered?", "NO — only FREE (unbound) drug is filtered"],
        ["Active tubular secretion affected by pH?", "NO — unaffected by pH and protein binding"],
        ["Tubular reabsorption — what form of drug is reabsorbed?", "UNIONIZED, lipophilic form (passive)"],
        ["To excrete acidic drug → make urine?", "ALKALINE (e.g., NaHCO₃)"],
        ["To excrete basic drug → make urine?", "ACIDIC (e.g., NH₄Cl)"],
        ["IV administration bioavailability =?", "100% (no absorption step)"],
        ["Route with highest bioavailability?", "Parenteral (IV) > Oral > Rectal > Topical"],
        ["Cmax reflects what?", "INTENSITY of action (also rate AND extent of absorption)"],
        ["tmax reflects what?", "RATE of absorption"],
        ["AUC reflects what?", "EXTENT of absorption (total drug absorbed)"],
        ["Most common method for measuring bioavailability?", "Plasma level-time study"],
        ["Urinary excretion study criterion?", "≥20% of dose excreted UNCHANGED in urine"],
        ["Best IVIVC level?", "Level A (point-to-point)"],
        ["BCS Class I examples?", "Diltiazem, Propranolol, Metoprolol (High S + High P)"],
        ["BCS Class IV examples?", "Furosemide, Taxol, Chlorothiazide (Low S + Low P)"],
        ["Dissolution Apparatus 2 name?", "Rotating Paddle (most widely used)"],
        ["Dissolution Apparatus 4 name?", "Flow-Through Cell (perfect sink conditions)"],
        ["Cyclodextrin used for?", "Molecular encapsulation of hydrophobic drugs → ↑ solubility"],
        ["GRDDS is used for?", "Enhancing GI retention time (gastric retention)"],
        ["Enterohepatic recycling causes?", "Prolonged drug action (e.g., oral contraceptives)"],
        ["Solid solutions vs solid dispersions — which is better?", "Solid SOLUTIONS > Solid dispersions in dissolution rate"],
        ["Amorphous vs crystalline — which is more soluble?", "AMORPHOUS > crystalline"],
    ],
    col_widths=[3.2, 3.3]
)

doc.add_paragraph()
add_heading(doc, "🧠 MNEMONICS COLLECTION", 2)
add_mnemonic(doc, "'FIRE COMES FIRST' = Phase I (Functionalisation) before Phase II (Conjugation)")
add_mnemonic(doc, "'OxRHy' = Phase I reactions: Oxidation, Reduction, Hydrolysis")
add_mnemonic(doc, "'GAS GAMe' = Phase II: Glucuronidation, Acetylation, Sulfation, Glycine, Acetylation, Methylation")
add_mnemonic(doc, "'LLIKE' = Drug metabolising organ order: Liver, Lungs, kIdneys, intestine, placenta, adrenals, sKin, Extrahepatic")
add_mnemonic(doc, "'ACID-ALKALINE-OUT' = Acidic drug excreted in ALKaline urine; Basic drug excreted in ACIDic urine")
add_mnemonic(doc, "'TRAP THE ION' = Ionized drugs TRAPPED in tubular lumen → cannot reabsorb → excreted")
add_mnemonic(doc, "'BSP GPMS G' = Biliary, Salivary, Pulmonary, Mammary, GI, Skin, Genital = 7 non-renal routes")
add_mnemonic(doc, "'PAPA ROT' = BA route order: Parenteral > Oral > Rectal > Topical")
add_mnemonic(doc, "'High-High, Low-High, High-Low, Low-Low' = BCS I, II, III, IV (Solubility-Permeability)")
add_mnemonic(doc, "'Level A Is the ACE' = Level A IVIVC is the best (point-to-point; dissolution = surrogate for in vivo)")
add_mnemonic(doc, "'CTA' = Cmax (intensity), Tmax (rate), AUC (extent) — 3 BA parameters")
add_mnemonic(doc, "'MNESS CAS PE' = Micronization, Nanonization, SCF, SFL, EPAS, Surfactants, Cyclodextrins, Amorphs, Salt forms, Precipitation inhibitors, Eutectic/Solid dispersion")

doc.add_paragraph()
add_heading(doc, "📋 FREQUENTLY ASKED EXAM QUESTIONS — UNIT 2", 2)
add_table(doc,
    ["Topic", "Marks", "Frequency"],
    [
        ["Phase I and Phase II reactions of drug metabolism (with comparison table)", "10", "★★★★★"],
        ["Renal excretion — all 3 processes (GF, ATS, TR) with diagram", "10", "★★★★★"],
        ["Bioavailability — definition, absolute vs relative, measurement methods", "10", "★★★★★"],
        ["BCS classification with IVIVC levels", "10/5", "★★★★★"],
        ["Methods to enhance bioavailability (solubility/dissolution)", "10/5", "★★★★★"],
        ["Factors affecting renal excretion", "5/10", "★★★★☆"],
        ["Dissolution apparatus (all 7, App 1 and 2 in detail)", "5", "★★★★☆"],
        ["Non-renal routes of drug excretion (biliary, mammary, pulmonary)", "5", "★★★★☆"],
        ["Tubular reabsorption and pH partition hypothesis", "5", "★★★☆☆"],
        ["Renal clearance and clearance ratio", "5/2", "★★★☆☆"],
        ["IVIVC levels (A, B, C, Multiple C comparison)", "5", "★★★☆☆"],
        ["Bioequivalence studies, types of equivalence, biowaivers", "5", "★★★☆☆"],
        ["Urinary excretion studies for bioavailability measurement", "5", "★★★☆☆"],
        ["Cyclodextrin complexation", "2/5", "★★★☆☆"],
        ["Solid dispersion / Solid solutions / Eutectic mixtures", "2/5", "★★★☆☆"],
    ],
    col_widths=[3.5, 0.8, 1.9]
)

# ─────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────
output_path = r'R:\Phaiml\Biopharmaceutics_Unit2_ExamNotes.docx'
doc.save(output_path)
print(f"SUCCESS! Notes saved to: {output_path}")
