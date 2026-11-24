"""
community.py — Community endpoints (individual leaderboard, centre reporting).
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

REPORTED_CENTRES: list[dict] = []

class CentreReport(BaseModel):
    centre_id: int
    issue: str   # "full" | "closed" | "wrong_location" | "other"
    note: str = ""
    device_id: str

@router.post("/community/report-centre")
async def report_centre(report: CentreReport):
    REPORTED_CENTRES.append({
        "centre_id": report.centre_id,
        "issue": report.issue,
        "note": report.note,
        "device_id": report.device_id,
    })
    return {"success": True, "message": "Report received. Thank you for improving AMR-Guard!"}

@router.get("/community/stats")
async def community_stats():
    """High-level community stats for the Home screen."""
    return {
        "total_disposals_maharashtra": 6117,
        "antibiotics_prevented_grams": 18350,
        "active_guardians": 1281,
        "safedrop_centres": 148,
        "water_litres_protected": 18350000,
    }
