"""
pharmacy.py — Pharmacy panel API: auth, request management, OTP lifecycle, and OTP verification.

Auth:  Simple HMAC-signed token (no extra deps).
       Token = base64( pharmacy_id : expires_unix : sha256_sig )
       Valid for 24 hours.

Edge cases handled:
  - Wrong PIN / unknown pharmacy ID → 401
  - Expired / tampered token → 401
  - Accepting a non-PENDING request → 400
  - OTP generation on wrong status → 400
  - OTP expiry → auto-reset to ACCEPTED so pharmacist can regenerate
  - Max 3 wrong OTP attempts → lock, pharmacist must regenerate
  - User tries to verify an already-COMPLETED request → friendly 400
  - OTP reuse → OTP is nulled on first success, second attempt fails
  - user_id mismatch on verify → 403
  - Cancelling OTP by mistake → reset to ACCEPTED
  - Request not belonging to logged-in pharmacy → 403
"""
from __future__ import annotations

import os
import hmac
import random
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel, Field

import firebase_client as fc

router = APIRouter()

PHARMACY_SECRET = os.getenv("PHARMACY_SECRET", "amrguard-demo-2026")


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------
def _make_token(pharmacy_id: str) -> str:
    expires = int(datetime.now(timezone.utc).timestamp()) + 86400  # 24 h
    payload = f"{pharmacy_id}:{expires}"
    sig = hmac.new(PHARMACY_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _verify_token(token: str) -> Optional[str]:
    """Return pharmacy_id or None."""
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        # format: pharmacy_id:expires:sig
        # pharmacy_id may contain '-' so split from right
        parts = raw.rsplit(":", 2)
        if len(parts) != 3:
            return None
        pharmacy_id, expires_str, sig = parts
        if int(expires_str) < int(datetime.now(timezone.utc).timestamp()):
            return None
        expected = hmac.new(
            PHARMACY_SECRET.encode(),
            f"{pharmacy_id}:{expires_str}".encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        return pharmacy_id
    except Exception:
        return None


async def _auth(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    pid = _verify_token(authorization[7:])
    if not pid:
        raise HTTPException(401, "Invalid or expired pharmacy token")
    return pid


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    pharmacy_id: str
    pin: str = Field(..., min_length=4, max_length=6)


class VerifyOtpRequest(BaseModel):
    request_id: str
    otp: str = Field(..., min_length=6, max_length=6)
    user_id: str


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@router.post("/pharmacy/seed")
async def seed():
    """Seed 3 demo pharmacies into Firestore. Call once."""
    pharmacies = fc.seed_pharmacies()
    return {
        "success": True,
        "message": "Demo pharmacies seeded.",
        "pharmacies": [{"id": p["id"], "name": p["name"], "pin": p["pin_code"]} for p in pharmacies],
    }


@router.post("/pharmacy/login")
async def pharmacy_login(req: LoginRequest):
    pharmacy = fc.verify_pharmacy_pin(req.pharmacy_id, req.pin)
    if not pharmacy:
        raise HTTPException(401, "Invalid pharmacy ID or PIN")
    token = _make_token(req.pharmacy_id)
    return {
        "success": True,
        "token": token,
        "pharmacy_id": req.pharmacy_id,
        "pharmacy_name": pharmacy["name"],
        "expires_in": 86400,
    }


# User-facing OTP verification (public — called from the user app)
@router.post("/takeback/verify-otp")
async def verify_otp(req: VerifyOtpRequest):
    request = fc.get_request(req.request_id)

    # 1. Does the request exist?
    if not request:
        raise HTTPException(404, "Request not found. Check the request ID.")

    # 2. Ownership check
    if request.get("user_id") != req.user_id:
        raise HTTPException(403, "This request does not belong to your device.")

    status = request.get("status")

    # 3. Terminal states
    if status == "COMPLETED":
        raise HTTPException(400, "This request is already completed.")
    if status == "EXPIRED":
        raise HTTPException(400, "This request has expired.")

    # 4. Status must be OTP_GENERATED
    if status == "PENDING":
        raise HTTPException(400, "The pharmacist hasn't accepted your request yet. Please wait.")
    if status == "ACCEPTED":
        raise HTTPException(400, "The pharmacist has accepted but hasn't scanned your medicines yet. Please ask them to generate an OTP.")
    if status != "OTP_GENERATED":
        raise HTTPException(400, f"Cannot verify OTP — request status is '{status}'.")

    # 5. OTP expiry check
    expires_str = request.get("otp_expires_at")
    if expires_str:
        expires_dt = datetime.fromisoformat(expires_str)
        if datetime.now(timezone.utc) > expires_dt:
            # Reset to ACCEPTED so pharmacist can regenerate
            fc.update_request(req.request_id, {
                "status": "ACCEPTED",
                "otp": None,
                "otp_expires_at": None,
                "otp_attempts": 0,
                "updated_at": fc._now_iso(),
            })
            raise HTTPException(400, "OTP has expired. Ask the pharmacist to generate a new one.")

    # 6. Attempt count guard
    attempts = request.get("otp_attempts", 0)
    if attempts >= 3:
        raise HTTPException(400, "Too many wrong attempts. Ask the pharmacist to generate a new OTP.")

    # 7. OTP format check
    if not req.otp.isdigit() or len(req.otp) != 6:
        raise HTTPException(422, "OTP must be exactly 6 digits.")

    # 8. Match check
    stored_otp = request.get("otp")
    if req.otp != stored_otp:
        new_attempts = attempts + 1
        fc.update_request(req.request_id, {
            "otp_attempts": new_attempts,
            "updated_at": fc._now_iso(),
        })
        left = 3 - new_attempts
        if left == 0:
            raise HTTPException(400, "Wrong OTP. No attempts left — ask the pharmacist to regenerate.")
        raise HTTPException(400, f"Wrong OTP. {left} attempt{'s' if left != 1 else ''} remaining.")

    # 9. SUCCESS — complete and award points
    total_pts = request.get("total_points", 0)
    updated_rewards = fc.complete_takeback(req.request_id, req.user_id, total_pts)

    return {
        "success": True,
        "points_earned": total_pts,
        "total_points": updated_rewards.get("points", 0),
        "message": f"Disposal verified! +{total_pts} pts added to your wallet.",
    }


# ---------------------------------------------------------------------------
# Authenticated pharmacy endpoints
# ---------------------------------------------------------------------------

@router.get("/pharmacy/requests")
async def list_requests(pharmacy_id: str = Depends(_auth)):
    requests = fc.get_pharmacy_requests(pharmacy_id, ["PENDING", "ACCEPTED", "OTP_GENERATED"])
    return {"requests": requests, "count": len(requests)}


@router.get("/pharmacy/requests/history")
async def request_history(pharmacy_id: str = Depends(_auth)):
    history = fc.get_pharmacy_history(pharmacy_id, limit=50)
    return {"requests": history, "count": len(history)}


@router.get("/pharmacy/requests/{request_id}")
async def get_single_request(request_id: str, pharmacy_id: str = Depends(_auth)):
    req = fc.get_request(request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if req.get("pharmacy_id") != pharmacy_id:
        raise HTTPException(403, "Access denied — this request is not for your pharmacy")
    return req


@router.post("/pharmacy/requests/{request_id}/accept")
async def accept_request(request_id: str, pharmacy_id: str = Depends(_auth)):
    req = fc.get_request(request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if req.get("pharmacy_id") != pharmacy_id:
        raise HTTPException(403, "Access denied")
    if req.get("status") != "PENDING":
        raise HTTPException(400, f"Cannot accept — request is '{req.get('status')}', not PENDING.")
    fc.update_request(request_id, {"status": "ACCEPTED", "updated_at": fc._now_iso()})
    return {"success": True, "status": "ACCEPTED"}


@router.post("/pharmacy/requests/{request_id}/generate-otp")
async def generate_otp(request_id: str, pharmacy_id: str = Depends(_auth)):
    req = fc.get_request(request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if req.get("pharmacy_id") != pharmacy_id:
        raise HTTPException(403, "Access denied")
    # Allow regeneration from ACCEPTED or OTP_GENERATED (re-gen on expiry / mistake)
    if req.get("status") not in ("ACCEPTED", "OTP_GENERATED"):
        raise HTTPException(400, f"Cannot generate OTP — request is '{req.get('status')}'. Must be ACCEPTED.")

    otp = str(random.randint(100000, 999999))
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    fc.update_request(request_id, {
        "status": "OTP_GENERATED",
        "otp": otp,
        "otp_expires_at": expires_at,
        "otp_attempts": 0,
        "updated_at": fc._now_iso(),
    })
    return {
        "success": True,
        "otp": otp,
        "expires_at": expires_at,
        "expires_in_seconds": 600,
    }


@router.post("/pharmacy/requests/{request_id}/cancel-otp")
async def cancel_otp(request_id: str, pharmacy_id: str = Depends(_auth)):
    """Pharmacist cancels an accidentally generated OTP — resets to ACCEPTED."""
    req = fc.get_request(request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if req.get("pharmacy_id") != pharmacy_id:
        raise HTTPException(403, "Access denied")
    if req.get("status") != "OTP_GENERATED":
        raise HTTPException(400, "No active OTP to cancel.")
    fc.update_request(request_id, {
        "status": "ACCEPTED",
        "otp": None,
        "otp_expires_at": None,
        "otp_attempts": 0,
        "updated_at": fc._now_iso(),
    })
    return {"success": True, "status": "ACCEPTED"}
