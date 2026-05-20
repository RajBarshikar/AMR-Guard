"""
medication.py — Core medication analysis, manual entry, take-back, and OCR endpoints.
"""
from __future__ import annotations

import os
import random
import math
import uuid
import difflib
import requests
from datetime import datetime, timezone, date
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form
from pydantic import BaseModel, Field

from firebase_client import award_points, log_takeback_request, update_takeback_status, get_rewards
import firebase_client as fc

router = APIRouter()

# ---------------------------------------------------------------------------
# Drug Database
# ---------------------------------------------------------------------------
DRUG_DATABASE = [
    {"name": "Amoxicillin",    "type": "Antibiotic", "is_antibiotic": True,  "class": "Penicillin",       "hazard": 8, "amr_resistance_pct": 62, "persistence": "Highly persistent in water systems. Promotes resistant bacteria in groundwater."},
    {"name": "Azithromycin",   "type": "Antibiotic", "is_antibiotic": True,  "class": "Macrolide",        "hazard": 9, "amr_resistance_pct": 71, "persistence": "Extremely persistent. Detected in rivers up to 30km from disposal sites."},
    {"name": "Ciprofloxacin",  "type": "Antibiotic", "is_antibiotic": True,  "class": "Fluoroquinolone",  "hazard": 9, "amr_resistance_pct": 67, "persistence": "One of the most persistent antibiotics. Creates multi-drug resistant organisms."},
    {"name": "Metronidazole",  "type": "Antibiotic", "is_antibiotic": True,  "class": "Nitroimidazole",   "hazard": 7, "amr_resistance_pct": 44, "persistence": "Moderately persistent. Can contaminate soil and water for weeks."},
    {"name": "Doxycycline",    "type": "Antibiotic", "is_antibiotic": True,  "class": "Tetracycline",     "hazard": 8, "amr_resistance_pct": 55, "persistence": "Binds to soil particles. Long-term environmental contamination risk."},
    {"name": "Cephalexin",     "type": "Antibiotic", "is_antibiotic": True,  "class": "Cephalosporin",    "hazard": 7, "amr_resistance_pct": 38, "persistence": "Moderate persistence. Contributes to resistance gene transfer in bacteria."},
    {"name": "Cloxacillin",    "type": "Antibiotic", "is_antibiotic": True,  "class": "Penicillin",       "hazard": 7, "amr_resistance_pct": 41, "persistence": "Moderate persistence. Found in hospital wastewater."},
    {"name": "Levofloxacin",   "type": "Antibiotic", "is_antibiotic": True,  "class": "Fluoroquinolone",  "hazard": 9, "amr_resistance_pct": 58, "persistence": "Very high persistence. Bioaccumulates in aquatic organisms."},
    {"name": "Paracetamol",    "type": "Analgesic",  "is_antibiotic": False, "class": "Non-opioid",       "hazard": 3, "amr_resistance_pct": 0,  "persistence": "Low environmental risk. Biodegrades relatively quickly."},
    {"name": "Ibuprofen",      "type": "NSAID",      "is_antibiotic": False, "class": "Anti-inflammatory","hazard": 4, "amr_resistance_pct": 0,  "persistence": "Mild aquatic toxicity. Should still be disposed properly."},
    {"name": "Cetirizine",     "type": "Antihistamine","is_antibiotic": False,"class": "H1-blocker",      "hazard": 2, "amr_resistance_pct": 0,  "persistence": "Low environmental persistence. Minimal risk."},
    {"name": "Omeprazole",     "type": "PPI",        "is_antibiotic": False, "class": "Proton Pump Inhibitor","hazard": 3, "amr_resistance_pct": 0, "persistence": "Low toxicity but should not enter water systems."},
    {"name": "Metformin",      "type": "Antidiabetic","is_antibiotic": False,"class": "Biguanide",        "hazard": 4, "amr_resistance_pct": 0,  "persistence": "Detected in rivers at measurable concentrations. Dispose properly."},
    {"name": "Amlodipine",     "type": "Antihypertensive","is_antibiotic": False,"class": "CCB",          "hazard": 3, "amr_resistance_pct": 0,  "persistence": "Low environmental impact. Standard safe disposal recommended."},
]

DISPOSAL_CENTRES = [
    {"name": "SafeDrop Pharmacy — MG Road",          "address": "12, MG Road, Near City Hospital",              "type": "safe_drop_pharmacy",  "accepts": ["antibiotics","general_medication","syringes"],                    "offset_lat": 0.004,  "offset_lng": 0.003,  "pharmacy_id": "pharmacy-001"},
    {"name": "District Health Center",               "address": "45, Station Road, Opp. Railway Station",        "type": "govt_health_center",  "accepts": ["antibiotics","controlled_substances","general_medication"],       "offset_lat": -0.003, "offset_lng": 0.006,  "pharmacy_id": "pharmacy-002"},
    {"name": "SafeDrop Pharmacy — Market Lane",      "address": "78, Market Lane, Near Bus Stand",              "type": "safe_drop_pharmacy",  "accepts": ["general_medication","antibiotics"],                               "offset_lat": 0.006,  "offset_lng": -0.004, "pharmacy_id": "pharmacy-003"},
    {"name": "Civil Hospital Collection Point",      "address": "23, Civil Lines, District Hospital Complex",   "type": "govt_health_center",  "accepts": ["antibiotics","controlled_substances","biomedical_waste"],         "offset_lat": -0.005, "offset_lng": -0.002, "pharmacy_id": "pharmacy-001"},
    {"name": "SafeDrop Pharmacy — Nehru Nagar",      "address": "56, Nehru Nagar, Main Market",                 "type": "safe_drop_pharmacy",  "accepts": ["general_medication","antibiotics","syringes"],                    "offset_lat": 0.002,  "offset_lng": 0.008,  "pharmacy_id": "pharmacy-002"},
]

CITY_LEADERBOARD = [
    {"city": "Nashik",                    "district": "Nashik",    "disposals": 1247, "guardians": 312},
    {"city": "Pune",                      "district": "Pune",      "disposals": 1189, "guardians": 298},
    {"city": "Mumbai",                    "district": "Mumbai",    "disposals": 1056, "guardians": 264},
    {"city": "Nagpur",                    "district": "Nagpur",    "disposals": 891,  "guardians": 223},
    {"city": "Chhatrapati Sambhajinagar", "district": "Aurangabad","disposals": 734,  "guardians": 184},
]

# In-memory take-back store (Firebase in production)
_TAKEBACK_STORE: dict[str, dict] = {}
_PUBCHEM_CACHE: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# ERS Engine & PubChem API
# ---------------------------------------------------------------------------
def _get_medicine_data(name: str) -> Optional[dict]:
    name_lower = name.lower()
    if name_lower in _PUBCHEM_CACHE:
        return _PUBCHEM_CACHE[name_lower]
        
    try:
        cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/cids/JSON"
        res = requests.get(cid_url, timeout=5)
        if res.status_code != 200:
            return None
        data = res.json()
        cid = data["IdentifierList"]["CID"][0]
        
        prop_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/XLogP,MolecularWeight,TPSA/JSON"
        res = requests.get(prop_url, timeout=5)
        if res.status_code != 200:
            return None
        props = res.json()["PropertyTable"]["Properties"][0]
        result = {
            "cid": props.get("CID"),
            "xlogp": props.get("XLogP", 0),
            "molecularWeight": props.get("MolecularWeight"),
            "tpsa": props.get("TPSA")
        }
        _PUBCHEM_CACHE[name_lower] = result
        return result
    except Exception as e:
        print(f"[ERS Engine] PubChem API error for {name}: {e}")
        return None

def _calculate_bioaccumulation(xlogp: float) -> int:
    if xlogp < 2: return 1
    if xlogp < 4: return 2
    return 3

def _calculate_persistence(drug_name: str) -> int:
    d = _fuzzy_match_drug(drug_name)
    if d:
        hazard = d.get("hazard", 5)
        if hazard < 4: return 1
        if hazard < 7: return 2
        return 3
    return 2

def _calculate_pf(months_expired: int) -> float:
    if months_expired <= 6: return 0.3
    if months_expired <= 18: return 0.6
    return 0.9

def _calculate_ers(P: int, B: int, PF: float) -> float:
    return (P + B) * PF

def _get_risk_level(score: float) -> dict:
    """Returns risk level label, colour token, and short description."""
    if score <= 2:
        return {"level": "Low Impact",     "color": "#22c55e", "tier": 1, "description": "Minimal environmental threat. Safe disposal still recommended."}
    if score <= 4:
        return {"level": "Moderate Risk",  "color": "#f59e0b", "tier": 2, "description": "Can persist in soil/water. Requires SafeDrop pharmacy disposal."}
    if score <= 7:
        return {"level": "High Risk",      "color": "#ef4444", "tier": 3, "description": "Significant contamination risk. AMR spread likely if improperly discarded."}
    return     {"level": "Critical Risk",  "color": "#7f1d1d", "tier": 4, "description": "Immediate environmental and AMR hazard. Must be neutralised at a certified facility."}

def _risk_label_to_old_format(score: float) -> str:
    if score <= 2: return "Low"
    if score <= 4: return "Medium"
    if score < 7:  return "High"
    return "Critical"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _compute_expiry_risk(drug_name: str, expiry_date_str: Optional[str], is_antibiotic: bool) -> dict:
    """
    Computes ERS (Expiry Risk Score) using the formula: ERS = (P + B) * PF * AMR_mult
    Returns both the legacy flat fields AND a rich ers_data dict for storage & display.
    """
    if not expiry_date_str:
        status = random.choice(["expired", "expiring_soon", "valid"])
        score = random.randint(3, 9) if status == "expired" else 0
        risk_info = _get_risk_level(score)
        ers_data = {
            "score": score,
            "risk_level": risk_info["level"],
            "risk_color": risk_info["color"],
            "risk_tier": risk_info["tier"],
            "risk_description": risk_info["description"],
            "persistence_score": None,
            "bioaccumulation_score": None,
            "persistence_factor": None,
            "amr_multiplier": 1.3 if is_antibiotic else 1.0,
            "raw_score": score,
            "months_expired": 0,
            "formula": "ERS = (P + B) * PF * AMR",
            "formula_values": None,
            "xlogp": None,
            "expiry_known": False,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        return {
            "expiry_status": status,
            "expiry_label": status.replace("_", " ").title(),
            "expiry_risk_score": score,
            "expiry_risk_label": _risk_label_to_old_format(score),
            "months_expired": 0,
            "expiry_date": None,
            "ers_data": ers_data,
        }

    try:
        if len(expiry_date_str) == 7:
            expiry_date_str += "-01"
        exp = date.fromisoformat(expiry_date_str)
    except ValueError:
        exp = None

    today = date.today()

    if exp is None:
        risk_info = _get_risk_level(0)
        ers_data = {
            "score": 0, "risk_level": "Unknown", "risk_color": "#6b7280",
            "risk_tier": 0, "risk_description": "Expiry date could not be parsed.",
            "persistence_score": None, "bioaccumulation_score": None,
            "persistence_factor": None, "amr_multiplier": 1.3 if is_antibiotic else 1.0,
            "raw_score": 0, "months_expired": 0,
            "formula": "ERS = (P + B) * PF * AMR", "formula_values": None,
            "xlogp": None, "expiry_known": False,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        return {
            "expiry_status": "valid", "expiry_label": "Valid",
            "expiry_risk_score": 0, "expiry_risk_label": "Low",
            "months_expired": 0, "expiry_date": expiry_date_str,
            "ers_data": ers_data,
        }
    elif exp < today:
        delta_days = (today - exp).days
        months = delta_days // 30
        status = "expired"
        label = f"Expired {months}mo ago" if months > 0 else "Expired recently"

        # ERS Engine Logic
        pubchem_data = _get_medicine_data(drug_name)
        xlogp = pubchem_data.get("xlogp", 2.0) if pubchem_data else 2.0

        B = _calculate_bioaccumulation(xlogp)
        P = _calculate_persistence(drug_name)
        PF = _calculate_pf(months)
        amr_mult = 1.3 if is_antibiotic else 1.0
        raw_score = _calculate_ers(P, B, PF)
        ers_score = raw_score * amr_mult
        score = min(10, round(ers_score, 2))
        score_int = min(10, int(ers_score))
        risk_info = _get_risk_level(score)

        ers_data = {
            "score": score,
            "risk_level": risk_info["level"],
            "risk_color": risk_info["color"],
            "risk_tier": risk_info["tier"],
            "risk_description": risk_info["description"],
            "persistence_score": P,
            "bioaccumulation_score": B,
            "persistence_factor": PF,
            "amr_multiplier": amr_mult,
            "raw_score": round(raw_score, 2),
            "months_expired": months,
            "formula": "ERS = (P + B) * PF * AMR",
            "formula_values": f"({P} + {B}) * {PF} * {amr_mult} = {round(score, 2)}",
            "xlogp": xlogp,
            "expiry_known": True,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
    elif (exp - today).days <= 90:
        status, label, months, score_int = "expiring_soon", "Expiring Soon", 0, 0
        risk_info = _get_risk_level(0)
        ers_data = {
            "score": 0, "risk_level": "Expiring Soon", "risk_color": "#f59e0b",
            "risk_tier": 1, "risk_description": "Not yet expired but dispose promptly at a SafeDrop pharmacy.",
            "persistence_score": None, "bioaccumulation_score": None,
            "persistence_factor": None, "amr_multiplier": 1.3 if is_antibiotic else 1.0,
            "raw_score": 0, "months_expired": 0,
            "formula": "ERS = (P + B) * PF * AMR", "formula_values": "N/A — not yet expired",
            "xlogp": None, "expiry_known": True,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
    else:
        status, label, months, score_int = "valid", "Valid", 0, 0
        risk_info = _get_risk_level(0)
        ers_data = {
            "score": 0, "risk_level": "No Risk", "risk_color": "#22c55e",
            "risk_tier": 0, "risk_description": "Medicine is within its validity period.",
            "persistence_score": None, "bioaccumulation_score": None,
            "persistence_factor": None, "amr_multiplier": 1.3 if is_antibiotic else 1.0,
            "raw_score": 0, "months_expired": 0,
            "formula": "ERS = (P + B) * PF * AMR", "formula_values": "N/A — not expired",
            "xlogp": None, "expiry_known": True,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "expiry_status": status,
        "expiry_label": label,
        "expiry_risk_score": score_int,
        "expiry_risk_label": _risk_label_to_old_format(score_int),
        "months_expired": months,
        "expiry_date": expiry_date_str,
        "ers_data": ers_data,
    }


def _fuzzy_match_drug(name: str) -> Optional[dict]:
    names = [d["name"].lower() for d in DRUG_DATABASE]
    matches = difflib.get_close_matches(name.lower(), names, n=1, cutoff=0.55)
    if matches:
        return next(d for d in DRUG_DATABASE if d["name"].lower() == matches[0])
    return None


def _disposal_recommendation(drug: dict, expiry_info: dict) -> str:
    status = expiry_info["expiry_status"]
    if drug["is_antibiotic"]:
        if status == "expired":
            return (
                f"CRITICAL: This expired antibiotic ({drug['name']}) must NOT be flushed or binned. "
                f"AMR resistance to this class is {drug['amr_resistance_pct']}% in Maharashtra. "
                "Take it to a SafeDrop Pharmacy or Government Health Center immediately."
            )
        return (
            f"This is an antibiotic. Even if unused, never discard in household waste. "
            f"Local AMR resistance rate: {drug['amr_resistance_pct']}%. Drop at SafeDrop Pharmacy."
        )
    if status == "expired":
        return "This medication is expired. Take it to a SafeDrop Pharmacy for safe disposal."
    return "Still valid. Store safely. When expired, dispose at a SafeDrop Pharmacy — never in the bin or drain."


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class AnalysisResult(BaseModel):
    drug_name: str
    drug_type: str
    drug_class: str
    is_antibiotic: bool
    expiry_status: str
    expiry_label: str
    expiry_date: Optional[str]
    expiry_risk_score: int
    expiry_risk_label: str
    months_expired: int
    eco_hazard_score: int
    eco_hazard_info: str
    amr_resistance_pct: int
    disposal_recommendation: str
    confidence: float
    ocr_raw: Optional[dict] = None
    ers_data: Optional[dict] = None   # Full ERS breakdown for display & storage

class ManualEntryRequest(BaseModel):
    drug_name: str
    quantity: int = Field(default=1, ge=1, le=1000)
    expiry_date: Optional[str] = None   # YYYY-MM or YYYY-MM-DD
    is_antibiotic: Optional[bool] = None
    device_id: Optional[str] = None

class TakeBackRequest(BaseModel):
    device_id: str
    drug_name: str
    medicine_type: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    expiry_date: Optional[str] = None
    is_antibiotic: bool = False
    preferred_centre_id: Optional[int] = None
    preferred_date: Optional[str] = None        # ISO date YYYY-MM-DD
    contact_method: str = "none"                # whatsapp | call | none
    already_dropped: bool = False               # user self-reports immediate drop

class ConfirmDisposalRequest(BaseModel):
    device_id: str
    request_id: str
    centre_id: Optional[int] = None

class ERSRequest(BaseModel):
    drug_name: str
    is_antibiotic: bool
    expiry_date: str

class DisposalCentre(BaseModel):
    id: int
    name: str
    address: str
    type: str
    accepts: List[str]
    lat: float
    lng: float
    distance_km: float
    pharmacy_id: str

class LeaderboardEntry(BaseModel):
    rank: int
    city: str
    district: str
    disposals: int
    guardians: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/gemini-status")
async def gemini_status():
    """Returns whether Gemini Vision API is configured and active."""
    key = os.getenv("GEMINI_API_KEY", "")
    active = bool(key) and key != "your_gemini_api_key_here"
    return {
        "active": active,
        "model": "gemini-2.0-flash" if active else None,
        "mode": "AI Vision OCR" if active else "Demo Mode (mock data)",
    }

@router.post("/analyze-medication", response_model=AnalysisResult)
async def analyze_medication(
    file: UploadFile = File(...),
    district: Optional[str] = Form(None)
):
    """
    Scan a medication image. OCR via Gemini if API key is set, otherwise mock.
    Awards +10 pts (or +25 for antibiotic) to device if device_id header present.
    """
    contents = await file.read()

    ocr_raw = None
    drug = None
    expiry_date_str = None
    confidence = round(random.uniform(0.82, 0.95), 2)

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and gemini_key != "your_gemini_api_key_here" and len(contents) > 100:
        try:
            import json, re

            # ── Try new google-genai SDK first ──────────────────────────────
            try:
                from google import genai as genai_new
                from google.genai import types as genai_types
                client = genai_new.Client(api_key=gemini_key)
                prompt = (
                    "You are a medical OCR assistant. Carefully examine this medication image (strip, box, or blister pack).\n"
                    "Extract the following fields:\n"
                    "- drug_name: exact brand/generic name printed on the pack\n"
                    "- salt_name: active ingredient / salt (if shown)\n"
                    "- expiry_date: expiry date in format MM/YYYY or YYYY-MM (null if not visible)\n"
                    "- batch: batch/lot number (null if not visible)\n"
                    "- manufacturer: manufacturer name (null if not visible)\n"
                    "Return ONLY valid JSON with these keys. No explanation, no markdown."
                )
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[
                        genai_types.Part.from_bytes(data=contents, mime_type="image/jpeg"),
                        prompt,
                    ],
                )
                raw_text = response.text.strip()
            except ImportError:
                # ── Fall back to legacy google-generativeai SDK ──────────────
                import google.generativeai as genai_old
                import io
                from PIL import Image
                genai_old.configure(api_key=gemini_key)
                model = genai_old.GenerativeModel("gemini-1.5-flash")
                img = Image.open(io.BytesIO(contents))
                prompt = (
                    "You are a medical OCR assistant. Extract from this medication image:\n"
                    "- drug_name: brand or generic name\n"
                    "- salt_name: active ingredient (null if not visible)\n"
                    "- expiry_date: in MM/YYYY format (null if not visible)\n"
                    "- batch: batch number (null if not visible)\n"
                    "Return ONLY valid JSON. No markdown, no explanation."
                )
                response = model.generate_content([prompt, img])
                raw_text = response.text.strip()

            # ── Parse JSON from response ─────────────────────────────────────
            # Strip markdown code fences if present
            raw_text = re.sub(r"```json|```", "", raw_text).strip()
            # Extract first JSON object if there's surrounding text
            json_match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
            if json_match:
                raw_text = json_match.group(0)
            ocr_raw = json.loads(raw_text)

            ocr_name = ocr_raw.get("drug_name") or ocr_raw.get("salt_name")
            ocr_exp  = ocr_raw.get("expiry_date")

            # Normalise expiry date → YYYY-MM
            if ocr_exp:
                parts = str(ocr_exp).replace("-", "/").split("/")
                if len(parts) == 2 and len(parts[0]) == 2:          # MM/YYYY
                    expiry_date_str = f"{parts[1]}-{parts[0].zfill(2)}"
                elif len(parts) == 2 and len(parts[0]) == 4:        # YYYY/MM
                    expiry_date_str = f"{parts[0]}-{parts[1].zfill(2)}"
                elif len(parts) == 3:                                # DD/MM/YYYY
                    expiry_date_str = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                else:
                    expiry_date_str = str(ocr_exp)

            if ocr_name:
                drug = _fuzzy_match_drug(ocr_name)
                if drug:
                    confidence = 0.96   # High confidence: known drug confirmed by Gemini
                else:
                    # Unknown — create a generic entry from OCR text
                    display_name = ocr_name.strip().title()
                    drug = {
                        "name": display_name,
                        "type": "Tablet",
                        "is_antibiotic": any(
                            kw in ocr_name.lower()
                            for kw in ["cillin", "mycin", "cycline", "floxacin", "oxacin",
                                       "azole", "conazole", "sulfa", "antibiotic", "bacteria"]
                        ),
                        "class": "Prescription Drug",
                        "hazard": 6,
                        "amr_resistance_pct": 0,
                        "persistence": f"{display_name} was detected via AI scan. Dispose at a SafeDrop pharmacy as a precaution.",
                    }
                    confidence = 0.78
        except Exception as e:
            print(f"[AMR-Guard] Gemini Vision failed: {e} — falling back to mock")
            ocr_raw = None

    # ── Fallback mock if OCR not available or failed ──────────────────────────
    if drug is None:
        drug = random.choice(DRUG_DATABASE)

    expiry_info = _compute_expiry_risk(drug["name"], expiry_date_str, drug["is_antibiotic"])

    # Persist scan record to Firestore for research/analytics
    device_id = None
    try:
        from fastapi import Request
    except Exception:
        pass
    fc.save_scan_record({
        "drug_name": drug["name"],
        "is_antibiotic": drug["is_antibiotic"],
        "eco_hazard_score": drug["hazard"],
        "confidence": confidence,
        "source": "gemini_vision" if ocr_raw else "mock",
        "expiry_date": expiry_date_str,
        "expiry_status": expiry_info["expiry_status"],
        "ers_data": expiry_info.get("ers_data"),
        "district": district,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    })

    return AnalysisResult(
        drug_name=drug["name"],
        drug_type=drug["type"],
        drug_class=drug["class"],
        is_antibiotic=drug["is_antibiotic"],
        confidence=confidence,
        eco_hazard_score=drug["hazard"],
        eco_hazard_info=drug["persistence"],
        amr_resistance_pct=drug.get("amr_resistance_pct", 0),
        disposal_recommendation=_disposal_recommendation(drug, expiry_info),
        ocr_raw=ocr_raw,
        ers_data=expiry_info.get("ers_data"),
        **{k: v for k, v in expiry_info.items() if k != "ers_data"},
    )


@router.post("/manual-entry", response_model=AnalysisResult)
async def manual_entry(req: ManualEntryRequest):
    """
    Manual medication entry — no image needed.
    Awards +5 pts (+15 for antibiotic) if device_id is provided.
    """
    drug = _fuzzy_match_drug(req.drug_name)
    if drug is None:
        # Check if user specified is_antibiotic
        drug = {
            "name": req.drug_name.strip().title(),
            "type": "Unknown",
            "is_antibiotic": req.is_antibiotic or False,
            "class": "Unknown",
            "hazard": 5 if (req.is_antibiotic or False) else 3,
            "amr_resistance_pct": 0,
            "persistence": "Dispose at SafeDrop Pharmacy as a precaution.",
        }

    # Override is_antibiotic if user explicitly told us
    if req.is_antibiotic is not None:
        drug = {**drug, "is_antibiotic": req.is_antibiotic}

    expiry_info = _compute_expiry_risk(drug["name"], req.expiry_date, drug["is_antibiotic"])

    # Award points
    if req.device_id:
        pts = 15 if drug["is_antibiotic"] else 5
        reason = f"Manual entry: {drug['name']} (antibiotic scan)" if drug["is_antibiotic"] else f"Manual entry: {drug['name']}"
        award_points(req.device_id, pts, reason)

    return AnalysisResult(
        drug_name=drug["name"],
        drug_type=drug["type"],
        drug_class=drug["class"],
        is_antibiotic=drug["is_antibiotic"],
        confidence=0.99,  # user knows their own medicine
        eco_hazard_score=drug["hazard"],
        eco_hazard_info=drug["persistence"],
        amr_resistance_pct=drug.get("amr_resistance_pct", 0),
        disposal_recommendation=_disposal_recommendation(drug, expiry_info),
        ocr_raw=None,
        ers_data=expiry_info.get("ers_data"),
        **{k: v for k, v in expiry_info.items() if k != "ers_data"},
    )


@router.get("/drug-search")
async def drug_search(q: str = Query(..., min_length=1)):
    """Autocomplete drug names for manual entry."""
    q_lower = q.lower()
    results = [
        {"name": d["name"], "type": d["type"], "is_antibiotic": d["is_antibiotic"], "class": d["class"]}
        for d in DRUG_DATABASE
        if q_lower in d["name"].lower()
    ]
    # Also fuzzy-match
    fuzzy_names = difflib.get_close_matches(q_lower, [d["name"].lower() for d in DRUG_DATABASE], n=5, cutoff=0.4)
    for fn in fuzzy_names:
        d = next((x for x in DRUG_DATABASE if x["name"].lower() == fn), None)
        if d and not any(r["name"] == d["name"] for r in results):
            results.append({"name": d["name"], "type": d["type"], "is_antibiotic": d["is_antibiotic"], "class": d["class"]})
    return {"results": results[:8]}


@router.post("/calculate-ers")
async def calculate_ers(req: ERSRequest):
    """Calculate ERS live for manual entry."""
    drug = _fuzzy_match_drug(req.drug_name)
    if not drug:
        drug = {
            "name": req.drug_name,
            "type": "General Medicine",
            "is_antibiotic": req.is_antibiotic,
            "class": "Unknown",
            "hazard": 5 if req.is_antibiotic else 2,
            "persistence": "Medium" if req.is_antibiotic else "Low"
        }
    expiry_info = _compute_expiry_risk(drug["name"], req.expiry_date, req.is_antibiotic)
    return {"ers_data": expiry_info.get("ers_data")}


@router.post("/request-takeback")
async def request_takeback(req: TakeBackRequest):
    """
    Request a take-back / self-drop-off.
    Awards +20 pts immediately; +50 more on confirmed disposal.
    """
    request_id = str(uuid.uuid4())
    status = "completed" if req.already_dropped else "pending"

    # Resolve centre name
    centre_name = None
    if req.preferred_centre_id and 1 <= req.preferred_centre_id <= len(DISPOSAL_CENTRES):
        centre_name = DISPOSAL_CENTRES[req.preferred_centre_id - 1]["name"]

    takeback_record = {
        "id": request_id,
        "drug_name": req.drug_name,
        "medicine_type": req.medicine_type,
        "quantity": req.quantity,
        "expiry_date": req.expiry_date,
        "is_antibiotic": req.is_antibiotic,
        "preferred_centre_id": req.preferred_centre_id,
        "centre_name": centre_name,
        "preferred_date": req.preferred_date,
        "contact_method": req.contact_method,
        "already_dropped": req.already_dropped,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "device_id": req.device_id,
    }

    _TAKEBACK_STORE[request_id] = takeback_record
    log_takeback_request(req.device_id, takeback_record)

    # Write to Firestore takeback_requests so pharmacy panel can see it
    pharmacy_id = None
    if req.preferred_centre_id and 1 <= req.preferred_centre_id <= len(DISPOSAL_CENTRES):
        pharmacy_id = DISPOSAL_CENTRES[req.preferred_centre_id - 1].get("pharmacy_id", "pharmacy-001")
    else:
        pharmacy_id = "pharmacy-001"  # default for demo

    disposal_points = 70 if req.is_antibiotic else 50
    firestore_record = {
        **takeback_record,
        "user_id":      req.device_id,
        "pharmacy_id":  pharmacy_id,
        "total_points": disposal_points,
        "otp":          None,
        "otp_expires_at": None,
        "otp_attempts": 0,
    }
    if not req.already_dropped:
        fc.create_takeback_request(firestore_record)

    # Award points
    if req.already_dropped:
        pts = 70 if req.is_antibiotic else 50
        reason = f"Confirmed disposal: {req.drug_name}"
        award_points(req.device_id, pts, f"confirmed_disposal — {reason}")
    else:
        pts = 25 if req.is_antibiotic else 20
        reason = f"Take-back requested: {req.drug_name}"
        award_points(req.device_id, pts, reason)

    expiry_info = _compute_expiry_risk(req.drug_name, req.expiry_date, req.is_antibiotic)

    return {
        "success": True,
        "request_id": request_id,
        "status": status,
        "drug_name": req.drug_name,
        "centre_name": centre_name,
        "preferred_date": req.preferred_date,
        "points_awarded": pts,
        "message": (
            "Disposal logged! Points awarded." if req.already_dropped
            else f"Take-back request created! Show QR at {centre_name or 'any SafeDrop centre'} to earn +50 more pts."
        ),
        "expiry_risk_score": expiry_info["expiry_risk_score"],
        "expiry_risk_label": expiry_info["expiry_risk_label"],
    }


# ---------------------------------------------------------------------------
# Bundle Take-Back endpoint (new flow)
# ---------------------------------------------------------------------------

class BundleItem(BaseModel):
    drug_name: str
    medicine_type: str = "Tablet"  # Tablet | Capsule | Syrup
    quantity: int = Field(default=1, ge=1)
    expiry_date: Optional[str] = None
    is_antibiotic: bool = False


class TakeBackBundleRequest(BaseModel):
    device_id: str
    items: List[BundleItem]
    pharmacy_id: str
    pharmacy_name: str
    pharmacy_address: str = ""
    district: Optional[str] = None


@router.post("/request-takeback-bundle")
async def request_takeback_bundle(req: TakeBackBundleRequest):
    """
    Submit a bundle take-back request with multiple medicines.
    - Auto-registers pharmacy with PIN 0000 if not found.
    - Generates OTP at creation, stored in Firestore — NOT returned to user.
    - Sets status PENDING. Points only awarded after pharmacist OTP is verified by user.
    """
    if not req.items:
        raise HTTPException(400, "Bundle must have at least one medicine.")

    # Auto-register pharmacy with PIN 0000
    fc.get_or_create_pharmacy(req.pharmacy_id, req.pharmacy_name, req.pharmacy_address)

    # Calculate total points for the bundle
    total_points = sum(
        (70 if item.is_antibiotic else 50) for item in req.items
    )

    # Generate OTP now — stored, but not shared with user
    otp = str(random.randint(100000, 999999))
    from datetime import timedelta
    otp_expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    request_id = str(uuid.uuid4())
    req_number = f"REQ-{request_id[:4].upper()}"   # e.g. REQ-A3F2
    items_data = [item.dict() for item in req.items]

    # Per-item ERS computation for storage
    items_with_ers = []
    for item in req.items:
        item_expiry = _compute_expiry_risk(item.drug_name, item.expiry_date, item.is_antibiotic)
        items_with_ers.append({
            **item.dict(),
            "ers_data": item_expiry.get("ers_data"),
            "expiry_status": item_expiry["expiry_status"],
            "expiry_risk_score": item_expiry["expiry_risk_score"],
            "expiry_risk_label": item_expiry["expiry_risk_label"],
        })

    # Bundle-level ERS: max risk item drives the display score
    max_ers = max((i.get("ers_data", {}) or {}).get("score", 0) for i in items_with_ers)
    bundle_risk = _get_risk_level(max_ers)

    firestore_record = {
        "id": request_id,
        "req_number": req_number,
        "user_id": req.device_id,
        "pharmacy_id": req.pharmacy_id,
        "pharmacy_name": req.pharmacy_name,
        "items": items_with_ers,
        "segregation": {
            "Tablets": sum(i.quantity for i in req.items if i.medicine_type == "Tablet"),
            "Capsules": sum(i.quantity for i in req.items if i.medicine_type == "Capsule"),
            "Syrups": sum(i.quantity for i in req.items if i.medicine_type == "Syrup"),
            "Other": sum(i.quantity for i in req.items if i.medicine_type not in ["Tablet", "Capsule", "Syrup"]),
        },
        "drug_name": ", ".join(i.drug_name for i in req.items),
        "medicine_type": req.items[0].medicine_type if req.items else "Tablet",
        "quantity": sum(i.quantity for i in req.items),
        "district": req.district,
        "is_antibiotic": any(i.is_antibiotic for i in req.items),
        "expiry_date": req.items[0].expiry_date if req.items else None,
        "status": "PENDING",
        "otp": otp,
        "otp_expires_at": otp_expires_at,
        "otp_attempts": 0,
        "total_points": total_points,
        "bundle_ers_score": max_ers,
        "bundle_risk_level": bundle_risk["level"],
        "bundle_risk_color": bundle_risk["color"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    fc.create_takeback_request(firestore_record)

    return {
        "success": True,
        "request_id": request_id,
        "req_number": req_number,
        "status": "PENDING",
        "total_points_pending": total_points,
        "item_count": len(req.items),
        "message": f"Request submitted! Visit {req.pharmacy_name} with your medicines. The pharmacist will share an OTP to complete the transaction and credit your points.",
    }


@router.get("/user-requests/{device_id}")
async def get_user_requests(device_id: str):
    """Return all take-back requests submitted by this device, newest first."""
    requests = fc.get_user_requests(device_id)
    return {"requests": requests, "count": len(requests)}



@router.get("/takeback-status/{request_id}")
async def takeback_status(request_id: str, device_id: str = Query(...)):
    record = _TAKEBACK_STORE.get(request_id)
    if not record or record.get("device_id") != device_id:
        raise HTTPException(status_code=404, detail="Request not found")
    return record


@router.post("/confirm-disposal")
async def confirm_disposal(req: ConfirmDisposalRequest):
    """
    Called when a pharmacist / user confirms the physical drop-off.
    Awards +50 pts (or +70 for antibiotic).
    """
    record = _TAKEBACK_STORE.get(req.request_id)
    if not record or record.get("device_id") != req.device_id:
        raise HTTPException(status_code=404, detail="Request not found")

    if record.get("status") == "completed":
        raise HTTPException(status_code=400, detail="Disposal already confirmed")

    record["status"] = "completed"
    record["updated_at"] = datetime.now(timezone.utc).isoformat()
    if req.centre_id:
        record["confirmed_centre_id"] = req.centre_id

    _TAKEBACK_STORE[req.request_id] = record
    update_takeback_status(req.device_id, req.request_id, "completed")

    pts = 70 if record.get("is_antibiotic") else 50
    award_points(req.device_id, pts, f"confirmed_disposal — {record.get('drug_name', 'medication')}")

    return {
        "success": True,
        "points_awarded": pts,
        "message": f"Disposal confirmed! +{pts} pts added to your wallet.",
        "new_status": "completed",
    }


@router.get("/nearest-bins", response_model=List[DisposalCentre])
async def nearest_bins(lat: float = Query(...), lng: float = Query(...)):
    """
    Returns real pharmacies near the user via the Overpass API (OpenStreetMap).
    Falls back to mock offset data if Overpass is unreachable.
    """
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:10];
        (
          node["amenity"="pharmacy"](around:3000,{lat},{lng});
          node["amenity"="hospital"](around:3000,{lat},{lng});
          node["amenity"="clinic"](around:3000,{lat},{lng});
          node["healthcare"="pharmacy"](around:3000,{lat},{lng});
        );
        out 10;
        """
        resp = requests.post(overpass_url, data={"data": query}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            elements = data.get("elements", [])
            centres = []
            for i, el in enumerate(elements[:8]):
                tags = el.get("tags", {})
                name = tags.get("name") or tags.get("name:en") or tags.get("operator") or "Pharmacy"
                amenity = el.get("tags", {}).get("amenity", "pharmacy")
                c_lat = el.get("lat", lat)
                c_lng = el.get("lon", lng)
                dist = round(_haversine(lat, lng, c_lat, c_lng), 2)
                # Build a readable address from OSM tags
                addr_parts = filter(None, [
                    tags.get("addr:housenumber"),
                    tags.get("addr:street"),
                    tags.get("addr:suburb") or tags.get("addr:city"),
                ])
                address = ", ".join(addr_parts) or tags.get("addr:full") or "Address not listed"
                pharmacy_id = f"osm-{el.get('id', i)}"
                centre_type = "govt_health_center" if amenity in ("hospital", "clinic") else "safe_drop_pharmacy"
                accepts = ["antibiotics", "general_medication", "syringes"] if amenity == "pharmacy" else ["antibiotics", "controlled_substances", "general_medication"]
                centres.append(DisposalCentre(
                    id=i + 1,
                    name=name,
                    address=address,
                    type=centre_type,
                    accepts=accepts,
                    lat=round(c_lat, 6),
                    lng=round(c_lng, 6),
                    distance_km=dist,
                    pharmacy_id=pharmacy_id,
                ))
            if centres:
                centres.sort(key=lambda x: x.distance_km)
                return centres[:5]
    except Exception as e:
        print(f"[AMR-Guard] Overpass API failed: {e} — using fallback")

    # ── Fallback: offset-based mock data ────────────────────────────────────
    centres = []
    for i, c in enumerate(DISPOSAL_CENTRES):
        c_lat, c_lng = lat + c["offset_lat"], lng + c["offset_lng"]
        centres.append(DisposalCentre(
            id=i + 1, name=c["name"], address=c["address"], type=c["type"],
            accepts=c["accepts"], lat=round(c_lat, 6), lng=round(c_lng, 6),
            distance_km=round(_haversine(lat, lng, c_lat, c_lng), 2),
            pharmacy_id=c["pharmacy_id"],
        ))
    centres.sort(key=lambda x: x.distance_km)
    return centres[:3]


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def leaderboard():
    return [
        LeaderboardEntry(rank=i+1, **e)
        for i, e in enumerate(sorted(CITY_LEADERBOARD, key=lambda x: -x["disposals"]))
    ]


@router.get("/device-token")
async def get_device_token():
    return {"token": str(uuid.uuid4()), "message": "No login required. This token tracks your contributions anonymously."}
