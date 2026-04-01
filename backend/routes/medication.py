import random
import math
import uuid
from fastapi import APIRouter, UploadFile, File, Query
from pydantic import BaseModel
from typing import List

router = APIRouter()

# ---------------------------------------------------------------------------
# Mock drug database with Eco-Hazard data
# ---------------------------------------------------------------------------
DRUG_DATABASE = [
    {"name": "Amoxicillin", "type": "Antibiotic", "is_antibiotic": True, "class": "Penicillin", "hazard": 8, "persistence": "Highly persistent in water systems. Promotes resistant bacteria in groundwater."},
    {"name": "Azithromycin", "type": "Antibiotic", "is_antibiotic": True, "class": "Macrolide", "hazard": 9, "persistence": "Extremely persistent. Detected in rivers up to 30km from disposal sites."},
    {"name": "Ciprofloxacin", "type": "Antibiotic", "is_antibiotic": True, "class": "Fluoroquinolone", "hazard": 9, "persistence": "One of the most persistent antibiotics. Creates multi-drug resistant organisms."},
    {"name": "Metronidazole", "type": "Antibiotic", "is_antibiotic": True, "class": "Nitroimidazole", "hazard": 7, "persistence": "Moderately persistent. Can contaminate soil and water for weeks."},
    {"name": "Doxycycline", "type": "Antibiotic", "is_antibiotic": True, "class": "Tetracycline", "hazard": 8, "persistence": "Binds to soil particles. Long-term environmental contamination risk."},
    {"name": "Cephalexin", "type": "Antibiotic", "is_antibiotic": True, "class": "Cephalosporin", "hazard": 7, "persistence": "Moderate persistence. Contributes to resistance gene transfer in bacteria."},
    {"name": "Paracetamol", "type": "Analgesic", "is_antibiotic": False, "class": "Non-opioid", "hazard": 3, "persistence": "Low environmental risk. Biodegrades relatively quickly."},
    {"name": "Ibuprofen", "type": "NSAID", "is_antibiotic": False, "class": "Anti-inflammatory", "hazard": 4, "persistence": "Mild aquatic toxicity. Should still be disposed properly."},
    {"name": "Cetirizine", "type": "Antihistamine", "is_antibiotic": False, "class": "H1-blocker", "hazard": 2, "persistence": "Low environmental persistence. Minimal risk."},
    {"name": "Omeprazole", "type": "Proton Pump Inhibitor", "is_antibiotic": False, "class": "PPI", "hazard": 3, "persistence": "Low toxicity but should not enter water systems."},
]

EXPIRY_STATUSES = [
    {"status": "expired", "label": "Expired"},
    {"status": "expiring_soon", "label": "Expiring Soon"},
    {"status": "valid", "label": "Valid"},
]

# ---------------------------------------------------------------------------
# Safe-Drop Pharmacies & Government Health Centers
# ---------------------------------------------------------------------------
DISPOSAL_CENTRES = [
    {"name": "SafeDrop Pharmacy — MG Road", "address": "12, MG Road, Near City Hospital", "type": "safe_drop_pharmacy", "accepts": ["antibiotics", "general_medication", "syringes"], "offset_lat": 0.004, "offset_lng": 0.003},
    {"name": "District Health Center", "address": "45, Station Road, Opp. Railway Station", "type": "govt_health_center", "accepts": ["antibiotics", "controlled_substances", "general_medication"], "offset_lat": -0.003, "offset_lng": 0.006},
    {"name": "SafeDrop Pharmacy — Market Lane", "address": "78, Market Lane, Near Bus Stand", "type": "safe_drop_pharmacy", "accepts": ["general_medication", "antibiotics"], "offset_lat": 0.006, "offset_lng": -0.004},
    {"name": "Civil Hospital Collection Point", "address": "23, Civil Lines, District Hospital Complex", "type": "govt_health_center", "accepts": ["antibiotics", "controlled_substances", "biomedical_waste"], "offset_lat": -0.005, "offset_lng": -0.002},
    {"name": "SafeDrop Pharmacy — Nehru Nagar", "address": "56, Nehru Nagar, Main Market", "type": "safe_drop_pharmacy", "accepts": ["general_medication", "antibiotics", "syringes"], "offset_lat": 0.002, "offset_lng": 0.008},
]

# Mock Maha-Leaderboard
LEADERBOARD = [
    {"city": "Nashik", "district": "Nashik", "disposals": 1247, "guardians": 312},
    {"city": "Pune", "district": "Pune", "disposals": 1189, "guardians": 298},
    {"city": "Mumbai", "district": "Mumbai", "disposals": 1056, "guardians": 264},
    {"city": "Nagpur", "district": "Nagpur", "disposals": 891, "guardians": 223},
    {"city": "Chhatrapati Sambhajinagar", "district": "Aurangabad", "disposals": 734, "guardians": 184},
]


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------
class AnalysisResult(BaseModel):
    drug_name: str
    drug_type: str
    drug_class: str
    is_antibiotic: bool
    expiry_status: str
    expiry_label: str
    confidence: float
    eco_hazard_score: int
    eco_hazard_info: str
    disposal_recommendation: str


class DisposalCentre(BaseModel):
    id: int
    name: str
    address: str
    type: str
    accepts: List[str]
    lat: float
    lng: float
    distance_km: float


class LeaderboardEntry(BaseModel):
    rank: int
    city: str
    district: str
    disposals: int
    guardians: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/analyze-medication", response_model=AnalysisResult)
async def analyze_medication(file: UploadFile = File(...)):
    """Mock ML classification with Eco-Hazard scoring."""
    contents = await file.read()
    drug = random.choice(DRUG_DATABASE)
    expiry = random.choice(EXPIRY_STATUSES)

    if drug["is_antibiotic"]:
        if expiry["status"] == "expired":
            recommendation = (
                "CRITICAL: This is an expired antibiotic. Do NOT flush or discard in regular trash. "
                "Take it to a SafeDrop Pharmacy or Government Health Center immediately to prevent AMR contamination."
            )
        else:
            recommendation = (
                "This is an antibiotic. Even if not expired, unused antibiotics must never be discarded "
                "in household waste. Drop it at a SafeDrop Pharmacy near you."
            )
    else:
        if expiry["status"] == "expired":
            recommendation = (
                "This medication is expired. Take it to a SafeDrop Pharmacy or Health Center for safe disposal."
            )
        else:
            recommendation = (
                "This medication is still valid. If unused, store safely. When expired, dispose at a SafeDrop Pharmacy."
            )

    return AnalysisResult(
        drug_name=drug["name"],
        drug_type=drug["type"],
        drug_class=drug["class"],
        is_antibiotic=drug["is_antibiotic"],
        expiry_status=expiry["status"],
        expiry_label=expiry["label"],
        confidence=round(random.uniform(0.82, 0.99), 2),
        eco_hazard_score=drug["hazard"],
        eco_hazard_info=drug["persistence"],
        disposal_recommendation=recommendation,
    )


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/nearest-bins", response_model=List[DisposalCentre])
async def nearest_bins(lat: float = Query(...), lng: float = Query(...)):
    """Return nearest SafeDrop Pharmacies and Government Health Centers."""
    centres = []
    for i, c in enumerate(DISPOSAL_CENTRES):
        c_lat, c_lng = lat + c["offset_lat"], lng + c["offset_lng"]
        centres.append(DisposalCentre(
            id=i + 1, name=c["name"], address=c["address"], type=c["type"],
            accepts=c["accepts"], lat=round(c_lat, 6), lng=round(c_lng, 6),
            distance_km=round(_haversine(lat, lng, c_lat, c_lng), 2),
        ))
    centres.sort(key=lambda x: x.distance_km)
    return centres[:3]


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def leaderboard():
    """Return the Maha-Leaderboard: city-wise competition."""
    return [
        LeaderboardEntry(rank=i + 1, **entry)
        for i, entry in enumerate(sorted(LEADERBOARD, key=lambda x: -x["disposals"]))
    ]


@router.get("/device-token")
async def get_device_token():
    """Generate an anonymous device token for tracking contributions."""
    return {"token": str(uuid.uuid4()), "message": "No login required. This token tracks your contributions anonymously."}
