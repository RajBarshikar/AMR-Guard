"""
firebase_client.py — Firebase Firestore wrapper for AMR-Guard rewards system.

If FIREBASE_CREDENTIALS_PATH is not set or the file does not exist, the module
falls back to a thread-safe in-memory store so the entire app works perfectly
in demo / local-dev environments without any Firebase account.

Firestore Document Structure
─────────────────────────────
Collection: rewards
  Document: {device_id}
    points          : int
    tier            : str   ("Scout" | "Sentinel" | "AMR Guardian" | "Maha Guardian")
    badges          : list[str]
    transactions    : list[{id, type, amount, reason, timestamp}]
    take_back_reqs  : list[{id, drug_name, status, centre_id, created_at, points_awarded}]
    streak_days     : int
    last_activity   : str   (ISO date)
    total_disposed  : int   (count of confirmed disposals)
    total_scans     : int
"""

from __future__ import annotations

import os
import uuid
import threading
from datetime import datetime, timezone
from typing import Optional

# ─── Try to load Firebase ────────────────────────────────────────────────────
_firebase_available = False
_db = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    _creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-service-account.json")
    if os.path.exists(_creds_path):
        _cred = credentials.Certificate(_creds_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(_cred)
        _db = firestore.client()
        _firebase_available = True
        print("[AMR-Guard] OK Firebase Firestore connected")
    else:
        print("[AMR-Guard] WARN Firebase credentials not found - using in-memory store")
except Exception as e:
    print(f"[AMR-Guard] WARN Firebase init failed ({e}) - using in-memory store")


# ─── In-Memory Fallback ───────────────────────────────────────────────────────
_lock = threading.Lock()
_mem: dict[str, dict] = {}          # rewards
_mem_pharmacies: dict[str, dict] = {}   # pharmacies
_mem_requests:   dict[str, dict] = {}   # takeback_requests


def _tier_for(points: int) -> str:
    if points >= 2000:
        return "Maha Guardian"
    if points >= 500:
        return "AMR Guardian"
    if points >= 100:
        return "Sentinel"
    return "Scout"


def _check_badges(record: dict) -> list[str]:
    badges = list(record.get("badges", []))
    pts = record.get("points", 0)
    total_scans = record.get("total_scans", 0)
    total_disposed = record.get("total_disposed", 0)
    streak = record.get("streak_days", 0)

    badge_rules = [
        ("first_scan",        total_scans >= 1,    "First Scan"),
        ("scan_10",           total_scans >= 10,   "10 Scans"),
        ("scan_50",           total_scans >= 50,   "50 Scans"),
        ("disposal_1",        total_disposed >= 1, "First Disposal"),
        ("disposal_5",        total_disposed >= 5, "5 Safe Disposals"),
        ("disposal_20",       total_disposed >= 20,"20 Safe Disposals"),
        ("points_100",        pts >= 100,          "Century Club"),
        ("points_500",        pts >= 500,           "AMR Guardian"),
        ("points_2000",       pts >= 2000,         "Maha Guardian"),
        ("streak_7",          streak >= 7,         "7-Day Streak"),
        ("streak_30",         streak >= 30,        "30-Day Streak"),
    ]

    for key, condition, _ in badge_rules:
        if condition and key not in badges:
            badges.append(key)

    return badges


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_default(device_id: str) -> dict:
    return {
        "device_id": device_id,
        "points": 0,
        "tier": "Scout",
        "badges": [],
        "transactions": [],
        "take_back_reqs": [],
        "streak_days": 0,
        "last_activity": None,
        "total_disposed": 0,
        "total_scans": 0,
        "created_at": _now_iso(),
    }


# ─── Public API ───────────────────────────────────────────────────────────────

def get_rewards(device_id: str) -> dict:
    """Return the full rewards record for a device."""
    if _firebase_available:
        doc = _db.collection("rewards").document(device_id).get()
        if doc.exists:
            return doc.to_dict()
        # First time — create the document
        default = _make_default(device_id)
        _db.collection("rewards").document(device_id).set(default)
        return default
    else:
        with _lock:
            if device_id not in _mem:
                _mem[device_id] = _make_default(device_id)
            return dict(_mem[device_id])


def award_points(device_id: str, amount: int, reason: str, meta: Optional[dict] = None) -> dict:
    """
    Award `amount` points to a device, update tier and badges, log transaction.
    Returns the updated record.
    """
    record = get_rewards(device_id)

    record["points"] = record.get("points", 0) + amount
    record["tier"] = _tier_for(record["points"])

    # Streak logic
    today = datetime.now(timezone.utc).date().isoformat()
    last = record.get("last_activity")
    if last:
        from datetime import timedelta, date
        last_date = date.fromisoformat(last[:10])
        delta = (datetime.now(timezone.utc).date() - last_date).days
        if delta == 1:
            record["streak_days"] = record.get("streak_days", 0) + 1
            # Bonus for streak milestones
            if record["streak_days"] in (7, 14, 30):
                bonus = 10 * (record["streak_days"] // 7)
                record["points"] += bonus
                record["transactions"].append({
                    "id": str(uuid.uuid4()),
                    "type": "streak_bonus",
                    "amount": bonus,
                    "reason": f"{record['streak_days']}-day streak bonus!",
                    "timestamp": _now_iso(),
                })
        elif delta > 1:
            record["streak_days"] = 1
    else:
        record["streak_days"] = 1
    record["last_activity"] = today

    # Increment counters based on reason type
    if "scan" in reason.lower():
        record["total_scans"] = record.get("total_scans", 0) + 1
    if "disposal" in reason.lower() and "confirm" in reason.lower():
        record["total_disposed"] = record.get("total_disposed", 0) + 1

    # Update badges
    record["badges"] = _check_badges(record)

    # Log transaction
    txn = {
        "id": str(uuid.uuid4()),
        "type": "earn",
        "amount": amount,
        "reason": reason,
        "timestamp": _now_iso(),
        **(meta or {}),
    }
    record["transactions"] = [txn] + record.get("transactions", [])[:49]  # keep last 50

    _persist(device_id, record)
    return record


def redeem_points(device_id: str, points_to_redeem: int, voucher_type: str) -> dict:
    """
    Redeem points for a voucher. Returns { success, voucher_code, remaining_points }.
    """
    VOUCHER_COSTS = {
        "discount_20":  100,   # ₹20 off
        "discount_50":  250,   # ₹50 off
        "discount_100": 500,   # ₹100 off
        "free_delivery": 150,  # Free delivery from partner pharmacy
    }

    required = VOUCHER_COSTS.get(voucher_type)
    if not required:
        return {"success": False, "error": "Invalid voucher type"}

    record = get_rewards(device_id)
    current_pts = record.get("points", 0)

    if current_pts < required:
        return {"success": False, "error": f"Need {required} pts, you have {current_pts}"}

    voucher_code = f"AMR-{voucher_type.upper()}-{uuid.uuid4().hex[:8].upper()}"
    record["points"] = current_pts - required
    record["tier"] = _tier_for(record["points"])

    txn = {
        "id": str(uuid.uuid4()),
        "type": "redeem",
        "amount": -required,
        "reason": f"Redeemed: {voucher_type}",
        "voucher_code": voucher_code,
        "timestamp": _now_iso(),
    }
    record["transactions"] = [txn] + record.get("transactions", [])[:49]

    _persist(device_id, record)

    return {
        "success": True,
        "voucher_code": voucher_code,
        "voucher_type": voucher_type,
        "points_spent": required,
        "remaining_points": record["points"],
    }


def log_takeback_request(device_id: str, request: dict) -> None:
    """Append a take-back request to the user's record."""
    record = get_rewards(device_id)
    reqs = record.get("take_back_reqs", [])
    reqs = [request] + reqs[:19]  # keep last 20
    record["take_back_reqs"] = reqs
    _persist(device_id, record)


def update_takeback_status(device_id: str, request_id: str, status: str) -> bool:
    """Update status of a specific take-back request."""
    record = get_rewards(device_id)
    for req in record.get("take_back_reqs", []):
        if req.get("id") == request_id:
            req["status"] = status
            req["updated_at"] = _now_iso()
            _persist(device_id, record)
            return True
    return False


def get_leaderboard_data() -> list[dict]:
    """Return individual leaderboard (top 20 by points)."""
    if _firebase_available:
        docs = (
            _db.collection("rewards")
            .order_by("points", direction=firestore.Query.DESCENDING)
            .limit(20)
            .stream()
        )
        return [d.to_dict() for d in docs]
    else:
        with _lock:
            records = sorted(_mem.values(), key=lambda r: r.get("points", 0), reverse=True)
            return records[:20]


def _persist(device_id: str, record: dict) -> None:
    """Write record back to Firebase or in-memory store."""
    if _firebase_available:
        _db.collection("rewards").document(device_id).set(record)
    else:
        with _lock:
            _mem[device_id] = record


# ===========================================================================
# Pharmacy helpers
# ===========================================================================

DEMO_PHARMACIES = [
    {"id": "pharmacy-001", "name": "MedPlus Pune",              "address": "FC Road, Shivaji Nagar, Pune",   "lat": 18.5204, "lng": 73.8567, "pin_code": "1234", "is_verified": True},
    {"id": "pharmacy-002", "name": "Apollo Pharmacy Mumbai",    "address": "Andheri West, Mumbai",           "lat": 19.1136, "lng": 72.8697, "pin_code": "5678", "is_verified": True},
    {"id": "pharmacy-003", "name": "Jan Aushadhi Kendra Satara","address": "Main Road, Satara",             "lat": 17.6805, "lng": 74.0183, "pin_code": "4321", "is_verified": True},
]


def seed_pharmacies() -> list[dict]:
    for p in DEMO_PHARMACIES:
        p_with_ts = {**p, "created_at": _now_iso()}
        if _firebase_available:
            _db.collection("pharmacies").document(p["id"]).set(p_with_ts)
        else:
            with _lock:
                _mem_pharmacies[p["id"]] = p_with_ts
    return DEMO_PHARMACIES


def get_pharmacy(pharmacy_id: str) -> Optional[dict]:
    if _firebase_available:
        doc = _db.collection("pharmacies").document(pharmacy_id).get()
        return doc.to_dict() if doc.exists else None
    with _lock:
        return _mem_pharmacies.get(pharmacy_id)


def verify_pharmacy_pin(pharmacy_id: str, pin: str) -> Optional[dict]:
    pharmacy = get_pharmacy(pharmacy_id)
    if not pharmacy:
        return None
    if pharmacy.get("pin_code") != pin:
        return None
    return pharmacy


def get_or_create_pharmacy(pharmacy_id: str, name: str, address: str) -> dict:
    """Return existing pharmacy or create with PIN 0000."""
    existing = get_pharmacy(pharmacy_id)
    if existing:
        return existing
    new_p = {"id": pharmacy_id, "name": name, "address": address, "pin_code": "0000", "is_verified": False, "created_at": _now_iso()}
    if _firebase_available:
        _db.collection("pharmacies").document(pharmacy_id).set(new_p)
    else:
        with _lock:
            _mem_pharmacies[pharmacy_id] = new_p
    return new_p


def get_user_requests(device_id: str) -> list:
    """Return all take-back requests submitted by this device, newest first."""
    if _firebase_available:
        docs = (
            _db.collection("takeback_requests")
            .where("user_id", "==", device_id)
            .stream()   # No order_by — avoids composite index requirement
        )
        results = [d.to_dict() for d in docs]
        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)
    with _lock:
        return sorted(
            [r for r in _mem_requests.values() if r.get("user_id") == device_id],
            key=lambda x: x.get("created_at", ""), reverse=True
        )


# ===========================================================================
# Takeback-request helpers
# ===========================================================================

def create_takeback_request(request: dict) -> str:
    """Persist a new take-back request document."""
    if _firebase_available:
        _db.collection("takeback_requests").document(request["id"]).set(request)
    else:
        with _lock:
            _mem_requests[request["id"]] = request
    return request["id"]


def get_request(request_id: str) -> Optional[dict]:
    if _firebase_available:
        doc = _db.collection("takeback_requests").document(request_id).get()
        return doc.to_dict() if doc.exists else None
    with _lock:
        return dict(_mem_requests[request_id]) if request_id in _mem_requests else None


def update_request(request_id: str, updates: dict) -> bool:
    if _firebase_available:
        ref = _db.collection("takeback_requests").document(request_id)
        if not ref.get().exists:
            return False
        ref.update(updates)
        return True
    with _lock:
        if request_id not in _mem_requests:
            return False
        _mem_requests[request_id].update(updates)
        return True


def get_pharmacy_requests(pharmacy_id: str, statuses: list) -> list:
    """Return requests for a pharmacy filtered by status list. Sorts in Python to avoid composite-index requirement."""
    if _firebase_available:
        docs = (
            _db.collection("takeback_requests")
            .where("pharmacy_id", "==", pharmacy_id)
            .stream()   # No order_by — avoids composite index requirement
        )
        results = [d.to_dict() for d in docs if d.to_dict().get("status") in statuses]
        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)
    with _lock:
        return sorted(
            [r for r in _mem_requests.values() if r.get("pharmacy_id") == pharmacy_id and r.get("status") in statuses],
            key=lambda x: x.get("created_at", ""), reverse=True
        )


def get_pharmacy_history(pharmacy_id: str, limit: int = 50) -> list:
    if _firebase_available:
        docs = (
            _db.collection("takeback_requests")
            .where("pharmacy_id", "==", pharmacy_id)
            .where("status", "==", "COMPLETED")
            .order_by("completed_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        return [d.to_dict() for d in docs]
    with _lock:
        results = [r for r in _mem_requests.values() if r.get("pharmacy_id") == pharmacy_id and r.get("status") == "COMPLETED"]
        return sorted(results, key=lambda x: x.get("completed_at", ""), reverse=True)[:limit]


def complete_takeback(request_id: str, user_device_id: str, total_points: int) -> dict:
    """Mark request COMPLETED, clear OTP, award points to user."""
    update_request(request_id, {
        "status": "COMPLETED",
        "otp": None,
        "completed_at": _now_iso(),
        "updated_at": _now_iso(),
    })
    return award_points(user_device_id, total_points, f"confirmed_disposal — takeback {request_id[:8]}")


# ─── Scan Analytics ───────────────────────────────────────────────────────────
_mem_scans: list[dict] = []

def save_scan_record(record: dict) -> None:
    """
    Persist a medication scan result (including ERS data) for research analytics.
    Stored in 'scan_records' collection in Firestore, or in-memory for demo.
    """
    record_id = str(uuid.uuid4())
    record = {"id": record_id, **record}
    if _firebase_available and _db:
        try:
            _db.collection("scan_records").document(record_id).set(record)
            return
        except Exception as e:
            print(f"[AMR-Guard] save_scan_record Firestore error: {e}")
    with _lock:
        _mem_scans.append(record)


def get_scan_records(limit: int = 100) -> list[dict]:
    """Return recent scan records for analytics."""
    if _firebase_available and _db:
        try:
            docs = _db.collection("scan_records").limit(limit).stream()
            return [d.to_dict() for d in docs]
        except Exception as e:
            print(f"[AMR-Guard] get_scan_records error: {e}")
    with _lock:
        return list(reversed(_mem_scans[-limit:]))
