"""
rewards.py — Rewards & Points system endpoints for AMR-Guard.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from firebase_client import (
    get_rewards,
    award_points,
    redeem_points,
    get_leaderboard_data,
)

router = APIRouter()

# ─── Pydantic Models ──────────────────────────────────────────────────────────

class RewardsBalance(BaseModel):
    device_id: str
    points: int
    tier: str
    badges: list[str]
    streak_days: int
    total_scans: int
    total_disposed: int
    next_tier: Optional[str]
    points_to_next_tier: Optional[int]
    transactions: list[dict]
    phone_number: Optional[str] = None

class RedeemRequest(BaseModel):
    device_id: str
    voucher_type: str   # discount_20 | discount_50 | discount_100 | free_delivery

class AwardRequest(BaseModel):
    device_id: str
    amount: int
    reason: str

class LeaderboardUser(BaseModel):
    rank: int
    device_id_short: str   # Only last 8 chars shown — privacy
    tier: str
    points: int
    badges: list[str]
    total_disposed: int
    streak_days: int

class OtpRequest(BaseModel):
    phone_number: str

class OtpVerify(BaseModel):
    phone_number: str
    otp: str
    device_id: str

# ─── Constants ────────────────────────────────────────────────────────────────

TIER_THRESHOLDS = {
    "Scout":        (0,    99),
    "Sentinel":     (100,  499),
    "AMR Guardian": (500,  1999),
    "Maha Guardian":(2000, None),
}

TIER_ORDER = ["Scout", "Sentinel", "AMR Guardian", "Maha Guardian"]

VOUCHER_COSTS = {
    "discount_20":  100,
    "discount_50":  250,
    "discount_100": 500,
    "free_delivery": 150,
}

BADGE_META = {
    "first_scan":    {"label": "First Scan",         "emoji": "🔍", "color": "#0d9488"},
    "scan_10":       {"label": "10 Scans",            "emoji": "📸", "color": "#0d9488"},
    "scan_50":       {"label": "50 Scans",            "emoji": "🏅", "color": "#0d9488"},
    "disposal_1":    {"label": "First Disposal",      "emoji": "♻️", "color": "#22c55e"},
    "disposal_5":    {"label": "5 Safe Disposals",    "emoji": "🌿", "color": "#22c55e"},
    "disposal_20":   {"label": "20 Safe Disposals",   "emoji": "🌳", "color": "#22c55e"},
    "points_100":    {"label": "Century Club",         "emoji": "💯", "color": "#f59e0b"},
    "points_500":    {"label": "AMR Guardian",         "emoji": "🛡️", "color": "#8b5cf6"},
    "points_2000":   {"label": "Maha Guardian",        "emoji": "👑", "color": "#f59e0b"},
    "streak_7":      {"label": "7-Day Streak",         "emoji": "🔥", "color": "#ef4444"},
    "streak_30":     {"label": "30-Day Streak",        "emoji": "⚡", "color": "#ef4444"},
}


def _next_tier_info(points: int) -> tuple[Optional[str], Optional[int]]:
    for i, tier_name in enumerate(TIER_ORDER):
        low, high = TIER_THRESHOLDS[tier_name]
        if high is None or points <= high:
            if i + 1 < len(TIER_ORDER):
                next_name = TIER_ORDER[i + 1]
                next_threshold = TIER_THRESHOLDS[next_name][0]
                return next_name, max(0, next_threshold - points)
            return None, None   # Already Maha Guardian
    return None, None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/rewards/balance/{device_id}", response_model=RewardsBalance)
async def get_balance(device_id: str):
    """Fetch points, tier, badges, and recent transactions for a device."""
    record = get_rewards(device_id)
    pts = record.get("points", 0)
    next_tier, pts_to_next = _next_tier_info(pts)
    return RewardsBalance(
        device_id=device_id,
        points=pts,
        tier=record.get("tier", "Scout"),
        badges=record.get("badges", []),
        streak_days=record.get("streak_days", 0),
        total_scans=record.get("total_scans", 0),
        total_disposed=record.get("total_disposed", 0),
        next_tier=next_tier,
        points_to_next_tier=pts_to_next,
        transactions=record.get("transactions", [])[:20],
        phone_number=record.get("phone_number")
    )


@router.post("/rewards/award")
async def award(req: AwardRequest):
    """
    Internal endpoint to award points (called by other routes after events).
    Also usable by frontend for client-confirmed actions.
    """
    updated = award_points(req.device_id, req.amount, req.reason)
    return {
        "success": True,
        "points_awarded": req.amount,
        "new_balance": updated["points"],
        "new_tier": updated["tier"],
        "new_badges": updated["badges"],
        "streak_days": updated["streak_days"],
    }


@router.post("/rewards/redeem")
async def redeem(req: RedeemRequest):
    """Redeem points for a discount voucher."""
    result = redeem_points(req.device_id, 0, req.voucher_type)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Redemption failed"))
    return result


@router.get("/rewards/voucher-catalog")
async def voucher_catalog():
    """Return available vouchers with their costs."""
    return {
        "vouchers": [
            {
                "id": "discount_20",
                "label": "₹20 Off",
                "description": "₹20 discount on your next purchase at partner pharmacies",
                "points_required": 100,
                "emoji": "🎟️",
            },
            {
                "id": "discount_50",
                "label": "₹50 Off",
                "description": "₹50 discount on your next purchase at partner pharmacies",
                "points_required": 250,
                "emoji": "🎫",
            },
            {
                "id": "discount_100",
                "label": "₹100 Off",
                "description": "₹100 discount on your next purchase at partner pharmacies",
                "points_required": 500,
                "emoji": "🏷️",
            },
            {
                "id": "free_delivery",
                "label": "Free Home Delivery",
                "description": "Free medication delivery from partner pharmacy",
                "points_required": 150,
                "emoji": "🚚",
            },
        ]
    }


@router.get("/rewards/badge-catalog")
async def badge_catalog():
    """Return all possible badges with metadata."""
    return {"badges": BADGE_META}


@router.get("/rewards/individual-leaderboard", response_model=list[LeaderboardUser])
async def individual_leaderboard(limit: int = Query(20, ge=1, le=50)):
    """Return top users by points (privacy-safe — only last 8 chars of device_id shown)."""
    records = get_leaderboard_data()[:limit]
    result = []
    for i, r in enumerate(records):
        did = r.get("device_id", "unknown")
        result.append(LeaderboardUser(
            rank=i + 1,
            device_id_short=f"...{did[-8:]}",
            tier=r.get("tier", "Scout"),
            points=r.get("points", 0),
            badges=r.get("badges", []),
            total_disposed=r.get("total_disposed", 0),
            streak_days=r.get("streak_days", 0),
        ))
    return result

# ─── OTP Auth Flow (Mock) ─────────────────────────────────────────────────────

MOCK_OTPS = {}

@router.post("/auth/request-otp")
async def request_otp(req: OtpRequest):
    """Mocks sending an OTP to a phone number."""
    # In a real app, integrate with Twilio/Firebase Auth
    otp = "123456" # Fixed OTP for demo
    MOCK_OTPS[req.phone_number] = otp
    return {"success": True, "message": "OTP sent successfully."}

@router.post("/auth/verify-otp")
async def verify_otp(req: OtpVerify):
    """Verifies OTP and links device_id to phone_number in Firebase."""
    expected = MOCK_OTPS.get(req.phone_number)
    if not expected or expected != req.otp:
        # For demo purposes, allow 123456 regardless if not requested recently
        if req.otp != "123456":
            raise HTTPException(status_code=400, detail="Invalid OTP")
            
    # Mock saving to DB
    from firebase_client import _make_default, _db, _rewards_ref
    if _db is not None and _rewards_ref is not None:
        doc_ref = _rewards_ref.document(req.device_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({"phone_number": req.phone_number})
        else:
            new_record = _make_default(req.device_id)
            new_record["phone_number"] = req.phone_number
            doc_ref.set(new_record)
            
    return {"success": True, "message": "Phone number linked successfully!"}
