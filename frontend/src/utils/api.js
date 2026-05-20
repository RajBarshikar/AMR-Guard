import { saveToOfflineQueue, saveScanResult } from './offlineQueue';

const API_BASE = '/api/v1';

// ─── Helpers ─────────────────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: `HTTP ${res.status}` }));
    throw new Error(err.detail || err.message || `Request failed`);
  }
  return res.json();
}

// ─── Medication ───────────────────────────────────────────────────────────────
export async function analyzeMedication(imageBlob, district) {
  if (!navigator.onLine) {
    await saveToOfflineQueue(imageBlob);
    return { result: null, offline: true };
  }
  try {
    const formData = new FormData();
    formData.append('file', imageBlob, 'medication.jpg');
    if (district) formData.append('district', district);
    const result = await apiFetch('/analyze-medication', { method: 'POST', body: formData });
    await saveScanResult(result);
    return { result, offline: false };
  } catch (err) {
    console.warn('[AMR-Guard] API failed, queuing offline:', err.message);
    await saveToOfflineQueue(imageBlob);
    return { result: null, offline: true };
  }
}

export async function getGeminiStatus() {
  try {
    return await apiFetch('/gemini-status');
  } catch {
    return { active: false, mode: 'Demo Mode (mock data)' };
  }
}

export async function submitManualEntry(payload) {
  return apiFetch('/manual-entry', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function searchDrugs(q) {
  return apiFetch(`/drug-search?q=${encodeURIComponent(q)}`);
}

export async function calculateErs(payload) {
  return apiFetch('/calculate-ers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function requestTakeBack(payload) {
  return apiFetch('/request-takeback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

// Bundle take-back — multiple medicines in one request
export async function createTakeBackBundle(payload) {
  return apiFetch('/request-takeback-bundle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

// Get all take-back requests for a user (pending + completed)
export async function getUserRequests(deviceId) {
  return apiFetch(`/user-requests/${encodeURIComponent(deviceId)}`);
}

// User claims points by entering OTP received from pharmacist
export async function claimTakeBackPoints(requestId, otp, userId) {
  return apiFetch('/takeback/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_id: requestId, otp, user_id: userId }),
  });
}

export async function getTakeBackStatus(requestId, deviceId) {
  return apiFetch(`/takeback-status/${requestId}?device_id=${encodeURIComponent(deviceId)}`);
}

export async function confirmDisposal(requestId, deviceId, centreId) {
  return apiFetch('/confirm-disposal', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_id: requestId, device_id: deviceId, centre_id: centreId }),
  });
}

// ─── Map ─────────────────────────────────────────────────────────────────────
export async function getNearestBins(lat, lng) {
  return apiFetch(`/nearest-bins?lat=${lat}&lng=${lng}`);
}

// ─── Leaderboard / Community ──────────────────────────────────────────────────
export async function getLeaderboard() {
  return apiFetch('/leaderboard');
}

export async function getCommunityStats() {
  return apiFetch('/community/stats');
}

export async function reportCentre(payload) {
  return apiFetch('/community/report-centre', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

// ─── Rewards ─────────────────────────────────────────────────────────────────
export async function getRewardsBalance(deviceId) {
  return apiFetch(`/rewards/balance/${encodeURIComponent(deviceId)}`);
}

export async function awardPoints(deviceId, amount, reason) {
  return apiFetch('/rewards/award', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: deviceId, amount, reason }),
  });
}

export async function redeemPoints(deviceId, voucherType) {
  return apiFetch('/rewards/redeem', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: deviceId, voucher_type: voucherType }),
  });
}

export async function getVoucherCatalog() {
  return apiFetch('/rewards/voucher-catalog');
}

export async function getBadgeCatalog() {
  return apiFetch('/rewards/badge-catalog');
}

export async function getIndividualLeaderboard() {
  return apiFetch('/rewards/individual-leaderboard');
}

export async function getDeviceToken() {
  return apiFetch('/device-token');
}

// ─── Pharmacy Portal ──────────────────────────────────────────────────────────
export async function seedPharmacies() {
  return apiFetch('/pharmacy/seed', { method: 'POST' });
}

export async function pharmacyLogin(pharmacy_id, pin) {
  return apiFetch('/pharmacy/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pharmacy_id, pin }),
  });
}

function pharmacyFetch(path, token, opts = {}) {
  return apiFetch(path, {
    ...opts,
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', ...(opts.headers || {}) },
  });
}

export async function getPharmacyRequests(token) {
  return pharmacyFetch('/pharmacy/requests', token);
}

export async function acceptRequest(requestId, token) {
  return pharmacyFetch(`/pharmacy/requests/${requestId}/accept`, token, { method: 'POST' });
}

export async function generateOtp(requestId, token) {
  return pharmacyFetch(`/pharmacy/requests/${requestId}/generate-otp`, token, { method: 'POST' });
}

export async function cancelOtp(requestId, token) {
  return pharmacyFetch(`/pharmacy/requests/${requestId}/cancel-otp`, token, { method: 'POST' });
}

export async function getRequestStatus(requestId, token) {
  return pharmacyFetch(`/pharmacy/requests/${requestId}`, token);
}

export async function verifyOtp(requestId, otp, userId) {
  return apiFetch('/takeback/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_id: requestId, otp, user_id: userId }),
  });
}

// ─── Authentication ──────────────────────────────────────────────────────────

export async function requestAuthOtp(phoneNumber) {
  return apiFetch('/auth/request-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber }),
  });
}

export async function verifyAuthOtp(phoneNumber, otp, deviceId) {
  return apiFetch('/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone_number: phoneNumber, otp, device_id: deviceId }),
  });
}
